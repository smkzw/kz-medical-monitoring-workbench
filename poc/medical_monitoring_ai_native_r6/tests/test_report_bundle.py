"""Focused tests for R6 slice-03 ReportReviewBundle runtime.

Worker_01: shared identity envelope, sidecar vs proven in_place_copy,
original-byte hash retention, matrix/anchor-map hashes, verified-anchor gates.

Worker_02: optional DRAFT clean-draft provenance, IssueTransition
(reclassified/merge/split), and revision diff with not_evaluable on
incomparable identity/cutoff/revision.

Worker_03: independent verification — positive/negative/tamper/anchor/identity
mix/conflict preservation, slice-01/02 adjacency, medical-writing boundary,
protected ports, create-only allowlist, and raise-based normal/``-O``/``-OO``
× multi-``PYTHONHASHSEED`` reproducibility.

Does not claim product/runtime acceptance. Stdlib + pytest only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from mm_r6 import contracts, fixtures, report_bundle as rb, report_review as rr, validator

POC_ROOT = Path(__file__).resolve().parents[1]
IA_VER = "ia-r6-slice03-001"
IA_DIG = "ia-digest-r6-slice03-001"


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def _descriptor(**overrides):
    base = {
        "project_id": "project-r6-synthetic",
        "media_type": "docx",
        "source_name": "synthetic-report-slice03.docx",
        "reported_version_label": "v-synth-1",
        "reported_data_cutoff": "cutoff-2026-08-01",
        "reported_cutoff_status": "declared",
        "received_at": "2026-08-27T00:00:00Z",
        "source_scope": "project",
        "report_lineage_id": "lineage-r6-slice03",
        "parent_report_revision_id": None,
    }
    base.update(overrides)
    return base


def _evidence(eid: str = "ev-bundle-001"):
    return {
        "evidence_id": eid,
        "authority_class": "source_document",
        "snapshot_id": "snap-r6-001",
        "data_cutoff": "cutoff-2026-08-01",
        "source_revision_id": "run-source-revision-001",
        "locator": {"path": f"/evidence/{eid}"},
        "content_hash": f"hash-{eid}",
        "relation": "supports",
    }


def _binding(**overrides):
    base = {
        "project_id": "project-r6-synthetic",
        "run_id": "run-r6-001",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "cutoff-2026-08-01",
        "source_revision_id": "run-source-revision-001",
        "knowledge_pack_version": "kp-1",
        "rule_activation_version": "rav-1",
        "mapping_version": "map-1",
        "identity_algorithm_version": IA_VER,
        "identity_algorithm_digest": IA_DIG,
        "schema_version": "r6-0.1",
    }
    base.update(overrides)
    return base


def _unit_specs(report_revision_id: str):
    return [
        {
            "unit_id": "document-001",
            "unit_type": "document",
            "parent_unit_id": None,
            "required": True,
            "locator": {"path": "/"},
            "extractability": "text",
            "anchor_digest": "ad-doc-001",
        },
        {
            "unit_id": "body-001",
            "unit_type": "body",
            "parent_unit_id": "document-001",
            "required": True,
            "locator": {"path": "/body/1", "report_revision_id": report_revision_id},
            "extractability": "text",
            "anchor_digest": "ad-body-001",
        },
        {
            "unit_id": "footnote-001",
            "unit_type": "footnote",
            "parent_unit_id": "document-001",
            "required": True,
            "locator": {"path": "/footnote/1", "report_revision_id": report_revision_id},
            "extractability": "text",
            "anchor_digest": "ad-fn-001",
        },
    ]


def _positive_matrix(raw: bytes = b"slice03-bundle-positive-v1"):
    reg = rr.register_report_source(raw, _descriptor(), [])
    src = reg["report_source_revision"]
    units = [rr.build_report_unit(spec, src) for spec in _unit_specs(src["report_revision_id"])]
    for unit in units:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = (
            "no_claim" if unit["unit_type"] == "document" else "claimed"
        )
        unit["coverage_reason"] = None
    # footnote covered via omission issue rather than claim
    for unit in units:
        if unit["unit_id"] == "footnote-001":
            unit["coverage_status"] = "no_claim"
    claim = rr.build_report_claim(
        {
            "claim_id": "claim-bundle-001",
            "run_id": "run-r6-001",
            "unit_ids": ["body-001"],
            "claim_kind": "numeric",
            "source_text": "AE rate 11.9%",
            "normalized_claim_concept": "ae_rate",
            "scope": "project",
            "normalized_subject_or_site_scope": "project",
            "temporal_window": "cutoff-2026-08-01",
            "status": "supported",
            "evidence_refs": [_evidence()],
            "issue_ids": [],
            "locator": {"path": "/body/1"},
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    issue = rr.build_review_issue(
        {
            "issue_id": "issue-bundle-001",
            "run_id": "run-r6-001",
            "issue_kind": "omitted",
            "claim_ids": [],
            "unit_ids": ["footnote-001"],
            "severity": "medium",
            "clinical_or_document_scope": "footnote_gap",
            "evidence_refs": [_evidence("ev-fn")],
            "source_locators": [
                {
                    "path": "/footnote/1",
                    "report_revision_id": src["report_revision_id"],
                    "report_artifact_id": src["report_artifact_id"],
                    "unit_id": "footnote-001",
                    "unit_type": "footnote",
                }
            ],
            "lifecycle_state": "open",
            "revision_diff_state": "new",
            "related_issue_ids": [],
            "transition_refs": [],
            "current_note": "footnote not claimed",
            "normalized_clinical_concept": "footnote_gap",
            "normalized_subject_or_site_scope": "project",
            "normalized_temporal_window": "cutoff-2026-08-01",
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    surface = [
        {
            "expectation_id": "exp-risk-bundle-001",
            "expectation_kind": "accepted_risk",
            "authority_ref": "synthetic-authority/risk-001",
            "scope": "project",
            "temporal_window": "cutoff-2026-08-01",
        }
    ]
    reverse = [
        {
            "expectation_id": "exp-risk-bundle-001",
            "claim_ids": [],
            "issue_ids": ["issue-bundle-001"],
            "not_evaluable_exception": None,
            "evidence_refs": [_evidence("ev-fn")],
        }
    ]
    matrix = rr.build_report_review_matrix(
        _binding(),
        src,
        units,
        [claim],
        [issue],
        surface,
        reverse,
    )
    return {"matrix": matrix, "report_source": src, "registration": reg}


def _rebuild_matrix(pack, *, units=None, claims=None, issues=None):
    matrix = pack["matrix"]
    return rr.build_report_review_matrix(
        matrix["run_binding"],
        pack["report_source"],
        matrix["units"] if units is None else units,
        matrix["claims"] if claims is None else claims,
        matrix["issues"] if issues is None else issues,
        matrix["expected_review_surface"],
        matrix["reverse_coverage_links"],
    )


def _annotation_for(pack, *, anchor_status: str = "verified", **overrides):
    src = pack["report_source"]
    issue = pack["matrix"]["issues"][0]
    locator = copy.deepcopy(issue["source_locators"][0])
    base = {
        "annotation_id": "ann-001",
        "issue_id": issue["issue_id"],
        "locator": locator,
        "anchor_status": anchor_status,
        "note": "sidecar note",
    }
    base.update(overrides)
    return base


def test_shared_identity_has_eighteen_fields():
    assert len(rb.SHARED_IDENTITY_FIELDS) == 18
    pack = _positive_matrix()
    env = rb.extract_shared_identity(pack["matrix"], pack["report_source"])
    assert set(env) == set(rb.SHARED_IDENTITY_FIELDS)
    for field in rb.SHARED_IDENTITY_FIELDS:
        assert env[field] not in (None, ""), field


def test_sidecar_forced_when_lossless_unproven():
    pack = _positive_matrix(b"slice03-sidecar")
    ann = [_annotation_for(pack)]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        ann,
        lossless_in_place_proven=False,
    )
    assert projection["annotation_mode"] == "sidecar"
    assert projection["not_in_place_edit_of_original"] is True
    assert projection["is_in_place_source_mutation"] is False
    assert projection["is_original_bytes_preserved"] is True
    assert projection["source_bytes_hash"] == pack["report_source"]["report_artifact_id"]
    assert projection["projection_state"] == "qc_passed"
    assert projection["blocking_reasons"] == []


def test_in_place_copy_is_unavailable_without_a_proof_artifact():
    pack = _positive_matrix(b"slice03-inplace")
    ann = [_annotation_for(pack)]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        ann,
        lossless_in_place_proven=True,
    )
    assert projection["annotation_mode"] == "sidecar"
    assert projection["lossless_in_place_proven"] is True
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]
    assert projection["is_in_place_source_mutation"] is False
    assert projection["source_bytes_hash"] == pack["report_source"]["report_artifact_id"]


def test_unverified_anchor_fail_closed():
    pack = _positive_matrix(b"slice03-anchor-fail")
    ann = [_annotation_for(pack, anchor_status="unverified")]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        ann,
        lossless_in_place_proven=True,
    )
    assert projection["annotation_mode"] == "sidecar"
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]


def test_unknown_issue_annotation_fail_closed():
    pack = _positive_matrix(b"slice03-unknown-issue")
    ann = [_annotation_for(pack, issue_id="issue-does-not-exist")]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        ann,
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]
    # Matrix issue set is retained; projection does not delete it.
    assert "issue-bundle-001" in projection["issue_ids"]


def test_every_matrix_issue_requires_an_annotation():
    pack = _positive_matrix(b"slice03-annotation-coverage")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [],
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]


def test_annotation_cannot_invent_an_evidence_chain():
    pack = _positive_matrix(b"slice03-annotation-evidence")
    ann = _annotation_for(pack, evidence_refs=[_evidence("ev-invented")])
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [ann],
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]


def test_page_and_display_order_only_locator_is_not_a_verified_anchor():
    pack = _positive_matrix(b"slice03-page-only-anchor")
    issue = pack["matrix"]["issues"][0]
    page_only = {
        "page": 3,
        "display_order": 7,
        "report_revision_id": pack["report_source"]["report_revision_id"],
        "report_artifact_id": pack["report_source"]["report_artifact_id"],
    }
    issue["source_locators"] = [copy.deepcopy(page_only)]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [
            {
                "annotation_id": "ann-page-only",
                "issue_id": issue["issue_id"],
                "locator": page_only,
                "anchor_status": "verified",
            }
        ],
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]


@pytest.mark.parametrize(
    "locator",
    [
        {"token": "dummy"},
        {"path": "page:12"},
        {"path": "pg:12"},
        {"path": "PAGE-12"},
        {"path": "12"},
        {"xpath": "//page[12]"},
        {"paragraph": 3},
        {"section": "3.2"},
        {"footnote": "12"},
    ],
)
def test_non_content_locator_cannot_be_promoted_to_verified_anchor(locator):
    pack = _positive_matrix(b"slice03-non-content-anchor")
    issue = pack["matrix"]["issues"][0]
    bound = {
        **locator,
        "report_revision_id": pack["report_source"]["report_revision_id"],
        "report_artifact_id": pack["report_source"]["report_artifact_id"],
    }
    issue["source_locators"] = [copy.deepcopy(bound)]
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [
            {
                "annotation_id": "ann-non-content",
                "issue_id": issue["issue_id"],
                "locator": bound,
                "anchor_status": "verified",
            }
        ],
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]


def test_inputs_not_mutated():
    pack = _positive_matrix(b"slice03-immut")
    matrix_before = rr.canonical_bytes(pack["matrix"])
    source_before = rr.canonical_bytes(pack["report_source"])
    ann = [_annotation_for(pack)]
    ann_before = rr.canonical_bytes(ann)
    rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        ann,
        lossless_in_place_proven=False,
    )
    assert rr.canonical_bytes(pack["matrix"]) == matrix_before
    assert rr.canonical_bytes(pack["report_source"]) == source_before
    assert rr.canonical_bytes(ann) == ann_before


def test_matrix_and_anchor_map_hashes_stable():
    pack = _positive_matrix(b"slice03-hash-stable")
    ann = [_annotation_for(pack)]
    p1 = rb.build_annotated_projection(
        pack["matrix"], pack["report_source"], ann, lossless_in_place_proven=False
    )
    p2 = rb.build_annotated_projection(
        pack["matrix"], pack["report_source"], ann, lossless_in_place_proven=False
    )
    assert p1["matrix_content_hash"] == p2["matrix_content_hash"]
    assert p1["anchor_map_hash"] == p2["anchor_map_hash"]
    assert p1["annotated_artifact_id"] == p2["annotated_artifact_id"]
    assert p1["matrix_content_hash"] == rb.compute_matrix_content_hash(pack["matrix"])
    assert p1["anchor_map_hash"] == rr.sha256_hex(rr.canonical_bytes(p1["anchor_map"]))


def test_bundle_qc_passed_when_gates_clear():
    pack = _positive_matrix(b"slice03-bundle-pass")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection)
    assert bundle["bundle_state"] == "qc_passed"
    assert bundle["blocking_reasons"] == []
    assert bundle["clean_draft_artifact_id"] is None
    assert set(bundle["shared_identity"]) == set(rb.SHARED_IDENTITY_FIELDS)
    codes = rb.validate_report_review_bundle(bundle, pack["matrix"], projection)
    assert codes == ()


def test_bundle_identity_mismatch_on_run_mix():
    pack = _positive_matrix(b"slice03-id-mix")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection)
    tampered = copy.deepcopy(bundle)
    tampered["run_id"] = "run-tampered"
    tampered["shared_identity"] = dict(tampered["shared_identity"])
    tampered["shared_identity"]["run_id"] = "run-tampered"
    codes = rb.validate_report_review_bundle(tampered, pack["matrix"], projection)
    assert "bundle_identity_mismatch" in codes


def test_source_bytes_hash_tamper_detected():
    pack = _positive_matrix(b"slice03-bytes-tamper")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection)
    tampered = copy.deepcopy(projection)
    tampered["source_bytes_hash"] = "0" * 64
    codes = rb.validate_report_review_bundle(bundle, pack["matrix"], tampered)
    assert "bundle_identity_mismatch" in codes


def test_anchor_map_hash_tamper_detected():
    pack = _positive_matrix(b"slice03-anchor-hash")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection)
    tampered = copy.deepcopy(projection)
    tampered["anchor_map_hash"] = "0" * 64
    codes = rb.validate_report_review_bundle(bundle, pack["matrix"], tampered)
    assert "annotation_anchor_invalid" in codes


def test_content_addressed_piece_and_bundle_ids_detect_tamper():
    pack = _bundle_pack(b"slice03-content-id-tamper")
    bad_bundle = copy.deepcopy(pack["bundle"])
    bad_bundle["bundle_id"] = "bundle-" + "0" * 64
    assert "bundle_identity_mismatch" in rb.validate_report_review_bundle(
        bad_bundle, pack["matrix"], pack["projection"], pack["draft"]
    )

    bad_projection = copy.deepcopy(pack["projection"])
    bad_projection["annotated_artifact_id"] = "ann-" + "0" * 64
    assert "bundle_identity_mismatch" in rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], bad_projection, pack["draft"]
    )

    bad_draft = copy.deepcopy(pack["draft"])
    bad_draft["before_after_provenance"][0]["after"] = {"text": "tampered"}
    assert "bundle_identity_mismatch" in rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], pack["projection"], bad_draft
    )


def test_ports_8911_5174_stopped():
    assert _port_connect_ex(8911) != 0
    assert _port_connect_ex(5174) != 0


def test_worker01_apis_present():
    for name in (
        "SHARED_IDENTITY_FIELDS",
        "extract_shared_identity",
        "compute_issue_set_hash",
        "compute_matrix_content_hash",
        "build_annotated_projection",
        "build_report_review_bundle",
        "validate_report_review_bundle",
    ):
        assert hasattr(rb, name), name


# ---------------------------------------------------------------------------
# Worker_02: clean draft / IssueTransition / revision diff
# ---------------------------------------------------------------------------


def _mod_for(pack, **overrides):
    issue = pack["matrix"]["issues"][0]
    base = {
        "modification_id": "mod-001",
        "issue_ids": [issue["issue_id"]],
        "before": {"text": "AE rate 11.9%"},
        "after": {"text": "AE rate [DRAFT revision pending evidence]"},
        "scope": "body-001",
        "note": "draft rewrite bound to issue",
    }
    base.update(overrides)
    return base


def test_clean_draft_optional_when_not_requested():
    pack = _positive_matrix(b"slice03-draft-opt")
    assert (
        rb.build_clean_draft(
            pack["matrix"],
            pack["report_source"],
            [_mod_for(pack)],
            requested=False,
        )
        is None
    )


def test_clean_draft_visible_draft_not_final():
    pack = _positive_matrix(b"slice03-draft-pos")
    draft = rb.build_clean_draft(
        pack["matrix"],
        pack["report_source"],
        [_mod_for(pack)],
        requested=True,
    )
    assert draft is not None
    assert draft["draft_label"] == "DRAFT"
    assert draft["is_final"] is False
    assert draft["is_user_confirmed"] is False
    assert draft["artifact_type"] == "report_clean_draft"
    assert draft["source_bytes_hash"] == pack["report_source"]["report_artifact_id"]
    assert draft["issue_ids"] == sorted(
        issue["issue_id"] for issue in pack["matrix"]["issues"]
    )
    assert draft["before_after_provenance"][0]["before"]["text"] == "AE rate 11.9%"
    assert draft["before_after_provenance"][0]["after"]["text"].startswith("AE rate")
    # Unresolved open issue retained; cannot claim exportable final semantics.
    assert any(
        issue["issue_id"] == "issue-bundle-001"
        for issue in draft["unresolved_issues"]
    )
    assert draft["draft_state"] != "exported"
    assert draft["is_in_place_source_mutation"] is False


def test_clean_draft_rejects_unknown_issue_modification():
    pack = _positive_matrix(b"slice03-draft-unk")
    with pytest.raises(rb.ReportBundleError) as exc:
        rb.build_clean_draft(
            pack["matrix"],
            pack["report_source"],
            [_mod_for(pack, issue_ids=["issue-missing"])],
            requested=True,
        )
    assert exc.value.failure_code == "draft_identity_invalid"


def test_bundle_with_clean_draft_passes_draft_gate():
    pack = _positive_matrix(b"slice03-draft-bundle")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    draft = rb.build_clean_draft(
        pack["matrix"],
        pack["report_source"],
        [_mod_for(pack)],
        requested=True,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection, draft)
    assert bundle["clean_draft_artifact_id"] == draft["clean_draft_artifact_id"]
    codes = rb.validate_report_review_bundle(
        bundle, pack["matrix"], projection, draft
    )
    assert codes == ()
    assert "draft_identity_invalid" not in codes
    assert "unresolved_issue_dropped" not in codes


def test_draft_validation_detects_missing_draft_label_and_dropped_issue():
    pack = _positive_matrix(b"slice03-draft-neg")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    draft = rb.build_clean_draft(
        pack["matrix"],
        pack["report_source"],
        [_mod_for(pack)],
        requested=True,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection, draft)
    bad_label = copy.deepcopy(draft)
    bad_label["draft_label"] = "FINAL"
    codes = rb.validate_report_review_bundle(
        bundle, pack["matrix"], projection, bad_label
    )
    assert "draft_identity_invalid" in codes

    dropped = copy.deepcopy(draft)
    dropped["issue_ids"] = []
    dropped["unresolved_issues"] = []
    codes2 = rb.validate_report_review_bundle(
        bundle, pack["matrix"], projection, dropped
    )
    assert "unresolved_issue_dropped" in codes2


def test_draft_retention_is_content_exact_not_count_only():
    pack = _positive_matrix(b"slice03-draft-retention")
    matrix = copy.deepcopy(pack["matrix"])
    matrix["unresolved_conflicts"] = [
        {"conflict_id": "conflict-1", "issue_ids": ["issue-bundle-001"]}
    ]
    draft = rb.build_clean_draft(
        matrix, pack["report_source"], [_mod_for(pack)], requested=True
    )
    projection = rb.build_annotated_projection(
        matrix,
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(matrix, projection, draft)
    replaced = copy.deepcopy(draft)
    replaced["unresolved_conflicts"] = [
        {"conflict_id": "different", "issue_ids": ["issue-bundle-001"]}
    ]
    assert "unresolved_issue_dropped" in rb.validate_report_review_bundle(
        bundle, matrix, projection, replaced
    )


def test_issue_transition_reclassified_preserves_identity():
    pack = _positive_matrix(b"slice03-tr-reclass")
    src_issue = copy.deepcopy(pack["matrix"]["issues"][0])
    tgt_issue = copy.deepcopy(src_issue)
    tgt_issue["issue_kind"] = "coverage_gap"
    tgt_issue["report_revision_id"] = "rr-next"
    transition = rb.build_issue_transition(
        {
            "transition_kind": "reclassified",
            "source_issue_ids": [src_issue["issue_id"]],
            "target_issue_ids": [tgt_issue["issue_id"]],
            "from_report_revision_id": pack["report_source"]["report_revision_id"],
            "to_report_revision_id": "rr-next",
            "reason": "kind refined after evidence review",
            "evidence_refs": [_evidence("ev-reclass")],
            "before_evidence_relation": "supports",
            "after_evidence_relation": "qualifies",
        },
        [src_issue],
        [tgt_issue],
    )
    assert transition["transition_kind"] == "reclassified"
    assert transition["before_issue_kind"] == "omitted"
    assert transition["after_issue_kind"] == "coverage_gap"
    assert transition["source_issue_ids"] == [src_issue["issue_id"]]
    assert transition["target_issue_ids"] == [tgt_issue["issue_id"]]
    assert (
        transition["source_issue_identity_keys"]
        == transition["target_issue_identity_keys"]
    )


def test_issue_transition_merge_and_split_preserve_ids():
    pack = _positive_matrix(b"slice03-tr-merge")
    a = copy.deepcopy(pack["matrix"]["issues"][0])
    a["report_revision_id"] = "rr-a"
    b = copy.deepcopy(a)
    b["issue_id"] = "issue-bundle-002"
    b["issue_identity_key"] = a["issue_identity_key"] + "-b"
    merged = copy.deepcopy(a)
    merged["issue_id"] = "issue-merged-001"
    merged["lifecycle_state"] = "open"
    merged["report_revision_id"] = "rr-b"
    merge = rb.build_issue_transition(
        {
            "transition_kind": "merge",
            "source_issue_ids": [a["issue_id"], b["issue_id"]],
            "target_issue_ids": [merged["issue_id"]],
            "from_report_revision_id": "rr-a",
            "to_report_revision_id": "rr-b",
            "reason": "duplicate footnotes merged",
            "evidence_refs": [_evidence("ev-merge")],
        },
        [a, b],
        [merged],
    )
    assert set(merge["source_issue_ids"]) == {a["issue_id"], b["issue_id"]}
    assert merge["target_issue_ids"] == [merged["issue_id"]]

    left = copy.deepcopy(a)
    left["issue_id"] = "issue-split-a"
    left["report_revision_id"] = "rr-c"
    right = copy.deepcopy(a)
    right["issue_id"] = "issue-split-b"
    right["report_revision_id"] = "rr-c"
    split = rb.build_issue_transition(
        {
            "transition_kind": "split",
            "source_issue_ids": [a["issue_id"]],
            "target_issue_ids": [left["issue_id"], right["issue_id"]],
            "from_report_revision_id": "rr-a",
            "to_report_revision_id": "rr-c",
            "reason": "scope split across units",
            "evidence_refs": [_evidence("ev-split")],
        },
        [a],
        [left, right],
    )
    assert split["source_issue_ids"] == [a["issue_id"]]
    assert set(split["target_issue_ids"]) == {left["issue_id"], right["issue_id"]}


def test_issue_transition_rejects_duplicate_ids_and_revision_mismatch():
    pack = _positive_matrix(b"slice03-tr-negative")
    issue = copy.deepcopy(pack["matrix"]["issues"][0])
    spec = {
        "transition_kind": "merge",
        "source_issue_ids": [issue["issue_id"], issue["issue_id"]],
        "target_issue_ids": [issue["issue_id"]],
        "from_report_revision_id": issue["report_revision_id"],
        "to_report_revision_id": issue["report_revision_id"],
        "reason": "invalid duplicate",
        "evidence_refs": [_evidence("ev-duplicate")],
    }
    with pytest.raises(rb.ReportBundleError) as exc:
        rb.build_issue_transition(spec, [issue], [issue])
    assert exc.value.failure_code == "issue_transition_invalid"

    target = copy.deepcopy(issue)
    target["issue_kind"] = "coverage_gap"
    bad_revision = {
        **spec,
        "transition_kind": "reclassified",
        "source_issue_ids": [issue["issue_id"]],
        "target_issue_ids": [target["issue_id"]],
        "to_report_revision_id": "wrong-revision",
    }
    with pytest.raises(rb.ReportBundleError) as exc2:
        rb.build_issue_transition(bad_revision, [issue], [target])
    assert exc2.value.failure_code == "issue_transition_invalid"


def test_revision_diff_unchanged_and_new_and_absent_not_evaluable():
    prev = _positive_matrix(b"slice03-diff-prev")
    curr = _positive_matrix(b"slice03-diff-curr")
    # Same lineage/cutoff/identity via identical descriptor lineage; different
    # bytes → different revision ids, but shared identity fields for run match
    # except report revision / artifact / issue_set_hash.
    # Force current matrix shared run identity to match previous for comparability
    # of project/lineage/cutoff while keeping a distinct report revision.
    curr["matrix"]["run_binding"] = copy.deepcopy(prev["matrix"]["run_binding"])
    curr["matrix"]["source_identity"]["project_id"] = prev["matrix"]["source_identity"][
        "project_id"
    ]
    curr["matrix"]["source_identity"]["report_lineage_id"] = prev["matrix"][
        "source_identity"
    ]["report_lineage_id"]
    # Recompute issue set hash alignment is not required for comparability fields.
    # Keep the same issue identity key and open lifecycle → unchanged or unresolved.
    curr_issue = curr["matrix"]["issues"][0]
    prev_issue = prev["matrix"]["issues"][0]
    curr_issue["issue_identity_key"] = prev_issue["issue_identity_key"]
    curr_issue["lifecycle_state"] = "open"
    curr_issue["revision_diff_state"] = "unchanged"
    # Match substantive fingerprint for unchanged.
    for field in (
        "issue_kind",
        "claim_ids",
        "unit_ids",
        "evidence_refs",
        "source_locators",
        "current_note",
        "severity",
    ):
        curr_issue[field] = copy.deepcopy(prev_issue[field])

    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"], transitions=())
    assert rows
    assert all(row["revision_diff_state"] != "resolved" or row["comparable"] for row in rows)
    matched = [
        row
        for row in rows
        if prev_issue["issue_id"] in (row.get("source_issue_ids") or [])
    ]
    assert matched
    assert matched[0]["revision_diff_state"] in {"unchanged", "unresolved", "not_evaluable"}
    if matched[0]["comparable"]:
        assert matched[0]["revision_diff_state"] == "unchanged"


def test_revision_diff_incomparable_cutoff_is_not_evaluable_not_resolved():
    prev = _positive_matrix(b"slice03-diff-cut-a")
    curr = _positive_matrix(b"slice03-diff-cut-b")
    curr["matrix"]["run_binding"] = copy.deepcopy(prev["matrix"]["run_binding"])
    curr["matrix"]["run_binding"]["data_cutoff"] = "cutoff-OTHER"
    curr["matrix"]["issues"][0]["issue_identity_key"] = prev["matrix"]["issues"][0][
        "issue_identity_key"
    ]
    curr["matrix"]["issues"][0]["lifecycle_state"] = "resolved"
    curr["matrix"]["issues"][0]["revision_diff_state"] = "resolved"
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    assert rows
    assert all(row["revision_diff_state"] == "not_evaluable" for row in rows)
    assert all(row["comparable"] is False for row in rows)
    assert "resolved" not in {row["revision_diff_state"] for row in rows}


def test_revision_diff_does_not_trust_lifecycle_only_resolution():
    prev = _positive_matrix(b"slice03-diff-resolution-proof-a")
    curr = copy.deepcopy(prev)
    issue = curr["matrix"]["issues"][0]
    issue["lifecycle_state"] = "resolved"
    issue["revision_diff_state"] = "resolved"
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    assert rows
    assert rows[0]["revision_diff_state"] == "not_evaluable"


def test_revision_diff_changed_evidence_without_coverage_closure_is_not_resolved():
    prev = _positive_matrix(b"slice03-diff-open-a")
    curr = _positive_matrix(b"slice03-diff-open-b")
    issue = copy.deepcopy(curr["matrix"]["issues"][0])
    issue["issue_identity_key"] = prev["matrix"]["issues"][0]["issue_identity_key"]
    issue["lifecycle_state"] = "resolved"
    issue["revision_diff_state"] = "resolved"
    issue["evidence_refs"] = [_evidence("ev-resolution-new-but-open")]
    curr["matrix"] = _rebuild_matrix(curr, issues=[issue])

    assert rr.validate_report_review_matrix(curr["matrix"]) == ()
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    matched = [row for row in rows if row.get("source_issue_ids")]
    assert matched
    assert matched[0]["revision_diff_state"] == "not_evaluable"


def test_revision_diff_resolved_requires_open_to_claimed_coverage_change():
    prev = _positive_matrix(b"slice03-diff-closed-a")
    curr = _positive_matrix(b"slice03-diff-closed-b")
    issue = copy.deepcopy(curr["matrix"]["issues"][0])
    issue["issue_identity_key"] = prev["matrix"]["issues"][0]["issue_identity_key"]
    issue["lifecycle_state"] = "resolved"
    issue["revision_diff_state"] = "resolved"
    issue["evidence_refs"] = [_evidence("ev-resolution-closed")]

    units = copy.deepcopy(curr["matrix"]["units"])
    for unit in units:
        if unit["unit_id"] == "footnote-001":
            unit["coverage_status"] = "claimed"
    claims = copy.deepcopy(curr["matrix"]["claims"])
    claims[0]["unit_ids"] = sorted({*claims[0]["unit_ids"], "footnote-001"})
    curr["matrix"] = _rebuild_matrix(
        curr, units=units, claims=claims, issues=[issue]
    )

    assert rr.validate_report_review_matrix(curr["matrix"]) == ()
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    matched = [row for row in rows if row.get("source_issue_ids")]
    assert matched
    assert matched[0]["revision_diff_state"] == "resolved"


def test_revision_diff_omitted_relink_does_not_close_the_original_gap():
    prev = _positive_matrix(b"slice03-diff-relink-a")
    curr = _positive_matrix(b"slice03-diff-relink-b")
    issue = copy.deepcopy(curr["matrix"]["issues"][0])
    issue["issue_identity_key"] = prev["matrix"]["issues"][0]["issue_identity_key"]
    issue["unit_ids"] = ["body-001"]
    issue["lifecycle_state"] = "resolved"
    issue["revision_diff_state"] = "resolved"
    issue["evidence_refs"] = [_evidence("ev-resolution-relinked")]
    issue["source_locators"] = [
        {
            "path": "/body/1",
            "report_revision_id": curr["report_source"]["report_revision_id"],
            "report_artifact_id": curr["report_source"]["report_artifact_id"],
            "unit_id": "body-001",
            "unit_type": "body",
        }
    ]
    curr["matrix"] = _rebuild_matrix(curr, issues=[issue])

    entries = {row["unit_id"]: row for row in curr["matrix"]["entries"]}
    assert entries["footnote-001"]["coverage_status"] == "no_claim"
    assert rr.validate_report_review_matrix(curr["matrix"]) == ()
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    matched = [row for row in rows if row.get("source_issue_ids")]
    assert matched
    assert matched[0]["revision_diff_state"] == "not_evaluable"


@pytest.mark.parametrize("transition_kind", ["merge", "split"])
def test_merge_split_changed_evidence_without_all_coverage_closed_is_not_resolved(
    transition_kind,
):
    prev = _positive_matrix(f"slice03-{transition_kind}-open-a".encode())
    curr = _positive_matrix(f"slice03-{transition_kind}-open-b".encode())
    source = copy.deepcopy(prev["matrix"]["issues"][0])
    target = copy.deepcopy(curr["matrix"]["issues"][0])
    target["lifecycle_state"] = "resolved"
    target["revision_diff_state"] = "resolved"
    target["evidence_refs"] = [_evidence(f"ev-{transition_kind}-new-but-open")]

    if transition_kind == "merge":
        source_extra = copy.deepcopy(source)
        source_extra["issue_id"] = "issue-source-extra"
        previous_issues = [source, source_extra]
        current_issues = [target]
    else:
        target_extra = copy.deepcopy(target)
        target_extra["issue_id"] = "issue-target-extra"
        previous_issues = [source]
        current_issues = [target, target_extra]

    prev["matrix"] = _rebuild_matrix(prev, issues=previous_issues)
    curr["matrix"] = _rebuild_matrix(curr, issues=current_issues)
    spec = {
        "transition_kind": transition_kind,
        "source_issue_ids": [item["issue_id"] for item in previous_issues],
        "target_issue_ids": [item["issue_id"] for item in current_issues],
        "from_report_revision_id": prev["report_source"]["report_revision_id"],
        "to_report_revision_id": curr["report_source"]["report_revision_id"],
        "reason": "synthetic transition remains open",
        "evidence_refs": [_evidence(f"ev-{transition_kind}-transition")],
    }
    transition = rb.build_issue_transition(spec, previous_issues, current_issues)
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"], [transition])
    transition_rows = [row for row in rows if row.get("transition_kind")]
    assert len(transition_rows) == 1
    assert transition_rows[0]["revision_diff_state"] == "not_evaluable"


def test_duplicate_identity_group_requires_explicit_transition():
    prev = _positive_matrix(b"slice03-diff-ambiguous-a")
    curr = copy.deepcopy(prev)
    previous_extra = copy.deepcopy(prev["matrix"]["issues"][0])
    previous_extra["issue_id"] = "issue-previous-extra"
    current_extra = copy.deepcopy(curr["matrix"]["issues"][0])
    current_extra["issue_id"] = "issue-current-extra"
    prev["matrix"]["issues"].append(previous_extra)
    curr["matrix"]["issues"].append(current_extra)
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    assert len(rows) == 4
    assert all(row["revision_diff_state"] == "not_evaluable" for row in rows)
    assert all(
        row["reason"] == "ambiguous_identity_requires_transition" for row in rows
    )


def test_revision_diff_with_merge_transition():
    prev = _positive_matrix(b"slice03-diff-merge-a")
    curr = _positive_matrix(b"slice03-diff-merge-b")
    curr["matrix"]["run_binding"] = copy.deepcopy(prev["matrix"]["run_binding"])
    curr["matrix"]["source_identity"]["report_lineage_id"] = prev["matrix"][
        "source_identity"
    ]["report_lineage_id"]
    curr["matrix"]["source_identity"]["project_id"] = prev["matrix"]["source_identity"][
        "project_id"
    ]
    a = prev["matrix"]["issues"][0]
    b = copy.deepcopy(a)
    b["issue_id"] = "issue-bundle-extra"
    prev["matrix"]["issues"] = [a, b]
    merged = copy.deepcopy(a)
    merged["issue_id"] = "issue-merged-live"
    merged["report_revision_id"] = curr["report_source"]["report_revision_id"]
    merged["lifecycle_state"] = "partially_resolved"
    merged["revision_diff_state"] = "partially_resolved"
    curr["matrix"]["issues"] = [merged]
    transition = rb.build_issue_transition(
        {
            "transition_kind": "merge",
            "source_issue_ids": [a["issue_id"], b["issue_id"]],
            "target_issue_ids": [merged["issue_id"]],
            "from_report_revision_id": prev["report_source"]["report_revision_id"],
            "to_report_revision_id": curr["report_source"]["report_revision_id"],
            "reason": "merged for revision diff",
            "evidence_refs": [_evidence("ev-diff-merge")],
        },
        [a, b],
        [merged],
    )
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"], [transition])
    merge_rows = [row for row in rows if row.get("transition_kind") == "merge"]
    assert merge_rows
    assert set(merge_rows[0]["source_issue_ids"]) == {a["issue_id"], b["issue_id"]}
    assert merge_rows[0]["target_issue_ids"] == [merged["issue_id"]]
    if merge_rows[0]["comparable"]:
        assert merge_rows[0]["revision_diff_state"] == "partially_resolved"
    else:
        assert merge_rows[0]["revision_diff_state"] == "not_evaluable"


def test_worker02_apis_present():
    for name in (
        "build_clean_draft",
        "build_issue_transition",
        "build_revision_diff",
        "DRAFT_LABEL",
        "ISSUE_TRANSITION_KINDS",
    ):
        assert hasattr(rb, name), name
    pack = _positive_matrix(b"slice03-api")
    assert (
        rb.build_clean_draft(
            pack["matrix"],
            pack["report_source"],
            [],
            requested=False,
        )
        is None
    )


# ---------------------------------------------------------------------------
# worker_03 independent verification gates
# ---------------------------------------------------------------------------

WORKBENCH_ROOT = contracts.WORKBENCH_ROOT

REQUIRED_BUNDLE_APIS = (
    "SHARED_IDENTITY_FIELDS",
    "extract_shared_identity",
    "compute_issue_set_hash",
    "compute_matrix_content_hash",
    "build_annotated_projection",
    "build_clean_draft",
    "build_issue_transition",
    "build_revision_diff",
    "build_report_review_bundle",
    "validate_report_review_bundle",
)

# Slice-04 allowlist (extends accepted slice-01/02/03 create-only surface).
SLICE04_CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "src/mm_r6/report_review.py",
        "src/mm_r6/report_bundle.py",
        "src/mm_r6/mode_output.py",
        "src/mm_r6/agent_harness.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "tests/test_report_review.py",
        "tests/test_report_bundle.py",
        "tests/test_mode_output.py",
        "tests/test_agent_harness.py",
        "evidence/r6_contract_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
        "README.md",
    }
)
# Backward-compatible alias for adjacent slice-03 wording in older notes.
SLICE03_CREATE_ONLY_RELATIVE = SLICE04_CREATE_ONLY_RELATIVE

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 542
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
)
EXPECTED_CONTRACT_SHA = contracts.ACCEPTED_CONTRACT_SHA256
EXPECTED_MATRIX_SHA = contracts.ACCEPTED_MATRIX_SHA256
EXPECTED_PROSE_SHA = contracts.ACCEPTED_PROSE_SHA256
EXPECTED_SLICE01_SRC = {
    "src/mm_r6/contracts.py": (
        "f5ce93629bd008d438095fd9b23ab1f335b951087bf916b85ac990a350e8fcfa"
    ),
    "src/mm_r6/fixtures.py": (
        "e8064ad358e0a215d6b428bc1c48e97a4ef55a20131261e5b6a9c21eac44e56c"
    ),
    "src/mm_r6/validator.py": (
        "8c9bb8c60c64c1a102d37f5e4e49263844061fd5b37cce01060bbd4133d891d0"
    ),
}
PROTECTED_PORTS = (8911, 5174)
FROZEN_BUNDLE_BLOCKING_CODES = (
    "bundle_identity_mismatch",
    "annotation_anchor_invalid",
    "draft_identity_invalid",
    "unresolved_issue_dropped",
)


def _poc_files() -> set:
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        if "__pycache__" in rel.split("/") or ".pytest_cache" in rel.split("/"):
            continue
        if rel.endswith(".pyc"):
            continue
        found.add(rel)
    return found


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _medical_writing_boundary(root: Path) -> dict:
    matched = {}
    errors = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        base = root / root_relative
        if not base.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, dirnames, filenames in os.walk(
            base, topdown=True, followlinks=False
        ):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(directory) / filename
                relative = path.relative_to(root).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(
                        f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}"
                    )
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched[relative] = (
                        hashlib.sha256(path.read_bytes()).hexdigest().lower()
                    )
                except (OSError, UnicodeError) as exc:
                    errors.append(
                        f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}"
                    )
    aggregate = hashlib.sha256()
    for relative in sorted(matched, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "file_count": len(matched),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def _bundle_pack(raw: bytes = b"verifier-bundle-positive"):
    """Minimal positive bundle surface for worker_03 gates."""
    pack = _positive_matrix(raw)
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    draft = rb.build_clean_draft(
        pack["matrix"],
        pack["report_source"],
        [_mod_for(pack)],
        requested=True,
    )
    bundle = rb.build_report_review_bundle(pack["matrix"], projection, draft)
    return {**pack, "projection": projection, "draft": draft, "bundle": bundle}


def test_bundle_apis_required_for_slice03_completion():
    missing = [name for name in REQUIRED_BUNDLE_APIS if not hasattr(rb, name)]
    assert missing == [], (
        "worker_01/02 bundle APIs absent from report_bundle.py: "
        + ", ".join(missing)
    )


def test_positive_three_piece_shared_identity_and_qc_passed():
    pack = _bundle_pack(b"verifier-pos-three-piece")
    bundle = pack["bundle"]
    projection = pack["projection"]
    draft = pack["draft"]
    expected = rb.extract_shared_identity(pack["matrix"])
    assert bundle["bundle_state"] == "qc_passed"
    assert bundle["blocking_reasons"] == []
    for field in rb.SHARED_IDENTITY_FIELDS:
        assert bundle[field] == expected[field], field
        assert projection["shared_identity"][field] == expected[field], field
        assert draft[field] == expected[field], field
    assert set(bundle["shared_identity"]) == set(rb.SHARED_IDENTITY_FIELDS)
    codes = rb.validate_report_review_bundle(
        bundle, pack["matrix"], projection, draft
    )
    assert codes == ()


def test_negative_unverified_anchor_blocks_projection_and_bundle():
    pack = _positive_matrix(b"verifier-neg-anchor")
    projection = rb.build_annotated_projection(
        pack["matrix"],
        pack["report_source"],
        [_annotation_for(pack, anchor_status="unverified")],
        lossless_in_place_proven=False,
    )
    assert projection["projection_state"] == "qc_blocked"
    assert "annotation_anchor_invalid" in projection["blocking_reasons"]
    bundle = rb.build_report_review_bundle(pack["matrix"], projection)
    assert bundle["bundle_state"] == "qc_blocked"
    codes = rb.validate_report_review_bundle(bundle, pack["matrix"], projection)
    assert "annotation_anchor_invalid" in codes


def test_tamper_matrix_content_hash_and_source_bytes_detected():
    pack = _bundle_pack(b"verifier-tamper-hash")
    tampered_proj = copy.deepcopy(pack["projection"])
    tampered_proj["matrix_content_hash"] = "0" * 64
    codes = rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], tampered_proj, pack["draft"]
    )
    assert "bundle_identity_mismatch" in codes

    tampered_src = copy.deepcopy(pack["projection"])
    tampered_src["source_bytes_hash"] = "0" * 64
    codes2 = rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], tampered_src, pack["draft"]
    )
    assert "bundle_identity_mismatch" in codes2


def test_tamper_anchor_map_hash_detected():
    pack = _bundle_pack(b"verifier-tamper-anchor-map")
    tampered = copy.deepcopy(pack["projection"])
    tampered["anchor_map_hash"] = "0" * 64
    codes = rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], tampered, pack["draft"]
    )
    assert "annotation_anchor_invalid" in codes


def test_three_piece_identity_mix_detected():
    pack = _bundle_pack(b"verifier-id-mix")
    mixed_draft = copy.deepcopy(pack["draft"])
    mixed_draft["run_id"] = "run-mixed-draft"
    mixed_draft["shared_identity"] = dict(mixed_draft["shared_identity"])
    mixed_draft["shared_identity"]["run_id"] = "run-mixed-draft"
    codes = rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], pack["projection"], mixed_draft
    )
    assert "bundle_identity_mismatch" in codes

    mixed_bundle = copy.deepcopy(pack["bundle"])
    mixed_bundle["issue_set_hash"] = "0" * 64
    codes2 = rb.validate_report_review_bundle(
        mixed_bundle, pack["matrix"], pack["projection"], pack["draft"]
    )
    assert "bundle_identity_mismatch" in codes2


def test_unresolved_conflict_and_not_evaluable_preserved_in_draft():
    pack = _positive_matrix(b"verifier-conflict-ne")
    matrix = copy.deepcopy(pack["matrix"])
    matrix["unresolved_conflicts"] = [
        {
            "conflict_id": "conflict-001",
            "issue_ids": ["issue-bundle-001"],
            "reason": "synthetic unresolved cutoff gap",
        }
    ]
    for unit in matrix["units"]:
        if unit["unit_id"] == "footnote-001":
            unit["coverage_status"] = "not_evaluable"
            unit["coverage_reason"] = "cutoff_gap"
    draft = rb.build_clean_draft(
        matrix,
        pack["report_source"],
        [_mod_for(pack)],
        requested=True,
    )
    assert draft is not None
    assert len(draft["unresolved_conflicts"]) >= len(matrix["unresolved_conflicts"])
    assert draft["unresolved_conflicts"][0]["conflict_id"] == "conflict-001"
    assert any(
        unit.get("coverage_status") == "not_evaluable"
        for unit in draft["not_evaluable_units"]
    )
    projection = rb.build_annotated_projection(
        matrix,
        pack["report_source"],
        [_annotation_for(pack)],
        lossless_in_place_proven=False,
    )
    bundle = rb.build_report_review_bundle(matrix, projection, draft)
    dropped = copy.deepcopy(draft)
    dropped["unresolved_conflicts"] = []
    codes = rb.validate_report_review_bundle(bundle, matrix, projection, dropped)
    assert "unresolved_issue_dropped" in codes


def test_original_registration_bytes_unchanged_after_bundle_build():
    raw_bytes = b"verifier-original-bytes"
    pack = _positive_matrix(raw_bytes)
    artifact_before = pack["report_source"]["report_artifact_id"]
    built = _bundle_pack(raw_bytes)
    assert built["report_source"]["report_artifact_id"] == artifact_before
    assert built["projection"]["source_bytes_hash"] == artifact_before
    assert built["projection"]["is_original_bytes_preserved"] is True
    assert built["projection"]["is_in_place_source_mutation"] is False
    assert built["draft"]["source_bytes_hash"] == artifact_before
    assert built["draft"]["is_original_bytes_preserved"] is True


def test_revision_diff_not_evaluable_never_resolved_on_incomparable():
    prev = _positive_matrix(b"verifier-diff-ne-a")
    curr = _positive_matrix(b"verifier-diff-ne-b")
    curr["matrix"]["run_binding"] = copy.deepcopy(prev["matrix"]["run_binding"])
    curr["matrix"]["run_binding"]["identity_algorithm_version"] = "ia-OTHER"
    rows = rb.build_revision_diff(prev["matrix"], curr["matrix"])
    assert rows
    assert all(row["revision_diff_state"] == "not_evaluable" for row in rows)
    assert all(row["comparable"] is False for row in rows)


def test_frozen_bundle_blocking_codes_only():
    pack = _bundle_pack(b"verifier-frozen-codes")
    tampered = copy.deepcopy(pack["draft"])
    tampered["draft_label"] = "FINAL"
    codes = rb.validate_report_review_bundle(
        pack["bundle"], pack["matrix"], pack["projection"], tampered
    )
    extra = set(codes) - set(FROZEN_BUNDLE_BLOCKING_CODES) - set(
        validator.build_diagnostic_index(
            contracts.matrix_obj(contracts.matrix_raw())
        ).keys()
    )
    # Adjacent matrix coverage codes from validate_report_review_matrix are allowed.
    matrix_codes = set(rr.validate_report_review_matrix(pack["matrix"]))
    assert set(codes) - matrix_codes <= set(FROZEN_BUNDLE_BLOCKING_CODES)


def test_slice01_frozen_inputs_and_oracle_clean(contract, matrix):
    assert _sha256_file(contracts.contract_path()) == EXPECTED_CONTRACT_SHA
    assert _sha256_file(contracts.matrix_path()) == EXPECTED_MATRIX_SHA
    assert _sha256_file(contracts.prose_path()) == EXPECTED_PROSE_SHA
    for rel, digest in EXPECTED_SLICE01_SRC.items():
        assert _sha256_file(POC_ROOT / rel) == digest, rel
    report = validator.oracle_parity_report(matrix["rows"], contract, matrix)
    assert report["mismatch_count"] == 0
    assert report["row_count"] == 86
    catalog = fixtures.build_fixture_catalog(matrix["rows"])
    assert catalog["catalog_sha256"] == (
        "76b43076d896001fb4b393f43329a194b32d9091625101d8eed2ba2ece940b53"
    )


def test_slice02_adjacency_report_review_receipt_present():
    receipt = POC_ROOT / "evidence" / "r6_report_review_runtime_receipt.json"
    assert receipt.is_file()
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["slice"]["id"] == "r6_runtime_slice_02"
    assert payload["boundaries"]["medical_writing_unchanged"] is True
    # Slice-02 source/object surface must still import cleanly beside bundle.
    assert hasattr(rr, "build_report_review_matrix")
    assert hasattr(rr, "validate_report_review_matrix")


def test_medical_writing_aggregate_unchanged(workbench_root):
    boundary = _medical_writing_boundary(workbench_root)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


def test_slice04_create_only_allowlist_exact():
    found = _poc_files()
    optional_receipts = {
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
    }
    # Optional receipts may be present singly or jointly during verifier write.
    extras = found - SLICE04_CREATE_ONLY_RELATIVE
    missing_required = (SLICE04_CREATE_ONLY_RELATIVE - optional_receipts) - found
    assert extras == set()
    assert missing_required == set()
    assert found <= SLICE04_CREATE_ONLY_RELATIVE


_REPRO_PROBE = r"""
import copy, os, sys
sys.path.insert(0, os.environ["MM_R6_SRC"])
from mm_r6 import report_bundle as rb
from mm_r6 import report_review as rr

