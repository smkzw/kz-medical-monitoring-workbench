"""W01-R26（20260926）：真实Finding卡可导航——Finding DTO与QueryDraft分离。

验收锚点 R26-A12/A13（review_pack_0926V1/kz_review_0926V1/
04_ACCEPTANCE_0926V1.json）：
- A12 Finding与QueryDraft独立schema/身份关联：Finding冻结DTO含稳定
  finding_id/subject/site/事件与时间窗/状态/分类型claims/逐条source refs；
  QueryDraft保留自身query_draft_id并以finding_id引用Finding；提交侧
  强校验该引用关系；
- A13 零发现显式空集（findings:[]，无truthy省略）、载荷坏形态fail明确
  （不借query_drafts顶替findings）。

配套前端渲染契约见 frontend/src/features/medical-monitoring/
medicalMonitoringFindingCardRender.test.mjs（finding卡→事件锚→source
locator逐跳入口的静态markup断言）。全部fixture为冻结合成数据，0模型调用。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.medical_monitoring.api.r7_product.contracts import (
    ProductPublicationError,
)
from packages.medical_monitoring.api.r7_product.result_context_service import (
    ResolvedResultContext,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.reports import mode_output as mo
from packages.medical_monitoring.reports.mode_output_core import (
    build_affected_query_draft,
)
from packages.medical_monitoring.reports.report_review import (
    canonical_bytes,
    sha256_hex,
)


def _reseal(output: dict) -> dict:
    """重算output_id（载荷被篡改后必须重封，才能专测提交侧的
    Finding/QueryDraft引用校验而非envelope自校验）。"""
    out = dict(output)
    out.pop("output_id", None)
    output["output_id"] = "out-" + sha256_hex(canonical_bytes(out))
    return output
from packages.medical_monitoring.runtime import continuity_bridge as cb
from packages.medical_monitoring.runtime import launch_registry as lr

RUN_BINDING = {
    "project_id": "p1",
    "run_id": "r1",
    "mode": "daily",
    "data_cutoff": "2026-03-31",
    "source_revision_id": "rev-1",
    "execution_basis": "full",
    "knowledge_pack_version": "kp",
    "rule_activation_version": "rav",
    "mapping_version": "map",
    "identity_algorithm_version": "ia",
    "identity_algorithm_digest": "ia-d",
    "schema_version": "mm-run-v1",
    "carry_forward_run_ids": [],
    "mode_transition": "explicit_new_run",
}

FINDING = {
    "finding_id": "finding-001",
    "risk_id": "risk-001",
    "issue_id": "issue-001",
    "subject_id": "s7-subject-06021",
    "site_id": "s7-site-006",
    "scope_kind": "subject",
    "event_ref": "s7-event-001",
    "window_start": "2026-01-01",
    "window_end": "2026-03-31",
    "finding_state": "open",
    "basis": "方案要求报告不良事件",
    "finding": "受试者出现未记录的不良反应",
    "action": "请核实并补录",
    "evidence_refs": ["ev-listing-001"],
    "locator": {"path": "AE.AETERM", "record_id": "rec-001", "field": "AETERM"},
}


def _daily_outputs(findings, run_binding=None):
    binding = dict(RUN_BINDING)
    contract = mo.build_mode_contract("daily")
    entry_context = mo.default_entry_context_for_mode("daily", run_binding=binding)
    refs = {
        "project_id": binding["project_id"],
        "run_id": binding["run_id"],
        "data_cutoff": binding["data_cutoff"],
        "source_revision_id": binding["source_revision_id"],
        "authority_digest": "d" * 64,
        "coverage_digest": "d" * 64,
        "qc_digest": "d" * 64,
        "digest": "d" * 64,
    }
    return list(
        mo.build_daily_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            findings=list(findings),
            risks=[{"risk_id": "risk-001", "severity": "high"}],
            entry_context=entry_context,
        )
    )


def _affected_payload(findings):
    outputs = _daily_outputs(findings)
    return next(
        output["payload"]
        for output in outputs
        if output.get("output_kind") == "affected_query_draft"
    )


class _CloseStub:
    def close(self) -> None:
        return None


def _resolved_context(payload, artifact_id="art-affected-001"):
    return ResolvedResultContext(
        registry=_CloseStub(),
        entry=_CloseStub(),
        launch=None,
        publication=None,
        adapter=None,
        mode_outputs={
            "affected_query_draft": {"payload": payload},
        },
        mode_output_artifacts={"affected_query_draft": artifact_id},
    )


# ---------------------------------------------------------------------------
# A12：Finding DTO与QueryDraft独立schema、身份关联
# ---------------------------------------------------------------------------


def test_finding_dto_and_query_draft_are_separate_objects() -> None:
    payload = _affected_payload([FINDING])
    # 平行findings数组显式存在；QueryDraft保留自身ID并引用finding_id。
    assert isinstance(payload["findings"], list) and payload["findings"]
    assert isinstance(payload["query_drafts"], list) and payload["query_drafts"]
    assert payload["finding_count"] == len(payload["findings"])
    assert payload["draft_count"] == len(payload["query_drafts"])

    record = payload["findings"][0]
    # 稳定ID + subject/site。
    assert record["finding_id"] == "finding-001"
    assert record["subject_id"] == "s7-subject-06021"
    assert record["site_id"] == "s7-site-006"
    # 事件与时间窗。
    assert record["event_ref"] == "s7-event-001"
    assert record["window_start"] == "2026-01-01"
    assert record["window_end"] == "2026-03-31"
    # 状态。
    assert record["finding_state"] == "open"
    # 分类型claims（依据/发现/行动项）。
    assert [claim["kind"] for claim in record["claims"]] == [
        "basis",
        "finding",
        "action",
    ]
    assert [claim["text"] for claim in record["claims"]] == [
        "依据：方案要求报告不良事件。",
        "发现：受试者出现未记录的不良反应。",
        "行动项：请核实并补录。",
    ]
    # 逐条source refs + locator。
    assert record["source_refs"] == ["ev-listing-001"]
    assert record["locator"]["path"] == "AE.AETERM"

    draft = payload["query_drafts"][0]
    # QueryDraft独立身份，引用finding_id，但不冒充Finding（无claims）。
    assert draft["query_draft_id"].startswith("qd-")
    assert draft["finding_id"] == record["finding_id"]
    assert "claims" not in draft
    assert draft["draft_state"] == "draft"


def test_finding_dto_is_deterministic_and_content_addressed() -> None:
    first = _affected_payload([FINDING])["findings"]
    second = _affected_payload([FINDING])["findings"]
    assert first == second


def test_commit_rejects_query_draft_referencing_missing_finding(
    tmp_path: Path,
) -> None:
    from packages.medical_monitoring.reports.mode_output_core import (
        _query_draft_id,
    )

    outputs = _daily_outputs([FINDING])
    affected = next(
        output
        for output in outputs
        if output.get("output_kind") == "affected_query_draft"
    )
    payload = dict(affected["payload"])
    payload["query_drafts"] = [
        dict(draft, finding_id="finding-ghost") for draft in payload["query_drafts"]
    ]
    for draft in payload["query_drafts"]:
        # 保持query_draft_id自洽，专测finding引用关系这一道闸。
        draft["query_draft_id"] = _query_draft_id(draft)
    affected["payload"] = payload
    _reseal(affected)

    store = Store(tmp_path / "r1.sqlite3", tmp_path / "a1")
    try:
        with pytest.raises(Exception, match="AFFECTED_QUERY_DRAFT_PAYLOAD_INVALID"):
            cb.commit_mode_outputs(
                store,
                outputs,
                run_binding=dict(RUN_BINDING),
                r5_packet=None,
            )
    finally:
        store.close()


def test_commit_rejects_payload_without_findings_key(tmp_path: Path) -> None:
    outputs = _daily_outputs([FINDING])
    affected = next(
        output
        for output in outputs
        if output.get("output_kind") == "affected_query_draft"
    )
    affected["payload"] = {
        key: value
        for key, value in affected["payload"].items()
        if key not in ("findings", "finding_count")
    }
    _reseal(affected)

    store = Store(tmp_path / "r2.sqlite3", tmp_path / "a2")
    try:
        with pytest.raises(Exception, match="AFFECTED_QUERY_DRAFT_PAYLOAD_INVALID"):
            cb.commit_mode_outputs(
                store,
                outputs,
                run_binding=dict(RUN_BINDING),
                r5_packet=None,
            )
    finally:
        store.close()


def test_commit_accepts_dto_payload_and_historical_shape_rereads(
    tmp_path: Path,
) -> None:
    outputs = _daily_outputs([FINDING])
    store = Store(tmp_path / "r3.sqlite3", tmp_path / "a3")
    try:
        committed = cb.commit_mode_outputs(
            store,
            outputs,
            run_binding=dict(RUN_BINDING),
            r5_packet=None,
        )
        assert len(committed.artifact_member_ids) == 4
    finally:
        store.close()

    # pre-S3存量工件（仅query_drafts）重抽取保持原路径，不被新校验打断。
    affected = next(
        output
        for output in outputs
        if output.get("output_kind") == "affected_query_draft"
    )
    legacy_payload = {
        key: value
        for key, value in affected["payload"].items()
        if key not in ("findings", "finding_count")
    }
    legacy_output = dict(affected, payload=legacy_payload)
    atoms = cb.extract_atomic_items([legacy_output], mode="daily")
    assert any(atom.object_type == "query_draft" for atom in atoms)


# ---------------------------------------------------------------------------
# A13：零发现显式空集 + 读取侧不借query_drafts顶替
# ---------------------------------------------------------------------------


def test_zero_findings_payload_writes_explicit_empty_array() -> None:
    payload = _affected_payload([])
    assert payload["findings"] == []
    assert payload["finding_count"] == 0
    assert payload["query_drafts"] == []
    assert payload["draft_count"] == 0


def test_envelope_serves_finding_dto_rows_with_content_hash() -> None:
    payload = _affected_payload([FINDING])
    context = _resolved_context(payload, artifact_id="art-affected-001")
    envelope = context.public_findings_envelope()
    assert envelope["meta"]["payload_shape"] == "finding_dto_v1"
    assert envelope["meta"]["artifact"] == "art-affected-001"
    # content_sha256是真实载荷哈希，不再是artifact_id。
    assert envelope["meta"]["content_sha256"] == lr.content_digest(
        envelope["findings"]
    )
    assert envelope["meta"]["content_sha256"] != "art-affected-001"
    assert envelope["meta"]["total"] == 1
    assert envelope["findings"][0]["finding_id"] == "finding-001"
    assert envelope["query_drafts"][0]["finding_id"] == "finding-001"


def test_envelope_zero_findings_state_is_explicit() -> None:
    payload = _affected_payload([])
    context = _resolved_context(payload)
    envelope = context.public_findings_envelope()
    assert envelope["findings"] == []
    assert envelope["meta"]["state"] == "completed_no_findings"
    assert envelope["meta"]["payload_shape"] == "finding_dto_v1"
    assert envelope["meta"]["total"] == 0


def test_envelope_raises_when_payload_has_neither_findings_nor_drafts() -> None:
    # 新增失败反例：旧实现会把query_drafts换名为findings顶替；删除回退后，
    # 既无findings也无query_drafts的载荷必须明确result_context_unavailable。
    context = _resolved_context({"output_kind": "affected_query_draft"})
    with pytest.raises(ProductPublicationError) as excinfo:
        context.public_findings_envelope()
    assert excinfo.value.code == "result_context_unavailable"


def test_envelope_serves_legacy_payload_as_drafts_without_faking_dtos() -> None:
    # ⑤：旧token（S2冻结read model读出的pre-S3载荷）如实呈现——drafts以
    # 自身身份出现在query_drafts键下并标注legacy形态，findings不伪造。
    legacy_payload = {
        "output_kind": "affected_query_draft",
        "query_drafts": [
            {
                "query_draft_id": "qd-legacy-001",
                "finding_id": "finding-legacy",
                "display_text": "旧载荷草稿",
                "draft_state": "draft",
            }
        ],
        "draft_count": 1,
    }
    context = _resolved_context(legacy_payload, artifact_id="art-legacy-001")
    envelope = context.public_findings_envelope()
    assert envelope["meta"]["payload_shape"] == "legacy_query_drafts"
    assert envelope["findings"] == []  # 不伪造Finding DTO
    assert envelope["query_drafts"][0]["query_draft_id"] == "qd-legacy-001"
    assert envelope["meta"]["content_sha256"] == lr.content_digest(
        envelope["query_drafts"]
    )
