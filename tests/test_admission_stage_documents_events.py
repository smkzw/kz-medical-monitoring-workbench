"""状态机专项T2（02_DESIGN §5-T2/§2.2 documents表）：documents事件留痕。

覆盖：start/advance各状态分支→事件存在且from/to正确（analyzing链/
promoted/failed/needs_user_input-identity）；A5写失败→无事件无异常外泄
（best-effort纪律）；no_update触发器对documents事件同样生效；非识别链
business_key前缀不误落recognition事件（attempt_id=''项目级隔离）。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.document_authority import (  # noqa: E402
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    CandidateAssessment,
    DocumentAuthorityAnalysis,
    RoleSelection,
    document_authority_batch_sha256,
)
from packages.medical_monitoring.admission.mapping_gate import (  # noqa: E402
    DOC_AUTH_PRIMARY_MODEL,
    DOC_AUTH_PRIMARY_PROVIDER,
    DOC_AUTH_VERIFIER_MODEL,
    DOC_AUTH_VERIFIER_PROVIDER,
)
from services.api.app.ai_gateway import AiProviderRuntimeError  # noqa: E402
from services.api.app.monitoring_admission_stage_store import (  # noqa: E402
    recognition_attempt_id,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_ai_service import (  # noqa: E402
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from services.api.app.monitoring_document_authority_workflow import (  # noqa: E402
    MonitoringDocumentAuthorityWorkflow,
)
from services.api.app.monitoring_document_candidates import (  # noqa: E402
    MonitoringDocumentCandidateDecomposer,
)
from services.api.app.source_intake import (  # noqa: E402
    SourceRegistryService,
    SourceRegistryStore,
)
from tests.test_monitoring_document_authority_jobs import (  # noqa: E402
    _Provider,
    _runtime,
)
from tests.test_source_registry import (  # noqa: E402
    _minimal_docx_bytes,
    _minimal_xlsx_bytes,
)

PROJECT = "project-doc-events"


class _RaisingAnalysisProvider:
    """T2：模拟上游infra类失败——每次调用抛provider超时。"""

    transport_name = "openai_compatible"

    def __init__(self, provider: str, model: str) -> None:
        self.provider_name = provider
        self.model_name = model
        self.expected_response_model = model
        self.response_model = model

    def run(self, envelope):
        raise AiProviderRuntimeError(
            "provider timeout (simulated)",
            diagnostics={"failure_code": "provider_timeout"},
        )


def _documents_events(repo: MonitoringAiRepository) -> list[dict[str, Any]]:
    return repo.stage_store.list_events(PROJECT, "", stage="documents", limit=1000)


def _agreeing_analysis(batch: dict[str, Any]) -> DocumentAuthorityAnalysis:
    candidate_ids = {
        item["filename"]: item["candidate_id"]
        for item in batch["candidates"]
    }

    def _locators(filename: str) -> tuple:
        candidate = next(
            item
            for item in batch["candidates"]
            if item["filename"] == filename
        )
        source = candidate["excerpts"][:1] or candidate["sheets"][:1]
        return tuple(item["locator"] for item in source)

    return DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=batch["batch_id"],
        input_sha256=document_authority_batch_sha256(batch),
        candidate_assessments=(
            CandidateAssessment(
                candidate_id=candidate_ids["protocol.docx"],
                inferred_role="protocol",
                usable=True,
                confidence=0.99,
                evidence_locators=_locators("protocol.docx"),
            ),
            CandidateAssessment(
                candidate_id=candidate_ids["ecrf.xlsx"],
                inferred_role="ecrf",
                usable=True,
                confidence=0.99,
                evidence_locators=_locators("ecrf.xlsx"),
            ),
        ),
        role_selections=(
            RoleSelection(
                role="protocol",
                decision="selected",
                selected_candidate_id=candidate_ids["protocol.docx"],
                confidence=0.99,
                evidence_locators=_locators("protocol.docx"),
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="investigator_brochure",
                decision="missing",
                confidence=0.99,
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="ecrf",
                decision="selected",
                selected_candidate_id=candidate_ids["ecrf.xlsx"],
                confidence=0.99,
                evidence_locators=_locators("ecrf.xlsx"),
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="sap",
                decision="missing",
                confidence=0.99,
                supplementary_bindings=(),
            ),
        ),
    )


def _agreement_workflow(tmp_path: Path):
    protocol = _minimal_docx_bytes()
    ecrf = _minimal_xlsx_bytes()
    batch = MonitoringDocumentCandidateDecomposer(
        tmp_path / "preview"
    ).decompose_many([
        ("protocol.docx", protocol),
        ("ecrf.xlsx", ecrf),
    ]).to_dict()
    analysis = _agreeing_analysis(batch)
    repository = MonitoringAiRepository(tmp_path / "workflow.sqlite")
    services = []
    for role, provider, model in (
        ("primary", DOC_AUTH_PRIMARY_PROVIDER, DOC_AUTH_PRIMARY_MODEL),
        ("verifier", DOC_AUTH_VERIFIER_PROVIDER, DOC_AUTH_VERIFIER_MODEL),
    ):
        services.append(MonitoringAiService(
            repository,
            runtime_resolver=lambda provider=provider, model=model, role=role: _runtime(
                provider, model, f"monitoring-document-authority-{role}"
            ),
            provider_factory=lambda _env, provider=provider, model=model, analysis=analysis: _Provider(
                provider, model, analysis
            ),
        ))
    registry = SourceRegistryService(SourceRegistryStore(tmp_path / "registry.jsonl"))
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        services[0],
        services[1],
        registry,
        worker_wake=lambda: None,
    )
    return workflow, services, dict(files=[("protocol.docx", protocol), ("ecrf.xlsx", ecrf)])


def test_start_and_promote_emit_documents_event_chain(tmp_path) -> None:
    """start→analyzing；advance直通晋升→promoted（from=analyzing）。"""

    workflow, services, files = _agreement_workflow(tmp_path)
    started = workflow.start(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        files=files["files"],
    )
    assert started["state"] == "analyzing"
    events = _documents_events(workflow.repository)
    assert [event["event_type"] for event in events] == ["state_changed"]
    assert events[0]["to_state"] == "analyzing"
    assert events[0]["from_state"] == ""
    assert events[0]["attempt_id"] == ""
    assert events[0]["stage"] == "documents"

    for index, service in enumerate(services):
        service.run_next(f"t2-{index}", claim_identity=service.claim_identity())
    promoted = workflow.advance(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        batch_id=started["batch_id"],
    )
    assert promoted["authority_status"] == "promoted"
    events = _documents_events(workflow.repository)
    assert [(event["event_type"], event["to_state"]) for event in events] == [
        ("state_changed", "analyzing"),
        ("state_changed", "promoted"),
    ]
    assert events[1]["from_state"] == "analyzing"
    assert events[1]["reason_code"] == "promotion_receipt_written"


def test_infra_failure_recovery_and_explicit_retry_event_chain(tmp_path) -> None:
    """infra失败→auto recovery_action×预算→failed(failure_class=infra)
    →显式重试recovery_action(actor=user)→analyzing。"""

    repository = MonitoringAiRepository(tmp_path / "failing.sqlite")
    services = []
    for role, provider, model in (
        ("primary", DOC_AUTH_PRIMARY_PROVIDER, DOC_AUTH_PRIMARY_MODEL),
        ("verifier", DOC_AUTH_VERIFIER_PROVIDER, DOC_AUTH_VERIFIER_MODEL),
    ):
        services.append(MonitoringAiService(
            repository,
            runtime_resolver=lambda provider=provider, model=model, role=role: _runtime(
                provider, model, f"monitoring-document-authority-{role}"
            ),
            provider_factory=lambda _env, provider=provider, model=model: _RaisingAnalysisProvider(
                provider, model
            ),
        ))
    workflow = MonitoringDocumentAuthorityWorkflow(
        repository,
        services[0],
        services[1],
        SourceRegistryService(SourceRegistryStore(tmp_path / "registry.jsonl")),
        worker_wake=lambda: None,
    )
    started = workflow.start(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        files=[
            ("protocol.docx", _minimal_docx_bytes()),
            ("ecrf.xlsx", _minimal_xlsx_bytes()),
        ],
    )
    assert started["state"] == "analyzing"

    # 驱动「失败→advance自动重排」循环直至自动恢复预算耗尽落failed终态
    # （预算=R27-01 _AUTOMATIC_RECOVERY_LIMIT；上限为防死循环护栏）。
    failed = None
    for _round in range(15):
        for index, service in enumerate(services):
            service.run_next(
                f"t2-fail-{_round}-{index}",
                claim_identity=service.claim_identity(),
            )
        result = workflow.advance(
            project_id=PROJECT,
            workspace_dir=tmp_path / "workspace",
            batch_id=started["batch_id"],
        )
        if result["state"] == "failed":
            failed = result
            break
        assert result["state"] == "analyzing"
    assert failed is not None, "自动恢复预算耗尽后未落failed终态"

    events = _documents_events(repository)
    recovery_events = [
        event for event in events if event["event_type"] == "recovery_action"
    ]
    assert recovery_events, "自动重排未留痕"
    assert all(
        event["actor"] == "system"
        and event["from_state"] == "failed"
        and event["to_state"] == "analyzing"
        and event["reason_code"] == "auto_recovery"
        for event in recovery_events
    )
    failure_events = [
        event for event in events if event["event_type"] == "failure_recorded"
    ]
    assert len(failure_events) == 1
    assert failure_events[0]["from_state"] == "analyzing"
    assert failure_events[0]["to_state"] == "failed"
    # failure_class经failure_class_for分类：infra类失败码→infra。
    assert failure_events[0]["failure_class"] == "infra"
    assert failure_events[0]["reason_code"] == str(
        failed.get("failure_code") or ""
    )
    assert failure_events[0]["reason_code"]

    # 显式重试（「重新核对研究文件」按钮）→recovery_action actor=user。
    explicit = workflow.advance(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        batch_id=started["batch_id"],
        explicit_retry=True,
    )
    assert explicit["state"] == "analyzing"
    events = _documents_events(repository)
    last = events[-1]
    assert last["event_type"] == "recovery_action"
    assert last["actor"] == "user"
    assert last["reason_code"] == "explicit_retry"
    assert last["to_state"] == "analyzing"


def test_identity_gate_emits_needs_user_input_event(
    tmp_path, monkeypatch
) -> None:
    """身份门挂起→state_changed to=needs_user_input（reason=identity）。"""

    import services.api.app.monitoring_document_authority_workflow as wf_module

    workflow, services, files = _agreement_workflow(tmp_path)
    started = workflow.start(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        files=files["files"],
    )
    for index, service in enumerate(services):
        service.run_next(f"t2-id-{index}", claim_identity=service.claim_identity())

    def _mismatch(*_args, **_kwargs):
        return {
            "status": "mismatch",
            "attention_candidate_ids": [],
        }

    monkeypatch.setattr(
        wf_module,
        "resolve_document_authority_project_identity",
        _mismatch,
    )
    result = workflow.advance(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        batch_id=started["batch_id"],
    )
    assert result["state"] == "project_mismatch"
    events = _documents_events(workflow.repository)
    last = events[-1]
    assert (last["event_type"], last["to_state"]) == (
        "state_changed",
        "needs_user_input",
    )
    assert last["from_state"] == "analyzing"
    assert last["reason_code"] == "identity"


def test_stage_store_failure_does_not_leak_into_authority_path(tmp_path) -> None:
    """A5/事件写点故障→start/advance正常返回，无异常外泄（best-effort）。"""

    workflow, _services, files = _agreement_workflow(tmp_path)

    def _broken(*_args, **_kwargs):
        raise RuntimeError("stage store unavailable")

    workflow.repository.stage_store = SimpleNamespace(
        append_event_autonomous=_broken,
    )
    started = workflow.start(
        project_id=PROJECT,
        workspace_dir=tmp_path / "workspace",
        files=files["files"],
    )
    assert started["state"] == "analyzing"
    assert workflow.repository.list_jobs(PROJECT)


def test_documents_events_immutable_trigger(tmp_path) -> None:
    """no_update触发器对documents事件同样生效（append-only）。"""

    repository = MonitoringAiRepository(tmp_path / "immutable.sqlite")
    repository.stage_store.append_event_autonomous(
        project_id=PROJECT,
        attempt_id="",
        stage="documents",
        event_type="state_changed",
        to_state="analyzing",
    )
    events = _documents_events(repository)
    assert len(events) == 1
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with repository._connect() as connection:
            connection.execute(
                "UPDATE monitoring_admission_stage_events SET to_state = 'x' "
                "WHERE event_id = ?",
                (events[0]["event_id"],),
            )
            connection.commit()


def test_documents_events_do_not_leak_into_recognition_queries(tmp_path) -> None:
    """documents事件attempt_id=''项目级；非识别链business_key前缀
    不被recognition_attempt_id解析——识别事件查询零串扰。"""

    assert (
        recognition_attempt_id(
            "document-authority-analysis:primary:g1:mmbatch_x"
        )
        == ""
    )
    repository = MonitoringAiRepository(tmp_path / "isolation.sqlite")
    repository.stage_store.append_event_autonomous(
        project_id=PROJECT,
        attempt_id="",
        stage="documents",
        event_type="state_changed",
        to_state="promoted",
    )
    documents = repository.stage_store.list_events(PROJECT, "")
    assert all(event["stage"] == "documents" for event in documents)
    # 识别链按attempt键查询看不到项目级documents事件。
    assert repository.stage_store.list_events(PROJECT, "attempt-x") == []
    payload = json.dumps(documents[0], ensure_ascii=False)
    assert '"attempt_id": ""' in payload or "attempt_id" in documents[0]
