"""Worker-03 adversarial challenge battery for the R5-S3 offline runtime.

This file attacks the *runtime* (``mm_r5.s3_contracts`` /
``mm_r5.s3_authority_builder`` / ``mm_r5.s3_projection``), not the artifact
generator/verifier suite that ``test_s3_contract_artifacts.py`` owns.  The
contract rules are:

* Every mutation is a real, executable change on real typed objects
  (``dataclasses.replace`` / in-place ``object.__setattr__`` of frozen
  dataclasses), followed by a deterministic **coordinated re-sign** of the
  packet (audience replay hash, single-colon packet id, packet integrity
  hash) so the mutated packet cannot be rejected merely for a stale hash.
  The attack only counts when the projector still rejects the *semantics*
  after a perfect re-sign.
* Assertions use exact typed error codes / exact outcome checks -- never
  label-only assertions.  Where a path is intentionally a no-op (hidden-only
  private change, unit-order canonicalization, replay stability) the test
  asserts the *positive* identity properties instead (replay unchanged,
  integrity changed).
* The battery does not weaken itself for the implementation: no "lenient"
  expected code fallbacks.
* The R4 read-only SHA-256 evidence record is validated end-to-end: manifest
  bytes match the freeze, the manifest exactly equals the deterministic R4
  import closure of the S3 modules observed in a *fresh* interpreter, and
  hashes are re-checked before and after this file runs.

Minimum challenge families covered (assignment spec):
project/run/snapshot/cutoff/visibility/source/receipt drift; coordinated
packet re-sign; caller payload/hash echo; high/medium omission or
reassignment; low-cluster loss/merge/stale; hidden member/site leakage;
resolved/current/closure drift; change kind/cause misprojection; mixed
cause; count-layer cross-sum; member duplication/dangling/cross-unit refs;
denominator positive/zero/unknown/unclosed/exclusion; coverage
partial/truncated/unknown/not-applicable; cutoff/evaluation-limit drift; D09
pattern vs D10 individual and singleton upgrade; wrong site/domain/
classification; stable-order/replay; forbidden score/rank/top-N schema; no
nearest fallback.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import replace as dc_replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

_POC_ROOT = Path(__file__).resolve().parents[2]
for _src in (
    _POC_ROOT / "medical_monitoring_ai_native_r1" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r2" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r3" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r4" / "src",
    Path(__file__).resolve().parents[1] / "src",
):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import mm_r5.contracts as _r5c  # noqa: E402
from mm_r4.d09_projection import D09ProjectionBundle  # noqa: E402
from mm_r4.d10_projection import (  # noqa: E402
    D10ProjectionBundle,
    D10ProjectProjection,
)
from mm_r5 import s3_authority_builder as b  # noqa: E402
from mm_r5 import s3_contracts as c  # noqa: E402
from mm_r5 import s3_projection as p  # noqa: E402

R4_MMR4_DIR = (
    _POC_ROOT.parent / "medical_monitoring_ai_native_r4" / "src" / "mm_r4")
EVIDENCE_PATH = (
    _POC_ROOT / "evidence" / "r4_s3_readonly_sha256.json")


# ---------------------------------------------------------------------------
# Deterministic packet rebuild / fixture helpers
# ---------------------------------------------------------------------------


def _resign(packet: c.R5S3AuthorityPacket) -> c.R5S3AuthorityPacket:
    """Coordinated re-sign: recompute audience replay hash, single-colon
    packet id and packet integrity hash after an in-place mutation so the
    mutated packet is the best-case attacker output (never a stale-hash
    reject)."""
    expected_replay = c.audience_replay_content_hash(
        packet.audience_payload)
    object.__setattr__(packet, "audience_replay_content_hash",
                       expected_replay)
    object.__setattr__(packet, "packet_id",
                       c.PACKET_ID_PREFIX + ":" + expected_replay)
    object.__setattr__(packet, "packet_integrity_hash",
                       c.compute_packet_integrity_hash(packet))
    return packet


def _recompute_supplemental_hash(obj: Any) -> None:
    """Object-level perfect re-sign for one named supplemental: recompute the
    object's own canonical ``content_hash`` after a semantic-field mutation so
    the runtime's ``supplemental_content_hash_mismatch`` gate is not what the
    test exercises.  The semantic (authority/closure/domain/marker) checks are
    the real target; a stale object hash would mask them."""
    expected = c.s3_content_hash_excluding(obj, ("content_hash",))
    object.__setattr__(obj, "content_hash", expected)


def extra_d10(label: str, priority: str = "high",
              change_kind: str = "continued",
              change_cause: Optional[str] = "data") -> b.S3SyntheticUnit:
    """One deterministic extra D10 public unit (see worker_02's projection
    test for the same construction; kept local so this file is
    self-contained)."""
    members = (f"S3-MEMBER-{label}-001", f"S3-MEMBER-{label}-002")
    site = f"S3-SITE-{label}"
    subject = f"S3-SUBJ-{label}"
    marker = b._build_d10_marker(label, members)
    handoff = b._build_d10_handoff(
        label, "continue", priority, members, b.SYNTHETIC_PRIOR_INSTANCE_D10)
    audience = b._build_d10_audience(f"S3-SCOPE-{label}", members, site)
    counts = b._build_d10_counts(label, members, site)
    version = b._build_d10_version(label)
    center = b._build_d10_center_row(site, members)
    hotspot = b._build_d10_hotspot(label, site, subject, members, priority)
    trend = b._build_d10_trend(label)
    section = dc_replace(
        b._build_d10_change_section(),
        change_kind=change_kind, change_cause=change_cause)
    projection = D10ProjectProjection(
        projection_id=f"S3-PROJECTION-{label}",
        projection_version_ref=version.projection_version_id,
        change_section=section,
        center_distribution=(center,),
        trend_surface=trend,
        warning_markers=(),
        risk_marker_ref=marker.marker_id,
        hotspot_site_refs=(site,),
        hotspot_subject_refs=(subject,),
        count_surface_ref=b._fixture_hash(f"count.{label}"),
        coverage_refs=(),
        deep_link_target_refs=(),
        query_draft_ref=None,
        r2_handoff_ref=handoff.handoff_id,
        audience_text_ref=b.SYNTHETIC_AUDIENCE_CONTRACT_ID,
        projection_content_hash=b._fixture_hash(f"projection.{label}"),
    )
    bundle = D10ProjectionBundle(
        audience=audience,
        counts=counts,
        version=version,
        change_section=section,
        center_distribution=(center,),
        trend_surface=trend,
        warning_markers=(),
        risk_marker=marker,
        hotspots=(hotspot,),
        deep_links=(),
        query_draft=None,
        r2_handoff=handoff,
        project_projection=projection,
    )
    return b.S3SyntheticUnit(
        "d10", f"S3-UNIT-{label}", bundle,
        b._build_receipt("d10", f"S3-U-{label}"), "mh", "d10")


def packet_from_units(units_in: Tuple[Any, ...]) -> c.R5S3AuthorityPacket:
    """Assemble a fully supplemental packet from synthetic units through the
    public builder API (mirrors worker_02's helper)."""
    domain_ids = {unit.unit_ref: b._domain_authority_id(unit)
                  for unit in units_in}
    domains = tuple(
        b.build_clinical_domain_authority(
            domain_ids[unit.unit_ref], unit.clinical_domain, unit.receipt)
        for unit in units_in)
    units = tuple(
        b.build_authority_unit(unit, domain_ids[unit.unit_ref])
        for unit in units_in)
    aggregate = b.build_aggregate_receipt_set(units)
    lifecycles: List[Any] = []
    closures: List[Any] = []
    for unit, unit_in in zip(units, units_in):
        variant = c.unit_variant_payload(unit)
        marker = variant.risk_marker
        handoff = variant.r2_handoff
        assert marker is not None and handoff is not None
        if unit_in.kind == "d09" and \
                unit.unit_ref == b.SYNTHETIC_UNIT_D09_RESOLVED_REF:
            closure = b.build_closure_authority(
                "S3-CLOSURE-D09-002", "S3-CLOSE-DECISION-D09-002",
                c.D09_MARKER_PREFIX + marker.marker_id,
                b.SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED,
                unit.authority_receipt)
            closures.append(closure)
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind="d09", marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ids[unit.unit_ref],
                receipt=unit.authority_receipt,
                closure_authority_ref=closure.closure_authority_id,
                prior_marker_identity_ref=c.D09_MARKER_PREFIX
                + marker.marker_id)
        else:
            prior = (c.D10_MARKER_PREFIX + marker.marker_id
                     if unit_in.kind == "d10" else None)
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind=unit_in.kind, marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ids[unit.unit_ref],
                receipt=unit.authority_receipt,
                prior_marker_identity_ref=prior)
        lifecycles.append(lifecycle)
    first = units[0].authority_receipt
    return b.assemble_packet(
        units, aggregate,
        tuple(sorted(lifecycles, key=lambda item: item.marker_identity_ref)),
        tuple(closures),
        tuple(sorted(domains, key=lambda item: item.authority_id)),
        (), (),
        (b.build_cutoff_authority("S3-CUTOFF-AUTHORITY-001",
                                  b.SYNTHETIC_CUTOFF_REF, first),),
        (b.build_evaluation_limit_authority(
            "S3-EVALLIMIT-AUTHORITY-001",
            (b.SYNTHETIC_EVALUATION_LIMIT_D10,),
            (b.SYNTHETIC_EVALUATION_LIMIT_D10,), first),),
        (b.build_coverage_authority("S3-COVERAGE-AUTHORITY-001", "complete",
                                    first),),
        (b.build_change_cause_mixture_authority(
            "S3-CHANGE-CAUSE-MIXTURE-001", ("data", "coverage"), first),),
    )


