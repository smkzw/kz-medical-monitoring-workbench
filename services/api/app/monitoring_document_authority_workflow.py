from __future__ import annotations

import json
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from packages.medical_monitoring.admission.document_authority import (
    DOCUMENT_ROLES,
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
    content_sha256,
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
        actor: str = "medical_manager",
        expected_decision_version: int | None = None,
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = self._load_batch(candidate_root, batch_id)
        # V5-09：合并持久化裁决（文件中已有）与本次显式提交（落盘），
        # 之后所有阶段统一消费有效集——刷新/重启/无参数resolve不丢裁决。
        user_role_selections, decision_record = self._effective_user_decision(
            project_id=project_id,
            workspace_dir=workspace_dir,
            batch=batch,
            user_role_selections=user_role_selections,
            actor=actor,
            expected_decision_version=expected_decision_version,
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
                decision_record=decision_record,
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
                decision_record=decision_record,
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
                decision_record=decision_record,
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
            decision_record=decision_record,
        )

    @staticmethod
    def _candidate_root(workspace_dir: Path) -> Path:
        return Path(workspace_dir) / "document_authority_candidates"

    _USER_SELECTIONS_SCHEMA = "monitoring-document-authority-decision-v2"
    _LEGACY_USER_SELECTIONS_SCHEMA = (
        "monitoring-document-authority-user-selections-v1"
    )

    @classmethod
    def _selections_path(cls, workspace_dir: Path, batch_id: str) -> Path:
        return (
            cls._candidate_root(workspace_dir)
            / "user_selections"
            / f"{batch_id}.json"
        )

    @classmethod
    def _decision_revision_path(
        cls, workspace_dir: Path, batch_id: str, version: int
    ) -> Path:
        return (
            cls._candidate_root(workspace_dir)
            / "user_selection_revisions"
            / batch_id
            / f"decision-{version}.json"
        )

    @classmethod
    @contextmanager
    def _decision_lock(
        cls, workspace_dir: Path, batch_id: str
    ) -> Iterator[None]:
        """Serialize the read-check-write CAS across processes for one batch."""

        lock_path = (
            cls._candidate_root(workspace_dir)
            / "user_selection_revisions"
            / batch_id
            / ".decision.lock"
        )
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    @classmethod
    def _load_user_selections(
        cls, workspace_dir: Path, batch_id: str
    ) -> dict[str, Any] | None:
        """Read the current immutable decision pointer and fail on corruption."""

        path = cls._selections_path(workspace_dir, batch_id)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            raise DocumentAuthorityError(
                "document_authority_decision_corrupt"
            ) from exc
        if (
            not isinstance(value, dict)
            or value.get("batch_id") != batch_id
        ):
            raise DocumentAuthorityError("document_authority_decision_corrupt")
        if value.get("schema_version") == cls._LEGACY_USER_SELECTIONS_SCHEMA:
            if not isinstance(value.get("selections"), list):
                raise DocumentAuthorityError("document_authority_decision_corrupt")
            return value
        if value.get("schema_version") != cls._USER_SELECTIONS_SCHEMA:
            raise DocumentAuthorityError("document_authority_decision_corrupt")
        decision_sha256 = str(value.get("decision_sha256") or "")
        unsigned = {key: item for key, item in value.items() if key != "decision_sha256"}
        if decision_sha256 != content_sha256(unsigned):
            raise DocumentAuthorityError("document_authority_decision_corrupt")
        version = value.get("decision_version")
        if not isinstance(version, int) or version < 1:
            raise DocumentAuthorityError("document_authority_decision_corrupt")
        revision_path = cls._decision_revision_path(workspace_dir, batch_id, version)
        try:
            frozen = json.loads(revision_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DocumentAuthorityError(
                "document_authority_decision_revision_missing"
            ) from exc
        if frozen != value:
            raise DocumentAuthorityError("document_authority_decision_revision_mismatch")
        return value

    @classmethod
    def _write_decision_payload(
        cls,
        workspace_dir: Path,
        payload: dict[str, Any],
    ) -> None:
        batch_id = str(payload["batch_id"])
        version = int(payload["decision_version"])
        path = cls._selections_path(workspace_dir, batch_id)
        revision_path = cls._decision_revision_path(workspace_dir, batch_id, version)
        revision_path.parent.mkdir(parents=True, exist_ok=True)
        if revision_path.exists():
            try:
                existing = json.loads(revision_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise DocumentAuthorityError(
                    "document_authority_decision_revision_exists"
                ) from exc
            if existing != payload:
                raise DocumentAuthorityError(
                    "document_authority_decision_revision_exists"
                )
        else:
            revision_tmp = revision_path.with_suffix(".json.tmp")
            revision_tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            revision_tmp.replace(revision_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        temporary.replace(path)

    @classmethod
    def _save_user_selections(
        cls,
        workspace_dir: Path,
        batch: dict[str, Any],
        project_id: str,
        selections: list[dict[str, Any]],
        *,
        actor: str,
        expected_decision_version: int | None,
    ) -> dict[str, Any]:
        """Persist one CAS-protected decision revision and immutable history row."""

        batch_id = str(batch["batch_id"])
        with cls._decision_lock(workspace_dir, batch_id):
            current = cls._load_user_selections(workspace_dir, batch_id)
            if current and current.get("schema_version") != cls._USER_SELECTIONS_SCHEMA:
                raise DocumentAuthorityError("document_authority_decision_migration_required")
            current_version = int(current["decision_version"]) if current else 0
            merged = {
                str(item["role"]): {
                    "role": str(item["role"]),
                    "candidate_id": str(item.get("candidate_id") or ""),
                }
                for item in (current or {}).get("selections", ())
            }
            for item in selections:
                merged[str(item["role"])] = {
                    "role": str(item["role"]),
                    "candidate_id": str(item.get("candidate_id") or ""),
                }
            normalized = sorted(merged.values(), key=lambda item: item["role"])
            if current and normalized == current.get("selections"):
                return current
            if current_version and expected_decision_version != current_version:
                raise DocumentAuthorityError(
                    "document_authority_decision_revision_conflict"
                )
            if not current_version and expected_decision_version not in {None, 0}:
                raise DocumentAuthorityError(
                    "document_authority_decision_revision_conflict"
                )
            now = datetime.now(timezone.utc).isoformat()
            unsigned = {
                "schema_version": cls._USER_SELECTIONS_SCHEMA,
                "batch_id": batch_id,
                "project_id": project_id,
                "batch_manifest_sha256": content_sha256(batch),
                "decision_version": current_version + 1,
                "previous_decision_sha256": (
                    str(current["decision_sha256"]) if current else ""
                ),
                "actor": actor.strip(),
                "decided_at": now,
                "selections": normalized,
            }
            payload = {**unsigned, "decision_sha256": content_sha256(unsigned)}
            cls._write_decision_payload(workspace_dir, payload)
            return payload

    @classmethod
    def _migrate_legacy_decision(
        cls,
        *,
        workspace_dir: Path,
        batch: dict[str, Any],
        project_id: str,
    ) -> dict[str, Any]:
        """Migrate one valid v1 pointer exactly once under the batch CAS lock."""

        batch_id = str(batch["batch_id"])
        candidate_ids = {
            str(item.get("candidate_id") or "")
            for item in batch.get("candidates", ())
        }
        with cls._decision_lock(workspace_dir, batch_id):
            current = cls._load_user_selections(workspace_dir, batch_id)
            if current is None:
                raise DocumentAuthorityError("document_authority_decision_corrupt")
            if current.get("schema_version") == cls._USER_SELECTIONS_SCHEMA:
                return current
            legacy_selections = [
                {
                    "role": str(item.get("role") or "").strip(),
                    "candidate_id": str(item.get("candidate_id") or "").strip(),
                }
                for item in current.get("selections", ())
                if isinstance(item, dict)
            ]
            legacy_roles = [item["role"] for item in legacy_selections]
            if (
                current.get("project_id") != project_id
                or any(role not in DOCUMENT_ROLES for role in legacy_roles)
                or len(legacy_roles) != len(set(legacy_roles))
                or any(
                    item["candidate_id"]
                    and item["candidate_id"] not in candidate_ids
                    for item in legacy_selections
                )
            ):
                raise DocumentAuthorityError(
                    "document_authority_decision_scope_mismatch"
                )
            legacy_actor = next(
                (
                    str(item.get("actor") or "").strip()
                    for item in current.get("selections", ())
                    if isinstance(item, dict)
                    and str(item.get("actor") or "").strip()
                ),
                "medical_manager",
            )
            unsigned = {
                "schema_version": cls._USER_SELECTIONS_SCHEMA,
                "batch_id": batch_id,
                "project_id": project_id,
                "batch_manifest_sha256": content_sha256(batch),
                "decision_version": 1,
                "previous_decision_sha256": "",
                "actor": legacy_actor,
                "decided_at": str(
                    current.get("updated_at")
                    or datetime.now(timezone.utc).isoformat()
                ),
                "selections": sorted(
                    legacy_selections, key=lambda item: item["role"]
                ),
            }
            migrated = {**unsigned, "decision_sha256": content_sha256(unsigned)}
            cls._write_decision_payload(workspace_dir, migrated)
            return migrated

    def _effective_user_decision(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        batch: dict[str, Any],
        user_role_selections: Any,
        actor: str,
        expected_decision_version: int | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        batch_id = str(batch["batch_id"])
        persisted = self._load_user_selections(workspace_dir, batch_id)
        if (
            persisted
            and persisted.get("schema_version")
            == self._LEGACY_USER_SELECTIONS_SCHEMA
        ):
            persisted = self._migrate_legacy_decision(
                workspace_dir=workspace_dir,
                batch=batch,
                project_id=project_id,
            )
        if persisted:
            if (
                persisted.get("project_id") != project_id
                or persisted.get("batch_manifest_sha256") != content_sha256(batch)
            ):
                raise DocumentAuthorityError("document_authority_decision_scope_mismatch")
        incoming = [
            {
                "role": str(item.get("role") or "").strip(),
                "candidate_id": str(item.get("candidate_id") or "").strip(),
            }
            for item in (user_role_selections or ())
            if isinstance(item, dict)
        ]
        candidate_ids = {
            str(item.get("candidate_id") or "")
            for item in batch.get("candidates", ())
        }
        roles = [item["role"] for item in incoming]
        if (
            any(not role for role in roles)
            or any(role not in DOCUMENT_ROLES for role in roles)
            or len(roles) != len(set(roles))
            or any(
                item["candidate_id"] and item["candidate_id"] not in candidate_ids
                for item in incoming
            )
            or not actor.strip()
        ):
            raise DocumentAuthorityError("document_authority_user_selection_invalid")
        if incoming:
            persisted = self._save_user_selections(
                workspace_dir,
                batch,
                project_id,
                incoming,
                actor=actor,
                expected_decision_version=expected_decision_version,
            )
        return (
            [dict(item) for item in (persisted or {}).get("selections", ())],
            dict(persisted) if persisted else None,
        )

    def _effective_user_selections(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        batch_id: str,
        user_role_selections: Any,
        actor: str = "medical_manager",
        expected_decision_version: int | None = None,
    ) -> list[dict[str, Any]]:
        """Compatibility helper for callers that already persisted a batch manifest."""

        batch = self._load_batch(self._candidate_root(workspace_dir), batch_id)
        selections, _decision = self._effective_user_decision(
            project_id=project_id,
            workspace_dir=workspace_dir,
            batch=batch,
            user_role_selections=user_role_selections,
            actor=actor,
            expected_decision_version=expected_decision_version,
        )
        return selections

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
            # V5会商L2-1：失败必须可诊断——携带作业级错误码与消息透传。
            failed_jobs = [
                {
                    "business_key": str(job.business_key),
                    "status": str(job.status.value)
                    if hasattr(job.status, "value")
                    else str(job.status),
                    "failure_code": str(getattr(job, "failure_code", "") or ""),
                    "failure_message": str(
                        getattr(job, "failure_message", "") or ""
                    )[:300],
                    "observed_response_model": str(
                        getattr(job, "observed_response_model", "") or ""
                    ),
                }
                for job in jobs
                if job.status != MonitoringAiJobStatus.COMPLETED
            ]
            return {
                "state": "failed",
                "authority_status": "not_promoted",
                "failure_code": failed_jobs[0]["failure_code"]
                if failed_jobs
                else "",
                "failure_message": failed_jobs[0]["failure_message"]
                if failed_jobs
                else "",
                "failed_jobs": failed_jobs,
            }
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
