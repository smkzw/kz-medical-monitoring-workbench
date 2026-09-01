"""R4-D10 emitted-object verifier probes (worker_03).

Probes the EMITTED projection objects (Query draft, R2 handoff, project
projection and the authoritative result binding) rather than the evaluator
internals:

* every emitted Query draft / R2 handoff / project projection across all 312
  cases equals its authoritative rebuild and passes its closed validator;
* coherent re-signing: a tampered emitted object whose own public hashes/ids
  (query_draft_id + content_hash, handoff_id + idempotency_key, projection
  content hash / id, count-surface ref) are recomputed from the tampered
  object's own fields is STILL rejected by the authoritative rebuild.  The
  rejection is a semantic/tamper failure, never a stale-local-hash failure;
* the tamper probes recompute ordinary public hashes/ids only -- they never
  re-implement the validator's check logic (the validators are invoked as
  black boxes); case ids are test-side fixture selection only.

All data is synthetic and offline; the catalog/oracle/authority are read-only.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, List, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as adapter  # noqa: E402
from mm_r4 import d10_evaluator as evaluator  # noqa: E402
from mm_r4.d10_contracts import (  # noqa: E402
    D10_UNIT_ALGORITHM_VERSION,
    d10_content_hash,
)
from mm_r4.d10_projection import (  # noqa: E402
    D10AudiencePart,
    D10ProjectionError,
    build_d10_query_draft,
    build_d10_r2_handoff,
    project_d10_run,
    validate_d10_project_projection,
    validate_d10_query_draft,
    validate_d10_r2_handoff,
)


def _authority_for(cid: str) -> Any:
    authority = adapter.load_authority()
    entry = next(e for e in authority["entries"] if e["case_id"] == cid)
    return adapter.build_authority(entry)


def _evaluate(cid: str) -> Tuple[Any, Any]:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    case = next(c for c in catalog["cases"] if c["case_id"] == cid)
    typed = adapter.build_typed_input(case["typed_input"])
    return typed, evaluator.evaluate(typed, _authority_for(cid))


def _find_query_case() -> str:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    for case in catalog["cases"]:
        typed, result = _evaluate(case["case_id"])
        if build_d10_query_draft(typed, result) is not None:
            return case["case_id"]
    raise AssertionError("no catalog case emits a Query draft")


# ---------------------------------------------------------------------------
# Coherent re-sign helpers: recompute an emitted object's OWN public
# hashes/ids from the object's canonical fields (the production canonical
# recipes used by the builders), so a tampered object is self-consistently
# signed.  The validators are still invoked as black boxes.
# ---------------------------------------------------------------------------


def _parts_hash(parts: Tuple[D10AudiencePart, ...]) -> List[dict]:
    return [{"part_kind": part.part_kind, "text_zh": part.text_zh}
            for part in parts]


def _resign_query(draft: Any, **overrides: Any) -> Any:
    """Re-sign the emitted Query draft's own public ids after a tamper."""
    d = replace(draft, **overrides)
    query_draft_id = d10_content_hash({
        "unit_stable_core": d.unit_stable_core,
        "evaluation_content_identity": d.evaluation_content_identity,
        "member_refs": list(d.member_refs),
        "basis_parts": _parts_hash(d.basis_parts),
        "finding_parts": _parts_hash(d.finding_parts),
        "action_parts": _parts_hash(d.action_parts),
        "basis_sentence": d.basis_sentence,
        "finding_sentence": d.finding_sentence,
        "action_sentence": d.action_sentence,
        "scope_binding_id": d.scope_binding_id,
        "redundancy_decision_hash": d.redundancy_decision_hash,
        "pd_wording_state": d.pd_wording_state,
        "basis_refs": list(d.basis_refs),
        "source_revision_refs": list(d.source_revision_refs),
    })
    content_core = {
        "query_draft_id": query_draft_id,
        "unit_stable_core": d.unit_stable_core,
        "evaluation_content_identity": d.evaluation_content_identity,
        "query_owner": d.query_owner,
        "basis_parts": _parts_hash(d.basis_parts),
        "finding_parts": _parts_hash(d.finding_parts),
        "action_parts": _parts_hash(d.action_parts),
        "basis_sentence": d.basis_sentence,
        "finding_sentence": d.finding_sentence,
        "action_sentence": d.action_sentence,
        "member_refs": list(d.member_refs),
        "evidence_refs": list(d.evidence_refs),
        "source_locator_ids": list(d.source_locator_ids),
        "scope_binding_id": d.scope_binding_id,
        "redundancy_decision": d.redundancy_decision,
        "redundancy_decision_hash": d.redundancy_decision_hash,
        "unit_member_set_hash": d.unit_member_set_hash,
        "coverage_proof_hash": d.coverage_proof_hash,
        "covered_member_refs": list(d.covered_member_refs),
        "uncovered_member_refs": list(d.uncovered_member_refs),
        "max_query_member_fanout": d.max_query_member_fanout,
        "pd_wording_state": d.pd_wording_state,
        "basis_refs": list(d.basis_refs),
        "source_revision_refs": list(d.source_revision_refs),
    }
    return replace(d, query_draft_id=query_draft_id,
                   content_hash=d10_content_hash(content_core))


