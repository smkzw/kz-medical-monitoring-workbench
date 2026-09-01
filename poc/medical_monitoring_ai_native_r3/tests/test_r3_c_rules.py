"""R3-C natural-language rule lifecycle tests.

Proves:
* Rule draft carries NL text + structured conditions + source provenance.
* Simulation runs before activation; outcome is deterministic.
* Activation requires explicit version + evaluation scope.
* Machine activation cannot set user_confirmed; user activation must.
* Stale simulation (content hash mismatch) blocks activation.
* Three evaluation scope kinds and domain filtering.
* Condition operators evaluate correctly including missing-value semantics.
* No silent auto-promotion of draft to active.
"""

from __future__ import annotations

import pytest

from mm_r3.rules import (
    CONDITION_OPERATORS,
    ConditionOperator,
    EVALUATION_SCOPE_KINDS,
    EvaluationScope,
    EvaluationScopeKind,
    RuleActivation,
    RuleActivationError,
    RuleCondition,
    RuleDraft,
    RuleDraftStatus,
    RuleSimulation,
    SimulationMatch,
    SimulationOutcome,
    activate_rule,
    simulate_rule,
)


# ===========================================================================
# RuleCondition
# ===========================================================================

class TestRuleCondition:
    def test_eq_operator(self):
        c = RuleCondition("SEVERITY", ConditionOperator.EQ, "Severe")
        assert c.evaluate("Severe") is True
        assert c.evaluate("Mild") is False

    def test_gt_operator_numeric(self):
        c = RuleCondition("VALUE", ConditionOperator.GT, 3.5)
        assert c.evaluate(5) is True
        assert c.evaluate(2) is False
        assert c.evaluate("4") is True  # coerced

    def test_gt_on_non_numeric_returns_false(self):
        c = RuleCondition("VALUE", ConditionOperator.GT, 3)
        assert c.evaluate("abc") is False

    def test_in_operator(self):
        c = RuleCondition("DOMAIN", ConditionOperator.IN, ("AE", "MH"))
        assert c.evaluate("AE") is True
        assert c.evaluate("LB") is False

    def test_not_in_operator(self):
        c = RuleCondition("DOMAIN", ConditionOperator.NOT_IN, ("AE", "MH"))
        assert c.evaluate("LB") is True
        assert c.evaluate("AE") is False

    def test_contains_operator_string(self):
        c = RuleCondition("TERM", ConditionOperator.CONTAINS, "hepatic")
        assert c.evaluate("drug-induced hepatic injury") is True
        assert c.evaluate("cardiac") is False

    def test_is_missing_operator(self):
        c = RuleCondition("VALUE", ConditionOperator.IS_MISSING)
        assert c.evaluate(None) is True
        assert c.evaluate("") is True
        assert c.evaluate("UNK") is True
        assert c.evaluate("present") is False

    def test_is_present_operator(self):
        c = RuleCondition("VALUE", ConditionOperator.IS_PRESENT)
        assert c.evaluate(None) is False
        assert c.evaluate("x") is True

    def test_missing_value_never_satisfies_comparison(self):
        """A rule must never silently fire on absent data."""
        c = RuleCondition("VALUE", ConditionOperator.GT, 0)
        assert c.evaluate(None) is False
        assert c.evaluate("") is False

    def test_is_missing_must_not_declare_threshold(self):
        with pytest.raises(RuleActivationError, match="must not declare a threshold"):
            RuleCondition("X", ConditionOperator.IS_MISSING, threshold="bad")

    def test_in_requires_list_threshold(self):
        with pytest.raises(RuleActivationError, match="requires a list/tuple"):
            RuleCondition("X", ConditionOperator.IN, threshold="not-a-list")

    def test_invalid_operator_rejected(self):
        with pytest.raises(RuleActivationError, match="not in"):
            RuleCondition("X", "bogus")

    def test_extracted_from_preserved(self):
        c = RuleCondition("SEVERITY", ConditionOperator.EQ, "Severe",
                          extracted_from="severe or life-threatening")
        assert c.extracted_from == "severe or life-threatening"


