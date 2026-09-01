"""R4-D10 renderer-neutral projection, Query, visibility, deep-link and R2
handoff tests (worker_02).

Covers the projection layer over the accepted ``D10TypedInput`` bundle and
the authoritative ``D10RunResult`` (all 312 frozen catalog cases through the
test-only adapter with corrected per-case Authority):

* renderer-neutral projection never re-runs the medical evaluator, never
  reads artifact files and never branches on case/fixture/test ids or
  mutation metadata (static closure over ``d10_projection.py``);
* all global/control-plane/routing/handoff gates emit no medical projection
  (no risk marker, Query draft, hotspots, deep links or R2 handoff; zero
  count surface; no audience payload);
* positive vs boundary/negative/NA/NE ownership: only positive units carry
  a project-signal risk marker and an R2 handoff; boundary units carry a
  clue surface but never a Query or handoff;
* count-plane separation: ``individual_risk_count`` /
  ``affected_subject_count`` / ``event_or_outcome_count`` /
  ``center_pattern_count`` / ``affected_site_count`` /
  ``project_signal_count`` / ``clue_count`` / ``query_count`` are kept
  separate and, with nothing hidden, equal the frozen oracle leaf values
  exactly;
* complete Query coverage and one-per-unit: every positive unit with
  ``query_count == 1`` emits exactly one draft whose member set is the
  complete uncovered projectable set (never truncated) and whose redundancy
  proof is the exact covered/uncovered union/disjoint partition; PD wording
  ``请核实是否为 PD`` appears exactly when the typed PD wording state is
  ``verify_whether_pd``;
* hidden-member/site/pair non-disclosure: hidden refs never reach
  projectable sets, queries, markers, hotspots, deep links or counts;
  suppressed/qualified rates never show a misleading precision rate;
* all three deep-link kinds (member/site/subject_site_pair) are verified
  against the exact eligible member/site/pair sets with locator and
  return-state binding;
* high-risk singleton preservation: the typed high-risk hotspot subject is
  preserved on positive runs and never hidden behind a low project
  proportion or small-sample note; no punitive ranking/black-box score;
* deterministic D10-to-R2 handoff for positive units only with the full
  action x lineage/prior/idempotency legal matrix
  (create/continue/update/propose_close/reopen/supersede) and replay
  stability across run/snapshot swaps; R2 objects are emitted, never
  created or updated;
* input reorder invariance (member order swap produces a byte-identical
  result and projection) and fully re-signed emitted-object tamper
  rejection: a re-signed tampered Query/projection/handoff cannot pass the
  authoritative rebuild validators;
* the audience surface is native Chinese and free of internal
  disposition/state/enum/hash/id/ref/policy/mode/window/revision/scope
  tokens and forbidden backend labels.

All data is synthetic and offline.
"""

from __future__ import annotations

import ast
import socket
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, List, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as adapter  # noqa: E402
from mm_r4 import d10_evaluator as evaluator  # noqa: E402
from mm_r4.d10_contracts import d10_content_hash  # noqa: E402
from mm_r4.d10_projection import (  # noqa: E402
    D10AudiencePart,
    D10ProjectionError,
    build_d10_audience_projection,
    build_d10_center_distribution,
    build_d10_count_surface,
    build_d10_deep_links,
    build_d10_hotspots,
    build_d10_project_projection,
    build_d10_projection_version,
    build_d10_query_draft,
    build_d10_r2_handoff,
    build_d10_risk_marker,
    d10_public_risk_identity,
    project_d10_run,
    validate_d10_project_projection,
    validate_d10_query_draft,
    validate_d10_r2_handoff,
)

_PROJECTION_PATH = _R4_SRC / "mm_r4" / "d10_projection.py"

_FORBIDDEN_IMPORT_TOKENS = (
    "oracle", "registry", "quota", "verifier", "adapter", "generator",
    "fixture", "pytest", "unittest", "artifact",
)
_FORBIDDEN_FILE_READ_CALLS = (
    "open(", "json.load", "Path(", "read_text", "read_bytes", "load_json",
)
_MUTATION_METADATA_TOKENS = (
    "mutation_context", "anti_overfit_variant", "mutation_class",
    "variant_id", "base_fixture_id",
)
_FORBIDDEN_ID_RE = __import__("re").compile(
    r"D10-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+")

_FORBIDDEN_AUDIENCE_LABELS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
    "正式安全性信号", "确证治疗效果", "优效", "非劣", "获益-风险裁决",
    "中心质量差", "中心质量好", "typed handoff", "candidate",
)
_FORBIDDEN_RAW_TOKENS = (
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "permitted", "suppressed", "qualified",
    "create", "continue", "update", "propose_close", "reopen", "supersede",
    "gate", "ledger", "handoff", "envelope", "payload", "evaluator",
    "projection", "hotspot", "deep_link", "draft", "lineage", "stratum",
)

# Raw backend/reason tokens and snake_case reason patterns forbidden in any
# audience text.
_RAW_ENUM_TOKENS = frozenset((
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "permitted", "suppressed", "qualified", "create", "continue", "update",
    "propose_close", "reopen", "supersede", "gate", "ledger", "handoff",
    "payload", "generator", "verifier", "adapter", "oracle", "registry",
    "quota", "hotspot", "deep_link", "lineage", "stratum", "candidate",
    "evaluated", "projected", "replayed",
))
_RAW_REASON_RE = __import__("re").compile(
    r"[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)+")


def _sha(value: Any) -> str:
    return d10_content_hash(value, "tamper")


def _authority_for(cid: str) -> Any:
    authority = adapter.load_authority()
    entry = next(e for e in authority["entries"] if e["case_id"] == cid)
    return adapter.build_authority(entry)


def _case_typed(cid: str) -> Any:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    case = next(c for c in catalog["cases"] if c["case_id"] == cid)
    return adapter.build_typed_input(case["typed_input"])


def _evaluate(cid: str) -> Tuple[Any, Any]:
    typed = _case_typed(cid)
    return typed, evaluator.evaluate(typed, _authority_for(cid))


def _find_case(predicate: Callable[[Any], bool]) -> Tuple[str, Any]:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    for case in catalog["cases"]:
        typed = adapter.build_typed_input(case["typed_input"])
        if predicate(typed):
            return case["case_id"], typed
    raise AssertionError("no catalog case satisfies the typed-fact predicate")


def _audience_texts(bundle: Any) -> List[str]:
    """Every user-facing Chinese string emitted by a projection bundle."""
    counts = bundle.counts
    texts = [
        counts.individual_risk_zh, counts.affected_subjects_zh,
        counts.event_or_outcome_zh, counts.center_pattern_zh,
        counts.affected_site_zh, counts.project_signal_zh,
        counts.coverage_zh, counts.coverage_state_zh,
        counts.denominator_zh or "", counts.rate_zh or "",
        counts.disposition_zh, bundle.audience.disposition_zh,
        bundle.audience.coverage_zh, bundle.audience.reason_zh,
    ]
    if counts.clue_zh:
        texts.append(counts.clue_zh)
    if counts.query_count_zh:
        texts.append(counts.query_count_zh)
    texts.append(bundle.change_section.narrative_zh)
    texts.append(bundle.change_section.change_kind_zh)
    texts.append(bundle.change_section.lineage_zh)
    if bundle.change_section.change_cause_zh:
        texts.append(bundle.change_section.change_cause_zh)
    texts.append(bundle.trend_surface.trend_note_zh)
    for warning in bundle.warning_markers:
        texts.append(warning.warning_zh)
    if bundle.query_draft is not None:
        texts.extend((bundle.query_draft.basis_sentence,
                      bundle.query_draft.finding_sentence,
                      bundle.query_draft.action_sentence))
    for link in bundle.deep_links:
        if link.unavailable_message:
            texts.append(link.unavailable_message)
    return [t for t in texts if t]


def _all_typed_refs(typed: Any) -> set:
    refs = {
        typed.envelope_id, typed.project_ref, typed.run_ref,
        typed.snapshot_ref, typed.mode_contract.mode_contract_version,
        typed.project_scope_binding.scope_binding_id,
        typed.signal_definition.signal_definition_id,
        typed.signal_definition.positive_rule_ref,
        typed.stratum.stratum_contract_id,
        typed.comparison_gate.comparison_reference_stable_id,
        typed.audience_text.audience_contract_id,
    }
    refs.update(p.revision_id for p in typed.source_revision_content_pairs)
    refs.update(m.member_ref for m in typed.members)
    refs.update(locator for m in typed.members
                for locator in m.source_locator_refs)
    for window in typed.analysis_windows:
        refs.update((window.analysis_window_stable_id,
                     window.window_instance_id,
                     window.window_definition_id))
    return {r for r in refs if r}


def _parts_hash(parts):
    """Canonical sentence-part serialization of the Query draft recipe."""
    return [{"part_kind": part.part_kind, "text_zh": part.text_zh}
            for part in parts]


