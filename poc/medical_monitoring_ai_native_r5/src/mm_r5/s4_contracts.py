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

from mm_r4.d10_contracts import ModelEvidence
from mm_r4.d10_projection import D10QueryDraft
from mm_r4.ensemble import EvidenceDigestContext, WorkerAnalysisOutput
from mm_r4.ensemble_contracts import (
    AdjudicationBinding,
    AnalysisAttempt,
    ReferenceBaselineItem,
)
from mm_r5.contracts import (
    R5AuthorityReceipt,
    R5ChangeBand,
    R5DeepLinkState,
    R5RiskInspectorProjection,
)
from mm_r5.s2_thin_slice import R5S2SourceResolution

__all__ = [
    # frozen contract identity (constants only)
    "S4_PACKET_SCHEMA_ID", "S4_AUTHORITY_MODE", "S4_STATUS",
    "PACKET_ID_PREFIX", "PACKET_ID_GRAMMAR", "ANCHOR_REF_PREFIX",
    "RECEIPT_REF_PREFIX", "HISTORY_REF_PREFIX", "RAW_REF_PREFIX",
    "VERIFICATION_REF_PREFIX", "GENESIS_HASH", "ADJUDICATION_RECORD_REF",
    "HASH_CANONICALIZATION",
    # errors
    "S4RuntimeContractError", "S4RuntimeImplementationError",
    "R5S4ValidationIssue", "R5S4ValidationResult",
    # closed vocabularies / zh mappings / constants
    "ENSEMBLE_PROJECTION_STATES", "BASELINE_STATES", "RECHECK_REQUIRED_STATES",
    "ASSESSMENT_REASON_CODES", "VERIFICATION_DIMENSIONS",
    "VERIFICATION_RESULTS", "VERIFICATION_FAILURE_CODES", "CONFLICT_RELATIONS",
    "CONFLICT_DISPLAY_STATES", "NON_HIDEABLE_RELATIONS",
    "ADJUDICATION_OUTCOMES", "ATTEMPT_ROLES", "RAW_OUTPUT_FORMATS",
    "FALLBACK_POLICIES", "PD_WORDING_STATES", "MONITORING_PRIORITIES",
    "SEVERITIES", "SEVERITIES_ZH", "DOMAINS", "CHANGE_KINDS", "CHANGE_CAUSES",
    "HISTORY_ENTRY_KINDS", "MODEL_EVIDENCE_ROLES",
    "MODEL_EVIDENCE_ADJUDICATION_STATES", "ORDINAL_ZH", "DOMAIN_ZH",
    "SEVERITY_ZH_BY_SEVERITY", "SEVERITY_MAPPING", "CHANGE_KIND_ZH",
    "BASELINE_STATE_ZH", "RECHECK_ZH", "VERIFICATION_RESULT_ZH",
    "VERIFICATION_FAILURE_ZH", "CONFLICT_RELATION_ZH",
    "ADJUDICATION_OUTCOME_ZH", "PD_WORDING_ZH", "CONSENSUS_ZH",
    "ADJUDICATION_STATUS_ZH", "HISTORY_SUMMARY_ZH", "BASIS_ZH",
    "JOURNEY_LINK_ZH", "JOURNEY_UNAVAILABLE_REASON_ZH",
    "FORBIDDEN_AUDIENCE_TOKENS", "AUDIT_ONLY_LEAVES",
    "QUERY_TASK_FORBIDDEN_KEYS", "SEVEN_DIMENSIONS",
    "AUDIENCE_CONTRACT_ID", "SUPPORTING_OUTCOMES", "NEAREST_FALLBACK_TOKENS",
    "SOURCE_AVAILABILITY_STATES", "UNAVAILABLE_REASONS",
    # grammar constants
    "D09_MARKER_PREFIX", "D10_MARKER_PREFIX", "BASELINE_ROW_GRAMMAR",
    "PROJECT_REF_GRAMMAR", "RUN_REF_GRAMMAR", "SNAPSHOT_REF_GRAMMAR",
    "CUTOFF_REF_GRAMMAR", "SOURCE_REVISION_GRAMMAR",
    # typed data contracts (packet / anchor / runtime wrappers)
    "R5S4RiskIdentity", "R5S4WorkerView", "R5S4RawOutputArtifact",
    "R5S4BaselineItemProjection", "R5S4BaselineRow", "R5S4ConflictRow",
    "R5S4VerificationRow", "R5S4AdjudicationRow", "R5S4QueryDraftRow",
    "R5S4JourneyLink", "R5S4HistoryEntry", "R5S4HistoryLog",
    "R5S4AudienceBaselineRow", "R5S4AudienceWorkerSummary",
    "R5S4AudienceInspector", "R5S4AuditWorkerRow", "R5S4VerificationAuditRow",
    "R5S4DigestContextView", "R5S4ModelEvidenceRef", "R5S4AuditInspector",
    "R5S4AuthorityPacket", "S4AcceptedHistoryState", "S4SourceRevisionPair",
    "S4AcceptedAdjudicatorBinding", "S4AcceptedBaselineItem",
    "S4AcceptedQueryDraft", "S4AcceptedRiskIdentity", "S4AttemptAuthorityRow",
    "S4JourneyTargetIdentity", "S4ModelEvidencePermit",
    "S4AcceptedAuthorityAnchor",
    # runtime-only wrappers (data contracts)
    "R5S4RawOutputInput", "R5S4AdjudicatorInput", "R5S4SyntheticAudienceLabels",
    "R5S4SourceInput", "R5S4RuntimeInput", "R5S4BuildState",
]

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


# ---------------------------------------------------------------------------
# Packet typed objects (exact keys from the accepted machine schema)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S4RiskIdentity:
    """Root risk identity (audience/root plane).  ``risk_identity_hash`` is
    the externally accepted R4 public risk identity hash (accepted leaf; the
    runtime treats the external anchor instance as authoritative)."""

    risk_ref: str
    risk_identity_hash: str
    domain: str
    domain_zh: str
    monitoring_priority: str
    severity: str
    severity_zh: str
    change_kind: str
    change_cause: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    spine_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5S4RiskIdentity.risk_ref"))
        object.__setattr__(self, "risk_identity_hash", _check_hash(
            self.risk_identity_hash, "R5S4RiskIdentity.risk_identity_hash"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5S4RiskIdentity.domain", DOMAINS))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority,
            "R5S4RiskIdentity.monitoring_priority", MONITORING_PRIORITIES))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5S4RiskIdentity.severity", SEVERITIES))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "R5S4RiskIdentity.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "change_cause", _check_closed(
            self.change_cause, "R5S4RiskIdentity.change_cause", CHANGE_CAUSES))
        for name in ("project_ref", "run_ref", "snapshot_ref", "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4RiskIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4RiskIdentity.{name}"))
        if self.domain_zh != DOMAIN_ZH[self.domain]:
            raise S4RuntimeContractError(
                f"R5S4RiskIdentity.domain_zh {self.domain_zh!r} must be the "
                f"closed projection of domain {self.domain!r}")
        if self.severity_zh != SEVERITY_ZH_BY_SEVERITY[self.severity]:
            raise S4RuntimeContractError(
                f"R5S4RiskIdentity.severity_zh {self.severity_zh!r} must be "
                f"the closed projection of severity {self.severity!r}")


@dataclass(frozen=True)
class R5S4WorkerView:
    """One worker attempt's audit view (audit plane)."""

    attempt_id: str
    ordinal: int
    ordinal_zh: str
    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    role: str
    independent_context_hash: str
    input_content_hash: str
    output_artifact_ref: str
    declared_output_hash: str
    claimed_date_window: str
    claimed_unit_contract: str
    claimed_source_revision: str
    claimed_rule_id: str
    claimed_rule_version: str
    assessment_row_refs: Tuple[str, ...]
    finding_ids: Tuple[str, ...]
    gap_ids: Tuple[str, ...]
    raw_artifact_ref: str
    verification_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4WorkerView.attempt_id"))
        object.__setattr__(self, "ordinal", _check_int(
            self.ordinal, "R5S4WorkerView.ordinal"))
        if not (1 <= self.ordinal <= len(ORDINAL_ZH)):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.ordinal must be 1..{len(ORDINAL_ZH)}, got "
                f"{self.ordinal!r}")
        if self.ordinal_zh != ORDINAL_ZH[self.ordinal - 1]:
            raise S4RuntimeContractError(
                f"R5S4WorkerView.ordinal_zh {self.ordinal_zh!r} must be the "
                f"closed label of ordinal {self.ordinal}")
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4WorkerView.role", ATTEMPT_ROLES))
        if self.role != "worker":
            raise S4RuntimeContractError(
                "R5S4WorkerView.role must be 'worker', got "
                f"{self.role!r}")
        for name in ("binding_id", "session_id", "model_id", "model_version",
                     "claimed_date_window", "claimed_unit_contract",
                     "claimed_source_revision", "claimed_rule_id",
                     "claimed_rule_version", "output_artifact_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4WorkerView.{name}"))
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "R5S4WorkerView.independent_context_hash"))
        object.__setattr__(self, "input_content_hash", _check_hash(
            self.input_content_hash, "R5S4WorkerView.input_content_hash"))
        object.__setattr__(self, "declared_output_hash", _check_hash(
            self.declared_output_hash, "R5S4WorkerView.declared_output_hash"))
        for name in ("assessment_row_refs", "finding_ids", "gap_ids"):
            object.__setattr__(self, name, _freeze_str_tuple(
                getattr(self, name), f"R5S4WorkerView.{name}"))
        if not matches_grammar(self.raw_artifact_ref, "raw"):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.raw_artifact_ref {self.raw_artifact_ref!r} "
                f"must match raw:<ref>")
        if not matches_grammar(self.verification_ref, "verification"):
            raise S4RuntimeContractError(
                f"R5S4WorkerView.verification_ref {self.verification_ref!r} "
                f"must match verification:<ref>")


