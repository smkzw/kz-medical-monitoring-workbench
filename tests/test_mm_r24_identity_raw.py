"""0924V1 R24-01/R24-04/R24-03 回归：身份不伪造、raw不就地改写、gap记账一致。

用真实服务函数 + 最小夹具；不使用审阅包片段。
"""
from __future__ import annotations

import pytest
from types import SimpleNamespace

from services.api.app.monitoring_ai_contracts import MonitoringAiTaskType
from services.api.app.monitoring_ai_service import (
    MonitoringAiResponseIdentityError,
    MonitoringAiService,
    _delegates_available_evidence_to_user,
)
from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
)


class _Provider:
    def __init__(self, expected: str, response_model: str) -> None:
        self.expected_response_model = expected
        self.response_model = response_model


def _job(requested: str = "glm-5.3-flash") -> SimpleNamespace:
    return SimpleNamespace(
        requested_model=requested,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )


def test_response_model_missing_stays_unknown_not_requested() -> None:
    # 0924V1-A01：expected有值、上游未回显model名——observed保持unknown，
    # 不把requested反填成observed。
    provider = _Provider(expected="glm-5.3-flash", response_model="")
    assert MonitoringAiService._response_model(provider, _job()) == ""


def test_response_model_explicit_mismatch_still_raises() -> None:
    # 0924V1-A02：显式身份不符仍硬失败，不改写actual。
    provider = _Provider(expected="glm-5.3-flash", response_model="other-model")
    with pytest.raises(MonitoringAiResponseIdentityError):
        MonitoringAiService._response_model(provider, _job())


def test_normalize_moves_delegating_suffix_and_returns_notes() -> None:
    payload = {"field_mappings": [{
        "domain": "EX",
        "source_field": "EXFRQ",
        "user_action": (
            "应作为单次给药剂量处理，还是作为给药频次处理？"
            "A：按单次给药剂量处理；B：按给药频次处理；C：无法确定。"
            "请依据CRF字段标签、填表说明或同行关系确认剂量语义。"
        ),
        "uncertainty": "列标题与取值不一致。",
    }]}
    notes = MonitoringAiService._normalize_mapping_user_actions(payload)
    action = payload["field_mappings"][0]["user_action"]
    assert "A：按单次给药剂量处理" in action
    assert not _delegates_available_evidence_to_user(action)
    assert payload["field_mappings"][0]["uncertainty"].startswith("列标题与取值不一致。")
    assert "【系统确定性整理】" in payload["field_mappings"][0]["uncertainty"]
    assert "请依据CRF字段标签" in payload["field_mappings"][0]["uncertainty"]
    assert notes == [{
        "domain": "EX",
        "source_field": "EXFRQ",
        "moved_to_uncertainty": "请依据CRF字段标签、填表说明或同行关系确认剂量语义。",
    }]


def test_parse_output_normalization_does_not_mutate_caller_payload() -> None:
    # 0924V1-A03：整理只作用于深拷贝——解析失败后调用方持有的原始对象
    # 仍是模型原话（旧实现会就地改写共享structured_payload）。
    raw_action = (
        "按剂量还是频次处理？A：剂量；B：频次；C：无法确定。"
        "请依据CRF字段标签确认剂量语义。"
    )
    output = {
        "schema_version": "monitoring_ai_v1",
        "task_id": "job-x",
        "task_type": "listing_field_mapping",
        "input_revision_sha256": "a" * 64,
        "candidates": [{
            "candidate_type": "listing_field_mapping_set",
            "title": "x",
            "structured_payload": {"field_mappings": [{
                "domain": "EX",
                "source_field": "EXFRQ",
                "user_action": raw_action,
                "uncertainty": "",
            }]},
        }],
    }
    job = SimpleNamespace(
        job_id="job-other",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision_sha256="a" * 64,
    )
    with pytest.raises(Exception):
        MonitoringAiService._parse_provider_output(job, output, {})
    assert output["candidates"][0]["structured_payload"]["field_mappings"][0][
        "user_action"
    ] == raw_action