def assert_rejected(label: str, mutate: Callable[[Any], None],
                    expected_code: str,
                    surface: str = "surface") -> None:
    """Mutate a fresh packet, re-sign it, project it and require the exact
    typed fail-closed error code (S3ProjectionError.error_code)."""
    packet = b.build_s3_authority_packet()
    mutate(packet)
    _resign(packet)
    try:
        if surface == "surface":
            p.project_surface(packet)
        elif surface == "planes":
            p.project_current_risk_planes(packet)
        elif surface == "bands":
            p.project_change_bands(packet)
        elif surface == "cells":
            p.project_center_cells(packet)
        elif surface == "layers":
            p.project_quantity_layers(packet)
        elif surface == "cockpit":
            p.project_cockpit(packet)
        else:  # pragma: no cover - programmer error in test table
            raise AssertionError(f"unknown surface {surface!r}")
    except p.S3ProjectionError as error:
        assert error.error_code == expected_code, (
            f"{label}: expected {expected_code!r}, got {error.error_code!r}: "
            f"{error}")
        return
    except (_r5c.R5ContractError, c.S3ContractError) as error:
        raise AssertionError(
            f"{label}: expected projection error {expected_code!r} but the "
            f"typed contract rejected construction instead: {type(error)} "
            f"{error}") from error
    raise AssertionError(
        f"{label}: expected fail-closed {expected_code!r} but the mutated, "
        f"re-signed packet projected without error")


# ---------------------------------------------------------------------------
# R4 read-only SHA-256 evidence gate (worker_03 artifact)
# ---------------------------------------------------------------------------


def _fresh_import_closure() -> Dict[str, str]:
    """Compute the deterministic R4 transitive import closure of the three S3
    modules in a FRESH interpreter (no pre-imported mm_r4 state)."""
    script = (
        "import sys, hashlib, json\n"
        "from pathlib import Path\n"
        "import mm_r5.s3_contracts, mm_r5.s3_authority_builder, "
        "mm_r5.s3_projection\n"
        "r4 = Path('..')/'medical_monitoring_ai_native_r4'/'src'/'mm_r4'\n"
        "out = {}\n"
        "for _n, _m in sorted(sys.modules.items()):\n"
        "    _f = getattr(_m, '__file__', None)\n"
        "    if not _f:\n"
        "        continue\n"
        "    _f = Path(_f).resolve()\n"
        "    if str(_f).startswith(str(r4.resolve())):\n"
        "        _rel = str(_f.relative_to(r4.resolve()))\n"
        "        out[_rel] = hashlib.sha256(_f.read_bytes()).hexdigest()\n"
        "print(json.dumps(out, sort_keys=True))\n"
    )
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = os_pathsep_join(
        [str(_POC_ROOT / "src"),
         str(_POC_ROOT.parent / "medical_monitoring_ai_native_r1" / "src"),
         str(_POC_ROOT.parent / "medical_monitoring_ai_native_r2" / "src"),
         str(_POC_ROOT.parent / "medical_monitoring_ai_native_r3" / "src"),
         str(_POC_ROOT.parent / "medical_monitoring_ai_native_r4" / "src")])
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=str(_POC_ROOT), env=env,
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, (
        "fresh-interpreter R4 closure probe failed:\n"
        + result.stdout + result.stderr)
    return json.loads(result.stdout.strip().splitlines()[-1])


def os_pathsep_join(paths: List[str]) -> str:
    import os
    return os.pathsep.join(paths)


with EVIDENCE_PATH.open(encoding="utf-8") as _fh:
    _EVIDENCE_DATA = json.load(_fh)

BEFORE_MODULE_HASHES = {
    name: hashlib.sha256((R4_MMR4_DIR / name).read_bytes()).hexdigest()
    for name in sorted(_EVIDENCE_DATA["files"])}


def test_r4_s3_evidence_schema_and_scope() -> None:
    assert _EVIDENCE_DATA["schema"] == (
        "medical-monitoring-r5-s3-readonly-sha256-evidence-v1")
    assert _EVIDENCE_DATA["verification"]["algorithm"] == "sha256"
    assert "d09_projection.py" in _EVIDENCE_DATA["files"]
    assert "d10_projection.py" in _EVIDENCE_DATA["files"]


