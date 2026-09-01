"""R3-B semantic mapping tests.

Proves mapping candidates carry explainable scores + evidence, low-confidence
is never silently accepted, identifiers always need confirmation, field
dependencies are recorded, and decisions are the four explicit kinds.
"""

from __future__ import annotations

import pytest

from mm_r3.listing import FieldProfile, FieldRole, TableProfile, TableShapeKind, profile_table
from mm_r3.mapping import (
    MAPPING_DECISIONS,
    FieldMapping,
    MappingBasis,
    MappingCandidate,
    MappingDecision,
    MappingError,
    MappingResult,
    SystemPolicy,
    TargetConcept,
    auto_accept_under_policy,
    map_field,
    map_table,
    score_candidate,
)


# ===========================================================================
# Canonical target concepts (synthetic, SDTM-like, no project tokens)
# ===========================================================================

AE_TARGETS = [
    TargetConcept(
        "sdtm.ae.usubjid", "Subject identifier", "AE", "USUBJID",
        expected_roles=("identifier",),
        name_synonyms=("subject", "subj", "pt", "patient"),
        requires_confirmation=True,
    ),
    TargetConcept(
        "sdtm.ae.aeterm", "Reported term", "AE", "AETERM",
        expected_roles=("free_text",),
        name_synonyms=("ae_term", "aeterm", "term"),
    ),
    TargetConcept(
        "sdtm.ae.aestdtc", "Start date", "AE", "AESTDTC",
        expected_roles=("date",),
        name_synonyms=("ae_start", "aestdtc", "start"),
        expected_kind_hint="date",
    ),
    TargetConcept(
        "sdtm.ae.aesev", "Severity", "AE", "AESEV",
        expected_roles=("classifier",),
        name_synonyms=("severity", "aesev", "sev"),
    ),
]


# ===========================================================================
# Scoring
# ===========================================================================