def _resign_handoff(handoff: Any, **overrides: Any) -> Any:
    """Re-sign the emitted R2 handoff's own public ids after a tamper."""
    h = replace(handoff, **overrides)
    handoff_id = d10_content_hash({
        "public_d10_risk_identity": h.public_d10_risk_identity,
        "evaluation_content_identity": h.current_evaluation_content_ref,
        "action": h.action,
        "lineage_relation": h.lineage_relation,
        "prior_risk_instance_ref": h.prior_risk_instance_ref,
        "change_decision_hash": h.change_decision_ref,
        "completeness_decision_hash": h.completeness_decision_ref,
    })
    return replace(h, handoff_id=handoff_id, idempotency_key=handoff_id)


def _projection_core_hash(typed: Any, bundle: Any,
                          count_surface_ref: str) -> str:
    """Reproduce the project-projection PUBLIC content-hash recipe (contract
    section 12) from the emitted bundle's public leaf fields and one
    (possibly tampered) count-surface ref.  This is the production canonical
    recipe -- not the validator's decision logic -- used to build a coherent
    adversarial re-signed projection."""
    coverage_refs = tuple(sorted(set(
        locator for c in typed.coverage
        for locator in c.coverage_locator_ids)))
    projection_core = {
        "change_kind": bundle.change_section.change_kind,
        "center_site_refs": [row.site_ref for row in bundle.center_distribution],
        "trend_surface_present": bundle.trend_surface.trend_surface_present,
        "warning_refs": [w.reason_code for w in bundle.warning_markers],
        "risk_marker_ref": (bundle.risk_marker.marker_id
                            if bundle.risk_marker else None),
        "hotspot_refs": [h.projection_id for h in bundle.hotspots],
        "count_surface_ref": count_surface_ref,
        "coverage_refs": list(coverage_refs),
        "deep_link_refs": [link.link_id for link in bundle.deep_links],
        "query_draft_id": (bundle.query_draft.query_draft_id
                           if bundle.query_draft is not None else None),
        "r2_handoff_id": (bundle.r2_handoff.handoff_id
                          if bundle.r2_handoff is not None else None),
        "audience_text_ref": typed.audience_text.audience_contract_id,
        "algorithm_version": D10_UNIT_ALGORITHM_VERSION,
    }
    return d10_content_hash(projection_core)


def _resign_projection(projection: Any, bundle: Any, typed: Any,
                       count_surface_ref: str) -> Any:
    """Coherently re-sign a tampered project projection: recompute the
    complete ``projection_content_hash`` from the exact public projection
    core (including the mutated count-surface ref and every other core
    field) and then ``projection_id`` from the projection version ref plus
    the new content hash -- so the object's own local hash/id checks are
    internally consistent."""
    projection_content_hash = _projection_core_hash(
        typed, bundle, count_surface_ref)
    projection_id = d10_content_hash({
        "projection_version_id": bundle.version.projection_version_id,
        "projection_content_hash": projection_content_hash,
    })
    return replace(projection, count_surface_ref=count_surface_ref,
                   projection_content_hash=projection_content_hash,
                   projection_id=projection_id)