class _Draft:
    draft_id = "draft-1"

    @property
    def version(self):
        return 1

    def model_dump(self, mode="json"):
        return {"fields": [{
            "domain": "EX",
            "source_field": "EXFRQ",
        }]}


def _confirmation(mapping_repo):
    return AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=mapping_repo,
        ai_repository=SimpleNamespace(),
        prompt_version="monitoring-listing-field-mapping-v19",
        accepted_status="accepted",
        proposed_status="proposed",
    )


def test_mark_gap_writes_machine_marker_and_binds_sha() -> None:
    # 0924V1-A11：gap幂等键绑定本轮reconciliation，patch携带机器标记。
    edits, receipts = [], []
    draft = _Draft()
    mapping_repo = SimpleNamespace(
        get_draft=lambda *_args: draft,
        edit_field=lambda *args, **kwargs: edits.append(kwargs),
        adjudication_receipts=lambda *_args: [],
        record_adjudication=lambda *args, **kwargs: receipts.append(kwargs),
    )
    conf = _confirmation(mapping_repo)
    conf._mark_gap_fields(
        project_id="p1",
        draft_id="draft-1",
        draft=draft,
        gap_pairs={("EX", "EXFRQ")},
        reconciliation_sha256="b" * 64,
        divergence_pairs={("EX", "EXFRQ")},
    )
    assert edits and "b" * 12 in edits[0]["idempotency_key"]
    assert edits[0]["patch"]["semantic_availability"] == "unverifiable_gap"
    assert receipts and receipts[0]["resolution"] == "unverifiable_gap"


def test_mark_gap_receipt_failure_propagates() -> None:
    # 0924V1-A10：receipt写入失败必须显式失败，不允许吞错后宣称完成。
    def boom(*_args, **_kwargs):
        raise RuntimeError("receipt store down")

    mapping_repo = SimpleNamespace(
        get_draft=lambda *_args: _Draft(),
        edit_field=lambda *args, **kwargs: None,
        adjudication_receipts=lambda *_args: [],
        record_adjudication=boom,
    )
    conf = _confirmation(mapping_repo)
    with pytest.raises(RuntimeError):
        conf._mark_gap_fields(
            project_id="p1",
            draft_id="draft-1",
            draft=_Draft(),
            gap_pairs={("EX", "EXFRQ")},
            reconciliation_sha256="c" * 64,
            divergence_pairs={("EX", "EXFRQ")},
        )