@pytest.mark.parametrize("name", sorted(_EVIDENCE_DATA["files"]))
def test_r4_s3_manifest_entry_matches_frozen_sha256(name: str) -> None:
    """Every R4 file S3 relies on byte-matches its frozen SHA-256."""
    path = R4_MMR4_DIR / name
    assert path.is_file(), f"missing R4 manifest file: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == _EVIDENCE_DATA["files"][name], (
        f"R4 manifest file {name} drifted from the S3 freeze: {actual}")


def test_r4_s3_manifest_is_exact_import_closure() -> None:
    """The R4 manifest is exactly the deterministic import closure of the
    three S3 modules in a fresh interpreter -- no extra, no missing file."""
    fresh = _fresh_import_closure()
    assert set(fresh) == set(_EVIDENCE_DATA["files"]), (
        "R4 manifest does not equal the S3 import closure:\n"
        f"extra={sorted(set(fresh) - set(_EVIDENCE_DATA['files']))}\n"
        f"missing={sorted(set(_EVIDENCE_DATA['files']) - set(fresh))}")
    for name, expected in _EVIDENCE_DATA["files"].items():
        assert fresh[name] == expected, f"closure hash drift for {name}"


def test_r4_s3_manifest_unchanged_since_module_load() -> None:
    """The R4 sources are byte-identical at the end of this module run
    (before captured at module import; after checked here)."""
    after = {
        name: hashlib.sha256(
            (R4_MMR4_DIR / name).read_bytes()).hexdigest()
        for name in sorted(_EVIDENCE_DATA["files"])}
    assert after == BEFORE_MODULE_HASHES == _EVIDENCE_DATA["files"]


def test_r4_s3_direct_dependencies_are_in_manifest() -> None:
    """The R4 modules S3 statically imports all live inside the manifest."""
    required = {
        "d09_projection.py", "d10_projection.py", "d09_contracts.py",
        "d10_contracts.py", "d09_evaluator.py", "d10_evaluator.py",
        "__init__.py"}
    missing = required - set(_EVIDENCE_DATA["files"])
    assert not missing, f"direct/transitive R4 deps missing: {missing}"


# ---------------------------------------------------------------------------
# Caller payload / hash echo and non-typed inputs
# ---------------------------------------------------------------------------


def test_projector_rejects_non_typed_input() -> None:
    for bad in ({"not": "a packet"}, None, (), "S3-PACKET-STRING"):
        with pytest.raises(p.S3ProjectionError) as excinfo:
            p.project_surface(bad)
        assert excinfo.value.error_code == "caller_hash_not_trusted"


def test_projector_rejects_fake_typed_lookalike() -> None:
    packet = b.build_s3_authority_packet()
    # a caller-supplied current-risk projection with a drifted leaf must be
    # rejected via the caller-projection echo gate (never trusted).
    authoritative = p.project_current_risk(packet)
    doctored = dc_replace(authoritative, high_risk_refs=())
    with pytest.raises(p.S3ProjectionError) as excinfo:
        p.project_cockpit(packet, current_risk=doctored)
    assert excinfo.value.error_code == "caller_hash_not_trusted"

    bogus_center = dc_replace(
        p.project_center_graph(packet), stable_site_order=())
    with pytest.raises(p.S3ProjectionError) as excinfo:
        p.project_cockpit(packet, center_graph=bogus_center)
    assert excinfo.value.error_code == "caller_hash_not_trusted"


def test_packet_integrity_hash_is_recomputed_not_trusted() -> None:
    packet = b.build_s3_authority_packet()
    object.__setattr__(packet, "packet_integrity_hash", "f" * 64)
    result = c.validate_s3_authority_packet(packet)
    assert result["valid"] is False
    assert "packet_integrity_hash_mismatch" in result["reasons"], result
    # the projector also fails closed on the stale integrity
    with pytest.raises(p.S3ProjectionError) as excinfo:
        p.project_surface(packet)
    assert excinfo.value.error_code == "packet_integrity_hash_mismatch"


def test_supplemental_content_hash_tamper_fails_closed() -> None:
    """Direct tamper of a supplemental's own ``content_hash`` (no semantic
    change) is rejected with the exact ``supplemental_content_hash_mismatch``
    code, even after a packet-level re-sign.  Semantic-field mutations in the
    rest of this battery recompute the object hash so they exercise the
    semantic gate instead of this one."""
    for owner, pick in (
        ("lifecycle", lambda packet: packet.risk_lifecycle_authorities[0]),
        ("coverage", lambda packet: packet.coverage_authorities[0]),
        ("cutoff", lambda packet: packet.cutoff_authorities[0]),
        ("closure", lambda packet: packet.closure_authorities[0]),
        ("evaluation-limit", lambda packet:
         packet.evaluation_limit_authorities[0]),
    ):
        def mutate(packet: Any, _pick=pick) -> None:
            authority = _pick(packet)
            object.__setattr__(authority, "content_hash", "f" * 64)

        assert_rejected(f"direct {owner} content_hash tamper", mutate,
                        "supplemental_content_hash_mismatch")


# ---------------------------------------------------------------------------
# project / run / snapshot / cutoff / visibility / source / receipt drift
# ---------------------------------------------------------------------------


def test_receipt_content_and_visibility_source_drift_fails_closed() -> None:
    # receipt project identity drift
    assert_rejected(
        "receipt project_ref drift",
        lambda packet: object.__setattr__(
            packet.authority_units[0].authority_receipt,
            "project_ref", "S3-PROJECT-X"),
        "receipt_content_hash_mismatch")

    # unit receipt-content-hash drift (caller-supplied)
    assert_rejected(
        "unit receipt_content_hash drift",
        lambda packet: object.__setattr__(
            packet.authority_units[0], "receipt_content_hash", "f" * 64),
        "receipt_content_hash_mismatch")

    # visibility decision id drift
    assert_rejected(
        "receipt visibility_decision_id drift",
        lambda packet: object.__setattr__(
            packet.authority_units[0].authority_receipt,
            "visibility_decision_id", "S3-VIS-X"),
        "receipt_content_hash_mismatch")

    # visibility decision hash drift
    assert_rejected(
        "receipt visibility_decision_hash drift",
        lambda packet: object.__setattr__(
            packet.authority_units[0].authority_receipt,
            "visibility_decision_hash", "e" * 64),
        "receipt_content_hash_mismatch")

    # source revision-content pair drift
    def source_pair_drift(packet: Any) -> None:
        receipt = packet.authority_units[0].authority_receipt
        pair = _r5c.SourceRevisionContentPair(
            revision_id="S3-REV-WRONG", content_hash="1" * 64)
        object.__setattr__(
            receipt, "source_revision_content_pairs",
            tuple(receipt.source_revision_content_pairs) + (pair,))

    assert_rejected("source pairs drift", source_pair_drift,
                    "receipt_content_hash_mismatch")


