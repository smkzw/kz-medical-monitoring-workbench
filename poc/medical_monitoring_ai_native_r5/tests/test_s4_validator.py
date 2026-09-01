"""Focused W3 tests for the R5-S4 runtime validator
(``mm_r5.s4_validator``): fail-closed structural-first parsing, expected-
packet rebuild from the typed runtime input, stable single-code rejection,
message formula, and the no-oracle AST gate.

The 89 registry mutations are executed in
``tests/challenges/test_s4_runtime_challenges.py``; this module covers the
validator's own contract surface.
"""

from __future__ import annotations

import ast
import base64
import dataclasses
import pathlib
import re

import pytest

from mm_r5 import s4_contracts as s4
from mm_r5.s4_projection import build_s4_authority_packet
from mm_r5.s4_validator import validate_s4_authority_packet
from s4_runtime_fixtures import (
    ATTEMPT_SETS,
    CONTEXT_A1,
    CONTEXT_A2,
    build_runtime_input,
)

_R5_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "mm_r5"


# ---------------------------------------------------------------------------
# Base validity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_base_packet_valid_for_every_variant(state: str) -> None:
    """A packet built by the real builder from the typed input validates."""
    runtime_input = build_runtime_input(state)
    packet = build_s4_authority_packet(runtime_input)
    result = validate_s4_authority_packet(packet, runtime_input)
    assert result.ok
    assert result.issues == ()
    assert result.expected_packet is not None


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_candidate_mapping_and_packet_equivalent(state: str) -> None:
    """A Mapping candidate and the typed packet candidate validate the same."""
    runtime_input = build_runtime_input(state)
    packet = build_s4_authority_packet(runtime_input)
    as_mapping = s4.packet_as_mapping(packet)
    result_mapping = validate_s4_authority_packet(as_mapping, runtime_input)
    result_packet = validate_s4_authority_packet(packet, runtime_input)
    assert result_mapping.ok == result_packet.ok
    assert [i.code for i in result_mapping.issues] == \
        [i.code for i in result_packet.issues]


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_expected_packet_is_rebuilt_from_runtime_input(state: str) -> None:
    """``expected_packet`` equals an independent fresh rebuild; the candidate
    never proves itself."""
    runtime_input = build_runtime_input(state)
    packet = build_s4_authority_packet(runtime_input)
    result = validate_s4_authority_packet(s4.packet_as_mapping(packet),
                                          runtime_input)
    assert result.expected_packet == build_s4_authority_packet(runtime_input)


# ---------------------------------------------------------------------------
# Structural fail-closed (checks precede dataclass construction)
# ---------------------------------------------------------------------------


def _valid_candidate() -> tuple:
    runtime_input = build_runtime_input("multi_analysis")
    packet = build_s4_authority_packet(runtime_input)
    return runtime_input, s4.packet_as_mapping(packet)


def test_unknown_top_level_key_is_structural() -> None:
    runtime_input, candidate = _valid_candidate()
    candidate["extra_key"] = "x"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.schema_key_mismatch"]
    assert result.expected_packet is None


def test_missing_top_level_key_is_structural() -> None:
    runtime_input, candidate = _valid_candidate()
    del candidate["ensemble_size"]
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.schema_key_mismatch"]
    assert result.expected_packet is None


def test_wrong_primitive_type_is_structural_not_dataclass_error() -> None:
    """A wrong primitive must surface as schema_key_mismatch and never leak a
    raw dataclass TypeError."""
    runtime_input, candidate = _valid_candidate()
    candidate["ensemble_size"] = "2"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.schema_key_mismatch"]
    assert result.expected_packet is None


def test_wrong_container_type_is_structural() -> None:
    runtime_input, candidate = _valid_candidate()
    candidate["worker_views"] = {"not": "a list"}
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.schema_key_mismatch"]
    assert result.expected_packet is None


def test_wrong_nested_container_is_structural() -> None:
    """A malformed nested sub-object (wrong container shape) fails closed with
    schema_key_mismatch before any semantic join."""
    runtime_input, candidate = _valid_candidate()
    candidate["audience_inspector"] = ["not", "a", "dict"]
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.schema_key_mismatch"]
    assert result.expected_packet is None


def test_non_mapping_candidate_is_implementation_error() -> None:
    """A candidate that is neither a Mapping nor a packet is an
    implementation misuse, not a packet rejection."""
    runtime_input = build_runtime_input("multi_analysis")
    with pytest.raises(s4.S4RuntimeImplementationError):
        validate_s4_authority_packet(42, runtime_input)  # type: ignore[arg-type]


