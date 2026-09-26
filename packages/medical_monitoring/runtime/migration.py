"""Stable schema-migration coordinator facade."""

from .migration_contracts import *
from .migration_oracles import *
from .migration_steps import *
from .migration_runner_base import MigrationRunnerBase
from .migration_execution import MigrationExecutionMixin
from .migration_recovery import MigrationRecoveryMixin


class MigrationRunner(
    MigrationRecoveryMixin,
    MigrationExecutionMixin,
    MigrationRunnerBase,
):
    """Run one synthetic/offline legacy-to-current project migration."""

def _infer_staging_runtime_root(staged_path: Path) -> Path:
    resolved = staged_path.resolve()
    parts = resolved.parts
    try:
        marker_index = parts.index(MIGRATION_STAGING_DIR_NAME)
    except ValueError as exc:
        raise MigrationError("migration_requires_staging") from exc
    if marker_index == 0:
        return Path(parts[0])
    return Path(*parts[:marker_index])


def migrate_staged_member(
    staged_path: Union[str, Path],
    member: str,
    source_version: str,
    *,
    target_version: Optional[str] = None,
    runtime_root: Optional[Union[str, Path]] = None,
    failure_hook: Optional[Callable[[str], Any]] = None,
    failure_injector: Optional[Callable[[str], Any]] = None,
) -> MigrationStep:
    """Apply one legacy member step to an already-created sibling staging DB.

    This is the narrow migration seam for storage-specific tests and offline
    tooling.  It never accepts a live-project path, creates a ledger row, or
    opens a mutable product store; the full :class:`MigrationRunner` remains
    responsible for backup, cross-member verification, directory switching,
    and recovery.
    """
    path = Path(staged_path)
    if member not in {RUNTIME_MEMBER, LAUNCH_MEMBER}:
        raise MigrationError("migration_operation_conflict")
    expected_target = (
        RUNTIME_V6 if member == RUNTIME_MEMBER else LAUNCH_V5
    )
    if target_version is None:
        target_version = expected_target
    if target_version != expected_target:
        raise MigrationError("migration_operation_conflict")
    allowed_sources = (
        {RUNTIME_V4, RUNTIME_V5}
        if member == RUNTIME_MEMBER
        else {LAUNCH_V1, LAUNCH_V2, LAUNCH_V3, LAUNCH_V4}
    )
    if source_version not in allowed_sources or not path.is_file():
        raise MigrationError("migration_requires_staging")
    root = (
        Path(runtime_root)
        if runtime_root is not None
        else _infer_staging_runtime_root(path)
    )
    runner = MigrationRunner(
        root,
        "staged-member",
        failure_hook=failure_hook if failure_hook is not None else failure_injector,
    )
    try:
        if not runner._is_staging_path(path):
            raise MigrationError("migration_requires_staging")
        step = MigrationStep(
            member=member,
            source_version=source_version,
            target_version=target_version,
            actions=("explicit_staging_step", "verify_exact_target_shape", "update_marker_last"),
        )
        _StepRunner(runner, step).run(path)
        return step
    finally:
        runner.close()


def migrate_runtime_staging(
    staged_path: Union[str, Path],
    source_version: str,
    **kwargs: Any,
) -> MigrationStep:
    return migrate_staged_member(
        staged_path,
        RUNTIME_MEMBER,
        source_version,
        **kwargs,
    )


def migrate_launch_registry_staging(
    staged_path: Union[str, Path],
    source_version: str,
    **kwargs: Any,
) -> MigrationStep:
    return migrate_staged_member(
        staged_path,
        LAUNCH_MEMBER,
        source_version,
        **kwargs,
    )


# Functional entry points keep tests and small offline callers concise.
def inspect_project_schema(workspace: Union[str, Path]) -> ProjectSchemaInspection:
    return ProjectSchemaInspector(workspace).inspect()


def start_project_upgrade(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    idempotency_key: str,
    *,
    confirmation: bool = True,
    confirmed: Optional[bool] = None,
    **kwargs: Any,
) -> MigrationResult:
    runner = MigrationRunner(runtime_root, canonical_project_id, **kwargs)
    try:
        return runner.start_upgrade(
            idempotency_key,
            confirmation=confirmation,
            confirmed=confirmed,
        )
    finally:
        runner.close()