def test_aggregate_identity_shared_binding_fails_closed() -> None:
    # project/run/snapshot/cutoff/audience-contract identity drift is
    # authoritative at the R4 receipt leaf: a drifted receipt cannot be
    # hidden by re-signing.
    assert_rejected(
        "receipt project_ref drift",
        lambda packet: object.__setattr__(
            packet.authority_units[0].authority_receipt,
            "project_ref", "S3-PROJECT-X"),
        "receipt_content_hash_mismatch")

    def run_ref_drift(packet: Any) -> None:
        object.__setattr__(packet.authority_units[0].authority_receipt,
                           "run_ref", "S3-RUN-X")

    assert_rejected("receipt run_ref drift", run_ref_drift,
                    "receipt_content_hash_mismatch")


@pytest.mark.parametrize(
    "field, value",
    [
        ("project_ref", "S3-PROJECT-SPOOFED"),
        ("run_ref", "S3-RUN-SPOOFED"),
        ("snapshot_ref", "S3-SNAPSHOT-SPOOFED"),
        ("cutoff_ref", "S3-CUTOFF-SPOOFED"),
        ("audience_contract_id", "S3-AUDIENCE-SPOOFED"),
    ],
)
def test_aggregate_identity_fields_bind_shared_receipt(
        field: str, value: str) -> None:
    """A coordinated re-sign cannot drift aggregate identity copies away
    from the single shared authority receipt identity."""
    def mutate(packet: Any) -> None:
        object.__setattr__(packet.aggregate_receipt_set, field, value)

    assert_rejected(
        f"aggregate {field} drift",
        mutate,
        "aggregate_identity_mismatch",
    )


# ---------------------------------------------------------------------------
# coordinated packet re-sign cannot smuggle semantics
# ---------------------------------------------------------------------------


def test_resign_high_to_low_reassignment_still_caught() -> None:
    # re-sign the high lifecycle to low, keep the declared surface saying
    # high: authority binding (severity == public handoff) must fail.
    def mutate(packet: Any) -> None:
        lifecycle = next(l for l in packet.risk_lifecycle_authorities
                         if l.severity == "high")
        object.__setattr__(lifecycle, "severity", "low")
        _recompute_supplemental_hash(lifecycle)

    assert_rejected("re-signed lifecycle severity drift", mutate,
                    "authority_binding_mismatch")


def test_resign_declared_high_echo_smuggle_fails_closed() -> None:
    # keep authorities intact, only push a foreign marker ref into the
    # declared high plane (attackers controlling the payload echo): the
    # declared plane drifts from the authority-derived set AND the foreign
    # ref has no resolving lifecycle, both fail closed.
    def mutate(packet: Any) -> None:
        rs = packet.audience_payload.current_risk_set
        object.__setattr__(
            rs, "high_risk_refs",
            rs.high_risk_refs + ("d10_marker:" + "b" * 64,))

    assert_rejected("foreign ref into declared high", mutate,
                    "current_plane_high_mismatch")


# ---------------------------------------------------------------------------
# high/medium full-set, omission and reassignment
# ---------------------------------------------------------------------------


def test_high_and_medium_planes_are_full_non_top_n_sets() -> None:
    base = list(b.build_synthetic_units())
    extras = [extra_d10(f"EXTRA-{i:02d}", "high") for i in range(1, 4)]
    packet = packet_from_units((base[0], *extras, base[1], base[2]))
    surface = p.project_surface(packet)
    assert len(surface.current_risk.high_risk_refs) == 4
    assert len(surface.current_risk.medium_risk_refs) == 0
    assert surface.current_risk.high_risk_refs == tuple(sorted(
        surface.current_risk.high_risk_refs))
    for field in surface.current_risk.__dataclass_fields__.values():
        assert "top" not in field.name.lower()


def test_high_omission_and_reassignment_fails_closed() -> None:
    assert_rejected(
        "high omitted from declared plane",
        lambda packet: object.__setattr__(
            packet.audience_payload.current_risk_set, "high_risk_refs", ()),
        "current_plane_high_mismatch")

    def high_to_medium(packet: Any) -> None:
        rs = packet.audience_payload.current_risk_set
        object.__setattr__(rs, "medium_risk_refs", rs.high_risk_refs)
        object.__setattr__(rs, "high_risk_refs", ())

    assert_rejected("high reassigned into medium", high_to_medium,
                    "current_plane_high_mismatch")


def test_medium_omission_and_reassignment_fails_closed() -> None:
    base = list(b.build_synthetic_units())

    def medium_omitted(packet: Any) -> None:
        object.__setattr__(
            packet.audience_payload.current_risk_set, "medium_risk_refs", ())

    packet = packet_from_units((base[0], extra_d10("MED", "medium"),
                                base[1], base[2]))
    _medium_test(packet, medium_omitted, "current_plane_medium_mismatch")

    def medium_promoted(packet: Any) -> None:
        rs = packet.audience_payload.current_risk_set
        object.__setattr__(rs, "high_risk_refs",
                           rs.high_risk_refs + rs.medium_risk_refs)
        object.__setattr__(rs, "medium_risk_refs", ())

    packet = packet_from_units((base[0], extra_d10("MED", "medium"),
                                base[1], base[2]))
    _medium_test(packet, medium_promoted, "current_plane_high_mismatch")


def _medium_test(packet: c.R5S3AuthorityPacket,
                 mutate: Callable[[Any], None],
                 expected: str) -> None:
    mutate(packet)
    _resign(packet)
    try:
        p.project_surface(packet)
    except p.S3ProjectionError as error:
        assert error.error_code == expected, (expected, error.error_code,
                                              str(error))
        return
    raise AssertionError(
        f"expected {expected!r} but the mutated packet projected fine")


# ---------------------------------------------------------------------------
# low-cluster loss / merge / stale / hidden leak
# ---------------------------------------------------------------------------


def test_low_cluster_loss_and_duplicate_ref_fail_closed() -> None:
    assert_rejected(
        "low cluster dropped from declared plane",
        lambda packet: object.__setattr__(
            packet.audience_payload.current_risk_set,
            "low_risk_cluster_refs", ()),
        "current_plane_low_cluster_mismatch")

    def duplicated_cluster_ref(packet: Any) -> None:
        rs = packet.audience_payload.current_risk_set
        cluster_ref = rs.low_risk_cluster_refs[0]
        object.__setattr__(rs, "low_risk_cluster_refs",
                           (cluster_ref, cluster_ref))

    assert_rejected("duplicated low cluster ref", duplicated_cluster_ref,
                    "current_plane_low_cluster_mismatch")


