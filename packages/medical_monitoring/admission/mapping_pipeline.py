"""C3 candidate-only orchestration over the existing monitoring AI service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..graph.store import Store
from ..runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .mapping_bridge import (
    MAPPING_BRIDGE_SCHEMA_VERSION,
    MappingBridgeError,
    admission_record_to_harness_input,
)
from .mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    monitoring_mapping_runtime_matches,
)
from .pipeline import ADMISSION_RECORD_KIND
from .staging import StagingIncompleteError, load_attempt


class AdmissionMappingPipelineError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


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
    ) -> None:
        self._service = ai_service
        self._repository = ai_repository
        self._revision_factory = input_revision_factory
        self._task_type = task_type
        self._worker_wake = worker_wake
        self._required_provider = required_provider
        self._required_model = required_model

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

    def _configured(self) -> bool:
        return all((
            self._service is not None,
            self._repository is not None,
            self._revision_factory is not None,
            self._task_type is not None,
        ))

    def generate_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        if not self._configured():
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        record = self._load_record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        if record.get("state") != "profile_ready":
            raise AdmissionMappingPipelineError("mapping_profile_not_ready")
        runtime = self._service.runtime_resolver()
        if not monitoring_mapping_runtime_matches(
            runtime,
            required_provider=self._required_provider,
            required_model=self._required_model,
        ):
            raise AdmissionMappingPipelineError("mapping_model_not_configured")
        try:
            harness_input = admission_record_to_harness_input(
                project_id=project_id, attempt_id=attempt_id, record=record
            )
            revision = self._revision_factory(harness_input.input_revision)
            jobs = self._service.submit_listing_field_mapping_chunks(
                project_id=project_id,
                input_revision=revision,
                field_profile=harness_input.field_profile,
                chunk_size=12,
            )
        except (MappingBridgeError, ValueError) as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        self._worker_wake()
        return self._project(jobs, attempt_id=attempt_id)

    def list_candidates(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        if not self._configured():
            raise AdmissionMappingPipelineError("mapping_bridge_unconfigured")
        self._load_record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        jobs = self._repository.list_jobs(
            project_id,
            task_type=str(_value(self._task_type)),
            business_key_prefix=f"listing-field-mapping:{attempt_id}:",
        )
        if not jobs:
            raise AdmissionMappingPipelineError("mapping_candidates_not_found")
        return self._project(jobs, attempt_id=attempt_id)

    def _project(self, jobs: Any, *, attempt_id: str) -> dict[str, Any]:
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
) -> Optional[str]:
    """Resolve a C3 admission job against the current accepted profile.

    ``None`` means the job does not belong to the admission bridge and the
    caller should use its legacy batch resolver. An empty string means the
    admission identity is stale or cannot be re-established.
    """

    try:
        payload = repository.input_payload(job.project_id, job.job_id)
        field_profile = payload.get("field_profile")
        if not isinstance(field_profile, Mapping):
            return None
        if field_profile.get("bridge_schema_version") != MAPPING_BRIDGE_SCHEMA_VERSION:
            return None
        attempt_id = str(field_profile.get("batch_id") or "").strip()
        if not attempt_id:
            return ""
        record = AdmissionMappingPipeline()._load_record(
            project_id=job.project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if record.get("state") != "profile_ready":
            return ""
        current = admission_record_to_harness_input(
            project_id=job.project_id,
            attempt_id=attempt_id,
            record=record,
        ).field_profile
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
    "current_admission_mapping_revision",
]
