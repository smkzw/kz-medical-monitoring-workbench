"""R5-S4 contract artifact tests: external accepted-authority anchor, R4-backed.

The S4 contract freezes packet *semantics* that are RECOMPUTED from real R4
(``verify_attempt`` for all seven dimensions, ``derive_conflicts`` for the
exact conflict set, ``worker_output_content_hash`` for parsed hashes, real
``ModelEvidence``) and validated against an EXTERNAL accepted-authority anchor
(the packet never defines its own truth).  This suite:

  * reproduces every isolated-reviewer attack and requires exact rejection;
  * validates valid zero/one/N fixtures pass ``[]`` against the anchor;
  * executes the challenge registry (97 rows, exact single-code isolation,
    base valid before mutation);
  * asserts generator ``--check`` determinism; verifier normal == O2;
  * registry quota / unique ids / unique mutations / unique oracles / nodeids;
  * immutable pinned source SHAs, 8911 stopped, no S4 runtime, allowed paths.

No S4 runtime/UI, no real project/model, no production.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "tools" / "generate_medical_monitoring_r5_s4_contract_v0_1.py"
VERIFIER = ROOT / "tools" / "verify_medical_monitoring_r5_s4_contract_v0_1.py"
ARTIFACTS = ROOT / "artifacts" / "medical_monitoring_r5_s4_contract_v0_1"

EXPECTED_CHALLENGE_QUOTA = {
    "ensemble_0_1_n": 9,
    "input_identity_isolation": 8,
    "raw_parsed_hash_separation": 6,
    "baseline_recheck": 10,
    "verification_before_adjudication": 8,
    "conflict_relations_hideability": 10,
    "adjudicator_independence": 6,
    "support_counter_source_resolution": 8,
    "query_draft_three_part": 6,
    "history_append_only": 6,
    "journey_fallback_none": 4,
    "audience_audit_split": 8,
    "artifact_governance": 8,
}


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_verifier_module() -> Any:
    spec = importlib.util.spec_from_file_location("s4_contract_verifier", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


VMOD = _load_verifier_module()
SCHEMA = _load(ARTIFACTS / "packet_schema.json")
OVERLAY = _load(ARTIFACTS / "exact_overlay.json")
VMOD._schema_enums = {name: set(vals) for name, vals in
                      OVERLAY["enums"].items() if isinstance(vals, list)}
#: the external accepted-authority anchor is an INDEPENDENTLY PINNED test
#: input: the S4 generator never creates or signs it, the verifier never
#: trusts an in-band packet copy, and tamper requires the frozen SHA below.
ANCHOR_PATH = ARTIFACTS / "accepted_authority_anchor.json"
ANCHOR_SHA256 = "1fb07001aa1163bfe4044ad0b36d6879a454b740a1cda912b7acc11d503da0c4"
assert hashlib.sha256(ANCHOR_PATH.read_bytes()).hexdigest() == ANCHOR_SHA256, (
    "external anchor fixture tampered (independently frozen SHA)")
ANCHOR = VMOD._load_anchor(ANCHOR_PATH)
REGISTRY = _load(ARTIFACTS / "challenge_registry.json")
CHALLENGE_CASES = REGISTRY["challenges"]


def _run(script: Path, *extra: str, optimize: bool = False,
         timeout: int = 600) -> subprocess.CompletedProcess:
    env = dict(__import__("os").environ)
    if optimize:
        env["PYTHONOPTIMIZE"] = "2"
    return subprocess.run([sys.executable, str(script), *extra],
                          cwd=str(ROOT), env=env, capture_output=True,
                          text=True, timeout=timeout)


def _oracle(packet: Dict[str, Any], anchor: Dict[str, Any]) -> List[str]:
    return VMOD._packet_oracle(packet, anchor, SCHEMA, OVERLAY)


def _resign(packet: Dict[str, Any]) -> Dict[str, Any]:
    return VMOD._resign(packet)


def _rebuild(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Resign a rebuilt packet: refresh derived projections then all hashes."""
    return VMOD._resign(VMOD._rebuild_derived(packet))


# ---------------------------------------------------------------------------
# isolated-reviewer attacks (each must FAIL after repair with exact codes)
# ---------------------------------------------------------------------------


def test_attack_rule_id_drift_recomputed() -> None:
    """Changing artifact_rule_ids and keeping 'passed' must fail: the oracle
    recomputes verify_attempt and compares every dimension."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["digest_context"]["artifact_rule_ids"]["artifact:a1"] = "WRONG_RULE"
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.verification_label_only" in errs, errs


def test_attack_missing_baseline_miss_conflict_fails() -> None:
    """Deleting the derived baseline_miss conflict and re-signing must fail."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["conflict_rows"] = [c for c in p["conflict_rows"]
                          if c["relation"] != "baseline_miss"]
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.conflict_set_incomplete" in errs, errs


def test_attack_jointly_replaced_hashes_fail() -> None:
    """Replacing parsed/declared/worker hashes together to f*64 must fail."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["raw_artifacts"][0]["parsed_output_hash"] = "f" * 64
    p["raw_artifacts"][0]["declared_output_hash"] = "f" * 64
    p["worker_views"][0]["declared_output_hash"] = "f" * 64
    errs = _oracle(_resign(p), ANCHOR)
    assert any(c in errs for c in ("s4.anchor_claim_drift",
                                   "s4.parsed_output_hash_mismatch")), errs


def test_attack_zero_state_residual_rows_fail() -> None:
    """Zero-state with residual adjudication-audit/audience rows must fail."""
    p = copy.deepcopy(VMOD.build_sample_packet("no_ensemble", ANCHOR))
    p["audit_inspector"]["adjudication_audit"] = ["adj.record.1"]
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.ensemble_zero_must_be_empty" in errs, errs


def test_attack_missing_required_key_fails() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    del p["risk_identity"]["project_ref"]
    assert "s4.schema_key_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_unknown_key_fails() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["bogus_field"] = "x"
    assert "s4.schema_key_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_empty_required_title_fails() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audience_inspector"]["risk_title_zh"] = ""
    assert "s4.schema_key_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_imported_receipt_key_and_required_fail() -> None:
    """Unknown imported receipt key / missing receipt project_ref must fail:
    the imported R5AuthorityReceipt is not structurally free (content hash
    and schema both reject it)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["authority_receipt"]["bogus_key"] = "x"
    errs = _oracle(_resign(p), ANCHOR)
    assert any(c in errs for c in ("s4.schema_key_mismatch",
                                   "s4.receipt_hash_mismatch",
                                   "s4.imported_object_drift")), errs
    p2 = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    del p2["authority_receipt"]["project_ref"]
    errs2 = _oracle(_resign(p2), ANCHOR)
    assert any(c in errs2 for c in ("s4.schema_key_mismatch",
                                    "s4.receipt_hash_mismatch",
                                    "s4.imported_object_drift")), errs2


def test_attack_wrong_status_and_authority_mode_fail() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["status"] = "APPROVED"
    p["authority_mode"] = "production"
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.schema_key_mismatch" in errs, errs


def test_attack_project_ref_wrong_type_fails() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["project_ref"] = 123
    assert "s4.schema_key_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_reversed_conflict_order_still_fails() -> None:
    """Reordering conflict rows must not hide a set/identity mismatch."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["conflict_rows"] = list(reversed(p["conflict_rows"]))
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.conflict_set_incomplete" in errs, errs


def test_attack_raw_sha_external_mismatch() -> None:
    """Raw SHA must equal the externally accepted raw SHA, not packet-local."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["raw_artifacts"][0]["raw_bytes_sha256"] = "0" * 64
    assert "s4.raw_sha_external_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_history_prefix_rewrite() -> None:
    """Rewriting an accepted prior entry and rebuilding the chain must fail
    against the external accepted history head."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["history_log"]["entries"][0]["payload_ref"] = "payload.rewritten"
    # rebuild the chain after the rewrite.
    prior = VMOD.GENESIS_HASH
    for entry in p["history_log"]["entries"]:
        entry["prior_entry_hash"] = prior
        entry["entry_hash"] = VMOD._h({k: entry[k] for k in (
            "entry_id", "seq", "kind", "payload_ref", "prior_entry_hash")})
        prior = entry["entry_hash"]
    p["history_log"]["head_hash"] = p["history_log"]["entries"][-1]["entry_hash"]
    errs = _oracle(_resign(p), ANCHOR)
    assert any(c in errs for c in ("s4.history_prefix_rewrite",
                                   "s4.history_chain_break")), errs


def test_attack_critical_without_external_authority_fails() -> None:
    """A critical packet requires an explicit externally accepted critical
    severity authority; never a generic enum mismatch."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["severity"] = "critical"
    p["risk_identity"]["severity_zh"] = "紧急"
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.critical_severity_authority_missing" in errs, errs


def test_attack_model_evidence_invalid_role_and_leaf_fail() -> None:
    """Invalid ModelEvidence role/leaf must fail; ModelEvidence is audit-only
    and must be externally permitted.  An out-of-enum role is a structural
    type/schema failure (B short-circuit -> enum_value_mismatch); an
    in-enum-but-unpermitted role or unknown id is the semantic permit code."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["model_evidence"]["role"] = "provenance"
    assert "s4.enum_value_mismatch" in _oracle(_resign(p), ANCHOR)
    p3 = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p3["audit_inspector"]["model_evidence"]["role"] = \
        "counterevidence_suggestion"  # in-enum but unpermitted
    assert "s4.model_evidence_not_permitted" in _oracle(_resign(p3), ANCHOR)
    p2 = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p2["audit_inspector"]["model_evidence"]["model_evidence_id"] = "model_evidence:me.999"
    assert "s4.model_evidence_not_permitted" in _oracle(_resign(p2), ANCHOR)


def test_attack_cross_plane_baseline_drift() -> None:
    """Fabricated baseline unsupported/revision/snapshot must fail."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_rows"][0]["source_revision_id"] = "rev.FAKE"
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_audit_mirror_drift() -> None:
    """Audit worker rows must equal the root projection (no audit-only drift)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["worker_audit_rows"][0]["session_id"] = "stale.session"
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_joint_authority_claim_rewrite_all_dimensions() -> None:
    """Joint authority+claim rewrites for all seven verification dimensions
    must each fail."""
    base = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    attempts = [
        ("identity", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_finding_identities"].update(
                {"artifact:a1": ["risk-NOT"]})),
        ("version", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_source_versions"].update({"artifact:a1": "rev.WRONG"})),
        ("date", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_date_windows"].update({"artifact:a1": "2099-01-01"})),
        ("unit", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_unit_contracts"].update({"artifact:a1": "unit.other"})),
        ("source", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_authorized_source_locators"].update(
                {"artifact:a1": ["loc.other"]})),
        ("rule", lambda p: p["audit_inspector"]["digest_context"][
            "artifact_rule_versions"].update({"artifact:a1": "9.9"})),
        ("artifact_integrity", lambda p: p["audit_inspector"]["digest_context"][
            "output_digests"].update({"artifact:a1": "f" * 64})),
    ]
    for name, mutate in attempts:
        p = copy.deepcopy(base)
        mutate(p)
        errs = _oracle(_resign(p), ANCHOR)
        assert "s4.verification_label_only" in errs, (name, errs)


def test_attack_packet_rewrite_cannot_redefine_truth() -> None:
    """A coordinated packet rewrite that changes claims AND re-signs must still
    fail because the external anchor is authoritative."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["raw_artifacts"][0]["parsed_output_hash"] = "f" * 64
    p["raw_artifacts"][0]["declared_output_hash"] = "f" * 64
    p["worker_views"][0]["declared_output_hash"] = "f" * 64
    p["audit_inspector"]["digest_context"]["output_digests"]["artifact:a1"] = "f" * 64
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.anchor_claim_drift" in errs or \
        "s4.parsed_output_hash_mismatch" in errs, errs