def test_low_cluster_stale_replay_and_hidden_leak_fail_closed() -> None:
    # Swap a cluster member and re-derive its ref/hash: the rebuilt
    # authority clusters no longer match the declared cluster content.
    def cluster_member_swap(packet: Any) -> None:
        cluster = packet.audience_payload.low_risk_clusters[0]
        members = ("S3-MEMBER-D09-SWAPPED",)
        object.__setattr__(cluster, "member_refs", members)
        content_hash = c.cluster_content_hash(
            cluster.authority_receipt_ref, cluster.domain, cluster.site_ref,
            members)
        object.__setattr__(cluster, "content_hash", content_hash)
        object.__setattr__(cluster, "cluster_ref",
                           c.CLUSTER_REF_PREFIX + content_hash)

    with pytest.raises(p.S3ProjectionError) as excinfo:
        packet = b.build_s3_authority_packet()
        cluster_member_swap(packet)
        _resign(packet)
        p.project_surface(packet)
    assert excinfo.value.error_code == "caller_hash_not_trusted", \
        excinfo.value.error_code
    assert "declared low-risk cluster content drift" in str(excinfo.value)

    # hide a low cluster member behind the hidden plane: the member is
    # projectable on the same unit, so the hide attempt creates a hidden <-> 
    # projectable overlap that fails with the specific hidden_member_leak
    # code (the low cluster can never be made to carry a hidden member).
    def cluster_hides_member(packet: Any) -> None:
        unit = next(u for u in packet.authority_units
                    if u.variant_kind == "d09_center_pattern_unit")
        object.__setattr__(unit, "hidden_member_refs",
                           unit.hidden_member_refs + ("S3-MEMBER-D09-001",))

    assert_rejected("low cluster hidden member leak", cluster_hides_member,
                    "hidden_member_leak")


# ---------------------------------------------------------------------------
# hidden member / site leakage (positive + negative)
# ---------------------------------------------------------------------------


def test_true_hidden_only_change_keeps_replay_and_accepts() -> None:
    """P1-4 positive control at the runtime level: a hidden-only private
    change (unit leaf + its embedded public audience, minus any projectable
    surface) keeps the audience replay byte-identical, changes the packet
    integrity hash, and the re-signed packet still projects."""
    units_in = list(b.build_synthetic_units())
    d09u = units_in[1]
    audience = dc_replace(d09u.bundle.audience,
                          hidden_member_refs=d09u.bundle.audience
                          .hidden_member_refs + ("S3-MEMB-HIDDEN-1",))
    hidden_unit = b.S3SyntheticUnit(d09u.kind, d09u.unit_ref,
                                    dc_replace(d09u.bundle, audience=audience),
                                    d09u.receipt, d09u.clinical_domain,
                                    d09u.marker_kind)
    packet = packet_from_units(
        (units_in[0], hidden_unit, units_in[2]))
    before_replay = packet.audience_replay_content_hash
    before_integrity = packet.packet_integrity_hash

    def mutate(packet: Any) -> None:
        # the genuinely hidden-member-carrying low D09 unit
        unit = next(u for u in packet.authority_units
                    if u.unit_ref == b.SYNTHETIC_UNIT_D09_LOW_REF)
        aud = c.unit_variant_payload(unit).audience
        object.__setattr__(
            unit, "hidden_member_refs",
            unit.hidden_member_refs + ("S3-MEMB-HIDDEN-2",))
        object.__setattr__(
            aud, "hidden_member_refs",
            aud.hidden_member_refs + ("S3-MEMB-HIDDEN-2",))
        object.__setattr__(unit, "content_hash", c.unit_content_hash(unit))

    mutate(packet)
    _resign(packet)
    assert packet.audience_replay_content_hash == before_replay, (
        "hidden-only change must keep the public audience replay")
    assert packet.packet_integrity_hash != before_integrity, (
        "hidden-only change must move the private integrity hash")
    p.project_surface(packet)


def test_hidden_member_and_site_never_leak_into_projectable() -> None:
    # a hidden member smuggled into the same unit's projectable plane
    # (hidden <-> projectable overlap) must fail with hidden_member_leak
    def hidden_into_projectable(packet: Any) -> None:
        target = next(u for u in packet.authority_units
                      if u.unit_ref == b.SYNTHETIC_UNIT_D09_LOW_REF)
        object.__setattr__(
            target, "hidden_member_refs",
            target.hidden_member_refs + ("S3-MEMB-OVERLAP",))
        object.__setattr__(
            target, "projectable_member_refs",
            target.projectable_member_refs + ("S3-MEMB-OVERLAP",))

    assert_rejected("hidden member into projectable plane",
                    hidden_into_projectable, "hidden_member_leak")

    # a projectable ref pushed without a matching hidden member still fails
    # closed as an audience binding drift (write into the public plane)
    def smuggled_into_projectable(packet: Any) -> None:
        unit = packet.authority_units[2]  # D10 unit (no hidden members)
        object.__setattr__(
            unit, "projectable_member_refs",
            unit.projectable_member_refs + ("S3-SMUGGLED",))

    assert_rejected("smuggled projectable-ref write", smuggled_into_projectable,
                    "authority_binding_mismatch")

    # hidden site drift (D10-only hidden_site_refs) against declared audience
    def hidden_site_into_public(packet: Any) -> None:
        unit = packet.authority_units[2]
        object.__setattr__(
            unit, "hidden_site_refs", unit.hidden_site_refs + ("S3-SITE-X",))

    assert_rejected("hidden site leakage", hidden_site_into_public,
                    "authority_binding_mismatch")


def test_hidden_member_in_layer_membership_leaks_fails_closed() -> None:
    def mutate(packet: Any) -> None:
        unit = packet.authority_units[2]
        leak_authority = b.build_layer_membership_authority(
            "S3-MEMBERSHIP-LEAK", "individual_risk", "projectable",
            ("S3-HIDDEN-SMUGGLED",), Decimal("2"),
            "mm_r4.d10_projection:D10ProjectionCountSurface"
            ".individual_risk_count", "no_disabled_path",
            unit.authority_receipt)
        object.__setattr__(
            packet, "layer_membership_authorities",
            packet.layer_membership_authorities + (leak_authority,))

    assert_rejected("layer membership hidden-member leak", mutate,
                    "hidden_member_leak", surface="layers")


# ---------------------------------------------------------------------------
# resolved / current / closure drift
# ---------------------------------------------------------------------------


def test_resolved_current_and_closure_bindings_fail_closed() -> None:
    # current/resolved overlap in the declared plane
    assert_rejected(
        "resolved ref merged into high plane",
        lambda packet: object.__setattr__(
            packet.audience_payload.current_risk_set,
            "high_risk_refs",
            packet.audience_payload.current_risk_set.high_risk_refs
            + packet.audience_payload.current_risk_set.resolved_history_refs),
        "current_plane_high_mismatch")

    # a current lifecycle promoted to resolved without a closure authority:
    # after a perfect object-level + packet-level re-sign the packet gate
    # re-runs the lifecycle's own closed-enum validation and refuses the
    # resolved-without-closure shape with supplemental_enum_mismatch.
    def resolve_without_closure(packet: Any) -> None:
        lifecycle = next(l for l in packet.risk_lifecycle_authorities
                         if l.lifecycle_state == "current")
        object.__setattr__(lifecycle, "lifecycle_state", "resolved")
        _recompute_supplemental_hash(lifecycle)

    assert_rejected("current resolved without closure", resolve_without_closure,
                    "supplemental_enum_mismatch")

    # closure prior-instance binding drift
    def closure_prior_instance(packet: Any) -> None:
        closure = packet.closure_authorities[0]
        object.__setattr__(closure, "prior_risk_instance_ref",
                           "S3-INSTANCE-WRONG")
        _recompute_supplemental_hash(closure)

    assert_rejected("closure prior instance drift", closure_prior_instance,
                    "closure_prior_instance_mismatch")

    # closure decision-hash drift
    def closure_decision_drift(packet: Any) -> None:
        closure = packet.closure_authorities[0]
        object.__setattr__(closure, "closure_decision_hash", "e" * 64)
        _recompute_supplemental_hash(closure)

    assert_rejected("closure decision hash drift", closure_decision_drift,
                    "closure_prior_instance_mismatch")

    # orphan closure authority
    def orphan_closure(packet: Any) -> None:
        unit = packet.authority_units[0]
        orphan = b.build_closure_authority(
            "S3-CLOSURE-ORPHAN", "S3-ORPHAN-DECISION",
            c.D09_MARKER_PREFIX + "c" * 64, "S3-INSTANCE-ORPHAN",
            unit.authority_receipt)
        object.__setattr__(packet, "closure_authorities",
                           packet.closure_authorities + (orphan,))

    assert_rejected("orphan closure", orphan_closure, "closure_orphan")

    # dropping the closure of a resolved lifecycle
    assert_rejected(
        "resolved lifecycle without its closure authority",
        lambda packet: object.__setattr__(
            packet, "closure_authorities", ()),
        "closure_ambiguous")