@dataclass(frozen=True)
class R5S4RawOutputArtifact:
    """One raw-byte artifact (raw/parsed hash strictly separated)."""

    artifact_id: str
    attempt_id: str
    raw_format: str
    raw_bytes_b64: str
    raw_bytes_sha256: str
    parsed_output_hash: str
    declared_output_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_id", _check_str(
            self.artifact_id, "R5S4RawOutputArtifact.artifact_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4RawOutputArtifact.attempt_id"))
        object.__setattr__(self, "raw_format", _check_closed(
            self.raw_format, "R5S4RawOutputArtifact.raw_format",
            RAW_OUTPUT_FORMATS))
        object.__setattr__(self, "raw_bytes_b64", _check_str(
            self.raw_bytes_b64, "R5S4RawOutputArtifact.raw_bytes_b64"))
        object.__setattr__(self, "parsed_output_hash", _check_hash(
            self.parsed_output_hash,
            "R5S4RawOutputArtifact.parsed_output_hash"))
        object.__setattr__(self, "declared_output_hash", _check_hash(
            self.declared_output_hash,
            "R5S4RawOutputArtifact.declared_output_hash"))
        if self.declared_output_hash != self.parsed_output_hash:
            raise S4RuntimeContractError(
                "R5S4RawOutputArtifact.declared_output_hash must equal "
                "parsed_output_hash")
        # raw_bytes_sha256 is the canonical sha of the decoded raw bytes.
        try:
            raw_bytes = base64.b64decode(self.raw_bytes_b64, validate=True)
        except Exception as exc:
            raise S4RuntimeContractError(
                "R5S4RawOutputArtifact.raw_bytes_b64 is not valid base64: "
                f"{exc}") from None
        expected_sha = hashlib.sha256(raw_bytes).hexdigest()
        object.__setattr__(self, "raw_bytes_sha256", _check_hash(
            self.raw_bytes_sha256,
            "R5S4RawOutputArtifact.raw_bytes_sha256"))
        if self.raw_bytes_sha256 != expected_sha:
            raise S4RuntimeContractError(
                f"R5S4RawOutputArtifact.raw_bytes_sha256 "
                f"{self.raw_bytes_sha256!r} does not match "
                f"sha256(raw bytes) {expected_sha!r}")


@dataclass(frozen=True)
class R5S4BaselineItemProjection:
    """One packet baseline item: the imported R4 ``ReferenceBaselineItem``
    leaves plus the five approved import-extension fields
    (``project_ref``/``run_ref``/``snapshot_ref``/``cutoff_ref``/
    ``source_revision``) declared by the accepted machine schema's
    ``import_extensions``.  This is the exact typed shape a packet
    ``baseline_items`` entry must carry so the packet dict matches the machine
    schema."""

    item_id: str
    source_kind: str
    source_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    claimed_identity: str
    temporal_window: str
    claimed_content_hash: str
    origin_artifact_hash: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    source_revision: str

    def __post_init__(self) -> None:
        for name in ("item_id", "source_kind", "source_revision_id",
                     "snapshot_id", "claimed_identity", "temporal_window"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4BaselineItemProjection.{name}"))
        object.__setattr__(self, "source_locator_ids", _freeze_str_tuple(
            self.source_locator_ids,
            "R5S4BaselineItemProjection.source_locator_ids"))
        object.__setattr__(self, "claimed_content_hash", _check_hash(
            self.claimed_content_hash,
            "R5S4BaselineItemProjection.claimed_content_hash"))
        object.__setattr__(self, "origin_artifact_hash", _check_hash(
            self.origin_artifact_hash,
            "R5S4BaselineItemProjection.origin_artifact_hash"))
        for name, grammar in (("project_ref", PROJECT_REF_GRAMMAR),
                              ("run_ref", RUN_REF_GRAMMAR),
                              ("snapshot_ref", SNAPSHOT_REF_GRAMMAR),
                              ("source_revision", SOURCE_REVISION_GRAMMAR)):
            value = _check_str(getattr(self, name),
                               f"R5S4BaselineItemProjection.{name}")
            if not grammar.match(value):
                raise S4RuntimeContractError(
                    f"R5S4BaselineItemProjection.{name} {value!r} must match "
                    f"{grammar.pattern}")
            object.__setattr__(self, name, value)
        if self.cutoff_ref is not None:
            cutoff = _check_str(self.cutoff_ref,
                                "R5S4BaselineItemProjection.cutoff_ref")
            if not CUTOFF_REF_GRAMMAR.match(cutoff):
                raise S4RuntimeContractError(
                    f"R5S4BaselineItemProjection.cutoff_ref {cutoff!r} must "
                    f"match {CUTOFF_REF_GRAMMAR.pattern}")
            object.__setattr__(self, "cutoff_ref", cutoff)


@dataclass(frozen=True)
class R5S4BaselineRow:
    """One item x attempt six-state recheck row."""

    row_ref: str
    item_id: str
    attempt_id: str
    state: str
    reason_codes: Tuple[str, ...]
    source_recheck_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    recheck_complete: bool

    def __post_init__(self) -> None:
        if not matches_grammar(self.row_ref, "baseline_row"):
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.row_ref {self.row_ref!r} must match "
                f"baseline-row:<item_id>:<attempt_id>")
        parts = self.row_ref.split(":", 2)
        if len(parts) != 3 or parts[1] != self.item_id \
                or parts[2] != self.attempt_id:
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.row_ref {self.row_ref!r} must be "
                f"baseline-row:{self.item_id}:{self.attempt_id}")
        object.__setattr__(self, "item_id", _check_str(
            self.item_id, "R5S4BaselineRow.item_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4BaselineRow.attempt_id"))
        object.__setattr__(self, "state", _check_closed(
            self.state, "R5S4BaselineRow.state", BASELINE_STATES))
        object.__setattr__(self, "reason_codes", _freeze_closed_tuple(
            self.reason_codes, "R5S4BaselineRow.reason_codes",
            ASSESSMENT_REASON_CODES))
        object.__setattr__(self, "source_recheck_locator_ids",
                           _freeze_str_tuple(
                               self.source_recheck_locator_ids,
                               "R5S4BaselineRow.source_recheck_locator_ids"))
        object.__setattr__(self, "source_revision_id", _check_str(
            self.source_revision_id, "R5S4BaselineRow.source_revision_id"))
        object.__setattr__(self, "snapshot_id", _check_str(
            self.snapshot_id, "R5S4BaselineRow.snapshot_id"))
        object.__setattr__(self, "recheck_complete", _check_bool(
            self.recheck_complete, "R5S4BaselineRow.recheck_complete"))
        if self.state in RECHECK_REQUIRED_STATES and \
                not self.source_recheck_locator_ids:
            raise S4RuntimeContractError(
                f"R5S4BaselineRow.state {self.state!r} requires non-empty "
                "source_recheck_locator_ids (recheck_required_implies_locators)")


@dataclass(frozen=True)
class R5S4ConflictRow:
    """One cross-attempt disagreement kept visible after merge."""

    conflict_id: str
    relation: str
    display_state: str
    hidden: bool
    monitoring_priority: str
    member_attempt_ids: Tuple[str, ...]
    ordinal_labels_zh: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_id", _check_str(
            self.conflict_id, "R5S4ConflictRow.conflict_id"))
        object.__setattr__(self, "relation", _check_closed(
            self.relation, "R5S4ConflictRow.relation", CONFLICT_RELATIONS))
        object.__setattr__(self, "display_state", _check_closed(
            self.display_state, "R5S4ConflictRow.display_state",
            CONFLICT_DISPLAY_STATES))
        object.__setattr__(self, "hidden", _check_bool(
            self.hidden, "R5S4ConflictRow.hidden"))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority, "R5S4ConflictRow.monitoring_priority",
            MONITORING_PRIORITIES))
        object.__setattr__(self, "member_attempt_ids", _freeze_str_tuple(
            self.member_attempt_ids, "R5S4ConflictRow.member_attempt_ids"))
        _require_nonempty_tuple(self.member_attempt_ids,
                                "R5S4ConflictRow.member_attempt_ids")
        object.__setattr__(self, "ordinal_labels_zh", _freeze_str_tuple(
            self.ordinal_labels_zh, "R5S4ConflictRow.ordinal_labels_zh"))
        _require_nonempty_tuple(self.ordinal_labels_zh,
                                "R5S4ConflictRow.ordinal_labels_zh")
        if self.relation in NON_HIDEABLE_RELATIONS and self.hidden:
            raise S4RuntimeContractError(
                f"R5S4ConflictRow.relation {self.relation!r} is "
                "non-hideable (hidden must be False)")


@dataclass(frozen=True)
class R5S4VerificationRow:
    """One attempt's deterministic verification record (recomputed)."""

    verification_id: str
    attempt_id: str
    checked_dimensions: Tuple[str, ...]
    result: str
    failure_reason_codes: Tuple[str, ...]
    recomputed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "verification_id", _check_str(
            self.verification_id, "R5S4VerificationRow.verification_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4VerificationRow.attempt_id"))
        object.__setattr__(self, "checked_dimensions", _freeze_closed_tuple(
            self.checked_dimensions, "R5S4VerificationRow.checked_dimensions",
            VERIFICATION_DIMENSIONS))
        _require_exact_count(self.checked_dimensions, len(SEVEN_DIMENSIONS),
                             "R5S4VerificationRow.checked_dimensions")
        if set(self.checked_dimensions) != SEVEN_DIMENSIONS:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.checked_dimensions must be exactly the "
                "seven frozen dimensions")
        object.__setattr__(self, "result", _check_closed(
            self.result, "R5S4VerificationRow.result", VERIFICATION_RESULTS))
        object.__setattr__(self, "failure_reason_codes", _freeze_closed_tuple(
            self.failure_reason_codes,
            "R5S4VerificationRow.failure_reason_codes",
            VERIFICATION_FAILURE_CODES))
        object.__setattr__(self, "recomputed", _check_bool(
            self.recomputed, "R5S4VerificationRow.recomputed"))
        if not self.recomputed:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.recomputed must be True")
        if self.result == "passed" and self.failure_reason_codes:
            raise S4RuntimeContractError(
                "R5S4VerificationRow.result=passed carries no failure codes")


