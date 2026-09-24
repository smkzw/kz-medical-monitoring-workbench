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