def test_resolved_requires_closure_at_construction() -> None:
    units_in = b.build_synthetic_units()
    unit = b.build_authority_unit(units_in[0], "S3-CDA-d10-D10-001")
    variant = c.unit_variant_payload(unit)
    marker = variant.risk_marker
    handoff = variant.r2_handoff
    with pytest.raises(c.S3ContractError) as excinfo:
        b.build_lifecycle_authority(
            "S3-LIFE-BAD", "d10", marker, handoff, "S3-CDA-d10-D10-001",
            unit.authority_receipt, lifecycle_state="resolved")
    assert "resolved_without_lifecycle_authority" in str(excinfo.value)


def test_propose_close_never_resolves() -> None:
    assert c.LIFECYCLE_STATE_TABLE["propose_close"]["state"] == \
        "proposed_close"
    assert c.PROPOSE_CLOSE_STATE == "proposed_close"
    assert c.PROPOSE_CLOSE_STATE != c.RESOLVED_STATE


# ---------------------------------------------------------------------------
# change kind / cause misprojection and mixed cause
# ---------------------------------------------------------------------------


def test_change_emission_and_cause_misprojection_fail_closed() -> None:
    # authority change section says "resolved" while the lifecycle is current
    def section_resolved_on_current(packet: Any) -> None:
        d10u = next(u for u in packet.authority_units
                    if u.variant_kind == "d10_project_unit")
        object.__setattr__(c.unit_variant_payload(d10u).change_section,
                           "change_kind", "resolved")

    assert_rejected("resolved change section on current lifecycle",
                    section_resolved_on_current, "change_emission_mismatch",
                    surface="bands")

    # declared band kind echo drift (caller-echo cannot rewrite the surface)
    def declared_band_kind_drift(packet: Any) -> None:
        band = packet.audience_payload.change_bands[1]
        object.__setattr__(band, "change_kind", "superseded")

    assert_rejected("declared band kind drift", declared_band_kind_drift,
                    "caller_hash_not_trusted", surface="bands")

    # resolved band misprojected as continued
    def resolved_band_as_continued(packet: Any) -> None:
        band = next(cb for cb in packet.audience_payload.change_bands
                    if cb.change_kind == "resolved")
        object.__setattr__(band, "change_kind", "continued")

    assert_rejected("resolved band as continued", resolved_band_as_continued,
                    "caller_hash_not_trusted", surface="bands")


def test_unknown_change_kind_and_cause_are_rejected() -> None:
    # mutating the authority change section emits a band the typed
    # R5ChangeBand contract refuses to construct (fail closed before
    # projection).
    packet = b.build_s3_authority_packet()
    d10u = next(u for u in packet.authority_units
                if u.variant_kind == "d10_project_unit")

    object.__setattr__(c.unit_variant_payload(d10u).change_section,
                       "change_kind", "garbage_kind")
    with pytest.raises(_r5c.R5ContractError):
        b.project_change_bands(packet)

    packet = b.build_s3_authority_packet()
    d10u = next(u for u in packet.authority_units
                if u.variant_kind == "d10_project_unit")
    object.__setattr__(c.unit_variant_payload(d10u).change_section,
                       "change_cause", "garbage_cause")
    with pytest.raises(_r5c.R5ContractError):
        b.project_change_bands(packet)


def test_change_cause_mixture_requires_multi_cause() -> None:
    units_in = b.build_synthetic_units()
    receipt = b.build_authority_unit(units_in[0], "ref").authority_receipt

    with pytest.raises(c.S3ContractError) as excinfo:
        b.build_change_cause_mixture_authority("MIX-1", ("data",), receipt)
    assert "mixed_d10_cause" in str(excinfo.value)

    with pytest.raises(c.S3ContractError):
        b.build_change_cause_mixture_authority("MIX-2", ("data", "data"),
                                               receipt)

    with pytest.raises(c.S3ContractError):
        b.build_change_cause_mixture_authority(
            "MIX-3", ("data", "garbage"), receipt)

    for causes in (("data", "coverage"), ("coverage", "population")):
        authority = b.build_change_cause_mixture_authority(
            "MIX-OK-" + "-".join(causes), causes, receipt)
        assert "-".join(authority.causes) == "-".join(sorted(causes))


# ---------------------------------------------------------------------------
# count-layer cross-sum and independent layers
# ---------------------------------------------------------------------------


def test_quantity_layers_independent_no_cross_layer_total() -> None:
    surface = p.project_surface(b.build_s3_authority_packet())
    assert len(surface.quantity_layers) == len(c.S3_LAYERS) == 8
    by_layer = {layer.layer: layer for layer in surface.quantity_layers}
    assert set(by_layer) == set(c.S3_LAYERS)
    for layer in surface.quantity_layers:
        for field in layer.__dataclass_fields__.values():
            assert "total" not in field.name.lower(), (
                f"layer {layer.layer!r} has a total-bearing field")
        # every count leaf is a per-unit verbatim leaf from a public unit
        for count in layer.counts:
            assert count.unit_ref in {
                unit.unit_ref for unit in b.build_s3_authority_packet()
                .authority_units}
            assert count.source_count_value is not None


def test_measure_matches_public_numerator_and_members() -> None:
    packet = b.build_s3_authority_packet()
    measures = p.project_measures(packet)
    assert len(measures) == 1
    measure = measures[0]
    assert measure.numerator_kind == "individual_risk"
    d10u = next(u for u in packet.authority_units
                if u.variant_kind == "d10_project_unit")
    variant = c.unit_variant_payload(d10u)
    assert measure.numerator_value == Decimal(
        variant.counts.individual_risk_count)
    assert tuple(sorted(measure.numerator_member_refs)) == tuple(
        sorted(set(variant.risk_marker.member_refs)))


# ---------------------------------------------------------------------------
# member duplication / dangling / cross-unit refs
# ---------------------------------------------------------------------------