@dataclass(frozen=True)
class R5S4AdjudicationRow:
    """Independent adjudication record (present only for N>=2)."""

    present: bool
    binding_id: Optional[str]
    session_id: Optional[str]
    model_id: Optional[str]
    model_version: Optional[str]
    independent_context_hash: Optional[str]
    outcome: Optional[str]
    reviewed_artifact_refs: Tuple[str, ...]
    adds_explanation_only: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "present", _check_bool(
            self.present, "R5S4AdjudicationRow.present"))
        object.__setattr__(self, "reviewed_artifact_refs", _freeze_str_tuple(
            self.reviewed_artifact_refs,
            "R5S4AdjudicationRow.reviewed_artifact_refs"))
        object.__setattr__(self, "adds_explanation_only", _check_bool(
            self.adds_explanation_only, "R5S4AdjudicationRow.adds_explanation_only"))
        if not self.adds_explanation_only:
            raise S4RuntimeContractError(
                "R5S4AdjudicationRow.adds_explanation_only must be True")
        required = ("binding_id", "session_id", "model_id", "model_version",
                    "independent_context_hash", "outcome")
        if self.present:
            for name in required:
                value = getattr(self, name)
                if name == "independent_context_hash":
                    object.__setattr__(
                        self, name, _check_hash(value,
                                                f"R5S4AdjudicationRow.{name}"))
                else:
                    object.__setattr__(self, name, _check_str(
                        value, f"R5S4AdjudicationRow.{name}"))
            object.__setattr__(self, "outcome", _check_closed(
                self.outcome, "R5S4AdjudicationRow.outcome",
                ADJUDICATION_OUTCOMES))
            _require_nonempty_tuple(
                self.reviewed_artifact_refs,
                "R5S4AdjudicationRow.reviewed_artifact_refs")
        else:
            # present=False forbids a real value; None and the empty string
            # are both "absent" (the accepted machine shape uses "" for the
            # str fields and None for independent_context_hash).
            for name in required:
                value = getattr(self, name)
                if value not in (None, ""):
                    raise S4RuntimeContractError(
                        f"R5S4AdjudicationRow.{name} must be absent when "
                        "present=False")
            if self.reviewed_artifact_refs:
                raise S4RuntimeContractError(
                    "R5S4AdjudicationRow.reviewed_artifact_refs must be empty "
                    "when present=False")


@dataclass(frozen=True)
class R5S4QueryDraftRow:
    """Three-part draft-only Query (draft_only always True; structural task
    keys forbidden)."""

    query_draft_id: str
    risk_ref: str
    basis_zh: str
    finding_zh: str
    action_zh: str
    source_locator_refs: Tuple[str, ...]
    pd_wording_state: str
    draft_only: bool

    def __post_init__(self) -> None:
        for name in ("query_draft_id", "basis_zh", "finding_zh", "action_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4QueryDraftRow.{name}"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "R5S4QueryDraftRow.risk_ref"))
        if not is_marker_ref(self.risk_ref):
            raise S4RuntimeContractError(
                f"R5S4QueryDraftRow.risk_ref {self.risk_ref!r} must be a "
                "d09_marker:/d10_marker: marker")
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs, "R5S4QueryDraftRow.source_locator_refs"))
        _require_nonempty_tuple(self.source_locator_refs,
                                "R5S4QueryDraftRow.source_locator_refs")
        object.__setattr__(self, "pd_wording_state", _check_closed(
            self.pd_wording_state, "R5S4QueryDraftRow.pd_wording_state",
            PD_WORDING_STATES))
        object.__setattr__(self, "draft_only", _check_bool(
            self.draft_only, "R5S4QueryDraftRow.draft_only"))
        if not self.draft_only:
            raise S4RuntimeContractError(
                "R5S4QueryDraftRow.draft_only must be True")


@dataclass(frozen=True)
class R5S4JourneyLink:
    """Journey deep-link identity (fallback_policy=none; never nearest
    fallback)."""

    deep_link_project_ref: str
    deep_link_run_ref: str
    deep_link_snapshot_ref: str
    deep_link_cutoff_ref: Optional[str]
    deep_link_site_ref: Optional[str]
    deep_link_subject_ref: Optional[str]
    deep_link_risk_ref: str
    deep_link_event_ref: Optional[str]
    deep_link_visit_ref: Optional[str]
    deep_link_spine_ref: str
    deep_link_anchor_ref: str
    deep_link_source_locator_ref: Optional[str]
    fallback_policy: str
    journey_available: bool
    unavailable_reason_zh: Optional[str]

    def __post_init__(self) -> None:
        for name in ("deep_link_project_ref", "deep_link_run_ref",
                     "deep_link_snapshot_ref", "deep_link_risk_ref",
                     "deep_link_spine_ref", "deep_link_anchor_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4JourneyLink.{name}"))
        for name in ("deep_link_cutoff_ref", "deep_link_site_ref",
                     "deep_link_subject_ref", "deep_link_event_ref",
                     "deep_link_visit_ref", "deep_link_source_locator_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4JourneyLink.{name}"))
        object.__setattr__(self, "fallback_policy", _check_closed(
            self.fallback_policy, "R5S4JourneyLink.fallback_policy",
            FALLBACK_POLICIES))
        if self.fallback_policy != "none":
            raise S4RuntimeContractError(
                "R5S4JourneyLink.fallback_policy must be 'none'")
        object.__setattr__(self, "journey_available", _check_bool(
            self.journey_available, "R5S4JourneyLink.journey_available"))
        object.__setattr__(self, "unavailable_reason_zh", _check_optional_str(
            self.unavailable_reason_zh,
            "R5S4JourneyLink.unavailable_reason_zh"))
        if self.journey_available and self.unavailable_reason_zh is not None:
            raise S4RuntimeContractError(
                "R5S4JourneyLink.unavailable_reason_zh must be None when "
                "journey_available=True")


@dataclass(frozen=True)
class R5S4HistoryEntry:
    """One append-only history entry (hash chain includes prior_entry_hash)."""

    entry_id: str
    seq: int
    kind: str
    payload_ref: str
    prior_entry_hash: str
    entry_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_id", _check_str(
            self.entry_id, "R5S4HistoryEntry.entry_id"))
        object.__setattr__(self, "seq", _check_int(
            self.seq, "R5S4HistoryEntry.seq"))
        if self.seq < 1:
            raise S4RuntimeContractError(
                f"R5S4HistoryEntry.seq must be >= 1, got {self.seq!r}")
        object.__setattr__(self, "kind", _check_closed(
            self.kind, "R5S4HistoryEntry.kind", HISTORY_ENTRY_KINDS))
        object.__setattr__(self, "payload_ref", _check_str(
            self.payload_ref, "R5S4HistoryEntry.payload_ref"))
        prior = _check_str(self.prior_entry_hash,
                           "R5S4HistoryEntry.prior_entry_hash")
        if prior != GENESIS_HASH and not is_sha256_hex(prior):
            raise S4RuntimeContractError(
                f"R5S4HistoryEntry.prior_entry_hash {prior!r} must be "
                f"genesis or a sha256 hex")
        object.__setattr__(self, "prior_entry_hash", prior)
        # entry_hash = canonical sha of every leaf except entry_hash; an
        # empty supplied value is computed (builder/projection-friendly).
        expected = compute_history_entry_hash(self)
        if self.entry_hash:
            object.__setattr__(self, "entry_hash", _check_hash(
                self.entry_hash, "R5S4HistoryEntry.entry_hash"))
            if self.entry_hash != expected:
                raise S4RuntimeContractError(
                    f"R5S4HistoryEntry.entry_hash {self.entry_hash!r} does "
                    f"not match the canonical chain hash {expected!r}")
        else:
            object.__setattr__(self, "entry_hash", expected)


@dataclass(frozen=True)
class R5S4HistoryLog:
    """Append-only history log.  Errata: ``entries`` is ``min_items:0``; only
    ``no_ensemble`` may carry an empty log (``head_seq=0``,
    ``head_hash='genesis'``); single/multi remain ``min_items:1``."""

    history_ref: str
    head_seq: int
    head_hash: str
    entries: Tuple[R5S4HistoryEntry, ...]

    def __post_init__(self) -> None:
        if not matches_grammar(self.history_ref, "history"):
            raise S4RuntimeContractError(
                f"R5S4HistoryLog.history_ref {self.history_ref!r} must match "
                f"history:<ref>")
        object.__setattr__(self, "head_seq", _check_int(
            self.head_seq, "R5S4HistoryLog.head_seq"))
        entries = _freeze_obj_tuple(self.entries, "R5S4HistoryLog.entries",
                                    R5S4HistoryEntry)
        object.__setattr__(self, "entries", entries)
        if not entries:
            # Errata: empty chain requires head_seq=0 and head_hash='genesis'.
            if self.head_seq != 0 or self.head_hash != GENESIS_HASH:
                raise S4RuntimeContractError(
                    "R5S4HistoryLog empty entries requires head_seq=0 and "
                    "head_hash='genesis'")
            return
        seqs = [entry.seq for entry in entries]
        if seqs != list(range(1, len(entries) + 1)):
            raise S4RuntimeContractError(
                "R5S4HistoryLog.entries seq must be strictly 1..len(entries)")
        if entries[0].prior_entry_hash != GENESIS_HASH:
            raise S4RuntimeContractError(
                "R5S4HistoryLog first entry prior_entry_hash must be 'genesis'")
        for index in range(1, len(entries)):
            if entries[index].prior_entry_hash != entries[index - 1].entry_hash:
                raise S4RuntimeContractError(
                    "R5S4HistoryLog entries hash chain broken at seq "
                    f"{entries[index].seq}")
        if self.head_seq != len(entries):
            raise S4RuntimeContractError(
                f"R5S4HistoryLog.head_seq {self.head_seq!r} must equal "
                f"len(entries) {len(entries)}")
        if self.head_hash != entries[-1].entry_hash:
            raise S4RuntimeContractError(
                "R5S4HistoryLog.head_hash must equal the last entry's "
                "entry_hash")


