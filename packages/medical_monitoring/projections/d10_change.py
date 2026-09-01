"""Change, center distribution, trend, and warning projections."""

from .d10_core import *

# ---------------------------------------------------------------------------
# Change section (contract section 14)
# ---------------------------------------------------------------------------


def _derive_clinical_change_kind(ch: Any, result: D10RunResult) -> str:
    """Deterministic clinical-change kind from the typed change decision.

    Mirrors the evaluator's derivation without re-running the evaluator:
    full initial runs and replay runs report ``initial_current``; non-data
    change reports ``not_comparable``; otherwise the typed
    ``data_change_kind`` (or ``continued``) is used.
    """
    if ch is None:
        return "initial_current"
    if ch.execution_basis == "full":
        if (ch.cutoff_advance is not None
                and ch.cutoff_advance.decision_state == "same_window"
                and ch.claimed_cutoff_state is None):
            return "initial_current"
        return ch.data_change_kind or "initial_current"
    if ch.comparison_state == "not_comparable":
        return "not_comparable"
    non_data = _non_data_change_ref_count(ch)
    if non_data > 0:
        return "not_comparable"
    return ch.data_change_kind or "continued"


def _non_data_change_ref_count(ch: Any) -> int:
    if ch is None:
        return 0
    return (len(ch.denominator_change_refs) + len(ch.coverage_change_refs)
            + len(ch.knowledge_change_refs) + len(ch.rule_change_refs)
            + len(ch.mapping_change_refs) + len(ch.model_change_refs)
            + len(ch.method_change_refs) + len(ch.population_change_refs)
            + len(ch.visibility_change_refs) + len(ch.mode_change_refs))


def _change_cause(ch: Any) -> Optional[str]:
    if ch is None:
        return None
    non_data = [key for key, count in (
        ("denominator", len(ch.denominator_change_refs)),
        ("coverage", len(ch.coverage_change_refs)),
        ("knowledge", len(ch.knowledge_change_refs)),
        ("rule", len(ch.rule_change_refs)),
        ("mapping", len(ch.mapping_change_refs)),
        ("model", len(ch.model_change_refs)),
        ("method", len(ch.method_change_refs)),
        ("population", len(ch.population_change_refs)),
        ("visibility", len(ch.visibility_change_refs)),
        ("mode", len(ch.mode_change_refs)),
    ) if count > 0]
    if non_data:
        return non_data[0] if len(non_data) == 1 else "mixed"
    if len(ch.data_change_refs) > 0:
        return "data"
    return None


@dataclass(frozen=True)
class D10ChangeSection:
    """Current/change section of the project projection (contract section
    14).

    ``fresh_full`` is True only for an initial/replay full run whose
    audience narrative is 初始全量 (no new/resolved/… claim); ``analysis
    only`` marks non-data changes whose narrative is 分析口径变化 and never
    a clinical improvement/worsening claim."""

    change_kind: str
    change_cause: Optional[str]
    lineage_relation: str
    analysis_only: bool
    fresh_full: bool
    replay: bool
    change_kind_zh: str
    change_cause_zh: Optional[str]
    lineage_zh: str
    narrative_zh: str