def test_attack_combined_anchor_rewrite_all_authority_claims() -> None:
    """Holding the external anchor/pin fixed, joint rewrite of packet
    project/receipt/journey/anchor-hash and all other authority claims must
    fail with anchor codes."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    # packet project / receipt / journey / anchor-hash claims rewritten + re-signed.
    p["risk_identity"]["project_ref"] = "project.OTHER"
    p["authority_receipt"]["project_ref"] = "project.OTHER"
    p["journey_link"]["deep_link_project_ref"] = "project.OTHER"
    p["anchor_identity_hash"] = "0" * 64
    errs = _oracle(_resign(p), ANCHOR)
    assert any(c in errs for c in ("s4.anchor_identity_mismatch",
                                   "s4.anchor_claim_drift",
                                   "s4.receipt_hash_mismatch")), errs


def test_attack_adjudication_audit_deleted() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["adjudication_audit"] = []
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_reviewed_artifact_refs_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["adjudication_row"]["reviewed_artifact_refs"] = ["artifact:ghost"]
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_raw_artifact_ref_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"][0]["raw_artifact_ref"] = "raw:ghost"
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_verification_ref_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"][0]["verification_ref"] = "verification:ghost"
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_risk_identity_hash_mutation() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["risk_identity_hash"] = "0" * 64
    assert "s4.anchor_claim_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_noncritical_spine_ref_mutation() -> None:
    """spine_ref is bound to the external anchor for EVERY severity."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["spine_ref"] = "spine.other"
    assert "s4.anchor_claim_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_model_evidence_output_hash_mutation() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["model_evidence"]["output_hash"] = "0" * 64
    assert "s4.model_evidence_not_permitted" in _oracle(_resign(p), ANCHOR)


def test_attack_model_evidence_model_version_mutation() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["model_evidence"]["model_version"] = "9.9"
    assert "s4.model_evidence_not_permitted" in _oracle(_resign(p), ANCHOR)


def test_attack_baseline_exact_rebuild_combined() -> None:
    """confirmed/source_rechecked/rev.1/snap.s1 -> unsupported/content_match/
    rev.fabricated/snap.fabricated must fail against the raw projection."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_rows"][0].update({
        "state": "unsupported", "reason_codes": ["content_match"],
        "source_revision_id": "rev.fabricated", "snapshot_id": "snap.fabricated"})
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_history_kinds_single_adjudication() -> None:
    """single_analysis must not contain an adjudication_recorded event."""
    p = copy.deepcopy(VMOD.build_sample_packet("single_analysis", ANCHOR))
    p["history_log"]["entries"].append({
        "entry_id": "hX", "seq": 99, "kind": "adjudication_recorded",
        "payload_ref": "payload.hX", "prior_entry_hash": "0" * 64,
        "entry_hash": "0" * 64})
    p["history_log"]["head_seq"] = 99
    p["history_log"]["head_hash"] = "0" * 64
    assert "s4.history_append_only_violation" in _oracle(_resign(p), ANCHOR)


def test_attack_history_kinds_zero_nonempty() -> None:
    """no_ensemble must have an empty history log."""
    p = copy.deepcopy(VMOD.build_sample_packet("no_ensemble", ANCHOR))
    p["history_log"] = {"history_ref": "history:s4.0", "head_seq": 1,
                        "head_hash": "0" * 64,
                        "entries": [{"entry_id": "h1", "seq": 1,
                                     "kind": "attempt_bound",
                                     "payload_ref": "p1",
                                     "prior_entry_hash": "genesis",
                                     "entry_hash": "0" * 64}]}
    assert "s4.history_append_only_violation" in _oracle(_resign(p), ANCHOR)


def test_attack_illegal_severity_zh() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["severity_zh"] = "超高"
    assert "s4.enum_value_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_illegal_domain_zh() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["domain_zh"] = "非法域"
    assert "s4.enum_value_mismatch" in _oracle(_resign(p), ANCHOR)


def test_attack_reorder_worker_views() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"] = list(reversed(p["worker_views"]))
    assert "s4.cardinality_not_0_1_n" in _oracle(_resign(p), ANCHOR)


def test_attack_reorder_audience_worker_summaries() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audience_inspector"]["worker_ordinal_summaries"] = list(reversed(
        p["audience_inspector"]["worker_ordinal_summaries"]))
    assert "s4.ordinal_mapping_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_baseline_row_ref_grammar() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_rows"][0]["row_ref"] = "baseline-row:ghost:ghost"
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


# ---------------------------------------------------------------------------
# D-class: every declared audit/worker/audience leaf is reconstructed
# ---------------------------------------------------------------------------


def test_attack_audit_raw_bytes_sha_mutation() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["worker_audit_rows"][0]["raw_bytes_sha256"] = "f" * 64
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_audit_parsed_output_hash_mutation() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["worker_audit_rows"][0]["parsed_output_hash"] = "f" * 64
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_packet_fingerprints_arbitrary() -> None:
    """Fingerprints must be actual canonical hashes with the frozen recipe;
    an arbitrary SORTED-UNIQUE value fails even after the audit hash is
    recomputed (a non-sorted array is a structural failure first)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audit_inspector"]["packet_fingerprints"] = sorted(
        [f"a:{'0' * 64}", f"b:{'0' * 64}", f"c:{'0' * 64}", f"d:{'0' * 64}"])
    # recompute the audit hash over the tampered audit (no resign refresh).
    p["audit_content_hash"] = VMOD._audit_content_hash(p["audit_inspector"])
    p["packet_id"] = f"{VMOD.PACKET_ID_PREFIX}:{p['audience_content_hash']}"
    errs = _oracle(p, ANCHOR)
    assert "s4.cross_plane_projection_drift" in errs, errs


def test_attack_finding_ids_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"][0]["finding_ids"] = ["ghost"]
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_assessment_row_refs_empty() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"][0]["assessment_row_refs"] = []
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_gap_ids_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["worker_views"][0]["gap_ids"] = ["ghost"]
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_audience_baseline_rows_zh_deleted() -> None:
    """Deleting a required schema leaf is a structural/type failure (B
    short-circuit -> schema_key_mismatch) before any semantic projection."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audience_inspector"].pop("baseline_rows_zh")
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.schema_key_mismatch" in errs, errs


def test_attack_audience_baseline_state_falsified() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audience_inspector"]["baseline_rows_zh"][0]["state_zh"] = "未确认"
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_audience_verification_negated() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["audience_inspector"]["worker_ordinal_summaries"][0][
        "verification_zh"] = "七维验证未执行"
    assert "s4.cross_plane_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_journey_event_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["journey_link"]["deep_link_event_ref"] = "ghost"
    assert "s4.anchor_claim_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_journey_visit_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["journey_link"]["deep_link_visit_ref"] = "ghost"
    assert "s4.anchor_claim_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_journey_available_not_derived() -> None:
    """journey_available cannot be packet-chosen; it is derived from complete
    accepted target identity."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["journey_link"]["journey_available"] = False
    p["audience_inspector"]["journey_available"] = False
    p["audience_inspector"]["journey_unavailable_reason_zh"] = "无法定位"
    assert "s4.journey_fallback_not_none" in _oracle(_resign(p), ANCHOR)


def test_attack_query_joint_rewrite() -> None:
    """Packet+audience Query text copies are projections; the canonical content
    is the externally accepted QueryDraft."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["query_draft_row"].update({"basis_zh": "X", "finding_zh": "Y",
                                 "action_zh": "Z"})
    p["audience_inspector"].update({"query_basis_zh": "X", "query_finding_zh": "Y",
                                    "query_action_zh": "Z"})
    assert "s4.query_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_query_risk_ref_ghost() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["query_draft_row"]["risk_ref"] = "d09_marker:ghost"
    assert "s4.query_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_baseline_origin_artifact_hash() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_items"][0]["origin_artifact_hash"] = "0" * 64
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def _baseline_attack_rehash(p: Dict[str, Any]) -> None:
    """Recompute the R4 claimed_content_hash after a baseline-item mutation so
    the R4 dataclass accepts the mutated item (reviewer-style rewrite)."""
    ec = VMOD._r4_contracts()
    item = p["baseline_items"][0]
    obj = ec.ReferenceBaselineItem(item_id=item["item_id"],
                                   source_kind=item["source_kind"],
                                   source_locator_ids=tuple(item["source_locator_ids"]),
                                   source_revision_id=item["source_revision_id"],
                                   snapshot_id=item["snapshot_id"],
                                   claimed_identity=item["claimed_identity"],
                                   temporal_window=item["temporal_window"],
                                   claimed_content_hash="",
                                   origin_artifact_hash=item["origin_artifact_hash"])
    item["claimed_content_hash"] = obj.claimed_content_hash


def test_attack_baseline_claimed_identity() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_items"][0]["claimed_identity"] = "risk-FAKE"
    _baseline_attack_rehash(p)
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_baseline_temporal_window() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_items"][0]["temporal_window"] = "2099-01-01"
    _baseline_attack_rehash(p)
    assert "s4.baseline_projection_drift" in _oracle(_resign(p), ANCHOR)


def test_attack_baseline_multi_leaf_coordinated_rewrite() -> None:
    """A coordinated multi-leaf baseline rewrite (recompute content hash,
    mirror into rows, resign) must fail while the anchor stays fixed."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["baseline_items"][0].update({
        "source_revision_id": "rev.fab", "snapshot_id": "snap.fab",
        "claimed_identity": "risk-FAKE", "temporal_window": "2099-01-01",
        "origin_artifact_hash": "0" * 64})
    # recompute the R4 content hash to mimic a coordinated rewrite.
    ec = VMOD._r4_contracts()
    item = p["baseline_items"][0]
    obj = ec.ReferenceBaselineItem(item_id=item["item_id"],
                                   source_kind=item["source_kind"],
                                   source_locator_ids=tuple(item["source_locator_ids"]),
                                   source_revision_id=item["source_revision_id"],
                                   snapshot_id=item["snapshot_id"],
                                   claimed_identity=item["claimed_identity"],
                                   temporal_window=item["temporal_window"],
                                   claimed_content_hash="",
                                   origin_artifact_hash=item["origin_artifact_hash"])
    item["claimed_content_hash"] = obj.claimed_content_hash
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.baseline_projection_drift" in errs, errs