@dataclass(frozen=True)
class R5S4AudienceBaselineRow:
    """One audience-plane baseline row (machine-read-only row_ref separate
    from user-facing item_anchor_zh)."""

    row_ref: str
    item_anchor_zh: str
    ordinal_zh: str
    state_zh: str
    recheck_zh: str

    def __post_init__(self) -> None:
        if not matches_grammar(self.row_ref, "baseline_row"):
            raise S4RuntimeContractError(
                f"R5S4AudienceBaselineRow.row_ref {self.row_ref!r} must "
                f"match baseline-row:<item_id>:<attempt_id>")
        object.__setattr__(self, "item_anchor_zh", _check_str(
            self.item_anchor_zh, "R5S4AudienceBaselineRow.item_anchor_zh"))
        object.__setattr__(self, "ordinal_zh", _check_str(
            self.ordinal_zh, "R5S4AudienceBaselineRow.ordinal_zh"))
        if self.ordinal_zh not in ORDINAL_ZH:
            raise S4RuntimeContractError(
                f"R5S4AudienceBaselineRow.ordinal_zh {self.ordinal_zh!r} "
                f"must be a closed ordinal label")
        object.__setattr__(self, "state_zh", _check_str(
            self.state_zh, "R5S4AudienceBaselineRow.state_zh"))
        object.__setattr__(self, "recheck_zh", _check_str(
            self.recheck_zh, "R5S4AudienceBaselineRow.recheck_zh"))


@dataclass(frozen=True)
class R5S4AudienceWorkerSummary:
    """One worker's audience summary (ordinal-sorted)."""

    ordinal_zh: str
    finding_summary_zh: Tuple[str, ...]
    verification_zh: str
    gap_zh: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordinal_zh", _check_str(
            self.ordinal_zh, "R5S4AudienceWorkerSummary.ordinal_zh"))
        if self.ordinal_zh not in ORDINAL_ZH:
            raise S4RuntimeContractError(
                f"R5S4AudienceWorkerSummary.ordinal_zh {self.ordinal_zh!r} "
                f"must be a closed ordinal label")
        object.__setattr__(self, "finding_summary_zh", _freeze_str_tuple(
            self.finding_summary_zh,
            "R5S4AudienceWorkerSummary.finding_summary_zh"))
        object.__setattr__(self, "gap_zh", _freeze_str_tuple(
            self.gap_zh, "R5S4AudienceWorkerSummary.gap_zh"))
        object.__setattr__(self, "verification_zh", _check_str(
            self.verification_zh,
            "R5S4AudienceWorkerSummary.verification_zh"))


@dataclass(frozen=True)
class R5S4AudienceInspector:
    """The plain-Chinese audience plane (exact keys; no audit leaf)."""

    audience_contract_id: str
    risk_title_zh: str
    domain_zh: str
    severity_zh: str
    change_state_zh: str
    subject_display_zh: str
    center_display_zh: str
    project_display_zh: str
    cutoff_display_zh: str
    basis_zh: str
    support_evidence_zh: Tuple[str, ...]
    counterevidence_zh: Tuple[str, ...]
    source_one_hop_zh: str
    baseline_rows_zh: Tuple[R5S4AudienceBaselineRow, ...]
    worker_ordinal_summaries: Tuple[R5S4AudienceWorkerSummary, ...]
    consensus_zh: str
    adjudication_status_zh: str
    adjudication_explanation_zh: Optional[str]
    query_basis_zh: Optional[str]
    query_finding_zh: Optional[str]
    query_action_zh: Optional[str]
    query_pd_wording_zh: Optional[str]
    history_summary_zh: str
    journey_available: bool
    journey_link_zh: Optional[str]
    journey_unavailable_reason_zh: Optional[str]

    def __post_init__(self) -> None:
        if self.audience_contract_id != AUDIENCE_CONTRACT_ID:
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.audience_contract_id must be "
                f"{AUDIENCE_CONTRACT_ID!r}")
        if self.domain_zh not in DOMAIN_ZH.values():
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.domain_zh {self.domain_zh!r} must be "
                "a closed domain label")
        if self.severity_zh not in SEVERITY_ZH_BY_SEVERITY.values():
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.severity_zh {self.severity_zh!r} "
                "must be a closed severity label")
        for name in ("risk_title_zh", "change_state_zh", "subject_display_zh",
                     "center_display_zh", "project_display_zh",
                     "cutoff_display_zh", "basis_zh", "consensus_zh",
                     "adjudication_status_zh", "history_summary_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4AudienceInspector.{name}"))
        # source_one_hop_zh is a str that MAY be empty: the one-hop summary
        # is "" when no locator is projectable (contract section 6.1:
        # 一跳摘要为空时 ``""``).  It is never null, but empty is legal.
        if not isinstance(self.source_one_hop_zh, str):
            raise S4RuntimeContractError(
                f"R5S4AudienceInspector.source_one_hop_zh must be a str, got "
                f"{type(self.source_one_hop_zh).__name__}")
        object.__setattr__(self, "source_one_hop_zh",
                           unicodedata.normalize("NFC", self.source_one_hop_zh))
        object.__setattr__(self, "support_evidence_zh", _freeze_str_tuple(
            self.support_evidence_zh,
            "R5S4AudienceInspector.support_evidence_zh"))
        object.__setattr__(self, "counterevidence_zh", _freeze_str_tuple(
            self.counterevidence_zh,
            "R5S4AudienceInspector.counterevidence_zh"))
        object.__setattr__(self, "baseline_rows_zh", _freeze_obj_tuple(
            self.baseline_rows_zh, "R5S4AudienceInspector.baseline_rows_zh",
            R5S4AudienceBaselineRow))
        object.__setattr__(self, "worker_ordinal_summaries", _freeze_obj_tuple(
            self.worker_ordinal_summaries,
            "R5S4AudienceInspector.worker_ordinal_summaries",
            R5S4AudienceWorkerSummary))
        object.__setattr__(self, "adjudication_explanation_zh",
                           _check_optional_str(
                               self.adjudication_explanation_zh,
                               "R5S4AudienceInspector.adjudication_explanation_zh"))
        for name in ("query_basis_zh", "query_finding_zh", "query_action_zh",
                     "query_pd_wording_zh"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"R5S4AudienceInspector.{name}"))
        object.__setattr__(self, "journey_available", _check_bool(
            self.journey_available, "R5S4AudienceInspector.journey_available"))
        object.__setattr__(self, "journey_link_zh", _check_optional_str(
            self.journey_link_zh, "R5S4AudienceInspector.journey_link_zh"))
        object.__setattr__(
            self, "journey_unavailable_reason_zh", _check_optional_str(
                self.journey_unavailable_reason_zh,
                "R5S4AudienceInspector.journey_unavailable_reason_zh"))


@dataclass(frozen=True)
class R5S4AuditWorkerRow:
    """One audit-plane worker row (mirror of the root worker view + raw)."""

    attempt_id: str
    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    role: str
    independent_context_hash: str
    input_content_hash: str
    output_artifact_ref: str
    declared_output_hash: str
    raw_bytes_sha256: str
    parsed_output_hash: str

    def __post_init__(self) -> None:
        for name in ("attempt_id", "binding_id", "session_id", "model_id",
                     "model_version", "output_artifact_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4AuditWorkerRow.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4AuditWorkerRow.role", ATTEMPT_ROLES))
        if self.role != "worker":
            raise S4RuntimeContractError(
                "R5S4AuditWorkerRow.role must be 'worker'")
        for name in ("independent_context_hash", "input_content_hash",
                     "declared_output_hash", "raw_bytes_sha256",
                     "parsed_output_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"R5S4AuditWorkerRow.{name}"))


@dataclass(frozen=True)
class R5S4VerificationAuditRow:
    """One audit-plane verification row (recompute trace)."""

    verification_id: str
    attempt_id: str
    checked_dimensions: Tuple[str, ...]
    result: str
    failure_reason_codes: Tuple[str, ...]
    recomputed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "verification_id", _check_str(
            self.verification_id, "R5S4VerificationAuditRow.verification_id"))
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4VerificationAuditRow.attempt_id"))
        object.__setattr__(self, "checked_dimensions", _freeze_closed_tuple(
            self.checked_dimensions,
            "R5S4VerificationAuditRow.checked_dimensions",
            VERIFICATION_DIMENSIONS))
        _require_exact_count(self.checked_dimensions, len(SEVEN_DIMENSIONS),
                             "R5S4VerificationAuditRow.checked_dimensions")
        object.__setattr__(self, "result", _check_closed(
            self.result, "R5S4VerificationAuditRow.result",
            VERIFICATION_RESULTS))
        object.__setattr__(self, "failure_reason_codes", _freeze_closed_tuple(
            self.failure_reason_codes,
            "R5S4VerificationAuditRow.failure_reason_codes",
            VERIFICATION_FAILURE_CODES))
        object.__setattr__(self, "recomputed", _check_bool(
            self.recomputed, "R5S4VerificationAuditRow.recomputed"))
        if not self.recomputed:
            raise S4RuntimeContractError(
                "R5S4VerificationAuditRow.recomputed must be True")


@dataclass(frozen=True)
class R5S4DigestContextView:
    """Audit-plane view of the R4 ``EvidenceDigestContext``."""

    input_content_hash: str
    output_digests: Mapping[str, str]
    evidence_digests: Tuple[str, ...]
    expected_ensemble_identity: str
    artifact_date_windows: Mapping[str, str]
    artifact_unit_contracts: Mapping[str, str]
    artifact_source_versions: Mapping[str, str]
    artifact_model_versions: Mapping[str, str]
    artifact_rule_ids: Mapping[str, str]
    artifact_rule_versions: Mapping[str, str]
    artifact_finding_identities: Mapping[str, Tuple[str, ...]]
    artifact_authorized_source_locators: Mapping[str, Tuple[str, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_content_hash", _check_hash(
            self.input_content_hash,
            "R5S4DigestContextView.input_content_hash"))
        object.__setattr__(self, "expected_ensemble_identity", _check_str(
            self.expected_ensemble_identity,
            "R5S4DigestContextView.expected_ensemble_identity"))
        object.__setattr__(self, "output_digests", self._check_str_sha_map(
            self.output_digests, "output_digests"))
        object.__setattr__(self, "evidence_digests", _freeze_hash_tuple(
            self.evidence_digests, "R5S4DigestContextView.evidence_digests"))
        for name in ("artifact_date_windows", "artifact_unit_contracts",
                     "artifact_source_versions", "artifact_model_versions",
                     "artifact_rule_ids", "artifact_rule_versions"):
            object.__setattr__(self, name, self._check_str_map(
                getattr(self, name), name))
        object.__setattr__(
            self, "artifact_finding_identities",
            self._check_str_strset_map(self.artifact_finding_identities,
                                       "artifact_finding_identities"))
        object.__setattr__(
            self, "artifact_authorized_source_locators",
            self._check_str_strset_map(
                self.artifact_authorized_source_locators,
                "artifact_authorized_source_locators"))

    @staticmethod
    def _check_str_map(value: Any, name: str) -> Mapping[str, str]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _check_str(val, f"R5S4DigestContextView.{name}[]")
        return result

    @classmethod
    def _check_str_sha_map(cls, value: Any, name: str) -> Mapping[str, str]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _check_hash(val, f"R5S4DigestContextView.{name}[]")
        return result

    @staticmethod
    def _check_str_strset_map(value: Any, name: str) -> Mapping[str, Tuple[str, ...]]:
        if not isinstance(value, Mapping):
            raise S4RuntimeContractError(
                f"R5S4DigestContextView.{name} must be a str map")
        result = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key:
                raise S4RuntimeContractError(
                    f"R5S4DigestContextView.{name} key must be non-empty str")
            result[key] = _freeze_str_tuple(val, f"R5S4DigestContextView.{name}[]")
        return result


