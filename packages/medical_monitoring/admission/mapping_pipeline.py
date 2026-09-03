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
    admission_record_to_harness_input,
)
from .mapping_gate import (
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
    "monitoring-listing-field-mapping-adjudication-v2"
)
MAPPING_ADJUDICATION_BUSINESS_PREFIX = (
    "listing-field-mapping-adjudication"
)
_ADJUDICATION_GENERATION_RE = re.compile(r":g(\d{2}):")
_ADJUDICATION_MAX_GENERATIONS = 2


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

        return admission_record_to_harness_input(
            project_id=project_id,
            attempt_id=attempt_id,
            record=record,
            table_rows_by_snapshot=self._load_table_rows(
                record=record,
                workspace_dir=workspace_dir,
            ),
            relationship_profiler=self._required_relationship_profiler(),
        )

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
        if not self._cohort_runtime_ready(service, contract):
            raise AdmissionMappingPipelineError("mapping_model_not_configured")
        try:
            harness_input = self._frozen_harness_input(
                project_id=project_id,
                attempt_id=attempt_id,
                record=record,
                workspace_dir=workspace_dir,
            )
            revision = self._revision_factory(harness_input.input_revision)
            jobs = service.submit_listing_field_mapping_chunks(
                project_id=project_id,
                input_revision=revision,
                field_profile=harness_input.field_profile,
                chunk_size=12,
                prompt_version=contract.prompt_version,
                business_key_prefix=contract.business_key_prefix,
            )
        except (MappingBridgeError, ValueError) as exc:
            raise AdmissionMappingPipelineError("mapping_bridge_failed") from exc
        self._worker_wake()
        return self._project(jobs, attempt_id=attempt_id, cohort=contract.cohort)

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
    ) -> Mapping[str, Any]:
        """Run a focused, auditable second pass over unresolved fields only.

        Adjudication is a primary-cohort feature: it feeds first-pass draft
        decisions back to the primary model. The verifier cohort stays blind
        by construction and can never receive this pass.
        """

        if not self._configured():
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
        digest = hashlib.sha256(
            json.dumps(
                {"draft_id": draft_id, "fields": identity},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:20]
        query_prefix = (
            f"{MAPPING_ADJUDICATION_BUSINESS_PREFIX}:"
            f"{attempt_id}:{digest}:"
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
                "mappings": self._adjudication_mappings(jobs),
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
        runtime = self._service.runtime_resolver()
        if not monitoring_mapping_runtime_matches(
            runtime,
            required_provider=self._required_provider,
            required_model=self._required_model,
        ):
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
                "schema_version": "monitoring_mapping_adjudication_v1",
                "first_pass_mappings": [
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
                "decision_policy": (
                    "Only clear user decision when role and field kind remain "
                    "unchanged and the independent evidence is sufficient."
                ),
            }
            generation += 1
            jobs = self._service.submit_listing_field_mapping_chunks(
                project_id=project_id,
                input_revision=self._revision_factory(
                    harness_input.input_revision
                ),
                field_profile=profile,
                chunk_size=12,
                prompt_version=MAPPING_ADJUDICATION_PROMPT_VERSION,
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

    def _adjudication_mappings(self, jobs: Sequence[Any]) -> list[dict[str, Any]]:
        mappings = []
        for job in jobs:
            for candidate in self._repository.candidates(
                job.project_id,
                job.job_id,
            ):
                for item in candidate.structured_payload.get(
                    "field_mappings",
                    [],
                ):
                    mappings.append({
                        **dict(item),
                        "candidate_id": candidate.candidate_id,
                        "job_id": job.job_id,
                    })
        return mappings

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
        if field_profile.get("bridge_schema_version") != MAPPING_BRIDGE_SCHEMA_VERSION:
            return None
        attempt_id = str(field_profile.get("batch_id") or "").strip()
        if not attempt_id:
            return ""
        pipeline = AdmissionMappingPipeline(
            relationship_profiler=relationship_profiler,
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
        current = admission_record_to_harness_input(
            project_id=job.project_id,
            attempt_id=attempt_id,
            record=record,
            table_rows_by_snapshot=pipeline._load_table_rows(
                record=record,
                workspace_dir=workspace_dir,
            ),
            relationship_profiler=pipeline._resolve_relationship_profiler(),
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
    "MAPPING_ADJUDICATION_BUSINESS_PREFIX",
    "MAPPING_ADJUDICATION_PROMPT_VERSION",
    "current_admission_mapping_revision",
]