def test_unrebuildable_runtime_input_is_implementation_error() -> None:
    """A trusted-source failure (the typed input cannot rebuild a valid
    packet) surfaces as S4RuntimeImplementationError, never as a packet
    rejection."""
    runtime_input = build_runtime_input("multi_analysis")
    attempts = list(runtime_input.attempts)
    first = attempts[0]
    conflicting = dataclasses.replace(
        first, input_content_hash="0" * 64)
    broken = dataclasses.replace(runtime_input, attempts=(
        conflicting, *attempts[1:]))
    packet = build_s4_authority_packet(runtime_input)
    with pytest.raises(s4.S4RuntimeImplementationError):
        validate_s4_authority_packet(s4.packet_as_mapping(packet), broken)


# ---------------------------------------------------------------------------
# Issue shape / message formula / ordering
# ---------------------------------------------------------------------------


def test_issue_message_zh_uses_fixed_formula() -> None:
    runtime_input, candidate = _valid_candidate()
    candidate["ensemble_size"] = 0
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.message_zh == \
        f"核对未通过：{issue.path}（{issue.code}）"


def test_validation_result_orders_and_deduplicates_issues() -> None:
    """R5S4ValidationResult sorts and deduplicates by (code, path, message)."""
    result = s4.R5S4ValidationResult(
        ok=False,
        issues=(
            s4.R5S4ValidationIssue(code="s4.b", path="p.1", message_zh=""),
            s4.R5S4ValidationIssue(code="s4.a", path="p.2", message_zh=""),
            s4.R5S4ValidationIssue(code="s4.b", path="p.1", message_zh=""),
        ),
        expected_packet=None,
    )
    assert [i.code for i in result.issues] == ["s4.a", "s4.b"]
    assert not result.ok


def test_validation_result_forces_ok_false_on_issues() -> None:
    result = s4.R5S4ValidationResult(
        ok=True,
        issues=(s4.R5S4ValidationIssue(code="s4.x", path="p", message_zh=""),),
        expected_packet=None,
    )
    assert not result.ok


# ---------------------------------------------------------------------------
# Representative single-code rejections (family probes; the full 89-case
# matrix lives in the challenges module)
# ---------------------------------------------------------------------------


def _mutate(candidate: dict, path: str, value) -> None:
    parts = []
    for segment in path.split("."):
        match = re.fullmatch(r"([A-Za-z0-9_]+)((?:\[\d+\])*)", segment)
        parts.append(match.group(1))
        parts.extend(int(i) for i in re.findall(r"\[(\d+)\]",
                                                match.group(2)))
    assert parts[0] == "packet"
    parts = parts[1:]
    target = candidate
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