@dataclass(frozen=True)
class R5S4ModelEvidenceRef:
    """Packet/audit-only D10 ModelEvidence provenance (18 bound fields; never
    on the audience plane)."""

    model_evidence_id: str
    role: str
    permitted_leaf: str
    model_id: str
    model_version: str
    evaluation_content_identity: str
    input_content_hash: str
    source_revision_content_pairs: Tuple["S4SourceRevisionPair", ...]
    source_refs: Tuple[str, ...]
    independent_context_hash: str
    ensemble_id: str
    ensemble_size: int
    member_analysis_refs: Tuple[str, ...]
    member_analysis_ref_set_hash: str
    output_identity: str
    output_hash: str
    adjudication_state: str
    model_binding_hash: str

    def __post_init__(self) -> None:
        for name in ("model_evidence_id", "role", "permitted_leaf", "model_id",
                     "model_version", "evaluation_content_identity",
                     "ensemble_id", "output_identity"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4ModelEvidenceRef.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "R5S4ModelEvidenceRef.role", MODEL_EVIDENCE_ROLES))
        object.__setattr__(self, "adjudication_state", _check_closed(
            self.adjudication_state, "R5S4ModelEvidenceRef.adjudication_state",
            MODEL_EVIDENCE_ADJUDICATION_STATES))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "R5S4ModelEvidenceRef.ensemble_size"))
        if self.ensemble_size < 1:
            raise S4RuntimeContractError(
                "R5S4ModelEvidenceRef.ensemble_size must be >= 1")
        for name in ("input_content_hash", "independent_context_hash",
                     "member_analysis_ref_set_hash", "output_hash",
                     "model_binding_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"R5S4ModelEvidenceRef.{name}"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "R5S4ModelEvidenceRef.source_revision_content_pairs",
                               S4SourceRevisionPair))
        object.__setattr__(self, "source_refs", _freeze_str_tuple(
            self.source_refs, "R5S4ModelEvidenceRef.source_refs"))
        object.__setattr__(self, "member_analysis_refs", _freeze_str_tuple(
            self.member_analysis_refs,
            "R5S4ModelEvidenceRef.member_analysis_refs"))


@dataclass(frozen=True)
class R5S4AuditInspector:
    """The audit plane (private; excludes packet_fingerprints from its own
    content hash)."""

    authority_receipt_ref: str
    receipt_content_hash: str
    digest_context: Optional[R5S4DigestContextView]
    worker_audit_rows: Tuple[R5S4AuditWorkerRow, ...]
    verification_audit_rows: Tuple[R5S4VerificationAuditRow, ...]
    adjudication_audit: Tuple[str, ...]
    conflict_audit: Tuple[str, ...]
    history_audit: Tuple[str, ...]
    model_evidence: Optional[R5S4ModelEvidenceRef]
    packet_fingerprints: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not matches_grammar(self.authority_receipt_ref, "receipt"):
            raise S4RuntimeContractError(
                f"R5S4AuditInspector.authority_receipt_ref "
                f"{self.authority_receipt_ref!r} must match receipt:<sha256>")
        object.__setattr__(self, "receipt_content_hash", _check_hash(
            self.receipt_content_hash,
            "R5S4AuditInspector.receipt_content_hash"))
        if self.digest_context is not None:
            _check_obj_type(self.digest_context, R5S4DigestContextView,
                            "R5S4AuditInspector.digest_context")
        object.__setattr__(self, "worker_audit_rows", _freeze_obj_tuple(
            self.worker_audit_rows, "R5S4AuditInspector.worker_audit_rows",
            R5S4AuditWorkerRow))
        object.__setattr__(self, "verification_audit_rows", _freeze_obj_tuple(
            self.verification_audit_rows,
            "R5S4AuditInspector.verification_audit_rows",
            R5S4VerificationAuditRow))
        for name in ("adjudication_audit", "conflict_audit", "history_audit"):
            object.__setattr__(self, name, _freeze_str_tuple(
                getattr(self, name), f"R5S4AuditInspector.{name}"))
        if self.model_evidence is not None:
            _check_obj_type(self.model_evidence, R5S4ModelEvidenceRef,
                            "R5S4AuditInspector.model_evidence")
        object.__setattr__(self, "packet_fingerprints", _freeze_str_tuple(
            self.packet_fingerprints, "R5S4AuditInspector.packet_fingerprints"))
        _require_min_count(self.packet_fingerprints, 4,
                           "R5S4AuditInspector.packet_fingerprints")


@dataclass(frozen=True)
class R5S4AuthorityPacket:
    """The root packet (six-node acyclic hash DAG; no root content hash)."""

    packet_id: str
    schema: str
    status: str
    authority_mode: str
    authority_anchor_ref: str
    anchor_identity_hash: str
    ensemble_projection_state: str
    ensemble_id: str
    ensemble_size: int
    input_content_hash: Optional[str]
    risk_identity: R5S4RiskIdentity
    authority_receipt: R5AuthorityReceipt
    receipt_content_hash: str
    baseline_items: Tuple[R5S4BaselineItemProjection, ...]
    baseline_rows: Tuple[R5S4BaselineRow, ...]
    worker_views: Tuple[R5S4WorkerView, ...]
    raw_artifacts: Tuple[R5S4RawOutputArtifact, ...]
    verification_rows: Tuple[R5S4VerificationRow, ...]
    conflict_rows: Tuple[R5S4ConflictRow, ...]
    adjudication_row: R5S4AdjudicationRow
    query_draft_row: Optional[R5S4QueryDraftRow]
    journey_link: R5S4JourneyLink
    history_log: R5S4HistoryLog
    audience_inspector: R5S4AudienceInspector
    audit_inspector: R5S4AuditInspector
    audience_content_hash: str
    audit_content_hash: str
    packet_integrity_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "packet_id", _check_str(
            self.packet_id, "R5S4AuthorityPacket.packet_id"))
        if not matches_grammar(self.packet_id, "packet_id"):
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.packet_id {self.packet_id!r} must match "
                f"r5-s4-contract:<audience_content_hash>")
        if self.schema != S4_PACKET_SCHEMA_ID:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.schema must be {S4_PACKET_SCHEMA_ID!r}")
        if self.status != S4_STATUS:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.status must be {S4_STATUS!r}")
        if self.authority_mode != S4_AUTHORITY_MODE:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.authority_mode must be "
                f"{S4_AUTHORITY_MODE!r}")
        if not matches_grammar(self.authority_anchor_ref, "anchor"):
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.authority_anchor_ref "
                f"{self.authority_anchor_ref!r} must match anchor:<sha256>")
        object.__setattr__(self, "anchor_identity_hash", _check_hash(
            self.anchor_identity_hash,
            "R5S4AuthorityPacket.anchor_identity_hash"))
        object.__setattr__(self, "ensemble_projection_state", _check_closed(
            self.ensemble_projection_state,
            "R5S4AuthorityPacket.ensemble_projection_state",
            ENSEMBLE_PROJECTION_STATES))
        object.__setattr__(self, "ensemble_id", _check_str(
            self.ensemble_id, "R5S4AuthorityPacket.ensemble_id"))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "R5S4AuthorityPacket.ensemble_size"))
        state = self.ensemble_projection_state
        if state == "no_ensemble":
            if self.ensemble_size != 0:
                raise S4RuntimeContractError(
                    "no_ensemble requires ensemble_size=0")
            if self.input_content_hash is not None:
                raise S4RuntimeContractError(
                    "no_ensemble forbids input_content_hash")
        else:
            if self.ensemble_size < 1:
                raise S4RuntimeContractError(
                    f"{state} requires ensemble_size >= 1")
            object.__setattr__(self, "input_content_hash", _check_hash(
                self.input_content_hash,
                "R5S4AuthorityPacket.input_content_hash"))
        _check_obj_type(self.risk_identity, R5S4RiskIdentity,
                        "R5S4AuthorityPacket.risk_identity")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4AuthorityPacket.authority_receipt")
        object.__setattr__(self, "receipt_content_hash", _check_hash(
            self.receipt_content_hash,
            "R5S4AuthorityPacket.receipt_content_hash"))
        object.__setattr__(self, "baseline_items", _freeze_obj_tuple(
            self.baseline_items, "R5S4AuthorityPacket.baseline_items",
            R5S4BaselineItemProjection))
        object.__setattr__(self, "baseline_rows", _freeze_obj_tuple(
            self.baseline_rows, "R5S4AuthorityPacket.baseline_rows",
            R5S4BaselineRow))
        object.__setattr__(self, "worker_views", _freeze_obj_tuple(
            self.worker_views, "R5S4AuthorityPacket.worker_views",
            R5S4WorkerView))
        object.__setattr__(self, "raw_artifacts", _freeze_obj_tuple(
            self.raw_artifacts, "R5S4AuthorityPacket.raw_artifacts",
            R5S4RawOutputArtifact))
        object.__setattr__(self, "verification_rows", _freeze_obj_tuple(
            self.verification_rows, "R5S4AuthorityPacket.verification_rows",
            R5S4VerificationRow))
        object.__setattr__(self, "conflict_rows", _freeze_obj_tuple(
            self.conflict_rows, "R5S4AuthorityPacket.conflict_rows",
            R5S4ConflictRow))
        _check_obj_type(self.adjudication_row, R5S4AdjudicationRow,
                        "R5S4AuthorityPacket.adjudication_row")
        if self.query_draft_row is not None:
            _check_obj_type(self.query_draft_row, R5S4QueryDraftRow,
                            "R5S4AuthorityPacket.query_draft_row")
        _check_obj_type(self.journey_link, R5S4JourneyLink,
                        "R5S4AuthorityPacket.journey_link")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4AuthorityPacket.history_log")
        _check_obj_type(self.audience_inspector, R5S4AudienceInspector,
                        "R5S4AuthorityPacket.audience_inspector")
        _check_obj_type(self.audit_inspector, R5S4AuditInspector,
                        "R5S4AuthorityPacket.audit_inspector")
        object.__setattr__(self, "audience_content_hash", _check_hash(
            self.audience_content_hash,
            "R5S4AuthorityPacket.audience_content_hash"))
        object.__setattr__(self, "audit_content_hash", _check_hash(
            self.audit_content_hash, "R5S4AuthorityPacket.audit_content_hash"))
        object.__setattr__(self, "packet_integrity_hash", _check_hash(
            self.packet_integrity_hash,
            "R5S4AuthorityPacket.packet_integrity_hash"))
        # Six-node acyclic hash DAG (each node rebuilt; none includes itself).
        if self.audience_content_hash != audience_content_hash_of(
                self.audience_inspector):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.audience_content_hash does not match "
                "canonical(audience_inspector)")
        if self.audit_content_hash != audit_content_hash_of(self.audit_inspector):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.audit_content_hash does not match "
                "canonical(audit_inspector excluding packet_fingerprints)")
        if self.receipt_content_hash != receipt_content_hash_of(
                self.authority_receipt):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.receipt_content_hash does not match "
                "canonical(authority_receipt)")
        expected_pid = compute_packet_id(self.audience_content_hash)
        if self.packet_id != expected_pid:
            raise S4RuntimeContractError(
                f"R5S4AuthorityPacket.packet_id {self.packet_id!r} must be "
                f"{expected_pid!r}")
        expected_fps = compute_packet_fingerprints(
            self.audience_content_hash, self.receipt_content_hash,
            self.packet_id, self.risk_identity.risk_identity_hash)
        if self.audit_inspector.packet_fingerprints != expected_fps:
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket audit packet_fingerprints do not match "
                "the frozen recipe")
        if self.packet_integrity_hash != compute_packet_integrity_hash(
                packet_as_mapping(self)):
            raise S4RuntimeContractError(
                "R5S4AuthorityPacket.packet_integrity_hash does not match the "
                "canonical integrity body")


