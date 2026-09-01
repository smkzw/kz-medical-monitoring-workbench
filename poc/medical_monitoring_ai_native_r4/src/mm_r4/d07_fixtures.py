"""R4-D07 test-side fixture adapter, DSL interpreter and mutation operators.

Test-only support for the frozen 144-case D07 challenge matrix.  This module
mirrors the established D06 convention (``efficacy_fixtures.py``): it lives in
``src/mm_r4`` but is test-side infrastructure, never imported by the runtime
(``d07_safety`` / ``d07_safety_evaluator``).  It reads the frozen catalog /
oracle / registry under ``reviews/`` and re-compiles the frozen assertion DSL
programs with the frozen artifact generator, then interprets them against the
runtime's raw output root.

Boundaries honoured here:

* the runtime never imports this module and never reads the frozen artifacts
  (enforced by the static closure audit in ``test_d07_challenge_matrix.py``);
* no expected value is invented: every oracle leaf, trace/source leaf and
  integrity-error pin is transcribed from the frozen oracle; the compiled DSL
  program is a pure function of the oracle leaves and must reproduce the
  registry ``assertion_program_hash`` exactly;
* mutation operators are deterministic typed-input transformations: negative
  ids tamper the class-named semantic field (without rehashing unless the id
  *is* the synchronized-rewrite class), positive ids apply provably inert
  changes, and the suite asserts fail-closed / output-identical respectively.

All data is synthetic and offline.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_POC_ROOT = Path(__file__).resolve().parents[4]
_REVIEWS = _POC_ROOT / "reviews"
_TOOLS = _POC_ROOT / "tools"

CATALOG_PATH = _REVIEWS / "medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json"
ORACLE_PATH = _REVIEWS / "medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json"
REGISTRY_PATH = _REVIEWS / "medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json"

# Frozen contract identity (v0.4, accepted freeze record).
FROZEN_CONTRACT_SEMANTIC_HASH = (
    "6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a"
)
FROZEN_SCHEMA_VERSION = "1.0.0"
EXPECTED_CASE_COUNT = 144
ENTRYPOINT = "d07.safety_evaluator"

# Frozen project-rule parameter (typed baseline magnitude, contract §7.2):
# the relative deviation below which a post-baseline point is a
# baseline-confirmation.  The frozen catalog was authored without the typed
# ``baseline_rules.baseline_confirmation_relative_deviation`` field; this
# adapter binds the frozen value into each baseline rule (rehashed) so the
# runtime reads it typed and fails closed when it is absent.  The frozen
# catalog / oracle / registry / generator stay unchanged.
FROZEN_BASELINE_CONFIRMATION_RELATIVE_DEVIATION = "0.02"

# Frozen project-rule parameter (typed safety-critical magnitude threshold,
# contract §9 "受试者权益/安全关键阈值"): the 5xULN threshold behind the
# ``high_priority_clinical_flag`` precedence trigger.  Bound into the
# declared flag precedence rule (rehashed); absent -> fail-closed.
FROZEN_SAFETY_CRITICAL_RATIO_THRESHOLD = "5"

# Documented runtime-output contract leaves (D07_ROOT_OUTPUT_LEAVES): the
# oracle leaf sets do not contain them; they are the only permitted extras on
# the flattened runtime root.
ROOT_SYNTHETIC_LEAVES = frozenset(
    {"integrity_error", "medical_leaf_count", "trace_leaf_count", "source_leaf_count"}
)

# Fail-closed shell emitted by the runtime on pre-evaluator integrity failure
# (no medical/priority/risk/Query/Journey leaves).
FAIL_CLOSED_SHELL_LEAVES = frozenset(
    {
        "all_units_disposed", "domain_complete", "expected_set_reconciled",
        "l0_complete", "not_evaluable_count", "open_d05_gate_count",
        "unit_count", "unresolved_identity_count",
    }
)

# Closed DSL operator set (frozen v0.4 §14.1).
DSL_OPERATORS: Tuple[str, ...] = (
    "exists", "absent", "equals", "not_equals", "in_enum", "decimal_equals",
    "ordered_equals", "set_equals", "hash_equals", "ref_resolves",
    "scope_all_equal", "one_to_one", "count_equals", "error_equals",
)
FORBIDDEN_CONSTRUCTS: Tuple[str, ...] = (
    "lambda", "eval(", "exec(", "compile(", "import ", "from ", "globals(",
    "locals(", "getattr", "setattr", "__class__", "builtins", "subprocess",
    "os.", "sys.", "socket", "http://", "https://", "file://", "open(",
    "read_text", "write_text",
)


# ---------------------------------------------------------------------------
# Frozen artifact loaders
# ---------------------------------------------------------------------------

def load_frozen_catalog() -> Dict[str, Any]:
    with open(CATALOG_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def load_frozen_oracle() -> Dict[str, Any]:
    with open(ORACLE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def load_frozen_registry() -> Dict[str, Any]:
    with open(REGISTRY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    """Frozen canonical JSON (NFC, sorted keys, compact) -- byte-identical to
    the runtime's ``d07_canonical_json`` and the generator's ``canonical_json``
    (verified: substantive hashes match across all 144 cases)."""
    import unicodedata

    def _norm(v: Any) -> Any:
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        if isinstance(v, dict):
            return {_norm(k): _norm(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_norm(item) for item in v]
        return v

    return json.dumps(
        _norm(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def content_hash(value: Any) -> str:
    return _sha256_text(canonical_json(value))


# ---------------------------------------------------------------------------
# Frozen identity verification (registry is the frozen cross-check)
# ---------------------------------------------------------------------------

def _inject_frozen_rule_parameters(typed_input: Dict[str, Any]) -> None:
    """Bind the frozen typed baseline magnitude and the frozen safety-critical
    threshold into a deep-copied typed input (the synthetic overlay), rehashing
    the affected rules so they stay content-consistent with the runtime's
    canonical-hash stage.  Never mutates the frozen catalog view."""
    for rule in typed_input.get("baseline_rules", []):
        if isinstance(rule, dict) and "baseline_confirmation_relative_deviation" not in rule:
            rule["baseline_confirmation_relative_deviation"] = (
                FROZEN_BASELINE_CONFIRMATION_RELATIVE_DEVIATION
            )
            rehash_object(rule, "hash")
    policy = typed_input.get("priority_policy")
    flag_ids = (policy or {}).get("high_priority_clinical_flag_rules") or []
    for rule in typed_input.get("priority_precedence_rules", []):
        if (isinstance(rule, dict)
                and rule.get("trigger") == "high_priority_clinical_flag"
                and rule.get("precedence_rule_id") in flag_ids
                and "safety_critical_ratio_threshold" not in rule):
            rule["safety_critical_ratio_threshold"] = (
                FROZEN_SAFETY_CRITICAL_RATIO_THRESHOLD
            )
            rehash_object(rule, "hash")


def build_indexes(
    catalog: Optional[Mapping[str, Any]] = None,
    oracle: Optional[Mapping[str, Any]] = None,
    registry: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Load (if needed) and index the three frozen artifacts.

    The frozen catalog view is verified and returned unchanged (``catalog`` /
    ``frozen_catalog``).  A deep-copied, clearly-named synthetic overlay binds
    the frozen typed rule parameters into the runtime inputs and carries its
    own ``overlay_substantive_hashes``, kept separate from the frozen
    ``substantive_input_hash`` / ``frozen_substantive_hashes``.  The runtime
    consumes only the overlay cases (``cases_by_id`` /
    ``overlay_cases_by_id``).
    """
    catalog = catalog if catalog is not None else load_frozen_catalog()
    oracle = oracle if oracle is not None else load_frozen_oracle()
    registry = registry if registry is not None else load_frozen_registry()

    for artifact in (catalog, oracle, registry):
        assert artifact["schema_version"] == FROZEN_SCHEMA_VERSION
        assert artifact["contract_semantic_hash"] == FROZEN_CONTRACT_SEMANTIC_HASH

    assert catalog["artifact_kind"] == "typed_fixture_catalog"
    assert oracle["artifact_kind"] == "independent_expected_outcome_oracle"
    assert registry["artifact_kind"] == "challenge_registry"
    assert catalog["case_count"] == EXPECTED_CASE_COUNT
    assert oracle["case_count"] == EXPECTED_CASE_COUNT
    assert len(catalog["ordered_cases"]) == EXPECTED_CASE_COUNT
    assert len(oracle["ordered_expectations"]) == EXPECTED_CASE_COUNT
    assert len(registry["ordered_registry_core"]) == EXPECTED_CASE_COUNT

    # Frozen registry cross hashes must match the live artifacts.
    assert registry["catalog_hash"] == catalog["content_hash"]
    assert registry["oracle_hash"] == oracle["content_hash"]

    frozen_cases_by_id = {c["case_id"]: c for c in catalog["ordered_cases"]}
    expectations_by_id = {e["case_id"]: e for e in oracle["ordered_expectations"]}
    registry_core = {r["case_id"]: r for r in registry["ordered_registry_core"]}

    expected_ids = [f"{n:03d}" for n in range(1, EXPECTED_CASE_COUNT + 1)]
    assert list(frozen_cases_by_id) == expected_ids
    assert list(expectations_by_id) == expected_ids
    assert list(registry_core) == expected_ids

    # Five-way bijection columns per the registry bijection audit, on the
    # frozen catalog view (never the overlay).
    frozen_substantive_hashes: Dict[str, str] = {}
    for case_id in expected_ids:
        case = frozen_cases_by_id[case_id]
        exp = expectations_by_id[case_id]
        row = registry_core[case_id]
        assert case["fixture_id"] == exp["fixture_id"] == row["fixture_id"]
        assert row["oracle_case_id"] == case_id
        assert row["manifest_case_id"] == case_id
        assert row["test_id"] == f"d07-test-{case_id}"
        assert case["entrypoint"] == ENTRYPOINT == row["entrypoint"]
        # The frozen typed input is the substantive input: its content address
        # must equal the catalog and registry hashes.
        assert content_hash(case["typed_input"]) == case["substantive_input_hash"]
        assert row["substantive_input_hash"] == case["substantive_input_hash"]
        frozen_substantive_hashes[case_id] = case["substantive_input_hash"]

    # Synthetic overlay: a deep copy of the frozen catalog with the frozen
    # typed rule parameters bound in.  The overlay keeps its own substantive
    # hashes, distinct from the frozen ones; the frozen catalog stays intact.
    overlay_catalog = copy.deepcopy(catalog)
    # The overlay is a derived synthetic artifact, not the frozen catalog.
    # Preserve the frozen address under an explicit name and never expose it
    # as if it described the overlay's mutated content.
    overlay_catalog["frozen_content_hash"] = overlay_catalog.pop("content_hash")
    overlay_cases_by_id = {c["case_id"]: c for c in overlay_catalog["ordered_cases"]}
    overlay_substantive_hashes: Dict[str, str] = {}
    for case_id in expected_ids:
        case = overlay_cases_by_id[case_id]
        _inject_frozen_rule_parameters(case["typed_input"])
        overlay_substantive_hashes[case_id] = content_hash(case["typed_input"])
        case["substantive_input_hash"] = overlay_substantive_hashes[case_id]
    overlay_catalog["overlay_content_hash"] = content_hash(overlay_catalog)

    return {
        "frozen_catalog": catalog,
        "overlay_catalog": overlay_catalog,
        # Backward-compatible keys: ``catalog`` is the frozen catalog (never
        # the overlay); ``cases_by_id`` is the overlay the runtime consumes.
        "catalog": catalog,
        "cases_by_id": overlay_cases_by_id,
        "frozen_cases_by_id": frozen_cases_by_id,
        "overlay_cases_by_id": overlay_cases_by_id,
        "frozen_substantive_hashes": frozen_substantive_hashes,
        "overlay_substantive_hashes": overlay_substantive_hashes,
        "oracle": oracle,
        "registry": registry,
        "expectations_by_id": expectations_by_id,
        "registry_core": registry_core,
    }


