"""Read-only loader and verifier for the frozen R6 v0.1 machine contract.

Loads, in read-only mode, the two accepted contract artifacts:

* ``artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json``
* ``artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json``

and the frozen prose contract:

* ``reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md``

Verification checks (all deterministic, stdlib-only, no file writes):

* stable-byte SHA-256 identity against the accepted record
  (``context/medical_monitoring_r6_contract_acceptance_record_20260827.md``);
* contract identity and cross-file bindings
  (``contract_id``/``contract_version``/``challenge_matrix_binding``);
* structural contract counts (3 modes, 3 pieces, 9 unit types, 8 claim
  statuses, 5 coverage statuses, 16 output kinds, 11 validators, 16
  prohibitions);
* challenge matrix shape: 86 unique rows (R6C-001..R6C-086), 12 category
  counts, P0/P1/P2 severity counts, one ``replace`` mutation per row,
  RFC 6901 pointer well-formedness, expected-outcome grammar, and the
  reject/block error-code rule;
* the 49-diagnostic-code map: every ``error_semantics`` code occurs exactly
  once in ``error_code_map`` and binds to one validator id, one canonical
  failure code of that validator, and a blocking flag; no row may reference
  an undeclared diagnostic code.

This module never writes, never mutates the artifacts, and never produces
medical conclusions.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

#: Workbench repository root (three levels above the consolidated package).
WORKBENCH_ROOT: Path = Path(__file__).resolve().parents[3]

CONTRACT_DIR: Path = (
    WORKBENCH_ROOT
    / "artifacts"
    / "medical_monitoring_r6_external_report_mode_output_contract_v0_1"
)

CONTRACT_REL_PATH = (
    "artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json"
)
MATRIX_REL_PATH = (
    "artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json"
)
PROSE_REL_PATH = (
    "reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md"
)

# Accepted stable-byte SHA-256 values from
# context/medical_monitoring_r6_contract_acceptance_record_20260827.md
# (ACCEPT_R6_CONTRACT_V0_1_FOR_SYNTHETIC_OFFLINE_PLANNING, 2026-08-27).
ACCEPTED_CONTRACT_SHA256 = (
    "0fca738c19277777de25ce819285ace2e836b2e323e581ce04f52608ce0ed1d7"
)
ACCEPTED_MATRIX_SHA256 = (
    "cb5b30bc8397e022efff6bc7e57b4d23b99f1debff1c405879e42e698444b2dc"
)
ACCEPTED_PROSE_SHA256 = (
    "1c6fc588335206020389527bf0841bbf57abe227dbea46a2420c0456ed2f1acd"
)

EXPECTED_CONTRACT_ID = "medical_monitoring_r6_external_report_mode_output_contract"
EXPECTED_CONTRACT_VERSION = "0.1"
EXPECTED_MATRIX_SCHEMA = (
    "medical-monitoring-r6-external-report-mode-challenge-matrix-v0.1"
)
EXPECTED_ROW_COUNT = 86
EXPECTED_DIAGNOSTIC_CODE_COUNT = 49
EXPECTED_VALIDATOR_COUNT = 11
EXPECTED_PROHIBITION_COUNT = 16

_CHALLENGE_ID_RE = re.compile(r"^R6C-(\d{3})$")
_OUTCOME_GRAMMAR_RE = re.compile(
    r"^(?P<head>accept|record|reject|block):(?P<token>[A-Za-z0-9_]+)$"
)
_PLACEHOLDER_TOKENS = frozenset(
    {
        "",
        "TODO",
        "PLACEHOLDER",
        "FIXME",
        "XXX",
        "NULL",
        "UNDEFINED",
        "<PLACEHOLDER>",
        "...",
    }
)


class ContractVerificationError(RuntimeError):
    """Raised when a frozen contract artifact fails any verification check."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_bytes(path: Path) -> bytes:
    """Read a file in read-only mode and return its raw bytes."""
    return Path(path).read_bytes()


def check_stable_bytes(raw: bytes, expected_sha256: str, label: str) -> None:
    actual = sha256_hex(raw)
    if actual != expected_sha256:
        raise ContractVerificationError(
            f"stable_bytes:{label}: sha256 mismatch "
            f"expected={expected_sha256} actual={actual}"
        )


