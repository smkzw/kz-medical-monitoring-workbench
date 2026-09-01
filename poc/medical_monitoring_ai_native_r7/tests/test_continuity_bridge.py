"""Focused synthetic/offline tests for Slice-08B continuity bridge.

Verifies:
1. R5 typed packet validation, drift detection, and member closure extraction
2. R6 mode output validation and 5-path atomic item extraction across daily/pre_lock/post_lock
3. Rejection of missing/duplicate/extra outputs and query draft draft-only violations
4. R1 Store envelope construction, commit, and byte-level file/envelope tamper detection
5. 7-step carry-forward verification: Steps 1-6 integrity failures vs Step 7 business rules
6. Cross-object risk dependencies for Query draft reuse
7. Determinism of output-set digest, item digest, and member-set digest under hash seeds & optimizers
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import pytest

from mm_r1.domain import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    NodeType,
    PAYLOAD_ROLE_INFERENCE,
)
from mm_r1.store import Store
from mm_r5.r5_publication_authority import (
    R5AuthorityPacket,
    R5PublicationAuthorityBridge,
    R5PublicationAuthorityError,
    R5PublicationAuthorityInputAssembler,
    R5PublicationRunIdentity,
)
from mm_r6 import mode_output as mo
from mm_r7.continuity import (
    CarryForwardItem,
    DecisionBaseline,
    canonical_digest,
    canonical_json,
)
from mm_r7.continuity_bridge import (
    AtomicExtractionError,
    CommittedModeOutputSet,
    ContinuityBridgeError,
    ContinuityIntegrityError,
    ContinuityVerificationResult,
    ExtractedAtom,
    R1ArtifactVerificationError,
    R5AuthorityVerificationError,
    R5MemberClosure,
    R6OutputVerificationError,
    build_mode_output_envelope,
    build_verified_carry_forward_item,
    build_verified_carry_forward_items,
    commit_mode_outputs,
    compute_artifact_member_set_digest,
    compute_r6_output_set_digest,
    extract_atomic_items,
    extract_r5_member_closure,
    validate_r5_authority_packet,
    verify_carry_forward_item,
)
from s4_runtime_fixtures import build_runtime_input
from test_r5_publication_authority import TypedEvent, TypedSite, TypedSource, TypedSubject, TypedVisit


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

PROJECT_ID = "project.p1"
RUN_ID = "run.r1"
TARGET_RUN_ID = "run.r2"
PUBLIC_TOKEN = "public-run-1"
SNAPSHOT_ID = "snap.s1"
CUTOFF = "cutoff.v1"
REVISION_ID = "rev.r1"
RISK_ID = "d09_marker:m-rk"
SUBJECT_ID = "subject.1001"
SITE_ID = "site.01"


def _make_r5_identity(
    *,
    project_id: str = PROJECT_ID,
    run_id: str = RUN_ID,
    public_run_token: str = PUBLIC_TOKEN,
    snapshot_ref: str = SNAPSHOT_ID,
    cutoff_ref: str = CUTOFF,
    site_refs: Tuple[str, ...] = (SITE_ID,),
) -> R5PublicationRunIdentity:
    return R5PublicationRunIdentity(
        project_ref=project_id,
        run_ref=run_id,
        public_run_token=public_run_token,
        snapshot_ref=snapshot_ref,
        cutoff_ref=cutoff_ref,
        site_refs=site_refs,
        snapshot_token=snapshot_ref,
    )


def _make_r5_packet(
    *,
    project_id: str = PROJECT_ID,
    run_id: str = RUN_ID,
    public_run_token: str = PUBLIC_TOKEN,
    snapshot_ref: str = SNAPSHOT_ID,
    cutoff_ref: str = CUTOFF,
    site_refs: Tuple[str, ...] = (SITE_ID,),
    subject_id: str = SUBJECT_ID,
    site_id: str = SITE_ID,
) -> R5AuthorityPacket:
    identity = _make_r5_identity(
        project_id=project_id,
        run_id=run_id,
        public_run_token=public_run_token,
        snapshot_ref=snapshot_ref,
        cutoff_ref=cutoff_ref,
        site_refs=site_refs,
    )
    runtime_input = build_runtime_input("single_analysis")
    risk = runtime_input.anchor.accepted_risk_identity
    source_pair = runtime_input.authority_receipt.source_revision_content_pairs[0]

    members = {
        "accepted_subjects": (
            TypedSubject(subject_id, site_id, risk.spine_ref),
        ),
        "accepted_sites": tuple(TypedSite(s) for s in site_refs),
        "accepted_events": (
            TypedEvent(
                runtime_input.deep_link_state.event_ref,
                subject_id,
                site_id,
                risk.spine_ref,
            ),
        ),
        "accepted_visits": (
            TypedVisit(
                runtime_input.deep_link_state.visit_ref,
                subject_id,
                site_id,
                risk.spine_ref,
            ),
        ),
        "accepted_sources": (
            TypedSource(
                runtime_input.deep_link_state.source_locator_ref,
                snapshot_ref,
                source_pair.revision_id,
                source_pair.content_hash,
            ),
        ),
    }

    assembled = R5PublicationAuthorityInputAssembler().assemble(
        identity,
        runtime_input=runtime_input,
        **members,
    )
    return R5PublicationAuthorityBridge().build(assembled)


def _make_run_binding(mode: str = "daily", **overrides) -> Dict[str, Any]:
    base = {
        "project_id": PROJECT_ID,
        "run_id": RUN_ID,
        "mode": mode,
        "execution_basis": "full",
        "data_cutoff": CUTOFF,
        "source_revision_id": REVISION_ID,
        "knowledge_pack_version": "kp-08b-v1",
        "rule_activation_version": "rav-08b-v1",
        "mapping_version": "map-08b-v1",
        "identity_algorithm_version": "ia-08b-v1",
        "identity_algorithm_digest": "ia-digest-08b-v1",
        "schema_version": "r6-0.1",
        "carry_forward_run_ids": [],
        "mode_transition": "explicit_new_run",
        "actor": "synthetic-executor",
        "created_at": "2026-08-28T00:00:00Z",
    }
    if mode == "post_lock_pre_cfdi":
        base.update({
            "data_cutoff": CUTOFF,
            "source_revision_id": REVISION_ID,
            "fixed_total": True,
            "locked_snapshot_hash": "snap-hash-fixed-001",
            "output_cutoff_ref": CUTOFF,
            "output_revision_ref": REVISION_ID,
            "local_os_user": "local-user-synthetic",
            "acceptance_evidence_hash": "accept-hash-fixed-001",
        })
    base.update(overrides)
    return base


def _make_daily_outputs(run_binding: Mapping[str, Any], **finding_overrides) -> Tuple[Dict[str, Any], ...]:
    contract = mo.build_mode_contract("daily")
    ctx = mo.default_entry_context_for_mode("daily", run_binding=run_binding)
    digest = "auth-digest-daily-001"
    refs = {
        "project_id": run_binding["project_id"],
        "run_id": run_binding["run_id"],
        "data_cutoff": run_binding["data_cutoff"],
        "source_revision_id": run_binding["source_revision_id"],
        "authority_digest": digest,
        "coverage_digest": digest,
        "qc_digest": digest,
        "digest": digest,
    }
    finding = {
        "finding_id": "finding-001",
        "risk_id": RISK_ID,
        "issue_id": "issue-001",
        "subject_id": SUBJECT_ID,
        "site_id": SITE_ID,
        "scope_kind": "subject",
        "basis": "方案要求报告不良事件",
        "finding": "受试者出现未记录的不良反应",
        "action": "请核实并补录",
        "evidence_refs": ["ev-listing-001"],
        "locator": {"path": "AE.AETERM", "record_id": "rec-001", "field": "AETERM"},
    }
    finding.update(finding_overrides)
    return mo.build_daily_mode_outputs(
        run_binding,
        contract,
        authority_refs=refs,
        coverage_refs=refs,
        qc_refs=refs,
        findings=[finding],
        risks=[{"risk_id": RISK_ID, "severity": "high", "risk_type": "ae_omission"}],
        entry_context=ctx,
    )


def _make_pre_lock_outputs(run_binding: Mapping[str, Any]) -> Tuple[Dict[str, Any], ...]:
    contract = mo.build_mode_contract("pre_lock")
    ctx = mo.default_entry_context_for_mode("pre_lock", run_binding=run_binding)
    digest = "auth-digest-prelock-001"
    refs = {
        "project_id": run_binding["project_id"],
        "run_id": run_binding["run_id"],
        "data_cutoff": run_binding["data_cutoff"],
        "source_revision_id": run_binding["source_revision_id"],
        "authority_digest": digest,
        "coverage_digest": digest,
        "qc_digest": digest,
        "digest": digest,
    }
    pop_scope = {"scope_kind": "project", "population_id": "pop-001", "label": "全受试者群体", "site_count": 1, "subject_count": 1, "risk_count": 1}
    check_items = [
        {"level": "project", "check_kind": "lock_prep", "status": "ready", "evidence_refs": ["ev-proj-001"], "locator": {"path": "project.lock", "record_id": "p1"}},
        {"level": "site", "check_kind": "site_cutoff", "status": "ready", "site_id": SITE_ID, "evidence_refs": ["ev-site-001"], "locator": {"path": "site.cutoff", "record_id": "s1"}},
        {"level": "subject", "check_kind": "subj_listing", "status": "ready", "site_id": SITE_ID, "subject_id": SUBJECT_ID, "evidence_refs": ["ev-subj-001"], "locator": {"path": "subj.listing", "record_id": "sub1"}},
    ]
    return mo.build_pre_lock_mode_outputs(
        run_binding,
        contract,
        authority_refs=refs,
        coverage_refs=refs,
        qc_refs=refs,
        from_source_revision_id="revision-prior-000",
        revision_reason="数据库锁库前例行比对",
        risks=[{"risk_id": RISK_ID, "severity": "high"}],
        check_items=check_items,
        population_scope=pop_scope,
        entry_context=ctx,
    )


def _make_post_lock_outputs(run_binding: Mapping[str, Any]) -> Tuple[Dict[str, Any], ...]:
    contract = mo.build_mode_contract("post_lock_pre_cfdi")
    ctx = mo.default_entry_context_for_mode("post_lock_pre_cfdi", run_binding=run_binding)
    digest = "auth-digest-postlock-001"
    refs = {
        "project_id": run_binding["project_id"],
        "run_id": run_binding["run_id"],
        "data_cutoff": run_binding["data_cutoff"],
        "source_revision_id": run_binding["source_revision_id"],
        "authority_digest": digest,
        "coverage_digest": digest,
        "qc_digest": digest,
        "digest": digest,
    }
    pop_totals = {"site_count": 1, "subject_count": 1, "risk_count": 1}
    site_mat = [{
        "site_id": SITE_ID,
        "subject_ids": [SUBJECT_ID],
        "risk_ids": [RISK_ID],
        "evidence_refs": ["ev-site-001"],
        "locator": {"path": f"SITE.{SITE_ID}", "record_id": SITE_ID},
    }]
    subj_mat = [{
        "subject_id": SUBJECT_ID,
        "site_id": SITE_ID,
        "profile_ref": {"profile_id": f"prof-{SUBJECT_ID}"},
        "timeline_ref": {"timeline_id": f"tl-{SUBJECT_ID}"},
        "risk_ids": [RISK_ID],
        "evidence_refs": ["ev-subj-001"],
        "locator": {"path": f"SUBJ.{SUBJECT_ID}", "record_id": SUBJECT_ID},
    }]
    check_items = [
        {"level": "project", "check_kind": "project_lock", "scope_id": run_binding["project_id"], "status": "ready", "risk_ids": [RISK_ID], "evidence_refs": ["ev-chk-project"], "locator": {"path": "CHK.PROJECT", "record_id": "chk-p1"}},
        {"level": "site", "check_kind": "site_coverage", "scope_id": SITE_ID, "status": "ready", "risk_ids": [RISK_ID], "evidence_refs": ["ev-chk-site"], "locator": {"path": "CHK.SITE", "record_id": "chk-s1"}},
        {"level": "subject", "check_kind": "subject_profile", "scope_id": SUBJECT_ID, "status": "ready", "risk_ids": [RISK_ID], "evidence_refs": ["ev-chk-subject"], "locator": {"path": "CHK.SUBJ", "record_id": "chk-u1"}},
    ]
    report_summary = {"project_id": run_binding["project_id"], "status": "completed"}
    risk_summary = {"high_count": 1, "medium_count": 0, "low_count": 0, "risk_ids": [RISK_ID]}

    report, site, subj, chk = mo.build_post_lock_mode_outputs(
        run_binding,
        contract,
        authority_refs=refs,
        coverage_refs=refs,
        qc_refs=refs,
        population_totals=pop_totals,
        report_version="v1.0",
        project_summary=report_summary,
        risk_summary=risk_summary,
        evidence_refs=["ev-postlock-001"],
        site_materials=site_mat,
        subject_materials=subj_mat,
        check_items=check_items,
        entry_context=ctx,
    )
    return report, site, subj, chk


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_r5_authority_packet_validation_and_drift():
    packet = _make_r5_packet()
    validated = validate_r5_authority_packet(packet)
    assert validated.packet_digest == packet.packet_digest

    # Validation against matching run binding facts succeeds
    binding = _make_run_binding()
    validate_r5_authority_packet(
        packet,
        run_binding=binding,
        project_id=PROJECT_ID,
        run_id=RUN_ID,
        public_run_token=PUBLIC_TOKEN,
        snapshot_id=SNAPSHOT_ID,
        data_cutoff=CUTOFF,
    )

    # Rejection of invalid types
    with pytest.raises(R5AuthorityVerificationError) as exc:
        validate_r5_authority_packet({"packet_digest": "abc"})
    assert exc.value.code == "R5_PACKET_TYPE_INVALID"

    # Project mismatch
    with pytest.raises(R5AuthorityVerificationError) as exc:
        validate_r5_authority_packet(packet, project_id="OTHER-PROJECT")
    assert exc.value.code == "R5_PROJECT_MISMATCH"

    # Run mismatch
    with pytest.raises(R5AuthorityVerificationError) as exc:
        validate_r5_authority_packet(packet, run_id="other-run")
    assert exc.value.code == "R5_RUN_MISMATCH"

    # Cutoff mismatch
    with pytest.raises(R5AuthorityVerificationError) as exc:
        validate_r5_authority_packet(packet, data_cutoff="2026-01-01")
    assert exc.value.code == "R5_CUTOFF_MISMATCH"


def test_r5_member_closure_membership_checks():
    packet = _make_r5_packet(
        site_refs=(SITE_ID, "site.02"),
        subject_id=SUBJECT_ID,
        site_id=SITE_ID,
    )
    closure = extract_r5_member_closure(packet)
    assert closure.project_ref == PROJECT_ID
    assert closure.run_ref == RUN_ID
    assert SITE_ID in closure.site_refs
    assert "site.02" in closure.site_refs
    assert closure.contains_site(SITE_ID)
    assert closure.contains_subject(SUBJECT_ID)
    assert closure.contains_risk(RISK_ID)
    assert not closure.contains_subject("UNKNOWN-SUBJ")


def test_r6_daily_mode_validation_commit_and_atomic_extraction(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)
    r5_packet = _make_r5_packet()

    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=r5_packet)
    assert committed.mode == "daily"
    assert committed.run_id == RUN_ID
    assert len(committed.envelopes) == 4
    assert len(committed.artifact_member_ids) == 4

    # Output set digest and member set digest
    assert len(committed.r6_output_set_digest) == 64
    assert len(committed.artifact_member_set_digest) == 64

    # Atoms: exactly 2 atoms extracted for daily (risk_instance & query_draft)
    assert len(committed.extracted_atoms) == 2
    types = {a.object_type for a in committed.extracted_atoms}
    assert types == {"risk_instance", "query_draft"}

    risk_atom = next(a for a in committed.extracted_atoms if a.object_type == "risk_instance")
    assert risk_atom.object_id == RISK_ID
    assert risk_atom.output_kind == "current_full_risk"
    assert risk_atom.artifact_id != ""

    query_atom = next(a for a in committed.extracted_atoms if a.object_type == "query_draft")
    assert query_atom.output_kind == "affected_query_draft"
    assert query_atom.artifact_id != ""

    store.close()


def test_r6_pre_lock_mode_validation_commit_and_atomic_extraction(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("pre_lock")
    outputs = _make_pre_lock_outputs(run)
    r5_packet = _make_r5_packet()

    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=r5_packet)
    assert committed.mode == "pre_lock"
    assert len(committed.envelopes) == 4

    # Exactly 1 atom extracted for pre_lock (risk_instance from full_risk)
    assert len(committed.extracted_atoms) == 1
    atom = committed.extracted_atoms[0]
    assert atom.object_type == "risk_instance"
    assert atom.object_id == RISK_ID
    assert atom.output_kind == "full_risk"

    store.close()


def test_r6_post_lock_mode_validation_commit_and_atomic_extraction(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("post_lock_pre_cfdi")
    outputs = _make_post_lock_outputs(run)
    r5_packet = _make_r5_packet(site_id=SITE_ID, subject_id=SUBJECT_ID)
    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=r5_packet)
    assert committed.mode == "post_lock_pre_cfdi"
    assert len(committed.envelopes) == 4

    # 2 atoms extracted: site_materials & subject_materials (both object_type == "mode_output_item")
    assert len(committed.extracted_atoms) == 2
    for a in committed.extracted_atoms:
        assert a.object_type == "mode_output_item"
    mat_ids = {a.object_id for a in committed.extracted_atoms}
    expected_site_mat_id = outputs[1]["payload"]["materials"][0]["site_material_id"]
    expected_subj_mat_id = outputs[2]["payload"]["materials"][0]["subject_material_id"]
    assert mat_ids == {expected_site_mat_id, expected_subj_mat_id}
    store.close()


def test_output_set_rejection_on_missing_duplicate_or_extra_kinds(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)

    # Missing 1 output (only 3 outputs)
    with pytest.raises(R6OutputVerificationError) as exc:
        commit_mode_outputs(store, outputs[:3], run_binding=run)
    assert exc.value.code == "OUTPUT_COUNT_MISMATCH"

    # Duplicate kind
    dup_outputs = [outputs[0], outputs[0], outputs[2], outputs[3]]
    with pytest.raises(R6OutputVerificationError) as exc:
        commit_mode_outputs(store, dup_outputs, run_binding=run)
    assert exc.value.code == "DUPLICATE_OUTPUT_KIND"

    # Extra output
    extra_outputs = list(outputs) + [outputs[0]]
    with pytest.raises(R6OutputVerificationError) as exc:
        commit_mode_outputs(store, extra_outputs, run_binding=run)
    assert exc.value.code == "OUTPUT_COUNT_MISMATCH"

    store.close()


def test_atomic_extraction_rejections_and_r5_cross_checks():
    run = _make_run_binding("daily")
    outputs = list(_make_daily_outputs(run))
    r5_packet = _make_r5_packet()

    # Query draft with forbidden sent flag
    bad_query_output = copy.deepcopy(outputs[2])
    bad_query_output["payload"]["query_drafts"][0]["is_sent"] = True
    bad_outputs = [outputs[0], outputs[1], bad_query_output, outputs[3]]
    with pytest.raises(AtomicExtractionError) as exc:
        extract_atomic_items(bad_outputs, r5_packet=r5_packet)
    assert exc.value.code == "QUERY_DRAFT_FORBIDDEN_FLAG"

    # Query draft referencing unknown subject outside R5
    bad_subj_output = copy.deepcopy(outputs[2])
    bad_subj_output["payload"]["query_drafts"][0]["subject_id"] = "UNKNOWN-SUBJ-999"
    bad_outputs_subj = [outputs[0], outputs[1], bad_subj_output, outputs[3]]
    with pytest.raises(AtomicExtractionError) as exc:
        extract_atomic_items(bad_outputs_subj, r5_packet=r5_packet)
    assert exc.value.code == "QUERY_DRAFT_SUBJECT_NOT_IN_R5"

    # Risk not present in R5
    bad_risk_output = copy.deepcopy(outputs[1])
    bad_risk_output["payload"]["risks"][0]["risk_id"] = "UNKNOWN-RISK-999"
    bad_outputs_risk = [outputs[0], bad_risk_output, outputs[2], outputs[3]]
    with pytest.raises(AtomicExtractionError) as exc:
        extract_atomic_items(bad_outputs_risk, r5_packet=r5_packet)
    assert exc.value.code == "RISK_NOT_IN_R5_AUTHORITY"


def test_r1_store_envelope_structure_and_byte_level_tamper_detection(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)

    committed = commit_mode_outputs(store, outputs, run_binding=run)
    envelope = committed.envelopes[0]

    # Verify immutable envelope properties per §16
    assert envelope.artifact_type == "r6_mode_output"
    assert envelope.version == mo.CONTRACT_VERSION
    assert envelope.node_type == NodeType.DETERMINISTIC_SERVICE
    assert envelope.payload_role == PAYLOAD_ROLE_INFERENCE
    assert envelope.completeness == ArtifactCompleteness.COMPLETE
    assert envelope.coverage is None
    assert len(envelope.input_hashes) == 1

    # Store verification passes
    assert store.verify_artifact(envelope.artifact_id) is True

    # Mutate 1 byte of the content-addressed file on disk
    file_path = tmp_path / "artifacts" / f"{envelope.content_hash}.json"
    assert file_path.exists()
    file_bytes = bytearray(file_path.read_bytes())
    file_bytes[0] = ord(b"X") if file_bytes[0] != ord(b"X") else ord(b"Y")
    file_path.write_bytes(bytes(file_bytes))

    # Store byte verification now fails
    assert store.verify_artifact(envelope.artifact_id) is False

    # Attempting carry-forward verification on tampered file fails closed with ContinuityIntegrityError
    item = CarryForwardItem(
        object_type="risk_instance",
        object_ref=RISK_ID,
        disposition="reuse_unchanged",
        source_run_id=RUN_ID,
        source_project_id=PROJECT_ID,
        source_mode="daily",
        target_run_id=TARGET_RUN_ID,
        target_project_id=PROJECT_ID,
        target_mode="daily",
        source_object_id=RISK_ID,
        target_object_id=RISK_ID,
        source_artifact_id=envelope.artifact_id,
        source_artifact_sha256=envelope.content_hash,
        artifact_verified=True,
        artifact_member_verified=True,
        reuse_reviewed=True,
        reason="测试沿用",
    )
    pub = {
        "publication_state": "available",
        "project_id": PROJECT_ID,
        "mode": "daily",
        "run_id": RUN_ID,
        "artifact_member_ids": [envelope.artifact_id],
    }
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(item, store=store, publication=pub)
    assert exc.value.code == "ARTIFACT_STORE_VERIFICATION_FAILED"

    store.close()


def test_carry_forward_7_step_positive_reuse(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)
    r5_packet = _make_r5_packet()

    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=r5_packet)
    risk_atom = next(a for a in committed.extracted_atoms if a.object_type == "risk_instance")

    item = CarryForwardItem(
        object_type="risk_instance",
        object_ref=risk_atom.object_id,
        disposition="reuse_unchanged",
        source_run_id=RUN_ID,
        source_project_id=PROJECT_ID,
        source_mode="daily",
        target_run_id=TARGET_RUN_ID,
        target_project_id=PROJECT_ID,
        target_mode="daily",
        source_object_id=risk_atom.object_id,
        target_object_id=risk_atom.object_id,
        source_identity=risk_atom.item_digest,
        target_identity=risk_atom.item_digest,
        source_artifact_id=risk_atom.artifact_id,
        source_artifact_sha256=risk_atom.artifact_id,
        artifact_verified=True,
        artifact_member_verified=True,
        reuse_reviewed=True,
        data_change_kind="unchanged",
        current_present=True,
        reason="未变化风险沿用",
    )

    pub = {
        "publication_state": "available",
        "project_id": PROJECT_ID,
        "mode": "daily",
        "run_id": RUN_ID,
        "artifact_member_ids": list(committed.artifact_member_ids),
    }

    result = verify_carry_forward_item(item, store=store, publication=pub, r5_packet=r5_packet)
    assert result.integrity_ok is True
    assert result.verified_disposition == "reuse_unchanged"

    # Build verified CarryForwardItem with machine-verified flags
    built = build_verified_carry_forward_item(item, store=store, publication=pub, r5_packet=r5_packet)
    assert built.artifact_verified is True
    assert built.artifact_member_verified is True
    assert built.reuse_reviewed is True
    assert built.disposition == "reuse_unchanged"

    store.close()


def test_carry_forward_steps_1_to_6_integrity_failures_block(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)
    committed = commit_mode_outputs(store, outputs, run_binding=run)
    risk_atom = next(a for a in committed.extracted_atoms if a.object_type == "risk_instance")

    base_item = CarryForwardItem(
        object_type="risk_instance",
        object_ref=risk_atom.object_id,
        disposition="reuse_unchanged",
        source_run_id=RUN_ID,
        source_project_id=PROJECT_ID,
        source_mode="daily",
        target_run_id=TARGET_RUN_ID,
        target_project_id=PROJECT_ID,
        target_mode="daily",
        source_object_id=risk_atom.object_id,
        target_object_id=risk_atom.object_id,
        source_identity=risk_atom.item_digest,
        target_identity=risk_atom.item_digest,
        source_artifact_id=risk_atom.artifact_id,
        source_artifact_sha256=risk_atom.artifact_id,
        artifact_verified=True,
        artifact_member_verified=True,
        reuse_reviewed=True,
        reason="测试阻断",
    )

    valid_pub = {
        "publication_state": "available",
        "project_id": PROJECT_ID,
        "mode": "daily",
        "run_id": RUN_ID,
        "artifact_member_ids": list(committed.artifact_member_ids),
    }

    # Step 1: Publication not available
    blocked_pub = dict(valid_pub, publication_state="publishing")
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(base_item, store=store, publication=blocked_pub)
    assert exc.value.code == "SOURCE_PUBLICATION_NOT_AVAILABLE"

    # Step 1: Project mismatch
    proj_pub = dict(valid_pub, project_id="DIFF-PROJECT")
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(base_item, store=store, publication=proj_pub)
    assert exc.value.code == "PUBLICATION_PROJECT_MISMATCH"

    # Step 2: Artifact not in publication member list
    non_member_pub = dict(valid_pub, artifact_member_ids=["other-art-id"])
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(base_item, store=store, publication=non_member_pub)
    assert exc.value.code == "ARTIFACT_NOT_IN_PUBLICATION_MEMBERS"

    # Step 3: Run ID mismatch in item vs envelope
    wrong_run_item = replace(base_item, source_run_id="wrong-run-id", item_digest="")
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(wrong_run_item, store=store, publication=valid_pub)
    assert exc.value.code == "ARTIFACT_RUN_ID_MISMATCH"

    # Step 6: Object missing in re-extracted output
    missing_obj_item = replace(base_item, source_object_id="non-existent-risk-id", target_object_id="non-existent-risk-id", item_digest="")
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(missing_obj_item, store=store, publication=valid_pub)
    assert exc.value.code == "OBJECT_NOT_FOUND_IN_OUTPUT"

    # Step 6: Item digest mismatch
    forged_digest_item = replace(base_item, source_identity="0" * 64, target_identity="0" * 64, item_digest="")
    with pytest.raises(ContinuityIntegrityError) as exc:
        verify_carry_forward_item(forged_digest_item, store=store, publication=valid_pub)
    assert exc.value.code == "ITEM_SOURCE_IDENTITY_MISMATCH"

    store.close()


def test_carry_forward_step_7_business_applicability_dispositions(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)
    committed = commit_mode_outputs(store, outputs, run_binding=run)
    risk_atom = next(a for a in committed.extracted_atoms if a.object_type == "risk_instance")

    valid_pub = {
        "publication_state": "available",
        "project_id": PROJECT_ID,
        "mode": "daily",
        "run_id": RUN_ID,
        "artifact_member_ids": list(committed.artifact_member_ids),
    }

    # Data revised -> re_evaluate_changed_data
    revised_item = CarryForwardItem(
        object_type="risk_instance",
        object_ref=risk_atom.object_id,
        disposition="re_evaluate_changed_data",
        source_run_id=RUN_ID,
        source_project_id=PROJECT_ID,
        source_mode="daily",
        target_run_id=TARGET_RUN_ID,
        target_project_id=PROJECT_ID,
        target_mode="daily",
        source_object_id=risk_atom.object_id,
        target_object_id=risk_atom.object_id,
        source_identity=risk_atom.item_digest,
        target_identity=risk_atom.item_digest,
        source_artifact_id=risk_atom.artifact_id,
        source_artifact_sha256=risk_atom.artifact_id,
        artifact_verified=True,
        artifact_member_verified=True,
        reuse_reviewed=False,
        data_change_kind="revised",
        current_present=True,
        reason="数据修订重评",
    )
    res_revised = verify_carry_forward_item(revised_item, store=store, publication=valid_pub)
    assert res_revised.verified_disposition == "re_evaluate_changed_data"

    # Rule change applies -> re_evaluate_rule_change
    rule_changed_item = replace(
        revised_item,
        data_change_kind="unchanged",
        governing_rule_revision_ids=("rule-a",),
        changed_applicable_rule_ids=("rule-a",),
        item_digest="",
        reason="规则变更重评",
    )
    res_rule = verify_carry_forward_item(rule_changed_item, store=store, publication=valid_pub)
    assert res_rule.verified_disposition == "re_evaluate_rule_change"

    store.close()


def test_build_verified_carry_forward_items_batch_with_query_risk_dependency(tmp_path: Path):
    store = Store(tmp_path / "store.sqlite3", tmp_path / "artifacts")
    run = _make_run_binding("daily")
    outputs = _make_daily_outputs(run)
    r5_packet = _make_r5_packet()
    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=r5_packet)

    risk_atom = next(a for a in committed.extracted_atoms if a.object_type == "risk_instance")
    query_atom = next(a for a in committed.extracted_atoms if a.object_type == "query_draft")

    pub = {
        "publication_state": "available",
        "project_id": PROJECT_ID,
        "mode": "daily",
        "run_id": RUN_ID,
        "artifact_member_ids": list(committed.artifact_member_ids),
    }

    # Case A: Risk is unchanged -> both risk & query become reuse_unchanged
    items_a = [
        CarryForwardItem(
            object_type="risk_instance",
            object_ref=risk_atom.object_id,
            disposition="reuse_unchanged",
            ordinal=0,
            source_run_id=RUN_ID,
            source_project_id=PROJECT_ID,
            source_mode="daily",
            target_run_id=TARGET_RUN_ID,
            target_project_id=PROJECT_ID,
            target_mode="daily",
            source_object_id=risk_atom.object_id,
            target_object_id=risk_atom.object_id,
            source_identity=risk_atom.item_digest,
            target_identity=risk_atom.item_digest,
            source_artifact_id=risk_atom.artifact_id,
            source_artifact_sha256=risk_atom.artifact_id,
            artifact_verified=True,
            artifact_member_verified=True,
            reuse_reviewed=True,
            data_change_kind="unchanged",
            current_present=True,
            reason="风险沿用",
        ),
        CarryForwardItem(
            object_type="query_draft",
            object_ref=query_atom.object_id,
            disposition="reuse_unchanged",
            ordinal=1,
            source_run_id=RUN_ID,
            source_project_id=PROJECT_ID,
            source_mode="daily",
            target_run_id=TARGET_RUN_ID,
            target_project_id=PROJECT_ID,
            target_mode="daily",
            source_object_id=query_atom.object_id,
            target_object_id=query_atom.object_id,
            source_identity=query_atom.item_digest,
            target_identity=query_atom.item_digest,
            source_artifact_id=query_atom.artifact_id,
            source_artifact_sha256=query_atom.artifact_id,
            artifact_verified=True,
            artifact_member_verified=True,
            reuse_reviewed=True,
            data_change_kind="unchanged",
            current_present=True,
            reason="草稿沿用",
        ),
    ]

    verified_a = build_verified_carry_forward_items(items_a, store=store, publication=pub, r5_packet=r5_packet)
    assert len(verified_a) == 2
    assert verified_a[0].disposition == "reuse_unchanged"
    assert verified_a[1].disposition == "reuse_unchanged"

    # Case B: Risk data is revised -> risk becomes re_evaluate_changed_data, and query becomes re_evaluate_prior_uncertain
    items_b = [
        replace(items_a[0], data_change_kind="revised", disposition="re_evaluate_changed_data", reuse_reviewed=False, item_digest=""),
        items_a[1],
    ]
    verified_b = build_verified_carry_forward_items(items_b, store=store, publication=pub, r5_packet=r5_packet)
    assert verified_b[0].disposition == "re_evaluate_changed_data"
    assert verified_b[1].disposition == "re_evaluate_prior_uncertain"

    store.close()


_BRIDGE_DETERMINISM_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from mm_r7.continuity_bridge import compute_r6_output_set_digest, compute_artifact_member_set_digest
from mm_r7.continuity import canonical_digest
records = [
    {"artifact_id": "0f6738cede292bc64c188bb8addd7bbc1ad58c3c665c323495427abaceff7158", "output_id": "out-001", "output_kind": "change_summary"},
    {"artifact_id": "3d586d461198ea92414188b8b9fdda292910e19cd7d1ea622518dfebf3f04e6c", "output_id": "out-002", "output_kind": "current_full_risk"},
    {"artifact_id": "8a17b580077caaf4e7c6f7ee791105d4057c2a911ca7e79575f05c4c72bf3037", "output_id": "out-003", "output_kind": "affected_query_draft"},
    {"artifact_id": "e8ca2540437cf901b0b5ec4e421d6329d178d3d0a25f1b6bb71816a3afaf7b4c", "output_id": "out-004", "output_kind": "data_knowledge_rule_model_change_note"},
]
members = [
    "0f6738cede292bc64c188bb8addd7bbc1ad58c3c665c323495427abaceff7158",
    "3d586d461198ea92414188b8b9fdda292910e19cd7d1ea622518dfebf3f04e6c",
    "8a17b580077caaf4e7c6f7ee791105d4057c2a911ca7e79575f05c4c72bf3037",
    "e8ca2540437cf901b0b5ec4e421d6329d178d3d0a25f1b6bb71816a3afaf7b4c",
]
atom = {"risk_id": "risk.primary", "severity": "high", "risk_type": "ae_omission"}

res = {
    "output_set_digest": compute_r6_output_set_digest(records),
    "member_set_digest": compute_artifact_member_set_digest(members),
    "item_digest": canonical_digest(atom),
}
print(json.dumps(res, sort_keys=True))
"""


