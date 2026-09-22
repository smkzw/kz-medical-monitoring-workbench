from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from packages.medical_monitoring.admission.document_authority import (
    DocumentAuthorityError,
    PRIMARY_ADJUDICATION_PROMPT_VERSION,
    PRIMARY_CRITIQUE_PROMPT_VERSION,
    PRIMARY_PROMPT_VERSION,
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
    submit_document_authority_critique_pair,
    submit_document_authority_review_pair,
)
from .monitoring_document_candidates import MonitoringDocumentCandidateDecomposer
from .source_intake import SourceRegistryService


_ACTIVE = {MonitoringAiJobStatus.QUEUED, MonitoringAiJobStatus.RUNNING}
_ANALYSIS_GENERATION = PRIMARY_PROMPT_VERSION.rsplit("-", 1)[-1]
_ADJUDICATION_GENERATION = PRIMARY_ADJUDICATION_PROMPT_VERSION.rsplit("-", 1)[-1]
_CRITIQUE_GENERATION = PRIMARY_CRITIQUE_PROMPT_VERSION.rsplit("-", 1)[-1]


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
        ocr_runner: Callable[[int, int, str, bytes], Any] | None = None,
        ocr_model: str = "GLM-OCR-bf16",
        ocr_dpi: int = 200,
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = MonitoringDocumentCandidateDecomposer(
            candidate_root,
            ocr_runner=ocr_runner,
            ocr_model=ocr_model,
            ocr_dpi=ocr_dpi,
        ).decompose_many(files).to_dict()
        if any(
            candidate.get("role_hypotheses")
            and (
                candidate.get("technical_status") != "ready"
                or candidate.get("extraction_status") != "parsed"
            )
            for candidate in batch["candidates"]
        ):
            raise DocumentAuthorityError("document_authority_evidence_incomplete")
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
        user_role_selections: Any = (),
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = self._load_batch(candidate_root, batch_id)
        # V5-09：合并持久化裁决（文件中已有）与本次显式提交（落盘），
        # 之后所有阶段统一消费有效集——刷新/重启/无参数resolve不丢裁决。
        user_role_selections = self._effective_user_selections(
            project_id=project_id,
            workspace_dir=workspace_dir,
            batch_id=batch_id,
            user_role_selections=user_role_selections,
        )
        primary_job = self._job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:primary:{_ANALYSIS_GENERATION}:{batch_id}",
        )
        verifier_job = self._job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:verifier:{_ANALYSIS_GENERATION}:{batch_id}",
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
            user_role_selections=user_role_selections,
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
                user_role_selections=user_role_selections,
            )

        primary_adjudication = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-adjudication:primary:{_ADJUDICATION_GENERATION}:{packet_sha256}",
        )
        verifier_adjudication = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-adjudication:verifier:{_ADJUDICATION_GENERATION}:{packet_sha256}",
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
        adjudication_resolution = resolve_document_authority_from_jobs(
            self.repository,
            project_id=project_id,
            candidate_batch=batch,
            primary_analysis_job_id=primary_job.job_id,
            verifier_analysis_job_id=verifier_job.job_id,
            primary_review_job_id=primary_review.job_id,
            verifier_review_job_id=verifier_review.job_id,
            primary_adjudication_job_id=primary_adjudication.job_id,
            verifier_adjudication_job_id=verifier_adjudication.job_id,
            user_role_selections=user_role_selections,
        )
        if adjudication_resolution["state"] == "resolved":
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
                user_role_selections=user_role_selections,
            )

        primary_critique = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-critique:primary:{_CRITIQUE_GENERATION}:{packet_sha256}",
        )
        verifier_critique = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            f"document-authority-critique:verifier:{_CRITIQUE_GENERATION}:{packet_sha256}",
        )
        if primary_critique is None or verifier_critique is None:
            revision = self._input_revision(project_id, batch)
            _, primary_critique, verifier_critique = (
                submit_document_authority_critique_pair(
                    self.primary_service,
                    self.verifier_service,
                    input_revision=revision,
                    candidate_batch=batch,
                    primary_analysis_job_id=primary_job.job_id,
                    verifier_analysis_job_id=verifier_job.job_id,
                    primary_review_job_id=primary_review.job_id,
                    verifier_review_job_id=verifier_review.job_id,
                    primary_adjudication_job_id=primary_adjudication.job_id,
                    verifier_adjudication_job_id=verifier_adjudication.job_id,
                )
            )
            self.worker_wake()
            return {"state": "cross_checking", "batch_id": batch_id}
        if self._recover_failed_once((primary_critique, verifier_critique)):
            return {
                "state": "cross_checking",
                "authority_status": "not_promoted",
                "batch_id": batch_id,
            }
        pending = self._pending_state(
            (primary_critique, verifier_critique), "cross_checking"
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
            primary_critique_job_id=primary_critique.job_id,
            verifier_critique_job_id=verifier_critique.job_id,
            user_role_selections=user_role_selections,
        )

    @staticmethod
    def _candidate_root(workspace_dir: Path) -> Path:
        return Path(workspace_dir) / "document_authority_candidates"

    _USER_SELECTIONS_SCHEMA = "monitoring-document-authority-user-selections-v1"

    @classmethod
    def _selections_path(cls, workspace_dir: Path, batch_id: str) -> Path:
        return (
            cls._candidate_root(workspace_dir)
            / "user_selections"
            / f"{batch_id}.json"
        )

    @classmethod
    def _load_user_selections(
        cls, workspace_dir: Path, batch_id: str
    ) -> list[dict[str, Any]]:
        """V5-09：读取已持久化的用户裁决（刷新/重启/无参数resolve均生效）。"""

        try:
            value = json.loads(
                cls._selections_path(workspace_dir, batch_id).read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, ValueError):
            return []
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != cls._USER_SELECTIONS_SCHEMA
            or value.get("batch_id") != batch_id
        ):
            return []
        return [
            dict(item)
            for item in value.get("selections", ())
            if isinstance(item, dict) and str(item.get("role", "")).strip()
        ]

    @classmethod
    def _save_user_selections(
        cls,
        workspace_dir: Path,
        batch_id: str,
        project_id: str,
        selections: list[dict[str, Any]],
    ) -> None:
        """V5-09：按角色合并持久化（同角色新裁决覆盖旧值，幂等可重发）。"""

        if not selections:
            return
        path = cls._selections_path(workspace_dir, batch_id)
        merged = {
            str(item["role"]): dict(item)
            for item in cls._load_user_selections(workspace_dir, batch_id)
        }
        from datetime import datetime as _datetime  # noqa: PLC0415

        now = _datetime.now().isoformat()
        for item in selections:
            record = dict(item)
            record.setdefault("actor", "medical_manager")
            record["decided_at"] = now
            merged[str(item["role"])] = record
        payload = {
            "schema_version": cls._USER_SELECTIONS_SCHEMA,
            "batch_id": batch_id,
            "project_id": project_id,
            "selections": sorted(
                merged.values(), key=lambda item: str(item["role"])
            ),
            "updated_at": now,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        temporary.replace(path)

    def _effective_user_selections(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        batch_id: str,
        user_role_selections: Any,
    ) -> list[dict[str, Any]]:
        persisted = self._load_user_selections(workspace_dir, batch_id)
        merged: dict[str, dict[str, Any]] = {
            str(item["role"]): dict(item) for item in persisted
        }
        incoming = [
            dict(item)
            for item in (user_role_selections or ())
            if isinstance(item, dict) and str(item.get("role", "")).strip()
        ]
        if incoming:
            for item in incoming:
                merged[str(item["role"])] = item
            self._save_user_selections(
                workspace_dir, batch_id, project_id, incoming
            )
        return list(merged.values())

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
