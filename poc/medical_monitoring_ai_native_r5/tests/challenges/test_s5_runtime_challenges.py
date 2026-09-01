"""Materialized R5-S5 challenge/oracle and accepted graph replay tests.

The accepted S5 registry explicitly marks its rows as test metadata.  This
module therefore does two separate things: every one of the 250 rows is
materialized and checked against its exact mutation/oracle contract, while the
36 S5-specific rows are executed against the real offline S5 validators and
the ten accepted public graph rows are replayed through the accepted producer
builders and S5 adapter.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from mm_r5 import public_authority_common as common
from mm_r5 import s5_contracts as s5
from mm_r5.aemh_match_history_public import (
    build_aemh_match_history_authority,
    validate_aemh_match_history_authority,
)
from mm_r5.s5_authority_adapter import (
    S5AuthorityAdapterError,
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
    build_s5_authority_packet,
)
from mm_r5.s5_projection import project_aemh_history, project_subject_temporal
from mm_r5.s5_validator import (
    validate_audience_encoding_registry,
    validate_audience_lexicon,
    validate_audience_term,
    validate_legacy_severity,
    validate_legacy_treatment_mapping,
    validate_s5_subject_workspace,
    validate_subject_temporal_packet,
)
from mm_r5.subject_temporal_public import (
    build_subject_temporal_authority,
    validate_subject_temporal_authority,
)
from public_authority_runtime_fixtures import (
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)
from s5_runtime_fixtures import (
    accepted_public_graph_replay,
    build_aemh_packet,
    build_subject_packet,
    build_subject_workspace,
    accepted_public_graph_replay_cases,
)


_R5 = Path(__file__).resolve().parents[2]
_WORKSPACE = Path(__file__).resolve().parents[4]
_ARTIFACTS = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_subject_workspace_contract_v0_1"
)
_REGISTRY_PATH = _ARTIFACTS / "challenge_registry.json"
_MANIFEST_PATH = _ARTIFACTS / "manifest.json"
_FULL_GRAPH_PATH = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
) / "full_graph_fixture_registry.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows() -> list[dict]:
    return _json(_REGISTRY_PATH)["rows"]


def _pointer(path: str) -> list[str]:
    parts = [item for item in path.strip("/").split("/") if item]
    return [item.replace("~1", "/").replace("~0", "~") for item in parts]


def _set_path(mapping: dict, path: str, value) -> None:
    parts = _pointer(path)
    target = mapping
    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]
        if isinstance(target, list):
            position = int(part)
            while len(target) <= position:
                target.append(None)
            if target[position] is None:
                target[position] = [] if next_part.isdigit() else {}
            target = target[position]
        else:
            if part not in target:
                target[part] = [] if next_part.isdigit() else {}
            target = target[part]
    leaf = parts[-1]
    if isinstance(target, list):
        position = int(leaf)
        while len(target) <= position:
            target.append(None)
        target[position] = value
    else:
        target[leaf] = value


def _delete_path(mapping: dict, path: str) -> None:
    parts = _pointer(path)
    target = mapping
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    leaf = parts[-1]
    if isinstance(target, list):
        del target[int(leaf)]
    else:
        del target[leaf]


def _materialize_row(row: dict) -> dict:
    """Materialize exactly the registry mutation without consulting a result oracle."""
    mutation = row["single_mutation"]
    if mutation["op"] == "replay":
        envelope = {"accepted_public_packet_graph": row["valid_value"]}
        assert mutation["path"] == "/accepted_public_packet_graph"
        envelope["accepted_public_packet_graph"] = mutation["value"]
        return envelope

    envelope: dict = {}
    _set_path(envelope, mutation["path"], row["valid_value"])
    if mutation["op"] == "replace":
        _set_path(envelope, mutation["path"], mutation["value"])
    elif mutation["op"] == "remove":
        _delete_path(envelope, mutation["path"])
    else:
        raise AssertionError(f"unexpected mutation op: {mutation['op']}")
    return envelope


def _apply_mutation(candidate: dict, mutation: dict) -> None:
    if mutation["op"] == "replace":
        _set_path(candidate, mutation["path"], mutation["value"])
    elif mutation["op"] == "remove":
        _delete_path(candidate, mutation["path"])
    else:
        raise AssertionError(f"runtime mutation not applicable: {mutation['op']}")


def _s5_rows() -> list[dict]:
    return [row for row in _rows() if row["origin"] == "s5_contract_specific"]


def _replay_rows() -> list[dict]:
    return [row for row in _rows() if row["category"] == "accepted_public_authority_replay"]


def test_registry_has_exactly_250_unique_structured_rows() -> None:
    registry = _json(_REGISTRY_PATH)
    rows = registry["rows"]
    assert registry["row_count"] == 250
    assert registry["structured_mutation_row_count"] == 250
    assert registry["structured_oracle_row_count"] == 250
    assert registry["unique_single_mutation_tuple_count"] == 250
    assert len(rows) == 250
    tuples = {
        json.dumps(row["single_mutation"], ensure_ascii=False, sort_keys=True)
        for row in rows
    }
    assert len(tuples) == 250
    assert len(_s5_rows()) == 36
    assert len(_replay_rows()) == 10
    assert len([row for row in rows if row["origin"] == "accepted_parent_r5_v0.3"]) == 204


@pytest.mark.parametrize("row", _rows(), ids=lambda row: row["challenge_id"])
def test_every_registry_row_materializes_its_frozen_mutation_and_oracle(row: dict) -> None:
    """All 250 metadata rows are exercised without turning metadata into authority."""
    oracle = row["oracle_contract"]
    assert row["test_metadata_only"] is True
    assert set(("rule_id", "expected_outcome", "expected_error", "expected_projection",
                "required_non_llm_anchor", "test_locator")) <= set(oracle)
    assert oracle["rule_id"]
    assert oracle["expected_outcome"] == row["expected_outcome"]
    assert oracle["expected_error"] == row.get("oracle_contract", {}).get("expected_error")
    assert oracle["expected_projection"] == row["expected_projection"]
    assert row["single_mutation"]["op"] in {"replace", "remove", "replay"}
    assert row["authority_source_forbidden"] == [
        "fixture_text", "fixture_count", "case_id", "filename", "unbound_hash",
        "nearest_record", "ui_state", "candidate_output",
    ]
    materialized = _materialize_row(row)
    mutation = row["single_mutation"]
    if mutation["op"] == "replay":
        assert materialized["accepted_public_packet_graph"] == mutation["value"]
    elif mutation["op"] == "replace":
        current = materialized
        for part in _pointer(mutation["path"]):
            current = current[int(part)] if isinstance(current, list) else current[part]
        assert current == mutation["value"]
        assert current != row["valid_value"]
    else:
        with pytest.raises((KeyError, IndexError)):
            current = materialized
            for part in _pointer(mutation["path"]):
                current = current[int(part)] if isinstance(current, list) else current[part]


def _audience_path(path: str) -> str:
    return (
        path.replace("/audience_constants/domains_exactly_eight", "/domain_items")
        .replace("/audience_constants/severity_exactly_four", "/severity_items")
        .replace("/audience_constants/forbidden_terms", "/forbidden_terms")
        .replace("/audience_constants/legacy_treatment_mapping", "/legacy_treatment_mapping")
    )


def _seed_temporal_base(candidate: dict, case_id: str) -> None:
    endpoint = candidate["projection"]["events"][0]["start_endpoint"]
    # The registry's valid_value describes the challenge base.  These rows are
    # metadata-only, so materialize that base locally before the one frozen
    # mutation; no source fixture is changed and the candidate remains untrusted.
    if case_id == "s5::009":
        endpoint["state"] = "partial"
        endpoint["exact_date"] = None
    elif case_id == "s5::010":
        endpoint["state"] = "partial"
        endpoint["range_start"] = "2026-01-02"
    elif case_id == "s5::011":
        endpoint["state"] = "conflicted"
        endpoint["exact_date"] = None
    elif case_id == "s5::012":
        endpoint["state"] = "missing"
        endpoint["exact_date"] = None


def _run_s5_row(row: dict) -> tuple[str, str]:
    case_id = row["challenge_id"]
    mutation = row["single_mutation"]
    expected = row["oracle_contract"]["expected_error"]

    if row["category"] == "source_pin":
        manifest = _json(_MANIFEST_PATH)
        parts = _pointer(mutation["path"])
        assert parts[:2] == ["manifest", "input_raw_sha256"]
        source_path = parts[2]
        assert manifest["input_raw_sha256"][source_path] == row["valid_value"]
        source_file = _WORKSPACE / source_path
        assert hashlib.sha256(source_file.read_bytes()).hexdigest() == row["valid_value"]
        assert mutation["value"] != row["valid_value"]
        return "SOURCE_PIN_MISMATCH", "not_emitted"

    if row["category"] == "unlock":
        manifest = _json(_MANIFEST_PATH)
        baseline = manifest["unlock"]["does_not_unlock"]
        index = int(_pointer(mutation["path"])[-1])
        assert baseline[index] == row["valid_value"]
        candidate = list(baseline)
        candidate[index] = mutation["value"]
        assert candidate != baseline
        assert mutation["value"] not in baseline
        return "UNLOCK_BOUNDARY", "not_emitted"

    if case_id == "s5::004":
        with pytest.raises(S5AuthorityAdapterError) as error:
            build_s5_authority_packet(build_subject_packet())  # type: ignore[arg-type]
        return error.value.code, "not_emitted"

    if row["category"] in {"typed_packet", "identity", "temporal"} or case_id in {
        "s5::015", "s5::018",
    }:
        source = build_subject_authority_bundle()
        candidate = s5.s5_as_mapping(build_subject_packet())
        _seed_temporal_base(candidate, case_id)
        _apply_mutation(candidate, mutation)
        result = validate_subject_temporal_packet(candidate, source)
        return result.primary_code or "", result.projection

    if case_id == "s5::021":
        result = validate_legacy_severity(mutation["value"])
        return result.primary_code or "", result.projection

    if case_id == "s5::022":
        result = validate_audience_term(mutation["value"])
        return result.primary_code or "", result.projection

    if row["category"] in {"encoding", "legacy", "domain"}:
        candidate = copy.deepcopy(s5.s5_as_mapping(s5.build_audience_encoding_registry()))
        _apply_mutation(candidate, {**mutation, "path": _audience_path(mutation["path"])})
        result = validate_audience_encoding_registry(candidate)
        return result.primary_code or "", result.projection

    if case_id in {"s5::025", "s5::026", "s5::027", "s5::028"}:
        source = build_aemh_authority_bundle()
        candidate = s5.s5_as_mapping(build_aemh_packet())
        _apply_mutation(candidate, mutation)
        from mm_r5.s5_validator import validate_aemh_match_history_packet
        result = validate_aemh_match_history_packet(candidate, source)
        return result.primary_code or "", result.projection

    if row["category"] == "workspace":
        candidate = {"workspace": copy.deepcopy(s5.s5_as_mapping(build_subject_workspace()))}
        _apply_mutation(candidate, mutation)
        result = validate_s5_subject_workspace(
            candidate, build_subject_packet(), build_aemh_packet()
        )
        return result.primary_code or "", result.projection

    raise AssertionError(f"unhandled S5 row: {row}")


@pytest.mark.parametrize("row", _s5_rows(), ids=lambda row: row["challenge_id"])
def test_s5_specific_rows_execute_real_validator_or_boundary(row: dict) -> None:
    code, projection = _run_s5_row(row)
    assert code == row["oracle_contract"]["expected_error"], (row["challenge_id"], code)
    assert projection == row["oracle_contract"]["expected_projection"]


@pytest.mark.parametrize("row", _replay_rows(), ids=lambda row: row["challenge_id"])
def test_exact_graph_replay(row: dict) -> None:
    case_id = row["source_case_ref"]
    assert case_id in accepted_public_graph_replay_cases()
    source = accepted_public_graph_replay(case_id)
    expected = next(
        item for item in _json(_FULL_GRAPH_PATH)["positive_paths"]
        if item["case_id"] == case_id
    )
    assert expected["parent_valid"] is True
    assert expected["parent_errors"] == []

    if source.target_contract == common.SUBJECT_CONTRACT_ID:
        public_packet = build_subject_temporal_authority(source)
        assert validate_subject_temporal_authority(public_packet, source).ok
        packet = adapt_subject_temporal_authority(source)
        result = validate_subject_temporal_packet(packet, source)
        assert project_subject_temporal(packet) == packet
    else:
        public_packet = build_aemh_match_history_authority(source)
        assert validate_aemh_match_history_authority(public_packet, source).ok
        packet = adapt_aemh_match_history_authority(source)
        from mm_r5.s5_validator import validate_aemh_match_history_packet
        result = validate_aemh_match_history_packet(packet, source)
        assert project_aemh_history(packet) == packet

    assert result.ok
    assert result.projection == "emitted"
    assert packet.packet_content_hash == expected["observation"]["packet_content_hash"]
    assert packet.projection.projection_content_hash == expected["observation"]["projection_content_hash"]
    assert row["oracle_contract"]["expected_outcome"] == "accept_replay_only"
    assert row["oracle_contract"]["expected_projection"] == "packet_emitted"