@pytest.mark.parametrize("path,value,expected", [
    ("packet.ensemble_size", 0, "s4.cardinality_not_0_1_n"),
    ("packet.input_content_hash", "0" * 64, "s4.authority_drift"),
    ("packet.worker_views[0].binding_id", "worker.b.a2",
     "s4.duplicate_worker_binding"),
    ("packet.worker_views[0].independent_context_hash", CONTEXT_A2,
     "s4.duplicate_worker_context"),
    ("packet.risk_identity.domain", "mh", "s4.anchor_claim_drift"),
    ("packet.raw_artifacts[0].raw_bytes_sha256", "0" * 64,
     "s4.raw_sha_external_mismatch"),
    ("packet.raw_artifacts[0].raw_format", "text/plain",
     "s4.enum_value_mismatch"),
    ("packet.verification_rows[0].result", "failed",
     "s4.verification_label_only"),
    ("packet.verification_rows[0].recomputed", False,
     "s4.schema_key_mismatch"),
    ("packet.conflict_rows[0].hidden", True, "s4.baseline_miss_hidden"),
    ("packet.conflict_rows[1].display_state", "visible_baseline_miss",
     "s4.conflict_set_incomplete"),
    ("packet.adjudication_row.binding_id", "worker.b.a1",
     "s4.worker_self_adjudication"),
    ("packet.adjudication_row.independent_context_hash", CONTEXT_A1,
     "s4.adjudicator_context_collision"),
    ("packet.audit_inspector.model_evidence.model_id", "model.zzz",
     "s4.model_evidence_not_permitted"),
    ("packet.history_log.head_seq", 8, "s4.history_append_only_violation"),
    ("packet.history_log.entries[1].prior_entry_hash", "0" * 64,
     "s4.history_chain_break"),
    ("packet.journey_link.fallback_policy", "nearest_site",
     "s4.journey_fallback_not_none"),
    ("packet.journey_link.deep_link_project_ref", "",
     "s4.anchor_claim_drift"),
    ("packet.audience_inspector.query_basis_zh", "X",
     "s4.query_projection_drift"),
    ("packet.query_draft_row.risk_ref", "d09_marker:ghost",
     "s4.query_projection_drift"),
    ("packet.audience_inspector.baseline_rows_zh", [],
     "s4.baseline_projection_drift"),
    ("packet.baseline_rows[0].state", "unsupported",
     "s4.baseline_projection_drift"),
    ("packet.baseline_rows[0].recheck_complete", False,
     "s4.baseline_recheck_missing"),
    ("packet.audience_inspector.model_id", "m1",
     "s4.audience_hash_contains_audit_leaf"),
    ("packet.audience_inspector.model_evidence", {},
     "s4.model_evidence_on_audience"),
    ("packet.audience_inspector.consensus_zh", "多个 worker 达成共识",
     "s4.audience_audit_leak"),
    ("packet.audience_inspector.source_one_hop_zh", "就近替代方案已采用",
     "s4.nearest_fallback_forbidden"),
    ("packet.audience_inspector.support_evidence_zh",
     ["来源 loc.zzz 已定位，请核实"], "s4.hidden_source_leak"),
    ("packet.audience_inspector.counterevidence_zh",
     ["根据 loc.src1 的检查结果，未见明确反证"],
     "s4.cross_plane_projection_drift"),
    ("packet.raw_artifacts[0].raw_bytes_b64",
     base64.b64encode(b'{"attempt":"a1","x":1}').decode(),
     "s4.raw_output_rewritten"),
    ("packet.raw_artifacts[0].parsed_output_hash", "0" * 64,
     "s4.anchor_claim_drift"),
    ("packet.raw_artifacts[0].declared_output_hash", "0" * 64,
     "s4.parsed_output_hash_mismatch"),
])
def test_family_probe_single_code(path: str, value, expected: str) -> None:
    """One mutation -> exactly one frozen code (single-code precedence)."""
    runtime_input = build_runtime_input("multi_analysis")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    _mutate(candidate, path, value)
    result = validate_s4_authority_packet(candidate, runtime_input)
    codes = [issue.code for issue in result.issues]
    assert codes == [expected], (path, codes)


def test_single_analysis_consensus_forbidden() -> None:
    runtime_input = build_runtime_input("single_analysis")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["audience_inspector"]["consensus_zh"] = "多个分析结果一致"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert [i.code for i in result.issues] == \
        ["s4.single_model_consensus_forbidden"]


def test_no_ensemble_fabricated_consensus() -> None:
    runtime_input = build_runtime_input("no_ensemble")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["audience_inspector"]["consensus_zh"] = "两个分析达成共识"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert [i.code for i in result.issues] == ["s4.fabricated_consensus"]


def test_no_ensemble_residue_rejected() -> None:
    runtime_input = build_runtime_input("no_ensemble")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["raw_artifacts"] = [{
        "artifact_id": "raw:a1", "attempt_id": "a1",
        "raw_format": "utf8_text",
        "raw_bytes_b64": base64.b64encode(b"{}").decode(),
        "raw_bytes_sha256": "0" * 64, "parsed_output_hash": "1" * 64,
        "declared_output_hash": "1" * 64}]
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert [i.code for i in result.issues] == \
        ["s4.ensemble_zero_must_be_empty"]


def test_failed_verification_blocks_supporting_outcome() -> None:
    runtime_input = build_runtime_input("failed_verification")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["adjudication_row"]["outcome"] = "merged_supported"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert [i.code for i in result.issues] == \
        ["s4.verification_unresolved_authority"]


def test_audit_digest_context_drift_is_verification_label_only() -> None:
    runtime_input = build_runtime_input("multi_analysis")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["audit_inspector"]["digest_context"]["input_content_hash"] = \
        "3" * 64
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert [i.code for i in result.issues] == ["s4.verification_label_only"]


# ---------------------------------------------------------------------------
# Reviewer regression probes: hash-DAG nodes, deleted members, nested scalar
# replacement, honest N=6 max, builder-error stability
# ---------------------------------------------------------------------------

_ZERO = "0" * 64


def _fresh_candidate(state: str = "multi_analysis") -> tuple:
    runtime_input = build_runtime_input(state)
    packet = build_s4_authority_packet(runtime_input)
    return runtime_input, s4.packet_as_mapping(packet)


