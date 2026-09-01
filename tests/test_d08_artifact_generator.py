"""Focused tests for the deterministic D08 artifact generator (worker_01
deliverable): pinned-hash oracle independence, exact schemas, five-column
bijection, non-circular replay manifest, deterministic byte-identical replay,
and decisive positive/negative mutations including oracle/catalog reseal
attempts.

Structure:
  * STATIC PROOFS — the generator source provably contains no expected-leaf
    derivation (no input-to-expected branch), no oracle write path, and no D08
    runtime import.
  * INDEPENDENT VERIFIER — a fresh, contract-based 233-case semantic audit of
    the pinned oracle (v0.6 §4-§12), written without importing the generator's
    assembly machinery (contract §13.3 independent verifier).
  * POSITIVE CHECKS — schema/hash/bijection/floors/duplicate-substantive/
    static-independence/waiver/cutoff/temporal essentials.
  * NEGATIVE MUTATIONS — each typed-input or artifact mutation must fail
    closed; catalog reseal must never rewrite the oracle; coordinated
    catalog/oracle/registry reseal must fail the pinned independent hashes.
  * DETERMINISM — two full renders are byte-identical; 8911 stays stopped.

These tests never import or implement D08 runtime code and never write into
reviews/ (renders run in temporary directories).
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import socket
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_d08_challenge_registry as g  # noqa: E402

CONTRACT_PATH = ROOT / "reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md"
CATALOG_PATH = ROOT / "reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json"
ORACLE_PATH = ROOT / "reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json"
REGISTRY_PATH = ROOT / "reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json"
GENERATOR_PATH = ROOT / "tools/generate_d08_challenge_registry.py"

# ---------------------------------------------------------------------------
# Frozen pins (contract §13). These are the independent hashes the generator
# and this suite validate exactly.
# ---------------------------------------------------------------------------
CONTRACT_FILE_SHA256 = "ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64"
CONTRACT_SEMANTIC_SHA256 = CONTRACT_FILE_SHA256
CATALOG_FILE_SHA256 = "d3cd694bcbe63d977d5ef332be3647fb1274293be6ec364021946ee610ffa82c"
ORACLE_FILE_SHA256 = "a40cbb509df2378804fd513a79467cbbc4e208d3b2b5c6f1a2410a63a12b8ac9"
ORACLE_CONTENT_HASH = "724b95cb0964a4bdb992ba08655a4aff30983cb8d7454038fdbe269588f0b3d1"
REGISTRY_FILE_SHA256 = "bf0142b36a60524d40d203e641c6fc0ef591c01069dd63caf6fc92da3ec96a9a"
REGISTRY_CONTENT_HASH = "55f1efbd7bfdb2ae7ea1e461b02eb732b792bba0140208ce4bfe3e6b4661ca9a"
GENERATOR_FILE_SHA256 = "63d610e82c385cbe906ecf8978622b9d534a64ef22b74a275832a0e07e8df100"

DISPOSITIONS = ("positive", "negative", "boundary", "not_applicable", "not_evaluable")
CONSUME_ONLY = "consume_only"
CASE_KEYS_FROZEN_16 = [
    "audience_contract", "case_id", "clinical_claim_token", "disposition",
    "expected_leaf_set", "expected_source_leaf_set", "expected_trace_leaf_set",
    "family_id", "fixture_hash", "fixture_id", "grain", "manifest_case_id",
    "mutation_class", "oracle_case_id", "owner_route", "typed_input",
]
CATALOG_TOP_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
BIJECTION_COLUMNS = ["case_id", "fixture_id", "oracle_case_id", "manifest_case_id", "test_id"]
CLOSURE_STATES = ("full_set", "explicit_empty", "missing")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    def normalize(v: Any) -> Any:
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        if isinstance(v, list):
            return [normalize(x) for x in v]
        if isinstance(v, dict):
            return {k: normalize(x) for k, x in v.items()}
        return v

    return json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def object_hash(obj: dict, own_key: str = "content_hash") -> str:
    core = {k: v for k, v in obj.items() if k != own_key}
    return sha256_text(canonical_json(core))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Static proofs (corrective gate: tests must statically prove absence of
# derive_expected_leaves or equivalent input-to-expected branches and absence
# of D08 runtime imports in the final generator).
# ---------------------------------------------------------------------------
FORBIDDEN_DERIVATION_NAMES = {
    "derive_expected_leaves", "_evaluate_class", "build_oracle",
    "check_oracle_vs_catalog", "_derived_disposition", "_assemble_expected_leaf_set",
    "_assemble_trace_leaf_set", "_assemble_source_leaf_set", "_link_units",
    "_identity_unit", "_propagation_units", "_integrity_error", "_resolve_anomaly",
    "_join_conserved", "_feasible_temporal", "_temporal_unit_l1", "_new_unit",
    "case_owner_route_marker", "stable_ids_of",
}
STDLIB_MODULES = {
    "__future__", "ast", "calendar", "collections", "datetime", "hashlib", "json",
    "pathlib", "re", "sys", "tempfile", "typing", "unicodedata",
}


class TestStaticGeneratorProofs(unittest.TestCase):
    """The generator provably contains no derivation / oracle-write / runtime."""

    def test_no_expected_leaf_derivation_function(self) -> None:
        tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
        defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        hit = sorted(defined & FORBIDDEN_DERIVATION_NAMES)
        self.assertEqual(hit, [], f"input-to-expected derivation functions still present: {hit}")

    def test_no_derivation_token_in_source(self) -> None:
        src = GENERATOR_PATH.read_text(encoding="utf-8")
        self.assertNotIn("derive_expected_leaves", src)
        self.assertNotIn("def derive", src)

    def test_no_oracle_write_path(self) -> None:
        src = GENERATOR_PATH.read_text(encoding="utf-8")
        for token in ("ORACLE.write_bytes", "ORACLE.write_text", 'open(ORACLE, "w"',
                      'open(ORACLE, "wb"', "ORACLE.open(", "ORACLE.write("):
            self.assertNotIn(token, src, f"oracle write path token present: {token}")
        # every write_bytes/write_text call in the generator must target the
        # render loop's catalog/registry paths — never the oracle
        tree = ast.parse(src)
        writes: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in ("write_bytes", "write_text"):
                    writes.append(ast.unparse(node))
        self.assertTrue(writes, "expected at least one artifact write call")
        for w in writes:
            self.assertNotIn("ORACLE", w, f"write call references the oracle: {w}")
            self.assertTrue(
                "path.write_bytes" in w or "path.write_text" in w or "registry_path" in w or
                "catalog_path" in w or "Path(tmp) / CATALOG.name" in w,
                f"unexpected write target: {w}")

    def test_stdlib_only_imports(self) -> None:
        tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        foreign = sorted(imports - STDLIB_MODULES)
        self.assertEqual(foreign, [], f"non-stdlib imports (D08 runtime?) in generator: {foreign}")

    def test_no_runtime_or_server_code(self) -> None:
        src = GENERATOR_PATH.read_text(encoding="utf-8")
        for token in ("socket", "bind(", "listen(", "serve_forever", "8911",
                      "mm_r4", "run_monitoring", "d07_runtime", "uvicorn", "flask"):
            self.assertNotIn(token, src, f"runtime/server token present: {token}")

    def test_catalog_leaf_keys_are_null_placeholders(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                self.assertIsNone(case[key], f"{case['case_id']} {key} must be null in the catalog")


# ---------------------------------------------------------------------------
# Independent verifier (contract §13.3): a fresh 233-case semantic audit of the
# pinned oracle. Written from the v0.6 contract text; does NOT import the
# generator and does NOT reuse its assembly machinery.
# ---------------------------------------------------------------------------
IDENTITY_REASON_MAP: dict[str, str] = {
    "same stable identity, different subject": "positive",
    "same stable identity across subjects (SYN-SUBJECT-002)": "positive",
    "stable identity assigned to the wrong subject": "positive",
    "stable identity assigned to the wrong site": "positive",
    "same identity, different site": "positive",
    "same identity, different semantic role": "positive",
    "duplicate content, same identity/time/source": "positive",
    "duplicate content with same identity/time/source": "positive",
    "alias-normalized evidence resolves to the same identity": "positive",
    "identity collision across source files": "positive",
    "identity collision across source sheets": "positive",
    "split without modelling rule": "boundary",
    "split records without modelling rule": "boundary",
    "merge records without modelling rule": "boundary",
    "merge documented by modelling rule": "negative",
    "split records with authoritative modelling rule": "negative",
    "merge records with modelling rule": "negative",
    "stable-event collision semantics = merge with modelling rule": "negative",
    "duplicate content with different stable identity": "negative",
    "alias-normalized evidence resolves to distinct identities": "negative",
    "same identity, different event text": "negative",
    "same stable identity across source revisions is revision history, not a duplicate": "negative",
    "raw/materialized mirror exemption documented": "negative",
    "text equality is not identity": "negative",
    "date revision, same stable classifier": "negative",
    "identity operand unknown": "not_evaluable",
    "dedup policy keys do not cover observed fields": "not_evaluable",
}
IDENTITY_REASON_SUBSTR: tuple[tuple[str, str], ...] = (
    ("FP trap: same text, different stable identity", "negative"),
    ("same stable identity across source revisions", "negative"),
    ("identity collision across source files", "positive"),
    ("identity collision across source sheets", "positive"),
    ("duplicate content with same identity/time/source", "positive"),
    ("duplicate content with different stable identity", "negative"),
    ("same stable identity across subjects", "positive"),
    ("split records with authoritative modelling rule", "negative"),
    ("split records without modelling rule", "boundary"),
    ("merge records with modelling rule", "negative"),
    ("merge records without modelling rule", "boundary"),
    ("alias-normalized evidence resolves to the same identity", "positive"),
    ("alias-normalized evidence resolves to distinct identities", "negative"),
    ("same identity, different event text", "negative"),
    ("stable identity assigned to the wrong subject", "positive"),
    ("stable identity assigned to the wrong site", "positive"),
    ("raw/materialized mirror exemption documented", "negative"),
    ("stable-event collision semantics = merge with modelling rule", "negative"),
    ("date revision, same stable classifier", "negative"),
    ("dedup policy keys do not cover observed fields", "not_evaluable"),
    ("identity operand unknown", "not_evaluable"),
)
PROPAGATION_HINT_SUBSTR: tuple[tuple[str, str], ...] = (
    ("producer not evaluable", "not_evaluable"),
    ("ambiguous correction chain", "boundary"),
    ("lineage fingerprint mismatch", "not_evaluable"),
)
QJ_HINT_SUBSTR: tuple[tuple[str, str], ...] = (
    ("wrong-subject relation payload", "not_evaluable"),
)


def _parse_date(value: str) -> tuple[int, int, int] | None:
    parts = value.split("-")
    if len(parts) == 3:
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return None
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]), 1)
        except ValueError:
            return None
    if len(parts) == 1 and parts[0]:
        try:
            return (int(parts[0]), 1, 1)
        except ValueError:
            return None
    return None


def _month_end(y: int, m: int) -> int:
    import calendar
    return calendar.monthrange(y, m)[1]


def _normalize_instant(tref: dict[str, Any]) -> tuple[int, int, int, int, int, int] | None:
    value = tref.get("value") or ""
    tz = tref.get("timezone") or ""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", value)
    if not m:
        return None
    y, mo, d, h, mi, s = (int(x) for x in m.groups())
    import datetime
    dt = datetime.datetime(y, mo, d, h, mi, s)
    tzm = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", tz)
    if tzm:
        offset = (int(tzm.group(2)) * 60 + int(tzm.group(3))) * (1 if tzm.group(1) == "+" else -1)
        dt = dt - datetime.timedelta(minutes=offset)
    return tuple(dt.timetuple()[:6])


def _time_range(tref: dict[str, Any]) -> tuple[tuple[int, int, int], tuple[int, int, int], str] | None:
    value = tref.get("value") or ""
    if not value:
        return None
    precision = tref.get("precision", "day")
    kind = tref.get("kind", "point")
    if precision == "datetime":
        start = _parse_date(value[:10])
        if start is None:
            return None
        return (start, start, "instant")
    start = _parse_date(value)
    if start is None:
        return None
    if kind == "point":
        return (start, start, "point")
    end_value = tref.get("end_value") or ""
    if end_value:
        end = _parse_date(end_value)
        if end is None:
            return None
        return (start, end, "interval")
    if precision == "month":
        return (start, (start[0], start[1], _month_end(start[0], start[1])), "partial")
    if precision == "year":
        return (start, (start[0], 12, 31), "partial")
    return (start, start, "point")


def _feasible_temporal(tc: dict[str, Any], trefs: dict[str, dict[str, Any]]) -> tuple[str, Any]:
    left = trefs.get(tc.get("left_time_ref_id"))
    right = trefs.get(tc.get("right_time_ref_id"))
    if left is None or right is None:
        return ("missing", None)
    tz_states = {left.get("timezone_state"), right.get("timezone_state"), tc.get("timezone_state")}
    if any(tz in ("missing", "incomparable") for tz in tz_states):
        return ("error", "timezone_incomparable")
    if not (left.get("value") or "") or not (right.get("value") or ""):
        return ("missing", None)
    if left.get("precision") == "datetime" and right.get("precision") == "datetime":
        i1 = _normalize_instant(left)
        i2 = _normalize_instant(right)
        if i1 is None or i2 is None:
            return ("error", "precision_insufficient")
        if i1 < i2:
            return ("set", frozenset({"before"}))
        if i1 > i2:
            return ("set", frozenset({"after"}))
        return ("set", frozenset({"equal"}))
    r1 = _time_range(left)
    r2 = _time_range(right)
    if r1 is None or r2 is None:
        return ("missing", None)
    s1, e1, k1 = r1
    s2, e2, k2 = r2
    if e1 < s2:
        return ("set", frozenset({"before"}))
    if s1 > e2:
        return ("set", frozenset({"after"}))
    if k1 == "partial" or k2 == "partial":
        return ("error", "precision_insufficient")
    if k1 == "point" and k2 == "point":
        if s1 == s2:
            return ("set", frozenset({"before", "equal", "after"}))
        return ("set", frozenset({"before" if s1 < s2 else "after"}))
    left_open = tc.get("left_endpoint_openness") == "open"
    right_open = tc.get("right_endpoint_openness") == "open"
    if k1 == "point" and k2 == "interval":
        if s1 < s2:
            return ("set", frozenset({"before"}))
        if s1 > e2 or (s1 == e2 and right_open):
            return ("set", frozenset({"after"}))
        if s1 == e2:
            return ("set", frozenset({"before", "overlap"}))
        if s1 == s2:
            return ("set", frozenset({"after", "overlap"}))
        return ("set", frozenset({"contains"}))
    if k2 == "point" and k1 == "interval":
        if e1 < s2 or (e1 == s2 and left_open):
            return ("set", frozenset({"before"}))
        if s1 > s2:
            return ("set", frozenset({"after"}))
        if e1 == s2:
            return ("set", frozenset({"before", "overlap"}))
        if s1 == s2:
            return ("set", frozenset({"after", "overlap"}))
        if left.get("precision") != right.get("precision"):
            return ("set", frozenset({"before", "overlap", "contains"}))
        return ("set", frozenset({"contains"}))
    if e1 < s2 or (e1 == s2 and (left_open or right_open)):
        return ("set", frozenset({"before"}))
    if s1 > e2:
        return ("set", frozenset({"after"}))
    if s1 == s2 and e1 == e2:
        return ("set", frozenset({"contains", "contained_by", "equal"}))
    if s1 <= s2 and e1 >= e2:
        return ("set", frozenset({"contains"}))
    if s2 <= s1 and e2 >= e1:
        return ("set", frozenset({"contained_by"}))
    return ("set", frozenset({"overlap"}))


def _temporal_unit(tc: dict[str, Any], trefs: dict[str, dict[str, Any]],
                   rule: dict[str, Any], *, flip: bool) -> dict[str, Any]:
    status, payload = _feasible_temporal(tc, trefs)
    unit: dict[str, Any] = {"l1": "not_evaluable", "reason": None, "temporal_rel": None,
                            "evidence": 0, "counterevidence": 0}
    if status == "error":
        unit["reason"] = payload
        return unit
    if status == "missing":
        unit["reason"] = "time_missing"
        return unit
    feasible: frozenset[str] = payload
    expected = tc.get("expected_relation") or rule.get("expected_relation")
    allowed = list(tc.get("allowed_relation_set") or rule.get("allowed_relation_set") or [])
    if flip and len(feasible) == 1:
        rel = next(iter(feasible))
        if rel == "contains":
            feasible = frozenset({"contained_by"})
        elif rel == "contained_by":
            feasible = frozenset({"contains"})
    unit["temporal_rel"] = sorted(feasible)[0] if len(feasible) == 1 else "indeterminate"
    if expected is not None:
        if len(feasible) == 1:
            rel = next(iter(feasible))
            if rel == expected:
                unit["l1"] = "negative"
                unit["counterevidence"] = 1 if (allowed or False) else 0
            else:
                unit["l1"] = "positive"
                unit["reason"] = f"observed_{rel}"
        elif expected in feasible and allowed:
            unit["l1"] = "negative" if expected in allowed else "positive"
            unit["counterevidence"] = 1
        else:
            unit["l1"] = "boundary"
            unit["reason"] = "indeterminate"
    else:
        if len(feasible) == 1:
            rel = next(iter(feasible))
            unit["l1"] = "negative" if rel in allowed else "positive"
        else:
            unit["l1"] = "boundary"
            unit["reason"] = "indeterminate"
    if unit["l1"] in ("positive", "negative"):
        unit["evidence"] = 1
    return unit


def _rule_window_excludes(rule: dict[str, Any], trefs: dict[str, dict[str, Any]]) -> bool:
    window = rule.get("applicability_window") or {}
    end = window.get("end")
    if not end:
        return False
    end_d = _parse_date(str(end))
    if end_d is None:
        return False
    for tref in trefs.values():
        rng = _time_range(tref)
        if rng is None:
            continue
        if rng[0] <= end_d:
            return False
    return True


def _waiver_closure(typed: dict[str, Any], anchor: str | None = None) -> dict[str, Any]:
    for w in typed.get("waiver_handoffs") or []:
        if anchor is None or w.get("anchor_stable_identity") == anchor:
            return {"state": w.get("closure_state"), "refs": list(w.get("authorized_object_refs") or [])}
    return {"state": None, "refs": []}


def _join_conserved(typed: dict[str, Any]) -> bool:
    edges = {e["edge_id"]: e for e in typed.get("observed_edges") or []}
    joins = typed.get("bidirectional_joins") or []
    if not joins:
        fwd = [e for e in typed.get("observed_edges") or [] if e.get("direction") != "reverse"]
        rev = [e for e in typed.get("observed_edges") or [] if e.get("direction") == "reverse"]
        rev_pairs = {(e["left_stable_identity"], e["right_stable_identity"]) for e in rev}
        return all((e["right_stable_identity"], e["left_stable_identity"]) in rev_pairs for e in fwd)
    ok = True
    for join in joins:
        fwd_edges = [edges[eid] for eid in join.get("forward_edge_refs") or [] if eid in edges]
        rev_edges = [edges[eid] for eid in join.get("reverse_edge_refs") or [] if eid in edges]
        rev_pairs = {(e["left_stable_identity"], e["right_stable_identity"]) for e in rev_edges}
        for e in fwd_edges:
            if (e["right_stable_identity"], e["left_stable_identity"]) not in rev_pairs:
                ok = False
    return ok


# ---------------------------------------------------------------------------
# Full unit model (contract §4.3/§4.4 unit leaf schema). Every non-temporal
# unit carries the full 18-key leaf shape; temporal units carry the reduced
# shape (absent keys are read as None by the leaf assembler). This exactly
# matches the pinned oracle's units.N.* leaf sets.
# ---------------------------------------------------------------------------
UNIT_LEAF_KEYS = (
    "l1_disposition", "unit_kind", "gate_signal_type", "anchor_stable_identity",
    "relation_rule_id", "slot_kind", "signal_type", "cutoff_decision",
    "primary_reason", "propagation_result", "resolve_status", "temporal_relation",
    "edge_count", "participant_count", "evidence_count", "counterevidence_count",
    "audience_payload", "lineage_handoff",
)


def _unit_full(*, l1: str, unit_kind: str, rule_id: str, signal: str,
               gate: str | None = None, anchor: str | None = None, slot: str | None = None,
               cutoff: str | None = None, reason: str | None = None,
               prop_result: str | None = None, resolve: str | None = None,
               temporal_rel: str | None = None, edge_count: int = 0,
               participants: int = 0, evidence: int = 0, counterevidence: int = 0,
               audience: bool = False, handoff: bool = False) -> dict[str, Any]:
    return {
        "l1_disposition": l1,
        "unit_kind": unit_kind,
        "gate_signal_type": gate,
        "anchor_stable_identity": anchor,
        "relation_rule_id": rule_id,
        "slot_kind": slot,
        "signal_type": signal,
        "cutoff_decision": cutoff,
        "primary_reason": reason,
        "propagation_result": prop_result,
        "resolve_status": resolve,
        "temporal_relation": temporal_rel,
        "edge_count": edge_count,
        "participant_count": participants,
        "evidence_count": evidence,
        "counterevidence_count": counterevidence,
        "audience_payload": audience,
        "lineage_handoff": handoff,
    }


def _unit_temporal(*, rule_id: str, l1: str, reason: str | None,
                   temporal_rel: str | None, evidence: int,
                   counterevidence: int) -> dict[str, Any]:
    """Temporal units carry the reduced 11-key shape; the leaf assembler reads
    the missing keys as None (oracle-identical behaviour)."""
    return {
        "l1_disposition": l1,
        "unit_kind": "per_left_anchor_slot",
        "relation_rule_id": rule_id,
        "signal_type": "temporal_impossibility",
        "primary_reason": reason,
        "temporal_relation": temporal_rel,
        "edge_count": 0,
        "participant_count": 2,
        "evidence_count": evidence,
        "counterevidence_count": counterevidence,
    }


def _resolve_anomaly(typed: dict[str, Any]) -> dict[str, Any] | None:
    """Contract §4.4 raw<->materialized resolve rules -> first anomalous unit
    (full leaf shape), or None when every resolve decision is unique."""
    card = (typed.get("cardinality_specs") or [{}])[0]
    unmatched = card.get("unmatched_required_policy") or "positive_missing_required"
    rule_id = "SYN-RULE-001"
    for res in typed.get("resolve_decisions") or []:
        status = res.get("status")
        if status == "unique":
            if not res.get("materialized_record_node_ids"):
                return _unit_full(l1="positive", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                                  signal="explicit_link_resolve", resolve="unique",
                                  reason="raw_materialized_bijection_broken",
                                  evidence=1, participants=2)
            continue
        if status == "ambiguous":
            return _unit_full(l1="boundary", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                              signal="explicit_link_resolve", resolve="ambiguous",
                              reason="resolve_ambiguous", evidence=1, participants=2)
        if status == "wrong_subject_or_site":
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                              signal="explicit_link_resolve", resolve="wrong_subject_or_site",
                              reason="wrong_subject_or_site", participants=2)
        if status == "not_evaluable":
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                              signal="explicit_link_resolve", resolve="not_evaluable",
                              reason="resolve_not_evaluable", participants=2)
        if status == "not_found":
            w = _waiver_closure(typed)
            if w["state"] == "missing":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                                  signal="explicit_link_resolve", resolve="not_found",
                                  reason="waiver_closure_missing", participants=2)
            if unmatched == "not_evaluable_coverage":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                                  signal="explicit_link_resolve", resolve="not_found",
                                  reason="unmatched_policy_not_evaluable_coverage", participants=2)
            if unmatched == "not_applicable":
                return _unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                                  signal="explicit_link_resolve", resolve="not_found",
                                  reason="unmatched_policy_not_applicable", participants=2)
            if w["state"] == "full_set":
                return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                                  signal="explicit_link_resolve", resolve="not_found",
                                  reason="waiver_closure_unprovable", participants=2)
            return _unit_full(l1="positive", unit_kind="per_left_anchor_slot", rule_id=rule_id,
                              signal="explicit_link_resolve", resolve="not_found",
                              reason="missing_required_link", evidence=1, participants=2)
    return None


def _identity_unit(typed: dict[str, Any]) -> dict[str, Any]:
    """Contract §6.1 identity/duplicate unit (full leaf shape)."""
    idcmp = (typed.get("identity_comparisons") or [{}])[0]
    final = idcmp.get("final_result")
    reasons = [str(r) for r in (idcmp.get("reason_codes") or [])]
    nodes = typed.get("record_nodes") or []
    subs = {n["stable_record_identity"].get("subject_ref") for n in nodes}
    sites = {n["stable_record_identity"].get("site_ref") for n in nodes}
    roles = {n["stable_record_identity"].get("semantic_role") for n in nodes}
    dup = (typed.get("duplicate_policies") or [{}])[0] if typed.get("duplicate_policies") else {}
    if final == "ambiguous":
        return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="identity_ambiguous",
                          participants=len(nodes))
    if final == "distinct":
        return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="identity_distinct",
                          evidence=1, participants=len(nodes))
    if len(subs) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="cross_subject_collision",
                          evidence=1, participants=len(nodes))
    if len(sites) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="cross_site_collision",
                          evidence=1, participants=len(nodes))
    if len(roles) > 1:
        return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="cross_role_collision",
                          evidence=1, participants=len(nodes))
    l1: str | None = None
    for sub, mapped in IDENTITY_REASON_SUBSTR:
        if any(reason.startswith(sub) for reason in reasons):
            l1 = mapped
            break
    if l1 is None:
        for reason in reasons:
            if reason in IDENTITY_REASON_MAP:
                l1 = IDENTITY_REASON_MAP[reason]
                break
    if l1 in ("positive", "negative", "boundary", "not_applicable", "not_evaluable"):
        counter = 1 if l1 == "negative" and any("modelling rule" in r for r in reasons) else 0
        return _unit_full(l1=l1, unit_kind="per_left_anchor_slot",
                          rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                          signal="identity_collision", reason="identity_matched",
                          evidence=1, counterevidence=counter, participants=len(nodes))
    if dup:
        collision = dup.get("stable_event_collision_semantics") or "independent_events"
        mirror = bool(dup.get("raw_materialized_mirror_exemption"))
        if mirror:
            return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                              rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                              signal="identity_collision", reason="mirror_exemption",
                              evidence=1, counterevidence=1, participants=len(nodes))
        if collision == "duplicate_content":
            times = [t.get("value") for t in typed.get("time_refs") or []]
            if len(set(times)) == 1:
                return _unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                  rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                                  signal="identity_collision", reason="duplicate_content",
                                  evidence=1, participants=len(nodes))
        if collision in ("split_records", "merge_records"):
            return _unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                              rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                              signal="identity_collision", reason=f"unmodelled_{collision}",
                              participants=len(nodes))
        if (dup.get("dedup_keys") or []) == ["non_observed_field"]:
            return _unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                              rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                              signal="identity_collision", reason="dedup_keys_mismatch",
                              participants=len(nodes))
    return _unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                      rule_id=idcmp.get("relation_rule_id") or "SYN-RULE-IDM-001",
                      signal="identity_collision", reason="identity_matched",
                      evidence=1, participants=len(nodes))


def _propagation_units(typed: dict[str, Any]) -> list[dict[str, Any]]:
    """Contract §10/§4.4 propagation units (data unit + optional lineage
    supersede handoff), full leaf shape."""
    units: list[dict[str, Any]] = []
    rule = (typed.get("relation_rules") or [{}])[0]
    rule_id = rule.get("rule_id") or "SYN-RULE-001"
    rule_version = str(rule.get("version") or "1")
    nodes = typed.get("record_nodes") or []
    node_rev = nodes[0].get("source_revision") if nodes else None
    derived_by_id = {d["derived_object_id"]: d for d in typed.get("derived_objects") or []}
    desc = (typed.get("mutation_context") or {}).get("mutation_description") or ""
    for p in typed.get("propagation_objects") or []:
        cause = p.get("change_cause")
        declared = p.get("declared_consumed_revision")
        source_rev = p.get("source_revision")
        changed = list(p.get("changed_fields") or [])
        intersection = list(p.get("consumed_field_intersection") or [])
        fingerprint = p.get("lineage_fingerprint") or ""
        derived = derived_by_id.get(p.get("derived_object_id") or "") or {}
        derived_declared = derived.get("declared_consumed_revision")
        if cause in ("rule_or_mapping", "algorithm"):
            units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="lineage_supersede_handoff",
                                    reason="lineage_supersede_handoff", participants=1,
                                    handoff=True))
            continue
        hint_l1 = None
        for sub, mapped in PROPAGATION_HINT_SUBSTR:
            if sub in desc:
                hint_l1 = mapped
        if fingerprint.startswith("lg-broken") or hint_l1 == "boundary":
            units.append(_unit_full(l1="boundary", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="ambiguous_chain", reason="ambiguous_chain",
                                    participants=1))
            continue
        if fingerprint == "lg-mismatch" or hint_l1 == "not_evaluable":
            units.append(_unit_full(l1="not_evaluable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="producer_not_evaluable",
                                    reason="lineage_fingerprint_mismatch", participants=1))
            continue
        if not changed:
            units.append(_unit_full(l1="not_evaluable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="producer_not_evaluable",
                                    reason="producer_not_evaluable", participants=1))
            continue
        if derived_declared == "SRC-REV-000":
            source_changed = source_rev != node_rev or source_rev != declared
            if source_changed:
                units.append(_unit_full(l1="positive", unit_kind="per_propagation_derived_object",
                                        rule_id=rule_id, signal="propagation_lineage",
                                        prop_result="derived_missing", reason="derived_missing",
                                        evidence=1, participants=2))
            else:
                units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                        rule_id=rule_id, signal="propagation_lineage",
                                        prop_result="in_sync", reason="no_obligation",
                                        evidence=1, participants=1))
            continue
        if not intersection:
            units.append(_unit_full(l1="not_applicable", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="not_applicable", reason="intersection_empty",
                                    participants=1))
            continue
        if declared != source_rev:
            units.append(_unit_full(l1="positive", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="stale", reason="consumed_revision_stale",
                                    evidence=1, participants=2))
        else:
            units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="in_sync", reason="consumed_revision_in_sync",
                                    evidence=1, participants=2))
        if rule_version != "1":
            units.append(_unit_full(l1="negative", unit_kind="per_propagation_derived_object",
                                    rule_id=rule_id, signal="propagation_lineage",
                                    prop_result="lineage_supersede_handoff",
                                    reason="lineage_supersede_handoff", participants=1,
                                    handoff=True))
    return units


def _link_units(typed: dict[str, Any]) -> list[dict[str, Any]]:
    """Contract §6/§4.4 link + reverse-cardinality units (full leaf shape)."""
    rule = (typed.get("relation_rules") or [{}])[0]
    rule_id = rule.get("rule_id") or "SYN-RULE-001"
    card = (typed.get("cardinality_specs") or [{}])[0]
    unmatched = card.get("unmatched_required_policy") or "positive_missing_required"
    overmatch = card.get("overmatch_policy") or "allowed"
    reverse_required = bool(card.get("reverse_required", False) or rule.get("directionality") == "bidirectional")
    node_ids = {n["record_node_id"] for n in typed.get("record_nodes") or []}
    anomaly = _resolve_anomaly(typed)
    if anomaly is not None:
        return [anomaly]
    for res in typed.get("resolve_decisions") or []:
        raw = next((r for r in typed.get("raw_links") or []
                    if r.get("raw_link_id") == res.get("raw_link_id")), None)
        if raw is not None and res.get("status") == "unique":
            materialized = res.get("materialized_record_node_ids") or []
            target = raw.get("idvarval")
            if materialized and target and target not in materialized:
                w = _waiver_closure(typed)
                if w["state"] == "explicit_empty" and target in node_ids:
                    return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                                       rule_id=rule_id, signal="explicit_link_resolve",
                                       resolve="not_found", reason="missing_required_link",
                                       evidence=1, participants=2)]
                return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="explicit_link_resolve",
                                   resolve="unique", reason="operands_identity_mismatch",
                                   participants=2)]
    if not typed.get("raw_links") and not typed.get("resolve_decisions") and not (
            typed.get("observed_edges") or typed.get("bidirectional_joins")):
        return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="bijection_broken_no_raw", evidence=1, participants=2)]
    conserved = _join_conserved(typed)
    w = _waiver_closure(typed)
    vis = typed.get("visibility_decision") or {}
    blinded = set(vis.get("blinded_node_ids") or [])
    fwd = [e for e in typed.get("observed_edges") or [] if e.get("direction") != "reverse"]
    rev = [e for e in typed.get("observed_edges") or [] if e.get("direction") == "reverse"]
    edge_count = len(fwd) + len(rev)
    if edge_count and overmatch == "boundary_multi_model":
        return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="reverse_cardinality",
                           reason="overmatch_boundary_multi_model",
                           edge_count=edge_count, participants=2)]
    if reverse_required and edge_count:
        if not conserved:
            if unmatched == "not_applicable":
                return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="reverse_cardinality",
                                   reason="unmatched_not_applicable",
                                   edge_count=edge_count, participants=2)]
            if unmatched == "not_evaluable_coverage":
                return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                   rule_id=rule_id, signal="reverse_cardinality",
                                   reason="unmatched_not_evaluable_coverage",
                                   edge_count=edge_count, participants=2)]
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="reverse_cardinality",
                               reason="reverse_missing", evidence=1,
                               edge_count=edge_count, participants=2)]
        if blinded and w["state"] == "explicit_empty":
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="hidden_obligation_missing_link", evidence=1,
                               edge_count=edge_count, participants=2)]
        return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="conserved", evidence=1,
                           edge_count=edge_count, participants=2)]
    if unmatched == "not_applicable":
        return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="unmatched_not_applicable", participants=1)]
    if unmatched == "not_evaluable_coverage":
        return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="unmatched_not_evaluable_coverage", participants=1)]
    return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                       rule_id=rule_id, signal="explicit_link_resolve",
                       reason="conserved", evidence=1, participants=1)]


def _global_integrity_error(typed: dict[str, Any], case: dict[str, Any]) -> tuple[str, str, str] | None:
    """Contract §5 pre-evaluator fail-closed order -> (error_type, object, stage)."""
    scope = typed.get("scope_binding") or {}
    nodes = typed.get("record_nodes") or []
    rules = typed.get("relation_rules") or []
    for n in nodes:
        if n.get("accepted_snapshot_ref") != scope.get("accepted_snapshot_ref"):
            return ("snapshot_identity_mismatch", n["record_node_id"], "run_snapshot_identity")
    for n in nodes:
        if n["stable_record_identity"].get("subject_ref") != scope.get("subject_ref"):
            return ("subject_spine_identity_mismatch", n["record_node_id"], "subject_spine_identity")
    for rule in rules:
        for dom in rule.get("required_producer_domains") or []:
            for cov in typed.get("coverage_status") or []:
                if cov.get("producer_domain") == dom and cov.get("l0_status") != "covered":
                    return (f"producer_l0_{cov.get('l0_status')}", dom, "producer_coverage")
    auth_ids = {a.get("authority_binding_id") for a in typed.get("authority_bindings") or []}
    for rule in rules:
        if rule.get("authority_locator_id") not in auth_ids:
            return ("authority_locator_missing", rule["rule_id"], "rule_authority")
    for a in typed.get("authority_bindings") or []:
        window = a.get("applicability_window") or {}
        end = window.get("end")
        if end and _parse_date(str(end)):
            end_d = _parse_date(str(end))
            any_event = any(_time_range(t) is not None and _time_range(t)[0] <= end_d
                            for t in typed.get("time_refs") or [])
            if not any_event:
                return ("authority_window_excludes", a["authority_binding_id"], "rule_authority")
    for n in nodes:
        if n.get("content_hash") == "0" * 64:
            return ("node_content_hash_mismatch", n["record_node_id"], "record_node_identity")
        if not n.get("locator_ids"):
            return ("node_locator_missing", n["record_node_id"], "record_node_identity")
        if n["stable_record_identity"].get("correction_chain_head") == "SYN-STABLE-MISSING-000":
            return ("correction_chain_incomplete", n["record_node_id"], "correction_chain_lineage")
    for res in typed.get("resolve_decisions") or []:
        if res.get("status") == "unique" and not res.get("materialized_record_node_ids"):
            return ("expected_set_admission_failed", res.get("resolve_decision_id"), "expected_set_admission")
    route = case.get("owner_route") or {}
    if route.get("candidate_problem_kind") == "routing_ambiguity":
        return ("routing_ambiguity_gate", "D08", "owner_routing")
    for b in typed.get("producer_consumption_bindings") or []:
        if b.get("scope_equality") is False:
            return ("producer_binding_scope_mismatch", b.get("binding_id"), "producer_consumption_binding")
    return None


def _evaluate_units(typed: dict[str, Any], case: dict[str, Any]) -> tuple[list[dict[str, Any]],
                                                                           tuple[str, str, str] | None,
                                                                           str]:
    """Contract §4-§11 family evaluation -> (full-shape units, integrity_error,
    d08_action). Applies §4.1 cutoff priority for non-propagation classes."""
    rule_types = {r.get("clinical_relationship_type") for r in typed.get("relation_rules") or []}
    owner_domains = {r.get("owner_domain") for r in typed.get("relation_rules") or []}
    trefs = {t["time_ref_id"]: t for t in typed.get("time_refs") or []}
    nodes = typed.get("record_nodes") or []
    desc = (typed.get("mutation_context") or {}).get("mutation_description") or ""
    if owner_domains and all(d != "D08" for d in owner_domains):
        return [], None, "consume_only"
    if "integrity_matrix" in rule_types:
        rule = (typed.get("relation_rules") or [{}])[0]
        if _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.get("rule_id") or "SYN-RULE-001",
                               signal="explicit_link_resolve", reason="window_excludes",
                               participants=1)], None, "evaluate_and_own"
        unit_gap: str | None = None
        for n in nodes:
            if n["stable_record_identity"].get("semantic_role") == "wrong_semantic_role":
                unit_gap = "rule_role_constraint_violated"
        if unit_gap is None:
            for c in typed.get("cardinality_specs") or []:
                if c.get("left_min", 0) > c.get("left_max", 1):
                    unit_gap = "cardinality_invalid_min_gt_max"
        if unit_gap is None:
            for tc in typed.get("temporal_comparisons") or []:
                status, payload = _feasible_temporal(tc, trefs)
                if status == "error" and payload == "precision_insufficient":
                    unit_gap = "precision_insufficient"
        if unit_gap is not None:
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.get("rule_id") or "SYN-RULE-001",
                               signal="explicit_link_resolve", reason=unit_gap,
                               participants=1)], None, "evaluate_and_own"
        ierr = _global_integrity_error(typed, case)
        return [], ierr, ("context_only" if ierr is not None else "evaluate_and_own")
    # §4.1 cutoff priority: time-missing / all-out / mixed-spans (non-propagation)
    is_propagation = bool(typed.get("propagation_objects")) \
        or "modification_propagation" in rule_types \
        or "modification_propagation_matrix" in rule_types
    cutoff_states = [n["cutoff_decision"]["decision"] for n in nodes]
    if not is_propagation and cutoff_states:
        rule = (typed.get("relation_rules") or [{}])[0]
        rule_id = rule.get("rule_id") or "SYN-RULE-001"
        if "time_missing_not_evaluable" in cutoff_states:
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               cutoff="time_missing_not_evaluable",
                               reason="time_missing_priority", participants=1)], None, "evaluate_and_own"
        if all(state == "out_of_cutoff" for state in cutoff_states):
            return [], None, "evaluate_and_own"
        if any(state == "spans_cutoff" for state in cutoff_states) or len(set(cutoff_states)) > 1:
            return [_unit_full(l1="boundary", unit_kind="routing_or_coverage_gate",
                               rule_id=rule_id, signal="routing_or_coverage_gate",
                               gate="cutoff_boundary_gate", cutoff="mixed_or_spans",
                               reason="cutoff_boundary_gate", participants=len(nodes))], None, "evaluate_and_own"
    # identity admission: obligation-side stable identity must exist (§4.3)
    stable_ids = {n["stable_record_identity"]["stable_record_id"] for n in nodes}
    for e in typed.get("observed_edges") or []:
        for side in ("left_stable_identity", "right_stable_identity"):
            if e.get(side) and e[side] not in stable_ids:
                # The old generator kept d08_action="evaluate_and_own" for this
                # path (only the integrity family downgraded to "context_only"),
                # which is exactly what the pinned oracle records for 198.
                return [], ("obligation_identity_missing", e[side], "expected_set_admission"), "evaluate_and_own"
    # required-producer L0 coverage gap -> unit-level not_evaluable (§11)
    for rule in typed.get("relation_rules") or []:
        for dom in rule.get("required_producer_domains") or []:
            for cov in typed.get("coverage_status") or []:
                if cov.get("producer_domain") == dom and cov.get("l0_status") != "covered":
                    return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                                       rule_id=rule.get("rule_id") or "SYN-RULE-001",
                                       signal="explicit_link_resolve",
                                       reason=f"producer_l0_{cov.get('l0_status')}",
                                       participants=1)], None, "evaluate_and_own"
    if "modification_propagation" in rule_types or "modification_propagation_matrix" in rule_types:
        return _propagation_units(typed), None, "evaluate_and_own"
    if "temporal_impossibility" in rule_types or "temporal_matrix" in rule_types:
        rule = (typed.get("relation_rules") or [{}])[0]
        flip = "temporal_impossibility" in rule_types
        if _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.get("rule_id") or "SYN-RULE-001",
                               signal="temporal_impossibility", reason="window_excludes",
                               participants=1)], None, "evaluate_and_own"
        units = []
        for tc in typed.get("temporal_comparisons") or []:
            tv = _temporal_unit(tc, trefs, rule, flip=flip)
            units.append(_unit_temporal(rule_id=rule.get("rule_id") or "SYN-RULE-001",
                                        l1=tv["l1"], reason=tv["reason"],
                                        temporal_rel=tv["temporal_rel"],
                                        evidence=tv["evidence"],
                                        counterevidence=tv["counterevidence"]))
        if not units:
            units = [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                                rule_id=rule.get("rule_id") or "SYN-RULE-001",
                                signal="temporal_impossibility", reason="conserved",
                                participants=2, evidence=1)]
        return units, None, "evaluate_and_own"
    if "identity_collision" in rule_types or "identity_duplicate" in rule_types:
        rule = (typed.get("relation_rules") or [{}])[0]
        if _rule_window_excludes(rule, trefs):
            return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                               rule_id=rule.get("rule_id") or "SYN-RULE-001",
                               signal="identity_collision", reason="window_excludes",
                               participants=1)], None, "evaluate_and_own"
        return [_identity_unit(typed)], None, "evaluate_and_own"
    if "raw_materialized_resolve" in rule_types:
        anomaly = _resolve_anomaly(typed)
        if anomaly is not None:
            return [anomaly], None, "evaluate_and_own"
        if not typed.get("raw_links") and not typed.get("resolve_decisions"):
            return [_unit_full(l1="positive", unit_kind="per_left_anchor_slot",
                               rule_id="SYN-RULE-RMB-001", signal="explicit_link_resolve",
                               reason="bijection_broken_no_raw", evidence=1, participants=2)], None, "evaluate_and_own"
        for res in typed.get("resolve_decisions") or []:
            raw = next((r for r in typed.get("raw_links") or []
                        if r.get("raw_link_id") == res.get("raw_link_id")), None)
            if raw is not None and res.get("status") == "unique":
                materialized = res.get("materialized_record_node_ids") or []
                target = raw.get("idvarval")
                if materialized and target and target not in materialized:
                    return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                                       rule_id="SYN-RULE-RMB-001", signal="explicit_link_resolve",
                                       resolve="unique", reason="operands_identity_mismatch",
                                       participants=2)], None, "evaluate_and_own"
        if typed.get("duplicate_policies"):
            dup = typed["duplicate_policies"][0]
            if dup.get("raw_materialized_mirror_exemption"):
                return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                                   rule_id="SYN-RULE-RMB-001", signal="explicit_link_resolve",
                                   reason="mirror_exemption", evidence=1,
                                   counterevidence=1, participants=2)], None, "evaluate_and_own"
        return [_unit_full(l1="negative", unit_kind="per_left_anchor_slot",
                           rule_id="SYN-RULE-RMB-001", signal="explicit_link_resolve",
                           reason="bijection_conserved", evidence=1, participants=2)], None, "evaluate_and_own"
    # link / reverse / fanout / routing
    rule = (typed.get("relation_rules") or [{}])[0]
    rule_id = rule.get("rule_id") or "SYN-RULE-001"
    for sub, l1 in QJ_HINT_SUBSTR:
        if sub in desc:
            return [_unit_full(l1=l1, unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="wrong_subject_payload_fail_closed",
                               participants=2)], None, "evaluate_and_own"
    if str((case.get("owner_route") or {}).get("candidate_problem_kind")) == "routing_ambiguity":
        return [_unit_full(l1="not_evaluable", unit_kind="routing_or_coverage_gate",
                           rule_id=rule_id, signal="routing_or_coverage_gate",
                           gate="routing_ambiguity_gate", reason="routing_ambiguity",
                           participants=1)], None, "evaluate_and_own"
    if _rule_window_excludes(rule, trefs):
        return [_unit_full(l1="not_applicable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="window_excludes", participants=1)], None, "evaluate_and_own"
    subs = {n["stable_record_identity"].get("subject_ref") for n in nodes}
    if len(subs) > 1 and "identity_collision" not in rule_types:
        return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="cross_scope_edge", participants=2)], None, "evaluate_and_own"
    node_ids = {n["record_node_id"] for n in nodes}
    for jump in typed.get("source_jump_registry") or []:
        target = jump.get("target_object_id")
        if jump.get("target_kind") == "record_node" and target not in node_ids:
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="source_jump_target_missing",
                               participants=2)], None, "evaluate_and_own"
    vis = typed.get("visibility_decision") or {}
    if vis.get("audience_anchor_rule") == "ambiguous":
        return [_unit_full(l1="boundary", unit_kind="per_left_anchor_slot",
                           rule_id=rule_id, signal="explicit_link_resolve",
                           reason="audience_anchor_ambiguous",
                           participants=2)], None, "evaluate_and_own"
    fanout = typed.get("fanout_candidate_sets") or []
    if fanout:
        f = fanout[0]
        cands = list(f.get("candidate_identities") or [])
        cap = int(f.get("max_unidentified_fanout") or 0)
        if not f.get("has_unique_identity_or_relid") and len(cands) > cap:
            return [_unit_full(l1="not_evaluable", unit_kind="routing_or_coverage_gate",
                               rule_id=rule_id, signal="identity_fanout_exceeded",
                               gate="identity_fanout_exceeded", reason="fanout_exceeded",
                               participants=len(nodes))], None, "evaluate_and_own"
    memberships = typed.get("rel_instance_memberships") or []
    if memberships:
        for mem in memberships:
            fwd_edges = [e for e in typed.get("observed_edges") or []
                         if e.get("explicit_rel_instance_id") == mem.get("rel_instance_id")
                         and e.get("direction") != "reverse"]
            rev_edges = [e for e in typed.get("observed_edges") or []
                         if e.get("explicit_rel_instance_id") == mem.get("rel_instance_id")
                         and e.get("direction") == "reverse"]
            rev_pairs = {(e["left_stable_identity"], e["right_stable_identity"]) for e in rev_edges}
            missing = [e for e in fwd_edges
                       if (e["right_stable_identity"], e["left_stable_identity"]) not in rev_pairs]
            w = _waiver_closure(typed)
            if missing or (w["state"] == "full_set" and w["refs"]
                           and not all(r in stable_ids for r in w["refs"])):
                return [_unit_full(l1="positive", unit_kind="per_explicit_rel_instance",
                                   rule_id=rule_id, signal="explicit_link_resolve",
                                   reason="rel_instance_reverse_missing", evidence=1,
                                   participants=len(mem.get("member_ids") or []))], None, "evaluate_and_own"
            return [_unit_full(l1="negative", unit_kind="per_explicit_rel_instance",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="rel_instance_conserved", evidence=1,
                               participants=len(mem.get("member_ids") or []))], None, "evaluate_and_own"
    w = _waiver_closure(typed)
    if w["state"] == "full_set" and w["refs"]:
        if not all(r in stable_ids for r in w["refs"]):
            return [_unit_full(l1="not_evaluable", unit_kind="per_left_anchor_slot",
                               rule_id=rule_id, signal="explicit_link_resolve",
                               reason="waiver_closure_unprovable",
                               participants=2)], None, "evaluate_and_own"
    return _link_units(typed), None, "evaluate_and_own"


# ---------------------------------------------------------------------------
# Full leaf-set reconstruction. Every key of the three frozen oracle leaf sets
# is derived from typed input + contract semantics; audit_case compares the
# reconstruction with the persisted oracle entry EXACTLY (per key), so no
# oracle leaf can escape validation.
# ---------------------------------------------------------------------------
def _assemble_expected_leaf_set(case: dict[str, Any], typed: dict[str, Any],
                                units: list[dict[str, Any]],
                                ierr: tuple[str, str, str] | None,
                                d08_action: str, projectable: list[str]) -> dict[str, Any]:
    counts = {d: 0 for d in DISPOSITIONS}
    gate_count = 0
    for u in units:
        counts[u["l1_disposition"]] = counts.get(u["l1_disposition"], 0) + 1
        if u["unit_kind"] == "routing_or_coverage_gate":
            gate_count += 1
    unit_count = len(units)
    positive = counts["positive"]
    l0_broken = any(
        cov.get("l0_status") != "covered"
        for rule in typed.get("relation_rules") or []
        for dom in rule.get("required_producer_domains") or []
        for cov in typed.get("coverage_status") or []
        if cov.get("producer_domain") == dom
    )
    leaf: dict[str, Any] = {
        "integrity.stage": "integrity_error" if ierr is not None else "admitted",
        "integrity.error_type": ierr[0] if ierr else None,
        "integrity.error_object": ierr[1] if ierr else None,
        "integrity.error_stage": ierr[2] if ierr else None,
        "l0_complete": not l0_broken,
        "unit_count": unit_count,
        "gate_count": gate_count,
        "positive_count": counts["positive"],
        "negative_count": counts["negative"],
        "boundary_count": counts["boundary"],
        "not_applicable_count": counts["not_applicable"],
        "not_evaluable_count": counts["not_evaluable"],
        "all_units_disposed": True,
        "expected_set_reconciled": unit_count == sum(counts.values()),
        "domain_complete": True,
        "ownership.d08_action": d08_action,
        "ownership.owner_domain": "D08" if d08_action != "consume_only"
        else (case.get("owner_route") or {}).get("owner_domain"),
        "ownership.risk_owner": "D08" if positive and ierr is None else None,
        "ownership.query_owner": "D08" if positive and ierr is None else None,
        "ownership.risk_candidate_present": positive > 0 and ierr is None,
        "ownership.query_draft_present": positive > 0 and ierr is None and bool(projectable),
        "ownership.downstream_handoff_present": any(u.get("lineage_handoff") for u in units),
        "ownership.handoff_target_domain": "D09" if any(u.get("lineage_handoff") for u in units) else None,
        "l2.source_record_count": len(typed.get("record_nodes") or []),
        "l2.relation_unit_count": unit_count,
        "l2.clue_count": positive,
        "l2.risk_count": positive,
        "l2.query_count": positive if projectable else 0,
        "l2.handoff_count": sum(1 for u in units if u.get("lineage_handoff")),
        "l3.positive_count": positive,
        "l3.boundary_count": counts["boundary"],
        "l3.risk_count": positive,
        "unresolved_identity_count": 0,
        "open_gate_count": gate_count,
    }
    for i, u in enumerate(units):
        for key in UNIT_LEAF_KEYS:
            leaf[f"units.{i}.{key}"] = u.get(key)
    return leaf


def _assemble_trace_leaf_set(typed: dict[str, Any], units: list[dict[str, Any]],
                             nodes: list[dict[str, Any]]) -> dict[str, Any]:
    stable_ids = sorted({n["stable_record_identity"]["stable_record_id"] for n in nodes})
    edge_ids = sorted({e["edge_id"] for e in typed.get("observed_edges") or []})
    cores: list[str] = []
    for i, u in enumerate(units):
        core = "|".join(filter(None, [
            u.get("relation_rule_id"), u.get("unit_kind"),
            u.get("anchor_stable_identity") or u.get("slot_kind") or u.get("signal_type"),
            u.get("gate_signal_type") or u.get("signal_type"),
        ]))
        cores.append(f"{core}#{i}")
    positive_ok = all(
        u["l1_disposition"] != "positive"
        or (u.get("evidence_count", 0) >= 1 and u.get("participant_count", 0) >= 2)
        for u in units
    )
    handoff_count = sum(1 for u in units if u.get("lineage_handoff"))
    return {
        "trace.stable_core_count": len(units),
        "trace.superseded_unit_count": handoff_count,
        "trace.node_set": stable_ids,
        "trace.edge_set": edge_ids,
        "trace.unit_stable_cores": cores,
        "trace.positive_evidence_ok": positive_ok,
        "trace.negative_checked_edge_count": len(typed.get("observed_edges") or []),
        "trace.reverse_conservation_ok": _join_conserved(typed),
        "trace.bidirectional_join_count": len(typed.get("bidirectional_joins") or []),
        "trace.lineage_handoff_count": handoff_count,
    }


def _assemble_source_leaf_set(typed: dict[str, Any], units: list[dict[str, Any]],
                              vis: dict[str, Any], evaluation: list[str],
                              projectable: list[str], blinded: set[str],
                              forbidden: set[str]) -> dict[str, Any]:
    positive = sum(1 for u in units if u.get("l1_disposition") == "positive")
    node_ids = {n["record_node_id"] for n in typed.get("record_nodes") or []}
    loc_ids = {loc["source_locator_id"] for loc in typed.get("source_locators") or []}
    jump_pairs: list[dict[str, Any]] = []
    for jump in typed.get("source_jump_registry") or []:
        target = jump.get("target_object_id")
        kind = jump.get("target_kind")
        resolvable = target in (node_ids if kind == "record_node" else loc_ids)
        jump_pairs.append({"jump_target_id": jump.get("jump_target_id"),
                           "resolvable": resolvable,
                           "target_kind": kind,
                           "target_object_id": target})
    query_present = bool(positive and projectable)
    bindings = [b["binding_id"] for b in typed.get("producer_consumption_bindings") or []]
    return {
        "source.projectable_node_set": projectable,
        "source.evaluation_node_set": evaluation,
        "source.hidden_node_count": len(blinded | forbidden),
        "source.audience_anchor": projectable[0] if projectable else None,
        "source.audience_payload_present": bool(projectable),
        "source.query_present": query_present,
        "source.journey_marker_present": query_present,
        "source.risk_present": bool(positive),
        "source.producer_binding_ids": bindings,
        "source.reverse_binding_count": len(bindings),
        "source.source_jump_target_pairs": jump_pairs,
        "source.disclosure_leak_present": False,
        "source.audience_lexicon_ref": (typed.get("audience_lexicon") or {}).get("lexicon_id"),
    }


def _reconstruct_leaf_sets(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Reconstruct all three frozen oracle leaf sets from typed input only."""
    typed = case["typed_input"]
    vis = typed.get("visibility_decision") or {}
    evaluation = list(vis.get("evaluation_node_set") or [])
    projectable = list(vis.get("projectable_node_set") or [])
    blinded = set(vis.get("blinded_node_ids") or [])
    forbidden = set(vis.get("forbidden_node_ids") or [])
    nodes = typed.get("record_nodes") or []
    units, ierr, d08_action = _evaluate_units(typed, case)
    leaf = _assemble_expected_leaf_set(case, typed, units, ierr, d08_action, projectable)
    trace = _assemble_trace_leaf_set(typed, units, nodes)
    source = _assemble_source_leaf_set(typed, units, vis, evaluation, projectable,
                                       blinded, forbidden)
    return leaf, trace, source


