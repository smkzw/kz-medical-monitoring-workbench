"""R5-S4 Risk Inspector runtime typed contracts, closed vocabularies,
canonical/hash recipes and exact reference grammar (synthetic, offline).

This module is the contract surface of the R5-S4 runtime thin slice.  It is
the single shared source of:

* the immutable typed packet / external-anchor / runtime-input objects that
  ``s4_authority_builder``, ``s4_projection`` and ``s4_validator`` exchange;
* the closed vocabularies and every deterministic Chinese mapping declared by
  the accepted runtime contract (all word tables live here once; projection
  and validator share the same immutable tables);
* the canonical serialization + six-node acyclic hash DAG recipes
  (``utf8_nfc_sorted_keys_compact_json_newline``);
* the exact reference grammars (marker / ``baseline-row:`` / ``raw:`` /
  ``verification:`` / ``receipt:`` / ``history:`` / ``anchor:<sha256>``);
* the append-only history chain semantics and the locatable/unavailable
  source semantics.

Scope boundaries (accepted runtime contract):

* This module is local-structure and hash-invariant only: it never opens a
  file, never imports or reads the machine artifacts, generator or verifier,
  and never calls an R4 evaluator (``run_ensemble`` / ``verify_attempt`` /
  ``derive_conflicts`` / ``_adjudicate``).
* ``s4_contracts`` imports the frozen R4/R5 public *typed objects* read-only
  because the runtime input and packet reference them; it adds no medical
  semantics.
* The accepted machine schema ``packet_schema.json`` is the *test reference
  authority* for exact keys/type/cardinality/nullability/closed enums; this
  module does not read it at runtime.
* Two frozen errata override the older machine schema leaves and apply only
  to the runtime:
  ``R5S4HistoryLog.entries`` is ``min_items:0`` and only ``no_ensemble`` may
  carry an empty log (``head_seq=0``, ``head_hash="genesis"``); and
  ``S4AcceptedHistoryState.hash`` is ``genesis_or_sha`` (only ``seq=0`` and
  ``head="genesis"`` allow ``hash="genesis"``, every other state must be a
  SHA-256).  These rules are implemented below; they are never generalised
  into a blanket schema-rewrite right.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

from ...risks.d10_contracts import ModelEvidence
from ..d10 import D10QueryDraft
from ...risks.ensemble import EvidenceDigestContext, WorkerAnalysisOutput
from ...risks.ensemble_contracts import (
    AdjudicationBinding,
    AnalysisAttempt,
    ReferenceBaselineItem,
)
from .contracts import (
    R5AuthorityReceipt,
    R5ChangeBand,
    R5DeepLinkState,
    R5RiskInspectorProjection,
)
from .s2_thin_slice import R5S2SourceResolution


# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

#: The exact packet schema id (must equal the accepted machine schema).
S4_PACKET_SCHEMA_ID = "medical-monitoring-r5-s4-packet-schema-v0.1"
#: Frozen authority mode (schema ``authority_mode``).
S4_AUTHORITY_MODE = "synthetic_offline_test_only"
#: Frozen packet status (schema ``status``).
S4_STATUS = "R5_S4_CONTRACT_READY_FOR_REVIEW"

#: Literal single-colon packet identity grammar.
PACKET_ID_PREFIX = "r5-s4-contract"
PACKET_ID_GRAMMAR = f"{PACKET_ID_PREFIX}:<audience_content_hash>"
#: Reference prefixes.
ANCHOR_REF_PREFIX = "anchor:"
RECEIPT_REF_PREFIX = "receipt:"
HISTORY_REF_PREFIX = "history:"
RAW_REF_PREFIX = "raw:"
VERIFICATION_REF_PREFIX = "verification:"
#: Frozen genesis constant (overlay ``genesis_hash``).
GENESIS_HASH = "genesis"
#: Adjudication record ref projected by multi-analysis audit/adjudication.
ADJUDICATION_RECORD_REF = "adj.record.1"
#: Exact canonicalisation recipe name (hash_dag canonicalization).
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"

#: Closed audience contract id (never derived from receipt/label/candidate).
AUDIENCE_CONTRACT_ID = "contract.s4.1"

#: Marker-identity prefixes of the public D09/D10 risk markers.
D09_MARKER_PREFIX = "d09_marker:"
D10_MARKER_PREFIX = "d10_marker:"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def is_sha256_hex(value: Any) -> bool:
    """True iff ``value`` is a 64-char lowercase hex sha256 string."""
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class S4RuntimeContractError(Exception):
    """Closed-enum, exact-key, cardinality, shape, grammar or hash-invariant
    violation of an S4 typed packet / anchor / runtime-input object.

    This is a *packet-level* condition: an ill-formed or tampered packet or
    runtime input.  It is distinct from :class:`S4RuntimeImplementationError`,
    which is reserved for trusted-source/schema/implementation failures that
    must never be dressed up as a packet rejection."""


class S4RuntimeImplementationError(Exception):
    """Trusted-source / schema / implementation failure.

    Raised when a trusted artifact or runtime precondition is broken (for
    example an unresolvable imported-object type or a schema that cannot be
    parsed).  It is never used to reject an otherwise well-formed packet; a
    packet rejection must always surface as ``S4RuntimeContractError`` or a
    stable ``s4.*`` validation issue."""


@dataclass(frozen=True)
class R5S4ValidationIssue:
    """One stable validation issue (exact fields).

    ``message_zh`` is never free-formed: the unique formula is
    ``核对未通过：{path}（{code}）``.
    """

    code: str
    path: str
    message_zh: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _check_str(self.code, "code"))
        object.__setattr__(self, "path", _check_str(self.path, "path"))
        expected = f"核对未通过：{self.path}（{self.code}）"
        if not self.message_zh:
            object.__setattr__(self, "message_zh", expected)
        elif self.message_zh != expected:
            raise S4RuntimeContractError(
                "R5S4ValidationIssue.message_zh must use the fixed formula "
                "核对未通过：{path}（{code}）")


@dataclass(frozen=True)
class R5S4ValidationResult:
    """Fail-closed validator result (exact fields).

    ``issues`` are ordered and deduplicated by ``(code, path, message_zh)``.
    ``expected_packet`` is ``None`` when the candidate structure could not be
    parsed safely; otherwise the validator rebuilds the expected packet from
    the runtime input and compares (the candidate never proves itself).
    """

    ok: bool
    issues: Tuple[R5S4ValidationIssue, ...]
    expected_packet: Optional["R5S4AuthorityPacket"]

    def __post_init__(self) -> None:
        if not isinstance(self.issues, tuple):
            raise S4RuntimeContractError(
                "R5S4ValidationResult.issues must be a tuple")
        # ``ok`` must be an EXACT bool; never coerce arbitrary values with
        # ``bool(...)`` (an int/str/None must not silently become True/False).
        if type(self.ok) is not bool:
            raise S4RuntimeContractError(
                f"R5S4ValidationResult.ok must be an exact bool, got "
                f"{type(self.ok).__name__}: {self.ok!r}")
        ordered = tuple(sorted(
            self.issues,
            key=lambda issue: (issue.code, issue.path, issue.message_zh)))
        object.__setattr__(self, "issues", tuple(dict.fromkeys(ordered)))
        object.__setattr__(self, "ok", self.ok and not self.issues)


# ---------------------------------------------------------------------------
# Canonical serialization (frozen hash_recipes: utf8_nfc_sorted_keys_compact
# json_newline) + the R4-style hash used by the external anchor identity.
# ---------------------------------------------------------------------------


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_nfc(item) for item in value)
    if isinstance(value, dict):
        return {_nfc(key): _nfc(val) for key, val in value.items()}
    return value


def _to_plain(value: Any) -> Any:
    """Recursively convert a packet value to a plain JSON-able structure.

    Frozen dataclasses become field dicts; ``datetime.date`` becomes
    ``YYYY-MM-DD`` (the canonical date leaf).  Tuple/list items keep their
    stored order (a many field's canonical order is decided at construction by
    the schema-declared ``sorted_unique`` rule).
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_plain(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {_nfc(key): _to_plain(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        # passed through so ``json.dumps(..., allow_nan=False)`` rejects
        # non-finite values with the canonical ValueError.
        return value
    if isinstance(value, FrozenSet):
        return sorted(_to_plain(item) for item in value)
    raise S4RuntimeContractError(
        f"unsupported packet leaf type {type(value).__name__}: {value!r}")


def s4_canonical_bytes(value: Any) -> bytes:
    """Deterministic canonical bytes of any packet value (NFC, sorted keys,
    compact separators, ``allow_nan=False``, trailing newline)."""
    plain = _to_plain(value)
    return (json.dumps(_nfc(plain), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False)
            + "\n").encode("utf-8")


def s4_canonical_json(value: Any) -> str:
    """Deterministic canonical JSON text of any packet value."""
    return s4_canonical_bytes(value).decode("utf-8")


def s4_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def s4_content_hash(value: Any) -> str:
    """Canonical content address of any packet value (trailing-newline
    recipe).  This is the hash used by the six-node hash DAG."""
    return s4_sha256(s4_canonical_bytes(value))


def r4_style_hash(value: Any) -> str:
    """R4 content-hash recipe (compact, sorted keys, NO trailing newline).

    Used only for the external ``S4AcceptedAuthorityAnchor.anchor_identity_hash``
    (``canonical_sha256_of:self_excluding_anchor_identity_hash``) and for the
    machine-adjacent R4-style nested hashes that the typed R5 objects already
    carry as stored values.
    """
    return hashlib.sha256(json.dumps(_nfc(_to_plain(value)), ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def s4_content_hash_excluding(obj: Any, excluded: Tuple[str, ...]) -> str:
    """Canonical content hash of one dataclass object excluding the named root
    fields."""
    if not (is_dataclass(obj) and not isinstance(obj, type)):
        raise S4RuntimeContractError(
            f"s4_content_hash_excluding expects a dataclass, got "
            f"{type(obj).__name__}")
    core = {field.name: getattr(obj, field.name)
            for field in fields(obj) if field.name not in excluded}
    return s4_content_hash(core)


def compute_anchor_identity_hash(anchor_body: Mapping[str, Any]) -> str:
    """``anchor_identity_hash = r4_style_hash(anchor body excluding
    anchor_identity_hash)`` (the external accepted anchor's self hash)."""
    body = {k: v for k, v in anchor_body.items() if k != "anchor_identity_hash"}
    return r4_style_hash(body)


def compute_history_entry_hash(entry: "R5S4HistoryEntry") -> str:
    """``entry_hash = canonical sha256 of every entry leaf except entry_hash``
    (chain ``chain_includes_prior_hash``: ``prior_entry_hash`` participates)."""
    core = {field.name: getattr(entry, field.name)
            for field in fields(entry) if field.name != "entry_hash"}
    return s4_content_hash(core)


def audience_content_hash_of(inspector: "R5S4AudienceInspector") -> str:
    """``audience_content_hash = canonical sha256(audience_inspector)``
    covering every audience leaf (the audience plane has no audit leaf)."""
    return s4_content_hash(inspector)


def audit_content_hash_of(inspector: "R5S4AuditInspector") -> str:
    """``audit_content_hash = canonical sha256(audit_inspector) EXCLUDING the
    packet_fingerprints leaf`` (acyclic: the fingerprint leaf derives from
    independent upstream hashes and is not covered by the audit hash)."""
    core = {field.name: getattr(inspector, field.name)
            for field in fields(inspector) if field.name != "packet_fingerprints"}
    return s4_content_hash(core)


def receipt_content_hash_of(receipt: R5AuthorityReceipt) -> str:
    """``receipt_content_hash = canonical sha256(complete R5AuthorityReceipt)``
    (no field excluded)."""
    return s4_content_hash(receipt)


def compute_packet_id(audience_content_hash_value: str) -> str:
    """``packet_id = r5-s4-contract:<audience_content_hash>`` (single colon)."""
    if not is_sha256_hex(audience_content_hash_value):
        raise S4RuntimeContractError(
            f"audience_content_hash must be a sha256 hex for packet_id, got "
            f"{audience_content_hash_value!r}")
    return f"{PACKET_ID_PREFIX}:{audience_content_hash_value}"


def compute_packet_fingerprints(
    audience_content_hash_value: str,
    receipt_content_hash_value: str,
    packet_id_value: str,
    risk_identity_hash_value: str,
) -> Tuple[str, ...]:
    """``packet_fingerprints = sorted([audience:<...>, receipt:<...>,
    packet:<...>, risk_identity:<...>])`` (frozen acyclic prefix recipe)."""
    return tuple(sorted([
        f"audience:{audience_content_hash_value}",
        f"receipt:{receipt_content_hash_value}",
        f"packet:{packet_id_value}",
        f"risk_identity:{risk_identity_hash_value}",
    ]))


def compute_packet_integrity_hash(packet: Mapping[str, Any]) -> str:
    """``packet_integrity_hash = canonical sha256(packet excluding packet_id,
    packet_integrity_hash, audience/audit/receipt content hash, schema, status,
    authority_mode)``.  It covers both audience and audit planes (hidden-only
    private changes alter integrity but never audience/audit hash)."""
    excluded = {"packet_id", "packet_integrity_hash", "audience_content_hash",
                "audit_content_hash", "receipt_content_hash", "schema",
                "status", "authority_mode"}
    body = {k: v for k, v in packet.items() if k not in excluded}
    return s4_content_hash(body)


# ---------------------------------------------------------------------------
# Closed vocabularies (exact values from the accepted machine overlay)
# ---------------------------------------------------------------------------

ENSEMBLE_PROJECTION_STATES: Tuple[str, ...] = (
    "no_ensemble", "single_analysis", "multi_analysis")
BASELINE_STATES: Tuple[str, ...] = (
    "confirmed", "partially_supported", "unsupported", "outdated",
    "insufficient_evidence", "not_applicable")
RECHECK_REQUIRED_STATES: Tuple[str, ...] = ("confirmed", "unsupported")
ASSESSMENT_REASON_CODES: Tuple[str, ...] = (
    "source_rechecked", "content_match", "partial_content_match",
    "content_absent_from_source", "source_revision_superseded",
    "evidence_insufficient", "locator_unresolvable", "outside_assessment_scope")
VERIFICATION_DIMENSIONS: Tuple[str, ...] = (
    "identity", "version", "date", "unit", "source", "rule",
    "artifact_integrity")
SEVEN_DIMENSIONS: FrozenSet[str] = frozenset(VERIFICATION_DIMENSIONS)
VERIFICATION_RESULTS: Tuple[str, ...] = ("passed", "failed", "not_evaluable")
VERIFICATION_FAILURE_CODES: Tuple[str, ...] = (
    "identity_mismatch", "version_mismatch", "date_out_of_window",
    "unit_mismatch", "source_unresolvable", "rule_version_mismatch",
    "artifact_hash_mismatch", "input_content_mismatch")
CONFLICT_RELATIONS: Tuple[str, ...] = (
    "shared_finding", "single_model_new", "graded_conflict",
    "mutual_negation", "baseline_miss")
CONFLICT_DISPLAY_STATES: Tuple[str, ...] = (
    "needs_attention", "visible_conflict", "visible_baseline_miss")
NON_HIDEABLE_RELATIONS: FrozenSet[str] = frozenset(
    {"mutual_negation", "baseline_miss"})
ADJUDICATION_OUTCOMES: Tuple[str, ...] = (
    "merged_supported", "distinct_supported", "rejected_by_evidence",
    "version_mismatch", "needs_user_attention")
SUPPORTING_OUTCOMES: FrozenSet[str] = frozenset(
    {"merged_supported", "distinct_supported"})
ATTEMPT_ROLES: Tuple[str, ...] = ("worker", "adjudicator")
RAW_OUTPUT_FORMATS: Tuple[str, ...] = ("utf8_text",)
FALLBACK_POLICIES: Tuple[str, ...] = ("none",)
PD_WORDING_STATES: Tuple[str, ...] = ("not_pd", "verify_whether_pd")
MONITORING_PRIORITIES: Tuple[str, ...] = ("high", "medium", "low", "unknown")
SEVERITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")
SEVERITIES_ZH: Tuple[str, ...] = ("紧急", "高", "中", "低")
DOMAINS: Tuple[str, ...] = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance")
CHANGE_KINDS: Tuple[str, ...] = (
    "initial_current", "new", "upgraded", "continued", "downgraded",
    "resolved", "reopened", "superseded", "not_evaluable", "not_comparable")
CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "knowledge", "rule", "mapping", "model", "method", "coverage",
    "denominator", "population", "visibility", "mode", "user_decision")
HISTORY_ENTRY_KINDS: Tuple[str, ...] = (
    "attempt_bound", "baseline_assessed", "verification_recorded",
    "conflict_derived", "adjudication_recorded", "query_draft_generated",
    "inspection_finalized")
MODEL_EVIDENCE_ROLES: Tuple[str, ...] = (
    "candidate_explanation", "counterevidence_suggestion")
MODEL_EVIDENCE_ADJUDICATION_STATES: Tuple[str, ...] = (
    "accepted", "divergent", "pending")

#: Source availability states (runtime-only wrapper).
SOURCE_AVAILABILITY_STATES: Tuple[str, ...] = ("locatable", "unavailable")
#: Closed unavailable reasons (runtime-only wrapper).
UNAVAILABLE_REASONS: Tuple[str, ...] = ("target_not_projectable",
                                        "source_locator_missing")

# ---------------------------------------------------------------------------
# Closed Chinese mappings (declared once here; projection + validator share
# the same immutable tables)
# ---------------------------------------------------------------------------

#: ordinal labels 分析一..分析十 (index 0 => first analysis).
ORDINAL_ZH: Tuple[str, ...] = (
    "分析一", "分析二", "分析三", "分析四", "分析五",
    "分析六", "分析七", "分析八", "分析九", "分析十")

#: domain -> audience label.
DOMAIN_ZH: Dict[str, str] = {
    "ae": "AE", "mh": "MH", "cm": "合并用药", "ip": "试验药",
    "lab_exam": "检验/检查", "hospital_procedure": "住院/操作",
    "symptom_efficacy": "症状/疗效", "protocol_compliance": "方案符合",
}

#: severity -> severity_zh.
SEVERITY_ZH_BY_SEVERITY: Dict[str, str] = {
    "critical": "紧急", "high": "高", "medium": "中", "low": "低",
}

#: frozen severity mapping (R4 monitoring_priority -> R5 severity);
#: ``unknown`` fails closed (no generic enum mismatch, no promotion).
SEVERITY_MAPPING: Dict[str, str] = {
    "high": "high", "medium": "medium", "low": "low", "unknown": "fail_closed",
}

#: change_kind -> change_state_zh.
CHANGE_KIND_ZH: Dict[str, str] = {
    "initial_current": "首次识别",
    "new": "新发",
    "upgraded": "风险升高",
    "continued": "持续存在",
    "downgraded": "风险降低",
    "resolved": "已消失",
    "reopened": "再次出现",
    "superseded": "已被后续记录替代",
    "not_evaluable": "暂无法评估",
    "not_comparable": "暂不可比较",
}

#: baseline state -> state_zh.
BASELINE_STATE_ZH: Dict[str, str] = {
    "confirmed": "已确认",
    "partially_supported": "部分支持",
    "unsupported": "不支持",
    "outdated": "已过期",
    "insufficient_evidence": "证据不足",
    "not_applicable": "不适用",
}

#: recheck provenance label (source actually rechecked or not).
RECHECK_ZH: Dict[bool, str] = {True: "已回查来源", False: "未回查来源"}

#: verification result -> verification_zh (closed).
VERIFICATION_RESULT_ZH: Dict[str, str] = {
    "passed": "七项核对均通过",
    "failed": "核对未通过",
    "not_evaluable": "暂无法核对",
}

#: verification failure code -> Chinese item (sorted by code before joining).
VERIFICATION_FAILURE_ZH: Dict[str, str] = {
    "identity_mismatch": "身份不一致",
    "version_mismatch": "版本不一致",
    "date_out_of_window": "日期超出范围",
    "unit_mismatch": "单位不一致",
    "source_unresolvable": "来源无法定位",
    "rule_version_mismatch": "规则版本不一致",
    "artifact_hash_mismatch": "文件内容不一致",
    "input_content_mismatch": "输入内容不一致",
}

#: conflict relation -> Chinese relation (frozen presentation order).
CONFLICT_RELATION_ZH: Dict[str, str] = {
    "shared_finding": "共同发现",
    "single_model_new": "单一分析新增发现",
    "graded_conflict": "风险分级不一致",
    "mutual_negation": "结论相互矛盾",
    "baseline_miss": "基线项目未被评估",
}
#: frozen relation presentation order (used to join multi-relation phrases).
CONFLICT_RELATION_ORDER: Tuple[str, ...] = CONFLICT_RELATIONS

#: adjudication outcome -> audience explanation mapping (upstream-outcome
#: frozen Chinese projection; adds no new medical conclusion).
ADJUDICATION_OUTCOME_ZH: Dict[str, str] = {
    "merged_supported": "可合并为同一发现",
    "distinct_supported": "应保留为不同发现",
    "rejected_by_evidence": "现有证据不支持",
    "version_mismatch": "版本不一致，暂无法判断",
    "needs_user_attention": "需要医学监察员重点查看",
}

#: PD wording state -> Chinese leaf.
PD_WORDING_ZH: Dict[str, str] = {
    "not_pd": "非方案偏离",
    "verify_whether_pd": "请核实是否为方案偏离",
}

#: consensus phrases gated by ensemble state (contract section 6).
CONSENSUS_ZH: Dict[str, str] = {
    "no_ensemble": "尚无独立分析",
    "single_analysis": "单一分析不形成一致性结论",
    "multi_consistent": "多个独立分析结果一致",
    "multi_conflict": "独立分析存在{conflicts}，请结合来源核实",
}

#: adjudication status phrases (N<2 vs N>=2).
ADJUDICATION_STATUS_ZH: Dict[str, str] = {
    "none": "尚未进行独立裁决",
    "done": "已完成独立裁决",
}

#: history summary phrases (per ensemble state).
HISTORY_SUMMARY_ZH: Dict[str, str] = {
    "no_ensemble": "尚无独立分析记录",
    "single_analysis": "已记录一次独立分析及来源核对过程",
    "multi_analysis": "已记录多次独立分析、冲突核对及裁决过程",
}

#: basis phrases (per ensemble state).
BASIS_ZH: Dict[str, str] = {
    "no_ensemble": "当前仅展示已识别风险及其来源",
    "single_analysis": "已完成一次独立分析，请结合来源核实",
    "multi_analysis": "已完成多次独立分析，请结合基线、冲突与来源核实",
}

#: journey link phrase when locatable.
JOURNEY_LINK_ZH = "查看该受试者历时记录"
#: journey unavailable reason (fixed Chinese repair path; never nearest
#: fallback).
JOURNEY_UNAVAILABLE_REASON_ZH = \
    "无法定位到该受试者的对应记录，请核对项目、受试者和数据截止点"

#: frozen forbidden audience tokens (closed; enforced by validator).
FORBIDDEN_AUDIENCE_TOKENS: Tuple[str, ...] = (
    "provider", "model_id", "model_version", "attempt", "hash", "backend",
    "session", "consensus", "worker", "adjudicator", "binding", "正式事实",
    "候选信号", "只读", "待办", "未读", "金标准", "已证实", "权威结论",
    "model_majority", "卡列表", "已发送", "已关闭",
)

#: frozen audit-only leaves that may never appear on the audience plane
#: (hash_dag ``audience_content_hash.forbidden_leaves`` + static audit leaves).
AUDIT_ONLY_LEAVES: FrozenSet[str] = frozenset({
    "binding_id", "session_id", "model_id", "model_version",
    "independent_context_hash", "raw_bytes_b64", "raw_bytes_sha256",
    "declared_output_hash", "verification_audit_rows", "history_audit",
    "packet_fingerprints", "model_evidence", "digest_context",
    "output_digests", "artifact_source_versions",
})

#: structural task keys forbidden on the Query draft row (schema forbidden
#: keys; their presence is ``s4.query_task_semantics``).
QUERY_TASK_FORBIDDEN_KEYS: FrozenSet[str] = frozenset({
    "send_status", "reply", "closed_at", "assignee", "todo", "unread",
})

#: nearest-fallback wording tokens (their presence is
#: ``s4.nearest_fallback_forbidden``).
NEAREST_FALLBACK_TOKENS: Tuple[str, ...] = (
    "就近", "邻近", "最近替代", "相邻站点", "就近替代",
)

# ---------------------------------------------------------------------------
# Exact reference grammar
# ---------------------------------------------------------------------------

BASELINE_ROW_GRAMMAR = re.compile(r"^baseline-row:[^:]+:[^:]+$")
PROJECT_REF_GRAMMAR = re.compile(r"^project\.[A-Za-z0-9_.-]+$")
RUN_REF_GRAMMAR = re.compile(r"^run\.[A-Za-z0-9_.-]+$")
SNAPSHOT_REF_GRAMMAR = re.compile(r"^snap\.[A-Za-z0-9_.-]+$")
CUTOFF_REF_GRAMMAR = re.compile(r"^cutoff\.[A-Za-z0-9_.-]+$")
SOURCE_REVISION_GRAMMAR = re.compile(r"^rev\.[A-Za-z0-9_.-]+$")
_ANCHOR_REF_GRAMMAR = re.compile(r"^anchor:[0-9a-f]{64}$")
_RAW_REF_GRAMMAR = re.compile(r"^raw:[^:]+$")
_VERIFICATION_REF_GRAMMAR = re.compile(r"^verification:[^:]+$")
_RECEIPT_REF_GRAMMAR = re.compile(r"^receipt:[0-9a-f]{64}$")
_HISTORY_REF_GRAMMAR = re.compile(r"^history:[^:]+$")


def matches_grammar(value: Any, grammar: str) -> bool:
    """Match one named grammar (``marker`` / ``baseline_row`` / ``raw`` /
    ``verification`` / ``receipt`` / ``history`` / ``anchor`` /
    ``project_ref`` / ``run_ref`` / ``snapshot_ref`` / ``cutoff_ref`` /
    ``source_revision`` / ``packet_id``)."""
    if not isinstance(value, str):
        return False
    if grammar == "marker":
        return value.startswith(D09_MARKER_PREFIX) or \
            value.startswith(D10_MARKER_PREFIX)
    if grammar == "baseline_row":
        return bool(BASELINE_ROW_GRAMMAR.match(value))
    if grammar == "raw":
        return bool(_RAW_REF_GRAMMAR.match(value))
    if grammar == "verification":
        return bool(_VERIFICATION_REF_GRAMMAR.match(value))
    if grammar == "receipt":
        return bool(_RECEIPT_REF_GRAMMAR.match(value))
    if grammar == "history":
        return bool(_HISTORY_REF_GRAMMAR.match(value))
    if grammar == "anchor":
        return bool(_ANCHOR_REF_GRAMMAR.match(value))
    if grammar == "project_ref":
        return bool(PROJECT_REF_GRAMMAR.match(value))
    if grammar == "run_ref":
        return bool(RUN_REF_GRAMMAR.match(value))
    if grammar == "snapshot_ref":
        return bool(SNAPSHOT_REF_GRAMMAR.match(value))
    if grammar == "cutoff_ref":
        return bool(CUTOFF_REF_GRAMMAR.match(value))
    if grammar == "source_revision":
        return bool(SOURCE_REVISION_GRAMMAR.match(value))
    if grammar == "packet_id":
        suffix = value[len(PACKET_ID_PREFIX) + 1:]
        return value.count(":") == 1 and \
            value.startswith(PACKET_ID_PREFIX + ":") and \
            is_sha256_hex(suffix)
    raise S4RuntimeImplementationError(f"unknown grammar {grammar!r}")


def is_marker_ref(value: Any) -> bool:
    return matches_grammar(value, "marker")


# ---------------------------------------------------------------------------
# Validation helpers (fail closed, never ``assert``)
# ---------------------------------------------------------------------------


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise S4RuntimeContractError(
            f"{name} must be a non-empty str, got {value!r}")
    return unicodedata.normalize("NFC", value)


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_str(value, name)


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise S4RuntimeContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise S4RuntimeContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_hash(value: Any, name: str) -> str:
    if not is_sha256_hex(value):
        raise S4RuntimeContractError(
            f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_optional_hash(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_hash(value, name)


def _check_closed(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise S4RuntimeContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_optional_closed(
    value: Any, name: str, allowed: Tuple[str, ...],
) -> Optional[str]:
    if value is None:
        return None
    return _check_closed(value, name, allowed)


def _freeze_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise S4RuntimeContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_str(item, f"{name}[]") for item in value)
    return tuple(sorted(dict.fromkeys(result)))


def _freeze_hash_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise S4RuntimeContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_hash(item, f"{name}[]") for item in value)
    return tuple(sorted(dict.fromkeys(result)))


def _freeze_closed_tuple(
    value: Any, name: str, allowed: Tuple[str, ...],
) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise S4RuntimeContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_closed(item, name, allowed) for item in value)
    return tuple(sorted(dict.fromkeys(result)))


def _freeze_obj_tuple(value: Any, name: str, cls: type) -> Tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise S4RuntimeContractError(f"{name} must be a list/tuple, got {value!r}")
    for item in value:
        if not isinstance(item, cls):
            raise S4RuntimeContractError(
                f"{name}[] must be a {cls.__name__}, got {type(item).__name__}")
    return tuple(value)


def _require_nonempty_tuple(value: Tuple[Any, ...], name: str) -> None:
    if not value:
        raise S4RuntimeContractError(f"{name} must be non-empty, got ()")


def _require_min_count(items: Tuple[Any, ...], minimum: int, name: str) -> None:
    if len(items) < minimum:
        raise S4RuntimeContractError(
            f"{name} must have at least {minimum} items, got {len(items)}")


def _require_exact_count(items: Tuple[Any, ...], expected: int, name: str) -> None:
    if len(items) != expected:
        raise S4RuntimeContractError(
            f"{name} must have exactly {expected} items, got {len(items)}")


def _check_obj_type(value: Any, cls: type, name: str) -> None:
    if not isinstance(value, cls):
        raise S4RuntimeContractError(
            f"{name} must be a {cls.__name__}, got {type(value).__name__}")


def _verify_content_hash(obj: Any, hash_field: str) -> None:
    """Canonical content-hash verification (tamper rejection): a supplied
    non-empty hash must equal the deterministic canonical hash of the non-hash
    fields, else ``S4RuntimeContractError``.  An empty supplied hash is filled
    in."""
    expected = s4_content_hash_excluding(obj, (hash_field,))
    supplied = getattr(obj, hash_field)
    if supplied and supplied != expected:
        raise S4RuntimeContractError(
            f"{type(obj).__name__}.{hash_field} {supplied!r} does not match "
            f"the canonical hash {expected!r}")
    if not supplied:
        object.__setattr__(obj, hash_field, expected)


__all__ = [name for name in globals() if not name.startswith("__")]