class TestEmittedQueryDraftAuthoritative(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        cls.cases = []
        for case in cls.catalog["cases"]:
            typed, result = _evaluate(case["case_id"])
            draft = build_d10_query_draft(typed, result)
            if draft is None:
                if result.unit is not None \
                        and result.unit.query_count == 1:
                    cls.cases.append(
                        (case["case_id"], typed, result, None))
                continue
            cls.cases.append((case["case_id"], typed, result, draft))

    def test_every_emitted_draft_passes_authoritative_rebuild(self) -> None:
        """Every EMITTED draft validates.  Some admitted positive units with
        ``query_count == 1`` are suppressed by the projection when a hidden
        member/site intersects the audience boundary (the evaluator grant is
        kept, the draft is deliberately suppressed) -- those carry ``None``
        here and assert zero leakage in the closure suite."""
        emitted = [c for c in self.cases if c[3] is not None]
        self.assertGreaterEqual(len(emitted), 100)
        for cid, typed, result, draft in emitted:
            assert draft is not None
            validation = validate_d10_query_draft(draft, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")

    def test_coherently_resigned_finding_rejected_not_stale_hash(self) -> None:
        for cid, typed, result, draft in self.cases[:12]:
            if draft is None:
                continue
            new_finding_parts = tuple(
                D10AudiencePart(part.part_kind,
                                part.text_zh.replace("本项目", "项目", 1))
                for part in draft.finding_parts)
            new_finding_sentence = "".join(
                p.text_zh for p in new_finding_parts)
            if new_finding_sentence == draft.finding_sentence:
                continue
            tampered = _resign_query(
                draft, finding_parts=new_finding_parts,
                finding_sentence=new_finding_sentence)
            validation = validate_d10_query_draft(tampered, typed, result)
            self.assertFalse(validation["valid"], cid)
            self.assertIn(
                "query_draft_not_exact_authoritative_projection",
                validation["reasons"], cid)
            self.assertNotIn("content_hash_stale",
                             validation["reasons"], cid)

    def test_coherently_resigned_incomplete_member_set_rejected(self) -> None:
        for cid, typed, result, draft in self.cases[:12]:
            if draft is None or len(draft.member_refs) < 2:
                continue
            removed = draft.member_refs[1:]
            tampered = _resign_query(draft, member_refs=removed,
                                     member_count=len(removed))
            validation = validate_d10_query_draft(tampered, typed, result)
            self.assertFalse(validation["valid"], cid)
            self.assertIn(
                "member_set_not_complete_uncovered_projectable",
                validation["reasons"], cid)
            self.assertNotIn("content_hash_stale",
                             validation["reasons"], cid)


class TestEmittedR2HandoffAuthoritative(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        cls.cases = []
        for case in cls.catalog["cases"]:
            typed, result = _evaluate(case["case_id"])
            handoff = build_d10_r2_handoff(typed, result)
            if handoff is None:
                continue
            cls.cases.append((case["case_id"], typed, result, handoff))

    def test_every_emitted_handoff_passes_authoritative_rebuild(self) -> None:
        self.assertGreaterEqual(len(self.cases), 113)
        for cid, typed, result, handoff in self.cases:
            validation = validate_d10_r2_handoff(handoff, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")

    def test_re_signed_action_change_rejected_on_binding_not_stale(self) -> None:
        """Re-signing a tampered (but closed-legal) action keeps
        handoff_id/idempotency_key internally consistent with the
        authoritative identity pins; the validator must reject for the wrong
        action binding, not a stale hash."""
        legal_actions = ("create", "continue", "update", "propose_close",
                         "reopen", "supersede")
        probed = 0
        for cid, typed, result, handoff in self.cases:
            target = next((a for a in legal_actions if a != handoff.action),
                          None)
            if target is None:
                continue
            tampered = _resign_handoff(handoff, action=target)
            validation = validate_d10_r2_handoff(tampered, typed, result)
            self.assertFalse(validation["valid"], cid)
            self.assertTrue(any("action_mismatch" in reason
                                for reason in validation["reasons"]), cid)
            self.assertNotIn("handoff_id_stale",
                             validation["reasons"], cid)
            probed += 1
            if probed >= 8:
                break
        self.assertGreaterEqual(probed, 8)

    def test_re_signed_prior_change_rejected_on_prior_binding(self) -> None:
        cid, typed, result, handoff = self.cases[0]
        tampered = _resign_handoff(
            handoff, prior_risk_instance_ref="SYN-D10-R2-PRIOR-FORGED")
        validation = validate_d10_r2_handoff(tampered, typed, result)
        self.assertFalse(validation["valid"], cid)
        self.assertTrue(any("prior_ref_mismatch" in reason
                            for reason in validation["reasons"]), cid)
        self.assertNotIn("handoff_id_stale",
                         validation["reasons"], cid)


class TestEmittedProjectProjectionAuthoritative(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        cls.cases = []
        for case in cls.catalog["cases"]:
            typed, result = _evaluate(case["case_id"])
            cls.cases.append((case["case_id"], typed, result,
                              project_d10_run(typed, result)))

    def test_every_emitted_projection_passes_authoritative_rebuild(self) -> None:
        for cid, typed, result, bundle in self.cases:
            validation = validate_d10_project_projection(
                bundle.project_projection, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")

    def test_coherently_signed_display_leaf_tamper_rejected(self) -> None:
        """Tampering an audience narrative leaf while keeping the stored
        projection id/content hash at their authoritative values yields a
        self-consistent object whose whole-object equality to the rebuild
        is the only reason for rejection."""
        for cid, typed, result, bundle in self.cases:
            projection = bundle.project_projection
            tampered = replace(
                projection,
                change_section=replace(
                    projection.change_section,
                    narrative_zh="伪造的变化叙述"))
            self.assertEqual(tampered.projection_content_hash,
                             projection.projection_content_hash, cid)
            self.assertEqual(tampered.projection_id,
                             projection.projection_id, cid)
            validation = validate_d10_project_projection(
                tampered, typed, result)
            self.assertFalse(validation["valid"], cid)
            self.assertIn(
                "project_projection_not_exact_authoritative_rebuild",
                validation["reasons"], cid)

    def test_re_signed_count_surface_ref_tamper_rejected(self) -> None:
        """A count-surface tamper is coherently FULL re-signed: both the
        count-surface ref AND the complete projection_content_hash (from the
        exact public projection core, including the mutated ref and every
        other core field) AND projection_id are recomputed with the
        production public recipes, so all local hash/id consistency checks
        are satisfied.  The authoritative rebuild must still reject -- the
        count leaf no longer matches -- on the whole-object rebuild reason,
        never on a stale content hash or stale id."""
        cid = "D10-CASE-218"
        typed, result = _evaluate(cid)
        bundle = project_d10_run(typed, result)
        projection = bundle.project_projection

        # The replica reproduces the authoritative content hash exactly when
        # given the authoritative count-surface ref: proof that the public
        # core recipe below is faithful, not a guess.
        self.assertEqual(
            _projection_core_hash(typed, bundle,
                                  projection.count_surface_ref),
            projection.projection_content_hash)

        counts = bundle.counts
        tampered_counts = replace(counts, individual_risk_count=999)
        tampered_count_surface_ref = d10_content_hash({
            "evaluation_window_instance_ref":
                tampered_counts.evaluation_window_instance_ref,
            "individual_risk_count": tampered_counts.individual_risk_count,
            "affected_subject_count": tampered_counts.affected_subject_count,
            "event_or_outcome_count": tampered_counts.event_or_outcome_count,
            "center_pattern_count": tampered_counts.center_pattern_count,
            "affected_site_count": tampered_counts.affected_site_count,
            "project_signal_count": tampered_counts.project_signal_count,
            "clue_count": tampered_counts.clue_count,
            "query_count": tampered_counts.query_count,
            "hidden_member_count": tampered_counts.hidden_member_count,
            "hidden_site_count": tampered_counts.hidden_site_count,
        })
        tampered = _resign_projection(
            projection, bundle, typed, tampered_count_surface_ref)

        # the mutation is identity-bearing: every public hash/id differs
        self.assertNotEqual(tampered_count_surface_ref,
                            projection.count_surface_ref, cid)
        self.assertNotEqual(tampered.projection_content_hash,
                            projection.projection_content_hash, cid)
        self.assertNotEqual(tampered.projection_id,
                            projection.projection_id, cid)
        # ordinary LOCAL hash/id consistency checks are satisfied: the
        # object's own content hash and id match their public recipes
        self.assertEqual(
            _projection_core_hash(typed, bundle,
                                  tampered.count_surface_ref),
            tampered.projection_content_hash, cid)
        self.assertEqual(
            d10_content_hash({
                "projection_version_id": bundle.version.projection_version_id,
                "projection_content_hash": tampered.projection_content_hash,
            }),
            tampered.projection_id, cid)

        validation = validate_d10_project_projection(
            tampered, typed, result)
        self.assertFalse(validation["valid"], cid)
        self.assertEqual(
            validation["reasons"],
            ["project_projection_not_exact_authoritative_rebuild"], cid)


class TestAuthoritativeResultBindingProbe(unittest.TestCase):
    def test_projection_binds_to_authoritative_result_not_resigned(self) -> None:
        """Feeding a result whose unit belongs to a DIFFERENT signal kind
        than the typed bundle fails closed at build time -- the projection
        never re-runs the evaluator and never accepts a mismatched result."""
        cid = _find_query_case()
        typed, result = _evaluate(cid)
        self.assertIsNotNone(result.unit, cid)
        wanted_kind = typed.signal_definition.signal_kind
        catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        foreign_cid = None
        for case in catalog["cases"]:
            if case["case_id"] == cid:
                continue
            _f_typed, f_result = _evaluate(case["case_id"])
            if f_result.unit is not None \
                    and f_result.unit.signal_kind != wanted_kind:
                foreign_cid = case["case_id"]
                break
        self.assertIsNotNone(foreign_cid, "no different-kind result found")
        _foreign_typed, foreign_result = _evaluate(foreign_cid)
        with self.assertRaises(D10ProjectionError):
            project_d10_run(typed, foreign_result)
        with self.assertRaises(D10ProjectionError):
            build_d10_query_draft(typed, foreign_result)
        with self.assertRaises(D10ProjectionError):
            build_d10_r2_handoff(typed, foreign_result)


if __name__ == "__main__":
    unittest.main()
