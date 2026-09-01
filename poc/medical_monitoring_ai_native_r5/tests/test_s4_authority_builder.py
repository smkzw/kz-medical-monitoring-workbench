"""Focused W2 tests for the R5-S4 runtime authority builder
(``mm_r5.s4_authority_builder``): typed R4/R5 joins, real R4 recomputation,
baseline extension projection, and the fail-closed build gates.

The builder never reads oracle files; ``test_builder_no_oracle_reads`` scans
the runtime source with the stdlib ``ast`` module (no file I/O in runtime).
"""

from __future__ import annotations

import ast
import dataclasses
import pathlib
from typing import Optional

import pytest

import mm_r4.ensemble as en
import mm_r4.ensemble_contracts as ec
import mm_r4.d10_contracts as d10c
import mm_r5.contracts as c5
from mm_r4.ensemble_contracts import AdjudicationBinding
from mm_r5 import s4_contracts as s4
from mm_r5.s4_authority_builder import (
    _baseline_rows,
    _bind_baseline_recheck,
    build_s4_authority_state,
)
from mm_r5.s4_projection import build_s4_authority_packet
from s4_runtime_fixtures import (
    ATTEMPT_SETS,
    build_attempts,
    build_audience_labels,
    build_baseline_items,
    build_change_band,
    build_deep_link_state,
    build_digest_context,
    build_history_log,
    build_model_evidence,
    build_query_draft,
    build_raw_outputs,
    build_receipt,
    build_runtime_input,
    build_source_input,
    build_typed_anchor,
    build_worker_outputs,
    _derive_refs,
)

_R5_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "mm_r5"

#: States whose active ensemble is exactly the a1/a2 pair that the single
#: accepted ModelEvidence permit covers.  The strict permit closure forbids
#: projecting the a1/a2 permit into any other ensemble, so those variants
#: must build with ``model_evidence=None``.
_MODEL_EVIDENCE_PERMITTED_STATES = ("multi_analysis", "failed_verification")


def _variant_input(state: str) -> s4.R5S4RuntimeInput:
    """A valid runtime input for one variant under the strict ModelEvidence
    permit closure: the a1/a2-only permit may not be projected into any
    ensemble other than exactly a1/a2, so single/mutual/graded build with
    ``model_evidence=None``."""
    ri = build_runtime_input(state)
    if state not in _MODEL_EVIDENCE_PERMITTED_STATES:
        return dataclasses.replace(ri, model_evidence=None)
    return ri


# ---------------------------------------------------------------------------
# Per-variant build state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_build_state_valid_for_every_variant(state: str) -> None:
    """Every runtime-input variant yields a valid internal build state (the
    a1/a2-only ModelEvidence permit is not projected into other ensembles)."""
    ri = _variant_input(state)
    bs = build_s4_authority_state(ri)
    n = len(ri.attempts)
    expected_state = {0: "no_ensemble", 1: "single_analysis"}.get(
        n, "multi_analysis")
    assert bs.ensemble_projection_state == expected_state
    assert len(bs.worker_views) == n
    assert len(bs.raw_artifacts) == n
    assert len(bs.verification_rows) == n
    assert (bs.input_content_hash is None) == (n == 0)
    if n:
        assert bs.input_content_hash == ri.attempts[0].input_content_hash
    # every repeated field is a tuple (build state never stores a list)
    for field in dataclasses.fields(bs):
        value = getattr(bs, field.name)
        if field.name in (
                "attempts", "worker_outputs", "worker_views", "raw_artifacts",
                "baseline_items", "baseline_rows", "verification_rows",
                "conflict_rows"):
            assert isinstance(value, tuple), field.name


def test_risk_identity_bound_from_anchor() -> None:
    """Risk identity is the external accepted identity, projected verbatim."""
    anchor = build_typed_anchor()
    bs = build_s4_authority_state(build_runtime_input("multi_analysis"))
    rid = anchor.accepted_risk_identity
    assert bs.risk_identity.risk_ref == rid.risk_ref
    assert bs.risk_identity.risk_identity_hash == rid.risk_identity_hash
    assert bs.risk_identity.domain == rid.domain == "ae"
    assert bs.risk_identity.domain_zh == "AE"
    assert bs.risk_identity.severity == rid.severity == "high"
    assert bs.risk_identity.severity_zh == "高"
    assert bs.risk_identity.change_kind == rid.change_kind == "new"
    assert bs.risk_identity.change_cause == rid.change_cause == "data"


def test_worker_view_ordinal_by_sorted_attempt_id() -> None:
    """Ordinal 1..N is assigned by sorted attempt id; ordinal_zh closed."""
    bs = build_s4_authority_state(build_runtime_input("multi_analysis"))
    views = bs.worker_views
    assert [view.attempt_id for view in views] == ["a1", "a2"]
    assert [view.ordinal for view in views] == [1, 2]
    assert [view.ordinal_zh for view in views] == ["分析一", "分析二"]
    for view in views:
        assert view.role == "worker"
        assert view.raw_artifact_ref == f"raw:{view.attempt_id}"
        assert view.verification_ref == f"verification:v-{view.attempt_id}"
        assert view.output_artifact_ref == f"artifact:{view.attempt_id}"


def test_worker_view_declared_hash_is_r4_recompute() -> None:
    """declared_output_hash equals the real R4 recompute of the typed output."""
    ri = build_runtime_input("multi_analysis")
    bs = build_s4_authority_state(ri)
    output_by_attempt = {out.attempt_id: out for out in ri.worker_outputs}
    for view in bs.worker_views:
        assert view.declared_output_hash == en.worker_output_content_hash(
            output_by_attempt[view.attempt_id])


