"""R5-S4 Risk Inspector runtime validator (synthetic, offline, fail-closed).

This module is the third half of the renderer-neutral runtime thin slice.  It
implements the single public entry
:func:`validate_s4_authority_packet`, which accepts an untrusted candidate
``Mapping`` (or a typed :class:`mm_r5.s4_contracts.R5S4AuthorityPacket`) and a
typed runtime input, and rejects any drift with one stable ``s4.*`` code.

Design contract (accepted runtime contract section 3.4 / 9 / 10):

* The candidate never proves itself.  The validator independently rebuilds the
  expected packet from the runtime input (real builder + projection:
  ``build_s4_authority_packet(runtime_input)``) and compares the candidate to
  that rebuilt expected packet.  A candidate that re-signs its own hashes
  consistently is still rejected whenever any leaf drifts from the rebuilt
  expected packet.
* Structural/type/exact-key checks precede ordering, arithmetic, dataclass
  construction and semantic joins.  The candidate ``Mapping`` is validated
  RECURSIVELY (every nested plane: risk identity, worker views, raw
  artifacts, baseline items/rows, verification/conflict rows, adjudication,
  Query, Journey, history entries, audience and audit inspectors and their
  sub-objects) before any semantic access or dataclass construction.  Unknown
  keys, missing keys, scalar-instead-of-object, bool-as-int and wrong
  list/object/nullability are stable ``s4.schema_key_mismatch`` issues (or
  the frozen audience-plane codes) and never leak ``AttributeError``,
  ``TypeError`` or another raw exception.
* After the specific-code precedence chain, every remaining candidate leaf is
  compared against the independently rebuilt expected packet; any drift not
  assigned a more specific accepted rule fails with the accepted generic
  cross-plane code.  The six hash-DAG nodes, packet identity and integrity
  leaves, receipt content hash and audit fingerprints are explicitly
  recomputed from the candidate's own content so a hash leaf cannot be forged.
* Every issue is fail-closed and deterministic.  Because each accepted
  registry mutation isolates exactly one contract rule, the validator returns
  exactly one issue (the single-code registry precedence): checks run in a
  fixed priority order and the first violation wins.  ``expected_packet`` is
  ``None`` only when the candidate structure cannot be parsed safely;
  otherwise it is the rebuilt expected packet.
* R4/dataclass/trusted-source failures surface as
  :class:`mm_r5.s4_contracts.S4RuntimeImplementationError`, never as a packet
  rejection.  A runtime input the builder rejects is an implementation error
  (distinct from a candidate rejection).

The validator never opens a file, never imports or reads the machine
artifacts/generator/verifier/registry, and never branches on challenge case
ids, indices, mutations, filenames or test locators.
"""

from __future__ import annotations

import base64
import collections.abc
import dataclasses
import hashlib
import re
from typing import Any, Dict, Mapping, Optional, Tuple, Union, get_args, \
    get_origin, get_type_hints

from mm_r5 import s4_contracts as s4
from mm_r5.s4_projection import build_s4_authority_packet

__all__ = ["validate_s4_authority_packet"]

#: Evidence locator template regex (``来源 <locator> 已定位``).  Used only to
#: detect an unauthorized (hidden) source locator leaking into the audience
#: support/counter evidence planes.
_EVIDENCE_LOCATOR_RE = re.compile(r"来源 (.+?) 已定位")

#: The six hash-DAG / identity leaves recomputed in the dedicated hash section
#: (excluded from the generic full-leaf compare so a changed hash leaf gets its
#: specific accepted code).
_HASH_LEAVES = frozenset({
    "audience_content_hash", "audit_content_hash", "receipt_content_hash",
    "packet_id", "packet_integrity_hash",
})


def _issue(code: str, path: str) -> s4.R5S4ValidationIssue:
    """Build one stable issue (``message_zh`` auto-fills the frozen formula
    ``核对未通过：{path}（{code}）``)."""
    return s4.R5S4ValidationIssue(code=code, path=path, message_zh="")


def _result(ok: bool, issues: Tuple[s4.R5S4ValidationIssue, ...],
            expected_packet: Optional[s4.R5S4AuthorityPacket],
            ) -> s4.R5S4ValidationResult:
    return s4.R5S4ValidationResult(ok=ok, issues=issues,
                                   expected_packet=expected_packet)


def _candidate_mapping(
    candidate: Mapping[str, object] | s4.R5S4AuthorityPacket,
) -> Dict[str, Any]:
    """Normalize the candidate to a plain mapping without trusting any leaf.

    A typed packet is converted with the canonical ``packet_as_mapping``; a
    ``Mapping`` is copied so a caller's dict is never mutated.  Anything else
    is an implementation misuse (not a packet rejection).
    """
    if isinstance(candidate, s4.R5S4AuthorityPacket):
        return s4.packet_as_mapping(candidate)
    if isinstance(candidate, Mapping):
        return dict(candidate)
    raise s4.S4RuntimeImplementationError(
        "validate_s4_authority_packet candidate must be a Mapping or an "
        f"R5S4AuthorityPacket, got {type(candidate).__name__}")