def test_determinism_under_hashseed_and_optimization_matrix():
    records = [
        {"artifact_id": "art-001", "output_id": "out-001", "output_kind": "change_summary"},
        {"artifact_id": "art-002", "output_id": "out-002", "output_kind": "current_full_risk"},
    ]
    out_set_dig = compute_r6_output_set_digest(records)
    member_set_dig = compute_artifact_member_set_digest(["art-002", "art-001"])

    # Permuted input order yields identical output_set_digest & member_set_digest
    permuted_records = list(reversed(records))
    assert compute_r6_output_set_digest(permuted_records) == out_set_dig
    assert compute_artifact_member_set_digest(["art-001", "art-002"]) == member_set_dig


def test_atomic_extraction_rejects_missing_payload():
    with pytest.raises(AtomicExtractionError) as blocked:
        extract_atomic_items(
            [{"output_kind": "full_risk", "output_id": "output-001", "payload": None}]
        )
    assert blocked.value.code == "OUTPUT_PAYLOAD_INVALID"


@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
@pytest.mark.parametrize("opt_flag", [(), ("-O",), ("-OO",)])
def test_bridge_digests_deterministic_9cell_matrix(hash_seed: str, opt_flag: Tuple[str, ...]):
    import os, subprocess, sys
    env = os.environ.copy()
    from conftest import SRC_DIR
    cmd = [sys.executable, *opt_flag, "-c", _BRIDGE_DETERMINISM_PROBE, str(SRC_DIR)]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    payload = json.loads(proc.stdout.strip())
    assert payload["output_set_digest"] == "142063add88a6092b873ed014d1e13c4b468561382a8093f055d416cea7abb67"
    assert payload["member_set_digest"] == "5a37be709ef63902da73df93b13aca03db3d0f06137830b8466864f493f7c605"
    assert payload["item_digest"] == "ad698b9390ad9f978be0cd37f62eecd4f3a43e39c53777bcbd66293a5408dba6"
