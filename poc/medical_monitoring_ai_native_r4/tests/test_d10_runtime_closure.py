"""R4-D10 runtime closure suite: public exports, static import/read closure,
fresh-interpreter package import, exact 312/312 oracle parity, emitted
projection/Query/handoff validation and audience-isolation closure.

Worker-03 slice (over the accepted Worker-01/Worker-02 snapshots):

* exact public exports: the bounded D10 ``__all__`` surface in
  ``mm_r4/__init__.py`` (public constants, immutable contract types,
  evaluator entrypoint/result types, projection types/builders/validators
  and public identities), with aliases for generic names and no
  test-only adapter / artifact / catalog / oracle / registry / quota /
  generator / verifier symbols;
* static closure: the three runtime modules (``d10_contracts.py`` /
  ``d10_evaluator.py`` / ``d10_projection.py``) contain no
  artifact/generator/test references, no file/service/network IO, no
  case/fixture/test identifiers, no oracle/registry/quota vocabulary, no
  audit-metadata access in the semantic modules and no audience prose in
  the evaluator (AST scan that skips docstrings so boundary declarations
  are not false positives);
* fresh interpreter: ``import mm_r4`` succeeds with ONLY the R1-R4 source
  roots on ``PYTHONPATH`` (no tests dir, no artifacts), loads no
  ``test_d10*`` module and writes no cache/output files;
* exact 312/312 oracle disposition/core/trace/source parity via the frozen
  test adapter (zero diffs, zero skips);
* every emitted projection / Query draft / R2 handoff across all 312 cases
  passes closed validation;
* hidden member/site/exact-pair and wrong-scope data never reach any
  audience surface; all audience strings remain native Chinese and free of
  raw enums / internal refs / backend labels;
* TCP port 8911 stays stopped.
"""

from __future__ import annotations

import ast
import os
import re
import socket
import subprocess
import sys
import tempfile
import unittest
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
from mm_r4 import d10_contracts as _dc  # noqa: E402
from mm_r4 import d10_evaluator as _ev  # noqa: E402
from mm_r4 import d10_projection as _pr  # noqa: E402

_RUNTIME_PATHS = (
    _R4_SRC / "mm_r4" / "d10_contracts.py",
    _R4_SRC / "mm_r4" / "d10_evaluator.py",
    _R4_SRC / "mm_r4" / "d10_projection.py",
)

# Tokens forbidden as EXACT code identifiers/attribute/argument names and
# code string constants in all three runtime modules (docstrings excluded):
# artifact/generator/test references, file/service/network IO and
# oracle/registry/quota leaf vocabulary.  Exact-membership matching keeps
# the legitimate runtime ``_IDENTITY_EXCLUDED_KEYS`` (``case_id`` /
# ``oracle_case_id``) and leaf vocabulary (``expected_disposition`` /
# ``expected_leaf``) from false-positiving.
_FORBIDDEN_CODE_TOKENS = (
    "catalog", "oracle", "registry", "quota", "generator", "verifier",
    "fixture", "adapter", "artifact", "load_artifacts", "load_authority",
    "verify_frozen_hashes", "build_typed_input", "ordered_expectations",
    "case_count", "unittest", "pytest", "test_d10",
    "open(", "read_text", "read_bytes", "json.load", "urllib", "requests",
    "subprocess", "socket", "8911", "print(",
)
_FORBIDDEN_ID_RE = re.compile(r"D10-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+")

# Audit/test-metadata tokens forbidden in the SEMANTIC modules (evaluator +
# projection); they may legitimately exist as schema in d10_contracts.py.
_SEMANTIC_ONLY_TOKENS = (
    "mutation_context", "anti_overfit_variant", "mutation_class",
    "variant_id", "base_fixture_id",
)

# Natural-language / display-label tokens forbidden in the evaluator.
_FORBIDDEN_PROSE_TOKENS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
    "请核实", "受试者", "中心模式相关成员", "事件 {n}",
)

