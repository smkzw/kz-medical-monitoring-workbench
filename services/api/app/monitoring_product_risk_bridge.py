"""R24轮（R24-05）：r7产品发布链 → 医学风险快照桥。

产品循环（数据接入→运行→发布）的 R5 publication packet 此前只落 frozen
read model（结果视图可看），从不写入 ``medical_risk_repository``——总看板
风险摘要、模块开放风险数、统一工作收件箱读到的都是空库，与已发布监查
结果（如18条运行、29条开放风险）直接矛盾。发布成功后把 packet 风险桥接
为 RiskCase 快照，使聚合面（总看板/收件箱/风险摘要）与结果视图同源。

桥接是确定性的：同一 packet、同一 run 创建时间重建出的 RiskCase 列表
逐字节一致（发布重放幂等的前提）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.contracts.workbench_contracts.models import (
    RiskCase,
    RiskSeverity,
    RiskStatus,
)

# 产品发布链的风险快照引擎标识（与 legacy daily-run 规则链区分）。
PRODUCT_RISK_ENGINE_VERSION = "r7-product-publication-v1"

_SEVERITY_MAP = {
    "critical": RiskSeverity.CRITICAL,
    "high": RiskSeverity.HIGH,
    "medium": RiskSeverity.MEDIUM,
    "low": RiskSeverity.LOW,
}


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix):] if value.startswith(prefix) else value


def _canonical_locations(packet: Any) -> dict[str, str]:
    """locator_ref → canonical_location（如 ``AE!row19``）映射。"""

    locations: dict[str, str] = {}
    for source in getattr(packet, "sources", ()) or ():
        locator_ref = str(getattr(source, "locator_ref", "") or "")
        canonical = str(getattr(source, "canonical_location", "") or "")
        if locator_ref and canonical:
            locations[locator_ref] = canonical
    return locations


def product_packet_risk_cases(
    packet: Any,
    *,
    project_id: str,
    source_revision: str,
    rule_profile_revision: str,
    engine_version: str = PRODUCT_RISK_ENGINE_VERSION,
    created_at: datetime,
) -> list[RiskCase]:
    """把 R5 publication packet 的风险记录转换为收件箱/看板 RiskCase。"""

    locations = _canonical_locations(packet)
    cases: list[RiskCase] = []
    for risk in getattr(packet, "risks", ()) or ():
        risk_ref = str(getattr(risk, "risk_ref", "") or "").strip()
        if not risk_ref:
            continue
        severity_raw = str(getattr(risk, "severity", "") or "").strip().lower()
        severity = _SEVERITY_MAP.get(severity_raw, RiskSeverity.MEDIUM)
        subject_ref = str(getattr(risk, "subject_ref", "") or "").strip()
        subject_id = _strip_prefix(subject_ref, "subject-") or None
        site_ref = str(getattr(risk, "site_ref", "") or "").strip()
        domain = str(getattr(risk, "domain", "") or "").strip().upper()
        risk_type = str(getattr(risk, "risk_type_zh", "") or "").strip() or "医学监查发现"
        title = f"{risk_type}（受试者{_strip_prefix(subject_ref, 'subject-')}）" if subject_id else risk_type
        medical_note = str(getattr(risk, "medical_note", "") or "").strip()
        evidence_spans = [
            locations.get(locator_ref, locator_ref)
            for locator_ref in (
                getattr(risk, "source_locator_refs", ()) or ()
            )
            if str(locator_ref).strip()
        ]
        cases.append(
            RiskCase(
                risk_id=risk_ref,
                risk_key=str(getattr(risk, "risk_key", "") or "").strip() or risk_ref,
                risk_instance_id=(
                    str(getattr(risk, "risk_instance_ref", "") or "").strip()
                    or risk_ref
                ),
                project_id=project_id,
                module="medical_monitoring",
                risk_type=risk_type,
                tags=[f"source_domain:{domain}"] if domain else [],
                title=title,
                subject_id=subject_id,
                site_id=_strip_prefix(site_ref, "site-") or None,
                severity=severity,
                status=RiskStatus.NEW,
                source_revision=source_revision,
                rule_profile_revision=rule_profile_revision,
                engine_version=engine_version,
                rule_id=str(getattr(risk, "risk_key", "") or "").strip() or risk_ref,
                evidence_span_ids=evidence_spans[:8],
                rationale=medical_note or "基于已发布监查结果的风险发现，待医学复核。",
                recommended_action="进入医学监查结果视图复核该发现。",
                created_at=created_at,
            )
        )
    return cases


def record_publication_risk_snapshot(
    *,
    project_id: str,
    run_id: str,
    packet: Any,
    risk_repository: Any,
    rule_profile_revision: str,
    created_at: datetime,
) -> dict[str, Any]:
    """发布成功后写入（幂等）聚合风险快照；返回写入结果摘要。

    该函数只做桥接写入，不做发布成败判定——调用方在发布已确认成功后
    调用；桥接自身的失败向上抛出，由调用方决定是否留痕（不得阻断已
    成功的发布响应）。
    """

    cases = product_packet_risk_cases(
        packet,
        project_id=project_id,
        # source_revision 绑定 run 与 packet 指纹：同一 run 重复发布幂等，
        # 新 run/新数据自动成为新快照。
        source_revision=f"product-publication:{run_id}",
        rule_profile_revision=rule_profile_revision,
        created_at=created_at,
    )
    snapshot = risk_repository.save_snapshot(
        project_id=project_id,
        source_batch_id=None,
        source_revision=f"product-publication:{run_id}",
        rule_profile_revision=rule_profile_revision,
        engine_version=PRODUCT_RISK_ENGINE_VERSION,
        evaluated_subject_count=0,
        risks=cases,
        resolution_complete=True,
    )
    return {
        "snapshot_id": snapshot.snapshot_id,
        "risk_count": snapshot.risk_count,
    }


__all__ = [
    "PRODUCT_RISK_ENGINE_VERSION",
    "product_packet_risk_cases",
    "record_publication_risk_snapshot",
]
