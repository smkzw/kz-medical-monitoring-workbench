from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from packages.medical_monitoring.admission.document_authority import (
    DocumentAuthorityError,
    build_anonymous_conflict_packet,
    reconcile_document_authority,
)

from .monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from .monitoring_ai_repository import MonitoringAiRepository
from .monitoring_document_authority_jobs import (
    load_document_authority_analysis_run,
    promote_document_authority_from_jobs,
    resolve_document_authority_from_jobs,
    submit_document_authority_adjudication_pair,
    submit_document_authority_review_pair,
)
from .monitoring_document_candidates import MonitoringDocumentCandidateDecomposer
from .source_intake import SourceRegistryService


_ACTIVE = {MonitoringAiJobStatus.QUEUED, MonitoringAiJobStatus.RUNNING}


class MonitoringDocumentAuthorityWorkflow:
    """Drive the independent two-model authority workflow without client adjudication."""

    def __init__(
        self,
        repository: MonitoringAiRepository,
        primary_service: Any,
        verifier_service: Any,
        source_registry: SourceRegistryService,
        *,
        worker_wake: Callable[[], None],
    ) -> None:
        self.repository = repository
        self.primary_service = primary_service
        self.verifier_service = verifier_service
        self.source_registry = source_registry
        self.worker_wake = worker_wake

    def start(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        files: list[tuple[str, bytes]],
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = MonitoringDocumentCandidateDecomposer(candidate_root).decompose_many(
            files
        ).to_dict()
        revision = self._input_revision(project_id, batch)
        self.primary_service.submit_document_authority_analysis(
            project_id=project_id,
            input_revision=revision,
            candidate_batch=batch,
            role="primary",
        )
        self.verifier_service.submit_document_authority_analysis(
            project_id=project_id,
            input_revision=revision,
            candidate_batch=batch,
            role="verifier",
        )
        self.worker_wake()
        return {"state": "analyzing", "batch_id": batch["batch_id"]}

    def advance(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        batch_id: str,
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = self._load_batch(candidate_root, batch_id)
        primary_job = self._job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:primary:{batch_id}",
        )
        verifier_job = self._job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:verifier:{batch_id}",
        )
        if self._recover_failed_once((primary_job, verifier_job)):
            return {
                "state": "analyzing",
                "authority_status": "not_promoted",
                "batch_id": batch_id,
            }
        pending = self._pending_state((primary_job, verifier_job), "analyzing")
        if pending is not None:
            return {**pending, "batch_id": batch_id}

        primary_run = load_document_authority_analysis_run(
            self.repository,
            project_id=project_id,
            job_id=primary_job.job_id,
            candidate_batch=batch,
            role="primary",
        )
        verifier_run = load_document_authority_analysis_run(
            self.repository,
            project_id=project_id,
            job_id=verifier_job.job_id,
            candidate_batch=batch,
            role="verifier",
        )
        reconciliation = reconcile_document_authority(
            batch,
            primary_run,
            verifier_run,
        )
        if reconciliation["state"] == "resolved":
            return promote_document_authority_from_jobs(
                self.repository,
                project_id=project_id,
                candidate_batch=batch,
                candidate_root=candidate_root,
                source_registry=self.source_registry,
                primary_analysis_job_id=primary_job.job_id,
                verifier_analysis_job_id=verifier_job.job_id,
            )

        packet = build_anonymous_conflict_packet(batch, primary_run, verifier_run)
        packet_sha256 = str(packet["conflict_packet_sha256"])
        primary_review = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-review:primary:{packet_sha256}",
        )
        verifier_review = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-review:verifier:{packet_sha256}",
        )
        if primary_review is None or verifier_review is None:
            revision = self._input_revision(project_id, batch)
            _, primary_review, verifier_review = submit_document_authority_review_pair(
                self.primary_service,
                self.verifier_service,
                input_revision=revision,
                candidate_batch=batch,
                primary_analysis_job_id=primary_job.job_id,
                verifier_analysis_job_id=verifier_job.job_id,
            )
            self.worker_wake()
            return {"state": "reviewing", "batch_id": batch_id}
        if self._recover_failed_once((primary_review, verifier_review)):
            return {
                "state": "reviewing",
                "authority_status": "not_promoted",
                "batch_id": batch_id,
            }
        pending = self._pending_state(
            (primary_review, verifier_review),
            "reviewing",
        )
        if pending is not None:
            return {**pending, "batch_id": batch_id}
        review_resolution = resolve_document_authority_from_jobs(
            self.repository,
            project_id=project_id,
            candidate_batch=batch,
            primary_analysis_job_id=primary_job.job_id,
            verifier_analysis_job_id=verifier_job.job_id,
            primary_review_job_id=primary_review.job_id,
            verifier_review_job_id=verifier_review.job_id,
        )
        if review_resolution["state"] == "resolved":
            return promote_document_authority_from_jobs(
                self.repository,
                project_id=project_id,
                candidate_batch=batch,
                candidate_root=candidate_root,
                source_registry=self.source_registry,
                primary_analysis_job_id=primary_job.job_id,
                verifier_analysis_job_id=verifier_job.job_id,
                primary_review_job_id=primary_review.job_id,
                verifier_review_job_id=verifier_review.job_id,
            )

        primary_adjudication = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-adjudication:primary:v4:{packet_sha256}",
        )
        verifier_adjudication = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-adjudication:verifier:v4:{packet_sha256}",
        )
        if primary_adjudication is None or verifier_adjudication is None:
            revision = self._input_revision(project_id, batch)
            _, primary_adjudication, verifier_adjudication = (
                submit_document_authority_adjudication_pair(
                    self.primary_service,
                    self.verifier_service,
                    input_revision=revision,
                    candidate_batch=batch,
                    primary_analysis_job_id=primary_job.job_id,
                    verifier_analysis_job_id=verifier_job.job_id,
                    primary_review_job_id=primary_review.job_id,
                    verifier_review_job_id=verifier_review.job_id,
                )
            )
            self.worker_wake()
            return {"state": "adjudicating", "batch_id": batch_id}
        if self._recover_failed_once((primary_adjudication, verifier_adjudication)):
            return {
                "state": "adjudicating",
                "authority_status": "not_promoted",
                "batch_id": batch_id,
            }
        pending = self._pending_state(
            (primary_adjudication, verifier_adjudication),
            "adjudicating",
        )
        if pending is not None:
            return {**pending, "batch_id": batch_id}
        return promote_document_authority_from_jobs(
            self.repository,
            project_id=project_id,
            candidate_batch=batch,
            candidate_root=candidate_root,
            source_registry=self.source_registry,
            primary_analysis_job_id=primary_job.job_id,
            verifier_analysis_job_id=verifier_job.job_id,
            primary_review_job_id=primary_review.job_id,
            verifier_review_job_id=verifier_review.job_id,
            primary_adjudication_job_id=primary_adjudication.job_id,
            verifier_adjudication_job_id=verifier_adjudication.job_id,
        )

    @staticmethod
    def _candidate_root(workspace_dir: Path) -> Path:
        return Path(workspace_dir) / "document_authority_candidates"

    @staticmethod
    def _input_revision(
        project_id: str,
        batch: dict[str, Any],
    ) -> MonitoringAiInputRevision:
        return MonitoringAiInputRevision(
            project_id=project_id,
            batch_revision=str(batch["batch_id"]),
            sources=tuple(
                MonitoringAiSourceBinding(
                    source_entry_id=str(item["file_id"]),
                    source_content_sha256=str(item["content_sha256"]),
                )
                for item in batch["candidates"]
            ),
        )

    @staticmethod
    def _load_batch(candidate_root: Path, batch_id: str) -> dict[str, Any]:
        try:
            value = json.loads(
                (candidate_root / "batches" / f"{batch_id}.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, ValueError) as exc:
            raise DocumentAuthorityError(
                "document_authority_batch_manifest_missing"
            ) from exc
        if not isinstance(value, dict) or value.get("batch_id") != batch_id:
            raise DocumentAuthorityError("document_authority_batch_manifest_mismatch")
        return value

    def _job(self, project_id: str, task_type: MonitoringAiTaskType, key: str) -> Any:
        job = self._optional_job(project_id, task_type, key)
        if job is None:
            raise DocumentAuthorityError("document_authority_job_missing")
        return job

    def _optional_job(
        self,
        project_id: str,
        task_type: MonitoringAiTaskType,
        key: str,
    ) -> Any | None:
        jobs = [
            item
            for item in self.repository.list_jobs(
                project_id,
                task_type=task_type.value,
                business_key_prefix=key,
            )
            if item.business_key == key
        ]
        if len(jobs) > 1:
            raise DocumentAuthorityError("document_authority_job_not_unique")
        return jobs[0] if jobs else None

    @staticmethod
    def _pending_state(jobs: tuple[Any, Any], active_state: str) -> dict[str, str] | None:
        if any(job.status in _ACTIVE for job in jobs):
            return {"state": active_state, "authority_status": "not_promoted"}
        if any(job.status != MonitoringAiJobStatus.COMPLETED for job in jobs):
            return {"state": "failed", "authority_status": "not_promoted"}
        return None

    def _recover_failed_once(self, jobs: tuple[Any, Any]) -> bool:
        retryable = [
            job
            for job in jobs
            if job.status in {
                MonitoringAiJobStatus.FAILED,
                MonitoringAiJobStatus.BLOCKED,
                MonitoringAiJobStatus.STALE_INPUT,
            }
            and job.max_attempts <= 2
            and not job.contract_retirement_code
        ]
        for job in retryable:
            self.repository.retry_terminal(
                job.project_id,
                job.job_id,
                current_input_revision_sha256=job.input_revision_sha256,
            )
        if retryable:
            self.worker_wake()
        return bool(retryable)


__all__ = ["MonitoringDocumentAuthorityWorkflow"]