class TestScoring:
    def test_name_exact_match_high_score(self):
        f = FieldProfile(name="AETERM", role=FieldRole.FREE_TEXT)
        t = TargetConcept("c", "lbl", "AE", "AETERM", name_synonyms=("ae_term",))
        score, evidence = score_candidate(f, t)
        assert score > 0.4
        assert MappingBasis.NAME_MATCH in evidence

    def test_role_match_contributes(self):
        f = FieldProfile(name="X", role=FieldRole.DATE)
        t = TargetConcept("c", "lbl", "AE", "AESTDTC",
                          expected_roles=("date",), expected_kind_hint="date")
        score, evidence = score_candidate(f, t)
        assert MappingBasis.ROLE_MATCH in evidence

    def test_no_match_zero_score(self):
        f = FieldProfile(name="XYZ", role=FieldRole.UNKNOWN)
        t = TargetConcept("c", "lbl", "AE", "AETERM", name_synonyms=("ae_term",))
        score, evidence = score_candidate(f, t)
        assert score == 0.0
        assert evidence == ()

    def test_score_in_unit_interval(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        for t in AE_TARGETS:
            score, _ = score_candidate(f, t)
            assert 0.0 <= score <= 1.0

    def test_domain_scope_boost(self):
        f = FieldProfile(name="WEIRD", role=FieldRole.UNKNOWN)
        t = TargetConcept("c", "lbl", "AE", "WEIRD", name_synonyms=("weird",))
        s_no_domain, _ = score_candidate(f, t)
        s_with_domain, _ = score_candidate(f, t, table_domain_hint="AE")
        assert s_with_domain >= s_no_domain


# ===========================================================================
# map_field: decisions
# ===========================================================================

class TestMapFieldDecisions:
    def test_strong_non_identifier_auto_accepted_under_policy(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE,
                         normalization_kind_hint="date")
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.5)
        fm = map_field(f, AE_TARGETS, policy=policy)
        assert fm.decision == MappingDecision.ACCEPTED
        assert fm.chosen is not None
        assert fm.chosen.target_variable == "AESTDTC"
        assert fm.resolved_by == "system_policy:default-mapping-policy@1"
        assert fm.chosen.decision == MappingDecision.ACCEPTED

    def test_identifier_never_auto_accepted(self):
        f = FieldProfile(name="SUBJECT", role=FieldRole.IDENTIFIER)
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.0)
        fm = map_field(f, AE_TARGETS, policy=policy)
        # even with threshold 0, identifier requires confirmation
        assert fm.decision == MappingDecision.NEEDS_CONFIRMATION
        assert "requires user confirmation" in fm.uncertainty

    def test_explicit_target_confirmation_flag_is_respected(self):
        f = FieldProfile(name="SPECIAL_FIELD", role=FieldRole.FREE_TEXT)
        target = TargetConcept(
            "custom.special", "Special", "AE", "SPECIAL",
            expected_roles=("free_text",),
            name_synonyms=("special_field",),
            requires_confirmation=True,
        )
        fm = map_field(
            f, [target],
            policy=SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.0),
        )
        assert fm.decision == MappingDecision.NEEDS_CONFIRMATION

    def test_no_policy_means_needs_confirmation(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        fm = map_field(f, AE_TARGETS, policy=None)
        assert fm.decision == MappingDecision.NEEDS_CONFIRMATION
        assert "no auto-accept policy" in fm.uncertainty

    def test_below_threshold_needs_confirmation(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.99)
        fm = map_field(f, AE_TARGETS, policy=policy)
        assert fm.decision == MappingDecision.NEEDS_CONFIRMATION
        assert "below auto-accept" in fm.uncertainty

    def test_no_candidates_not_evaluable(self):
        f = FieldProfile(name="WEIRD_UNKNOWN_FIELD", role=FieldRole.UNKNOWN)
        fm = map_field(f, AE_TARGETS, policy=SystemPolicy())
        assert fm.decision == MappingDecision.NOT_EVALUABLE
        assert fm.candidates == ()

    def test_low_confidence_never_silently_accepted(self):
        # a weak match (stem overlap only) must not auto-accept even with a
        # permissive policy, because the score is below threshold
        f = FieldProfile(name="AE_CATEGORY", role=FieldRole.CLASSIFIER)
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.5)
        fm = map_field(f, AE_TARGETS, policy=policy)
        assert fm.decision != MappingDecision.ACCEPTED

    def test_candidates_sorted_by_score_desc(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        fm = map_field(f, AE_TARGETS, policy=None)
        scores = [c.score for c in fm.candidates]
        assert scores == sorted(scores, reverse=True)


# ===========================================================================
# map_table: full table mapping + baseline blocking
# ===========================================================================

class TestMapTable:
    def setup_method(self):
        self.table = profile_table({
            "name": "AE",
            "columns": ["SUBJECT", "AE_TERM", "AE_START", "SEVERITY"],
            "rows": [
                {"SUBJECT": "S001", "AE_TERM": "Nausea", "AE_START": "2026-02-01", "SEVERITY": "Mild"},
                {"SUBJECT": "S002", "AE_TERM": "Headache", "AE_START": "2026-02-02", "SEVERITY": "Moderate"},
            ],
        })

    def test_maps_all_fields(self):
        res = map_table(self.table, AE_TARGETS,
                        project_id="p", source_revision_id="rev")
        assert len(res.field_mappings) == 4

    def test_blocks_baseline_with_identifier(self):
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.5)
        res = map_table(self.table, AE_TARGETS,
                        project_id="p", source_revision_id="rev", policy=policy)
        # SUBJECT needs confirmation -> blocks baseline
        assert res.blocks_baseline is True
        assert res.n_needs_confirmation >= 1

    def test_tallies_derived(self):
        policy = SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.5)
        res = map_table(self.table, AE_TARGETS,
                        project_id="p", source_revision_id="rev", policy=policy)
        total = (
            res.n_accepted + res.n_rejected
            + res.n_needs_confirmation + res.n_not_evaluable
        )
        assert total == len(res.field_mappings)
        assert res.n_accepted >= 1  # AE_START at least

    def test_content_hash_deterministic(self):
        r1 = map_table(self.table, AE_TARGETS, project_id="p", source_revision_id="rev")
        r2 = map_table(self.table, AE_TARGETS, project_id="p", source_revision_id="rev")
        assert r1.content_hash == r2.content_hash

    def test_dependencies_recorded(self):
        deps = {"AE_START": ["SUBJECT"]}  # AE_START depends on SUBJECT mapping
        res = map_table(self.table, AE_TARGETS, project_id="p",
                        source_revision_id="rev", dependencies=deps)
        ae_start_fm = res.field_mapping("AE_START")
        assert ae_start_fm is not None
        assert "SUBJECT" in ae_start_fm.depends_on


# ===========================================================================
# Invariants / validation
# ===========================================================================

