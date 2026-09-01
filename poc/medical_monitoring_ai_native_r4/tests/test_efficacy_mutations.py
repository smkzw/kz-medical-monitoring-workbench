"""R4-D06 non-circular mutation / tamper / immutability tests.

These tests prove the raw runtime output is derived from typed input plus
frozen rules and cannot be influenced by the expected outcome, manifest
traces, case/test/challenge identity, or post-construction mutation of the
input:

* tampering the expected outcome text or the manifest trace edges never
  changes the raw entrypoint output;
* changing the fixture's ``challenge_number`` never branches evaluator
  behavior (only the input-derived annotation leaves change);
* mutating baseline candidates, enrollment rules/events, risk/public
  identity inputs, TTE event identities, priority policy, scope, accepted
  report/result fields, or nested source mappings fails closed or changes
  the derived identity/hash;
* the deeply frozen fixture cannot be mutated after construction (nested
  source-dict/list changes and direct nested mutation are inert);
* the journey projection and its source jumps derive from the actual
  runtime inputs.

All data is synthetic and offline.
"""

from __future__ import annotations

import copy
import hashlib
import sys
from dataclasses import replace
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.efficacy import (  # noqa: E402
    D06ContractViolationError,
    SCOPE_IDENTITY_FIELDS,
    d06_canonical_json,
    d06_content_hash,
)
from mm_r4.efficacy_evaluator import (  # noqa: E402
    evaluate_efficacy_fixture,
    validate_audience_projection,
    validate_challenge_registry_input,
)
from mm_r4.efficacy_fixtures import (  # noqa: E402
    D06FixtureAdapter,
    ENTRYPOINTS,
    build_d06_challenge_matrix,
)

MATRIX = build_d06_challenge_matrix()
ADAPTER = D06FixtureAdapter()


def _run_case_entrypoint(fixture_dict, number):
    """Execute the case through its declared frozen entrypoint."""
    case = MATRIX.by_number(number)
    return ENTRYPOINTS[case.entrypoint_id](ADAPTER.build(fixture_dict)).to_plain()


def _run_built_fixture(fixture, number):
    """Execute an already-built runtime fixture through the entrypoint."""
    case = MATRIX.by_number(number)
    return ENTRYPOINTS[case.entrypoint_id](fixture).to_plain()


_SEMANTIC_KEYS = (
    "output_kind",
    "l1_disposition",
    "primary_subtype",
    "coverage_status",
    "gate_state",
    "gate_disposition",
    "error_type",
    "error_stage",
    "l2_counts",
    "trace_edges",
    "audience_validation_state",
)


def _mutate_case(number: int, mutation):
    case = MATRIX.by_number(number)
    mutated = copy.deepcopy(case.catalog_case)
    mutation(mutated["fixture"])
    return ADAPTER.build(mutated), case


def _rehash_content(obj):
    """Recompute ``content_hash`` payload-consistently after a mutation."""
    core = {key: value for key, value in obj.items() if key != "content_hash"}
    obj["content_hash"] = "sha256:{0}".format(
        hashlib.sha256(d06_canonical_json(core).encode("utf-8")).hexdigest()
    )


def _rehash_embedded(obj):
    """Recompute the ``hash`` field payload-consistently (registry/event
    objects)."""
    core = {key: value for key, value in obj.items() if key != "hash"}
    obj["hash"] = "sha256:{0}".format(
        hashlib.sha256(d06_canonical_json(core).encode("utf-8")).hexdigest()
    )


def _rehash_lineage(obj):
    """Recompute the ``lineage_hash`` field payload-consistently
    (assessment/ref/binding objects that use lineage_hash instead of hash)."""
    core = {key: value for key, value in obj.items() if key != "lineage_hash"}
    obj["lineage_hash"] = "sha256:{0}".format(
        hashlib.sha256(d06_canonical_json(core).encode("utf-8")).hexdigest()
    )


# ---------------------------------------------------------------------------
# Expected / manifest tampering never changes raw output
# ---------------------------------------------------------------------------


class TestNoExpectedOrManifestInjection:
    def test_tampered_expected_text_does_not_change_raw_output(self):
        case = MATRIX.by_number(2)
        raw = case.assemble()
        mutated = copy.deepcopy(case.catalog_case)
        mutated["expected_outcome"]["domain_assertions"][
            "clinical_outcome_contract"
        ] = "TAMPERED EXPECTED TEXT"
        out = _run_case_entrypoint(mutated, 2)
        assert out == raw

    def test_tampered_manifest_trace_does_not_change_raw_output(self):
        case = MATRIX.by_number(2)
        raw = case.assemble()
        mutated = copy.deepcopy(case.catalog_case)
        mutated["required_trace_edge_types"] = ["accepted_artifact"] + list(
            mutated["required_trace_edge_types"]
        )
        out = _run_case_entrypoint(mutated, 2)
        assert out == raw

    def test_tampered_expected_l1_does_not_change_raw_output(self):
        case = MATRIX.by_number(1)
        raw = case.assemble()
        mutated = copy.deepcopy(case.catalog_case)
        mutated["expected_outcome"]["l1_disposition"] = "positive"
        out = _run_case_entrypoint(mutated, 1)
        assert out == raw

    def test_case_106_manifest_trace_injection_ignored(self):
        case = MATRIX.by_number(106)
        raw = case.assemble()
        mutated = copy.deepcopy(case.catalog_case)
        mutated["required_trace_edge_types"] = [
            "accepted_artifact",
            "rule_lineage",
            "scope_binding",
            "source_locator",
        ]
        out = _run_case_entrypoint(mutated, 106)
        assert out == raw
        assert "accepted_artifact" not in out["trace_edges"]


# ---------------------------------------------------------------------------
# Case identity is not a behavior discriminator
# ---------------------------------------------------------------------------


class TestCaseIdentityInaccessible:
    def test_challenge_number_does_not_branch_behavior(self):
        case = MATRIX.by_number(2)
        raw = case.assemble()
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["challenge_number"] = 999
        out = _run_case_entrypoint(mutated, 2)
        for key in _SEMANTIC_KEYS:
            assert out[key] == raw[key], f"{key} branched on challenge number"
        # Only the input-derived annotation leaves follow the input.
        assert out["domain_assertions"]["challenge_assertion_code"] == "D06-CH-999"

    def test_challenge_number_mutation_across_family(self):
        for number in (1, 31, 196, 214):
            case = MATRIX.by_number(number)
            raw = case.assemble()
            mutated = copy.deepcopy(case.catalog_case)
            mutated["fixture"]["challenge_number"] = 777
            out = _run_case_entrypoint(mutated, number)
            for key in _SEMANTIC_KEYS:
                assert out[key] == raw[key], (
                    f"case {number} {key} branched on challenge number"
                )


# ---------------------------------------------------------------------------
# Typed input drift fails closed or changes the derived identity
# ---------------------------------------------------------------------------


