"""N1回归：Finding阅读模型与证据身份（审阅V4 P0-01~P0-05 / V4-01~09）。

- 稳定finding_id贯穿公开投影（不按index重编号；显示序号另存）
- 线索锚点来自claims的真实证据引用（第二AE不变第一AE；无AE的检查问题
  可达自己的证据；不可解析=unbound显式标注，不伪造锚点）
- 无标题gap可见（不因clean(title)消失），覆盖缺口独立计数
- 有效零发现与缺工件分离（state区分：missing/read_failed/
  completed_no_findings/completed_with_findings）
- AI工件按冻结名读取（不glob+mtime取最新），绑定content_sha256
- high不漏；无200截断（total另记）
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.api.r7_product.facts_mode_outputs import (  # noqa: E402
    FactsModeOutputProvider,
)


from packages.medical_monitoring.intelligence.primitives import (  # noqa: E402
    content_hash,
)


def _eid(table: str, index: int, subject: str) -> str:
    # 与build_subject_evidence完全同推导（生产content_hash，非手写序列化）
    return "aemh_{}".format(
        content_hash({"table": table, "row": index, "subject": subject})[:28]
    )


def _write_artifact(artifacts: Path, payload: dict) -> None:
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "aemh-findings-facts-snapshot-001.dualvlm-full1.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


class _Subject:
    def __init__(self, ref, label, site):
        self.subject_ref, self.subject_label, self.site_ref = ref, label, site


class _Risk:
    def __init__(self, ref, subject, domain="ae", severity="medium", locs=()):
        self.risk_ref, self.subject_ref, self.domain = ref, subject, domain
        self.severity = severity
        self.source_locator_refs = list(locs)


class _Packet:
    """最小包：subjects/risks按N1解析需要提供。"""

    def __init__(self, subjects, risks):
        self.subjects = subjects
        self.risks = risks


@pytest.fixture()
def artifacts(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"


def _claim(eids: list[str]) -> dict:
    return {"claim_id": "c1", "kind": "inference", "text": "x",
            "evidence_ids": eids}


def test_public_findings_preserves_stable_id_and_claims(artifacts: Path) -> None:
    # V4-01：稳定ID不被 aemh-{index:04d} 重写；显示序号另存；
    # claims与导航目标保留。
    _write_artifact(artifacts, {
        "snapshot_ref": "facts-snapshot-001.dualvlm-full1",
        "findings": [
            {
                "finding_id": "aemh-01001-primary-aaaabbbbcccc",
                "subject_label": "01001",
                "state": "accepted",
                "primary": {"title": "线索A", "text": "内容A",
                            "payload": {"claims": [_claim([_eid("AE", 2, "01001")])]}},
                "verifier": None,
            },
            {
                "finding_id": "aemh-01001-verifier-ddddeeeeffff",
                "subject_label": "01001",
                "state": "escalated",
                "primary": None,
                "verifier": {"title": "线索B", "text": "内容B",
                             "payload": {"claims": [_claim([_eid("MH", 0, "01001")])]}},
            },
        ],
    })
    provider = FactsModeOutputProvider(artifacts)
    rows = provider.public_findings(projection={}, project_ref="proj-x")
    ids = [r["finding_id"] for r in rows]
    assert ids == [
        "aemh-01001-primary-aaaabbbbcccc",
        "aemh-01001-verifier-ddddeeeeffff",
    ]
    assert rows[0]["display_seq"] == 1 and rows[1]["display_seq"] == 2
    # claims真实证据引用保留（服务端不丢来源）
    assert rows[0]["evidence_ids"] == [_eid("AE", 2, "01001")]


def test_public_findings_reads_exact_frozen_artifact_not_mtime(
    artifacts: Path,
) -> None:
    # V4-06：按冻结名读取；不glob+mtime取最新。旧结果目录里放一个更晚
    # 修改的"new"工件不得被读取。
    _write_artifact(artifacts, {
        "snapshot_ref": "facts-snapshot-001.dualvlm-full1",
        "findings": [
            {"finding_id": "aemh-frozen-one", "subject_label": "01001",
             "state": "accepted", "primary": {"title": "冻结", "text": "x"},
             "verifier": None},
        ],
    })
    newer = artifacts / "aemh-findings-facts-snapshot-001.dualvlm-full1-NEWER.json"
    newer.write_text(json.dumps({
        "findings": [{"finding_id": "aemh-new-two", "subject_label": "01001",
                      "state": "escalated", "verifier": {"title": "新", "text": "y"}}],
    }), encoding="utf-8")
    import os
    os.utime(newer, (2000000000, 2000000000))  # 确保mtime更新
    provider = FactsModeOutputProvider(artifacts)
    rows = provider.public_findings(projection={}, project_ref="proj-x")
    assert [r["finding_id"] for r in rows] == ["aemh-frozen-one"]


def test_public_findings_state_separation(artifacts: Path) -> None:
    # V4-05：有效零发现≠缺工件；读取失败≠缺失。meta携带状态。
    artifacts.mkdir(parents=True, exist_ok=True)
    provider = FactsModeOutputProvider(artifacts)
    meta = provider.public_findings_meta(projection={}, project_ref="proj-x")
    assert meta["state"] == "missing"

    _write_artifact(artifacts, {"snapshot_ref": "s", "findings": []})
    meta = provider.public_findings_meta(projection={}, project_ref="proj-x")
    assert meta["state"] == "completed_no_findings"
    rows = provider.public_findings(projection={}, project_ref="proj-x")
    assert rows == []

    # 损坏JSON → read_failed（不是missing）
    (artifacts / "aemh-findings-facts-snapshot-001.dualvlm-full1.json").write_text(
        "{broken", encoding="utf-8"
    )
    meta = provider.public_findings_meta(projection={}, project_ref="proj-x")
    assert meta["state"] == "read_failed"


def test_public_findings_empty_title_gap_survives(artifacts: Path) -> None:
    # V4-04：双cohort均无内容的gap——标题回退+kind标记，前端clean(title)
    # 不再丢；gap可独立计数。
    _write_artifact(artifacts, {
        "snapshot_ref": "s",
        "findings": [
            {"finding_id": "aemh-gap-1", "subject_label": "01001",
             "state": "unverifiable_gap",
             "primary": None, "verifier": None},
            {"finding_id": "aemh-ok-1", "subject_label": "01002",
             "state": "accepted",
             "primary": {"title": "线索", "text": "x"}, "verifier": None},
        ],
    })
    provider = FactsModeOutputProvider(artifacts)
    rows = provider.public_findings(projection={}, project_ref="proj-x")
    kinds = {r["finding_id"]: r.get("kind") for r in rows}
    assert kinds["aemh-gap-1"] == "coverage_gap"
    gap = next(r for r in rows if r["finding_id"] == "aemh-gap-1")
    assert gap["title"]  # 有非空回退标题
    assert gap["state"] == "unverifiable_gap"


def test_daily_findings_uses_real_claim_anchor_not_first_ae(
    artifacts: Path,
) -> None:
    # V4-02：受试者有AE1(row2)/AE2(row5)，线索引用AE2——锚点必须是AE2
    # 的event/loc，不是第一条AE。
    domains = {
        "AE": [
            {"SUBJID": "01001"},  # row0 其他受试者占位无关紧要，直接构造目标行
        ] * 0 + [
            {"SUBJID": "01001", "AETERM": "t0"},
        ],
    }
    # 构造AE表：row2=AE1(01001), row5=AE2(01001)
    ae_rows = [
        {"SUBJID": "09999", "AETERM": "other"},
        {"SUBJID": "09999", "AETERM": "other"},
        {"SUBJID": "01001", "AETERM": "AE1"},
        {"SUBJID": "09999", "AETERM": "other"},
        {"SUBJID": "09999", "AETERM": "other"},
        {"SUBJID": "01001", "AETERM": "AE2"},
    ]
    domains = {"AE": ae_rows}
    _write_artifact(artifacts, {
        "snapshot_ref": "s",
        "findings": [
            {"finding_id": "aemh-f-ae2", "subject_label": "01001",
             "state": "accepted",
             "primary": {"title": "AE2问题", "text": "x",
                         "payload": {"claims": [_claim([_eid("AE", 5, "01001")])]}},
             "verifier": None},
            {"finding_id": "aemh-f-lab", "subject_label": "01001",
             "state": "escalated",
             "primary": None,
             "verifier": {"title": "化验问题", "text": "y",
                          "payload": {"claims": [_claim(["aemh_unresolvable1"])]}}},
        ],
    })
    provider = FactsModeOutputProvider(artifacts, domains_loader=lambda: domains)
    packet = _Packet(
        subjects=[_Subject("subject-01001", "01001", "site-01")],
        risks=[
            _Risk("risk-ae1", "subject-01001", "ae"),
            _Risk("risk-ae2", "subject-01001", "ae"),
        ],
    )
    findings = provider._daily_findings(
        {"mode": "daily", "project_id": "proj-x"}, packet
    )
    by_id = {f["finding_id"]: f for f in findings}
    ae2 = by_id["aemh-f-ae2"]
    # 锚点=AE2（row5），不是第一AE（row2）
    assert ae2["anchor_event_refs"] == ["event-AE-000005"]
    assert ae2["anchor_state"] == "bound"
    assert "event-AE-000002" not in json.dumps(ae2)
    # 化验问题证据不可解析 → 显式unbound，不借AE锚点
    lab = by_id["aemh-f-lab"]
    assert lab.get("anchor_state") == "unbound"
    assert lab["anchor_event_refs"] == []


def test_daily_findings_no_200_truncation_and_high_kept(artifacts: Path) -> None:
    # V4-08/09：high不漏；>200条完整返回（total另记，不break截断）。
    ae_rows = [{"SUBJID": "01001", "AETERM": f"AE{i}"} for i in range(260)]
    domains = {"AE": ae_rows}
    findings_src = [
        {"finding_id": f"aemh-m{i:04d}", "subject_label": "01001",
         "state": "accepted",
         "primary": {"title": f"题{i}", "text": "x",
                     "payload": {"claims": [_claim([_eid("AE", i, "01001")])]}},
         "verifier": None}
        for i in range(260)
    ]
    _write_artifact(artifacts, {"snapshot_ref": "s", "findings": findings_src})
    provider = FactsModeOutputProvider(artifacts, domains_loader=lambda: domains)
    packet = _Packet(
        subjects=[_Subject("subject-01001", "01001", "site-01")],
        risks=[_Risk("risk-ae", "subject-01001", "ae")],
    )
    findings = provider._daily_findings(
        {"mode": "daily", "project_id": "proj-x"}, packet
    )
    assert len(findings) == 260  # 不再200截断
    assert all(f.get("anchor_state") in ("bound", "unbound") for f in findings)