IA_VER = "ia-r6-slice03-001"
IA_DIG = "ia-digest-r6-slice03-001"
raw = b"repro-bundle-subprocess"
desc = {
    "project_id": "project-r6-synthetic",
    "media_type": "docx",
    "source_name": "synthetic-report-slice03.docx",
    "reported_version_label": "v-synth-1",
    "reported_data_cutoff": "cutoff-2026-08-01",
    "reported_cutoff_status": "declared",
    "received_at": "2026-08-27T00:00:00Z",
    "source_scope": "project",
    "report_lineage_id": "lineage-r6-slice03",
    "parent_report_revision_id": None,
}
ev = lambda eid: {
    "evidence_id": eid, "authority_class": "source_document", "snapshot_id": "snap-1",
    "data_cutoff": "cutoff-2026-08-01", "source_revision_id": "run-source-revision-001",
    "locator": {"path": "/ev/" + eid}, "content_hash": "hash-" + eid, "relation": "supports",
}
reg = rr.register_report_source(raw, desc, [])
src = reg["report_source_revision"]
rrid = src["report_revision_id"]
units = []
for spec in (
    {"unit_id": "document-001", "unit_type": "document", "parent_unit_id": None,
     "required": True, "locator": {"path": "/"}, "extractability": "text",
     "anchor_digest": "ad-doc"},
    {"unit_id": "body-001", "unit_type": "body", "parent_unit_id": "document-001",
     "required": True, "locator": {"path": "/body/1", "report_revision_id": rrid},
     "extractability": "text", "anchor_digest": "ad-body"},
    {"unit_id": "footnote-001", "unit_type": "footnote", "parent_unit_id": "document-001",
     "required": True, "locator": {"path": "/footnote/1", "report_revision_id": rrid},
     "extractability": "text", "anchor_digest": "ad-fn"},
):
    unit = rr.build_report_unit(spec, src)
    unit["anchor_status"] = "verified"
    if unit["unit_id"] == "footnote-001":
        unit["coverage_status"] = "no_claim"
    else:
        unit["coverage_status"] = "no_claim" if unit["unit_type"] == "document" else "claimed"
    unit["coverage_reason"] = None
    units.append(unit)