def test_cross_unit_shared_member_refused_at_assembly() -> None:
    """A member projected by two units (potential singleton-upgrade /
    duplicate risk) is refused while assembling the packet."""
    def _extra_d09_shared() -> b.S3SyntheticUnit:
        members = ("S3-MEMBER-D09-001",)  # same member as the low d09 unit
        site = "S3-SITE-DUP"
        subject = "S3-SUBJ-DUP"
        marker = b._build_d09_marker("DUP", members)
        handoff = b._build_d09_handoff("DUP", "create", "medium", members,
                                       None, None)
        audience = b._build_d09_audience("S3-SCOPE-DUP", members, site)
        counts = b._build_d09_counts("DUP", members)
        hotspot = b._build_d09_hotspot("DUP-1", site, subject, members,
                                       "medium")
        bundle = D09ProjectionBundle(
            audience=audience, counts=counts, risk_marker=marker,
            hotspots=(hotspot,), deep_links=(), query_draft=None,
            r2_handoff=handoff)
        return b.S3SyntheticUnit("d09", "S3-UNIT-DUP", bundle,
                                 b._build_receipt("d09", "S3-U-DUP"), "ae",
                                 "d09")

    base = list(b.build_synthetic_units())
    with pytest.raises(b.S3AuthorityBuilderError) as excinfo:
        packet_from_units((base[0], base[1], base[2], _extra_d09_shared()))
    assert "center_cell_duplicate_member" in str(excinfo.value)


def test_dangling_lifecycle_and_cross_unit_marker_fail_closed() -> None:
    # dangling lifecycle marker id (no matching unit)
    def dangling_marker(packet: Any) -> None:
        lifecycle = packet.risk_lifecycle_authorities[0]
        object.__setattr__(lifecycle, "marker_id", "deadbeef" * 8)
        object.__setattr__(lifecycle, "marker_identity_ref",
                           c.D09_MARKER_PREFIX + "deadbeef" * 8)
        _recompute_supplemental_hash(lifecycle)

    assert_rejected("dangling lifecycle marker", dangling_marker,
                    "authority_binding_mismatch")

    # a marker that carries a member outside its unit's projectable plane
    def cross_unit_marker_member(packet: Any) -> None:
        d10u = next(u for u in packet.authority_units
                    if u.variant_kind == "d10_project_unit")
        object.__setattr__(
            c.unit_variant_payload(d10u).risk_marker, "member_refs",
            c.unit_variant_payload(d10u).risk_marker.member_refs
            + ("S3-MEMBER-D09-001",))

    assert_rejected("cross-unit marker member", cross_unit_marker_member,
                    "hidden_member_leak")

    # duplicate unit identity is refused at packet construction (sorted-unique
    # by unit_ref) no matter how the rest of the packet is formed
    units_in = b.build_synthetic_units()
    built = [b.build_authority_unit(u, "ref") for u in units_in]
    with pytest.raises(c.S3ContractError) as excinfo:
        c.R5S3AuthorityPacket(
            packet_id="x", schema=c.S3_PACKET_SCHEMA_ID,
            status=c.STAGE_STATUS_S3, authority_mode=c.AUTHORITY_MODE_S3,
            authority_units=(built[0], built[0], built[1], built[2]),
            aggregate_receipt_set=b.build_aggregate_receipt_set(
                (built[0], built[1], built[2])),
            risk_lifecycle_authorities=(), closure_authorities=(),
            clinical_domain_authorities=(), denominator_authorities=(),
            layer_membership_authorities=(), cutoff_authorities=(),
            evaluation_limit_authorities=(), coverage_authorities=(),
            change_cause_mixture_authorities=(), audience_payload=None,
            audience_replay_content_hash="", packet_integrity_hash=None)
    assert "sorted-unique by unit_ref" in str(excinfo.value)


# ---------------------------------------------------------------------------
# denominator positive / zero / unknown / unclosed and exclusions
# ---------------------------------------------------------------------------


def test_denominator_states_and_exclusions_exact() -> None:
    units_in = b.build_synthetic_units()
    receipt = b.build_authority_unit(units_in[0], "ref").authority_receipt

    for kind, state, value, unit in (
            ("treated_subjects", "closed_positive", Decimal("8"), "subject"),
            ("treated_subjects", "closed_zero", Decimal("0"), "subject"),
            ("safety_evaluable_subjects", "unknown", None, "subject"),
            ("exposure_time", "unclosed", None, "subject_day"),
            ("enrolled_subjects", "closed_positive", Decimal("100"),
             "subject")):
        authority = b.build_denominator_authority(
            "DEN-" + state, kind, state, value, unit,
            ("S3-MEMBER-D10-001",), ("S3-MEMBER-D09-002",), receipt)
        assert authority.denominator_kind == kind
        assert authority.denominator_state == state
        assert authority.member_refs == ("S3-MEMBER-D10-001",)
        assert authority.exclusion_refs == ("S3-MEMBER-D09-002",)

    with pytest.raises(c.S3ContractError):
        b.build_denominator_authority(
            "DEN-BAD", "garbage", "closed_positive", Decimal("1"),
            "subject", (), (), receipt)
    with pytest.raises(c.S3ContractError):
        b.build_denominator_authority(
            "DEN-BAD2", "treated_subjects", "garbage_state", Decimal("1"),
            "subject", (), (), receipt)


def test_ambiguous_denominator_authorities_fail_closed() -> None:
    def mutate(packet: Any) -> None:
        unit = packet.authority_units[2]
        extra = b.build_denominator_authority(
            "DEN-2", "enrolled_subjects", "closed_positive", Decimal("10"),
            "subject", (), (), unit.authority_receipt)
        object.__setattr__(packet, "denominator_authorities",
                           packet.denominator_authorities + (extra,))

    assert_rejected("ambiguous denominator authorities", mutate,
                    "quantity_state_mismatch", surface="layers")


# ---------------------------------------------------------------------------
# coverage partial/truncated/unknown/not-applicable and cutoff/eval drift
# ---------------------------------------------------------------------------


def test_coverage_closed_states_buildable_except_not_evaluable() -> None:
    units_in = b.build_synthetic_units()
    receipt = b.build_authority_unit(units_in[0], "ref").authority_receipt
    for state in ("complete", "partial", "truncated", "unknown",
                  "not_applicable"):
        authority = b.build_coverage_authority("COV-" + state, state, receipt)
        assert authority.coverage_state == state
    assert "not_evaluable" not in c.S3_COVERAGE_STATES
    with pytest.raises(c.S3ContractError):
        b.build_coverage_authority("COV-BAD", "not_evaluable", receipt)


def test_coverage_authority_public_drift_fails_closed() -> None:
    def mutate(packet: Any) -> None:
        authority = packet.coverage_authorities[0]
        object.__setattr__(authority, "coverage_state", "partial")
        object.__setattr__(
            authority, "content_hash",
            c.s3_content_hash_excluding(authority, ("content_hash",)))

    assert_rejected("coverage authority/public drift", mutate,
                    "quantity_state_mismatch", surface="layers")