# ===========================================================================
# EvaluationScope
# ===========================================================================

class TestEvaluationScope:
    def test_three_scope_kinds(self):
        assert len(EVALUATION_SCOPE_KINDS) == 3
        assert EvaluationScopeKind.FULL_HISTORY in EVALUATION_SCOPE_KINDS
        assert EvaluationScopeKind.CURRENT_SNAPSHOT in EVALUATION_SCOPE_KINDS
        assert EvaluationScopeKind.FUTURE_ONLY in EVALUATION_SCOPE_KINDS

    def test_default_kind(self):
        s = EvaluationScope()
        assert s.scope_kind == EvaluationScopeKind.CURRENT_SNAPSHOT

    def test_full_history(self):
        s = EvaluationScope(scope_kind=EvaluationScopeKind.FULL_HISTORY)
        assert s.is_full_history
        assert not s.is_future_only

    def test_future_only(self):
        s = EvaluationScope(
            scope_kind=EvaluationScopeKind.FUTURE_ONLY,
            valid_from="2026-08-10",
        )
        assert s.is_future_only
        assert not s.is_full_history

    def test_future_only_requires_explicit_boundary(self):
        with pytest.raises(RuleActivationError, match="valid_from"):
            EvaluationScope(scope_kind=EvaluationScopeKind.FUTURE_ONLY)

    def test_domain_scope_filtering(self):
        s = EvaluationScope(domain_scope=("AE", "MH"))
        assert s.applies_to_domain("AE")
        assert s.applies_to_domain("ae")  # case-insensitive
        assert not s.applies_to_domain("LB")

    def test_empty_domain_scope_admits_all(self):
        s = EvaluationScope()
        assert s.applies_to_domain("AE")
        assert s.applies_to_domain("LB")

    def test_subject_scope_filtering(self):
        s = EvaluationScope(subject_scope=("S002", "S001", "S001"))
        assert s.subject_scope == ("S001", "S002")
        assert s.applies_to_subject("S001")
        assert not s.applies_to_subject("S003")

    def test_invalid_kind_rejected(self):
        with pytest.raises(RuleActivationError, match="not in"):
            EvaluationScope(scope_kind="bogus")


# ===========================================================================
# RuleDraft
# ===========================================================================

class TestRuleDraft:
    def _make_draft(self, **kw):
        defaults = dict(
            draft_id="draft-1",
            project_id="proj-alpha",
            rule_name="severe_ae_flag",
            natural_language="Flag any AE with severity grade >= 3",
            conditions=(
                RuleCondition("SEVERITY", ConditionOperator.EQ, "Severe",
                              extracted_from="severity grade >= 3"),
            ),
            source_revision_id="rev-protocol-1",
        )
        defaults.update(kw)
        return RuleDraft(**defaults)

    def test_basic_draft(self):
        d = self._make_draft()
        assert d.rule_name == "severe_ae_flag"
        assert d.status == RuleDraftStatus.DRAFT
        assert len(d.conditions) == 1
        assert d.content_hash  # auto-computed

    def test_requires_at_least_one_condition(self):
        with pytest.raises(RuleActivationError, match="at least one condition"):
            self._make_draft(conditions=())

    def test_logical_combination_all(self):
        d = self._make_draft(
            conditions=(
                RuleCondition("A", ConditionOperator.EQ, 1),
                RuleCondition("B", ConditionOperator.EQ, 2),
            ),
            logical_combination="all",
        )
        assert d.matches_record({"A": 1, "B": 2}) is True
        assert d.matches_record({"A": 1, "B": 99}) is False

    def test_logical_combination_any(self):
        d = self._make_draft(
            conditions=(
                RuleCondition("A", ConditionOperator.EQ, 1),
                RuleCondition("B", ConditionOperator.EQ, 2),
            ),
            logical_combination="any",
        )
        assert d.matches_record({"A": 1, "B": 99}) is True
        assert d.matches_record({"A": 0, "B": 0}) is False

    def test_invalid_logical_combination(self):
        with pytest.raises(RuleActivationError, match="logical_combination"):
            self._make_draft(logical_combination="xor")

    def test_content_hash_deterministic(self):
        d1 = self._make_draft()
        d2 = self._make_draft()
        assert d1.content_hash == d2.content_hash

    def test_different_nl_different_hash(self):
        d1 = self._make_draft(natural_language="rule A")
        d2 = self._make_draft(natural_language="rule B")
        assert d1.content_hash != d2.content_hash

    def test_declared_hash_mismatch_rejected(self):
        with pytest.raises(RuleActivationError, match="content_hash mismatch"):
            self._make_draft(content_hash="0" * 64)

    def test_nl_and_conditions_preserved(self):
        d = self._make_draft(natural_language="Flag ALT > 3x ULN")
        assert "ALT" in d.natural_language
        assert d.conditions[0].field == "SEVERITY"


