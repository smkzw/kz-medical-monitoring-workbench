"""Stable project backup and restore public facade."""

from .project_backup_support import *
from .project_backup_base import ProjectBackupBase
from .project_backup_archive import ProjectBackupArchiveMixin
from .project_backup_restore import ProjectBackupRestoreMixin


class ProjectBackupManager(
    ProjectBackupRestoreMixin,
    ProjectBackupArchiveMixin,
    ProjectBackupBase,
):
    """Backup, preflight, restore, and atomic rollback for one project."""

ProjectBackup = ProjectBackupManager
BackupManager = ProjectBackupManager
ProjectBackupRestore = ProjectBackupManager


def backup_project(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    *,
    idempotency_key: Optional[str] = None,
    **kwargs: Any,
) -> BackupResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).backup(idempotency_key)


def preflight_backup(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    package: Union[str, Path],
    *,
    idempotency_key: Optional[str] = None,
    **kwargs: Any,
) -> PreflightResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).preflight(package, idempotency_key)


def restore_project(
    runtime_root: Union[str, Path],
    canonical_project_id: str,
    package: Union[str, Path, PreflightResult],
    *,
    idempotency_key: Optional[str] = None,
    confirmation: bool = False,
    **kwargs: Any,
) -> RestoreResult:
    return ProjectBackupManager(runtime_root, canonical_project_id, **kwargs).restore(
        package, idempotency_key, confirmation=confirmation
    )


__all__ = [
    "ARTIFACT_DIR_NAME",
    "BACKUP_PUBLICATION_DIR_NAME",
    "BACKUP_SUFFIX",
    "BackupError",
    "BackupManager",
    "BackupResult",
    "CONTRACT_VERSION",
    "FAILURE_HOOK_POINTS",
    "HOOK_POINTS",
    "InjectedFailure",
    "LAUNCH_REGISTRY_DB_NAME",
    "MAX_ARCHIVE_BYTES",
    "MAX_ARCHIVE_MEMBERS",
    "MAX_MEMBER_BYTES",
    "OPERATIONS_DB_NAME",
    "OP_BACKUP",
    "OP_PREFLIGHT",
    "OP_RESTORE",
    "OperationLedger",
    "OperationRecord",
    "PreflightError",
    "PreflightResult",
    "PROFILE_DB_NAME",
    "ProjectBackup",
    "ProjectBackupError",
    "ProjectBackupManager",
    "ProjectBackupRestore",
    "WorkspaceSnapshot",
    "workspace_fingerprint",
    "RestoreError",
    "RestoreResult",
    "RISK_RULE_DB_NAME",
    "RUN_BINDING_DB_NAME",
    "RUNTIME_DB_NAME",
    "RUNTIME_DIR_NAME",
    "SCHEMA_VERSION",
    "backup_project",
    "canonical_json",
    "canonical_json_bytes",
    "preflight_backup",
    "restore_project",
    "sha256_hex",
]