# ---------------------------------------------------------------------------
# single-state fixture gates (canonical token, strict cardinality/history)
# ---------------------------------------------------------------------------


def test_single_analysis_fixture_is_exactly_one_attempt() -> None:
    p = VMOD.build_sample_packet("single_analysis", ANCHOR)
    assert p["ensemble_projection_state"] == "single_analysis"
    assert p["ensemble_size"] == 1
    assert len(p["worker_views"]) == 1
    assert len(p["raw_artifacts"]) == 1
    assert len(p["verification_rows"]) == 1
    # no conflict consensus, no adjudicator.
    assert p["adjudication_row"]["present"] is False
    assert p["audit_inspector"]["adjudication_audit"] == []
    # single-state history kinds (no adjudication_recorded).
    kinds = [e["kind"] for e in p["history_log"]["entries"]]
    assert "adjudication_recorded" not in kinds
    assert "attempt_bound" in kinds and "verification_recorded" in kinds


def test_zero_fixture_empty_history() -> None:
    p = VMOD.build_sample_packet("no_ensemble", ANCHOR)
    assert p["ensemble_projection_state"] == "no_ensemble"
    assert p["ensemble_size"] == 0
    assert p["history_log"]["entries"] == []
    assert p["adjudication_row"]["present"] is False


def test_declared_leaf_coverage_gate() -> None:
    """Every declared audit/worker/audience leaf must be reconstructed by the
    verifier (a NEW unchecked leaf fails this gate)."""
    schema = SCHEMA["objects"]
    # The verifier's declared-leaf reconstruction covers these object leaves.
    covered = {
        "R5S4AuditInspector": {"worker_audit_rows", "packet_fingerprints",
                               "adjudication_audit", "conflict_audit",
                               "history_audit", "receipt_content_hash",
                               "authority_receipt_ref", "digest_context",
                               "model_evidence", "verification_audit_rows"},
        "R5S4WorkerView": {"finding_ids", "gap_ids", "assessment_row_refs",
                           "raw_artifact_ref", "verification_ref",
                           "declared_output_hash", "input_content_hash",
                           "model_id", "model_version", "role",
                           "independent_context_hash", "binding_id",
                           "session_id", "output_artifact_ref", "attempt_id",
                           "claimed_date_window", "claimed_rule_id",
                           "claimed_rule_version", "claimed_source_revision",
                           "claimed_unit_contract", "ordinal", "ordinal_zh"},
        "R5S4AudienceInspector": {"baseline_rows_zh", "worker_ordinal_summaries",
                                  "journey_available", "journey_link_zh",
                                  "journey_unavailable_reason_zh",
                                  "query_basis_zh", "query_finding_zh",
                                  "query_action_zh", "query_pd_wording_zh",
                                  "adjudication_explanation_zh",
                                  "adjudication_status_zh",
                                  "audience_contract_id", "basis_zh",
                                  "center_display_zh", "change_state_zh",
                                  "consensus_zh", "counterevidence_zh",
                                  "cutoff_display_zh", "domain_zh",
                                  "history_summary_zh", "project_display_zh",
                                  "risk_title_zh", "severity_zh",
                                  "source_one_hop_zh", "subject_display_zh",
                                  "support_evidence_zh"},
        "R5S4AuditWorkerRow": {"raw_bytes_sha256", "parsed_output_hash",
                               "declared_output_hash", "attempt_id",
                               "binding_id", "independent_context_hash",
                               "input_content_hash", "model_id",
                               "model_version", "output_artifact_ref",
                               "role", "session_id"},
    }
    # every leaf under these objects must be listed as covered.
    for obj_name, fields in covered.items():
        for leaf in schema[obj_name]:
            assert leaf in fields, f"uncovered declared leaf {obj_name}.{leaf}"


# ---------------------------------------------------------------------------
# valid fixtures pass [] against the anchor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["no_ensemble", "single_analysis",
                                  "multi_analysis", "mutual", "graded"])
def test_base_fixture_passes_oracle(mode: str) -> None:
    errs = _oracle(VMOD.build_sample_packet(mode, ANCHOR), ANCHOR)
    assert errs == [], f"{mode} must pass [], got {errs}"