def contract_path() -> Path:
    return WORKBENCH_ROOT / CONTRACT_REL_PATH


def matrix_path() -> Path:
    return WORKBENCH_ROOT / MATRIX_REL_PATH


def prose_path() -> Path:
    return WORKBENCH_ROOT / PROSE_REL_PATH


def contract_raw() -> bytes:
    raw = load_bytes(contract_path())
    check_stable_bytes(raw, ACCEPTED_CONTRACT_SHA256, "contract.json")
    return raw


def matrix_raw() -> bytes:
    raw = load_bytes(matrix_path())
    check_stable_bytes(raw, ACCEPTED_MATRIX_SHA256, "challenge_matrix.json")
    return raw


def contract_obj(raw: bytes | None = None) -> dict:
    if raw is None:
        raw = contract_raw()
    return json.loads(raw.decode("utf-8"))


def matrix_obj(raw: bytes | None = None) -> dict:
    if raw is None:
        raw = matrix_raw()
    return json.loads(raw.decode("utf-8"))


def _fail(check: str, detail: str) -> "ContractVerificationError":
    return ContractVerificationError(f"{check}:{detail}")


# ---------------------------------------------------------------------------
# contract.json structure
# ---------------------------------------------------------------------------

def verify_contract_object(contract: dict) -> None:
    """Verify identity, structural counts, enums, validators, prohibitions."""
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise _fail("contract_identity", f"contract_id={contract.get('contract_id')!r}")
    if contract.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        raise _fail(
            "contract_identity", f"contract_version={contract.get('contract_version')!r}"
        )

    counts = contract.get("contract_counts", {})
    enums = contract.get("enums", {})
    expected_enum_counts = {
        "mode_count": ("mode", 3),
        "three_piece_count": ("piece_type", 3),
        "report_unit_type_count": ("report_unit_type", 9),
        "claim_status_count": ("claim_status", 8),
        "coverage_status_count": ("coverage_status", 5),
        "output_kind_count": ("output_kind", 16),
    }
    for field, (enum_name, expected) in expected_enum_counts.items():
        values = enums.get(enum_name)
        if not isinstance(values, list) or len(values) != expected:
            raise _fail(
                f"count_{field}",
                f"enums.{enum_name} length={len(values) if isinstance(values, list) else type(values).__name__} "
                f"expected={expected}",
            )
        if len(set(values)) != len(values):
            raise _fail(f"count_{field}", f"enums.{enum_name} contains duplicates")
        if any(not isinstance(v, str) or not v for v in values):
            raise _fail(f"count_{field}", f"enums.{enum_name} contains non-string/empty values")
        if counts.get(field) != expected:
            raise _fail(
                f"count_{field}", f"contract_counts.{field}={counts.get(field)!r} expected={expected}"
            )

    validators = contract.get("deterministic_validators")
    if not isinstance(validators, list) or len(validators) != EXPECTED_VALIDATOR_COUNT:
        raise _fail(
            "count_deterministic_validator_count",
            f"len(deterministic_validators)={len(validators) if isinstance(validators, list) else type(validators).__name__} "
            f"expected={EXPECTED_VALIDATOR_COUNT}",
        )
    validator_ids = [v.get("id") for v in validators]
    if len(set(validator_ids)) != len(validator_ids):
        raise _fail("validator_ids_unique", f"duplicate validator ids: {validator_ids}")
    for v in validators:
        codes = v.get("failure_codes")
        if not isinstance(codes, list) or not codes or any(
            not isinstance(c, str) or not c for c in codes
        ):
            raise _fail("validator_failure_codes", f"validator {v.get('id')!r} has empty/invalid failure_codes")
        if not v.get("check") or not v.get("effect"):
            raise _fail("validator_fields", f"validator {v.get('id')!r} missing check/effect")
    if counts.get("deterministic_validator_count") != EXPECTED_VALIDATOR_COUNT:
        raise _fail(
            "count_deterministic_validator_count",
            f"contract_counts.deterministic_validator_count={counts.get('deterministic_validator_count')!r} "
            f"expected={EXPECTED_VALIDATOR_COUNT}",
        )

    prohibitions = contract.get("prohibitions")
    if not isinstance(prohibitions, list) or len(prohibitions) != EXPECTED_PROHIBITION_COUNT:
        raise _fail(
            "count_prohibition_count",
            f"len(prohibitions)={len(prohibitions) if isinstance(prohibitions, list) else type(prohibitions).__name__} "
            f"expected={EXPECTED_PROHIBITION_COUNT}",
        )
    if len(set(prohibitions)) != len(prohibitions):
        raise _fail("prohibitions_unique", "duplicate prohibition entries")
    if counts.get("prohibition_count") != EXPECTED_PROHIBITION_COUNT:
        raise _fail(
            "count_prohibition_count",
            f"contract_counts.prohibition_count={counts.get('prohibition_count')!r} "
            f"expected={EXPECTED_PROHIBITION_COUNT}",
        )

    for key in (
        "scope",
        "objective",
        "hard_boundaries",
        "identity_rules",
        "objects",
        "state_semantics",
        "claim_issue_coverage",
        "three_piece_bundle",
        "mode_contracts",
        "mode_transition_rules",
        "output_contract",
        "numeric_reconciliation_policy",
        "implementation_allowlist",
        "challenge_matrix_binding",
    ):
        if key not in contract:
            raise _fail("contract_sections", f"missing required section {key!r}")