def test_raw_artifact_hash_separation() -> None:
    """raw sha != parsed hash; raw sha == sha256(bytes); declared == parsed."""
    ri = build_runtime_input("multi_analysis")
    bs = build_s4_authority_state(ri)
    raw_by_attempt = {raw.attempt_id: raw for raw in ri.raw_outputs}
    for artifact in bs.raw_artifacts:
        raw = raw_by_attempt[artifact.attempt_id]
        assert artifact.raw_bytes_sha256 != artifact.parsed_output_hash
        assert artifact.raw_bytes_sha256 == s4.s4_sha256(raw.raw_bytes)
        assert artifact.declared_output_hash == artifact.parsed_output_hash
        assert artifact.attempt_id == artifact.artifact_id.removeprefix("raw:")


def test_baseline_item_projection_equals_anchor() -> None:
    """W1 alignment #1: packet baseline items = R4 items + accepted anchor
    import extensions (project/run/snapshot/cutoff/source_revision)."""
    anchor = build_typed_anchor()
    bs = build_s4_authority_state(build_runtime_input("multi_analysis"))
    accepted = sorted(anchor.accepted_baseline_items, key=lambda b: b.item_id)
    projected = sorted(bs.baseline_items, key=lambda b: b.item_id)
    assert [b.item_id for b in projected] == [b.item_id for b in accepted]
    for item, acc in zip(projected, accepted):
        for key in ("item_id", "source_kind", "source_locator_ids",
                    "source_revision_id", "snapshot_id", "claimed_identity",
                    "temporal_window", "claimed_content_hash",
                    "origin_artifact_hash", "project_ref", "run_ref",
                    "snapshot_ref", "cutoff_ref", "source_revision"):
            assert getattr(item, key) == getattr(acc, key), key


def test_baseline_rows_item_x_attempt_only_assessed() -> None:
    """Baseline rows are real item x attempt assessments only; unassessed
    item.b2 never becomes a default 'baseline established' row."""
    bs = build_s4_authority_state(build_runtime_input("multi_analysis"))
    rows = bs.baseline_rows
    assert len(rows) == 2  # item.b1 x a1, item.b1 x a2
    assert {row.item_id for row in rows} == {"item.b1"}
    for row in rows:
        assert row.row_ref == f"baseline-row:{row.item_id}:{row.attempt_id}"
        assert row.state == "confirmed"
        assert row.source_recheck_locator_ids == ("loc.src1",)
        assert row.recheck_complete is True
        assert row.source_revision_id == "rev.1"
        assert row.snapshot_id == "snap.1"


def test_verification_rows_recomputed_by_r4() -> None:
    """Verification rows equal the real R4 verify_attempt recompute."""
    ri = build_runtime_input("multi_analysis")
    bs = build_s4_authority_state(ri)
    attempt_by_id = {attempt.attempt_id: attempt for attempt in ri.attempts}
    output_by_id = {out.attempt_id: out for out in ri.worker_outputs}
    for row in bs.verification_rows:
        ver = en.verify_attempt(attempt_by_id[row.attempt_id],
                                output_by_id[row.attempt_id],
                                ri.digest_context)
        assert row.verification_id == ver.verification_id
        assert row.result == ver.result
        assert row.checked_dimensions == tuple(sorted(set(
            ver.checked_dimensions)))
        assert set(row.checked_dimensions) == s4.SEVEN_DIMENSIONS
        assert row.recomputed is True


def test_failed_verification_variant_has_failed_row() -> None:
    """The failed_verification fixture yields a real failed row (a1
    rule_version_mismatch) while the base packet stays constructible."""
    bs = build_s4_authority_state(build_runtime_input("failed_verification"))
    by_attempt = {row.attempt_id: row for row in bs.verification_rows}
    assert by_attempt["a1"].result == "failed"
    assert by_attempt["a1"].failure_reason_codes == ("rule_version_mismatch",)
    assert by_attempt["a2"].result == "passed"
    assert by_attempt["a2"].failure_reason_codes == ()


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_conflict_rows_equal_full_r4_derivation(state: str) -> None:
    """W1 alignment #3: the conflict set is the FULL real R4 derivation --
    nothing added, removed or hidden; N=0 stays frozen empty."""
    ri = _variant_input(state)
    bs = build_s4_authority_state(ri)
    n = len(ri.attempts)
    if n == 0:
        assert bs.conflict_rows == ()
        return
    outputs = {out.attempt_id: out for out in ri.worker_outputs}
    derived = en.derive_conflicts(attempts=ri.attempts,
                                  worker_outputs=outputs,
                                  baseline_items=ri.baseline_items)
    assert [row.conflict_id for row in bs.conflict_rows] == [
        c.conflict_id for c in derived]
    assert [row.relation for row in bs.conflict_rows] == [
        c.relation for c in derived]
    ordinal_by_attempt = {attempt.attempt_id: index
                          for index, attempt in enumerate(sorted(
                              ri.attempts, key=lambda a: a.attempt_id),
                              start=1)}
    for row in bs.conflict_rows:
        assert row.ordinal_labels_zh == tuple(sorted(
            s4.ORDINAL_ZH[ordinal_by_attempt[aid] - 1]
            for aid in row.member_attempt_ids))


def test_conflict_row_ordinal_labels_and_non_hideable() -> None:
    """Conflict ordinal labels derive from sorted attempt ids; high /
    mutual_negation / baseline_miss are never hidden."""
    bs = build_s4_authority_state(_variant_input("mutual_negation"))
    by_relation = {row.relation: row for row in bs.conflict_rows}
    assert by_relation["mutual_negation"].hidden is False
    assert by_relation["baseline_miss"].hidden is False
    assert by_relation["shared_finding"].hidden is False
    for row in bs.conflict_rows:
        assert len(row.ordinal_labels_zh) == len(row.member_attempt_ids)