def packet_as_mapping(packet: "R5S4AuthorityPacket") -> Dict[str, Any]:
    """Canonical plain-dict projection of a packet (asdict of every field)."""
    return {field.name: _to_plain(getattr(packet, field.name))
            for field in fields(packet)}


# ---------------------------------------------------------------------------
# External accepted-authority anchor typed objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class S4AcceptedHistoryState:
    """One accepted per-state history anchor.

    Errata: ``hash`` is ``genesis_or_sha`` -- only ``seq=0`` and
    ``head='genesis'`` allow ``hash='genesis'``; every other state must be a
    SHA-256.
    """

    seq: int
    head: str
    hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_int(
            self.seq, "S4AcceptedHistoryState.seq"))
        if self.seq < 0:
            raise S4RuntimeContractError(
                f"S4AcceptedHistoryState.seq must be >= 0, got {self.seq!r}")
        object.__setattr__(self, "head", _check_str(
            self.head, "S4AcceptedHistoryState.head"))
        if self.seq == 0 and self.head == GENESIS_HASH:
            if self.hash != GENESIS_HASH:
                raise S4RuntimeContractError(
                    "S4AcceptedHistoryState.hash must be 'genesis' when "
                    "seq=0 and head='genesis'")
        else:
            if not is_sha256_hex(self.hash):
                raise S4RuntimeContractError(
                    f"S4AcceptedHistoryState.hash {self.hash!r} must be a "
                    "sha256 hex for seq>0")


@dataclass(frozen=True)
class S4SourceRevisionPair:
    """One source revision -> content hash binding (packet/audit)."""

    revision_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", _check_str(
            self.revision_id, "S4SourceRevisionPair.revision_id"))
        object.__setattr__(self, "content_hash", _check_hash(
            self.content_hash, "S4SourceRevisionPair.content_hash"))


@dataclass(frozen=True)
class S4AcceptedAdjudicatorBinding:
    """Externally accepted adjudication binding identity."""

    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    outcome: str
    independent_context_hash: str

    def __post_init__(self) -> None:
        for name in ("binding_id", "session_id", "model_id", "model_version"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedAdjudicatorBinding.{name}"))
        object.__setattr__(self, "outcome", _check_closed(
            self.outcome, "S4AcceptedAdjudicatorBinding.outcome",
            ADJUDICATION_OUTCOMES))
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "S4AcceptedAdjudicatorBinding.independent_context_hash"))


@dataclass(frozen=True)
class S4AcceptedBaselineItem:
    """Externally accepted reference-baseline item (never packet-defined)."""

    item_id: str
    source_kind: str
    source_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    claimed_identity: str
    temporal_window: str
    claimed_content_hash: str
    origin_artifact_hash: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    source_revision: str

    def __post_init__(self) -> None:
        for name in ("item_id", "source_kind", "source_revision_id",
                     "snapshot_id", "claimed_identity", "temporal_window",
                     "project_ref", "run_ref", "snapshot_ref",
                     "source_revision"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedBaselineItem.{name}"))
        object.__setattr__(self, "source_locator_ids", _freeze_str_tuple(
            self.source_locator_ids, "S4AcceptedBaselineItem.source_locator_ids"))
        _require_nonempty_tuple(self.source_locator_ids,
                                "S4AcceptedBaselineItem.source_locator_ids")
        object.__setattr__(self, "claimed_content_hash", _check_hash(
            self.claimed_content_hash,
            "S4AcceptedBaselineItem.claimed_content_hash"))
        object.__setattr__(self, "origin_artifact_hash", _check_hash(
            self.origin_artifact_hash,
            "S4AcceptedBaselineItem.origin_artifact_hash"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "S4AcceptedBaselineItem.cutoff_ref"))


@dataclass(frozen=True)
class S4AcceptedQueryDraft:
    """Externally accepted three-part draft-only Query."""

    query_draft_id: str
    risk_ref: str
    basis_zh: str
    finding_zh: str
    action_zh: str
    source_locator_refs: Tuple[str, ...]
    pd_wording_state: str
    content_hash: str
    draft_only: bool

    def __post_init__(self) -> None:
        for name in ("query_draft_id", "basis_zh", "finding_zh", "action_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedQueryDraft.{name}"))
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "S4AcceptedQueryDraft.risk_ref"))
        if not is_marker_ref(self.risk_ref):
            raise S4RuntimeContractError(
                f"S4AcceptedQueryDraft.risk_ref {self.risk_ref!r} must be a "
                "marker")
        object.__setattr__(self, "source_locator_refs", _freeze_str_tuple(
            self.source_locator_refs,
            "S4AcceptedQueryDraft.source_locator_refs"))
        _require_nonempty_tuple(self.source_locator_refs,
                                "S4AcceptedQueryDraft.source_locator_refs")
        object.__setattr__(self, "pd_wording_state", _check_closed(
            self.pd_wording_state, "S4AcceptedQueryDraft.pd_wording_state",
            PD_WORDING_STATES))
        object.__setattr__(self, "content_hash", _check_hash(
            self.content_hash, "S4AcceptedQueryDraft.content_hash"))
        object.__setattr__(self, "draft_only", _check_bool(
            self.draft_only, "S4AcceptedQueryDraft.draft_only"))
        if not self.draft_only:
            raise S4RuntimeContractError(
                "S4AcceptedQueryDraft.draft_only must be True")


@dataclass(frozen=True)
class S4AcceptedRiskIdentity:
    """Externally accepted R5 risk-identity instance (authoritative)."""

    risk_ref: str
    risk_identity_hash: str
    domain: str
    domain_zh: str
    monitoring_priority: str
    severity: str
    severity_zh: str
    change_kind: str
    change_cause: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    spine_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_ref", _check_str(
            self.risk_ref, "S4AcceptedRiskIdentity.risk_ref"))
        object.__setattr__(self, "risk_identity_hash", _check_hash(
            self.risk_identity_hash, "S4AcceptedRiskIdentity.risk_identity_hash"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "S4AcceptedRiskIdentity.domain", DOMAINS))
        object.__setattr__(self, "monitoring_priority", _check_closed(
            self.monitoring_priority,
            "S4AcceptedRiskIdentity.monitoring_priority", MONITORING_PRIORITIES))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "S4AcceptedRiskIdentity.severity", SEVERITIES))
        object.__setattr__(self, "change_kind", _check_closed(
            self.change_kind, "S4AcceptedRiskIdentity.change_kind", CHANGE_KINDS))
        object.__setattr__(self, "change_cause", _check_closed(
            self.change_cause, "S4AcceptedRiskIdentity.change_cause", CHANGE_CAUSES))
        for name in ("project_ref", "run_ref", "snapshot_ref", "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedRiskIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4AcceptedRiskIdentity.{name}"))
        if self.domain_zh != DOMAIN_ZH[self.domain]:
            raise S4RuntimeContractError(
                f"S4AcceptedRiskIdentity.domain_zh {self.domain_zh!r} must be "
                f"the closed projection of domain {self.domain!r}")
        if self.severity_zh != SEVERITY_ZH_BY_SEVERITY[self.severity]:
            raise S4RuntimeContractError(
                f"S4AcceptedRiskIdentity.severity_zh {self.severity_zh!r} "
                f"must be the closed projection of severity {self.severity!r}")