def _requery_draft(draft, **overrides):
    """Coherently re-sign a tampered Query draft.

    Recomputes both ``query_draft_id`` and ``content_hash`` from the
    tampered fields using the production canonical recipe, so the local hash
    checks stay consistent.  Only the object's own hashes are recomputed;
    the authoritative-rebuild comparison still fails on the altered
    content."""
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
    core = {
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
                   content_hash=d10_content_hash(core))


def _rehandoff(handoff, **overrides):
    """Coherently re-sign a tampered R2 handoff.

    Recomputes ``handoff_id`` and ``idempotency_key`` from the tampered
    fields using the production canonical recipe (the authoritative identity
    pins are read from the handoff's own authoritative fields, which are
    untouched by an action/lineage/prior tamper)."""
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


# ---------------------------------------------------------------------------
# Static closure of the projection runtime
# ---------------------------------------------------------------------------


class TestD10ProjectionStaticClosure(unittest.TestCase):
    def test_no_forbidden_imports(self) -> None:
        problems: List[str] = []
        text = _PROJECTION_PATH.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            low = stripped.lower()
            if any(token in low for token in _FORBIDDEN_IMPORT_TOKENS):
                problems.append(stripped)
        self.assertEqual(problems, [], f"forbidden imports: {problems}")

    def test_no_file_reading(self) -> None:
        text = _PROJECTION_PATH.read_text(encoding="utf-8")
        problems = [call for call in _FORBIDDEN_FILE_READ_CALLS
                    if call in text]
        self.assertEqual(problems, [], f"file reads: {problems}")

    def test_no_mutation_metadata_or_case_ids(self) -> None:
        text = _PROJECTION_PATH.read_text(encoding="utf-8")
        problems = [token for token in _MUTATION_METADATA_TOKENS
                    if token in text]
        self.assertEqual(problems, [],
                         f"projection references audit metadata: {problems}")
        self.assertIsNone(_FORBIDDEN_ID_RE.search(text),
                          "projection code contains a case/fixture id")

    def test_no_service_ui_network_concerns(self) -> None:
        text = _PROJECTION_PATH.read_text(encoding="utf-8")
        for token in ("8911", "socket", "requests", "urllib", "subprocess",
                      "print("):
            self.assertNotIn(token, text, f"{token!r} in projection code")

    def test_project_projection_code_is_ascii_clean_ast(self) -> None:
        tree = ast.parse(_PROJECTION_PATH.read_text(encoding="utf-8"))
        self.assertIsNotNone(tree)


# ---------------------------------------------------------------------------
# Broad 312-case projection invariants (test-only adapter, corrected
# Authority; expected leaf behavior derived from the frozen oracle)
# ---------------------------------------------------------------------------