def test_adjudication_row_presence_and_independence() -> None:
    """Adjudication present iff N>=2; binding disjoint from every worker."""
    for state in ("no_ensemble", "single_analysis", "multi_analysis"):
        bs = build_s4_authority_state(_variant_input(state))
        present = bs.adjudication_row.present
        assert present == (state == "multi_analysis")
        if present:
            assert bs.adjudication_row.adds_explanation_only is True
            assert bs.adjudication_row.reviewed_artifact_refs == (
                "artifact:a1", "artifact:a2")
            for view in bs.worker_views:
                assert bs.adjudication_row.binding_id != view.binding_id
                assert bs.adjudication_row.session_id != view.session_id
                assert (bs.adjudication_row.independent_context_hash
                        != view.independent_context_hash)


def test_query_draft_row_only_multi_analysis() -> None:
    """Query draft row exists only for multi_analysis."""
    for state in ("no_ensemble", "single_analysis", "multi_analysis"):
        bs = build_s4_authority_state(_variant_input(state))
        assert (bs.query_draft_row is not None) == (state == "multi_analysis")
    row = build_s4_authority_state(
        _variant_input("multi_analysis")).query_draft_row
    assert row is not None
    assert row.risk_ref == "d09_marker:m-rk"
    assert row.draft_only is True
    assert row.pd_wording_state == "not_pd"
    assert row.source_locator_refs == ("loc.src1",)


def test_journey_link_fallback_none_and_availability() -> None:
    """Journey fallback is always 'none'; availability derived mechanically
    from the accepted target + typed source availability."""
    bs = build_s4_authority_state(build_runtime_input("multi_analysis"))
    assert bs.journey_link.fallback_policy == "none"
    assert bs.journey_link.journey_available is True
    assert bs.journey_link.unavailable_reason_zh is None
    # typed unavailable source => unlocatable journey with the fixed reason.
    ri = dataclasses.replace(
        build_runtime_input("multi_analysis"),
        source_input=build_source_input(available=False,
                                        reason="target_not_projectable"),
        deep_link_state=build_deep_link_state(source_available=False))
    bs2 = build_s4_authority_state(ri)
    assert bs2.journey_link.journey_available is False
    assert bs2.journey_link.unavailable_reason_zh == (
        s4.JOURNEY_UNAVAILABLE_REASON_ZH)


def test_input_reorder_does_not_change_build_state() -> None:
    """Attempt/output/raw reordering never changes the build state (packet
    identity/hash stability)."""
    ri = build_runtime_input("multi_analysis")
    base = build_s4_authority_state(ri)
    reordered = dataclasses.replace(
        ri,
        attempts=tuple(reversed(ri.attempts)),
        worker_outputs=tuple(reversed(ri.worker_outputs)),
        raw_outputs=tuple(reversed(ri.raw_outputs)),
    )
    assert build_s4_authority_state(reordered) == base


# ---------------------------------------------------------------------------
# Upstream Inspector per-reference rebuild (W1 alignment #3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_upstream_inspector_rebuild_matches_fixture_derivation(state: str) -> None:
    """The independently rebuilt Inspector refs equal the fixture's real-R4
    derivation for every variant (no cross_plane_projection_drift on base
    packets)."""
    ri = _variant_input(state)
    refs = _derive_refs(ATTEMPT_SETS[state])
    assert refs["risk_ref"] == ri.upstream_inspector.risk_ref
    assert (refs["authority_receipt_ref"]
            == ri.upstream_inspector.authority_receipt_ref)
    assert refs["analysis_attempt_refs"] == (
        ri.upstream_inspector.analysis_attempt_refs)
    assert refs["baseline_item_refs"] == (
        ri.upstream_inspector.baseline_item_refs)
    assert refs["baseline_assessment_refs"] == (
        ri.upstream_inspector.baseline_assessment_refs)
    assert refs["conflict_refs"] == ri.upstream_inspector.conflict_refs
    assert refs["verification_refs"] == (
        ri.upstream_inspector.verification_refs)
    assert refs["adjudication_ref"] == ri.upstream_inspector.adjudication_ref
    assert refs["source_locator_refs"] == (
        ri.upstream_inspector.source_locator_refs)


def test_upstream_inspector_empty_planes_frozen() -> None:
    """S2-frozen empty planes stay empty on every base packet input."""
    ri = build_runtime_input("multi_analysis")
    assert ri.upstream_inspector.worker_output_refs == ()
    assert ri.upstream_inspector.support_evidence_refs == ()
    assert ri.upstream_inspector.counterevidence_refs == ()
    assert ri.upstream_inspector.query_draft_ref is None


# ---------------------------------------------------------------------------
# Fail-closed build gates
# ---------------------------------------------------------------------------


def test_fail_closed_missing_raw_output() -> None:
    ri = build_runtime_input("multi_analysis")
    ri = dataclasses.replace(ri, raw_outputs=ri.raw_outputs[:1])
    with pytest.raises(s4.S4RuntimeContractError):
        build_s4_authority_state(ri)


def test_fail_closed_unknown_attempt() -> None:
    ri = build_runtime_input("multi_analysis")
    extra = build_attempts(("m1",))
    ri = dataclasses.replace(ri, attempts=ri.attempts + extra)
    with pytest.raises(s4.S4RuntimeContractError):
        build_s4_authority_state(ri)


def test_fail_closed_input_hash_mismatch() -> None:
    ri = build_runtime_input("multi_analysis")
    attempt = ri.attempts[0]
    attempt = ec.AnalysisAttempt(
        attempt_id=attempt.attempt_id, ensemble_id=attempt.ensemble_id,
        binding_id=attempt.binding_id, session_id=attempt.session_id,
        model_id=attempt.model_id, model_version=attempt.model_version,
        role=attempt.role,
        independent_context_hash=attempt.independent_context_hash,
        input_content_hash=s4.s4_sha256(b"other"),  # divergent input hash
        output_artifact_ref=attempt.output_artifact_ref,
        output_hash=attempt.output_hash,
        claimed_date_window=attempt.claimed_date_window,
        claimed_unit_contract=attempt.claimed_unit_contract,
        claimed_source_revision=attempt.claimed_source_revision,
        claimed_rule_id=attempt.claimed_rule_id,
        claimed_rule_version=attempt.claimed_rule_version)
    ri = dataclasses.replace(ri, attempts=(attempt, ri.attempts[1]))
    with pytest.raises(s4.S4RuntimeContractError):
        build_s4_authority_state(ri)