class TestMappingInvariants:
    def test_score_out_of_range_rejected(self):
        with pytest.raises(MappingError):
            MappingCandidate(
                field_name="X", target_concept_id="c", target_domain="AE",
                target_variable="V", score=1.5,
            )

    def test_invalid_decision_rejected(self):
        with pytest.raises(MappingError):
            MappingCandidate(
                field_name="X", target_concept_id="c", target_domain="AE",
                target_variable="V", decision="bogus",
            )

    def test_accepted_requires_chosen_candidate(self):
        with pytest.raises(MappingError):
            FieldMapping(field_name="X", decision=MappingDecision.ACCEPTED)

    def test_rejected_mapping_never_counts_as_fully_accepted(self):
        rejected = FieldMapping(
            field_name="X", decision=MappingDecision.REJECTED,
            uncertainty="user rejected candidate",
        )
        result = MappingResult(
            result_id="map-1", project_id="p", source_revision_id="rev",
            table_name="T", field_mappings=(rejected,),
        )
        assert result.n_rejected == 1
        assert result.is_fully_accepted is False
        assert result.blocks_baseline is True

    def test_chosen_must_be_among_candidates(self):
        c = MappingCandidate(
            candidate_id="c1", field_name="X", target_concept_id="c",
            target_domain="AE", target_variable="V", score=0.9,
        )
        with pytest.raises(MappingError):
            FieldMapping(
                field_name="X", candidates=(c,), chosen_candidate_id="other",
                decision=MappingDecision.ACCEPTED,
            )

    def test_all_decisions_are_explicit_kinds(self):
        for d in MAPPING_DECISIONS:
            assert d in (
                MappingDecision.ACCEPTED,
                MappingDecision.REJECTED,
                MappingDecision.NEEDS_CONFIRMATION,
                MappingDecision.NOT_EVALUABLE,
            )

    def test_result_immutable(self):
        res = map_table(
            profile_table({"name": "T", "columns": ["A"], "rows": []}),
            AE_TARGETS, project_id="p", source_revision_id="rev",
        )
        with pytest.raises(Exception):
            res.project_id = "x"  # type: ignore[misc]

    def test_policy_threshold_validated(self):
        with pytest.raises(MappingError):
            SystemPolicy(auto_accept_threshold=1.5)


# ===========================================================================
# auto_accept_under_policy
# ===========================================================================

class TestAutoAcceptHelper:
    def test_no_op_when_already_accepted(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        fm = map_field(f, AE_TARGETS, policy=SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.5))
        assert fm.decision == MappingDecision.ACCEPTED
        fm2 = auto_accept_under_policy(fm, SystemPolicy())
        assert fm2 is fm

    def test_no_candidates_unchanged(self):
        f = FieldProfile(name="WEIRD", role=FieldRole.UNKNOWN)
        fm = map_field(f, AE_TARGETS, policy=None)
        assert fm.decision == MappingDecision.NOT_EVALUABLE
        fm2 = auto_accept_under_policy(fm, SystemPolicy(auto_accept_threshold=0.0))
        assert fm2 is fm

    def test_explicit_policy_promotes_eligible_candidate(self):
        f = FieldProfile(name="AE_START", role=FieldRole.DATE)
        fm = map_field(f, AE_TARGETS, policy=None)
        fm2 = auto_accept_under_policy(fm, SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.0))
        assert fm2.decision == MappingDecision.ACCEPTED
        assert fm2.chosen is not None
        assert fm2.chosen.decision == MappingDecision.ACCEPTED

    def test_explicit_policy_does_not_promote_identifier(self):
        f = FieldProfile(name="SUBJECT", role=FieldRole.IDENTIFIER)
        fm = map_field(f, AE_TARGETS, policy=None)
        fm2 = auto_accept_under_policy(
            fm, SystemPolicy(allow_auto_accept=True, auto_accept_threshold=0.0)
        )
        assert fm2.decision == MappingDecision.NEEDS_CONFIRMATION


# ===========================================================================
# Three heterogeneous shapes map without hardcoding
# ===========================================================================

class TestThreeHeterogeneousShapes:
    def test_wide_ae_maps(self):
        t = profile_table({
            "name": "AE", "columns": ["SUBJECT", "AE_TERM", "AE_START", "SEVERITY"],
            "rows": [{"SUBJECT": "S001", "AE_TERM": "N", "AE_START": "2026-01-01", "SEVERITY": "Mild"}],
        })
        res = map_table(t, AE_TARGETS, project_id="p1", source_revision_id="r1")
        assert len(res.field_mappings) == 4

    def test_long_labs_maps(self):
        lab_targets = [
            TargetConcept("sdtm.lb.lbtestcd", "Lab test code", "LB", "LBTESTCD",
                          expected_roles=("classifier",), name_synonyms=("paramcd", "lbtestcd", "test")),
            TargetConcept("sdtm.lb.lbstat", "Subject", "LB", "LBSTAT",
                          expected_roles=("identifier",), name_synonyms=("subject", "subj")),
        ]
        t = profile_table({
            "name": "LB", "columns": ["SUBJECT", "PARAM", "PARAMCD", "VAL", "UNIT"],
            "rows": [{"SUBJECT": "S001", "PARAM": "ALT", "PARAMCD": "ALT", "VAL": "45", "UNIT": "U/L"}],
        })
        res = map_table(t, lab_targets, project_id="p2", source_revision_id="r2")
        assert len(res.field_mappings) == 5

    def test_multi_table_workbook_maps(self):
        t = profile_table({
            "name": "DM", "columns": ["SUBJECT", "SEX", "AGE"],
            "rows": [{"SUBJECT": "S001", "SEX": "F", "AGE": "42"}],
        })
        dm_targets = [
            TargetConcept("sdtm.dm.usubjid", "Subject", "DM", "USUBJID",
                          expected_roles=("identifier",), name_synonyms=("subject",)),
        ]
        res = map_table(t, dm_targets, project_id="p3", source_revision_id="r3")
        assert res.table_name == "DM"
