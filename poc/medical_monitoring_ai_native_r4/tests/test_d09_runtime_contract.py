"""R4-D09 focused runtime contract tests (self-contained synthetic inputs).

Tests the closed typed contract and the deterministic center-pattern
evaluator with locally-built synthetic envelopes (no frozen artifact reads,
no case/fixture/test identifiers, no expected-leaf coupling):

* closed-enum and required-field validation of the typed envelope;
* contract-ordered fail-closed: pre-admission identity/authority/expected-set
  failure emits only the global gate and zero medical units; post-admission
  producer/coverage/denominator/opportunity/origin/window defects emit one
  ``not_evaluable`` unit and no risk/query payload;
* resolved domain facts drive the formerly metadata-carried decisions:
  authority validity and minimum-member threshold, producer content
  verification, method validity, statistical-signal role and member
  expansion, lineage supersession/carry-forward/site identity, Query
  redundancy and fanout, locator/anchor resolution;
* n=1 repeated risk boundary, closed-zero negative, design-clause
  not-applicable, window-pair gates, blinded treatment-stratum rejection;
* deterministic replay, member-order/display-label invariance;
* audit-metadata isolation: mutation context / anti-overfit records and
  synthetic sentinel spellings never change any result;
* runtime import/read closure and port-8911-stopped static/network checks.
"""

from __future__ import annotations

import hashlib
import re
import socket
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d09_contracts import (  # noqa: E402
    AnalysisWindow,
    AudienceLexicon,
    CenterQueryPolicy,
    CoverageStatus,
    Cutoff,
    D09ContractError,
    D09TypedInput,
    Denominator,
    ExpectedSet,
    LineageContext,
    MethodComparabilityDecision,
    MutationContext,
    NumericPolicy,
    Opportunity,
    PatternDefinition,
    QueryRedundancyDecision,
    ResolvedAuthorityDecision,
    ScopeBinding,
    SourceVerificationRecord,
    Stratum,
    SubjectRiskMember,
    VisibilityDecision,
    d09_content_hash,
    validate_typed_input,
)
from mm_r4.d09_evaluator import evaluate  # noqa: E402


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _authority(kind: str = "repeated_subject_risk", *, validity: str = "valid",
               repeated_minimum: Optional[int] = 2,
               gap_minimum: Optional[int] = 5,
               trend_minimum: Optional[int] = 3) -> ResolvedAuthorityDecision:
    repeated = repeated_minimum if kind == "repeated_subject_risk" else None
    gap = gap_minimum if kind == "systematic_data_or_process_gap" else None
    trend = trend_minimum if kind == "within_site_time_trend" else None
    if validity == "invalid":
        repeated = gap = trend = None
    payload = {
        "authority_ref": "SYN-AUTH-1",
        "mode_contract_version": "SYN-D09-MODE-001",
        "minimum_member_subject_count": repeated,
        "gap_positive_minimum_opportunity_count": gap,
        "trend_positive_minimum_subject_count": trend,
    }
    return ResolvedAuthorityDecision(
        minimum_member_subject_count=repeated,
        gap_positive_minimum_opportunity_count=gap,
        trend_positive_minimum_subject_count=trend,
        authority_validity_state=validity,
        authority_ref="SYN-AUTH-1",
        authority_locator_ref="SYN-AUTH-LOC-1",
        mode_contract_version="SYN-D09-MODE-001",
        authority_content_hash=d09_content_hash(payload),
    )


def _query_policy(fanout: int = 100) -> CenterQueryPolicy:
    payload = {
        "policy_id": "SYN-QPOL-1",
        "mode_contract_version": "SYN-D09-MODE-001",
        "max_query_member_fanout": fanout,
        "member_order_policy": "stable_member_ref_ascending",
        "redundancy_rule_ref": "SYN-QRED-RULE-1",
        "allowed_action_kinds": ["request_record_verification", "verify_pd"],
        "pd_wording_rule_ref": "SYN-PD-WORDING-1",
        "effective_interval": "synthetic-open-interval",
    }
    return CenterQueryPolicy(
        **{**payload, "allowed_action_kinds": tuple(payload["allowed_action_kinds"])},
        content_hash=d09_content_hash(payload),
    )


def _query_decision(members: Tuple[Any, ...], *,
                    decision: str = "site_process_delta_present",
                    fanout: int = 100) -> QueryRedundancyDecision:
    member_ids = sorted(member.member_id for member in members)
    member_queries = sorted(set(
        ref for member in members
        for ref in getattr(member, "query_draft_refs", ())
    ))
    covered = member_ids if decision == "fully_covered_by_member_queries" else []
    uncovered = [] if decision == "fully_covered_by_member_queries" else member_ids
    proof = {
        "decision": decision,
        "covered": covered,
        "uncovered": uncovered,
        "member_queries": member_queries,
        "fanout": fanout,
    }
    return QueryRedundancyDecision(
        decision=decision,
        max_query_member_fanout=fanout,
        unit_member_set_hash=d09_content_hash(member_ids),
        covered_member_refs=tuple(covered),
        uncovered_member_refs=tuple(uncovered),
        member_query_refs=tuple(member_queries),
        coverage_proof_hash=d09_content_hash(proof),
    )


def _risk(member_id: str, subject: str, *, cutoff: str = "in_cutoff",
          origin: str = "distinct", locator: str = "SYN-LOC-1",
          event: Optional[str] = None,
          loc_state: str = "locatable",
          query_refs: Tuple[str, ...] = ()) -> SubjectRiskMember:
    return SubjectRiskMember(
        member_id=member_id,
        subject_stable_id=subject,
        site_stable_id="SYN-SITE-1",
        producer_domain="D01",
        risk_kind="d01_seriousness_hospital_death",
        monitoring_priority="medium",
        public_r4_risk_identity=f"SYN-RID-{member_id}",
        source_event_identity=event or f"SYN-EVT-{member_id}",
        event_time_ref="2026-02-01",
        cutoff_relation=cutoff,
        origin_decision=origin,
        source_locator_refs=(locator,),
        query_draft_refs=query_refs,
        source_locator_resolution_state=loc_state,
    )


def _definition(**overrides: Any) -> PatternDefinition:
    base = dict(
        pattern_definition_id="SYN-DEF-1",
        pattern_kind="repeated_subject_risk",
        clinical_label_zh="synthetic label",
        risk_domain="safety_quality",
        clinical_claim_token="d09_repeated_subject_risk",
        d09_action="evaluate_and_own",
        required_producer_domains=("D01",),
        accepted_member_risk_kinds=("d01_seriousness_hospital_death",),
        numerator_contract_id="SYN-NUM-1",
        allowed_denominator_kinds=("evaluable_subjects",),
        window_contract_id="SYN-WC-1",
        stratum_contract_id="SYN-SC-1",
        comparability_contract_id="SYN-CC-1",
        positive_rule_ref="SYN-RULE-POS-1",
        counterevidence_rule_refs=(),
        monitoring_priority_rule_ref="SYN-RULE-PRIO-1",
        center_query_policy_id="SYN-QP-1",
        minimum_member_subject_count_ref=None,
        required_window_count_ref=None,
        opportunity_contract_id=None,
        authority_version="SYN-AUTH-1",
        pattern_definition_content_hash=_sha("d09-content-v1:def:SYN-DEF-1"),
        legal_definition_matrix_content_hash=_sha(
            "d09-content-v1:legal-definition-matrix-d09-v1"),
        numeric_execution_policy_content_hash=_sha(
            "d09-content-v1:numeric-execution-policy-d09-v1"),
    )
    base.update(overrides)
    return PatternDefinition(**base)