def test_fail_closed_critical_severity_deferred() -> None:
    """Critical severity is a frozen deferred boundary: any critical accepted
    identity fails closed at build time (s4.critical_severity_authority_missing)."""
    anchor = build_typed_anchor()
    rid = anchor.accepted_risk_identity
    critical_rid = s4.S4AcceptedRiskIdentity(
        risk_ref=rid.risk_ref, risk_identity_hash=rid.risk_identity_hash,
        domain=rid.domain, domain_zh=rid.domain_zh,
        monitoring_priority=rid.monitoring_priority,
        severity="critical", severity_zh="紧急",
        change_kind=rid.change_kind, change_cause=rid.change_cause,
        project_ref=rid.project_ref, run_ref=rid.run_ref,
        snapshot_ref=rid.snapshot_ref, cutoff_ref=rid.cutoff_ref,
        site_ref=rid.site_ref, subject_ref=rid.subject_ref,
        spine_ref=rid.spine_ref)
    critical_anchor_body = s4.packet_as_mapping(anchor)
    critical_anchor_body["severity_authority"] = "critical"
    critical_anchor_body["critical_severity_authority"] = "crit.auth.v1"
    critical_anchor_body["accepted_risk_identity"] = s4.packet_as_mapping(
        critical_rid)
    critical_hash = s4.compute_anchor_identity_hash(critical_anchor_body)
    critical_anchor = s4.S4AcceptedAuthorityAnchor(
        schema=anchor.schema, status=anchor.status,
        authority_mode=anchor.authority_mode, project_ref=anchor.project_ref,
        run_ref=anchor.run_ref, snapshot_ref=anchor.snapshot_ref,
        cutoff_ref=anchor.cutoff_ref, site_ref=anchor.site_ref,
        subject_ref=anchor.subject_ref, risk_ref=anchor.risk_ref,
        spine_ref=anchor.spine_ref,
        risk_priority_authority=anchor.risk_priority_authority,
        severity_authority="critical",
        critical_severity_authority="crit.auth.v1",
        accepted_receipt_content_hash=anchor.accepted_receipt_content_hash,
        accepted_receipt_identity=anchor.accepted_receipt_identity,
        accepted_risk_identity_hash=anchor.accepted_risk_identity_hash,
        accepted_risk_identity=critical_rid,
        accepted_adjudicator_binding=anchor.accepted_adjudicator_binding,
        accepted_baseline_items=anchor.accepted_baseline_items,
        accepted_query_draft=anchor.accepted_query_draft,
        accepted_journey_target=anchor.accepted_journey_target,
        accepted_history_no_ensemble=anchor.accepted_history_no_ensemble,
        accepted_history_single_analysis=(
            anchor.accepted_history_single_analysis),
        accepted_history_multi_analysis=anchor.accepted_history_multi_analysis,
        attempt_authority_rows=anchor.attempt_authority_rows,
        model_evidence_permits=anchor.model_evidence_permits,
        anchor_identity_hash=critical_hash)
    ri = dataclasses.replace(build_runtime_input("single_analysis"),
                             anchor=critical_anchor)
    with pytest.raises(s4.S4RuntimeContractError):
        build_s4_authority_state(ri)


def test_no_ensemble_never_calls_derive_conflicts() -> None:
    """N=0 short-circuits: conflict set frozen empty, no member-less
    baseline_miss is fabricated."""
    bs = build_s4_authority_state(build_runtime_input("no_ensemble"))
    assert bs.conflict_rows == ()
    assert bs.baseline_rows == ()


# ---------------------------------------------------------------------------
# Runtime source never reads oracle files (AST scan)
# ---------------------------------------------------------------------------


def test_builder_no_oracle_reads() -> None:
    """s4_authority_builder/s4_projection source performs zero file I/O and
    imports no generator/verifier/registry/oracle module."""
    for name in ("s4_authority_builder.py", "s4_projection.py"):
        source = (_R5_SRC / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        # no assert statements (fail closed, never assert)
        assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree))
        # no open / read_text / read_bytes / Path usage
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute):
                    calls.append(fn.attr)
                elif isinstance(fn, ast.Name):
                    calls.append(fn.id)
        forbidden = {"open", "read_text", "read_bytes", "read"}
        assert not (set(calls) & forbidden), name
        names = {node.id for node in ast.walk(tree)
                 if isinstance(node, ast.Name)}
        assert "Path" not in names, name
        # no oracle-module imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "tools" not in node.module, name
                assert "generate_medical_monitoring" not in node.module, name
                assert "verify_medical_monitoring" not in node.module, name
                assert "artifacts" not in node.module, name
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "tools" not in alias.name, name
                    assert "artifacts" not in alias.name, name


# ---------------------------------------------------------------------------
# Authoritative join negative tests (independent, not registry-driven)
# ---------------------------------------------------------------------------


def _rejects_code(state: str, mutate, code: str) -> None:
    """Apply one input mutation and assert the builder fails closed with the
    accepted single contract code."""
    ri = mutate(build_runtime_input(state))
    with pytest.raises(s4.S4RuntimeContractError, match=code):
        build_s4_authority_state(ri)


def test_receipt_wrong_project_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, authority_receipt=dataclasses.replace(
                ri.authority_receipt, project_ref="project.X")),
        "s4.receipt_hash_mismatch")


def test_receipt_wrong_revision_rejected() -> None:
    receipt = build_receipt()
    pair = receipt.source_revision_content_pairs[0]
    wrong = c5.SourceRevisionContentPair(revision_id="rev.zzz",
                                         content_hash=pair.content_hash)
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, authority_receipt=dataclasses.replace(
                ri.authority_receipt, source_revision_content_pairs=(wrong,))),
        "s4.receipt_hash_mismatch")