# ---------------------------------------------------------------------------
# Recursive structural specification (exact keys + primitive/container types)
# ---------------------------------------------------------------------------
#
# A spec mirrors the frozen dataclass field graph: every object field is
# ('object', cls), every many-field ('list', item_spec) / ('map', value_spec),
# every Optional ('opt', inner_spec) and every scalar ('scalar', base).  The
# validator walks the candidate against this spec so no malformed nested plane
# ever reaches a semantic check (which would otherwise leak AttributeError /
# TypeError).

_SPEC_CACHE: Dict[type, Dict[str, Any]] = {}


def _type_spec(annotation: Any) -> Any:
    """One structural spec node from a typed dataclass field annotation."""
    origin = get_origin(annotation)
    if origin is Union:  # Optional[X]
        args = get_args(annotation)
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) != 1:
            raise s4.S4RuntimeImplementationError(
                f"unexpected Union annotation {annotation!r} in S4 schema")
        return ("opt", _type_spec(non_none[0]))
    if origin in (tuple, list):
        args = get_args(annotation)
        if not args:
            raise s4.S4RuntimeImplementationError(
                f"untyped container annotation {annotation!r} in S4 schema")
        return ("list", _type_spec(args[0]))
    if origin is dict or (
            isinstance(origin, type)
            and issubclass(origin, collections.abc.Mapping)):
        args = get_args(annotation)
        value_spec = _type_spec(args[1]) if args and len(args) == 2 \
            else ("scalar", str)
        return ("map", value_spec)
    if isinstance(annotation, type) \
            and dataclasses.is_dataclass(annotation) \
            and not isinstance(annotation, type(None)):
        return ("object", annotation)
    if annotation is str:
        return ("scalar", str)
    if annotation is int:
        return ("scalar", int)
    if annotation is bool:
        return ("scalar", bool)
    raise s4.S4RuntimeImplementationError(
        f"unsupported S4 schema annotation {annotation!r}")


def _dataclass_spec(cls: type) -> Dict[str, Any]:
    """The exact field spec of one frozen S4 dataclass (cached)."""
    if cls in _SPEC_CACHE:
        return _SPEC_CACHE[cls]
    hints = get_type_hints(cls)
    spec = {name: _type_spec(annotation)
            for name, annotation in hints.items()}
    _SPEC_CACHE[cls] = spec
    return spec


