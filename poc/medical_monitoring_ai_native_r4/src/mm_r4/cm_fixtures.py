"""R4-D02 CM synthetic fixtures, challenge matrix and N-to-N+1 lifecycle
harness (worker_04).

Every fixture in this module is **deterministic, synthetic and offline**.
No real-project data, table names, drug names, thresholds or 30-day rules
are encoded.  The fixtures build the same frozen public value objects the
D02 engine (``mm_r4.cm``) and projection (``mm_r4.cm_projection``) use, so
tests exercise the real join invariants, the real R2 identity/lifecycle
public API and the real CoverageLedger rather than mocks.

The module delivers three things required by the frozen D02 contract
``FROZEN_R4_D02_CONTRACT_V1`` §12 (synthetic challenge matrix) and §4.2/§9
(identity persistence, supersede, identity_ambiguous, deterministic
replay):

1. Thin primitive builders (:func:`make_locator`, :func:`make_binding`,
   :func:`make_episode`, :func:`make_rule`, :func:`make_strategy`,
   :func:`make_policy`, :func:`make_cm_record`) that construct the frozen
   versioned inputs with stable hashes.
2. :func:`build_cm_challenge_matrix` -- all 30 frozen §12 challenge cases,
   each carrying its expected per-unit L1 dispositions, candidate/Query/
   cross-domain counts and identity/projection/lifecycle assertions.
3. An N-to-N+1 lifecycle harness (:func:`make_acceptance_service`,
   :func:`make_baseline_snapshot`, :func:`make_subsequent_snapshot`,
   :func:`make_closed_cm_ledger`, :func:`run_n_to_n1_replay`) that proves
   immutable historical completion, stable event identity across
   locator/snapshot revision, versioned lineage, no duplicate D01/D02
   candidates/risks/Queries, and deterministic replay.

All data is synthetic.  No production UI, real project, provider,
dictionary, or product service is involved; port 8911 is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as _replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY,
    AcceptanceService,
    SnapshotAcceptanceState,
    SnapshotBinding,
)
from mm_r2.domain import (
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    SourceRevision,
)
from mm_r2.identity import IdentityResolution, make_record_identity
from mm_r2.risk import RiskLifecycle

from .cm import (
    CONFIRMATION_CONFIRMED,
    CONFIRMATION_UNRESOLVED,
    CMSemanticRecord,
    CMExpectedSetExpansion,
    CMIntervalDescriptor,
    CMUnitResult,
    D02_DOMAIN,
    D02PriorityPolicy,
    D02_RULE_LINEAGE_DEFAULT,
    IngredientBinding,
    MedicationEpisode,
    MedicationIdentityBinding,
    MedicationMatchStrategy,
    POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED,
    POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
    POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
    ProtocolMedicationRule,
    TreatmentInterpretationEvidence,
    TARGET_KIND_CATEGORY,
    TARGET_KIND_INGREDIENT,
    TARGET_KIND_PRODUCT_TYPE,
    expand_cm_expected_set,
    evaluate_cm_unit,
)
from .contracts import (
    L1Disposition,
    SourceLocator,
    UnitEvaluation,
)
from .coverage import (
    CoverageLedger,
    ExpectedSet,
    expected_set_hash,
)

__all__ = [
    # constants
    "PROJECT_ID",
    "DOMAIN_ID",
    "RUN_ID",
    "RULE_LINEAGE",
    "SNAPSHOT_ID",
    "SOURCE_REV_ID",
    "SITE_REF",
    # primitive builders
    "make_locator",
    "make_strategy",
    "make_policy",
    "make_binding",
    "make_episode",
    "make_rule",
    "make_cm_record",
    "evaluate",
    "evaluate_one",
    # challenge matrix
    "CMChallengeCase",
    "CMChallengeMatrix",
    "build_cm_challenge_matrix",
    # lifecycle harness
    "make_acceptance_service",
    "make_baseline_snapshot",
    "make_subsequent_snapshot",
    "make_lifecycle",
    "make_closed_cm_ledger",
    "attach_risk_ref",
    "NToN1Replay",
    "run_n_to_n1_replay",
]


# ---------------------------------------------------------------------------
# Stable synthetic constants (no project specifics, no fixed table names)
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = D02_DOMAIN
RUN_ID = "run-synthetic-d02-001"
RULE_LINEAGE = D02_RULE_LINEAGE_DEFAULT
SNAPSHOT_ID = "snap-d02-accepted-001"
SOURCE_REV_ID = "sr-d02-listing-001"
SITE_REF = "SITE01"


# ---------------------------------------------------------------------------
# Primitive builders
# ---------------------------------------------------------------------------

def make_locator(
    record_id: str, table_semantic: str = "recorded_cm",
    snapshot_id: str = SNAPSHOT_ID,
    source_revision_id: str = SOURCE_REV_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=source_revision_id,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_strategy(version: str = "ms-d02-v1",
                  chash: str = "d02sch1") -> MedicationMatchStrategy:
    return MedicationMatchStrategy(
        version=version, strategy_content_hash=chash)


def make_strategy_v2() -> MedicationMatchStrategy:
    """A second versioned strategy for lineage-change supersede tests."""
    return MedicationMatchStrategy(
        version="ms-d02-v2", strategy_content_hash="d02sch2")


def make_policy(version: str = "pp-d02-v1") -> D02PriorityPolicy:
    return D02PriorityPolicy(
        version=version, policy_content_hash="d02pch1",
        rationale="synthetic D02 default priority policy",
        indication_unexplained_priority="medium",
        treatment_without_event_priority="medium")


def make_policy_unknown() -> D02PriorityPolicy:
    """Policy whose indication subtypes resolve to ``unknown`` priority --
    proves unknown is never downgraded to low."""
    return D02PriorityPolicy(
        version="pp-d02-unk", policy_content_hash="d02pch-unk",
        rationale="synthetic unknown-priority policy",
        indication_unexplained_priority="unknown",
        treatment_without_event_priority="unknown")


def make_binding(
    ingredients: Sequence[IngredientBinding],
    original_name: str = "合成药物A",
    normalized_name: str = "synthetic_a",
    record_id: str = "dict-1",
    confirmation: str = CONFIRMATION_CONFIRMED,
    dictionary_name: str = "DICT",
    dictionary_version: str = "v1",
    dictionary_content_hash: str = "dh1",
) -> MedicationIdentityBinding:
    return MedicationIdentityBinding(
        original_name=original_name, normalized_name=normalized_name,
        ingredients=tuple(ingredients),
        dictionary_name=dictionary_name, dictionary_version=dictionary_version,
        dictionary_content_hash=dictionary_content_hash,
        evidence_locator=make_locator(record_id, "medication_identity"),
        confirmation_status=confirmation)


def make_episode(
    record_id: str = "CM#9",
    subject: str = "SYN-001",
    binding: Optional[MedicationIdentityBinding] = None,
    cm_start: str = "2026-01-03",
    cm_end: str = "2026-01-05",
    ongoing: bool = False,
    cutoff: str = "",
    phase: str = "treatment",
    treatment_role: str = "treatment",
    treatment_role_confirmed: bool = True,
    indication_text: str = "",
    indication_concept: str = "",
    indication_mappable: Optional[bool] = None,
    indication_source_record_id: Optional[str] = None,
    dose: str = "100",
    dose_unit: str = "mg",
    route: str = "口服",
    frequency: str = "每日一次",
    study_phase: str = "treatment",
    study_phase_confirmed: bool = True,
    indication_treatment_of_study_event: bool = False,
    treatment_interpretation_evidence: Sequence[
        TreatmentInterpretationEvidence] = (),
    stable_treatment_evidence_complete: bool = False,
    stable_treatment_duration_confirmed: bool = False,
    dose_frequency_unchanged: bool = False,
    rule_window_start: str = "",
    rule_window_end: str = "",
    rule_window_start_inclusive: Optional[bool] = None,
    rule_window_end_inclusive: Optional[bool] = None,
) -> MedicationEpisode:
    """Build a synthetic :class:`MedicationEpisode`.

    If ``binding`` is None a single confirmed ``ingredientA`` binding is
    used.  Episode/locator ids are derived from ``record_id`` so stable
    event identity is deterministic.
    """
    if binding is None:
        binding = make_binding(
            (IngredientBinding(ingredient="ingredientA"),))
    indication_loc: Optional[SourceLocator] = None
    if indication_source_record_id is not None:
        indication_loc = make_locator(
            indication_source_record_id, "recorded_cm")
    return MedicationEpisode(
        episode_id=f"ep-{record_id}", subject_ref=subject, site_ref=SITE_REF,
        stable_cm_source_event_key=f"recorded_cm:{record_id}",
        source_locator=make_locator(record_id),
        identity_binding=binding,
        interval=CMIntervalDescriptor(
            cm_start=cm_start, cm_end=cm_end, ongoing=ongoing, cutoff=cutoff,
            applicable_phase=phase,
            rule_window_start=rule_window_start,
            rule_window_end=rule_window_end,
            rule_window_start_inclusive=rule_window_start_inclusive,
            rule_window_end_inclusive=rule_window_end_inclusive),
        dose=dose, dose_unit=dose_unit, route=route, frequency=frequency,
        treatment_role=treatment_role,
        treatment_role_confirmed=treatment_role_confirmed,
        indication_text=indication_text,
        indication_concept=indication_concept,
        indication_mappable=indication_mappable,
        indication_source_locator=indication_loc,
        study_phase=study_phase,
        study_phase_confirmed=study_phase_confirmed,
        indication_treatment_of_study_event=indication_treatment_of_study_event,
        treatment_interpretation_evidence=tuple(
            treatment_interpretation_evidence),
        stable_treatment_evidence_complete=stable_treatment_evidence_complete,
        stable_treatment_duration_confirmed=stable_treatment_duration_confirmed,
        dose_frequency_unchanged=dose_frequency_unchanged)


def make_rule(
    rule_id: str = "R-CM-007",
    rule_type: str = "prohibited",
    target_kind: str = TARGET_KIND_INGREDIENT,
    target_value: str = "ingredientA",
    window_start: str = "2026-01-01",
    window_end: str = "2026-06-30",
    start_inc: Optional[bool] = True,
    end_inc: Optional[bool] = True,
    priority: str = "high",
    applicable_phases: Tuple[str, ...] = ("treatment",),
    clause_locator: str = "P12-4",
    rule_version: str = "v1",
    rule_content_hash: str = "rc1",
    rule_lineage: str = "rl1",
    allowed_conditions: Tuple[str, ...] = (),
    stable_treatment_exception: bool = False,
    rescue_exception: bool = False,
    prophylaxis_exception: bool = False,
    priority_rationale: str = "禁止成分",
) -> ProtocolMedicationRule:
    return ProtocolMedicationRule(
        rule_id=rule_id, rule_version=rule_version,
        clause_locator=clause_locator, rule_type=rule_type,
        target_kind=target_kind, target_value=target_value,
        applicable_phases=applicable_phases,
        window_start=window_start, window_end=window_end,
        window_start_inclusive=start_inc, window_end_inclusive=end_inc,
        allowed_conditions=allowed_conditions,
        stable_treatment_exception=stable_treatment_exception,
        rescue_exception=rescue_exception,
        prophylaxis_exception=prophylaxis_exception,
        priority_on_hit=priority, priority_rationale=priority_rationale,
        rule_content_hash=rule_content_hash, rule_lineage=rule_lineage)


def make_cm_record(
    role: str, concept: str, record_id: str,
    subject_ref: str = "SYN-001", site_ref: str = SITE_REF,
    event_date_raw: str = "", indication_text: str = "",
    treatment_role: str = "",
) -> CMSemanticRecord:
    return CMSemanticRecord(
        role=role, concept=concept, locator=make_locator(record_id, role),
        subject_ref=subject_ref, site_ref=site_ref,
        event_date_raw=event_date_raw, indication_text=indication_text,
        treatment_role=treatment_role)


_NO_POLICY = object()


def evaluate(
    episodes: Sequence[MedicationEpisode],
    rules: Sequence[ProtocolMedicationRule],
    *,
    strategy: Optional[MedicationMatchStrategy] = None,
    policy: Any = _NO_POLICY,
    evidence_records: Sequence[CMSemanticRecord] = (),
    snapshot_id: str = SNAPSHOT_ID,
    ip_exposure_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
) -> Tuple[CMExpectedSetExpansion, Dict[str, List[CMUnitResult]]]:
    """Expand + evaluate a synthetic CM collection through the D02 engine.

    Returns ``(expansion, results_by_subject)`` where each unit receives
    exactly one L1 disposition.
    """
    if strategy is None:
        strategy = make_strategy()
    if policy is _NO_POLICY:
        policy = make_policy()
    expansion = expand_cm_expected_set(
        project_id=PROJECT_ID, episodes=episodes,
        active_rules=rules, strategy=strategy)
    by_subject: Dict[str, List[CMUnitResult]] = {}
    for eu in expansion.units:
        r = evaluate_cm_unit(
            project_id=PROJECT_ID, expanded=eu,
            evidence_records=evidence_records, strategy=strategy,
            priority_policy=policy, snapshot_id=snapshot_id,
            ip_exposure_records=ip_exposure_records,
            linkage_coverage_complete=linkage_coverage_complete)
        by_subject.setdefault(r.subject_ref, []).append(r)
    return expansion, by_subject


def evaluate_one(
    episode: MedicationEpisode,
    rules: Sequence[ProtocolMedicationRule] = (),
    *,
    strategy: Optional[MedicationMatchStrategy] = None,
    policy: Any = _NO_POLICY,
    evidence_records: Sequence[CMSemanticRecord] = (),
    ip_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
) -> Tuple[CMExpectedSetExpansion, List[CMUnitResult]]:
    """Evaluate one episode and return ``(expansion, [results])``.

    The list is ordered as the expansion produced the units.
    """
    expansion, by_subject = evaluate(
        (episode,), rules, strategy=strategy, policy=policy,
        evidence_records=evidence_records,
        ip_exposure_records=ip_records,
        linkage_coverage_complete=linkage_coverage_complete)
    subj = episode.subject_ref
    return expansion, by_subject.get(subj, [])


# ---------------------------------------------------------------------------
# Challenge matrix
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMExpectedUnit:
    """Expected outcome for one expanded unit identified by the substring
    of its ``risk_family``/``rule_item`` token, or by ``unit_index``.

    Exactly one of ``risk_family_contains`` / ``rule_item_contains`` /
    ``unit_index`` should identify the unit.  ``expected_l1`` is the L1
    disposition that unit must receive.  Optional count fields default to
    ``None`` (don't assert) so each case asserts only what the contract
    requires.
    """

    expected_l1: str
    risk_family_contains: str = ""
    rule_item_contains: str = ""
    unit_index: Optional[int] = None
    expected_candidate_count: Optional[int] = None
    expected_query_count: Optional[int] = None
    expected_cross_domain_ref_count: Optional[int] = None
    expected_positive_subtype: str = ""
    expected_audience_label: str = ""

    def matches_unit(self, expanded_unit: Any) -> bool:
        if self.unit_index is not None:
            return False  # index match handled by caller
        if self.risk_family_contains and (
                self.risk_family_contains not in expanded_unit.risk_family):
            return False
        if self.rule_item_contains and (
                self.rule_item_contains not in expanded_unit.rule_item_or_concept):
            return False
        return bool(self.risk_family_contains or self.rule_item_contains)


@dataclass(frozen=True)
class CMChallengeCase:
    """One numbered frozen §12 challenge case.

    ``build_episodes`` / ``build_rules`` / ``build_evidence`` /
    ``build_ip_records`` are zero-arg factories returning the synthetic
    inputs (rebuilt fresh so cases are independent and deterministic).
    ``expected_units`` lists the expected per-unit outcomes; each entry
    must match exactly one expanded unit.  ``expected_set_size`` is the
    expected number of expanded units (defaults to
    ``len(expected_units)`` when not set, but cases with mixed flags
    set it explicitly).
    """

    number: int
    name: str
    category: str
    description: str
    build_episodes: Any = field(repr=False)
    build_rules: Any = field(default=tuple, repr=False)
    build_evidence: Any = field(default=tuple, repr=False)
    build_ip_records: Any = field(default=tuple, repr=False)
    expected_units: Tuple[CMExpectedUnit, ...] = ()
    expected_set_size: Optional[int] = None
    linkage_coverage_complete: bool = False
    strategy_override: Optional[MedicationMatchStrategy] = None
    policy_override: Any = _NO_POLICY

    def build(self, **kwargs: Any) -> Tuple[
        CMExpectedSetExpansion, List[CMUnitResult]]:
        """Build inputs, run the engine, return (expansion, results)."""
        strategy = self.strategy_override or make_strategy()
        policy = (self.policy_override
                  if self.policy_override is not _NO_POLICY else make_policy())
        exp, by_subject = evaluate(
            list(self.build_episodes()), list(self.build_rules()),
            strategy=strategy, policy=policy,
            evidence_records=list(self.build_evidence()),
            ip_exposure_records=list(self.build_ip_records()),
            linkage_coverage_complete=self.linkage_coverage_complete)
        all_results: List[CMUnitResult] = []
        for urs in by_subject.values():
            all_results.extend(urs)
        # Order by expansion unit order for index-based matching.
        ordered: List[CMUnitResult] = []
        for eu in exp.units:
            uid = eu.build_unit(PROJECT_ID, strategy).unit_id
            for r in all_results:
                if r.unit_id == uid:
                    ordered.append(r)
                    break
        return exp, ordered

    def expected_count(self) -> int:
        if self.expected_set_size is not None:
            return self.expected_set_size
        return len(self.expected_units)


@dataclass(frozen=True)
class CMChallengeMatrix:
    """The full 30-case frozen §12 challenge matrix for D02."""

    cases: Tuple[CMChallengeCase, ...]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def numbers(self) -> Tuple[int, ...]:
        return tuple(c.number for c in self.cases)

    def by_number(self, number: int) -> CMChallengeCase:
        for c in self.cases:
            if c.number == number:
                return c
        raise KeyError(f"no challenge case #{number}")

    def by_name(self, name: str) -> CMChallengeCase:
        for c in self.cases:
            if c.name == name:
                return c
        raise KeyError(f"no challenge case named {name!r}")


# -- helpers for building the 30 cases --------------------------------------

def _ev(l1: str, *, risk_family_contains: str = "",
        rule_item_contains: str = "", unit_index: Optional[int] = None,
        cand: Optional[int] = None, query: Optional[int] = None,
        cer: Optional[int] = None, subtype: str = "",
        audience: str = "") -> CMExpectedUnit:
    return CMExpectedUnit(
        expected_l1=l1, risk_family_contains=risk_family_contains,
        rule_item_contains=rule_item_contains, unit_index=unit_index,
        expected_candidate_count=cand, expected_query_count=query,
        expected_cross_domain_ref_count=cer,
        expected_positive_subtype=subtype, expected_audience_label=audience)


def build_cm_challenge_matrix() -> CMChallengeMatrix:
    """Build the frozen §12 30-case synthetic challenge matrix.

    Every category required by the frozen contract is represented as an
    executable case with explicit expected L1/L2/cross-domain assertions.
    Cases are independent: each rebuilds fresh synthetic inputs.
    """
    cases: List[CMChallengeCase] = []

    # 1. 明确禁用成分且时间窗命中 -----------------------------------------
    cases.append(CMChallengeCase(
        number=1, name="prohibited_ingredient_in_window",
        category="positive",
        description="禁用成分精确命中且区间落入适用窗口 -> positive",
        build_episodes=lambda: (
            make_episode(record_id="CM#1",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-1", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA",
                      window_start="2026-01-01", window_end="2026-06-30",
                      start_inc=True, end_inc=True, priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1, cer=0,
                subtype=POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH,
                audience="禁用药使用待核实"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check",
                rule_item_contains="indication:unmapped"),
        ),
    ))

    # 2. 明确不同成分/类别且窗口完整, negative ----------------------------
    cases.append(CMChallengeCase(
        number=2, name="different_ingredient_negative",
        category="negative",
        description="已确认成分精确不同于规则目标 -> negative",
        build_episodes=lambda: (
            make_episode(record_id="CM#2",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientZ"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-2", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA",
                      window_start="2026-01-01", window_end="2026-06-30",
                      priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.NEGATIVE,
                rule_item_contains="prohibited:ingredient:ingredientA"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 3. 商品名/成分不明, not_evaluable -----------------------------------
    cases.append(CMChallengeCase(
        number=3, name="unresolved_ingredient_not_evaluable",
        category="not_evaluable",
        description="成分未知（商品名不映射）-> not_evaluable",
        build_episodes=lambda: (
            make_episode(record_id="CM#3",
                         binding=make_binding(
                             (IngredientBinding(
                                 component_slot="slot1",
                                 confirmation=CONFIRMATION_UNRESOLVED),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-3", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="ingredient_resolution",
                rule_item_contains="ingredient_resolution:slot1"),
        ),
        expected_set_size=1,
    ))

    # 4. 复方一个禁用成分+一个未知成分 -> positive 与 not_evaluable 共存 --
    cases.append(CMChallengeCase(
        number=4, name="compound_prohibited_plus_unresolved",
        category="compound",
        description="复方：禁用成分 positive + 未知成分 not_evaluable 分单元共存",
        build_episodes=lambda: (
            make_episode(record_id="CM#4",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),
                              IngredientBinding(
                                  component_slot="slot1",
                                  confirmation=CONFIRMATION_UNRESOLVED)),
                             original_name="合成复方B")),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-4", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1,
                subtype=POSITIVE_SUBTYPE_PROHIBITED_MEDICATION_MATCH),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="ingredient_resolution",
                rule_item_contains="ingredient_resolution:slot1"),
        ),
    ))

    # 5. 只有 J07 上位码却规则要求活/减毒活疫苗, not_evaluable ------------
    cases.append(CMChallengeCase(
        number=5, name="j07_supertype_not_evaluable",
        category="granularity",
        description="规则要求活/减毒活疫苗但仅有 J07 上位码 -> not_evaluable",
        build_episodes=lambda: (
            make_episode(record_id="CM#5",
                         binding=make_binding(
                             (IngredientBinding(
                                 ingredient="vacc-generic",
                                 categories=("J07",)),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-5", target_kind=TARGET_KIND_PRODUCT_TYPE,
                      target_value="live_attenuated_vaccine",
                      priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="prohibited:product_type:"
                                   "live_attenuated_vaccine"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 6. 开始/结束恰在规则端点, boundary ---------------------------------
    cases.append(CMChallengeCase(
        number=6, name="endpoint_inclusivity_boundary",
        category="boundary",
        description="CM 起始恰在规则窗口端点且包含关系未明 -> boundary",
        build_episodes=lambda: (
            make_episode(record_id="CM#6",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),)),
                         cm_start="2026-01-01", cm_end="2026-06-30"),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-6", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA",
                      window_start="2026-01-01", window_end="2026-06-30",
                      start_inc=None, end_inc=True, priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.BOUNDARY,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=0),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 7. 月/年部分日期可能重叠, boundary ---------------------------------
    cases.append(CMChallengeCase(
        number=7, name="partial_date_boundary",
        category="boundary",
        description="月精度部分日期可能重叠规则窗口 -> boundary",
        build_episodes=lambda: (
            make_episode(record_id="CM#7",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),)),
                         cm_start="2026-03", cm_end="2026-04"),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-7", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA",
                      window_start="2026-01-01", window_end="2026-06-30",
                      start_inc=True, end_inc=True, priority="high"),
        ),
        expected_units=(
            _ev(L1Disposition.BOUNDARY,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=0),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 8. 明确稳定治疗满足条件, counterevidence/negative -----------------
    cases.append(CMChallengeCase(
        number=8, name="stable_treatment_conditions_met_negative",
        category="negative",
        description="限制规则要求稳定治疗且稳定证据充分 -> negative",
        build_episodes=lambda: (
            make_episode(record_id="CM#8",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientB"),)),
                         treatment_role="stable_treatment",
                         treatment_role_confirmed=True,
                         stable_treatment_evidence_complete=True,
                         stable_treatment_duration_confirmed=True,
                         dose_frequency_unchanged=True),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-REST-8", rule_type="restricted",
                      target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientB", priority="medium",
                      clause_locator="P8",
                      allowed_conditions=("stable_treatment",),
                      priority_rationale="限制成分"),
        ),
        expected_units=(
            _ev(L1Disposition.NEGATIVE,
                rule_item_contains="restricted:ingredient:ingredientB"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 9. 长期用药两解释 boundary；稳定信息缺失 not_evaluable --------------
    cases.append(CMChallengeCase(
        number=9, name="stable_treatment_evidence_missing_not_evaluable",
        category="not_evaluable",
        description="限制规则要求稳定治疗但稳定证据缺失 -> not_evaluable",
        build_episodes=lambda: (
            make_episode(record_id="CM#9",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientB"),)),
                         treatment_role="stable_treatment",
                         treatment_role_confirmed=True,
                         stable_treatment_evidence_complete=False,
                         stable_treatment_duration_confirmed=False,
                         dose_frequency_unchanged=False),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-REST-9", rule_type="restricted",
                      target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientB", priority="medium",
                      clause_locator="P9",
                      allowed_conditions=("stable_treatment",),
                      priority_rationale="限制成分"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="restricted:ingredient:ingredientB"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 10. 抢救/预防角色明确, 不因无 AE/MH 判漏报 --------------------------
    cases.append(CMChallengeCase(
        number=10, name="rescue_prophylaxis_no_auto_under_report",
        category="negative",
        description="预防角色明确+适应证可映射+覆盖完整且无事件 -> negative",
        build_episodes=lambda: (
            make_episode(record_id="CM#10",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientP"),)),
                         treatment_role="prophylaxis",
                         treatment_role_confirmed=True,
                         indication_text="预防性用药",
                         indication_concept="prophylaxis_concept",
                         indication_mappable=True),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.NEGATIVE,
                risk_family_contains="indication_check"),
        ),
        expected_set_size=1,
    ))

    # 11. 明确治疗适应证但 AE/MH/诊断无对应, positive+D01 evidence link ----
    cases.append(CMChallengeCase(
        number=11, name="treatment_indication_no_event_positive",
        category="positive",
        description="治疗适应证可映射但无对应 AE/MH -> positive + cm_indication ref",
        build_episodes=lambda: (
            make_episode(record_id="CM#11",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientT"),)),
                         treatment_role="treatment",
                         treatment_role_confirmed=True,
                         indication_text="头痛",
                         indication_concept="headache",
                         indication_mappable=True,
                         indication_source_record_id="IND#11"),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                risk_family_contains="indication_check",
                rule_item_contains="indication:headache",
                cand=1, query=1, cer=1,
                subtype=POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED,
                audience="用药依据待核实"),
        ),
        expected_set_size=1,
    ))

    # 12. 适应证缺失, not_evaluable, 不伪装为无依据 ----------------------
    cases.append(CMChallengeCase(
        number=12, name="missing_indication_not_evaluable",
        category="not_evaluable",
        description="适应证信息缺失 -> not_evaluable, 不等于无适应证",
        build_episodes=lambda: (
            make_episode(record_id="CM#12",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),)),
                         indication_text="", indication_mappable=None),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
        expected_set_size=1,
    ))

    # 13. CM 与 IP/EX 无法区分, not_evaluable ----------------------------
    cases.append(CMChallengeCase(
        number=13, name="cm_ip_role_conflict_not_evaluable",
        category="not_evaluable",
        description="同一来源行同时映射为 CM 与 IP/EX -> not_evaluable",
        build_episodes=lambda: (
            make_episode(record_id="CM#13",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-13", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P13"),
        ),
        build_ip_records=lambda: (
            make_cm_record("ip_exposure", "ip", record_id="CM#13"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="prohibited:ingredient:ingredientA"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 14. 同一受试者另一药物/另一规则不得维持或关闭旧风险 ------------------
    cases.append(CMChallengeCase(
        number=14, name="different_drug_does_not_persist_old_risk",
        category="identity",
        description="同一受试者另一药物产生不同 risk identity, 不得维持旧风险",
        build_episodes=lambda: (
            make_episode(record_id="CM#14a",
                         subject="SYN-014",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
            make_episode(record_id="CM#14b",
                         subject="SYN-014",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientC"),),
                             original_name="合成药物C")),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-14", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P14"),
        ),
        expected_units=(
            # 14a: ingredientA hits -> positive (index 0)
            _ev(L1Disposition.POSITIVE, unit_index=0, cand=1, query=1),
            # 14a indication -> not_evaluable (index 1)
            _ev(L1Disposition.NOT_EVALUABLE, unit_index=1),
            # 14b: ingredientC does not hit rule -> negative (index 2)
            _ev(L1Disposition.NEGATIVE, unit_index=2),
            # 14b indication -> not_evaluable (index 3)
            _ev(L1Disposition.NOT_EVALUABLE, unit_index=3),
        ),
    ))

    # 15. N+1 正式更正后 low/medium 仅凭完整 linked-negative 关闭并保留历史
    # (handled by N-to-N+1 lifecycle harness below + dedicated test)
    cases.append(CMChallengeCase(
        number=15, name="n_to_n1_linked_negative_close",
        category="lifecycle",
        description="N+1 完整 linked-negative 关闭 low/medium 风险并保留历史",
        build_episodes=lambda: (
            make_episode(record_id="CM#15",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-15", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P15"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 16. 词典/规则 lineage 变化产生 superseded/not_evaluable ------------
    cases.append(CMChallengeCase(
        number=16, name="dictionary_lineage_change_superseded",
        category="lifecycle",
        description="词典 lineage 变化产生 superseded（N-to-N+1 harness 证明）",
        build_episodes=lambda: (
            make_episode(record_id="CM#16",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),),
                             dictionary_content_hash="dh1")),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-16", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P16"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 17. 身份竞争产生 identity_ambiguous (N-to-N+1 harness) -------------
    cases.append(CMChallengeCase(
        number=17, name="competing_identity_ambiguous",
        category="lifecycle",
        description="两个竞争 identity binding 产生 identity_ambiguous",
        build_episodes=lambda: (
            make_episode(record_id="CM#17",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-17", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P17"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 18. Query 三段式、最小来源、PD 仅核实、旅程区间与风险双向 join ------
    cases.append(CMChallengeCase(
        number=18, name="query_three_part_journey_join",
        category="query_projection",
        description="Query 三段式含最小来源；旅程区间与风险双向 join 稳定 id",
        build_episodes=lambda: (
            make_episode(record_id="CM#18",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-18", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P12-4"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 19. 同一 CM 同时满足 indication subtype 1/2, 按优先规则一个 primary -
    cases.append(CMChallengeCase(
        number=19, name="indication_subtype_precedence",
        category="positive",
        description="明确治疗研究期事件+无记录 -> subtype 2 优先, 单个 primary",
        build_episodes=lambda: (
            make_episode(record_id="CM#19",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientT"),)),
                         treatment_role="treatment",
                         treatment_role_confirmed=True,
                         indication_text="头痛",
                         indication_concept="headache",
                         indication_mappable=True,
                         indication_source_record_id="IND#19",
                         indication_treatment_of_study_event=True),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                risk_family_contains="indication_check",
                rule_item_contains="indication:headache",
                cand=1, query=1, cer=1,
                subtype=POSITIVE_SUBTYPE_TREATMENT_WITHOUT_EVENT_RECORD,
                audience="治疗用药与 AE/MH 记录待核实"),
        ),
        expected_set_size=1,
    ))

    # 20. 限制规则要求确认抢救角色, 角色未记录 -> not_evaluable -----------
    cases.append(CMChallengeCase(
        number=20, name="restricted_rescue_role_unconfirmed_not_evaluable",
        category="not_evaluable",
        description="限制规则要求抢救角色但未记录角色 -> not_evaluable 而非 boundary",
        build_episodes=lambda: (
            make_episode(record_id="CM#20",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientB"),)),
                         treatment_role="", treatment_role_confirmed=False),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-REST-20", rule_type="restricted",
                      target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientB", priority="medium",
                      clause_locator="P20",
                      rescue_exception=True, priority_rationale="限制成分"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="restricted:ingredient:ingredientB"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 21. 适应证为笼统不可映射文本 -> not_evaluable/coverage gap ----------
    cases.append(CMChallengeCase(
        number=21, name="vague_indication_not_evaluable",
        category="not_evaluable",
        description="适应证为对症治疗/遵医嘱等不可映射 -> not_evaluable",
        build_episodes=lambda: (
            make_episode(record_id="CM#21",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),)),
                         indication_text="对症治疗",
                         indication_mappable=True),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
        expected_set_size=1,
    ))

    # 22. 复方全部成分未确认 -> 所有 unresolved component 进入 expected ---
    cases.append(CMChallengeCase(
        number=22, name="all_components_unresolved",
        category="compound",
        description="复方全部成分未确认且涉及规则 -> 全部 unresolved 进入 expected",
        build_episodes=lambda: (
            make_episode(record_id="CM#22",
                         binding=make_binding(
                             (IngredientBinding(
                                 component_slot="slot1",
                                 confirmation=CONFIRMATION_UNRESOLVED),
                              IngredientBinding(
                                  component_slot="slot2",
                                  confirmation=CONFIRMATION_UNRESOLVED)),
                             original_name="合成复方F")),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-22", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P22"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="ingredient_resolution:slot1"),
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="ingredient_resolution:slot2"),
        ),
        expected_set_size=2,
    ))

    # 23. 规则目标就是 J07 上位类且词典明确绑定时可匹配 -------------------
    cases.append(CMChallengeCase(
        number=23, name="j07_supertype_rule_matchable",
        category="granularity",
        description="规则目标本身就是 J07 上位类且词典明确绑定 -> positive",
        build_episodes=lambda: (
            make_episode(record_id="CM#23",
                         binding=make_binding(
                             (IngredientBinding(
                                 ingredient="vacc-generic",
                                 categories=("J07",)),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-23", target_kind=TARGET_KIND_CATEGORY,
                      target_value="J07", priority="high",
                      clause_locator="P23"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:category:J07",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 24. 同一单元同时有端点 boundary 与关键角色缺失 -> not_evaluable 优先
    cases.append(CMChallengeCase(
        number=24, name="boundary_plus_role_gap_not_evaluable",
        category="not_evaluable",
        description="端点 boundary 与未确认抢救治疗角色同时存在 -> not_evaluable 优先",
        build_episodes=lambda: (
            make_episode(record_id="CM#24",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientB"),)),
                         cm_start="2026-01-01", cm_end="2026-06-30",
                         treatment_role="", treatment_role_confirmed=False,
                         study_phase="treatment", study_phase_confirmed=True),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-REST-24", rule_type="restricted",
                      target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientB", priority="medium",
                      clause_locator="P24",
                      window_start="2026-01-01", window_end="2026-06-30",
                      start_inc=None, end_inc=True,
                      rescue_exception=True, priority_rationale="限制成分"),
        ),
        expected_units=(
            _ev(L1Disposition.NOT_EVALUABLE,
                rule_item_contains="restricted:ingredient:ingredientB"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 25. 同一稳定 CM event、相同成分/规则、普通更正且 lineage 不变 -> 持续
    # (身份持续 + deterministic replay -- N-to-N+1 harness + 专属断言)
    cases.append(CMChallengeCase(
        number=25, name="identity_persistence_on_data_correction",
        category="identity",
        description="相同成分/规则/lineage 数据更正 -> 身份持续 (deterministic replay)",
        build_episodes=lambda: (
            make_episode(record_id="CM#25",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-25", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P25"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 26. 两个竞争 identity binding 对同一 stable_core -> identity_ambiguous
    # (拒绝自动关闭) -- 由 N-to-N+1 harness 证明
    cases.append(CMChallengeCase(
        number=26, name="competing_identity_rejects_auto_close",
        category="lifecycle",
        description="竞争 identity 对同一 stable_core 产生 identity_ambiguous, 拒绝关闭",
        build_episodes=lambda: (
            make_episode(record_id="CM#26",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-26", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P26"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    # 27. cm_indication handoff 与 active mapping 双路去重 ----------------
    cases.append(CMChallengeCase(
        number=27, name="cm_indication_handoff_dedup",
        category="cross_domain",
        description="cm_indication ref content_hash 不含 snapshot id；claim 不变不重复",
        build_episodes=lambda: (
            make_episode(record_id="CM#27",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientT"),)),
                         treatment_role="treatment",
                         treatment_role_confirmed=True,
                         indication_text="头痛",
                         indication_concept="headache",
                         indication_mappable=True,
                         indication_source_record_id="IND#27"),
        ),
        linkage_coverage_complete=True,
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                risk_family_contains="indication_check",
                rule_item_contains="indication:headache",
                cand=1, query=1, cer=1,
                subtype=POSITIVE_SUBTYPE_MEDICATION_INDICATION_UNEXPLAINED),
        ),
        expected_set_size=1,
    ))

    # 28. compound episode 同时显示 positive 与 not_evaluable flags ---------
    cases.append(CMChallengeCase(
        number=28, name="compound_flags_l2_source_one",
        category="compound",
        description="复方 positive+not_evaluable 共存; L2 源记录仍为 1; not_eval 不产 candidate",
        build_episodes=lambda: (
            make_episode(record_id="CM#28",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),
                              IngredientBinding(
                                  component_slot="slot1",
                                  confirmation=CONFIRMATION_UNRESOLVED)),
                             original_name="合成复方H")),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-28", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P28"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="ingredient_resolution",
                rule_item_contains="ingredient_resolution:slot1",
                cand=0, query=0),
        ),
    ))

    # 29. 仅映射为 ip_exposure 的行不生成 D02 CM episode/unit --------------
    #     (通过 expand 对纯 IP 行零 episode 证明 -- 本 case 给空 episode 集合)
    cases.append(CMChallengeCase(
        number=29, name="ip_exposure_no_cm_unit",
        category="coverage",
        description="纯 ip_exposure 来源行不生成 D02 episode/unit; CM/IP 冲突 not_evaluable",
        build_episodes=lambda: (),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-29", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="high",
                      clause_locator="P29"),
        ),
        expected_units=(),
        expected_set_size=0,
    ))

    # 30. duck-type D02 结果不含 MedicalGrading 仍可复用 lifecycle ---------
    cases.append(CMChallengeCase(
        number=30, name="duck_type_lifecycle_no_medical_grading",
        category="lifecycle",
        description="D02 结果不含 MedicalGrading 仍满足协议并复用 lifecycle; identity tamper 失败",
        build_episodes=lambda: (
            make_episode(record_id="CM#30",
                         binding=make_binding(
                             (IngredientBinding(ingredient="ingredientA"),))),
        ),
        build_rules=lambda: (
            make_rule(rule_id="R-PROH-30", target_kind=TARGET_KIND_INGREDIENT,
                      target_value="ingredientA", priority="medium",
                      clause_locator="P30"),
        ),
        expected_units=(
            _ev(L1Disposition.POSITIVE,
                rule_item_contains="prohibited:ingredient:ingredientA",
                cand=1, query=1),
            _ev(L1Disposition.NOT_EVALUABLE,
                risk_family_contains="indication_check"),
        ),
    ))

    return CMChallengeMatrix(cases=tuple(cases))


# ---------------------------------------------------------------------------
# Coverage-ledger / lifecycle harness
# ---------------------------------------------------------------------------

def make_unit_evaluation(
    unit_result: CMUnitResult,
    *,
    snapshot_id: str = SNAPSHOT_ID,
    rule_lineage: str = RULE_LINEAGE,
    l0_status: str = "covered",
) -> UnitEvaluation:
    """Build a :class:`UnitEvaluation` from a D02 unit result with
    caller-supplied L0/provenance."""
    return unit_result.to_unit_evaluation(
        l0_status=l0_status,
        provenance_snapshot_id=snapshot_id,
        provenance_rule_lineage=rule_lineage)


def make_closed_cm_ledger(
    unit_results: Sequence[CMUnitResult],
    *,
    snapshot_id: str = SNAPSHOT_ID,
    rule_lineage: str = RULE_LINEAGE,
    domain_id: str = DOMAIN_ID,
    run_id: str = RUN_ID,
) -> CoverageLedger:
    """Build a *closed* R4 :class:`CoverageLedger` whose expected unit ids
    exactly equal the supplied unit results' unit ids.

    Works for any :class:`RiskDomainUnitResult`; D02 ``CMUnitResult``
    implements ``to_unit_evaluation``.
    """
    unit_ids = [ur.unit_id for ur in unit_results]
    eset = ExpectedSet(
        expected_set_hash_value=expected_set_hash(unit_ids),
        unit_ids=tuple(unit_ids),
        domain_id=domain_id, run_id=run_id,
        expected_count=len(unit_ids))
    ledger = CoverageLedger(expected_set=eset)
    for ur in unit_results:
        ue = make_unit_evaluation(
            ur, snapshot_id=snapshot_id, rule_lineage=rule_lineage)
        ledger.assign(ue)
    ledger.close()
    return ledger


def attach_risk_ref(
    unit_result: CMUnitResult,
    *,
    risk_instance_id: str,
    risk_identity_id: str,
    risk_state: str = "established",
) -> CMUnitResult:
    """Return a copy of ``unit_result`` with a historical risk-instance
    ref attached, so a NEGATIVE N+1 unit explicitly links the prior risk
    (Codex round-3 finding 4 / D02 §9.1 linked-negative close)."""
    from .contracts import RiskInstanceRef
    ref = RiskInstanceRef(
        risk_instance_id=risk_instance_id,
        risk_identity_id=risk_identity_id,
        risk_state=risk_state)
    return _replace(
        unit_result,
        risk_instance_refs=unit_result.risk_instance_refs + (ref,))


# ---------------------------------------------------------------------------
# Acceptance-service + lifecycle factories
# ---------------------------------------------------------------------------

def make_acceptance_service(local_user: str = "test") -> AcceptanceService:
    """A fresh real :class:`AcceptanceService` for synthetic snapshots."""
    return AcceptanceService(local_user=local_user)


def _make_accepted_snapshot(
    service: AcceptanceService,
    *,
    pid: str, rid: str, sid: str,
    rows: Optional[List[Dict[str, Any]]] = None,
    eligible: bool = True,
) -> Any:
    """Build a synthetic accepted snapshot via public R2 APIs only."""
    _rows = rows if rows is not None else [{"subject": "S001", "cm": "drugA"}]
    source = SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="v1", source_bytes=b"synthetic-d02")
    snap = ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version=f"cutoff-{sid}", rows=_rows)
    algo = IdentityAlgorithm(
        algorithm_id="alg-d02-1", name="record-id", version="1")
    mapping = MappingDefinition(
        mapping_id="m-d02-1", project_id=pid, source_revision_id=rid,
        identity_algorithm_id="alg-d02-1", source_field="CMTRT",
        canonical_field="cm_term", version="1", confidence=1.0,
        is_critical=True)
    result = MappingResult.from_verified(
        result_id="mr-d02-1", project_id=pid, snapshot=snap,
        mapping=mapping, identity_algorithm=algo, record_count=len(_rows))
    subjects = [r.get("subject", "S001") for r in _rows]
    rec_ids = [make_record_identity(pid, algo, {"subject": s}) for s in subjects]
    resolution = IdentityResolution(algorithm=algo, resolved=tuple(rec_ids))
    binding = SnapshotBinding(
        project_id=pid, snapshot=snap, source=source,
        identity_algorithm=algo, mapping_definitions=(mapping,),
        mapping_results=(result,), identity_resolution=resolution)
    actor = ACCEPTED_BY_SYSTEM_POLICY
    service.register(binding, actor)
    service.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                    evidence=service.evidence(sid, actor,
                                              structural_validation_complete=True))
    service.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                    evidence=service.evidence(sid, actor))
    service.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                    evidence=service.evidence(sid, actor, approved_scope=True))
    if eligible:
        service.advance(sid, SnapshotAcceptanceState.BASELINE_ELIGIBLE, actor,
                        evidence=service.evidence(
                            sid, actor, source_coverage_complete=True,
                            approved_scope=True))
    return snap


def make_baseline_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str = SNAPSHOT_ID,
    revision_id: str = SOURCE_REV_ID,
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a baseline-eligible full snapshot and return its id."""
    if rows is None:
        rows = [{"subject": "S001", "cm": "drugA"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_subsequent_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str,
    revision_id: str,
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a *subsequent* baseline-eligible full snapshot for close."""
    if rows is None:
        rows = [{"subject": "S001", "cm": "drugA"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_lifecycle(local_user: str = "test") -> RiskLifecycle:
    return RiskLifecycle(local_user=local_user)


# ---------------------------------------------------------------------------
# N-to-N+1 deterministic replay harness
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NToN1Replay:
    """Result of one N-to-N+1 deterministic replay.

    Captures the N positive unit/candidate/identity, the N+1 negative
    unit (with the historical risk link attached), the
    :class:`ReconcileResult` and the post-replay lifecycle state, so the
    test can assert immutable historical completion, stable identity,
    versioned lineage, no duplicates and deterministic replay.
    """

    n_unit: CMUnitResult
    n_candidate_id: str
    n_identity_id: str
    n_instance_id: str
    n1_unit: CMUnitResult
    established_instance: Any
    reconcile: Any
    lifecycle: RiskLifecycle

    @property
    def closed(self) -> bool:
        return self.reconcile.closed != ()


def run_n_to_n1_replay(
    *,
    case: CMChallengeCase,
    service: AcceptanceService,
    lifecycle: RiskLifecycle,
    adapter: Any,
    n_snapshot_id: str = "snap-d02-N",
    n1_snapshot_id: str = "snap-d02-N1",
    strategy_override: Optional[MedicationMatchStrategy] = None,
    n1_strategy_override: Optional[MedicationMatchStrategy] = None,
    n1_linkage_coverage_complete: bool = True,
    force_negative_n1: bool = True,
) -> NToN1Replay:
    """Run a deterministic N->N+1 replay for one challenge case.

    1. Evaluate the case at snapshot N (baseline-eligible) with the
       case's own strategy.
    2. Promote the single positive unit through the adapter, establishing
       exactly one risk.
    3. Re-evaluate the *same* synthetic inputs at snapshot N+1.  By
       default (``force_negative_n1=True``) every N+1 unit is forced to
       NEGATIVE and the matching unit is given the exact historical
       risk-instance link (exact linked-negative, §9.1), so a low/medium
       risk machine-closes and the historical record is preserved.
    4. Build a closed, complete CoverageLedger over the N+1 units and
       call ``reconcile_n_to_n1``.

    Set ``force_negative_n1=False`` for the lineage-change path: when
    ``n1_strategy_override`` differs from the N strategy, the same stable
    event re-evaluates POSITIVE under a new lineage fingerprint.  The
    reconcile then detects the lineage change and supersedes the risk
    rather than closing it (§9.1: ``superseded``, never
    ``resolved_by_data``).

    The replay is deterministic: the same inputs always produce the same
    N identity, the same N+1 identity, and the same reconcile outcome.
    """

    strategy_n = strategy_override or make_strategy()

    # -- N evaluation ----------------------------------------------------
    exp_n, results_n = _evaluate_case_at(
        case, snapshot_id=n_snapshot_id, strategy=strategy_n,
        linkage_coverage_complete=case.linkage_coverage_complete)
    positive_n = _pick_positive(results_n)
    if positive_n is None:
        raise ValueError(
            f"case {case.number} ({case.name}) produced no positive N unit; "
            f"cannot run N->N+1 replay")
    # Promote: register + establish exactly one risk.
    outcome = adapter.promote_unit_result(positive_n)
    if not outcome.established_risk_ids:
        raise ValueError(
            f"case {case.number} N promotion established no risk")
    instance_id, identity_id = outcome.established_risk_ids[0]
    established = lifecycle.get(instance_id)

    # -- N+1 evaluation -------------------------------------------------
    strategy_n1 = n1_strategy_override or strategy_n
    _, results_n1_raw = _evaluate_case_at(
        case, snapshot_id=n1_snapshot_id, strategy=strategy_n1,
        linkage_coverage_complete=n1_linkage_coverage_complete)
    if force_negative_n1:
        # Full correction snapshot: force every N+1 unit NEGATIVE and
        # attach the exact historical risk link to the unit that carried
        # the N positive's rule_item token (exact linked-negative, §9.1).
        n1_results, n1_unit, found = _link_negative_n1(
            results_n1_raw, positive_n, established)
        if not found:
            raise ValueError(
                f"case {case.number} produced no corresponding N+1 "
                f"negative unit")
    else:
        # Lineage-change path: keep the positive N+1 rule unit (same
        # stable event, new lineage fingerprint) but force every other
        # unit NEGATIVE so no not_evaluable sibling blocks the supersede
        # detection (the reconcile checks carry-forward before lineage).
        n1_unit = _pick_positive(results_n1_raw)
        if n1_unit is None:
            raise ValueError(
                f"case {case.number} produced no positive N+1 unit for "
                f"the supersede path")
        n1_results = [
            r if r.unit_id == n1_unit.unit_id else _force_negative(r)
            for r in results_n1_raw]

    # -- closed complete ledger over the corrected N+1 units ------------
    ledger = make_closed_cm_ledger(
        n1_results, snapshot_id=n1_snapshot_id)

    reconcile = adapter.reconcile_n_to_n1(
        previous_instances=[established],
        next_unit_results=n1_results,
        coverage_snapshot_id=n1_snapshot_id,
        coverage_ledger=ledger)

    return NToN1Replay(
        n_unit=positive_n,
        n_candidate_id=(positive_n.r2_candidates[0].candidate_id
                        if positive_n.r2_candidates else ""),
        n_identity_id=identity_id,
        n_instance_id=instance_id,
        n1_unit=n1_unit,
        established_instance=established,
        reconcile=reconcile,
        lifecycle=lifecycle)


def _evaluate_case_at(
    case: CMChallengeCase,
    *,
    snapshot_id: str,
    strategy: MedicationMatchStrategy,
    linkage_coverage_complete: bool,
) -> Tuple[CMExpectedSetExpansion, List[CMUnitResult]]:
    """Re-evaluate a case's synthetic inputs at a given snapshot/strategy."""
    policy = make_policy()
    exp, by_subject = evaluate(
        list(case.build_episodes()), list(case.build_rules()),
        strategy=strategy, policy=policy,
        evidence_records=list(case.build_evidence()),
        ip_exposure_records=list(case.build_ip_records()),
        snapshot_id=snapshot_id,
        linkage_coverage_complete=linkage_coverage_complete)
    ordered: List[CMUnitResult] = []
    for eu in exp.units:
        uid = eu.build_unit(PROJECT_ID, strategy).unit_id
        for urs in by_subject.values():
            for r in urs:
                if r.unit_id == uid:
                    ordered.append(r)
                    break
    return exp, ordered


def _pick_positive(
    results: Sequence[CMUnitResult],
) -> Optional[CMUnitResult]:
    for r in results:
        if r.l1_disposition == L1Disposition.POSITIVE and r.r2_candidates:
            return r
def _link_negative_n1(
    n1_results: Sequence[CMUnitResult],
    n_positive: CMUnitResult,
    established: Any,
) -> Tuple[List[CMUnitResult], CMUnitResult, bool]:
    """Force every N+1 unit to NEGATIVE (the corrected snapshot state) and
    attach the exact historical risk link to the unit that carried the N
    positive's rule_item token.

    Returns ``(forced_results, linked_unit, found)``.  The forced results
    form a complete negative N+1 domain so the machine-close coverage
    proof can succeed (no not_evaluable blocks completeness).  The linked
    unit carries the exact ``risk_instance_id`` + ``risk_identity_id`` of
    the established N risk (the exact linked-negative contract, §9.1).

    Matching: the N positive's candidate stores ``rule_item_or_concept``;
    we find the N+1 unit whose re-evaluated candidate carries the same
    token, or fall back to identical ``unit_id`` (identity-persistence
    path where the N+1 strategy equals the N strategy).
    """
    target_token = ""
    for cand in n_positive.r2_candidates:
        target_token = str(cand.detail.get("rule_item_or_concept", ""))
        if target_token:
            break
    linked_unit: Optional[CMUnitResult] = None
    forced: List[CMUnitResult] = []
    found = False
    for r in n1_results:
        cand_token = ""
        for cand in r.r2_candidates:
            cand_token = str(cand.detail.get("rule_item_or_concept", ""))
            break
        same_token = (target_token and cand_token
                      and cand_token == target_token)
        if (same_token or r.unit_id == n_positive.unit_id) and not found:
            forced.append(attach_risk_ref(
                _force_negative(r),
                risk_instance_id=established.risk_instance_id,
                risk_identity_id=established.risk_identity_id,
                risk_state=established.current_state))
            linked_unit = forced[-1]
            found = True
        else:
            forced.append(_force_negative(r))
    return forced, linked_unit, found


def _force_negative(unit: CMUnitResult) -> CMUnitResult:
    """Return a copy of ``unit`` forced to NEGATIVE with no candidates.

    Used only to model the linked-negative N+1 outcome for the replay
    harness: the N+1 snapshot has resolved the clue (e.g. AE/MH now
    recorded), so the same rule unit becomes a clean negative that
    explicitly links the prior risk.  The unit_id and identity dimensions
    are preserved so the ledger expected-set still matches.
    """
    return _replace(
        unit,
        l1_disposition=L1Disposition.NEGATIVE,
        r2_candidates=(),
        risk_candidate_refs=(),
        query_refs=(),
        cross_domain_evidence_refs=(),
        positive_subtype="",
        audience_label="",
        not_evaluable_reason="",
        boundary_reason="")