def test_critical_always_rejects_without_external_authority() -> None:
    """No accepted external critical authority exists in this scope: every
    critical packet must reject with the exact missing/deferred code."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    p["risk_identity"]["severity"] = "critical"
    p["risk_identity"]["severity_zh"] = "紧急"
    errs = _oracle(_resign(p), ANCHOR)
    assert "s4.critical_severity_authority_missing" in errs, errs


def test_seven_dimensions_recomputed_by_r4() -> None:
    p = VMOD.build_sample_packet("multi", ANCHOR)
    ctx = VMOD._typed_digest_context(p["audit_inspector"])
    ens = VMOD._r4_ensemble()
    for view in p["worker_views"]:
        output = VMOD._reconstruct_worker_output(p, view["attempt_id"])
        attempt = VMOD._typed_attempt(view, p["ensemble_id"])
        recomputed = ens.verify_attempt(attempt, output, ctx)
        stored = next(r for r in p["verification_rows"]
                      if r["attempt_id"] == view["attempt_id"])
        assert set(recomputed.checked_dimensions) == VMOD.SEVEN_DIMENSIONS
        assert stored["result"] == recomputed.result
        assert stored["failure_reason_codes"] == sorted(
            set(recomputed.failure_reason_codes))
        assert stored["verification_id"] == recomputed.verification_id


def test_conflict_set_rebuilt_by_r4_derive() -> None:
    ens = VMOD._r4_ensemble()
    for mode, expect in [("multi", {"shared_finding", "baseline_miss"}),
                         ("single", {"single_model_new", "baseline_miss"}),
                         ("mutual", {"mutual_negation", "shared_finding",
                                     "baseline_miss"}),
                         ("graded", {"graded_conflict", "baseline_miss"})]:
        p = VMOD.build_sample_packet(mode, ANCHOR)
        attempts = [VMOD._typed_attempt(v, p["ensemble_id"])
                    for v in p["worker_views"]]
        outputs = {v["attempt_id"]: VMOD._reconstruct_worker_output(p, v["attempt_id"])
                   for v in p["worker_views"]}
        items = [VMOD._typed_baseline_item(b) for b in p["baseline_items"]]
        derived = ens.derive_conflicts(attempts=attempts, worker_outputs=outputs,
                                       baseline_items=items)
        assert {c.relation for c in derived} == expect, mode


def test_raw_parsed_hash_recomputed_from_bytes() -> None:
    p = VMOD.build_sample_packet("multi", ANCHOR)
    for artifact in p["raw_artifacts"]:
        raw = base64.b64decode(artifact["raw_bytes_b64"], validate=True)
        assert artifact["raw_bytes_sha256"] == hashlib.sha256(raw).hexdigest()
        assert artifact["parsed_output_hash"] == \
            VMOD._recompute_parsed_hash(p, artifact["attempt_id"])
        assert artifact["parsed_output_hash"] != artifact["raw_bytes_sha256"]


def test_model_evidence_real_r4_role() -> None:
    p = VMOD.build_sample_packet("multi", ANCHOR)
    me = p["audit_inspector"]["model_evidence"]
    assert me["role"] in VMOD.MODEL_EVIDENCE_ROLES
    d10 = VMOD._r4_d10()
    obj = d10.ModelEvidence(
        model_evidence_id=me["model_evidence_id"], role=me["role"],
        permitted_leaf=me["permitted_leaf"], model_id=me["model_id"],
        model_version=me["model_version"], output_hash=me["output_hash"],
        ensemble_id=me["ensemble_id"],
        independent_context_hash=me["independent_context_hash"],
        adjudication_state=me["adjudication_state"])
    assert obj.role in ("candidate_explanation", "counterevidence_suggestion")


# ---------------------------------------------------------------------------
# registry gates
# ---------------------------------------------------------------------------


def test_registry_exactly_97_rows_and_quota() -> None:
    assert len(CHALLENGE_CASES) == 97
    ids = [c["case_id"] for c in CHALLENGE_CASES]
    assert len(set(ids)) == len(ids)
    counts: Dict[str, int] = {}
    for case in CHALLENGE_CASES:
        counts[case["category"]] = counts.get(case["category"], 0) + 1
    assert counts == EXPECTED_CHALLENGE_QUOTA, counts


def test_registry_matches_overlay_spec_and_codes() -> None:
    spec = OVERLAY["challenge_spec"]
    assert spec["total_exact"] == 97
    assert spec["categories"] == EXPECTED_CHALLENGE_QUOTA
    codes = set(OVERLAY["enums"]["error_code"])
    for case in CHALLENGE_CASES:
        code = case["expected_typed_outcome_or_error"]
        assert code.startswith("s4.") and code in codes, case["case_id"]


def test_registry_mutations_all_unique() -> None:
    sigs = [VMOD._canonical_bytes(c["single_mutation"]).decode("utf-8")
            for c in CHALLENGE_CASES]
    assert len(sigs) == len(set(sigs))


def test_registry_oracle_contracts_all_unique() -> None:
    sigs = [VMOD._canonical_bytes(c["stage_oracle_contract"]).decode("utf-8")
            for c in CHALLENGE_CASES]
    assert len(sigs) == len(set(sigs))


def _collect_test_nodeids() -> List[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         str(Path(__file__))],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    return [line for line in result.stdout.splitlines()
            if "::test_challenge_case[" in line]


def test_every_challenge_locator_is_a_real_nodeid() -> None:
    nodeids = _collect_test_nodeids()
    for case in CHALLENGE_CASES:
        locator = case["stage_oracle_contract"]["test_locator"]
        assert locator == (
            "poc/medical_monitoring_ai_native_r5/tests/"
            "test_s4_contract_artifacts.py::test_challenge_case["
            f"{case['case_id']}]"), locator
        assert any(case["case_id"] in node for node in nodeids), (
            f"locator not a real collected nodeid: {case['case_id']}")


def _fixture_anchor(precondition: str) -> Dict[str, Any]:
    return ANCHOR


@pytest.mark.parametrize("case", CHALLENGE_CASES, ids=lambda c: c["case_id"])
def test_challenge_case(case: Dict[str, Any]) -> None:
    """Every row: base passes [] -> one mutation -> exactly one s4.* code."""
    mutation = case["single_mutation"]
    expected = case["expected_typed_outcome_or_error"]
    if mutation["path"].startswith("artifacts."):
        rejection = _run_artifact_governance(mutation)
        assert expected in rejection, (case["case_id"], rejection)
        assert set(VMOD._extract_codes(rejection)) == {expected}, (
            case["case_id"], rejection)
        return
    anchor = _fixture_anchor(case.get("precondition", "multi_analysis packet"))
    packet = VMOD._registry_fixture(case.get("precondition", "multi_analysis packet"),
                                    VMOD.build_sample_packet, anchor)
    base_errs = _oracle(VMOD._resign(VMOD._rebuild_derived(packet)), anchor)
    assert base_errs == [], (case["case_id"], sorted(set(base_errs)))
    inner = dict(mutation)
    inner["path"] = mutation["path"][len("packet."):]
    VMOD._apply_mutation(packet, inner)
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(packet)), anchor)
    assert set(errs) == {expected}, (
        case["case_id"], f"expected {expected}, got {sorted(set(errs))}")


_ARTIFACT_ROLES = {"overlay": "exact_overlay.json", "schema": "packet_schema.json"}


def _run_artifact_governance(mutation: Dict[str, Any]) -> str:
    parts = mutation["path"].split(".")
    assert parts[0] == "artifacts", mutation["path"]
    role = parts[1]
    file_name = _ARTIFACT_ROLES[role]
    data = copy.deepcopy(_load(ARTIFACTS / file_name))
    inner_path = ".".join(parts[2:]) or parts[1]
    inner = {"op": mutation["op"], "path": inner_path,
             "value": mutation.get("value")}
    if "." in inner_path:
        VMOD._apply_mutation(data, inner)
    else:
        data[inner_path] = inner["value"]
    maps = {m: VMOD._parse_classes(p, ROOT)
            for m, p in VMOD.MODULE_FILES.items()}
    try:
        if role == "overlay":
            VMOD._validate_overlay(data, maps)
        else:
            VMOD._validate_schema(data, maps)
    except VMOD.VerificationError as error:
        return str(error)
    return ""


# ---------------------------------------------------------------------------
# independent family probes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mutation,expected", [
    ({"op": "set", "path": "packet.ensemble_projection_state", "value": "no_ensemble"},
     "s4.cardinality_not_0_1_n"),  # input_content_hash forbidden_when no_ensemble (structural first)
    ({"op": "set", "path": "packet.worker_views[0].binding_id", "value": "worker.b.a2"},
     "s4.duplicate_worker_binding"),
    ({"op": "set", "path": "packet.raw_artifacts[0].raw_bytes_b64",
      "value": base64.b64encode(b'{"attempt":"a1","x":1}').decode()},
     "s4.raw_output_rewritten"),
    ({"op": "set", "path": "packet.baseline_rows[0].source_recheck_locator_ids", "value": []},
     "s4.baseline_recheck_missing"),
    ({"op": "set", "path": "packet.verification_rows[0].checked_dimensions",
      "value": sorted(VMOD.SEVEN_DIMENSIONS - {"identity"})},
     "s4.verification_label_only"),
    ({"op": "set", "path": "packet.conflict_rows[3].hidden", "value": True},
     "s4.high_risk_hidden"),
    ({"op": "set", "path": "packet.adjudication_row.binding_id", "value": "worker.b.a1"},
     "s4.worker_self_adjudication"),
    ({"op": "set", "path": "packet.query_draft_row.send_status", "value": "draft"},
     "s4.query_task_semantics"),
    ({"op": "set", "path": "packet.history_log.entries[1].prior_entry_hash", "value": "0" * 64},
     "s4.history_chain_break"),
    ({"op": "set", "path": "packet.journey_link.fallback_policy", "value": "nearest_site"},
     "s4.journey_fallback_not_none"),
    ({"op": "set", "path": "packet.audience_inspector.model_id", "value": "m1"},
     "s4.audience_hash_contains_audit_leaf"),
])
def test_family_probes_fire(mutation: Dict[str, Any], expected: str) -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi", ANCHOR))
    inner = dict(mutation)
    inner["path"] = mutation["path"][len("packet."):]
    VMOD._apply_mutation(p, inner)
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert expected in errs, f"expected {expected}, got {sorted(set(errs))}"


def test_five_conflict_relations_covered() -> None:
    assert set(OVERLAY["enums"]["conflict_relation"]) == {
        "shared_finding", "single_model_new", "graded_conflict",
        "mutual_negation", "baseline_miss"}


def test_seven_dimensions_exact() -> None:
    dims = OVERLAY["enums"]["verification_dimension"]
    assert len(dims) == 7 and set(dims) == VMOD.SEVEN_DIMENSIONS


def test_source_matrix_covers_all_schema_leaves() -> None:
    matrix = {row["leaf"] for row in OVERLAY["source_matrix"]}
    objects = SCHEMA["objects"]
    expected = set(VMOD.EXPECTED_DEFERRED_LEAVES)
    for obj_name, fields in objects.items():
        for field_name, descriptor in fields.items():
            ftype = descriptor.get("type", "str")
            if ftype in objects or ftype.startswith("import:"):
                continue
            expected.add(f"{obj_name}.{field_name}")
    for leaf in expected:
        assert leaf in matrix, f"schema leaf missing from source matrix: {leaf}"


def test_model_evidence_role_enum_real() -> None:
    assert OVERLAY["enums"]["model_evidence_role"] == [
        "candidate_explanation", "counterevidence_suggestion"]


# ---------------------------------------------------------------------------
# generator / verifier gates
# ---------------------------------------------------------------------------


def test_generator_check_is_deterministic() -> None:
    result = _run(GENERATOR, "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_generator_reproducibility() -> None:
    assert _run(GENERATOR, "--check").stdout == _run(GENERATOR, "--check").stdout


def test_verifier_normal_mode() -> None:
    result = _run(VERIFIER, "--anchor", str(ANCHOR_PATH))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["tamper_probes_rejected"] >= 13
    assert payload["registry_rows_executed"] == 97


def test_verifier_optimized_mode() -> None:
    result = _run(VERIFIER, "--anchor", str(ANCHOR_PATH), optimize=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_verifier_results_identical_normal_and_optimized() -> None:
    normal = json.loads(_run(VERIFIER, "--anchor", str(ANCHOR_PATH)).stdout)
    optimized = json.loads(_run(VERIFIER, "--anchor", str(ANCHOR_PATH),
                                optimize=True).stdout)
    assert normal == optimized


# ---------------------------------------------------------------------------
# immutable-SHA / 8911 / boundary
# ---------------------------------------------------------------------------


def test_8911_service_not_started() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        assert sock.connect_ex(("127.0.0.1", 8911)) != 0
    finally:
        sock.close()


def test_no_s4_runtime_imported() -> None:
    source = (ROOT / "poc" / "medical_monitoring_ai_native_r5" / "src"
              / "mm_r5").glob("*.py")
    assert not any("s4" in path.name.lower() for path in source)


def test_artifact_files_canonical_nfc_json() -> None:
    for name in ("exact_overlay.json", "packet_schema.json",
                 "source_pins.json", "manifest.json", "challenge_registry.json",
                 "accepted_authority_anchor.json"):
        path = ARTIFACTS / name
        assert path.read_bytes() == VMOD._canonical_bytes(_load(path)), name
    # the anchor file is a deterministic canonical JSON but is NOT produced by
    # the generator (checked separately in test_anchor_is_external_not_generator_owned).


def test_r4_r5_sources_unchanged_sha() -> None:
    pins = _load(ARTIFACTS / "source_pins.json")
    for item in pins["sources"]:
        target = ROOT / item["path"]
        assert target.is_file(), item["path"]
        assert hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"], (
            f"pinned source drifted: {item['path']}")


def test_anchor_is_external_not_generator_owned() -> None:
    """The external anchor must NOT be part of the generator-owned artifact
    set/manifest; the generator cannot create, rewrite, or sign it."""
    manifest = _load(ARTIFACTS / "manifest.json")
    roles = {a["role"] for a in manifest["artifacts"]}
    assert "authority_anchor" not in roles
    assert hashlib.sha256(ANCHOR_PATH.read_bytes()).hexdigest() == ANCHOR_SHA256
    p = VMOD.build_sample_packet("multi", ANCHOR)
    assert p["authority_anchor_ref"] == "anchor:" + ANCHOR["anchor_identity_hash"]
    assert p["anchor_identity_hash"] == ANCHOR["anchor_identity_hash"]
    # accepted receipt identity binds the real R5 exact-contract JSON raw SHA.
    assert ANCHOR["accepted_receipt_identity"].endswith(
        VMOD.R5_EXACT_CONTRACT_SHA)
    assert VMOD.R5_EXACT_CONTRACT_SHA == \
        "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949"


def test_anchor_identity_hash_is_canonical_self() -> None:
    body = dict(ANCHOR)
    body.pop("anchor_identity_hash", None)
    assert ANCHOR["anchor_identity_hash"] == VMOD._r4_style_hash(body)


# ---------------------------------------------------------------------------
# A. acyclic hash DAG: independent recompute + one-field drift checks
# ---------------------------------------------------------------------------


def _canonical(value: Any) -> bytes:
    """Test-side canonicalization (utf8_nfc_sorted_keys_compact_json_newline)
    implemented WITHOUT any verifier helper: the hash DAG is self-describing."""
    def nfc(v: Any) -> Any:
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        if isinstance(v, list):
            return [nfc(i) for i in v]
        if isinstance(v, dict):
            return {nfc(k): nfc(val) for k, val in v.items()}
        return v
    return (json.dumps(nfc(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n"
            ).encode("utf-8")


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _independent_hash_recompute(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute EVERY hash from the schema-declared DAG recipe, reading only
    the generated machine schema (no verifier helper functions)."""
    dag = SCHEMA["hash_dag"]
    recomputed = {
        "audience_content_hash": _canonical_hash(
            packet["audience_inspector"]),
    }
    audit_excluded = set(dag["audit_content_hash"]["excluded_leaves"])
    recomputed["audit_content_hash"] = _canonical_hash(
        {k: v for k, v in packet["audit_inspector"].items()
         if k not in audit_excluded})
    recomputed["receipt_content_hash"] = _canonical_hash(
        packet["authority_receipt"])
    recomputed["packet_id"] = f"{dag['packet_id']['ref_prefix']}:" \
        + recomputed["audience_content_hash"]
    fp_parts = {
        "audience_content_hash": recomputed["audience_content_hash"],
        "receipt_content_hash": recomputed["receipt_content_hash"],
        "packet_id": recomputed["packet_id"],
        "risk_identity_hash": packet["risk_identity"]["risk_identity_hash"],
    }
    fp_recipe = dag["packet_fingerprints"]["recipe"]
    recomputed["packet_fingerprints"] = sorted(
        _fill_recipe(key, fp_parts) for key in fp_recipe)
    excluded = set(dag["packet_integrity_hash"]["excluded_root_keys"])
    recomputed["packet_integrity_hash"] = _canonical_hash(
        {k: v for k, v in packet.items() if k not in excluded})
    return recomputed