def _check_value(spec: Any, value: Any, path: str) -> Optional[
        s4.R5S4ValidationIssue]:
    """Type-check one value against a structural spec node.  Returns the first
    schema_key_mismatch issue or ``None``.  Never raises on a bad value."""
    kind = spec[0]
    if kind == "opt":
        if value is None:
            return None
        return _check_value(spec[1], value, path)
    if kind == "scalar":
        base = spec[1]
        if base is str:
            ok = isinstance(value, str)
        elif base is int:
            ok = isinstance(value, int) and not isinstance(value, bool)
        elif base is bool:
            ok = isinstance(value, bool)
        else:
            ok = True
        return None if ok else _issue("s4.schema_key_mismatch", path)
    if kind == "list":
        if not isinstance(value, list):
            return _issue("s4.schema_key_mismatch", path)
        for index, item in enumerate(value):
            issue = _check_value(spec[1], item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    if kind == "map":
        if not isinstance(value, dict):
            return _issue("s4.schema_key_mismatch", path)
        for key, val in value.items():
            if not isinstance(key, str):
                return _issue("s4.schema_key_mismatch", f"{path}.<key>")
            issue = _check_value(spec[1], val, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if kind == "object":
        if not isinstance(value, dict):
            return _issue("s4.schema_key_mismatch", path)
        return _check_object(value, _dataclass_spec(spec[1]), path)
    return None


def _check_object(
    value: Dict[str, Any], spec: Dict[str, Any], path: str,
) -> Optional[s4.R5S4ValidationIssue]:
    """Exact-key + per-field type check of one plain-dict object against a
    dataclass field spec.  Unknown and missing keys are schema_key_mismatch;
    wrong types are schema_key_mismatch."""
    for key in value:
        if key not in spec:
            return _issue("s4.schema_key_mismatch", f"{path}.{key}")
    for name, sub in spec.items():
        if name not in value:
            return _issue("s4.schema_key_mismatch", f"{path}.{name}")
        issue = _check_value(sub, value[name], f"{path}.{name}")
        if issue is not None:
            return issue
    return None


def _recursive_structure_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Recursive exact-key / primitive / container validation of every nested
    candidate plane EXCEPT the audience inspector, whose unknown-key handling
    carries the frozen audience-specific codes and is therefore deferred to
    ``_audience_issue``.  Returns the first structural issue or ``None``.

    A structural failure means the candidate cannot be parsed safely, so the
    caller returns ``expected_packet=None``.
    """
    root_spec = _dataclass_spec(s4.R5S4AuthorityPacket)
    for key in cand:
        if key not in root_spec:
            return _issue("s4.schema_key_mismatch", f"packet.{key}")
    for name, sub in root_spec.items():
        if name not in cand:
            return _issue("s4.schema_key_mismatch", f"packet.{name}")
        if name == "audience_inspector":
            # root-level container type only; internals deferred (audience
            # unknown keys carry specific codes).
            if not isinstance(cand[name], dict):
                return _issue("s4.schema_key_mismatch", f"packet.{name}")
            continue
        issue = _check_value(sub, cand[name], f"packet.{name}")
        if issue is not None:
            return issue
    return None


# ---------------------------------------------------------------------------
# Frozen packet identity
# ---------------------------------------------------------------------------


def _root_meta_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Frozen packet identity leaves (schema/status/mode/anchor ref)."""
    for key, code in (("schema", "s4.schema_key_mismatch"),
                      ("status", "s4.schema_key_mismatch"),
                      ("authority_mode", "s4.schema_key_mismatch")):
        if cand.get(key) != exp.get(key):
            return _issue(code, f"packet.{key}")
    if cand.get("authority_anchor_ref") != exp.get("authority_anchor_ref"):
        return _issue("s4.anchor_claim_drift", "packet.authority_anchor_ref")
    if cand.get("anchor_identity_hash") != exp.get("anchor_identity_hash"):
        return _issue("s4.anchor_claim_drift", "packet.anchor_identity_hash")
    return None


# ---------------------------------------------------------------------------
# 0 / 1 / N ensemble cardinality and identity isolation
# ---------------------------------------------------------------------------


def _cardinality_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """0/1/N tagged union across the root planes.

    ``ensemble_size`` must equal the rebuilt worker count (C-001/C-005);
    ``baseline_items`` must carry the accepted item set cardinality (C-006);
    a non-zero ensemble requires a non-null shared ``input_content_hash``
    (C-014); for a non-zero ensemble the worker / raw / verification lists
    must each carry exactly ``ensemble_size`` members (schema exact_count).
    """
    if cand.get("ensemble_size") != exp.get("ensemble_size"):
        return _issue("s4.cardinality_not_0_1_n", "packet.ensemble_size")
    if cand.get("ensemble_projection_state") != exp.get(
            "ensemble_projection_state"):
        return _issue("s4.cardinality_not_0_1_n",
                      "packet.ensemble_projection_state")
    cand_items = cand.get("baseline_items", [])
    exp_items = exp.get("baseline_items", [])
    if len(cand_items) != len(exp_items):
        return _issue("s4.cardinality_not_0_1_n", "packet.baseline_items")
    cand_ids = [item.get("item_id") for item in cand_items]
    exp_ids = [item.get("item_id") for item in exp_items]
    if cand_ids != exp_ids:
        return _issue("s4.cardinality_not_0_1_n", "packet.baseline_items")
    state = cand.get("ensemble_projection_state")
    if state != "no_ensemble":
        if cand.get("input_content_hash") is None:
            return _issue("s4.cardinality_not_0_1_n",
                          "packet.input_content_hash")
        size = cand.get("ensemble_size")
        for field in ("worker_views", "raw_artifacts", "verification_rows"):
            if len(cand.get(field, [])) != size:
                return _issue("s4.cardinality_not_0_1_n", f"packet.{field}")
    return None


def _no_ensemble_empty_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """no_ensemble forbids any residue across every plane (C-007/C-008)."""
    if cand.get("ensemble_projection_state") != "no_ensemble":
        return None
    if cand.get("raw_artifacts"):
        return _issue("s4.ensemble_zero_must_be_empty", "packet.raw_artifacts")
    if cand.get("worker_views") or cand.get("verification_rows") \
            or cand.get("conflict_rows"):
        return _issue("s4.ensemble_zero_must_be_empty",
                      "packet.worker_views")
    audit = cand.get("audit_inspector", {})
    if audit.get("model_evidence") is not None:
        return _issue("s4.ensemble_zero_must_be_empty",
                      "packet.audit_inspector.model_evidence")
    if audit.get("worker_audit_rows") or audit.get("verification_audit_rows"):
        return _issue("s4.ensemble_zero_must_be_empty",
                      "packet.audit_inspector.worker_audit_rows")
    adj = cand.get("adjudication_row", {})
    if adj.get("present") or adj.get("binding_id") \
            or adj.get("independent_context_hash") is not None:
        return _issue("s4.ensemble_zero_must_be_empty",
                      "packet.adjudication_row")
    if cand.get("query_draft_row") is not None:
        return _issue("s4.ensemble_zero_must_be_empty",
                      "packet.query_draft_row")
    return None


def _worker_uniqueness_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Per-attempt identity isolation (binding/session/context unique) for
    N>=2 (C-010/C-011/C-012)."""
    workers = cand.get("worker_views", [])
    if len(workers) < 2:
        return None
    if len({w.get("binding_id") for w in workers}) != len(workers):
        return _issue("s4.duplicate_worker_binding", "packet.worker_views")
    if len({w.get("session_id") for w in workers}) != len(workers):
        return _issue("s4.duplicate_worker_session", "packet.worker_views")
    if len({w.get("independent_context_hash") for w in workers}) != len(workers):
        return _issue("s4.duplicate_worker_context", "packet.worker_views")
    return None


def _input_authority_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Shared input identity isolation (C-013): the root input content hash
    and every worker's declared input hash must equal the rebuilt value."""
    if cand.get("input_content_hash") != exp.get("input_content_hash"):
        return _issue("s4.authority_drift", "packet.input_content_hash")
    exp_workers = {w.get("attempt_id"): w for w in exp.get("worker_views", [])}
    for w in cand.get("worker_views", []):
        expected = exp_workers.get(w.get("attempt_id"))
        if expected is not None \
                and w.get("input_content_hash") != expected.get(
                    "input_content_hash"):
            return _issue("s4.authority_drift",
                          "packet.worker_views[].input_content_hash")
    return None


# ---------------------------------------------------------------------------
# Audit-plane bound objects (model evidence / raw / adjudicator /
# verification)
# ---------------------------------------------------------------------------


def _model_evidence_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """D10 ModelEvidence must equal the accepted permit projection (18 bound
    fields; C-002/C-003/C-055/C-056)."""
    cand_me = cand.get("audit_inspector", {}).get("model_evidence")
    exp_me = exp.get("audit_inspector", {}).get("model_evidence")
    if cand_me == exp_me:
        return None
    if isinstance(cand_me, dict) and isinstance(exp_me, dict):
        for key in exp_me:
            if cand_me.get(key) != exp_me.get(key):
                return _issue("s4.model_evidence_not_permitted",
                              f"packet.audit_inspector.model_evidence.{key}")
    return _issue("s4.model_evidence_not_permitted",
                  "packet.audit_inspector.model_evidence")


def _raw_artifact_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Raw/parsed hash strict separation per artifact (C-018/C-019/C-020/
    C-022/C-023).  Raw bytes are never trusted: the sha256 is recomputed and
    the parsed hash is recomputed before a declared value is accepted."""
    exp_by_aid = {a.get("artifact_id"): a for a in exp.get("raw_artifacts", [])}
    for idx, artifact in enumerate(cand.get("raw_artifacts", [])):
        expected = exp_by_aid.get(artifact.get("artifact_id"))
        path = f"packet.raw_artifacts[{idx}]"
        if expected is None:
            return _issue("s4.raw_output_rewritten", path)
        if artifact.get("raw_format") != expected.get("raw_format"):
            return _issue("s4.enum_value_mismatch", f"{path}.raw_format")
        if artifact.get("raw_bytes_sha256") != expected.get("raw_bytes_sha256"):
            return _issue("s4.raw_sha_external_mismatch",
                          f"{path}.raw_bytes_sha256")
        try:
            raw_bytes = base64.b64decode(artifact.get("raw_bytes_b64", ""),
                                         validate=True)
        except Exception:
            return _issue("s4.raw_output_rewritten", f"{path}.raw_bytes_b64")
        if artifact.get("raw_bytes_sha256") != hashlib.sha256(
                raw_bytes).hexdigest():
            return _issue("s4.raw_output_rewritten", f"{path}.raw_bytes_b64")
        if artifact.get("parsed_output_hash") != expected.get(
                "parsed_output_hash"):
            return _issue("s4.anchor_claim_drift", f"{path}.parsed_output_hash")
        if artifact.get("declared_output_hash") != expected.get(
                "declared_output_hash"):
            return _issue("s4.parsed_output_hash_mismatch",
                          f"{path}.declared_output_hash")
    return None


def _adjudicator_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Adjudicator independence (C-052/C-053/C-054/C-057)."""
    cand_adj = cand.get("adjudication_row", {})
    exp_adj = exp.get("adjudication_row", {})
    if not cand_adj.get("present"):
        return None
    workers = cand.get("worker_views", [])
    worker_bindings = {w.get("binding_id") for w in workers}
    worker_sessions = {w.get("session_id") for w in workers}
    worker_contexts = {w.get("independent_context_hash") for w in workers}
    if cand_adj.get("binding_id") in worker_bindings:
        return _issue("s4.worker_self_adjudication",
                      "packet.adjudication_row.binding_id")
    if cand_adj.get("session_id") in worker_sessions:
        return _issue("s4.worker_self_adjudication",
                      "packet.adjudication_row.session_id")
    if cand_adj.get("independent_context_hash") in worker_contexts:
        return _issue("s4.adjudicator_context_collision",
                      "packet.adjudication_row.independent_context_hash")
    if cand_adj.get("model_id") != exp_adj.get("model_id"):
        return _issue("s4.anchor_claim_drift", "packet.adjudication_row.model_id")
    return None


def _verification_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Verification rows must be the exact recompute trace and the audit
    digest context must match (C-034..C-040).  ``recomputed`` is a frozen
    True leaf -> ``schema_key_mismatch`` when false (C-039)."""
    exp_by_aid = {v.get("attempt_id"): v
                  for v in exp.get("verification_rows", [])}
    for idx, row in enumerate(cand.get("verification_rows", [])):
        expected = exp_by_aid.get(row.get("attempt_id"))
        path = f"packet.verification_rows[{idx}]"
        if expected is None:
            return _issue("s4.verification_label_only", path)
        if row.get("recomputed") is not True:
            return _issue("s4.schema_key_mismatch", f"{path}.recomputed")
        for key in ("verification_id", "checked_dimensions", "result",
                    "failure_reason_codes"):
            if row.get(key) != expected.get(key):
                return _issue("s4.verification_label_only", f"{path}.{key}")
    cand_digest = cand.get("audit_inspector", {}).get("digest_context")
    exp_digest = exp.get("audit_inspector", {}).get("digest_context")
    if cand_digest != exp_digest:
        return _issue("s4.verification_label_only",
                      "packet.audit_inspector.digest_context")
    return None


def _verification_adjudication_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """A failed/not-evaluable authority blocks any supporting adjudication
    outcome (C-041)."""
    failed = any(
        row.get("result") in ("failed", "not_evaluable")
        for row in cand.get("verification_rows", []))
    if not failed:
        return None
    outcome = cand.get("adjudication_row", {}).get("outcome")
    if outcome in s4.SUPPORTING_OUTCOMES:
        return _issue("s4.verification_unresolved_authority",
                      "packet.adjudication_row.outcome")
    return None


# ---------------------------------------------------------------------------
# Conflict rows (hideability then full-set completeness)
# ---------------------------------------------------------------------------


def _conflict_hideability_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Non-hideable / high / single-addition / mutual-negation conflicts must
    stay visible (C-031/C-042/C-043/C-044)."""
    exp_by_id = {c.get("conflict_id"): c for c in exp.get("conflict_rows", [])}
    state = cand.get("ensemble_projection_state")
    for idx, row in enumerate(cand.get("conflict_rows", [])):
        expected = exp_by_id.get(row.get("conflict_id"))
        if expected is None:
            continue
        if row.get("hidden") == expected.get("hidden"):
            continue
        path = f"packet.conflict_rows[{idx}].hidden"
        if not row.get("hidden"):
            continue
        relation = row.get("relation")
        if relation == "baseline_miss":
            return _issue("s4.baseline_miss_hidden", path)
        if relation == "mutual_negation":
            return _issue("s4.mutual_negation_hidden", path)
        if relation == "single_model_new" and state == "single_analysis":
            return _issue("s4.single_addition_omitted", path)
        return _issue("s4.high_risk_hidden", path)
    return None


def _conflict_set_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """The full derived conflict set must equal the packet set exactly; any
    add/remove/leaf change is incomplete (C-045..C-051)."""
    if cand.get("conflict_rows") != exp.get("conflict_rows"):
        return _issue("s4.conflict_set_incomplete", "packet.conflict_rows")
    return None


# ---------------------------------------------------------------------------
# Baseline (recheck then projection)
# ---------------------------------------------------------------------------


def _baseline_recheck_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """confirmed/unsupported rows must be rechecked against the authorized
    source (C-030)."""
    for idx, row in enumerate(cand.get("baseline_rows", [])):
        if row.get("state") in s4.RECHECK_REQUIRED_STATES \
                and not row.get("source_recheck_locator_ids"):
            return _issue("s4.baseline_recheck_missing",
                          f"packet.baseline_rows[{idx}].recheck_complete")
        if row.get("recheck_complete") is False \
                and row.get("state") in s4.RECHECK_REQUIRED_STATES:
            return _issue("s4.baseline_recheck_missing",
                          f"packet.baseline_rows[{idx}].recheck_complete")
    return None


def _baseline_projection_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Every baseline row / baseline item leaf must equal the rebuilt
    projection (C-024..C-029, C-033)."""
    if cand.get("baseline_rows") != exp.get("baseline_rows"):
        return _issue("s4.baseline_projection_drift", "packet.baseline_rows")
    if cand.get("baseline_items") != exp.get("baseline_items"):
        return _issue("s4.baseline_projection_drift", "packet.baseline_items")
    return None


# ---------------------------------------------------------------------------
# History (append-only then chain)
# ---------------------------------------------------------------------------


def _history_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Append-only accepted history: head identity then contiguous chain
    (C-072..C-077)."""
    cand_log = cand.get("history_log", {})
    exp_log = exp.get("history_log", {})
    if cand_log.get("head_seq") != exp_log.get("head_seq"):
        return _issue("s4.history_append_only_violation",
                      "packet.history_log.head_seq")
    if cand_log.get("head_hash") != exp_log.get("head_hash"):
        return _issue("s4.history_append_only_violation",
                      "packet.history_log.head_hash")
    cand_entries = cand_log.get("entries", [])
    exp_entries = exp_log.get("entries", [])
    if len(cand_entries) != len(exp_entries):
        return _issue("s4.history_chain_break", "packet.history_log.entries")
    for idx, entry in enumerate(cand_entries):
        expected = exp_entries[idx]
        path = f"packet.history_log.entries[{idx}]"
        for key in ("entry_id", "seq", "kind", "payload_ref",
                    "prior_entry_hash", "entry_hash"):
            if entry.get(key) != expected.get(key):
                return _issue("s4.history_chain_break", f"{path}.{key}")
    return None


# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


def _journey_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Journey deep-link identity (fallback_policy=none; never nearest
    fallback; C-078..C-081)."""
    cand_j = cand.get("journey_link", {})
    exp_j = exp.get("journey_link", {})
    if cand_j.get("fallback_policy") != "none":
        return _issue("s4.journey_fallback_not_none",
                      "packet.journey_link.fallback_policy")
    for key in exp_j:
        if key in ("fallback_policy", "journey_available",
                   "unavailable_reason_zh"):
            continue
        if cand_j.get(key) != exp_j.get(key):
            return _issue("s4.anchor_claim_drift", f"packet.journey_link.{key}")
    return None


# ---------------------------------------------------------------------------
# Risk identity anchor claim
# ---------------------------------------------------------------------------


def _anchor_claim_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """The root risk identity must equal the accepted external identity
    (C-016/C-017/C-021)."""
    cand_rid = cand.get("risk_identity", {})
    exp_rid = exp.get("risk_identity", {})
    for key in exp_rid:
        if cand_rid.get(key) != exp_rid.get(key):
            return _issue("s4.anchor_claim_drift",
                          f"packet.risk_identity.{key}")
    return None


# ---------------------------------------------------------------------------
# Query projection
# ---------------------------------------------------------------------------


def _query_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Three-part draft-only Query identity (C-066..C-071)."""
    cand_row = cand.get("query_draft_row")
    exp_row = exp.get("query_draft_row")
    if cand_row == exp_row:
        return None
    if isinstance(cand_row, dict) and isinstance(exp_row, dict):
        for key in exp_row:
            if cand_row.get(key) != exp_row.get(key):
                return _issue("s4.query_projection_drift",
                              f"packet.query_draft_row.{key}")
    return _issue("s4.query_projection_drift", "packet.query_draft_row")


# ---------------------------------------------------------------------------
# Audience plane (structure -> forbidden -> nearest -> hidden -> consensus ->
# query -> baseline_zh -> generic drift)
# ---------------------------------------------------------------------------


def _audience_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
    journey_link: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """The plain-Chinese audience plane with the frozen precedence:
    structural/type (schema_key_mismatch) and the audit-only-leaf /
    model-evidence-on-audience codes (C-082..C-084, C-088) -> forbidden token
    (C-085..C-087) -> nearest fallback (C-062/C-064/C-065) -> hidden source
    leak (C-058/C-060) -> consensus special (C-004/C-009) -> query
    (C-066..C-069) -> baseline_zh (C-032) -> generic cross-plane drift
    (C-059/C-061/C-089)."""
    cand_aud = cand.get("audience_inspector", {})
    exp_aud = exp.get("audience_inspector", {})
    if not isinstance(cand_aud, dict):
        return _issue("s4.schema_key_mismatch", "packet.audience_inspector")
    aud_spec = _dataclass_spec(s4.R5S4AudienceInspector)

    # 1) unknown keys -> the frozen audience-specific codes.
    for key in cand_aud:
        if key not in aud_spec:
            if key == "model_evidence":
                return _issue("s4.model_evidence_on_audience",
                              "packet.audience_inspector.model_evidence")
            if key in s4.AUDIT_ONLY_LEAVES:
                return _issue("s4.audience_hash_contains_audit_leaf",
                              f"packet.audience_inspector.{key}")
            return _issue("s4.schema_key_mismatch",
                          f"packet.audience_inspector.{key}")
    # 2) missing keys + known-key exact type (recursive structural).
    for name, sub in aud_spec.items():
        if name not in cand_aud:
            return _issue("s4.schema_key_mismatch",
                          f"packet.audience_inspector.{name}")
        issue = _check_value(sub, cand_aud[name],
                             f"packet.audience_inspector.{name}")
        if issue is not None:
            return issue

    # text leaves to scan for forbidden / nearest-fallback tokens.
    text_paths = [(f"packet.audience_inspector.{key}", cand_aud.get(key))
                  for key in exp_aud
                  if isinstance(cand_aud.get(key), str)]
    if isinstance(journey_link.get("unavailable_reason_zh"), str):
        text_paths.append(("packet.journey_link.unavailable_reason_zh",
                           journey_link.get("unavailable_reason_zh")))

    # 3) forbidden audience tokens.
    for path, value in text_paths:
        if any(token in value for token in s4.FORBIDDEN_AUDIENCE_TOKENS):
            return _issue("s4.audience_audit_leak", path)
    for key in ("support_evidence_zh", "counterevidence_zh"):
        items = cand_aud.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str) and any(
                        token in item for token in s4.FORBIDDEN_AUDIENCE_TOKENS):
                    return _issue("s4.audience_audit_leak",
                                  f"packet.audience_inspector.{key}")

    # 4) nearest-fallback wording.
    for path, value in text_paths:
        if any(token in value for token in s4.NEAREST_FALLBACK_TOKENS):
            return _issue("s4.nearest_fallback_forbidden", path)
    for key in ("support_evidence_zh", "counterevidence_zh"):
        items = cand_aud.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str) and any(
                        token in item for token in s4.NEAREST_FALLBACK_TOKENS):
                    return _issue("s4.nearest_fallback_forbidden",
                                  f"packet.audience_inspector.{key}")

    # 5) hidden (unauthorized) source locator on the evidence planes.
    authorized = _located_locators(exp_aud)
    for key in ("support_evidence_zh", "counterevidence_zh"):
        for item in cand_aud.get(key) or []:
            match = _EVIDENCE_LOCATOR_RE.search(str(item))
            if match and match.group(1) not in authorized:
                return _issue("s4.hidden_source_leak",
                              f"packet.audience_inspector.{key}")

    # 6) consensus special codes.
    state = cand.get("ensemble_projection_state")
    consensus = cand_aud.get("consensus_zh")
    if state == "no_ensemble" and consensus != s4.CONSENSUS_ZH["no_ensemble"]:
        return _issue("s4.fabricated_consensus",
                      "packet.audience_inspector.consensus_zh")
    if state == "single_analysis" and consensus != exp_aud.get("consensus_zh"):
        return _issue("s4.single_model_consensus_forbidden",
                      "packet.audience_inspector.consensus_zh")

    # 7) query leaves.
    for key in ("query_basis_zh", "query_finding_zh", "query_action_zh",
                "query_pd_wording_zh"):
        if cand_aud.get(key) != exp_aud.get(key):
            return _issue("s4.query_projection_drift",
                          f"packet.audience_inspector.{key}")

    # 8) audience baseline rows.
    if cand_aud.get("baseline_rows_zh") != exp_aud.get("baseline_rows_zh"):
        return _issue("s4.baseline_projection_drift",
                      "packet.audience_inspector.baseline_rows_zh")

    # 9) generic cross-plane drift on the remaining audience leaves.
    for key in exp_aud:
        if cand_aud.get(key) != exp_aud.get(key):
            return _issue("s4.cross_plane_projection_drift",
                          f"packet.audience_inspector.{key}")
    return None


