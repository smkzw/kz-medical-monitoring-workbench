"""R4-D06 synthetic challenge matrix, fixture adapter and DSL interpreter.

Frozen source of truth: ``FROZEN_R4_D06_CONTRACT_V1_16`` (§12.1, §13).
This module is the **test-side / adapter surface**:

* :class:`D06ChallengeCase` maps one frozen challenge row to a named,
  executable case through the real D06 entrypoints (``efficacy_evaluator``,
  ``gate_evaluator``, ``contract_schema_validator``,
  ``audience_projection_validator``, ``challenge_registry_validator``).
* :func:`build_d06_challenge_matrix` loads the frozen typed fixture
  catalog / oracle / registry (test-side only; the runtime never sees
  them) and returns all 219 cases.
* :class:`D06FixtureAdapter` converts a frozen catalog fixture dict into
  the runtime typed :class:`~mm_r4.efficacy_evaluator.D06Fixture` without
  applying any expected outcome.
* :func:`interpret_assertion_dsl` is the frozen ``d06-assert-v1``
  interpreter: clause-field validation, exact leaf bijection, per-clause
  assertion and tautological/static-callback rejection.
* :func:`validate_challenge_registry_input` implements the
  ``d06.challenge_registry_validator`` entrypoint contract: it rejects
  tautological callbacks, unconsumed/input-only assertions and registry
  integrity drift before any evaluator runs.

Expected outcomes remain test-side: the runtime engine never reads the
oracle, the DSL, or any expected text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .efficacy import (
    ChallengeAssertionContractError,
    D06ChallengeOutcome,
    d06_canonical_json,
    d06_content_hash,
)
from .efficacy_evaluator import (
    D06Fixture,
    evaluate_efficacy_fixture,
    evaluate_gate,
    validate_audience_projection,
    validate_contract_schema,
)

# ---------------------------------------------------------------------------
# Frozen artifact locations (test-side only)
# ---------------------------------------------------------------------------

_REVIEWS = Path(__file__).resolve().parents[4] / "reviews"
CATALOG_PATH = _REVIEWS / (
    "medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json"
)
ORACLE_PATH = _REVIEWS / (
    "medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json"
)
REGISTRY_PATH = _REVIEWS / (
    "medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json"
)

CANONICAL_CATALOG_ID = "medical-monitoring-r4-d06-typed-fixtures"
CANONICAL_CATALOG_VERSION = "8.0.3"
CANONICAL_CATALOG_HASH = (
    "44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774"
)
CANONICAL_ORACLE_HASH = (
    "16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a"
)
CANONICAL_REGISTRY_HASH = (
    "f7a7733b00c1367d95e66d7f8b5e1a12793d51ab0f7585367dcad664922be1b4"
)
CANONICAL_CONTRACT_SEMANTIC_HASH = (
    "247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642"
)

ENTRYPOINTS: Dict[str, Callable[[D06Fixture], D06ChallengeOutcome]] = {
    "d06.efficacy_evaluator": evaluate_efficacy_fixture,
    "d06.gate_evaluator": evaluate_gate,
    "d06.contract_schema_validator": validate_contract_schema,
    "d06.audience_projection_validator": validate_audience_projection,
}


def load_frozen_catalog() -> Dict[str, Any]:
    with open(CATALOG_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def load_frozen_oracle() -> Dict[str, Any]:
    with open(ORACLE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def load_frozen_registry() -> Dict[str, Any]:
    with open(REGISTRY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# Fixture adapter (catalog dict -> runtime typed fixture)
# ---------------------------------------------------------------------------


class D06FixtureAdapter:
    """Build the runtime typed fixture from a frozen catalog case."""

    def build(self, catalog_case: Mapping[str, Any]) -> D06Fixture:
        from .efficacy_evaluator import build_d06_fixture

        return build_d06_fixture(catalog_case["fixture"])


def fixture_content_hash(fixture: Mapping[str, Any]) -> str:
    """Hex sha256 of the frozen fixture object."""
    return d06_content_hash(fixture)


def scope_content_hash(scope: Mapping[str, Any]) -> str:
    return d06_content_hash(scope)


# ---------------------------------------------------------------------------
# DSL interpreter (frozen d06-assert-v1)
# ---------------------------------------------------------------------------


def _outcome_leaves(
    value: Any, prefix: Tuple[str, ...] = ()
) -> Dict[Tuple[str, ...], Any]:
    """All leaf paths of the outcome with their values."""
    if isinstance(value, dict):
        result: Dict[Tuple[str, ...], Any] = {}
        for key, item in value.items():
            result.update(_outcome_leaves(item, prefix + (str(key),)))
        return result
    return {prefix: value}


def _lookup_path(outcome: Any, path: Sequence[str]) -> Any:
    current = outcome
    for part in path:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise ChallengeAssertionContractError(
                f"assertion path {'.'.join(path)} does not resolve in outcome"
            )
    return current


class DslAssertion:
    """One executed DSL clause against the actual outcome."""

    def __init__(self, clause: Mapping[str, Any], outcome: Mapping[str, Any]):
        self.clause_id = str(clause["clause_id"])
        self.outcome_path = list(clause["outcome_path"])
        self.operator = str(clause["operator"])
        self.expected = clause["typed_expected_value"]
        self.actual = _lookup_path(outcome, self.outcome_path)
        self.passed = self._evaluate()

    def _evaluate(self) -> bool:
        if self.operator == "is_null":
            return self.actual is None
        if self.operator == "equals":
            return self.actual == self.expected
        raise ChallengeAssertionContractError(
            f"unknown assertion operator {self.operator!r}"
        )

    def as_named_assertion(self) -> Tuple[str, bool, Any, Any]:
        return (self.clause_id, self.passed, self.actual, self.expected)


def validate_dsl_structure(
    clauses: Sequence[Mapping[str, Any]], outcome: Mapping[str, Any]
) -> None:
    """Frozen DSL structural contract (exact bijection + clause schema)."""
    if not clauses:
        raise ChallengeAssertionContractError("missing assertion DSL")
    for index, clause in enumerate(clauses, 1):
        if set(clause) != {
            "canonicalization_rule",
            "clause_id",
            "operator",
            "outcome_path",
            "typed_expected_value",
        }:
            raise ChallengeAssertionContractError(
                "assertion DSL clause fields are not exact and complete"
            )
        if (
            clause.get("clause_id") != f"assert-{index:03d}"
            or clause.get("operator") not in {"equals", "is_null"}
            or clause.get("canonicalization_rule") != "d06-canonical-v1"
        ):
            raise ChallengeAssertionContractError(
                "assertion DSL contains unknown, extra, or non-canonical clause"
            )
        operator = clause["operator"]
        expected = clause["typed_expected_value"]
        if (operator == "is_null" and expected is not None) or (
            operator == "equals" and expected is None
        ):
            raise ChallengeAssertionContractError(
                "assertion DSL operator/value compatibility mismatch"
            )
    clause_paths = [tuple(clause.get("outcome_path", [])) for clause in clauses]
    expected_leaf_paths = set(_outcome_leaves(outcome).keys())
    if (
        len(clauses) != len(expected_leaf_paths)
        or set(clause_paths) != expected_leaf_paths
    ):
        raise ChallengeAssertionContractError(
            "assertion DSL paths are not an exact bijection to outcome leaves"
        )


def interpret_assertion_dsl(
    outcome: Mapping[str, Any],
    clauses: Sequence[Mapping[str, Any]],
) -> List[DslAssertion]:
    """Execute every frozen DSL clause against the actual outcome.

    Raises :class:`ChallengeAssertionContractError` when any clause fails
    or the DSL structure is violated (rejecting tautological, static,
    unconsumed or missing assertions).
    """
    validate_dsl_structure(clauses, outcome)
    assertions: List[DslAssertion] = []
    for clause in clauses:
        assertion = DslAssertion(clause, outcome)
        if not assertion.passed:
            raise ChallengeAssertionContractError(
                f"assertion {assertion.clause_id} failed for "
                f"{'.'.join(assertion.outcome_path)}: expected "
                f"{assertion.expected!r}, got {assertion.actual!r}"
            )
        assertions.append(assertion)
    return assertions


# ---------------------------------------------------------------------------
# Outcome assembly (runtime outcome + manifest metadata -> frozen shape)
# ---------------------------------------------------------------------------


def assemble_outcome(
    runtime: D06ChallengeOutcome,
    catalog_case: Mapping[str, Any],
) -> Dict[str, Any]:
    """Raw runtime outcome serialization.

    This is the object compared with the independent oracle/DSL.  It is
    exactly the evaluator/gate/schema/audience/registry entrypoint output:
    no field is copied or replaced from the expected outcome, oracle,
    manifest trace edges, challenge number, fixture/test ids or
    annotations.  The runtime derives every annotation leaf
    (``challenge_assertion_code``, ``clinical_outcome_contract``,
    ``evaluated_fixture_hash``, ``input_scope_hash``, trace edges) from
    its actual typed input and frozen rules.
    """
    return runtime.to_plain()


def outcome_matches_expected(
    actual: Mapping[str, Any], expected: Mapping[str, Any]
) -> bool:
    """Whole-object comparison after canonical normalization."""
    return d06_canonical_json(actual) == d06_canonical_json(expected)


# ---------------------------------------------------------------------------
# Challenge case container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D06ChallengeCase:
    """One frozen challenge row bound to a real D06 entrypoint."""

    number: int
    name: str
    fixture_id: str
    test_id: str
    entrypoint_id: str
    catalog_case: Mapping[str, Any]
    expected_outcome: Mapping[str, Any]
    assertion_dsl: Tuple[Mapping[str, Any], ...]
    required_outcome_fields: Tuple[str, ...]
    required_hash_relations: Tuple[str, ...]
    required_trace_edge_types: Tuple[str, ...]
    required_audience_checks: Tuple[str, ...]
    fixture_hash: str

    @property
    def fixture(self) -> Mapping[str, Any]:
        return self.catalog_case["fixture"]

    def build_runtime_fixture(self) -> D06Fixture:
        return D06FixtureAdapter().build(self.catalog_case)

    def run(self) -> D06ChallengeOutcome:
        if self.entrypoint_id not in ENTRYPOINTS:
            raise KeyError(
                f"case {self.number} has no runtime entrypoint {self.entrypoint_id!r}"
            )
        entrypoint = ENTRYPOINTS[self.entrypoint_id]
        return entrypoint(self.build_runtime_fixture())

    def assemble(self) -> Dict[str, Any]:
        """Raw entrypoint output; no expected/manifest annotation is added."""
        return self.run().to_plain()

    def interpret(self) -> List[DslAssertion]:
        """Run the entrypoint and assert every frozen DSL clause."""
        return interpret_assertion_dsl(self.assemble(), self.assertion_dsl)


def _case_name(number: int, contract_text: str) -> str:
    return f"challenge_{number:03d}"


# ---------------------------------------------------------------------------
# Challenge matrix builder (test-side)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D06ChallengeMatrix:
    cases: Tuple[D06ChallengeCase, ...]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def numbers(self) -> Tuple[int, ...]:
        return tuple(case.number for case in self.cases)

    def by_number(self, number: int) -> D06ChallengeCase:
        for case in self.cases:
            if case.number == number:
                return case
        raise KeyError(number)


def build_d06_challenge_matrix(
    catalog: Optional[Mapping[str, Any]] = None,
) -> D06ChallengeMatrix:
    """Build all 219 frozen challenge cases (test-side)."""
    catalog = catalog if catalog is not None else load_frozen_catalog()
    cases: List[D06ChallengeCase] = []
    for catalog_case in catalog["cases"]:
        number = int(catalog_case["challenge_number"])
        expected = catalog_case["expected_outcome"]
        contract_text = expected.get("domain_assertions", {}).get(
            "clinical_outcome_contract", ""
        )
        cases.append(
            D06ChallengeCase(
                number=number,
                name=_case_name(number, contract_text),
                fixture_id=str(catalog_case["fixture_id"]),
                test_id=str(catalog_case["test_id"]),
                entrypoint_id=str(catalog_case["entrypoint_id"]),
                catalog_case=catalog_case,
                expected_outcome=expected,
                assertion_dsl=tuple(catalog_case["assertion_dsl"]),
                required_outcome_fields=tuple(catalog_case["required_outcome_fields"]),
                required_hash_relations=tuple(catalog_case["required_hash_relations"]),
                required_trace_edge_types=tuple(
                    catalog_case["required_trace_edge_types"]
                ),
                required_audience_checks=tuple(
                    catalog_case["required_audience_checks"]
                ),
                fixture_hash=fixture_content_hash(catalog_case["fixture"]),
            )
        )
    return D06ChallengeMatrix(tuple(cases))


# ---------------------------------------------------------------------------
# d06.challenge_registry_validator entrypoint
# ---------------------------------------------------------------------------


ENTRYPOINTS["d06.challenge_registry_validator"] = lambda fixture: _REGISTRY_RUNTIME(
    fixture
)


def _REGISTRY_RUNTIME(fixture: D06Fixture) -> D06ChallengeOutcome:
    """Runtime ``d06.challenge_registry_validator`` entrypoint."""
    from .efficacy_evaluator import EfficacyEngine

    return EfficacyEngine(fixture, "d06.challenge_registry_validator").run_registry()


def validate_challenge_registry_input(
    fixture: D06Fixture,
) -> D06ChallengeOutcome:
    """Test-surface alias of the runtime registry validator."""
    from .efficacy_evaluator import validate_challenge_registry_input as _impl

    return _impl(fixture)


ENTRYPOINTS["d06.challenge_registry_validator"] = _REGISTRY_RUNTIME