def build_d10_change_section(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10ChangeSection:
    """Build the change section narrative from typed change facts."""
    _assert_authoritative_result(typed, result)
    ch = typed.change_decision
    if ch is None:
        return D10ChangeSection(
            change_kind="initial_current", change_cause=None,
            lineage_relation="initial_full_snapshot", analysis_only=False,
            fresh_full=True, replay=False,
            change_kind_zh=_CHANGE_KIND_ZH["initial_current"],
            change_cause_zh=None,
            lineage_zh=_LINEAGE_ZH["initial_full_snapshot"],
            narrative_zh="本次为首次全量快照，仅呈现当前状态，不产生新增或关闭等变化判定。")
    kind = _derive_clinical_change_kind(ch, result)
    cause = _change_cause(ch)
    lineage = ch.lineage_relation or ("initial_full_snapshot"
                                      if ch.execution_basis == "full"
                                      else "continued_from_data_revision")
    replay = bool(ch.execution_basis == "full"
                  and ch.cutoff_advance is not None
                  and ch.cutoff_advance.decision_state == "same_window"
                  and ch.claimed_cutoff_state is None)
    fresh_full = bool(ch.execution_basis == "full" and not replay)
    analysis_only = bool(_non_data_change_ref_count(ch) > 0
                         or ch.comparison_state == "not_comparable")
    kind_zh = _CHANGE_KIND_ZH.get(kind, kind)
    cause_zh = _CHANGE_CAUSE_ZH.get(cause, cause) if cause else None
    lineage_zh = _LINEAGE_ZH.get(lineage, lineage)
    if replay or fresh_full:
        narrative = "本次为初始或同窗全量快照，仅呈现当前状态，不产生新增或关闭等变化判定。"
    elif analysis_only:
        narrative = "分析口径变化，前后不可直接比较。"
    elif kind == "continued":
        narrative = ("本版相对上一可比版本为持续状态，变化原因为"
                     f"{cause_zh or '数据变化'}。")
    elif kind == "resolved":
        narrative = "本版相对上一可比版本为关闭状态，变化原因为数据变化。"
    elif kind == "reopened":
        narrative = "本版相对上一可比版本为重开状态，变化原因为数据变化。"
    elif kind == "new":
        narrative = f"本版相对上一可比版本为新增状态，变化原因为{cause_zh or '数据变化'}。"
    elif kind in ("upgraded", "downgraded"):
        narrative = (f"本版相对上一可比版本为{kind_zh}状态，变化原因为"
                     f"{cause_zh or '数据变化'}。")
    else:
        narrative = f"本版状态为{kind_zh}，变化原因为{cause_zh or '数据变化'}。"
    _assert_clean_zh(kind_zh, cause_zh or "", lineage_zh, narrative)
    _assert_no_structured_ref_in_text(typed, narrative)
    return D10ChangeSection(
        change_kind=kind,
        change_cause=cause,
        lineage_relation=lineage,
        analysis_only=analysis_only,
        fresh_full=fresh_full,
        replay=replay,
        change_kind_zh=kind_zh,
        change_cause_zh=cause_zh,
        lineage_zh=lineage_zh,
        narrative_zh=narrative,
    )


# ---------------------------------------------------------------------------
# Center distribution and trend/warning surfaces (contract section 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D10CenterPatternRow:
    """One center column of the center distribution surface.

    Absolute counts and an explicit-denominator rate per projectable site;
    the rate column is present only under the permitted rate state with no
    hidden members/sites.  Small-sample / late-start / follow-up warnings
    are carried as typed warning codes, never as a quality verdict."""

    site_ref: str
    site_activation_state: str
    member_count: int
    affected_subject_count: int
    denominator_value: Optional[int]
    rate_zh: Optional[str]
    warning_codes: Tuple[str, ...]
    coverage_state: str


def _site_denominator_value(typed: D10TypedInput, site: str) -> Optional[int]:
    ledger = typed.site_ledger
    if ledger.site_ref != site:
        return None
    kind = typed.denominator.denominator_kind
    if kind == "treated_subjects":
        return len(ledger.treated_subject_refs)
    if kind == "enrolled_subjects":
        return len(ledger.eligible_subject_refs)
    if kind == "safety_evaluable_subjects":
        return len(ledger.evaluable_subject_refs)
    if kind == "efficacy_evaluable_subjects":
        return len(ledger.evaluable_subject_refs)
    return None


def build_d10_center_distribution(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10CenterPatternRow, ...]:
    """Center distribution surface: absolute counts and explicit
    denominator rates per projectable site.  No punitive ranking: rows are
    ordered by stable site identity."""
    _assert_authoritative_result(typed, result)
    _eval_sites, proj_sites, _hidden_sites = _resolve_visibility_sites(typed, result)
    if not proj_sites:
        return ()
    visibility = typed.visibility_decision
    withheld = (len(typed.visibility_decision.hidden_member_refs) > 0
                or len(typed.visibility_decision.hidden_site_refs) > 0)
    pair_visible = _pair_visible_members(typed, result)
    members_by_site: Dict[str, List[Any]] = {}
    for member in pair_visible:
        members_by_site.setdefault(member.site_stable_id, []).append(member)
    warning_codes = [code for code in typed.comparison_gate.reason_codes
                     if not code.startswith("comparison_")
                     and not code.startswith("window_pair_")]
    precision = max(0, typed.numeric_policy.display_precision)
    rows: List[D10CenterPatternRow] = []
    for site in sorted(proj_sites):
        members = members_by_site.get(site, [])
        subjects = len({m.subject_stable_id for m in members
                        if m.subject_stable_id})
        den_value = _site_denominator_value(typed, site)
        rate_zh: Optional[str] = None
        if (visibility.rate_projection_state == "permitted" and not withheld
                and den_value and den_value > 0):
            percent = _half_up(100.0 * subjects / den_value, precision)
            rate_zh = f"{subjects}/{den_value}（{percent:.{precision}f}%）"
        rows.append(D10CenterPatternRow(
            site_ref=site,
            site_activation_state=typed.site_ledger.site_activation_state
            if typed.site_ledger.site_ref == site else "active",
            member_count=len(members),
            affected_subject_count=subjects,
            denominator_value=den_value,
            rate_zh=rate_zh,
            warning_codes=tuple(warning_codes),
            coverage_state=_coverage_state(typed),
        ))
    return tuple(rows)


@dataclass(frozen=True)
class D10TrendSurface:
    """Time/safety/efficacy trend surface (contract sections 8/12).

    A descriptive-monitoring surface only: analysis set, window, denominator,
    method and uncertainty are carried in typed engineering fields; the
    audience narrative is the frozen descriptive-monitoring phrase and never
    a confirmatory or benefit-risk verdict."""

    trend_surface_present: bool
    signal_kind: str
    evaluation_window_instance_ref: str
    window_text_zh: str
    analysis_population_ref: Optional[str]
    denominator_kind: str
    denominator_value: int
    estimate_kind: Optional[str]
    exposure_definition_ref: Optional[str]
    coding_dictionary_ref: Optional[str]
    severity_scale_ref: Optional[str]
    endpoint_definition_ref: Optional[str]
    estimand_ref: Optional[str]
    missing_data_rule_ref: Optional[str]
    intercurrent_event_rule_ref: Optional[str]
    treatment_role_authority_ref: Optional[str]
    small_sample: bool
    limited_evidence: bool
    limited_reason: Optional[str]
    trend_note_zh: str


def build_d10_trend_surface(
    typed: D10TypedInput,
    result: D10RunResult,
) -> D10TrendSurface:
    """Build the time/safety/efficacy trend surface for trend signal
    kinds."""
    _assert_authoritative_result(typed, result)
    kind = typed.signal_definition.signal_kind
    safety = typed.safety_context
    efficacy = typed.efficacy_context
    limits = typed.evaluation_limits
    trend_present = kind in ("project_time_trend", "project_safety_trend",
                             "project_efficacy_trend")
    estimate = None
    if result.unit is not None:
        estimate = result.unit.estimate_kind
    elif efficacy is not None:
        estimate = efficacy.estimate_kind
    note = "描述性监测结果，仅供项目内复核；不构成正式确证或获益-风险结论。"
    if not trend_present:
        note = ""
    _assert_clean_zh(note)
    return D10TrendSurface(
        trend_surface_present=trend_present,
        signal_kind=kind,
        evaluation_window_instance_ref=_evaluation_window_instance_ref(typed),
        window_text_zh=_window_text(typed),
        analysis_population_ref=(typed.analysis_population.analysis_population_ref
                                 if typed.analysis_population.present else None),
        denominator_kind=typed.denominator.denominator_kind,
        denominator_value=typed.denominator.denominator_value,
        estimate_kind=estimate,
        exposure_definition_ref=safety.exposure_definition_ref if safety else None,
        coding_dictionary_ref=safety.coding_dictionary_ref if safety else None,
        severity_scale_ref=safety.severity_scale_ref if safety else None,
        endpoint_definition_ref=(efficacy.endpoint_definition_ref
                                 if efficacy else None),
        estimand_ref=efficacy.estimand_ref if efficacy else None,
        missing_data_rule_ref=efficacy.missing_data_rule_ref if efficacy else None,
        intercurrent_event_rule_ref=(efficacy.intercurrent_event_rule_ref
                                     if efficacy else None),
        treatment_role_authority_ref=(efficacy.treatment_role_authority_ref
                                      if efficacy else None),
        small_sample=limits.small_sample,
        limited_evidence=limits.limited_evidence,
        limited_reason=limits.limited_reason,
        trend_note_zh=note,
    )


@dataclass(frozen=True)
class D10WarningMarker:
    """One audience-safe warning marker.

    ``warning_zh`` is native Chinese; ``reason_code`` is a typed engineering
    field (never rendered to the audience)."""

    reason_code: str
    warning_zh: str


def build_d10_warnings(
    typed: D10TypedInput,
    result: D10RunResult,
) -> Tuple[D10WarningMarker, ...]:
    """Audience-safe warning markers from typed facts (contract section 12).

    Small-sample / short-follow-up / case-mix / method warnings are
    descriptive and never a center quality verdict; no punitive ranking and
    no black-box score is produced."""
    _assert_authoritative_result(typed, result)
    warnings: List[D10WarningMarker] = []
    seen: set = set()
    for code in typed.comparison_gate.reason_codes:
        if code.startswith("comparison_") or code.startswith("window_pair_"):
            continue
        if code in seen:
            continue
        seen.add(code)
        text = _CODED_WARNING_ZH.get(code)
        if text is None:
            continue
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(reason_code=code, warning_zh=text))
    limits = typed.evaluation_limits
    if limits.small_sample:
        text = "样本量较小，相关比例需谨慎解读。"
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code="small_sample", warning_zh=text))
    if limits.limited_evidence:
        detail = limits.limited_reason or ""
        text = (f"证据有限（{detail}），需结合更多信息复核。"
                if detail else "证据有限，需结合更多信息复核。")
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code="limited_evidence", warning_zh=text))
    rate_state = typed.visibility_decision.rate_projection_state
    if rate_state in ("suppressed", "qualified"):
        text = _RATE_STATE_ZH[rate_state]
        _assert_clean_zh(text)
        warnings.append(D10WarningMarker(
            reason_code=rate_state, warning_zh=text))
    return tuple(warnings)


__all__ = [name for name in globals() if not name.startswith("__")]