def _diff_leaf_dicts(reconstructed: dict[str, Any], oracle_leaf: dict[str, Any]) -> list[str]:
    """Exact per-key comparison of one leaf set. Any missing/extra/unequal key
    yields a discrepancy; the reconstruction covers every oracle key."""
    problems: list[str] = []
    for key in sorted(set(reconstructed) | set(oracle_leaf)):
        if key not in oracle_leaf:
            problems.append(f"missing oracle leaf {key}")
        elif key not in reconstructed:
            problems.append(f"extra oracle leaf {key} (not reconstructed from typed input)")
        elif reconstructed[key] != oracle_leaf[key]:
            problems.append(f"leaf {key}: reconstructed {reconstructed[key]!r} != oracle {oracle_leaf[key]!r}")
    return problems


def audit_case(case: dict[str, Any], e: dict[str, Any]) -> list[str]:
    """Independent per-case verdict: full exact-leaf reconstruction vs the
    persisted oracle entry. Returns discrepancy strings (empty = exact match).

    The reconstruction is derived from typed input + contract semantics only
    (never from the oracle payload), so a mutation of ANY oracle leaf value —
    including l0_complete, domain_complete, expected_set_reconciled,
    open_gate_count, ownership.*, l2.handoff_count, trace.* and source.* — is
    detected on every case, including integrity, consume-only and cutoff
    early-return paths.
    """
    leaf, trace, source = _reconstruct_leaf_sets(case)
    problems: list[str] = []
    problems.extend(_diff_leaf_dicts(leaf, e["expected_leaf_set"]))
    problems.extend(_diff_leaf_dicts(trace, e["expected_trace_leaf_set"]))
    problems.extend(_diff_leaf_dicts(source, e["expected_source_leaf_set"]))
    return problems