def _window(window_kind: str = "calendar_interval", *,
            stable_id: str = "SYN-WIN-1",
            anchor: str = "calendar_date", state: str = "closed",
            contract_hash: Optional[str] = None,
            definition_id: Optional[str] = None) -> AnalysisWindow:
    return AnalysisWindow(
        window_instance_id=f"{stable_id}-INST",
        analysis_window_stable_id=stable_id,
        window_kind=window_kind,
        window_definition_id=definition_id or f"SYN-WD-{stable_id}",
        inclusivity="both_inclusive",
        anchor_kind=anchor,
        computed_window_start="2026-01-01",
        computed_window_end="2026-03-31",
        cutoff_id="SYN-CUT-1",
        scope_binding_stable_id="SYN-SCOPE-1",
        window_state=state,
        window_contract_content_hash=contract_hash or _sha(
            "d09-content-v1:window-contract:SYN-WC-1"),
    )


def _base_typed_input(**overrides: Any) -> D09TypedInput:
    """A minimal valid typed bundle (all facts closed and consistent)."""
    base: Dict[str, Any] = dict(
        envelope_id="SYN-ENV-1",
        input_schema="d09-typed-input-v1",
        project_ref="SYN-PROJECT-1",
        run_ref="SYN-RUN-1",
        snapshot_ref="SYN-SNAP-1",
        source_revision_set=("SYN-REV-1",),
        source_content_hashes=(_sha("d09-rev:SYN-REV-1"),),
        site_stable_id="SYN-SITE-1",
        scope_binding=ScopeBinding(scope_binding_id="SYN-SB-1"),
        pattern_definition=_definition(),
        mode_contract_version="SYN-D09-MODE-001",
        matched_counterevidence_rule_refs=(),
        mode_contract_design_clause_ref=None,
        analysis_windows=(_window(),),
        stratum=Stratum(
            stratum_contract_id="SYN-SC-1",
            stratum_contract_content_hash=_sha("d09-content-v1:stratum-contract:SYN-SC-1"),
            stratum_key="overall",
            stratum_state="closed",
            stratum_admission="admitted",
        ),
        coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                 l1_medical_completeness_state="complete"),),
        subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),),
        gap_members=(),
        change_ledger_members=(),
        denominator=Denominator(denominator_kind="evaluable_subjects",
                                denominator_value=42,
                                denominator_state="closed_positive"),
        opportunity=Opportunity(opportunity_definition_ref="SYN-OPPDEF-1",
                                expected_opportunity_count=42,
                                observed_opportunity_count=0,
                                opportunity_state="sufficient"),
        cutoff=Cutoff(cutoff_id="SYN-CUT-1", cutoff_contract_id="SYN-CUTC-1",
                      snapshot_as_of="2026-07-01T00:00:00+00:00",
                      clinical_event_cutoff="2026-06-30",
                      cutoff_identity_state="consistent",
                      cutoff_policy_ref="SYN-RULE-CUT-1"),
        numeric_policy=NumericPolicy(),
        visibility_decision=VisibilityDecision(audience_scope_id="SYN-AUD-1"),
        expected_set=ExpectedSet(),
        mutation_context=MutationContext(),
        anti_overfit_variant=None,
        evidence_refs=(),
        audience_lexicon=AudienceLexicon(
            affected_subjects_zh="受影响受试者 {n} 名",
            center_pattern_count_zh="中心模式 {n} 项",
            coverage_zh="本次可评价范围/数据完整性",
            event_count_zh="事件 {n} 起",
            individual_risk_count_zh="相关个体风险 {n} 条",
            pattern_label_zh="中心重复风险模式",
            disposition_zh={},
            lifecycle_zh={},
            forbidden_internal_terms=()),
        method_comparability_decision=MethodComparabilityDecision(
            method_validity_state="valid",
            statistical_signal_role="none",
            member_expansion_state="not_applicable",
            window_rule_version_refs=("SYN-WRULE-1",),
            stratum_method_version_refs=("SYN-SMVER-1",)),
        lineage_context=LineageContext(),
        source_verification_records=(SourceVerificationRecord(
            revision="SYN-REV-1",
            declared_content_hash=_sha("d09-rev:SYN-REV-1"),
            verified_content_hash=_sha("d09-rev:SYN-REV-1"),
            verification_state="verified"),),
    )
    base.update(overrides)
    kind = base["pattern_definition"].pattern_kind
    if "resolved_authority_decision" not in overrides:
        base["resolved_authority_decision"] = _authority(kind)
    explicit_query = overrides.get("query_redundancy_decision")
    fanout = (explicit_query.max_query_member_fanout
              if explicit_query is not None else 100)
    if "center_query_policy" not in overrides:
        base["center_query_policy"] = _query_policy(fanout)
    if "query_redundancy_decision" not in overrides:
        if kind == "repeated_subject_risk":
            members = tuple(base["subject_risk_members"])
        elif kind == "systematic_data_or_process_gap":
            members = tuple(base["gap_members"])
        else:
            members = tuple(base["change_ledger_members"])
        base["query_redundancy_decision"] = _query_decision(
            members, fanout=base["center_query_policy"].max_query_member_fanout)
    if ("source_verification_records" not in overrides
            and ("source_revision_set" in overrides
                 or "source_content_hashes" in overrides)):
        base["source_verification_records"] = tuple(
            SourceVerificationRecord(
                revision=revision,
                declared_content_hash=content_hash,
                verified_content_hash=content_hash,
                verification_state="verified",
            )
            for revision, content_hash in zip(
                base["source_revision_set"], base["source_content_hashes"])
        )
    return D09TypedInput(**base)


def _semantic_snapshot(result: Any) -> Tuple[Any, ...]:
    """Deterministic view of a run result excluding the typed envelope ref."""
    excluded = {"typed"}
    return tuple((name, getattr(result, name))
                 for name in sorted(vars(result))
                 if name not in excluded and not name.startswith("_"))


def _run(**overrides: Any):
    typed = _base_typed_input(**overrides)
    validate_typed_input(typed)
    return evaluate(typed)


# ---------------------------------------------------------------------------
# Typed validation
# ---------------------------------------------------------------------------