def _fill_recipe(recipe: str, parts: Dict[str, str]) -> str:
    """'audience:<audience_content_hash>' -> 'audience:<hash-value>'."""
    prefix, field = recipe.split(":", 1)
    assert field.startswith("<") and field.endswith(">"), recipe
    return f"{prefix}:{parts[field[1:-1]]}"


@pytest.mark.parametrize("mode", ["no_ensemble", "single_analysis",
                                  "multi_analysis"])
def test_hash_dag_independent_recompute(mode: str) -> None:
    """The generated machine schema DAG alone must deterministically rebuild
    every packet hash byte-for-byte for all valid zero/single/N fixtures."""
    p = VMOD.build_sample_packet(mode, ANCHOR)
    p = VMOD._resign(VMOD._rebuild_derived(p))
    recomputed = _independent_hash_recompute(p)
    assert p["audience_content_hash"] == recomputed["audience_content_hash"]
    assert p["audit_content_hash"] == recomputed["audit_content_hash"]
    assert p["receipt_content_hash"] == recomputed["receipt_content_hash"]
    assert p["packet_id"] == recomputed["packet_id"]
    assert p["audit_inspector"]["packet_fingerprints"] == \
        recomputed["packet_fingerprints"]
    assert p["packet_integrity_hash"] == recomputed["packet_integrity_hash"]


def test_hash_dag_aclaimed_names_exact() -> None:
    """Source matrix / DAG must describe the ACTUAL recipe (audience/receipt/
    packet-id/risk-identity), never legacy audience/audit/integrity/packet."""
    matrix = {row["leaf"]: row["path"] for row in OVERLAY["source_matrix"]}
    desc = matrix["R5S4AuditInspector.packet_fingerprints"]
    assert "audience:<audience_content_hash>" in desc
    assert "receipt:<receipt_content_hash>" in desc
    assert "packet:<packet_id>" in desc
    assert "risk_identity:<risk_identity_hash>" in desc
    inputs = desc.split("sorted([", 1)[1].split("])", 1)[0]
    assert "audit_content_hash" not in inputs
    assert "integrity" not in inputs
    dag = SCHEMA["hash_dag"]
    assert dag["audit_content_hash"]["excluded_leaves"] == \
        ["packet_fingerprints"]
    assert dag["packet_id"]["depends_on"] == ["audience_content_hash"]
    assert dag["packet_fingerprints"]["depends_on"] == [
        "audience_content_hash", "receipt_content_hash", "packet_id",
        "risk_identity_hash"]


def test_audit_content_hash_schema_matches_recipe() -> None:
    """The schema constraint names the acyclic exclusion explicitly, so the
    independent computation over the declared recipe equals the stored hash."""
    p = VMOD.build_sample_packet("multi_analysis", ANCHOR)
    p = VMOD._resign(VMOD._rebuild_derived(p))
    assert _canonical_hash(
        {k: v for k, v in p["audit_inspector"].items()
         if k != "packet_fingerprints"}) == p["audit_content_hash"]
    assert _canonical_hash(p["audit_inspector"]) != p["audit_content_hash"]


_HASH_DRIFT_CASES = [
    # (path, expected single code)
    ("packet.audience_content_hash", "s4.audience_hash_contains_audit_leaf"),
    ("packet.audit_content_hash", "s4.audience_audit_leak"),
    ("packet.receipt_content_hash", "s4.receipt_hash_mismatch"),
    ("packet.packet_id", "s4.packet_id_grammar_mismatch"),
    ("packet.packet_integrity_hash", "s4.hash_recipe_cycle"),
    ("packet.risk_identity.risk_identity_hash", "s4.anchor_claim_drift"),
]


def _refresh_dependents(p: Dict[str, Any],
                        skip: frozenset = frozenset()) -> None:
    """Recompute the derived projections EXCEPT the drifted target field(s)
    from the packet's CURRENT fields so a one-field hash drift is the ONLY
    inconsistency the oracle sees."""
    dag = SCHEMA["hash_dag"]
    if "packet_fingerprints" not in skip:
        p["audit_inspector"]["packet_fingerprints"] = sorted([
            f"audience:{p['audience_content_hash']}",
            f"receipt:{p['receipt_content_hash']}",
            f"packet:{p['packet_id']}",
            f"risk_identity:{p['risk_identity']['risk_identity_hash']}",
        ])
    # the audit receipt mirror is a dependent of the packet receipt hash:
    # refresh it BEFORE the audit hash recompute (no-op when unchanged).
    p["audit_inspector"]["receipt_content_hash"] = \
        p["receipt_content_hash"]
    p["audit_inspector"]["authority_receipt_ref"] = \
        f"{VMOD.RECEIPT_REF_PREFIX}{p['receipt_content_hash']}"
    if "audit_content_hash" not in skip:
        p["audit_content_hash"] = _canonical_hash(
            {k: v for k, v in p["audit_inspector"].items()
             if k != "packet_fingerprints"})
    if "packet_integrity_hash" not in skip:
        excluded = set(dag["packet_integrity_hash"]["excluded_root_keys"])
        p["packet_integrity_hash"] = _canonical_hash(
            {k: v for k, v in p.items() if k not in excluded})


@pytest.mark.parametrize("path,expected", _HASH_DRIFT_CASES,
                         ids=[p.split(".")[-1] for p, _ in _HASH_DRIFT_CASES])
def test_hash_dag_one_field_drift(path: str, expected: str) -> None:
    """A one-field drift in any hash/fingerprint input must yield exactly one
    stable closed error (mutated AFTER resign; derived projections refreshed
    so the drifted field is the only inconsistency)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p = VMOD._resign(VMOD._rebuild_derived(p))
    target = path.split(".")[-1]
    inner = {"op": "set", "path": path[len("packet."):], "value": "f" * 64}
    VMOD._apply_mutation(p, inner)
    if target == "audience_content_hash":
        p["packet_id"] = f"{SCHEMA['hash_dag']['packet_id']['ref_prefix']}:" \
            + p["audience_content_hash"]
    _refresh_dependents(p, skip=frozenset({target}))
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {expected}, f"{path}: got {sorted(set(errs))}"


@pytest.mark.parametrize("entry_idx", [0, 1, 2, 3])
def test_hash_dag_fingerprint_entry_drift(entry_idx: int) -> None:
    """Each packet_fingerprints entry is a frozen-prefix label of an
    independent hash input; a one-entry drift rejects with exactly one code.
    The replacement keeps the array sorted/unique so no schema rule fires."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p = VMOD._resign(VMOD._rebuild_derived(p))
    p["audit_inspector"]["packet_fingerprints"][entry_idx] = \
        p["audit_inspector"]["packet_fingerprints"][entry_idx].split(":")[0] \
        + ":" + "0" * 64
    _refresh_dependents(p, skip=frozenset({"packet_fingerprints"}))
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {"s4.cross_plane_projection_drift"}, sorted(set(errs))


# ---------------------------------------------------------------------------
# B. typed reconstruction exception containment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mutate", [
    lambda p: p["baseline_items"][0].update(
        {"claimed_content_hash": "f" * 64}),
    lambda p: p["baseline_items"][0].update({"origin_artifact_hash": "f" * 64}),
    lambda p: p["baseline_items"][0].update({"item_id": ""}),
    lambda p: p["raw_artifacts"][0].update(
        {"raw_bytes_b64": base64.b64encode(b"not-json").decode()}),
    lambda p: p["worker_views"][0].update(
        {"independent_context_hash": "not-a-hash"}),
])
def test_no_uncaught_exception_malformed_typed_inputs(mutate: Any) -> None:
    """Malformed-but-schema-shaped values through every R4 typed
    reconstruction route must return a stable s4.* code, never raise."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    mutate(p)
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert errs, "malformed typed input must reject"
    assert all(code.startswith("s4.") for code in errs)


def test_baseline_bad_content_hash_contained() -> None:
    """Reviewer reproduction: claimed_content_hash=f*64 must return exactly
    s4.baseline_projection_drift, never an uncaught EnsembleContractError."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["claimed_content_hash"] = "f" * 64
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.baseline_projection_drift"}, sorted(set(errs))


# ---------------------------------------------------------------------------
# C. complete ModelEvidence binding (every dataclass field)
# ---------------------------------------------------------------------------


def test_model_evidence_upstream_field_coverage() -> None:
    """Every upstream d10 ModelEvidence dataclass field must be bound; a new
    upstream field with no binding fails the coverage assertion."""
    import dataclasses
    d10 = VMOD._r4_d10()
    upstream = {f.name for f in dataclasses.fields(d10.ModelEvidence)}
    assert upstream == set(VMOD.MODEL_EVIDENCE_BOUND_FIELDS), (
        upstream ^ set(VMOD.MODEL_EVIDENCE_BOUND_FIELDS))


_ME_LEAF_CASES = [
    "model_evidence_id", "role", "permitted_leaf", "model_id",
    "model_version", "evaluation_content_identity", "input_content_hash",
    "source_revision_content_pairs", "source_refs",
    "independent_context_hash", "ensemble_id", "ensemble_size",
    "member_analysis_refs", "member_analysis_ref_set_hash",
    "output_identity", "output_hash", "adjudication_state",
    "model_binding_hash",
]


@pytest.mark.parametrize("leaf", _ME_LEAF_CASES)
def test_model_evidence_every_field_one_leaf_mutation(leaf: str) -> None:
    """One-leaf mutation of EVERY ModelEvidence field must reject with the
    fixed permit/projection code (s4.model_evidence_not_permitted)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    me = p["audit_inspector"]["model_evidence"]
    if leaf == "adjudication_state":
        me[leaf] = "accepted" if me[leaf] == "pending" else "pending"
    elif leaf == "role":
        me[leaf] = "counterevidence_suggestion" if me[leaf] != \
            "counterevidence_suggestion" else "candidate_explanation"
    elif leaf == "ensemble_size":
        me[leaf] = int(me[leaf]) + 1
    elif leaf == "source_revision_content_pairs":
        me[leaf] = [{"revision_id": "rev.9", "content_hash": "f" * 64}]
    elif leaf in ("source_refs", "member_analysis_refs"):
        me[leaf] = list(me[leaf]) + ["tampered"]
    else:
        me[leaf] = "f" * 64 if isinstance(me[leaf], str) else me[leaf]
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.model_evidence_not_permitted"}, (
        leaf, sorted(set(errs)))


# ---------------------------------------------------------------------------
# D. external risk identity / change / adjudication binding
# ---------------------------------------------------------------------------


def test_risk_identity_domain_closed_projection_of_accepted() -> None:
    """Reviewer reproduction: coordinated domain/domain_zh mh/MH rewrite must
    reject with exactly s4.anchor_claim_drift."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["risk_identity"]["domain"] = "mh"
    p["risk_identity"]["domain_zh"] = "MH"
    p["audience_inspector"]["domain_zh"] = "MH"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.anchor_claim_drift"}, sorted(set(errs))


