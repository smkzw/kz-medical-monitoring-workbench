"""R5-S4 runtime challenge closure (``R5S4C-001``..``R5S4C-089``).

Every accepted runtime challenge is executed for real in this module:

1. build the base packet through the real builder
   (``mm_r5.s4_projection.build_s4_authority_packet``) and prove it validates;
2. apply exactly ONE registry mutation to the canonical packet mapping;
3. call the real runtime validator
   (``mm_r5.s4_validator.validate_s4_authority_packet``);
4. assert the candidate is rejected with exactly the frozen single ``s4.*``
   code.

The validator never reads the registry: it receives only the mutated candidate
mapping and the typed runtime input and rebuilds the expected packet from the
input (the candidate never proves itself).

``R5S4C-090``..``R5S4C-097`` (``artifact_governance``) are NOT re-run in the
runtime phase: they are the frozen construction-phase governance evidence
referenced by ``ACCEPT_R5_S4_CONTRACT`` and the read-only SHA evidence file
(``evidence/r4_r5_s4_readonly_sha256.json``).  This module only asserts that
the registry keeps them out of the runtime set and that the frozen evidence
still exists.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

# ``s4_runtime_fixtures`` lives in the ``tests/`` parent directory, but pytest
# inserts this ``tests/challenges/`` basedir (not its parent) into sys.path.
_TESTS_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from mm_r5 import s4_contracts as s4  # noqa: E402
from mm_r5.s4_projection import build_s4_authority_packet  # noqa: E402
from mm_r5.s4_validator import validate_s4_authority_packet  # noqa: E402
from s4_runtime_fixtures import build_runtime_input  # noqa: E402

_WORKSPACE = pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent
_ARTIFACTS = _WORKSPACE / "artifacts" / "medical_monitoring_r5_s4_contract_v0_1"
_EVIDENCE = (pathlib.Path(__file__).resolve().parent.parent.parent
             / "evidence" / "r4_r5_s4_readonly_sha256.json")

_FIRST_RUNTIME = "R5S4C-001"
_LAST_RUNTIME = "R5S4C-089"
_FIRST_GOVERNANCE = "R5S4C-090"
_LAST_GOVERNANCE = "R5S4C-097"

#: Frozen artifact-governance codes (contract section 9; R5S4C-090..097).
_GOVERNANCE_EXPECTED = {
    "R5S4C-090": "s4.schema_key_mismatch",
    "R5S4C-091": "s4.audience_hash_contains_audit_leaf",
    "R5S4C-092": "s4.enum_value_mismatch",
    "R5S4C-093": "s4.hash_recipe_cycle",
    "R5S4C-094": "s4.join_recipe_unresolvable",
    "R5S4C-095": "s4.receipt_hash_mismatch",
    "R5S4C-096": "s4.packet_id_grammar_mismatch",
    "R5S4C-097": "s4.history_chain_break",
}


def _load_registry() -> list:
    return json.loads((_ARTIFACTS / "challenge_registry.json").read_text(
        encoding="utf-8"))["challenges"]


def _state_from_precondition(precondition: str) -> str:
    match = re.match(r"^([a-z_]+) packet$", precondition)
    if match is None:
        raise ValueError(f"unexpected precondition {precondition!r}")
    return match.group(1)


def _path_parts(path: str):
    """``packet.worker_views[0].binding_id`` -> ["packet","worker_views",0,
    "binding_id"]."""
    parts = []
    for segment in path.split("."):
        match = re.fullmatch(r"([A-Za-z0-9_]+)((?:\[\d+\])*)", segment)
        if match is None:
            raise ValueError(f"unparseable mutation path segment {segment!r}")
        parts.append(match.group(1))
        parts.extend(int(index) for index in re.findall(r"\[(\d+)\]",
                                                        match.group(2)))
    return parts


def _apply_single_mutation(candidate: dict, mutation: dict) -> None:
    """Apply exactly one registry mutation to a plain packet mapping."""
    assert mutation["path"].startswith("packet.")
    parts = _path_parts(mutation["path"])[1:]
    target = candidate
    if mutation["op"] == "set":
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = mutation["value"]
    elif mutation["op"] == "append":
        for part in parts:
            target = target[part]
        assert isinstance(target, list)
        target.append(mutation["value"])
    else:
        raise ValueError(f"unknown mutation op {mutation['op']!r}")


def _runtime_cases():
    cases = [case for case in _load_registry()
             if _FIRST_RUNTIME <= case["case_id"] <= _LAST_RUNTIME]
    assert len(cases) == 89, f"expected 89 runtime cases, got {len(cases)}"
    return cases


_RUNTIME_CASES = _runtime_cases()


# ---------------------------------------------------------------------------
# Registry shape gates
# ---------------------------------------------------------------------------


def test_registry_has_exactly_89_runtime_and_8_governance_cases() -> None:
    """The accepted registry has exactly 89 executable runtime cases and 8
    artifact-governance cases frozen as evidence."""
    cases = _load_registry()
    runtime = [c for c in cases if _FIRST_RUNTIME <= c["case_id"]
               <= _LAST_RUNTIME]
    governance = [c for c in cases if _FIRST_GOVERNANCE <= c["case_id"]
                  <= _LAST_GOVERNANCE]
    assert len(runtime) == 89
    assert len(governance) == 8
    assert len(runtime) + len(governance) == 97
    assert all(c["category"] == "artifact_governance" for c in governance)


def test_governance_cases_reference_frozen_evidence() -> None:
    """R5S4C-090..097 are frozen governance evidence: their accepted codes are
    recorded in the read-only SHA evidence file, not re-run in this runtime
    phase."""
    evidence = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    gov = evidence["governance_cases"]
    assert set(gov) == set(_GOVERNANCE_EXPECTED)
    assert gov == _GOVERNANCE_EXPECTED
    # the frozen raw SHAs of the accepted S4 artifacts are present and stable.
    for key in ("challenge_registry.json", "exact_overlay.json",
                "packet_schema.json", "accepted_authority_anchor.json"):
        sha = evidence["files"][
            f"artifacts/medical_monitoring_r5_s4_contract_v0_1/{key}"]
        assert re.fullmatch(r"[0-9a-f]{64}", sha), key


# ---------------------------------------------------------------------------
# Real execution of every runtime challenge
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", _RUNTIME_CASES,
                         ids=lambda c: c["case_id"])
def test_runtime_challenge_single_code(case: dict) -> None:
    """Each runtime row: base passes [] -> one mutation -> exactly one frozen
    s4.* code from the real validator."""
    mutation = case["single_mutation"]
    expected = case["expected_typed_outcome_or_error"]
    state = _state_from_precondition(case["precondition"])

    runtime_input = build_runtime_input(state)
    base = build_s4_authority_packet(runtime_input)

    # 1) the base packet built by the real builder must validate.
    base_result = validate_s4_authority_packet(base, runtime_input)
    assert base_result.ok, (
        case["case_id"], f"base packet must be valid, got "
        f"{[i.code for i in base_result.issues]}")

    # 2) exactly one mutation on the canonical packet mapping.
    candidate = s4.packet_as_mapping(base)
    _apply_single_mutation(candidate, mutation)

    # 3) the real runtime validator.
    result = validate_s4_authority_packet(candidate, runtime_input)

    # 4) exactly the frozen single code.
    codes = [issue.code for issue in result.issues]
    assert codes == [expected], (
        case["case_id"], f"expected {expected!r}, got {codes!r}")
    # the validator rebuilt the expected packet from the runtime input.
    assert result.expected_packet is not None, case["case_id"]


@pytest.mark.parametrize("case", _RUNTIME_CASES,
                         ids=lambda c: c["case_id"])
def test_runtime_challenge_does_not_let_candidate_prove_itself(
        case: dict) -> None:
    """The validator's expected packet must equal a fresh rebuild from the
    runtime input (never derived from the mutated candidate)."""
    state = _state_from_precondition(case["precondition"])
    runtime_input = build_runtime_input(state)
    base = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(base)
    _apply_single_mutation(candidate, case["single_mutation"])
    result = validate_s4_authority_packet(candidate, runtime_input)
    expected = build_s4_authority_packet(runtime_input)
    assert result.expected_packet == expected, case["case_id"]