class TestTypedValidation(unittest.TestCase):
    def _reject(self, **overrides: Any) -> None:
        with self.assertRaises(D09ContractError):
            validate_typed_input(_base_typed_input(**overrides))

    def test_closed_enums_reject_invalid_values(self) -> None:
        self._reject(pattern_definition=_definition(pattern_kind="bogus_kind"))
        self._reject(
            pattern_definition=_definition(
                clinical_claim_token="d09_cross_site_outlier"))
        self._reject(
            denominator=Denominator(denominator_kind="enrolled_subjects",
                                    denominator_value=42,
                                    denominator_state="closed"),
        )
        self._reject(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="bogus",
                                     l1_medical_completeness_state="complete"),),
        )
        self._reject(input_schema="d09-typed-input-v2")
        self._reject(visibility_decision=VisibilityDecision(
            audience_scope_id="SYN-AUD-1", blind_status="bogus"))

    def test_resolved_fact_enums_reject_invalid_values(self) -> None:
        self._reject(resolved_authority_decision=replace(
            _authority(), authority_validity_state="bogus"))
        self._reject(method_comparability_decision=MethodComparabilityDecision(
            method_validity_state="bogus"))
        self._reject(method_comparability_decision=MethodComparabilityDecision(
            statistical_signal_role="bogus"))
        self._reject(lineage_context=LineageContext(carry_forward_state="bogus"))
        self._reject(lineage_context=LineageContext(lineage_relation="bogus"))
        self._reject(lineage_context=LineageContext(site_identity_state="bogus"))
        self._reject(query_redundancy_decision=replace(
            _query_decision((_risk("R-1", "SYN-SUBJ-1"),)),
            decision="bogus"))
        self._reject(source_verification_records=(SourceVerificationRecord(
            revision="SYN-REV-1",
            declared_content_hash=_sha("a"),
            verified_content_hash=_sha("b"),
            verification_state="bogus"),))
        self._reject(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", loc_state="bogus"),))
        from mm_r4.d09_contracts import GapMember
        self._reject(gap_members=(GapMember(
            member_id="SYN-GAP-1", subject_stable_id="SYN-SUBJ-1",
            site_stable_id="SYN-SITE-1", producer_domain="D05",
            gap_kind="missing_required_field", gap_opportunity_id="SYN-GAPOPP-1",
            gap_definition_id="SYN-GAPDEF-1",
            normalized_field_or_process_identity="SYN-FIELD-1",
            obligation_or_opportunity_ref="SYN-OBL-1",
            visit_or_time_anchor_refs=("2026-02-01",),
            anchor_resolution_state="bogus"),))

    def test_required_fields_enforced(self) -> None:
        self._reject(envelope_id="")
        self._reject(source_revision_set=("A", "B"),
                     source_content_hashes=(_sha("d09-rev:A"),))
        self._reject(source_content_hashes=("not-a-hash",))
        with self.assertRaises(D09ContractError):
            validate_typed_input(None)  # type: ignore[arg-type]

    def test_audit_metadata_shape_only(self) -> None:
        # Mutation context is opaque audit metadata: closed vocabulary is
        # test-side; the runtime only requires a well-formed shape.
        typed = _base_typed_input(mutation_context=MutationContext(
            mutation_class="any_test_label", desc="any prose",
            variant_id="v1", base_fixture_id="bf-1"))
        validate_typed_input(typed)
        with self.assertRaises(D09ContractError):
            validate_typed_input(_base_typed_input(
                mutation_context=MutationContext(mutation_class="")))

    def test_three_ownable_token_kind_bijections_validate(self) -> None:
        bijections = (
            ("repeated_subject_risk", "d09_repeated_subject_risk"),
            ("systematic_data_or_process_gap", "d09_systematic_data_or_process_gap"),
            ("within_site_time_trend", "d09_within_site_time_trend"),
        )
        for kind, token in bijections:
            typed = _base_typed_input(
                pattern_definition=_definition(pattern_kind=kind,
                                               clinical_claim_token=token))
            validate_typed_input(typed)

    def test_claim_kind_action_and_member_scope_fail_closed(self) -> None:
        invalid_definitions = (
            _definition(clinical_claim_token="d06_site_efficacy_rate"),
            _definition(d09_action="consume_only"),
            _definition(
                pattern_kind="systematic_data_or_process_gap",
                clinical_claim_token="d09_within_site_time_trend"),
        )
        for definition in invalid_definitions:
            with self.subTest(definition=definition):
                with self.assertRaises(D09ContractError):
                    validate_typed_input(_base_typed_input(
                        pattern_definition=definition))

        with self.assertRaises(D09ContractError):
            validate_typed_input(_base_typed_input(subject_risk_members=(
                replace(_risk("R-1", "SYN-SUBJ-1"),
                        site_stable_id="SYN-SITE-OTHER"),)))
        with self.assertRaises(D09ContractError):
            validate_typed_input(_base_typed_input(subject_risk_members=(
                replace(_risk("R-1", "SYN-SUBJ-1"),
                        risk_kind="d08_cross_domain_relation"),)))


# ---------------------------------------------------------------------------
# Determinism and invariance
# ---------------------------------------------------------------------------


class TestDeterminism(unittest.TestCase):
    def test_identical_input_yields_identical_result(self) -> None:
        first = _run()
        second = _run()
        self.assertEqual(_semantic_snapshot(first), _semantic_snapshot(second))
        self.assertEqual(first.units, second.units)
        self.assertEqual(first.trace_edges, second.trace_edges)

    def test_member_order_shuffle_is_invariant(self) -> None:
        members = (
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2"),
            _risk("R-3", "SYN-SUBJ-3"),
        )
        base = _run(subject_risk_members=members)
        shuffled = _run(subject_risk_members=(members[2], members[0], members[1]))
        self.assertEqual(_semantic_snapshot(base), _semantic_snapshot(shuffled))

    def test_display_label_rename_is_invariant(self) -> None:
        base = _run()
        renamed = _run(
            pattern_definition=_definition(clinical_label_zh="renamed label"),
            audience_lexicon=AudienceLexicon(
                affected_subjects_zh="renamed", center_pattern_count_zh="renamed",
                coverage_zh="renamed", event_count_zh="renamed",
                individual_risk_count_zh="renamed", pattern_label_zh="renamed",
                disposition_zh={}, lifecycle_zh={}, forbidden_internal_terms=()),
        )
        self.assertEqual(_semantic_snapshot(base), _semantic_snapshot(renamed))

    def test_duplicate_revision_rejected(self) -> None:
        with self.assertRaises(D09ContractError):
            _run(source_revision_set=("SYN-REV-1", "SYN-REV-1"),
                 source_content_hashes=(_sha("d09-rev:SYN-REV-1"),
                                        _sha("d09-rev:SYN-REV-1")))


# ---------------------------------------------------------------------------
# Audit-metadata and sentinel-spelling isolation
# ---------------------------------------------------------------------------


class TestAuditMetadataIsolation(unittest.TestCase):
    """The runtime result never depends on audit/test metadata or on
    synthetic sentinel spellings; only explicit typed facts decide."""

    def test_mutation_class_never_changes_result(self) -> None:
        base = _run(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                          _risk("R-2", "SYN-SUBJ-2")))
        for mutation_class in ("none", "authority_fail", "validity_insufficient",
                               "carry_forward", "rule_supersession",
                               "signal_unexpandable", "statistics_only",
                               "query_no_process_delta", "arbitrary_label"):
            varied = _run(
                subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                      _risk("R-2", "SYN-SUBJ-2")),
                mutation_context=MutationContext(
                    mutation_class=mutation_class,
                    desc="any prose",
                    variant_id="variant-1",
                    base_fixture_id="base-1"),
            )
            self.assertEqual(_semantic_snapshot(base), _semantic_snapshot(varied),
                             mutation_class)

    def test_locator_spelling_never_changes_result(self) -> None:
        # The locator string is an opaque ref; only the explicit resolution
        # state is semantic.
        sentinel_string = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", locator="SYN-D09-LOC-MISSING"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-D09-LOC-MISSING")))
        self.assertEqual(sentinel_string.disposition, "positive")
        self.assertEqual(sentinel_string.primary_reason,
                         "min_member_subject_count_satisfied")
        unresolved = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", locator="SYN-LOC-1", loc_state="missing"),
            _risk("R-2", "SYN-SUBJ-2", locator="SYN-LOC-2")))
        self.assertEqual(unresolved.disposition, "boundary")
        self.assertEqual(unresolved.primary_reason, "deep_link_deficient")
        self.assertEqual(unresolved.all_members_locatable, False)

    def test_anchor_spelling_never_changes_result(self) -> None:
        from mm_r4.d09_contracts import GapMember
        base_gaps = tuple(GapMember(
            member_id=f"SYN-GAP-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1", producer_domain="D05",
            gap_kind="missing_required_field",
            gap_opportunity_id=f"SYN-GAPOPP-{n}",
            gap_definition_id="SYN-GAPDEF-1",
            normalized_field_or_process_identity="SYN-FIELD-1",
            obligation_or_opportunity_ref=f"SYN-OBL-{n}",
            visit_or_time_anchor_refs=("UNKNOWN",),
            source_locator_refs=(f"SYN-LOC-{n}",))
            for n in range(1, 3))
        args = dict(
            pattern_definition=_definition(
                pattern_kind="systematic_data_or_process_gap",
                clinical_claim_token="d09_systematic_data_or_process_gap",
                required_producer_domains=("D05",),
                accepted_member_risk_kinds=(),
                allowed_denominator_kinds=("evaluable_subjects",)),
            coverage=(CoverageStatus(producer_domain="D05", l0_status="covered",
                                     l1_medical_completeness_state="complete"),),
            subject_risk_members=(),
            gap_members=base_gaps,
            opportunity=Opportunity(opportunity_definition_ref="SYN-OPPDEF-1",
                                    expected_opportunity_count=42,
                                    observed_opportunity_count=40,
                                    opportunity_state="sufficient"))
        # "UNKNOWN" is an ordinary anchor string; the resolution state is
        # the semantic fact.
        self.assertEqual(_run(**args).disposition, "positive")
        unresolved_gaps = tuple(GapMember(
            member_id=f"SYN-GAP-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1", producer_domain="D05",
            gap_kind="missing_required_field",
            gap_opportunity_id=f"SYN-GAPOPP-{n}",
            gap_definition_id="SYN-GAPDEF-1",
            normalized_field_or_process_identity="SYN-FIELD-1",
            obligation_or_opportunity_ref=f"SYN-OBL-{n}",
            visit_or_time_anchor_refs=("2026-02-01",),
            source_locator_refs=(f"SYN-LOC-{n}",),
            anchor_resolution_state="unresolved")
            for n in range(1, 3))
        result = _run(**{**args, "gap_members": unresolved_gaps})
        self.assertEqual(result.disposition, "boundary")
        self.assertEqual(result.primary_reason, "deep_link_deficient")

    def test_content_hash_recipe_never_used(self) -> None:
        # Any 64-hex declared hash passes schema validation; only the
        # explicit verification records decide integrity.
        tampered = _sha("d09-rev:SYN-REV-1-TAMPERED")
        ok = _run(
            source_revision_set=("SYN-REV-1",),
            source_content_hashes=(tampered,),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(ok.disposition, "positive")
        mismatch = _run(
            source_revision_set=("SYN-REV-1",),
            source_content_hashes=(tampered,),
            source_verification_records=(SourceVerificationRecord(
                revision="SYN-REV-1", declared_content_hash=tampered,
                verified_content_hash=_sha("d09-rev:SYN-REV-1"),
                verification_state="mismatch"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(mismatch.disposition, "not_evaluable")
        self.assertEqual(mismatch.primary_reason, "source_hash_mismatch")


# ---------------------------------------------------------------------------
# Resolved domain facts drive the formerly metadata-carried decisions
# ---------------------------------------------------------------------------


class TestResolvedAuthorityDecision(unittest.TestCase):
    def test_invalid_authority_fail_closed(self) -> None:
        result = _run(
            resolved_authority_decision=_authority(validity="invalid"),
            denominator=Denominator(denominator_kind="evaluable_subjects",
                                    denominator_value=0,
                                    denominator_state="unclosed"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "authority_fail")
        self.assertEqual(result.risk_count, 0)

    def test_resolved_minimum_threshold(self) -> None:
        # Resolved minimum of 3 with 2 in-cutoff subjects -> sub-threshold
        # boundary (contract section 9), not positive.
        result = _run(
            resolved_authority_decision=_authority(repeated_minimum=3),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "n1_minimum")

    def test_missing_or_below_floor_repeated_threshold_rejected(self) -> None:
        for value in (None, 0, 1):
            with self.subTest(value=value), self.assertRaises(D09ContractError):
                _run(resolved_authority_decision=_authority(
                    repeated_minimum=value))

    def test_authority_content_hash_tamper_rejected(self) -> None:
        with self.assertRaises(D09ContractError):
            _run(resolved_authority_decision=replace(
                _authority(), authority_content_hash=_sha("tampered")))


class TestSourceVerification(unittest.TestCase):
    def test_mismatch_blocks_medical_output(self) -> None:
        result = _run(
            source_content_hashes=(_sha("declared"),),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            source_verification_records=(SourceVerificationRecord(
                revision="SYN-REV-1",
                declared_content_hash=_sha("declared"),
                verified_content_hash=_sha("verified"),
                verification_state="mismatch"),))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "source_hash_mismatch")

    def test_source_verification_alignment_rejects_tamper(self) -> None:
        with self.assertRaises(D09ContractError):
            _run(source_verification_records=())
        with self.assertRaises(D09ContractError):
            _run(source_verification_records=(SourceVerificationRecord(
                revision="WRONG-REVISION",
                declared_content_hash=_sha("d09-rev:SYN-REV-1"),
                verified_content_hash=_sha("d09-rev:SYN-REV-1"),
                verification_state="verified"),))
        with self.assertRaises(D09ContractError):
            _run(source_verification_records=(SourceVerificationRecord(
                revision="SYN-REV-1",
                declared_content_hash=_sha("d09-rev:SYN-REV-1"),
                verified_content_hash=_sha("different"),
                verification_state="verified"),))


class TestMethodComparabilityDecision(unittest.TestCase):
    def test_method_insufficient_repeated(self) -> None:
        result = _run(
            method_comparability_decision=MethodComparabilityDecision(
                method_validity_state="insufficient"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "validity_insufficient")

    def test_signal_sole_evidence_boundary(self) -> None:
        result = _run(
            method_comparability_decision=MethodComparabilityDecision(
                statistical_signal_role="sole_evidence"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "statistics_only")

    def test_signal_unexpandable_boundary(self) -> None:
        result = _run(
            method_comparability_decision=MethodComparabilityDecision(
                statistical_signal_role="supporting",
                member_expansion_state="unexpandable"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "signal_unexpandable")


class TestLineageContext(unittest.TestCase):
    def test_rule_supersession_boundary_and_superseded_count(self) -> None:
        result = _run(
            lineage_context=LineageContext(
                lineage_relation="superseded_by_rule_or_method_change"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "rule_supersession")
        self.assertEqual(result.superseded_unit_count, 1)

    def test_carry_forward_handoff_without_positive(self) -> None:
        result = _run(
            lineage_context=LineageContext(
                prior_risk_instance_ref="SYN-PRIOR-RISK-1",
                prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
                carry_forward_state="active",
                lineage_relation="continued_from_data_revision"),
            denominator=Denominator(denominator_kind="evaluable_subjects",
                                    denominator_value=0,
                                    denominator_state="unclosed"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.downstream_handoff, True)
        self.assertEqual(result.handoff_target_domain, "R2")
        self.assertEqual(result.units[0].lineage_handoff, True)

    def test_site_merge_split_not_evaluable(self) -> None:
        result = _run(
            lineage_context=LineageContext(site_identity_state="split"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "site_merge_split")


class TestQueryRedundancyDecision(unittest.TestCase):
    def _positive(self, decision: str, *, fanout: int = 100,
                  with_member_queries: bool = False) -> Any:
        members = (
            _risk("R-1", "SYN-SUBJ-1",
                  query_refs=("SYN-Q-1",) if with_member_queries else ()),
            _risk("R-2", "SYN-SUBJ-2",
                  query_refs=("SYN-Q-2",) if with_member_queries else ()),
        )
        return _run(
            subject_risk_members=members,
            query_redundancy_decision=_query_decision(
                members, decision=decision, fanout=fanout))

    def test_delta_present_generates_query(self) -> None:
        result = self._positive("site_process_delta_present")
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.query_count, 1)

    def test_fully_covered_suppresses_query(self) -> None:
        result = self._positive(
            "fully_covered_by_member_queries", with_member_queries=True)
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.query_count, 0)

    def test_members_unlistable_suppresses_query(self) -> None:
        result = self._positive("members_unlistable")
        self.assertEqual(result.query_count, 0)

    def test_not_applicable_suppresses_query(self) -> None:
        result = self._positive("not_applicable")
        self.assertEqual(result.query_count, 0)

    def test_fanout_exceeded_suppresses_query(self) -> None:
        members = tuple(
            _risk(f"R-{n}", f"SYN-SUBJ-{n}") for n in range(1, 13))
        result = _run(
            subject_risk_members=members,
            query_redundancy_decision=_query_decision(
                members, fanout=10))
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.query_count, 0)

    def test_policy_and_member_proof_tamper_rejected(self) -> None:
        typed = _base_typed_input()
        with self.assertRaises(D09ContractError):
            validate_typed_input(replace(
                typed,
                query_redundancy_decision=replace(
                    typed.query_redundancy_decision,
                    unit_member_set_hash=_sha("tampered")),
            ))
        with self.assertRaises(D09ContractError):
            validate_typed_input(replace(
                typed,
                query_redundancy_decision=replace(
                    typed.query_redundancy_decision,
                    coverage_proof_hash=_sha("tampered")),
            ))
        with self.assertRaises(D09ContractError):
            validate_typed_input(replace(
                typed,
                center_query_policy=replace(
                    typed.center_query_policy,
                    max_query_member_fanout=10),
            ))

    def test_query_fanout_has_no_runtime_default(self) -> None:
        with self.assertRaises(TypeError):
            QueryRedundancyDecision(decision="site_process_delta_present")

    def test_public_evaluate_revalidates_typed_input(self) -> None:
        typed = _base_typed_input()
        tampered = replace(
            typed,
            query_redundancy_decision=replace(
                typed.query_redundancy_decision,
                coverage_proof_hash=_sha("tampered")),
        )
        with self.assertRaises(D09ContractError):
            evaluate(tampered)


# ---------------------------------------------------------------------------
# Fail-closed order (contract section 8)
# ---------------------------------------------------------------------------


class TestFailClosedOrder(unittest.TestCase):
    def test_pre_admission_gate_emits_zero_medical_units(self) -> None:
        result = _run(
            expected_set=ExpectedSet(
                expected_set_state="global_admission_failed",
                admission_gate=None))
        self.assertEqual(result.unit_count, 0)
        self.assertEqual(result.integrity_stage, "global_admission_failed")
        self.assertEqual(result.gate_count, 1)
        self.assertEqual(result.open_gate_count, 1)
        self.assertEqual(result.disposition, "not_applicable")
        self.assertEqual(result.primary_reason, "routed_or_gated")
        self.assertEqual(result.risk_count, 0)
        self.assertEqual(result.query_count, 0)
        self.assertEqual(result.clue_count, 0)
        self.assertEqual(result.downstream_handoff, False)

    def test_routed_consume_only_gate_zero_units(self) -> None:
        result = _run(
            pattern_definition=_definition(
                pattern_kind=None,
                clinical_claim_token="d06_site_efficacy_rate",
                d09_action="consume_only"),
            expected_set=ExpectedSet(
                expected_set_state="routed_consume_only",
                admission_gate=None))
        self.assertEqual(result.unit_count, 0)
        self.assertEqual(result.owner_domain, "D06")
        self.assertEqual(result.d09_action, "consume_only")
        self.assertEqual(result.risk_count, 0)

    def test_unresolved_token_routing_gate_zero_units(self) -> None:
        result = _run(
            pattern_definition=_definition(
                pattern_kind="routing_gate",
                clinical_claim_token="unresolved",
                d09_action="routing_gate"),
            expected_set=ExpectedSet(
                expected_set_state="routing_gate_unresolved",
                admission_gate=None))
        self.assertEqual(result.unit_count, 0)
        self.assertEqual(result.owner_domain, "unresolved")
        self.assertEqual(result.disposition, "not_applicable")

    def test_coverage_hole_after_admission_one_not_evaluable_unit(self) -> None:
        result = _run(
            coverage=(CoverageStatus(producer_domain="D01", l0_status="missing",
                                     l1_medical_completeness_state="missing"),))
        self.assertEqual(result.unit_count, 1)
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "coverage_hole")
        self.assertEqual(result.risk_count, 0)
        self.assertEqual(result.query_count, 0)

    def test_l1_hole_is_not_negative(self) -> None:
        result = _run(
            subject_risk_members=(),
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="not_evaluable"),))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "coverage_hole")
        self.assertEqual(result.negative_count, 0)

    def test_denominator_unclosed_not_evaluable(self) -> None:
        result = _run(
            denominator=Denominator(denominator_kind="evaluable_subjects",
                                    denominator_value=0,
                                    denominator_state="unclosed"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "denominator_unclosed")

    def test_denominator_closed_zero_not_evaluable(self) -> None:
        result = _run(
            denominator=Denominator(denominator_kind="evaluable_subjects",
                                    denominator_value=0,
                                    denominator_state="closed_zero"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "denominator_closed_zero")

    def test_opportunity_unknown_not_evaluable(self) -> None:
        result = _run(opportunity=Opportunity(
            opportunity_definition_ref="SYN-OPPDEF-1",
            expected_opportunity_count=42, observed_opportunity_count=0,
            opportunity_state="unknown"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "opportunity_unknown")

    def test_origin_wrong_scope_not_evaluable(self) -> None:
        result = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", origin="wrong_scope"),
            _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "origin_wrong_scope")
        self.assertEqual(result.risk_count, 0)

    def test_origin_ambiguous_boundary(self) -> None:
        result = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", origin="ambiguous"),
            _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "origin_ambiguous")
        self.assertEqual(result.clue_count, 1)
        self.assertEqual(result.risk_count, 0)

    def test_cutoff_conflict_fail_closed(self) -> None:
        result = _run(cutoff=Cutoff(
            cutoff_id="SYN-CUT-1", cutoff_contract_id="SYN-CUTC-1",
            snapshot_as_of="2026-07-01T00:00:00+00:00",
            clinical_event_cutoff="2026-06-30", cutoff_identity_state="conflict",
            cutoff_policy_ref="SYN-RULE-CUT-1"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "cutoff_conflict")

    def test_opportunity_provenance_raw_only_not_evaluable(self) -> None:
        result = _run(opportunity=Opportunity(
            opportunity_definition_ref="SYN-OPPDEF-1",
            expected_opportunity_count=42, observed_opportunity_count=0,
            opportunity_state="sufficient",
            opportunity_provenance="raw_listing_only"))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason, "opportunity_provenance")

    def test_blinded_treatment_stratum_rejected(self) -> None:
        result = _run(
            stratum=Stratum(
                stratum_contract_id="SYN-SC-1",
                stratum_contract_content_hash=_sha(
                    "d09-content-v1:stratum-contract:SYN-SC-1"),
                stratum_key="treatment_arm",
                stratum_state="closed",
                stratum_admission="fanout_rejected"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(result.units[0].primary_reason,
                         "blinded_stratum_rejected")
        self.assertEqual(result.risk_count, 0)

    def test_unblinded_treatment_stratum_allowed(self) -> None:
        result = _run(
            stratum=Stratum(
                stratum_contract_id="SYN-SC-1",
                stratum_contract_content_hash=_sha(
                    "d09-content-v1:stratum-contract:SYN-SC-1"),
                stratum_key="treatment_arm",
                stratum_state="closed",
                stratum_admission="admitted"),
            visibility_decision=VisibilityDecision(
                audience_scope_id="SYN-AUD-1",
                blind_status="unblinded_authorized"),
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.risk_count, 1)


# ---------------------------------------------------------------------------
# Five dispositions (contract section 9)
# ---------------------------------------------------------------------------


class TestDispositions(unittest.TestCase):
    def test_n1_repeated_risk_boundary(self) -> None:
        result = _run(subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "n1_minimum")
        self.assertEqual(result.boundary_count, 1)
        self.assertEqual(result.clue_count, 1)
        self.assertEqual(result.risk_count, 0)
        self.assertEqual(result.query_count, 0)
        self.assertEqual(result.affected_subject_count, 1)

    def test_two_member_repeated_risk_positive(self) -> None:
        result = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"),
            _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.units[0].primary_reason,
                         "min_member_subject_count_satisfied")
        self.assertEqual(result.risk_count, 1)
        self.assertEqual(result.query_count, 1)
        self.assertEqual(result.center_pattern_count, 1)
        self.assertEqual(result.downstream_handoff, True)
        self.assertEqual(result.handoff_target_domain, "R2")
        self.assertEqual(result.owner_domain, "D09")

    def test_closed_zero_negative(self) -> None:
        result = _run(subject_risk_members=())
        self.assertEqual(result.units[0].l1_disposition, "negative")
        self.assertEqual(result.units[0].primary_reason, "closed_zero_no_members")
        self.assertEqual(result.negative_count, 1)
        self.assertEqual(result.risk_count, 0)
        self.assertEqual(result.query_count, 0)
        self.assertEqual(result.clue_count, 0)

    def test_short_exposure_boundary(self) -> None:
        result = _run(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            denominator=Denominator(denominator_kind="subject_time",
                                    denominator_value=30,
                                    denominator_state="closed_positive"))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "short_exposure")
        self.assertEqual(result.risk_count, 0)

    def test_late_activation_boundary(self) -> None:
        result = _run(
            subject_risk_members=(_risk("R-1", "SYN-SUBJ-1"),
                                  _risk("R-2", "SYN-SUBJ-2")),
            analysis_windows=(_window(anchor="site_activation"),))
        self.assertEqual(result.units[0].l1_disposition, "boundary")
        self.assertEqual(result.units[0].primary_reason, "late_activation")

    def test_design_clause_not_applicable_unit(self) -> None:
        result = _run(
            mode_contract_design_clause_ref="SYN-DC-1",
            subject_risk_members=(),
            denominator=Denominator(denominator_kind="evaluable_subjects",
                                    denominator_value=0,
                                    denominator_state="closed_zero"))
        self.assertEqual(result.unit_count, 1)
        self.assertEqual(result.units[0].l1_disposition, "not_applicable")
        self.assertEqual(result.units[0].primary_reason, "design_not_applicable")
        self.assertEqual(result.not_applicable_count, 1)
        self.assertEqual(result.risk_count, 0)

    def test_same_origin_dedup(self) -> None:
        members = (
            SubjectRiskMember(
                member_id="SYN-RISK-1", subject_stable_id="SYN-SUBJ-1",
                site_stable_id="SYN-SITE-1", producer_domain="D01",
                risk_kind="d01_seriousness_hospital_death",
                monitoring_priority="medium",
                public_r4_risk_identity="SYN-RID-PAIR",
                source_event_identity="SYN-EVT-1", event_time_ref="2026-02-01",
                cutoff_relation="in_cutoff", origin_decision="verified_same_origin",
                source_locator_refs=("SYN-LOC-1",)),
            SubjectRiskMember(
                member_id="SYN-RISK-2", subject_stable_id="SYN-SUBJ-1",
                site_stable_id="SYN-SITE-1", producer_domain="D08",
                risk_kind="d08_cross_domain_relation",
                monitoring_priority="medium",
                public_r4_risk_identity="SYN-RID-PAIR",
                source_event_identity="SYN-EVT-1", event_time_ref="2026-02-01",
                cutoff_relation="in_cutoff", origin_decision="verified_same_origin",
                source_locator_refs=("SYN-LOC-2",)),
            SubjectRiskMember(
                member_id="SYN-RISK-3", subject_stable_id="SYN-SUBJ-2",
                site_stable_id="SYN-SITE-1", producer_domain="D01",
                risk_kind="d01_seriousness_hospital_death",
                monitoring_priority="medium",
                public_r4_risk_identity="SYN-RID-PAIR",
                source_event_identity="SYN-EVT-2", event_time_ref="2026-02-01",
                cutoff_relation="in_cutoff", origin_decision="verified_same_origin",
                source_locator_refs=("SYN-LOC-3",)),
            SubjectRiskMember(
                member_id="SYN-RISK-4", subject_stable_id="SYN-SUBJ-2",
                site_stable_id="SYN-SITE-1", producer_domain="D08",
                risk_kind="d08_cross_domain_relation",
                monitoring_priority="medium",
                public_r4_risk_identity="SYN-RID-PAIR",
                source_event_identity="SYN-EVT-2", event_time_ref="2026-02-01",
                cutoff_relation="in_cutoff", origin_decision="verified_same_origin",
                source_locator_refs=("SYN-LOC-4",)),
        )
        result = _run(
            pattern_definition=_definition(accepted_member_risk_kinds=(
                "d01_seriousness_hospital_death", "d08_cross_domain_relation")),
            subject_risk_members=members)
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.individual_risk_count, 2)
        self.assertEqual(result.affected_subject_count, 2)
        self.assertEqual(result.event_count, 2)
        self.assertEqual(result.source_record_count, 4)

    def test_gap_only_positive_without_risk_instance(self) -> None:
        from mm_r4.d09_contracts import GapMember
        gaps = tuple(GapMember(
            member_id=f"SYN-GAP-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1", producer_domain="D05",
            gap_kind="missing_required_field",
            gap_opportunity_id=f"SYN-GAPOPP-{n}",
            gap_definition_id="SYN-GAPDEF-1",
            normalized_field_or_process_identity="SYN-FIELD-1",
            obligation_or_opportunity_ref=f"SYN-OBL-{n}",
            visit_or_time_anchor_refs=("2026-02-01",),
            source_locator_refs=(f"SYN-LOC-{n}",))
            for n in range(1, 10))
        result = _run(
            pattern_definition=_definition(
                pattern_kind="systematic_data_or_process_gap",
                clinical_claim_token="d09_systematic_data_or_process_gap",
                required_producer_domains=("D05",),
                accepted_member_risk_kinds=(),
                allowed_denominator_kinds=("evaluable_subjects",)),
            coverage=(CoverageStatus(producer_domain="D05", l0_status="covered",
                                     l1_medical_completeness_state="complete"),),
            subject_risk_members=(),
            gap_members=gaps,
            opportunity=Opportunity(opportunity_definition_ref="SYN-OPPDEF-1",
                                    expected_opportunity_count=42,
                                    observed_opportunity_count=33,
                                    opportunity_state="sufficient"))
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.units[0].primary_reason,
                         "accepted_gap_opportunity_sufficient")
        self.assertEqual(result.individual_risk_count, 0)
        self.assertEqual(result.gap_opportunity_count, 9)
        self.assertEqual(result.affected_subject_count, 9)
        self.assertEqual(result.risk_count, 1)
        self.assertEqual(result.center_pattern_count, 1)


class TestWindowPairGates(unittest.TestCase):
    def test_single_trend_window_insufficient_gate(self) -> None:
        result = _run(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window(),),
            subject_risk_members=(),
            change_ledger_members=(),
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))
        self.assertEqual(result.unit_count, 0)
        self.assertEqual(result.disposition, "not_applicable")
        self.assertEqual(result.primary_reason, "window_pair_gate")
        self.assertEqual(result.window_pair_gate_present, True)
        self.assertEqual(result.window_pair_state, "insufficient_windows")
        self.assertEqual(result.gate_count, 1)
        self.assertEqual(result.risk_count, 0)

    def test_incomparable_window_kinds_gate(self) -> None:
        result = _run(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window("exposure_time_interval"),
                              _window("calendar_interval", stable_id="SYN-WIN-2")),
            subject_risk_members=(),
            change_ledger_members=(),
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))
        self.assertEqual(result.unit_count, 0)
        self.assertEqual(result.window_pair_gate_present, True)
        self.assertEqual(result.window_pair_state, "incomparable_windows")

    def test_incomparable_trend_boundary_and_resolved_reasons(self) -> None:
        from mm_r4.d09_contracts import ChangeLedgerMember

        def changes(cause: str = "data") -> Tuple[Any, ...]:
            return tuple(ChangeLedgerMember(
                member_id=f"SYN-CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
                site_stable_id="SYN-SITE-1",
                change_ledger_member_id=f"SYN-CHGID-{n}",
                current_window_instance_ref="SYN-WIN-2-INST",
                prior_window_instance_ref="SYN-WIN-1-INST",
                comparable_state="not_evaluable", change_kind="not_comparable",
                change_cause=cause, unit="rate_per_subject",
                supporting_member_refs=(f"SYN-RISK-{n}",),
                source_locator_refs=(f"SYN-LOC-{n}",))
                for n in range(1, 4))

        trend_args = dict(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window(stable_id="SYN-WIN-1"),
                              _window(stable_id="SYN-WIN-2")),
            subject_risk_members=(),
            change_ledger_members=changes(),
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))

        plain = _run(**trend_args)
        self.assertEqual(plain.units[0].l1_disposition, "boundary")
        self.assertEqual(plain.units[0].primary_reason, "not_comparable")

        method = _run(**{**trend_args, "method_comparability_decision":
                         MethodComparabilityDecision(method_validity_state="insufficient")})
        self.assertEqual(method.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(method.units[0].primary_reason, "validity_insufficient")

        carry = _run(**{**trend_args, "lineage_context": LineageContext(
            prior_risk_instance_ref="SYN-PRIOR-1",
            prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
            carry_forward_state="active",
            lineage_relation="continued_from_data_revision")})
        self.assertEqual(carry.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(carry.units[0].primary_reason, "carry_forward")

        window_change = _run(**{**trend_args, "method_comparability_decision":
                                MethodComparabilityDecision(
                                    window_rule_version_refs=("SYN-WRULE-1", "SYN-WRULE-2"))})
        self.assertEqual(window_change.units[0].l1_disposition, "boundary")
        self.assertEqual(window_change.units[0].primary_reason,
                         "window_definition_change")

        superseded = _run(**{**trend_args, "lineage_context": LineageContext(
            lineage_relation="superseded_by_rule_or_method_change")})
        self.assertEqual(superseded.units[0].l1_disposition, "boundary")
        self.assertEqual(superseded.units[0].primary_reason, "rule_supersession")

        stratum_change = _run(**{**trend_args, "method_comparability_decision":
                                 MethodComparabilityDecision(
                                     stratum_method_version_refs=(
                                         "SYN-SMVER-1", "SYN-SMVER-2"))})
        self.assertEqual(stratum_change.units[0].l1_disposition, "not_evaluable")
        self.assertEqual(stratum_change.units[0].primary_reason, "stratum_change")

    def test_comparable_trend_positive(self) -> None:
        from mm_r4.d09_contracts import ChangeLedgerMember
        changes = tuple(ChangeLedgerMember(
            member_id=f"SYN-CHG-{n}", subject_stable_id=f"SYN-SUBJ-{n}",
            site_stable_id="SYN-SITE-1",
            change_ledger_member_id=f"SYN-CHGID-{n}",
            current_window_instance_ref="SYN-WIN-2-INST",
            prior_window_instance_ref="SYN-WIN-1-INST",
            comparable_state="comparable", change_kind="increased",
            change_cause="data", unit="rate_per_subject",
            supporting_member_refs=(f"SYN-RISK-{n}",),
            source_locator_refs=(f"SYN-LOC-{n}",))
            for n in range(1, 4))
        result = _run(
            pattern_definition=_definition(
                pattern_kind="within_site_time_trend",
                clinical_claim_token="d09_within_site_time_trend"),
            analysis_windows=(_window(stable_id="SYN-WIN-1"),
                              _window(stable_id="SYN-WIN-2")),
            subject_risk_members=(),
            change_ledger_members=changes,
            coverage=(CoverageStatus(producer_domain="D01", l0_status="covered",
                                     l1_medical_completeness_state="complete"),))
        self.assertEqual(result.units[0].l1_disposition, "positive")
        self.assertEqual(result.units[0].primary_reason,
                         "comparable_windows_change_ledger")
        self.assertEqual(result.affected_subject_count, 3)
        self.assertEqual(result.risk_count, 1)
        self.assertEqual(result.units[0].stable_core,
                         "SYN-PROJECT-1|SYN-SITE-1|SYN-DEF-1|SYN-WIN-2|SYN-SC-1|overall")


class TestCountsAndOwnership(unittest.TestCase):
    def test_separated_count_surface(self) -> None:
        result = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1", locator="SYN-LOC-1"),
            _risk("R-2", "SYN-SUBJ-2", event="SYN-EVT-SAME", locator="SYN-LOC-2"),
            _risk("R-3", "SYN-SUBJ-2", event="SYN-EVT-SAME", locator="SYN-LOC-3")))
        self.assertEqual(result.individual_risk_count, 3)
        self.assertEqual(result.affected_subject_count, 2)
        self.assertEqual(result.event_count, 2)
        self.assertEqual(result.source_record_count, 3)

    def test_measure_ledger_fields(self) -> None:
        result = _run(subject_risk_members=(
            _risk("R-1", "SYN-SUBJ-1"), _risk("R-2", "SYN-SUBJ-2")))
        self.assertEqual(result.denominator_kind, "evaluable_subjects")
        self.assertEqual(result.denominator_value, 42)
        self.assertEqual(result.denominator_state, "closed_positive")
        self.assertEqual(result.opportunity_expected, 42)
        self.assertEqual(result.opportunity_observed, 0)
        self.assertEqual(result.opportunity_missing, 42)
        self.assertEqual(result.opportunity_state, "sufficient")


