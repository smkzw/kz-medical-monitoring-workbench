"""R5 S1 W3 -- frozen S1 challenge tests, ``authority_identity`` (R5C-001..008).

Executes the challenge-registry locators
``tests/challenges/test_authority_identity.py::test_{project_ref,run_ref,
snapshot_ref,cutoff_ref,projection_id,projection_content_hash,
evaluation_content_identity,audience_contract_id}`` against REAL R4 typed
fixtures (the read-only R4 test-artifact flow, identical to the R4
oracle-parity suite) and the actual ``mm_r5.authority_adapter``
build/verify functions.

Per frozen rule (``exact_contract.json`` challenge_rules /
``challenge_registry.json``): every case mutates exactly ONE typed authority
fact with the frozen ``mutated_value``, then proves
``build_authority_receipt`` emits NO receipt (fail-closed
``AuthorityReceiptError`` carrying the reason codes) and that the declared
slot reason is the cause -- cross-checked by ``verify_authority_receipt``
returning the same codes for the same tampered typed objects.

Declared-slot -> adapter-code mapping (the adapter emits the exact frozen
slot reason; it may also emit a broader integrity reason):

    R5C-001 authority_identity.project_ref
            -> authority_identity.project_ref            (typed.project_ref)
    R5C-002 authority_identity.run_ref
            -> authority_identity.run_ref                (typed.run_ref)
    R5C-003 authority_identity.snapshot_ref
            -> authority_identity.snapshot_ref           (typed.snapshot_ref)
    R5C-004 authority_identity.cutoff_ref
            -> authority_identity.cutoff_ref             (version.cutoff_ref)
    R5C-005 authority_identity.projection_id
            -> authority_identity.projection_id           (projection.projection_id)
    R5C-006 authority_identity.projection_content_hash
            -> authority_identity.projection_content_hash (projection.projection_content_hash)
    R5C-007 authority_identity.evaluation_content_identity
            -> authority_identity.evaluation_content_identity
               (version.source_evaluation_content_identities)
    R5C-008 authority_identity.audience_contract_id
            -> authority_identity.audience_contract_id   (typed.audience_text.audience_contract_id)

No mutation label, case id or test name is ever used as semantic proof: the
adapter rejects because the typed binding/hash actually broke, and every
test proves the rejection through ``build_authority_receipt`` raising and
``verify_authority_receipt`` failing with the mapped reason codes.

Adjacent deterministic separation check (same file): a valid receipt proves
identity/content binding only -- it is NOT permission to display an R4
projection whose own integrity/disposition gate blocks audience emission.
Ten real R4 fixtures (D10-CASE-078/093/110/125/126/157/245/286/287/295)
carry internally consistent typed envelopes, so the receipt builds, yet the
R4 evaluation's own integrity gate (``integrity_gate``) blocks audience
emission: the R4 audience projection carries no payload and the frozen
Chinese disposition text says no medical evaluation was produced.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

_POC_ROOT = Path(__file__).resolve().parents[3]
_R5_SRC = Path(__file__).resolve().parents[2] / "src"
_R4_SRC = _POC_ROOT / "medical_monitoring_ai_native_r4" / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC, _R5_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as r4_adapter  # noqa: E402
from mm_r4 import d10_evaluator as r4_evaluator  # noqa: E402
from mm_r4 import d10_projection as r4_projection  # noqa: E402
from mm_r5.authority_adapter import (  # noqa: E402
    AuthorityReceiptError,
    build_authority_receipt,
    verify_authority_receipt,
)
from mm_r5.contracts import R5_CONTRACT_SHA256  # noqa: E402

# Frozen S0 artifact identities (see manifest.json / acceptance record).
CHALLENGE_REGISTRY_SHA256 = (
    "ef459f58ad6997a823c3ff57d51256cdf531b806d9033df636ab2912085b0887")
REGISTRY_PATH = (
    Path(__file__).resolve().parents[4]
    / "artifacts" / "medical_monitoring_r5_contract_v0_3"
    / "challenge_registry.json")

#: declared challenge slot -> adapter reason code(s) implementing it.
DECLARED_TO_ADAPTER: Dict[str, Tuple[str, ...]] = {
    "authority_identity.project_ref": ("authority_identity.project_ref",),
    "authority_identity.run_ref": ("authority_identity.run_ref",),
    "authority_identity.snapshot_ref": ("authority_identity.snapshot_ref",),
    "authority_identity.cutoff_ref": ("authority_identity.cutoff_ref",),
    "authority_identity.projection_id": ("authority_identity.projection_id",),
    "authority_identity.projection_content_hash": (
        "authority_identity.projection_content_hash",),
    "authority_identity.evaluation_content_identity": (
        "authority_identity.evaluation_content_identity",),
    "authority_identity.audience_contract_id": (
        "authority_identity.audience_contract_id",),
}

# ---------------------------------------------------------------------------
# Frozen R4 artifact loading (read-only, same flow as the R4 test suite)
# ---------------------------------------------------------------------------

_CATALOG_CACHE: Dict[str, Any] = {}


def _r4() -> Tuple[Any, Any]:
    """(catalog, authority) -- frozen R4 artifacts, loaded once."""
    if "catalog" not in _CATALOG_CACHE:
        catalog, _oracle, _registry, _quota = r4_adapter.load_artifacts()
        _CATALOG_CACHE["catalog"] = catalog
        _CATALOG_CACHE["authority"] = r4_adapter.load_authority()
    return _CATALOG_CACHE["catalog"], _CATALOG_CACHE["authority"]


def _bundle(case_id: str) -> Tuple[Any, Any, Any, Any, Any]:
    """Real R4 bundle (typed, version, projection, receipt, result).

    ``receipt`` is the valid receipt of the authoritative bundle: it proves
    the fixture is identity/content-authoritative and is the reference
    receipt the verify cross-check uses against each tampered typed fact.
    """
    catalog, authority = _r4()
    case = next(c for c in catalog["cases"] if c["case_id"] == case_id)
    entry = next(e for e in authority["entries"] if e["case_id"] == case_id)
    typed = r4_adapter.build_typed_input(case["typed_input"])
    result = r4_evaluator.evaluate(typed, r4_adapter.build_authority(entry))
    version = r4_projection.build_d10_projection_version(typed, result)
    projection = r4_projection.build_d10_project_projection(typed, result)
    receipt = build_authority_receipt(typed, version, projection)
    return typed, version, projection, receipt, result


@pytest.fixture(scope="session")
def registry() -> Dict[str, Any]:
    """Frozen challenge registry (read-only, SHA-pinned)."""
    raw = REGISTRY_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CHALLENGE_REGISTRY_SHA256, (
        "challenge_registry.json drifted from the S0 freeze")
    data = json.loads(raw)
    assert data["contract_sha256"] == R5_CONTRACT_SHA256, (
        "registry embedded contract SHA drifted from the S0 freeze")
    return {row["case_id"]: row for row in data["rows"]}


def _registry_case(
    registry: Dict[str, Any],
    case_id: str,
    locator_suffix: str,
    declared_rule_id: str,
) -> Dict[str, Any]:
    """Pin one frozen registry row to its declared locator and reason."""
    row = registry[case_id]
    locator = row["stage_oracle_contract"]["test_locator"]
    assert locator.endswith(locator_suffix), (case_id, locator)
    assert row["stage_oracle_contract"]["rule_id"] == declared_rule_id, case_id
    assert row["expected_typed_outcome_or_error"] == (
        f"reject:{declared_rule_id}"), case_id
    assert row["stage_oracle_contract"]["expected_outcome"] == (
        f"reject:{declared_rule_id}"), case_id
    assert row["stage_oracle_contract"]["expected_projection"] == (
        "not_emitted"), case_id
    assert row["single_mutation"]["op"] == "replace", case_id
    return row


def _assert_rejected_no_receipt(
    typed: Any,
    version: Any,
    projection: Any,
    valid_receipt: Any,
    declared_rule_id: str,
    adapter_codes: Tuple[str, ...],
) -> None:
    """Fail-closed proof for one mutated typed authority fact.

    * ``build_authority_receipt`` raises ``AuthorityReceiptError`` -- the
      only emission channel is the exception, so NO receipt is emitted;
    * the exception message carries every mapped adapter reason code;
    * the declared slot is pinned by the frozen mapping table;
    * ``verify_authority_receipt`` (the reference valid receipt against the
      tampered typed objects) fails closed with the same codes.
    """
    assert DECLARED_TO_ADAPTER[declared_rule_id] == adapter_codes, (
        declared_rule_id, adapter_codes)
    with pytest.raises(AuthorityReceiptError) as excinfo:
        build_authority_receipt(typed, version, projection)
    assert type(excinfo.value) is AuthorityReceiptError
    message = str(excinfo.value)
    for code in adapter_codes:
        assert code in message, (declared_rule_id, code, message)
    result = verify_authority_receipt(
        valid_receipt, typed, version, projection)
    assert result["valid"] is False, declared_rule_id
    for code in adapter_codes:
        assert code in result["reasons"], (
            declared_rule_id, code, result["reasons"])


# ---------------------------------------------------------------------------
# R5C-001..008 -- authority_identity typed-fact mutations
# ---------------------------------------------------------------------------


def test_project_ref(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-001",
        "test_authority_identity.py::test_project_ref",
        "authority_identity.project_ref")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        typed, project_ref=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_identity.project_ref",
        ("authority_identity.project_ref",))


def test_run_ref(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-002",
        "test_authority_identity.py::test_run_ref",
        "authority_identity.run_ref")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        typed, run_ref=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_identity.run_ref",
        ("authority_identity.run_ref",))


def test_snapshot_ref(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-003",
        "test_authority_identity.py::test_snapshot_ref",
        "authority_identity.snapshot_ref")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        typed, snapshot_ref=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_identity.snapshot_ref",
        ("authority_identity.snapshot_ref",))


def test_cutoff_ref(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-004",
        "test_authority_identity.py::test_cutoff_ref",
        "authority_identity.cutoff_ref")
    # Real cutoff bundle: the version cutoff is a non-None window cutoff.
    typed, version, projection, receipt, _ = _bundle("D10-CASE-010")
    assert version.cutoff_ref == "SYN-D10-CUT-010"
    tampered = dataclasses.replace(
        version, cutoff_ref=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        typed, tampered, projection, receipt,
        "authority_identity.cutoff_ref",
        ("authority_identity.cutoff_ref",))


def test_projection_id(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-005",
        "test_authority_identity.py::test_projection_id",
        "authority_identity.projection_id")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        projection, projection_id=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        typed, version, tampered, receipt,
        "authority_identity.projection_id",
        ("authority_identity.projection_id",))


def test_projection_content_hash(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-006",
        "test_authority_identity.py::test_projection_content_hash",
        "authority_identity.projection_content_hash")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        projection, projection_content_hash=row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        typed, version, tampered, receipt,
        "authority_identity.projection_content_hash",
        ("authority_identity.projection_content_hash",))


def test_evaluation_content_identity(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-007",
        "test_authority_identity.py::test_evaluation_content_identity",
        "authority_identity.evaluation_content_identity")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered = dataclasses.replace(
        version,
        source_evaluation_content_identities=(
            row["single_mutation"]["value"],))
    _assert_rejected_no_receipt(
        typed, tampered, projection, receipt,
        "authority_identity.evaluation_content_identity",
        ("authority_identity.evaluation_content_identity",))


def test_audience_contract_id(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-008",
        "test_authority_identity.py::test_audience_contract_id",
        "authority_identity.audience_contract_id")
    typed, version, projection, receipt, _ = _bundle("D10-CASE-001")
    tampered_typed = dataclasses.replace(
        typed,
        audience_text=dataclasses.replace(
            typed.audience_text,
            audience_contract_id=row["single_mutation"]["value"]))
    _assert_rejected_no_receipt(
        tampered_typed, version, projection, receipt,
        "authority_identity.audience_contract_id",
        ("authority_identity.audience_contract_id",))


# ---------------------------------------------------------------------------
# Separation: a valid receipt is NOT permission to emit a gated projection
# ---------------------------------------------------------------------------

#: Real R4 fixtures whose typed envelope is internally consistent (the R5
#: receipt builds and re-verifies) while the R4 evaluation's own integrity
#: gate blocks audience emission.
_INTEGRITY_GATED_WITH_VALID_RECEIPT: Tuple[str, ...] = (
    "D10-CASE-078", "D10-CASE-093", "D10-CASE-110", "D10-CASE-125",
    "D10-CASE-126", "D10-CASE-157", "D10-CASE-245", "D10-CASE-286",
    "D10-CASE-287", "D10-CASE-295",
)

_FROZEN_INTEGRITY_GATE_ZH = "本次未生成医学评价（数据自洽性校验未通过）"


def test_receipt_is_not_display_permission_for_integrity_gated_projection(
) -> None:
    """A valid receipt proves identity/content binding only.

    For every fixture above the receipt is valid (``build_authority_receipt``
    emits it and ``verify_authority_receipt`` accepts it) yet the R4
    evaluation result is ``integrity_gate``: the R4 audience projection
    carries no audience payload and the frozen disposition text states no
    medical evaluation was produced.  The receipt must never be treated as
    permission to display such a projection.
    """
    for case_id in _INTEGRITY_GATED_WITH_VALID_RECEIPT:
        typed, version, projection, receipt, result = _bundle(case_id)
        assert verify_authority_receipt(
            receipt, typed, version, projection)["valid"], case_id
        assert result.disposition_or_gate == "integrity_gate", case_id
        audience = r4_projection.build_d10_audience_projection(typed, result)
        assert audience.audience_payload_present is False, case_id
        assert audience.disposition_zh == _FROZEN_INTEGRITY_GATE_ZH, case_id


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
