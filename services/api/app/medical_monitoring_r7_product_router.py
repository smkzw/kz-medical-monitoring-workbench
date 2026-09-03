"""Project-scoped R7 product mount adapter (Slice-07C-1/2/4).

Thin FastAPI adapters over the frozen ``mm_r7`` run-entry, run-setup and
launch-registry contracts. Import and router construction perform no R7
directory / SQLite / schema / seed writes. Existing runtime routes resolve the
project and authorize first, then open a per-project ``MonitoringRunEntry``
and close it in ``finally``. Setup and product-launch routes use deterministic
synthetic inputs and lazily open project-scoped registries after the same
workspace check.

Product errors are local top-level ``{code, message}`` Chinese envelopes.
This module never registers app-wide exception handlers and never mounts the
isolated ``/api/medical-monitoring/r7`` prefix.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union

from fastapi import APIRouter, Request
from pydantic import ValidationError
from fastapi.responses import JSONResponse

from packages.medical_monitoring.runtime import profile_store as ps
from packages.medical_monitoring.api.run_entry import (
    ProfileFieldsRequest,
    chinese_message_for,
)
from packages.medical_monitoring.runtime.run_entry import (
    PROFILE_DB_NAME,
    RUN_BINDING_DB_NAME,
    MonitoringRunEntry,
    RunEntryError,
)
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
    RuntimeProgressError,
    validate_public_data_cutoff,
)

from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime import run_setup as rs
from packages.medical_monitoring.runtime import project_backup as pb
from packages.medical_monitoring.runtime.maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from packages.medical_monitoring.runtime import launch_registry as lr
from packages.medical_monitoring.runtime.migration import (
    MigrationError,
    MigrationOperationLedger,
    MigrationRunner,
    TERMINAL_STATES,
)
from packages.medical_monitoring.runtime.project_lifecycle import (
    DATA_COVERAGE_COMPLETE,
    DATA_COVERAGE_INCOMPLETE,
    OPEN_MODE_BLOCKED,
    OPEN_MODE_EDIT,
    OPEN_MODE_READONLY,
    ProjectCompatibilityError,
    ProjectOpenDTO,
    ReadOnlyProjectView,
    inspect_project_schema,
    open_project_result,
    open_read_only_project_view,
    require_current_project,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from packages.medical_monitoring.runtime.schema_manifest import (
    SchemaClassification,
    inspect_member,
)
from packages.medical_monitoring.runtime.project_verifier import (
    ProjectVerificationDTO,
    ProjectVerificationError,
    RecoveryCoordinationError,
    RecoveryCoordinator,
    ProjectVerifier,
    RESULT_RECORD_COMPLETE,
    RESULT_RECOVERY_REQUIRED,
)
from packages.medical_monitoring.projections.product_adapter import (
    R5ProductAdapter,
    R5ProductAdapterError,
)
from .monitoring_identity_authorization import (
    MonitoringAction,
    authorize_monitoring_action,
)
from .monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
    MonitoringRuntimePrincipalDenied,
)
from .monitoring_runtime_route_context import (
    MonitoringRuntimeRouteContextError,
    build_monitoring_runtime_route_context,
)


R7_PRODUCT_PREFIX = "/api/projects/{project_id}/modules/medical-monitoring/r7"
R7_PRODUCT_SCHEMA = "mm-r7-product-mount-v1"
R7_RISK_RULE_DB_NAME = "risk_rules.sqlite3"
#
# These are the only product write workflows intentionally reachable while a
# supported legacy project is read-only. Every ordinary project mutation calls
# ``mutable_project_error`` and remains blocked until an upgrade/reopen.
LEGACY_WORKFLOW_WRITE_ROUTES = frozenset(
    {
        "/project/upgrade",
        "/backups",
        "/restores/preflight",
        "/restores",
    }
)
_PRODUCT_BACKUP_WORKERS: dict[tuple[str, str, str, str], threading.Thread] = {}
_PRODUCT_BACKUP_WORKERS_LOCK = threading.RLock()
_PRODUCT_BACKUP_TERMINAL = frozenset({pb.STATUS_AVAILABLE, pb.STATUS_FAILED})
_PRODUCT_RESTORE_TERMINAL = frozenset(
    {
        pb.STATUS_COMPLETED,
        pb.STATUS_ALREADY_CURRENT,
        pb.STATUS_RETAINED_FOR_TRIAGE,
    }
)

_LAYER_KINDS = frozenset(ps.LAYER_KINDS)

class _BlockedLegacyView:
    """Non-readable sentinel used when legacy semantic checks fail."""

    def close(self) -> None:
        return None

    def __getattr__(self, _name: str) -> Any:
        raise ProjectCompatibilityError("project_open_blocked")




from packages.medical_monitoring.api.r7_product.contracts import (
    ProductPublicationError,
    _StrictModel,
    ProductBackupRequest,
    ProductRestorePreflightRequest,
    ProductRestoreRequest,
    ProductProjectUpgradeRequest,
    ProjectOpenResult,
    ProjectUpgradeProgress,
    ProjectUpgradeResult,
    ProductBootstrapRequest,
    ProductCreateRunRequest,
    ProductPrepareExecutionRequest,
    ProductExecutionActionRequest,
    ProductRiskRulePreviewRequest,
    ProductRiskRuleRequest,
    ProductPrepareAndStartRequest,
    ProductPublicationRequest,
)


from packages.medical_monitoring.api.r7_product.public_text import (
    _SECRET_FIELDS,
    _FORBIDDEN_PUBLIC,
    _SECRET_VALUE,
    _RUNTIME_INTERNAL_TOKENS,
    _public_continuity_text,
    _projection,
)
from packages.medical_monitoring.api.r7_product.result_projections import (
    _PUBLICATION_MESSAGES,
    _launch_projection,
    _publication_status_text,
    _publication_projection,
    _PUBLIC_RESULT_LOCATOR_KEYS,
    _PUBLIC_RESULT_FORBIDDEN_KEYS,
    _public_result_projection,
)
from packages.medical_monitoring.api.r7_product.errors import (
    _NOT_FOUND,
    _CONFLICT,
    _BACKUP_NOT_FOUND,
    _BACKUP_CONFLICT,
    _BACKUP_INTERNAL,
    _EXECUTION_STATE_CONFLICT,
    _AUTH_MESSAGES,
    _RUNTIME_MESSAGES,
    _status_for,
    _error_response,
    _run_entry_error_response,
    _launch_error_response,
    _validation_error_response,
)
from packages.medical_monitoring.api.r7_product.continuity_contracts import (
    _normalize_severity_zh,
    _validate_continuity_risk_semantics,
    _continuity_row_sort_key,
    _CONTINUITY_RISK_CHANGE_KINDS_ZH,
    _CONTINUITY_DISPOSITIONS_ZH,
    _CONTINUITY_DATA_CHANGE_KINDS_ZH,
    _CONTINUITY_ATTENTION_TEXTS,
    _CONTINUITY_SEVERITIES,
    _CONTINUITY_OBJECT_TYPES_ZH,
    _SEVERITY_TEXT_MAP,
    _SEVERITY_RANK,
    ProductContinuityChangeCounts,
    ProductContinuityRow,
    ProductContinuityComparison,
    ProductContinuityIdentity,
    ProductContinuityResponse,
)











from packages.medical_monitoring.api.r7_product.backup_projections import (
    _BACKUP_STATUS_LABEL,
    _BACKUP_STEP_LABEL,
    _BACKUP_IMPACT_LABEL,
    _backup_payload_manifest,
    _backup_progress,
    _backup_text,
    _backup_scope_summary,
    _public_backup_projection,
    _public_impact_items,
    _public_preflight_projection,
    _public_restore_projection,
)
from packages.medical_monitoring.api.r7_product.legacy_projections import (
    _legacy_profile_projection,
    _legacy_binding_projection,
    _legacy_launch_record,
    _legacy_risk_projection,
    _legacy_progress_projection,
    _execution_action_projection,
    _safe_setup_projection,
    _setup_projection,
    _runtime_work_units,
)
from packages.medical_monitoring.api.r7_product.public_result_requests import (
    _reject_public_result_body,
    _parse_public_result_query,
    _canonical_public_result_value,
    _parse_public_result_date,
    _comparison_range_text,
)
from packages.medical_monitoring.api.r7_product.runtime_manifest import (
    _publication_manifest_identity,
    _runtime_manifest_digest,
    _runtime_manifest_metadata,
    _runtime_audit_chain_is_invalid,
)
from packages.medical_monitoring.api.r7_product.publication_providers import (
    _r5_publication_types,
    _call_publication_method,
    _publication_provider_value,
    _publication_product_factory,
    _r6_publication_types,
    _call_r6_provider_method,
    _obtain_r6_mode_outputs,
    _validate_r5_publication_packet,
)
from packages.medical_monitoring.api.r7_product.setup_routes import (
    SetupRouteContext,
    register_setup_routes,
)
from packages.medical_monitoring.api.r7_product.run_routes import (
    RunRouteContext,
    register_run_launch_routes,
    register_execution_routes,
    register_run_detail_route,
)
from packages.medical_monitoring.api.r7_product.admission_routes import (
    AdmissionRouteContext,
    register_admission_routes,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    MappingCandidateRouteContext,
    register_mapping_candidate_routes,
)
from packages.medical_monitoring.api.r7_product.fact_routes import (
    FactRouteContext,
    register_fact_routes,
)
from packages.medical_monitoring.api.r7_product.publication_routes import (
    PublicationRouteContext,
    register_publication_routes,
    register_public_result_routes,
)
from packages.medical_monitoring.api.r7_product.project_routes import (
    ProjectRouteContext,
    register_project_routes,
)
from packages.medical_monitoring.api.r7_product.publication_services import (
    build_r5_publication_packet as _build_r5_publication_packet_impl,
    read_publication_gate as _read_publication_gate_impl,
)
from packages.medical_monitoring.api.r7_product.route_utils import (
    R7_WORKSPACE_ROOT_NAME,
    _request_id,
    _workspace_dir,
    _workspace_is_ready,
)
from packages.medical_monitoring.api.r7_product.synthetic_setup import (
    synthetic_setup_inputs as _synthetic_setup_inputs_impl,
)
from packages.medical_monitoring.api.r7_product.continuity_service import (
    build_public_continuity_envelope as _build_public_continuity_envelope_impl,
)
from packages.medical_monitoring.api.r7_product.result_context_service import (
    ResultContextDependencies,
    load_public_result_context as _load_public_result_context_impl,
)
from packages.medical_monitoring.api.r7_product.publication_view_helpers import (
    publication_overlay as _publication_overlay_impl,
    publication_setup_inputs as _publication_setup_inputs_impl,
    record_publication_failure as _record_publication_failure_impl,
    publication_failure_response as _publication_failure_response_impl,
    public_result_envelope as _public_result_envelope_impl,
    public_result_error as _public_result_error_impl,
)
from packages.medical_monitoring.api.r7_product.project_operations import (
    ProjectOperationDependencies,
    build_project_operations,
)





def _build_r5_publication_packet(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
    bridge: Any = None,
    product_packet_factory: Optional[Callable[[Any], Any]] = None,
) -> Any:
    return _build_r5_publication_packet_impl(
        provider,
        identity,
        attempts=attempts,
        bridge=bridge,
        product_packet_factory=product_packet_factory,
    )


def _read_publication_gate(
    workspace: Path,
    run_id: str,
    *,
    entry: MonitoringRunEntry,
    harness_r1_profile: Any,
) -> dict[str, Any]:
    return _read_publication_gate_impl(
        workspace,
        run_id,
        entry=entry,
        harness_r1_profile=harness_r1_profile,
    )

def _synthetic_setup_inputs(
    canonical_project_id: str,
) -> tuple[tuple[rs.DataSnapshot, ...], tuple[rs.PublishedBaseline, ...]]:
    return _synthetic_setup_inputs_impl(canonical_project_id)


def _raise_run_data_not_ready() -> None:
    raise rs.RunSetupError("run_data_not_ready")

def create_medical_monitoring_r7_product_router(
    *,
    runtime_dir: Union[str, Path],
    project_resolver: Callable[[str], str] = lambda project_id: project_id,
    principal_resolver: Optional[
        Callable[[Request], MonitoringAuthenticatedPrincipal | None]
    ] = None,
    require_server_principal: bool = True,
    synthetic_fixture_mode: bool = False,
    maintenance_wait_seconds: float = DEFAULT_WAIT_SECONDS,
    harness_runtime_factory: Optional[Callable[..., Any]] = None,
    harness_adapter: Any = None,
    harness_catalog: Any = None,
    harness_r1_profile: Any = None,
    authority_provider: Any = None,
    r5_authority_provider: Any = None,
    publication_authority_provider: Any = None,
    r5_publication_provider: Any = None,
    r5_authority_bridge: Any = None,
    publication_authority_bridge: Any = None,
    r5_product_packet_factory: Optional[Callable[[Any], Any]] = None,
    r6_output_provider: Any = None,
    r6_publication_provider: Any = None,
    mode_output_provider: Any = None,
    r6_mode_output_provider: Any = None,
    continuity_bridge: Any = None,
    admission_pipeline: Any = None,
    admission_mapping_pipeline: Any = None,
    admission_mapping_confirmation: Any = None,
    monitoring_document_registrar: Any = None,
    admission_fact_materializer: Any = None,
    audit_ledger_factory: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    """Create the project-scoped R7 product router; no workspace I/O here."""
    # Publication never synthesizes authority.  A caller must inject one
    # explicit R5 publication provider (or the already constructed bridge
    # input); the aliases preserve naming compatibility with R5 routes.
    publication_provider = next(
        (
            value
            for value in (
                publication_authority_provider,
                r5_publication_provider,
                r5_authority_provider,
                authority_provider,
            )
            if value is not None
        ),
        None,
    )
    publication_bridge = next(
        (
            value
            for value in (r5_authority_bridge, publication_authority_bridge)
            if value is not None
        ),
        None,
    )
    r6_provider = next(
        (
            value
            for value in (
                r6_output_provider,
                r6_publication_provider,
                mode_output_provider,
                r6_mode_output_provider,
            )
            if value is not None
        ),
        None,
    )

    root = Path(runtime_dir)
    router = APIRouter(prefix=R7_PRODUCT_PREFIX, tags=["medical-monitoring-r7-product"])
    risk_registries: dict[str, rs.RiskRuleRegistry] = {}
    risk_registry_lock = threading.RLock()
    backup_runtime_root = root / R7_WORKSPACE_ROOT_NAME

    project_operations = build_project_operations(
        router,
        ProjectOperationDependencies(
            root=root,
            backup_runtime_root=backup_runtime_root,
            maintenance_wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            risk_registries=risk_registries,
            risk_registry_lock=risk_registry_lock,
            harness_runtime_factory=harness_runtime_factory,
            harness_adapter=harness_adapter,
            harness_catalog=harness_catalog,
            harness_r1_profile=harness_r1_profile,
            project_resolver=project_resolver,
            backup_workers=_PRODUCT_BACKUP_WORKERS,
            backup_workers_lock=_PRODUCT_BACKUP_WORKERS_LOCK,
            backup_terminal=_PRODUCT_BACKUP_TERMINAL,
            restore_terminal=_PRODUCT_RESTORE_TERMINAL,
            recovery_coordinator_factory=(
                lambda *args, **kwargs: RecoveryCoordinator(*args, **kwargs)
            ),
            blocked_legacy_view_type=_BlockedLegacyView,
            monitoring_action=MonitoringAction,
            synthetic_setup_inputs=(
                (lambda project_id: _synthetic_setup_inputs(project_id))
                if synthetic_fixture_mode
                else (lambda _project_id: (_raise_run_data_not_ready()))
            ),
            risk_rule_db_name=R7_RISK_RULE_DB_NAME,
        ),
    )
    acquire_product_write_gate = project_operations.acquire_product_write_gate
    close_cached_risk_registry = project_operations.close_cached_risk_registry
    operation_record = project_operations.operation_record
    backup_source = project_operations.backup_source
    requested_operation_id = project_operations.requested_operation_id
    operation_key = project_operations.operation_key
    reserve_operation = project_operations.reserve_operation
    product_worker_key = project_operations.product_worker_key
    start_worker_once = project_operations.start_worker_once
    mark_worker_failed = project_operations.mark_worker_failed
    start_backup_worker = project_operations.start_backup_worker
    start_restore_worker = project_operations.start_restore_worker
    restore_should_start = project_operations.restore_should_start
    setup_registry = project_operations.setup_registry
    setup_catalog = project_operations.setup_catalog
    open_launch_registry = project_operations.open_launch_registry
    resolve_launch_inputs = project_operations.resolve_launch_inputs
    progress_adapter = project_operations.progress_adapter
    resolve_project = project_operations.resolve_project
    mutable_project_error = project_operations.mutable_project_error
    open_project_inspection = project_operations.open_project_inspection
    verification_context_hashes = project_operations.verification_context_hashes
    verification_projection = project_operations.verification_projection
    operation_projection_for = project_operations.operation_projection_for
    begin_product_boundary = project_operations.begin_product_boundary
    finish_product_boundary = project_operations.finish_product_boundary
    boundary_verification_result = project_operations.boundary_verification_result
    rollback_evidence_digest = project_operations.rollback_evidence_digest
    release_product_rollback = project_operations.release_product_rollback
    classify_product_recovery = project_operations.classify_product_recovery
    migration_records = project_operations.migration_records
    migration_record = project_operations.migration_record
    migration_projection = project_operations.migration_projection
    blocked_project_open_projection = (
        project_operations.blocked_project_open_projection
    )
    open_legacy_view = project_operations.open_legacy_view
    legacy_setup_projection = project_operations.legacy_setup_projection

    def authorize(
        request: Request,
        *,
        project_id: str,
        action: MonitoringAction,
    ) -> Union[MonitoringAuthenticatedPrincipal, None, JSONResponse]:
        if not require_server_principal:
            # Explicit offline TestClient harness only; production host keeps True.
            return None
        if principal_resolver is None:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        try:
            principal = principal_resolver(request)
        except Exception:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        if not isinstance(principal, MonitoringAuthenticatedPrincipal):
            return _error_response(
                503,
                "principal_required",
                _AUTH_MESSAGES["principal_required"],
            )
        try:
            route_context = build_monitoring_runtime_route_context(
                principal,
                request_id=_request_id(request),
                route_project_id=project_id,
                tenant_id=principal.tenant_id,
                target_scope="trial",
                action=action,
            )
            decision = authorize_monitoring_action(
                route_context.principal.to_monitoring_principal(
                    now=route_context.validated_at,
                ),
                route_context.request,
            )
        except MonitoringRuntimePrincipalDenied:
            return _error_response(
                403, "principal_denied", _AUTH_MESSAGES["principal_denied"]
            )
        except (MonitoringRuntimeRouteContextError, ValueError):
            return _error_response(
                403,
                "authorization_invalid",
                _AUTH_MESSAGES["authorization_invalid"],
            )
        if not decision.allowed:
            return _error_response(
                403, "not_permitted", _AUTH_MESSAGES["not_permitted"]
            )
        return principal

    async def _read_json_object(request: Request) -> Union[dict[str, Any], JSONResponse]:
        raw = await request.body()
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        return payload

    def _validated_layer_scope(
        *,
        layer_kind: str,
        scope_key: str,
        canonical_project_id: str,
    ) -> Union[str, JSONResponse]:
        if layer_kind not in _LAYER_KINDS:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if (
            not isinstance(scope_key, str)
            or not scope_key.strip()
            or scope_key != scope_key.strip()
        ):
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_GLOBAL_DEFAULT and scope_key != ps.GLOBAL_SCOPE_KEY:
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_PROJECT:
            resolved_scope = resolve_project(scope_key)
            if (
                isinstance(resolved_scope, JSONResponse)
                or resolved_scope != canonical_project_id
            ):
                return _error_response(
                    422,
                    "empty_or_illegal_scope_key",
                    chinese_message_for("empty_or_illegal_scope_key"),
                )
            return canonical_project_id
        return scope_key

    def _auto_scopes(
        entry: MonitoringRunEntry,
        *,
        canonical_project_id: str,
        run_id: str,
        capability_scope_key: str,
    ) -> dict[str, str]:
        project_scope = ""
        if (
            entry.profile_store.latest_revision(ps.LAYER_PROJECT, canonical_project_id)
            is not None
        ):
            project_scope = canonical_project_id
        run_scope = ""
        if entry.profile_store.latest_revision(ps.LAYER_RUN_OVERRIDE, run_id) is not None:
            run_scope = run_id
        return {
            "capability_scope_key": capability_scope_key or "",
            "project_scope_key": project_scope,
            "run_override_scope_key": run_scope,
        }

    def _open_entry(
        workspace: Path,
        *,
        allow_create: bool,
    ) -> Union[MonitoringRunEntry, JSONResponse]:
        if not allow_create and not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(workspace.name)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            return MonitoringRunEntry(workspace)
        except RunEntryError as exc:
            return _run_entry_error_response(exc)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    def _publication_overlay(
        canonical_project_id: str,
        run_id: str,
        base: Mapping[str, Any],
    ) -> dict[str, Any]:
        return _publication_overlay_impl(
            root, canonical_project_id, run_id, base
        )

    def _publication_setup_inputs(
        canonical_project_id: str,
        launch: lr.LaunchRecord,
    ) -> tuple[
        rs.DataSnapshot,
        rs.WorkUnitManifest,
        tuple[str, ...],
        dict[str, Any],
        str,
    ]:
        return _publication_setup_inputs_impl(
            resolve_launch_inputs, canonical_project_id, launch
        )

    def _record_publication_failure(
        registry: lr.LaunchRegistry,
        publication: lr.ResultPublication,
        *,
        code: str,
        recoverable: bool,
    ) -> lr.ResultPublication:
        return _record_publication_failure_impl(
            registry,
            publication,
            code=code,
            recoverable=recoverable,
        )

    def _publication_failure_response(
        publication: lr.ResultPublication,
    ) -> JSONResponse:
        return _publication_failure_response_impl(publication)

    result_context_dependencies = ResultContextDependencies(
        root=root,
        open_legacy_view=open_legacy_view,
        open_launch_registry=open_launch_registry,
        open_entry=_open_entry,
        publication_setup_inputs=_publication_setup_inputs,
        publication_bridge=publication_bridge,
        publication_provider=publication_provider,
        r5_product_packet_factory=r5_product_packet_factory,
        harness_r1_profile=harness_r1_profile,
        build_r5_publication_packet=(
            lambda *args, **kwargs: _build_r5_publication_packet(
                *args, **kwargs
            )
        ),
        read_publication_gate=(
            lambda *args, **kwargs: _read_publication_gate(*args, **kwargs)
        ),
    )

    def _load_public_result_context(
        canonical_project_id: str,
        result_context_token: str,
        *,
        site_ref: Optional[str] = None,
        require_product_adapter: bool = True,
        continuity_context: bool = False,
    ) -> tuple[
        lr.LaunchRegistry,
        MonitoringRunEntry,
        lr.LaunchRecord,
        lr.ResultPublication,
        Optional[R5ProductAdapter],
    ]:
        return _load_public_result_context_impl(
            result_context_dependencies,
            canonical_project_id,
            result_context_token,
            site_ref=site_ref,
            require_product_adapter=require_product_adapter,
            continuity_context=continuity_context,
        )

    def _public_result_envelope(
        result: Mapping[str, Any],
        *,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        result_context_token: str,
    ) -> dict[str, Any]:
        return _public_result_envelope_impl(
            result,
            launch=launch,
            publication=publication,
            result_context_token=result_context_token,
        )

    def _public_result_error(exc: Exception) -> JSONResponse:
        return _public_result_error_impl(exc)

    def _build_public_continuity_envelope(
        *,
        registry: lr.LaunchRegistry,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        adapter: R5ProductAdapter,
        result_context_token: str,
        site_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        return _build_public_continuity_envelope_impl(
            root,
            registry=registry,
            launch=launch,
            publication=publication,
            adapter=adapter,
            result_context_token=result_context_token,
            site_ref=site_ref,
        )

    register_project_routes(
        router,
        ProjectRouteContext(
            root=root,
            backup_runtime_root=backup_runtime_root,
            maintenance_wait_seconds=maintenance_wait_seconds,
            resolve_project=resolve_project,
            authorize=authorize,
            blocked_project_open_projection=blocked_project_open_projection,
            open_project_inspection=open_project_inspection,
            verification_projection=verification_projection,
            read_json_object=_read_json_object,
            begin_product_boundary=begin_product_boundary,
            boundary_verification_result=boundary_verification_result,
            classify_product_recovery=classify_product_recovery,
            finish_product_boundary=finish_product_boundary,
            operation_key=operation_key,
            operation_projection_for=operation_projection_for,
            migration_projection=migration_projection,
            migration_records=migration_records,
            migration_record=migration_record,
            reserve_operation=reserve_operation,
            start_backup_worker=start_backup_worker,
            operation_record=operation_record,
            backup_source=backup_source,
            requested_operation_id=requested_operation_id,
            restore_should_start=restore_should_start,
            start_restore_worker=start_restore_worker,
            acquire_product_write_gate=acquire_product_write_gate,
            mutable_project_error=mutable_project_error,
            open_entry=_open_entry,
            workspace_dir=_workspace_dir,
            backup_terminal=_PRODUCT_BACKUP_TERMINAL,
            monitoring_action=MonitoringAction,
        ),
    )

    register_setup_routes(
        router,
        SetupRouteContext(
            root=root,
            resolve_project=resolve_project,
            authorize=authorize,
            mutable_project_error=mutable_project_error,
            read_json_object=_read_json_object,
            acquire_product_write_gate=acquire_product_write_gate,
            open_entry=_open_entry,
            legacy_setup_projection=legacy_setup_projection,
            setup_catalog=setup_catalog,
            setup_registry=setup_registry,
            open_legacy_view=open_legacy_view,
            validated_layer_scope=_validated_layer_scope,
            workspace_dir=_workspace_dir,
            risk_registry_lock=risk_registry_lock,
            monitoring_action=MonitoringAction,
        ),
    )

    run_route_context = RunRouteContext(
        root=root,
        resolve_project=resolve_project,
        authorize=authorize,
        mutable_project_error=mutable_project_error,
        read_json_object=_read_json_object,
        acquire_product_write_gate=acquire_product_write_gate,
        open_entry=_open_entry,
        auto_scopes=_auto_scopes,
        open_launch_registry=open_launch_registry,
        progress_adapter=progress_adapter,
        resolve_launch_inputs=resolve_launch_inputs,
        open_legacy_view=open_legacy_view,
        publication_overlay=_publication_overlay,
        workspace_dir=_workspace_dir,
        workspace_is_ready=_workspace_is_ready,
        monitoring_action=MonitoringAction,
    )
    register_run_launch_routes(router, run_route_context)

    publication_route_context = PublicationRouteContext(
        root=root,
        resolve_project=resolve_project,
        authorize=authorize,
        mutable_project_error=mutable_project_error,
        read_json_object=_read_json_object,
        acquire_product_write_gate=acquire_product_write_gate,
        open_entry=_open_entry,
        publication_failure_response=_publication_failure_response,
        publication_setup_inputs=_publication_setup_inputs,
        record_publication_failure=_record_publication_failure,
        open_launch_registry=open_launch_registry,
        progress_adapter=progress_adapter,
        publication_bridge=publication_bridge,
        publication_provider=publication_provider,
        r5_product_packet_factory=r5_product_packet_factory,
        r6_provider=r6_provider,
        harness_r1_profile=harness_r1_profile,
        open_legacy_view=open_legacy_view,
        load_public_result_context=_load_public_result_context,
        public_result_envelope=_public_result_envelope,
        public_result_error=_public_result_error,
        build_public_continuity_envelope=_build_public_continuity_envelope,
        workspace_dir=_workspace_dir,
        build_r5_publication_packet=(
            lambda *args, **kwargs: _build_r5_publication_packet(
                *args, **kwargs
            )
        ),
        read_publication_gate=(
            lambda *args, **kwargs: _read_publication_gate(*args, **kwargs)
        ),
        monitoring_action=MonitoringAction,
    )
    register_publication_routes(router, publication_route_context)
    register_execution_routes(router, run_route_context)

    register_public_result_routes(router, publication_route_context)
    register_run_detail_route(router, run_route_context)

    register_admission_routes(
        router,
        AdmissionRouteContext(
            root=root,
            resolve_project=resolve_project,
            authorize=authorize,
            read_json_object=_read_json_object,
            acquire_product_write_gate=acquire_product_write_gate,
            workspace_dir=_workspace_dir,
            monitoring_action=MonitoringAction,
            admission_pipeline=admission_pipeline,
        ),
    )

    register_mapping_candidate_routes(
        router,
        MappingCandidateRouteContext(
            root=root,
            resolve_project=resolve_project,
            authorize=authorize,
            acquire_product_write_gate=acquire_product_write_gate,
            workspace_dir=_workspace_dir,
            monitoring_action=MonitoringAction,
            admission_mapping_pipeline=admission_mapping_pipeline,
            admission_mapping_confirmation=admission_mapping_confirmation,
            monitoring_document_registrar=monitoring_document_registrar,
        ),
    )
    register_fact_routes(
        router,
        FactRouteContext(
            root=root,
            resolve_project=resolve_project,
            authorize=authorize,
            acquire_product_write_gate=acquire_product_write_gate,
            workspace_dir=_workspace_dir,
            monitoring_action=MonitoringAction,
            fact_materializer=admission_fact_materializer,
        ),
    )

    @router.api_route(
        "/{r7_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    async def unmatched_r7_route(r7_path: str) -> JSONResponse:
        del r7_path
        return _error_response(404, "route_not_found", _AUTH_MESSAGES["route_not_found"])

    return router


__all__ = [
    "ProductBackupRequest",
    "ProductContinuityChangeCounts",
    "ProductContinuityComparison",
    "ProductContinuityIdentity",
    "ProductContinuityResponse",
    "ProductContinuityRow",
    "ProductProjectUpgradeRequest",
    "ProjectOpenResult",
    "ProjectUpgradeProgress",
    "ProjectUpgradeResult",
    "ProductCreateRunRequest",
    "ProductExecutionActionRequest",
    "ProductRestorePreflightRequest",
    "ProductRestoreRequest",
    "ProductPublicationError",
    "ProductPublicationRequest",
    "ProductRiskRulePreviewRequest",
    "ProductRiskRuleRequest",
    "R7_PRODUCT_PREFIX",
    "R7_PRODUCT_SCHEMA",
    "R7_RISK_RULE_DB_NAME",
    "R7_WORKSPACE_ROOT_NAME",
    "create_medical_monitoring_r7_product_router",
]