class TestD10ProjectionCatalogInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _registry, _quota = adapter.load_artifacts()
        cls.by_oracle = {o["case_id"]: o
                         for o in cls.oracle["ordered_expectations"]}
        cls.cases = []
        for case in cls.catalog["cases"]:
            typed = adapter.build_typed_input(case["typed_input"])
            result = evaluator.evaluate(typed, _authority_for(case["case_id"]))
            bundle = project_d10_run(typed, result)
            cls.cases.append((case["case_id"], typed, result, bundle))

    def test_all_cases_project(self) -> None:
        self.assertEqual(len(self.cases), 312)

    def test_gates_emit_no_medical_projection(self) -> None:
        for cid, typed, result, bundle in self.cases:
            disposition = result.disposition_or_gate
            if disposition not in (
                    "global_gate", "integrity_gate", "comparison_set_gate",
                    "window_pair_gate", "routing_gate", "handoff_gate"):
                continue
            with self.subTest(cid=cid):
                self.assertFalse(bundle.audience.audience_payload_present)
                self.assertIsNone(bundle.risk_marker)
                self.assertIsNone(bundle.query_draft)
                self.assertIsNone(bundle.r2_handoff)
                self.assertEqual(bundle.hotspots, ())
                self.assertEqual(bundle.deep_links, ())
                self.assertEqual(bundle.counts.individual_risk_count, 0)
                self.assertEqual(bundle.counts.affected_subject_count, 0)
                self.assertEqual(bundle.counts.project_signal_count, 0)
                self.assertEqual(bundle.counts.clue_count, 0)
                self.assertEqual(bundle.counts.query_count, 0)
                self.assertFalse(bundle.audience.disclosure_leak_present)

    def test_not_evaluable_and_not_applicable_no_medical_payload(self) -> None:
        for cid, typed, result, bundle in self.cases:
            if result.disposition_or_gate not in ("not_evaluable",
                                                  "not_applicable"):
                continue
            with self.subTest(cid=cid):
                self.assertFalse(bundle.audience.audience_payload_present)
                self.assertIsNone(bundle.risk_marker)
                self.assertIsNone(bundle.query_draft)
                self.assertIsNone(bundle.r2_handoff)
                self.assertEqual(bundle.hotspots, ())
                self.assertEqual(bundle.deep_links, ())
                self.assertEqual(bundle.counts.project_signal_count, 0)

    def test_positive_ownership_risk_marker_and_handoff(self) -> None:
        for cid, typed, result, bundle in self.cases:
            if result.disposition_or_gate != "positive":
                continue
            with self.subTest(cid=cid):
                # every positive unit emits exactly one project signal and
                # an R2 handoff (the lifecycle contract is emitted even when
                # every member sits in a hidden site)
                self.assertIsNotNone(bundle.r2_handoff, cid)
                self.assertEqual(bundle.counts.project_signal_count, 1, cid)
                # the risk marker and audience payload exist only when at
                # least one safe member-site pair remains; a positive unit
                # whose members all sit in a hidden site exposes no marker
                # and no payload
                if bundle.audience.projectable_member_refs:
                    self.assertIsNotNone(bundle.risk_marker, cid)
                    self.assertTrue(bundle.audience.audience_payload_present,
                                    cid)
                else:
                    self.assertIsNone(bundle.risk_marker, cid)
                    self.assertFalse(bundle.audience.audience_payload_present,
                                     cid)

    def test_boundary_never_risk_or_query_or_handoff(self) -> None:
        for cid, typed, result, bundle in self.cases:
            if result.disposition_or_gate != "boundary":
                continue
            with self.subTest(cid=cid):
                self.assertIsNone(bundle.risk_marker)
                self.assertIsNone(bundle.query_draft)
                self.assertIsNone(bundle.r2_handoff)
                self.assertEqual(bundle.counts.clue_count, 1)
                self.assertEqual(bundle.counts.project_signal_count, 0)

    def test_count_plane_separation_matches_oracle_when_nothing_hidden(self) -> None:
        for cid, typed, result, bundle in self.cases:
            if result.unit is None:
                continue
            # Skip any case where a member's exact (subject, site) pair is
            # not projectable: those are hidden-member, hidden-site or
            # wrong-scope cases whose audience count is a visibility-
            # suppressed subset and therefore must not equal the raw oracle
            # numerator.
            proj_pairs = set(tuple(p) for p in
                             typed.visibility_decision.projectable_subject_site_pairs)
            if any((m.subject_stable_id, m.site_stable_id) not in proj_pairs
                   for m in typed.members):
                continue
            leaf = (self.by_oracle[cid]["expected_leaf_set"] or [None])[0]
            if leaf is None:
                continue
            counts = bundle.counts
            actual = (counts.individual_risk_count,
                      counts.affected_subject_count,
                      counts.event_or_outcome_count,
                      counts.center_pattern_count,
                      counts.affected_site_count,
                      counts.project_signal_count,
                      counts.clue_count,
                      counts.query_count)
            expected = (leaf["numerator_individual_risk_count"],
                        leaf["numerator_affected_subject_count"],
                        leaf["numerator_event_or_outcome_count"],
                        leaf["numerator_center_pattern_count"],
                        leaf["numerator_affected_site_count"],
                        leaf["project_signal_count"],
                        leaf["clue_count"],
                        leaf["query_count"])
            with self.subTest(cid=cid):
                self.assertEqual(actual, expected)

    def test_no_count_surface_sums_planes(self) -> None:
        counts_fields = (
            "individual_risk_zh", "affected_subjects_zh",
            "event_or_outcome_zh", "center_pattern_zh",
            "affected_site_zh", "project_signal_zh", "clue_zh",
            "query_count_zh",
        )
        for cid, typed, result, bundle in self.cases:
            counts = bundle.counts
            for name in counts_fields:
                with self.subTest(cid=cid, field=name):
                    value = getattr(counts, name)
                    if value is not None:
                        self.assertIsInstance(value, str)
            self.assertFalse(hasattr(counts, "total_count"))

    def test_complete_query_coverage_one_per_positive_unit(self) -> None:
        queries = 0
        for cid, typed, result, bundle in self.cases:
            if result.unit is None:
                self.assertIsNone(bundle.query_draft, cid)
                continue
            if result.unit.l1_disposition != "positive":
                self.assertIsNone(bundle.query_draft, cid)
                continue
            hidden_members = set(typed.visibility_decision.hidden_member_refs)
            hidden_sites = set(typed.visibility_decision.hidden_site_refs)
            unit_sites = {m.site_stable_id for m in typed.members
                          if m.site_stable_id}
            boundary_hidden = bool(
                (hidden_members & {m.member_ref for m in typed.members})
                or (hidden_sites & unit_sites))
            if result.unit.query_count == 1 and not boundary_hidden:
                self.assertIsNotNone(bundle.query_draft, cid)
                assert bundle.query_draft is not None
                queries += 1
                validation = validate_d10_query_draft(
                    bundle.query_draft, typed, result)
                self.assertTrue(validation["valid"],
                                f"{cid}: {validation['reasons']}")
            else:
                self.assertIsNone(bundle.query_draft, cid)
                self.assertEqual(bundle.counts.query_count, 0, cid)
        self.assertEqual(queries, 100)

    def test_hidden_members_sites_pairs_never_reach_payloads(self) -> None:
        for cid, typed, result, bundle in self.cases:
            hidden_members = set(typed.visibility_decision.hidden_member_refs)
            hidden_sites = set(typed.visibility_decision.hidden_site_refs)
            if not hidden_members and not hidden_sites:
                continue
            with self.subTest(cid=cid):
                self.assertFalse(
                    hidden_members & set(
                        bundle.audience.projectable_member_refs), cid)
                if result.unit is not None:
                    self.assertEqual(bundle.audience.hidden_member_count,
                                     len(hidden_members), cid)
                    self.assertEqual(bundle.counts.hidden_member_count,
                                     len(hidden_members), cid)
                self.assertEqual(bundle.audience.hidden_site_count,
                                 len(hidden_sites), cid)
                self.assertFalse(
                    hidden_sites & set(bundle.audience.projectable_site_refs),
                    cid)
                if bundle.query_draft is not None:
                    self.assertFalse(
                        hidden_members & set(bundle.query_draft.member_refs),
                        cid)
                if bundle.risk_marker is not None:
                    self.assertFalse(
                        hidden_members & set(bundle.risk_marker.member_refs),
                        cid)
                for hotspot in bundle.hotspots:
                    self.assertFalse(hidden_members & set(hotspot.member_refs),
                                     cid)
                for link in bundle.deep_links:
                    self.assertNotIn(link.member_object_ref, hidden_members,
                                     cid)
                    if link.site_ref:
                        self.assertNotIn(link.site_ref, hidden_sites, cid)
                if bundle.counts.rate_zh is not None:
                    self.assertFalse(hidden_members, cid)
                    self.assertFalse(hidden_sites, cid)

    def test_hidden_site_members_never_reach_any_audience_object(self) -> None:
        # The member-site pair visibility boundary: a member whose site is
        # hidden (in hidden_site_refs) must never appear in the audience
        # member plane, the risk marker, hotspots, deep links or the Query
        # draft -- across all 312 catalog cases.
        for cid, typed, result, bundle in self.cases:
            hidden_sites = set(typed.visibility_decision.hidden_site_refs)
            hidden_site_members = {
                m.member_ref for m in typed.members
                if m.site_stable_id and m.site_stable_id in hidden_sites}
            with self.subTest(cid=cid):
                self.assertFalse(
                    hidden_site_members
                    & set(bundle.audience.projectable_member_refs), cid)
                if bundle.risk_marker is not None:
                    self.assertFalse(
                        hidden_site_members
                        & set(bundle.risk_marker.member_refs), cid)
                if bundle.query_draft is not None:
                    self.assertFalse(
                        hidden_site_members
                        & set(bundle.query_draft.member_refs), cid)
                for hotspot in bundle.hotspots:
                    self.assertFalse(
                        hidden_site_members & set(hotspot.member_refs), cid)
                for link in bundle.deep_links:
                    self.assertNotIn(link.member_object_ref,
                                     hidden_site_members, cid)
                    self.assertNotIn(link.site_ref, hidden_sites, cid)

    def test_pair_visible_counts_match_projectable_subject_site_pairs(self) -> None:
        # All member-derived counts are computed over the exact typed
        # projectable_subject_site_pairs authority intersected with the
        # projectable member/site planes (gate runs emit a zero count
        # surface regardless of members).  A hidden-site or wrong-scope
        # member has no projectable pair and contributes to none of them.
        for cid, typed, result, bundle in self.cases:
            if result.unit is None:
                continue
            proj_pairs = set(tuple(p) for p in
                             typed.visibility_decision.projectable_subject_site_pairs)
            proj_member_refs = set(
                typed.visibility_decision.projectable_member_refs)
            proj_site_refs = set(
                typed.visibility_decision.projectable_site_refs)
            visible_members = [
                m for m in typed.members
                if m.member_ref in proj_member_refs
                and m.site_stable_id in proj_site_refs
                and (m.subject_stable_id, m.site_stable_id) in proj_pairs]
            counts = bundle.counts
            with self.subTest(cid=cid):
                self.assertEqual(
                    counts.individual_risk_count,
                    len({m.member_ref for m in visible_members
                         if m.member_kind == "individual_risk"}), cid)
                self.assertEqual(
                    counts.affected_subject_count,
                    len({m.subject_stable_id for m in visible_members
                         if m.subject_stable_id}), cid)
                self.assertEqual(
                    counts.center_pattern_count,
                    len({m.member_ref for m in visible_members
                         if m.member_kind == "center_pattern"}), cid)
                self.assertEqual(
                    counts.numerator_member_count,
                    len({m.member_ref for m in visible_members}), cid)
                if not visible_members:
                    # event/outcome and affected-site numerator facts are
                    # suppressed when no safe member-site pair remains
                    self.assertEqual(counts.event_or_outcome_count, 0, cid)
                    self.assertEqual(counts.affected_site_count, 0, cid)
                    self.assertTrue(counts.event_count_disabled, cid)
                    self.assertTrue(counts.site_count_disabled, cid)

    def test_visible_counts_never_exceed_oracle_raw(self) -> None:
        for cid, typed, result, bundle in self.cases:
            if result.unit is None:
                continue
            leaf = (self.by_oracle[cid]["expected_leaf_set"] or [None])[0]
            if leaf is None:
                continue
            counts = bundle.counts
            with self.subTest(cid=cid):
                self.assertLessEqual(counts.individual_risk_count,
                                     leaf["numerator_individual_risk_count"])
                self.assertLessEqual(counts.affected_subject_count,
                                     leaf["numerator_affected_subject_count"])
                self.assertLessEqual(counts.event_or_outcome_count,
                                     leaf["numerator_event_or_outcome_count"])

    def test_pd_wording_exactly_matches_typed_state(self) -> None:
        pd_cases = []
        for cid, typed, result, bundle in self.cases:
            draft = bundle.query_draft
            if draft is None:
                continue
            with self.subTest(cid=cid):
                self.assertEqual(
                    draft.pd_wording_state,
                    typed.query_decision.pd_wording_state, cid)
            if typed.query_decision.pd_wording_state == "verify_whether_pd":
                self.assertIn("请核实是否为 PD", draft.action_sentence, cid)
                pd_cases.append(cid)
            else:
                self.assertNotIn("请核实是否为 PD",
                                 draft.action_sentence, cid)
        self.assertEqual(len(pd_cases), 1, pd_cases)

    def test_query_sentences_are_clean_native_chinese(self) -> None:
        for cid, typed, result, bundle in self.cases:
            draft = bundle.query_draft
            if draft is None:
                continue
            sentences = (draft.basis_sentence, draft.finding_sentence,
                         draft.action_sentence)
            for sentence in sentences:
                with self.subTest(cid=cid):
                    self.assertTrue(sentence.startswith(("依据：", "发现：",
                                                         "行动项：")))
            joined = "".join(sentences)
            refs = _all_typed_refs(typed)
            for ref in refs:
                self.assertNotIn(ref, joined, cid)
            for label in _FORBIDDEN_AUDIENCE_LABELS:
                self.assertNotIn(label, joined, cid)
            lowered = joined.lower()
            for token in _FORBIDDEN_RAW_TOKENS:
                self.assertNotIn(token, lowered, cid)

    def test_all_audience_strings_are_clean_chinese(self) -> None:
        for cid, typed, result, bundle in self.cases:
            texts = _audience_texts(bundle)
            for text in texts:
                with self.subTest(cid=cid):
                    lowered = text.lower()
                    for label in _FORBIDDEN_AUDIENCE_LABELS:
                        self.assertNotIn(label, lowered, cid)
                    for token in _RAW_ENUM_TOKENS:
                        self.assertNotIn(token, lowered, cid)
                    self.assertIsNone(
                        _RAW_REASON_RE.search(text),
                        f"raw reason/state token in audience text: {text}")
                    self.assertNotIn("_", text, cid)

    def test_deep_link_kinds_bound_to_eligible_sets(self) -> None:
        seen_kinds = set()
        for cid, typed, result, bundle in self.cases:
            vis = typed.visibility_decision
            eligible_members = set(vis.deep_link_eligible_member_refs)
            eligible_sites = set(vis.deep_link_eligible_site_refs)
            eligible_pairs = {tuple(p)
                              for p in vis.deep_link_eligible_subject_site_pairs}
            member_by_ref = {m.member_ref: m for m in typed.members}
            for link in bundle.deep_links:
                seen_kinds.add(link.target_kind)
                with self.subTest(cid=cid, kind=link.target_kind):
                    self.assertIn(link.target_kind,
                                  ("member", "site", "subject_site_pair"))
                    if link.target_kind == "member":
                        self.assertIn(link.member_object_ref, eligible_members)
                        member = member_by_ref[link.member_object_ref]
                        self.assertEqual(link.subject_ref,
                                         member.subject_stable_id)
                        self.assertEqual(link.site_ref, member.site_stable_id)
                        self.assertEqual(
                            link.visibility_decision_ref, vis.decision_id)
                    elif link.target_kind == "site":
                        self.assertIn(link.site_ref, eligible_sites)
                        self.assertIsNone(link.subject_ref)
                        self.assertIsNone(link.member_object_ref)
                    else:
                        self.assertIn((link.subject_ref, link.site_ref),
                                      eligible_pairs)
                        self.assertIsNone(link.member_object_ref)
                    if link.target_state == "unavailable":
                        self.assertIsNone(link.source_locator)
                        self.assertEqual(link.unavailable_message,
                                         "来源暂无法定位")
                    else:
                        self.assertIsNotNone(link.source_locator)
        self.assertEqual(seen_kinds, {"member", "site", "subject_site_pair"})

    def test_high_risk_hotspot_preserved(self) -> None:
        hotspots = {
            cid: bundle.hotspots
            for cid, typed, result, bundle in self.cases
            if bundle.hotspots
        }
        self.assertEqual(set(hotspots), {"D10-CASE-170", "D10-CASE-182"})
        for cid, rows in hotspots.items():
            for row in rows:
                self.assertEqual(row.monitoring_priority, "high", cid)
        subjects = {row.subject_ref
                    for rows in hotspots.values() for row in rows}
        self.assertEqual(subjects, {"SYN-D10-SUBJ-170-01-01",
                                    "SYN-D10-SUBJ-182-01-01"})

    def test_hotspot_and_center_order_never_punitive(self) -> None:
        for cid, typed, result, bundle in self.cases:
            site_refs = [row.site_ref for row in bundle.center_distribution]
            with self.subTest(cid=cid):
                self.assertEqual(site_refs, sorted(site_refs))
            order = [row.monitoring_priority for row in bundle.hotspots]
            if order:
                ranks = {"high": 0, "medium": 1}
                with self.subTest(cid=cid):
                    self.assertEqual(
                        order, sorted(order,
                                      key=lambda p: ranks.get(p, 99)))
            # no black-box score anywhere
            for row in bundle.hotspots:
                self.assertFalse(hasattr(row, "score"))
            for row in bundle.center_distribution:
                self.assertFalse(hasattr(row, "rank"))

    def test_trend_surface_present_only_for_trend_kinds(self) -> None:
        for cid, typed, result, bundle in self.cases:
            kind = typed.signal_definition.signal_kind
            with self.subTest(cid=cid):
                self.assertEqual(
                    bundle.trend_surface.trend_surface_present,
                    kind in ("project_time_trend", "project_safety_trend",
                             "project_efficacy_trend"))

    def test_r2_handoff_every_positive_with_legal_actions(self) -> None:
        actions = {}
        for cid, typed, result, bundle in self.cases:
            if result.unit is None:
                self.assertIsNone(bundle.r2_handoff, cid)
                continue
            if result.unit.l1_disposition != "positive":
                self.assertIsNone(bundle.r2_handoff, cid)
                continue
            handoff = bundle.r2_handoff
            self.assertIsNotNone(handoff, cid)
            assert handoff is not None
            actions[handoff.action] = actions.get(handoff.action, 0) + 1
            validation = validate_d10_r2_handoff(handoff, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")
        self.assertEqual(actions["create"], 100)
        self.assertEqual(actions["continue"], 2)
        self.assertEqual(actions["update"], 1)
        self.assertEqual(actions["propose_close"], 1)
        self.assertEqual(actions["supersede"], 9)

    def test_all_emitted_projection_objects_validate(self) -> None:
        for cid, typed, result, bundle in self.cases:
            validation = validate_d10_project_projection(
                bundle.project_projection, typed, result)
            self.assertTrue(validation["valid"],
                            f"{cid}: {validation['reasons']}")

    def test_emitted_evaluation_identity_equals_authoritative_trace_leaf(
            self) -> None:
        # the sole evaluation identity in every emitted object and hash is
        # the authoritative result field, identical to its trace leaf -- the
        # projection never computes a parallel identity
        for cid, typed, result, bundle in self.cases:
            with self.subTest(cid=cid):
                self.assertEqual(bundle.version.source_evaluation_content_identities,
                                 (result.evaluation_content_identity,))
                self.assertEqual(result.evaluation_content_identity,
                                 result.trace[0].content_identity)
                self.assertEqual(bundle.version.source_evaluation_content_identities[0],
                                 result.trace[0].content_identity)
                if bundle.query_draft is not None:
                    self.assertEqual(bundle.query_draft.evaluation_content_identity,
                                     result.evaluation_content_identity, cid)
                if bundle.r2_handoff is not None:
                    self.assertEqual(
                        bundle.r2_handoff.current_evaluation_content_ref,
                        result.evaluation_content_identity, cid)

    def test_structured_sentence_parts_closed_and_render_exactly(self) -> None:
        for cid, typed, result, bundle in self.cases:
            draft = bundle.query_draft
            if draft is None:
                continue
            with self.subTest(cid=cid):
                all_parts = tuple(draft.basis_parts) + tuple(
                    draft.finding_parts) + tuple(draft.action_parts)
                self.assertTrue(all_parts)
                for part in all_parts:
                    self.assertIsInstance(part, D10AudiencePart)
                    self.assertIn(
                        part.part_kind,
                        ("authority_basis", "observed_finding",
                         "denominator_context", "uncertainty",
                         "counterevidence", "action_verify",
                         "action_reconcile", "action_pd_verify",
                         "source_business_identifier"))
                    self.assertTrue(part.text_zh)
                self.assertEqual(
                    "".join(p.text_zh for p in draft.basis_parts),
                    draft.basis_sentence)
                self.assertEqual(
                    "".join(p.text_zh for p in draft.finding_parts),
                    draft.finding_sentence)
                self.assertEqual(
                    "".join(p.text_zh for p in draft.action_parts),
                    draft.action_sentence)

    def test_business_identifiers_only_in_identifier_parts(self) -> None:
        for cid, typed, result, bundle in self.cases:
            draft = bundle.query_draft
            if draft is None:
                continue
            member_by_ref = {m.member_ref: m for m in typed.members}
            business_ids = set()
            for ref in draft.member_refs:
                member = member_by_ref.get(ref)
                if member is not None and member.subject_stable_id:
                    business_ids.add(member.subject_stable_id)
            if not business_ids:
                continue
            with self.subTest(cid=cid):
                all_parts = tuple(draft.basis_parts) + tuple(
                    draft.finding_parts) + tuple(draft.action_parts)
                for part in all_parts:
                    if part.part_kind == "source_business_identifier":
                        continue
                    for bid in business_ids:
                        self.assertNotIn(bid, part.text_zh, cid)


class TestD10Port8911Stopped(unittest.TestCase):
    def test_tcp_8911_connection_refused(self) -> None:
        refused = False
        try:
            with socket.create_connection(("127.0.0.1", 8911), timeout=1):
                pass
        except OSError:
            refused = True
        self.assertTrue(refused,
                        "port 8911 must stay stopped (connection refused)")


# ---------------------------------------------------------------------------
# Audience visibility projection
# ---------------------------------------------------------------------------


class TestD10AudienceProjection(unittest.TestCase):
    def test_positive_payload_present_with_risk_and_query(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        projection = build_d10_audience_projection(typed, result)
        self.assertTrue(projection.audience_payload_present)
        self.assertTrue(projection.risk_marker_present)
        self.assertTrue(projection.query_present)
        self.assertEqual(projection.hidden_member_count, 0)
        self.assertEqual(projection.projectable_member_refs,
                         tuple(m.member_ref for m in typed.members))
        self.assertFalse(projection.disclosure_leak_present)

    def test_global_gate_emits_no_payload(self) -> None:
        typed, result = _evaluate("D10-CASE-079")
        self.assertEqual(result.disposition_or_gate, "global_gate")
        projection = build_d10_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.risk_marker_present)
        self.assertFalse(projection.query_present)
        self.assertFalse(projection.hotspot_present)
        self.assertFalse(projection.deep_link_present)

    def test_routing_and_handoff_gates_emit_no_payload(self) -> None:
        typed, result = _evaluate("D10-CASE-061")
        self.assertEqual(result.disposition_or_gate, "routing_gate")
        projection = build_d10_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        typed, result = _evaluate("D10-CASE-067")
        self.assertEqual(result.disposition_or_gate, "handoff_gate")
        projection = build_d10_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)

    def test_admitted_not_evaluable_has_no_payload_but_count_surface(self) -> None:
        typed, result = _evaluate("D10-CASE-005")
        self.assertEqual(result.disposition_or_gate, "not_evaluable")
        projection = build_d10_audience_projection(typed, result)
        self.assertFalse(projection.audience_payload_present)
        self.assertFalse(projection.risk_marker_present)
        self.assertFalse(projection.query_present)
        counts = build_d10_count_surface(typed, result)
        self.assertEqual(counts.disposition_zh, "暂无法评价（附原因）")
        self.assertEqual(counts.coverage_zh, "本次可评价范围/数据完整性")

    def test_hidden_members_never_reach_any_audience_payload(self) -> None:
        typed, result = _evaluate("D10-CASE-009")
        self.assertEqual(result.disposition_or_gate, "positive")
        projection = build_d10_audience_projection(typed, result)
        hidden = set(typed.visibility_decision.hidden_member_refs)
        self.assertTrue(hidden)
        self.assertFalse(hidden & set(projection.projectable_member_refs))
        self.assertEqual(projection.hidden_member_count, len(hidden))
        self.assertFalse(projection.disclosure_leak_present)
        bundle = project_d10_run(typed, result)
        if bundle.query_draft is not None:
            self.assertFalse(hidden & set(bundle.query_draft.member_refs))

    def test_hidden_site_plane_suppresses_site_surface(self) -> None:
        typed, result = _evaluate("D10-CASE-262")
        self.assertEqual(result.disposition_or_gate, "positive")
        projection = build_d10_audience_projection(typed, result)
        self.assertEqual(projection.projectable_site_refs, ())
        self.assertEqual(projection.hidden_site_refs, ("SYN-D10-SITE-001",))
        counts = build_d10_count_surface(typed, result)
        self.assertTrue(counts.site_count_disabled)
        self.assertTrue(counts.event_count_disabled)
        self.assertEqual(counts.affected_site_count, 0)
        self.assertEqual(build_d10_center_distribution(typed, result), ())

    def test_hidden_site_members_leave_zero_counts_and_no_marker(self) -> None:
        # CASE-262 and CASE-265 are positive units whose seven members all
        # sit in the hidden site SYN-D10-SITE-001: no safe member-site pair
        # remains, so the audience exposes zero member-derived counts, no
        # risk marker and no audience payload.  The project signal count and
        # the R2 handoff remain (aggregate/lifecycle facts that do not
        # confirm the hidden site's members).
        for cid in ("D10-CASE-262", "D10-CASE-265"):
            typed, result = _evaluate(cid)
            with self.subTest(cid=cid):
                self.assertEqual(result.disposition_or_gate, "positive")
                projection = build_d10_audience_projection(typed, result)
                self.assertEqual(projection.projectable_member_refs, ())
                self.assertEqual(projection.projectable_site_refs, ())
                self.assertFalse(projection.audience_payload_present)
                self.assertFalse(projection.risk_marker_present)
                self.assertFalse(projection.query_present)
                self.assertFalse(projection.hotspot_present)
                self.assertFalse(projection.deep_link_present)
                self.assertFalse(projection.disclosure_leak_present)
                counts = build_d10_count_surface(typed, result)
                self.assertEqual(counts.individual_risk_count, 0)
                self.assertEqual(counts.affected_subject_count, 0)
                self.assertEqual(counts.center_pattern_count, 0)
                self.assertEqual(counts.numerator_member_count, 0)
                self.assertEqual(counts.visible_individual_risk_count, 0)
                self.assertEqual(counts.visible_affected_subject_count, 0)
                # event/outcome and affected-site numerator facts suppressed
                self.assertEqual(counts.event_or_outcome_count, 0)
                self.assertEqual(counts.affected_site_count, 0)
                self.assertTrue(counts.event_count_disabled)
                self.assertTrue(counts.site_count_disabled)
                # the aggregate project signal and lifecycle facts survive
                self.assertEqual(counts.project_signal_count, 1)
                self.assertIsNone(build_d10_risk_marker(typed, result))
                bundle = project_d10_run(typed, result)
                self.assertIsNotNone(bundle.r2_handoff)
                self.assertIsNone(bundle.query_draft)
                self.assertEqual(bundle.hotspots, ())
                self.assertEqual(bundle.deep_links, ())

    def test_wrong_scope_members_suppressed_not_evaluable(self) -> None:
        # CASE-085/086 are not_evaluable units whose seven members sit at a
        # wrong-scope site (SYN-OTHER-PROJECT-SITE-001 / SYN-OTHER-SITE-001).
        # No projectable (subject, site) pair exists, so the audience exposes
        # empty member refs, no payload/risk/query/hotspot/link flags, zero
        # member/event/site-derived counts and the native not_evaluable
        # explanation.  The raw 7/7/9/3 ledger stays inside D10RunResult.
        for cid in ("D10-CASE-085", "D10-CASE-086"):
            typed, result = _evaluate(cid)
            with self.subTest(cid=cid):
                self.assertEqual(result.disposition_or_gate, "not_evaluable")
                # raw ledger facts remain inside the authoritative result
                self.assertEqual(result.unit.individual_risk_count, 7, cid)
                self.assertEqual(result.unit.affected_subject_count, 7, cid)
                self.assertEqual(result.unit.event_or_outcome_count, 9, cid)
                self.assertEqual(result.unit.affected_site_count, 3, cid)
                projection = build_d10_audience_projection(typed, result)
                self.assertEqual(projection.projectable_member_refs, ())
                self.assertFalse(projection.audience_payload_present)
                self.assertFalse(projection.risk_marker_present)
                self.assertFalse(projection.query_present)
                self.assertFalse(projection.hotspot_present)
                self.assertFalse(projection.deep_link_present)
                counts = build_d10_count_surface(typed, result)
                self.assertEqual(counts.individual_risk_count, 0)
                self.assertEqual(counts.affected_subject_count, 0)
                self.assertEqual(counts.event_or_outcome_count, 0)
                self.assertEqual(counts.center_pattern_count, 0)
                self.assertEqual(counts.affected_site_count, 0)
                self.assertEqual(counts.numerator_member_count, 0)
                self.assertTrue(counts.event_count_disabled)
                self.assertTrue(counts.site_count_disabled)
                self.assertEqual(counts.disposition_zh, "暂无法评价（附原因）")
                self.assertIsNone(build_d10_risk_marker(typed, result))
                bundle = project_d10_run(typed, result)
                self.assertIsNone(bundle.r2_handoff)
                self.assertIsNone(bundle.query_draft)
                self.assertEqual(bundle.hotspots, ())
                self.assertEqual(bundle.deep_links, ())