# ===========================================================================
# Simulation
# ===========================================================================

class TestSimulation:
    def _make_draft(self):
        return RuleDraft(
            draft_id="draft-1",
            project_id="proj-alpha",
            rule_name="alt_elevated",
            natural_language="Flag ALT values above 40",
            conditions=(
                RuleCondition("VAL", ConditionOperator.GT, 40,
                              extracted_from="ALT above 40"),
            ),
            source_revision_id="rev-1",
        )

    def test_simulate_basic(self):
        d = self._make_draft()
        records = [
            {"_record_id": "r1", "VAL": 45},
            {"_record_id": "r2", "VAL": 30},
            {"_record_id": "r3", "VAL": 50},
        ]
        sim = simulate_rule(d, records)
        assert sim.outcome.n_total == 3
        assert sim.outcome.n_matched == 2
        assert sim.outcome.n_not_matched == 1
        assert sim.outcome.match_rate == pytest.approx(2 / 3)

    def test_simulate_missing_field(self):
        d = self._make_draft()
        records = [
            {"_record_id": "r1", "VAL": 45},
            {"_record_id": "r2"},  # missing VAL
        ]
        sim = simulate_rule(d, records)
        assert sim.outcome.n_missing_field == 1
        # missing value does not match
        r2 = [m for m in sim.outcome.matches if m.record_id == "r2"][0]
        assert r2.matched is False

    def test_simulate_deterministic(self):
        d = self._make_draft()
        records = [{"VAL": 45}, {"VAL": 30}]
        s1 = simulate_rule(d, records, simulation_id="sim-x")
        s2 = simulate_rule(d, records, simulation_id="sim-x")
        assert s1.content_hash == s2.content_hash

    def test_simulate_binds_to_draft_hash(self):
        d = self._make_draft()
        sim = simulate_rule(d, [{"VAL": 45}])
        assert sim.draft_content_hash == d.content_hash
        assert sim.draft_id == d.draft_id

    def test_simulate_empty_records(self):
        d = self._make_draft()
        sim = simulate_rule(d, [])
        assert sim.outcome.n_total == 0
        assert sim.outcome.match_rate == 0.0

    def test_requires_rule_draft(self):
        with pytest.raises(RuleActivationError):
            simulate_rule("not-a-draft", [])

    def test_duplicate_simulation_record_ids_rejected(self):
        d = self._make_draft()
        with pytest.raises(RuleActivationError, match="duplicate simulation record_id"):
            simulate_rule(
                d,
                [
                    {"_record_id": "same", "VAL": 45},
                    {"_record_id": "same", "VAL": 30},
                ],
            )


# ===========================================================================
# Activation
# ===========================================================================