def _located_locators(audience: Dict[str, Any]) -> set:
    """The authorized located-source set derived from the rebuilt expected
    audience (support + counter evidence locators)."""
    located: set = set()
    for key in ("support_evidence_zh", "counterevidence_zh"):
        for item in audience.get(key) or []:
            match = _EVIDENCE_LOCATOR_RE.search(str(item))
            if match:
                located.add(match.group(1))
    return located


# ---------------------------------------------------------------------------
# Generic full-leaf comparison and hash-DAG recompute
# ---------------------------------------------------------------------------


def _first_leaf_drift(
    cand: Any, exp: Any, path: str,
) -> Optional[s4.R5S4ValidationIssue]:
    """Deep-compare every candidate leaf against the rebuilt expected packet,
    returning the first drift as the accepted generic cross-plane code.

    The six hash-DAG leaves and the audit ``packet_fingerprints`` leaf are
    excluded here and handled by ``_hash_recompute_issue`` with their specific
    codes.
    """
    if isinstance(exp, dict) and isinstance(cand, dict):
        for key in exp:
            if key not in cand:
                return _issue("s4.cross_plane_projection_drift",
                              f"{path}.{key}")
            if key in _HASH_LEAVES and path == "packet":
                continue
            if key == "packet_fingerprints":
                continue
            issue = _first_leaf_drift(cand[key], exp[key], f"{path}.{key}")
            if issue is not None:
                return issue
        for key in cand:
            if key not in exp:
                return _issue("s4.cross_plane_projection_drift",
                              f"{path}.{key}")
        return None
    if isinstance(exp, list) and isinstance(cand, list):
        if len(cand) != len(exp):
            return _issue("s4.cross_plane_projection_drift", path)
        for index, (candidate, expected) in enumerate(zip(cand, exp)):
            issue = _first_leaf_drift(candidate, expected, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    if cand != exp:
        return _issue("s4.cross_plane_projection_drift", path)
    return None


def _hash_recompute_issue(
    cand: Dict[str, Any], exp: Dict[str, Any],
) -> Optional[s4.R5S4ValidationIssue]:
    """Explicitly recompute every hash-DAG node from the candidate's own
    content and require it to equal the candidate's declared leaf.

    Runs only after the full-leaf compare passed, so the candidate content
    equals the rebuilt expected content; a declared-hash-vs-recompute drift is
    therefore a forged hash leaf and gets its specific accepted code."""
    # audience content hash (covers every audience leaf).
    aud_hash = s4.s4_content_hash(cand["audience_inspector"])
    if cand["audience_content_hash"] != aud_hash:
        return _issue("s4.audience_hash_contains_audit_leaf",
                      "packet.audience_content_hash")
    # audit content hash (excludes packet_fingerprints).
    audit = cand["audit_inspector"]
    audit_core = {key: val for key, val in audit.items()
                  if key != "packet_fingerprints"}
    audit_hash = s4.s4_content_hash(audit_core)
    if cand["audit_content_hash"] != audit_hash:
        return _issue("s4.audience_audit_leak", "packet.audit_content_hash")
    # receipt content hash.
    receipt_hash = s4.s4_content_hash(cand["authority_receipt"])
    if cand["receipt_content_hash"] != receipt_hash:
        return _issue("s4.receipt_hash_mismatch",
                      "packet.receipt_content_hash")
    # packet id from the audience content hash.
    packet_id = s4.compute_packet_id(aud_hash)
    if cand["packet_id"] != packet_id:
        return _issue("s4.packet_id_grammar_mismatch", "packet.packet_id")
    # packet fingerprints (audience/receipt/packet/risk-identity hashes).
    fingerprints = list(s4.compute_packet_fingerprints(
        aud_hash, receipt_hash, packet_id,
        cand["risk_identity"]["risk_identity_hash"]))
    if audit.get("packet_fingerprints") != fingerprints:
        return _issue("s4.cross_plane_projection_drift",
                      "packet.audit_inspector.packet_fingerprints")
    # packet integrity hash (covers both planes minus hash/id/schema/mode).
    integrity_hash = s4.compute_packet_integrity_hash(cand)
    if cand["packet_integrity_hash"] != integrity_hash:
        return _issue("s4.hash_recipe_cycle", "packet.packet_integrity_hash")
    return None


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def validate_s4_authority_packet(
    candidate: Mapping[str, object] | s4.R5S4AuthorityPacket,
    runtime_input: s4.R5S4RuntimeInput,
) -> s4.R5S4ValidationResult:
    """Fail-closed validation of an untrusted candidate packet against the
    typed runtime input.

    Rebuilds the expected packet from the runtime input via the real builder
    + projection, then runs the recursive structural gate, the fixed-priority
    semantic checks, the generic full-leaf comparison and the hash-DAG
    recompute.  The first violated invariant is the single returned issue
    (registry single-code precedence); a structurally unparseable candidate
    yields ``expected_packet=None``.  A runtime input the builder rejects is
    an ``S4RuntimeImplementationError`` (never a packet rejection).
    """
    cand = _candidate_mapping(candidate)

    # Rebuild the expected packet from the typed authority (candidate never
    # proves itself).  A trusted-source failure is an implementation error
    # and is kept distinct from a candidate rejection.
    try:
        expected = build_s4_authority_packet(runtime_input)
    except s4.S4RuntimeImplementationError:
        raise
    except Exception as exc:  # noqa: BLE001 - trusted-source failure
        raise s4.S4RuntimeImplementationError(
            "failed to rebuild the expected S4 authority packet from the "
            f"runtime input ({type(exc).__name__}: {exc})") from exc
    exp = s4.packet_as_mapping(expected)

    # 0) recursive structural gate: an unparseable candidate has no safe
    #    expected-packet comparison.
    structural = _recursive_structure_issue(cand, exp)
    if structural is not None:
        return _result(False, (structural,), None)

    # 1) frozen packet identity.
    issue = _root_meta_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 2) 0/1/N ensemble cardinality and identity isolation.
    issue = _cardinality_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _no_ensemble_empty_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _worker_uniqueness_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _input_authority_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 3) audit-plane bound objects.
    issue = _model_evidence_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _raw_artifact_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _adjudicator_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _verification_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _verification_adjudication_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 4) conflict rows.
    issue = _conflict_hideability_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _conflict_set_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 5) baseline.
    issue = _baseline_recheck_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _baseline_projection_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 6) history / journey / anchor claim / query.
    issue = _history_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _journey_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _anchor_claim_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)
    issue = _query_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    # 7) audience plane (all audience invariants with internal precedence).
    issue = _audience_issue(cand, exp, cand.get("journey_link", {}))
    if issue is not None:
        return _result(False, (issue,), expected)

    # 8) generic full-leaf comparison (catches any drift no specific rule
    #    assigned, incl. deleted members / changed nested leaves).
    issue = _first_leaf_drift(cand, exp, "packet")
    if issue is not None:
        return _result(False, (issue,), expected)

    # 9) explicit hash-DAG recompute (forged hash leaf rejection).
    issue = _hash_recompute_issue(cand, exp)
    if issue is not None:
        return _result(False, (issue,), expected)

    return _result(True, (), expected)