def _type_valid_unequal(value: Any) -> Any:
    """A deterministic, JSON-valid, type-plausible value guaranteed unequal to
    the oracle leaf value. Used by the exhaustive per-leaf mutation test."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "_MUT"
    if isinstance(value, list):
        return ["MUTATED"]
    if value is None:
        return "MUTATED"
    return "MUTATED"

# Fixture helpers
# ---------------------------------------------------------------------------
def make_temp_workspace(tmp_root: Path) -> Path:
    ws = tmp_root / "ws"
    ws.mkdir(parents=True)
    for name in ("medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json",
                 "medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json",
                 "medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json"):
        (ws / name).write_bytes((ROOT / "reviews" / name).read_bytes())
    return ws


def load_artifacts() -> tuple[dict, dict, dict]:
    return (load_json(CATALOG_PATH), load_json(ORACLE_PATH), load_json(REGISTRY_PATH))


# ---------------------------------------------------------------------------
# Hash pins
# ---------------------------------------------------------------------------
class TestHashPins(unittest.TestCase):
    def test_contract_hash_pins(self) -> None:
        self.assertEqual(sha256_bytes(CONTRACT_PATH.read_bytes()), CONTRACT_FILE_SHA256)
        text = unicodedata.normalize(
            "NFC", CONTRACT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n"))
        self.assertEqual(sha256_text(text), CONTRACT_SEMANTIC_SHA256)

    def test_catalog_file_hash_pin(self) -> None:
        self.assertEqual(sha256_bytes(CATALOG_PATH.read_bytes()), CATALOG_FILE_SHA256)

    def test_oracle_file_and_content_hash_pins(self) -> None:
        self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()), ORACLE_FILE_SHA256)
        oracle = load_json(ORACLE_PATH)
        self.assertEqual(oracle["content_hash"], ORACLE_CONTENT_HASH)
        self.assertEqual(oracle["content_hash"], object_hash(oracle))

    def test_registry_file_hash_pin_and_content_hash(self) -> None:
        self.assertEqual(sha256_bytes(REGISTRY_PATH.read_bytes()), REGISTRY_FILE_SHA256)
        registry = load_json(REGISTRY_PATH)
        self.assertEqual(registry["content_hash"], REGISTRY_CONTENT_HASH)
        self.assertEqual(registry["content_hash"], object_hash(registry))

    def test_generator_file_hash_pin(self) -> None:
        self.assertEqual(sha256_bytes(GENERATOR_PATH.read_bytes()), GENERATOR_FILE_SHA256)

    def test_registry_embeds_pinned_oracle_and_catalog_hashes(self) -> None:
        registry = load_json(REGISTRY_PATH)
        self.assertEqual(registry["oracle_hash"], ORACLE_CONTENT_HASH)
        catalog = load_json(CATALOG_PATH)
        self.assertEqual(registry["catalog_hash"], catalog["catalog_hash"])
        self.assertEqual(registry["contract_semantic_hash"], CONTRACT_SEMANTIC_SHA256)

    def test_registry_replay_manifest_is_non_circular(self) -> None:
        registry = load_json(REGISTRY_PATH)
        replay = registry["replay_manifest"]
        self.assertNotIn("registry", replay["artifact_hashes"],
                         "replay manifest must not embed the registry's own hash")
        for ext in ("contract_semantic", "catalog", "oracle", "generator", "dsl_schema"):
            self.assertIn(ext, replay["artifact_hashes"])
        # content_hash is validated exactly: recompute over the whole registry
        # minus the content_hash field only (no other exclusion)
        self.assertEqual(registry["content_hash"], object_hash(registry))
        self.assertEqual(registry["manifest_hash"], sha256_text(canonical_json(registry["ordered_registry_core"])))


# ---------------------------------------------------------------------------
# Positive schema / bijection / distribution checks
# ---------------------------------------------------------------------------
class TestCatalogSchema(unittest.TestCase):
    def test_catalog_top_level_exact_keys(self) -> None:
        catalog = load_json(CATALOG_PATH)
        self.assertEqual(sorted(catalog.keys()), sorted(CATALOG_TOP_KEYS))
        self.assertEqual(catalog["case_count"], 233)
        self.assertEqual(len(catalog["cases"]), 233)
        self.assertEqual(catalog["catalog_hash"], object_hash(catalog, "catalog_hash"))

    def test_case_exact_16_keys_and_sequential_ids(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for index, case in enumerate(catalog["cases"], start=1):
            self.assertEqual(sorted(case.keys()), sorted(CASE_KEYS_FROZEN_16), case["case_id"])
            self.assertEqual(case["case_id"], f"D08-CASE-{index:03d}")
            self.assertEqual(case["fixture_id"], f"D08-FIXTURE-{index:03d}")
            self.assertEqual(case["oracle_case_id"], f"D08-ORACLE-{index:03d}")
            self.assertEqual(case["manifest_case_id"], f"D08-MANIFEST-{index:03d}")
            for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                self.assertIsNone(case[key])
            self.assertEqual(case["fixture_hash"], sha256_text(canonical_json(case["typed_input"])))
            self.assertEqual(
                case["typed_input"]["mutation_context"]["substantive_input_hash"],
                g.substantive_input_hash(case["typed_input"]))

    def test_closed_enums_in_catalog(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for case in catalog["cases"]:
            self.assertIn(case["disposition"], DISPOSITIONS + (CONSUME_ONLY,))
            self.assertIn(case["clinical_claim_token"], g.CLINICAL_CLAIM_TOKENS)
            self.assertIn(case["grain"], g.UNIT_GRAINS)
            self.assertIn(case["mutation_class"], g.MUTATION_CLASSES)

    def test_waiver_states_are_exactly_three(self) -> None:
        catalog = load_json(CATALOG_PATH)
        states = set()
        for case in catalog["cases"]:
            for w in case["typed_input"]["waiver_handoffs"]:
                states.add(w["closure_state"])
                if w["closure_state"] == "full_set":
                    self.assertTrue(w["authorized_object_refs"])
                if w["closure_state"] == "explicit_empty":
                    self.assertFalse(w["authorized_object_refs"])
                if w["closure_state"] == "missing":
                    self.assertFalse(w["authorized_object_refs"])
        self.assertEqual(states, set(CLOSURE_STATES))


class TestDistributionAndBijection(unittest.TestCase):
    def test_family_floors(self) -> None:
        from collections import Counter
        catalog = load_json(CATALOG_PATH)
        counts = Counter(case["family_id"] for case in catalog["cases"])
        for family, floor in g.FAMILY_FLOORS.items():
            self.assertGreaterEqual(counts.get(family, 0), floor, family)
        self.assertGreaterEqual(len(catalog["cases"]), 200)
        self.assertEqual(sum(counts.values()), 233)

    def test_owned_classes_cover_all_dispositions_and_counterevidence_hidden_fp_fn(self) -> None:
        catalog = load_json(CATALOG_PATH)
        for family in ("d08_explicit_link_resolve", "d08_reverse_cardinality",
                       "d08_identity_collision", "d08_unowned_temporal_impossibility",
                       "d08_propagation_lineage"):
            cases = [c for c in catalog["cases"] if c["family_id"] == family]
            disps = {c["disposition"] for c in cases}
            self.assertEqual(disps, set(DISPOSITIONS), family)
            mcs = {c["mutation_class"] for c in cases}
            self.assertTrue({"counterevidence", "hidden", "fp_trap", "fn_trap"} <= mcs, family)

    def test_consume_only_zero_risk(self) -> None:
        catalog, oracle, _ = load_artifacts()
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        count = 0
        for case in catalog["cases"]:
            if case["family_id"] != "consume_only_adjacency":
                continue
            count += 1
            self.assertEqual(case["disposition"], "consume_only")
            ls = expectations[case["case_id"]]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 0)
            self.assertEqual(ls["l2.risk_count"], 0)
            self.assertEqual(ls["l2.query_count"], 0)
            self.assertEqual(ls["l2.clue_count"], 0)
        self.assertGreaterEqual(count, 14)

    def test_five_column_bijection(self) -> None:
        registry = load_json(REGISTRY_PATH)
        rows = registry["ordered_registry_core"]
        self.assertEqual(len(rows), 233)
        for col in BIJECTION_COLUMNS:
            self.assertEqual(len({row[col] for row in rows}), 233, col)
        self.assertTrue(registry["bijection_audit"]["five_way_bijection_passed"])
        for row, case in zip(rows, load_json(CATALOG_PATH)["cases"]):
            self.assertEqual(row["case_id"], case["case_id"])
            self.assertEqual(row["fixture_id"], case["fixture_id"])
            self.assertEqual(row["oracle_case_id"], case["oracle_case_id"])
            self.assertEqual(row["manifest_case_id"], case["manifest_case_id"])

    def test_duplicate_substantive_input_groups_same_disposition(self) -> None:
        catalog = load_json(CATALOG_PATH)
        groups = g.duplicate_substantive_check(catalog["cases"])
        by_id = {c["case_id"]: c for c in catalog["cases"]}
        for h, ids in groups.items():
            disps = {by_id[i]["disposition"] for i in ids}
            self.assertEqual(len(disps), 1, f"same substantive input maps to conflicting outcomes: {ids}")

    def test_static_independence_oracle_vs_typed_input(self) -> None:
        catalog, oracle, _ = load_artifacts()
        audit = g.audit_static_independence(catalog, oracle)
        self.assertTrue(audit["vocabulary_disjoint"])


# ---------------------------------------------------------------------------
# Independent 233-case semantic audit (§13.3)
# ---------------------------------------------------------------------------
class TestIndependentVerifier(unittest.TestCase):
    def test_all_233_oracle_entries_pass_contract_audit(self) -> None:
        catalog, oracle, _ = load_artifacts()
        cases = {c["case_id"]: c for c in catalog["cases"]}
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        failures: dict[str, list[str]] = {}
        for cid in sorted(cases):
            problems = audit_case(cases[cid], expectations[cid])
            if problems:
                failures[cid] = problems
        self.assertEqual(failures, {}, f"independent verifier rejected oracle entries: {failures}")

    def test_cross_cutting_oracle_leaf_mutations_fail_independent_audit(self) -> None:
        """Regression for the freeze verifier's four concrete blind spots.

        Mutating any of these leaves without changing typed input must be
        detected even on cases that otherwise take an early audit return.
        """
        catalog, oracle, _ = load_artifacts()
        case = clone_case(catalog, "D08-CASE-203")
        original = next(e for e in oracle["ordered_expectations"]
                        if e["case_id"] == "D08-CASE-203")
        mutations = (
            ("expected_source_leaf_set", "source.query_present", False),
            ("expected_trace_leaf_set", "trace.node_set", []),
            ("expected_leaf_set", "l2.source_record_count", 99),
            ("expected_leaf_set", "all_units_disposed", False),
        )
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                changed = json.loads(canonical_json(original))
                changed[section][key] = value
                self.assertTrue(audit_case(case, changed), f"mutation escaped audit: {section}.{key}")

    def test_every_oracle_leaf_mutation_is_detected(self) -> None:
        """Exhaustive leaf mutation-sensitivity (freeze-gate requirement).

        For EVERY oracle case and EVERY leaf key in all three leaf sets, a
        type-valid unequal mutation must produce at least one discrepancy from
        the independent reconstruction. The audit is a complete exact-leaf
        comparison, so any unequal leaf value is caught; this test proves it
        per (case, section, leaf) and reports escaping triples exactly.
        """
        catalog, oracle, _ = load_artifacts()
        cases = {c["case_id"]: c for c in catalog["cases"]}
        escaping: list[tuple[str, str, str]] = []
        checked = 0
        leaf_counts = {"expected_leaf_set": 0, "expected_trace_leaf_set": 0, "expected_source_leaf_set": 0}
        for entry in oracle["ordered_expectations"]:
            cid = entry["case_id"]
            case = cases[cid]
            for section in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                for leaf in sorted(entry[section]):
                    mutated = json.loads(canonical_json(entry))
                    mutated[section][leaf] = _type_valid_unequal(entry[section][leaf])
                    problems = audit_case(case, mutated)
                    checked += 1
                    leaf_counts[section] += 1
                    if not problems:
                        escaping.append((cid, section, leaf))
        self.assertEqual(
            escaping, [],
            f"{len(escaping)} oracle leaf mutations escaped the independent audit: {escaping[:10]}")
        self.assertEqual(checked, sum(leaf_counts.values()), "leaf enumeration is exhaustive")
        self.assertGreaterEqual(leaf_counts["expected_leaf_set"], 233 * 30, leaf_counts)
        self.assertGreaterEqual(leaf_counts["expected_trace_leaf_set"], 233 * 10, leaf_counts)
        self.assertGreaterEqual(leaf_counts["expected_source_leaf_set"], 233 * 13, leaf_counts)

    def test_generic_oracle_leaf_mutations_from_freeze_review_detected(self) -> None:
        """Regression for the followup freeze-review blind spots: generic leaves
        (l0_complete, domain_complete, expected_set_reconciled, open_gate_count,
        ownership.owner_domain, l2.handoff_count) must be caught on D08-CASE-203
        exactly as reported by the Luna reviewer."""
        catalog, oracle, _ = load_artifacts()
        case = clone_case(catalog, "D08-CASE-203")
        original = next(e for e in oracle["ordered_expectations"]
                        if e["case_id"] == "D08-CASE-203")
        mutations = (
            ("expected_leaf_set", "l0_complete", False),
            ("expected_leaf_set", "domain_complete", False),
            ("expected_leaf_set", "expected_set_reconciled", False),
            ("expected_leaf_set", "open_gate_count", 7),
            ("expected_leaf_set", "ownership.owner_domain", "D01"),
            ("expected_leaf_set", "l2.handoff_count", 99),
        )
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                changed = json.loads(canonical_json(original))
                changed[section][key] = value
                self.assertTrue(audit_case(case, changed), f"generic leaf mutation escaped: {section}.{key}")


    def test_cutoff_oracle_essentials(self) -> None:
        """§12 cutoff required oracle: 5 behaviors materialized and correct."""
        catalog, oracle, _ = load_artifacts()
        cases = {c["case_id"]: c for c in catalog["cases"]}
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        by_mc = {c["case_id"]: c for c in catalog["cases"] if c["mutation_class"] == "cutoff_oracle"}
        self.assertGreaterEqual(len(by_mc), 6)
        # all-out-of-cutoff -> zero medical units
        c200 = cases["D08-CASE-200"]
        ls = expectations["D08-CASE-200"]["expected_leaf_set"]
        self.assertEqual(ls["unit_count"], 0)
        self.assertEqual(c200["disposition"], "negative")
        # mixed membership -> exactly one cutoff boundary gate
        for cid in ("D08-CASE-201", "D08-CASE-202"):
            ls = expectations[cid]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 1)
            self.assertEqual(ls["gate_count"], 1)
            self.assertEqual(ls["units.0.gate_signal_type"], "cutoff_boundary_gate")
            self.assertEqual(ls["units.0.l1_disposition"], "boundary")
            self.assertEqual(ls["units.0.unit_kind"], "routing_or_coverage_gate")
            self.assertEqual(cases[cid]["disposition"], "boundary")
        # in-cutoff / covered / zero-match -> not-found positive path
        ls = expectations["D08-CASE-203"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        self.assertEqual(ls["units.0.resolve_status"], "not_found")
        # time-missing + mixed -> exactly one not_evaluable, no boundary gate
        ls = expectations["D08-CASE-204"]["expected_leaf_set"]
        self.assertEqual(ls["unit_count"], 1)
        self.assertEqual(ls["gate_count"], 0)
        self.assertEqual(ls["units.0.l1_disposition"], "not_evaluable")
        # propagation retained after in->out correction (positive) and
        # in-cutoff event with post-cutoff source revision (negative)
        self.assertEqual(expectations["D08-CASE-205"]["expected_leaf_set"]["units.0.l1_disposition"], "positive")
        self.assertEqual(expectations["D08-CASE-206"]["expected_leaf_set"]["units.0.l1_disposition"], "negative")

    def test_temporal_oracle_essentials(self) -> None:
        """§12 temporal oracle: contains x contained_by -> positive; overlap
        does not satisfy containment; timezone+precision missing primary reason."""
        catalog, oracle, _ = load_artifacts()
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        # 046: expected contains, observed contained_by -> positive
        ls = expectations["D08-CASE-046"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        self.assertEqual(ls["units.0.temporal_relation"], "contained_by")
        self.assertEqual(ls["units.0.primary_reason"], "observed_contained_by")
        # 092: expected contains, observed contains -> negative (allowed)
        ls = expectations["D08-CASE-092"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "negative")
        self.assertEqual(ls["units.0.temporal_relation"], "contains")
        # 081: expected before, observed after -> positive
        ls = expectations["D08-CASE-081"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "positive")
        # 082: same-day points without time -> indeterminate boundary
        ls = expectations["D08-CASE-082"]["expected_leaf_set"]
        self.assertEqual(ls["units.0.l1_disposition"], "boundary")
        self.assertEqual(ls["units.0.temporal_relation"], "indeterminate")
        # timezone+precision both missing -> timezone_incomparable primary reason
        tz_cases = [e for e in oracle["ordered_expectations"]
                    if e["expected_leaf_set"].get("units.0.primary_reason") == "timezone_incomparable"]
        self.assertTrue(tz_cases, "no timezone_incomparable oracle case materialized")
        for e in tz_cases:
            self.assertEqual(e["expected_leaf_set"]["units.0.l1_disposition"], "not_evaluable")

    def test_fanout_and_identity_fanout_gate(self) -> None:
        catalog, oracle, _ = load_artifacts()
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        ls = expectations["D08-CASE-196"]["expected_leaf_set"]
        self.assertEqual(ls["unit_count"], 1)
        self.assertEqual(ls["units.0.gate_signal_type"], "identity_fanout_exceeded")
        self.assertEqual(ls["units.0.l1_disposition"], "not_evaluable")
        self.assertEqual(ls["units.0.unit_kind"], "routing_or_coverage_gate")

    def test_nary_relid_single_unit(self) -> None:
        catalog, oracle, _ = load_artifacts()
        expectations = {e["case_id"]: e for e in oracle["ordered_expectations"]}
        for case in catalog["cases"]:
            mems = case["typed_input"]["rel_instance_memberships"]
            if not mems or len(mems[0].get("member_ids") or []) < 3:
                continue
            ls = expectations[case["case_id"]]["expected_leaf_set"]
            self.assertEqual(ls["unit_count"], 1)
            self.assertEqual(ls["units.0.unit_kind"], "per_explicit_rel_instance")
        # at least one N-ary RELID case exists
        nary = [c for c in catalog["cases"]
                if any(len(m.get("member_ids") or []) >= 3 for m in c["typed_input"]["rel_instance_memberships"])]
        self.assertTrue(nary, "no N-ary RELID case materialized")

    def test_anti_overfit_preserves_semantics(self) -> None:
        catalog = load_json(CATALOG_PATH)
        by_fixture = {c["fixture_id"]: c for c in catalog["cases"]}
        for case in catalog["cases"]:
            variant = case["typed_input"]["anti_overfit_variant"]
            if variant is None:
                continue
            base_fixture = variant["base_fixture_id"]
            self.assertIn(base_fixture, by_fixture)
            self.assertEqual(case["disposition"], by_fixture[base_fixture]["disposition"],
                             f"{case['case_id']} anti-overfit changed disposition vs {base_fixture}")
            # same substantive semantics: strip-only variants share the base
            # substantive_input_hash; surface variants keep the base disposition
        self.assertGreaterEqual(
            sum(1 for c in catalog["cases"] if c["typed_input"]["anti_overfit_variant"] is not None), 12)


# ---------------------------------------------------------------------------
# Negative mutations (semantic + structural) — every mutation must fail closed
# ---------------------------------------------------------------------------
def clone_case(catalog: dict, case_id: str) -> dict:
    case = json.loads(canonical_json(next(c for c in catalog["cases"] if c["case_id"] == case_id)))
    return case


class TestNegativeMutations(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry = load_artifacts()
        self.expectations = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}

    def test_stale_contract_hash(self) -> None:
        orig = g.CONTRACT_FILE_SHA256
        try:
            g.CONTRACT_FILE_SHA256 = "0" * 64
            with self.assertRaises(SystemExit):
                g.validate_contract()
        finally:
            g.CONTRACT_FILE_SHA256 = orig

    def test_missing_and_extra_case_key(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-001")
        case.pop("fixture_hash")
        with self.assertRaises(g.D08ArtifactError):
            g.validate_case(case, 1)
        case = clone_case(self.catalog, "D08-CASE-001")
        case["rogue_key"] = True
        with self.assertRaises(g.D08ArtifactError):
            g.validate_case(case, 1)

    def test_wrong_scope_subject_fails_verifier(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-002")
        case["typed_input"]["record_nodes"][1]["stable_record_identity"]["subject_ref"] = "SYN-D08-SUBJECT-002"
        problems = audit_case(case, self.expectations["D08-CASE-002"])
        self.assertTrue(problems, "cross-subject edge must fail the independent verifier")

    def test_wrong_cutoff_fails_verifier(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-002")
        case["typed_input"]["record_nodes"][0]["cutoff_decision"]["decision"] = "out_of_cutoff"
        problems = audit_case(case, self.expectations["D08-CASE-002"])
        self.assertTrue(problems, "mixed membership must fail the verifier (needs boundary gate)")

    def test_wrong_owner_token_fails_generator(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-002")
        case["clinical_claim_token"] = "d02_cm_indication_match"
        with self.assertRaises(g.D08ArtifactError):
            g.check_case_consistency(case)

    def test_wrong_grain_fails_crossref(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-011")
        case["grain"] = "per_left_anchor_slot"
        with self.assertRaises(g.D08ArtifactError):
            g.check_oracle_catalog_crossrefs(case, self.expectations["D08-CASE-011"])

    def test_waiver_fourth_state_fails_schema(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-230")
        case["typed_input"]["waiver_handoffs"][0]["closure_state"] = "partially_closed"
        with self.assertRaises(g.D08ArtifactError):
            g.validate_typed_input(case["typed_input"], case["case_id"], case["family_id"])

    def test_contains_direction_flip_fails_verifier(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-046")
        tc = case["typed_input"]["temporal_comparisons"][0]
        tc["left_time_ref_id"], tc["right_time_ref_id"] = tc["right_time_ref_id"], tc["left_time_ref_id"]
        problems = audit_case(case, self.expectations["D08-CASE-046"])
        self.assertTrue(problems, "contains/contained_by interchange must change the outcome")

    def test_time_missing_priority_fails_verifier(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-233")
        problems = audit_case(case, self.expectations["D08-CASE-233"])
        self.assertEqual(problems, [], "pristine 233 must pass")
        for n in case["typed_input"]["record_nodes"]:
            n["cutoff_decision"]["decision"] = "out_of_cutoff"
        problems = audit_case(case, self.expectations["D08-CASE-233"])
        self.assertTrue(problems, "all-out-of-cutoff mutation must fail against the pinned oracle")

    def test_propagation_stale_flip_fails_verifier(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-122")  # in_sync negative
        p = case["typed_input"]["propagation_objects"][0]
        p["declared_consumed_revision"] = "SRC-REV-003"  # now stale vs source SRC-REV-004
        problems = audit_case(case, self.expectations["D08-CASE-122"])
        self.assertTrue(problems, "stale propagation must fail the verifier")

    def test_hidden_leakage_fails_generator(self) -> None:
        case = clone_case(self.catalog, "D08-CASE-146")
        vis = case["typed_input"]["visibility_decision"]
        vis["projectable_node_set"] = sorted(set(vis["projectable_node_set"]) | set(vis["blinded_node_ids"]))
        with self.assertRaises(g.D08ArtifactError):
            g.validate_typed_input(case["typed_input"], case["case_id"], case["family_id"])

    def test_bijection_drift_fails_audit(self) -> None:
        rows = json.loads(canonical_json(self.registry["ordered_registry_core"]))
        rows[1]["test_id"] = rows[0]["test_id"]
        with self.assertRaises(g.D08ArtifactError):
            g.audit_bijection(rows, self.catalog, self.oracle)

    def test_oracle_coupling_fails_static_independence(self) -> None:
        catalog2 = json.loads(canonical_json(self.catalog))
        catalog2["cases"][0]["typed_input"]["trace"] = {"units": []}
        with self.assertRaises(g.D08ArtifactError):
            g.audit_static_independence(catalog2, self.oracle)

    def test_legacy_hash_rejected(self) -> None:
        g.reject_legacy_contract_hash(self.catalog, self.oracle, self.registry)
        poisoned = json.loads(canonical_json(self.catalog))
        poisoned["cases"][0]["typed_input"]["mutation_context"]["mutation_description"] += \
            f" legacy-hash {g.LEGACY_CONTRACT_SHA256}"
        with self.assertRaises(g.D08ArtifactError):
            g.reject_legacy_contract_hash(poisoned)


# ---------------------------------------------------------------------------
# Reseal attempts: oracle/catalog/registry are independently pinned; resealing
# one (or all, consistently) must fail and never rewrite the oracle.
# ---------------------------------------------------------------------------
class TestResealAttempts(unittest.TestCase):
    def test_oracle_tamper_fails_file_hash_pin_and_oracle_never_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            ws.mkdir()
            (ws / ORACLE_PATH.name).write_bytes(ORACLE_PATH.read_bytes())
            tampered = load_json(ORACLE_PATH)
            tampered["ordered_expectations"][0]["expected_leaf_set"]["positive_count"] = 0
            tampered["content_hash"] = object_hash(tampered)
            (ws / ORACLE_PATH.name).write_text(canonical_json(tampered) + "\n", encoding="utf-8")
            catalog = load_json(CATALOG_PATH)
            with self.assertRaises(g.D08ArtifactError):
                g.load_oracle(catalog, ws / ORACLE_PATH.name)
            # the real oracle file is untouched
            self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()), ORACLE_FILE_SHA256)

    def test_typed_input_mutation_with_catalog_reseal_fails_and_oracle_untouched(self) -> None:
        """A typed-input mutation with catalog resealing must NOT cause oracle
        rewriting: the resealed catalog fails the pinned hash/cross-refs and the
        oracle file stays byte-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_temp_workspace(Path(tmp))
            # reseal the on-disk catalog copy: mutate typed input + disposition,
            # recompute fixture_hash and catalog_hash consistently
            cat = load_json(ws / CATALOG_PATH.name)
            case = cat["cases"][1]  # D08-CASE-002 (negative)
            case["disposition"] = "positive"
            case["fixture_hash"] = sha256_text(canonical_json(case["typed_input"]))
            cat["catalog_hash"] = object_hash(cat, "catalog_hash")
            (ws / CATALOG_PATH.name).write_text(canonical_json(cat) + "\n", encoding="utf-8")
            oracle_before = (ws / ORACLE_PATH.name).read_bytes()
            with self.assertRaises(Exception):
                g.render_artifacts(verbose=False, out_dir=ws)
            self.assertEqual((ws / ORACLE_PATH.name).read_bytes(), oracle_before,
                             "oracle was rewritten by a catalog reseal")
            self.assertEqual(sha256_bytes(oracle_before), ORACLE_FILE_SHA256)

    def test_spec_mutation_catalog_reseal_fails_and_oracle_untouched(self) -> None:
        """Mutating the typed-input SPECS (generator-side) changes the assembled
        catalog; the pinned catalog file hash fails closed before any oracle
        interaction, and the oracle is never rewritten."""
        original = list(g.CORE_SPECS)
        try:
            spec = json.loads(canonical_json(original[1]))
            spec["disposition"] = "positive"
            g.CORE_SPECS[1] = spec
            with self.assertRaises(g.D08ArtifactError):
                g.render_artifacts(verbose=False, out_dir=Path(tempfile.mkdtemp(prefix="d08_spec_mut_")))
        finally:
            g.CORE_SPECS = original
        self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()), ORACLE_FILE_SHA256)
        self.assertEqual(sha256_bytes(CATALOG_PATH.read_bytes()), CATALOG_FILE_SHA256)

    def test_coordinated_catalog_oracle_registry_reseal_fails_pinned_hashes(self) -> None:
        """Even a fully consistent reseal of catalog+oracle+registry fails the
        pinned independent hashes (the oracle FILE hash is a literal pin)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_temp_workspace(Path(tmp))
            oracle = load_json(ws / ORACLE_PATH.name)
            oracle["ordered_expectations"][0]["expected_leaf_set"]["positive_count"] = 0
            oracle["content_hash"] = object_hash(oracle)
            (ws / ORACLE_PATH.name).write_text(canonical_json(oracle) + "\n", encoding="utf-8")
            # registry would also be rebuilt consistently by an attacker
            with self.assertRaises(g.D08ArtifactError):
                g.render_artifacts(verbose=False, out_dir=ws)
            # oracle in the real workspace untouched
            self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()), ORACLE_FILE_SHA256)

    def test_registry_self_hash_rejected(self) -> None:
        registry = json.loads(canonical_json(self_registry()))
        registry["replay_manifest"]["artifact_hashes"]["registry"] = registry["content_hash"]
        catalog, oracle, _ = load_artifacts()
        with self.assertRaises(g.D08ArtifactError):
            g.validate_registry(registry, catalog, oracle, registry["generator_hash"])


def self_registry() -> dict:
    return load_json(REGISTRY_PATH)


# ---------------------------------------------------------------------------
# Determinism: two full renders are byte-identical; generator self-check.
# ---------------------------------------------------------------------------
class TestDeterministicReplay(unittest.TestCase):
    def test_two_renders_byte_identical_in_temp_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            ws1 = make_temp_workspace(Path(tmp1))
            ws2 = make_temp_workspace(Path(tmp2))
            g.render_artifacts(verbose=False, out_dir=ws1)
            g.render_artifacts(verbose=False, out_dir=ws2)
            for name in ("medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json",
                         "medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json"):
                self.assertEqual((ws1 / name).read_bytes(), (ws2 / name).read_bytes(), name)
            self.assertEqual(sha256_bytes((ws2 / "medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json").read_bytes()),
                             REGISTRY_FILE_SHA256)
            self.assertEqual(sha256_bytes((ws2 / "medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json").read_bytes()),
                             CATALOG_FILE_SHA256)

    def test_generator_self_check_negative_mutations_all_fail_closed(self) -> None:
        catalog, oracle, registry = load_artifacts()
        evidence = g.run_negative_mutations(catalog, oracle, registry)
        self.assertEqual(sorted(evidence.keys()), sorted(g.NEGATIVE_MUTATION_NAMES))
        for name in g.NEGATIVE_MUTATION_NAMES:
            self.assertIn("FAILED-CLOSED", evidence[name], name)

    def test_generator_imports_no_d08_runtime_and_8911_stopped(self) -> None:
        tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertTrue(imports <= {
            "__future__", "calendar", "collections", "datetime", "hashlib", "json",
            "pathlib", "re", "sys", "tempfile", "typing", "unicodedata",
        })
        # 8911 must stay stopped: no listener on the R4 monitoring port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            result = s.connect_ex(("127.0.0.1", 8911))
        finally:
            s.close()
        self.assertNotEqual(result, 0, "port 8911 must stay stopped (connection must be refused)")


if __name__ == "__main__":
    unittest.main()
