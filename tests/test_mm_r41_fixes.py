"""R41轮修复回归：六条修复的关键契约。

- R41-01：阻断组可处置载荷——_public_draft 公开投影必须携带
  finding_groups 的 rule_id/affected_fields（前端逐字段角色修订入口的
  数据源），G-ROLE-002 组随组携带闭合目录角色候选；
- R39-04收口①：「AE严重度vs化验矛盾」风险行必须把被引用化验原始行
  加入 source_locator_refs（发现卡引用的化验值可一跳回看）；
- R39-04收口③：来源证据定位符直读——无风险绑定的事件（量表/检验）
  按 source_locator_ref 即可出示来源证据信封，风险语义为空；
- R34-11：量表数值序列按量表名归并（UAS7跨周趋势一条序列，按日期
  排序），不再逐周各成单点指标。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_facts_publication_event_time import (  # noqa: E402
    _workspace,
)
from packages.medical_monitoring.projections.facts_publication import (  # noqa: E402
    FactsPublicationAuthorityProvider,
)
from packages.medical_monitoring.projections.product_adapter import (  # noqa: E402
    R5ProductAdapter,
)


def _csu_style_tables() -> dict[str, list[dict]]:
    """最小CSU形态数据：AE≥3级+同指标化验无降幅（矛盾发现）+UAS周分值。"""

    return {
        "AE": [
            {
                "SUBJID": "23003",
                "AETERM": "血小板减少",
                "AESEV": "3级",
                "AESTDAT": "2026-04-02",
                "AEREL": "可能有关",
            },
        ],
        # 4次血小板检测均未达到3级降幅（未低于参考下限60%）→矛盾提示。
        "LB_HEM": [
            {
                "SUBJID": "23003",
                "LBTEST": "血小板计数",
                "LBORRES": "180",
                "LBREF": "125-350",
                "LBUNIT": "10^9/L",
                "VISIT": "W2",
                "LBDAT": "2026-03-29",
            },
            {
                "SUBJID": "23003",
                "LBTEST": "血小板计数",
                "LBORRES": "175",
                "LBREF": "125-350",
                "LBUNIT": "10^9/L",
                "VISIT": "W4",
                "LBDAT": "2026-04-12",
            },
            {
                "SUBJID": "23003",
                "LBTEST": "血小板计数",
                "LBORRES": "168",
                "LBREF": "125-350",
                "LBUNIT": "10^9/L",
                "VISIT": "W8",
                "LBDAT": "2026-05-10",
            },
            {
                "SUBJID": "23003",
                "LBTEST": "血小板计数",
                "LBORRES": "172",
                "LBREF": "125-350",
                "LBUNIT": "10^9/L",
                "VISIT": "W12",
                "LBDAT": "2026-06-07",
            },
        ],
        "UAS": [
            {
                "SUBJID": "23003",
                "UASW2": "6",
                "UASW4": "9",
                "UASW8": "4",
                "UASW12": "2",
            },
        ],
        "SV": [
            {"SUBJID": "23003", "VISIT": "W2", "VISDAT": "2026-03-29"},
            {"SUBJID": "23003", "VISIT": "W4", "VISDAT": "2026-04-12"},
            {"SUBJID": "23003", "VISIT": "W8", "VISDAT": "2026-05-10"},
            {"SUBJID": "23003", "VISIT": "W12", "VISDAT": "2026-06-07"},
        ],
    }


def _packet(tables: dict[str, list[dict]], tmp_path: Path):
    workspace = _workspace(tmp_path, tables)
    return FactsPublicationAuthorityProvider(workspace).get_packet(
        "proj-r41", snapshot_ref="facts-snapshot-001"
    )


# --- R39-04收口①：化验矛盾发现绑定被引用的化验行 -------------------------
def test_ae_lab_contradiction_binds_lab_row_locators(tmp_path: Path) -> None:
    packet = _packet(_csu_style_tables(), tmp_path)
    ae_risks = [
        item
        for item in packet.risks
        if item.domain == "ae" and "化验趋势存在矛盾" in (item.medical_note or "")
    ]
    assert ae_risks, "AE≥3级且同指标化验无降幅时应产出矛盾提示"
    risk = ae_risks[0]
    ae_locators = [ref for ref in risk.source_locator_refs if "AE" in ref]
    lab_locators = [ref for ref in risk.source_locator_refs if "LB" in ref]
    assert len(ae_locators) == 1, "AE行定位保留"
    # 矛盾提示引用4次血小板检测——4个化验原始行都必须可回看。
    assert len(lab_locators) == 4, (
        f"矛盾发现应绑定4条化验行定位，实得 {risk.source_locator_refs}"
    )
    locator_refs = {item.locator_ref for item in packet.sources}
    assert set(lab_locators) <= locator_refs, "化验定位必须已在来源台账登记"


# --- R34-11：量表跨周趋势归并为一条序列 ----------------------------------
def test_scale_indicators_merge_weekly_points_into_one_series(tmp_path: Path) -> None:
    from packages.medical_monitoring.projections.product_projection_helpers import (
        _indicator_payloads,
    )

    packet = _packet(_csu_style_tables(), tmp_path)
    payload = _indicator_payloads(packet, events=packet.events, risks=packet.risks)
    scale_indicators = [
        item
        for item in payload
        if str(item.get("indicator_ref", "")).startswith("r5-indicator-scale-value-")
    ]
    assert len(scale_indicators) == 1, (
        "UAS7四个周分值应归并为一条量表指标序列，"
        f"实得 {len(scale_indicators)} 条："
        f"{[item.get('label') for item in scale_indicators]}"
    )
    indicator = scale_indicators[0]
    assert indicator["label"] == "UAS7量表"
    values = [point["value"] for point in indicator["points"]]
    assert values == [6, 9, 4, 2], f"各周分值按日期升序为序列点，实得 {values}"
    assert indicator["unit"] == "分"


# --- R41-01：阻断组公开投影携带可处置载荷 --------------------------------
def test_public_draft_projection_keeps_affected_fields_and_role_catalog() -> None:
    from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
        _public_draft,
    )

    quality = {
        "status": "blocked",
        "activation_disposition": "reject",
        "global_blocker_count": 1,
        "capability_blocker_count": 0,
        "warning_count": 0,
        "finding_groups": [
            {
                "finding_group_id": "semfg_abc",
                "rule_id": "G-ROLE-002",
                "severity": "global_blocker",
                "title_zh": "核心角色未进入闭合目录",
                "summary_zh": "应选择目录角色或保持未映射",
                "affected_fields": [
                    {
                        "domain": "EX",
                        "source_field": "EXTRT",
                        "role_concept_id": "unresolved",
                    },
                ],
                "affected_capability_ids": [],
            },
        ],
        "capability_states": [],
    }
    public = _public_draft({
        "draft_id": "monmapd_1",
        "version": 2,
        "status": "draft",
        "facts_generated": False,
        "fields": [],
        "user_questions": [],
        "semantic_quality": quality,
        "review_summary": {},
    })
    projected_quality = public["semantic_quality"]
    groups = projected_quality["finding_groups"]
    assert groups and groups[0]["rule_id"] == "G-ROLE-002"
    assert groups[0]["affected_fields"] == [
        {"domain": "EX", "source_field": "EXTRT", "role_concept_id": "unresolved"},
    ]
    # G-ROLE-002 阻断组必须随组携带目录角色候选（前端datalist数据源）。
    catalog = projected_quality.get("role_catalog") or []
    assert catalog, "G-ROLE-002 组应随组下发闭合目录角色候选"
    assert any(
        item.get("role_concept_id") == "metadata.subject_id" for item in catalog
    )
    # 非角色阻断组不带目录（投影按需携带，不无谓膨胀载荷）。
    quality["finding_groups"][0]["rule_id"] = "G-COVER-001"
    public_plain = _public_draft({
        "draft_id": "monmapd_1",
        "version": 2,
        "status": "draft",
        "facts_generated": False,
        "fields": [],
        "user_questions": [],
        "semantic_quality": quality,
        "review_summary": {},
    })
    assert "role_catalog" not in public_plain["semantic_quality"]


# --- R39-04收口③：定位符直读来源证据（无风险绑定事件） -------------------
def test_source_evidence_by_locator_only(tmp_path: Path) -> None:
    packet = _packet(_csu_style_tables(), tmp_path)
    adapter = R5ProductAdapter(
        lambda project_ref, run_ref=None, snapshot_ref=None, cutoff_ref=None: packet
    )
    scale_event = next(
        (item for item in packet.events if item.subtype == "scale"),
        None,
    )
    assert scale_event is not None and scale_event.source_locator_refs, (
        "量表周分值事件应携带来源定位（with_risk=False 无风险行）"
    )
    locator = scale_event.source_locator_refs[0]
    result = adapter.source_evidence(
        project_ref="proj-r41",
        run_ref="run-facts-001",
        snapshot_ref="facts-snapshot-001",
        cutoff_ref=None,
        source_locator_ref=locator,
    )
    projection = result["projection"]
    assert projection["kind"] == "source_evidence"
    assert projection["source_locator_ref"] == locator
    assert projection["risk_ref"] == "" and projection["risk_instance_ref"] == ""
    identity = result["identity"]
    assert identity["source_locator_ref"] == locator
    assert identity["subject_ref"] == "subject-23003"
    assert identity["view"] == "evidence"
    assert len(result["source_refs"]) == 1
    # 风险绑定语义保持不变：带风险实例+匹配定位仍可读；错配拒绝。
    ae_risk = next(item for item in packet.risks if item.domain == "ae")
    bound = adapter.source_evidence(
        project_ref="proj-r41",
        run_ref="run-facts-001",
        snapshot_ref="facts-snapshot-001",
        cutoff_ref=None,
        risk_instance_ref=ae_risk.risk_instance_ref,
        source_locator_ref=ae_risk.source_locator_refs[0],
    )
    assert bound["projection"]["risk_instance_ref"] == ae_risk.risk_instance_ref
    from packages.medical_monitoring.projections.product_types import (
        R5ProductAdapterError,
    )

    try:
        adapter.source_evidence(
            project_ref="proj-r41",
            run_ref="run-facts-001",
            snapshot_ref="facts-snapshot-001",
            cutoff_ref=None,
            source_locator_ref="loc-does-not-exist",
        )
    except R5ProductAdapterError:
        pass
    else:
        raise AssertionError("不存在的定位符必须拒绝（fail-closed）")
