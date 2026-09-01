"""Continuity response contracts and audience labels for the R7 product API."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .contracts import ProductPublicationError, _StrictModel

_CONTINUITY_RISK_CHANGE_KINDS_ZH = {
    "new": "新增",
    "upgraded": "升级",
    "continued": "持续",
    "downgraded": "降级",
    "closed": "关闭",
    "reopened": "重开",
    "needs_rejudgment": "需重新判断",
}
_CONTINUITY_DISPOSITIONS_ZH = {
    "reuse_unchanged": "沿用不变",
    "re_evaluate_changed_data": "数据变化，已重新分析",
    "re_evaluate_rule_change": "规则变化，已重新分析",
    "re_evaluate_prior_uncertain": "上轮依据不足，本轮重新分析",
    "close_with_evidence": "已有证据支持关闭",
    "blocked_incompatible": "前后版本不可直接比较",
}
_CONTINUITY_DATA_CHANGE_KINDS_ZH = {
    "unchanged": "无变化",
    "added": "新增数据",
    "revised": "数据修订",
    "deleted": "数据删除",
    "cannot_compare": "无法直接比较",
    "missing": "本轮未见对应记录",
}
_CONTINUITY_ATTENTION_TEXTS = frozenset(
    {
        "",
        "未见记录不代表风险已解除",
        "身份或数据不完整，需重新判断",
        "等级变化待确认",
        "原始记录位置待确认",
    }
)
_CONTINUITY_SEVERITIES = frozenset({"", "高", "中", "低"})
_CONTINUITY_OBJECT_TYPES_ZH = {
    "risk": "风险",
    "query_draft": "Query 草稿",
    "monitoring_output": "监查结果项",
}
_SEVERITY_TEXT_MAP = {
    "high": "高",
    "medium": "中",
    "low": "低",
}
_SEVERITY_RANK = {"高": 3, "中": 2, "低": 1}


class ProductContinuityChangeCounts(_StrictModel):
    new: int
    upgraded: int
    continued: int
    downgraded: int
    closed: int
    reopened: int
    needs_rejudgment: int
    mid_high_total: int
    changed_subject_count: int


class ProductContinuityRow(_StrictModel):
    row_ref: str
    object_type: str
    object_type_text: str
    ordinal: int
    change_kind: str
    change_text: str
    disposition: str
    disposition_text: str
    data_change_kind: str
    data_change_text: str
    severity_before_text: str
    severity_after_text: str
    title: str
    reason_text: str
    attention_text: str
    site_ref: str
    site_label: str
    subject_ref: str
    subject_label: str
    date_label: str
    window_start: str
    window_end: str
    risk_ref: str
    risk_instance_ref: str
    risk_anchor_ref: str
    event_ref: str
    source_locator_ref: str
    source_count: int


class ProductContinuityComparison(_StrictModel):
    available: bool
    basis_text: str
    comparison_text: str
    source_run_text: str
    change_counts: ProductContinuityChangeCounts
    rows: list[ProductContinuityRow]
    shown_count: int
    total_count: int
    truncated: bool


class ProductContinuityIdentity(_StrictModel):
    project_ref: str
    public_run_token: str
    snapshot_token: str
    data_cutoff_text: str
    mode_text: str
    site_scope_text: str
    site_ref: Optional[str] = None


class ProductContinuityResponse(_StrictModel):
    result_context_token: str
    identity: ProductContinuityIdentity
    comparison: ProductContinuityComparison
    response_digest: str


def _normalize_severity_zh(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    try:
        return _SEVERITY_TEXT_MAP[text]
    except KeyError as exc:
        raise ProductPublicationError("continuity_unavailable") from exc


def _validate_continuity_risk_semantics(item: Any, change_kind: str) -> None:
    from packages.medical_monitoring.runtime.continuity import (
        RiskProjectionError,
        project_risk_change_kind,
    )

    try:
        projected = project_risk_change_kind(
            from_state=getattr(item, "prior_risk_state", None),
            to_state=getattr(item, "current_risk_state", None),
            transition_type=(getattr(item, "r2_transition_type", "") or None),
            from_severity=getattr(item, "prior_severity", None),
            to_severity=getattr(item, "current_severity", None),
            identity_ambiguous=bool(getattr(item, "identity_ambiguous", False))
            or not getattr(item, "identity_compatible", True),
            lineage_changed=bool(getattr(item, "lineage_changed", False))
            or not getattr(item, "source_compatible", True),
            data_missing=bool(getattr(item, "data_missing", False))
            or not getattr(item, "output_contract_compatible", True)
            or not getattr(item, "current_present", True)
            or getattr(item, "data_change_kind", "")
            in {"missing", "cannot_compare"},
        )
    except (RiskProjectionError, TypeError, ValueError) as exc:
        raise ProductPublicationError("continuity_unavailable") from exc
    if projected.value != change_kind:
        raise ProductPublicationError("continuity_unavailable")
    if change_kind == "closed" and not (
        item.disposition == "close_with_evidence"
        and bool(item.closure_evidence_refs)
        and item.closure_allowed
        and item.current_listing_complete
        and item.baseline_eligible
    ):
        raise ProductPublicationError("continuity_unavailable")


def _continuity_row_sort_key(row: Mapping[str, Any]) -> tuple[int, int, str]:
    obj_type = str(row.get("object_type", ""))
    change_kind = str(row.get("change_kind", ""))
    sev_after = str(row.get("severity_after_text", ""))
    sev_before = str(row.get("severity_before_text", ""))
    ordinal = int(row.get("ordinal", 0))
    row_ref = str(row.get("row_ref", ""))

    priority_kinds = {"upgraded", "new", "reopened", "needs_rejudgment"}
    if obj_type == "risk":
        if sev_after == "高" and change_kind in priority_kinds:
            group = 0
        elif sev_after == "中" and change_kind in priority_kinds:
            group = 1
        elif (sev_after in {"高", "中"}) or (
            change_kind == "closed" and sev_before in {"高", "中"}
        ):
            group = 2
        else:
            group = 3
    elif obj_type == "query_draft":
        group = 4
    elif obj_type == "monitoring_output":
        group = 5
    else:
        group = 6
    return (group, ordinal, row_ref)


__all__ = [
    "_CONTINUITY_RISK_CHANGE_KINDS_ZH",
    "_CONTINUITY_DISPOSITIONS_ZH",
    "_CONTINUITY_DATA_CHANGE_KINDS_ZH",
    "_CONTINUITY_ATTENTION_TEXTS",
    "_CONTINUITY_SEVERITIES",
    "_CONTINUITY_OBJECT_TYPES_ZH",
    "_SEVERITY_TEXT_MAP",
    "_SEVERITY_RANK",
    "ProductContinuityChangeCounts",
    "ProductContinuityRow",
    "ProductContinuityComparison",
    "ProductContinuityIdentity",
    "ProductContinuityResponse",
    "_normalize_severity_zh",
    "_validate_continuity_risk_semantics",
    "_continuity_row_sort_key",
]
