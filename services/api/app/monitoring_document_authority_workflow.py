from __future__ import annotations

import json
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from packages.medical_monitoring.admission.document_authority import (
    DOCUMENT_ROLES,
    DocumentAuthorityError,
    PRIMARY_ADJUDICATION_PROMPT_VERSION,
    PRIMARY_CRITIQUE_PROMPT_VERSION,
    PRIMARY_PROMPT_VERSION,
    build_document_authority_project_context,
    build_anonymous_conflict_packet,
    reconcile_document_authority,
    resolve_document_authority_project_identity,
)

from .monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
    content_sha256,
)
from .monitoring_ai_repository import (
    MonitoringAiRepository,
    MonitoringAiStateConflictError,
)
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
        project_context: Mapping[str, Any] | None = None,
        ocr_runner: Callable[[int, int, str, bytes], Any] | None = None,
        ocr_model: str = "GLM-OCR-bf16",
        ocr_dpi: int = 200,
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        frozen_project_context = (
            build_document_authority_project_context(project_context)
            if project_context is not None
            else None
        )
        batch = MonitoringDocumentCandidateDecomposer(
            candidate_root,
            ocr_runner=ocr_runner,
            ocr_model=ocr_model,
            ocr_dpi=ocr_dpi,
        ).decompose_many(
            files,
            project_context=frozen_project_context,
        ).to_dict()
        # R1测试循环第1轮：原判定「任一候选未完全解析即拒收整批」把
        # 「合法方案docx + 图片型eCRF pdf」组合整体挡在身份核对之外
        # （测试者D六次尝试全败，报"尚未通过完整性核对"且无原因）。
        # 现改为fail-closed于「批内没有任何可解析候选」；部分候选
        # needs_ocr时照常进入双盲分析，该候选依旧不可被选为权威文件
        # （下游_validate_analysis的eligible校验与提示词约束不变）。
        parsable_candidates = [
            candidate
            for candidate in batch["candidates"]
            if candidate.get("technical_status") == "ready"
            and candidate.get("extraction_status") == "parsed"
        ]
        if not any(
            candidate.get("role_hypotheses")
            for candidate in parsable_candidates
        ):
            # R26轮（R26-02）：拒收必须可诊断——逐文件列出技术状态与
            # 限制码，不再只给「全部为扫描版」的笼统归因。
            per_file = "；".join(
                f"{candidate['filename']}：{candidate['extraction_status']}"
                + (
                    f"（{','.join(candidate['limitation_codes'])}）"
                    if candidate.get("limitation_codes")
                    else ""
                )
                for candidate in batch["candidates"]
            )
            self._record_last_check_note(
                workspace_dir,
                "最近一次研究文件核对结论：未能从这组文件中读取到可核对的内容"
                f"（逐文件状态：{per_file}）。文本版PDF请确认非扫描件；"
                "扫描版暂不能作为权威研究文件，可将该文件角色标记为缺失"
                "后继续。",
            )
            raise DocumentAuthorityError("document_authority_evidence_incomplete")
        revision = self._input_revision(project_id, batch)
        # R9轮（R7-03跨档案组污染）：开新批次核对即清除上一组的结论
        # 留痕——原实现仅PDF组的失败结论会在重传完整文件组后继续挂
        # 在readiness上误导可用性判断（新组还在核对中≠旧组失败）。
        self._record_last_check_note(workspace_dir, "")
        # R3循环（报告B）：批次指纹是内容确定性的——同一组文件重传会
        # 得到同一batch_id并复用已完成的判定（表现为"缓存秒回"）。
        # 向界面透传该事实，让"重复上传秒出结论"与"新文件全量核对"
        # 两条路径都可预期。
        # R11轮（R11-01）：仅当既有作业确实completed才声称"复用已有结论"
        # ——infra类终态失败（代理503/SSE中断）不是内容性判定，重传
        # 必须重新核对而非秒回同一失败。
        existing_primary = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:primary:{_ANALYSIS_GENERATION}:{batch['batch_id']}",
        )
        existing_verifier = self._optional_job(
            project_id,
            MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            f"document-authority-analysis:verifier:{_ANALYSIS_GENERATION}:{batch['batch_id']}",
        )
        previously_analyzed = (
            existing_primary is not None
            and str(getattr(existing_primary, "status", "").value
                   if hasattr(getattr(existing_primary, "status", ""), "value")
                   else getattr(existing_primary, "status", "")) == "completed"
        )
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
        # R27轮（R27-03）：重新上传是用户的显式重核动作。作业指纹随内容
        # 确定——同组文件的create_or_get只会原样取回既有作业行，不会重排
        # 已落终态失败的作业；此前卡死诊断横幅承诺「重新上传会触发完整
        # 重核」因此从未兑现（重传后仍永久停在核对中）。这里对同批既有
        # 终态失败作业显式重排（不受_automatic_recovery_limit限制——
        # 自动预算只约束advance轮询路径的无感重试，不约束用户动作），
        # 让「重新上传→完整重核」成为真实可用的恢复路径。
        for existing in (existing_primary, existing_verifier):
            if existing is None or existing.contract_retirement_code:
                continue
            if existing.status not in {
                MonitoringAiJobStatus.FAILED,
                MonitoringAiJobStatus.BLOCKED,
                MonitoringAiJobStatus.STALE_INPUT,
            }:
                continue
            try:
                self.repository.retry_terminal(
                    existing.project_id,
                    existing.job_id,
                    current_input_revision_sha256=existing.input_revision_sha256,
                )
            except MonitoringAiStateConflictError:
                # 输入版本并发变化等竞态：不阻断本次上传的202响应，
                # advance轮询会按既有状态机继续处理。
                continue
        self.worker_wake()
        result = {"state": "analyzing", "batch_id": batch["batch_id"]}
        if previously_analyzed:
            # 仅在确为重复内容且已有完成结论时附带该事实，保持既有
            # 返回契约不变。
            result["previously_analyzed"] = True
        return result

    def advance(
        self,
        *,
        project_id: str,
        workspace_dir: Path,
        batch_id: str,
        user_role_selections: Any = (),
        actor: str = "medical_manager",
        expected_decision_version: int | None = None,
        identity_confirmation: Mapping[str, Any] | None = None,
        # R28轮（R28-03/R28-04）：「重新核对研究文件」按钮是用户显式
        # 重试。该标记只由按钮路径传入；轮询路径不传——自动恢复预算
        # （R27-01）继续约束无感重试，显式动作与重新上传同权（不受
        # 预算约束），否则预算耗尽后按钮永远同因再败、无任何出路。
        explicit_retry: bool = False,
    ) -> dict[str, Any]:
        candidate_root = self._candidate_root(workspace_dir)
        batch = self._load_batch(candidate_root, batch_id)
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
        recovered = (
            self._recover_failed_once(
                (primary_job, verifier_job), explicit=True
            )
            if explicit_retry
            else self._recover_failed_once((primary_job, verifier_job))
        )
        if recovered:
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
        identity = resolve_document_authority_project_identity(
            batch,
            primary_run,
            verifier_run,
        )
        if identity["status"] != "aligned" and identity["status"] != "not_assessed":
            # R1测试循环第1轮：身份门默认fail-closed（防串项目），但必须
            # 留人工裁决出口——测试者B/C的项目代号与研究方案编号字面
            # 不一致时被整体拒收且无入口，全链阻断。人工确认需显式提交
            # 并落盘审计后才放行；未确认时行为与原短路完全一致。
            override = self._effective_identity_override(
                project_id=project_id,
                workspace_dir=workspace_dir,
                batch=batch,
                confirmation=identity_confirmation,
                actor=actor,
                identity_status=str(identity["status"]),
            )
            if override is None:
                filenames = {
                    str(item.get("candidate_id") or ""): str(
                        item.get("filename") or ""
                    )
                    for item in batch["candidates"]
                }
                attention_files = [
                    filenames[candidate_id]
                    for candidate_id in identity["attention_candidate_ids"]
                    if filenames.get(candidate_id)
                ]
                self._record_last_check_note(
                    workspace_dir,
                    (
                        "最近一次研究文件核对结论："
                        + (
                            "系统未能自动确认这组资料属于当前项目"
                            if identity["status"] == "mismatch"
                            else "系统还无法确认资料归属（缺少可比对的项目标识）"
                        )
                        + (
                            f"；涉及文件：{'、'.join(attention_files)}"
                            if attention_files
                            else ""
                        )
                        + "。可在向导第3步人工确认归属或更换文件。"
                    ),
                )
                return {
                    "state": (
                        "project_mismatch"
                        if identity["status"] == "mismatch"
                        else "project_identity_incomplete"
                    ),
                    "authority_status": "not_promoted",
                    "batch_id": batch_id,
                    "identity_status": identity["status"],
                    "attention_files": attention_files,
                }
        # 只有资料已通过研究身份门，才合并持久化裁决（文件中已有）与
        # 本次显式提交（落盘）。错研究或归属不明的资料不得留下角色选择。
        # 之后所有阶段统一消费有效集——刷新/重启/无参数resolve不丢裁决。
        user_role_selections, decision_record = self._effective_user_decision(
            project_id=project_id,
            workspace_dir=workspace_dir,
            batch=batch,
            user_role_selections=user_role_selections,
            actor=actor,
            expected_decision_version=expected_decision_version,
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

    @classmethod
    def _record_last_check_note(
        cls, workspace_dir: Path, note: str
    ) -> None:
        """R5冲刺（R1-11）：持久化最近一次核对结论，刷新后仍可读。"""

        text = str(note or "").strip()
        path = (
            cls._candidate_root(workspace_dir) / "last_document_check_note.json"
        )
        try:
            if not text:
                path.unlink(missing_ok=True)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(
                    {
                        "schema_version": "monitoring-document-check-note-v1",
                        "note": text[:1_000],
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            temporary.replace(path)
        except OSError:
            # 留痕失败不阻断核对主链路。
            return

    @staticmethod
    def _candidate_root(workspace_dir: Path) -> Path:
        return Path(workspace_dir) / "document_authority_candidates"

    _USER_SELECTIONS_SCHEMA = "monitoring-document-authority-decision-v2"
    _LEGACY_USER_SELECTIONS_SCHEMA = (
        "monitoring-document-authority-user-selections-v1"
    )
    _IDENTITY_OVERRIDE_SCHEMA = (
        "monitoring-document-authority-identity-override-v1"
    )

    @classmethod
    def _identity_override_path(cls, workspace_dir: Path, batch_id: str) -> Path:
        return (
            cls._candidate_root(workspace_dir)
            / "identity_overrides"
            / f"{batch_id}.json"
        )

    @classmethod
    def _load_identity_override(
        cls,
        workspace_dir: Path,
        batch_id: str,
    ) -> dict[str, Any] | None:
        """Read one persisted human identity adjudication, fail-closed on drift."""

        path = cls._identity_override_path(workspace_dir, batch_id)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            raise DocumentAuthorityError(
                "document_authority_identity_override_corrupt"
            ) from exc
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != cls._IDENTITY_OVERRIDE_SCHEMA
            or value.get("batch_id") != batch_id
        ):
            raise DocumentAuthorityError(
                "document_authority_identity_override_corrupt"
            )
        override_sha256 = str(value.get("override_sha256") or "")
        unsigned = {
            key: item
            for key, item in value.items()
            if key != "override_sha256"
        }
        if override_sha256 != content_sha256(unsigned):
            raise DocumentAuthorityError(
                "document_authority_identity_override_corrupt"
            )
        return value

    @classmethod
    def _effective_identity_override(
        cls,
        *,
        project_id: str,
        workspace_dir: Path,
        batch: dict[str, Any],
        confirmation: Mapping[str, Any] | None,
        actor: str,
        identity_status: str,
    ) -> dict[str, Any] | None:
        """Return the human identity adjudication for this batch, if any.

        未确认返回None（保持fail-closed短路）；首次显式确认按CAS写盘；
        已有确认直接复用。确认记录绑定批次指纹与项目，防止跨批次重放。
        """

        batch_id = str(batch["batch_id"])
        with cls._decision_lock(workspace_dir, batch_id):
            persisted = cls._load_identity_override(workspace_dir, batch_id)
            if persisted is not None:
                if (
                    persisted.get("project_id") != project_id
                    or persisted.get("batch_manifest_sha256")
                    != content_sha256(batch)
                ):
                    raise DocumentAuthorityError(
                        "document_authority_identity_override_scope_mismatch"
                    )
                return persisted
            if not isinstance(confirmation, Mapping):
                return None
            if confirmation.get("confirmed") is not True:
                raise DocumentAuthorityError(
                    "document_authority_identity_confirmation_invalid"
                )
            reason = str(confirmation.get("reason") or "").strip()
            actor_name = str(actor or "").strip()
            if len(reason) < 2 or not actor_name:
                raise DocumentAuthorityError(
                    "document_authority_identity_confirmation_invalid"
                )
            now = datetime.now(timezone.utc).isoformat()
            unsigned = {
                "schema_version": cls._IDENTITY_OVERRIDE_SCHEMA,
                "batch_id": batch_id,
                "project_id": project_id,
                "batch_manifest_sha256": content_sha256(batch),
                "original_identity_status": identity_status,
                "actor": actor_name,
                "reason": reason[:2_000],
                "confirmed_at": now,
            }
            payload = {
                **unsigned,
                "override_sha256": content_sha256(unsigned),
            }
            path = cls._identity_override_path(workspace_dir, batch_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            temporary.replace(path)
            return payload

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
    def _pending_state(jobs: tuple[Any, Any], active_state: str) -> dict[str, Any] | None:
        if any(job.status in _ACTIVE for job in jobs):
            active = [job for job in jobs if job.status in _ACTIVE]
            created = [
                str(getattr(job, "created_at", "") or "")
                for job in active
                if str(getattr(job, "created_at", "") or "")
            ]
            return {
                "state": active_state,
                "authority_status": "not_promoted",
                # R25轮（R25-03）：pending不再只是一个无限期词——R25C实测
                # 归属人工确认后「正在核对」45分钟零状态变化、无超时无提示
                # 无重试入口。暴露在途作业数与最早入队时间，前端据此显示
                # 已耗时并在长时间无进展时给出重试指引。队列本身有租约
                # 超时与attempt上限，worker侧收割（R25-01）保证最终落终态。
                "pending_job_count": len(active),
                "pending_since": min(created) if created else "",
            }
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

    # R11轮（R11-01）：基础设施/提供方类失败码——瞬时故障（代理503、
    # SSE中断、上游5xx）不是内容性判定，不得被指纹去重或重试预算固化为
    # 终态结论；这类失败可自动重试。
    _INFRA_FAILURE_CODES = frozenset({
        "provider_runtime_error",
        "provider_sse_error_event",
        "provider_unavailable",
        "provider_timeout",
        "provider_rate_limited",
        "provider_auth_error",
        "provider_overloaded",
        "ai_not_configured",
        "network_error",
        "proxy_error",
    })

    # R27轮（R27-01）：infra类失败的自动重试预算。原实现「无限次自动
    # 重试」在上游持续限流（如glm-5.3-flash全credential 429冷却两小时）
    # 时，每次resolve轮询都重排重跑、作业attempt无界增长（ISO实测涨到
    # 32），且advance永远返回analyzing——界面无限「正在核对」，真实
    # 失败原因对用户完全不可见（第3步全链挂死表象）。预算内瞬断仍可
    # 无感自愈；预算耗尽后不再静默重排，advance落failed终态，resolve
    # 据此409+failure_code/message，界面如实呈现原因与恢复入口。用户
    # 显式动作（重新上传研究文件）不受此预算限制，见start()。
    _AUTOMATIC_RECOVERY_LIMIT = 3

    @classmethod
    def _is_infra_failure(cls, job: Any) -> bool:
        return str(getattr(job, "failure_code", "") or "") in cls._INFRA_FAILURE_CODES

    def _recover_failed_once(self, jobs: tuple[Any, Any], *, explicit: bool = False) -> bool:
        retryable = []
        for job in jobs:
            if job.status not in {
                MonitoringAiJobStatus.FAILED,
                MonitoringAiJobStatus.BLOCKED,
                MonitoringAiJobStatus.STALE_INPUT,
            }:
                continue
            if job.contract_retirement_code:
                continue
            # R11轮（R11-01）：infra类失败不受max_attempts<=2预算限制——
            # 一次提供方抖动曾把项目锁死（同版重传被「复用已有结论」拒、
            # 重新核对仍瞬间同409）。
            if self._is_infra_failure(job) or job.max_attempts <= 2:
                retryable.append(job)
        requeued = False
        for job in retryable:
            try:
                retried = self.repository.retry_terminal(
                    job.project_id,
                    job.job_id,
                    current_input_revision_sha256=job.input_revision_sha256,
                    # R27轮（R27-01）：自动恢复限预算；耗尽后retry_terminal
                    # 原样返回终态作业，不再重排。
                    # R28轮（R28-03）：explicit=True（「重新核对研究文件」
                    # 按钮）与重新上传同权——不传预算即不受其约束，作业
                    # 真实重排。这是上游恢复后按钮唯一可用出口。
                    automatic_recovery_limit=(
                        None if explicit else self._AUTOMATIC_RECOVERY_LIMIT
                    ),
                )
            except MonitoringAiStateConflictError:
                # 输入版本并发变化等竞态：留给下一次advance判定，不阻断。
                continue
            if retried.status not in {
                MonitoringAiJobStatus.FAILED,
                MonitoringAiJobStatus.BLOCKED,
                MonitoringAiJobStatus.STALE_INPUT,
            }:
                requeued = True
        if requeued:
            self.worker_wake()
        return requeued


__all__ = ["MonitoringDocumentAuthorityWorkflow"]
