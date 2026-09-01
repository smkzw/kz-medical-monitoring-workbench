"""Focused tests for the deterministic D07 artifact generator and its exact
schema/hash/integrity validation (worker-01 deliverable).

These tests exercise the generator's pure machinery with synthetic mini-artifacts
built on the real worker-02 envelope, plus integration tests that load the real
frozen 144-case catalog and oracle and prove schema/content/semantic/identity/
bijection/leaf/static-independence checks pass up to the explicit missing-manifest
boundary. They never import or implement D07 runtime code and never write into
reviews/.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_d07_challenge_registry as g  # noqa: E402

CONTRACT_PATH = ROOT / "reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md"
CATALOG_PATH = ROOT / "reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json"
ORACLE_PATH = ROOT / "reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json"
MANIFEST_PATH = ROOT / "reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json"


def make_scope(seed: int) -> dict:
    return {
        "accepted_snapshot_ref": "SYN-D07-SNAPSHOT-001",
        "clinical_event_cutoff": "2026-01-31T23:59:59+08:00",
        "ib_rsi_version": "SYN-D07-IB-1",
        "lab_manual_version": "SYN-D07-LABMAN-1",
        "lineage_hash": hashlib.sha256(f"scope-{seed}".encode()).hexdigest(),
        "mapping_version": "SYN-D07-MAP-1",
        "monitoring_mode": "full",
        "project_ref": "SYN-D07-PROJECT",
        "protocol_version": "SYN-D07-PROTOCOL-1",
        "rule_set_versions": {"grade": "SYN-D07-GRADE-1"},
        "run_ref": "SYN-D07-RUN-001",
        "scope_binding_id": f"SYN-D07-SCOPE-{seed:03d}",
        "snapshot_as_of": "2026-01-31T23:59:59+08:00",
        "source_locator_ids": [f"SYN-LOC-SCOPE-{seed:03d}"],
        "source_revision": "SYN-REV-001",
        "unit_dictionary_version": "SYN-D07-UNITDICT-1",
    }


def make_typed_input(seed: int) -> dict:
    sections: dict[str, object] = {key: [] for key in g.TYPED_INPUT_LIST_SECTIONS}
    sections.update({
        "input_schema": g.TYPED_INPUT_SCHEMA,
        "audience_lexicon": {
            "allowed_domain_labels": ["实验室"],
            "allowed_risk_type_labels": ["检验结果待核实"],
            "forbidden_internal_tokens": ["payload"],
            "lexicon_id": f"SYN-LEX-{seed:03d}",
            "required_sentence_patterns": ["basis", "finding", "action"],
            "source_locator_ids": [f"SYN-LOC-LEX-{seed:03d}"],
            "version": "1",
        },
        "priority_policy": {
            "high_priority_clinical_flag_rules": [],
            "machine_close_forbidden_rules": [],
            "ordered_precedence_rule_ids": ["SYN-PRI-1"],
            "policy_id": f"SYN-PRI-{seed:03d}",
            "source_locator_ids": [f"SYN-LOC-PRI-{seed:03d}"],
            "version": "1",
        },
        "run_scope_binding": make_scope(seed),
        "previous_run_scope_binding": None,
        "shared_spine_binding": None,
        "shared_spine_scope_equality_decision": None,
        "observed_results": [{"object_type": "ObservedSafetyResult", "result_id": f"SYN-RES-{seed:03d}"}],
    })
    return sections


def make_case(n: int, entrypoint: str = "d07.safety_evaluator") -> dict:
    typed = make_typed_input(n)
    return {
        "case_id": f"{n:03d}",
        "case_name": f"synthetic-case-{n:03d}",
        "fixture_id": f"d07f-{n:03d}",
        "entrypoint": entrypoint,
        "typed_input": typed,
        "substantive_input_hash": g.sha256_text(g.canonical_json(typed)),
        "positive_mutation_ids": [f"P-MUT-{n:03d}"],
        "negative_mutation_ids": [f"N-MUT-{n:03d}"],
        "input_source_locator_ids": [f"SYN-SRC-{n:03d}"],
    }


def integrity_error_obj(error_type: str, error_object: str) -> dict:
    contract_stage = g.ERROR_TYPE_TO_STAGE[error_type]
    return {
        "error_object": error_object,
        "error_type": error_type,
        "stage": g.INTEGRITY_STAGE_ARTIFACT_NAMES[contract_stage],
    }


def make_expectation(n: int, integrity_error: dict | None = None) -> dict:
    expectation = {
        "case_id": f"{n:03d}",
        "fixture_id": f"d07f-{n:03d}",
        "expected_leaf_set": {
            "l1_disposition": "negative",
            "monitoring_priority": "low",
            "case_assertion_code": f"D07-CH-{n:03d}",
        },
        "expected_trace_leaf_set": {
            "trace.rule_set_id": f"RULE-SET-{n:03d}",
            "trace.unit_ids": ["U-1", "U-2"] if n % 2 == 0 else [],
        },
        "expected_source_leaf_set": {
            "source.source_locator_ids": [f"SYN-SRC-{n:03d}"],
            "source.source_jump_target_pairs": [] if n % 2 == 0 else [
                {"cardinality": "one", "source_object_id": f"OBJ-{n:03d}", "target_kind": "listing_row"}
            ],
        },
        "expected_integrity_error": integrity_error,
    }
    return expectation


def make_binding(n: int, entrypoint: str = "d07.safety_evaluator") -> dict:
    return {
        "case_id": f"{n:03d}",
        "fixture_id": f"d07f-{n:03d}",
        "oracle_case_id": f"{n:03d}",
        "entrypoint": entrypoint,
        "required_assertion_clause_ids": ["d07-assert-001"],
        "required_trace_paths": ["trace.rule_set_id"],
        "required_source_paths": ["source.source_locator_ids"],
        "required_test_id": f"d07-test-{n:03d}",
    }


def make_catalog(count: int = 2, entries: list[dict] | None = None) -> dict:
    cases = entries if entries is not None else [make_case(n) for n in range(1, count + 1)]
    core = {
        "schema_version": g.SCHEMA_VERSION,
        "artifact_kind": "typed_fixture_catalog",
        "contract_semantic_hash": g.CANONICAL_CONTRACT_SEMANTIC_HASH,
        "catalog_id": g.CATALOG_ID,
        "ordered_cases": cases,
        "case_count": len(cases),
    }
    core["content_hash"] = g.content_hash(core)
    return core


def make_oracle(count: int = 2, expectations: list[dict] | None = None) -> dict:
    exps = expectations if expectations is not None else [make_expectation(n) for n in range(1, count + 1)]
    core = {
        "schema_version": g.SCHEMA_VERSION,
        "artifact_kind": "independent_expected_outcome_oracle",
        "contract_semantic_hash": g.CANONICAL_CONTRACT_SEMANTIC_HASH,
        "oracle_id": g.ORACLE_ID,
        "ordered_expectations": exps,
        "case_count": len(exps),
    }
    core["content_hash"] = g.content_hash(core)
    return core


def make_manifest(count: int = 2, bindings: list[dict] | None = None) -> dict:
    binds = bindings if bindings is not None else [make_binding(n) for n in range(1, count + 1)]
    core = {
        "schema_version": g.SCHEMA_VERSION,
        "artifact_kind": "challenge_manifest",
        "contract_semantic_hash": g.CANONICAL_CONTRACT_SEMANTIC_HASH,
        "manifest_id": "medical-monitoring-r4-d07-challenge-manifest",
        "ordered_bindings": binds,
        "case_count": len(binds),
    }
    core["content_hash"] = g.content_hash(core)
    return core


def make_ref_case(n: int, overrides: dict | None = None) -> dict:
    """Synthetic case whose typed_input sections can be overridden while keeping
    the envelope/hash self-consistent (for reference-validation unit tests)."""
    typed = make_typed_input(n)
    for section, value in (overrides or {}).items():
        typed[section] = value
    case = make_case(n)
    case["typed_input"] = typed
    case["substantive_input_hash"] = g.sha256_text(g.canonical_json(typed))
    return case


def ref_expectation(n: int, trace: dict, source: dict, integrity_error: dict | None = None) -> dict:
    """Oracle expectation with caller-supplied trace/source reference leaves."""
    expectation = make_expectation(n, integrity_error=integrity_error)
    expectation["expected_trace_leaf_set"] = trace
    expectation["expected_source_leaf_set"] = source
    return expectation


def audit_synthetic(cases: list[dict], expectations: list[dict]) -> dict:
    """Validate synthetic artifacts and run the non-raising reference audit."""
    catalog = make_catalog(entries=cases)
    oracle = make_oracle(expectations=expectations)
    _, catalog_by_id = g.validate_catalog(catalog, len(cases))
    _, oracle_by_id, _ = g.validate_oracle(oracle, catalog_by_id, len(expectations))
    return g.audit_oracle_reference_bindings(catalog_by_id, oracle_by_id)


def validate_synthetic(cases: list[dict], expectations: list[dict]) -> dict:
    """Validate synthetic artifacts and run the strict reference validation."""
    catalog = make_catalog(entries=cases)
    oracle = make_oracle(expectations=expectations)
    _, catalog_by_id = g.validate_catalog(catalog, len(cases))
    _, oracle_by_id, _ = g.validate_oracle(oracle, catalog_by_id, len(expectations))
    return g.validate_oracle_reference_bindings(catalog_by_id, oracle_by_id)


def run_pipeline(catalog: dict, oracle: dict, manifest: dict, count: int = 2):
    cases, catalog_by_id = g.validate_catalog(catalog, count)
    expectations, oracle_by_id, path_types = g.validate_oracle(oracle, catalog_by_id, count)
    bindings, manifest_by_id = g.validate_manifest(manifest, catalog_by_id, count)
    g.check_required_paths_covered(manifest_by_id, oracle_by_id)
    groups = g.check_duplicate_substantive_input_invariant(catalog_by_id, oracle_by_id)
    registry, rendered, programs = g.build_registry(
        catalog, oracle, manifest, catalog_by_id, oracle_by_id, manifest_by_id,
        groups, path_types, expected_count=count,
    )
    return registry, rendered, programs


def make_base_clause(operator: str, **overrides) -> dict:
    clause = {
        "clause_id": "d07-assert-001",
        "operator": operator,
        "actual_path": "l1_disposition",
        "expected_typed_value": None,
        "expected_ref_path": None,
        "value_type": "string",
        "reason_code": "test",
    }
    clause.update(overrides)
    return clause


def clause_error(clause: dict) -> g.D07ArtifactError | None:
    try:
        g.validate_dsl_clause(clause, "test clause")
        return None
    except g.D07ArtifactError as exc:
        return exc


class CanonicalJsonTests(unittest.TestCase):
    def test_nfc_normalization_of_keys_and_strings(self):
        value = {"caf\u00e9": ["\u00e9", {"\u0041": 1}]}
        rendered = g.canonical_json(value)
        self.assertIn("caf\u00e9", rendered)
        self.assertNotIn("cafe", rendered.replace("\u00e9", ""))
        self.assertEqual(rendered, g.canonical_json({"caf\u00e9": ["\u00e9", {"A": 1}]}))

    def test_keys_sorted_and_arrays_preserved(self):
        value = {"z": 1, "a": [3, 1, 2]}
        self.assertEqual(g.canonical_json(value), '{"a":[3,1,2],"z":1}')

    def test_ensure_ascii_false_keeps_chinese(self):
        rendered = g.canonical_json({"label": "肝酶持续升高"})
        self.assertIn("肝酶持续升高", rendered)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            g.canonical_json({"x": float("nan")})
        with self.assertRaises(ValueError):
            g.canonical_json({"x": [float("inf")]})

    def test_sha256_stable(self):
        self.assertEqual(
            g.sha256_text("abc"),
            hashlib.sha256(b"abc").hexdigest(),
        )


class ContractSnapshotTests(unittest.TestCase):
    def test_tampered_contract_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = CONTRACT_PATH.read_text(encoding="utf-8")
            broken = original.replace("`REVISED_DRAFT_V0_4_FOR_INDEPENDENT_REVIEW`", "`TAMPERED`")
            path = Path(tmp) / "contract.md"
            path.write_text(broken, encoding="utf-8")
            saved = g.CONTRACT
            g.CONTRACT = path
            try:
                with self.assertRaises(g.D07ArtifactError):
                    g.validate_contract()
            finally:
                g.CONTRACT = saved

    def test_tampered_semantic_body_rejected(self):
        text = CONTRACT_PATH.read_text(encoding="utf-8")
        broken = text.replace("五类 L1 disposition", "五类 L1 disposition TAMPERED")
        normalized = g.normalize_contract(broken)
        segment = g.contract_semantic_segment(normalized)
        self.assertNotEqual(g.sha256_text(segment), g.CANONICAL_CONTRACT_SEMANTIC_HASH)

    def test_validate_contract_passes_on_frozen_file(self):
        g.validate_contract()


class DslSchemaTests(unittest.TestCase):
    def test_dsl_schema_exact_keys(self):
        self.assertEqual(
            sorted(g.DSL_SCHEMA),
            sorted(["schema_version", "artifact_kind", "contract_semantic_hash",
                    "dsl_schema_id", "allowed_operators", "closed_clause_schemas",
                    "path_grammar", "value_type_grammar", "forbidden_constructs"]),
        )

    def test_allowed_operators_exact_closed_set(self):
        self.assertEqual(g.DSL_OPERATORS, [
            "exists", "absent", "equals", "not_equals", "in_enum", "decimal_equals",
            "ordered_equals", "set_equals", "hash_equals", "ref_resolves",
            "scope_all_equal", "one_to_one", "count_equals", "error_equals",
        ])

    def test_integrity_stage_order_and_error_enum_exact(self):
        self.assertEqual(g.INTEGRITY_STAGE_ORDER, [
            "schema_parse", "canonical_hash", "artifact_hash", "contract_semantic_hash",
            "scope/cutoff", "authority_version", "correction_chain", "identity/duplicate",
            "foreign_key/bijection", "D05_gate/applicability", "evaluator_admission",
        ])
        self.assertEqual(len(g.INTEGRITY_ERRORS), 15)
        self.assertEqual(g.INTEGRITY_ERRORS[0], "schema_error")
        self.assertEqual(g.INTEGRITY_ERRORS[-1], "evaluator_not_admitted")

    def test_stage_artifact_names_cover_contract_stages(self):
        self.assertEqual(
            set(g.INTEGRITY_STAGE_ARTIFACT_NAMES),
            set(g.INTEGRITY_STAGE_ORDER),
        )
        for contract_stage, artifact_name in g.INTEGRITY_STAGE_ARTIFACT_NAMES.items():
            self.assertNotIn("/", artifact_name)
            self.assertEqual(artifact_name, artifact_name.replace("/", "_"))

    def test_error_type_to_stage_consistent(self):
        self.assertEqual(set(g.ERROR_TYPE_TO_STAGE), set(g.INTEGRITY_ERRORS))
        for error_type, contract_stage in g.ERROR_TYPE_TO_STAGE.items():
            self.assertIn(contract_stage, g.INTEGRITY_STAGE_ORDER)

    def test_entrypoint_enum_closed(self):
        self.assertEqual(g.ENTRYPOINTS, ["d07.safety_evaluator"])

    def test_typed_input_section_enum(self):
        self.assertEqual(len(g.TYPED_INPUT_SECTION_KEYS), 38)
        self.assertIn("input_schema", g.TYPED_INPUT_SECTION_KEYS)
        self.assertIn("run_scope_binding", g.TYPED_INPUT_SECTION_KEYS)
        self.assertEqual(len(set(g.TYPED_INPUT_SECTION_KEYS)), len(g.TYPED_INPUT_SECTION_KEYS))
        self.assertEqual(
            set(g.TYPED_INPUT_SECTION_KEYS),
            set(g.TYPED_INPUT_LIST_SECTIONS) | set(g.TYPED_INPUT_DICT_SECTIONS)
            | set(g.TYPED_INPUT_NULLABLE_DICT_SECTIONS) | {"input_schema"},
        )

    def test_row_distribution_sums_to_144(self):
        total = sum(int(end) - int(start) + 1 for start, end, _ in g.ROW_CATEGORIES)
        self.assertEqual(total, 144)
        self.assertEqual([int(end) - int(start) + 1 for start, end, _ in g.ROW_CATEGORIES],
                         [12, 16, 16, 16, 14, 18, 14, 12, 10, 8, 8])

    def test_every_operator_accepts_valid_clause(self):
        valid: dict[str, dict] = {
            "exists": make_base_clause("exists", expected_typed_value=True, value_type="boolean"),
            "absent": make_base_clause("absent", expected_typed_value=False, value_type="boolean"),
            "equals": make_base_clause("equals", expected_typed_value="positive", value_type="string"),
            "not_equals": make_base_clause("not_equals", expected_typed_value="negative", value_type="string"),
            "in_enum": make_base_clause("in_enum", expected_typed_value=["low", "high"], value_type="string_list"),
            "decimal_equals": make_base_clause("decimal_equals", expected_typed_value="3.2", value_type="decimal_string"),
            "ordered_equals": make_base_clause("ordered_equals", expected_typed_value=["a", "b"], value_type="list"),
            "set_equals": make_base_clause("set_equals", expected_typed_value=["b", "a"], value_type="string_list"),
            "hash_equals": make_base_clause("hash_equals", expected_typed_value="a" * 64, value_type="hash_string"),
            "ref_resolves": make_base_clause("ref_resolves", expected_ref_path="refs.rule_set", value_type="path_string"),
            "scope_all_equal": make_base_clause("scope_all_equal", expected_ref_path="scope.tuple", value_type="path_string"),
            "one_to_one": make_base_clause("one_to_one", expected_ref_path="units[0].risk", value_type="path_string"),
            "count_equals": make_base_clause("count_equals", actual_path="medical_leaf_count", expected_typed_value=3, value_type="integer"),
            "error_equals": make_base_clause("error_equals", actual_path="integrity_error", expected_typed_value="schema_error", value_type="enum_string"),
        }
        for operator, clause in valid.items():
            error = clause_error(clause)
            self.assertIsNone(error, f"{operator}: {error}")

    def test_unknown_operator_rejected(self):
        error = clause_error(make_base_clause("magic"))
        self.assertIsNotNone(error)
        self.assertEqual(error.error_class, "schema_error")

    def test_unknown_extra_key_rejected(self):
        clause = make_base_clause("equals", expected_typed_value="x", value_type="string")
        clause["sneaky"] = True
        self.assertIsNotNone(clause_error(clause))

    def test_missing_required_key_rejected(self):
        clause = make_base_clause("equals", expected_typed_value="x", value_type="string")
        del clause["reason_code"]
        self.assertIsNotNone(clause_error(clause))

    def test_both_expected_fields_rejected(self):
        clause = make_base_clause("equals", expected_typed_value="x", expected_ref_path="refs.x", value_type="string")
        self.assertIsNotNone(clause_error(clause))

    def test_ref_operator_with_typed_value_rejected(self):
        clause = make_base_clause("ref_resolves", expected_typed_value="x", value_type="path_string")
        self.assertIsNotNone(clause_error(clause))

    def test_null_value_with_non_null_value_type_rejected(self):
        clause = make_base_clause("equals", expected_typed_value=None, value_type="string")
        self.assertIsNotNone(clause_error(clause))

    def test_null_value_with_null_value_type_accepted(self):
        clause = make_base_clause("equals", expected_typed_value=None, value_type="null")
        self.assertIsNone(clause_error(clause))

    def test_wrong_value_type_rejected(self):
        clause = make_base_clause("count_equals", expected_typed_value="three", value_type="integer")
        self.assertIsNotNone(clause_error(clause))
        clause = make_base_clause("hash_equals", expected_typed_value="zz" * 32, value_type="hash_string")
        self.assertIsNotNone(clause_error(clause))

    def test_exists_absent_flags_enforced(self):
        self.assertIsNotNone(clause_error(make_base_clause("exists", expected_typed_value=False, value_type="boolean")))
        self.assertIsNotNone(clause_error(make_base_clause("absent", expected_typed_value=True, value_type="boolean")))

    def test_error_equals_requires_closed_enum(self):
        clause = make_base_clause("error_equals", actual_path="integrity_error", expected_typed_value="made_up", value_type="enum_string")
        self.assertIsNotNone(clause_error(clause))

    def test_count_equals_negative_rejected(self):
        clause = make_base_clause("count_equals", actual_path="medical_leaf_count", expected_typed_value=-1, value_type="integer")
        self.assertIsNotNone(clause_error(clause))

    def test_forbidden_constructs_rejected(self):
        for token in ["lambda", "eval(", "import ", "getattr", "os.", "subprocess", "compile(", "__class__"]:
            clause = make_base_clause("equals", expected_typed_value="x", value_type="string",
                                      clause_id=f"d07-assert-{token}")
            self.assertIsNotNone(clause_error(clause), f"forbidden token {token!r} accepted in clause_id")
            clause = make_base_clause("equals", expected_typed_value=token, value_type="string")
            self.assertIsNotNone(clause_error(clause), f"forbidden token {token!r} accepted in expected value")
            clause = make_base_clause("equals", expected_typed_value="x", value_type="string",
                                      actual_path=f"l1.{token}")
            self.assertIsNotNone(clause_error(clause), f"forbidden token {token!r} accepted in path")

    def test_path_grammar_valid(self):
        for path in ["l1_disposition", "l2_counts.risks", "units[0].result", "units.0.action_state",
                     "a.b[2].c[10]", "integrity_error", "medical_leaf_count", "case_assertion_code"]:
            g.validate_path(path, "test")

    def test_path_grammar_invalid(self):
        for path in ["", "l1..disposition", ".l1", "l1.", "l1[0", "l1]", "l1[abc]",
                     "1l1", "l1 .x", "a b", "a['x']", "a.b-c", "a.(b)", "a.0x", "../x"]:
            with self.assertRaises(g.D07ArtifactError, msg=f"path {path!r} should fail"):
                g.validate_path(path, "test")

    def test_leaf_value_type_mapping(self):
        self.assertEqual(g.leaf_value_type(None, "t"), "null")
        self.assertEqual(g.leaf_value_type(True, "t"), "boolean")
        self.assertEqual(g.leaf_value_type(3, "t"), "integer")
        self.assertEqual(g.leaf_value_type("x", "t"), "string")
        self.assertEqual(g.leaf_value_type(["a", "b"], "t"), "string_list")
        self.assertEqual(g.leaf_value_type([1, 2], "t"), "list")
        self.assertEqual(g.leaf_value_type([{"a": 1}], "t"), "list")
        with self.assertRaises(g.D07ArtifactError):
            g.leaf_value_type(1.5, "t")
        with self.assertRaises(g.D07ArtifactError):
            g.leaf_value_type({"nested": 1}, "t")
        with self.assertRaises(g.D07ArtifactError):
            g.leaf_value_type([], "t")
        self.assertEqual(
            g.leaf_value_type([], "t", path="units.0.ids", path_types={"units.0.ids": "string_list"}),
            "string_list",
        )

    def test_dsl_schema_content_hash_exact_keys(self):
        materialized = {**g.DSL_SCHEMA, "content_hash": g.content_hash(g.DSL_SCHEMA)}
        self.assertEqual(sorted(materialized), sorted([
            "schema_version", "artifact_kind", "contract_semantic_hash", "dsl_schema_id",
            "allowed_operators", "closed_clause_schemas", "path_grammar",
            "value_type_grammar", "forbidden_constructs", "content_hash",
        ]))
        self.assertEqual(materialized["content_hash"], g.content_hash(g.DSL_SCHEMA))


class MiniPipelineTests(unittest.TestCase):
    def test_pipeline_accepts_valid_artifacts(self):
        catalog, oracle, manifest = make_catalog(), make_oracle(), make_manifest()
        registry, rendered, programs = run_pipeline(catalog, oracle, manifest)
        self.assertEqual(sorted(registry), sorted(g.REGISTRY_KEYS))
        self.assertTrue(registry["bijection_audit"]["five_way_bijection_passed"])
        self.assertEqual(registry["bijection_audit"]["case_count"], 2)
        self.assertEqual(registry["bijection_audit"]["row_distribution"]["disposition_applicability"], 2)
        self.assertTrue(registry["bijection_audit"]["row_distribution_passed"])
        self.assertEqual(registry["catalog_hash"], catalog["content_hash"])
        self.assertEqual(registry["oracle_hash"], oracle["content_hash"])
        self.assertEqual(registry["manifest_hash"], manifest["content_hash"])
        self.assertEqual(registry["contract_semantic_hash"], g.CANONICAL_CONTRACT_SEMANTIC_HASH)
        self.assertEqual(registry["content_hash"], g.content_hash(registry))
        for row in registry["ordered_registry_core"]:
            self.assertEqual(sorted(row), sorted(g.REGISTRY_CORE_KEYS))
        self.assertEqual(len(programs), 2)
        for program in programs.values():
            for clause in program:
                self.assertEqual(sorted(clause), sorted(g.CLOSED_CLAUSE_SCHEMAS["clause_keys"]))
            self.assertEqual(program[-1]["reason_code"], "no_integrity_error")
            self.assertEqual(program[-1]["operator"], "equals")
            self.assertEqual(program[-1]["expected_typed_value"], None)
            self.assertEqual(program[-1]["value_type"], "null")

    def test_registry_rendering_deterministic(self):
        catalog, oracle, manifest = make_catalog(), make_oracle(), make_manifest()
        first = run_pipeline(copy.deepcopy(catalog), copy.deepcopy(oracle), copy.deepcopy(manifest))
        second = run_pipeline(copy.deepcopy(catalog), copy.deepcopy(oracle), copy.deepcopy(manifest))
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[2], second[2])

    def test_registry_rendering_byte_stable_across_json_roundtrip(self):
        catalog, oracle, manifest = make_catalog(), make_oracle(), make_manifest()
        _, rendered, _ = run_pipeline(catalog, oracle, manifest)
        reparsed = json.loads(rendered)
        rerendered = json.dumps(reparsed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self.assertEqual(rendered, rerendered)

    def test_integrity_error_case_compiles_error_equals(self):
        catalog = make_catalog(entries=[make_case(1), make_case(2)])
        oracle = make_oracle(expectations=[
            make_expectation(1),
            make_expectation(2, integrity_error_obj("scope_mismatch", "observed_results[0]")),
        ])
        manifest = make_manifest()
        registry, _, programs = run_pipeline(catalog, oracle, manifest)
        self.assertEqual(registry["bijection_audit"]["integrity_error_case_count"], 1)
        last = programs["002"][-1]
        self.assertEqual(last["operator"], "error_equals")
        self.assertEqual(last["expected_typed_value"], "scope_mismatch")
        self.assertEqual(last["actual_path"], "integrity_error")

    def test_required_assertion_clause_ids_checked(self):
        catalog, oracle, manifest = make_catalog(), make_oracle(), make_manifest()
        manifest["ordered_bindings"][0]["required_assertion_clause_ids"] = ["d07-assert-999"]
        manifest["content_hash"] = g.content_hash(manifest)
        with self.assertRaises(g.D07ArtifactError) as ctx:
            run_pipeline(catalog, oracle, manifest)
        self.assertEqual(ctx.exception.error_class, "bijection_error")

    def test_duplicate_substantive_input_with_identical_leaves_accepted(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"] = copy.deepcopy(cases[0]["typed_input"])
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[0]["typed_input"]))
        catalog = make_catalog(entries=cases)
        expectations = [make_expectation(1), make_expectation(2)]
        expectations[1]["expected_leaf_set"] = copy.deepcopy(expectations[0]["expected_leaf_set"])
        expectations[1]["expected_trace_leaf_set"] = copy.deepcopy(expectations[0]["expected_trace_leaf_set"])
        expectations[1]["expected_source_leaf_set"] = copy.deepcopy(expectations[0]["expected_source_leaf_set"])
        oracle = make_oracle(expectations=expectations)
        manifest = make_manifest()
        registry, _, _ = run_pipeline(catalog, oracle, manifest)
        self.assertEqual(registry["bijection_audit"]["duplicate_substantive_input_groups"], 1)

    def test_duplicate_substantive_input_with_divergent_leaves_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"] = copy.deepcopy(cases[0]["typed_input"])
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[0]["typed_input"]))
        catalog = make_catalog(entries=cases)
        oracle = make_oracle()  # leaves differ per case -> invariant violation
        manifest = make_manifest()
        with self.assertRaises(g.D07ArtifactError) as ctx:
            run_pipeline(catalog, oracle, manifest)
        self.assertEqual(ctx.exception.error_class, "duplicate_identity")

    def test_case_bound_leaf_exception(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"] = copy.deepcopy(cases[0]["typed_input"])
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[0]["typed_input"]))
        catalog = make_catalog(entries=cases)
        expectations = [make_expectation(1), make_expectation(2)]
        # only the case-bound leaf differs; all other leaves identical
        expectations[1]["expected_leaf_set"] = {
            "l1_disposition": "negative",
            "monitoring_priority": "low",
            "case_assertion_code": "DIFFERENT",
        }
        expectations[1]["expected_trace_leaf_set"] = copy.deepcopy(expectations[0]["expected_trace_leaf_set"])
        expectations[1]["expected_source_leaf_set"] = copy.deepcopy(expectations[0]["expected_source_leaf_set"])
        oracle = make_oracle(expectations=expectations)
        manifest = make_manifest()
        registry, _, _ = run_pipeline(catalog, oracle, manifest)
        self.assertEqual(registry["bijection_audit"]["duplicate_substantive_input_groups"], 1)


class MutationRejectionTests(unittest.TestCase):
    def _expect_rejection(self, catalog=None, oracle=None, manifest=None, error_class=None, count=2):
        catalog = catalog if catalog is not None else make_catalog()
        oracle = oracle if oracle is not None else make_oracle()
        manifest = manifest if manifest is not None else make_manifest()
        with self.assertRaises(g.D07ArtifactError) as ctx:
            run_pipeline(catalog, oracle, manifest, count)
        if error_class is not None:
            self.assertEqual(ctx.exception.error_class, error_class)

    def test_unknown_top_level_key_rejected(self):
        catalog = make_catalog()
        catalog["extra"] = True
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_missing_top_level_key_rejected(self):
        catalog = make_catalog()
        del catalog["catalog_id"]
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_wrong_case_count_rejected(self):
        catalog = make_catalog()
        catalog["case_count"] = 3
        self._expect_rejection(catalog=catalog, error_class="duplicate_identity")

    def test_non_contiguous_case_ids_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["case_id"] = "003"
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="identity_ambiguous")

    def test_duplicate_fixture_id_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["fixture_id"] = "d07f-001"
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="duplicate_identity")

    def test_fixture_id_case_id_mismatch_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["fixture_id"] = "d07f-999"
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="identity_ambiguous")

    def test_unknown_entrypoint_rejected(self):
        cases = [make_case(1), make_case(2, "d07.magic_entry")]
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_stale_catalog_hash_rejected(self):
        catalog = make_catalog()
        catalog["content_hash"] = "0" * 64
        self._expect_rejection(catalog=catalog, error_class="stale_hash")

    def test_stale_substantive_input_hash_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[0]["substantive_input_hash"] = "1" * 64
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="stale_hash")

    def test_bad_typed_input_envelope_rejected(self):
        cases = [make_case(1), make_case(2)]
        typed = cases[1]["typed_input"]
        del typed["trend_rules"]
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(typed))
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_bad_input_schema_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"]["input_schema"] = "d07-typed-input-v2"
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[1]["typed_input"]))
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_scope_binding_bad_lineage_hash_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"]["run_scope_binding"]["lineage_hash"] = "zzz"
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[1]["typed_input"]))
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_nullable_section_wrong_type_rejected(self):
        cases = [make_case(1), make_case(2)]
        cases[1]["typed_input"]["shared_spine_binding"] = []
        cases[1]["substantive_input_hash"] = g.sha256_text(g.canonical_json(cases[1]["typed_input"]))
        catalog = make_catalog(entries=cases)
        catalog["content_hash"] = g.content_hash(catalog)
        self._expect_rejection(catalog=catalog, error_class="schema_error")

    def test_oracle_fixture_mismatch_rejected(self):
        expectations = [make_expectation(1), make_expectation(2)]
        expectations[1]["fixture_id"] = "d07f-999"
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="bijection_error")

    def test_oracle_integrity_stage_type_mismatch_rejected(self):
        expectations = [make_expectation(1), make_expectation(2, {
            "error_object": "observed_results[0]",
            "error_type": "scope_mismatch",
            "stage": "authority_version",
        })]
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="schema_error")

    def test_oracle_integrity_error_outside_enum_rejected(self):
        expectations = [make_expectation(1), make_expectation(2, {
            "error_object": "observed_results[0]",
            "error_type": "not_a_closed_error",
            "stage": "scope_cutoff",
        })]
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="schema_error")

    def test_oracle_integrity_error_object_out_of_range_rejected(self):
        expectations = [make_expectation(1), make_expectation(2, integrity_error_obj("scope_mismatch", "observed_results[9]"))]
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="foreign_key_error")

    def test_oracle_integrity_error_object_bad_path_rejected(self):
        expectations = [make_expectation(1), make_expectation(2, integrity_error_obj("scope_mismatch", "../etc/passwd"))]
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="schema_error")

    def test_oracle_leaf_path_grammar_rejected(self):
        expectations = [make_expectation(1), make_expectation(2)]
        expectations[1]["expected_leaf_set"]["bad path"] = "x"
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="schema_error")

    def test_manifest_duplicate_test_id_rejected(self):
        bindings = [make_binding(1), make_binding(2)]
        bindings[1]["required_test_id"] = "d07-test-001"
        manifest = make_manifest(bindings=bindings)
        self._expect_rejection(manifest=manifest, error_class="duplicate_identity")

    def test_manifest_required_trace_path_not_covered_rejected(self):
        bindings = [make_binding(1), make_binding(2)]
        bindings[0]["required_trace_paths"] = ["missing.path"]
        manifest = make_manifest(bindings=bindings)
        self._expect_rejection(manifest=manifest, error_class="bijection_error")

    def test_manifest_entrypoint_divergence_rejected(self):
        bindings = [make_binding(1), make_binding(2, "d07.priority_resolver")]
        manifest = make_manifest(bindings=bindings)
        self._expect_rejection(manifest=manifest, error_class="evaluator_not_admitted")

    def test_stale_oracle_hash_rejected(self):
        oracle = make_oracle()
        oracle["content_hash"] = "2" * 64
        self._expect_rejection(oracle=oracle, error_class="stale_hash")

    def test_manifest_artifact_kind_mismatch_rejected(self):
        manifest = make_manifest()
        manifest["artifact_kind"] = "challenge_registry"
        manifest["content_hash"] = g.content_hash(manifest)
        self._expect_rejection(manifest=manifest, error_class="schema_error")

    def test_contract_semantic_hash_mismatch_rejected(self):
        catalog = make_catalog()
        catalog["contract_semantic_hash"] = "0" * 64
        self._expect_rejection(catalog=catalog, error_class="semantic_hash_mismatch")

    def test_float_leaf_value_rejected(self):
        expectations = [make_expectation(1), make_expectation(2)]
        expectations[1]["expected_leaf_set"]["ratio_to_uln"] = 3.2
        oracle = make_oracle(expectations=expectations)
        self._expect_rejection(oracle=oracle, error_class="schema_error")


class GeneratorManifestTests(unittest.TestCase):
    def test_generator_manifest_exact_keys_and_self_hash(self):
        source_hash = g.sha256_bytes(Path(ROOT / "tools" / "generate_d07_challenge_registry.py").read_bytes())
        manifest = g.build_generator_manifest(
            source_hash=source_hash,
            input_hashes={"catalog_hash": "0" * 64, "oracle_hash": "1" * 64, "manifest_hash": "2" * 64},
            output_schema_hash="3" * 64,
        )
        self.assertEqual(sorted(manifest), sorted(g.GENERATOR_MANIFEST_KEYS))
        self.assertEqual(manifest["content_hash"], g.content_hash(manifest))
        self.assertEqual(manifest["generator_source_hash"], source_hash)
        self.assertEqual(manifest["integrity_stage_order"], g.INTEGRITY_STAGE_ORDER)
        self.assertEqual(manifest["semantic_hash_range"], g.SEMANTIC_HASH_RANGE)

    def test_generator_source_hash_self_consistent(self):
        source_hash = g.sha256_bytes(Path(ROOT / "tools" / "generate_d07_challenge_registry.py").read_bytes())
        self.assertRegex(source_hash, r"^[0-9a-f]{64}$")

    def test_output_schema_exact(self):
        self.assertEqual(sorted(g.OUTPUT_SCHEMA["top_level_keys"]), sorted(g.REGISTRY_KEYS))
        self.assertEqual(sorted(g.OUTPUT_SCHEMA["registry_core_keys"]), sorted(g.REGISTRY_CORE_KEYS))


class IndependenceAuditTests(unittest.TestCase):
    def test_generator_imports_only_stdlib(self):
        import ast
        source_path = ROOT / "tools" / "generate_d07_challenge_registry.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        for module in imported:
            root_module = module.split(".")[0]
            self.assertIn(root_module, {"hashlib", "json", "os", "re", "sys", "unicodedata", "typing", "pathlib", "__future__", "annotations"},
                          f"generator imports non-stdlib module {module!r}")
        for forbidden in ("from poc", "import poc", "from services", "from packages",
                          "from reviews", "importlib", "__import__", "def run_runtime"):
            self.assertNotIn(forbidden, source, f"generator contains forbidden import pattern {forbidden!r}")

    def test_generator_never_reads_runtime_output(self):
        source = Path(ROOT / "tools" / "generate_d07_challenge_registry.py").read_text(encoding="utf-8")
        self.assertNotIn("def run_runtime", source)
        self.assertNotIn("importlib", source)
        self.assertNotIn("__import__", source)

    def test_dsl_programs_derive_values_only_from_oracle(self):
        # compiler must not invent expected values: every equals clause value must
        # appear verbatim in the oracle leaf sets it is compiled from.
        catalog, oracle, manifest = make_catalog(), make_oracle(), make_manifest()
        _, _, programs = run_pipeline(catalog, oracle, manifest)
        for case_id, program in programs.items():
            expectation = oracle["ordered_expectations"][int(case_id) - 1]
            known_values = set()
            for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                known_values.update(
                    json.dumps(value, sort_keys=True, ensure_ascii=False)
                    for value in expectation[key].values()
                )
            for clause in program:
                if clause["operator"] == "equals" and clause["actual_path"] != "integrity_error":
                    serialized = json.dumps(clause["expected_typed_value"], sort_keys=True, ensure_ascii=False)
                    self.assertIn(serialized, known_values,
                                  f"{case_id} clause invented value {serialized!r}")

    def test_audit_static_independence_disjoint_vocabularies(self):
        catalog, oracle, _ = make_catalog(), make_oracle(), make_manifest()
        result = g.audit_static_independence(catalog, oracle)
        self.assertTrue(result["vocabulary_disjoint"])
        self.assertEqual(result["leaf_root_overlap"], [])
        self.assertEqual(result["leaf_segment_overlap"], [])

    def test_audit_static_independence_rejects_overlap(self):
        catalog = make_catalog()
        # "trace" is a root of the synthetic oracle leaf vocabulary; injecting it
        # as a typed-input key must trip the vocabulary-disjointness check.
        catalog["ordered_cases"][0]["typed_input"]["trace"] = {}
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.audit_static_independence(catalog, make_oracle())
        self.assertEqual(ctx.exception.error_class, "identity_ambiguous")

    def test_artifact_files_are_pure_json(self):
        for name in ("catalog", "oracle"):
            path = CATALOG_PATH if name == "catalog" else ORACLE_PATH
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for token in ("def ", "lambda", "import ", "eval(", "exec("):
                self.assertNotIn(token, text)

    def test_no_runtime_module_imported_by_generator(self):
        spec = importlib.util.find_spec("generate_d07_challenge_registry")
        self.assertIsNotNone(spec)
        self.assertNotIn("poc", str(spec.origin))


@unittest.skipUnless(
    CATALOG_PATH.exists() and ORACLE_PATH.exists(),
    "real worker-02 catalog/oracle not present",
)
class RealArtifactIntegrationTests(unittest.TestCase):
    """Load the real frozen 144-case catalog and oracle and run every generator
    stage up to the explicit missing-manifest boundary."""

    def setUp(self) -> None:
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        self.cases, self.catalog_by_id = g.validate_catalog(self.catalog)
        self.expectations, self.oracle_by_id, self.path_types = g.validate_oracle(
            self.oracle, self.catalog_by_id,
        )

    def test_real_counts_and_identity(self):
        self.assertEqual(self.catalog["case_count"], 144)
        self.assertEqual(len(self.cases), 144)
        self.assertEqual([case["case_id"] for case in self.cases],
                         [f"{n:03d}" for n in range(1, 145)])
        self.assertEqual([e["case_id"] for e in self.expectations],
                         [f"{n:03d}" for n in range(1, 145)])
        self.assertEqual(sorted(self.catalog_by_id), sorted(self.oracle_by_id))
        self.assertEqual(len(self.catalog_by_id), 144)

    def test_real_schema_version_and_ids(self):
        self.assertEqual(self.catalog["schema_version"], "1.0.0")
        self.assertEqual(self.oracle["schema_version"], "1.0.0")
        for case in self.cases:
            self.assertEqual(case["entrypoint"], "d07.safety_evaluator")
            self.assertEqual(case["fixture_id"], f"d07f-{case['case_id']}")
            self.assertEqual(case["typed_input"]["input_schema"], "d07-typed-input-v1")

    def test_real_substantive_input_hashes(self):
        for case in self.cases:
            self.assertEqual(
                case["substantive_input_hash"],
                g.sha256_text(g.canonical_json(case["typed_input"])),
                f"case {case['case_id']} substantive_input_hash mismatch",
            )
        hashes = [case["substantive_input_hash"] for case in self.cases]
        self.assertEqual(len(set(hashes)), 144, "substantive input hashes must be unique")

    def test_real_leaf_paths_and_types(self):
        self.assertTrue(self.path_types)
        for expectation in self.expectations:
            for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                for path, value in expectation[key].items():
                    g.validate_path(path, f"{expectation['case_id']} {key}")
                    g.leaf_value_type(value, f"{expectation['case_id']}", path=path, path_types=self.path_types)

    def test_real_integrity_error_cases(self):
        errored = [e for e in self.expectations if e.get("expected_integrity_error")]
        self.assertEqual(len(errored), 11)
        self.assertEqual(sorted(e["case_id"] for e in errored),
                         ["028"] + [f"{n:03d}" for n in range(119, 129)])
        error_types = {e["expected_integrity_error"]["error_type"] for e in errored}
        self.assertTrue(error_types <= set(g.INTEGRITY_ERRORS))

    def test_real_duplicate_substantive_invariant(self):
        groups = g.check_duplicate_substantive_input_invariant(self.catalog_by_id, self.oracle_by_id)
        self.assertEqual(len(groups), 0)

    def test_real_static_independence(self):
        result = g.audit_static_independence(self.catalog, self.oracle)
        self.assertTrue(result["vocabulary_disjoint"])
        self.assertGreaterEqual(result["oracle_leaf_path_count"], 100)

    def test_real_row_distribution(self):
        distribution = g.row_distribution(self.cases)
        self.assertEqual(list(distribution.values()), [12, 16, 16, 16, 14, 18, 14, 12, 10, 8, 8])

    def test_real_manifest_boundary(self):
        # Worker-03 authored the challenge_manifest and the generator emitted the
        # challenge_registry at the output path. In this final state the path no
        # longer holds the authored manifest, so a registry render must fail
        # closed at the manifest load (schema_error, artifact_kind guard) and the
        # written registry must pass self-consistency.
        if not MANIFEST_PATH.exists():
            self.skipTest("manifest/registry not authored (pre-worker-03 state)")
        existing = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(existing.get("artifact_kind"), "challenge_registry")
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.render_registry()
        self.assertEqual(ctx.exception.error_class, "schema_error")
        g.verify_registry_self_consistency(existing)
        self.assertTrue(existing["bijection_audit"]["five_way_bijection_passed"])

    def test_real_check_inputs_summary(self):
        summary = g.validate_inputs_only(verbose=False)
        self.assertEqual(summary["case_count"], 144)
        self.assertTrue(summary["case_ids_contiguous"])
        self.assertTrue(summary["catalog_oracle_case_bijection"])
        self.assertEqual(summary["duplicate_substantive_input_groups"], 0)
        self.assertEqual(summary["integrity_error_case_count"], 11)
        self.assertEqual(summary["manifest_boundary"], "not_authored")
        self.assertTrue(summary["row_distribution_passed"])

    def test_real_reject_stale_catalog_hash(self):
        mutated = copy.deepcopy(self.catalog)
        mutated["content_hash"] = "0" * 64
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.validate_catalog(mutated)
        self.assertEqual(ctx.exception.error_class, "stale_hash")

    def test_real_reject_stale_oracle_hash(self):
        mutated = copy.deepcopy(self.oracle)
        mutated["content_hash"] = "0" * 64
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.validate_oracle(mutated, self.catalog_by_id)
        self.assertEqual(ctx.exception.error_class, "stale_hash")

    def test_real_reject_wrong_semantic_hash(self):
        mutated = copy.deepcopy(self.catalog)
        mutated["contract_semantic_hash"] = "0" * 64
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.validate_catalog(mutated)
        self.assertEqual(ctx.exception.error_class, "semantic_hash_mismatch")

    def test_real_reject_tampered_integrity_error(self):
        mutated = copy.deepcopy(self.oracle)
        for expectation in mutated["ordered_expectations"]:
            err = expectation.get("expected_integrity_error")
            if err and err["error_type"] not in ("scope_mismatch", "out_of_cutoff"):
                err["stage"] = "scope_cutoff"
                break
        with self.assertRaises(g.D07ArtifactError) as ctx:
            g.validate_oracle(mutated, self.catalog_by_id)
        self.assertEqual(ctx.exception.error_class, "schema_error")


class ReferenceResolverTableTests(unittest.TestCase):
    """The closed resolver table itself: every trace/source leaf path must be
    reference-resolvable or explicitly non-reference; every resolver member
    must address a real typed-input section/field."""

    def test_resolver_counts_closed(self):
        self.assertEqual(len(g.ORACLE_TRACE_REFERENCE_RESOLVERS), 27)
        # source_locator_ids and source.source_jump_target_pairs are resolved by
        # their own closed rules (locator vocabulary / pair resolver), not by
        # the (section, field) map.
        self.assertEqual(len(g.ORACLE_SOURCE_REFERENCE_RESOLVERS), 2)
        self.assertEqual(g.ORACLE_NON_REFERENCE_LEAF_PATHS,
                         frozenset({"trace.unit_algorithm_versions", "source.reverse_binding_count"}))
        self.assertEqual(set(g.SOURCE_JUMP_TARGET_KINDS), {
            "listing_cell", "listing_row", "protocol_clause", "ib_clause", "lab_manual_rule",
            "ae_record", "cm_record", "ip_action", "visit", "examination_report",
        })
        self.assertEqual(set(g.SOURCE_JUMP_PAIR_KEYS),
                         {"cardinality", "source_object_id", "target_kind", "target_object_id"})
        self.assertEqual(set(g.SOURCE_JUMP_CARDINALITIES), {"one", "many"})
        self.assertEqual(set(g.SOURCE_JUMP_TARGET_KIND_RESOLVERS), set(g.SOURCE_JUMP_TARGET_KINDS))

    def test_resolver_members_are_real_typed_input_sections(self):
        members = set(g.ORACLE_REFERENCE_SECTION_FIELDS)
        for resolver in g.SOURCE_JUMP_TARGET_KIND_RESOLVERS.values():
            members.update(resolver)
        for section, field in members:
            self.assertIn(section, g.TYPED_INPUT_SECTION_KEYS,
                          f"resolver member {section}.{field} not a typed-input section")

    def test_trace_and_source_resolvers_are_disjoint_leaf_sets(self):
        self.assertTrue(
            set(g.ORACLE_TRACE_REFERENCE_RESOLVERS).isdisjoint(g.ORACLE_SOURCE_REFERENCE_RESOLVERS),
        )
        self.assertTrue(
            set(g.ORACLE_TRACE_REFERENCE_RESOLVERS).isdisjoint(g.ORACLE_NON_REFERENCE_LEAF_PATHS),
        )
        self.assertTrue(
            set(g.ORACLE_SOURCE_REFERENCE_RESOLVERS).isdisjoint(g.ORACLE_NON_REFERENCE_LEAF_PATHS),
        )

    def test_permitting_error_sets_closed(self):
        self.assertEqual(g.REFERENCE_PERMITTING_INTEGRITY_ERRORS,
                         frozenset({"foreign_key_error", "bijection_error"}))
        self.assertEqual(g.REFERENCE_DUPLICATE_PERMITTING_ERRORS,
                         frozenset({"foreign_key_error", "bijection_error", "duplicate_identity"}))
        for error_type in g.REFERENCE_PERMITTING_INTEGRITY_ERRORS:
            self.assertIn(error_type, g.INTEGRITY_ERRORS)


class ReferenceValidationUnitTests(unittest.TestCase):
    """Synthetic fixtures for every acceptance-P2 defect class plus the
    integrity-fixture permission matrix. Independent of the worker-02 artifacts:
    each defect is constructed and must fail closed."""

    def _audit(self, overrides: dict, trace: dict, source: dict | None = None,
               integrity_error: dict | None = None, seed: int = 1) -> dict:
        source = source if source is not None else {
            "source.source_locator_ids": ["SYN-SRC-001"],
        }
        expectations = [ref_expectation(seed, trace, source, integrity_error)]
        return audit_synthetic([make_ref_case(seed, overrides)], expectations)

    def test_missing_range_ref_fails(self):
        # acceptance P2: case-017 class - oracle expects a range id the typed
        # input does not declare
        audit = self._audit(
            {"reference_range_definitions": [{"range_definition_id": "SYN-RANGE-OTHER"}]},
            {"trace.range_definition_ids": ["SYN-RANGE-SCR-AGE-1"]},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"missing_target": 1})
        self.assertIn("trace.range_definition_ids", audit["failing_problems_by_leaf"])

    def test_missing_obligation_definitions_fails(self):
        audit = self._audit(
            {"action_obligation_definitions": []},
            {"trace.obligation_definition_ids": ["SYN-OBL-REPEAT-1"]},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["failing_problems"][0]["reference"], "trace.obligation_definition_ids")

    def test_stale_conversion_ref_fails(self):
        # acceptance P2: case-028 class - typed conversion is SYN-CONV-ALT-V4,
        # oracle still references SYN-CONV-ALT-1
        audit = self._audit(
            {"unit_conversion_rules": [{"conversion_rule_id": "SYN-CONV-ALT-V4"}]},
            {"trace.unit_conversion_rule_ids": ["SYN-CONV-ALT-1"]},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["failing_problems"][0]["value"], "SYN-CONV-ALT-1")

    def test_missing_carry_forward_ref_fails(self):
        # acceptance P2: case-137 class - oracle expects SYN-CARRY-137 but typed
        # carry_forward_refs is empty
        audit = self._audit(
            {"carry_forward_refs": []},
            {"trace.carry_forward_ref_ids": ["SYN-CARRY-137"]},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["failing_problems"][0]["reference"], "trace.carry_forward_ref_ids")

    def test_unknown_reference_bearing_path_fails_even_under_fk_fixture(self):
        audit = self._audit(
            {},
            {"trace.mystery_ref_ids": ["SYN-X-1"]},
            integrity_error=integrity_error_obj("foreign_key_error", "observed_results[0]"),
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"unknown_reference_path": 1})

    def test_mismatched_object_kind_fails(self):
        # the id exists in the typed input but only under a different object
        # kind: must not resolve as a range
        audit = self._audit(
            {
                "reference_range_definitions": [{"range_definition_id": "SYN-RANGE-1"}],
                "grade_rules": [{"grade_rule_id": "SYN-GR-1"}],
            },
            {"trace.range_definition_ids": ["SYN-GR-1"]},
        )
        self.assertFalse(audit["passed"])
        detail = audit["failing_problems"][0]["detail"]
        self.assertIn("mismatched object kind", detail)

    def test_duplicate_id_in_declared_identity_fails(self):
        audit = self._audit(
            {"observed_results": [
                {"result_id": "SYN-RES-1", "stable_source_record_id": "SYN-REC-DUP"},
                {"result_id": "SYN-RES-2", "stable_source_record_id": "SYN-REC-DUP"},
            ]},
            {"trace.record_envelope_ids": []},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"ambiguous_duplicate_id": 1})
        self.assertEqual(audit["failing_problems"][0]["value"], "SYN-REC-DUP")

    def test_duplicate_id_permitted_under_duplicate_identity_fixture(self):
        audit = self._audit(
            {"observed_results": [
                {"result_id": "SYN-RES-1", "stable_source_record_id": "SYN-REC-DUP"},
                {"result_id": "SYN-RES-2", "stable_source_record_id": "SYN-REC-DUP"},
            ]},
            {"trace.record_envelope_ids": []},
            integrity_error=integrity_error_obj("duplicate_identity", "observed_results[1]"),
        )
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["permitted_problem_count"], 1)

    def test_value_reference_field_duplicates_are_not_ambiguous(self):
        # d05_cutoff_policy_id legitimately repeats across cutoff decisions
        audit = self._audit(
            {"cutoff_decisions": [
                {"cutoff_decision_id": "SYN-CUT-1", "d05_cutoff_policy_id": "SYN-POL-1"},
                {"cutoff_decision_id": "SYN-CUT-2", "d05_cutoff_policy_id": "SYN-POL-1"},
            ]},
            {"trace.d05_cutoff_policy_id": "SYN-POL-1"},
        )
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["problem_count"], 0)

    def test_valid_multi_ref_case_passes(self):
        overrides = {
            "measure_definitions": [{"definition_id": "SYN-D07-M-1"}],
            "reference_range_definitions": [{"range_definition_id": "SYN-RANGE-1"}],
            "grade_rule_sets": [{"rule_set_id": "SYN-GRADESET-1"}],
            "grade_rules": [{"grade_rule_id": "SYN-GR-1"}],
            "monitoring_rules": [{"rule_id": "SYN-MR-1"}],
            "monitoring_predicates": [{"predicate_id": "SYN-PRED-1"}],
            "baseline_rules": [{"rule_id": "SYN-BL-1"}],
            "trend_rules": [{"rule_id": "SYN-TREND-1"}],
            "priority_precedence_rules": [{"precedence_rule_id": "SYN-PPR-1"}],
            "authority_bindings": [{"authority_binding_id": "SYN-AUTH-1"}],
            "cutoff_decisions": [{"cutoff_decision_id": "SYN-CUT-1", "d05_cutoff_policy_id": "SYN-POL-1"}],
            "scope_envelopes": [{"envelope_id": "SYN-ENV-1", "record_id": "SYN-REC-1"}],
            "observed_results": [
                {"result_id": "SYN-RES-1", "stable_source_record_id": "SYN-REC-1"},
            ],
            "visit_refs": [{"visit_ref_id": "SYN-VISIT-1"}],
            "unit_conversion_rules": [{"conversion_rule_id": "SYN-CONV-1"}],
            "action_obligation_definitions": [{"obligation_definition_id": "SYN-OBL-1"}],
            "carry_forward_refs": [{"carry_forward_ref_id": "SYN-CARRY-1"}],
            "producer_consumption_bindings": [{"binding_id": "SYN-PB-1"}],
        }
        trace = {
            "trace.measure_definition_ids": ["SYN-D07-M-1"],
            "trace.range_definition_ids": ["SYN-RANGE-1"],
            "trace.grade_rule_set_ids": ["SYN-GRADESET-1"],
            "trace.grade_rule_ids": ["SYN-GR-1"],
            "trace.monitoring_rule_ids": ["SYN-MR-1"],
            "trace.monitoring_predicate_ids": ["SYN-PRED-1"],
            "trace.baseline_rule_id": "SYN-BL-1",
            "trace.trend_rule_id": "SYN-TREND-1",
            "trace.priority_precedence_rule_ids": ["SYN-PPR-1"],
            "trace.authority_binding_ids": ["SYN-AUTH-1"],
            "trace.cutoff_decision_ids": ["SYN-CUT-1"],
            "trace.d05_cutoff_policy_id": "SYN-POL-1",
            "trace.record_envelope_ids": ["SYN-ENV-1"],
            "trace.visit_ref_ids": ["SYN-VISIT-1"],
            "trace.unit_conversion_rule_ids": ["SYN-CONV-1"],
            "trace.obligation_definition_ids": ["SYN-OBL-1"],
            "trace.carry_forward_ref_ids": ["SYN-CARRY-1"],
            "trace.producer_binding_ids": ["SYN-PB-1"],
            "trace.scope_binding_id": "SYN-D07-SCOPE-001",
        }
        source = {
            "source.producer_binding_ids": ["SYN-PB-1"],
            "source.stable_source_record_ids": ["SYN-REC-1"],
            "source.source_locator_ids": ["SYN-SRC-001"],
            "source.source_jump_target_pairs": [
                {"cardinality": "one", "source_object_id": "SYN-RES-1",
                 "target_kind": "listing_row", "target_object_id": "SYN-REC-1"},
            ],
        }
        audit = self._audit(overrides, trace, source)
        self.assertTrue(audit["passed"], audit["problems"])
        self.assertEqual(audit["problem_count"], 0)
        self.assertGreater(audit["resolved_reference_value_count"], 20)

    def test_null_singletons_are_skipped(self):
        audit = self._audit(
            {},
            {"trace.baseline_rule_id": None, "trace.trend_rule_id": None,
             "trace.shared_spine_binding_id": None},
        )
        self.assertTrue(audit["passed"])

    def test_integrity_fixture_permits_broken_fk(self):
        # foreign_key_error fixture: the oracle asserts the broken FK itself
        audit = self._audit(
            {"reference_range_definitions": [{"range_definition_id": "SYN-RANGE-1"}]},
            {"trace.range_definition_ids": ["SYN-RANGE-BROKEN"]},
            integrity_error=integrity_error_obj("foreign_key_error", "observed_results[0]"),
        )
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["permitted_problem_count"], 1)
        self.assertEqual(audit["failing_problem_count"], 0)

    def test_integrity_fixture_with_unrelated_error_still_fails(self):
        # case-028 semantics: authority_mismatch does not excuse a broken ref
        with self.assertRaises(g.D07ArtifactError) as ctx:
            validate_synthetic(
                [make_ref_case(1, {"unit_conversion_rules": [{"conversion_rule_id": "SYN-CONV-V4"}]})],
                [ref_expectation(
                    1,
                    {"trace.unit_conversion_rule_ids": ["SYN-CONV-1"]},
                    {"source.source_locator_ids": ["SYN-SRC-001"]},
                    integrity_error_obj("authority_mismatch", "authority_bindings[0]"),
                )],
            )
        self.assertEqual(ctx.exception.error_class, "foreign_key_error")
        self.assertEqual(ctx.exception.stage, "foreign_key/bijection")

    def test_strict_validation_raises_on_missing_target(self):
        with self.assertRaises(g.D07ArtifactError) as ctx:
            validate_synthetic(
                [make_ref_case(1, {"reference_range_definitions": [{"range_definition_id": "SYN-RANGE-1"}]})],
                [ref_expectation(
                    1,
                    {"trace.range_definition_ids": ["SYN-RANGE-MISSING"]},
                    {"source.source_locator_ids": ["SYN-SRC-001"]},
                )],
            )
        self.assertEqual(ctx.exception.error_class, "foreign_key_error")

    def test_jump_pair_unknown_target_kind_fails(self):
        audit = self._audit(
            {"observed_results": [{"result_id": "SYN-RES-1"}]},
            {"trace.scope_binding_id": "SYN-D07-SCOPE-001"},
            {
                "source.source_locator_ids": ["SYN-SRC-001"],
                "source.source_jump_target_pairs": [
                    {"cardinality": "one", "source_object_id": "SYN-RES-1",
                     "target_kind": "magic_kind", "target_object_id": "SYN-T-1"},
                ],
            },
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"invalid_source_jump_pair": 1})

    def test_jump_pair_unresolved_target_fails(self):
        audit = self._audit(
            {"observed_results": [{"result_id": "SYN-RES-1"}]},
            {"trace.scope_binding_id": "SYN-D07-SCOPE-001"},
            {
                "source.source_locator_ids": ["SYN-SRC-001"],
                "source.source_jump_target_pairs": [
                    {"cardinality": "one", "source_object_id": "SYN-RES-1",
                     "target_kind": "lab_manual_rule", "target_object_id": "SYN-NO-RULE"},
                ],
            },
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"unmatched_source_jump_target": 1})

    def test_jump_pair_unresolved_source_fails(self):
        audit = self._audit(
            {
                "observed_results": [{"result_id": "SYN-RES-1"}],
                "scope_envelopes": [{"envelope_id": "SYN-ENV-1", "record_id": "SYN-REC-1"}],
            },
            {"trace.scope_binding_id": "SYN-D07-SCOPE-001"},
            {
                "source.source_locator_ids": ["SYN-SRC-001"],
                "source.source_jump_target_pairs": [
                    {"cardinality": "one", "source_object_id": "SYN-RES-999",
                     "target_kind": "listing_row", "target_object_id": "SYN-REC-1"},
                ],
            },
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"unmatched_source_jump_source": 1})

    def test_unmatched_locator_fails(self):
        audit = self._audit(
            {},
            {"trace.scope_binding_id": "SYN-D07-SCOPE-001"},
            {"source.source_locator_ids": ["SYN-LOC-NOT-DECLARED"]},
        )
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["problems_by_kind"], {"unmatched_locator": 1})


@unittest.skipUnless(
    CATALOG_PATH.exists() and ORACLE_PATH.exists(),
    "real worker-02 catalog/oracle not present",
)
class RealReferenceValidationTests(unittest.TestCase):
    """Value-level reference validation against the live frozen artifacts
    (worker-02 corrected catalog/oracle)."""

    def setUp(self) -> None:
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        self.cases, self.catalog_by_id = g.validate_catalog(self.catalog)
        self.expectations, self.oracle_by_id, _ = g.validate_oracle(
            self.oracle, self.catalog_by_id,
        )

    @staticmethod
    def _typed_ids(case: dict, section: str, field: str) -> set[str]:
        values = set()
        obj = case["typed_input"].get(section)
        if isinstance(obj, dict):
            value = obj.get(field)
            if isinstance(value, list):
                values.update(value)
            elif value is not None:
                values.add(value)
        elif isinstance(obj, list):
            for item in obj:
                if not isinstance(item, dict):
                    continue
                value = item.get(field)
                if isinstance(value, list):
                    values.update(value)
                elif value is not None:
                    values.add(value)
        return {value for value in values if isinstance(value, str)}

    def test_real_reference_validation_passes(self):
        audit = g.audit_oracle_reference_bindings(self.catalog_by_id, self.oracle_by_id)
        self.assertTrue(audit["passed"], audit["problems"][:5])
        self.assertEqual(audit["failing_problem_count"], 0)
        self.assertEqual(audit["checked_case_count"], 144)
        self.assertGreater(audit["resolved_reference_value_count"], 7000)
        # the only permitted problems are case 124's intentional duplicate
        # identity fixture (duplicate_identity asserts the broken identity)
        self.assertEqual(audit["permitted_problem_count"], 2)
        self.assertEqual(audit["permitted_integrity_cases"], ["124"])
        self.assertEqual(
            {p["reference"] for p in audit["permitted_problems"]},
            {"observed_results.stable_source_record_id", "scope_envelopes.record_id"},
        )

    def test_real_strict_validation_passes(self):
        audit = g.validate_oracle_reference_bindings(self.catalog_by_id, self.oracle_by_id)
        self.assertTrue(audit["passed"])

    def test_real_resolver_table_closed_over_oracle_vocabulary(self):
        for expectation in self.expectations:
            for key in ("expected_trace_leaf_set", "expected_source_leaf_set"):
                for leaf_path in expectation[key]:
                    self.assertTrue(
                        leaf_path in g.ORACLE_TRACE_REFERENCE_RESOLVERS
                        or leaf_path in g.ORACLE_SOURCE_REFERENCE_RESOLVERS
                        or leaf_path in g.ORACLE_NON_REFERENCE_LEAF_PATHS
                        or leaf_path == "source.source_locator_ids"
                        or leaf_path == "source.source_jump_target_pairs",
                        f"{expectation['case_id']} leaf {leaf_path!r} has no resolver",
                    )

    def test_real_resolver_fields_exist_in_typed_input(self):
        # every resolver (section, field) must address a field the worker-02
        # envelope actually carries (optional fields only exist in some cases)
        seen: dict[str, set[str]] = {}
        for case in self.cases:
            for section in g.TYPED_INPUT_SECTION_KEYS:
                obj = case["typed_input"][section]
                items = obj if isinstance(obj, list) else [obj]
                for item in items:
                    if isinstance(item, dict):
                        seen.setdefault(section, set()).update(item)
        members = set(g.ORACLE_REFERENCE_SECTION_FIELDS)
        for resolver in g.SOURCE_JUMP_TARGET_KIND_RESOLVERS.values():
            members.update(resolver)
        for section, field in members:
            if section == "input_schema":
                continue
            self.assertIn(field, seen.get(section, set()),
                          f"resolver member {section}.{field} not a typed-input field")

    def test_real_acceptance_defect_classes_resolved(self):
        # acceptance P2: case-017 missing age-specific range ref
        e017 = self.oracle_by_id["017"]
        typed_ranges = self._typed_ids(self.catalog_by_id["017"], "reference_range_definitions", "range_definition_id")
        self.assertLessEqual(set(e017["expected_trace_leaf_set"]["trace.range_definition_ids"]), typed_ranges)
        self.assertIn("SYN-RANGE-SCR-AGE-1", typed_ranges)
        # acceptance P2: stale conversion ref (case-028)
        e028 = self.oracle_by_id["028"]
        typed_conversions = self._typed_ids(self.catalog_by_id["028"], "unit_conversion_rules", "conversion_rule_id")
        self.assertLessEqual(set(e028["expected_trace_leaf_set"]["trace.unit_conversion_rule_ids"]), typed_conversions)
        # acceptance P2: missing carry-forward ref (case-137)
        e137 = self.oracle_by_id["137"]
        typed_carry = self._typed_ids(self.catalog_by_id["137"], "carry_forward_refs", "carry_forward_ref_id")
        self.assertLessEqual(set(e137["expected_trace_leaf_set"]["trace.carry_forward_ref_ids"]), typed_carry)
        # acceptance P2: missing obligation definitions
        for expectation in self.expectations:
            obligations = expectation["expected_trace_leaf_set"].get("trace.obligation_definition_ids")
            if not obligations:
                continue
            typed_obligations = self._typed_ids(
                self.catalog_by_id[expectation["case_id"]],
                "action_obligation_definitions", "obligation_definition_id",
            )
            self.assertLessEqual(
                set(obligations), typed_obligations,
                f"case {expectation['case_id']} obligation defs unresolved",
            )

    def test_real_strict_detects_regression(self):
        mutated = copy.deepcopy(self.oracle)
        for expectation in mutated["ordered_expectations"]:
            if expectation["case_id"] == "001":
                expectation["expected_trace_leaf_set"]["trace.obligation_definition_ids"] = ["SYN-OBL-MISSING"]
                break
        mutated["content_hash"] = g.content_hash(mutated)
        with self.assertRaises(g.D07ArtifactError) as ctx:
            _, by_id, _ = g.validate_oracle(mutated, self.catalog_by_id)
            g.validate_oracle_reference_bindings(self.catalog_by_id, by_id)
        self.assertEqual(ctx.exception.error_class, "foreign_key_error")
        self.assertEqual(ctx.exception.stage, "foreign_key/bijection")

    def test_real_check_refs_audit_shape(self):
        audit = g.audit_oracle_reference_bindings(self.catalog_by_id, self.oracle_by_id)
        self.assertEqual(set(audit), {
            "passed", "checked_case_count", "checked_reference_leaf_count",
            "resolved_reference_value_count", "problem_count", "failing_problem_count",
            "permitted_problem_count", "problems", "failing_problems", "permitted_problems",
            "problems_by_kind", "failing_problems_by_leaf", "affected_case_ids",
            "integrity_fixture_case_count", "permitted_integrity_cases",
        })


if __name__ == "__main__":
    unittest.main()