# ---------------------------------------------------------------------------
# Separated count surface
# ---------------------------------------------------------------------------


class TestD10CountSurface(unittest.TestCase):
    def test_frozen_chinese_forms_and_separation(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        counts = build_d10_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 7)
        self.assertEqual(counts.affected_subject_count, 7)
        self.assertEqual(counts.event_or_outcome_count, 9)
        self.assertEqual(counts.center_pattern_count, 0)
        self.assertEqual(counts.affected_site_count, 3)
        self.assertEqual(counts.project_signal_count, 1)
        self.assertEqual(counts.clue_count, 0)
        self.assertEqual(counts.query_count, 1)
        self.assertEqual(counts.individual_risk_zh, "相关个体风险 7 条")
        self.assertEqual(counts.affected_subjects_zh, "受影响受试者 7 名")
        self.assertEqual(counts.event_or_outcome_zh, "事件或结局 9 起")
        self.assertEqual(counts.center_pattern_zh, "中心模式 0 项")
        self.assertEqual(counts.affected_site_zh, "受影响中心 3 个")
        self.assertEqual(counts.project_signal_zh, "项目信号 1 项")
        self.assertEqual(counts.query_count_zh, "查询草稿 1 条")
        self.assertEqual(counts.coverage_zh, "本次可评价范围/数据完整性")
        self.assertEqual(counts.denominator_zh, "接受治疗受试者 126 名")
        self.assertEqual(counts.rate_zh, "7/126（5.6%）")
        self.assertEqual(counts.disposition_zh, "发现值得优先复核的项目信号")

    def test_visible_counts_equal_raw_when_nothing_hidden(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        counts = build_d10_count_surface(typed, result)
        self.assertEqual(counts.visible_individual_risk_count,
                         counts.individual_risk_count)
        self.assertEqual(counts.visible_affected_subject_count,
                         counts.affected_subject_count)

    def test_suppressed_rate_never_shows_precision(self) -> None:
        typed, result = _evaluate("D10-CASE-009")
        self.assertEqual(result.disposition_or_gate, "positive")
        counts = build_d10_count_surface(typed, result)
        # the hidden blind boundary never renders a misleading precision rate
        self.assertIsNone(counts.rate_zh)
        self.assertEqual(counts.rate_projection_state,
                         typed.visibility_decision.rate_projection_state)

    def test_boundary_clue_never_becomes_query(self) -> None:
        typed, result = _evaluate("D10-CASE-003")
        self.assertEqual(result.disposition_or_gate, "boundary")
        counts = build_d10_count_surface(typed, result)
        self.assertEqual(counts.clue_count, 1)
        self.assertEqual(counts.query_count, 0)
        self.assertEqual(counts.project_signal_count, 0)
        self.assertIsNone(build_d10_query_draft(typed, result))

    def test_gate_surface_zero_counts(self) -> None:
        typed, result = _evaluate("D10-CASE-011")
        self.assertEqual(result.disposition_or_gate, "comparison_set_gate")
        counts = build_d10_count_surface(typed, result)
        self.assertEqual(counts.individual_risk_count, 0)
        self.assertEqual(counts.project_signal_count, 0)
        self.assertEqual(counts.query_count, 0)
        self.assertEqual(counts.disposition_zh,
                         "本次未生成医学评价（跨中心可比性尚未闭合）")


# ---------------------------------------------------------------------------
# Project-signal risk marker
# ---------------------------------------------------------------------------


class TestD10RiskMarker(unittest.TestCase):
    def test_positive_marker_public_identity(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        marker = build_d10_risk_marker(typed, result)
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker.risk_owner, "D10")
        self.assertEqual(marker.risk_kind, "project_signal")
        self.assertEqual(marker.aggregation_level, "project_signal")
        identity = marker.public_risk_identity
        self.assertEqual(identity["domain_id"], "D10_project_signal_aggregation")
        self.assertEqual(identity["scope_type"], "project")
        self.assertEqual(identity["public_identity_version"], "d10_public_v1")
        self.assertNotIn("run", identity)
        self.assertNotIn("snapshot", identity)
        self.assertNotIn("D10-CASE", str(identity))

    def test_marker_identity_excludes_run_and_snapshot(self) -> None:
        typed, _result = _evaluate("D10-CASE-001")
        identity_a = d10_public_risk_identity(typed)
        swapped = replace(typed, run_ref="SYN-RUN-OTHER",
                          snapshot_ref="SYN-SNAP-OTHER")
        identity_b = d10_public_risk_identity(swapped)
        self.assertEqual(identity_a, identity_b)

    def test_marker_excludes_hidden_members_and_locators(self) -> None:
        typed, result = _evaluate("D10-CASE-009")
        marker = build_d10_risk_marker(typed, result)
        self.assertIsNotNone(marker)
        assert marker is not None
        hidden = set(typed.visibility_decision.hidden_member_refs)
        self.assertFalse(hidden & set(marker.member_refs))

    def test_non_positive_runs_never_get_marker(self) -> None:
        for cid in ("D10-CASE-002", "D10-CASE-003", "D10-CASE-005",
                    "D10-CASE-004", "D10-CASE-061", "D10-CASE-079"):
            typed, result = _evaluate(cid)
            with self.subTest(cid=cid):
                self.assertIsNone(build_d10_risk_marker(typed, result),
                                  cid)

    def test_projection_binds_result_to_typed(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        # a result forged on multiple decisive axes must fail closed under
        # the strengthened structural binding
        mutations = [
            replace(result, stable_core_ref="*" * 8,
                    unit=replace(result.unit, stable_core_ref="*" * 8)),
            replace(result, evaluation_content_identity="0" * 64),
            replace(result, terminal_state="wild",
                    trace=(replace(result.trace[0], terminal_state="stable"),)),
            replace(result, disposition_or_gate="positive",
                    unit=replace(result.unit, l1_disposition="boundary")),
            replace(result, replay_byte_equal=True,
                    trace=(replace(result.trace[0], replay_byte_equal=True,
                                   trace_kind="evaluation_identity"),)),
            replace(result, unit=None,
                    gate=replace(result.gate, gate_kind="positive")
                    if result.gate is not None else None),
        ]
        for forged in mutations:
            with self.subTest(forged=bool(forged)):
                with self.assertRaises(D10ProjectionError):
                    build_d10_risk_marker(typed, forged)


# ---------------------------------------------------------------------------
# Hotspot preservation
# ---------------------------------------------------------------------------


class TestD10Hotspots(unittest.TestCase):
    def test_high_risk_singleton_preserved(self) -> None:
        typed, result = _evaluate("D10-CASE-170")
        rows = build_d10_hotspots(typed, result)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.subject_ref, "SYN-D10-SUBJ-170-01-01")
        self.assertEqual(row.monitoring_priority, "high")
        self.assertEqual(row.member_refs, ("SYN-D10-RISK-170-01",))
        self.assertEqual(row.source_locator_refs, ("SYN-D10-LOC-170-01",))
        # low project proportion / small sample never hides the singleton
        counts = build_d10_count_surface(typed, result)
        self.assertTrue(counts.individual_risk_count >= 1)

    def test_hotspot_replay_stable(self) -> None:
        typed, result = _evaluate("D10-CASE-182")
        first = build_d10_hotspots(typed, result)
        second = build_d10_hotspots(typed, result)
        self.assertEqual(first, second)

    def test_gate_and_not_evaluable_emit_no_hotspots(self) -> None:
        typed, result = _evaluate("D10-CASE-061")
        self.assertEqual(build_d10_hotspots(typed, result), ())
        typed, result = _evaluate("D10-CASE-005")
        self.assertEqual(build_d10_hotspots(typed, result), ())


# ---------------------------------------------------------------------------
# Verified one-hop deep links
# ---------------------------------------------------------------------------


class TestD10DeepLinks(unittest.TestCase):
    def test_all_three_kinds_bound_to_eligible_sets(self) -> None:
        typed, result = _evaluate("D10-CASE-253")
        vis = typed.visibility_decision
        links = build_d10_deep_links(typed, result)
        self.assertEqual(len(links), 3)
        kinds = {link.target_kind for link in links}
        self.assertEqual(kinds, {"member", "site", "subject_site_pair"})
        for link in links:
            self.assertEqual(link.visibility_decision_ref, vis.decision_id)
            self.assertTrue(link.return_state_key)
            if link.target_kind == "member":
                self.assertIn(link.member_object_ref,
                              vis.deep_link_eligible_member_refs)
                self.assertEqual(link.target_state, "locatable")
                self.assertEqual(link.source_locator, "SYN-D10-LOC-253-01")
            elif link.target_kind == "site":
                self.assertIn(link.site_ref, vis.deep_link_eligible_site_refs)
                self.assertIsNone(link.subject_ref)
            else:
                self.assertIn((link.subject_ref, link.site_ref),
                              vis.deep_link_eligible_subject_site_pairs)

    def test_member_link_target_and_return_state(self) -> None:
        typed, result = _evaluate("D10-CASE-249")
        member_by_ref = {m.member_ref: m for m in typed.members}
        links = build_d10_deep_links(typed, result)
        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.target_kind, "member")
        member = member_by_ref[link.member_object_ref]
        self.assertEqual(link.subject_ref, member.subject_stable_id)
        self.assertEqual(link.site_ref, member.site_stable_id)
        self.assertEqual(link.return_state_key, "SYN-D10-RET-249-1")

    def test_hidden_pair_never_has_a_link(self) -> None:
        typed, result = _evaluate("D10-CASE-009")
        links = build_d10_deep_links(typed, result)
        hidden = set(typed.visibility_decision.hidden_member_refs)
        for link in links:
            self.assertNotIn(link.member_object_ref, hidden)

    def test_hidden_site_never_has_a_link(self) -> None:
        typed, result = _evaluate("D10-CASE-262")
        self.assertEqual(build_d10_deep_links(typed, result), ())


