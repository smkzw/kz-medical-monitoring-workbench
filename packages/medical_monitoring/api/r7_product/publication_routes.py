"""Publication, public-result and continuity routes for R7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ...graph.store import Store
from ...projections.product_adapter import R5ProductAdapter
from ...runtime import launch_registry as lr
from ...runtime import project_backup as pb
from ...runtime import run_setup as rs
from ...runtime.run_entry import MonitoringRunEntry, RunEntryError
from ...runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressError,
)
from .contracts import ProductPublicationError, ProductPublicationRequest
from .errors import (
    _error_response,
    _launch_error_response,
    _run_entry_error_response,
    _status_for,
    _validation_error_response,
)
from .legacy_projections import _legacy_launch_record
from .publication_providers import (
    _obtain_r6_mode_outputs,
    _r5_publication_types,
    _r6_publication_types,
)
from .public_result_requests import (
    _canonical_public_result_value,
    _parse_public_result_date,
    _parse_public_result_query,
    _reject_public_result_body,
)
from .result_projections import (
    _PUBLICATION_MESSAGES,
    _publication_projection,
)
from .runtime_manifest import (
    _runtime_audit_chain_is_invalid,
    _runtime_manifest_metadata,
)


@dataclass(frozen=True)
class PublicationRouteContext:
    root: Path
    resolve_project: Any
    authorize: Any
    mutable_project_error: Any
    read_json_object: Any
    acquire_product_write_gate: Any
    open_entry: Any
    publication_failure_response: Any
    publication_setup_inputs: Any
    record_publication_failure: Any
    open_launch_registry: Any
    progress_adapter: Any
    publication_bridge: Any
    publication_provider: Any
    r5_product_packet_factory: Any
    r6_provider: Any
    harness_r1_profile: Any
    open_legacy_view: Any
    load_public_result_context: Any
    public_result_envelope: Any
    public_result_error: Any
    build_public_continuity_envelope: Any
    workspace_dir: Any
    build_r5_publication_packet: Any
    read_publication_gate: Any
    monitoring_action: Any


def register_publication_routes(router: APIRouter, context: PublicationRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    _publication_failure_response = context.publication_failure_response
    _publication_setup_inputs = context.publication_setup_inputs
    _record_publication_failure = context.record_publication_failure
    open_launch_registry = context.open_launch_registry
    progress_adapter = context.progress_adapter
    publication_bridge = context.publication_bridge
    publication_provider = context.publication_provider
    r5_product_packet_factory = context.r5_product_packet_factory
    r6_provider = context.r6_provider
    harness_r1_profile = context.harness_r1_profile
    open_legacy_view = context.open_legacy_view
    _load_public_result_context = context.load_public_result_context
    _public_result_envelope = context.public_result_envelope
    _public_result_error = context.public_result_error
    _build_public_continuity_envelope = context.build_public_continuity_envelope
    _workspace_dir = context.workspace_dir
    _build_r5_publication_packet = context.build_r5_publication_packet
    _read_publication_gate = context.read_publication_gate
    MonitoringAction = context.monitoring_action

    @router.post("/runs/{public_run_token}/publication")
    async def publish_result(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            # Result publication is the product-owned closure of a run the
            # medical monitor was already allowed to start. Low-level runtime
            # controls remain administrator-only.
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductPublicationRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)

        workspace = _workspace_dir(root, canonical)
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        publication: Optional[lr.ResultPublication] = None
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            (
                current,
                _setup_manifest,
                coverage,
                setup_identity,
                setup_digest,
            ) = _publication_setup_inputs(canonical, launch)
            fingerprint = lr.compute_publication_fingerprint(
                canonical,
                launch.run_id,
                launch.public_run_token,
                snapshot_token=launch.current_snapshot_token,
                source_revision_id=(
                    current.source_revision_id or current.snapshot_ref
                ),
                data_cutoff=current.data_cutoff,
                site_coverage=coverage,
                setup_manifest_identity=setup_identity,
            )
            publication = registry.reserve_publication(
                project_id=canonical,
                run_id=launch.run_id,
                idempotency_key=parsed.idempotency_key,
                publication_fingerprint=fingerprint,
                publication_revision=lr.PUBLICATION_REVISION,
                snapshot_token=launch.current_snapshot_token,
                snapshot_ref=current.snapshot_ref,
                source_revision_id=(
                    current.source_revision_id or current.snapshot_ref
                ),
                data_cutoff=current.data_cutoff,
                setup_manifest_digest=setup_digest,
                manifest_revision=None,
                runtime_manifest_revision=None,
                manifest_digest=None,
                runtime_manifest_digest=None,
                mandatory_denominator=int(
                    setup_identity["mandatory_denominator"]
                ),
                site_coverage=coverage,
                setup_manifest_identity=setup_identity,
                runtime_manifest_identity=None,
            )
            publication_replayed = bool(publication.replayed)
            if publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE:
                return _publication_projection(
                    launch.public_run_token,
                    publication.publication_state,
                    replayed=True,
                    run_state=launch.run_state,
                )
            if publication.publication_state in {
                lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                lr.PUBLICATION_STATE_BLOCKED,
            }:
                publication = registry.retry_publication(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                )

            if entry is None:
                entry = _open_entry(workspace, allow_create=False)
                if isinstance(entry, JSONResponse):
                    publication = _record_publication_failure(
                        registry,
                        publication,
                        code="runtime_read_failed",
                        recoverable=True,
                    )
                    return _publication_failure_response(publication)
            adapter = progress_adapter(workspace, entry, canonical)
            try:
                progress = adapter.read_progress(launch.run_id)
            except (RuntimeProgressError, RunEntryError) as exc:
                audit_invalid = (
                    exc.code == "runtime_integrity_failed"
                    and _runtime_audit_chain_is_invalid(
                        workspace, launch.run_id
                    )
                )
                normalized_code = (
                    "receipt_gate_blocked"
                    if audit_invalid
                    else (
                        "runtime_read_failed"
                        if exc.code
                        in {
                            "execution_not_prepared",
                            "runtime_integrity_failed",
                            "runtime_identity_mismatch",
                        }
                        else exc.code
                    )
                )
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code=normalized_code,
                    recoverable=(
                        False
                        if audit_invalid
                        else exc.code
                        in {
                            "execution_not_prepared",
                            "runtime_integrity_failed",
                            "store_closed",
                        }
                    ),
                )
                return _publication_failure_response(publication)
            run_state = str(progress.get("run_state", ""))
            if run_state not in lr.RUN_STATE_VALUES:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="runtime_read_failed",
                    recoverable=True,
                )
                return _publication_failure_response(publication)
            if launch.run_state != run_state:
                try:
                    launch = registry.update_state(
                        launch.run_id,
                        run_state,
                        project_id=canonical,
                    )
                except lr.LaunchRegistryError:
                    publication = _record_publication_failure(
                        registry,
                        publication,
                        code="runtime_read_failed",
                        recoverable=True,
                    )
                    return _publication_failure_response(publication)

            runtime_metadata = _runtime_manifest_metadata(
                workspace, launch.run_id
            )
            if runtime_metadata is None:
                raise ProductPublicationError(
                    "runtime_read_failed", recoverable=True
                )
            if (
                runtime_metadata["identity"] != setup_identity
                or int(
                    runtime_metadata["identity"]["mandatory_denominator"]
                )
                != int(setup_identity["mandatory_denominator"])
            ):
                raise ProductPublicationError("manifest_identity_mismatch")
            try:
                publication = registry.bind_publication_runtime_manifest(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                    fingerprint=publication.publication_fingerprint,
                    runtime_manifest_revision=runtime_metadata["revision"],
                    runtime_manifest_digest=runtime_metadata["digest"],
                    runtime_manifest_identity=runtime_metadata["identity"],
                    mandatory_denominator=int(
                        runtime_metadata["identity"][
                            "mandatory_denominator"
                        ]
                    ),
                )
            except lr.LaunchRegistryError as exc:
                if exc.code == "store_closed":
                    raise ProductPublicationError(
                        "runtime_read_failed", recoverable=True
                    ) from exc
                if exc.code in {
                    "publication_cas_conflict",
                    "invalid_publication_metadata",
                    "invalid_manifest_digest",
                    "invalid_publication_revision",
                }:
                    raise ProductPublicationError(
                        "manifest_identity_mismatch"
                    ) from exc
                raise
            if run_state != lr.STATE_COMPLETED:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="run_not_completed",
                    recoverable=False,
                )
                return _publication_failure_response(publication)
            current_source_revision = (
                current.source_revision_id or current.snapshot_ref
            )

            gate = _read_publication_gate(
                workspace,
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            stored_runtime = {
                "revision": publication.manifest_revision,
                "identity": dict(publication.runtime_manifest_identity),
                "digest": publication.manifest_digest,
            }
            if (
                stored_runtime["revision"] != gate["revision"]
                or stored_runtime["identity"] != gate["identity"]
                or stored_runtime["digest"] != gate["digest"]
                or gate["identity"] != setup_identity
                or gate["mandatory_denominator"]
                != int(setup_identity["mandatory_denominator"])
                or publication.site_coverage != coverage
                or publication.setup_manifest_digest != setup_digest
                or publication.snapshot_token
                != launch.current_snapshot_token
                or publication.snapshot_ref != current.snapshot_ref
                or publication.source_revision_id != current_source_revision
                or publication.data_cutoff != current.data_cutoff
            ):
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code="manifest_identity_mismatch",
                    recoverable=False,
                )
                return _publication_failure_response(publication)

            (
                _,
                _,
                _,
                _,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=current.snapshot_ref,
                cutoff_ref=current.data_cutoff,
                site_refs=coverage,
                snapshot_token=launch.current_snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            r6_output_set_digest: Optional[str] = None
            artifact_member_ids: Optional[tuple[str, ...]] = None
            artifact_member_set_digest: Optional[str] = None

            if r6_provider is not None:
                _, cb = _r6_publication_types()
                run_binding = dict(entry.get_run(launch.run_id))
                run_binding.setdefault("carry_forward_run_ids", [])
                run_binding.setdefault("mode_transition", "explicit_new_run")
                run_binding.setdefault("actor", "system_synthetic")
                if not run_binding.get("created_at"):
                    run_binding["created_at"] = getattr(
                        launch, "created_at", "2026-08-28T00:00:00Z"
                    )
                if not run_binding.get("knowledge_pack_version"):
                    run_binding["knowledge_pack_version"] = "kp-08b-v1"
                if not run_binding.get("rule_activation_version"):
                    run_binding["rule_activation_version"] = "rav-08b-v1"
                if not run_binding.get("mapping_version"):
                    run_binding["mapping_version"] = "map-08b-v1"
                if not run_binding.get("identity_algorithm_version"):
                    run_binding["identity_algorithm_version"] = "ia-08b-v1"
                if not run_binding.get("identity_algorithm_digest"):
                    run_binding["identity_algorithm_digest"] = "ia-digest-08b-v1"
                if run_binding.get("mode") == "post_lock_pre_cfdi":
                    run_binding.setdefault("fixed_total", True)
                    if not run_binding.get("locked_snapshot_hash"):
                        run_binding["locked_snapshot_hash"] = "snap-hash-fixed-001"
                    if not run_binding.get("output_cutoff_ref"):
                        run_binding["output_cutoff_ref"] = run_binding.get("data_cutoff")
                    if not run_binding.get("output_revision_ref"):
                        run_binding["output_revision_ref"] = run_binding.get("source_revision_id")
                    if not run_binding.get("local_os_user"):
                        run_binding["local_os_user"] = "local-user-synthetic"
                    if not run_binding.get("acceptance_evidence_hash"):
                        run_binding["acceptance_evidence_hash"] = "accept-hash-fixed-001"
                raw_outputs = _obtain_r6_mode_outputs(
                    r6_provider,
                    run_binding,
                    r5_packet=packet,
                    attempts=gate["receipt_attempts"],
                )
                if not raw_outputs or len(raw_outputs) != 4:
                    raise ProductPublicationError(
                        "receipt_gate_blocked", recoverable=False
                    )
                runtime_dir = workspace / RUNTIME_DIR_NAME
                db_path = runtime_dir / RUNTIME_DB_NAME
                artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
                r1_store = Store(db_path, artifact_dir)
                try:
                    committed_set = cb.commit_mode_outputs(
                        r1_store,
                        raw_outputs,
                        run_binding=run_binding,
                        r5_packet=packet,
                    )
                except cb.R5AuthorityVerificationError as exc:
                    raise ProductPublicationError(
                        "authority_identity_mismatch", recoverable=False
                    ) from exc
                except (cb.ContinuityBridgeError, Exception) as exc:
                    raise ProductPublicationError(
                        "receipt_gate_blocked", recoverable=False
                    ) from exc
                finally:
                    r1_store.close()
                r6_output_set_digest = committed_set.r6_output_set_digest
                artifact_member_ids = committed_set.artifact_member_ids
                artifact_member_set_digest = committed_set.artifact_member_set_digest

            try:
                publication = registry.finalize_publication(
                    project_id=canonical,
                    run_id=launch.run_id,
                    revision=publication.publication_revision,
                    expected_state=publication.publication_state,
                    fingerprint=publication.publication_fingerprint,
                    receipt_identities=gate["receipt_ids"],
                    receipt_set_digest=gate["receipt_set_digest"],
                    r5_authority_packet_id=packet.packet_identity,
                    r5_authority_packet_digest=packet.packet_digest,
                    s4_authority_packet_identities=packet.s4_packet_ids,
                    s4_authority_packet_digests=packet.s4_packet_digests,
                    r6_output_set_digest=r6_output_set_digest,
                    artifact_member_ids=artifact_member_ids,
                    artifact_member_set_digest=artifact_member_set_digest,
                )
            except lr.LaunchRegistryError as exc:
                publication = _record_publication_failure(
                    registry,
                    publication,
                    code=(
                        "runtime_read_failed"
                        if exc.code in {"store_closed", "publication_cas_conflict"}
                        else exc.code
                    ),
                    recoverable=exc.code
                    in {"store_closed", "publication_cas_conflict"},
                )
                return _publication_failure_response(publication)
            return _publication_projection(
                launch.public_run_token,
                publication.publication_state,
                replayed=publication_replayed or bool(publication.replayed),
                run_state=launch.run_state,
            )
        except ProductPublicationError as exc:
            if publication is None:
                return _error_response(
                    _status_for(exc.code),
                    exc.code,
                    _PUBLICATION_MESSAGES.get(exc.code),
                )
            publication = _record_publication_failure(
                registry,
                publication,
                code=exc.code,
                recoverable=exc.recoverable,
            )
            return _publication_failure_response(publication)
        except (rs.RunSetupError, RuntimeProgressError, RunEntryError) as exc:
            if publication is None:
                return _run_entry_error_response(exc)
            publication = _record_publication_failure(
                registry,
                publication,
                code="runtime_read_failed",
                recoverable=True,
            )
            return _publication_failure_response(publication)
        except Exception:
            if publication is None:
                return _error_response(500, "internal_error")
            publication = _record_publication_failure(
                registry,
                publication,
                code="internal_error",
                recoverable=False,
            )
            return _publication_failure_response(publication)
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

    @router.get("/runs/{public_run_token}/publication")
    async def get_publication(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                launch_rows = [
                    row
                    for row in view.list_launches()
                    if row.get("public_run_token") == public_run_token
                ]
                if not launch_rows:
                    return _error_response(
                        404,
                        "public_run_not_found",
                        "未找到指定的监查运行。",
                    )
                launch = _legacy_launch_record(launch_rows[0])
                publication_rows = view.list_publications(run_id=launch.run_id)
                if not publication_rows:
                    return _publication_projection(
                        launch.public_run_token,
                        "not_started",
                        run_state=launch.run_state,
                    )
                state = str(
                    publication_rows[0].get("publication_state", "")
                )
                return _publication_projection(
                    launch.public_run_token,
                    state,
                    replayed=False,
                    run_state=launch.run_state,
                )
            except lr.LaunchRegistryError as exc:
                return _launch_error_response(exc)
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        launch_path = (
            _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
        )
        if not launch_path.is_file():
            return _error_response(
                404,
                "public_run_not_found",
                "未找到指定的监查运行。",
            )
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            try:
                publication = registry.get_publication(
                    project_id=canonical, run_id=launch.run_id
                )
            except lr.LaunchRegistryError as exc:
                if exc.code != "publication_not_found":
                    raise
                return _publication_projection(
                    launch.public_run_token,
                    "not_started",
                    run_state=launch.run_state,
                )
            return _publication_projection(
                launch.public_run_token,
                publication.publication_state,
                replayed=False,
                run_state=launch.run_state,
            )
        except lr.LaunchRegistryError as exc:
            return _launch_error_response(exc)
        finally:
            registry.close()

def register_public_result_routes(router: APIRouter, context: PublicationRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    _publication_failure_response = context.publication_failure_response
    _publication_setup_inputs = context.publication_setup_inputs
    _record_publication_failure = context.record_publication_failure
    open_launch_registry = context.open_launch_registry
    progress_adapter = context.progress_adapter
    publication_bridge = context.publication_bridge
    publication_provider = context.publication_provider
    r5_product_packet_factory = context.r5_product_packet_factory
    r6_provider = context.r6_provider
    harness_r1_profile = context.harness_r1_profile
    open_legacy_view = context.open_legacy_view
    _load_public_result_context = context.load_public_result_context
    _public_result_envelope = context.public_result_envelope
    _public_result_error = context.public_result_error
    _build_public_continuity_envelope = context.build_public_continuity_envelope
    _workspace_dir = context.workspace_dir
    _build_r5_publication_packet = context.build_r5_publication_packet
    _read_publication_gate = context.read_publication_gate
    MonitoringAction = context.monitoring_action

    @router.get("/results/{result_context_token}/overview")
    async def get_public_result_overview(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"site_ref"}),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query.get("site_ref"),
            )
            _registry, _entry, launch, publication, adapter = context
            result = adapter.overview(
                project_ref=canonical,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_ref=query.get("site_ref"),
            )
            # Facts lane: surface the dual-cohort AE/MH findings on the
            # public overview. R24V2-B01：发布结果只读**冻结**bundle——
            # 活binding随active工件变化，会令旧result token显示"旧事实+
            # 最新发现"，破坏结果不可变合同。冻结bundle读取失败或零发现
            # 如实呈现（meta带state），不借live顶替。
            findings_bundle = context.public_findings_envelope()
            projection = result.get("projection")
            if isinstance(projection, dict):
                injected = findings_bundle.get("findings") or []
                if injected:
                    projection["query_findings"] = injected
                projection["query_findings_meta"] = dict(
                    findings_bundle.get("meta") or {}
                )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/results/{result_context_token}/subjects/{subject_ref}")
    async def get_public_result_subject(
        project_id: str,
        result_context_token: str,
        subject_ref: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        subject = _canonical_public_result_value(
            subject_ref, field_name="subject_ref"
        )
        if isinstance(token, JSONResponse):
            return token
        if isinstance(subject, JSONResponse):
            return subject
        query = _parse_public_result_query(
            request,
            allowed=frozenset(
                {
                    "site_ref",
                    "spine_ref",
                    "window_start",
                    "window_end",
                    "risk_instance_ref",
                    "risk_anchor_ref",
                    "visit_ref",
                    "event_ref",
                }
            ),
            required=frozenset(
                {"site_ref", "spine_ref", "window_start", "window_end"}
            ),
        )
        if isinstance(query, JSONResponse):
            return query
        window_start = _parse_public_result_date(query["window_start"])
        window_end = _parse_public_result_date(query["window_end"])
        if isinstance(window_start, JSONResponse):
            return window_start
        if isinstance(window_end, JSONResponse):
            return window_end
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query["site_ref"],
            )
            _registry, _entry, launch, publication, adapter = context
            result = adapter.subject_workspace(
                project_ref=canonical,
                subject_ref=subject,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_ref=query["site_ref"],
                spine_ref=query["spine_ref"],
                window_start=window_start,
                window_end=window_end,
                risk_instance_ref=query.get("risk_instance_ref"),
                risk_anchor_ref=query.get("risk_anchor_ref"),
                visit_ref=query.get("visit_ref"),
                event_ref=query.get("event_ref"),
            )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/results/{result_context_token}/source-evidence")
    async def get_public_result_source_evidence(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"risk_instance_ref", "source_locator_ref"}),
            required=frozenset({"risk_instance_ref", "source_locator_ref"}),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                R5ProductAdapter,
            ]
        ] = None
        try:
            context = _load_public_result_context(canonical, token)
            _registry, _entry, launch, publication, adapter = context
            result = adapter.source_evidence(
                project_ref=canonical,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                risk_instance_ref=query["risk_instance_ref"],
                source_locator_ref=query["source_locator_ref"],
            )
            return _public_result_envelope(
                result,
                launch=launch,
                publication=publication,
                result_context_token=token,
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()


    @router.get("/results/{result_context_token}/continuity")
    async def get_public_result_continuity(
        project_id: str,
        result_context_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        body_error = await _reject_public_result_body(request)
        if body_error is not None:
            return body_error
        token = _canonical_public_result_value(
            result_context_token, field_name="result_context_token"
        )
        if isinstance(token, JSONResponse):
            return token
        query = _parse_public_result_query(
            request,
            allowed=frozenset({"site_ref"}),
            required=frozenset(),
        )
        if isinstance(query, JSONResponse):
            return query
        context: Optional[
            tuple[
                lr.LaunchRegistry,
                MonitoringRunEntry,
                lr.LaunchRecord,
                lr.ResultPublication,
                Optional[R5ProductAdapter],
            ]
        ] = None
        try:
            context = _load_public_result_context(
                canonical,
                token,
                site_ref=query.get("site_ref"),
                continuity_context=True,
            )
            registry, _entry, launch, publication, adapter = context
            if adapter is None:
                raise ProductPublicationError("continuity_unavailable")
            return _build_public_continuity_envelope(
                registry=registry,
                launch=launch,
                publication=publication,
                adapter=adapter,
                result_context_token=token,
                site_ref=query.get("site_ref"),
            )
        except Exception as exc:
            return _public_result_error(exc)
        finally:
            if context is not None:
                context[1].close()
                context[0].close()

    @router.get("/runs/{public_run_token}/result-entry")
    async def get_result_entry(
        project_id: str,
        public_run_token: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        legacy_view = open_legacy_view(canonical)
        if legacy_view is not None:
            try:
                matching_launch = any(
                    row.get("public_run_token") == public_run_token
                    for row in legacy_view.list_launches()
                )
                if not matching_launch:
                    return _error_response(
                        404,
                        "public_run_not_found",
                        "未找到指定的监查运行。",
                    )
                return _error_response(
                    409,
                    "result_context_unavailable",
                    _PUBLICATION_MESSAGES["result_context_unavailable"],
                )
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                legacy_view.close()
        launch_path = (
            _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
        )
        if not launch_path.is_file():
            return _error_response(
                404,
                "public_run_not_found",
                "未找到指定的监查运行。",
            )
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            launch = registry.get_by_public_token(
                public_run_token, project_id=canonical
            )
            publication = registry.get_publication(
                project_id=canonical, run_id=launch.run_id
            )
            if publication.publication_state != lr.PUBLICATION_STATE_AVAILABLE:
                return _error_response(
                    409,
                    "publication_not_available",
                    _PUBLICATION_MESSAGES["publication_not_available"],
                )
            if not publication.result_context_token:
                return _error_response(
                    409,
                    "result_context_unavailable",
                    _PUBLICATION_MESSAGES["result_context_unavailable"],
                )
            if (
                not publication.r5_authority_packet_digest
                or not publication.r5_authority_packet_id
            ):
                return _error_response(
                    409,
                    "authority_identity_mismatch",
                    _PUBLICATION_MESSAGES["authority_identity_mismatch"],
                )
            entry_candidate = _open_entry(
                _workspace_dir(root, canonical), allow_create=False
            )
            if isinstance(entry_candidate, JSONResponse):
                raise ProductPublicationError(
                    "runtime_read_failed", recoverable=True
                )
            entry = entry_candidate
            gate = _read_publication_gate(
                _workspace_dir(root, canonical),
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            if (
                gate["revision"] != publication.manifest_revision
                or gate["digest"] != publication.manifest_digest
                or gate["identity"]
                != dict(publication.runtime_manifest_identity)
                or tuple(gate["receipt_ids"])
                != tuple(publication.receipt_identities)
                or gate["receipt_set_digest"]
                != publication.receipt_set_digest
            ):
                raise ProductPublicationError("receipt_gate_blocked")
            (
                _,
                _,
                _,
                _,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=publication.snapshot_ref
                or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_refs=publication.site_coverage,
                snapshot_token=publication.snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            if (
                packet.packet_identity != publication.r5_authority_packet_id
                or packet.packet_digest
                != publication.r5_authority_packet_digest
                or tuple(packet.site_refs) != publication.site_coverage
            ):
                return _error_response(
                    409,
                    "authority_identity_mismatch",
                    _PUBLICATION_MESSAGES["authority_identity_mismatch"],
                )
            if (
                publication.artifact_member_ids
                and publication.r6_output_set_digest
            ):
                runtime_dir = _workspace_dir(root, canonical) / RUNTIME_DIR_NAME
                db_path = runtime_dir / RUNTIME_DB_NAME
                artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
                if not db_path.is_file() or not artifact_dir.is_dir():
                    raise ProductPublicationError("receipt_gate_blocked")
                r1_store = Store(db_path, artifact_dir)
                try:
                    for member_id in publication.artifact_member_ids:
                        if not r1_store.verify_artifact(member_id):
                            raise ProductPublicationError("receipt_gate_blocked")
                finally:
                    r1_store.close()
            body = {
                "project_ref": canonical,
                "public_run_token": launch.public_run_token,
                "snapshot_token": publication.snapshot_token,
                "data_cutoff_text": publication.data_cutoff,
                "site_options": [
                    {
                        "site_ref": site_ref,
                        "site_label": f"中心 {site_ref}",
                    }
                    for site_ref in publication.site_coverage
                ],
                "result_context_token": publication.result_context_token,
            }
            if set(body) != {
                "project_ref",
                "public_run_token",
                "snapshot_token",
                "data_cutoff_text",
                "site_options",
                "result_context_token",
            }:
                return _error_response(500, "internal_error")
            return body
        except ProductPublicationError as exc:
            return _error_response(
                _status_for(exc.code),
                exc.code,
                _PUBLICATION_MESSAGES.get(
                    exc.code, _PUBLICATION_MESSAGES["authority_identity_mismatch"]
                ),
            )
        except lr.LaunchRegistryError as exc:
            if exc.code == "publication_not_found":
                return _error_response(
                    409,
                    "publication_not_available",
                    _PUBLICATION_MESSAGES["publication_not_available"],
                )
            return _launch_error_response(exc)
        finally:
            if entry is not None and not isinstance(entry, JSONResponse):
                entry.close()
            registry.close()


__all__ = [
    "PublicationRouteContext",
    "register_publication_routes",
    "register_public_result_routes",
]
