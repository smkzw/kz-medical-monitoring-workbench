"""R4-D09 runtime closure suite: static import/read closure, fresh
interpreter package import, exact 179/179 oracle parity, emitted-object
validation, audience-label/hidden-count isolation and cache/output freedom.

* static closure: the three runtime modules (``d09_contracts.py`` /
  ``d09_evaluator.py`` / ``d09_projection.py``) contain no artifact/generator/
  test references, no file/service IO, no case/fixture/test identifiers, no
  oracle leaf vocabulary, no audit-metadata access in the semantic modules
  and no display prose in the evaluator (AST-based scan that skips
  docstrings, so boundary declarations in prose are not false positives);
* fresh interpreter: ``import mm_r4`` succeeds with ONLY the R1-R4 source
  roots on ``PYTHONPATH`` (no tests dir, no artifacts), loads no
  ``test_d09*`` module and writes no cache/output files;
* exact 179/179 evaluator oracle parity via the frozen test adapter
  (zero diffs, zero skips);
* every emitted Query draft and R2 handoff across all 179 cases passes
  closed validation;
* forbidden audience labels and engineering identifiers never reach
  user-facing Chinese output; hidden audience counts stay isolated from
  every payload;
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

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d09_contracts as _dc  # noqa: E402
from mm_r4 import d09_evaluator as _ev  # noqa: E402
from mm_r4 import d09_projection as _pr  # noqa: E402

from test_d09_adapter import (  # noqa: E402
    CASE_COUNT,
    audit_all_cases,
    load_artifacts,
    run_case,
)
from mm_r4.d09_projection import (  # noqa: E402
    project_d09_run,
    validate_d09_r2_handoff,
    validate_query_draft,
)

_RUNTIME_PATHS = (
    _R4_SRC / "mm_r4" / "d09_contracts.py",
    _R4_SRC / "mm_r4" / "d09_evaluator.py",
    _R4_SRC / "mm_r4" / "d09_projection.py",
)

# Tokens forbidden in the CODE of all three runtime modules (docstrings
# excluded): artifact/generator/test references, file/service IO and oracle
# leaf vocabulary.
_FORBIDDEN_CODE_TOKENS = (
    "catalog", "oracle", "registry", "quota", "generator",
    "typed_fixture_catalog", "expected_outcome_oracle", "challenge_manifest_registry",
    "partition_quota_manifest", "generate_d09", "test_d09", "artifact_generator",
    "load_artifacts", "audit_all_cases", "ordered_expectations", "expected_leaf",
    "open(", "read_text", "read_bytes", "json.load", "urllib", "requests",
    "subprocess", "socket", "8911", "print(",
)
_FORBIDDEN_ID_RE = re.compile(r"D09-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+")

# Audit/test-metadata tokens forbidden in the SEMANTIC modules
# (evaluator + projection); they may legitimately exist as schema in
# d09_contracts.py.
_SEMANTIC_ONLY_TOKENS = (
    "mutation", "anti_overfit", "base_fixture", "variant_id",
    "mutation_class", "fixture_id", "case_id", "desc",
)

# Natural-language / display-label tokens forbidden in the evaluator.
_FORBIDDEN_PROSE_TOKENS = (
    "正式事实", "候选信号", "已记录事项", "只读", "通用风险点",
    "请核实", "中心重复风险模式", "受影响受试者", "事件 {n}",
)

# Forbidden audience labels; in the projection they may appear only inside
# the closed declaration tuple (at most once each).
_PROJECTION_LABELS = ("正式事实", "候选信号", "已记录事项", "只读", "通用风险点")

_EXPECTED_D09_EXPORTS = (
    "D09_SCHEMA_VERSION", "D09_TYPED_INPUT_SCHEMA", "D09_UNIT_ALGORITHM_VERSION",
    "D09_PUBLIC_IDENTITY_VERSION", "D09_DOMAIN_ID", "D09ContractError",
    "D09TypedInput", "D09UnitResult", "D09TraceEdge", "D09RunResult",
    "d09_normalize_nfc", "d09_canonical_json", "d09_sha256_text",
    "d09_content_hash", "d09_unit_stable_core", "validate_d09_typed_input",
    "evaluate_d09", "D09ProjectionError", "D09AudienceProjection",
    "D09ProjectionCountSurface", "D09RiskMarker", "D09HotspotProjection",
    "D09DeepLinkTarget", "D09QueryDraft", "D09R2RiskHandoff",
    "D09ProjectionBundle", "UNAVAILABLE_SOURCE_ZH",
    "build_d09_audience_projection", "build_d09_count_surface",
    "build_d09_risk_marker", "build_d09_hotspots", "build_d09_deep_links",
    "build_d09_query_draft", "validate_d09_query_draft",
    "d09_public_risk_identity", "d09_evaluation_content_identity",
    "build_d09_r2_handoff", "validate_d09_r2_handoff", "project_d09_run",
)


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


def _code_text(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return "\n".join(_iter_code_strings(tree) + _iter_code_names(tree))


class TestStaticRuntimeClosure(unittest.TestCase):
    def test_runtime_code_never_reads_acceptance_artifacts(self) -> None:
        for path in _RUNTIME_PATHS:
            code = _code_text(path)
            for token in _FORBIDDEN_CODE_TOKENS:
                self.assertNotIn(token, code,
                                 f"{path.name} code contains {token!r}")
            self.assertIsNone(_FORBIDDEN_ID_RE.search(code),
                              f"{path.name} code contains a case/fixture id")

    def test_semantic_modules_never_access_audit_metadata(self) -> None:
        for path in (_RUNTIME_PATHS[1], _RUNTIME_PATHS[2]):
            code = _code_text(path)
            for token in _SEMANTIC_ONLY_TOKENS:
                self.assertNotIn(token, code,
                                 f"{path.name} code contains audit token "
                                 f"{token!r}")

    def test_evaluator_free_of_display_prose(self) -> None:
        code = _code_text(_RUNTIME_PATHS[1])
        for token in _FORBIDDEN_PROSE_TOKENS:
            self.assertNotIn(token, code,
                             f"d09_evaluator.py code contains prose "
                             f"{token!r}")

    def test_projection_labels_declared_exactly_once(self) -> None:
        code = _code_text(_RUNTIME_PATHS[2])
        for label in _PROJECTION_LABELS:
            self.assertLessEqual(code.count(label), 1,
                                 f"projection label {label!r} appears "
                                 f"outside its closed declaration")

    def test_runtime_modules_import_without_artifacts(self) -> None:
        import importlib
        for module_name in ("mm_r4.d09_contracts", "mm_r4.d09_evaluator",
                            "mm_r4.d09_projection"):
            module = importlib.import_module(module_name)
            self.assertIsNotNone(module)


class TestPublicExports(unittest.TestCase):
    def test_exact_d09_all_membership(self) -> None:
        import mm_r4
        exported = set(mm_r4.__all__)
        for name in _EXPECTED_D09_EXPORTS:
            self.assertIn(name, exported, f"{name} missing from __all__")
        # no stray D09 names beyond the intended surface
        d09_named = {name for name in exported if "d09" in name.lower()}
        self.assertLessEqual(d09_named, set(_EXPECTED_D09_EXPORTS),
                             d09_named - set(_EXPECTED_D09_EXPORTS))
        # test adapters / frozen artifacts are never exported
        for name in ("test_d09_adapter", "load_artifacts", "audit_all_cases",
                     "catalog", "oracle", "registry", "quota"):
            self.assertNotIn(name, exported)

    def test_representative_export_object_identity(self) -> None:
        import mm_r4
        pairs = (
            ("D09ContractError", _dc.D09ContractError),
            ("D09TypedInput", _dc.D09TypedInput),
            ("D09RunResult", _dc.D09RunResult),
            ("D09UnitResult", _dc.D09UnitResult),
            ("d09_content_hash", _dc.d09_content_hash),
            ("d09_unit_stable_core", _dc.d09_unit_stable_core),
            ("validate_d09_typed_input", _dc.validate_typed_input),
            ("evaluate_d09", _ev.evaluate),
            ("D09ProjectionBundle", _pr.D09ProjectionBundle),
            ("build_d09_query_draft", _pr.build_d09_query_draft),
            ("validate_d09_query_draft", _pr.validate_query_draft),
            ("project_d09_run", _pr.project_d09_run),
            ("build_d09_r2_handoff", _pr.build_d09_r2_handoff),
            ("validate_d09_r2_handoff", _pr.validate_d09_r2_handoff),
            ("d09_public_risk_identity", _pr.d09_public_risk_identity),
        )
        for name, module_object in pairs:
            self.assertIs(getattr(mm_r4, name), module_object, name)


class TestFreshInterpreterImport(unittest.TestCase):
    def test_package_import_fresh_interpreter_no_cache_no_output(self) -> None:
        code = (
            "import sys\n"
            "import mm_r4\n"
            "expected = " + repr(list(_EXPECTED_D09_EXPORTS)) + "\n"
            "missing = [n for n in expected if n not in mm_r4.__all__]\n"
            "assert not missing, missing\n"
            "assert mm_r4.evaluate_d09 and mm_r4.validate_d09_typed_input\n"
            "bad = [m for m in sys.modules if m.startswith('test_d09')]\n"
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
                capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0,
                             f"fresh interpreter failed:\n{result.stdout}\n"
                             f"{result.stderr}")
            self.assertIn("FRESH-OK", result.stdout)
            leftovers = list(Path(tmp).iterdir())
            self.assertEqual(leftovers, [],
                             f"fresh interpreter wrote files: {leftovers}")


class TestOracleParityClosure(unittest.TestCase):
    def test_179_case_oracle_parity_exact(self) -> None:
        problems = audit_all_cases()
        self.assertEqual(problems, {},
                         f"{len(problems)} cases with leaf diffs: "
                         f"{sorted(problems)[:5]}")
        catalog, _oracle, _registry, _quota = load_artifacts()
        self.assertEqual(len(catalog["cases"]), CASE_COUNT)

    def test_all_emitted_query_and_r2_objects_validate(self) -> None:
        catalog, _oracle, _registry, _quota = load_artifacts()
        drafts = 0
        for case in catalog["cases"]:
            typed, result = run_case(case)
            bundle = project_d09_run(typed, result)
            if result.query_count == 1:
                self.assertIsNotNone(bundle.query_draft, case["case_id"])
                assert bundle.query_draft is not None
                validation = validate_query_draft(bundle.query_draft,
                                                  typed, result)
                self.assertTrue(validation["valid"],
                                f"{case['case_id']}: {validation['reasons']}")
                drafts += 1
            else:
                self.assertIsNone(bundle.query_draft, case["case_id"])
            if bundle.r2_handoff is not None:
                validation = validate_d09_r2_handoff(
                    bundle.r2_handoff, typed, result)
                self.assertTrue(validation["valid"],
                                f"{case['case_id']}: {validation['reasons']}")
        self.assertEqual(drafts, 65)


class TestAudienceIsolationClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, _oracle, _registry, _quota = load_artifacts()
        cls.bundles = {}
        for case in cls.catalog["cases"]:
            typed, result = run_case(case)
            cls.bundles[case["case_id"]] = (typed, result,
                                            project_d09_run(typed, result))

    def test_forbidden_audience_labels_absent_from_outputs(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            counts = bundle.counts
            texts = [
                counts.individual_risk_zh, counts.affected_subjects_zh,
                counts.event_count_zh, counts.center_pattern_count_zh,
                counts.coverage_zh, counts.coverage_state_zh,
                counts.disposition_zh, counts.denominator_zh or "",
                counts.rate_zh or "", bundle.audience.disposition_zh,
            ]
            if counts.lifecycle_zh:
                texts.append(counts.lifecycle_zh)
            if bundle.query_draft is not None:
                texts.extend((bundle.query_draft.basis_sentence,
                              bundle.query_draft.finding_sentence,
                              bundle.query_draft.action_sentence))
            for link in bundle.deep_links:
                if link.unavailable_message:
                    texts.append(link.unavailable_message)
            joined = "".join(texts)
            for label in _PROJECTION_LABELS:
                self.assertNotIn(label, joined, cid)

    def test_engineering_ids_absent_from_query_prose(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            draft = bundle.query_draft
            if draft is None:
                continue
            joined = (draft.basis_sentence + draft.finding_sentence
                      + draft.action_sentence)
            definition = typed.pattern_definition
            for ref in (definition.pattern_definition_id,
                        definition.positive_rule_ref,
                        definition.center_query_policy_id,
                        typed.mode_contract_version):
                self.assertNotIn(ref, joined, cid)
            for window in typed.analysis_windows:
                self.assertNotIn(window.analysis_window_stable_id, joined, cid)
                self.assertNotIn(window.window_instance_id, joined, cid)
            for member in (typed.subject_risk_members + typed.gap_members
                           + typed.change_ledger_members):
                self.assertNotIn(member.member_id, joined, cid)
            for revision in typed.source_revision_set:
                self.assertNotIn(revision, joined, cid)

    def test_hidden_audience_counts_isolated(self) -> None:
        for cid, (typed, result, bundle) in self.bundles.items():
            hidden = set(result.hidden_member_refs)
            if not hidden:
                continue
            self.assertFalse(hidden & set(bundle.audience.projectable_member_refs),
                             cid)
            self.assertEqual(bundle.audience.hidden_member_count,
                             len(hidden), cid)
            self.assertEqual(bundle.counts.hidden_member_count, len(hidden),
                             cid)
            if bundle.query_draft is not None:
                self.assertFalse(hidden & set(bundle.query_draft.member_refs),
                                 cid)
            if bundle.risk_marker is not None:
                self.assertFalse(hidden & set(bundle.risk_marker.member_refs),
                                 cid)
            for hotspot in bundle.hotspots:
                refs = set(hotspot.member_risk_refs) | set(hotspot.gap_member_refs)
                self.assertFalse(hidden & refs, cid)
            for link in bundle.deep_links:
                self.assertNotIn(link.member_ref, hidden, cid)
            # visible counts never exceed the evaluation-plane raw counts
            self.assertLessEqual(bundle.counts.visible_individual_risk_count,
                                 result.individual_risk_count, cid)
            self.assertLessEqual(bundle.counts.visible_affected_subject_count,
                                 result.affected_subject_count, cid)


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