@dataclass(frozen=True)
class S4AttemptAuthorityRow:
    """One accepted per-attempt authority row (input/content/rule binding)."""

    attempt_id: str
    model_id: str
    model_version: str
    input_content_hash: str
    artifact_ref: str
    parsed_output_hash: str
    raw_bytes_sha256: str
    date_window: str
    unit_contract: str
    source_revision: str
    rule_id: str
    rule_version: str

    def __post_init__(self) -> None:
        for name in ("attempt_id", "model_id", "model_version", "artifact_ref",
                     "date_window", "unit_contract", "source_revision",
                     "rule_id", "rule_version"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AttemptAuthorityRow.{name}"))
        for name in ("input_content_hash", "parsed_output_hash",
                     "raw_bytes_sha256"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"S4AttemptAuthorityRow.{name}"))


@dataclass(frozen=True)
class S4JourneyTargetIdentity:
    """Accepted Journey target identity (full project/run/snapshot/cutoff/
    site/subject/risk/event/visit/spine/anchor/source)."""

    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    risk_ref: str
    event_ref: Optional[str]
    visit_ref: Optional[str]
    spine_ref: str
    anchor_ref: str
    source_locator_ref: Optional[str]

    def __post_init__(self) -> None:
        for name in ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                     "spine_ref", "anchor_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4JourneyTargetIdentity.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref", "event_ref",
                     "visit_ref", "source_locator_ref"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4JourneyTargetIdentity.{name}"))


@dataclass(frozen=True)
class S4ModelEvidencePermit:
    """Externally accepted D10 ModelEvidence permit (covers all 18 upstream
    fields)."""

    model_evidence_id: str
    role: str
    permitted_leaf: str
    model_id: str
    model_version: str
    evaluation_content_identity: str
    input_content_hash: str
    source_revision_content_pairs: Tuple[S4SourceRevisionPair, ...]
    source_refs: Tuple[str, ...]
    independent_context_hash: str
    ensemble_id: str
    ensemble_size: int
    member_analysis_refs: Tuple[str, ...]
    member_analysis_ref_set_hash: str
    output_identity: str
    output_hash: str
    adjudication_state: str
    model_binding_hash: str

    def __post_init__(self) -> None:
        for name in ("model_evidence_id", "role", "permitted_leaf", "model_id",
                     "model_version", "evaluation_content_identity",
                     "ensemble_id", "output_identity"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4ModelEvidencePermit.{name}"))
        object.__setattr__(self, "role", _check_closed(
            self.role, "S4ModelEvidencePermit.role", MODEL_EVIDENCE_ROLES))
        object.__setattr__(self, "adjudication_state", _check_closed(
            self.adjudication_state,
            "S4ModelEvidencePermit.adjudication_state",
            MODEL_EVIDENCE_ADJUDICATION_STATES))
        object.__setattr__(self, "ensemble_size", _check_int(
            self.ensemble_size, "S4ModelEvidencePermit.ensemble_size"))
        if self.ensemble_size < 1:
            raise S4RuntimeContractError(
                "S4ModelEvidencePermit.ensemble_size must be >= 1")
        for name in ("input_content_hash", "independent_context_hash",
                     "member_analysis_ref_set_hash", "output_hash",
                     "model_binding_hash"):
            object.__setattr__(self, name, _check_hash(
                getattr(self, name), f"S4ModelEvidencePermit.{name}"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_obj_tuple(
                               self.source_revision_content_pairs,
                               "S4ModelEvidencePermit.source_revision_content_pairs",
                               S4SourceRevisionPair))
        object.__setattr__(self, "source_refs", _freeze_str_tuple(
            self.source_refs, "S4ModelEvidencePermit.source_refs"))
        object.__setattr__(self, "member_analysis_refs", _freeze_str_tuple(
            self.member_analysis_refs,
            "S4ModelEvidencePermit.member_analysis_refs"))


@dataclass(frozen=True)
class S4AcceptedAuthorityAnchor:
    """The external accepted-authority anchor (separate input; never packet-
    defined truth).  ``anchor_identity_hash`` is the R4-style canonical self
    hash excluding itself."""

    schema: str
    status: str
    authority_mode: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_ref: Optional[str]
    subject_ref: Optional[str]
    risk_ref: str
    spine_ref: str
    risk_priority_authority: str
    severity_authority: str
    critical_severity_authority: Optional[str]
    accepted_receipt_content_hash: str
    accepted_receipt_identity: str
    accepted_risk_identity_hash: str
    accepted_risk_identity: S4AcceptedRiskIdentity
    accepted_adjudicator_binding: S4AcceptedAdjudicatorBinding
    accepted_baseline_items: Tuple[S4AcceptedBaselineItem, ...]
    accepted_query_draft: Optional[S4AcceptedQueryDraft]
    accepted_journey_target: S4JourneyTargetIdentity
    accepted_history_no_ensemble: S4AcceptedHistoryState
    accepted_history_single_analysis: S4AcceptedHistoryState
    accepted_history_multi_analysis: S4AcceptedHistoryState
    attempt_authority_rows: Tuple[S4AttemptAuthorityRow, ...]
    model_evidence_permits: Tuple[S4ModelEvidencePermit, ...]
    anchor_identity_hash: str

    def __post_init__(self) -> None:
        if self.schema != "medical-monitoring-r5-s4-authority-anchor-v0.1":
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor.schema must be "
                "medical-monitoring-r5-s4-authority-anchor-v0.1")
        if self.status != S4_STATUS:
            raise S4RuntimeContractError(
                f"S4AcceptedAuthorityAnchor.status must be {S4_STATUS!r}")
        if self.authority_mode != S4_AUTHORITY_MODE:
            raise S4RuntimeContractError(
                f"S4AcceptedAuthorityAnchor.authority_mode must be "
                f"{S4_AUTHORITY_MODE!r}")
        for name in ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                     "spine_ref"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"S4AcceptedAuthorityAnchor.{name}"))
        for name in ("cutoff_ref", "site_ref", "subject_ref",
                     "critical_severity_authority"):
            object.__setattr__(self, name, _check_optional_str(
                getattr(self, name), f"S4AcceptedAuthorityAnchor.{name}"))
        object.__setattr__(self, "risk_priority_authority", _check_closed(
            self.risk_priority_authority,
            "S4AcceptedAuthorityAnchor.risk_priority_authority",
            MONITORING_PRIORITIES))
        object.__setattr__(self, "severity_authority", _check_closed(
            self.severity_authority,
            "S4AcceptedAuthorityAnchor.severity_authority", SEVERITIES))
        if self.severity_authority == "critical" and \
                not self.critical_severity_authority:
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor requires critical_severity_authority "
                "when severity_authority is critical")
        object.__setattr__(self, "accepted_receipt_content_hash", _check_hash(
            self.accepted_receipt_content_hash,
            "S4AcceptedAuthorityAnchor.accepted_receipt_content_hash"))
        object.__setattr__(self, "accepted_receipt_identity", _check_str(
            self.accepted_receipt_identity,
            "S4AcceptedAuthorityAnchor.accepted_receipt_identity"))
        object.__setattr__(self, "accepted_risk_identity_hash", _check_hash(
            self.accepted_risk_identity_hash,
            "S4AcceptedAuthorityAnchor.accepted_risk_identity_hash"))
        _check_obj_type(self.accepted_risk_identity, S4AcceptedRiskIdentity,
                        "S4AcceptedAuthorityAnchor.accepted_risk_identity")
        _check_obj_type(self.accepted_adjudicator_binding,
                        S4AcceptedAdjudicatorBinding,
                        "S4AcceptedAuthorityAnchor.accepted_adjudicator_binding")
        object.__setattr__(self, "accepted_baseline_items", _freeze_obj_tuple(
            self.accepted_baseline_items,
            "S4AcceptedAuthorityAnchor.accepted_baseline_items",
            S4AcceptedBaselineItem))
        if self.accepted_query_draft is not None:
            _check_obj_type(self.accepted_query_draft, S4AcceptedQueryDraft,
                            "S4AcceptedAuthorityAnchor.accepted_query_draft")
        _check_obj_type(self.accepted_journey_target, S4JourneyTargetIdentity,
                        "S4AcceptedAuthorityAnchor.accepted_journey_target")
        for state_name in ("accepted_history_no_ensemble",
                           "accepted_history_single_analysis",
                           "accepted_history_multi_analysis"):
            _check_obj_type(getattr(self, state_name), S4AcceptedHistoryState,
                            f"S4AcceptedAuthorityAnchor.{state_name}")
        object.__setattr__(self, "attempt_authority_rows", _freeze_obj_tuple(
            self.attempt_authority_rows,
            "S4AcceptedAuthorityAnchor.attempt_authority_rows",
            S4AttemptAuthorityRow))
        object.__setattr__(self, "model_evidence_permits", _freeze_obj_tuple(
            self.model_evidence_permits,
            "S4AcceptedAuthorityAnchor.model_evidence_permits",
            S4ModelEvidencePermit))
        object.__setattr__(self, "anchor_identity_hash", _check_hash(
            self.anchor_identity_hash,
            "S4AcceptedAuthorityAnchor.anchor_identity_hash"))
        body = packet_as_mapping(self)
        if self.anchor_identity_hash != compute_anchor_identity_hash(body):
            raise S4RuntimeContractError(
                "S4AcceptedAuthorityAnchor.anchor_identity_hash does not "
                "match the canonical self hash (excluding itself)")


# ---------------------------------------------------------------------------
# Runtime-only wrappers (typed runtime input / build state)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S4RawOutputInput:
    """Raw-byte input (attempt + artifact identity, format, injected bytes)."""

    attempt_id: str
    artifact_id: str
    raw_format: str
    raw_bytes: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _check_str(
            self.attempt_id, "R5S4RawOutputInput.attempt_id"))
        object.__setattr__(self, "artifact_id", _check_str(
            self.artifact_id, "R5S4RawOutputInput.artifact_id"))
        object.__setattr__(self, "raw_format", _check_closed(
            self.raw_format, "R5S4RawOutputInput.raw_format",
            RAW_OUTPUT_FORMATS))
        if not isinstance(self.raw_bytes, bytes):
            raise S4RuntimeContractError(
                "R5S4RawOutputInput.raw_bytes must be bytes")


