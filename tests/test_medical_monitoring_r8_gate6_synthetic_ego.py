"""R8 G6 synthetic fixture, binding, notification, and user-task tests.

These tests stay offline and in memory.  They do not start an app/browser,
connect to a network, call a model, or access a real project root.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import synthetic_ego as g  # noqa: E402


def test_cross_domain_fixture_has_required_shape_and_deterministic_digest() -> None:
    first = g.build_synthetic_fixture()
    second = g.build_synthetic_fixture()

    assert first == second
    assert first["fixture_digest"] == second["fixture_digest"]
    assert first["binding_digest"] == first["profile_binding_digest"]
    assert first["counts"] == {
        "projects": 2,
        "centers": 3,
        "subjects": 12,
        "visits": 48,
        "events": 96,
        "analysis_inputs": 6,
        "flow_rows": 30,
        "risk_scenarios": 8,
        "domain_counts": {domain: 12 for domain in g.DOMAINS},
    }
    assert first["analysis_modes"] == list(g.ANALYSIS_MODES)
    assert {row["risk_state"] for row in first["risk_scenarios"]} == set(g.RISK_STATES)
    assert first["journey"]["orientation"] == "horizontal"
    dense = first["challenge"]["dense_same_day"]
    dense_events = [event for event in first["events"] if event["event_ref"] in dense["event_refs"]]
    assert dense["event_count"] == len(g.DOMAINS)
    assert set(event["domain"] for event in dense_events) == set(g.DOMAINS)
    assert len({event["occurred_on"] for event in dense_events}) == 1
    assert first["challenge"]["flow_shape"] == {
        "has_split": True,
        "has_merge": True,
        "has_zero": True,
        "has_center_differences": True,
    }
    assert first["challenge"]["long_label_min_chars"] >= 20
    assert first["table_totals"]["domain_counts"] == {domain: 12 for domain in g.DOMAINS}
    assert first["table_totals"]["center_subject_counts"]["synthetic-project-alpha"] != (
        first["table_totals"]["center_subject_counts"]["synthetic-project-beta"]
    )
    assert len(first["flow_totals"]) == 6
    assert all(row["consent_to_screening"] == row["terminal_total"] for row in first["flow_totals"])
    assert first["section_15_4"]["evidence_mode"] == "required_task_specification"
    assert first["section_15_4"]["task_spec_digest"] == g.TASK_SPEC_DIGEST
    assert any(row["count"] == 0 for row in first["flow_rows"])
    assert first["section_15_4"]["task_count"] == 13


def test_fixture_validation_rejects_digest_or_scope_tampering() -> None:
    fixture = g.build_synthetic_fixture()

    forged = copy.deepcopy(fixture)
    forged["events"][0]["domain"] = "UNKNOWN"
    with pytest.raises(g.SyntheticEgoError, match="fixture_digest_mismatch|event.domain_invalid"):
        g.validate_synthetic_fixture(forged)

    forged = copy.deepcopy(fixture)
    forged["subjects"][0]["risk_state"] = "not-a-risk-state"
    with pytest.raises(g.SyntheticEgoError, match="fixture_digest_mismatch|subject.risk_state_invalid"):
        g.validate_synthetic_fixture(forged)


def test_binding_freezes_fixture_and_rejects_non_synthetic_provider() -> None:
    fixture = g.build_synthetic_fixture()
    binding = g.build_synthetic_binding(
        fixture,
        "synthetic-project-alpha",
        "periodic_increment",
    )

    assert binding["fixture_digest"] == fixture["fixture_digest"]
    assert binding["fixture_binding_digest"] == fixture["binding_digest"]
    assert binding["adapter_kind"] == "mock_recorded"
    assert binding["provider"].startswith("synthetic-")
    assert binding["model"].startswith("synthetic-")
    assert binding["profile_binding_digest"] == fixture["profile_binding_digest"]
    assert binding["profile_binding_digest"] != binding["binding_digest"]
    assert g.validate_synthetic_binding(binding, fixture=fixture) == binding

    with pytest.raises(g.SyntheticEgoError, match="non_synthetic_provider_or_model"):
        g.build_synthetic_binding(
            fixture,
            "synthetic-project-alpha",
            provider="real-provider",
        )

    forged = copy.deepcopy(binding)
    forged["fixture_digest"] = "sha256:" + "f" * 64
    with pytest.raises(g.SyntheticEgoError, match="binding_digest_mismatch|binding_fixture_digest_mismatch"):
        g.validate_synthetic_binding(forged, fixture=fixture)


def test_recorded_adapter_is_idempotent_and_never_falls_back() -> None:
    fixture = g.build_synthetic_fixture()
    binding = g.build_synthetic_binding(fixture, "synthetic-project-alpha")
    adapter = g.SyntheticRecordedAdapter(fixture, binding)

    first = adapter.execute_analysis(binding)
    second = adapter.execute_analysis(binding)

    assert first == second
    assert len(adapter.analysis_calls) == 1
    assert adapter.real_model_calls == ()
    assert adapter.external_calls == ()
    assert adapter.fallback_attempts == ()
    assert adapter.adapter_descriptor["network_allowed"] is False
    with pytest.raises(g.SyntheticEgoError, match="fallback_forbidden"):
        adapter.attempt_fallback("test")
    assert len(adapter.fallback_attempts) == 1


def test_notification_matrix_covers_36_rows_and_six_blocked_paths() -> None:
    fixture = g.build_synthetic_fixture()
    matrix = g.build_notification_matrix(fixture)

    assert matrix["row_count"] == 36
    assert len(matrix["rows"]) == len(g.TERMINAL_STATUSES) * len(g.CAPABILITY_STATES)
    assert {
        (row["terminal_status"], row["capability_state"]) for row in matrix["rows"]
    } == {
        (terminal_status, capability_state)
        for terminal_status in g.TERMINAL_STATUSES
        for capability_state in g.CAPABILITY_STATES
    }
    assert {
        row["channel_evidence"]
        for row in matrix["rows"]
        if row["capability_state"] == "authorized"
    } == {"presented"}
    assert all(
        row["channel_evidence"] == "unknown"
        for row in matrix["rows"]
        if row["capability_state"] != "authorized"
    )
    complete_authorized = next(
        row
        for row in matrix["rows"]
        if row["terminal_status"] == "complete" and row["capability_state"] == "authorized"
    )
    failed_authorized = next(
        row
        for row in matrix["rows"]
        if row["terminal_status"] == "failed" and row["capability_state"] == "authorized"
    )
    assert complete_authorized["system_attempt_count"] == 1
    assert failed_authorized["system_attempt_count"] == 1
    assert all(row["in_app_persistent"] for row in matrix["rows"])
    assert all(row["run_side_effect_count"] == 0 for row in matrix["rows"])
    assert {row["case"] for row in matrix["negative_navigation_cases"]} == {
        "old_revision",
        "binding_drift",
        "source_manifest_drift",
        "output_manifest_drift",
        "target_deleted",
        "target_inaccessible",
    }
    assert all(row["status"] == "blocked" for row in matrix["negative_navigation_cases"])
    assert g.replay_notification_matrix(matrix, fixture=fixture).valid is True


def test_notification_matrix_replay_rejects_forged_navigation_or_evidence() -> None:
    fixture = g.build_synthetic_fixture()
    matrix = g.build_notification_matrix(fixture)

    forged = copy.deepcopy(matrix)
    forged["rows"][0]["run_side_effect_count"] = 1
    with pytest.raises(g.SyntheticEgoError, match="notification_matrix_digest_mismatch"):
        g.validate_notification_matrix(forged, fixture=fixture)

    forged = copy.deepcopy(matrix)
    forged["rows"][0]["channel_evidence"] = "accepted_by_platform"
    forged["matrix_digest"] = g._digest_without(forged, "matrix_digest")
    with pytest.raises(g.SyntheticEgoError, match="notification_matrix_channel_evidence_mismatch"):
        g.validate_notification_matrix(forged, fixture=fixture)


def test_application_task_specification_requires_explicit_user_actions() -> None:
    fixture = g.build_synthetic_fixture()
    binding = g.build_synthetic_binding(fixture, "synthetic-project-alpha")
    specification = g.build_user_task_evidence(fixture, binding)

    assert specification["task_count"] == 13
    assert specification["evidence_kind"] == "required_task_specification"
    assert specification["status"] == "awaiting_user_actions"
    assert specification["task_spec_digest"] == g.TASK_SPEC_DIGEST
    assert [task["key"] for task in specification["tasks"]] == list(g.TASK_KEYS)
    assert all("result" not in task and "steps" not in task for task in specification["tasks"])
    assert specification["tasks"][9]["initial_state"]["files"]["credential_values"] == 0
    assert specification["tasks"][9]["initial_state"]["files"]["environment_members"] == 0
    assert all(
        "/" not in action["visible_result"]
        for task in specification["tasks"]
        for action in task["actions"]
    )
    replay = g.replay_user_task_evidence(specification, fixture=fixture, binding=binding)
    assert replay.valid is True
    assert replay.status == "specification_valid"

    recorder = g.SyntheticUserTaskEvidenceRecorder(fixture, binding)
    for spec in g.TASK_SPECS:
        recorder.start_task(spec["key"])
        for action in spec["actions"]:
            recorder.record_step(
                action=action["action"],
                visible_result=action["visible_result"],
                file_state=spec["initial_state"]["files"],
                restart_required=action["restart_required"],
                negative_assertions=spec["negative_assertions"],
            )
        recorder.finish_task(
            summary=spec["expected_user_result"],
            restart_points=spec["restart_points"],
            negative_assertions=spec["negative_assertions"],
            cleanup=spec["cleanup"],
            file_state_summary=spec["initial_state"]["files"],
        )
    runtime_evidence = recorder.build_manifest()
    assert runtime_evidence["evidence_kind"] == "application_internal_recorded"
    assert runtime_evidence["status"] == "passed"
    assert all(task["result"] == "passed" for task in runtime_evidence["tasks"])
    assert g.replay_user_task_evidence(
        runtime_evidence, fixture=fixture, binding=binding
    ).valid is True

    forged = copy.deepcopy(specification)
    forged["status"] = "passed"
    forged["manifest_digest"] = g._digest_without(forged, "manifest_digest")
    assert g.replay_user_task_evidence(
        forged,
        fixture=fixture,
        binding=binding,
    ).valid is False

def test_bundle_replays_fixture_binding_matrix_and_task_evidence() -> None:
    bundle = g.build_synthetic_audience_bundle()
    checked = g.validate_synthetic_audience_bundle(bundle)

    assert checked["schema"] == g.BUNDLE_SCHEMA
    assert checked["fixture"]["counts"]["projects"] == 2
    assert checked["notification_matrix"]["row_count"] == 36
    assert checked["binding_role"] == "backward_compatible_default_alpha_full"
    assert checked["run_binding_count"] == 6
    assert {
        (row["project_ref"], row["analysis_mode"])
        for row in checked["run_bindings"]
    } == {
        (project_ref, analysis_mode)
        for project_ref in ("synthetic-project-alpha", "synthetic-project-beta")
        for analysis_mode in g.ANALYSIS_MODES
    }
    assert len({row["binding_digest"] for row in checked["run_bindings"]}) == 6
    assert checked["binding"] == next(
        row
        for row in checked["run_bindings"]
        if row["project_ref"] == "synthetic-project-alpha"
        and row["analysis_mode"] == "full"
    )
    assert checked["user_task_evidence"]["status"] == "awaiting_user_actions"
    assert checked["user_task_evidence"]["task_spec_digest"] == g.TASK_SPEC_DIGEST
    assert checked["user_task_evidence"]["task_count"] == 13


def test_run_binding_matrix_rejects_missing_duplicate_and_stale_rows() -> None:
    bundle = g.build_synthetic_audience_bundle()

    missing = copy.deepcopy(bundle)
    missing["run_bindings"].pop()
    with pytest.raises(g.SyntheticEgoError, match="bundle_run_binding_matrix_mismatch"):
        g.validate_synthetic_audience_bundle(missing)

    duplicate = copy.deepcopy(bundle)
    duplicate["run_bindings"][-1] = copy.deepcopy(duplicate["run_bindings"][0])
    duplicate["bundle_digest"] = g._digest_without(duplicate, "bundle_digest")
    with pytest.raises(g.SyntheticEgoError, match="bundle_duplicate_run_binding_pair"):
        g.validate_synthetic_audience_bundle(duplicate)

    stale = copy.deepcopy(bundle)
    stale["run_bindings"][0]["output_manifest_digest"] = "sha256:" + "0" * 64
    stale["run_bindings"][0]["binding_digest"] = g._digest_without(
        stale["run_bindings"][0], "binding_digest"
    )
    stale["bundle_digest"] = g._digest_without(stale, "bundle_digest")
    with pytest.raises(g.SyntheticEgoError, match="binding_output_manifest_mismatch"):
        g.validate_synthetic_audience_bundle(stale)

    forged = copy.deepcopy(bundle)
    forged["run_bindings"][0] = g.build_synthetic_binding(
        forged["fixture"],
        "synthetic-project-alpha",
        "full",
        run_ref="synthetic-run-forged",
    )
    forged["bundle_digest"] = g._digest_without(forged, "bundle_digest")
    with pytest.raises(g.SyntheticEgoError, match="bundle_run_binding_direct_mismatch"):
        g.validate_synthetic_audience_bundle(forged)
