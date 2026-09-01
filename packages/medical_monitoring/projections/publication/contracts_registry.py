"""Canonical registration and frozen audience constants for R5 contracts."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional, Tuple

from .canonical import R5CanonicalError, canonical_object_hash, register_object_fields
from .contracts_core import *
from .contracts_objects import *

# ---------------------------------------------------------------------------
# Canonical field registration (static; verified against the JSON by tests)
# ---------------------------------------------------------------------------

register_object_fields(
    "SourceRevisionContentPair",
    hash_fields=("content_hash",))
register_object_fields(
    "R5AEMHMatchHistory",
    hash_fields=("history_content_hash",))
register_object_fields(
    "R5AudienceEncodingRegistry")
register_object_fields(
    "R5AudienceLexicon",
    hash_fields=("content_hash",))
register_object_fields(
    "R5AuthorityReceipt",
    hash_fields=(
        "public_projection_content_hash",
        "visibility_decision_hash",
        "evaluation_content_identities",
    ))
register_object_fields(
    "R5CenterMapCell")
register_object_fields(
    "R5CenterMapProjection",
    hash_fields=("content_hash",),
    ordered_fields=("stable_site_order",))
register_object_fields(
    "R5ChangeBand")
register_object_fields(
    "R5CurrentRiskSet")
register_object_fields(
    "R5DeepLinkState")
register_object_fields(
    "R5DomainEncodingItem")
register_object_fields(
    "R5FilterState")
register_object_fields(
    "R5JourneyEvent")
register_object_fields(
    "R5JourneyTrack",
    hash_fields=("content_hash",))
register_object_fields(
    "R5LegacyTreatmentMappingItem")
register_object_fields(
    "R5LexiconItem")
register_object_fields(
    "R5PageState")
register_object_fields(
    "R5PendingDateItem")
register_object_fields(
    "R5ProjectCockpitProjection",
    hash_fields=("content_hash",))
register_object_fields(
    "R5ProjectionInstance",
    hash_fields=("content_hash", "replay_content_identity"))
register_object_fields(
    "R5QuantitativeMeasure")
register_object_fields(
    "R5ReturnContext",
    hash_fields=("canonical_state_hash",))
register_object_fields(
    "R5RiskAnchor")
register_object_fields(
    "R5RiskInspectorProjection")
register_object_fields(
    "R5ScrollState")
register_object_fields(
    "R5SeverityLexiconItem")
register_object_fields(
    "R5SortState")
register_object_fields(
    "R5SubjectWorkspaceState",
    hash_fields=("content_hash",))
register_object_fields(
    "R5TemporalSpineProjection",
    hash_fields=("content_hash",))
register_object_fields(
    "R5VisitNode")

#: class name -> typed class (used by deferred_leaf_objects and validation).
_CLASS_BY_NAME: Dict[str, type] = {
    cls.__name__: cls for cls in (
        SourceRevisionContentPair,
        R5AEMHMatchHistory,
        R5AudienceEncodingRegistry,
        R5AudienceLexicon,
        R5AuthorityReceipt,
        R5CenterMapCell,
        R5CenterMapProjection,
        R5ChangeBand,
        R5CurrentRiskSet,
        R5DeepLinkState,
        R5DomainEncodingItem,
        R5FilterState,
        R5JourneyEvent,
        R5JourneyTrack,
        R5LegacyTreatmentMappingItem,
        R5LexiconItem,
        R5PageState,
        R5PendingDateItem,
        R5ProjectCockpitProjection,
        R5ProjectionInstance,
        R5QuantitativeMeasure,
        R5ReturnContext,
        R5RiskAnchor,
        R5RiskInspectorProjection,
        R5ScrollState,
        R5SeverityLexiconItem,
        R5SortState,
        R5SubjectWorkspaceState,
        R5TemporalSpineProjection,
        R5VisitNode,
    )
}


def known_object_names() -> Tuple[str, ...]:
    """Every R5 object class name declared by the typed surface."""
    return tuple(sorted(_CLASS_BY_NAME))


def is_r5_object(obj: Any) -> bool:
    return type(obj) in _CLASS_BY_NAME.values()


def validate_object(obj: Any) -> bool:
    """Fail-closed check that ``obj`` is a known R5 typed object whose
    canonical core is serializable (construction already enforced all
    invariants; this re-proves the canonical path for the W2 adapter)."""
    if not is_r5_object(obj):
        raise R5ContractError(
            f"not an R5 typed object: {type(obj).__name__}")
    canonical_object_hash(obj)  # raises R5CanonicalError on any defect
    return True


# ---------------------------------------------------------------------------
# Frozen contract constants (values NOT pinned by the S0 SHAs; see
# CONTRACT_CONSTANT_PIN_STATUS and the W1 report)
# ---------------------------------------------------------------------------

#: 8-domain audience encoding (stage contract v0.3 §8 table).  §8 lists
#: symptom_efficacy uses one event shape (circle); longitudinal change is
#: expressed only by the trend line style, so the registry has no second
#: shape convention.
DOMAIN_ENCODING_ITEMS: Tuple[R5DomainEncodingItem, ...] = (
    R5DomainEncodingItem(domain="ae", short_label_zh="AE",
                         event_shape="rounded_rect", line_style="solid"),
    R5DomainEncodingItem(domain="mh", short_label_zh="MH",
                         event_shape="bookmark", line_style="dot_dash"),
    R5DomainEncodingItem(domain="cm", short_label_zh="合并用药",
                         event_shape="capsule", line_style="solid"),
    R5DomainEncodingItem(domain="ip", short_label_zh="试验药",
                         event_shape="hexagon", line_style="step"),
    R5DomainEncodingItem(domain="lab_exam", short_label_zh="检验/检查",
                         event_shape="square", line_style="trend"),
    R5DomainEncodingItem(domain="hospital_procedure",
                         short_label_zh="住院/操作",
                         event_shape="doorframe", line_style="solid"),
    R5DomainEncodingItem(domain="symptom_efficacy",
                         short_label_zh="症状/疗效",
                         event_shape="circle", line_style="trend"),
    R5DomainEncodingItem(domain="protocol_compliance",
                         short_label_zh="方案符合",
                         event_shape="single_flag", line_style="bracket"),
)

#: 4 severity lexicon items.  Labels are pinned (§10 紧急/高/中/低 and the
#: severity_lexicon_bijection invariant); line weights 4/3/2/1 are an
#: unpinned choice (flagged in CONTRACT_CONSTANT_PIN_STATUS).
SEVERITY_LEXICON_ITEMS: Tuple[R5SeverityLexiconItem, ...] = (
    R5SeverityLexiconItem(severity="critical", label_zh="紧急", line_weight=4),
    R5SeverityLexiconItem(severity="high", label_zh="高", line_weight=3),
    R5SeverityLexiconItem(severity="medium", label_zh="中", line_weight=2),
    R5SeverityLexiconItem(severity="low", label_zh="低", line_weight=1),
)

#: Legacy treatment mapping: no frozen project mapping exists in the frozen
#: contract, so both legacy kinds stay unmapped_fail_closed (legacy_domain_
#: policy: frozen_mapping_or_fail_closed) and enter the domain-confirmation
#: surface.
LEGACY_TREATMENT_MAPPING_ITEMS: Tuple[R5LegacyTreatmentMappingItem, ...] = (
    R5LegacyTreatmentMappingItem(
        legacy_kind="background_treatment", mapping_state="unmapped_fail_closed",
        mapping_authority_ref=None, target_domain=None, target_subtype=None),
    R5LegacyTreatmentMappingItem(
        legacy_kind="non_drug_treatment", mapping_state="unmapped_fail_closed",
        mapping_authority_ref=None, target_domain=None, target_subtype=None),
)

#: Forbidden audience structure labels (stage contract v0.3 §8 / §14
#: elimination lists).  Exact token set is NOT closed by an S0 SHA (flagged).
FORBIDDEN_TERMS: Tuple[str, ...] = (
    "已记录事项", "正式事实", "候选信号", "通用风险点", "只读", "只读来源原文片段",
    "Checklist", "项目医学风险 Checklist", "待行动", "未读", "个例优先队列",
    "Safety/PV",
)

#: Audience lexicon items: 8 domain tokens + 4 severity tokens + PV-context
#: 信号 (allowed only for 药物警戒/安全性信号, §8) + the forbidden terms
#: (audience_allowed=False).  Exact token list is NOT closed by an S0 SHA.
LEXICON_ITEMS: Tuple[R5LexiconItem, ...] = (
    R5LexiconItem(token="ae", label_zh="AE", audience_allowed=True),
    R5LexiconItem(token="mh", label_zh="MH", audience_allowed=True),
    R5LexiconItem(token="cm", label_zh="合并用药", audience_allowed=True),
    R5LexiconItem(token="ip", label_zh="试验药", audience_allowed=True),
    R5LexiconItem(token="lab_exam", label_zh="检验/检查",
                  audience_allowed=True),
    R5LexiconItem(token="hospital_procedure", label_zh="住院/操作",
                  audience_allowed=True),
    R5LexiconItem(token="symptom_efficacy", label_zh="症状/疗效",
                  audience_allowed=True),
    R5LexiconItem(token="protocol_compliance", label_zh="方案符合",
                  audience_allowed=True),
    R5LexiconItem(token="critical", label_zh="紧急", audience_allowed=True),
    R5LexiconItem(token="high", label_zh="高", audience_allowed=True),
    R5LexiconItem(token="medium", label_zh="中", audience_allowed=True),
    R5LexiconItem(token="low", label_zh="低", audience_allowed=True),
    R5LexiconItem(token="signal", label_zh="信号", audience_allowed=True),
    *(
        R5LexiconItem(token=term, label_zh=term, audience_allowed=False)
        for term in FORBIDDEN_TERMS
    ),
)


def build_audience_encoding_registry() -> R5AudienceEncodingRegistry:
    """The frozen audience encoding registry (contract constants)."""
    return R5AudienceEncodingRegistry(
        domain_items=DOMAIN_ENCODING_ITEMS,
        legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
        risk_overlay_shape=RISK_OVERLAY_SHAPE,
        severity_items=SEVERITY_LEXICON_ITEMS,
        symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES,
    )


def build_audience_lexicon() -> R5AudienceLexicon:
    """The frozen audience lexicon (contract constants); ``content_hash``
    is the deterministic canonical hash of its non-hash fields."""
    return R5AudienceLexicon(
        content_hash="",
        forbidden_terms=FORBIDDEN_TERMS,
        items=LEXICON_ITEMS,
    )


#: Pin status of every contract-constant value group.  ``PINNED_*`` values
#: trace to a frozen SHA or exact_contract.json; ``PARTIAL`` values are
#: markdown-derived with at least one unpinned choice (see W1 report).
CONTRACT_CONSTANT_PIN_STATUS: Dict[str, Tuple[str, str]] = {
    "DOMAIN_ENCODING_ITEMS": (
        "PINNED_POLICY",
        "labels/shapes/line styles from stage contract v0.3 §8; "
        "domain_encoding_complete_unique freezes eight unique domains and "
        "symptom_efficacy circle + trend"),
    "SEVERITY_LEXICON_ITEMS": (
        "PARTIAL",
        "labels pinned (§10 + severity_lexicon_bijection invariant); "
        "line_weight 4/3/2/1 unpinned by any SHA"),
    "SYMPTOM_EFFICACY_SUBTYPES": (
        "PINNED_EXACT_CONTRACT",
        "exact_contract.json enums.symptom_efficacy_subtype"),
    "LEGACY_TREATMENT_MAPPING_ITEMS": (
        "PINNED_POLICY",
        "legacy_domain_policy frozen_mapping_or_fail_closed; no frozen "
        "project mapping exists -> unmapped_fail_closed"),
    "LEXICON_ITEMS": (
        "PARTIAL",
        "tokens/labels derived from §8/§10/§14; exact token list unpinned "
        "by any SHA"),
    "FORBIDDEN_TERMS": (
        "PARTIAL",
        "derived from §8/§14 forbidden lists; exact set unpinned by any SHA"),
    "RISK_OVERLAY_SHAPE": (
        "PINNED_EXACT_CONTRACT",
        "exact_contract.json risk_overlay_shape"),
    "DOMAIN_SUBTYPE_MATRIX": (
        "PARTIAL",
        "derived from journey_subtype enum + §7/§8; literal matrix unpinned"),
    "LEGACY_SEVERITY_MAPPING": (
        "PINNED_INVARIANT",
        "invariants.legacy_severity_mapping"),
}

__all__ = [
    "APPLICABILITY_STATES",
    "AXIS_MODES",
    "CHANGE_CAUSES",
    "CHANGE_KINDS",
    "CONTRACT_CONSTANT_PIN_STATUS",
    "COVERAGE_STATES",
    "DATE_STATES",
    "DEFERRED_CONTRACT_BY_ID",
    "DEFERRED_CONTRACT_SPECS",
    "DENOMINATOR_KINDS",
    "DENOMINATOR_STATES",
    "DOMAIN_ENCODING_ITEMS",
    "DOMAIN_SUBTYPE_MATRIX",
    "DOMAINS",
    "EVENT_FORBIDDEN_SHAPES",
    "EVENT_SHAPES",
    "FORBIDDEN_TERMS",
    "JOURNEY_SUBTYPES",
    "LEGACY_DOMAIN_POLICY",
    "LEGACY_MAPPING_STATES",
    "LEGACY_SEVERITY_MAPPING",
    "LEGACY_TREATMENT_KINDS",
    "LEGACY_TREATMENT_MAPPING_ITEMS",
    "LEXICON_ITEMS",
    "LINE_STYLES",
    "MATCH_STATES",
    "MEASURE_UNITS",
    "NUMERATOR_KINDS",
    "PENDING_ITEM_KINDS",
    "PROJECTION_KINDS",
    "R4_AUTHORITY_SEVERITY_VOCABULARY",
    "R5AEMHMatchHistory",
    "R5AudienceEncodingRegistry",
    "R5AudienceLexicon",
    "R5AuthorityReceipt",
    "R5CanonicalError",
    "R5CenterMapCell",
    "R5CenterMapProjection",
    "R5ChangeBand",
    "R5ContractError",
    "R5CurrentRiskSet",
    "R5DeepLinkState",
    "R5DeferredContract",
    "R5DomainEncodingItem",
    "R5FilterState",
    "R5HashMismatchError",
    "R5JourneyEvent",
    "R5JourneyTrack",
    "R5LegacyTreatmentMappingItem",
    "R5LexiconItem",
    "R5PageState",
    "R5PendingDateItem",
    "R5ProjectCockpitProjection",
    "R5ProjectionInstance",
    "R5QuantitativeMeasure",
    "R5ReturnContext",
    "R5RiskAnchor",
    "R5RiskInspectorProjection",
    "R5ScrollState",
    "R5SeverityLexiconItem",
    "R5SortState",
    "R5SubjectWorkspaceState",
    "R5TemporalSpineProjection",
    "R5VisitNode",
    "R5_CONTRACT_SHA256",
    "R5_CONTRACT_SCHEMA_ID",
    "R5_EXACT_CONTRACT_ARTIFACT_SHA256",
    "RATE_STATES",
    "RISK_OVERLAY_SHAPE",
    "SEVERITIES",
    "SEVERITY_LEXICON_ITEMS",
    "SEVERITY_TO_ZH",
    "SEVERITY_ZH",
    "SORT_DIRECTIONS",
    "SORT_KEYS",
    "SYMPTOM_EFFICACY_SUBTYPES",
    "UNKNOWN_DOMAIN_POLICY",
    "VISIBILITY_STATES",
    "VISIT_KINDS",
    "WORKSPACE_VIEWS",
    "ZH_TO_SEVERITY",
    "build_audience_encoding_registry",
    "build_audience_lexicon",
    "deferred_contract",
    "deferred_fields_for",
    "deferred_leaf_objects",
    "enum_values",
    "is_deferred_field",
    "is_r5_object",
    "known_object_names",
    "legacy_severity_to_r5",
    "severity_to_zh",
    "validate_object",
    "validate_severity_authority",
    "zh_to_severity",
]