@pytest.mark.parametrize("mutate,expected", [
    (lambda c: c.__setitem__("receipt_content_hash", _ZERO),
     "s4.receipt_hash_mismatch"),
    (lambda c: c.__setitem__("audience_content_hash", _ZERO),
     "s4.audience_hash_contains_audit_leaf"),
    (lambda c: c.__setitem__("audit_content_hash", _ZERO),
     "s4.audience_audit_leak"),
    (lambda c: c.__setitem__("packet_id", "r5-s4-contract:" + _ZERO),
     "s4.packet_id_grammar_mismatch"),
    (lambda c: c.__setitem__("packet_integrity_hash", _ZERO),
     "s4.hash_recipe_cycle"),
    (lambda c: c["audit_inspector"].__setitem__(
        "packet_fingerprints", ["x", "y", "z", "w"]),
     "s4.cross_plane_projection_drift"),
    (lambda c: c.__setitem__("ensemble_id", "ens.zzz"),
     "s4.cross_plane_projection_drift"),
])
def test_hash_node_and_identity_leaf_drift_single_code(
        mutate, expected: str) -> None:
    """Every hash-DAG node / packet identity leaf is recomputed and a forged
    leaf yields exactly one accepted code."""
    runtime_input, candidate = _fresh_candidate()
    mutate(candidate)
    result = validate_s4_authority_packet(candidate, runtime_input)
    codes = [issue.code for issue in result.issues]
    assert codes == [expected], (expected, codes)
    assert result.expected_packet is not None


@pytest.mark.parametrize("mutate,expected", [
    (lambda c: c["worker_views"][0].__setitem__("model_version", "9.9"),
     "s4.cross_plane_projection_drift"),
    (lambda c: c["audit_inspector"]["worker_audit_rows"][0].__setitem__(
        "session_id", "xx"),
     "s4.cross_plane_projection_drift"),
    (lambda c: c["journey_link"].__setitem__("journey_available", False),
     "s4.cross_plane_projection_drift"),
    (lambda c: c["adjudication_row"].__setitem__("session_id", "adj.zzz"),
     "s4.cross_plane_projection_drift"),
])
def test_nested_content_drift_generic_cross_plane(mutate, expected: str) -> None:
    """A content leaf not assigned a more specific rule fails with the
    accepted generic cross-plane code."""
    runtime_input, candidate = _fresh_candidate()
    mutate(candidate)
    result = validate_s4_authority_packet(candidate, runtime_input)
    codes = [issue.code for issue in result.issues]
    assert codes == [expected], (expected, codes)


@pytest.mark.parametrize("mutate,expected", [
    (lambda c: c["raw_artifacts"].pop(0), "s4.cardinality_not_0_1_n"),
    (lambda c: c["worker_views"].pop(0), "s4.cardinality_not_0_1_n"),
    (lambda c: c["conflict_rows"].pop(0), "s4.conflict_set_incomplete"),
    (lambda c: c["history_log"]["entries"].pop(0),
     "s4.history_chain_break"),
    (lambda c: c["baseline_rows"].pop(0), "s4.baseline_projection_drift"),
])
def test_deleted_member_fails(mutate, expected: str) -> None:
    """Deleting any member of a multi member list must fail with exactly one
    accepted code."""
    runtime_input, candidate = _fresh_candidate()
    mutate(candidate)
    result = validate_s4_authority_packet(candidate, runtime_input)
    codes = [issue.code for issue in result.issues]
    assert codes == [expected], (expected, codes)


@pytest.mark.parametrize("mutate", [
    lambda c: c.__setitem__("risk_identity", "scalar"),
    lambda c: c["worker_views"].__setitem__(0, "scalar"),
    lambda c: c.__setitem__("audience_inspector", "scalar"),
    lambda c: c.__setitem__("audit_inspector", "scalar"),
    lambda c: c.__setitem__("worker_views", "scalar"),
    lambda c: c.__setitem__("raw_artifacts", "scalar"),
    lambda c: c.__setitem__("verification_rows", "scalar"),
    lambda c: c["audit_inspector"].__setitem__("model_evidence", "scalar"),
    lambda c: c["audit_inspector"].__setitem__("digest_context", "scalar"),
    lambda c: c.__setitem__("ensemble_size", True),  # bool as int
    lambda c: c["worker_views"][0].__setitem__("ordinal", "2"),
    lambda c: c["history_log"].__setitem__("entries", "scalar"),
])
def test_nested_scalar_replacement_is_structural(mutate) -> None:
    """A nested object replaced by a scalar (or a wrong primitive) is a
    recursive structural rejection: schema_key_mismatch, expected_packet=None,
    and never a raw AttributeError/TypeError."""
    runtime_input, candidate = _fresh_candidate()
    mutate(candidate)
    result = validate_s4_authority_packet(candidate, runtime_input)
    codes = [issue.code for issue in result.issues]
    assert codes == ["s4.schema_key_mismatch"], codes
    assert result.expected_packet is None


