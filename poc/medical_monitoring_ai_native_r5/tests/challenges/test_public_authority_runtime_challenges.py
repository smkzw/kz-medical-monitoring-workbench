"""Challenge-surface coverage for accepted R5-S5 authority registries."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

_R5 = Path(__file__).resolve().parents[2]
_WORKSPACE = Path(__file__).resolve().parents[4]
if str(_R5 / "tests") not in sys.path:
    sys.path.insert(0, str(_R5 / "tests"))

from mm_r5.aemh_match_history_public import (  # noqa: E402
    build_aemh_match_history_authority,
    validate_aemh_match_history_authority,
)
from mm_r5.public_authority_common import (  # noqa: E402
    PublicAuthorityConstructionError,
    canonical_sha256,
    without_field,
)
from mm_r5.subject_temporal_public import (  # noqa: E402
    build_subject_temporal_authority,
    validate_subject_temporal_authority,
)
from public_authority_runtime_fixtures import (  # noqa: E402
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)

_V042 = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2"
)
_TEMPORAL_V02 = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reseal(bundle, source):
    candidate = replace(bundle, source=source, bundle_content_identity="0" * 64)
    return replace(
        candidate,
        bundle_content_identity=canonical_sha256(
            without_field(candidate, "bundle_content_identity")
        ),
    )


def test_192_error_replays_are_complete_and_candidate_independent() -> None:
    registry = _json(_V042 / "error_replay_execution_registry.json")
    rows = registry["rows"]
    assert registry["row_count"] == 192
    assert len(rows) == 192
    assert registry["pre_delta_count"] == 170
    assert registry["accepted_error_replay_delta_count"] == 22
    assert Counter(row["replay_plane"] for row in rows) == Counter({
        "accepted_pre_delta": 170,
        "accepted_error_replay_delta": 22,
    })

    accepted_sources = {
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json",
        "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json",
        "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json",
        "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/challenge_registry.json",
    }
    for row in rows:
        assert row["candidate_matrix_metadata_forbidden"] is True
        assert row["generator_replay_executed"] is True
        assert row["source_challenge_ref"].split("#", 1)[0] in accepted_sources
        assert len(row["execution_binding_digest"]) == 64
        assert row["mutation"].get("op", row["mutation"].get("operation"))
        assert isinstance(row["reseal"], dict)
        assert row["observed_ordered_issue_codes"]
        assert len(row["observed_ordered_issue_codes"]) == len(
            row["observed_ordered_issues"]
        )
        assert row["observed_ordered_issue_codes"] == [
            issue["code"] for issue in row["observed_ordered_issues"]
        ]
        assert {
            row["code"],
            row["path"],
            row["origin"],
            row["priority"],
            row["message"],
        } <= {
            value
            for issue in row["observed_ordered_issues"]
            for value in (
                issue["code"],
                issue["path"],
                issue["origin"],
                issue["priority"],
                issue["message"],
            )
        }


def test_226_runtime_reject_traces_rebuild_issue_digests() -> None:
    registry = _json(_V042 / "runtime_reject_metadata_registry.json")
    rows = registry["rows"]
    assert registry["row_count"] == 226
    assert len(rows) == 226
    assert all(row["generator_reject_executed"] is True for row in rows)
    assert all(
        row["issue_metadata_source"]
        == "independently_reconstructed_accepted_error_authority"
        for row in rows
    )
    assert all(row["candidate_error_matrix_backfill_forbidden"] is True for row in rows)
    assert len({row["trace_identity"] for row in rows}) == 226
    for row in rows:
        assert row["ordered_issue_codes"] == [
            issue["code"] for issue in row["issue_objects"]
        ]
        assert row["issue_object_digest"] == hashlib.sha256(
            json.dumps(
                row["issue_objects"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        assert row["issue_objects"]


def test_58_active_gates_keep_all_families_and_primary_bindings() -> None:
    registry = _json(_V042 / "active_gate_execution_registry.json")
    rows = registry["rows"]
    assert registry["row_count"] == 58
    assert len(rows) == 58
    assert registry["accepted_governance_count"] == 22
    assert registry["accepted_error_delta_count"] == 22
    assert registry["v042_contract_attack_count"] == 14
    assert Counter(row["family"] for row in rows) == Counter({
        "accepted_parent_governance": 22,
        "accepted_error_delta": 22,
        "leaf_fake_typed_plane": 1,
        "leaf_recipe_packet_mutation": 1,
        "leaf_cutoff_digest_mutation": 1,
        "leaf_authority_root_mutation": 1,
        "error_fake_gate_replacement": 1,
        "error_fake_base_replacement": 1,
        "error_fake_mutation_replacement": 1,
        "error_fake_reseal_replacement": 1,
        "gate_fake_spec_count_preserve": 1,
        "gate_fake_governance_replacement": 1,
        "gate_fake_delta_replacement": 1,
        "reject_candidate_backfill": 1,
        "reject_issue_object_fabrication": 1,
        "candidate_as_input_authority": 1,
    })
    assert len({row["attack_id"] for row in rows}) == 58
    assert all(row["generator_executed"] is True for row in rows)
    assert all(len(row["execution_binding_digest"]) == 64 for row in rows)
    assert all(row["expected_exact_issue"] for row in rows)


def test_236_temporal_runtime_specs_are_unique_and_reconciled() -> None:
    registry = _json(_TEMPORAL_V02 / "trace_realization_registry.json")
    rows = registry["records"]
    assert registry["spec_count"] == 236
    assert registry["unique_trace_count"] == 236
    assert registry["alias_count"] == 0
    assert len(rows) == 236
    assert len({row["trace_identity"] for row in rows}) == 236
    assert len({row["source_case_ref"] for row in rows}) == 236
    assert Counter(row["contract"] for row in rows) == Counter({
        "subject-temporal-public-v1": 143,
        "aemh-match-history-public-v1": 93,
    })
    assert Counter(row["expected_disposition"] for row in rows) == Counter({
        "reject": 226,
        "accept": 10,
    })
    assert Counter(row["observed_disposition"] for row in rows) == Counter({
        "reject": 226,
        "accept": 10,
    })
    assert registry["counts"] == {
        "subject-temporal-public-v1": {"inherited": 48, "specific": 95},
        "aemh-match-history-public-v1": {"inherited": 16, "specific": 77},
    }
    for row in rows:
        assert row["expected_disposition"] == row["observed_disposition"]
        assert row["operation_count"] == len(row["reseal_order"])
        assert row["exact_path"].startswith("/")
        assert row["realized_mutation"].get(
            "op", row["realized_mutation"].get("operation")
        )
        assert row["post_authority_input_content_identity"]
        assert row["post_graph_content_hash"]


def test_272_192_and_236_rows_are_inventory_only_and_runtime_gate_is_executed() -> None:
    """Registry digests are inventory; typed builders remain the executable gate."""
    leaf_rows = _json(_V042 / "leaf_execution_registry.json")["rows"]
    replay_rows = _json(_V042 / "error_replay_execution_registry.json")["rows"]
    temporal_rows = _json(_TEMPORAL_V02 / "trace_realization_registry.json")["records"]

    # These registries carry pointers, hashes, and mutation metadata, not an
    # AuthorityBundleV02/source graph.  They must not be mistaken for runtime
    # execution inputs.
    executable_graph_keys = {
        "authority_bundle",
        "authority_graph",
        "source_graph",
        "typed_input",
        "typed_authority",
    }
    assert all(not executable_graph_keys.intersection(row) for row in leaf_rows)
    assert all(not executable_graph_keys.intersection(row) for row in replay_rows)
    assert all(not executable_graph_keys.intersection(row) for row in temporal_rows)
    assert {row["base_input_ref"] for row in temporal_rows} >= {
        "subject_temporal_valid_base",
        "aemh_match_history_valid_base",
    }

    subject_authority = build_subject_authority_bundle()
    subject_packet = build_subject_temporal_authority(subject_authority)
    assert validate_subject_temporal_authority(subject_packet, subject_authority).ok
    subject_source = replace(
        subject_authority.source,
        axis=replace(subject_authority.source.axis, mode=["calendar"]),
    )
    with pytest.raises(PublicAuthorityConstructionError) as subject_error:
        build_subject_temporal_authority(_reseal(subject_authority, subject_source))
    assert subject_error.value.result.primary_code == "PUB_TYPE_MISMATCH"

    aemh_authority = build_aemh_authority_bundle()
    aemh_packet = build_aemh_match_history_authority(aemh_authority)
    assert validate_aemh_match_history_authority(aemh_packet, aemh_authority).ok
    aemh_source = replace(
        aemh_authority.source,
        decision_records=(
            replace(aemh_authority.source.decision_records[0], match_state="ambiguous"),
        ) + aemh_authority.source.decision_records[1:],
    )
    with pytest.raises(PublicAuthorityConstructionError) as aemh_error:
        build_aemh_match_history_authority(_reseal(aemh_authority, aemh_source))
    assert aemh_error.value.result.primary_code == "AEMH_MATCH_EVIDENCE_MISSING"


@pytest.mark.parametrize(
    "registry_name",
    (
        "leaf_execution_registry.json",
        "error_replay_execution_registry.json",
        "active_gate_execution_registry.json",
        "runtime_reject_metadata_registry.json",
    ),
)
def test_v042_registry_rows_do_not_use_candidate_as_authority(registry_name: str) -> None:
    registry = _json(_V042 / registry_name)
    assert registry["contract_id"] == (
        "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4.2"
    )
    assert registry["forbidden"]