# ---------------------------------------------------------------------------
# challenge_matrix.json structure
# ---------------------------------------------------------------------------

def _pointer_is_well_formed(pointer: str) -> bool:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return False
    if pointer == "/":
        return True
    if pointer.endswith("/") or "//" in pointer:
        return False
    return True


def _is_placeholder(value) -> bool:
    return isinstance(value, str) and value.upper() in _PLACEHOLDER_TOKENS


def verify_matrix_object(matrix: dict, contract: dict) -> None:
    """Verify the 86-row challenge matrix against its row contract."""
    if matrix.get("schema") != EXPECTED_MATRIX_SCHEMA:
        raise _fail("matrix_identity", f"schema={matrix.get('schema')!r}")
    if matrix.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise _fail("matrix_identity", f"contract_id={matrix.get('contract_id')!r}")
    if matrix.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        raise _fail("matrix_identity", f"contract_version={matrix.get('contract_version')!r}")

    rows = matrix.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROW_COUNT:
        raise _fail(
            "row_count",
            f"len(rows)={len(rows) if isinstance(rows, list) else type(rows).__name__} "
            f"expected={EXPECTED_ROW_COUNT}",
        )
    if matrix.get("row_count") != EXPECTED_ROW_COUNT:
        raise _fail("row_count", f"matrix.row_count={matrix.get('row_count')!r} expected={EXPECTED_ROW_COUNT}")

    row_contract = matrix.get("row_contract", {})
    required_fields = row_contract.get("required_fields", [])
    allowed_ops = row_contract.get("allowed_mutation_ops", ["replace"])
    projection_values = set(row_contract.get("expected_projection_values", []))
    error_semantics = matrix.get("error_semantics", {})

    seen_ids = set()
    for row in rows:
        cid = row.get("challenge_id", "<missing>")
        for field in required_fields:
            if field not in row:
                raise _fail("row_required_fields", f"row {cid} missing field {field!r}")
        m = _CHALLENGE_ID_RE.match(cid)
        if not m or not (1 <= int(m.group(1)) <= EXPECTED_ROW_COUNT):
            raise _fail("challenge_id_format", f"invalid challenge_id {cid!r}")
        if cid in seen_ids:
            raise _fail("challenge_id_unique", f"duplicate challenge_id {cid!r}")
        seen_ids.add(cid)

        mutation = row["single_mutation"]
        for field in ("op", "path", "value"):
            if field not in mutation:
                raise _fail("single_mutation_fields", f"row {cid} missing single_mutation.{field}")
        if mutation["op"] not in allowed_ops:
            raise _fail("mutation_op_replace_only", f"row {cid} op={mutation['op']!r}")
        if not _pointer_is_well_formed(mutation["path"]):
            raise _fail("pointer_well_formed", f"row {cid} path={mutation['path']!r}")
        if not mutation["path"].startswith("/candidate/"):
            raise _fail("pointer_candidate_root", f"row {cid} path={mutation['path']!r}")
        if _is_placeholder(mutation["value"]) or _is_placeholder(row.get("target", "")):
            raise _fail(
                "placeholder_mutations_forbidden", f"row {cid} contains a placeholder value"
            )

        outcome = row["expected_outcome"]
        om = _OUTCOME_GRAMMAR_RE.match(outcome) if isinstance(outcome, str) else None
        if not om:
            raise _fail("outcome_grammar", f"row {cid} expected_outcome={outcome!r}")
        head, token = om.group("head"), om.group("token")
        expected_error = row["expected_error"]
        if head in ("accept", "record"):
            if expected_error is not None:
                raise _fail(
                    "error_rule",
                    f"row {cid} {head} row must have expected_error=null, got {expected_error!r}",
                )
            if not re.match(r"^[a-z][a-z0-9_]*$", token):
                raise _fail("outcome_grammar", f"row {cid} accept/record token {token!r} not lowercase_snake")
        else:  # reject | block
            if expected_error != token:
                raise _fail(
                    "error_rule",
                    f"row {cid} expected_outcome token {token!r} != expected_error {expected_error!r}",
                )
            if expected_error not in error_semantics:
                raise _fail(
                    "declared_diagnostic_only",
                    f"row {cid} references undeclared diagnostic code {expected_error!r}",
                )

        if row["expected_projection"] not in projection_values:
            raise _fail(
                "projection_values",
                f"row {cid} expected_projection={row['expected_projection']!r} not in row_contract set",
            )
        if row["severity"] not in ("P0", "P1", "P2"):
            raise _fail("severity_values", f"row {cid} severity={row['severity']!r}")
        if not isinstance(row["oracle"], str) or not row["oracle"]:
            raise _fail("oracle_present", f"row {cid} oracle missing/empty")
        if row["test_metadata_only"] is not True:
            raise _fail("test_metadata_only", f"row {cid} test_metadata_only is not true")

    expected_ids = {f"R6C-{i:03d}" for i in range(1, EXPECTED_ROW_COUNT + 1)}
    if seen_ids != expected_ids:
        missing = sorted(expected_ids - seen_ids)
        extra = sorted(seen_ids - expected_ids)
        raise _fail("challenge_id_unique", f"missing={missing} extra={extra}")

    from collections import Counter

    category_counts = matrix.get("category_counts", {})
    actual_categories = Counter(row["category"] for row in rows)
    if dict(actual_categories) != category_counts:
        raise _fail(
            "category_counts",
            f"matrix.category_counts={category_counts} actual={dict(actual_categories)}",
        )
    severity_counts = matrix.get("severity_counts", {})
    actual_severities = Counter(row["severity"] for row in rows)
    if dict(actual_severities) != severity_counts:
        raise _fail(
            "severity_counts",
            f"matrix.severity_counts={severity_counts} actual={dict(actual_severities)}",
        )

    _verify_diagnostic_map(matrix, contract)