def test_validator_never_leaks_raw_exception_on_malformed_candidate() -> None:
    """A battery of malformed nested shapes must all return a stable issue (no
    exception escapes the validator)."""
    mutations = [
        lambda c: c.__setitem__("risk_identity", 42),
        lambda c: c["audit_inspector"].__setitem__("worker_audit_rows", {}),
        lambda c: c["worker_views"][0].__setitem__(
            "independent_context_hash", None),
        lambda c: c["baseline_rows"][0].__setitem__("reason_codes", "x"),
        lambda c: c["journey_link"].__setitem__("deep_link_project_ref", 7),
        lambda c: c["history_log"]["entries"][0].__setitem__("seq", "1"),
        lambda c: c["audience_inspector"].__setitem__("support_evidence_zh", 9),
        lambda c: c["adjudication_row"].__setitem__("binding_id", []),
    ]
    runtime_input, candidate = _fresh_candidate()
    for mutate in mutations:
        trial = dict(candidate)
        # deep-enough copy of the touched plane so later mutations stay isolated
        import copy
        trial = copy.deepcopy(candidate)
        mutate(trial)
        result = validate_s4_authority_packet(trial, runtime_input)
        assert not result.ok
        assert len(result.issues) == 1
        assert result.issues[0].code.startswith("s4.")


def test_builder_fail_closed_error_is_implementation_error() -> None:
    """An invalid runtime input (one the builder rejects) surfaces as
    S4RuntimeImplementationError, never as a packet rejection, keeping
    candidate rejection distinct from invalid runtime input."""
    import dataclasses as _dc
    runtime_input = build_runtime_input("multi_analysis")
    attempts = list(runtime_input.attempts)
    conflicting = _dc.replace(attempts[0], input_content_hash="0" * 64)
    bad_input = _dc.replace(runtime_input,
                            attempts=(conflicting, *attempts[1:]))
    # the builder rejects the divergent input hash (fail-closed authority
    # error), which the validator must surface as an implementation error.
    with pytest.raises(s4.S4RuntimeImplementationError):
        validate_s4_authority_packet(
            s4.packet_as_mapping(build_s4_authority_packet(runtime_input)),
            bad_input)


def test_valid_runtime_input_with_bad_candidate_is_rejection() -> None:
    """A valid runtime input + a drifted candidate is a packet rejection
    (issues), not an implementation error."""
    runtime_input = build_runtime_input("multi_analysis")
    packet = build_s4_authority_packet(runtime_input)
    candidate = s4.packet_as_mapping(packet)
    candidate["ensemble_id"] = "ens.zzz"
    result = validate_s4_authority_packet(candidate, runtime_input)
    assert not result.ok
    assert [i.code for i in result.issues] == ["s4.cross_plane_projection_drift"]


def test_honest_max_cardinality_n6_builds_and_validates() -> None:
    """The accepted anchor supports an honest maximum of N=6 multi_analysis
    (all six attempt-authority rows used once).  N=10 is NOT claimed: the
    accepted anchor carries exactly six rows (see test_s4_contracts)."""
    from s4_runtime_fixtures import build_max_cardinality_input, \
        MAX_CARDINALITY_ATTEMPTS
    runtime_input = build_max_cardinality_input()
    assert len(runtime_input.attempts) == 6
    assert len(MAX_CARDINALITY_ATTEMPTS) == 6
    packet = build_s4_authority_packet(runtime_input)
    assert packet.ensemble_size == 6
    assert packet.ensemble_projection_state == "multi_analysis"
    assert len(packet.worker_views) == 6
    assert len(packet.raw_artifacts) == 6
    assert len(packet.verification_rows) == 6
    result = validate_s4_authority_packet(
        s4.packet_as_mapping(packet), runtime_input)
    assert result.ok
    assert result.expected_packet == packet


# ---------------------------------------------------------------------------
# No-oracle AST gate for the validator source
# ---------------------------------------------------------------------------


def test_validator_no_oracle_reads() -> None:
    """s4_validator source performs zero file I/O, imports no
    generator/verifier/registry/oracle module and never uses ``assert`` to
    enforce a runtime invariant."""
    source = (_R5_SRC / "s4_validator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                calls.append(fn.attr)
            elif isinstance(fn, ast.Name):
                calls.append(fn.id)
    forbidden = {"open", "read_text", "read_bytes", "read"}
    assert not (set(calls) & forbidden)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "Path" not in names
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "tools" not in node.module
            assert "generate_medical_monitoring" not in node.module
            assert "verify_medical_monitoring" not in node.module
            assert "artifacts" not in node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "tools" not in alias.name
                assert "artifacts" not in alias.name