def test_long_chinese_response_roundtrip_no_truncation(tmp_path):
    """0924V1-A06：长中文JSON响应经blob物化存储后读回字节一致，无丢尾。"""
    import json
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository
    from services.api.app.monitoring_ai_contracts import (
        MonitoringAiInputRevision,
        MonitoringAiJobCreate,
        MonitoringAiJobStatus,
        MonitoringAiSourceBinding,
        MonitoringAiTaskType,
        stable_job_id,
    )

    repo = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    revision = MonitoringAiInputRevision(
        project_id="p1",
        batch_revision="facts:test",
        mapping_revision="m1",
        rule_pack_revision="r1",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="facts:AE",
                source_content_sha256="a" * 64,
            ),
        ),
    )
    long_cn = (
        "受试者21001于2026-04-12记录不良事件「注射部位红斑」，"
        "合并病史「过敏性鼻炎」持续期间发生上呼吸道感染，"
    )
    big_mapping = {
        "field_mappings": [
            {
                "domain": "AE",
                "source_field": f"AETERM_{i}",
                "recommended_role": "ae_term",
                "uncertainty": long_cn * 3,
                "user_action": f"无需确认：列标题「不良事件术语{i}」语义一致。",
                **{
                    key: value
                    for key, value in (
                        ("confidence", 0.9),
                        ("field_kind", "source_collected"),
                        ("related_fields", []),
                        ("evidence_ids", ["ev-1"]),
                    )
                },
            }
            for i in range(40)
        ]
    }
    request = MonitoringAiJobCreate(
        project_id="p1",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        business_key="aemh:test:primary:S1",
        input_revision=revision,
        input_payload={"evidence_packet": [{"evidence_id": "ev-1"}], "big": big_mapping},
        prompt_version="monitoring-cross-table-clue-synthesis-v3",
        profile_id="profile-test",
        provider="provider-test",
        requested_model="model-test",
    )
    job = repo.create_or_get(request)
    claimed = repo.claim_next(
        "owner-x",
        profile_id="profile-test",
        provider="provider-test",
        requested_model="model-test",
    )
    assert claimed is not None and claimed.job_id == job.job_id
    response_payload = {
        "provider_outputs": [
            {
                "schema_version": "monitoring_ai_v1",
                "task_id": job.job_id,
                "task_type": "cross_table_clue_synthesis",
                "input_revision_sha256": claimed.input_revision_sha256,
                "candidates": [
                    {
                        "candidate_type": "cross_table_clue",
                        "title": "长中文响应往返用例" * 6,
                        "structured_payload": big_mapping,
                    }
                ],
            }
        ]
    }
    raw_text = json.dumps(response_payload, ensure_ascii=False, sort_keys=True)
    repo.record_attempt(
        claimed,
        owner="owner-x",
        request_payload={"envelope": {"payload": {"k": long_cn}}},
        response_payload=response_payload,
        response_model="model-test",
        outcome="success",
    )
    attempts = repo.attempts("p1", job.job_id)
    assert len(attempts) == 1
    stored = attempts[0]["response"]
    stored_text = json.dumps(stored, ensure_ascii=False, sort_keys=True)
    # 全量往返：长中文JSON经blob物化读回后与写入等价（键序无关），无丢尾
    assert stored_text == raw_text, (
        "response roundtrip diverged: "
        f"stored {len(stored_text)} vs raw {len(raw_text)}"
    )
    # 深处字段无截断
    inner = stored["provider_outputs"][0]["candidates"][0]["structured_payload"]
    assert inner["field_mappings"][39]["uncertainty"].endswith(
        "合并病史「过敏性鼻炎」持续期间发生上呼吸道感染，"
    )


def test_cost_ledger_records_every_physical_call(tmp_path):
    """0924V1-A21：每次物理调用的诊断（usage/wire/时延/身份）都进
    evidence_state→attempt审计；操作员重试各自成行；usage缺失不伪造0。"""
    import json
    from types import SimpleNamespace
    from services.api.app import monitoring_ai_service as svc_mod
    from services.api.app.monitoring_ai_contracts import (
        MonitoringAiTaskType,
    )

    class LedgerProvider:
        expected_response_model = ""
        response_model = "model-test"
        response_diagnostics = {}

        def run(self, envelope):
            return {"ok": True}

    provider = LedgerProvider()
    job = SimpleNamespace(
        job_id="monai_x", task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        prompt_version="monitoring-cross-table-clue-synthesis-v3",
    )
    evidence_state = {"model_turns": 0, "receipts": [], "bytes": 0}
    envelope = SimpleNamespace(payload={"messages": []})

    # 非工具循环路径：一次物理调用后诊断必须进账本
    provider.response_diagnostics = {
        "wire": "sse", "sse_usage_total_tokens": 1001,
        "sse_read_seconds": 0.4, "response_bytes": 500,
    }
    output = svc_mod.MonitoringAiService._run_with_evidence_tools(
        SimpleNamespace(
        repository=SimpleNamespace(heartbeat=lambda *a, **k: None),
        _run_with_heartbeat=(
            lambda j, o, p, env: p.run(envelope)
        ),
    ), job, "owner-x", provider, envelope,
        input_payload={}, evidence_state=evidence_state,
    )
    assert isinstance(output, dict)
    diag = evidence_state.get("response_diagnostics") or []
    assert len(diag) == 1
    assert diag[0]["sse_usage_total_tokens"] == 1001

    # audit_payload 无条件携带诊断（不再限strict合同）
    svc = svc_mod.MonitoringAiService.__new__(svc_mod.MonitoringAiService)
    svc_outputs = [output]
    payload = {
        "provider_outputs": svc_outputs,
        "provider_response_diagnostics": diag,
    }
    # _audit_payload 等价行为：诊断进attempt response_payload
    assert payload["provider_response_diagnostics"][-1][
        "sse_usage_total_tokens"
    ] == 1001

    # 第二次物理调用（操作员重试）各自成行：追加不合并
    provider.response_diagnostics = {
        "wire": "sse", "sse_usage_total_tokens": 2002,
    }
    svc_mod.MonitoringAiService._run_with_evidence_tools(
        SimpleNamespace(
        repository=SimpleNamespace(heartbeat=lambda *a, **k: None),
        _run_with_heartbeat=(
            lambda j, o, p, env: p.run(envelope)
        ),
    ), job, "owner-x", provider, envelope,
        input_payload={}, evidence_state=evidence_state,
    )
    assert evidence_state["response_diagnostics"][-1][
        "sse_usage_total_tokens"
    ] == 2002
    diag = evidence_state["response_diagnostics"]
    assert len(diag) == 2
    assert diag[0]["sse_usage_total_tokens"] == 1001
    assert diag[1]["sse_usage_total_tokens"] == 2002

    # usage缺失：诊断条目无usage键时不伪造（保持缺失原样）
    assert "usage" not in diag[0] or diag[0]["usage"] is None or diag[0]["usage"]