# A source-enumerated list for deterministic failure-injection matrices.  The
# list intentionally includes every boundary implemented above, while DB step
# hooks are generated from the actual plan member/version in _StepRunner.
FAILURE_HOOK_POINTS = (
    "migration.source_recheck.before",
    "migration.source_recheck.after",
    "migration.staging_create.before",
    "migration.staging_create.after",
    "migration.live_quiesce.before",
    "migration.live_quiesce.after",
    "migration.project_oracle.before",
    "migration.project_oracle.after",
    "migration.switch.live_to_rollback.before",
    "migration.switch.live_to_rollback.after",
    "migration.switch.staging_to_live.before",
    "migration.switch.staging_to_live.after",
    "migration.live_reopen.before",
    "migration.live_reopen.after",
    "migration.identity_verification.before",
    "migration.identity_verification.after",
    "migration.rollback.before",
    "migration.rollback.after",
    "migration.ledger_commit.before",
    "migration.ledger_commit.after",
    "migration.recovery.before",
    "migration.recovery.after",
) + tuple(
    "migration.%s.%s.%s" % (member, stage, boundary)
    for member, stages in (
        (RUNTIME_MEMBER, ("ddl", "backfill", "oracle", "marker", "commit")),
        (LAUNCH_MEMBER, ("ddl", "oracle", "marker", "commit")),
    )
    for stage in stages
    for boundary in ("before", "after")
)
HOOK_POINTS = FAILURE_HOOK_POINTS


__all__ = [
    "MigrationError",
    "FAILURE_HOOK_POINTS",
    "HOOK_POINTS",
    "LAUNCH_V1",
    "LAUNCH_V2",
    "LAUNCH_V3",
    "LAUNCH_V4",
    "LAUNCH_V5",
    "MIGRATION_OPERATION_KIND",
    "MIGRATION_ROLLBACK_DIR_NAME",
    "MIGRATION_STAGING_DIR_NAME",
    "InjectedMigrationFailure",
    "MigrationOperation",
    "MigrationOperationLedger",
    "MigrationPlan",
    "MigrationResult",
    "migrate_launch_registry_staging",
    "migrate_runtime_staging",
    "migrate_staged_member",
    "MigrationRunner",
    "MigrationStep",
    "PROGRESS_BACKUP_VERIFIED",
    "PROGRESS_REQUEST_ACCEPTED",
    "PROGRESS_COMPLETE",
    "PROGRESS_CONTENT_UPDATED",
    "PROGRESS_INSPECTION_COMPLETE",
    "PROGRESS_PROJECT_IDLE",
    "PROGRESS_SWITCHED",
    "PROGRESS_STAGED_VERIFIED",
    "PROGRESS_STAGING_COMPLETE",
    "PUBLIC_RECOVERY_STATES",
    "RUNTIME_V4",
    "RUNTIME_V5",
    "RUNTIME_V6",
    "STATUS_REQUESTED",
    "STATUS_ALREADY_CURRENT",
    "STATUS_BACKUP_IN_PROGRESS",
    "STATUS_BACKUP_REQUIRED",
    "STATUS_BACKUP_VERIFIED",
    "STATUS_BLOCKED",
    "STATUS_COMPLETED",
    "STATUS_INSPECTING",
    "STATUS_LEGACY_READONLY",
    "STATUS_LIVE_VERIFYING",
    "STATUS_MAINTENANCE_ACQUIRED",
    "STATUS_MIGRATING",
    "STATUS_MIGRATION_OPERATION_CONFLICT",
    "STATUS_ROLLED_BACK",
    "STATUS_RETAINED_FOR_TRIAGE",
    "STATUS_RETRYABLE_FAILED",
    "TERMINAL_STATES",
    "STATUS_ROLLBACK_IN_PROGRESS",
    "STATUS_STAGED_VERIFIED",
    "STATUS_STAGING",
    "STATUS_SWITCHING",
    "STATUS_WAITING_FOR_PROJECT",
    "inspect_project_schema",
    "start_project_upgrade",
]