claim = rr.build_report_claim(
    {"claim_id": "claim-1", "run_id": "run-r6-001", "unit_ids": ["body-001"],
     "claim_kind": "numeric", "source_text": "AE rate 11.9%", "normalized_claim_concept": "ae_rate",
     "scope": "project", "normalized_subject_or_site_scope": "project",
     "temporal_window": "cutoff-2026-08-01", "status": "supported",
     "evidence_refs": [ev("ev-1")], "issue_ids": [], "locator": {"path": "/body/1"}},
    src, identity_algorithm_version=IA_VER, identity_algorithm_digest=IA_DIG,
)
issue = rr.build_review_issue(
    {"issue_id": "issue-1", "run_id": "run-r6-001", "issue_kind": "omitted",
     "claim_ids": [], "unit_ids": ["footnote-001"], "severity": "medium",
     "clinical_or_document_scope": "footnote_gap", "evidence_refs": [ev("ev-fn")],
     "source_locators": [{"path": "/footnote/1", "report_revision_id": rrid,
     "report_artifact_id": src["report_artifact_id"], "unit_id": "footnote-001",
     "unit_type": "footnote"}], "lifecycle_state": "open", "revision_diff_state": "new",
     "related_issue_ids": [], "transition_refs": [], "current_note": "footnote gap",
     "normalized_clinical_concept": "footnote_gap", "normalized_subject_or_site_scope": "project",
     "normalized_temporal_window": "cutoff-2026-08-01"},
    src, identity_algorithm_version=IA_VER, identity_algorithm_digest=IA_DIG,
)
binding = {
    "project_id": "project-r6-synthetic", "run_id": "run-r6-001", "mode": "daily",
    "execution_basis": "full", "data_cutoff": "cutoff-2026-08-01",
    "source_revision_id": "run-source-revision-001", "knowledge_pack_version": "kp-1",
    "rule_activation_version": "rav-1", "mapping_version": "map-1",
    "identity_algorithm_version": IA_VER, "identity_algorithm_digest": IA_DIG,
    "schema_version": "r6-0.1",
}
surface = [{"expectation_id": "exp-risk-1", "expectation_kind": "accepted_risk",
            "authority_ref": "synthetic/risk-1", "scope": "project",
            "temporal_window": "cutoff-2026-08-01"}]