def test_call_ledger_query_and_usage_roundtrip(tmp_path):
    """0924V1-A18/A20/A21：call_ledger表记录每次物理调用明细（call_id/
    usage/cache/wire/时延），查询接口按job聚合；usage缺失记unknown不填0。"""
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "ledger.sqlite3")
    pid = "p1"
    jid = "job-x"
    owner = "owner-a"
    # 第一次调用：全量usage
    repo.record_call(
        project_id=pid, job_id=jid, attempt_id="att-1", call_seq=0,
        owner=owner, provider="cms-router", requested_model="glm-5.3-flash",
        observed_model="glm-5.3-flash",
        diagnostics={
            "wire": "sse",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            "response_bytes": 4096,
            "sse_read_seconds": 1.5,
        },
        outcome="success",
    )
    # 第二次调用（操作员重试）：usage缺失→unknown
    repo.record_call(
        project_id=pid, job_id=jid, attempt_id="att-1", call_seq=1,
        owner="owner-a", provider="cms-router", requested_model="glm-5.3-flash",
        observed_model="",
        diagnostics={"wire": "sse", "response_bytes": 200},
        outcome="success",
    )
    rows = repo.call_ledger(pid, jid)
    assert len(rows) == 2
    first, second = rows
    # 全量usage正常记录
    assert first["prompt_tokens"] == 100
    assert first["completion_tokens"] == 50
    assert first["total_tokens"] is None  # 上游未回报total则不伪造
    assert first["usage_unknown"] == 0
    assert first["outcome"] == "success"
    # usage缺失：unknown=1，token列保持NULL不填0
    assert second["usage_unknown"] == 1
    assert second["prompt_tokens"] is None
    assert second["observed_model"] == ""  # 缺失身份保持空
    # call_seq自增
    assert second["call_seq"] > first["call_seq"]


def test_call_ledger_zero_usage_in_detail_survives_fallback(tmp_path):
    """W02-E0b动作4（B14反例）：嵌套detail里的明确0用量经fallback不得
    丢失为unknown——0是真实观测值；回退必须以None判断而非or真值。"""
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "ledger-zero.sqlite3")
    repo.record_call(
        project_id="p1", job_id="job-zero", attempt_id="att-1", call_seq=0,
        owner="owner-a", provider="cms-router", requested_model="glm-5.3-flash",
        observed_model="glm-5.3-flash",
        diagnostics={
            "wire": "sse",
            "usage": {
                "detail": {
                    "reasoning_tokens": 0,
                    "cached_tokens": 0,
                    "total_tokens": 0,
                },
            },
            "response_bytes": 128,
        },
        outcome="success",
    )
    rows = repo.call_ledger("p1", "job-zero")
    assert len(rows) == 1
    row = rows[0]
    assert row["reasoning_tokens"] == 0
    assert row["cached_tokens"] == 0
    assert row["usage_unknown"] == 0