def test_change_band_wrong_receipt_ref_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, change_band=dataclasses.replace(
                ri.change_band, authority_receipt_ref="receipt:" + "a" * 64)),
        "s4.receipt_hash_mismatch")


def test_change_band_wrong_risk_ref_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, change_band=dataclasses.replace(
                ri.change_band, risk_ref="d10_marker:ghost")),
        "s4.anchor_claim_drift")


def test_upstream_inspector_wrong_risk_ref_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, upstream_inspector=dataclasses.replace(
                ri.upstream_inspector, risk_ref="d09_marker:ghost")),
        "s4.cross_plane_projection_drift")


def test_upstream_inspector_deferred_leaf_nonempty_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, upstream_inspector=dataclasses.replace(
                ri.upstream_inspector, worker_output_refs=("artifact:a1",))),
        "s4.imported_object_drift")


def test_deep_link_wrong_project_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, deep_link_state=dataclasses.replace(
                ri.deep_link_state, project_ref="project.X")),
        "s4.source_path_unresolvable")


def test_deep_link_wrong_risk_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, deep_link_state=dataclasses.replace(
                ri.deep_link_state, risk_ref="d10_marker:ghost")),
        "s4.source_path_unresolvable")


def test_source_resolution_wrong_locator_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, source_input=dataclasses.replace(
                ri.source_input, resolution=dataclasses.replace(
                    ri.source_input.resolution, locator_id="loc.zzz"))),
        "s4.source_path_unresolvable")


def test_source_resolution_wrong_revision_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, source_input=dataclasses.replace(
                ri.source_input, resolution=dataclasses.replace(
                    ri.source_input.resolution, revision_id="rev.zzz"))),
        "s4.source_path_unresolvable")


def test_unavailable_source_identity_mismatch_still_rejected() -> None:
    """The typed unavailable state only relaxes the SOURCE LOCATOR; every
    other identity mismatch still fails closed (never downgraded)."""
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri,
            source_input=build_source_input(available=False,
                                            reason="target_not_projectable"),
            deep_link_state=dataclasses.replace(
                build_deep_link_state(source_available=False),
                project_ref="project.X")),
        "s4.source_path_unresolvable")


def test_unavailable_source_with_deep_locator_rejected() -> None:
    """unavailable requires the deep-link source locator to be absent."""
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, source_input=build_source_input(available=False,
                                                reason="target_not_projectable")),
        "s4.source_path_unresolvable")


def test_query_wrong_basis_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, query_draft=dataclasses.replace(
                ri.query_draft, basis_sentence="X")),
        "s4.query_projection_drift")


def test_query_forbidden_on_single_rejected() -> None:
    _rejects_code(
        "single_analysis",
        lambda ri: dataclasses.replace(ri, query_draft=build_query_draft()),
        "s4.query_projection_drift")


def test_adjudicator_wrong_reviewed_refs_rejected() -> None:
    def mutate(ri):
        binding = ri.adjudicator.binding
        wrong = AdjudicationBinding(
            binding_id=binding.binding_id, session_id=binding.session_id,
            model_id=binding.model_id, model_version=binding.model_version,
            outcome=binding.outcome,
            reviewed_artifact_refs=("artifact:a1",))
        return dataclasses.replace(
            ri, adjudicator=dataclasses.replace(ri.adjudicator, binding=wrong))
    _rejects_code("multi_analysis", mutate, "s4.anchor_claim_drift")


def test_adjudicator_identity_drift_rejected() -> None:
    def mutate(ri):
        binding = ri.adjudicator.binding
        wrong = AdjudicationBinding(
            binding_id=binding.binding_id, session_id=binding.session_id,
            model_id="adj.zzz", model_version=binding.model_version,
            outcome=binding.outcome,
            reviewed_artifact_refs=binding.reviewed_artifact_refs)
        return dataclasses.replace(
            ri, adjudicator=dataclasses.replace(ri.adjudicator, binding=wrong))
    _rejects_code("multi_analysis", mutate, "s4.anchor_claim_drift")


def test_adjudicator_on_single_rejected() -> None:
    _rejects_code(
        "single_analysis",
        lambda ri: dataclasses.replace(
            ri, adjudicator=dataclasses.replace(
                build_runtime_input("multi_analysis").adjudicator)),
        "s4.cardinality_not_0_1_n")


def test_adjudicator_missing_on_multi_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(ri, adjudicator=None),
        "s4.cardinality_not_0_1_n")


def _reanchor(base: s4.S4AcceptedAuthorityAnchor, **changes) -> s4.S4AcceptedAuthorityAnchor:
    """Rebuild an accepted anchor with the given field changes and a
    recomputed self-hash (a dataclasses.replace would re-run __post_init__
    against the stale hash)."""
    accepted_risk_identity = changes.get(
        "accepted_risk_identity", base.accepted_risk_identity)
    accepted_adjudicator_binding = changes.get(
        "accepted_adjudicator_binding", base.accepted_adjudicator_binding)
    accepted_risk_identity_hash = changes.get(
        "accepted_risk_identity_hash", base.accepted_risk_identity_hash)
    body = s4.packet_as_mapping(base)
    body["accepted_risk_identity"] = s4.packet_as_mapping(
        accepted_risk_identity)
    body["accepted_adjudicator_binding"] = s4.packet_as_mapping(
        accepted_adjudicator_binding)
    body["accepted_risk_identity_hash"] = accepted_risk_identity_hash
    return s4.S4AcceptedAuthorityAnchor(
        schema=base.schema, status=base.status, authority_mode=base.authority_mode,
        project_ref=base.project_ref, run_ref=base.run_ref,
        snapshot_ref=base.snapshot_ref, cutoff_ref=base.cutoff_ref,
        site_ref=base.site_ref, subject_ref=base.subject_ref,
        risk_ref=base.risk_ref, spine_ref=base.spine_ref,
        risk_priority_authority=base.risk_priority_authority,
        severity_authority=base.severity_authority,
        critical_severity_authority=base.critical_severity_authority,
        accepted_receipt_content_hash=base.accepted_receipt_content_hash,
        accepted_receipt_identity=base.accepted_receipt_identity,
        accepted_risk_identity_hash=accepted_risk_identity_hash,
        accepted_risk_identity=accepted_risk_identity,
        accepted_adjudicator_binding=accepted_adjudicator_binding,
        accepted_baseline_items=base.accepted_baseline_items,
        accepted_query_draft=base.accepted_query_draft,
        accepted_journey_target=base.accepted_journey_target,
        accepted_history_no_ensemble=base.accepted_history_no_ensemble,
        accepted_history_single_analysis=base.accepted_history_single_analysis,
        accepted_history_multi_analysis=base.accepted_history_multi_analysis,
        attempt_authority_rows=base.attempt_authority_rows,
        model_evidence_permits=base.model_evidence_permits,
        anchor_identity_hash=s4.compute_anchor_identity_hash(body))