@pytest.mark.parametrize("leaf,value", [
    ("change_kind", "continued"),
    ("change_kind", "upgraded"),
    ("change_cause", "model"),
    ("change_cause", "mapping"),
])
def test_change_leaves_must_equal_accepted_instance(leaf: str, value: str) -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["risk_identity"][leaf] = value
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.anchor_claim_drift"}, (leaf, sorted(set(errs)))


def test_adjudication_binding_upstream_field_coverage() -> None:
    """Every upstream AdjudicationBinding dataclass field must be bound."""
    import dataclasses
    ens = VMOD._r4_ensemble()
    upstream = {f.name for f in dataclasses.fields(ens.AdjudicationBinding)}
    assert set(VMOD.ADJUDICATION_BOUND_FIELDS) == upstream, (
        upstream ^ set(VMOD.ADJUDICATION_BOUND_FIELDS))


@pytest.mark.parametrize("leaf,value", [
    ("binding_id", "adj.zzz"),
    ("session_id", "adj.s9"),
    ("model_id", "adj.hacker"),
    ("model_version", "9.9"),
    ("independent_context_hash", "f" * 64),
    ("outcome", "merged_supported"),
    ("outcome", "distinct_supported"),
])
def test_adjudication_binding_leaves_must_equal_accepted(leaf: str, value: str) -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["adjudication_row"][leaf] = value
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.anchor_claim_drift"}, (leaf, sorted(set(errs)))


@pytest.mark.parametrize("refs,expected", [
    (["artifact:a1"], {"s4.anchor_claim_drift"}),                 # subset
    (["artifact:a1", "artifact:a2", "artifact:a3"],
     {"s4.cross_plane_projection_drift"}),                        # superset ghost
    (["artifact:a1", "artifact:a1", "artifact:a2"],
     {"s4.schema_key_mismatch"}),                                 # duplicate
])
def test_reviewed_artifact_refs_exact_set(refs: Any, expected: Any) -> None:
    """N state: reviewed_artifact_refs must equal the exact sorted set of every
    active worker raw artifact; subset/superset/duplicate each reject with one
    stable closed code."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["adjudication_row"]["reviewed_artifact_refs"] = refs
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == expected, sorted(set(errs))


def test_reviewed_artifact_refs_exact_set_valid() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    expected = sorted(f"artifact:{w['attempt_id']}"
                      for w in p["worker_views"])
    assert p["adjudication_row"]["reviewed_artifact_refs"] == expected


# ---------------------------------------------------------------------------
# E. deterministic evidence/source Chinese projection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mutate", [
    lambda p: p["audience_inspector"].update(
        {"support_evidence_zh": ["根据 loc.src1 的检查结果，患者出现发热性中性粒细胞减少"]}),
    lambda p: p["audience_inspector"].update(
        {"support_evidence_zh": ["支持证据已核实：来源 loc.src1"]}),
    lambda p: p["audience_inspector"].update(
        {"support_evidence_zh": []}),
    lambda p: p["audience_inspector"].update(
        {"counterevidence_zh": ["根据 loc.src1 的检查结果，未见明确反证"]}),
    lambda p: p["audience_inspector"].update(
        {"counterevidence_zh": ["来源 loc.src1 已定位"]}),
    lambda p: p["audience_inspector"].update(
        {"source_one_hop_zh": "来自 loc.src1 的最新源在一跳内完成定位"}),
    lambda p: p["audience_inspector"].update(
        {"source_one_hop_zh": "来源 loc.src1 已在一跳内完成定位"}),
    lambda p: p["audience_inspector"].update(
        {"source_one_hop_zh": "来源 loc.src1 已在一跳内定位；未解析来源请核实"}),
])
def test_evidence_zh_exact_projection(mutate: Any) -> None:
    """Replacing evidence/source Chinese with a DIFFERENT medical sentence
    that merely includes an allowed locator must reject with exactly
    s4.cross_plane_projection_drift."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    mutate(p)
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.cross_plane_projection_drift"}, sorted(set(errs))


def test_evidence_zh_valid_projection_exact() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    assert p["audience_inspector"]["support_evidence_zh"] == \
        ["来源 loc.src1 已定位"]
    assert p["audience_inspector"]["counterevidence_zh"] == []
    assert p["audience_inspector"]["source_one_hop_zh"] == \
        "来源 loc.src1 已在一跳内定位"


def test_evidence_zh_mutual_counter_projection() -> None:
    """The mutual fixture's unsupported finding yields a deterministic
    counterevidence line; a hand-authored removal must reject."""
    p = copy.deepcopy(VMOD.build_sample_packet("mutual", ANCHOR))
    assert p["audience_inspector"]["counterevidence_zh"] == \
        ["来源 loc.src1 已定位"]
    p["audience_inspector"]["counterevidence_zh"] = []
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.cross_plane_projection_drift"}, sorted(set(errs))


# ---------------------------------------------------------------------------
# direct preservation tests (registry slots moved to new cases)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("leaf,value", [
    ("ordinal", 9),
    ("ordinal_zh", "分析三"),
])
def test_ordinal_mapping_drift_direct(leaf: str, value: Any) -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["worker_views"][0][leaf] = value
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.ordinal_mapping_drift" in errs, sorted(set(errs))


def test_outcome_off_enum_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["adjudication_row"]["outcome"] = "accepted"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.off_enum_s2_adjudication_state" in errs, sorted(set(errs))


def test_outcome_enum_mismatch_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["adjudication_row"]["outcome"] = "bogus"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.enum_value_mismatch" in errs, sorted(set(errs))


def test_adds_explanation_only_required_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["adjudication_row"]["adds_explanation_only"] = False
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.schema_key_mismatch" in errs, sorted(set(errs))


# ---------------------------------------------------------------------------
# A. recursive imported-schema execution
# ---------------------------------------------------------------------------


def test_import_reference_resolution_exactly_once() -> None:
    """Every `import:<Name>` reference in the packet schema AND every object
    type reference inside an import_schema resolves exactly once against
    import_schemas (no unresolved ref, no orphan)."""
    objects = SCHEMA["objects"]
    import_schemas = SCHEMA["import_schemas"]
    refs = {}
    for owner, fields in list(objects.items()) + [
            (f"import.{k}", v) for k, v in import_schemas.items()]:
        for fname, descriptor in fields.items():
            ftype = descriptor.get("type", "")
            if ftype.startswith("import:"):
                name = ftype[len("import:"):]
                refs.setdefault(name, []).append(f"{owner}.{fname}")
            elif ftype in import_schemas:
                refs.setdefault(ftype, []).append(f"{owner}.{fname}")
    for name, uses in refs.items():
        assert name in import_schemas, f"unresolved import {name} -> {uses}"
    for name in import_schemas:
        assert name in refs, f"orphan import_schema {name}"
    # both imported object types present.
    assert "ReferenceBaselineItem" in import_schemas
    assert "R5AuthorityReceipt" in import_schemas
    assert "SourceRevisionContentPair" in import_schemas


def test_import_fields_recursively_visited() -> None:
    """Every imported field (ReferenceBaselineItem + R5AuthorityReceipt +
    SourceRevisionContentPair) is recursively validated: a wrong nested type
    in either import must reject with s4.schema_key_mismatch."""
    # ReferenceBaselineItem nested/list: source_locator_ids is a str list.
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["source_locator_ids"] = [42]
    assert set(_oracle(_resign(_rebuild(p)), ANCHOR)) == {
        "s4.schema_key_mismatch"}
    # R5AuthorityReceipt nested object: SourceRevisionContentPair.
    p2 = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p2["authority_receipt"]["source_revision_content_pairs"][0][
        "content_hash"] = "not-a-hash"
    errs = _oracle(_resign(_rebuild(p2)), ANCHOR)
    assert "s4.schema_key_mismatch" in errs or \
        "s4.hash_algorithm_mismatch" in errs, sorted(set(errs))
    p3 = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p3["authority_receipt"]["source_revision_content_pairs"][0][
        "unexpected_key"] = "x"
    assert set(_oracle(_resign(_rebuild(p3)), ANCHOR)) == {
        "s4.schema_key_mismatch"}


def test_import_unknown_key_rejected() -> None:
    """Reviewer reproduction: adding unexpected_leaf to baseline_items[0]
    must reject with s4.schema_key_mismatch (no silent skip, no [])."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["unexpected_leaf"] = "x"
    errs = _oracle(_resign(_rebuild(p)), ANCHOR)
    assert set(errs) == {"s4.schema_key_mismatch"}, sorted(set(errs))


def test_import_missing_required_key_rejected() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    del p["authority_receipt"]["project_ref"]
    assert set(_oracle(_resign(_rebuild(p)), ANCHOR)) == {
        "s4.schema_key_mismatch"}


def test_import_wrong_primitive_type_rejected() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["authority_receipt"]["run_ref"] = 123
    assert set(_oracle(_resign(_rebuild(p)), ANCHOR)) == {
        "s4.schema_key_mismatch"}


def test_import_nullability_violation_rejected() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["claimed_content_hash"] = None  # non-null sha256
    assert set(_oracle(_resign(_rebuild(p)), ANCHOR)) == {
        "s4.schema_key_mismatch"}


def test_import_s4_extra_keys_permitted() -> None:
    """The S4-declared projection fields on baseline_items (project/run/
    snapshot/cutoff/source relation) are permitted; a non-declared extra key
    still rejects."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    assert set(p["baseline_items"][0]) >= {
        "project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
        "source_revision"}
    assert _oracle(_resign(_rebuild(p)), ANCHOR) == []


