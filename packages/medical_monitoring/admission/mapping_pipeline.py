"""C3 candidate-only orchestration over the existing monitoring AI service."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Optional, Sequence

from ..domain.execution import StoreError
from ..graph.store import Store
from ..runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .mapping_bridge import (
    MAPPING_BRIDGE_SCHEMA_VERSION,
    MappingBridgeError,
    MappingHarnessInput,
    admission_record_to_harness_input,
)
from .document_evidence import DOCUMENT_ROLES, MAPPING_REQUIRED_DOCUMENT_ROLES
from .mapping_gate import (
    MONITORING_C3_LOCAL_FALLBACK_MODEL,
    MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
    MONITORING_MAPPING_COHORT_PRIMARY,
    MONITORING_MAPPING_COHORT_VERIFIER,
    MonitoringMappingCohortContract,
    monitoring_mapping_cohort_contract,
    monitoring_mapping_runtime_matches,
)
from .pipeline import ADMISSION_RECORD_KIND
from .staging import StagingIncompleteError, load_attempt


class AdmissionMappingPipelineError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


MAPPING_ADJUDICATION_PROMPT_VERSION = (
    "monitoring-listing-field-mapping-adjudication-v3"
)
MAPPING_ADJUDICATION_VERIFIER_PROMPT_VERSION = (
    "monitoring-listing-field-mapping-adjudication-verifier-v1"
)
MAPPING_ADJUDICATION_BUSINESS_PREFIX = (
    "listing-field-mapping-adjudication"
)
_ADJUDICATION_GENERATION_RE = re.compile(r":g(\d{2}):")
_ADJUDICATION_MAX_GENERATIONS = 2
_REMOTE_UNAVAILABLE_FAILURES = frozenset({
    "ai_not_configured",
    "ai_transport_rejected",
    "ai_configuration_error",
    "provider_runtime_error",
})
DOCUMENT_SELECTION_KIND = "monitoring_document_selection"
_DOCUMENT_ROLE_LABELS = {
    "protocol": "研究方案",
    "investigator_brochure": "研究者手册",
    "ecrf": "电子病例报告表",
    "sap": "统计分析计划",
}


def _anonymous_review_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Remove model identity while preserving the two evidence-bound options."""

    projected = []
    for row in rows:
        options = []
        for key in ("primary", "verifier"):
            raw = row.get(key)
            if not isinstance(raw, Mapping):
                continue
            option = {
                name: value
                for name, value in raw.items()
                if name not in {"candidate_id", "job_id"}
            }
            options.append(option)
        options.sort(
            key=lambda value: json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        projected.append({
            "domain": str(row.get("domain") or ""),
            "source_field": str(row.get("source_field") or ""),
            "candidate_options": options,
        })
    return sorted(
        projected,
        key=lambda row: (row["domain"], row["source_field"]),
    )


def _store(workspace_dir: Path) -> Store:
    runtime = Path(workspace_dir) / RUNTIME_DIR_NAME
    runtime.mkdir(parents=True, exist_ok=True)
    return Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _evidence_summary(candidate: Any, evidence_ids: list[str]) -> list[dict[str, Any]]:
    selected = set(evidence_ids)
    rows = []
    for evidence in getattr(candidate, "evidence", ()):
        if str(getattr(evidence, "evidence_id", "")) not in selected:
            continue
        raw = getattr(evidence, "raw_fields", {})
        if not isinstance(raw, Mapping):
            continue
        samples = list(raw.get("representative_values") or [])
        rows.append({
            "inferred_type": str(raw.get("inferred_type") or ""),
            "total_rows": int(raw.get("total_rows") or 0),
            "non_empty_count": int(raw.get("non_empty_count") or 0),
            "sample_count": min(len(samples), 3),
            "samples_hidden": True,
        })
    return rows


def _latest_job_cohort(jobs: Sequence[Any]) -> tuple[Any, ...]:
    """Keep only the newest submission contract for an admission attempt."""

    if not jobs:
        return ()
    latest = max(jobs, key=lambda item: (item.created_at, item.job_id))
    identity = (str(latest.prompt_version), str(latest.input_revision_sha256))
    return tuple(
        job
        for job in jobs
        if (
            str(job.prompt_version),
            str(job.input_revision_sha256),
        )
        == identity
    )


class AdmissionMappingPipeline:
    """Submit admitted profiles to the established candidate repository.

    Dependencies are injected to keep ``packages`` independent of the FastAPI
    service layer. No method accepts, confirms, or materializes a mapping.
    """

    def __init__(
        self,
        *,
        ai_service: Any = None,
        ai_repository: Any = None,
        input_revision_factory: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        task_type: Any = None,
        worker_wake: Callable[[], Any] = lambda: None,
        required_provider: str = MONITORING_C3_MAPPING_PROVIDER,
        required_model: str = MONITORING_C3_MAPPING_MODEL,
        verifier_ai_service: Any = None,
        verifier_required_provider: str = MONITORING_C3_VERIFIER_PROVIDER,
        verifier_required_model: str = MONITORING_C3_VERIFIER_MODEL,
        relationship_profiler: Optional[Callable[..., Any]] = None,
        require_document_evidence: bool = False,
        document_evidence_resolver: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._service = ai_service
        self._repository = ai_repository
        self._revision_factory = input_revision_factory
        self._task_type = task_type
        self._worker_wake = worker_wake
        self._required_provider = required_provider
        self._required_model = required_model
        self._verifier_service = verifier_ai_service
        self._verifier_required_provider = verifier_required_provider
        self._verifier_required_model = verifier_required_model
        self._relationship_profiler_override = relationship_profiler
        self._require_document_evidence = bool(require_document_evidence)
        self._document_evidence_resolver = document_evidence_resolver

    def _resolve_relationship_profiler(self) -> Optional[Callable[..., Any]]:
        """Return the deterministic relationship profiler for submissions.

        The injected override wins; otherwise the default profiler module is
        resolved lazily so a fresh context can light the bridge up without
        production wiring. ``None`` means no profiler is available and every
        submission path must refuse to run (fail-closed, no silent empty
        relationship evidence).
        """

        if self._relationship_profiler_override is not None:
            return self._relationship_profiler_override
        try:
            from .relationship_profiler import build_relationship_profile
        except ImportError:
            return None
        return build_relationship_profile

    def _required_relationship_profiler(self) -> Callable[..., Any]:
        profiler = self._resolve_relationship_profiler()
        if profiler is None:
            raise AdmissionMappingPipelineError(
                "mapping_relationship_profiler_unavailable"
            )
        return profiler

    def _ready_record(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
    ) -> dict[str, Any]:
        record = self._load_record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        if record.get("state") != "profile_ready":
            raise AdmissionMappingPipelineError("mapping_profile_not_ready")
        return record

    def _frozen_harness_input(
        self,
        *,
        project_id: str,
        attempt_id: str,
        record: Mapping[str, Any],
        workspace_dir: Path,
    ) -> Any:
        """Build the evidence-bound harness input for one admitted record.

        Both mapping cohorts and the revision resolver must build their input
        through this path so the frozen relationship evidence stays
        byte-identical across cohorts and rechecks. A missing profiler or a
        missing/malformed relationship payload refuses the input (fail-closed);
        no submission ever runs on silently empty relationship evidence.
        """

        frozen_record = dict(record)
        if self._document_evidence_resolver is not None:
            attempt = load_attempt(
                Path(workspace_dir) / "admissions",
                attempt_id,
                verify_files=False,
            )
            technical = dict(record.get("technical_details") or {})
            selections = self._document_selection_ids(
                workspace_dir,
                attempt_id,
            )
            resolved = self._document_evidence_resolver(
                project_id=project_id,
                listing_admission_date=str(attempt.created_at)[:10],
                selected_entry_ids=selections,
            )
            for item in resolved.roles:
                if (
                    item.status == "current"
                    and item.binding is not None
                    and item.role not in selections
                ):
                    self._write_document_selection(
                        project_id=project_id,
                        attempt_id=attempt_id,
                        workspace_dir=workspace_dir,
                        role=item.role,
                        source_entry_id=item.binding.source_entry_id,
                    )
            technical["monitoring_document_evidence"] = (
                resolved.to_dict()
                if hasattr(resolved, "to_dict")
                else dict(resolved)
            )
            frozen_record["technical_details"] = technical
        elif self._require_document_evidence:
            raise AdmissionMappingPipelineError(
                "mapping_document_evidence_resolver_unavailable"
            )
        return admission_record_to_harness_input(
            project_id=project_id,
            attempt_id=attempt_id,
            record=frozen_record,
            table_rows_by_snapshot=self._load_table_rows(
                record=record,
                workspace_dir=workspace_dir,
            ),
            relationship_profiler=self._required_relationship_profiler(),
            require_document_evidence=self._require_document_evidence,
        )

    @staticmethod
    def _document_selection_ids(
        workspace_dir: Path,
        attempt_id: str,
    ) -> dict[str, str]:
        store = _store(workspace_dir)
        try:
            selected = {}
            for role in DOCUMENT_ROLES:
                row = store.get_domain_object(
                    DOCUMENT_SELECTION_KIND,
                    f"{attempt_id}::{role}",
                )
                if row is None or not isinstance(row[1], Mapping):
                    continue
                payload = row[1]
                if (
                    payload.get("attempt_id") != attempt_id
                    or payload.get("role") != role
                ):
                    continue
                entry_id = str(payload.get("source_entry_id") or "").strip()
                if entry_id:
                    selected[role] = entry_id
            return selected
        finally:
            store.close()

    def select_document(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
        role: str,
        source_entry_id: str,
    ) -> Mapping[str, Any]:
        """Version one explicit role selection; resolver revalidates its source."""

        role = str(role or "").strip()
        source_entry_id = str(source_entry_id or "").strip()
        if role not in DOCUMENT_ROLES or not source_entry_id:
            raise AdmissionMappingPipelineError(
                "mapping_document_selection_invalid"
            )
        self._ready_record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if self._document_evidence_resolver is None:
            raise AdmissionMappingPipelineError(
                "mapping_document_evidence_resolver_unavailable"
            )
        attempt = load_attempt(
            Path(workspace_dir) / "admissions",
            attempt_id,
            verify_files=False,
        )
        selections = self._document_selection_ids(workspace_dir, attempt_id)
        selections[role] = source_entry_id
        packet = self._document_evidence_resolver(
            project_id=project_id,
            listing_admission_date=str(attempt.created_at)[:10],
            selected_entry_ids=selections,
        )
        selected_role = next(
            (item for item in packet.roles if item.role == role),
            None,
        )
        if selected_role is None or (
            selected_role.status == "incomplete"
            and f"{role}_selection_stale"
            in selected_role.limitation_codes
        ):
            raise AdmissionMappingPipelineError(
                "mapping_document_selection_not_found_or_role_mismatch"
            )
        if (
            selected_role.status != "current"
            or selected_role.binding is None
            or selected_role.binding.source_entry_id != source_entry_id
        ):
            raise AdmissionMappingPipelineError(
                "mapping_document_selection_unusable"
            )
        version = self._write_document_selection(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
            role=role,
            source_entry_id=source_entry_id,
        )
        return {
            "role": role,
            "source_entry_id": source_entry_id,
            "version": version,
        }

    @staticmethod
    def _write_document_selection(
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
        role: str,
        source_entry_id: str,
    ) -> int:
        store = _store(workspace_dir)
        try:
            version = store.put_domain_object(
                DOCUMENT_SELECTION_KIND,
                f"{attempt_id}::{role}",
                {
                    "schema_version": "mm-c3-document-selection-v2",
                    "project_id": project_id,
                    "attempt_id": attempt_id,
                    "role": role,
                    "source_entry_id": source_entry_id,
                },
            )
        finally:
            store.close()
        return version

    def document_readiness(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
    ) -> Mapping[str, Any]:
        """Project document readiness without registry or model internals."""

        self._ready_record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if self._document_evidence_resolver is None:
            raise AdmissionMappingPipelineError(
                "mapping_document_evidence_resolver_unavailable"
            )
        attempt = load_attempt(
            Path(workspace_dir) / "admissions",
            attempt_id,
            verify_files=False,
        )
        packet = self._document_evidence_resolver(
            project_id=project_id,
            listing_admission_date=str(attempt.created_at)[:10],
            selected_entry_ids=self._document_selection_ids(
                workspace_dir,
                attempt_id,
            ),
        )
        status_text = {
            "current": "已识别",
            "missing": "尚未添加",
            "ambiguous": "系统正在核对版本",
            "incomplete": "需要重新识别",
        }
        roles = [
            {
                "role": item.role,
                "label": _DOCUMENT_ROLE_LABELS[item.role],
                "required_now": item.role in MAPPING_REQUIRED_DOCUMENT_ROLES,
                "status": item.status,
                "status_text": status_text[item.status],
            }
            for item in packet.roles
        ]
        ready = bool(packet.mapping_context_ready)
        return {
            "ready": ready,
            "headline": (
                "研究方案和电子病例报告表已准备好"
                if ready
                else "还需补充研究方案或电子病例报告表"
            ),
            "guidance": (
                "系统会自动完成字段理解和两次独立核对，无需逐项确认。"
                if ready
                else "添加文件后，系统会自动识别，不需要您填写技术信息。"
            ),
            "roles": roles,
        }

    def _cohort_contract(self, cohort: str) -> MonitoringMappingCohortContract:
        try:
            return monitoring_mapping_cohort_contract(cohort)
        except ValueError as exc:
            raise AdmissionMappingPipelineError("mapping_cohort_invalid") from exc

    def _cohort_service(self, cohort: str) -> Any:
        if cohort == MONITORING_MAPPING_COHORT_VERIFIER:
            if self._verifier_service is None:
                raise AdmissionMappingPipelineError("mapping_verifier_unconfigured")
            return self._verifier_service
        return self._service

    def _cohort_runtime_ready(
        self,
        service: Any,
        contract: MonitoringMappingCohortContract,
    ) -> bool:
        runtime = service.runtime_resolver()
        if contract.cohort == MONITORING_MAPPING_COHORT_PRIMARY:
            return monitoring_mapping_runtime_matches(
                runtime,
                required_provider=self._required_provider,
                required_model=self._required_model,
            )
        return monitoring_mapping_runtime_matches(
            runtime,
            required_provider=self._verifier_required_provider,
            required_model=self._verifier_required_model,
        )

    @staticmethod
    def _runtime_identity(runtime: Any) -> tuple[str, str]:
        provider = str(getattr(runtime, "provider", "") or "").strip()
        model = str(getattr(runtime, "model", "") or "").strip().casefold()
        return provider, model

    def _remote_unavailability_receipt(
        self,
        *,
        project_id: str,
        attempt_id: str,
        profile_sha256: str,
    ) -> dict[str, Any]:
        """Derive a bounded receipt from immutable job-attempt evidence."""

        routes = (
            (
                "primary",
                MONITORING_C3_MAPPING_PROVIDER,
                MONITORING_C3_MAPPING_MODEL,
                f"listing-field-mapping:{attempt_id}:",
            ),
            (
                "verifier",
                MONITORING_C3_VERIFIER_PROVIDER,
                MONITORING_C3_VERIFIER_MODEL,
                f"listing-field-mapping-verifier:{attempt_id}:",
            ),
        )
        evidence = []
        for cohort, provider, model, prefix in routes:
            candidates = []
            for job in self._repository.list_jobs(
                project_id,
                task_type=str(_value(self._task_type)),
                business_key_prefix=prefix,
            ):
                if (
                    str(job.provider) != provider
                    or str(job.requested_model).casefold() != model.casefold()
                    or str(_value(job.status)) != "failed"
                    or job.contract_retirement_code
                    or job.failure_code not in _REMOTE_UNAVAILABLE_FAILURES
                ):
                    continue
                payload = self._repository.input_payload(project_id, job.job_id)
                profile = payload.get("field_profile") or {}
                if profile.get("full_profile_sha256") != profile_sha256:
                    continue
                attempts = self._repository.attempts(project_id, job.job_id)
                if not attempts or attempts[-1]["failure_code"] != job.failure_code:
                    continue
                if job.failure_code == "provider_runtime_error" and (
                    job.attempt_count < job.max_attempts or not job.retryable
                ):
                    continue
                if job.failure_code != "provider_runtime_error" and job.retryable:
                    continue
                candidates.append((job, attempts))
            if not candidates:
                raise AdmissionMappingPipelineError(
                    "mapping_fallback_terminal_evidence_missing"
                )
            job, attempts = max(
                candidates, key=lambda item: (item[0].updated_at, item[0].job_id)
            )
            evidence.append({
                "cohort": cohort,
                "provider": provider,
                "model": model,
                "job_id": job.job_id,
                "input_revision_sha256": job.input_revision_sha256,
                "prompt_version": job.prompt_version,
                "failure_code": job.failure_code,
                "attempt_count": job.attempt_count,
                "attempt_receipts": [
                    {
                        "attempt_id": item["attempt_id"],
                        "attempt_number": item["attempt_number"],
                        "outcome": item["outcome"],
                        "failure_code": item["failure_code"],
                        "request_sha256": item["request_sha256"],
                        "response_sha256": item["response_sha256"],
                    }
                    for item in attempts
                ],
            })
        receipt = {
            "schema_version": "mm-c3-remote-unavailability-receipt-v1",
            "project_id": project_id,
            "attempt_id": attempt_id,
            "profile_sha256": profile_sha256,
            "routes": evidence,
        }
        receipt["receipt_sha256"] = hashlib.sha256(
            json.dumps(
                receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        return receipt

    def _admit_local_fallback(
        self,
        harness_input: MappingHarnessInput,
        *,
        project_id: str,
        attempt_id: str,
    ) -> MappingHarnessInput:
        receipt = self._remote_unavailability_receipt(
            project_id=project_id,
            attempt_id=attempt_id,
            profile_sha256=harness_input.field_profile["profile_sha256"],
        )
        return self._apply_local_fallback_receipt(harness_input, receipt)

    def _apply_local_fallback_receipt(
        self,
        harness_input: MappingHarnessInput,
        receipt: Mapping[str, Any],
    ) -> MappingHarnessInput:
        unsigned = {
            key: value for key, value in receipt.items()
            if key != "receipt_sha256"
        }
        digest = hashlib.sha256(
            json.dumps(
                unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if (
            receipt.get("schema_version")
            != "mm-c3-remote-unavailability-receipt-v1"
            or receipt.get("profile_sha256")
            != harness_input.field_profile["profile_sha256"]
            or receipt.get("receipt_sha256") != digest
            or len(receipt.get("routes") or ()) != 2
        ):
            raise AdmissionMappingPipelineError(
                "mapping_fallback_terminal_evidence_invalid"
            )
        for route in receipt["routes"]:
            job = self._repository.get(receipt["project_id"], route["job_id"])
            attempts = self._repository.attempts(
                receipt["project_id"], route["job_id"]
            )
            projected_attempts = [
                {
                    "attempt_id": item["attempt_id"],
                    "attempt_number": item["attempt_number"],
                    "outcome": item["outcome"],
                    "failure_code": item["failure_code"],
                    "request_sha256": item["request_sha256"],
                    "response_sha256": item["response_sha256"],
                }
                for item in attempts
            ]
            if (
                str(job.provider) != route["provider"]
                or str(job.requested_model) != route["model"]
                or job.input_revision_sha256 != route["input_revision_sha256"]
                or job.prompt_version != route["prompt_version"]
                or projected_attempts != route["attempt_receipts"]
                or not attempts
                or attempts[-1]["failure_code"] != route["failure_code"]
            ):
                raise AdmissionMappingPipelineError(
                    "mapping_fallback_terminal_evidence_invalid"
                )
        profile = deepcopy(harness_input.field_profile)
        profile["fallback_admission"] = receipt
        profile["input_sha256"] = hashlib.sha256(
            json.dumps(
                {
                    "base_input_sha256": profile["input_sha256"],
                    "fallback_admission": receipt,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        profile["profile_sha256"] = hashlib.sha256(
            json.dumps(
                {key: value for key, value in profile.items() if key != "profile_sha256"},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return MappingHarnessInput(
            field_profile=profile,
            input_revision=harness_input.input_revision,
        )

    def _load_record(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> dict[str, Any]:
        try:
            load_attempt(Path(workspace_dir) / "admissions", attempt_id)
        except StagingIncompleteError as exc:
            raise AdmissionMappingPipelineError("mapping_admission_not_found") from exc
        store = _store(workspace_dir)
        try:
            persisted = store.get_domain_object(ADMISSION_RECORD_KIND, attempt_id)
        finally:
            store.close()
        if persisted is None or not isinstance(persisted[1], dict):
            raise AdmissionMappingPipelineError("mapping_admission_not_found")
        record = dict(persisted[1])
        if record.get("project_id") != project_id or record.get("attempt_id") != attempt_id:
            raise AdmissionMappingPipelineError("mapping_admission_not_found")
        return record

    def _load_table_rows(
        self, *, record: Mapping[str, Any], workspace_dir: Path
    ) -> dict[str, Mapping[str, Sequence[Mapping[str, Any]]]]:
        technical = record.get("technical_details") or {}
        snapshot_ids = technical.get("snapshot_ids") or []
        if not isinstance(snapshot_ids, list):
            raise AdmissionMappingPipelineError("mapping_bridge_failed")
        store = _store(workspace_dir)
        try:
            return {
                str(snapshot_id): store.load_listing_content(str(snapshot_id))
                for snapshot_id in snapshot_ids
            }
        except (OSError, StoreError, ValueError) as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        finally:
            store.close()

    def _configured(self, service: Any = None) -> bool:
        return all((
            (self._service if service is None else service) is not None,
            self._repository is not None,
            self._revision_factory is not None,
            self._task_type is not None,
        ))

    def generate_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
        cohort: str = MONITORING_MAPPING_COHORT_PRIMARY,
    ) -> Mapping[str, Any]:
        """Submit blind candidate jobs for one mapping cohort.

        Both cohorts receive the identical deterministic field profile built
        from the admitted record — the verifier input never carries primary
        analysis results, adjudication context, or draft decisions. The
        frozen relationship evidence is part of that shared input and is
        content-bound into the input revision, so both cohorts always map
        the exact same rows and pair statistics.
        """

        contract = self._cohort_contract(cohort)
        service = self._cohort_service(contract.cohort)
        if not self._configured(service):
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        record = self._ready_record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        try:
            harness_input = self._frozen_harness_input(
                project_id=project_id,
                attempt_id=attempt_id,
                record=record,
                workspace_dir=workspace_dir,
            )
            harness_input = self._admit_runtime(
                service,
                contract,
                harness_input,
                project_id=project_id,
                attempt_id=attempt_id,
                allow_local_fallback=True,
            )
            jobs = self._submit_harness(
                service,
                contract,
                harness_input,
                project_id=project_id,
            )
        except MappingBridgeError as exc:
            code = str(getattr(exc, "code", ""))
            raise AdmissionMappingPipelineError(
                code
                if code.startswith(("mapping_document_", "document_packet_"))
                else "mapping_bridge_failed"
            ) from exc
        except ValueError as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        self._worker_wake()
        return self._project(jobs, attempt_id=attempt_id, cohort=contract.cohort)

    def generate_dual_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
    ) -> Mapping[str, Any]:
        """Freeze once, preflight both routes, then enqueue both blind cohorts."""

        contracts = tuple(
            self._cohort_contract(cohort)
            for cohort in (
                MONITORING_MAPPING_COHORT_PRIMARY,
                MONITORING_MAPPING_COHORT_VERIFIER,
            )
        )
        services = tuple(
            self._cohort_service(contract.cohort)
            for contract in contracts
        )
        if any(not self._configured(service) for service in services):
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        record = self._ready_record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        try:
            harness_input = self._frozen_harness_input(
                project_id=project_id,
                attempt_id=attempt_id,
                record=record,
                workspace_dir=workspace_dir,
            )
            for service, contract in zip(services, contracts):
                self._admit_runtime(
                    service,
                    contract,
                    harness_input,
                    project_id=project_id,
                    attempt_id=attempt_id,
                    allow_local_fallback=False,
                )
            submitted = tuple(
                self._submit_harness(
                    service,
                    contract,
                    harness_input,
                    project_id=project_id,
                )
                for service, contract in zip(services, contracts)
            )
        except MappingBridgeError as exc:
            code = str(getattr(exc, "code", ""))
            raise AdmissionMappingPipelineError(
                code
                if code.startswith(("mapping_document_", "document_packet_"))
                else "mapping_bridge_failed"
            ) from exc
        except ValueError as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        self._worker_wake()
        primary = self._project(
            submitted[0],
            attempt_id=attempt_id,
            cohort=contracts[0].cohort,
        )
        verifier = self._project(
            submitted[1],
            attempt_id=attempt_id,
            cohort=contracts[1].cohort,
        )
        return {
            **dict(primary),
            "verification": {
                "state": verifier.get("state"),
                "summary": verifier.get("summary"),
            },
        }

    def _admit_runtime(
        self,
        service: Any,
        contract: MonitoringMappingCohortContract,
        harness_input: MappingHarnessInput,
        *,
        project_id: str,
        attempt_id: str,
        allow_local_fallback: bool,
    ) -> MappingHarnessInput:
        runtime_identity = self._runtime_identity(service.runtime_resolver())
        expected_identity = (
            (self._required_provider, self._required_model.casefold())
            if contract.cohort == MONITORING_MAPPING_COHORT_PRIMARY
            else (
                self._verifier_required_provider,
                self._verifier_required_model.casefold(),
            )
        )
        local_identity = (
            MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
            MONITORING_C3_LOCAL_FALLBACK_MODEL.casefold(),
        )
        if (
            allow_local_fallback
            and contract.cohort == MONITORING_MAPPING_COHORT_PRIMARY
            and runtime_identity == local_identity
        ):
            return self._admit_local_fallback(
                harness_input,
                project_id=project_id,
                attempt_id=attempt_id,
            )
        alternate_primary = (
            contract.cohort == MONITORING_MAPPING_COHORT_PRIMARY
            and runtime_identity == ("cms-router", "minimax-m3")
        )
        if runtime_identity != expected_identity and not alternate_primary:
            raise AdmissionMappingPipelineError("mapping_model_not_configured")
        return harness_input

    def _submit_harness(
        self,
        service: Any,
        contract: MonitoringMappingCohortContract,
        harness_input: MappingHarnessInput,
        *,
        project_id: str,
    ) -> tuple[Any, ...]:
        revision = self._revision_factory(harness_input.input_revision)
        return service.submit_listing_field_mapping_chunks(
            project_id=project_id,
            input_revision=revision,
            field_profile=harness_input.field_profile,
            chunk_size=12,
            prompt_version=contract.prompt_version,
            business_key_prefix=contract.business_key_prefix,
        )

    def list_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
        cohort: str = MONITORING_MAPPING_COHORT_PRIMARY,
    ) -> Mapping[str, Any]:
        contract = self._cohort_contract(cohort)
        if not self._configured(self._cohort_service(contract.cohort)):
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        self._load_record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        jobs = self._repository.list_jobs(
            project_id,
            task_type=str(_value(self._task_type)),
            business_key_prefix=contract.job_business_key_prefix(attempt_id),
        )
        if not jobs:
            raise AdmissionMappingPipelineError("mapping_candidates_not_found")
        return self._project(
            _latest_job_cohort(jobs),
            attempt_id=attempt_id,
            cohort=contract.cohort,
        )

    def adjudicate_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        draft_id: str,
        draft_fields: Sequence[Mapping[str, Any]],
        workspace_dir: Path,
        review_context: Optional[Mapping[str, Any]] = None,
        cohort: str = MONITORING_MAPPING_COHORT_PRIMARY,
    ) -> Mapping[str, Any]:
        """Run one cohort's anonymous, evidence-bound second review."""

        contract = self._cohort_contract(cohort)
        service = self._cohort_service(contract.cohort)
        if not self._configured(service):
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        fields = [dict(field) for field in draft_fields]
        if not fields:
            return {"state": "not_needed", "mappings": [], "job_count": 0}
        identity = [
            {
                "domain": str(field.get("domain") or "").strip(),
                "source_field": str(field.get("source_field") or "").strip(),
                "recommended_role": str(
                    field.get("recommended_role") or ""
                ).strip(),
                "field_kind": str(_value(field.get("field_kind") or "")).strip(),
            }
            for field in fields
        ]
        if any(not row["domain"] or not row["source_field"] for row in identity):
            raise AdmissionMappingPipelineError("mapping_bridge_failed")
        identity.sort(key=lambda row: (row["domain"], row["source_field"]))
        dual_rows = []
        if review_context is not None:
            raw_rows = review_context.get("divergences") or []
            if not isinstance(raw_rows, list):
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            dual_rows = _anonymous_review_rows(raw_rows)
        digest = hashlib.sha256(
            json.dumps(
                {
                    "draft_id": draft_id,
                    "fields": identity,
                    "dual_review": dual_rows,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:20]
        query_prefix = (
            f"{MAPPING_ADJUDICATION_BUSINESS_PREFIX}:"
            f"{contract.cohort}:{attempt_id}:{digest}:"
        )
        existing = self._repository.list_jobs(
            project_id,
            task_type=str(_value(self._task_type)),
            business_key_prefix=query_prefix,
        )
        generation = max(
            (
                int(match.group(1))
                for job in existing
                if (match := _ADJUDICATION_GENERATION_RE.search(job.business_key))
            ),
            default=0,
        )
        jobs = tuple(
            job
            for job in existing
            if f":g{generation:02d}:" in str(job.business_key)
        )
        states = [str(_value(job.status)) for job in jobs]
        if states and all(state == "completed" for state in states):
            return {
                "state": "ready",
                "generation": generation,
                "job_count": len(jobs),
                **self._adjudication_payload(jobs),
            }
        if states and not any(
            state in {"failed", "blocked", "stale_input", "cancelled"}
            for state in states
        ):
            return {
                "state": "running",
                "generation": generation,
                "job_count": len(jobs),
                "mappings": [],
            }
        if generation >= _ADJUDICATION_MAX_GENERATIONS:
            return {
                "state": "failed",
                "generation": generation,
                "job_count": len(jobs),
                "mappings": [],
            }

        record = self._ready_record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if not self._cohort_runtime_ready(service, contract):
            raise AdmissionMappingPipelineError("mapping_model_not_configured")
        try:
            harness_input = self._frozen_harness_input(
                project_id=project_id,
                attempt_id=attempt_id,
                record=record,
                workspace_dir=workspace_dir,
            )
            profile = deepcopy(harness_input.field_profile)
            pair_set = {
                (row["domain"], row["source_field"])
                for row in identity
            }
            question_domains = {domain for domain, _ in pair_set}
            question_names = {name for _, name in pair_set}
            all_fields = list(profile["fields"])
            profile["fields"] = [
                field
                for field in all_fields
                if (
                    str(field.get("domain") or "").strip(),
                    str(field.get("field") or "").strip(),
                )
                in pair_set
            ]
            if len(profile["fields"]) != len(pair_set):
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            # The trimmed profile only carries the question fields, and the
            # harness relationship validator requires both sides of a pair to
            # exist in the submitted field set — so keep only fully covered
            # pairs; everything else stays in the full-profile evidence.
            profile["relationships"] = [
                relationship
                for relationship in profile.get("relationships", [])
                if (
                    str(relationship.get("domain") or "").strip(),
                    str(relationship.get("left_field") or "").strip(),
                )
                in pair_set
                and (
                    str(relationship.get("domain") or "").strip(),
                    str(relationship.get("right_field") or "").strip(),
                )
                in pair_set
            ]
            profile["cross_table_relationships"] = [
                entry
                for entry in profile.get("cross_table_relationships", [])
                if (
                    str(entry.get("left_domain") or "").strip(),
                    str(entry.get("left_field") or "").strip(),
                )
                in pair_set
                or (
                    str(entry.get("right_domain") or "").strip(),
                    str(entry.get("right_field") or "").strip(),
                )
                in pair_set
                or str(entry.get("left_domain") or "").strip() in question_domains
                or str(entry.get("right_domain") or "").strip() in question_domains
            ]
            profile["read_only_adjudication_context_profiles"] = [
                field
                for field in all_fields
                if (
                    (
                        str(field.get("domain") or "").strip()
                        in question_domains
                        or str(field.get("field") or "").strip()
                        in question_names
                    )
                    and (
                        str(field.get("domain") or "").strip(),
                        str(field.get("field") or "").strip(),
                    )
                    not in pair_set
                )
            ]
            profile["table_bindings"] = [
                binding
                for binding in profile.get("table_bindings", [])
                if str(binding.get("domain") or "").strip()
                in question_domains
            ]
            profile["treatment_identity_bindings"] = [
                binding
                for binding in profile.get(
                    "treatment_identity_bindings",
                    [],
                )
                if str(binding.get("target_domain") or "").strip()
                in question_domains
            ]
            profile["table_field_order"] = []
            profile["adjudication_contract"] = {
                "schema_version": (
                    "monitoring_mapping_dual_adjudication_v1"
                    if dual_rows
                    else "monitoring_mapping_adjudication_v1"
                ),
                "first_pass_mappings": [] if dual_rows else [
                    {
                        **row,
                        "uncertainty": str(field.get("uncertainty") or "")[:1000],
                        "user_question": str(field.get("user_action") or "")[:1000],
                    }
                    for row, field in zip(identity, sorted(
                        fields,
                        key=lambda item: (
                            str(item.get("domain") or ""),
                            str(item.get("source_field") or ""),
                        ),
                    ))
                ],
                "question_count": len(identity),
                "candidate_options_review": dual_rows,
                "decision_policy": (
                    "Resolve the anonymous candidate options from evidence. "
                    "Return the best-supported mapping, including a conservative "
                    "unmapped result when appropriate. Set user_decision_required "
                    "only when medically material ambiguity remains, and ask one "
                    "plain Chinese question without mentioning models."
                    if dual_rows
                    else "Only clear user decision when role and field kind "
                    "remain unchanged and the independent evidence is sufficient."
                ),
            }
            generation += 1
            jobs = service.submit_listing_field_mapping_chunks(
                project_id=project_id,
                input_revision=self._revision_factory(
                    harness_input.input_revision
                ),
                field_profile=profile,
                chunk_size=12,
                prompt_version=(
                    MAPPING_ADJUDICATION_VERIFIER_PROMPT_VERSION
                    if contract.cohort == MONITORING_MAPPING_COHORT_VERIFIER
                    else MAPPING_ADJUDICATION_PROMPT_VERSION
                ),
                business_key_prefix=(
                    f"{query_prefix}g{generation:02d}"
                ),
            )
        except (MappingBridgeError, ValueError) as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        self._worker_wake()
        return {
            "state": "running",
            "generation": generation,
            "job_count": len(jobs),
            "mappings": [],
        }

    def _adjudication_payload(self, jobs: Sequence[Any]) -> dict[str, Any]:
        mappings = []
        evidence_ids: set[str] = set()
        for job in jobs:
            for candidate in self._repository.candidates(
                job.project_id,
                job.job_id,
            ):
                evidence_ids.update(
                    str(item.evidence_id) for item in candidate.evidence
                )
                for item in candidate.structured_payload.get(
                    "field_mappings",
                    [],
                ):
                    mappings.append({
                        **dict(item),
                        "candidate_id": candidate.candidate_id,
                        "job_id": job.job_id,
                    })
        return {
            "mappings": mappings,
            "evidence_ids": sorted(evidence_ids),
        }

    def _project(
        self,
        jobs: Any,
        *,
        attempt_id: str,
        cohort: str = MONITORING_MAPPING_COHORT_PRIMARY,
    ) -> dict[str, Any]:
        job_rows = []
        mappings = []
        for job in jobs:
            status = str(_value(job.status))
            job_rows.append({
                "status": status,
                "provider": str(job.provider),
                "requested_model": str(job.requested_model),
                "response_model": str(job.response_model),
                "failure_code": str(job.failure_code),
            })
            if status != "completed":
                continue
            for candidate in self._repository.candidates(job.project_id, job.job_id):
                for item in candidate.structured_payload.get("field_mappings", []):
                    evidence_ids = list(item.get("evidence_ids") or [])
                    mappings.append({
                        "domain": item.get("domain"),
                        "source_field": item.get("source_field"),
                        "recommended_role": item.get("recommended_role"),
                        "field_kind": item.get("field_kind"),
                        "confidence": item.get("confidence"),
                        "uncertainty": item.get("uncertainty"),
                        "user_action": item.get("user_action"),
                        "user_decision_required": bool(
                            item.get("user_decision_required", False)
                        ),
                        "evidence_ids": evidence_ids,
                        "evidence_summary": _evidence_summary(
                            candidate,
                            evidence_ids,
                        ),
                        "confirmation_status": "pending_confirmation",
                    })
        states = [item["status"] for item in job_rows]
        state = (
            "candidates_ready"
            if states and all(value == "completed" for value in states)
            else "needs_attention"
            if any(
                value in {"failed", "blocked", "stale_input", "cancelled"}
                for value in states
            )
            else "generating"
        )
        return {
            "attempt_id": attempt_id,
            "cohort": cohort,
            "state": state,
            "confirmation_status": "pending_confirmation",
            "summary": {
                "job_count": len(job_rows),
                "completed_job_count": sum(value == "completed" for value in states),
                "candidate_count": len(mappings),
                "pending_confirmation_count": len(mappings),
            },
            "execution": {
                "providers": sorted({item["provider"] for item in job_rows}),
                "requested_models": sorted(
                    {item["requested_model"] for item in job_rows}
                ),
            },
            "jobs": job_rows,
            "candidates": mappings,
        }


def current_admission_mapping_revision(
    repository: Any,
    job: Any,
    *,
    workspace_dir: Path,
    relationship_profiler: Optional[Callable[..., Any]] = None,
    document_evidence_resolver: Optional[Callable[..., Any]] = None,
) -> Optional[str]:
    """Resolve a C3 admission job against the current accepted profile.

    ``None`` means the job does not belong to the admission bridge and the
    caller should use its legacy batch resolver. An empty string means the
    admission identity is stale or cannot be re-established. Callers that
    submit through a specific profiler must pass the same
    ``relationship_profiler`` so the recomputed digests cover the identical
    frozen evidence; without it the default profiler is resolved, and no
    evidence-bearing profile can pass while it is unavailable.
    """

    try:
        payload = repository.input_payload(job.project_id, job.job_id)
        field_profile = payload.get("field_profile")
        if not isinstance(field_profile, Mapping):
            return None
        if field_profile.get("bridge_schema_version") not in {
            "mm-c3-mapping-profile-bridge-v7",
            MAPPING_BRIDGE_SCHEMA_VERSION,
        }:
            return None
        attempt_id = str(field_profile.get("batch_id") or "").strip()
        if not attempt_id:
            return ""
        pipeline = AdmissionMappingPipeline(
            ai_repository=repository,
            task_type=job.task_type,
            relationship_profiler=relationship_profiler,
            document_evidence_resolver=document_evidence_resolver,
        )
        record = pipeline._load_record(
            project_id=job.project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if record.get("state") != "profile_ready":
            return ""
        # Recompute must mirror the submission path, including the frozen
        # relationship evidence. When the profiler is unavailable a v6
        # profile (which always carries evidence) cannot be reproduced and
        # the job falls back to the stale branch instead of passing.
        current_input = pipeline._frozen_harness_input(
            project_id=job.project_id,
            attempt_id=attempt_id,
            record=record,
            workspace_dir=workspace_dir,
        )
        if (
            str(job.provider) == MONITORING_C3_LOCAL_FALLBACK_PROVIDER
            and str(job.requested_model).casefold()
            == MONITORING_C3_LOCAL_FALLBACK_MODEL.casefold()
        ):
            stored_receipt = field_profile.get("fallback_admission")
            if not isinstance(stored_receipt, Mapping):
                return ""
            current_input = pipeline._apply_local_fallback_receipt(
                current_input, stored_receipt
            )
        current = current_input.field_profile
        expected = {
            "project_id": job.project_id,
            "batch_id": attempt_id,
            "full_profile_sha256": current["profile_sha256"],
            "full_input_sha256": current["input_sha256"],
            "source_bindings": current["source_bindings"],
            "source_sha256s": current["source_sha256s"],
        }
        if any(field_profile.get(key) != value for key, value in expected.items()):
            return ""
        return str(job.input_revision_sha256)
    except (AdmissionMappingPipelineError, MappingBridgeError, KeyError, ValueError):
        return ""


__all__ = [
    "AdmissionMappingPipeline",
    "AdmissionMappingPipelineError",
    "MAPPING_ADJUDICATION_BUSINESS_PREFIX",
    "MAPPING_ADJUDICATION_PROMPT_VERSION",
    "current_admission_mapping_revision",
]
