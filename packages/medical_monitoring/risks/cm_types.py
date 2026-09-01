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


__all__ = [name for name in globals() if not name.startswith("__")]


__all__ = [name for name in globals() if not name.startswith("__")]