# ---------------------------------------------------------------------------
# B. structural/type failure short-circuits semantic analysis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mutate", [
    lambda p: p.update({"ensemble_size": "2"}),          # root scalar wrong type
    lambda p: p.update({"ensemble_size": None}),          # root non-null None
    lambda p: p.update({"ensemble_id": 7}),               # root scalar
    lambda p: p.update({"worker_views": "not-a-list"}),   # root list wrong type
    lambda p: p.update({"worker_views": [None]}),         # list element wrong type
    lambda p: p.update({"baseline_items": "not-a-list"}),  # import list wrong type
    lambda p: p["risk_identity"].update({"domain": 9}),    # nested object wrong type
    lambda p: p["audience_inspector"].update(
        {"worker_ordinal_summaries": "bad"}),              # nested list wrong type
    lambda p: p["worker_views"][0].update({"ordinal": "2"}),  # list elem wrong type
    lambda p: p["baseline_items"][0].update({"item_id": 5}),  # import elem wrong type
    lambda p: p["authority_receipt"].update(
        {"evaluation_content_identities": [None]}),        # import nested elem
])
def test_wrong_type_no_exception(mutate: Any) -> None:
    """Wrong-type root/nested/list/import values must return a stable s4.*
    structural code and NEVER leak TypeError/KeyError/ValueError/R4
    exceptions, and must NOT reach semantic arithmetic/ordering code.  The
    structural short-circuit precedes any hash/semantic check, so the oracle
    is called directly on the mutated packet (no resign needed)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    mutate(p)
    errs = _oracle(p, ANCHOR)
    assert errs, "wrong-type mutation must reject"
    assert all(code.startswith("s4.") for code in errs)


def test_ensemble_size_string_contained() -> None:
    """Reviewer reproduction: ensemble_size='2' must return s4.schema_key_
    mismatch (structural), never reach `'2' < 2` (no uncaught TypeError)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["ensemble_size"] = "2"
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {"s4.schema_key_mismatch"}, sorted(set(errs))


def test_structural_failure_skips_semantic_codes() -> None:
    """When structural validation fails, semantic codes must NOT appear: e.g.
    a malformed ensemble_size cannot also produce a cross-plane projection
    error from the same malformed field."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["ensemble_size"] = "2"
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {"s4.schema_key_mismatch"}
    assert not any("cross_plane" in c or "verification" in c
                   for c in errs)


# ---------------------------------------------------------------------------
# A. generic sorted_unique_by executor (all object arrays)
# ---------------------------------------------------------------------------


def _packet_reachable_sorted_unique_fields() -> Dict[str, str]:
    """Enumerate every packet-reachable schema field declaring
    `sorted_unique_by:<key>` (excluding anchor-only S4Accepted* objects)."""
    out = {}
    for obj_name, fields in SCHEMA["objects"].items():
        if obj_name.startswith("S4Accepted"):
            continue
        for fname, descriptor in fields.items():
            for c in descriptor.get("constraints", []):
                if c.startswith("sorted_unique_by:"):
                    out[f"{obj_name}.{fname}"] = c[len("sorted_unique_by:"):]
    return out


def test_sorted_unique_walker_visits_every_declaration() -> None:
    """The generic executor visits EVERY packet-reachable schema field that
    declares sorted_unique_by (coverage assertion)."""
    declared = _packet_reachable_sorted_unique_fields()
    assert declared, "no sorted_unique_by declarations found"
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p = VMOD._resign(VMOD._rebuild_derived(p))
    visited = VMOD._check_sorted_unique_declarations(p, SCHEMA, [])
    missing = set(declared) - set(visited)
    assert not missing, f"sorted_unique_by fields the executor did NOT visit: {missing}"


# arrays with >=2 members in the legal multi fixture.
_MULTI_OBJECT_ARRAYS = [
    ("worker_views", "attempt_id", "s4.cardinality_not_0_1_n"),
    ("raw_artifacts", "artifact_id", "s4.cardinality_not_0_1_n"),
    ("verification_rows", "verification_id", "s4.cardinality_not_0_1_n"),
    ("conflict_rows", "conflict_id", "s4.cardinality_not_0_1_n"),
    ("baseline_rows", "row_ref", "s4.cardinality_not_0_1_n"),
    ("baseline_items", "item_id", "s4.cardinality_not_0_1_n"),
    ("audience_inspector.worker_ordinal_summaries", "ordinal_zh",
     "s4.ordinal_mapping_drift"),
    ("audience_inspector.baseline_rows_zh", "row_ref",
     "s4.baseline_projection_drift"),
    ("audit_inspector.worker_audit_rows", "attempt_id",
     "s4.cardinality_not_0_1_n"),
    ("audit_inspector.verification_audit_rows", "verification_id",
     "s4.cardinality_not_0_1_n"),
    ("history_log.entries", "seq", "s4.history_append_only_violation"),
]


def _get_path(p: Dict[str, Any], path: str) -> Any:
    node = p
    for part in path.split("."):
        node = node[part]
    return node


@pytest.mark.parametrize("path,key,code", _MULTI_OBJECT_ARRAYS,
                         ids=[p[0].replace(".", "_") for p in _MULTI_OBJECT_ARRAYS])
def test_object_array_reverse_fires_code(path: str, key: str, code: str) -> None:
    """Reversing ANY multi-member object array must fire its stable
    sorted_unique code.  Audit rows are validated on the DIRECT path (the
    registry _rebuild_derived helper would rebuild them)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    arr = _get_path(p, path)
    assert len(arr) >= 2, f"{path} needs >=2 members"
    arr.reverse()
    if "audit_inspector" not in path:
        p = VMOD._resign(VMOD._rebuild_derived(p))
    else:
        p = VMOD._resign(p)
    errs = _oracle(p, ANCHOR)
    assert code in errs, f"reverse {path}: expected {code}, got {sorted(set(errs))}"


@pytest.mark.parametrize("path,key,code", _MULTI_OBJECT_ARRAYS,
                         ids=[p[0].replace(".", "_") for p in _MULTI_OBJECT_ARRAYS])
def test_object_array_duplicate_key_fires_code(path: str, key: str, code: str) -> None:
    """Duplicating the sort key of ANY multi-member object array must fire its
    stable sorted_unique code."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    arr = _get_path(p, path)
    assert len(arr) >= 2
    arr[1][key] = arr[0][key]
    if "audit_inspector" not in path:
        p = VMOD._resign(VMOD._rebuild_derived(p))
    else:
        p = VMOD._resign(p)
    errs = _oracle(p, ANCHOR)
    assert code in errs, f"dup {path}.{key}: expected {code}, got {sorted(set(errs))}"


def test_sorted_unique_missing_key_is_structural() -> None:
    """A row missing its sort key is a structural error (schema_key_mismatch),
    never a Python comparison exception."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    del p["baseline_items"][1]["item_id"]
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert "s4.schema_key_mismatch" in errs, sorted(set(errs))


def test_sorted_unique_same_key_different_row_rejects() -> None:
    """Two rows with the SAME sort key but different content reject (B stable
    identity requirement)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    zh = p["audience_inspector"]["baseline_rows_zh"]
    zh[1]["row_ref"] = zh[0]["row_ref"]
    zh[1]["state_zh"] = "不支持"  # different row content, same stable key
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.baseline_projection_drift" in errs, sorted(set(errs))


# ---------------------------------------------------------------------------
# B. stable unique audience baseline row identity
# ---------------------------------------------------------------------------


def test_baseline_zh_two_assessments_same_item_distinct() -> None:
    """Two assessments of the SAME baseline item (item.b1) are distinct and
    deterministic via row_ref, and the legal fixture conforms ([])."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    zh = p["audience_inspector"]["baseline_rows_zh"]
    assert len(zh) == 2
    assert zh[0]["row_ref"] != zh[1]["row_ref"]
    assert zh[0]["row_ref"] == "baseline-row:item.b1:a1"
    assert zh[1]["row_ref"] == "baseline-row:item.b1:a2"
    assert zh[0]["item_anchor_zh"] == zh[1]["item_anchor_zh"]  # same display
    assert [r["row_ref"] for r in zh] == sorted(r["row_ref"] for r in zh)
    assert _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR) == []


def test_baseline_zh_duplicate_stable_identity_rejects() -> None:
    """Duplicate stable row_ref in audience baseline rows rejects with
    s4.baseline_projection_drift."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    zh = p["audience_inspector"]["baseline_rows_zh"]
    zh[1]["row_ref"] = zh[0]["row_ref"]
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.baseline_projection_drift"}, sorted(set(errs))


def test_baseline_zh_row_ref_grammar_reconstruction() -> None:
    """The declared-leaf reconstruction binds row_ref to the typed baseline
    row identity; a fabricated row_ref rejects with baseline_projection_drift."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["audience_inspector"]["baseline_rows_zh"][1]["row_ref"] = "baseline-row:ghost:a2"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.baseline_projection_drift" in errs, sorted(set(errs))


# ---------------------------------------------------------------------------
# C. typed import_extensions (five S4 baseline projection fields)
# ---------------------------------------------------------------------------


_BASELINE_EXTENSION_FIELDS = [
    "project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "source_revision",
]


def test_import_extensions_exact_five_field_set() -> None:
    """Artifact validation: baseline_items import_extensions keys == the exact
    approved five-field set, each descriptor uses supported constraint tokens,
    no collision with base ReferenceBaselineItem fields."""
    desc = SCHEMA["objects"]["R5S4AuthorityPacket"]["baseline_items"]
    ext = desc["import_extensions"]
    assert set(ext) == VMOD.EXPECTED_BASELINE_EXTENSIONS, set(ext)
    assert not (set(ext) & set(
        SCHEMA["import_schemas"]["ReferenceBaselineItem"]))
    for name, d in ext.items():
        assert d["type"] == "str"
        for c in d.get("constraints", []):
            assert VMOD._is_supported_constraint(c), (name, c)


def test_import_extensions_typing_matches_schema() -> None:
    """The generated packet_schema declares the five typed descriptors with
    correct nullability (cutoff_ref nullable, rest required)."""
    desc = SCHEMA["objects"]["R5S4AuthorityPacket"]["baseline_items"]
    ext = desc["import_extensions"]
    assert ext["cutoff_ref"]["nullable"] is True
    for name in ("project_ref", "run_ref", "snapshot_ref", "source_revision"):
        assert ext[name]["nullable"] is False
        assert "nonempty" in ext[name].get("constraints", [])


_C_EXTENSION_MUTATIONS = [
    ("project_ref", 123),                 # wrong primitive type
    ("project_ref", None),                 # null on non-nullable
    ("project_ref", ""),                   # empty (nonempty violation)
    ("project_ref", {"x": 1}),             # object where str expected
    ("project_ref", ["a"]),                # list where str expected
    ("run_ref", 5),                        # wrong type
    ("snapshot_ref", None),                # null on non-nullable
    ("source_revision", []),               # list where str expected
    ("source_revision", ""),               # empty
    ("cutoff_ref", 7),                     # wrong type (nullable but typed str)
]