# ---------------------------------------------------------------------------
# Leaf flattening and exact oracle comparison (v0.4 §14.1)
# ---------------------------------------------------------------------------

def flatten_root(root: Mapping[str, Any]) -> Dict[str, Any]:
    """Flatten the runtime raw root with the runtime's own semantics: dict
    values recurse, every other value (including lists) is a leaf.  This is
    exactly ``D07SafetyEvaluator._flatten`` and matches the frozen oracle
    dotted-path vocabulary (``units.0.action_state`` ...)."""
    out: Dict[str, Any] = {}

    def walk(value: Any, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{prefix}.{key}" if prefix else str(key))
        else:
            out[prefix] = value

    walk(root)
    return out


def oracle_leaf_union(expectation: Mapping[str, Any]) -> Dict[str, Any]:
    """Merge expected_leaf_set + expected_trace_leaf_set + expected_source_leaf_set."""
    merged: Dict[str, Any] = {}
    for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
        for path, value in expectation[key].items():
            if path in merged:
                raise AssertionError(f"oracle leaf path {path!r} appears in two sets")
            merged[path] = value
    return merged


def exact_leaf_check(
    flat: Mapping[str, Any], expectation: Mapping[str, Any]
) -> Tuple[List[str], List[str], List[str], bool]:
    """Exact leaf bijection vs the frozen oracle.

    Returns ``(missing, extra, mismatches, integrity_ok)``.  Extra leaves are
    only permitted if they are the documented root-synthetic leaves.  The
    integrity outcome must match ``expected_integrity_error.error_type``."""
    expected = oracle_leaf_union(expectation)
    missing = sorted(set(expected) - set(flat))
    extra = sorted((set(flat) - set(expected)) - ROOT_SYNTHETIC_LEAVES)
    mismatches = sorted(
        path for path in set(expected) & set(flat) if expected[path] != flat[path]
    )
    pinned = expectation.get("expected_integrity_error")
    actual_error = flat.get("integrity_error")
    if pinned is None:
        integrity_ok = actual_error is None
    else:
        integrity_ok = pinned.get("error_type") == actual_error
    return missing, extra, mismatches, integrity_ok


def fail_closed_root(root: Mapping[str, Any]) -> bool:
    """True iff the run failed closed: a pre-evaluator integrity error was
    emitted and no medical/priority/risk/Query/Journey leaves exist."""
    return (
        root.get("integrity_error") is not None
        and root.get("unit_count") == 0
        and not root.get("units")
        and "ownership" not in root
        and "query" not in root
        and "journey" not in root
        and root.get("medical_leaf_count") == len(FAIL_CLOSED_SHELL_LEAVES)
    )


# ---------------------------------------------------------------------------
# Frozen DSL: compile (via the frozen generator) + interpret
# ---------------------------------------------------------------------------

def _load_generator():
    """Import the frozen artifact generator (test-side authority) by file
    path, without mutating ``sys.path``."""
    import importlib.util

    target = _TOOLS / "generate_d07_challenge_registry.py"
    spec = importlib.util.spec_from_file_location(
        "generate_d07_challenge_registry", target)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def compile_frozen_program(
    expectation: Mapping[str, Any], oracle: Optional[Mapping[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """Re-compile the frozen assertion DSL program for one case from oracle
    leaves only, and return ``(program, program_hash)``.

    The hash must reproduce the registry ``assertion_program_hash`` (asserted
    by the runner), proving the executed program is the frozen one."""
    g = _load_generator()
    if oracle is None:
        oracle = load_frozen_oracle()
    path_types = g.build_leaf_path_type_map(oracle)
    program = g.compile_assertion_program(
        expectation["case_id"],
        expectation["expected_leaf_set"],
        expectation["expected_trace_leaf_set"],
        expectation["expected_source_leaf_set"],
        expectation.get("expected_integrity_error"),
        path_types,
    )
    return program, _sha256_text(g.canonical_json(program))


def validate_program_structure(program: Sequence[Mapping[str, Any]]) -> None:
    """Closed DSL structural contract: exact clause keys, closed operator set,
    no forbidden constructs, path grammar."""
    clause_keys = {
        "clause_id", "operator", "actual_path", "expected_typed_value",
        "expected_ref_path", "value_type", "reason_code",
    }
    path_re = __import__("re").compile(
        r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*|\.[0-9]+|\[[0-9]+\])*$"
    )
    for clause in program:
        assert set(clause) == clause_keys, f"clause keys {sorted(clause)}"
        assert clause["operator"] in DSL_OPERATORS, clause["operator"]
        assert path_re.match(clause["actual_path"]), clause["actual_path"]
        for field in ("clause_id", "actual_path", "expected_typed_value",
                      "expected_ref_path", "reason_code"):
            value = clause.get(field)
            if isinstance(value, str):
                for token in FORBIDDEN_CONSTRUCTS:
                    assert token not in value, f"{field} contains {token!r}"


def interpret_program(
    program: Sequence[Mapping[str, Any]], flat: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    """Execute every frozen DSL clause against the flattened runtime root.

    Returns one result dict per clause:
    ``{"clause_id", "operator", "actual_path", "passed", "actual", "expected"}``.
    Frozen programs only use ``equals`` / ``error_equals``; the remaining
    closed operators are implemented for completeness and rejected if unknown.
    """
    results: List[Dict[str, Any]] = []

    def lookup(path: str) -> Any:
        return flat.get(path, _MISSING)

    for clause in program:
        operator = clause["operator"]
        path = clause["actual_path"]
        expected = clause["expected_typed_value"]
        ref = clause["expected_ref_path"]
        actual = lookup(path)
        if operator == "equals":
            passed = actual == expected
        elif operator == "error_equals":
            passed = flat.get("integrity_error") == expected
        elif operator == "exists":
            passed = path in flat and actual is expected
        elif operator == "absent":
            passed = path not in flat and actual is expected
        elif operator == "not_equals":
            passed = actual != expected
        elif operator == "in_enum":
            passed = isinstance(expected, list) and actual in expected
        elif operator == "decimal_equals":
            passed = _decimal_equal(actual, expected)
        elif operator == "ordered_equals":
            passed = actual == expected
        elif operator == "set_equals":
            passed = sorted(actual) == sorted(expected) if isinstance(actual, list) else actual == expected
        elif operator == "hash_equals":
            passed = isinstance(actual, str) and actual == expected
        elif operator == "count_equals":
            passed = isinstance(actual, list) and len(actual) == expected
        elif operator == "ref_resolves":
            passed = _ref_resolves(flat, actual, ref)
        elif operator == "scope_all_equal":
            passed = _scope_all_equal(flat, ref)
        elif operator == "one_to_one":
            passed = _one_to_one(flat, actual, ref)
        else:  # pragma: no cover -- guarded by validate_program_structure
            raise AssertionError(f"unknown DSL operator {operator!r}")
        results.append({
            "clause_id": clause["clause_id"],
            "operator": operator,
            "actual_path": path,
            "passed": bool(passed),
            "actual": actual,
            "expected": expected,
        })
    return results


_MISSING = object()


def _decimal_equal(actual: Any, expected: Any) -> bool:
    from decimal import Decimal, InvalidOperation

    if not isinstance(actual, str) or not isinstance(expected, str):
        return False
    try:
        return Decimal(actual) == Decimal(expected)
    except InvalidOperation:
        return False


def _ref_resolves(flat: Mapping[str, Any], actual: Any, ref: Optional[str]) -> bool:
    """The id at actual_path resolves to an id set at the ref path."""
    if ref is None:
        return False
    resolved = flat.get(ref)
    if isinstance(resolved, list):
        return actual in resolved
    return actual == resolved


def _scope_all_equal(flat: Mapping[str, Any], ref: Optional[str]) -> bool:
    """All id values addressed by the ref path must be equal (scope equality)."""
    if ref is None:
        return False
    value = flat.get(ref)
    if isinstance(value, list):
        return len(set(value)) <= 1
    return True


def _one_to_one(flat: Mapping[str, Any], actual: Any, ref: Optional[str]) -> bool:
    """Cardinality probe: actual id set and ref id set are in bijection."""
    if ref is None:
        return False
    other = flat.get(ref)
    if not isinstance(actual, list) or not isinstance(other, list):
        return False
    return len(set(actual)) == len(actual) == len(set(other)) == len(other)


# ---------------------------------------------------------------------------
# Mutation machinery (deterministic typed-input transformations)
# ---------------------------------------------------------------------------

# Section -> embedded self-hash field (must mirror the runtime's canonical-hash
# verification so that rehashed mutations are hash-consistent).
SECTION_HASH_FIELD: Mapping[str, str] = {
    "run_scope_binding": "lineage_hash",
    "cutoff_decisions": "hash",
    "authority_bindings": "hash",
    "scope_envelopes": "record_content_hash",
    "observed_results": "lineage_hash",
    "measure_definitions": "definition_hash",
    "reference_range_definitions": "hash",
    "grade_rules": "hash",
    "baseline_rules": "hash",
    "trend_rules": "hash",
    "monitoring_rules": "hash",
    "monitoring_predicates": "hash",
    "action_obligation_definitions": "hash",
    "organ_pattern_rule_definitions": "hash",
    "examination_requirement_sets": "hash",
    "priority_precedence_rules": "hash",
    "producer_consumption_bindings": "lineage_hash",
    "correction_chain_decisions": "hash",
    "d05_gate_bindings": "hash",
    "applicability_evidence": "hash",
    "visit_refs": "hash",
    "carry_forward_refs": "hash",
    "d04_context_refs": "hash",
    "clinical_review_refs": "hash",
    "clinical_significance_reason_refs": "hash",
    "subject_demographics": "hash",
    "time_refs": "hash",
    "audience_lexicon": "content_hash",
    "previous_run_scope_binding": "lineage_hash",
    "previous_time_refs": "hash",
    "previous_scope_envelopes": "record_content_hash",
    "previous_observed_results": "lineage_hash",
}

# Singleton sections (dict, not list).
SINGLETON_SECTIONS = frozenset({
    "run_scope_binding", "previous_run_scope_binding", "priority_policy",
    "audience_lexicon", "shared_spine_binding", "shared_spine_scope_equality_decision",
    "input_schema",
})

# Sections that are lists of objects.
LIST_SECTIONS = frozenset({
    "action_obligation_definitions", "applicability_evidence", "authority_bindings",
    "baseline_rules", "carry_forward_refs", "clinical_review_refs",
    "clinical_significance_reason_refs", "correction_chain_decisions",
    "cutoff_decisions", "d04_context_refs", "d05_gate_bindings",
    "examination_requirement_sets", "grade_rule_sets", "grade_rules",
    "measure_definitions", "monitoring_predicates", "monitoring_rules",
    "observed_results", "organ_pattern_rule_definitions", "previous_observed_results",
    "previous_scope_envelopes", "previous_time_refs", "priority_precedence_rules",
    "producer_consumption_bindings", "reference_range_definitions",
    "scope_envelopes", "time_refs", "trend_rules", "unit_conversion_rules",
    "visit_refs",
})


class D07MutationError(Exception):
    """A mutation operator could not be applied to the given typed input."""


def rehash_object(obj: Mapping[str, Any], hash_field: str) -> None:
    """Recompute the embedded self-hash payload-consistently after a mutation."""
    core = {key: value for key, value in obj.items() if key != hash_field}
    obj[hash_field] = content_hash(core)


def _objects(typed_input: Mapping[str, Any], section: str) -> List[Dict[str, Any]]:
    value = typed_input.get(section)
    if isinstance(value, list):
        return [obj for obj in value if isinstance(obj, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _first(typed_input: Mapping[str, Any], section: str) -> Dict[str, Any]:
    objs = _objects(typed_input, section)
    if not objs:
        raise D07MutationError(f"section {section!r} is empty on this case")
    return objs[0]


def _last(typed_input: Mapping[str, Any], section: str) -> Dict[str, Any]:
    objs = _objects(typed_input, section)
    if not objs:
        raise D07MutationError(f"section {section!r} is empty on this case")
    return objs[-1]


def _flip_str(typed_input: Mapping[str, Any], section: str, field: str,
              alt: str) -> None:
    obj = _first(typed_input, section)
    current = obj.get(field)
    if current is None:
        obj[field] = alt
    elif isinstance(current, str):
        obj[field] = alt if current != alt else current + "-ALT"
    else:
        raise D07MutationError(f"{section}.{field} is not a string on this case")


def _suffix(typed_input: Mapping[str, Any], section: str, field: str,
            suffix: str = "-TAMPER") -> None:
    obj = _first(typed_input, section)
    current = obj.get(field)
    if not isinstance(current, str):
        raise D07MutationError(f"{section}.{field} is not a string on this case")
    obj[field] = current + suffix


def _suffix_or_set(typed_input: Mapping[str, Any], section: str, field: str,
                   alt: str, suffix: str = "-TAMPER") -> None:
    """Suffix the field when it is a string; else set the documented alt value
    (the mutation must always change the substantive input)."""
    obj = _first(typed_input, section)
    current = obj.get(field)
    if isinstance(current, str):
        obj[field] = current + suffix
    else:
        obj[field] = alt


def _set(typed_input: Mapping[str, Any], section: str, field: str, value: Any) -> None:
    obj = _first(typed_input, section)
    obj[field] = value


# Negative mutation operators: id -> callable(typed_input) mutating a deep copy
# in place.  Unless documented otherwise the mutation is NOT rehashed: the
# canonical-hash pre-evaluator stage must detect the tamper (fail closed).  Ids
# in ``_SYNC_REWRITE_IDS`` rehash their target (they ARE the synchronized
# rewrite class) and must fail at a later consistency stage.
NEGATIVE_OPERATORS: Dict[str, Any] = {}


def _neg(id_):
    def _register(fn):
        NEGATIVE_OPERATORS[id_] = fn
        return fn
    return _register


@_neg("N-STALE-HASH")
def _(ti):
    if _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-SYNC-REWRITE-NO-AUTHORITY")
def _(ti):
    """Synchronized rewrite without independent authority: the result claims a
    new stable record identity while its scope envelope still binds the old
    record id -> the foreign-key bijection stage must reject it."""
    obj = _first(ti, "observed_results")
    obj["stable_source_record_id"] = "SYN-SYNC-REWRITE-NO-AUTH"
    rehash_object(obj, SECTION_HASH_FIELD["observed_results"])


@_neg("N-WRONG-SCOPE-DRIFT")
def _(ti):
    _suffix(ti, "run_scope_binding", "project_ref")


@_neg("N-WRONG-SITE")
def _(ti):
    _suffix(ti, "scope_envelopes", "site_ref")


@_neg("N-WRONG-RUN")
def _(ti):
    _suffix(ti, "run_scope_binding", "run_ref")


@_neg("N-WRONG-RUN-REF")
def _(ti):
    _suffix(ti, "run_scope_binding", "run_ref")


@_neg("N-WRONG-SUBJECT")
def _(ti):
    if _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "subject_ref")
    else:
        _suffix(ti, "scope_envelopes", "subject_ref")


@_neg("N-WRONG-CUTOFF")
def _(ti):
    _set(ti, "run_scope_binding", "clinical_event_cutoff", "2027-01-01T00:00:00+08:00")


@_neg("N-WRONG-SNAPSHOT")
def _(ti):
    _suffix(ti, "run_scope_binding", "accepted_snapshot_ref")


@_neg("N-WRONG-MODE")
def _(ti):
    _set(ti, "run_scope_binding", "monitoring_mode", "SYN-WRONG-MODE")


@_neg("N-WRONG-EPISODE")
def _(ti):
    _suffix(ti, "scope_envelopes", "episode_key")


@_neg("N-WRONG-DOMAIN")
def _(ti):
    _suffix(ti, "scope_envelopes", "domain_id")


@_neg("N-WRONG-SOURCE-REVISION")
def _(ti):
    _suffix(ti, "run_scope_binding", "source_revision")


@_neg("N-OUT-OF-CUTOFF-RECORD")
def _(ti):
    _set(ti, "observed_results", "record_status", "out_of_cutoff")


@_neg("N-WRONG-VISIT-DRIFT")
def _(ti):
    _suffix(ti, "observed_results", "visit_ref")


@_neg("N-WRONG-WINDOW-DRIFT")
def _(ti):
    _set(ti, "visit_refs", "window", ["9d", "99d"])


@_neg("N-AUTHORITY-VERSION-DRIFT")
def _(ti):
    _set(ti, "authority_bindings", "selected_version", "999")


@_neg("N-RULE-VERSION-DRIFT")
def _(ti):
    _set(ti, "run_scope_binding", "mapping_version", "999")


@_neg("N-CORRECTION-FORK")
def _(ti):
    if _objects(ti, "correction_chain_decisions"):
        obj = _first(ti, "correction_chain_decisions")
        if obj.get("branch_state") != "forked":
            obj["branch_state"] = "forked"
        else:
            # Already forked (defect fixture): force a second fork dimension by
            # marking an accepted-current result corrected without a decision.
            _set(ti, "observed_results", "correction_status", "corrected")
    else:
        _set(ti, "observed_results", "correction_status", "corrected")


@_neg("N-DUPLICATE-IDENTITY")
def _(ti):
    objs = _objects(ti, "observed_results")
    if len(objs) < 2:
        raise D07MutationError("N-DUPLICATE-IDENTITY needs >=2 observed results")
    used: Dict[str, Dict[str, Any]] = {}
    for obj in objs:
        sid = obj.get("stable_source_record_id")
        if isinstance(sid, str) and sid not in used:
            used[sid] = obj
    if len(used) >= 2:
        sid_a = next(iter(used))
        sid_b = list(used)[-1]
        if sid_a != sid_b:
            used[sid_b]["stable_source_record_id"] = sid_a
            return
    # All stable ids already duplicate: duplicate a result_id instead.
    objs[-1]["result_id"] = objs[0]["result_id"]


@_neg("N-IDENTITY-DRIFT")
def _(ti):
    _set(ti, "observed_results", "stable_source_record_id", "SYN-TAMPER-IDENTITY")


@_neg("N-DUPLICATE-RISK-DRIFT")
def _(ti):
    objs = _objects(ti, "observed_results")
    if len(objs) >= 2:
        objs[-1]["result_id"] = objs[0]["result_id"]
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-UNIT-DRIFT")
def _(ti):
    _set(ti, "observed_results", "original_unit", "SYN-WRONG-UNIT")


@_neg("N-RANGE-DRIFT")
def _(ti):
    _suffix(ti, "reference_range_definitions", "range_definition_id")


@_neg("N-GRADE-DRIFT")
def _(ti):
    if _objects(ti, "grade_rules"):
        _suffix(ti, "grade_rules", "grade_rule_id")
    else:
        _suffix_or_set(ti, "observed_results", "reported_grade", "G5")


@_neg("N-CS-NCS-DRIFT")
def _(ti):
    _flip_str(ti, "observed_results", "reported_cs_ncs", "CS")


@_neg("N-ENDPOINT-DRIFT")
def _(ti):
    _set(ti, "observed_results", "stable_measure_key", "SYN-WRONG-MEASURE")


@_neg("N-BASELINE-DRIFT")
def _(ti):
    _suffix(ti, "baseline_rules", "rule_id")


@_neg("N-TREND-DRIFT")
def _(ti):
    _suffix(ti, "trend_rules", "rule_id")


@_neg("N-PATTERN-DRIFT")
def _(ti):
    if _objects(ti, "organ_pattern_rule_definitions"):
        _suffix(ti, "organ_pattern_rule_definitions", "pattern_rule_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-SERIOUSNESS-DRIFT")
def _(ti):
    if _objects(ti, "organ_pattern_rule_definitions"):
        obj = _first(ti, "organ_pattern_rule_definitions")
        obj["seriousness_clue_permitted"] = not obj.get("seriousness_clue_permitted")
    else:
        _flip_str(ti, "observed_results", "reported_abnormal_flag", "H")


@_neg("N-FOREIGN-KEY-BROKEN")
def _(ti):
    _set(ti, "observed_results", "scope_envelope_id", "SYN-NO-SUCH-ENVELOPE")


@_neg("N-ACTION-DRIFT")
def _(ti):
    if _objects(ti, "action_obligation_definitions"):
        _suffix(ti, "action_obligation_definitions", "obligation_definition_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-OWNER-ROUTE-DRIFT")
def _(ti):
    if _objects(ti, "monitoring_rules"):
        _suffix(ti, "monitoring_rules", "owner_route")
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-QUERY-OWNER-DRIFT")
def _(ti):
    if _objects(ti, "action_obligation_definitions"):
        _set(ti, "action_obligation_definitions", "query_owner", "D01")
    elif _objects(ti, "monitoring_rules"):
        _suffix(ti, "monitoring_rules", "owner_route")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-PD-WORDING-WITHOUT-PERMISSION")
def _(ti):
    if _objects(ti, "d04_context_refs"):
        # Tamper the acceptance condition (not rehashed): the canonical-hash
        # stage must reject the drift before any PD wording can be produced.
        _set(ti, "d04_context_refs", "context_accepted", False)
    elif _objects(ti, "producer_consumption_bindings"):
        _suffix(ti, "producer_consumption_bindings", "permitted_outputs")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-PRIORITY-DRIFT")
def _(ti):
    _suffix(ti, "priority_precedence_rules", "precedence_rule_id")


@_neg("N-LIFECYCLE-DRIFT")
def _(ti):
    if _objects(ti, "carry_forward_refs"):
        _set(ti, "carry_forward_refs", "identity_resolution_state", "ambiguous")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-REOPEN-WITHOUT-AUTHORITY")
def _(ti):
    if _objects(ti, "carry_forward_refs"):
        _set(ti, "carry_forward_refs", "identity_resolution_state", "not_resolved")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-JOURNEY-MARKER-DRIFT")
def _(ti):
    lex = ti.get("audience_lexicon")
    if isinstance(lex, dict) and isinstance(lex.get("allowed_risk_type_labels"), list) \
            and lex["allowed_risk_type_labels"]:
        lex["allowed_risk_type_labels"][0] = "SYN-WRONG-RISK-LABEL"
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-JUMP-DRIFT")
def _(ti):
    if _objects(ti, "producer_consumption_bindings"):
        _suffix(ti, "producer_consumption_bindings", "producer_object_id")
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-PAYLOAD-DRIFT")
def _(ti):
    if isinstance(ti.get("shared_spine_binding"), dict):
        _suffix(ti, "shared_spine_binding", "binding_id")
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-REVERSE-BINDING-MISSING")
def _(ti):
    if isinstance(ti.get("shared_spine_scope_equality_decision"), dict):
        dec = ti["shared_spine_scope_equality_decision"]
        dec["all_equal"] = not dec.get("all_equal")
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-SAMPLE-DRIFT")
def _(ti):
    _set(ti, "observed_results", "specimen_quality", "SYN-WRONG-QUALITY")


@_neg("N-CONTEXT-DRIFT")
def _(ti):
    if _objects(ti, "d04_context_refs"):
        _suffix(ti, "d04_context_refs", "protocol_clause_ref")
    elif _objects(ti, "examination_requirement_sets"):
        _suffix(ti, "examination_requirement_sets", "requirement_set_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-MEDICAL-ACTION-DRIFT")
def _(ti):
    if _objects(ti, "action_obligation_definitions"):
        _suffix(ti, "action_obligation_definitions", "obligation_definition_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-CROSS-DOMAIN-DRIFT")
def _(ti):
    if _objects(ti, "producer_consumption_bindings"):
        _set(ti, "producer_consumption_bindings", "producer_domain", "D99")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-AGGREGATION-DRIFT")
def _(ti):
    _suffix(ti, "scope_envelopes", "envelope_id")


@_neg("N-AE-DRIFT")
def _(ti):
    if _objects(ti, "d04_context_refs"):
        _set(ti, "d04_context_refs", "context_kind", "eligibility_context")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-METHOD-DRIFT")
def _(ti):
    _suffix_or_set(ti, "observed_results", "method_kind", "SYN-WRONG-METHOD")


@_neg("N-RECURRENT-GAP-DRIFT")
def _(ti):
    if _objects(ti, "action_obligation_definitions"):
        _suffix(ti, "action_obligation_definitions", "obligation_definition_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-APPLICABILITY-DRIFT")
def _(ti):
    if _objects(ti, "applicability_evidence"):
        _suffix(ti, "applicability_evidence", "applicability_evidence_id")
    elif _objects(ti, "observed_results"):
        _suffix(ti, "observed_results", "result_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-APP-AUTHORITY-UNVERSIONED")
def _(ti):
    if _objects(ti, "applicability_evidence"):
        _set(ti, "applicability_evidence", "authority_binding_id", "SYN-UNVERSIONED")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-APP-CONTROL-PLANE-NO-MATCH")
def _(ti):
    if _objects(ti, "applicability_evidence"):
        obj = _first(ti, "applicability_evidence")
        obj["control_plane_no_match"] = True
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-APP-EVIDENCE-REMOVED")
def _(ti):
    """Remove the evidence's authority: tamper the evidence binding without
    rehash so the canonical-hash stage must reject it (evidence removal is
    otherwise a legitimate snapshot change the runtime cannot detect)."""
    if _objects(ti, "applicability_evidence"):
        _suffix(ti, "applicability_evidence", "authority_binding_id")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-NOT-APPLICABLE-WITHOUT-AUTHORITY")
def _(ti):
    if _objects(ti, "applicability_evidence"):
        _set(ti, "applicability_evidence", "applicability", "not_applicable")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-NEGATIVE-EMPTY-TABLE")
def _(ti):
    if _objects(ti, "applicability_evidence"):
        _set(ti, "applicability_evidence", "applicability", "applicable")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-L0-GAP-MASKED")
def _(ti):
    if _objects(ti, "observed_results"):
        _set(ti, "observed_results", "record_status", "withdrawn")
    else:
        _suffix(ti, "authority_bindings", "authority_binding_id")


@_neg("N-GATE-CLOSED-DRIFT")
def _(ti):
    if _objects(ti, "d05_gate_bindings"):
        _suffix(ti, "d05_gate_bindings", "d05_gate_binding_id")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-GATE-STAGE-DRIFT")
def _(ti):
    if _objects(ti, "d05_gate_bindings"):
        _set(ti, "d05_gate_bindings", "blocked_stage", "SYN-WRONG-STAGE")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-GATE-CONTROL-PLANE-DRIFT")
def _(ti):
    if _objects(ti, "d05_gate_bindings"):
        _set(ti, "d05_gate_bindings", "control_plane_state", "SYN-WRONG-PLANE")
    else:
        _suffix(ti, "observed_results", "result_id")


@_neg("N-GATE-BYPASS-QUERY")
def _(ti):
    if _objects(ti, "d05_gate_bindings"):
        _suffix(ti, "d05_gate_bindings", "blocked_observation_id")
    else:
        _suffix(ti, "observed_results", "result_id")


# Positive mutation operators: the mutation must leave the raw output byte
# identical (proven inert on all 144 cases).
POSITIVE_OPERATORS: Dict[str, Any] = {}


def _pos(id_):
    def _register(fn):
        POSITIVE_OPERATORS[id_] = fn
        return fn
    return _register


def _reorder_inert_list(ti: Dict[str, Any]) -> bool:
    """Reverse a provably order-insensitive list: time_refs, then
    monitoring_predicates, then audience-lexicon vocab lists."""
    for section in ("time_refs", "monitoring_predicates"):
        value = ti.get(section)
        if isinstance(value, list) and len(value) >= 2:
            ti[section] = list(reversed(value))
            return True
    lex = ti.get("audience_lexicon")
    if isinstance(lex, dict):
        for field in ("allowed_domain_labels", "allowed_risk_type_labels",
                      "forbidden_internal_tokens", "required_sentence_patterns"):
            if isinstance(lex.get(field), list) and len(lex[field]) >= 2:
                lex[field] = list(reversed(lex[field]))
                # The lexicon is a content-addressed singleton: a vocabulary
                # reorder is a legitimate new lexicon version, so the
                # synchronized rewrite must rehash it to stay provably inert
                # (mirrors P-ADD-UNRELATED-RECORD).
                rehash_object(lex, SECTION_HASH_FIELD["audience_lexicon"])
                return True
    raise D07MutationError("no order-insensitive list available on this case")


@_pos("P-ARRAY-REORDER")
def _(ti):
    _reorder_inert_list(ti)


def _add_inert_lexicon_label(ti: Dict[str, Any]) -> None:
    lex = ti.get("audience_lexicon")
    if not isinstance(lex, dict):
        raise D07MutationError("audience_lexicon missing")
    lex["allowed_domain_labels"] = list(lex.get("allowed_domain_labels", [])) + ["D99-UNRELATED"]
    rehash_object(lex, "content_hash")


@_pos("P-ADD-UNRELATED-RECORD")
def _(ti):
    """Add unrelated, non-medical context that must not change any output leaf
    (a new allowed domain label mirrors a new, inert lexicon version)."""
    _add_inert_lexicon_label(ti)


@_pos("P-COUNTEREVIDENCE-ADDED")
def _(ti):
    """Add non-qualifying context (inert label) that must not alter the
    negative chain outcome."""
    _add_inert_lexicon_label(ti)


@_pos("P-APP-EVIDENCE-ADDED")
def _(ti):
    """Add non-authoritative context that must not change the L0-gap outcome."""
    _add_inert_lexicon_label(ti)


def apply_mutation(typed_input: Mapping[str, Any], mutation_id: str) -> Dict[str, Any]:
    """Deep-copy the typed input and apply one deterministic mutation operator."""
    mutated = copy.deepcopy(dict(typed_input))
    if mutation_id in NEGATIVE_OPERATORS:
        NEGATIVE_OPERATORS[mutation_id](mutated)
    elif mutation_id in POSITIVE_OPERATORS:
        POSITIVE_OPERATORS[mutation_id](mutated)
    else:
        raise D07MutationError(f"unknown mutation id {mutation_id!r}")
    return mutated


# ---------------------------------------------------------------------------
# Declared mutation pairs (from the frozen catalog)
# ---------------------------------------------------------------------------

def declared_mutation_pairs(catalog: Optional[Mapping[str, Any]] = None) -> Tuple[
    List[Tuple[str, str]], List[Tuple[str, str]]
]:
    """All declared (case_id, mutation_id) pairs: (negative, positive)."""
    catalog = catalog if catalog is not None else load_frozen_catalog()
    negative: List[Tuple[str, str]] = []
    positive: List[Tuple[str, str]] = []
    for case in catalog["ordered_cases"]:
        for mid in case["negative_mutation_ids"]:
            negative.append((case["case_id"], mid))
        for mid in case["positive_mutation_ids"]:
            positive.append((case["case_id"], mid))
    return negative, positive