# ---------------------------------------------------------------------------
# Runtime closure: static proof of independence from acceptance artifacts
# ---------------------------------------------------------------------------

_RUNTIME_MODULES = (
    Path(__file__).resolve().parents[1] / "src" / "mm_r4" / "d09_contracts.py",
    Path(__file__).resolve().parents[1] / "src" / "mm_r4" / "d09_evaluator.py",
)
_FORBIDDEN_ID_RE = re.compile(r"D09-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+")
# Tokens forbidden in BOTH runtime modules: artifact reads, service/runtime
# tokens, oracle leaf vocabulary, and all synthetic test conventions.
_FORBIDDEN_TOKENS = (
    # frozen artifact file names / generator names / test module names
    "typed_fixture_catalog", "expected_outcome_oracle", "challenge_manifest_registry",
    "partition_quota_manifest", "generate_d09", "test_d09", "artifact_generator",
    # service/runtime tokens
    "socket", "bind(", "listen(", "serve_forever", "8911", "uvicorn", "flask",
    "run_monitoring", "open(", "read_text", "read_bytes", "json.load", "urllib",
    "requests", "subprocess",
    # oracle leaf vocabulary (decision coupling)
    "expected_leaf", "units.0", "trace.stable_core_count", "source.jump_target",
    "ordered_expectations",
    # synthetic sentinel / hash-convention tokens
    "MISSING", "UNKNOWN", "d09-rev", "TAMPERED", "LOC-MISSING",
    # frozen mutation-class vocabulary that is NOT also legit contract
    # enum/reason vocabulary (shared tokens such as n1_minimum, cutoff_*,
    # time_missing, consume_only, origin_* are legit typed facts)
    "revision_repeat", "export_repeat", "order_shuffle", "display_rename",
    "same_origin_verified", "coverage_missing", "coverage_partial",
    "coverage_truncated", "coverage_failed", "anti_overfit_rename",
    "anti_overfit_shuffle",
)
# Tokens forbidden in the SEMANTIC module (d09_evaluator.py) that may
# legitimately exist as schema in d09_contracts.py.
_SEMANTIC_ONLY_TOKENS = (
    "mutation", "anti_overfit", "base_fixture", "variant_id",
)
# Natural-language / display-label tokens forbidden in the semantic module.
_FORBIDDEN_PROSE_TOKENS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
    "中心重复风险模式", "受影响受试者", "事件 {n}", "请核实",
)