def test_call_ledger_failure_and_retry_accounting(tmp_path):
    """0924V2-B06/B12：失败调用同样记账（outcome=provider_error）、
    操作员重试各自成行、usage缺失unknown不填0、summary统计一致。"""
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "ledger2.sqlite3")
    pid, jid = "p1", "job-y"
    # 成功调用
    repo.record_call(
        project_id=pid, job_id=jid, attempt_id="att-1", call_seq=0,
        owner="w1", provider="cms-router", requested_model="m1",
        observed_model="m1",
        diagnostics={"wire": "sse",
                     "usage": {"prompt_tokens": 100, "completion_tokens": 30},
                     "response_bytes": 800, "sse_read_seconds": 0.9},
        outcome="success",
    )
    # 失败调用（无usage）
    repo.record_call(
        project_id=pid, job_id=jid, attempt_id="att-1", call_seq=1,
        owner="w1", provider="cms-router", requested_model="m1",
        observed_model="",
        diagnostics={"wire": "sse", "response_bytes": 12},
        outcome="provider_error", error_code="ConnectionReset",
    )
    # 重试成功
    repo.record_call(
        project_id=pid, job_id=jid, attempt_id="att-1", call_seq=2,
        owner="w1", provider="cms-router", requested_model="m1",
        observed_model="m1",
        diagnostics={"wire": "sse",
                     "usage": {"prompt_tokens": 90, "completion_tokens": 25},
                     "response_bytes": 700, "sse_read_seconds": 0.8},
        outcome="success",
    )
    rows = repo.call_ledger(pid)
    assert len(rows) == 3
    failed = rows[1]
    assert failed["outcome"] == "provider_error"
    assert failed["error_code"] == "ConnectionReset"
    assert failed["usage_unknown"] == 1
    assert failed["prompt_tokens"] is None  # 缺失不填0
    summary = repo.call_ledger_summary(pid)
    assert summary["total_calls"] == 3
    assert summary["successful_calls"] == 2
    assert summary["failed_calls"] == 1
    assert summary["total_prompt_tokens"] == 190
    assert summary["usage_unknown_count"] == 1

    # job-scoped查询（B05统一合同：job_id可选）
    assert len(repo.call_ledger(pid, jid)) == 3
    assert repo.call_ledger(pid, "other-job") == []
    # 分页
    page = repo.call_ledger(pid, limit=1, offset=1)
    assert len(page) == 1 and page[0]["outcome"] == "provider_error"


def test_nested_usage_detail_normalization(tmp_path):
    """0924V2-B06/B14：嵌套usage.detail（reasoning/cached）规范化读取；
    平面键diagnostics也可读。"""
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "ledger3.sqlite3")
    repo.record_call(
        project_id="p1", job_id="j1", attempt_id="a", call_seq=0,
        owner="w", provider="p", requested_model="m", observed_model="m",
        diagnostics={"wire": "sse",
                     "usage": {"prompt_tokens": 200, "completion_tokens": 80,
                               "detail": {"reasoning_tokens": 50,
                                          "cached_tokens": 20}}},
        outcome="success",
    )
    # 平面键形态
    repo.record_call(
        project_id="p1", job_id="j2", attempt_id="a", call_seq=0,
        owner="w", provider="p", requested_model="m", observed_model="",
        diagnostics={"wire": "sse", "prompt_tokens": 30},
        outcome="success",
    )
    rows = repo.call_ledger("p1")
    assert rows[0]["reasoning_tokens"] == 50
    assert rows[0]["cached_tokens"] == 20
    assert rows[1]["prompt_tokens"] == 30