def test_supporting_outcome_after_failed_verification_rejected() -> None:
    """A failed verification blocks any supporting adjudication outcome
    (s4.verification_unresolved_authority), even when the binding identity is
    otherwise consistent with the accepted binding."""
    def mutate(ri):
        adj = build_typed_anchor().accepted_adjudicator_binding
        supporting_binding = s4.S4AcceptedAdjudicatorBinding(
            binding_id=adj.binding_id, session_id=adj.session_id,
            model_id=adj.model_id, model_version=adj.model_version,
            outcome="merged_supported",
            independent_context_hash=adj.independent_context_hash)
        anchor = _reanchor(build_typed_anchor(),
                           accepted_adjudicator_binding=supporting_binding)
        binding = ri.adjudicator.binding
        adjudicator = s4.R5S4AdjudicatorInput(
            binding=AdjudicationBinding(
                binding_id=binding.binding_id,
                session_id=binding.session_id,
                model_id=binding.model_id,
                model_version=binding.model_version,
                outcome="merged_supported",
                reviewed_artifact_refs=binding.reviewed_artifact_refs),
            independent_context_hash=ri.adjudicator.independent_context_hash)
        return dataclasses.replace(
            ri, anchor=anchor, adjudicator=adjudicator)
    _rejects_code("failed_verification", mutate,
                  "s4.verification_unresolved_authority")


def test_history_foreign_chain_rejected() -> None:
    """A self-consistent foreign chain (valid internal hashes) that does not
    contain the accepted prefix must fail closed."""
    def mutate(ri):
        log = ri.history_log
        entries = []
        prior = s4.GENESIS_HASH
        for entry in log.entries:
            forged = s4.R5S4HistoryEntry(
                entry_id=entry.entry_id, seq=entry.seq, kind=entry.kind,
                payload_ref=entry.payload_ref + "-foreign",
                prior_entry_hash=prior, entry_hash="")
            entries.append(forged)
            prior = forged.entry_hash
        return dataclasses.replace(
            ri, history_log=s4.R5S4HistoryLog(
                history_ref=log.history_ref, head_seq=len(entries),
                head_hash=entries[-1].entry_hash, entries=tuple(entries)))
    _rejects_code("multi_analysis", mutate, "s4.history_append_only_violation")


def test_history_multi_empty_rejected() -> None:
    def mutate(ri):
        empty = s4.R5S4HistoryLog(history_ref="history:s4.0", head_seq=0,
                                  head_hash=s4.GENESIS_HASH, entries=())
        return dataclasses.replace(ri, history_log=empty)
    _rejects_code("multi_analysis", mutate, "s4.history_append_only_violation")


def test_history_no_ensemble_nonempty_rejected() -> None:
    def mutate(ri):
        return dataclasses.replace(
            ri, history_log=build_history_log("single_analysis"))
    _rejects_code("no_ensemble", mutate, "s4.ensemble_zero_must_be_empty")


def test_model_evidence_leaf_drift_rejected() -> None:
    _rejects_code(
        "multi_analysis",
        lambda ri: dataclasses.replace(
            ri, model_evidence=dataclasses.replace(
                ri.model_evidence, role="counterevidence_suggestion")),
        "s4.model_evidence_not_permitted")


def test_model_evidence_zero_residue_rejected() -> None:
    _rejects_code(
        "no_ensemble",
        lambda ri: dataclasses.replace(
            ri, model_evidence=build_model_evidence("multi_analysis")),
        "s4.model_evidence_not_permitted")


def test_missing_attempt_output_rejected() -> None:
    def mutate(ri):
        return dataclasses.replace(ri, worker_outputs=ri.worker_outputs[:1])
    _rejects_code("multi_analysis", mutate, "s4.cardinality_not_0_1_n")


def test_extra_unaccepted_attempt_rejected() -> None:
    """An attempt with no accepted attempt_authority_rows entry is rejected
    even when its worker output/raw collections are consistent."""
    def mutate(ri):
        extra_attempt = dataclasses.replace(
            build_attempts(("a1",))[0], attempt_id="zzz",
            binding_id="worker.b.zzz", session_id="worker.s.zzz",
            output_artifact_ref="artifact:zzz")
        extra_output = en.WorkerAnalysisOutput(
            attempt_id="zzz", assessments=(), findings=(), gap_candidates=())
        extra_raw = s4.R5S4RawOutputInput(
            attempt_id="zzz", artifact_id="raw:zzz", raw_format="utf8_text",
            raw_bytes=b"{}")
        return dataclasses.replace(
            ri,
            attempts=ri.attempts + (extra_attempt,),
            worker_outputs=ri.worker_outputs + (extra_output,),
            raw_outputs=ri.raw_outputs + (extra_raw,))
    _rejects_code("multi_analysis", mutate, "s4.anchor_claim_drift")


