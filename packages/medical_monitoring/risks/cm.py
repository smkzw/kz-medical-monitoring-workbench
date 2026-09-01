"""R4-D02 CM medication rationale, prohibited/restricted medication,
cross-domain evidence, Query and journey contract.

Frozen source of truth: ``FROZEN_R4_D02_CONTRACT_V1`` (§§2-13).  This
module implements the D02 CM domain engine on top of the shared
``RiskDomainUnitResult`` protocol, reusing the accepted R1 coverage, R2
identity/lifecycle, and R3 mapping/rule/knowledge public contracts.

Design constraints enforced here (frozen D02 contract):

1. Stable classifier / stable-core versus versioned scope/lineage.
2. Compound ingredient-resolution units.
3. Explicit indication/role sufficiency.
4. Rule-target granularity (ingredient-exact > category > product-type).
5. Five L1 dispositions with six positive subtypes.
6. Linked-negative closure, Query generation, canonical cross-domain
   evidence references, and D01/D02 non-duplication.

All data is synthetic/offline.  No real project, provider, dictionary,
or product service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from ..intelligence.normalization import NormalizedValue, normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    L0CoverageStatus,
    EvaluationUnit,
    EvidenceItem,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
    cross_domain_evidence_content_hash,
)

__all__ = [
    "REQUIRED_CM_ROLES",
    "OPTIONAL_CM_ROLES",
    "CM_ROLES",
    "CMSliceError",
    "IngredientBinding",
    "MedicationIdentityBinding",
    "ProtocolMedicationRule",
    "MedicationMatchStrategy",
    "MedicationEpisode",
    "TreatmentInterpretationEvidence",
    "D02PriorityPolicy",
    "CMIntervalDescriptor",
    "CMSemanticRecord",
    "CMUnitResult",
    "CMUnitExpanded",
    "CMExpectedSetExpansion",
    "CMSliceResult",
    "CMEpisodeRollup",
    "expand_cm_expected_set",
    "evaluate_cm_unit",
    "evaluate_cm_slice",
    "POSITIVE_SUBTYPE_LABELS",
    "positive_subtype_audience_label",
    "D02_DOMAIN",
    "D02_UNIT_ALGO_VERSION",
    "D02_RULE_TYPES",
    "CONFIRMATION_CONFIRMED",
    "CONFIRMATION_UNRESOLVED",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D02_DOMAIN = "D02_cm"
D02_UNIT_ALGO_VERSION = "d02_unit_v1"
D02_RULE_LINEAGE_DEFAULT = "d02-cm-rule-v1"

REQUIRED_CM_ROLES: Tuple[str, ...] = (
    "recorded_cm", "subject_identity", "site_identity", "temporal_anchor",
)

OPTIONAL_CM_ROLES: Tuple[str, ...] = (
    "reported_ae", "reported_mh", "diagnosis", "symptom_event",
    "ip_exposure", "visit", "study_phase",
)

CM_ROLES: Tuple[str, ...] = REQUIRED_CM_ROLES + OPTIONAL_CM_ROLES

D02_RULE_TYPES: Tuple[str, ...] = (
    "prohibited", "restricted",
    "stable_treatment_allowed", "rescue_allowed", "prophylaxis_allowed",
    "record_consistency", "action_relationship",
)

RECORD_CONSISTENCY_FIELDS: Tuple[str, ...] = (
    "dose", "dose_unit", "route", "frequency", "start", "end",
    "treatment_role",
)

CONFIRMATION_CONFIRMED = "confirmed"
CONFIRMATION_UNRESOLVED = "unresolved"

POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED = (
    "medication_indication_unexplained")
POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD = (
    "treatment_without_event_record")
POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH = "prohibited_medication_match"
POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH = (
    "restricted_medication_condition_mismatch")
POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY = (
    "medication_record_inconsistency")
POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT = (
    "treatment_action_relationship_inconsistent")

POSITIVE_SUBTYPES: Tuple[str, ...] = (
    POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED,
    POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
    POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
    POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH,
    POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY,
    POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT,
)

POSITIVE_SUBTYPE_LABELS: Dict[str, str] = {
    POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED: "用药依据待核实",
    POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH: "禁用药使用待核实",
    POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH:
        "限制用药条件待核实",
    POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY:
        "用药信息与方案要求不一致",
    POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD:
        "治疗用药与 AE/MH 记录待核实",
    POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT:
        "用药与处置记录关系待核实",
}

TARGET_KIND_INGREDIENT = "ingredient"
TARGET_KIND_CATEGORY = "category"
TARGET_KIND_PRODUCT_TYPE = "product_type"

_VAGUE_INDICATION_TOKENS: Tuple[str, ...] = (
    "对症治疗", "其他", "其它", "遵医嘱", "未知", "",
)

INGREDIENT_RESOLUTION_RISK_FAMILY = "ingredient_resolution"
INGREDIENT_RESOLUTION_SIGNAL_TYPE = "ingredient_unresolved"


def positive_subtype_audience_label(subtype: str) -> str:
    if subtype not in POSITIVE_SUBTYPE_LABELS:
        raise CMSliceError(f"unknown positive subtype {subtype!r}")
    return POSITIVE_SUBTYPE_LABELS[subtype]


class CMSliceError(Exception):
    """A D02 CM slice evaluation invariant was violated."""


# ---------------------------------------------------------------------------
# Versioned non-listing inputs (frozen D02 §3.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IngredientBinding:
    """One resolved ingredient or an unresolved component slot."""

    ingredient: str = ""
    component_slot: str = ""
    confirmation: str = CONFIRMATION_CONFIRMED
    categories: Tuple[str, ...] = ()
    product_types: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.confirmation not in (CONFIRMATION_CONFIRMED,
                                     CONFIRMATION_UNRESOLVED):
            raise CMSliceError(
                f"IngredientBinding.confirmation={self.confirmation!r} "
                f"is not confirmed/unresolved")
        if self.confirmation == CONFIRMATION_CONFIRMED:
            if not self.ingredient.strip():
                raise CMSliceError(
                    "confirmed IngredientBinding requires ingredient name")
        else:
            if not self.component_slot.strip():
                raise CMSliceError(
                    "unresolved IngredientBinding requires component_slot")
            if self.ingredient.strip():
                raise CMSliceError(
                    "unresolved IngredientBinding must not carry ingredient")
        object.__setattr__(self, "categories", tuple(sorted(set(self.categories))))
        object.__setattr__(self, "product_types", tuple(sorted(set(self.product_types))))

    @property
    def is_unresolved(self) -> bool:
        return self.confirmation == CONFIRMATION_UNRESOLVED

    @property
    def identity_token(self) -> str:
        if self.is_unresolved:
            return f"unresolved:{self.component_slot.strip()}"
        return self.ingredient.strip()


@dataclass(frozen=True)
class MedicationIdentityBinding:
    """Versioned controlled-dictionary identity binding for one CM record."""

    original_name: str
    normalized_name: str
    ingredients: Tuple[IngredientBinding, ...]
    dictionary_name: str
    dictionary_version: str
    dictionary_content_hash: str
    evidence_locator: SourceLocator
    confirmation_status: str = CONFIRMATION_CONFIRMED

    def __post_init__(self) -> None:
        if not self.original_name.strip():
            raise CMSliceError("original_name is required")
        if not self.normalized_name.strip():
            raise CMSliceError("normalized_name is required")
        if not self.ingredients:
            raise CMSliceError("at least one IngredientBinding required")
        if not self.dictionary_name.strip():
            raise CMSliceError("dictionary_name is required")
        if not self.dictionary_version.strip():
            raise CMSliceError("dictionary_version is required")
        if not self.dictionary_content_hash.strip():
            raise CMSliceError("dictionary_content_hash is required")
        if not isinstance(self.evidence_locator, SourceLocator):
            raise CMSliceError("evidence_locator must be a SourceLocator")
        if self.confirmation_status not in (CONFIRMATION_CONFIRMED,
                                            CONFIRMATION_UNRESOLVED):
            raise CMSliceError("invalid confirmation_status")

    @property
    def confirmed_ingredients(self) -> Tuple[IngredientBinding, ...]:
        return tuple(ib for ib in self.ingredients if not ib.is_unresolved)

    @property
    def unresolved_components(self) -> Tuple[IngredientBinding, ...]:
        return tuple(ib for ib in self.ingredients if ib.is_unresolved)

    @property
    def has_unresolved(self) -> bool:
        return any(ib.is_unresolved for ib in self.ingredients)


@dataclass(frozen=True)
class ProtocolMedicationRule:
    """Versioned protocol medication rule (frozen D02 §3.2, §9.1)."""

    rule_id: str
    rule_version: str
    clause_locator: str
    rule_type: str
    target_kind: str
    target_value: str
    applicable_phases: Tuple[str, ...]
    window_start: str = ""
    window_end: str = ""
    window_start_inclusive: Optional[bool] = None
    window_end_inclusive: Optional[bool] = None
    allowed_conditions: Tuple[str, ...] = ()
    stable_treatment_exception: bool = False
    rescue_exception: bool = False
    prophylaxis_exception: bool = False
    comparison_field: str = ""
    expected_values: Tuple[str, ...] = ()
    related_role: str = ""
    related_concept: str = ""
    expected_actions: Tuple[str, ...] = ()
    priority_on_hit: str = MONITORING_PRIORITY_UNKNOWN
    priority_rationale: str = ""
    rule_content_hash: str = ""
    rule_lineage: str = ""

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise CMSliceError("rule_id is required")
        if not self.rule_version.strip():
            raise CMSliceError("rule_version is required")
        if not self.clause_locator.strip():
            raise CMSliceError("clause_locator is required")
        if self.rule_type not in D02_RULE_TYPES:
            raise CMSliceError(f"rule_type={self.rule_type!r} invalid")
        if self.target_kind not in (TARGET_KIND_INGREDIENT,
                                    TARGET_KIND_CATEGORY,
                                    TARGET_KIND_PRODUCT_TYPE):
            raise CMSliceError(f"target_kind={self.target_kind!r} invalid")
        if not self.target_value.strip():
            raise CMSliceError("target_value is required")
        if not self.applicable_phases:
            raise CMSliceError("applicable_phases is required")
        if self.priority_on_hit not in VALID_MONITORING_PRIORITIES:
            raise CMSliceError("priority_on_hit invalid")
        if not self.priority_rationale.strip():
            raise CMSliceError("priority_rationale is required")
        if not self.rule_content_hash.strip():
            raise CMSliceError("rule_content_hash is required")
        if not self.rule_lineage.strip():
            raise CMSliceError("rule_lineage is required")
        object.__setattr__(self, "applicable_phases", tuple(self.applicable_phases))
        object.__setattr__(self, "allowed_conditions", tuple(self.allowed_conditions))
        object.__setattr__(self, "expected_values", tuple(self.expected_values))
        object.__setattr__(self, "expected_actions", tuple(self.expected_actions))
        if self.is_record_consistency:
            if self.comparison_field not in RECORD_CONSISTENCY_FIELDS:
                raise CMSliceError(
                    "record_consistency rule requires a supported "
                    "comparison_field")
            if not self.expected_values or any(
                    not value.strip() for value in self.expected_values):
                raise CMSliceError(
                    "record_consistency rule requires non-empty expected_values")
        elif self.comparison_field or self.expected_values:
            raise CMSliceError(
                "comparison_field/expected_values are only valid for "
                "record_consistency rules")
        if self.is_action_relationship:
            if self.related_role not in ("reported_ae", "reported_mh",
                                         "ip_exposure"):
                raise CMSliceError(
                    "action_relationship rule requires related_role "
                    "reported_ae/reported_mh/ip_exposure")
            if not self.expected_actions or any(
                    not action.strip() for action in self.expected_actions):
                raise CMSliceError(
                    "action_relationship rule requires non-empty "
                    "expected_actions")
        elif self.related_role or self.related_concept or self.expected_actions:
            raise CMSliceError(
                "relationship fields are only valid for action_relationship "
                "rules")

    @property
    def is_prohibited(self) -> bool:
        return self.rule_type == "prohibited"

    @property
    def is_restricted(self) -> bool:
        return self.rule_type == "restricted"

    @property
    def is_record_consistency(self) -> bool:
        return self.rule_type == "record_consistency"

    @property
    def is_action_relationship(self) -> bool:
        return self.rule_type == "action_relationship"


@dataclass(frozen=True)
class MedicationMatchStrategy:
    """Versioned match strategy (frozen D02 §3.2)."""

    version: str
    ingredient_exact_match: bool = True
    category_membership_requires_explicit_evidence: bool = True
    compound_split_per_ingredient: bool = True
    indication_concept_equivalence: Tuple[Tuple[str, str], ...] = ()
    strategy_content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise CMSliceError("version is required")
        if not self.strategy_content_hash.strip():
            raise CMSliceError("strategy_content_hash is required")
        eq = tuple((a.strip(), b.strip())
                   for a, b in self.indication_concept_equivalence
                   if a.strip() and b.strip())
        object.__setattr__(self, "indication_concept_equivalence", eq)

    def indication_concepts_equivalent(self, concept_a: str,
                                       concept_b: str) -> bool:
        a, b = concept_a.strip(), concept_b.strip()
        if not a or not b:
            return False
        if a == b:
            return True
        for x, y in self.indication_concept_equivalence:
            if {x, y} == {a, b}:
                return True
        return False


@dataclass(frozen=True)
class D02PriorityPolicy:
    """Versioned priority policy for non-rule D02 risks (frozen D02 §3.2)."""

    version: str
    policy_content_hash: str
    indication_unexplained_priority: str = MONITORING_PRIORITY_MEDIUM
    treatment_without_event_priority: str = MONITORING_PRIORITY_MEDIUM
    record_inconsistency_priority: str = MONITORING_PRIORITY_MEDIUM
    treatment_action_priority: str = MONITORING_PRIORITY_MEDIUM
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise CMSliceError("version is required")
        if not self.policy_content_hash.strip():
            raise CMSliceError("policy_content_hash is required")
        if not self.rationale.strip():
            raise CMSliceError("rationale is required")
        for name, val in (
            ("indication_unexplained_priority", self.indication_unexplained_priority),
            ("treatment_without_event_priority", self.treatment_without_event_priority),
            ("record_inconsistency_priority", self.record_inconsistency_priority),
            ("treatment_action_priority", self.treatment_action_priority),
        ):
            if val not in VALID_MONITORING_PRIORITIES:
                raise CMSliceError(f"D02PriorityPolicy.{name}={val!r} invalid")

    def priority_for_subtype(self, subtype: str) -> str:
        if subtype == POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED:
            return self.indication_unexplained_priority
        if subtype == POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD:
            return self.treatment_without_event_priority
        if subtype == POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY:
            return self.record_inconsistency_priority
        if subtype == POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT:
            return self.treatment_action_priority
        return MONITORING_PRIORITY_UNKNOWN


@dataclass(frozen=True)
class CMIntervalDescriptor:
    """Versioned CM interval and rule/check window descriptor (§7)."""

    cm_start: str = ""
    cm_end: str = ""
    ongoing: bool = False
    cutoff: str = ""
    rule_window_start: str = ""
    rule_window_end: str = ""
    rule_window_start_inclusive: Optional[bool] = None
    rule_window_end_inclusive: Optional[bool] = None
    applicable_phase: str = ""

    def normalized_start(self) -> Optional[NormalizedValue]:
        if not self.cm_start.strip():
            return None
        return normalize_partial_date(self.cm_start)

    def normalized_end(self) -> Optional[NormalizedValue]:
        if self.ongoing:
            if not self.cutoff.strip():
                return None
            return normalize_partial_date(self.cutoff)
        if not self.cm_end.strip():
            return None
        return normalize_partial_date(self.cm_end)

    def temporal_window_descriptor(self) -> str:
        end_token = "ongoing" if self.ongoing else (self.cm_end or "none")
        inc: List[str] = []
        if self.rule_window_start_inclusive is True:
            inc.append("si")
        elif self.rule_window_start_inclusive is False:
            inc.append("sx")
        if self.rule_window_end_inclusive is True:
            inc.append("ei")
        elif self.rule_window_end_inclusive is False:
            inc.append("ex")
        inc_token = "-".join(inc) if inc else "inc_unset"
        return (
            f"cm[{self.cm_start or 'none'},{end_token}]"
            f"|ph[{self.applicable_phase or 'none'}]"
            f"|rw[{self.rule_window_start or 'none'},"
            f"{self.rule_window_end or 'none'},{inc_token}]"
        )

# ---------------------------------------------------------------------------
# Semantic-role record (frozen D02 §3.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMSemanticRecord:
    """One semantic-role record carrying row-level content and a source
    locator.  Roles come from active mapping, not fixed table names."""

    role: str
    concept: str
    locator: SourceLocator
    subject_ref: str = ""
    site_ref: str = ""
    event_date_raw: str = ""
    indication_text: str = ""
    treatment_role: str = ""
    action_value: str = ""
    linked_cm_source_event_key: str = ""
    relationship_confirmation: str = CONFIRMATION_UNRESOLVED
    ai_assertion: bool = False
    raw_payload: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise CMSliceError("CMSemanticRecord.role is required")
        if not isinstance(self.locator, SourceLocator):
            raise CMSliceError("locator must be a SourceLocator")
        if self.relationship_confirmation not in (
                CONFIRMATION_CONFIRMED, CONFIRMATION_UNRESOLVED):
            raise CMSliceError("invalid relationship_confirmation")
        if (self.relationship_confirmation == CONFIRMATION_CONFIRMED
                and (not self.action_value.strip()
                     or not self.linked_cm_source_event_key.strip())):
            raise CMSliceError(
                "confirmed treatment relationship requires action_value and "
                "linked_cm_source_event_key")
        object.__setattr__(self, "raw_payload", dict(self.raw_payload))

    def normalized_date(self) -> Optional[NormalizedValue]:
        if not self.event_date_raw.strip():
            return None
        return normalize_partial_date(self.event_date_raw)

    @property
    def stable_source_event_key(self) -> str:
        return f"{self.locator.table_semantic}:{self.locator.record_id}"


@dataclass(frozen=True)
class TreatmentInterpretationEvidence:
    """Versioned source support for one treatment interpretation.

    Competing, independently sourced ``stable_treatment`` and ``new_start``
    interpretations produce a boundary; absence of sufficient evidence stays
    not_evaluable.  Free-text model guesses are not accepted here.
    """

    interpretation: str
    evidence_locator: SourceLocator
    evidence_version: str
    evidence_content_hash: str

    def __post_init__(self) -> None:
        if self.interpretation not in ("stable_treatment", "new_start"):
            raise CMSliceError("unsupported treatment interpretation")
        if not isinstance(self.evidence_locator, SourceLocator):
            raise CMSliceError("interpretation evidence_locator is required")
        if not self.evidence_version.strip():
            raise CMSliceError("interpretation evidence_version is required")
        if not self.evidence_content_hash.strip():
            raise CMSliceError("interpretation evidence_content_hash is required")


@dataclass(frozen=True)
class MedicationEpisode:
    """One CM medication episode derived from an accepted CM source record."""

    episode_id: str
    subject_ref: str
    site_ref: str
    stable_cm_source_event_key: str
    source_locator: SourceLocator
    identity_binding: MedicationIdentityBinding
    interval: CMIntervalDescriptor
    dose: str = ""
    dose_unit: str = ""
    route: str = ""
    frequency: str = ""
    treatment_role: str = ""
    treatment_role_confirmed: bool = False
    indication_text: str = ""
    indication_concept: str = ""
    indication_mappable: Optional[bool] = None
    indication_source_locator: Optional[SourceLocator] = None
    study_phase: str = ""
    study_phase_confirmed: bool = False
    indication_treatment_of_study_event: bool = False
    treatment_interpretation_evidence: Tuple[
        TreatmentInterpretationEvidence, ...] = ()
    stable_treatment_evidence_complete: bool = False
    stable_treatment_duration_confirmed: bool = False
    dose_frequency_unchanged: bool = False

    def __post_init__(self) -> None:
        if not self.episode_id.strip():
            raise CMSliceError("episode_id is required")
        if not self.subject_ref.strip():
            raise CMSliceError("subject_ref is required")
        if not self.stable_cm_source_event_key.strip():
            raise CMSliceError("stable_cm_source_event_key is required")
        if not isinstance(self.source_locator, SourceLocator):
            raise CMSliceError("source_locator must be a SourceLocator")
        if not isinstance(self.identity_binding, MedicationIdentityBinding):
            raise CMSliceError("identity_binding must be MedicationIdentityBinding")
        if not isinstance(self.interval, CMIntervalDescriptor):
            raise CMSliceError("interval must be a CMIntervalDescriptor")
        object.__setattr__(
            self, "treatment_interpretation_evidence",
            tuple(self.treatment_interpretation_evidence))

    @property
    def is_prophylaxis(self) -> bool:
        return self.treatment_role.strip().lower() == "prophylaxis"

    @property
    def is_rescue(self) -> bool:
        return self.treatment_role.strip().lower() == "rescue"

    @property
    def indication_is_vague(self) -> bool:
        return self.indication_text.strip().lower() in _VAGUE_INDICATION_TOKENS

    @property
    def indication_confirmed_mappable(self) -> bool:
        return (bool(self.indication_text.strip())
                and self.indication_mappable is True
                and bool(self.indication_concept.strip()))

    @property
    def stable_treatment_evidence_sufficient(self) -> bool:
        """Stable treatment needs duration/stability AND dose/frequency-
        unchanged evidence, not merely treatment_role_confirmed (§9.1)."""
        return (self.treatment_role_confirmed
                and self.stable_treatment_evidence_complete
                and self.stable_treatment_duration_confirmed
                and self.dose_frequency_unchanged)

# ---------------------------------------------------------------------------
# Identity helpers (frozen D02 §4.2)
# ---------------------------------------------------------------------------

def _stable_cm_event_key(episode: MedicationEpisode) -> str:
    return episode.stable_cm_source_event_key


def _d02_risk_classifier(
    *, episode: MedicationEpisode, ingredient_token: str,
    rule_item_or_concept: str, risk_family: str, signal_type: str,
) -> str:
    """Deterministic D02 classifier (frozen D02 §4.2)."""
    return "|".join((
        "d02", risk_family, _stable_cm_event_key(episode),
        ingredient_token, rule_item_or_concept, signal_type,
    ))


def _d02_risk_scope(
    *, episode: MedicationEpisode, rule: Optional[ProtocolMedicationRule],
    interval: CMIntervalDescriptor,
    identity_binding: MedicationIdentityBinding,
    strategy: "MedicationMatchStrategy",
    rule_item_or_concept: str,
) -> List[str]:
    """Deterministic D02 scope/lineage dimensions (frozen D02 §4.2)."""
    norm_start = interval.normalized_start()
    dp = norm_start.detail if norm_start else "none"
    parts: Set[str] = {
        f"site:{episode.site_ref}" if episode.site_ref else "site:",
        f"tw:{interval.temporal_window_descriptor()}",
        f"dp:{dp}",
        f"dict:{identity_binding.dictionary_name}/"
        f"{identity_binding.dictionary_version}/"
        f"{identity_binding.dictionary_content_hash}",
        f"ua:{D02_UNIT_ALGO_VERSION}",
        f"strat:{strategy.version}/{strategy.strategy_content_hash}",
    }
    if rule is not None:
        parts.add(f"rule:{rule.rule_id}/{rule.rule_version}/"
                  f"{rule.rule_content_hash}")
        parts.add(f"rl:{rule.rule_lineage}")
    else:
        parts.add("rule:none")
    return sorted(parts)


def _build_d02_risk_identity(
    *, project_id: str, episode: MedicationEpisode,
    ingredient_token: str, rule_item_or_concept: str,
    risk_family: str, signal_type: str,
    rule: Optional[ProtocolMedicationRule],
    interval: CMIntervalDescriptor,
    identity_binding: MedicationIdentityBinding,
    strategy: "MedicationMatchStrategy",
) -> RiskIdentity:
    classifier = _d02_risk_classifier(
        episode=episode, ingredient_token=ingredient_token,
        rule_item_or_concept=rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type)
    scope = _d02_risk_scope(
        episode=episode, rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        rule_item_or_concept=rule_item_or_concept)
    return make_risk_identity(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D02_DOMAIN, scope=scope, classifier=classifier)


def _d02_identity_detail(
    *, episode: MedicationEpisode, identity: RiskIdentity,
    ingredient_token: str, rule_item_or_concept: str,
    risk_family: str, signal_type: str,
) -> Dict[str, Any]:
    return {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": _d02_risk_classifier(
            episode=episode, ingredient_token=ingredient_token,
            rule_item_or_concept=rule_item_or_concept,
            risk_family=risk_family, signal_type=signal_type),
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": _stable_cm_event_key(episode),
        "full_locator_id": episode.source_locator.locator_id(),
    }

def _build_d02_candidate(
    *, project_id: str, episode: MedicationEpisode,
    ingredient_token: str, rule_item_or_concept: str,
    risk_family: str, signal_type: str,
    rule: Optional[ProtocolMedicationRule],
    interval: CMIntervalDescriptor,
    identity_binding: MedicationIdentityBinding,
    strategy: "MedicationMatchStrategy",
    snapshot_id: str, monitoring_priority: str,
    match_reason: str, positive_subtype: str = "",
    audience_label: str = "",
) -> Tuple[RiskCandidate, RiskIdentity]:
    identity = _build_d02_risk_identity(
        project_id=project_id, episode=episode,
        ingredient_token=ingredient_token,
        rule_item_or_concept=rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type,
        rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy)
    detail: Dict[str, Any] = {
        "risk_family": risk_family,
        "ingredient_token": ingredient_token,
        "rule_item_or_concept": rule_item_or_concept,
        "signal_type": signal_type,
        "monitoring_priority": monitoring_priority,
        "match_reason": match_reason,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "original_name": identity_binding.original_name,
        "normalized_name": identity_binding.normalized_name,
        "dose": episode.dose,
        "dose_unit": episode.dose_unit,
        "route": episode.route,
        "frequency": episode.frequency,
        "treatment_role": episode.treatment_role,
        "locator_id": episode.source_locator.locator_id(),
    }
    if rule is not None:
        detail.update({
            "rule_id": rule.rule_id,
            "rule_version": rule.rule_version,
            "rule_clause_locator": rule.clause_locator,
            "comparison_field": rule.comparison_field,
            "expected_values": list(rule.expected_values),
            "related_role": rule.related_role,
            "related_concept": rule.related_concept,
            "expected_actions": list(rule.expected_actions),
        })
    detail.update(_d02_identity_detail(
        episode=episode, identity=identity,
        ingredient_token=ingredient_token,
        rule_item_or_concept=rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type))
    rule_lineage = rule.rule_lineage if rule else D02_RULE_LINEAGE_DEFAULT
    candidate = RiskCandidate.from_signal(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D02_DOMAIN, signal_type=signal_type,
        source_snapshot_id=snapshot_id, rule_activation_id=rule_lineage,
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)
    return candidate, identity


# ---------------------------------------------------------------------------
# Expected-set expansion (frozen D02 §4.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMUnitExpanded:
    """One expanded expected EvaluationUnit seed for D02."""

    episode: MedicationEpisode
    ingredient_token: str
    rule_item_or_concept: str
    risk_family: str
    is_ingredient_resolution: bool
    rule: Optional[ProtocolMedicationRule] = None
    interval_override: Optional[CMIntervalDescriptor] = None

    @property
    def interval(self) -> CMIntervalDescriptor:
        return self.interval_override or self.episode.interval

    def signal_type(self) -> str:
        if self.is_ingredient_resolution:
            return INGREDIENT_RESOLUTION_SIGNAL_TYPE
        return self.risk_family

    def build_unit(self, project_id: str,
                   strategy: "MedicationMatchStrategy") -> EvaluationUnit:
        norm_concept = "|".join((
            _stable_cm_event_key(self.episode),
            self.ingredient_token,
            self.rule_item_or_concept,
            self.risk_family,
        ))
        scope_lineage = "|".join(_d02_risk_scope(
            episode=self.episode, rule=self.rule, interval=self.interval,
            identity_binding=self.episode.identity_binding,
            strategy=strategy,
            rule_item_or_concept=self.rule_item_or_concept))
        return EvaluationUnit(
            project_id=project_id, domain_id=D02_DOMAIN,
            scope_type="subject", scope_key=self.episode.subject_ref,
            normalized_concept_or_rule_item=norm_concept,
            temporal_window=self.interval.temporal_window_descriptor(),
            rule_or_knowledge_lineage=scope_lineage,
            unit_algorithm_version=D02_UNIT_ALGO_VERSION)


@dataclass(frozen=True)
class CMExpectedSetExpansion:
    """Result of expanding episodes + rules into the expected unit set."""

    units: Tuple[CMUnitExpanded, ...]
    project_id: str
    strategy: MedicationMatchStrategy
    unit_ids: Tuple[str, ...] = ()
    expected_set_hash: str = ""

    def __post_init__(self) -> None:
        ids = tuple(u.build_unit(self.project_id, self.strategy).unit_id
                    for u in self.units)
        object.__setattr__(self, "unit_ids", ids)
        object.__setattr__(self, "expected_set_hash", _expected_set_hash(ids))

    @property
    def count(self) -> int:
        return len(self.units)

    def has_not_evaluable(self) -> bool:
        return any(u.is_ingredient_resolution for u in self.units)


def _expected_set_hash(unit_ids: Sequence[str]) -> str:
    return "d02-eset-" + content_hash(sorted(set(unit_ids)))


def _rule_item_token(rule: ProtocolMedicationRule) -> str:
    if rule.is_record_consistency:
        return (f"{rule.rule_type}:{rule.rule_id}:"
                f"{rule.target_kind}:{rule.target_value}:"
                f"{rule.comparison_field}")
    if rule.is_action_relationship:
        concept = rule.related_concept or "any"
        return (f"{rule.rule_type}:{rule.rule_id}:"
                f"{rule.target_kind}:{rule.target_value}:"
                f"{rule.related_role}:{concept}")
    return f"{rule.rule_type}:{rule.target_kind}:{rule.target_value}"


def _rule_risk_family(rule: ProtocolMedicationRule) -> str:
    if rule.is_prohibited:
        return "prohibited_medication"
    if rule.is_restricted:
        return "restricted_medication"
    if rule.is_record_consistency:
        return "medication_record_consistency"
    if rule.is_action_relationship:
        return "treatment_action_relationship"
    return f"rule_{rule.rule_type}"


def _indication_check_token(episode: MedicationEpisode) -> str:
    if episode.indication_confirmed_mappable:
        return f"indication:{episode.indication_concept.strip()}"
    return "indication:unmapped"


def expand_cm_expected_set(
    *, project_id: str, episodes: Sequence[MedicationEpisode],
    active_rules: Sequence[ProtocolMedicationRule],
    strategy: MedicationMatchStrategy,
) -> CMExpectedSetExpansion:
    """Expand CM episodes and active rules into the expected unit set
    (frozen D02 §4.1 compound expansion order).

    1. Split identity binding into confirmed ingredients and unresolved
       component slots.
    2. Each active rule x confirmed ingredient -> ingredient x rule unit.
    3. Indication-check unit per confirmed ingredient.
    4. Unresolved component slot -> ingredient_resolution:<slot> unit.
    """
    if not project_id.strip():
        raise CMSliceError("project_id is required")
    expanded: List[CMUnitExpanded] = []
    for episode in episodes:
        binding = episode.identity_binding
        confirmed = binding.confirmed_ingredients
        unresolved = binding.unresolved_components
        for ingredient in confirmed:
            for rule in active_rules:
                expanded.append(CMUnitExpanded(
                    episode=episode,
                    ingredient_token=ingredient.identity_token,
                    rule_item_or_concept=_rule_item_token(rule),
                    risk_family=_rule_risk_family(rule),
                    is_ingredient_resolution=False, rule=rule))
            expanded.append(CMUnitExpanded(
                episode=episode,
                ingredient_token=ingredient.identity_token,
                rule_item_or_concept=_indication_check_token(episode),
                risk_family="indication_check",
                is_ingredient_resolution=False, rule=None))
        for comp in unresolved:
            expanded.append(CMUnitExpanded(
                episode=episode,
                ingredient_token=comp.identity_token,
                rule_item_or_concept=(
                    f"ingredient_resolution:{comp.component_slot}"),
                risk_family=INGREDIENT_RESOLUTION_RISK_FAMILY,
                is_ingredient_resolution=True, rule=None))
    return CMExpectedSetExpansion(
        units=tuple(expanded), project_id=project_id, strategy=strategy)

# ---------------------------------------------------------------------------
# Interval / window comparison (frozen D02 §7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _IntervalOverlap:
    inside: bool
    outside: bool
    possibly_overlap: bool
    comparable: bool
    boundary_reason: str


def _prec_rank(p: str) -> int:
    return {"day": 3, "month": 2, "year": 1, "none": 0}.get(p, 0)


def _nv_precision(nv: Optional[NormalizedValue]) -> str:
    if nv is None or not nv.normalized:
        return "none"
    s = str(nv.normalized)
    parts = s.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if len(parts) >= 1 and len(parts[0]) == 4:
        return "year"
    return "none"


def _compare_interval_to_window(
    interval: CMIntervalDescriptor, rule: ProtocolMedicationRule,
) -> _IntervalOverlap:
    """Compare the CM interval against the rule's effective window (§7).

    Full-day precision with explicit inclusivity determines inside/outside.
    Unstated endpoint inclusivity -> boundary.  Partial month/year dates
    that possibly overlap -> boundary.  Incomparable anchors -> not_evaluable.
    """
    cm_start = interval.normalized_start()
    if cm_start is None:
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False,
            boundary_reason="CM start date missing or unparseable")
    rw_start_raw = rule.window_start or interval.rule_window_start
    rw_end_raw = rule.window_end or interval.rule_window_end
    rw_start = (normalize_partial_date(rw_start_raw)
                if rw_start_raw.strip() else None)
    rw_end = (normalize_partial_date(rw_end_raw)
              if rw_end_raw.strip() else None)
    if rw_start is None and rw_end is None:
        return _IntervalOverlap(
            inside=True, outside=False, possibly_overlap=False,
            comparable=True, boundary_reason="")
    cm_end_eff = interval.normalized_end()
    if cm_end_eff is None and not interval.ongoing:
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="CM end date missing; possibly overlaps window")
    p_start = _nv_precision(cm_start)
    p_end = _nv_precision(cm_end_eff)
    p_rw_start = _nv_precision(rw_start)
    p_rw_end = _nv_precision(rw_end)
    min_prec = min(_prec_rank(p_start), _prec_rank(p_end),
                   _prec_rank(p_rw_start), _prec_rank(p_rw_end))
    if min_prec < 3:
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason=(
                f"partial date precision (cm_start={p_start},"
                f"cm_end={p_end},rw_start={p_rw_start},"
                f"rw_end={p_rw_end}); possibly overlaps window"))
    import datetime
    try:
        cs = datetime.date.fromisoformat(str(cm_start.normalized)[:10])
        ce = (datetime.date.fromisoformat(str(cm_end_eff.normalized)[:10])
              if cm_end_eff and cm_end_eff.normalized else None)
        rws = (datetime.date.fromisoformat(str(rw_start.normalized)[:10])
               if rw_start and rw_start.normalized else None)
        rwe = (datetime.date.fromisoformat(str(rw_end.normalized)[:10])
               if rw_end and rw_end.normalized else None)
    except (ValueError, TypeError):
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False,
            boundary_reason="day-precision dates unparseable")
    start_inc = rule.window_start_inclusive
    end_inc = rule.window_end_inclusive
    if rws is not None and start_inc is None and cs == rws:
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="CM start on rule window start endpoint; "
                            "inclusivity unstated")
    if (rwe is not None and end_inc is None and ce is not None
            and ce == rwe):
        return _IntervalOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="CM end on rule window end endpoint; "
                            "inclusivity unstated")
    after_start = True
    if rws is not None:
        after_start = cs >= rws if start_inc is True else cs > rws
    before_end = True
    if rwe is not None and ce is not None:
        before_end = ce <= rwe if end_inc is True else ce < rwe
    inside = after_start and before_end
    definitely_outside = False
    if rws is not None and ce is not None:
        definitely_outside = ce < rws
    if rwe is not None:
        definitely_outside = definitely_outside or (cs > rwe)
    if inside:
        return _IntervalOverlap(
            inside=True, outside=False, possibly_overlap=False,
            comparable=True, boundary_reason="")
    if definitely_outside:
        return _IntervalOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    return _IntervalOverlap(
        inside=False, outside=False, possibly_overlap=True,
        comparable=True, boundary_reason="interval possibly overlaps window")


# ---------------------------------------------------------------------------
# Rule matching (frozen D02 §6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _RuleMatchOutcome:
    matched: bool
    match_reason: str
    target_granularity_satisfied: bool
    fail_closed_reason: str = ""


def _match_rule_to_ingredient(
    rule: ProtocolMedicationRule, ingredient: IngredientBinding,
) -> _RuleMatchOutcome:
    """Match one rule against one ingredient (frozen D02 §6).

    Ingredient-exact match precedes category membership.  A super-class
    code only proves its own super-class; a rule requiring a finer
    product type is not_evaluable when only the super-class is bound.
    """
    if ingredient.is_unresolved:
        return _RuleMatchOutcome(
            matched=False, match_reason="",
            target_granularity_satisfied=False,
            fail_closed_reason="unresolved component slot")
    if rule.target_kind == TARGET_KIND_INGREDIENT:
        if rule.target_value.strip() == ingredient.ingredient.strip():
            return _RuleMatchOutcome(
                matched=True,
                match_reason=f"ingredient-exact match: {ingredient.ingredient}",
                target_granularity_satisfied=True)
        return _RuleMatchOutcome(
            matched=False,
            match_reason="ingredient does not exactly match target",
            target_granularity_satisfied=True)
    if rule.target_kind == TARGET_KIND_CATEGORY:
        if rule.target_value in ingredient.categories:
            return _RuleMatchOutcome(
                matched=True,
                match_reason=f"explicit category membership: {rule.target_value}",
                target_granularity_satisfied=True)
        return _RuleMatchOutcome(
            matched=False, match_reason="ingredient not in target category",
            target_granularity_satisfied=True)
    if rule.target_kind == TARGET_KIND_PRODUCT_TYPE:
        if rule.target_value in ingredient.product_types:
            return _RuleMatchOutcome(
                matched=True,
                match_reason=f"explicit product-type membership: {rule.target_value}",
                target_granularity_satisfied=True)
        return _RuleMatchOutcome(
            matched=False, match_reason="product type not confirmed",
            target_granularity_satisfied=False,
            fail_closed_reason=(
                f"rule requires product_type {rule.target_value!r}; "
                f"only categories {ingredient.categories} bound"))
    return _RuleMatchOutcome(
        matched=False, match_reason="unknown target kind",
        target_granularity_satisfied=False,
        fail_closed_reason=f"unknown target_kind {rule.target_kind!r}")
@dataclass(frozen=True)
class _IndicationAssessment:
    has_mappable_indication: bool
    treatment_role_confirmed: bool
    is_prophylaxis_or_rescue: bool
    matching_event_records: Tuple[CMSemanticRecord, ...]
    temporally_uninterpretable: bool
    indication_concept: str
    indication_vague: bool
    is_treatment_of_study_event: bool


def _assess_indication(
    episode: MedicationEpisode,
    evidence_records: Sequence[CMSemanticRecord],
    strategy: MedicationMatchStrategy,
) -> _IndicationAssessment:
    """Assess the episode indication against AE/MH/diagnosis records (§8).

    Subject ownership: only records with the exact same ``subject_ref``
    may act as counterevidence; another participant's record is never
    used.  Temporal: a same-concept record whose date cannot be
    interpreted fails closed rather than silently matching.
    """
    event_roles = {"reported_ae", "reported_mh", "diagnosis", "symptom_event"}
    matching: List[CMSemanticRecord] = []
    temporally_uninterpretable = False
    concept = ""
    if episode.indication_confirmed_mappable:
        concept = episode.indication_concept.strip()
        for rec in evidence_records:
            if rec.role not in event_roles:
                continue
            # Subject ownership: exact subject_ref match required.
            if rec.subject_ref != episode.subject_ref:
                continue
            if not strategy.indication_concepts_equivalent(concept, rec.concept):
                continue
            # Temporal: when the record carries a date, it must be
            # interpretable; an uninterpretable date fails closed.
            if rec.event_date_raw.strip():
                nv = rec.normalized_date()
                if nv is None or not nv.normalized:
                    temporally_uninterpretable = True
                    continue
            matching.append(rec)
    return _IndicationAssessment(
        has_mappable_indication=episode.indication_confirmed_mappable,
        treatment_role_confirmed=episode.treatment_role_confirmed,
        is_prophylaxis_or_rescue=(episode.is_prophylaxis or episode.is_rescue),
        matching_event_records=tuple(matching),
        temporally_uninterpretable=temporally_uninterpretable,
        indication_concept=concept,
        indication_vague=episode.indication_is_vague,
        is_treatment_of_study_event=episode.indication_treatment_of_study_event)


def _find_ingredient(
    expanded: CMUnitExpanded,
    identity_binding: MedicationIdentityBinding,
) -> IngredientBinding:
    """Locate the IngredientBinding whose identity_token matches the
    expanded unit's ingredient_token."""
    for ib in identity_binding.ingredients:
        if ib.identity_token == expanded.ingredient_token:
            return ib
    raise CMSliceError(
        f"no IngredientBinding matches token {expanded.ingredient_token!r}")