def test_cutoff_and_evaluation_limit_drift_fail_closed() -> None:
    def cutoff_drift(packet: Any) -> None:
        authority = packet.cutoff_authorities[0]
        object.__setattr__(authority, "cutoff_ref", "S3-CUTOFF-WRONG")
        object.__setattr__(
            authority, "content_hash",
            c.s3_content_hash_excluding(authority, ("content_hash",)))

    assert_rejected("cutoff authority drift", cutoff_drift,
                    "quantity_state_mismatch", surface="layers")

    def eval_drift(packet: Any) -> None:
        authority = packet.evaluation_limit_authorities[0]
        object.__setattr__(authority, "evaluation_limit_refs",
                           ("S3-EVAL-WRONG",))
        object.__setattr__(authority, "evaluation_limit_values",
                           ("S3-EVAL-WRONG",))
        object.__setattr__(
            authority, "content_hash",
            c.s3_content_hash_excluding(authority, ("content_hash",)))

    assert_rejected("evaluation-limit authority drift", eval_drift,
                    "quantity_state_mismatch", surface="layers")


# ---------------------------------------------------------------------------
# D09 pattern vs D10 individual and singleton upgrade
# ---------------------------------------------------------------------------


def test_singleton_d09_stays_pattern_d10_stays_individual() -> None:
    surface = p.project_surface(b.build_s3_authority_packet())
    d09_cells = [cell for cell in surface.center_graph.cells
                 if cell.pattern_refs]
    d10_cells = [cell for cell in surface.center_graph.cells
                 if cell.individual_risk_refs]
    assert d09_cells, "singleton D09 low unit must remain a pattern cell"
    for cell in d09_cells:
        assert not cell.individual_risk_refs
        assert len(cell.pattern_refs) >= 1
    for cell in d10_cells:
        assert not cell.pattern_refs
        assert len(cell.individual_risk_refs) >= 1


def test_cell_classification_miswrite_is_rejected() -> None:
    """Rewriting a declared center cell so a D09 pattern cell also claims an
    individual-risk member is a forbidden classification write: the declared
    center map must equal the authority-derived one byte-for-byte."""
    def mutate(packet: Any) -> None:
        cells = packet.audience_payload.center_map.cells
        rebuilt = []
        for cell in cells:
            if cell.pattern_refs:
                cell = dc_replace(
                    cell,
                    individual_risk_refs=cell.individual_risk_refs
                    + ("S3-MEMBER-D10-001",))
            rebuilt.append(cell)
        object.__setattr__(packet.audience_payload.center_map,
                           "cells", tuple(rebuilt))

    assert_rejected("center-cell classification write", mutate,
                    "caller_hash_not_trusted", surface="cells")


def test_wrong_site_and_domain_declared_drift_fails_closed() -> None:
    def site_drift(packet: Any) -> None:
        cells = packet.audience_payload.center_map.cells
        object.__setattr__(
            packet.audience_payload.center_map, "cells",
            tuple(dc_replace(cell, site_ref="S3-SITE-WRONG")
                  for cell in cells))

    assert_rejected("declared center-map site drift", site_drift,
                    "caller_hash_not_trusted", surface="cells")

    # lifecycle domain binding drift (points at the wrong domain authority)
    def domain_ref_drift(packet: Any) -> None:
        lifecycle = next(l for l in packet.risk_lifecycle_authorities
                         if l.severity == "high")
        object.__setattr__(lifecycle, "clinical_domain_ref",
                           "S3-CDA-d09-D09-001")
        _recompute_supplemental_hash(lifecycle)

    assert_rejected("lifecycle domain-ref drift", domain_ref_drift,
                    "authority_binding_mismatch")


# ---------------------------------------------------------------------------
# stable-order / replay and forbidden score/rank/top-N schema
# ---------------------------------------------------------------------------


def test_replay_and_surface_are_stable_and_unit_order_canonicalized() -> None:
    first = p.project_surface(b.build_s3_authority_packet())
    second = p.project_surface(b.build_s3_authority_packet())
    assert first == second
    assert first.content_hash == second.content_hash

    # unit order is canonicalized (sorted-unique) before hashing: feeding
    # the SAME already-built authority units in reversed order to
    # assemble_packet yields a byte-identical packet.
    base = b.build_s3_authority_packet()
    bucket_base = b.assemble_packet(
        base.authority_units, base.aggregate_receipt_set,
        base.risk_lifecycle_authorities, base.closure_authorities,
        base.clinical_domain_authorities, base.denominator_authorities,
        base.layer_membership_authorities, base.cutoff_authorities,
        base.evaluation_limit_authorities, base.coverage_authorities,
        base.change_cause_mixture_authorities)
    bucket_reversed = b.assemble_packet(
        tuple(reversed(base.authority_units)), base.aggregate_receipt_set,
        base.risk_lifecycle_authorities, base.closure_authorities,
        base.clinical_domain_authorities, base.denominator_authorities,
        base.layer_membership_authorities, base.cutoff_authorities,
        base.evaluation_limit_authorities, base.coverage_authorities,
        base.change_cause_mixture_authorities)
    assert bucket_base == bucket_reversed
    assert bucket_base.audience_replay_content_hash == \
        bucket_reversed.audience_replay_content_hash
    assert bucket_base.packet_integrity_hash == \
        bucket_reversed.packet_integrity_hash
    assert p.project_surface(bucket_base) == p.project_surface(
        bucket_reversed)


def test_no_forbidden_score_rank_topn_schema_field() -> None:
    forbidden = ("score", "rank", "top", "top_n")
    classes = (
        p.S3ProjectedSurface, p.S3CurrentRiskProjection, p.S3RiskLeaf,
        p.S3RiskClusterLeaf, p.S3QuantityLayer, p.S3LayerCount,
        p.S3ChangeBandProjection, p.S3ChangeBandLeaf, p.S3CenterCellLeaf,
        p.S3CenterGraphProjection, p.S3CockpitProjection, p.S3AuthorityTrace,
        c.R5S3AudiencePayload, c.R5S3RiskLifecycleAuthority,
        c.R5S3LowRiskCluster, _r5c.R5CurrentRiskSet, _r5c.R5ChangeBand,
        _r5c.R5QuantitativeMeasure, _r5c.R5CenterMapCell,
        _r5c.R5CenterMapProjection, _r5c.R5ProjectCockpitProjection,
    )
    for cls in classes:
        names = [field.name.lower()
                 for field in cls.__dataclass_fields__.values()]
        hits = [name for name in names
                if any(token in name for token in forbidden)]
        assert not hits, f"{cls.__name__} carries forbidden schema fields {hits}"


def test_no_nearest_fallback_for_declared_domain() -> None:
    """No nearest-fallback: a lifecycle whose clinical-domain authority
    cannot be resolved must fail closed rather than leak to a sibling
    domain."""
    def remove_domain(packet: Any) -> None:
        removed = packet.clinical_domain_authorities[2]
        object.__setattr__(
            packet, "clinical_domain_authorities",
            tuple(authority for authority in
                  packet.clinical_domain_authorities
                  if authority.authority_id != removed.authority_id))

    assert_rejected("removed clinical-domain authority", remove_domain,
                    "nearest_fallback_forbidden")