class TestTypedInputDrift:
    def test_191_accepted_report_source_removal_fails_closed(self):
        # Removing a required typed source field fails closed at the
        # adapter boundary (before medical evaluation).
        case = MATRIX.by_number(191)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["case_inputs"]["typed_parameters"]["source"].pop(
            "accepted_result_ids"
        )
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_191_claim_not_accepted_fails_closed(self):
        fixture, _ = _mutate_case(
            191,
            lambda fx: fx["case_inputs"]["typed_parameters"]["report"].update(
                {"acceptance_state": "unaccepted"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_191_accepted_result_value_drift_changes_or_fails(self):
        case = MATRIX.by_number(191)
        raw = case.assemble()
        fixture, _ = _mutate_case(
            191, lambda fx: fx["records"]["accepted_result"].update({"value": "999"})
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error" or out != raw

    def test_35_baseline_candidate_mutation_fails_closed(self):
        fixture, _ = _mutate_case(
            35,
            lambda fx: fx["case_inputs"]["typed_parameters"]["baseline"].update(
                {"candidates": ["ASM-MUT-A", "ASM-MUT-B"]}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_35_baseline_candidate_order_swaps_selection(self):
        # Candidate reordering must either keep the deterministic
        # chronological-last selection or fail closed (annotation drift).
        fixture, _ = _mutate_case(
            35,
            lambda fx: fx["case_inputs"]["typed_parameters"]["baseline"].update(
                {"candidates": ["ASM-BASE-D1", "ASM-BASE-D7"]}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        if out["output_kind"] == "error":
            return  # fail closed on input drift is acceptable
        assert out["domain_assertions"]["selected_candidate_id"] == "ASM-BASE-D1"
        assert out["l1_disposition"] == "negative"

    def test_2_risk_public_identity_drift_changes_hash(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["source_registries"]["d06_unit_stable_core"].update(
                {"stable_endpoint_key": "SYN-ENDPOINT-MUT"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_2_stable_core_unit_id_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["source_registries"]["d06_unit_stable_core"].update(
                {"unit_id": "UNIT-999"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_162_enrollment_rule_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            162,
            lambda fx: fx["source_registries"]["enrollment_rule_registry"].update(
                {"rule_version": "9.9"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_188_enrollment_decision_drift_changes_derivation(self):
        case = MATRIX.by_number(188)
        raw = case.assemble()
        fixture, _ = _mutate_case(
            188,
            lambda fx: fx["bindings"]["enrollment_context_decisions"][0].update(
                {"query_context": "enrollment_not_occurred"}
            ),
        )
        out = validate_audience_projection(fixture).to_plain()
        assert out["output_kind"] == "error" or out != raw

    def test_196_tte_event_identity_drift(self):
        case = MATRIX.by_number(196)
        raw = case.assemble()
        fixture, _ = _mutate_case(
            196,
            lambda fx: fx["source_registries"]["tte_source_events"][0].update(
                {"event_id": "EV-MUTATED"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error" or out != raw

    def test_196_tte_binding_id_drift_fails_closed(self):
        # A missing/drifted typed precedence binding id must fail closed;
        # the runtime never falls back to a fixed TTE-BIND id.
        fixture, _ = _mutate_case(
            196,
            lambda fx: fx["bindings"]["tte_precedence_binding"].update(
                {"id": "TTE-BIND-MUT"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_tte_binding_id_removal_fails_closed(self):
        # Removing a required typed binding field fails closed at the
        # adapter boundary (before medical evaluation).
        case = MATRIX.by_number(196)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["bindings"]["tte_precedence_binding"].pop("id")
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_196_tte_selected_event_removal_fails_closed(self):
        # Removing the competing event from the typed source registry
        # must fail closed (no fixed EV-COMP-001 fallback).
        fixture, _ = _mutate_case(
            196,
            lambda fx: fx["source_registries"]["tte_source_events"].pop(1),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_tte_rule_linkage_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            196,
            lambda fx: fx["source_registries"]["tte_rule_registry"].update(
                {"event_precedence_rule_id": "TTE-RULE-999"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_196_tte_binding_scope_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            196,
            lambda fx: fx["bindings"]["tte_precedence_binding"].update(
                {"run_ref": "SYN-WRONG-RUN"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06BindingContractError"
        assert out["error_stage"] == "typed_binding_validation"

    def test_2_risk_binding_drift_fails_closed(self):
        # Supplied risk binding drift must fail closed (never ignored).
        fixture, _ = _mutate_case(
            2, lambda fx: fx["risk_binding"].update({"risk_id": "RISK-999"})
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_2_risk_binding_lifecycle_ref_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["risk_binding"].update(
                {"R2_lifecycle_ref": "R2-LIFECYCLE-999"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_2_risk_binding_locator_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["risk_binding"].update(
                {"source_locator_ids": ["SYN-LOC-MUTATED"]}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_2_public_identity_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["public_r4_risk_identity"].update(
                {"risk_id": "RISK-999"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_public_identity_hash_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["public_r4_risk_identity"].update(
                {"public_identity_hash": "sha256:MUTATED"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_2_public_identity_scope_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            2,
            lambda fx: fx["public_r4_risk_identity"].update(
                {"scope_key": ["SYN-WRONG", "SYN-WRONG", "SYN-WRONG"]}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_162_variant_source_event_removal_fails_closed(self):
        # Removing an enrollment variant source event must fail closed
        # and suppress the Query instead of echoing unresolved refs.
        fixture, _ = _mutate_case(
            162,
            lambda fx: fx["source_registries"]["enrollment_source_events"].pop(0),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert "query_context_outcomes" not in out["domain_assertions"]

    def test_67_priority_policy_hash_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            67,
            lambda fx: fx["policies"]["priority_resolution_input"].update(
                {"priority_policy_hash": "sha256:MUTATED"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_1_wrong_scope_fails_closed_with_actual_hash(self):
        case = MATRIX.by_number(1)
        fixture, _ = _mutate_case(
            1, lambda fx: fx["scope"].update({"project_ref": "SYN-MUTATED"})
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06BindingContractError"
        assert out["error_stage"] == "typed_binding_validation"
        assert out["input_scope_hash"] == (
            "sha256:"
            + d06_content_hash(
                case.fixture | {"project_ref": "SYN-MUTATED"}
                if False
                else {**case.fixture["scope"], "project_ref": "SYN-MUTATED"}
            )
        )
        # Scope integrity failure emits no priority / resolver / identity
        # / projection (P1-2 wrong-scope mutation proof).
        assert "priority_resolution" not in out["domain_assertions"]
        assert out["object_hashes"]["priority_resolver_input_hash"] is None
        assert out["object_hashes"]["public_r4_identity_hash"] is None
        assert "audience_payload" not in out

    def test_153_wrong_scope_gate_case_no_priority(self):
        # A mutated fixture scope on a gate entrypoint also fails closed
        # with no priority resolution.
        fixture, _ = _mutate_case(
            153, lambda fx: fx["scope"].update({"project_ref": "SYN-MUTATED"})
        )
        out = _run_built_fixture(fixture, 153)
        assert out["output_kind"] == "error"
        assert "priority_resolution" not in out["domain_assertions"]
        assert out["object_hashes"]["priority_resolver_input_hash"] is None

    def test_214_registry_integrity_error_has_no_priority_on_broken_scope(self):
        # When the fixture/schema/scope integrity itself fails, no
        # priority resolution, resolver input hash/object, risk/public
        # identity or clinical projection is emitted.
        fixture, _ = _mutate_case(
            214, lambda fx: fx["scope"].update({"run_ref": "SYN-MUTATED"})
        )
        out = validate_challenge_registry_input(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "ChallengeRegistryIntegrityError"
        assert out["error_stage"] == "pre_fixture_integrity"
        assert out["domain_assertions"]["evaluator_invoked"] is False
        assert "priority_resolution" not in out["domain_assertions"]
        assert out["object_hashes"]["priority_resolver_input_hash"] is None
        assert out["object_hashes"]["public_r4_identity_hash"] is None
        # No clinical projection / audience payload is emitted.
        assert "audience_payload" not in out
        assert "audience_validation_result" not in out

    def test_nested_source_mapping_mutation_fails_closed(self):
        fixture, _ = _mutate_case(
            191,
            lambda fx: fx["bindings"]["d05_refs"][0].update(
                {"source_record_id": "ASM-MUTATED"}
            ),
        )
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"


# ---------------------------------------------------------------------------
# Deep immutability
# ---------------------------------------------------------------------------


class TestDeepImmutability:
    def test_nested_mutation_of_frozen_fixture_raises(self):
        case = MATRIX.by_number(2)
        fixture = case.build_runtime_fixture()
        with pytest.raises(TypeError):
            fixture.scope["project_ref"] = "MUT"  # type: ignore[index]
        with pytest.raises(TypeError):
            fixture.records["item_values"]["I1"] = "99"  # type: ignore[index]

    def test_post_construction_source_mutation_does_not_change_outcome(self):
        case = MATRIX.by_number(2)
        source = copy.deepcopy(case.catalog_case)
        fixture = ADAPTER.build(source)
        before = evaluate_efficacy_fixture(fixture).to_plain()
        # Mutate the caller's source dict after construction.
        source["fixture"]["case_inputs"]["typed_parameters"]["accepted_result"][
            "value"
        ] = "999"
        source["fixture"]["scope"]["project_ref"] = "SYN-MUTATED"
        after = evaluate_efficacy_fixture(fixture).to_plain()
        assert after == before

    def test_nested_list_mutation_does_not_change_outcome(self):
        case = MATRIX.by_number(2)
        fixture = case.build_runtime_fixture()
        before = evaluate_efficacy_fixture(fixture).to_plain()
        with pytest.raises(TypeError):
            fixture.records["trend_points"][0]["value"] = "999"  # type: ignore[index]
        after = evaluate_efficacy_fixture(fixture).to_plain()
        assert after == before


# ---------------------------------------------------------------------------
# Journey projection derives from actual runtime inputs
# ---------------------------------------------------------------------------


class TestJourneyDerivation:
    def test_projection_source_jumps_from_runtime_objects(self):
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(31)
        fixture = case.build_runtime_fixture()
        projection = project_efficacy_journey(
            fixture, scope_status="out_of_cutoff", unit_l1=None
        )
        out_of_cutoff = [
            marker
            for marker in projection.out_of_cutoff_markers
            if marker.marker_kind == "out_of_cutoff"
        ]
        assert out_of_cutoff
        assert all(marker.source_jump_target for marker in out_of_cutoff)
        # Identities derive from the typed runtime objects, never static
        # fallback ids.
        spine = fixture.bindings["shared_temporal_spine_binding"]
        assert (
            projection.shared_temporal_spine_binding_id
            == spine["spine_binding_id"]
        )
        assert projection.projection_id.startswith("D06-PROJECTION-")
        assert projection.projection_id != "D06-PROJECTION-001"

    def test_projection_identity_changes_on_typed_spine_drift(self):
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(31)
        base = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        fixture, _ = _mutate_case(
            31,
            lambda fx: fx["bindings"]["shared_temporal_spine_binding"].update(
                {"spine_binding_id": "SPINE-MUT"}
            ),
        )
        drifted = project_efficacy_journey(
            fixture, scope_status=None, unit_l1=None
        )
        assert drifted.shared_temporal_spine_binding_id == "SPINE-MUT"
        assert drifted.projection_id != base.projection_id

    def test_spine_hash_drift_fails_closed_in_pipeline(self):
        # A drifted temporal spine (stale hash) suppresses the journey
        # payload with the exact projection error state.
        fixture, _ = _mutate_case(
            31,
            lambda fx: fx["bindings"]["shared_temporal_spine_binding"].update(
                {"spine_binding_id": "SPINE-MUT"}
            ),
        )
        out = validate_audience_projection(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out.get("audience_payload") is None
        assert out["audience_payload_absent"] is True

    def test_positive_projection_risk_anchor_from_runtime(self):
        from mm_r4.efficacy import D06PriorityDecision
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(2)
        fixture = case.build_runtime_fixture()
        raw = fixture.policies["priority_resolution_input"]
        decision = D06PriorityDecision(
            scope=dict(fixture.scope),
            unit_id=fixture.source_registries["d06_unit_stable_core"]["unit_id"],
            risk_id="RISK-001",
            priority_decision_id="PRIORITY-DEC-001",
            endpoint_definition_id=raw["endpoint_definition_id"],
            stable_endpoint_key=raw["stable_endpoint_key"],
            stable_timepoint_key=raw["stable_timepoint_key"],
            endpoint_role=raw["endpoint_role"],
            impact_resolution_state=raw["impact_resolution_state"],
            impact_class=raw["impact_class"],
            recurrence_class=raw["recurrence_class"],
            recoverability=raw["recoverability"],
            actionability=raw["actionability"],
            monitoring_priority=raw["monitoring_priority"],
            matched_precedence_step=raw["matched_precedence_step"],
            reason_codes=tuple(raw["reason_codes"]),
            machine_close_forbidden=raw["machine_close_forbidden"],
            priority_policy_id=raw["priority_policy_id"],
            priority_policy_version=raw["priority_policy_version"],
            priority_policy_hash=raw["priority_policy_hash"],
            priority_resolver_input_hash="sha256:" + "0" * 64,
            source_locator_ids=tuple(raw["source_locator_ids"]),
        )
        projection = project_efficacy_journey(
            fixture,
            scope_status="in_scope",
            unit_l1="positive",
            priority_decision=decision,
        )
        risk_markers = [
            marker for marker in projection.markers if marker.marker_kind == "risk"
        ]
        assert risk_markers
        assert risk_markers[0].risk_anchor == "RISK-001"
        assert risk_markers[0].marker_id == "MRK-RISK-001"
        assert risk_markers[0].monitoring_priority == "medium"

    def test_positive_projection_risk_identity_from_decision(self):
        from mm_r4.efficacy import D06PriorityDecision
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(2)
        fixture = case.build_runtime_fixture()
        raw = fixture.policies["priority_resolution_input"]
        base = D06PriorityDecision(
            scope=dict(fixture.scope),
            unit_id=fixture.source_registries["d06_unit_stable_core"]["unit_id"],
            risk_id="RISK-001",
            priority_decision_id="PRIORITY-DEC-001",
            endpoint_definition_id=raw["endpoint_definition_id"],
            stable_endpoint_key=raw["stable_endpoint_key"],
            stable_timepoint_key=raw["stable_timepoint_key"],
            endpoint_role=raw["endpoint_role"],
            impact_resolution_state=raw["impact_resolution_state"],
            impact_class=raw["impact_class"],
            recurrence_class=raw["recurrence_class"],
            recoverability=raw["recoverability"],
            actionability=raw["actionability"],
            monitoring_priority=raw["monitoring_priority"],
            matched_precedence_step=raw["matched_precedence_step"],
            reason_codes=tuple(raw["reason_codes"]),
            machine_close_forbidden=raw["machine_close_forbidden"],
            priority_policy_id=raw["priority_policy_id"],
            priority_policy_version=raw["priority_policy_version"],
            priority_policy_hash=raw["priority_policy_hash"],
            priority_resolver_input_hash="sha256:" + "0" * 64,
            source_locator_ids=tuple(raw["source_locator_ids"]),
        )
        drifted = replace(
            base, risk_id="RISK-777", monitoring_priority="high"
        )
        projection = project_efficacy_journey(
            fixture,
            scope_status="in_scope",
            unit_l1="positive",
            priority_decision=drifted,
        )
        risk_markers = [
            marker for marker in projection.markers if marker.marker_kind == "risk"
        ]
        assert risk_markers
        assert risk_markers[0].risk_anchor == "RISK-777"
        assert risk_markers[0].marker_id == "MRK-RISK-777"
        assert risk_markers[0].monitoring_priority == "high"

    def test_positive_projection_without_decision_fails_closed(self):
        from mm_r4.efficacy import D06ContractViolationError
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(2)
        fixture = case.build_runtime_fixture()
        with pytest.raises(D06ContractViolationError):
            project_efficacy_journey(
                fixture, scope_status="in_scope", unit_l1="positive"
            )


# ---------------------------------------------------------------------------
# v1.18 semantic identity and definition-boundary adaptation
# ---------------------------------------------------------------------------


class TestV118SemanticIdentity:
    """Removing only ``fixture.challenge_number`` must not change any
    non-case-bound outcome field: entrypoint, traces and every non-case
    field stay identical; only ``challenge_assertion_code``,
    ``evaluated_fixture_hash`` and ``object_hashes.fixture_hash`` may
    differ (v1.18 generator invariance)."""

    _CASE_BOUND_LEAVES = {
        "domain_assertions.challenge_assertion_code",
        "domain_assertions.evaluated_fixture_hash",
        "object_hashes.fixture_hash",
    }

    @pytest.mark.parametrize("number", [1, 2, 17, 31, 106, 191, 196, 214, 216])
    def test_challenge_number_removal_preserves_all_other_fields(self, number):
        case = MATRIX.by_number(number)
        base = case.assemble()
        stripped = copy.deepcopy(case.catalog_case)
        stripped["fixture"].pop("challenge_number", None)
        out = _run_case_entrypoint(stripped, number)
        assert out["invoked_entrypoint"] == base["invoked_entrypoint"]
        assert out["trace_edges"] == base["trace_edges"]
        base_leaves = {".".join(path): value for path, value in _leaves(base)}
        out_leaves = {".".join(path): value for path, value in _leaves(out)}
        for path, value in base_leaves.items():
            if path in self._CASE_BOUND_LEAVES:
                continue
            assert out_leaves.get(path) == value, (
                f"case {number} non-case-bound leaf {path} changed after "
                "challenge_number removal"
            )

    def test_17_and_173_share_identical_semantic_outcome(self):
        """Cases 17 and 173 have identical substantive fixtures (modulo
        challenge_number) and must yield identical entrypoint, traces and
        every non-case-bound outcome field, including the unified
        clinical_outcome_contract text."""
        case17 = MATRIX.by_number(17)
        case173 = MATRIX.by_number(173)
        out17 = case17.assemble()
        out173 = case173.assemble()
        assert out17["invoked_entrypoint"] == out173["invoked_entrypoint"]
        assert out17["trace_edges"] == out173["trace_edges"]
        assert (
            out17["domain_assertions"]["clinical_outcome_contract"]
            == (out173["domain_assertions"]["clinical_outcome_contract"])
        )
        for key in _SEMANTIC_KEYS:
            assert out17[key] == out173[key], f"{key} differs between 17/173"
        for key in ("object_hashes", "domain_assertions"):
            if key == "object_hashes":
                assert (
                    out17[key]["priority_policy_hash"]
                    == out173[key]["priority_policy_hash"]
                )
                assert (
                    out17[key]["priority_resolver_input_hash"]
                    == out173[key]["priority_resolver_input_hash"]
                )
            elif key == "domain_assertions":
                assert (
                    out17[key]["priority_resolution"]
                    == out173[key]["priority_resolution"]
                )


class TestV118DefinitionBoundary:
    def test_instrument_content_hash_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            17,
            lambda fx: fx["definitions"]["instrument"].update(
                {"content_hash": "sha256:MUTATED"}
            ),
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_instrument_schema_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            17,
            lambda fx: fx["definitions"]["instrument"].update(
                {"recall_period": "4_weeks"}
            ),
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_endpoint_version_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            17, lambda fx: fx["definitions"]["endpoint"].update({"version": "2.0"})
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_endpoint_schema_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            17,
            lambda fx: fx["definitions"]["endpoint"].update(
                {"directionality": "higher_better"}
            ),
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_definition_scope_drift_fails_closed(self):
        fixture, _ = _mutate_case(
            17,
            lambda fx: fx["definitions"]["instrument"]["definition_scope"].update(
                {"site_ref": "SYN-WRONG-SITE"}
            ),
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06BindingContractError"
        assert out["error_stage"] == "typed_binding_validation"

    def test_instrument_rehashed_version_drift_fails_closed(self):
        # A validly rehashed version drift must still fail: the boundary
        # resolver enforces the canonical version identity, not just the
        # payload digest.
        def mutate(fx):
            fx["definitions"]["instrument"].update({"version": "9.9"})
            _rehash_content(fx["definitions"]["instrument"])

        fixture, _ = _mutate_case(17, mutate)
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_endpoint_rehashed_version_drift_fails_closed(self):
        def mutate(fx):
            fx["definitions"]["endpoint"].update({"version": "9.9"})
            _rehash_content(fx["definitions"]["endpoint"])

        fixture, _ = _mutate_case(17, mutate)
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_instrument_rehashed_unknown_key_fails_closed(self):
        # An unknown schema key with a payload-consistent rehash must
        # fail before medical evaluation: the exact key set is enforced
        # at the adapter boundary.
        case = MATRIX.by_number(17)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["definitions"]["instrument"][
            "unexpected_field"
        ] = "x"
        _rehash_content(mutated["fixture"]["definitions"]["instrument"])
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_endpoint_rehashed_unknown_key_fails_closed(self):
        case = MATRIX.by_number(17)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["definitions"]["endpoint"]["unexpected_field"] = "x"
        _rehash_content(mutated["fixture"]["definitions"]["endpoint"])
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_instrument_rehashed_missing_field_fails_closed(self):
        # Removing a schema field (and rehashing) must fail the exact
        # key set before medical evaluation.
        case = MATRIX.by_number(17)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["definitions"]["instrument"].pop("reporter_type")
        _rehash_content(mutated["fixture"]["definitions"]["instrument"])
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_instrument_rehashed_semantic_value_fails_closed(self):
        # A rehashed semantic value drift (recall period) no longer
        # preserves the gate: the semantic state drift fails the derived
        # contract text (no identity lookup, no bypass).
        def mutate(fx):
            fx["definitions"]["instrument"].update({"recall_period": "4_weeks"})
            _rehash_content(fx["definitions"]["instrument"])

        fixture, _ = _mutate_case(17, mutate)
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_endpoint_rehashed_semantic_value_fails_closed(self):
        def mutate(fx):
            fx["definitions"]["endpoint"].update(
                {"directionality": "higher_better"}
            )
            _rehash_content(fx["definitions"]["endpoint"])

        fixture, _ = _mutate_case(17, mutate)
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_applicable_instrument_ids_drift_changes_decision(self):
        # Single applicable instrument -> unique selection; multi ->
        # definition boundary gate; identity-free.
        fixture, _ = _mutate_case(
            17,
            lambda fx: fx["case_inputs"]["typed_parameters"].update(
                {"applicable_instrument_ids": ["INST-001"]}
            ),
        )
        out = _run_built_fixture(fixture, 17)
        assert out["output_kind"] == "result" and out["l1_disposition"] is None


# ---------------------------------------------------------------------------
# followup4: scope-integrity priority suppression, stable source authority,
# recursive typed schema, TTE/enrollment linkage, Journey provenance and
# error-class regression
# ---------------------------------------------------------------------------


class TestFollowup4ScopeIntegrityPriority:
    def test_typed_scope_override_fails_before_priority(self):
        # An invalid typed scope override must fail closed and suppress
        # priority/resolver/identity/projection (verifier P1).
        case = MATRIX.by_number(1)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["case_inputs"]["typed_parameters"].update(
            {"scope": {"project_ref": "SYN-WRONG-PROJECT"}}
        )
        out = _run_case_entrypoint(mutated, 1)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06BindingContractError"
        assert out["error_stage"] == "typed_binding_validation"
        assert "priority_resolution" not in out["domain_assertions"]
        assert out["object_hashes"]["priority_resolver_input_hash"] is None
        assert out["object_hashes"]["public_r4_identity_hash"] is None
        assert "audience_payload" not in out

    def test_frozen_wrong_scope_rows_keep_oracle_priority(self):
        # Unmutated frozen wrong-scope rows keep their oracle priority.
        for number in (117, 133, 134, 135, 136):
            out = MATRIX.by_number(number).assemble()
            assert (
                out["domain_assertions"]["priority_resolution"][
                    "projection_state"
                ]
                == "resolver_result_only"
            )


# ---------------------------------------------------------------------------
# W4: typed authority scope binding -- no SYN-* sentinel / canonical-scope
# equality in the production binding path
# ---------------------------------------------------------------------------

_SCOPE_RENAME_MAP = {
    "SYN-D06-PROJECT": "RENAMED-PROJECT-ALPHA",
    "SYN-D06-RUN-001": "RENAMED-RUN-ALPHA",
    "SYN-D06-SITE-001": "RENAMED-SITE-ALPHA",
    "SYN-D06-SUBJECT-001": "RENAMED-SUBJECT-ALPHA",
    "SYN-D06-SCOPE-001": "RENAMED-SCOPE-ALPHA",
    "SYN-SNAPSHOT-001": "RENAMED-SNAPSHOT-ALPHA",
    "SYN-REV-001": "RENAMED-REV-ALPHA",
    "EPISODE-001": "RENAMED-EPISODE-ALPHA",
    # The frozen wrong-subject sentinel is fixture data: a coherent rename
    # maps it onto the renamed scope subject so the renamed fixture is
    # internally consistent.
    "SYN-WRONG-SUBJECT": "RENAMED-SUBJECT-ALPHA",
}


def _remap_scope_values(value):
    if isinstance(value, str):
        return _SCOPE_RENAME_MAP.get(value, value)
    if isinstance(value, list):
        return [_remap_scope_values(item) for item in value]
    if isinstance(value, dict):
        return {key: _remap_scope_values(item) for key, item in value.items()}
    return value


def _rehash_all_embedded(obj):
    """Recompute every embedded ``hash`` / ``lineage_hash`` /
    ``content_hash`` field payload-consistently (children before
    parents), so a coherent rename keeps every payload digest valid."""
    if isinstance(obj, dict):
        for value in obj.values():
            _rehash_all_embedded(value)
        for key in ("hash", "lineage_hash", "content_hash"):
            if (
                key in obj
                and isinstance(obj[key], str)
                and obj[key].startswith("sha256:")
            ):
                core = {k: v for k, v in obj.items() if k != key}
                obj[key] = "sha256:{0}".format(
                    hashlib.sha256(
                        d06_canonical_json(core).encode("utf-8")
                    ).hexdigest()
                )
    elif isinstance(obj, list):
        for value in obj:
            _rehash_all_embedded(value)


def _fix_producer_payload_links(fx):
    """Restore the D05 authority cross-links after a coherent rename: the
    accepted assessment ``lineage_hash`` must equal the inventory / D05
    binding ref / foreign-key ``producer_payload_hash``."""
    assessments = {
        assessment.get("id"): assessment
        for assessment in fx["records"].get("assessments", [])
    }
    for item in fx["source_registries"].get("accepted_d05_assessment_inventory", []):
        aid = item.get("source_record_id")
        if aid in assessments:
            item["producer_payload_hash"] = assessments[aid]["lineage_hash"]
    for item in fx["bindings"].get("d05_refs", []):
        aid = item.get("source_record_id")
        if aid in assessments:
            item["producer_payload_hash"] = assessments[aid]["lineage_hash"]
    for item in fx["source_registries"].get("d05_assessment_foreign_keys", []):
        aid = item.get("source_record_id")
        if aid in assessments:
            item["producer_payload_hash"] = assessments[aid]["lineage_hash"]


class TestTypedAuthorityScopeBinding:
    """The D06 authority scope is the fixture's own declared binding:
    typed child references and scope claims are validated against it, so
    wrong project/site/subject/run values fail closed through the same
    typed binding stage/type regardless of the value spelling.  No
    ``SYN-*`` sentinel and no module-level canonical-scope equality
    decides any production path."""

    def test_082_ice_wrong_subject_any_spelling_same_binding_error(self):
        baseline = MATRIX.by_number(82).assemble()
        semantic = {key: baseline[key] for key in _SEMANTIC_KEYS}
        for wrong in ("SUBJECT-999", "WRONG-SUBJECT-2", "ANY-OTHER-SUB", "x", ""):
            fixture, _ = _mutate_case(
                82,
                lambda fx, w=wrong: fx["case_inputs"]["typed_parameters"][
                    "ice"
                ].update({"subject_ref": w}),
            )
            out = _run_built_fixture(fixture, 82)
            assert {key: out[key] for key in _SEMANTIC_KEYS} == semantic, wrong

    def test_180_tte_wrong_subject_any_spelling_same_binding_error(self):
        baseline = MATRIX.by_number(180).assemble()
        semantic = {key: baseline[key] for key in _SEMANTIC_KEYS}
        for wrong in ("SUBJECT-999", "WRONG-SUBJECT-2", "ANY-OTHER-SUB", "x", ""):
            fixture, _ = _mutate_case(
                180,
                lambda fx, w=wrong: fx["case_inputs"]["typed_parameters"][
                    "tte"
                ].update({"subject_ref": w}),
            )
            out = _run_built_fixture(fixture, 180)
            assert {key: out[key] for key in _SEMANTIC_KEYS} == semantic, wrong

    def test_082_ice_wrong_identity_field_same_binding_error(self):
        # Any wrong identity field on the typed ICE event fails through
        # the same typed binding stage/type as the frozen wrong-subject
        # row, for every scope identity dimension.
        baseline = MATRIX.by_number(82).assemble()
        semantic = {key: baseline[key] for key in _SEMANTIC_KEYS}
        for field in SCOPE_IDENTITY_FIELDS:
            if field == "subject_ref":
                continue  # covered by the subject-spelling tests above
            fixture, _ = _mutate_case(
                82,
                lambda fx, f=field: fx["case_inputs"]["typed_parameters"][
                    "ice"
                ].update(
                    {
                        "subject_ref": "SYN-D06-SUBJECT-001",
                        f: "WRONG-" + f,
                    }
                ),
            )
            out = _run_built_fixture(fixture, 82)
            assert {key: out[key] for key in _SEMANTIC_KEYS} == semantic, field

    def test_180_tte_wrong_identity_field_same_binding_error(self):
        baseline = MATRIX.by_number(180).assemble()
        semantic = {key: baseline[key] for key in _SEMANTIC_KEYS}
        for field in SCOPE_IDENTITY_FIELDS:
            if field == "subject_ref":
                continue
            fixture, _ = _mutate_case(
                180,
                lambda fx, f=field: fx["case_inputs"]["typed_parameters"][
                    "tte"
                ].update(
                    {
                        "subject_ref": "SYN-D06-SUBJECT-001",
                        f: "WRONG-" + f,
                    }
                ),
            )
            out = _run_built_fixture(fixture, 180)
            assert {key: out[key] for key in _SEMANTIC_KEYS} == semantic, field

    def test_scope_claim_conflict_arbitrary_values_fail_closed(self):
        # A typed-parameter scope claim conflicting with the fixture's own
        # declared scope binding fails closed for ANY value spelling: the
        # frozen SYN-WRONG-* rows keep their frozen oracle leaves, and
        # arbitrary other spellings produce identical semantic leaves,
        # never a medical unit or risk.
        for number in (117, 133, 134, 135):
            outcomes = []
            for field, wrong in (
                ("project_ref", "PRJ-999"),
                ("project_ref", "OTHER"),
                ("site_ref", "SITE-X"),
                ("run_ref", "RUN-42"),
                ("episode_key", "EP-77"),
            ):
                fixture, _ = _mutate_case(
                    number,
                    lambda fx, f=field, w=wrong: fx["case_inputs"][
                        "typed_parameters"
                    ].update({"scope": {f: w}}),
                )
                out = _run_built_fixture(fixture, number)
                assert out["l1_disposition"] is None
                assert out.get("l2_counts") is None  # no unit, no risk/query counts
                outcomes.append({key: out[key] for key in _SEMANTIC_KEYS})
            assert len({repr(item) for item in outcomes}) == 1, number
            assert outcomes[0]["output_kind"] == "error"
            assert outcomes[0]["error_type"] == "D06ContractViolationError"
            assert outcomes[0]["error_stage"] == "pre_medical_output_validation"

    def test_scope_claim_conflict_gate_any_value(self):
        # The cutoff-scope gate opens for any conflicting snapshot/revision
        # claim spelling (frozen gate row 136 keeps its oracle leaves).
        outcomes = []
        for wrong in ("SNAP-999", "S-2", "SNX"):
            fixture, _ = _mutate_case(
                136,
                lambda fx, w=wrong: fx["case_inputs"]["typed_parameters"].update(
                    {"scope": {"accepted_snapshot_ref": w}}
                ),
            )
            out = _run_built_fixture(fixture, 136)
            assert out["gate_state"] == "open"
            assert out["gate_disposition"] == "not_evaluable"
            outcomes.append({key: out[key] for key in _SEMANTIC_KEYS})
        assert len({repr(item) for item in outcomes}) == 1

    def test_coherent_scope_rename_executes_preserving_semantics(self):
        # A semantically equivalent fixture whose ENTIRE scope and nested
        # references are coherently renamed executes through its declared
        # entrypoint: no pre-fixture integrity failure, no binding error,
        # identical medical semantics and trace; only the scope-derived
        # hashes change.
        case = MATRIX.by_number(1)
        renamed = copy.deepcopy(case.catalog_case)
        fx = renamed["fixture"]
        fx["scope"] = _remap_scope_values(fx["scope"])
        renamed["fixture"] = _remap_scope_values(fx)
        fx = renamed["fixture"]
        _rehash_all_embedded(fx)
        _fix_producer_payload_links(fx)
        _rehash_all_embedded(fx)
        out = _run_case_entrypoint(renamed, 1)
        frozen = case.assemble()
        assert out["output_kind"] == "result"
        assert out["error_type"] is None
        assert out["l1_disposition"] == frozen["l1_disposition"] == "negative"
        assert out["coverage_status"] == frozen["coverage_status"] == "covered"
        assert out["trace_edges"] == frozen["trace_edges"]
        assert (
            out["object_hashes"]["scope_hash"]
            != frozen["object_hashes"]["scope_hash"]
        )
        assert (
            out["domain_assertions"]["priority_resolution"]["projection_state"]
            == frozen["domain_assertions"]["priority_resolution"]["projection_state"]
        )

    def test_082_180_coherent_rename_passes_typed_binding(self):
        # Coherently renaming a wrong-subject fixture (scope AND the child
        # reference together) makes the typed binding pass: the binding is
        # scope-relative, never sentinel-relative.  Any remaining fail
        # closed is the frozen input-drift annotation behavior, not a
        # binding decision.
        for number, child in ((82, "ice"), (180, "tte")):
            renamed = copy.deepcopy(MATRIX.by_number(number).catalog_case)
            fx = renamed["fixture"]
            fx["scope"] = _remap_scope_values(fx["scope"])
            renamed["fixture"] = _remap_scope_values(fx)
            fx = renamed["fixture"]
            _rehash_all_embedded(fx)
            _fix_producer_payload_links(fx)
            _rehash_all_embedded(fx)
            out = _run_case_entrypoint(renamed, number)
            assert out["error_type"] != "D06BindingContractError", number
            assert out["error_stage"] != "typed_binding_validation", number
            assert out["output_kind"] == "error"
            if number == 180:
                # The TTE child evaluation was reached past the binding.
                assert "tte_precedence" in out["trace_edges"]


class TestFollowup4StableSourceAuthority:
    def test_2_domain_id_d07_synchronized_rehash_fails_closed(self):
        # A rewritten stable-core domain with a synchronized rehash of
        # core + public identity + risk binding must fail (domain
        # authority), never produce a successful result.
        def mutate(fx):
            core = fx["source_registries"]["d06_unit_stable_core"]
            core["domain_id"] = "D07"
            _rehash_embedded(core)
            pi = fx["public_r4_risk_identity"]
            pi["canonical_tuple"][1] = "D07"
            pi["public_identity_hash"] = "sha256:{0}".format(
                hashlib.sha256(
                    d06_canonical_json(pi["canonical_tuple"]).encode("utf-8")
                ).hexdigest()
            )
            pi["public_r4_risk_identity_id"] = "R4ID-{0}".format(
                pi["public_identity_hash"][-16:]
            )
            rb = fx["risk_binding"]
            rb["lineage_hash"] = "sha256:{0}".format(
                hashlib.sha256(
                    d06_canonical_json(
                        {k: v for k, v in rb.items() if k != "lineage_hash"}
                    ).encode("utf-8")
                ).hexdigest()
            )

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_synchronized_fake_source_fails_closed(self):
        # A fake stable source identity with a fully synchronized rehash
        # of core + public identity + risk binding must fail because the
        # source does not resolve to an accepted-current record.
        def mutate(fx):
            core = fx["source_registries"]["d06_unit_stable_core"]
            core["stable_source_record_id"] = "ASM-FAKE"
            _rehash_embedded(core)
            pi = fx["public_r4_risk_identity"]
            pi["stable_source_or_event_identity"] = "ASM-FAKE"
            pi["canonical_tuple"][4] = "ASM-FAKE"
            pi["public_identity_hash"] = "sha256:{0}".format(
                hashlib.sha256(
                    d06_canonical_json(pi["canonical_tuple"]).encode("utf-8")
                ).hexdigest()
            )
            pi["public_r4_risk_identity_id"] = "R4ID-{0}".format(
                pi["public_identity_hash"][-16:]
            )
            rb = fx["risk_binding"]
            rb["lineage_hash"] = "sha256:{0}".format(
                hashlib.sha256(
                    d06_canonical_json(
                        {k: v for k, v in rb.items() if k != "lineage_hash"}
                    ).encode("utf-8")
                ).hexdigest()
            )

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_source_assessment_status_drift_fails_closed(self):
        # The resolved source record must be accepted_current; a drifted
        # status fails closed.
        def mutate(fx):
            for assessment in fx["records"]["assessments"]:
                if assessment.get("id") == "ASM-W4-A":
                    assessment["record_status"] = "superseded"
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"


class TestFollowup4NestedSchema:
    def test_unknown_definition_field_fails_before_evaluation(self):
        # Unknown nested field in definitions.endpoint must fail at the
        # adapter boundary (verifier P2 NESTED_UNKNOWN_DEFINITION).
        case = MATRIX.by_number(2)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["definitions"]["endpoint"]["unknown_field"] = "x"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_unknown_assessment_field_fails_before_evaluation(self):
        # Unknown nested field in records.assessments[0] must fail at the
        # adapter boundary (verifier P2 NESTED_UNKNOWN_ASSESSMENT).
        case = MATRIX.by_number(2)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["records"]["assessments"][0]["unknown_field"] = "x"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_unknown_tt_event_field_fails_before_evaluation(self):
        case = MATRIX.by_number(196)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["source_registries"]["tte_source_events"][0][
            "unknown_field"
        ] = "x"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_unknown_enrollment_event_field_fails_before_evaluation(self):
        case = MATRIX.by_number(162)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["source_registries"]["enrollment_source_events"][0][
            "unknown_field"
        ] = "x"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_unknown_risk_binding_field_fails_before_evaluation(self):
        case = MATRIX.by_number(2)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["risk_binding"]["unknown_field"] = "x"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)

    def test_locator_value_type_drift_fails_before_evaluation(self):
        # A locator that is not a list of strings is an incompatible
        # nested value and fails before medical evaluation.
        case = MATRIX.by_number(2)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["records"]["assessments"][0][
            "source_locator_ids"
        ] = "NOT-A-LIST"
        with pytest.raises(D06ContractViolationError):
            ADAPTER.build(mutated)


class TestFollowup4TTEBinding:
    def test_196_event_time_drift_fails_closed(self):
        # A rehashed TTE event-time drift that no longer matches the
        # typed TTE records fails closed.
        def mutate(fx):
            event = fx["source_registries"]["tte_source_events"][1]
            event["effective_time_ref"] = "2026-02-10T09:00:00+08:00"
            _rehash_embedded(event)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_event_locator_removal_fails_closed(self):
        def mutate(fx):
            event = fx["source_registries"]["tte_source_events"][1]
            event["source_locator_ids"] = []
            _rehash_embedded(event)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_196_binding_source_registry_mismatch_fails_closed(self):
        # A rehashed binding reference that no longer resolves the typed
        # source registry fails closed.
        def mutate(fx):
            binding = fx["bindings"]["tte_precedence_binding"]
            binding["event_precedence_rule_id"] = "TTE-RULE-999"
            binding["lineage_hash"] = "sha256:{0}".format(
                hashlib.sha256(
                    d06_canonical_json(
                        {k: v for k, v in binding.items() if k != "lineage_hash"}
                    ).encode("utf-8")
                ).hexdigest()
            )

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"


class TestFollowup4EnrollmentBinding:
    def test_162_event_time_drift_fails_closed(self):
        # A rehashed enrollment event-time drift that no longer resolves
        # the decision's time symbol fails closed and suppresses Query.
        def mutate(fx):
            event = fx["source_registries"]["enrollment_source_events"][0]
            event["effective_time_ref"] = "TIME-MUTATED"
            _rehash_embedded(event)

        fixture, _ = _mutate_case(162, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert "query_context_outcomes" not in out["domain_assertions"]

    def test_162_event_locator_removal_fails_closed(self):
        def mutate(fx):
            event = fx["source_registries"]["enrollment_source_events"][0]
            event["source_locator_ids"] = []
            _rehash_embedded(event)

        fixture, _ = _mutate_case(162, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_162_decision_scope_drift_fails_closed(self):
        def mutate(fx):
            decision = fx["bindings"]["enrollment_context_decisions"][0]
            decision["run_ref"] = "SYN-WRONG-RUN"
            _rehash_embedded(decision)

        fixture, _ = _mutate_case(162, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06BindingContractError"
        assert out["error_stage"] == "typed_binding_validation"


class TestFollowup4JourneyProvenance:
    def test_markers_carry_source_locators_and_payload_hash(self):
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(31)
        projection = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        all_markers = (
            projection.markers
            + projection.pending_markers
            + projection.out_of_cutoff_markers
        )
        assert any(marker.source_locator_ids for marker in all_markers)
        assert all(marker.payload_hash for marker in all_markers)
        assert projection.payload_hash() is not None

    def test_locator_id_mutation_changes_projection_hash(self):
        from mm_r4.efficacy_projection import project_efficacy_journey

        case = MATRIX.by_number(31)
        base = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        fixture, _ = _mutate_case(
            31,
            lambda fx: fx["records"]["assessments"][0].update(
                {"source_locator_ids": ["SYN-LOC-MUTATED"]}
            ),
        )
        drifted = project_efficacy_journey(
            fixture, scope_status=None, unit_l1=None
        )
        # The content-addressed projection must change; the generic
        # payload is never retained unchanged for drifted locators.
        assert drifted.payload_hash() != base.payload_hash()
        assert any(
            "SYN-LOC-MUTATED" in marker.source_locator_ids
            for marker in drifted.markers + drifted.out_of_cutoff_markers
        )

    def test_locator_removal_suppresses_payload(self):
        # With no validated source locators anywhere, the audience
        # payload is suppressed with the exact error state.
        def mutate(fx):
            for assessment in fx["records"]["assessments"]:
                assessment["source_locator_ids"] = []

        fixture, _ = _mutate_case(31, mutate)
        out = validate_audience_projection(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out.get("audience_payload") is None
        assert out.get("audience_payload_absent") is True


# ---------------------------------------------------------------------------
# followup5: cross-authority/provenance escapes
# ---------------------------------------------------------------------------


class TestFollowup5TTEAuthority:
    def test_196_registry_target_event_ref_drift_fails(self):
        def mutate(fx):
            reg = fx["source_registries"]["tte_source_registry"]
            reg["target_event_ref"] = "EV-MUTATED"
            _rehash_embedded(reg)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_registry_event_time_ref_drift_fails(self):
        def mutate(fx):
            reg = fx["source_registries"]["tte_source_registry"]
            reg["event_time_ref"] = "2027-01-01T09:00:00+08:00"
            _rehash_embedded(reg)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_registry_tie_policy_drift_fails(self):
        def mutate(fx):
            reg = fx["source_registries"]["tte_source_registry"]
            reg["tie_policy"] = "boundary"
            _rehash_embedded(reg)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_registry_origin_time_ref_drift_fails(self):
        def mutate(fx):
            reg = fx["source_registries"]["tte_source_registry"]
            reg["origin_time_ref"] = "2027-06-01T09:00:00+08:00"
            _rehash_embedded(reg)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_196_registry_locator_removal_fails(self):
        def mutate(fx):
            fx["source_registries"]["tte_source_registry"]["source_locator_ids"] = []
            _rehash_embedded(fx["source_registries"]["tte_source_registry"])

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_196_binding_identity_removal_fails(self):
        def mutate(fx):
            binding = fx["bindings"]["tte_precedence_binding"]
            binding["stable_source_identity"] = ""
            _rehash_lineage(binding)

        fixture, _ = _mutate_case(196, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"


class TestFollowup5AssessmentAuthority:
    def test_2_rehashed_time_drift_fails(self):
        """A rehashed assessment time drift fails because the inventory/ref
        producer_payload_hash no longer matches the assessment lineage."""
        def mutate(fx):
            for a in fx["records"]["assessments"]:
                if a.get("id") == "ASM-W4-A":
                    a["time"] = "2026-02-01T09:00:00+08:00"
                    _rehash_lineage(a)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_rehashed_locator_drift_fails(self):
        def mutate(fx):
            for a in fx["records"]["assessments"]:
                if a.get("id") == "ASM-W4-A":
                    a["source_locator_ids"] = ["SYN-LOC-MUTATED"]
                    _rehash_lineage(a)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_rehashed_recall_period_drift_fails(self):
        def mutate(fx):
            for a in fx["records"]["assessments"]:
                if a.get("id") == "ASM-W4-A":
                    a["actual_recall_period"] = "14_days"
                    _rehash_lineage(a)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_31_locator_mutation_suppresses_journey_payload(self):
        """An assessment locator mutation in the journey-pipeline fails
        the assessment authority check, so the payload is never equal."""
        def mutate(fx):
            for a in fx["records"]["assessments"]:
                a["source_locator_ids"] = ["SYN-LOC-MUT"]
                _rehash_lineage(a)

        fixture, _ = _mutate_case(31, mutate)
        out = validate_audience_projection(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"


class TestFollowup5EnrollmentAuthority:
    def test_162_rule_locator_removal_fails(self):
        def mutate(fx):
            fx["source_registries"]["enrollment_rule_registry"][
                "source_locator_ids"
            ] = []
            _rehash_embedded(fx["source_registries"]["enrollment_rule_registry"])

        fixture, _ = _mutate_case(162, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"

    def test_162_decision_producer_domain_drift_fails(self):
        def mutate(fx):
            fx["bindings"]["enrollment_context_decisions"][0][
                "producer_domain"
            ] = "D09"
            _rehash_embedded(fx["bindings"]["enrollment_context_decisions"][0])

        fixture, _ = _mutate_case(162, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_162_variant_context_mismatch_fails(self):
        """The by-context mapping and the decision query_context must agree
        bidirectionally; a drift breaks the reference relationship."""
        case = MATRIX.by_number(162)
        mutated = copy.deepcopy(case.catalog_case)
        mutated["fixture"]["bindings"]["enrollment_context_decisions"][1][
            "query_context"
        ] = "enrollment_not_occurred"
        _rehash_embedded(
            mutated["fixture"]["bindings"]["enrollment_context_decisions"][1]
        )
        out = _run_case_entrypoint(mutated, 162)
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

# ---------------------------------------------------------------------------
# followup6: D05 semantic cross-authority + direct serializer provenance
# ---------------------------------------------------------------------------


class TestFollowup6D05Authority:
    def test_2_fk_producer_payload_rehash_fails(self):
        """A rehashed foreign-key producer payload must fail because it no
        longer authenticates the assessment lineage."""
        def mutate(fx):
            for fk in fx["source_registries"]["d05_assessment_foreign_keys"]:
                if fk.get("source_record_id") == "ASM-W4-A":
                    fk["producer_payload_hash"] = "sha256:" + "0" * 64
                    _rehash_embedded(fk)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_fk_actual_time_rehash_fails(self):
        def mutate(fx):
            for fk in fx["source_registries"]["d05_assessment_foreign_keys"]:
                if fk.get("source_record_id") == "ASM-W4-A":
                    fk["actual_time_ref"] = "2027-01-01T09:00:00+08:00"
                    _rehash_embedded(fk)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_assessment_d05_unit_rehash_fails(self):
        def mutate(fx):
            for a in fx["records"]["assessments"]:
                if a.get("id") == "ASM-W4-A":
                    a["d05_unit_id"] = "D05-UNIT-MUT"
                    _rehash_lineage(a)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_ref_occurrence_disposition_rehash_fails(self):
        def mutate(fx):
            for r in fx["bindings"]["d05_refs"]:
                if r.get("source_record_id") == "ASM-W4-A":
                    r["occurrence_disposition"] = "positive"
                    _rehash_embedded(r)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_inventory_assignment_rehash_fails(self):
        def mutate(fx):
            for inv in fx["source_registries"]["accepted_d05_assessment_inventory"]:
                if inv.get("source_record_id") == "ASM-W4-A":
                    inv["assignment_status"] = "duplicate"
                    _rehash_embedded(inv)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_item_raw_value_rehash_fails(self):
        """A rehashed assessment item value fails the typed item-values
        authority."""
        def mutate(fx):
            for item in fx["records"]["assessment_items"]:
                if item.get("item_record_id") == "ITEM-W4-A-I1":
                    item["raw_value"] = "99"
                    item["normalized_value"] = "99"
                    _rehash_content(item)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"

    def test_2_item_locator_removal_rehash_fails(self):
        def mutate(fx):
            for item in fx["records"]["assessment_items"]:
                if item.get("item_record_id") == "ITEM-W4-A-I1":
                    item["source_locator_ids"] = []
                    _rehash_content(item)
                    break

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"


# ---------------------------------------------------------------------------
# followup7: embedded-hash validation of D05 content-addressed authorities
# ---------------------------------------------------------------------------


class TestFollowup7D05EmbeddedHash:
    def test_inventory_item_hash_tamper_fails_closed(self):
        """A hash-only tamper on an AcceptedD05AssessmentInventoryItem must
        fail closed: the embedded hash must match a recomputation over its
        own typed fields before it is consumed as authority."""
        def mutate(fx):
            fx["source_registries"]["accepted_d05_assessment_inventory"][0][
                "hash"
            ] = "sha256:" + "0" * 64

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_foreign_key_hash_tamper_fails_closed(self):
        """A hash-only tamper on a D05AssessmentForeignKey must fail closed
        through the contract-violation path."""
        def mutate(fx):
            fx["source_registries"]["d05_assessment_foreign_keys"][0][
                "hash"
            ] = "sha256:" + "0" * 64

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"

    def test_d05_ref_hash_tamper_fails_closed(self):
        """Adjacent: a hash-only tamper on a D05AssessmentBindingRef must
        fail closed as well."""
        def mutate(fx):
            fx["bindings"]["d05_refs"][0]["hash"] = "sha256:" + "0" * 64

        fixture, _ = _mutate_case(2, mutate)
        out = evaluate_efficacy_fixture(fixture).to_plain()
        assert out["output_kind"] == "error"
        assert out["error_type"] == "D06ContractViolationError"
        assert out["error_stage"] == "pre_medical_output_validation"


class TestFollowup6SerializerProvenance:
    def test_stale_marker_hash_raises(self):
        from dataclasses import replace as _replace

        from mm_r4.efficacy import ProjectionContractError
        from mm_r4.efficacy_projection import (
            journey_audience_payload_from_projection,
            project_efficacy_journey,
        )

        case = MATRIX.by_number(31)
        projection = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        marker = projection.markers[0]
        stale = _replace(marker, source_locator_ids=("SYN-LOC-STALE",))
        mutated = _replace(projection, markers=(stale,) + projection.markers[1:])
        with pytest.raises(ProjectionContractError):
            journey_audience_payload_from_projection(mutated)

    def test_jump_without_locators_raises(self):
        from dataclasses import replace as _replace

        from mm_r4.efficacy import ProjectionContractError
        from mm_r4.efficacy_projection import (
            journey_audience_payload_from_projection,
            project_efficacy_journey,
        )

        case = MATRIX.by_number(31)
        projection = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        marker = projection.markers[0]
        stale = _replace(
            marker,
            source_locator_ids=(),
            payload_hash=None,
            source_jump_target="受试者历时资料",
        )
        mutated = _replace(projection, markers=(stale,) + projection.markers[1:])
        with pytest.raises(ProjectionContractError):
            journey_audience_payload_from_projection(mutated)

    def test_valid_projection_serializes_frozen_payload(self):
        from mm_r4.efficacy_projection import (
            journey_audience_payload_from_projection,
            project_efficacy_journey,
        )

        case = MATRIX.by_number(31)
        projection = project_efficacy_journey(
            case.build_runtime_fixture(), scope_status=None, unit_l1=None
        )
        payload = journey_audience_payload_from_projection(projection)
        assert payload == {
            "payload_kind": "journey",
            "payload_schema_version": "d06-journey-audience-v1",
            "display_text": "查看访视轴与来源依据",
            "visit_axis_label": "访视轴",
            "endpoint_lanes": [
                {
                    "endpoint_label": "主要疗效终点",
                    "marker_label": "查看评估记录",
                    "source_jump_target": "受试者历时资料",
                }
            ],
        }


class TestErrorClassRegression:
    """Frozen error rows must retain their exact error classes/stages --
    never degraded into an unrelated generic contract error."""

    @pytest.mark.parametrize(
        "number,error_type,error_stage",
        [
            (18, "D06ContractViolationError", "pre_medical_output_validation"),
            (66, "OwnerScopeContractError", "owner_scope_validation"),
            (82, "D06BindingContractError", "typed_binding_validation"),
            (121, "AudiencePayloadValidationError", "audience_payload_validation"),
            (161, "ProjectionContractError", "projection_validation"),
            (170, "ChallengeAssertionContractError", "assertion_manifest_validation"),
            (204, "SchemaContractError", "gate_binding_validation"),
            (214, "ChallengeRegistryIntegrityError", "pre_fixture_integrity"),
        ],
    )
    def test_frozen_error_rows_retain_exact_classes(
        self, number, error_type, error_stage
    ):
        out = MATRIX.by_number(number).assemble()
        assert out["output_kind"] == "error"
        assert out["error_type"] == error_type
        assert out["error_stage"] == error_stage
        assert out["domain_assertions"]["priority_resolution"][
            "projection_state"
        ] == "resolver_result_only"


def _leaves(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _leaves(item, prefix + (str(key),))
    else:
        yield prefix, value
