"""R5 S1 W3 -- frozen S1 challenge tests, ``authority_visibility``
(R5C-009..016).

Executes the challenge-registry locators
``tests/challenges/test_authority_visibility.py::test_{visibility_decision_id,
visibility_decision_hash,projectable_member,hidden_member,projectable_site,
hidden_site,source_revision,source_content_hash}`` against REAL R4 typed
fixtures (the read-only R4 test-artifact flow) and the actual
``mm_r5.authority_adapter`` build/verify functions.

Per frozen rule (``exact_contract.json`` challenge_rules /
``challenge_registry.json``): every case mutates exactly ONE typed authority
fact with the frozen ``mutated_value``, then proves
``build_authority_receipt`` emits NO receipt (fail-closed
``AuthorityReceiptError`` carrying the reason codes) and that the declared
slot reason is the cause -- cross-checked by ``verify_authority_receipt``
returning the same codes for the same tampered typed objects.

Declared-slot -> adapter-code mapping (the adapter emits the exact frozen
slot reason; it may also emit a broader partition/hash integrity reason):

    R5C-009 authority_visibility.visibility_decision_id
            -> authority_visibility.visibility_decision_id
               (typed.visibility_decision.decision_id)
    R5C-010 authority_visibility.visibility_decision_hash
            -> authority_visibility.visibility_decision_hash
               (decision CONTENT: one decision field is mutated, so the
               decision_id no longer equals the canonical content hash)
    R5C-011 authority_visibility.projectable_member
            -> authority_visibility.projectable_member
               (typed.visibility_decision.projectable_member_refs)
    R5C-012 authority_visibility.hidden_member
            -> authority_visibility.hidden_member
               (typed.visibility_decision.hidden_member_refs)
    R5C-013 authority_visibility.projectable_site
            -> authority_visibility.projectable_site
               (typed.visibility_decision.projectable_site_refs)
    R5C-014 authority_visibility.hidden_site
            -> authority_visibility.hidden_site
               (typed.visibility_decision.hidden_site_refs)
    R5C-015 authority_visibility.source_revision
            -> authority_visibility.source_revision
               (typed.source_revision_content_pairs[0].revision_id)
    R5C-016 authority_visibility.source_content_hash
            -> authority_visibility.source_content_hash
               (typed.source_revision_content_pairs[0].content_hash)

No mutation label, case id or test name is ever used as semantic proof: the
adapter rejects because the typed partition algebra / decision content hash /
source-pair recipe actually broke, and every test proves the rejection
through ``build_authority_receipt`` raising and ``verify_authority_receipt``
failing with the mapped reason codes.  Hidden member/site identities never
enter the receipt: only the decision id/hash and the public partition do
(covered by the W2 hidden-leak tests).
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
    "authority_visibility.visibility_decision_id": (
        "authority_visibility.visibility_decision_id",),
    "authority_visibility.visibility_decision_hash": (
        "authority_visibility.visibility_decision_hash",),
    "authority_visibility.projectable_member": (
        "authority_visibility.projectable_member",),
    "authority_visibility.hidden_member": (
        "authority_visibility.hidden_member",),
    "authority_visibility.projectable_site": (
        "authority_visibility.projectable_site",),
    "authority_visibility.hidden_site": (
        "authority_visibility.hidden_site",),
    "authority_visibility.source_revision": (
        "authority_visibility.source_revision",),
    "authority_visibility.source_content_hash": (
        "authority_visibility.source_content_hash",),
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


def _bundle(case_id: str) -> Tuple[Any, Any, Any, Any]:
    """Real R4 bundle (typed, version, projection, receipt)."""
    catalog, authority = _r4()
    case = next(c for c in catalog["cases"] if c["case_id"] == case_id)
    entry = next(e for e in authority["entries"] if e["case_id"] == case_id)
    typed = r4_adapter.build_typed_input(case["typed_input"])
    result = r4_evaluator.evaluate(typed, r4_adapter.build_authority(entry))
    version = r4_projection.build_d10_projection_version(typed, result)
    projection = r4_projection.build_d10_project_projection(typed, result)
    receipt = build_authority_receipt(typed, version, projection)
    return typed, version, projection, receipt


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


def _mutated_decision(
    typed: Any, field_name: str, value: Any,
) -> Any:
    """Typed copy with exactly ONE visibility-decision fact replaced."""
    return dataclasses.replace(
        typed,
        visibility_decision=dataclasses.replace(
            typed.visibility_decision, **{field_name: value}))


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
# R5C-009..016 -- authority_visibility typed-fact mutations
# ---------------------------------------------------------------------------


def test_visibility_decision_id(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-009",
        "test_authority_visibility.py::test_visibility_decision_id",
        "authority_visibility.visibility_decision_id")
    typed, version, projection, receipt = _bundle("D10-CASE-001")
    tampered = _mutated_decision(
        typed, "decision_id", row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.visibility_decision_id",
        ("authority_visibility.visibility_decision_id",))


def test_visibility_decision_hash(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-010",
        "test_authority_visibility.py::test_visibility_decision_hash",
        "authority_visibility.visibility_decision_hash")
    # Real hidden-member case: the decision content is mutated (one decision
    # field), so decision_id no longer equals the canonical content hash of
    # the decision -- the declared hash slot fails closed.
    typed, version, projection, receipt = _bundle("D10-CASE-009")
    assert len(typed.visibility_decision.hidden_member_refs) > 0
    tampered = _mutated_decision(
        typed, "blind_status", row["single_mutation"]["value"])
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.visibility_decision_hash",
        ("authority_visibility.visibility_decision_hash",))


def test_projectable_member(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-011",
        "test_authority_visibility.py::test_projectable_member",
        "authority_visibility.projectable_member")
    typed, version, projection, receipt = _bundle("D10-CASE-009")
    assert len(typed.visibility_decision.projectable_member_refs) > 0
    tampered = _mutated_decision(
        typed, "projectable_member_refs",
        (row["single_mutation"]["value"],))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.projectable_member",
        ("authority_visibility.projectable_member",))


def test_hidden_member(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-012",
        "test_authority_visibility.py::test_hidden_member",
        "authority_visibility.hidden_member")
    typed, version, projection, receipt = _bundle("D10-CASE-009")
    assert len(typed.visibility_decision.hidden_member_refs) > 0
    tampered = _mutated_decision(
        typed, "hidden_member_refs",
        (row["single_mutation"]["value"],))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.hidden_member",
        ("authority_visibility.hidden_member",))


def test_projectable_site(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-013",
        "test_authority_visibility.py::test_projectable_site",
        "authority_visibility.projectable_site")
    typed, version, projection, receipt = _bundle("D10-CASE-009")
    assert len(typed.visibility_decision.projectable_site_refs) > 0
    tampered = _mutated_decision(
        typed, "projectable_site_refs",
        (row["single_mutation"]["value"],))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.projectable_site",
        ("authority_visibility.projectable_site",))


def test_hidden_site(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-014",
        "test_authority_visibility.py::test_hidden_site",
        "authority_visibility.hidden_site")
    typed, version, projection, receipt = _bundle("D10-CASE-262")
    assert len(typed.visibility_decision.hidden_site_refs) == 1
    tampered = _mutated_decision(
        typed, "hidden_site_refs",
        (row["single_mutation"]["value"],))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.hidden_site",
        ("authority_visibility.hidden_site",))


def test_source_revision(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-015",
        "test_authority_visibility.py::test_source_revision",
        "authority_visibility.source_revision")
    typed, version, projection, receipt = _bundle("D10-CASE-001")
    pair = typed.source_revision_content_pairs[0]
    tampered_pair = dataclasses.replace(
        pair, revision_id=row["single_mutation"]["value"])
    tampered = dataclasses.replace(
        typed, source_revision_content_pairs=(tampered_pair,))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.source_revision",
        ("authority_visibility.source_revision",))


def test_source_content_hash(registry: Dict[str, Any]) -> None:
    row = _registry_case(
        registry, "R5C-016",
        "test_authority_visibility.py::test_source_content_hash",
        "authority_visibility.source_content_hash")
    typed, version, projection, receipt = _bundle("D10-CASE-001")
    pair = typed.source_revision_content_pairs[0]
    tampered_pair = dataclasses.replace(
        pair, content_hash=row["single_mutation"]["value"])
    tampered = dataclasses.replace(
        typed, source_revision_content_pairs=(tampered_pair,))
    _assert_rejected_no_receipt(
        tampered, version, projection, receipt,
        "authority_visibility.source_content_hash",
        ("authority_visibility.source_content_hash",))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