def _verify_diagnostic_map(matrix: dict, contract: dict) -> None:
    error_semantics = matrix.get("error_semantics", {})
    code_map = matrix.get("error_code_map", [])
    if not isinstance(code_map, list):
        raise _fail("diagnostic_map_bidirectional", "error_code_map is not a list")

    map_codes = [c for entry in code_map for c in entry.get("diagnostic_codes", [])]
    if len(map_codes) != len(set(map_codes)):
        raise _fail(
            "diagnostic_map_bidirectional",
            f"diagnostic code occurs more than once in error_code_map: "
            f"{sorted(c for c in map_codes if map_codes.count(c) > 1)}",
        )
    semantics_keys = set(error_semantics.keys())
    if set(map_codes) != semantics_keys:
        raise _fail(
            "diagnostic_map_bidirectional",
            f"in map not semantics={sorted(set(map_codes) - semantics_keys)} "
            f"in semantics not map={sorted(semantics_keys - set(map_codes))}",
        )
    if len(semantics_keys) != EXPECTED_DIAGNOSTIC_CODE_COUNT:
        raise _fail(
            "diagnostic_map_bidirectional",
            f"error_semantics has {len(semantics_keys)} codes, "
            f"expected {EXPECTED_DIAGNOSTIC_CODE_COUNT}",
        )

    validators = {
        v["id"]: set(v["failure_codes"]) for v in contract.get("deterministic_validators", [])
    }
    seen_bindings = set()
    for entry in code_map:
        vid = entry.get("validator_id")
        fcode = entry.get("failure_code")
        if vid not in validators:
            raise _fail("map_validator_binding", f"unknown validator_id {vid!r}")
        if fcode not in validators[vid]:
            raise _fail(
                "map_validator_binding",
                f"failure_code {fcode!r} not declared by validator {vid!r}",
            )
        if entry.get("blocking") is not True:
            raise _fail("map_validator_binding", f"entry {vid}/{fcode} blocking is not true")
        key = (vid, fcode)
        if key in seen_bindings:
            raise _fail("map_validator_binding", f"duplicate binding {key}")
        seen_bindings.add(key)