def test_raw_parsed_equality_rejected(monkeypatch) -> None:
    """Raw/parsed hash equality is rejected (strict separation)."""
    def _collide(output):
        raw = next(r for r in build_raw_outputs(("a1",))
                   if r.attempt_id == output.attempt_id)
        import hashlib as _hashlib
        return _hashlib.sha256(raw.raw_bytes).hexdigest()
    monkeypatch.setattr(en, "worker_output_content_hash", _collide)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.raw_parsed_hash_confusion"):
        build_s4_authority_state(build_runtime_input("single_analysis"))


def test_raw_bytes_external_mismatch_rejected() -> None:
    """Tampered injected raw bytes no longer match the accepted raw sha."""
    def mutate(ri):
        raw = ri.raw_outputs[0]
        return dataclasses.replace(
            ri, raw_outputs=(dataclasses.replace(
                raw, raw_bytes=b"tampered"),) + ri.raw_outputs[1:])
    _rejects_code("multi_analysis", mutate, "s4.raw_sha_external_mismatch")


def test_baseline_recheck_per_item_subset_rule() -> None:
    """Unit rule: a row's recheck locators must be a subset of the item's own
    authorized source locators (per-item subset, not a global set)."""
    ri = build_runtime_input("multi_analysis")
    items_by_id = {item.item_id: item for item in ri.baseline_items}
    row = s4.R5S4BaselineRow(
        row_ref="baseline-row:item.b1:a1", item_id="item.b1",
        attempt_id="a1", state="confirmed",
        reason_codes=("source_rechecked",),
        source_recheck_locator_ids=("loc.other",),
        source_revision_id="rev.1", snapshot_id="snap.1",
        recheck_complete=True)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.baseline_recheck_missing"):
        _bind_baseline_recheck(ri, (row,), items_by_id)


def test_recheck_complete_only_when_recheck_performed() -> None:
    """``recheck_complete`` is True only for recheck-required states; it is
    never set unconditionally."""
    from mm_r4.ensemble_contracts import BaselineAssessment
    items_by_id = {item.item_id: item
                   for item in build_baseline_items()}
    output = en.WorkerAnalysisOutput(
        attempt_id="a1",
        assessments=(BaselineAssessment(
            item_id="item.b1", state="not_applicable",
            source_recheck_locator_ids=(),
            evidence_hashes=(s4.s4_sha256(b"ev"),), attempt_id="a1",
            reason_codes=("outside_assessment_scope",)),),
        findings=(), gap_candidates=())
    rows = _baseline_rows((output,), items_by_id)
    assert len(rows) == 1
    assert rows[0].state == "not_applicable"
    assert rows[0].recheck_complete is False


def test_anchor_internal_identity_drift_rejected() -> None:
    """Anchor root accepted_risk_identity_hash must equal the accepted risk
    identity instance's own hash."""
    anchor = _reanchor(build_typed_anchor(),
                       accepted_risk_identity_hash="0" * 64)
    ri = dataclasses.replace(build_runtime_input("multi_analysis"),
                             anchor=anchor)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.anchor_claim_drift"):
        build_s4_authority_state(ri)


def test_model_evidence_field_sets_cover_permit() -> None:
    """Every R4 ModelEvidence field must have an accepted permit binding;
    the two field sets must be identical today and fail closed on drift."""
    from dataclasses import fields as _fields
    upstream = {field.name for field in _fields(d10c.ModelEvidence)}
    permit = {field.name for field in _fields(s4.S4ModelEvidencePermit)}
    assert upstream == permit


# ---------------------------------------------------------------------------
# Honest accepted-anchor maximum (N=6) through builder + projection
# ---------------------------------------------------------------------------

ALL_SIX = ("a1", "a2", "m1", "m2", "g1", "g2")


def _build_n6_runtime_input() -> s4.R5S4RuntimeInput:
    """All six accepted attempt rows exercised at once (the accepted-anchor
    maximum; no N=10 authority is invented)."""
    anchor = build_typed_anchor()
    receipt = build_receipt()
    receipt_ref = s4.RECEIPT_REF_PREFIX + s4.receipt_content_hash_of(receipt)
    attempts = build_attempts(ALL_SIX)
    outputs = build_worker_outputs(ALL_SIX)
    raws = build_raw_outputs(ALL_SIX)
    baseline_items = build_baseline_items()
    digest = build_digest_context(ALL_SIX)
    refs = _derive_refs(ALL_SIX)
    inspector = c5.R5RiskInspectorProjection(
        adjudication_ref=refs["adjudication_ref"],
        analysis_attempt_refs=refs["analysis_attempt_refs"],
        authority_receipt_ref=refs["authority_receipt_ref"],
        baseline_assessment_refs=refs["baseline_assessment_refs"],
        baseline_item_refs=refs["baseline_item_refs"],
        conflict_refs=refs["conflict_refs"],
        counterevidence_refs=(),
        domain=refs["domain"], query_draft_ref=None,
        risk_ref=refs["risk_ref"], severity=refs["severity"],
        source_locator_refs=refs["source_locator_refs"],
        support_evidence_refs=(), verification_refs=refs["verification_refs"],
        worker_output_refs=())
    accepted_adj = anchor.accepted_adjudicator_binding
    adjudicator = s4.R5S4AdjudicatorInput(
        binding=AdjudicationBinding(
            binding_id=accepted_adj.binding_id,
            session_id=accepted_adj.session_id,
            model_id=accepted_adj.model_id,
            model_version=accepted_adj.model_version,
            outcome=accepted_adj.outcome,
            reviewed_artifact_refs=tuple(sorted(
                f"artifact:{aid}" for aid in ALL_SIX))),
        independent_context_hash=accepted_adj.independent_context_hash)
    return s4.R5S4RuntimeInput(
        anchor=anchor, authority_receipt=receipt,
        upstream_inspector=inspector, change_band=build_change_band(receipt_ref),
        deep_link_state=build_deep_link_state(),
        source_input=build_source_input(available=True),
        attempts=attempts, worker_outputs=outputs, raw_outputs=raws,
        baseline_items=baseline_items, digest_context=digest,
        adjudicator=adjudicator, model_evidence=None,
        query_draft=build_query_draft(),
        history_log=build_history_log("multi_analysis"),
        audience_labels=build_audience_labels())