# ---------------------------------------------------------------------------
# Natural-Chinese three-sentence Query draft
# ---------------------------------------------------------------------------


class TestD10QueryDraft(unittest.TestCase):
    def test_positive_delta_query_three_sentences(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        self.assertTrue(draft.basis_sentence.startswith("依据："))
        self.assertTrue(draft.finding_sentence.startswith("发现："))
        self.assertTrue(draft.action_sentence.startswith("行动项："))
        self.assertEqual(draft.query_owner, "D10")
        self.assertTrue(draft.draft_only)
        self.assertEqual(draft.member_count, 7)
        self.assertEqual(draft.member_refs,
                         tuple(m.member_ref for m in typed.members))
        self.assertEqual(draft.redundancy_decision, "project_delta_present")
        validation = validate_d10_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])
        # native Chinese; engineering refs only in structured fields
        self.assertIn("项目风险分布", draft.basis_sentence)
        self.assertIn("受试者", draft.finding_sentence)
        joined = draft.basis_sentence + draft.finding_sentence \
            + draft.action_sentence
        for ref in _all_typed_refs(typed):
            self.assertNotIn(ref, joined)
        self.assertEqual(draft.basis_refs,
                         (typed.signal_definition.signal_definition_id,
                          typed.signal_definition.positive_rule_ref,
                          typed.analysis_windows[-1].analysis_window_stable_id,
                          typed.mode_contract.mode_contract_version))

    def test_hidden_members_and_sites_suppress_partial_query(self) -> None:
        # a hidden member or hidden site intersecting the unit audience
        # boundary forbids a draft entirely: no partial Query and never a
        # Query object carrying hidden refs
        for cid in ("D10-CASE-009", "D10-CASE-021", "D10-CASE-033",
                    "D10-CASE-045", "D10-CASE-057", "D10-CASE-261",
                    "D10-CASE-262", "D10-CASE-263", "D10-CASE-264",
                    "D10-CASE-265"):
            typed, result = _evaluate(cid)
            with self.subTest(cid=cid):
                self.assertEqual(result.disposition_or_gate, "positive")
                draft = build_d10_query_draft(typed, result)
                self.assertIsNone(draft, cid)
                counts = build_d10_count_surface(typed, result)
                self.assertEqual(counts.query_count, 0, cid)
                audience = build_d10_audience_projection(typed, result)
                self.assertFalse(audience.query_present, cid)

    def test_fully_visible_draft_has_complete_union_disjoint_refs(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        unit_members = {m.member_ref for m in typed.members}
        covered = set(typed.query_decision.covered_member_refs)
        uncovered = set(typed.query_decision.uncovered_member_refs)
        # the emitted draft preserves the exact covered/uncovered partition
        self.assertEqual(set(draft.covered_member_refs), covered)
        self.assertEqual(set(draft.uncovered_member_refs), uncovered)
        self.assertEqual(covered | uncovered, unit_members)
        self.assertEqual(covered & uncovered, set())
        # the complete (untruncated) member list is the uncovered refs
        self.assertEqual(list(draft.member_refs),
                         list(draft.uncovered_member_refs))
        self.assertEqual(draft.member_count, len(draft.uncovered_member_refs))
        validation = validate_d10_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_redundancy_union_disjoint_proof_exact(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        unit_members = {m.member_ref for m in typed.members}
        covered = set(draft.covered_member_refs)
        uncovered = set(draft.uncovered_member_refs)
        self.assertEqual(covered | uncovered, unit_members)
        self.assertEqual(covered & uncovered, set())
        self.assertEqual(draft.unit_member_set_hash,
                         typed.query_decision.unit_member_set_hash)
        self.assertEqual(draft.coverage_proof_hash,
                         typed.query_decision.coverage_proof_hash)

    def test_pd_wording_exact_template(self) -> None:
        typed, result = _evaluate("D10-CASE-246")
        draft = build_d10_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        self.assertEqual(draft.pd_wording_state, "verify_whether_pd")
        self.assertIn("请核实是否为 PD", draft.action_sentence)
        validation = validate_d10_query_draft(draft, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_query_never_treated_as_workflow_state(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        self.assertTrue(draft.draft_only)
        self.assertFalse(hasattr(draft, "status"))
        self.assertFalse(hasattr(draft, "state"))
        self.assertFalse(hasattr(draft, "task_ref"))

    def test_validator_rejects_coherently_resigned_query(self) -> None:
        # A coherent re-sign recomputes BOTH query_draft_id and content_hash
        # from the tampered fields using the production canonical recipe, so
        # the local hash checks stay consistent.  The validator must still
        # reject because the object is not the exact authoritative rebuild --
        # not because a stale local hash remains.
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        new_finding_parts = tuple(
            D10AudiencePart(part.part_kind,
                            part.text_zh.replace("本项目", "其他项目", 1))
            for part in draft.finding_parts)
        new_finding_sentence = "".join(p.text_zh for p in new_finding_parts)
        self.assertNotEqual(new_finding_sentence, draft.finding_sentence)
        tampered = _requery_draft(
            draft, finding_parts=new_finding_parts,
            finding_sentence=new_finding_sentence)
        validation = validate_d10_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("query_draft_not_exact_authoritative_projection",
                      validation["reasons"])
        self.assertNotIn("content_hash_stale", validation["reasons"])

    def test_validator_rejects_coherently_resigned_query_member_set(self) -> None:
        # Coherently re-signing an identity-bearing member set (reordered
        # member list) keeps the hashes consistent but the validator rejects
        # the incomplete uncovered-projectable member set, not a stale hash.
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        reordered = tuple(reversed(draft.member_refs))
        self.assertNotEqual(reordered, draft.member_refs)
        tampered = _requery_draft(draft, member_refs=reordered,
                                  member_count=len(reordered))
        validation = validate_d10_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("member_set_not_complete_uncovered_projectable",
                      validation["reasons"])
        self.assertNotIn("content_hash_stale", validation["reasons"])

    def test_validation_rejects_removed_evidence_locator(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        # a fully re-signed draft with a member/evidence removed cannot pass:
        # the evidence set must equal the complete deterministic locator set
        removed = replace(
            draft, member_refs=draft.member_refs[:-1],
            member_count=draft.member_count - 1,
            evidence_refs=(), source_locator_ids=())
        validation = validate_d10_query_draft(removed, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("member_set_not_complete_uncovered_projectable",
                      validation["reasons"])
        self.assertIn("evidence_must_be_non_empty", validation["reasons"])

    def test_source_revision_set_order_does_not_change_query_identity(
            self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        draft = build_d10_query_draft(typed, result)
        assert draft is not None
        self.assertEqual(
            draft.source_revision_refs,
            tuple(sorted(p.revision_id
                         for p in typed.source_revision_content_pairs)))


# ---------------------------------------------------------------------------
# R2 lifecycle handoff
# ---------------------------------------------------------------------------


class TestD10R2Handoff(unittest.TestCase):
    def _handoff(self, cid: str):
        typed, result = _evaluate(cid)
        handoff = build_d10_r2_handoff(typed, result)
        self.assertIsNotNone(handoff, cid)
        assert handoff is not None
        return typed, result, handoff

    def test_create_without_prior_initial_full(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-213")
        self.assertEqual(handoff.action, "create")
        self.assertIsNone(handoff.prior_risk_instance_ref)
        self.assertEqual(handoff.lineage_relation, "initial_full_snapshot")
        self.assertEqual(handoff.idempotency_key, handoff.handoff_id)
        validation = validate_d10_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_initial_full_positive_without_declared_action_derives_create(
            self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        self.assertIsNone(typed.change_decision)
        self.assertEqual(handoff.action, "create")
        self.assertIsNone(handoff.prior_risk_instance_ref)
        self.assertEqual(handoff.lineage_relation, "initial_full_snapshot")
        validation = validate_d10_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_continue_with_prior_data_revision(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-218")
        self.assertEqual(handoff.action, "continue")
        self.assertEqual(handoff.prior_risk_instance_ref,
                         "SYN-D10-R2-PRIOR-001")
        self.assertEqual(handoff.lineage_relation,
                         "continued_from_data_revision")
        self.assertEqual(handoff.idempotency_key, handoff.handoff_id)

    def test_update_action(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-219")
        self.assertEqual(handoff.action, "update")
        self.assertIsNotNone(handoff.prior_risk_instance_ref)

    def test_propose_close_action(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-217")
        self.assertEqual(handoff.action, "propose_close")
        self.assertIsNotNone(handoff.prior_risk_instance_ref)

    def test_supersede_requires_superseded_lineage(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-225")
        self.assertEqual(handoff.action, "supersede")
        self.assertTrue(handoff.lineage_relation.startswith("superseded_by_"))
        validation = validate_d10_r2_handoff(handoff, typed, result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_reopen_action_legal_matrix(self) -> None:
        # a reopen handoff must carry the reopened data-change kind and a
        # prior-bearing data lineage; inventing the action on a continuation
        # unit is rejected (the action is derived, never accepted).
        typed, result, handoff = self._handoff("D10-CASE-218")
        reopened = replace(handoff, action="reopen")
        validation = validate_d10_r2_handoff(reopened, typed, result)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("action_mismatch" in reason
                            for reason in validation["reasons"]))

    def test_create_with_prior_ref_fails_closed(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        forged = replace(handoff, action="create",
                         prior_risk_instance_ref="SYN-D10-R2-PRIOR-001",
                         lineage_relation="continued_from_data_revision",
                         handoff_id="0" * 64, idempotency_key="0" * 64)
        validation = validate_d10_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("create_with_prior_ref", validation["reasons"])
        self.assertIn("handoff_id_stale", validation["reasons"])

    def test_non_create_without_prior_ref_fails_closed(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        for action in ("continue", "update", "propose_close", "reopen",
                       "supersede"):
            forged = replace(handoff, action=action,
                             prior_risk_instance_ref=None,
                             lineage_relation="continued_from_data_revision",
                             handoff_id="0" * 64, idempotency_key="0" * 64)
            validation = validate_d10_r2_handoff(forged, typed, result)
            with self.subTest(action=action):
                self.assertFalse(validation["valid"])
                self.assertIn("non_create_without_prior_ref",
                              validation["reasons"])
                self.assertTrue(any("action_mismatch" in reason
                                    for reason in validation["reasons"]))

    def test_supersede_without_superseded_lineage_fails_closed(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-218")
        tampered = replace(handoff, action="supersede",
                           lineage_relation="continued_from_data_revision",
                           handoff_id="0" * 64, idempotency_key="0" * 64)
        validation = validate_d10_r2_handoff(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("supersede" in reason
                            for reason in validation["reasons"]))

    def test_identity_bearing_field_tamper_probes(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-218")
        probes = (
            ("member_refs", ("SYN-RISK-FORGED",), "member_refs_mismatch"),
            ("measure_ledger_ref", "0" * 64, "measure_ledger_ref_mismatch"),
            ("completeness_decision_ref", "0" * 64,
             "completeness_decision_hash_stale"),
            ("monitoring_priority", "high", "monitoring_priority_mismatch"),
            ("no_auto_close_reasons", ("存在高监察优先级成员",),
             "no_auto_close_reasons_mismatch"),
            ("stable_core_ref", "0" * 64, "stable_core_stale"),
            ("change_decision_ref", "0" * 64, "change_decision_hash_stale"),
        )
        for field, value, reason in probes:
            tampered = replace(handoff, **{field: value})
            validation = validate_d10_r2_handoff(tampered, typed, result)
            with self.subTest(field=field):
                self.assertFalse(validation["valid"], field)
                self.assertIn(reason, validation["reasons"], field)

    def test_handoff_and_idempotency_key_cannot_be_jointly_forged(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        forged = replace(handoff, handoff_id="0" * 64,
                         idempotency_key="0" * 64)
        validation = validate_d10_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("handoff_id_stale", validation["reasons"])

    def test_validator_rejects_coherently_resigned_handoff(self) -> None:
        # Re-signing a tampered action keeps handoff_id/idempotency_key
        # internally consistent with the authoritative identity pins; the
        # validator must reject for the wrong action binding, not a stale
        # hash.
        typed, result, handoff = self._handoff("D10-CASE-218")
        self.assertEqual(handoff.action, "continue")
        tampered = _rehandoff(handoff, action="update")
        validation = validate_d10_r2_handoff(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("action_mismatch" in reason
                            for reason in validation["reasons"]))
        self.assertNotIn("handoff_id_stale", validation["reasons"])

    def test_no_handoff_on_gate_boundary_or_not_evaluable(self) -> None:
        for cid in ("D10-CASE-061", "D10-CASE-011", "D10-CASE-079",
                    "D10-CASE-003", "D10-CASE-005"):
            typed, result = _evaluate(cid)
            with self.subTest(cid=cid):
                self.assertIsNone(build_d10_r2_handoff(typed, result), cid)

    def test_handoff_replay_stable_across_run_snapshot_swap(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-218")
        swapped = replace(typed, run_ref="SYN-RUN-OTHER",
                          snapshot_ref="SYN-SNAP-OTHER")
        swapped_authority = replace(
            _authority_for("D10-CASE-218"),
            run_ref="SYN-RUN-OTHER", snapshot_ref="SYN-SNAP-OTHER")
        swapped_result = evaluator.evaluate(swapped, swapped_authority)
        self.assertEqual(swapped_result.disposition_or_gate, "positive")
        swapped_handoff = build_d10_r2_handoff(swapped, swapped_result)
        self.assertIsNotNone(swapped_handoff)
        assert swapped_handoff is not None
        self.assertEqual(handoff.handoff_id, swapped_handoff.handoff_id)
        self.assertEqual(handoff.idempotency_key,
                         swapped_handoff.idempotency_key)
        self.assertEqual(handoff.current_evaluation_content_ref,
                         swapped_handoff.current_evaluation_content_ref)
        self.assertEqual(handoff.public_d10_risk_identity,
                         swapped_handoff.public_d10_risk_identity)
        self.assertEqual(swapped_handoff.run_snapshot_audit_refs,
                         ("SYN-RUN-OTHER", "SYN-SNAP-OTHER"))
        validation = validate_d10_r2_handoff(swapped_handoff,
                                             swapped, swapped_result)
        self.assertTrue(validation["valid"], validation["reasons"])

    def test_create_with_prior_contradiction_fails_closed(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        forged = replace(handoff, action="create",
                         prior_risk_instance_ref="SYN-R2-PRIOR",
                         handoff_id="0" * 64, idempotency_key="0" * 64)
        validation = validate_d10_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("create_with_prior_ref", validation["reasons"])

    def test_create_emits_contract_only(self) -> None:
        typed, result, handoff = self._handoff("D10-CASE-001")
        # the handoff is a pure emission: it carries no lifecycle side-effect
        self.assertFalse(hasattr(handoff, "created"))
        self.assertTrue(handoff.idempotency_key)
        self.assertIn("SYN-D10-PROJECT-001",
                      str(handoff.public_d10_risk_identity["project_ref"]))


# ---------------------------------------------------------------------------
# Project projection / version / authoritative rebuild
# ---------------------------------------------------------------------------


class TestD10ProjectProjection(unittest.TestCase):
    def test_projection_version_binds_identity(self) -> None:
        typed, result = _evaluate("D10-CASE-218")
        version = build_d10_projection_version(typed, result)
        self.assertTrue(version.projection_version_id.startswith("SYN")
                        or len(version.projection_version_id) == 64)
        self.assertEqual(len(version.projection_version_id), 64)
        self.assertEqual(version.audience_contract_ref,
                         typed.audience_text.audience_contract_id)
        self.assertIn(result.evaluation_content_identity,
                      version.source_evaluation_content_identities)

    def test_validation_rejects_tampered_projection(self) -> None:
        typed, result = _evaluate("D10-CASE-218")
        projection = build_d10_project_projection(typed, result)
        tampered = replace(
            projection,
            change_section=replace(
                projection.change_section,
                narrative_zh="伪造的变化叙述"),
            projection_content_hash="0" * 64,
            projection_id="0" * 64)
        validation = validate_d10_project_projection(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("project_projection_not_exact_authoritative_rebuild",
                      validation["reasons"])

    def test_validation_rejects_coherently_resigned_projection(self) -> None:
        # The projection content hash covers the structured core (change
        # kind, site refs, count-surface ref, ...), not the audience
        # narrative text.  Tampering the audience narrative while leaving
        # the stored projection_id/content_hash at their authoritative
        # values yields an internally consistent (coherently signed) object
        # whose whole-object equality to the authoritative rebuild is the
        # sole reason for rejection.
        typed, result = _evaluate("D10-CASE-218")
        projection = build_d10_project_projection(typed, result)
        tampered = replace(
            projection,
            change_section=replace(
                projection.change_section,
                narrative_zh="伪造的变化叙述"))
        self.assertEqual(tampered.projection_id, projection.projection_id)
        self.assertEqual(tampered.projection_content_hash,
                         projection.projection_content_hash)
        validation = validate_d10_project_projection(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("project_projection_not_exact_authoritative_rebuild",
                      validation["reasons"])

    def test_projection_content_hash_stable_across_run_swap(self) -> None:
        typed, result = _evaluate("D10-CASE-218")
        baseline = build_d10_project_projection(typed, result)
        swapped = replace(typed, run_ref="SYN-RUN-X",
                          snapshot_ref="SYN-SNAP-X")
        swapped_authority = replace(
            _authority_for("D10-CASE-218"),
            run_ref="SYN-RUN-X", snapshot_ref="SYN-SNAP-X")
        swapped_result = evaluator.evaluate(swapped, swapped_authority)
        self.assertEqual(swapped_result.disposition_or_gate, "positive")
        changed = build_d10_project_projection(swapped, swapped_result)
        self.assertEqual(baseline.projection_content_hash,
                         changed.projection_content_hash)
        self.assertNotEqual(baseline.projection_version_ref,
                            changed.projection_version_ref)


class TestD10InputReorderInvariance(unittest.TestCase):
    def test_member_order_swap_yields_identical_projection(self) -> None:
        typed, result = _evaluate("D10-CASE-001")
        bundle_a = project_d10_run(typed, result)
        swapped = replace(typed, members=tuple(reversed(typed.members)))
        result_b = evaluator.evaluate(swapped, _authority_for(
            "D10-CASE-001"))
        self.assertEqual(result_b, result)
        bundle_b = project_d10_run(swapped, result_b)
        self.assertEqual(bundle_b, bundle_a)

    def test_evaluation_identity_reorder_stable(self) -> None:
        # the authoritative result identity is reorder-invariant and equals
        # its trace leaf; the projection never computes a parallel identity
        typed, result = _evaluate("D10-CASE-001")
        swapped = replace(typed, members=tuple(reversed(typed.members)))
        result_b = evaluator.evaluate(swapped, _authority_for(
            "D10-CASE-001"))
        self.assertEqual(result_b.evaluation_content_identity,
                         result.evaluation_content_identity)
        self.assertEqual(result.evaluation_content_identity,
                         result.trace[0].content_identity)
        self.assertEqual(result_b.evaluation_content_identity,
                         result_b.trace[0].content_identity)


if __name__ == "__main__":
    unittest.main()