@pytest.mark.parametrize("field,value", _C_EXTENSION_MUTATIONS,
                         ids=[f"{f}__{type(v).__name__}" for f, v in
                              _C_EXTENSION_MUTATIONS])
def test_import_extension_wrong_type_rejects_no_exception(field: str,
                                                          value: Any) -> None:
    """A wrong-type/null/empty/list/object value on ANY of the five S4
    baseline extension fields is a structural schema_key_mismatch, with no
    downstream exception (structural short-circuit)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0][field] = value
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert "s4.schema_key_mismatch" in errs, (field, sorted(set(errs)))
    assert not any("cross_plane" in c for c in errs)


def test_import_extension_valid_cutoff_null_ok() -> None:
    """cutoff_ref is nullable; a valid packet (None cutoff) passes structural
    validation (semantic anchor binding still applies)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["cutoff_ref"] = None
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert not any(c in errs for c in ("s4.schema_key_mismatch",)), \
        sorted(set(errs))


def test_import_extension_unknown_key_still_rejects() -> None:
    """A NON-declared extra key on an imported baseline item still rejects."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["bogus_extension"] = "x"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.schema_key_mismatch"}, sorted(set(errs))


def test_import_extension_base_field_cannot_be_overridden() -> None:
    """Base ReferenceBaselineItem fields cannot be overridden by the S5
    extension descriptors (artifact validation forbids collision)."""
    base = set(SCHEMA["import_schemas"]["ReferenceBaselineItem"])
    ext = set(SCHEMA["objects"]["R5S4AuthorityPacket"]["baseline_items"][
        "import_extensions"])
    assert not (ext & base), f"extension collides with base fields: {ext & base}"


# ---------------------------------------------------------------------------
# displaced coverage (registry slots moved to new A/B cases)
# ---------------------------------------------------------------------------


def test_zero_state_residue_worker_summaries_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("no_ensemble", ANCHOR))
    p["audience_inspector"]["worker_ordinal_summaries"] = [{
        "ordinal_zh": "分析一", "finding_summary_zh": ["x"],
        "verification_zh": "y", "gap_zh": []}]
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.ensemble_zero_must_be_empty" in errs, sorted(set(errs))


def test_zero_state_residue_raw_artifacts_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("no_ensemble", ANCHOR))
    p["raw_artifacts"] = [copy.deepcopy(
        VMOD.build_sample_packet("multi_analysis", ANCHOR)["raw_artifacts"][0])]
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.ensemble_zero_must_be_empty" in errs, sorted(set(errs))


def test_zero_state_residue_model_evidence_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("no_ensemble", ANCHOR))
    p["audit_inspector"]["model_evidence"] = copy.deepcopy(
        VMOD.build_sample_packet("multi_analysis", ANCHOR)[
            "audit_inspector"]["model_evidence"])
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert "s4.ensemble_zero_must_be_empty" in errs, sorted(set(errs))


def test_baseline_state_outdated_direct() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_rows"][0]["state"] = "outdated"
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.baseline_projection_drift"}, sorted(set(errs))


def test_verification_recomputed_false_structural_direct() -> None:
    """recomputed=False is a structural equals:true violation (schema_key_
    mismatch) under the B short-circuit."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["verification_rows"][0]["recomputed"] = False
    errs = _oracle(VMOD._resign(VMOD._rebuild_derived(p)), ANCHOR)
    assert set(errs) == {"s4.schema_key_mismatch"}, sorted(set(errs))


# ---------------------------------------------------------------------------
# A (8th). structural ref grammar on all five import extensions
# ---------------------------------------------------------------------------

_EXT_GRAMMAR_CASES = [
    # (field, valid_value, malformed, expected structural code on malformed)
    ("project_ref", "project.p1", "not-a-reference", "s4.schema_key_mismatch"),
    ("run_ref", "run.r1", "not-a-reference", "s4.schema_key_mismatch"),
    ("snapshot_ref", "snap.s1", "not-a-reference", "s4.schema_key_mismatch"),
    ("source_revision", "rev.1", "not-a-reference", "s4.schema_key_mismatch"),
    ("cutoff_ref", "cutoff.v1", "not-a-reference", "s4.schema_key_mismatch"),
]


@pytest.mark.parametrize("field,valid,malformed,code", _EXT_GRAMMAR_CASES,
                         ids=[c[0] for c in _EXT_GRAMMAR_CASES])
def test_import_extension_grammar_valid_and_malformed(
        field: str, valid: str, malformed: str, code: str) -> None:
    """Each of the five S4 baseline extension fields has a frozen structural
    ref grammar (prefix matching the accepted anchor value).  The valid value
    passes structural; a malformed ref and empty string return exactly the
    stable schema code with no downstream exception."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0][field] = malformed
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert code in errs, (field, malformed, sorted(set(errs)))
    # empty string on a non-nullable field is also structural.
    p2 = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p2["baseline_items"][0][field] = ""
    p2 = VMOD._resign(VMOD._rebuild_derived(p2))
    errs2 = _oracle(p2, ANCHOR)
    assert "s4.schema_key_mismatch" in errs2, (field, sorted(set(errs2)))


def test_import_extension_grammar_valid_boundary() -> None:
    """Valid boundary values for all five fields pass structural validation
    (semantic anchor binding may still apply but no schema_key_mismatch)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    vals = {"project_ref": "project.p1", "run_ref": "run.r1",
            "snapshot_ref": "snap.s1", "source_revision": "rev.1",
            "cutoff_ref": "cutoff.v1"}
    for f, v in vals.items():
        p["baseline_items"][0][f] = v
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert "s4.schema_key_mismatch" not in errs, sorted(set(errs))


def test_import_extension_grammar_null_boundary() -> None:
    """cutoff_ref=None is structurally allowed (nullable); the other four
    non-nullable fields reject None structurally."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["baseline_items"][0]["cutoff_ref"] = None
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert "s4.schema_key_mismatch" not in errs, sorted(set(errs))
    for f in ("project_ref", "run_ref", "snapshot_ref", "source_revision"):
        p2 = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
        p2["baseline_items"][0][f] = None
        p2 = VMOD._resign(VMOD._rebuild_derived(p2))
        errs2 = _oracle(p2, ANCHOR)
        assert "s4.schema_key_mismatch" in errs2, (f, sorted(set(errs2)))


def test_extension_grammar_grounded_in_anchor() -> None:
    """The frozen grammars match the accepted anchor identity values (do not
    invent a grammar broader/narrower than the accepted examples)."""
    for key, prefix in (("project_ref", "project."), ("run_ref", "run."),
                        ("snapshot_ref", "snap."), ("cutoff_ref", "cutoff.")):
        val = ANCHOR.get(key)
        assert val is not None and val.startswith(prefix), (key, val)
    srev = ANCHOR["accepted_baseline_items"][0]["source_revision"]
    assert srev.startswith("rev."), srev


# ---------------------------------------------------------------------------
# B (8th). deprecated untyped import_extra_keys rejected
# ---------------------------------------------------------------------------


def _build_schema_with_import_ext(ext: Any) -> Dict[str, Any]:
    schema = copy.deepcopy(SCHEMA)
    schema["objects"]["R5S4AuthorityPacket"]["baseline_items"][
        "import_extensions"] = ext
    return schema


@pytest.mark.parametrize("ext", [
    {"project_ref": ["project_ref"], "run_ref": ["run_ref"],
     "snapshot_ref": ["snapshot_ref"], "cutoff_ref": ["cutoff_ref"],
     "source_revision": ["source_revision"]},          # name-only (deprecated)
    {"project_ref": ["project_ref", "extra"]},          # mixed
    {"project_ref": ["project_ref"]},                   # partial
    {"project_ref": []},                                # empty value
])
def test_deprecated_import_extra_keys_rejected(ext: Any) -> None:
    """A name-only import_extra_keys-shaped import_extensions is a deprecated/
    unknown artifact shape and must raise VerificationError (trusted-artifact
    failure), never validate silently."""
    schema = _build_schema_with_import_ext(ext)
    maps = {m: VMOD._parse_classes(p, ROOT)
            for m, p in VMOD.MODULE_FILES.items()}
    with pytest.raises(VMOD.VerificationError):
        VMOD._validate_schema(schema, maps)


def test_deprecated_import_extra_keys_key_rejected() -> None:
    """Any import_extra_keys key in the schema is an unknown/deprecated shape
    and raises VerificationError."""
    schema = copy.deepcopy(SCHEMA)
    schema["objects"]["R5S4AuthorityPacket"]["baseline_items"][
        "import_extra_keys"] = ["project_ref"]
    maps = {m: VMOD._parse_classes(p, ROOT)
            for m, p in VMOD.MODULE_FILES.items()}
    with pytest.raises(VMOD.VerificationError):
        VMOD._validate_schema(schema, maps)


def test_generator_never_emits_deprecated_key() -> None:
    """The generator never emits import_extra_keys anywhere in the schema."""
    s = json.dumps(SCHEMA)
    assert "import_extra_keys" not in s


def test_import_extensions_require_exact_five_typed_descriptors() -> None:
    """Machine schema validation hard-requires the typed five-descriptor
    import_extensions on baseline_items (complete descriptors)."""
    desc = SCHEMA["objects"]["R5S4AuthorityPacket"]["baseline_items"]
    assert set(desc["import_extensions"]) == VMOD.EXPECTED_BASELINE_EXTENSIONS
    for name, d in desc["import_extensions"].items():
        assert d["type"] == "str"
        assert "nonempty" in d.get("constraints", []) or \
            d.get("nullable", False)


# ---------------------------------------------------------------------------
# C (8th). history ordering before chain checks
# ---------------------------------------------------------------------------


def test_history_reverse_returns_ordering_code_exactly() -> None:
    """Reversing history_log.entries returns exactly s4.history_append_only_
    violation (generic ordering code), with NO chain-break / prefix-rewrite
    cascade."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["history_log"]["entries"].reverse()
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {"s4.history_append_only_violation"}, sorted(set(errs))


def test_history_duplicate_seq_returns_ordering_code_exactly() -> None:
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["history_log"]["entries"][1]["seq"] = p["history_log"]["entries"][0]["seq"]
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert set(errs) == {"s4.history_append_only_violation"}, sorted(set(errs))


def test_history_legit_chain_break_still_reports() -> None:
    """A NON-ordering history mutation (prior-hash break) still reports
    s4.history_chain_break (no regression of the dedicated chain check)."""
    p = copy.deepcopy(VMOD.build_sample_packet("multi_analysis", ANCHOR))
    p["history_log"]["entries"][1]["prior_entry_hash"] = "0" * 64
    p = VMOD._resign(VMOD._rebuild_derived(p))
    errs = _oracle(p, ANCHOR)
    assert "s4.history_chain_break" in errs, sorted(set(errs))