# Forbidden audience labels; in the projection they may appear only inside
# the closed declaration tuple (at most once each).
_PROJECTION_LABELS = ("正式事实", "候选信号", "已记录事项", "只读", "通用风险点")

_EXPECTED_D10_EXPORTS = (
    "D10_SCHEMA_VERSION", "D10_TYPED_INPUT_SCHEMA", "D10_UNIT_ALGORITHM_VERSION",
    "D10_DOMAIN_ID", "D10ContractError", "D10TypedInput",
    "D10EvaluationAuthority", "d10_normalize_nfc", "d10_canonical_json",
    "d10_sha256_text", "d10_content_hash", "d10_unit_stable_core",
    "validate_d10_typed_input", "evaluate_d10", "D10RunResult",
    "D10UnitResult", "D10GateResult", "D10TraceLeaf", "D10SourceLeaf",
    "D10ForbiddenLeaf", "d10_evaluation_content_identity", "D10ProjectionError",
    "D10AudienceProjection", "D10ProjectionCountSurface", "D10ProjectionVersion",
    "D10RiskMarker", "D10HotspotProjection", "D10DeepLinkTarget",
    "D10AudiencePart", "D10QueryDraft", "D10ChangeSection", "D10CenterPatternRow",
    "D10TrendSurface", "D10WarningMarker", "D10R2RiskHandoff",
    "D10ProjectProjection", "D10ProjectionBundle", "build_d10_audience_projection",
    "build_d10_count_surface", "build_d10_projection_version",
    "build_d10_risk_marker", "build_d10_hotspots", "build_d10_deep_links",
    "build_d10_query_draft", "build_d10_change_section",
    "build_d10_center_distribution", "build_d10_trend_surface",
    "build_d10_warnings", "build_d10_r2_handoff", "build_d10_project_projection",
    "validate_d10_query_draft", "validate_d10_r2_handoff",
    "validate_d10_project_projection", "d10_public_risk_identity",
    "project_d10_run",
)

# Backend/raw reason tokens and snake_case reason patterns forbidden in any
# user-facing Chinese audience string.
_RAW_ENUM_TOKENS = frozenset((
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "permitted", "suppressed", "qualified", "create", "continue", "update",
    "propose_close", "reopen", "supersede", "gate", "ledger", "handoff",
    "payload", "generator", "verifier", "adapter", "oracle", "registry",
    "quota", "hotspot", "deep_link", "lineage", "stratum", "candidate",
    "evaluator", "projection", "envelope", "draft", "revision",
))
_RAW_REASON_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)+")


def _iter_code_strings(node) -> list:
    """All string constants in code, skipping docstrings at every level."""
    out = []
    for child in ast.iter_child_nodes(node):
        if (isinstance(node, (ast.Module, ast.FunctionDef,
                              ast.AsyncFunctionDef, ast.ClassDef))
                and node.body and node.body[0] is child
                and isinstance(child, ast.Expr)
                and isinstance(child.value, ast.Constant)
                and isinstance(child.value.value, str)):
            continue
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            out.append(child.value)
        else:
            out.extend(_iter_code_strings(child))
    return out


def _iter_code_names(node) -> list:
    out = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            out.append(child.id)
        elif isinstance(child, ast.Attribute):
            out.append(child.attr)
        elif isinstance(child, ast.arg):
            out.append(child.arg)
    return out