def test_accepted_anchor_max_n6_builds() -> None:
    """All six accepted attempt rows exercise the builder + projection as one
    multi-analysis packet (the honest accepted-anchor maximum)."""
    ri = _build_n6_runtime_input()
    bs = build_s4_authority_state(ri)
    assert bs.ensemble_projection_state == "multi_analysis"
    assert len(bs.worker_views) == 6
    assert len(bs.verification_rows) == 6
    assert len(bs.conflict_rows) == 4
    packet = build_s4_authority_packet(ri)
    assert packet.ensemble_size == 6
    assert len(packet.worker_views) == 6
    assert len(packet.audience_inspector.worker_ordinal_summaries) == 6
    assert len(packet.audit_inspector.worker_audit_rows) == 6
    assert packet.audit_inspector.adjudication_audit == ("adj.record.1",)
    assert packet.packet_integrity_hash == s4.compute_packet_integrity_hash(
        s4.packet_as_mapping(packet))
    # frozen consensus phrase for the six-worker relation set.
    assert packet.audience_inspector.consensus_zh == (
        "独立分析存在风险分级不一致、结论相互矛盾、基线项目未被评估，请结合来源核实")


def _permit_model_evidence(anchor: s4.S4AcceptedAuthorityAnchor,
                           output_hash: Optional[str] = None,
                           ) -> d10c.ModelEvidence:
    """The ModelEvidence instance bound exactly to the single accepted
    permit (optionally with a replaced ``output_hash`` for the probe)."""
    permit = anchor.model_evidence_permits[0]
    return d10c.ModelEvidence(
        model_evidence_id=permit.model_evidence_id, role=permit.role,
        permitted_leaf=permit.permitted_leaf, model_id=permit.model_id,
        model_version=permit.model_version,
        evaluation_content_identity=permit.evaluation_content_identity,
        input_content_hash=permit.input_content_hash,
        source_revision_content_pairs=tuple(
            d10c.SourceRevisionPair(revision_id=p.revision_id,
                                    content_hash=p.content_hash)
            for p in permit.source_revision_content_pairs),
        source_refs=permit.source_refs,
        independent_context_hash=permit.independent_context_hash,
        ensemble_id=permit.ensemble_id, ensemble_size=permit.ensemble_size,
        member_analysis_refs=permit.member_analysis_refs,
        member_analysis_ref_set_hash=permit.member_analysis_ref_set_hash,
        output_identity=permit.output_identity,
        output_hash=output_hash or permit.output_hash,
        adjudication_state=permit.adjudication_state,
        model_binding_hash=permit.model_binding_hash)


def test_n6_carrying_a1_a2_permit_rejected() -> None:
    """Reviewer probe: the a1/a2-only permit must not project into the N=6
    ensemble; any ModelEvidence presence there fails with
    ``s4.model_evidence_not_permitted``."""
    ri = _build_n6_runtime_input()
    anchor = ri.anchor
    model_evidence = _permit_model_evidence(anchor)
    ri = dataclasses.replace(ri, model_evidence=model_evidence)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.model_evidence_not_permitted"):
        build_s4_authority_state(ri)


def test_n6_same_model_different_worker_output_hash_rejected() -> None:
    """Reviewer probe: ``output_hash`` must equal the accepted permit's
    member output exactly; a same-model different worker (m1 is model.a like
    the permitted a1, but its output hash differs) must be rejected."""
    anchor = build_typed_anchor()
    m1_row = next(r for r in anchor.attempt_authority_rows
                  if r.attempt_id == "m1")
    ri = _build_n6_runtime_input()
    model_evidence = _permit_model_evidence(
        anchor, output_hash=m1_row.parsed_output_hash)
    ri = dataclasses.replace(ri, model_evidence=model_evidence)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.model_evidence_not_permitted"):
        build_s4_authority_state(ri)


def test_n6_without_model_evidence_is_valid() -> None:
    """The N=6 accepted-anchor maximum is valid with ``model_evidence=None``
    (the single permit covers only the a1/a2 ensemble)."""
    ri = _build_n6_runtime_input()
    assert ri.model_evidence is None
    bs = build_s4_authority_state(ri)
    assert bs.model_evidence is None
    packet = build_s4_authority_packet(ri)
    assert packet.audit_inspector.model_evidence is None


def test_model_evidence_rejects_forged_active_ensemble_identity() -> None:
    """Reviewer probe: an internally consistent forged active ensemble id
    is not the ensemble identity authorized by the accepted permit."""
    ri = build_runtime_input("multi_analysis")
    forged_id = "ens.forged"
    forged_attempts = tuple(
        dataclasses.replace(attempt, ensemble_id=forged_id)
        for attempt in ri.attempts)
    forged_digest = dataclasses.replace(
        ri.digest_context, expected_ensemble_identity=forged_id)
    forged = dataclasses.replace(
        ri, attempts=forged_attempts, digest_context=forged_digest)
    with pytest.raises(s4.S4RuntimeContractError,
                       match="s4.model_evidence_not_permitted"):
        build_s4_authority_state(forged)


def test_single_mutual_graded_carrying_permit_rejected() -> None:
    """The a1/a2-only permit must be absent from every other ensemble: the
    single (a1-only), mutual (m1/m2) and graded (g1/g2) variants reject a
    projected ModelEvidence with ``s4.model_evidence_not_permitted``."""
    for state in ("single_analysis", "mutual_negation", "graded_conflict"):
        ri = build_runtime_input(state)
        model_evidence = _permit_model_evidence(ri.anchor)
        ri = dataclasses.replace(ri, model_evidence=model_evidence)
        with pytest.raises(s4.S4RuntimeContractError,
                           match="s4.model_evidence_not_permitted"):
            build_s4_authority_state(ri)