reverse = [{"expectation_id": "exp-risk-1", "claim_ids": [], "issue_ids": ["issue-1"],
            "not_evaluable_exception": None, "evidence_refs": [ev("ev-fn")]}]
matrix = rr.build_report_review_matrix(binding, src, units, [claim], [issue], surface, reverse)
locator = copy.deepcopy(issue["source_locators"][0])
ann = [{"annotation_id": "ann-1", "issue_id": issue["issue_id"], "locator": locator,
        "anchor_status": "verified", "note": "n"}]
p1 = rb.build_annotated_projection(matrix, src, ann, lossless_in_place_proven=False)
p2 = rb.build_annotated_projection(matrix, src, ann, lossless_in_place_proven=False)
if rr.canonical_bytes(p1) != rr.canonical_bytes(p2):
    raise SystemExit("projection_bytes_diverge")
if p1["projection_state"] != "qc_passed":
    raise SystemExit("projection_blocked:%s" % p1.get("blocking_reasons"))
bundle = rb.build_report_review_bundle(matrix, p1)
codes = rb.validate_report_review_bundle(bundle, matrix, p1)
if "bundle_identity_mismatch" in codes or "annotation_anchor_invalid" in codes:
    raise SystemExit("bundle_gate_fail:%s" % (codes,))
tampered = copy.deepcopy(p1)
tampered["anchor_map_hash"] = "0" * 64
codes2 = rb.validate_report_review_bundle(bundle, matrix, tampered)
if "annotation_anchor_invalid" not in codes2:
    raise SystemExit("tamper_miss")
print("ok")
"""


@pytest.mark.parametrize("opt_flag", ["", "-O", "-OO"])
@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
def test_repro_bundle_raise_based(opt_flag, hash_seed):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MM_R6_SRC"] = str(POC_ROOT / "src")
    cmd = [sys.executable]
    if opt_flag:
        cmd.append(opt_flag)
    cmd.extend(["-c", _REPRO_PROBE])
    proc = subprocess.run(
        cmd,
        cwd=str(WORKBENCH_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"opt={opt_flag!r} seed={hash_seed} rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "ok" in proc.stdout