@dataclass(frozen=True)
class R5S4AdjudicatorInput:
    """Runtime-only adjudicator wrapper: the R4 binding plus the S4 sealed
    independent context hash."""

    binding: AdjudicationBinding
    independent_context_hash: str

    def __post_init__(self) -> None:
        _check_obj_type(self.binding, AdjudicationBinding,
                        "R5S4AdjudicatorInput.binding")
        object.__setattr__(self, "independent_context_hash", _check_hash(
            self.independent_context_hash,
            "R5S4AdjudicatorInput.independent_context_hash"))


@dataclass(frozen=True)
class R5S4SyntheticAudienceLabels:
    """Synthetic/offline display labels.  These affect display text only and
    never risk identity/domain/severity/verification/conflict/adjudication/
    Query/authority/hash semantics."""

    risk_title_zh: str
    project_display_zh: str
    center_display_zh: str
    subject_display_zh: str
    cutoff_display_zh: str

    def __post_init__(self) -> None:
        for name in ("risk_title_zh", "project_display_zh", "center_display_zh",
                     "subject_display_zh", "cutoff_display_zh"):
            object.__setattr__(self, name, _check_str(
                getattr(self, name), f"R5S4SyntheticAudienceLabels.{name}"))


@dataclass(frozen=True)
class R5S4SourceInput:
    """Runtime-only source input.

    ``locatable`` must carry a non-null resolution and a null reason;
    ``unavailable`` must carry a null resolution and a non-null closed reason.
    No third combination is allowed.
    """

    availability_state: str
    resolution: Optional[R5S2SourceResolution]
    unavailable_reason: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "availability_state", _check_closed(
            self.availability_state, "R5S4SourceInput.availability_state",
            SOURCE_AVAILABILITY_STATES))
        if self.resolution is not None:
            _check_obj_type(self.resolution, R5S2SourceResolution,
                            "R5S4SourceInput.resolution")
        object.__setattr__(self, "unavailable_reason", _check_optional_str(
            self.unavailable_reason, "R5S4SourceInput.unavailable_reason"))
        if self.availability_state == "locatable":
            if self.resolution is None or self.unavailable_reason is not None:
                raise S4RuntimeContractError(
                    "locatable requires non-null resolution and null "
                    "unavailable_reason")
        else:  # unavailable
            if self.resolution is not None or \
                    self.unavailable_reason is None or \
                    self.unavailable_reason not in UNAVAILABLE_REASONS:
                raise S4RuntimeContractError(
                    "unavailable requires null resolution and a closed "
                    "unavailable_reason")


def validate_source_input_shape(source_input: "R5S4SourceInput") -> None:
    """Explicit shape gate for the runtime source input (fail closed on the
    third combination)."""
    if source_input.availability_state == "locatable":
        if source_input.resolution is None or \
                source_input.unavailable_reason is not None:
            raise S4RuntimeContractError(
                "R5S4SourceInput locatable requires resolution and no reason")
    elif source_input.availability_state == "unavailable":
        if source_input.resolution is not None or \
                source_input.unavailable_reason is None or \
                source_input.unavailable_reason not in UNAVAILABLE_REASONS:
            raise S4RuntimeContractError(
                "R5S4SourceInput unavailable requires reason and no resolution")
    else:
        raise S4RuntimeContractError(
            f"unknown availability_state {source_input.availability_state!r}")


@dataclass(frozen=True)
class R5S4RuntimeInput:
    """The single legal runtime input: typed external anchor + R4/R5 public
    typed objects + raw bytes + accepted history + synthetic labels."""

    anchor: S4AcceptedAuthorityAnchor
    authority_receipt: R5AuthorityReceipt
    upstream_inspector: R5RiskInspectorProjection
    change_band: R5ChangeBand
    deep_link_state: R5DeepLinkState
    source_input: R5S4SourceInput
    attempts: Tuple[AnalysisAttempt, ...]
    worker_outputs: Tuple[WorkerAnalysisOutput, ...]
    raw_outputs: Tuple[R5S4RawOutputInput, ...]
    baseline_items: Tuple[ReferenceBaselineItem, ...]
    digest_context: Optional[EvidenceDigestContext]
    adjudicator: Optional[R5S4AdjudicatorInput]
    model_evidence: Optional[ModelEvidence]
    query_draft: Optional[D10QueryDraft]
    history_log: R5S4HistoryLog
    audience_labels: R5S4SyntheticAudienceLabels

    def __post_init__(self) -> None:
        _check_obj_type(self.anchor, S4AcceptedAuthorityAnchor,
                        "R5S4RuntimeInput.anchor")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4RuntimeInput.authority_receipt")
        _check_obj_type(self.upstream_inspector, R5RiskInspectorProjection,
                        "R5S4RuntimeInput.upstream_inspector")
        _check_obj_type(self.change_band, R5ChangeBand,
                        "R5S4RuntimeInput.change_band")
        _check_obj_type(self.deep_link_state, R5DeepLinkState,
                        "R5S4RuntimeInput.deep_link_state")
        _check_obj_type(self.source_input, R5S4SourceInput,
                        "R5S4RuntimeInput.source_input")
        object.__setattr__(self, "attempts", _freeze_obj_tuple(
            self.attempts, "R5S4RuntimeInput.attempts", AnalysisAttempt))
        object.__setattr__(self, "worker_outputs", _freeze_obj_tuple(
            self.worker_outputs, "R5S4RuntimeInput.worker_outputs",
            WorkerAnalysisOutput))
        object.__setattr__(self, "raw_outputs", _freeze_obj_tuple(
            self.raw_outputs, "R5S4RuntimeInput.raw_outputs",
            R5S4RawOutputInput))
        object.__setattr__(self, "baseline_items", _freeze_obj_tuple(
            self.baseline_items, "R5S4RuntimeInput.baseline_items",
            ReferenceBaselineItem))
        if self.digest_context is not None:
            _check_obj_type(self.digest_context, EvidenceDigestContext,
                            "R5S4RuntimeInput.digest_context")
        if self.adjudicator is not None:
            _check_obj_type(self.adjudicator, R5S4AdjudicatorInput,
                            "R5S4RuntimeInput.adjudicator")
        if self.model_evidence is not None:
            _check_obj_type(self.model_evidence, ModelEvidence,
                            "R5S4RuntimeInput.model_evidence")
        if self.query_draft is not None:
            _check_obj_type(self.query_draft, D10QueryDraft,
                            "R5S4RuntimeInput.query_draft")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4RuntimeInput.history_log")
        _check_obj_type(self.audience_labels, R5S4SyntheticAudienceLabels,
                        "R5S4RuntimeInput.audience_labels")
        validate_source_input_shape(self.source_input)


@dataclass(frozen=True)
class R5S4BuildState:
    """Internal immutable build state produced by the builder and consumed by
    the projector/validator.  It never stores a candidate audience, audit or
    candidate hash; every repeated field is a tuple."""

    anchor: S4AcceptedAuthorityAnchor
    authority_receipt: R5AuthorityReceipt
    upstream_inspector: R5RiskInspectorProjection
    change_band: R5ChangeBand
    deep_link_state: R5DeepLinkState
    source_input: R5S4SourceInput
    risk_identity: R5S4RiskIdentity
    ensemble_id: str
    ensemble_projection_state: str
    input_content_hash: Optional[str]
    attempts: Tuple[AnalysisAttempt, ...]
    worker_outputs: Tuple[WorkerAnalysisOutput, ...]
    worker_views: Tuple[R5S4WorkerView, ...]
    raw_artifacts: Tuple[R5S4RawOutputArtifact, ...]
    baseline_items: Tuple[R5S4BaselineItemProjection, ...]
    baseline_rows: Tuple[R5S4BaselineRow, ...]
    verification_rows: Tuple[R5S4VerificationRow, ...]
    conflict_rows: Tuple[R5S4ConflictRow, ...]
    adjudication_row: R5S4AdjudicationRow
    query_draft_row: Optional[R5S4QueryDraftRow]
    journey_link: R5S4JourneyLink
    history_log: R5S4HistoryLog
    digest_context: Optional[EvidenceDigestContext]
    model_evidence: Optional[ModelEvidence]
    audience_labels: R5S4SyntheticAudienceLabels

    def __post_init__(self) -> None:
        _check_obj_type(self.anchor, S4AcceptedAuthorityAnchor,
                        "R5S4BuildState.anchor")
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S4BuildState.authority_receipt")
        _check_obj_type(self.risk_identity, R5S4RiskIdentity,
                        "R5S4BuildState.risk_identity")
        _check_obj_type(self.adjudication_row, R5S4AdjudicationRow,
                        "R5S4BuildState.adjudication_row")
        _check_obj_type(self.journey_link, R5S4JourneyLink,
                        "R5S4BuildState.journey_link")
        _check_obj_type(self.history_log, R5S4HistoryLog,
                        "R5S4BuildState.history_log")


# ---------------------------------------------------------------------------
# History / source semantic helpers (shared by projection and validator)
# ---------------------------------------------------------------------------


def history_chain_valid(entries: Tuple[R5S4HistoryEntry, ...]) -> bool:
    """True iff the entry chain is contiguous and well-formed: seq strictly
    ``1..len``, first ``prior_entry_hash == 'genesis'``, every later
    ``prior_entry_hash`` equals the previous ``entry_hash``, and every
    ``entry_hash`` is the canonical chain hash."""
    if not entries:
        return True
    seqs = [entry.seq for entry in entries]
    if seqs != list(range(1, len(entries) + 1)):
        return False
    if entries[0].prior_entry_hash != GENESIS_HASH:
        return False
    for index in range(1, len(entries)):
        if entries[index].prior_entry_hash != entries[index - 1].entry_hash:
            return False
    for entry in entries:
        if entry.entry_hash != compute_history_entry_hash(entry):
            return False
    return True


def history_log_valid(log: R5S4HistoryLog) -> bool:
    """True iff the history log obeys the append-only + errata rules."""
    if not log.entries:
        return log.head_seq == 0 and log.head_hash == GENESIS_HASH
    if not history_chain_valid(log.entries):
        return False
    return log.head_seq == len(log.entries) and \
        log.head_hash == log.entries[-1].entry_hash