def _code_terms(path: Path) -> Tuple[list, str]:
    """(code term list, joined code text) with docstrings skipped."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    terms = list(_iter_code_strings(tree)) + list(_iter_code_names(tree))
    code = "\n".join(terms)
    return terms, code


def _authority_for(cid: str) -> Any:
    authority = adapter.load_authority()
    entry = next(e for e in authority["entries"] if e["case_id"] == cid)
    return adapter.build_authority(entry)


def _evaluate(cid: str) -> Tuple[Any, Any]:
    catalog, _oracle, _registry, _quota = adapter.load_artifacts()
    case = next(c for c in catalog["cases"] if c["case_id"] == cid)
    typed = adapter.build_typed_input(case["typed_input"])
    return typed, _ev.evaluate(typed, _authority_for(cid))


def _trace_leaf_dict(result: Any) -> dict:
    leaf = result.trace[0] if result.trace else None
    return {
        "trace_kind": leaf.trace_kind if leaf else None,
        "stable_core_ref": leaf.stable_core_ref if leaf else None,
        "content_identity": leaf.content_identity if leaf else None,
        "replay_byte_equal": leaf.replay_byte_equal if leaf else None,
        "terminal_state": leaf.terminal_state if leaf else None,
    }


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


class TestStaticRuntimeClosure(unittest.TestCase):
    def test_runtime_code_never_reads_acceptance_artifacts(self) -> None:
        for path in _RUNTIME_PATHS:
            terms, code = _code_terms(path)
            for token in _FORBIDDEN_CODE_TOKENS:
                self.assertNotIn(token, terms,
                                 f"{path.name} code contains {token!r}")
            self.assertIsNone(_FORBIDDEN_ID_RE.search(code),
                              f"{path.name} code contains a case/fixture id")

    def test_semantic_modules_never_access_audit_metadata(self) -> None:
        for path in (_RUNTIME_PATHS[1], _RUNTIME_PATHS[2]):
            terms, _code = _code_terms(path)
            for token in _SEMANTIC_ONLY_TOKENS:
                self.assertNotIn(token, terms,
                                 f"{path.name} code contains audit token "
                                 f"{token!r}")

    def test_evaluator_free_of_display_prose(self) -> None:
        terms, _code = _code_terms(_RUNTIME_PATHS[1])
        for token in _FORBIDDEN_PROSE_TOKENS:
            self.assertNotIn(token, terms,
                             f"d10_evaluator.py code contains prose "
                             f"{token!r}")

    def test_projection_labels_declared_exactly_once(self) -> None:
        terms, _code = _code_terms(_RUNTIME_PATHS[2])
        for label in _PROJECTION_LABELS:
            # the label may appear only inside its closed declaration tuple
            # (at most once as a code string constant)
            self.assertLessEqual(terms.count(label), 1,
                                 f"projection label {label!r} appears "
                                 f"outside its closed declaration")

    def test_runtime_modules_import_without_artifacts(self) -> None:
        import importlib
        for module_name in ("mm_r4.d10_contracts", "mm_r4.d10_evaluator",
                            "mm_r4.d10_projection"):
            module = importlib.import_module(module_name)
            self.assertIsNotNone(module)


class TestPublicExports(unittest.TestCase):
    def test_exact_d10_all_membership(self) -> None:
        import mm_r4
        exported = set(mm_r4.__all__)
        for name in _EXPECTED_D10_EXPORTS:
            self.assertIn(name, exported, f"{name} missing from __all__")
        # no stray D10 names beyond the intended surface
        d10_named = {name for name in exported if "d10" in name.lower()}
        self.assertLessEqual(d10_named, set(_EXPECTED_D10_EXPORTS),
                             d10_named - set(_EXPECTED_D10_EXPORTS))
        # test-only adapter / frozen artifact symbols are never exported
        for name in ("d10_adapter", "load_artifacts", "load_authority",
                     "verify_frozen_hashes", "build_typed_input", "catalog",
                     "oracle", "registry", "quota", "generator", "verifier"):
            self.assertNotIn(name, exported)

    def test_representative_export_object_identity(self) -> None:
        import mm_r4
        pairs = (
            ("D10ContractError", _dc.D10ContractError),
            ("D10TypedInput", _dc.D10TypedInput),
            ("D10EvaluationAuthority", _dc.D10EvaluationAuthority),
            ("D10RunResult", _ev.D10RunResult),
            ("D10UnitResult", _ev.D10UnitResult),
            ("D10GateResult", _ev.D10GateResult),
            ("d10_content_hash", _dc.d10_content_hash),
            ("d10_unit_stable_core", _dc.d10_unit_stable_core),
            ("validate_d10_typed_input", _dc.validate_typed_input),
            ("evaluate_d10", _ev.evaluate),
            ("d10_evaluation_content_identity",
             _ev.evaluation_content_identity),
            ("D10ProjectionBundle", _pr.D10ProjectionBundle),
            ("build_d10_query_draft", _pr.build_d10_query_draft),
            ("validate_d10_query_draft", _pr.validate_d10_query_draft),
            ("validate_d10_r2_handoff", _pr.validate_d10_r2_handoff),
            ("validate_d10_project_projection",
             _pr.validate_d10_project_projection),
            ("build_d10_r2_handoff", _pr.build_d10_r2_handoff),
            ("d10_public_risk_identity", _pr.d10_public_risk_identity),
            ("project_d10_run", _pr.project_d10_run),
        )
        for name, module_object in pairs:
            self.assertIs(getattr(mm_r4, name), module_object, name)
        # the D10 slice never shadows an existing generic export: its
        # entrypoints are exposed under the D10-prefixed aliases, which are
        # distinct objects from the generic actors of the other slices
        self.assertIn("evaluate_d10", mm_r4.__all__)
        self.assertIn("validate_d10_typed_input", mm_r4.__all__)
        self.assertIsNot(mm_r4.evaluate_d10, mm_r4.evaluate)


class TestFreshInterpreterImport(unittest.TestCase):
    def test_package_import_fresh_interpreter_no_cache_no_output(self) -> None:
        code = (
            "import sys\n"
            "import mm_r4\n"
            "expected = " + repr(list(_EXPECTED_D10_EXPORTS)) + "\n"
            "missing = [n for n in expected if n not in mm_r4.__all__]\n"
            "assert not missing, missing\n"
            "assert mm_r4.evaluate_d10 and mm_r4.validate_d10_typed_input\n"
            "assert mm_r4.project_d10_run\n"
            "bad = [m for m in sys.modules if m.startswith('test_d10')]\n"
            "assert not bad, bad\n"
            "print('FRESH-OK')\n"
        )
        env = {
            "PYTHONPATH": ":".join(str(p) for p in
                                   (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC)),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "-B", "-c", code],
                cwd=tmp, env={**dict(os.environ), **env},
                capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0,
                             f"fresh interpreter failed:\n{result.stdout}\n"
                             f"{result.stderr}")
            self.assertIn("FRESH-OK", result.stdout)
            leftovers = list(Path(tmp).iterdir())
            self.assertEqual(leftovers, [],
                             f"fresh interpreter wrote files: {leftovers}")


class TestOracleParityClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, _registry, _quota = adapter.load_artifacts()

    def test_312_case_oracle_parity_exact(self) -> None:
        """Accept dispositions/core/trace/source exactly against the oracle
        via the test-only adapter (zero diffs)."""
        self.assertEqual(len(self.catalog["cases"]), adapter.CASE_COUNT)
        expectations = {
            entry["case_id"]: entry
            for entry in self.oracle["ordered_expectations"]
        }
        disposition_problems = []
        core_problems = []
        trace_problems = []
        source_problems = []
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            expectation = expectations[cid]
            typed, result = _evaluate(cid)
            if result.disposition_or_gate != \
                    expectation["expected_disposition_or_gate"]:
                disposition_problems.append(
                    f"{cid}: runtime={result.disposition_or_gate} "
                    f"oracle={expectation['expected_disposition_or_gate']}")
            oracle_trace = expectation["expected_trace_leaf_set"]
            runtime_trace = _trace_leaf_dict(result)
            if len(result.trace) != len(oracle_trace):
                trace_problems.append(f"{cid}: trace count mismatch")
                continue
            for key in ("trace_kind", "stable_core_ref", "content_identity",
                        "replay_byte_equal", "terminal_state"):
                if runtime_trace[key] != oracle_trace[0][key]:
                    if key == "stable_core_ref":
                        core_problems.append(
                            f"{cid}: core {runtime_trace[key]!r} != "
                            f"{oracle_trace[0][key]!r}")
                    else:
                        trace_problems.append(
                            f"{cid}.{key}: {runtime_trace[key]!r} != "
                            f"{oracle_trace[0][key]!r}")
            if adapter.result_source_leaves(result) != \
                    expectation["expected_source_leaf_set"]:
                source_problems.append(f"{cid}: source leaf set mismatch")
        self.assertEqual(disposition_problems, [],
                         f"{len(disposition_problems)} disposition diffs: "
                         f"{disposition_problems[:10]}")
        self.assertEqual(core_problems, [],
                         f"{len(core_problems)} stable-core diffs: "
                         f"{core_problems[:10]}")
        self.assertEqual(trace_problems, [],
                         f"{len(trace_problems)} trace diffs: "
                         f"{trace_problems[:10]}")
        self.assertEqual(source_problems, [],
                         f"{len(source_problems)} source diffs: "
                         f"{source_problems[:10]}")

    def test_all_emitted_projection_query_handoff_validate(self) -> None:
        drafts = 0
        handoffs = 0
        for case in self.catalog["cases"]:
            cid = case["case_id"]
            typed, result = _evaluate(cid)
            bundle = _pr.project_d10_run(typed, result)
            projection_validation = _pr.validate_d10_project_projection(
                bundle.project_projection, typed, result)
            self.assertTrue(projection_validation["valid"],
                            f"{cid}: {projection_validation['reasons']}")
            if bundle.query_draft is not None:
                validation = _pr.validate_d10_query_draft(
                    bundle.query_draft, typed, result)
                self.assertTrue(validation["valid"],
                                f"{cid}: {validation['reasons']}")
                drafts += 1
            if bundle.r2_handoff is not None:
                validation = _pr.validate_d10_r2_handoff(
                    bundle.r2_handoff, typed, result)
                self.assertTrue(validation["valid"],
                                f"{cid}: {validation['reasons']}")
                handoffs += 1
        self.assertEqual(drafts, 100)
        self.assertEqual(handoffs, 113)


class TestAudienceIsolationClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = adapter.load_artifacts()
        cls.bundles = {}
        for case in cls.catalog["cases"]:
            typed, result = _evaluate(case["case_id"])
            cls.bundles[case["case_id"]] = (typed, result,
                                            _pr.project_d10_run(typed, result))

    def test_hidden_and_wrong_scope_never_reach_audience(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            hidden = set(typed.visibility_decision.hidden_member_refs or ())
            hidden_sites = set(typed.visibility_decision.hidden_site_refs or ())
            wrong_scope = {m.member_ref for m in typed.members
                           if m.member_scope_state != "in_scope"}
            if hidden:
                member_plane = {m.member_ref for m in typed.members}
                # a gate run may carry an external hidden ref (attack
                # input); only in-plane hidden refs are resolvable and
                # projected
                in_plane_hidden = hidden & member_plane
                visible = set(bundle.audience.projectable_member_refs)
                self.assertFalse(in_plane_hidden & visible, cid)
                self.assertTrue(
                    in_plane_hidden.issubset(
                        set(bundle.audience.hidden_member_refs)), cid)
                if bundle.query_draft is not None:
                    self.assertFalse(
                        hidden & set(bundle.query_draft.member_refs), cid)
                if bundle.risk_marker is not None:
                    self.assertFalse(
                        hidden & set(bundle.risk_marker.member_refs), cid)
                for hotspot in bundle.hotspots:
                    self.assertFalse(hidden & set(hotspot.member_refs), cid)
                for link in bundle.deep_links:
                    if link.member_object_ref is not None:
                        self.assertNotIn(link.member_object_ref, hidden, cid)
            if hidden_sites:
                self.assertFalse(
                    hidden_sites
                    & set(bundle.audience.projectable_site_refs), cid)
            if wrong_scope:
                # wrong-scope members dispose to not_evaluable and never
                # reach any audience payload object
                self.assertEqual(result.disposition_or_gate, "not_evaluable",
                                 cid)
                self.assertFalse(bundle.audience.audience_payload_present, cid)
                self.assertIsNone(bundle.risk_marker, cid)
                self.assertIsNone(bundle.query_draft, cid)
                self.assertIsNone(bundle.r2_handoff, cid)
                self.assertEqual(bundle.hotspots, (), cid)
                self.assertEqual(bundle.deep_links, (), cid)
            # visible counts never exceed the raw unit counts
            unit = result.unit
            if unit is not None:
                self.assertLessEqual(
                    bundle.counts.visible_individual_risk_count,
                    unit.individual_risk_count, cid)
                self.assertLessEqual(
                    bundle.counts.visible_affected_subject_count,
                    unit.affected_subject_count, cid)

    def test_no_forbidden_labels_or_raw_tokens_in_audience(self) -> None:
        for cid, (_typed, _result, bundle) in self.bundles.items():
            texts = _audience_texts(bundle)
            self.assertTrue(texts, cid)
            for text in texts:
                self.assertTrue(text, cid)
                for label in _PROJECTION_LABELS:
                    self.assertNotIn(label, text, cid)
                lowered = text.lower()
                for token in _RAW_ENUM_TOKENS:
                    self.assertNotIn(token, lowered, f"{cid}: {text}")
                self.assertEqual(_RAW_REASON_RE.search(text), None,
                                 f"{cid}: raw reason token in {text}")

    def test_forbidden_engineering_refs_absent_from_query_prose(self) -> None:
        for cid, (typed, _result, bundle) in self.bundles.items():
            draft = bundle.query_draft
            if draft is None:
                continue
            joined = (draft.basis_sentence + draft.finding_sentence
                      + draft.action_sentence)
            business_ids = {m.subject_stable_id for m in typed.members
                            if m.subject_stable_id}
            refs = self._all_typed_refs(typed) - business_ids
            for ref in sorted(refs):
                # engineering refs (hashes/ids/contracts/windows) may never
                # enter audience prose; business subject ids are allowed only
                # inside the source_business_identifier part and are excluded
                self.assertNotIn(ref, joined, f"{cid}: {ref}")

    @staticmethod
    def _all_typed_refs(typed: Any) -> set:
        refs = {
            typed.envelope_id, typed.project_ref, typed.run_ref,
            typed.snapshot_ref, typed.mode_contract.mode_contract_version,
            typed.project_scope_binding.scope_binding_id,
            typed.signal_definition.signal_definition_id,
            typed.signal_definition.positive_rule_ref,
            typed.signal_definition.legal_matrix_row_ref,
            typed.legal_matrix_row.row_id,
            typed.stratum.stratum_contract_id,
            typed.comparison_gate.comparison_reference_stable_id,
            typed.audience_text.audience_contract_id,
        }
        refs.update(p.revision_id for p in typed.source_revision_content_pairs)
        refs.update(p.content_hash for p in typed.source_revision_content_pairs)
        refs.update(m.member_ref for m in typed.members)
        refs.update(e.locator_id for e in typed.evidence_refs)
        for window in typed.analysis_windows:
            refs.update((window.analysis_window_stable_id,
                         window.window_instance_id,
                         window.window_definition_id))
        if typed.model_evidence is not None:
            refs.add(typed.model_evidence.model_evidence_id)
        return {r for r in refs if r}


class TestPort8911Stopped(unittest.TestCase):
    def test_tcp_8911_connection_refused(self) -> None:
        refused = False
        try:
            with socket.create_connection(("127.0.0.1", 8911), timeout=1):
                pass
        except OSError:
            refused = True
        self.assertTrue(refused,
                        "port 8911 must stay stopped (connection refused)")


if __name__ == "__main__":
    unittest.main()