class TestRuntimeClosure(unittest.TestCase):
    def test_runtime_never_reads_acceptance_artifacts(self) -> None:
        for path in _RUNTIME_MODULES:
            source = path.read_text(encoding="utf-8")
            for token in _FORBIDDEN_TOKENS:
                self.assertNotIn(token, source,
                                 f"{path.name} contains forbidden token {token!r}")
            self.assertIsNone(_FORBIDDEN_ID_RE.search(source),
                              f"{path.name} contains a case/fixture identifier")

    def test_semantic_module_never_accesses_audit_metadata(self) -> None:
        evaluator_source = _RUNTIME_MODULES[1].read_text(encoding="utf-8")
        for token in _SEMANTIC_ONLY_TOKENS:
            self.assertNotIn(token, evaluator_source,
                             f"d09_evaluator.py contains audit token {token!r}")
        for token in _FORBIDDEN_PROSE_TOKENS:
            self.assertNotIn(token, evaluator_source,
                             f"d09_evaluator.py contains prose token {token!r}")

    def test_runtime_modules_import_without_artifacts(self) -> None:
        import importlib
        for module_name in ("mm_r4.d09_contracts", "mm_r4.d09_evaluator"):
            module = importlib.import_module(module_name)
            self.assertIsNotNone(module)


class TestPort8911Stopped(unittest.TestCase):
    def test_tcp_8911_connection_refused(self) -> None:
        refused = False
        try:
            with socket.create_connection(("127.0.0.1", 8911), timeout=1):
                pass
        except OSError:
            refused = True
        self.assertTrue(refused, "port 8911 must stay stopped (connection refused)")


if __name__ == "__main__":
    unittest.main()