# ---------------------------------------------------------------------------
# CMUnitResult (frozen D02 §2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMUnitResult:
    """The evaluation outcome for one D02 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol AND can
    materialize a full ``UnitEvaluation`` for the CoverageLedger.
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    monitoring_priority: str
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    not_evaluable_reason: str = ""
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    journey_markers: Tuple[Dict[str, Any], ...] = ()
    cross_domain_evidence_refs: Tuple[CrossDomainEvidenceRef, ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise CMSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise CMSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        object.__setattr__(self, "r2_candidates", tuple(self.r2_candidates))
        object.__setattr__(self, "risk_candidate_refs",
                           tuple(self.risk_candidate_refs))
        object.__setattr__(self, "risk_instance_refs",
                           tuple(self.risk_instance_refs))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "source_record_refs",
                           tuple(self.source_record_refs))
        object.__setattr__(self, "query_refs", tuple(self.query_refs))
        object.__setattr__(self, "journey_markers",
                           tuple(self.journey_markers))
        object.__setattr__(self, "cross_domain_evidence_refs",
                           tuple(self.cross_domain_evidence_refs))

    def all_source_locator_ids(self) -> Tuple[str, ...]:
        ids: List[str] = []
        for ref in self.source_record_refs:
            ids.append(ref.locator.locator_id())
        for item in self.evidence:
            ids.append(item.locator.locator_id())
        for ref in self.risk_candidate_refs:
            if ref.locator is not None:
                ids.append(ref.locator.locator_id())
        return tuple(sorted(set(ids)))

    def to_unit_evaluation(
        self, *, l0_status: str = L0CoverageStatus.COVERED,
        provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity in (L1bEvidencePolarity.SUPPORTING,
                                L1bEvidencePolarity.COUNTEREVIDENCE,
                                L1bEvidencePolarity.CONTEXT):
                if ev.polarity not in polarities:
                    polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(polarities),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Episode rollup (frozen D02 §4.1 step 4, §11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMEpisodeRollup:
    """Read-only episode rollup preserving all child unit ids and flags."""

    episode_id: str
    subject_ref: str
    child_unit_ids: Tuple[str, ...]
    has_positive: bool
    has_boundary: bool
    has_not_evaluable: bool
    has_negative: bool
    source_record_count: int

# ---------------------------------------------------------------------------
# Query construction (frozen D02 §9.3)
# ---------------------------------------------------------------------------

def _target_kind_label(kind: str) -> str:
    return {TARGET_KIND_INGREDIENT: "成分", TARGET_KIND_CATEGORY: "类别",
            TARGET_KIND_PRODUCT_TYPE: "产品类型"}.get(kind, kind)


def _match_reason_finding(rule: ProtocolMedicationRule) -> str:
    if rule.target_kind == TARGET_KIND_INGREDIENT:
        return f"含目标成分 {rule.target_value}"
    if rule.target_kind == TARGET_KIND_CATEGORY:
        return f"属于目标类别 {rule.target_value}"
    if rule.target_kind == TARGET_KIND_PRODUCT_TYPE:
        return f"属于目标产品类型 {rule.target_value}"
    return "命中目标"


def _query_text(
    *, subtype: str, subject_ref: str, episode: MedicationEpisode,
    rule: Optional[ProtocolMedicationRule],
    identity_binding: MedicationIdentityBinding,
    relationship_record: Optional[CMSemanticRecord] = None,
) -> Tuple[str, str, str]:
    """Build the three-part Chinese Query text (frozen D02 §9.3)."""
    interval = episode.interval
    start_txt = interval.cm_start or "（开始日期缺失）"
    end_txt = "持续中" if interval.ongoing else (interval.cm_end or "（结束日期缺失）")
    cm_locator = episode.source_locator.locator_id()
    if subtype in (POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
                   POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH):
        r = rule
        basis = (f"方案规则 {r.rule_id} 规定{r.applicable_phases[0]}阶段"
                 f"{'禁用' if r.is_prohibited else '限制'}目标"
                 f"{_target_kind_label(r.target_kind)}"
                 f"（条款 {r.clause_locator}）。")
        finding = (f"参与者 {subject_ref} 在 {start_txt} 至 {end_txt} 使用"
                   f"{identity_binding.original_name}；受控绑定"
                   f"{identity_binding.dictionary_name}-"
                   f"{identity_binding.dictionary_version} 显示其"
                   f"{_match_reason_finding(r)}，记录定位 {cm_locator}。")
        action = ("请核实该用药是否符合方案要求以及是否构成方案偏离；"
                  "如需，请按相应流程处理。")
        return basis, finding, action
    if subtype in (POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
                   POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED):
        basis = "治疗用药通常应与相应医学事件或诊断记录一致。"
        indication_txt = episode.indication_text or "（适应证未具体记录）"
        finding = (f"参与者 {subject_ref} 在 {start_txt} 至 {end_txt} 使用"
                   f"{identity_binding.original_name} 治疗 {indication_txt}；"
                   f"当前 AE/MH/诊断中未找到可对应记录。"
                   f"记录定位 {cm_locator}。")
        action = ("请核实用药原因及 AE/MH/诊断记录是否完整，"
                  "并按核实结果补充或更正。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY:
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        actual = _episode_record_value(episode, rule.comparison_field)
        expected = "、".join(rule.expected_values)
        basis = (f"方案规则 {rule.rule_id}（条款 {rule.clause_locator}）要求"
                 f"{label}为 {expected}。")
        finding = (f"参与者 {subject_ref} 的 {identity_binding.original_name}"
                   f"{label}记录为 {actual}，与方案要求不一致。"
                   f"记录定位 {cm_locator}。")
        action = ("请核实用药信息是否准确以及是否构成方案偏离；"
                  "如需，请按核实结果更正并按相应流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT:
        expected = "、".join(rule.expected_actions)
        basis = (f"方案规则 {rule.rule_id}（条款 {rule.clause_locator}）要求"
                 f"相关处置为 {expected}。")
        actual = (relationship_record.action_value
                  if relationship_record is not None else "（记录不明确）")
        related_locator = (relationship_record.locator.locator_id()
                           if relationship_record is not None else "未定位")
        finding = (f"参与者 {subject_ref} 的 {identity_binding.original_name} 用药"
                   f"与 {rule.related_role} 处置记录存在冲突；处置记录为"
                   f" {actual}。CM 定位 {cm_locator}，关联记录定位"
                   f" {related_locator}。")
        action = ("请核实用药与处置记录的关系以及是否构成方案偏离；"
                  "如需，请按核实结果补充或更正并按相应流程处理。")
        return basis, finding, action
    raise CMSliceError(f"no Query template for subtype {subtype!r}")


def _build_query_ref(
    *, query_id: str, unit_id: str, subtype: str, subject_ref: str,
    episode: MedicationEpisode, rule: Optional[ProtocolMedicationRule],
    identity_binding: MedicationIdentityBinding, candidate_id: str,
    source_locator_ids: Sequence[str],
    relationship_record: Optional[CMSemanticRecord] = None,
) -> QueryDraftRef:
    basis_body, finding_body, action_body = _query_text(
        subtype=subtype, subject_ref=subject_ref, episode=episode,
        rule=rule, identity_binding=identity_binding,
        relationship_record=relationship_record)
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=f"依据：{basis_body}",
        finding=f"发现：{finding_body}",
        action=f"行动项：{action_body}",
        source_locator_ids=tuple(source_locator_ids),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Cross-domain evidence (frozen D02 §3.3, §8)
# ---------------------------------------------------------------------------

def _build_cm_indication_ref(
    *, evidence_ref_id: str, producer_unit_id: str,
    episode: MedicationEpisode,
    indication_assessment: _IndicationAssessment,
) -> CrossDomainEvidenceRef:
    """Build a CrossDomainEvidenceRef(role=cm_indication) for D01 (§8)."""
    locator = episode.indication_source_locator or episode.source_locator
    context: Dict[str, Any] = {
        "subject_ref": episode.subject_ref,
        "site_ref": episode.site_ref,
        "treatment_role": episode.treatment_role,
        "indication_text": episode.indication_text,
        "indication_concept": indication_assessment.indication_concept,
        "ingredient_status": (
            "confirmed" if episode.identity_binding.confirmed_ingredients
            else "unresolved"),
        "original_name": episode.identity_binding.original_name,
    }
    ch = cross_domain_evidence_content_hash(
        source_locator=locator, evidence_role="cm_indication",
        claim_scope="treatment", context_payload=context)
    return CrossDomainEvidenceRef(
        evidence_ref_id=evidence_ref_id, producer_domain=D02_DOMAIN,
        consumer_domain="D01_aemh", evidence_role="cm_indication",
        source_locator=locator, producer_unit_id=producer_unit_id,
        content_hash=ch, claim_scope="treatment",
        context_payload=tuple(context.items()))


# ---------------------------------------------------------------------------
# Evidence / source-record / journey helpers
# ---------------------------------------------------------------------------

def _make_evidence_item(
    *, evidence_id: str, polarity: str, locator: SourceLocator,
    evidence_role: str, rule_lineage: str,
    uncertainty_note: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id, polarity=polarity, locator=locator,
        evidence_role=evidence_role, rule_lineage=rule_lineage,
        uncertainty_note=uncertainty_note)


def _dedup_locator_ids(*locators: Optional[SourceLocator]) -> Tuple[str, ...]:
    """Return deduplicated sorted locator ids from the given locators,
    skipping None.  Used for Query source_locator_ids provenance (§9.3)."""
    ids: List[str] = []
    for loc in locators:
        if loc is not None:
            ids.append(loc.locator_id())
    return tuple(sorted(set(ids)))


def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _journey_marker(
    *, episode: MedicationEpisode, unit_id: str, risk_family: str,
    audience_label: str, monitoring_priority: str,
) -> Dict[str, Any]:
    interval = episode.interval
    return {
        "domain_track": "cm", "event_id": episode.episode_id,
        "subject_ref": episode.subject_ref, "start": interval.cm_start,
        "end": interval.cm_end, "ongoing": interval.ongoing,
        "episode_id": episode.episode_id, "unit_id": unit_id,
        "risk_family": risk_family, "audience_label": audience_label,
        "monitoring_priority": monitoring_priority,
        "source_locator_id": episode.source_locator.locator_id(),
        "display_label": episode.identity_binding.original_name,
    }

# ---------------------------------------------------------------------------
# Core evaluation: evaluate_cm_unit
# ---------------------------------------------------------------------------

def evaluate_cm_unit(
    *, project_id: str, expanded: CMUnitExpanded,
    evidence_records: Sequence[CMSemanticRecord] = (),
    strategy: Optional[MedicationMatchStrategy] = None,
    priority_policy: Optional[D02PriorityPolicy] = None,
    snapshot_id: str = "",
    ip_exposure_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
    relationship_coverage_complete: bool = False,
) -> CMUnitResult:
    """Evaluate one D02 CM expanded unit (frozen D02 §5).

    ``linkage_coverage_complete`` (default False = fail-closed) is the
    explicit accepted proof that the relevant AE/MH/diagnosis source
    coverage for this subject is complete.  An empty ``evidence_records``
    alone cannot prove a complete search with no matching event; a
    positive or definitive-negative indication conclusion requires this
    proof (frozen D02 §8).

    ``relationship_coverage_complete`` independently proves that the
    relevant accepted AE/MH/IP action sources are complete before an
    action-relationship rule may conclude positive or negative.  Explicit
    stable CM linkage, subject/site identity and a comparable day-level
    event date remain mandatory.
    """
    if strategy is None:
        raise CMSliceError("strategy is required for evaluate_cm_unit")
    episode = expanded.episode
    identity_binding = episode.identity_binding
    interval = expanded.interval
    unit = expanded.build_unit(project_id, strategy)
    unit_id = unit.unit_id

    # -- ingredient_resolution: mandatory not_evaluable, no candidate --
    if expanded.is_ingredient_resolution:
        src_ref = _make_source_record_ref(episode.source_locator)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=(
                "复方药物的某项成分尚未确认，无法评价该成分是否命中"
                "禁用或限制用药规则"),
            source_record_refs=(src_ref,))

    # -- CM/IP role conflict check (frozen D02 §3.1) --
    for ip_rec in ip_exposure_records:
        if ip_rec.locator.record_id == episode.source_locator.record_id:
            src_ref = _make_source_record_ref(episode.source_locator)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=(
                    "同一来源行同时映射为 CM 与 IP/EX，角色互斥冲突"),
                source_record_refs=(src_ref,))

    rule = expanded.rule
    if rule is not None:
        return _evaluate_rule_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, identity_binding=identity_binding,
            interval=interval, rule=rule, strategy=strategy,
            snapshot_id=snapshot_id,
            evidence_records=tuple(evidence_records)
                + tuple(ip_exposure_records),
            relationship_coverage_complete=relationship_coverage_complete)

    if expanded.risk_family == "indication_check":
        return _evaluate_indication_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, identity_binding=identity_binding,
            interval=interval, strategy=strategy,
            priority_policy=priority_policy, snapshot_id=snapshot_id,
            evidence_records=evidence_records,
            linkage_coverage_complete=linkage_coverage_complete)

    src_ref = _make_source_record_ref(episode.source_locator)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=(
            f"未识别的用药核查类型 {expanded.risk_family!r}，当前无法评价"),
        source_record_refs=(src_ref,))


def _evaluate_rule_unit(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy, snapshot_id: str,
    evidence_records: Sequence[CMSemanticRecord],
    relationship_coverage_complete: bool,
) -> CMUnitResult:
    """Evaluate a rule-match unit (prohibited/restricted/etc.).

    Phase applicability (§5.5): a confirmed study phase that is outside
    the rule's ``applicable_phases`` is ``not_applicable`` with no
    candidate/Query.  A missing or unconfirmed phase is ``not_evaluable``.
    Identity non-match (§6): a confirmed ingredient-exact binding that
    differs from an ingredient-exact rule target is a deterministic
    ``negative`` with a complete identity binding; category/product-type
    absence remains fail-closed.
    """
    ingredient = _find_ingredient(expanded, identity_binding)
    src_ref = _make_source_record_ref(episode.source_locator)
    rule_lineage = rule.rule_lineage

    # -- Phase applicability (§5.5): fail closed for every inconsistent
    # -- or unconfirmed phase state.  Only (confirmed=True, phase non-empty)
    # -- may proceed; confirmed phase outside applicable_phases is
    # -- not_applicable; all other states are not_evaluable.
    if episode.study_phase_confirmed and episode.study_phase.strip():
        if episode.study_phase.strip() not in rule.applicable_phases:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-phase-na",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=(
                    f"已确认研究阶段 {episode.study_phase!r} 不在规则 "
                    f"{rule.rule_id} 适用阶段 {list(rule.applicable_phases)} 内"))
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
    else:
        # Every other combination is not_evaluable: phase missing,
        # blank, or confirmed flag inconsistent with phase content.
        if not episode.study_phase.strip():
            phase_note = "研究阶段缺失或为空，无法判定规则适用性"
        else:
            phase_note = (
                f"研究阶段 {episode.study_phase!r} 未获确认，"
                f"无法判定规则适用性")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-phase-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=phase_note)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=phase_note,
            evidence=(ev,), source_record_refs=(src_ref,))

    match = _match_rule_to_ingredient(rule, ingredient)

    # Fail-closed: target granularity not satisfiable -> not_evaluable.
    if not match.target_granularity_satisfied:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-granularity",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=identity_binding.evidence_locator,
            evidence_role="medication_identity",
            rule_lineage=rule_lineage,
            uncertainty_note=match.fail_closed_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=match.fail_closed_reason,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Definitive ingredient-exact non-match -> negative (complete identity).
    if not match.matched and rule.target_kind == TARGET_KIND_INGREDIENT:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-exact-nomatch",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"已确认成分 {ingredient.ingredient!r} 与规则目标成分 "
                f"{rule.target_value!r} 精确不同，身份完整可核实"))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    if not match.matched:
        overlap = _compare_interval_to_window(interval, rule)
        if (overlap.comparable and overlap.outside
                and not overlap.possibly_overlap):
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-outside",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=overlap.boundary_reason or "窗口外")
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NEGATIVE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
        ne_reason = (
            f"类别/产品类型未命中规则 {rule.rule_id}，"
            f"但身份不足以判 negative：{match.match_reason}")
        if not overlap.comparable:
            ne_reason = overlap.boundary_reason
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-unmatched",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # A blocking restricted-condition coverage gap outranks a temporal
    # boundary.  Check only the fail-closed state here; confirmed met/unmet
    # remains materialized after the interval is known to overlap.
    if rule.is_restricted:
        cond_state, cond_reason = _check_restricted_conditions(rule, episode)
        if cond_state == RESTRICTED_COND_UNEVALUABLE:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ne",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=cond_reason)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=cond_reason,
                evidence=(ev,), source_record_refs=(src_ref,))
        if cond_state == RESTRICTED_COND_BOUNDARY:
            return _build_rule_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                episode=episode, rule=rule, strategy=strategy,
                identity_binding=identity_binding, interval=interval,
                boundary_reason=cond_reason, src_ref=src_ref,
                rule_lineage=rule_lineage, snapshot_id=snapshot_id)

    # Matched: check interval overlap.
    overlap = _compare_interval_to_window(interval, rule)
    if not overlap.comparable:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-interval-ne",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=overlap.boundary_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=overlap.boundary_reason,
            evidence=(ev,), source_record_refs=(src_ref,))
    if overlap.possibly_overlap and not overlap.inside:
        return _build_rule_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            boundary_reason=overlap.boundary_reason,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)
    if overlap.outside:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-outside-matched",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note="命中成分/类别但区间在适用窗外")
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Matched AND inside window: evaluate the rule-specific medical contract.
    if rule.is_record_consistency:
        return _evaluate_record_consistency_rule(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)
    if rule.is_action_relationship:
        return _evaluate_action_relationship_rule(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            src_ref=src_ref, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id, evidence_records=evidence_records,
            relationship_coverage_complete=relationship_coverage_complete)

    # Matched AND inside window: positive (prohibited) or check conditions
    # (restricted/allowed-condition rules).
    return _build_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        match_reason=match.match_reason, src_ref=src_ref,
        rule_lineage=rule_lineage, snapshot_id=snapshot_id)


_RECORD_FIELD_LABELS: Dict[str, str] = {
    "dose": "剂量",
    "dose_unit": "剂量单位",
    "route": "给药途径",
    "frequency": "给药频次",
    "start": "开始日期",
    "end": "结束日期",
    "treatment_role": "治疗角色",
}


def _canonical_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _episode_record_value(episode: MedicationEpisode, field_name: str) -> str:
    if field_name == "start":
        return episode.interval.cm_start
    if field_name == "end":
        return "ongoing" if episode.interval.ongoing else episode.interval.cm_end
    return str(getattr(episode, field_name, ""))


def _canonical_record_value(field_name: str, value: str) -> Optional[str]:
    """Return a comparable canonical value or None when it is insufficient."""
    if not value.strip():
        return None
    if field_name in ("start", "end"):
        if field_name == "end" and _canonical_text(value) == "ongoing":
            return "ongoing"
        normalized = normalize_partial_date(value)
        if not normalized.normalized or _nv_precision(normalized) != "day":
            return None
        return str(normalized.normalized)
    return _canonical_text(value)


def _not_evaluable_rule_result(
    *, unit_id: str, episode: MedicationEpisode, src_ref: SourceRecordRef,
    rule_lineage: str, reason: str, locator: Optional[SourceLocator] = None,
    evidence_role: str = "recorded_cm",
) -> CMUnitResult:
    ev = _make_evidence_item(
        evidence_id=f"ev-{unit_id}-rule-ne",
        polarity=L1bEvidencePolarity.CONTEXT,
        locator=locator or episode.source_locator,
        evidence_role=evidence_role, rule_lineage=rule_lineage,
        uncertainty_note=reason)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=reason, evidence=(ev,),
        source_record_refs=(src_ref,))


def _negative_rule_result(
    *, unit_id: str, episode: MedicationEpisode, src_ref: SourceRecordRef,
    rule_lineage: str, reason: str,
    evidence_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    evidence: List[EvidenceItem] = [
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-rule-negative",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator, evidence_role="recorded_cm",
            rule_lineage=rule_lineage, uncertainty_note=reason)
    ]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-related-negative-{index}",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=reason)
        for index, record in enumerate(evidence_records)
    )
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NEGATIVE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        evidence=tuple(evidence), source_record_refs=(src_ref,))


def _evaluate_record_consistency_rule(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str,
) -> CMUnitResult:
    actual_raw = _episode_record_value(episode, rule.comparison_field)
    actual = _canonical_record_value(rule.comparison_field, actual_raw)
    expected = tuple(
        _canonical_record_value(rule.comparison_field, value)
        for value in rule.expected_values)
    if actual is None or any(value is None for value in expected):
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"{label}缺失或精度不足，无法与方案要求可靠比较")
    if actual in expected:
        label = _RECORD_FIELD_LABELS[rule.comparison_field]
        return _negative_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"{label}与方案规则 {rule.rule_id} 的要求一致")
    label = _RECORD_FIELD_LABELS[rule.comparison_field]
    reason = (
        f"{label}记录为 {actual_raw!r}，与方案规则 {rule.rule_id} 的"
        f"允许值 {list(rule.expected_values)!r} 明确不一致")
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id,
        subtype=POSITIVE_SUBTYPE_MEDICATION_RECORD_INCONSISTENCY,
        match_reason=reason)


def _record_inside_episode_window(
    record: CMSemanticRecord, interval: CMIntervalDescriptor,
) -> Optional[bool]:
    event = record.normalized_date()
    start = interval.normalized_start()
    end = interval.normalized_end()
    if any(value is None or _nv_precision(value) != "day"
           for value in (event, start, end)):
        return None
    event_value = str(event.normalized)
    return str(start.normalized) <= event_value <= str(end.normalized)


def _evaluate_action_relationship_rule(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str,
    evidence_records: Sequence[CMSemanticRecord],
    relationship_coverage_complete: bool,
) -> CMUnitResult:
    if not relationship_coverage_complete:
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason="AE/MH/IP 处置关系来源覆盖不完整，无法作出确定结论")

    related_by_locator: Dict[str, CMSemanticRecord] = {}
    for record in evidence_records:
        if (record.subject_ref == episode.subject_ref
                and record.site_ref == episode.site_ref
                and record.role == rule.related_role
                and record.linked_cm_source_event_key
                    == episode.stable_cm_source_event_key
                and (not rule.related_concept
                     or record.concept == rule.related_concept)):
            related_by_locator[record.locator.locator_id()] = record
    related = tuple(related_by_locator[key]
                    for key in sorted(related_by_locator))
    if not related:
        return _not_evaluable_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=("未找到带有明确 CM 关联键的处置记录，不能把缺少关联"
                    "自动判为处置关系冲突"))
    for record in related:
        if record.relationship_confirmation != CONFIRMATION_CONFIRMED:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="处置记录与 CM 的关联尚未确认，无法评价",
                locator=record.locator, evidence_role=record.role)
        inside = _record_inside_episode_window(record, interval)
        if inside is None:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="处置记录日期缺失或精度不足，无法确认同一时间窗",
                locator=record.locator, evidence_role=record.role)
        if not inside:
            return _not_evaluable_rule_result(
                unit_id=unit_id, episode=episode, src_ref=src_ref,
                rule_lineage=rule_lineage,
                reason="关联处置记录不在本次用药时间窗内，无法判定同窗关系",
                locator=record.locator, evidence_role=record.role)

    expected = {_canonical_text(action) for action in rule.expected_actions}
    matching = tuple(
        record for record in related
        if _canonical_text(record.action_value) in expected)
    conflicting = tuple(record for record in related if record not in matching)
    if matching and conflicting:
        reason = "同一用药关联中同时存在一致与冲突的处置记录，当前无法唯一判断"
        return _build_rule_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            episode=episode, rule=rule, strategy=strategy,
            identity_binding=identity_binding, interval=interval,
            boundary_reason=reason, src_ref=src_ref,
            rule_lineage=rule_lineage, snapshot_id=snapshot_id,
            related_records=related)
    if matching:
        return _negative_rule_result(
            unit_id=unit_id, episode=episode, src_ref=src_ref,
            rule_lineage=rule_lineage,
            reason=f"用药与 {rule.related_role} 处置记录关系一致",
            evidence_records=matching)

    actual_actions = sorted({record.action_value for record in conflicting})
    reason = (
        f"同一用药及时间窗内的 {rule.related_role} 处置记录为"
        f" {actual_actions!r}，与规则 {rule.rule_id} 要求的"
        f" {list(rule.expected_actions)!r} 明确冲突")
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id,
        subtype=POSITIVE_SUBTYPE_TREATMENT_ACTION_RELATIONSHIP_INCONSISTENT,
        match_reason=reason, related_records=conflicting)


RESTRICTED_COND_UNEVALUABLE = "unevaluable"
RESTRICTED_COND_MET = "met"
RESTRICTED_COND_UNMET = "unmet"
RESTRICTED_COND_BOUNDARY = "boundary"


def _check_restricted_conditions(
    rule: ProtocolMedicationRule, episode: MedicationEpisode,
) -> Tuple[str, str]:
    """Check restricted-rule allowed conditions (four-state).

    Returns ``(state, reason)`` where state is one of:
    - ``met``: the allowed condition is confirmed satisfied -> negative.
    - ``unmet``: the allowed condition is confirmed NOT satisfied -> positive.
    - ``unevaluable``: role/evidence missing or an unknown condition token
      -> not_evaluable (fail-closed).
    - ``boundary``: stable-treatment and new-start interpretations each have
      versioned source support and cannot yet be uniquely selected.

    Stable treatment requires explicit duration/stability AND
    dose/frequency-unchanged evidence; ``treatment_role_confirmed`` alone
    is insufficient.  Rescue/prophylaxis require a confirmed role.
    Unknown ``allowed_conditions`` tokens fail closed.
    """
    known_tokens = {"stable_treatment", "rescue", "prophylaxis"}
    conditions_to_check: List[str] = []
    if rule.allowed_conditions:
        conditions_to_check = list(rule.allowed_conditions)
        unknown = [c for c in conditions_to_check if c not in known_tokens]
        if unknown:
            return (RESTRICTED_COND_UNEVALUABLE,
                    f"未知的限制条件令牌 {unknown!r}，无法评价")
    elif rule.stable_treatment_exception:
        conditions_to_check = ["stable_treatment"]
    elif rule.rescue_exception:
        conditions_to_check = ["rescue"]
    elif rule.prophylaxis_exception:
        conditions_to_check = ["prophylaxis"]

    for cond in conditions_to_check:
        if cond == "stable_treatment":
            interpretations = {
                item.interpretation
                for item in episode.treatment_interpretation_evidence
            }
            if {"stable_treatment", "new_start"}.issubset(interpretations):
                return (
                    RESTRICTED_COND_BOUNDARY,
                    "稳定治疗与新启用两种解释均有来源支持，当前无法唯一确定",
                )
            if (not episode.treatment_role_confirmed
                    or not episode.stable_treatment_evidence_complete):
                return (RESTRICTED_COND_UNEVALUABLE,
                        "稳定治疗证据不完整（角色/时长/剂量频次未确认）")
            if not episode.stable_treatment_evidence_sufficient:
                return (RESTRICTED_COND_UNMET,
                        "已完成稳定治疗条件核对，但时长、稳定性或剂量频次条件不满足")
        elif cond == "rescue":
            if not episode.treatment_role_confirmed:
                return (RESTRICTED_COND_UNEVALUABLE, "治疗角色未确认")
            if not episode.is_rescue:
                return (RESTRICTED_COND_UNMET, "抢救角色未满足")
        elif cond == "prophylaxis":
            if not episode.treatment_role_confirmed:
                return (RESTRICTED_COND_UNEVALUABLE, "治疗角色未确认")
            if not episode.is_prophylaxis:
                return (RESTRICTED_COND_UNMET, "预防角色未满足")
    return RESTRICTED_COND_MET, ""


def _build_explicit_rule_positive_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, src_ref: SourceRecordRef,
    rule_lineage: str, snapshot_id: str, subtype: str,
    match_reason: str,
    related_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    """Materialize a rule-backed positive with complete provenance."""
    audience = positive_subtype_audience_label(subtype)
    priority = rule.priority_on_hit
    risk_family = _rule_risk_family(rule)
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=subtype,
        rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        match_reason=match_reason, positive_subtype=subtype,
        audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-match",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=match_reason),
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-identity",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=identity_binding.evidence_locator,
            evidence_role="medication_identity", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"词典 {identity_binding.dictionary_name}/"
                f"{identity_binding.dictionary_version}")),
    ]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-related-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=match_reason)
        for index, record in enumerate(related_records)
    )
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, identity_binding.evidence_locator,
        *(record.locator for record in related_records))
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode, rule=rule,
        identity_binding=identity_binding,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids,
        relationship_record=(related_records[0] if related_records else None))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=tuple(evidence),
        source_record_refs=(src_ref,), query_refs=(query,),
        journey_markers=(jm,), positive_subtype=subtype,
        audience_label=audience)


def _build_rule_positive_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, match_reason: str,
    src_ref: SourceRecordRef, rule_lineage: str, snapshot_id: str,
) -> CMUnitResult:
    """Build a positive result for a matched prohibited/restricted rule."""
    if rule.is_prohibited:
        subtype = POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH
    elif rule.is_restricted:
        cond_state, cond_reason = _check_restricted_conditions(rule, episode)
        if cond_state == RESTRICTED_COND_UNEVALUABLE:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ne",
                polarity=L1bEvidencePolarity.CONTEXT,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note=cond_reason)
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                not_evaluable_reason=cond_reason,
                evidence=(ev,), source_record_refs=(src_ref,))
        if cond_state == RESTRICTED_COND_BOUNDARY:
            return _build_rule_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                episode=episode, rule=rule, strategy=strategy,
                identity_binding=identity_binding, interval=interval,
                boundary_reason=cond_reason, src_ref=src_ref,
                rule_lineage=rule_lineage, snapshot_id=snapshot_id)
        if cond_state == RESTRICTED_COND_MET:
            ev = _make_evidence_item(
                evidence_id=f"ev-{unit_id}-conditions-ok",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=episode.source_locator,
                evidence_role="recorded_cm", rule_lineage=rule_lineage,
                uncertainty_note="限制规则允许条件已满足")
            return CMUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NEGATIVE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                evidence=(ev,), source_record_refs=(src_ref,))
        # cond_state == RESTRICTED_COND_UNMET -> positive
        subtype = POSITIVE_SUBTYPE_RESTRICTED_MEDICATION_CONDITION_MISMATCH
    else:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-rule-allowed",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=f"规则类型 {rule.rule_type} 允许")
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))
    return _build_explicit_rule_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        episode=episode, rule=rule, strategy=strategy,
        identity_binding=identity_binding, interval=interval,
        src_ref=src_ref, rule_lineage=rule_lineage,
        snapshot_id=snapshot_id, subtype=subtype,
        match_reason=match_reason)


def _build_rule_boundary_result(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, rule: ProtocolMedicationRule,
    strategy: MedicationMatchStrategy,
    identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, boundary_reason: str,
    src_ref: SourceRecordRef, rule_lineage: str, snapshot_id: str,
    related_records: Sequence[CMSemanticRecord] = (),
) -> CMUnitResult:
    """Build a boundary result for a matched rule with an unresolved interval."""
    risk_family = _rule_risk_family(rule)
    signal_type = (f"{rule.rule_type}_boundary")
    priority = MONITORING_PRIORITY_UNKNOWN
    if rule.is_prohibited:
        audience = "禁用药使用待核实（边界）"
    elif rule.is_restricted:
        audience = "限制用药条件待核实（边界）"
    elif rule.is_record_consistency:
        audience = "用药信息待核实（边界）"
    else:
        audience = "用药与处置记录关系待核实（边界）"
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type,
        rule=rule, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        match_reason=boundary_reason, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-boundary",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="recorded_cm", rule_lineage=rule_lineage,
        uncertainty_note=boundary_reason)]
    evidence.extend(
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-boundary-related-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=record.locator, evidence_role=record.role,
            rule_lineage=rule_lineage, uncertainty_note=boundary_reason)
        for index, record in enumerate(related_records))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.BOUNDARY,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=tuple(evidence),
        source_record_refs=(src_ref,), journey_markers=(jm,),
        boundary_reason=boundary_reason, audience_label=audience)

def _evaluate_indication_unit(
    *, project_id: str, expanded: CMUnitExpanded, unit_id: str,
    episode: MedicationEpisode, identity_binding: MedicationIdentityBinding,
    interval: CMIntervalDescriptor, strategy: MedicationMatchStrategy,
    priority_policy: Optional[D02PriorityPolicy],
    snapshot_id: str, evidence_records: Sequence[CMSemanticRecord],
    linkage_coverage_complete: bool = False,
) -> CMUnitResult:
    """Evaluate an indication-check unit (frozen D02 §5.1, §8).

    Required-phase gate: a missing, blank, or unconfirmed research phase
    is ``not_evaluable``; no candidate/Query/cross-domain ref is produced
    until the stage is a verifiable input (§5.1/§5.2/§5.4).

    Coverage gate: ``linkage_coverage_complete`` must be True for a
    positive or definitive-negative indication conclusion.  An empty
    ``evidence_records`` alone cannot prove a complete search.

    Role gate: prophylaxis/rescue can be negative only when the role is
    confirmed; an unconfirmed treatment role is ``not_evaluable``.

    Subtypes (§5.1): ``treatment_without_event_record`` (subtype 2)
    requires explicit evidence that the purpose is treatment of a
    study-period new/worsened event plus complete linkage coverage;
    other confirmed mappable role-confirmed but unexplained indications
    use ``medication_indication_unexplained`` (subtype 1).  Subtype 2
    takes precedence only when its stronger facts are present.
    """
    src_ref = _make_source_record_ref(episode.source_locator)
    rule_lineage = D02_RULE_LINEAGE_DEFAULT

    # Required-phase gate (§5.1/§5.2/§5.4): a missing, blank, or
    # unconfirmed research phase is not_evaluable; no candidate, Query,
    # or cross-domain ref may be produced until the stage is verifiable.
    if not (episode.study_phase_confirmed and episode.study_phase.strip()):
        if not episode.study_phase.strip():
            ne_reason = "研究阶段缺失或为空，无法评价用药依据"
        else:
            ne_reason = (
                f"研究阶段 {episode.study_phase!r} 未获确认，无法评价用药依据")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-phase-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    assessment = _assess_indication(episode, evidence_records, strategy)

    # Temporally uninterpretable same-concept record -> not_evaluable.
    if assessment.temporally_uninterpretable:
        ne_reason = (
            "存在与适应证同概念的记录，但其日期无法解析，"
            "不能确定时间关系，暂无法评价")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-temporal-ne",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # No mappable indication: coverage gap / not_evaluable.
    if not assessment.has_mappable_indication:
        if not episode.indication_text.strip():
            ne_reason = "适应证信息缺失，不等于无适应证，不自动生成无用药依据结论"
        elif assessment.indication_vague:
            ne_reason = "适应证记录不具体（笼统/不可映射），不反向判漏报"
        else:
            ne_reason = "适应证不可映射，无法判定用药依据"
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-indication-gap",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Coverage gate: incomplete relevant-source coverage -> not_evaluable.
    if not linkage_coverage_complete:
        ne_reason = (
            "相关 AE/MH/诊断来源覆盖不完整，不能证明已完整检索，"
            "暂无法对用药依据作出确定结论")
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-coverage-incomplete",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Mappable indication WITH matching same-subject event record -> negative.
    if assessment.matching_event_records:
        match_evs = tuple(
            _make_evidence_item(
                evidence_id=f"ev-{unit_id}-match-{i}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=rec.locator, evidence_role=rec.role,
                rule_lineage=rule_lineage,
                uncertainty_note="适应证与已记录医学事件一致")
            for i, rec in enumerate(assessment.matching_event_records))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=match_evs, source_record_refs=(src_ref,))

    # Mappable indication, NO matching event record, coverage complete.
    # Role gate: unconfirmed treatment role -> not_evaluable.
    if not assessment.treatment_role_confirmed:
        ne_reason = "治疗角色未确认，无法判定用药依据是否成立"
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-role-unconfirmed",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=ne_reason)
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            not_evaluable_reason=ne_reason, evidence=(ev,),
            source_record_refs=(src_ref,))

    # Confirmed prophylaxis/rescue role -> negative, no auto under-reporting.
    if assessment.is_prophylaxis_or_rescue:
        ev = _make_evidence_item(
            evidence_id=f"ev-{unit_id}-prophylaxis",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=episode.source_locator,
            evidence_role="recorded_cm", rule_lineage=rule_lineage,
            uncertainty_note=(
                f"治疗角色为 {episode.treatment_role}，不因缺 AE/MH 自动判漏报"))
        return CMUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            evidence=(ev,), source_record_refs=(src_ref,))

    # Determine subtype: subtype 2 requires explicit treatment-of-study-event
    # evidence; otherwise subtype 1 (§5.1 precedence rule).
    if assessment.is_treatment_of_study_event:
        subtype = POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD
    else:
        subtype = POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED
    audience = positive_subtype_audience_label(subtype)
    risk_family = "indication_check"
    signal_type = subtype
    # Priority: from versioned policy when supplied; else unknown (not medium).
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(subtype)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    candidate, identity = _build_d02_candidate(
        project_id=project_id, episode=episode,
        ingredient_token=expanded.ingredient_token,
        rule_item_or_concept=expanded.rule_item_or_concept,
        risk_family=risk_family, signal_type=signal_type,
        rule=None, interval=interval,
        identity_binding=identity_binding, strategy=strategy,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        match_reason=(
            f"用药适应证 {assessment.indication_concept} 无对应 AE/MH/诊断记录"),
        positive_subtype=subtype, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    ev = _make_evidence_item(
        evidence_id=f"ev-{unit_id}-indication-positive",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="recorded_cm", rule_lineage=rule_lineage,
        uncertainty_note=(
            f"用药 {identity_binding.original_name} 对应适应证 "
            f"{assessment.indication_concept}，未找到对应 AE/MH/诊断"))
    # Query provenance: CM source + identity evidence + indication locator.
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, identity_binding.evidence_locator,
        episode.indication_source_locator)
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode, rule=None,
        identity_binding=identity_binding,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids)
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, risk_family=risk_family,
        audience_label=audience, monitoring_priority=priority)
    cm_ref = _build_cm_indication_ref(
        evidence_ref_id=f"cer-{unit_id}", producer_unit_id=unit_id,
        episode=episode, indication_assessment=assessment)
    return CMUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, r2_candidates=(candidate,),
        risk_candidate_refs=(cand_ref,), evidence=(ev,),
        source_record_refs=(src_ref,), query_refs=(query,),
        journey_markers=(jm,),
        cross_domain_evidence_refs=(cm_ref,),
        positive_subtype=subtype, audience_label=audience)


# ---------------------------------------------------------------------------
# Slice-level evaluation (frozen D02 §4.1, §11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMSliceResult:
    """Aggregate result of evaluating one or more D02 units for a subject."""

    subject_ref: str
    unit_results: Tuple[CMUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def positive_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_APPLICABLE)

    def episode_rollups(
        self, expansions: CMExpectedSetExpansion,
    ) -> Tuple[CMEpisodeRollup, ...]:
        """Build read-only episode rollups preserving all child unit ids."""
        unit_by_expanded: Dict[str, CMUnitResult] = {
            r.unit_id: r for r in self.unit_results}
        rollups: List[CMEpisodeRollup] = []
        by_episode: Dict[str, List[CMUnitExpanded]] = {}
        for eu in expansions.units:
            by_episode.setdefault(eu.episode.episode_id, []).append(eu)
        for ep_id, eus in by_episode.items():
            child_ids: List[str] = []
            has_pos = has_bnd = has_ne = has_neg = False
            src_loc_ids: Set[str] = set()
            for eu in eus:
                unit = eu.build_unit(expansions.project_id, expansions.strategy)
                uid = unit.unit_id
                child_ids.append(uid)
                r = unit_by_expanded.get(uid)
                if r is None:
                    continue
                if r.l1_disposition == L1Disposition.POSITIVE:
                    has_pos = True
                elif r.l1_disposition == L1Disposition.BOUNDARY:
                    has_bnd = True
                elif r.l1_disposition == L1Disposition.NOT_EVALUABLE:
                    has_ne = True
                elif r.l1_disposition == L1Disposition.NEGATIVE:
                    has_neg = True
                for sref in r.source_record_refs:
                    src_loc_ids.add(sref.locator.locator_id())
            rollups.append(CMEpisodeRollup(
                episode_id=ep_id,
                subject_ref=eus[0].episode.subject_ref,
                child_unit_ids=tuple(sorted(set(child_ids))),
                has_positive=has_pos, has_boundary=has_bnd,
                has_not_evaluable=has_ne, has_negative=has_neg,
                source_record_count=len(src_loc_ids)))
        return tuple(rollups)


def evaluate_cm_slice(
    *, project_id: str, episodes: Sequence[MedicationEpisode],
    active_rules: Sequence[ProtocolMedicationRule],
    strategy: MedicationMatchStrategy,
    evidence_records: Sequence[CMSemanticRecord] = (),
    priority_policy: Optional[D02PriorityPolicy] = None,
    snapshot_id: str = "",
    ip_exposure_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
    relationship_coverage_complete: bool = False,
) -> Dict[str, CMSliceResult]:
    """Evaluate multiple D02 units, grouped by subject.

    Returns a mapping of subject_ref -> CMSliceResult.  Each unit gets
    exactly one L1 disposition.  Episode rollups are read-only views
    over the child units.  Indication-source and action-relationship source
    coverage are separate fail-closed proofs.
    """
    expansions = expand_cm_expected_set(
        project_id=project_id, episodes=episodes,
        active_rules=active_rules, strategy=strategy)
    results: List[CMUnitResult] = []
    for eu in expansions.units:
        r = evaluate_cm_unit(
            project_id=project_id, expanded=eu,
            evidence_records=evidence_records, strategy=strategy,
            priority_policy=priority_policy, snapshot_id=snapshot_id,
            ip_exposure_records=ip_exposure_records,
            linkage_coverage_complete=linkage_coverage_complete,
            relationship_coverage_complete=relationship_coverage_complete)
        results.append(r)
    by_subject: Dict[str, List[CMUnitResult]] = {}
    for r in results:
        by_subject.setdefault(r.subject_ref, []).append(r)
    all_cands: List[RiskCandidate] = []
    for r in results:
        all_cands.extend(r.r2_candidates)
    out: Dict[str, CMSliceResult] = {}
    for subj, urs in by_subject.items():
        subj_cands = [c for r in urs for c in r.r2_candidates]
        out[subj] = CMSliceResult(
            subject_ref=subj, unit_results=tuple(urs),
            r2_candidates=tuple(subj_cands),
            expected_set_hash=expansions.expected_set_hash,
            rule_lineage=D02_RULE_LINEAGE_DEFAULT)
    return out
