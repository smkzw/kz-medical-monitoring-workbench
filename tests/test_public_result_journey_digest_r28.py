"""R28-01（20261009）：种子→运行→发布→结果→受试者医学旅程整链集成测试。

背景（R26/R28两轮7/7复现「当前内容暂不可用」，旅程页死链）：
前端对结果信封做 JSON.parse→JSON.stringify 规范化后重算 SHA-256 与
response_digest 比对。事实层把 UAS7 周分值 float("12")=12.0 写入 packet，
Python json.dumps(12.0)="12.0" 而前端 JSON.stringify(12.0)="12"——两侧摘要
字节必然不一致，public_response_digest_mismatch 把所有含量表数值的结果视图
（旅程/概览/证据）全部拒绝。

本文件三层断言：
1. 事实层解析：整值周分值保持 int（新冻结数据即规范）；
2. 读取链（旧冻结数据兜底）：packet 内已存在的 12.0 浮点在 payload 构建
   时规范为 int（MX循开考-CSU 存量发布无需重跑监查即修复）；
3. 整链：种子（含 UAS 量表周分值）→prepare-and-start→publication→
   result-entry→subjects 旅程载荷——载荷非空、无浮点、且 response_digest
   在 JS 序列化语义（json.loads 后规范化重算）下逐字节可复算。

0模型调用，全部离线。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import pytest

from packages.medical_monitoring.projections.facts_publication import (
    FactsPublicationAuthorityProvider,
    _atomic_write_json,
    _build_facts_manifest,
)
from packages.medical_monitoring.projections.product_adapter import (
    R5ProductAdapter,
)
from packages.medical_monitoring.projections.product_fixture_records import (
    base_records_from_fixture,
)
from packages.medical_monitoring.projections.product_types import (
    SYNTHETIC_FIXTURE_MODE,
    R5AuthorityPacket,
    R5EventRecord,
    canonical_sha256,
)

PROJECT = "s7-synthetic-r28-journey"
SNAPSHOT = "s7-snapshot-current-001"


def _js_semantics_digest(envelope: Mapping[str, Any]) -> str:
    """以浏览器语义复算 response_digest。

    前端：JSON.parse(响应) 后对 {identity, projection} 递归排序键、
    JSON.stringify 紧凑序列化、SHA-256。Python 侧等价实现：json.loads
    （int/float 语义与 JSON.parse 一致）→ 规范化 → json.dumps(
    ensure_ascii=False, sort_keys=True, separators=(",",":"))。
    若 payload 仍含 12.0 浮点，dumps 输出 "12.0" 而浏览器输出 "12"，
    本函数与后端摘要必然不等——正是修复前死链的复现点。
    """

    parsed = json.loads(
        json.dumps(
            {
                "identity": envelope["identity"],
                "projection": envelope["projection"],
            },
            ensure_ascii=False,
        )
    )

    def canonicalize(value: Any) -> Any:
        if isinstance(value, list):
            return [canonicalize(item) for item in value]
        if isinstance(value, dict):
            return {key: canonicalize(value[key]) for key in sorted(value)}
        return value

    blob = json.dumps(
        canonicalize(parsed), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _assert_no_floats(value: Any, path: str = "") -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, float):
        raise AssertionError(f"payload 含浮点（JS侧序列化必然分叉）: {path} = {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_floats(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_floats(item, f"{path}[{index}]")


# ---------------------------------------------------------------------------
# 1. 事实层：量表周分值整值保持 int
# ---------------------------------------------------------------------------


def test_scale_week_integral_values_parse_as_int_not_float() -> None:
    rows = [
        {
            "SUBJID": "21001",
            "SITEID": "06",
            "UASW2": "12",
            "UASW4": "7",
            "UASW8": "16",
        }
    ]
    # 直接走事实层 provider：解析临时表并检查量表事件数值。
    # （附一张AE行：product packet要求risks非空，量表事件with_risk=False。）
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        artifacts = Path(tmp) / "runtime" / "artifacts"
        artifacts.mkdir(parents=True)
        allowed_files = []
        for table in (
            {
                "AE": [
                    {
                        "SUBJID": "21001",
                        "SITEID": "06",
                        "SITENM": "中心06",
                        "AETERM": "鼻咽炎",
                        "AESEV": "轻度",
                        "AESTDAT": "2026-01-10",
                    }
                ]
            },
            {"UAS": rows},
        ):
            encoded = json.dumps(table, ensure_ascii=False, sort_keys=True).encode()
            name = hashlib.sha256(encoded).hexdigest() + ".json"
            (artifacts / name).write_bytes(encoded)
            allowed_files.append(name)
        _atomic_write_json(
            artifacts / "facts-manifest.json",
            _build_facts_manifest(
                artifacts,
                allowed_files=allowed_files,
                project_id=PROJECT,
                attempt_id="attempt-r28",
                mapping_version="map-r28",
                snapshot_ref=SNAPSHOT,
            ),
        )
        provider = FactsPublicationAuthorityProvider(
            Path(tmp), project_ref=PROJECT, project_label="R28旅程整链"
        )
        packet = provider.get_packet(
            PROJECT, "run-r28-producer", SNAPSHOT, "2026-03-31"
        )
    events = [
        event
        for event in packet.events
        if event.subtype == "scale" and event.measure_value is not None
    ]
    assert events, "UAS 周分值应展开为量表数值事件"
    values = {event.measure_value for event in events}
    assert values == {12, 7, 16}, f"周分值应保持整数: {values!r}"
    for event in events:
        assert isinstance(event.measure_value, int), (
            f"measure_value 应为 int（float会让前端摘要复算失败）: {event!r}"
        )


# ---------------------------------------------------------------------------
# 2. 读取链：旧冻结数据里的 12.0 浮点在 payload 构建时规范为 int
# ---------------------------------------------------------------------------


def _packet_with_float_measure_event() -> tuple[Any, str, str, str]:
    """构造一个 measure_value=12.0（修复前冻结形态）的packet。"""

    from datetime import date

    (
        sources,
        sites,
        subjects,
        _events,
        visits,
        risks,
        _histories,
    ) = base_records_from_fixture(SNAPSHOT)
    subject = subjects[0]
    event = R5EventRecord(
        event_ref="event-UAS-000000-UASW2",
        subject_ref=subject.subject_ref,
        site_ref=subject.site_ref,
        spine_ref=subject.spine_ref,
        domain="symptom_efficacy",
        subtype="scale",
        date_state="exact",
        start_date=date(2026, 2, 1),
        end_date=None,
        visit_ref=None,
        risk_anchor_refs=(),
        source_locator_refs=(sources[0].locator_ref,),
        label_zh="UAS7量表·第2周=12",
        measure_value=12.0,
        measure_label="UAS7量表（第2周）",
    )
    packet = R5AuthorityPacket(
        project_ref=PROJECT,
        run_ref="run-r28-read",
        snapshot_ref=SNAPSHOT,
        cutoff_state="present",
        cutoff_ref="2026-03-31",
        project_label="R28旅程整链",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version="2026-08-26.1",
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id=f"s7-visibility:{SNAPSHOT}",
        visibility_decision_hash=canonical_sha256(
            {"snapshot_ref": SNAPSHOT, "projectable": True, "source_count": len(sources)}
        ),
        evaluation_content_identities=(
            canonical_sha256({"snapshot_ref": SNAPSHOT, "kind": "evaluation"}),
        ),
        source_revision_content_pairs=tuple(),
        sources=sources,
        sites=sites,
        subjects=subjects,
        events=(event, *_events),
        visits=visits,
        risks=risks,
        histories=(),
        synthetic=True,
        data_mode=SYNTHETIC_FIXTURE_MODE,
    )
    return packet, subject.subject_ref, subject.site_ref, subject.spine_ref


def test_legacy_frozen_float_measure_normalized_on_read_path() -> None:
    from datetime import date

    packet, subject_ref, site_ref, spine_ref = _packet_with_float_measure_event()
    assert packet.events[0].measure_value == 12.0
    assert isinstance(packet.events[0].measure_value, float)
    adapter = R5ProductAdapter(lambda *args, **kwargs: packet)
    workspace = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref=subject_ref,
        run_ref="run-r28-read",
        snapshot_ref=SNAPSHOT,
        cutoff_ref="2026-03-31",
        site_ref=site_ref,
        spine_ref=spine_ref,
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
    )
    projection = workspace["projection"]
    _assert_no_floats(projection, "projection")
    spine = projection["temporal_spine"]
    measure_events = [
        event
        for event in spine["events"]
        if event.get("measure_value") is not None
    ]
    assert measure_events, "旅程时间轴应携带量表数值事件"
    for event in measure_events:
        assert event["measure_value"] == 12
        assert isinstance(event["measure_value"], int), (
            "旧冻结浮点在读取链必须规范为 int"
        )


# ---------------------------------------------------------------------------
# 3. 整链：种子→运行→发布→结果→旅程载荷非空且摘要JS可复算
# ---------------------------------------------------------------------------


def test_journey_payload_full_chain_digest_matches_js_semantics(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod
    from packages.medical_monitoring.api.r7_product.facts_mode_outputs import (
        FactsModeOutputDispatcher,
    )
    from packages.medical_monitoring.api.r7_product.facts_publication_adapter import (
        FactsPublicationAdapter,
        FactsProviderDispatcher,
    )
    from packages.medical_monitoring.api.r7_product.synthetic_publication import (
        SyntheticModeOutputProvider,
    )
    from packages.medical_monitoring.runtime import run_setup as rs
    from tests.test_medical_monitoring_r7_product_router import (
        PROJECT_A,
        _base,
        _client,
        _principal,
        _wait_product_launch_completed,
    )

    provider_root = tmp_path / "r28-providers"
    project = PROJECT_A
    artifacts = provider_root / project / "runtime" / "artifacts"
    artifacts.mkdir(parents=True)

    def materialize(table: dict[str, list[dict[str, Any]]]) -> str:
        encoded = json.dumps(table, ensure_ascii=False, sort_keys=True).encode()
        name = hashlib.sha256(encoded).hexdigest() + ".json"
        (artifacts / name).write_bytes(encoded)
        return name

    allowed_files = [
        materialize(
            {
                "AE": [
                    {
                        "SUBJID": "21001",
                        "SITEID": "06",
                        "SITENM": "中心06",
                        "AETERM": "鼻咽炎",
                        "AESEV": "轻度",
                        "AESTDAT": "2026-01-10",
                    }
                ]
            }
        ),
        materialize(
            {
                "UAS": [
                    {
                        "SUBJID": "21001",
                        "SITEID": "06",
                        "UASW2": "12",
                        "UASW4": "7",
                    }
                ]
            }
        ),
    ]
    _atomic_write_json(
        artifacts / "facts-manifest.json",
        _build_facts_manifest(
            artifacts,
            allowed_files=allowed_files,
            project_id=project,
            attempt_id="attempt-r28-chain",
            mapping_version="map-r28",
            snapshot_ref=SNAPSHOT,
        ),
    )

    from packages.medical_monitoring.runtime import run_setup as rs
    from tests.test_medical_monitoring_r7_product_router import (
        PROJECT_A,
        _base,
        _client,
        _principal,
        _wait_product_launch_completed,
    )

    def setup_inputs(canonical_project_id: str):
        current = rs.DataSnapshot(
            snapshot_ref=SNAPSHOT,
            project_id=canonical_project_id,
            data_cutoff="2026-03-31",
            rows=(
                {
                    "canonical_key": "site-06/21001",
                    "site_ref": "site-06",
                    "subject_ref": "subject-21001",
                },
            ),
            key_fields=("canonical_key",),
            source_revision_id="source-r28",
        )
        return (current,), ()

    monkeypatch.setattr(product_mod, "_synthetic_setup_inputs", setup_inputs)

    client = _client(
        tmp_path,
        principal=_principal(project),
        authority_provider=FactsProviderDispatcher(
            {},
            provider_factory=lambda canonical: FactsPublicationAdapter(
                FactsPublicationAuthorityProvider(
                    provider_root / canonical,
                    project_ref=canonical,
                    project_label="R28旅程整链",
                )
            ),
        ),
        r6_output_provider=FactsModeOutputDispatcher(
            {}, provider_factory=lambda canonical: SyntheticModeOutputProvider()
        ),
    )

    assert client.post(f"{_base(project)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(project)}/run-setup/options")
    assert options.status_code == 200, options.text
    launched = client.post(
        f"{_base(project)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options.json()["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "r28-journey-chain-001",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, project, public_token)

    published = client.post(
        f"{_base(project)}/runs/{public_token}/publication",
        json={"idempotency_key": "r28-journey-publication-001"},
    )
    assert published.status_code == 200, published.text
    entry = client.get(f"{_base(project)}/runs/{public_token}/result-entry")
    assert entry.status_code == 200, entry.text
    result_token = entry.json()["result_context_token"]

    overview = client.get(f"{_base(project)}/results/{result_token}/overview")
    assert overview.status_code == 200, overview.text
    overview_envelope = overview.json()
    subjects = overview_envelope["projection"]["subjects"]
    assert subjects, "结果概览应提供受试者行（旅程入口）"
    target = subjects[0]

    journey = client.get(
        f"{_base(project)}/results/{result_token}/subjects/{target['subject_ref']}",
        params={
            "site_ref": target["site_ref"],
            "spine_ref": target["spine_ref"],
            "window_start": "2026-01-01",
            "window_end": "2026-03-31",
        },
    )
    assert journey.status_code == 200, journey.text
    envelope = journey.json()
    assert envelope["identity"]["view"] == "journey"
    projection = envelope["projection"]

    # 载荷非空：时间轴事件+风险锚点必须真实存在（此前死链=空壳或拒收）。
    spine = projection["temporal_spine"]
    assert spine["events"], "受试者医学旅程时间轴事件不得为空"
    assert spine["risk_anchors"], "受试者医学旅程风险锚点不得为空"
    measure_events = [
        event for event in spine["events"] if event.get("measure_value") is not None
    ]
    assert measure_events, "UAS 周分值应随事件透传到旅程页"
    for event in measure_events:
        assert isinstance(event["measure_value"], int)

    # 摘要契约：response_digest 必须在 JS 序列化语义下逐字节可复算。
    _assert_no_floats(envelope["identity"], "identity")
    _assert_no_floats(projection, "projection")
    assert _js_semantics_digest(envelope) == envelope["response_digest"], (
        "前端 JSON.parse→JSON.stringify 复算摘要必须与后端一致——"
        "不一致即旅程页验签必败（R28-01死链根因）"
    )

    # 指标趋势：量表数值序列点位同样非空且为整值。
    indicators = projection.get("indicators") or []
    value_indicators = [
        item
        for item in indicators
        if item.get("value_kind") == "scale_measure_value"
    ]
    assert value_indicators, "量表数值序列指标应存在（UAS7趋势）"
    for indicator in value_indicators:
        assert indicator["points"], "量表指标点位不得为空"
        for point in indicator["points"]:
            if point["value"] is not None:
                assert isinstance(point["value"], int)


# ---------------------------------------------------------------------------
# R28-07：AESER=是的AE风险必须带结构化serious位（SAE标识与置顶的依据）
# ---------------------------------------------------------------------------


def test_ae_aeser_yes_marks_risk_serious_and_surfaces_in_payload() -> None:
    import tempfile
    from datetime import date
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        artifacts = Path(tmp) / "runtime" / "artifacts"
        artifacts.mkdir(parents=True)
        allowed_files = []
        for table in (
            {
                "AE": [
                    {
                        "SUBJID": "23003",
                        "SITEID": "06",
                        "SITENM": "中心06",
                        "AETERM": "血小板计数降低",
                        "AESEV": "3级",
                        "AESER": "是",
                        "AEREL": "可能有关",
                        "AEOUT": "未愈",
                        "AESTDAT": "2026-02-01",
                    },
                    {
                        "SUBJID": "23011",
                        "SITEID": "06",
                        "SITENM": "中心06",
                        "AETERM": "鼻咽炎",
                        "AESEV": "3级",
                        "AESER": "否",
                        "AEREL": "肯定无关",
                        "AEOUT": "已痊愈",
                        "AESTDAT": "2026-02-05",
                    },
                ]
            },
        ):
            encoded = json.dumps(table, ensure_ascii=False, sort_keys=True).encode()
            name = hashlib.sha256(encoded).hexdigest() + ".json"
            (artifacts / name).write_bytes(encoded)
            allowed_files.append(name)
        _atomic_write_json(
            artifacts / "facts-manifest.json",
            _build_facts_manifest(
                artifacts,
                allowed_files=allowed_files,
                project_id=PROJECT,
                attempt_id="attempt-r28-sae",
                mapping_version="map-r28",
                snapshot_ref=SNAPSHOT,
            ),
        )
        provider = FactsPublicationAuthorityProvider(
            Path(tmp), project_ref=PROJECT, project_label="R28旅程整链"
        )
        packet = provider.get_packet(
            PROJECT, "run-r28-sae", SNAPSHOT, "2026-03-31"
        )
    ae_risks = [risk for risk in packet.risks if risk.domain == "ae"]
    assert len(ae_risks) == 2
    serious_flags = {risk.serious for risk in ae_risks}
    assert serious_flags == {True, False}, "AESER=是→serious=True；AESER=否→serious=False"
    serious = next(risk for risk in ae_risks if risk.serious)
    not_serious = next(risk for risk in ae_risks if not risk.serious)
    assert serious.subject_ref == "subject-23003"
    assert not_serious.subject_ref == "subject-23011"
    # 同为3级：两者severity相同——serious位是唯一区分，证明此前
    # SAE被等级映射淹没的结构性缺口。
    assert serious.severity == not_serious.severity == "high"

    # payload：读取链必须透出serious（前端徽章/置顶的合同依据）。
    # （facts provider固定run_ref="run-facts-001"，适配器按包身份取包。）
    adapter = R5ProductAdapter(lambda *args, **kwargs: packet)
    subject = packet.subjects[0]
    workspace = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref=subject.subject_ref,
        run_ref=packet.run_ref,
        snapshot_ref=packet.snapshot_ref,
        cutoff_ref=packet.cutoff_ref,
        site_ref=subject.site_ref,
        spine_ref=subject.spine_ref,
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
    )
    anchors = workspace["projection"]["temporal_spine"]["risk_anchors"]
    serious_payload = [item for item in anchors if item.get("serious") is True]
    assert serious_payload, "risk_anchors必须携带serious=true的SAE行"
    assert all(
        isinstance(item.get("serious"), bool) for item in anchors
    ), "serious必须是布尔位（缺省False），前端据此渲染SAE徽章"