def verify_identity(contract: dict, matrix: dict) -> None:
    """Cross-file identity bindings between contract and challenge matrix."""
    if matrix.get("contract_id") != contract.get("contract_id"):
        raise _fail(
            "identity_bindings",
            f"matrix.contract_id={matrix.get('contract_id')!r} "
            f"contract.contract_id={contract.get('contract_id')!r}",
        )
    if matrix.get("contract_version") != contract.get("contract_version"):
        raise _fail(
            "identity_bindings",
            f"matrix.contract_version={matrix.get('contract_version')!r} "
            f"contract.contract_version={contract.get('contract_version')!r}",
        )

    binding = contract.get("challenge_matrix_binding", {})
    if binding.get("artifact_path") != MATRIX_REL_PATH:
        raise _fail(
            "identity_bindings",
            f"challenge_matrix_binding.artifact_path={binding.get('artifact_path')!r} "
            f"expected={MATRIX_REL_PATH!r}",
        )
    for field in binding.get("required_challenge_fields", []):
        if field not in matrix:
            raise _fail("identity_bindings", f"matrix missing required field {field!r}")
    for ref in binding.get("required_contract_refs", []):
        node = contract
        for part in ref.split("."):
            if not isinstance(node, dict) or part not in node:
                raise _fail("identity_bindings", f"contract ref {ref!r} not resolvable")
            node = node[part]

    row_contract = matrix.get("row_contract", {})
    anchor = row_contract.get("required_non_llm_anchor")
    if anchor != "python-stdlib-deterministic-verifier":
        raise _fail(
            "identity_bindings",
            f"row_contract.required_non_llm_anchor={anchor!r} "
            "expected='python-stdlib-deterministic-verifier'",
        )


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------

def contested_paths(rows: list) -> list:
    """Paths whose baseline_value differs across rows (fixture-per-challenge)."""
    values_by_path: dict = {}
    for row in rows:
        values_by_path.setdefault(row["single_mutation"]["path"], set()).add(
            json.dumps(row["baseline_value"], sort_keys=True, ensure_ascii=False)
        )
    return sorted(p for p, values in values_by_path.items() if len(values) > 1)


def verify_all(contract: dict, matrix: dict) -> dict:
    """Run every check; return a machine-readable report dict.

    Raises :class:`ContractVerificationError` on the first failed check.
    """
    verify_contract_object(contract)
    verify_matrix_object(matrix, contract)
    verify_identity(contract, matrix)
    return {
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "row_count": len(matrix["rows"]),
        "validator_ids": [v["id"] for v in contract["deterministic_validators"]],
        "diagnostic_code_count": len(matrix["error_semantics"]),
        "category_counts": matrix["category_counts"],
        "severity_counts": matrix["severity_counts"],
        "contested_paths": contested_paths(matrix["rows"]),
        "checks": {
            "contract_object": True,
            "matrix_object": True,
            "identity_bindings": True,
        },
    }
