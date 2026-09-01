"""D02 expected-set expansion, interval comparison, and rule matching."""

from .cm_types import *

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


__all__ = [name for name in globals() if not name.startswith("__")]