class TestActivation:
    def _make_draft_and_sim(self):
        d = RuleDraft(
            draft_id="draft-1",
            project_id="proj-alpha",
            rule_name="alt_elevated",
            natural_language="Flag ALT values above 40",
            conditions=(RuleCondition("VAL", ConditionOperator.GT, 40),),
            source_revision_id="rev-1",
        )
        sim = simulate_rule(d, [{"_record_id": "r1", "VAL": 45}])
        return d, sim

    def test_machine_activation(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope(scope_kind=EvaluationScopeKind.CURRENT_SNAPSHOT)
        act = activate_rule(
            d, sim, version="1", evaluation_scope=scope,
            activated_by="system_policy",
        )
        assert act.version == "1"
        assert act.is_machine
        assert not act.user_confirmed
        assert act.draft_content_hash == d.content_hash
        assert act.simulation_id == sim.simulation_id

    def test_user_activation(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope(scope_kind=EvaluationScopeKind.FULL_HISTORY)
        act = activate_rule(
            d, sim, version="1", evaluation_scope=scope,
            activated_by="local_test_user",
            is_machine=False,
            user_confirmed=True,
        )
        assert act.user_confirmed
        assert not act.is_machine
        assert scope.is_full_history

    def test_machine_cannot_user_confirm(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope()
        with pytest.raises(RuleActivationError, match="cannot declare user_confirmed"):
            activate_rule(
                d, sim, version="1", evaluation_scope=scope,
                activated_by="system",
                is_machine=True,
                user_confirmed=True,
            )

    def test_user_must_confirm(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope()
        with pytest.raises(RuleActivationError, match="must declare user_confirmed"):
            activate_rule(
                d, sim, version="1", evaluation_scope=scope,
                activated_by="user",
                is_machine=False,
                user_confirmed=False,
            )

    def test_stale_simulation_blocks_activation(self):
        d, sim = self._make_draft_and_sim()
        # modify the draft (different NL) but try to activate with old sim
        d2 = RuleDraft(
            draft_id="draft-1",
            project_id="proj-alpha",
            rule_name="alt_elevated",
            natural_language="Flag ALT values above 50",  # changed
            conditions=(RuleCondition("VAL", ConditionOperator.GT, 50),),
            source_revision_id="rev-1",
        )
        scope = EvaluationScope()
        with pytest.raises(RuleActivationError, match="different draft content hash"):
            activate_rule(d2, sim, version="1", evaluation_scope=scope,
                          activated_by="system")

    def test_wrong_simulation_draft_id_blocks(self):
        d, sim = self._make_draft_and_sim()
        d_other = RuleDraft(
            draft_id="draft-OTHER",
            project_id="proj-alpha",
            rule_name="other",
            natural_language="other rule",
            conditions=(RuleCondition("VAL", ConditionOperator.GT, 40),),
            source_revision_id="rev-1",
        )
        scope = EvaluationScope()
        with pytest.raises(RuleActivationError, match="draft_id does not match"):
            activate_rule(d_other, sim, version="1", evaluation_scope=scope,
                          activated_by="system")

    def test_version_required(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope()
        with pytest.raises((RuleActivationError, ValueError)):
            activate_rule(d, sim, version="", evaluation_scope=scope,
                          activated_by="system")

    def test_scope_required(self):
        d, sim = self._make_draft_and_sim()
        with pytest.raises(RuleActivationError):
            activate_rule(d, sim, version="1", evaluation_scope=None,
                          activated_by="system")

    def test_activation_content_hash_deterministic(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope(scope_kind=EvaluationScopeKind.FUTURE_ONLY,
                                domain_scope=("AE",), valid_from="2026-08-10")
        a1 = activate_rule(d, sim, version="1", evaluation_scope=scope,
                           activated_by="system", activation_id="a-1")
        a2 = activate_rule(d, sim, version="1", evaluation_scope=scope,
                           activated_by="system", activation_id="a-1")
        assert a1.content_hash == a2.content_hash

    def test_supersedes_recorded(self):
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope()
        act = activate_rule(
            d, sim, version="2", evaluation_scope=scope,
            activated_by="system", supersedes=("act-old-1", "act-old-2"),
        )
        assert "act-old-1" in act.supersedes
        assert "act-old-2" in act.supersedes

    def test_activation_is_only_path(self):
        """RuleActivation constructor itself enforces invariants."""
        d, sim = self._make_draft_and_sim()
        scope = EvaluationScope()
        with pytest.raises((RuleActivationError, ValueError)):
            RuleActivation(
                activation_id="x",
                project_id="p",
                draft_id=d.draft_id,
                draft_content_hash=d.content_hash,
                simulation_id=sim.simulation_id,
                version="1",
                evaluation_scope=scope,
                activated_by="",
            )
