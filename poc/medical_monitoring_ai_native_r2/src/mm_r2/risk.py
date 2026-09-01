"""Risk lifecycle for the R2 kernel (Design v1.1 sections 10.1, 9.4; plan R2
step 4).

VETO 2 repairs:
* ``_verified_instance`` / ``_verified_adjudication`` removed from class and
  module surfaces; issuance uses closure-only factories.
* ``issue_user_adjudication(user=...)`` must equal the configured local_user.
* Adjudication binds action + complete target set; establish/transition/merge/
  split verify same lifecycle, stored hash, project, outcome, action, targets.
* Close reads real AcceptanceService (no caller-asserted booleans).
* ``confirmed_by_user`` persists through all subsequent transitions.
* Merge validates ALL target identities; split validates all child specs
  before mutation.
"""

from __future__ import annotations

import getpass
import re
from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    MmR2Error,
    content_hash,
    deep_freeze_json,
    new_id,
    now_iso,
    validate_sha256_hex,
)
from .identity import RiskIdentity

_RISK_VERIFIED = object()
_ADJ_ISSUED = object()

__all__ = [
    "RiskError", "IllegalTransitionError", "AdjudicationError",
    "RiskCandidate", "RiskInstance", "RiskTransition",
    "RiskLifecycleState", "RiskTransitionType",
    "AdjudicationRecord", "AdjudicationOutcome", "AdjudicationEvidenceBinding",
    "RiskLifecycle", "CANDIDATE_AUTO_PROMOTE_FORBIDDEN",
]


class RiskError(MmR2Error):
    """Generic risk-lifecycle violation."""


class IllegalTransitionError(RiskError):
    """An illegal, out-of-order, or unauthorized risk transition."""


class AdjudicationError(RiskError):
    """Adjudication authority violation."""


# ---------------------------------------------------------------------------
# Lifecycle enums
# ---------------------------------------------------------------------------

class RiskLifecycleState:
    ESTABLISHED = "established"
    ESCALATED = "escalated"
    DEESCALATED = "deescalated"
    CLOSED = "closed"
    REOPENED = "reopened"
    IDENTITY_AMBIGUOUS = "identity_ambiguous"
    SUPERSEDED = "superseded"
    NOT_EVALUABLE = "not_evaluable"

    @classmethod
    def all_states(cls) -> Tuple[str, ...]:
        return (cls.ESTABLISHED, cls.ESCALATED, cls.DEESCALATED, cls.CLOSED,
                cls.REOPENED, cls.IDENTITY_AMBIGUOUS, cls.SUPERSEDED,
                cls.NOT_EVALUABLE)

    @classmethod
    def active_states(cls) -> Tuple[str, ...]:
        return (cls.ESTABLISHED, cls.ESCALATED, cls.DEESCALATED,
                cls.REOPENED, cls.IDENTITY_AMBIGUOUS)

    @classmethod
    def terminal_states(cls) -> Tuple[str, ...]:
        return (cls.CLOSED, cls.SUPERSEDED, cls.NOT_EVALUABLE)


class RiskTransitionType:
    ESTABLISHED = "established"
    ESCALATED = "escalated"
    DEESCALATED = "deescalated"
    CLOSED = "closed"
    REOPENED = "reopened"
    IDENTITY_AMBIGUOUS = "identity_ambiguous"
    SUPERSEDED = "superseded"
    NOT_EVALUABLE = "not_evaluable"
    MERGED = "merged"
    SPLIT = "split"


class AdjudicationOutcome:
    MERGED_SUPPORTED = "merged_supported"
    DISTINCT_SUPPORTED = "distinct_supported"
    REJECTED_BY_EVIDENCE = "rejected_by_evidence"
    VERSION_MISMATCH = "version_mismatch"
    NEEDS_USER_ATTENTION = "needs_user_attention"

    @classmethod
    def all_outcomes(cls) -> Tuple[str, ...]:
        return (cls.MERGED_SUPPORTED, cls.DISTINCT_SUPPORTED,
                cls.REJECTED_BY_EVIDENCE, cls.VERSION_MISMATCH,
                cls.NEEDS_USER_ATTENTION)


# Valid adjudication actions.
_ACTION_ESTABLISH = "establish"
_ACTION_ESCALATE = "escalate"
_ACTION_DEESCALATE = "deescalate"
_ACTION_CLOSE = "close"
_ACTION_REOPEN = "reopen"
_ACTION_MERGE = "merge"
_ACTION_SPLIT = "split"
_ACTION_SUPERSEDE = "supersede"

_VALID_ACTIONS = frozenset({
    _ACTION_ESTABLISH, _ACTION_ESCALATE, _ACTION_DEESCALATE,
    _ACTION_CLOSE, _ACTION_REOPEN, _ACTION_MERGE, _ACTION_SPLIT,
    _ACTION_SUPERSEDE,
})

_ACTION_ALLOWED_OUTCOMES: Dict[str, Tuple[str, ...]] = {
    _ACTION_ESTABLISH: (AdjudicationOutcome.DISTINCT_SUPPORTED,),
    _ACTION_ESCALATE: (AdjudicationOutcome.DISTINCT_SUPPORTED,),
    _ACTION_DEESCALATE: (AdjudicationOutcome.DISTINCT_SUPPORTED,),
    _ACTION_CLOSE: (
        AdjudicationOutcome.DISTINCT_SUPPORTED,
        AdjudicationOutcome.REJECTED_BY_EVIDENCE,
    ),
    _ACTION_REOPEN: (AdjudicationOutcome.DISTINCT_SUPPORTED,),
    _ACTION_MERGE: (AdjudicationOutcome.MERGED_SUPPORTED,),
    _ACTION_SPLIT: (AdjudicationOutcome.DISTINCT_SUPPORTED,),
    _ACTION_SUPERSEDE: (
        AdjudicationOutcome.DISTINCT_SUPPORTED,
        AdjudicationOutcome.REJECTED_BY_EVIDENCE,
        AdjudicationOutcome.VERSION_MISMATCH,
    ),
}

# Map transition type -> required action.
_TRANSITION_ACTION: Dict[str, str] = {
    RiskTransitionType.ESTABLISHED: _ACTION_ESTABLISH,
    RiskTransitionType.ESCALATED: _ACTION_ESCALATE,
    RiskTransitionType.DEESCALATED: _ACTION_DEESCALATE,
    RiskTransitionType.CLOSED: _ACTION_CLOSE,
    RiskTransitionType.REOPENED: _ACTION_REOPEN,
    RiskTransitionType.MERGED: _ACTION_MERGE,
    RiskTransitionType.SPLIT: _ACTION_SPLIT,
    RiskTransitionType.SUPERSEDED: _ACTION_SUPERSEDE,
}


CANDIDATE_AUTO_PROMOTE_FORBIDDEN = (
    "RiskCandidate cannot auto-promote to RiskInstance; an explicit "
    "adjudicated decision with bound evidence is required"
)


# ---------------------------------------------------------------------------
# Transition legality table
# ---------------------------------------------------------------------------

_LEGAL_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    RiskLifecycleState.ESTABLISHED: (
        RiskTransitionType.ESCALATED, RiskTransitionType.DEESCALATED,
        RiskTransitionType.CLOSED, RiskTransitionType.IDENTITY_AMBIGUOUS,
        RiskTransitionType.SUPERSEDED, RiskTransitionType.NOT_EVALUABLE,
        RiskTransitionType.MERGED, RiskTransitionType.SPLIT,
    ),
    RiskLifecycleState.ESCALATED: (
        RiskTransitionType.DEESCALATED, RiskTransitionType.CLOSED,
        RiskTransitionType.IDENTITY_AMBIGUOUS, RiskTransitionType.SUPERSEDED,
        RiskTransitionType.NOT_EVALUABLE, RiskTransitionType.MERGED,
        RiskTransitionType.SPLIT,
    ),
    RiskLifecycleState.DEESCALATED: (
        RiskTransitionType.ESCALATED, RiskTransitionType.CLOSED,
        RiskTransitionType.IDENTITY_AMBIGUOUS, RiskTransitionType.SUPERSEDED,
        RiskTransitionType.NOT_EVALUABLE, RiskTransitionType.MERGED,
        RiskTransitionType.SPLIT,
    ),
    RiskLifecycleState.REOPENED: (
        RiskTransitionType.ESCALATED, RiskTransitionType.DEESCALATED,
        RiskTransitionType.CLOSED, RiskTransitionType.IDENTITY_AMBIGUOUS,
        RiskTransitionType.SUPERSEDED, RiskTransitionType.NOT_EVALUABLE,
        RiskTransitionType.MERGED, RiskTransitionType.SPLIT,
    ),
    RiskLifecycleState.CLOSED: (RiskTransitionType.REOPENED,),
    RiskLifecycleState.IDENTITY_AMBIGUOUS: (
        RiskTransitionType.ESCALATED, RiskTransitionType.DEESCALATED,
        RiskTransitionType.CLOSED, RiskTransitionType.SUPERSEDED,
        RiskTransitionType.NOT_EVALUABLE, RiskTransitionType.MERGED,
        RiskTransitionType.SPLIT, RiskTransitionType.ESTABLISHED,
    ),
    RiskLifecycleState.SUPERSEDED: (),
    RiskLifecycleState.NOT_EVALUABLE: (),
}

_TRANSITION_RESULT_STATE: Dict[str, str] = {
    RiskTransitionType.ESTABLISHED: RiskLifecycleState.ESTABLISHED,
    RiskTransitionType.ESCALATED: RiskLifecycleState.ESCALATED,
    RiskTransitionType.DEESCALATED: RiskLifecycleState.DEESCALATED,
    RiskTransitionType.CLOSED: RiskLifecycleState.CLOSED,
    RiskTransitionType.REOPENED: RiskLifecycleState.REOPENED,
    RiskTransitionType.IDENTITY_AMBIGUOUS: RiskLifecycleState.IDENTITY_AMBIGUOUS,
    RiskTransitionType.SUPERSEDED: RiskLifecycleState.SUPERSEDED,
    RiskTransitionType.NOT_EVALUABLE: RiskLifecycleState.NOT_EVALUABLE,
    RiskTransitionType.MERGED: RiskLifecycleState.SUPERSEDED,
    RiskTransitionType.SPLIT: RiskLifecycleState.SUPERSEDED,
}


def _resolve_state(transition_type: str) -> str:
    result = _TRANSITION_RESULT_STATE.get(transition_type)
    if result is None:
        raise IllegalTransitionError(f"unknown transition type {transition_type!r}")
    return result


_REQUIRES_ADJUDICATION: Dict[str, bool] = {
    RiskTransitionType.ESTABLISHED: True,
    RiskTransitionType.ESCALATED: True,
    RiskTransitionType.DEESCALATED: True,
    RiskTransitionType.CLOSED: True,
    RiskTransitionType.REOPENED: True,
    RiskTransitionType.IDENTITY_AMBIGUOUS: False,
    RiskTransitionType.SUPERSEDED: True,
    RiskTransitionType.NOT_EVALUABLE: False,
    RiskTransitionType.MERGED: True,
    RiskTransitionType.SPLIT: True,
}

_HIGH_SEVERITIES = frozenset({
    "high", "severe", "serious", "sae", "aesi", "life_threatening",
})

_MEDIUM_SEVERITIES = frozenset({"medium", "moderate"})
_LOW_SEVERITIES = frozenset({"low", "mild"})


def _normalized_risk_terms(value: str) -> Tuple[str, Tuple[str, ...]]:
    """Return a stable ASCII term form while preserving camel-case bounds."""
    if type(value) is not str:
        raise DomainValidationError("risk severity/classifier must be a string")
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    normalized = re.sub(
        r"[^a-z0-9]+", "_", camel_split.casefold()
    ).strip("_")
    tokens = tuple(token for token in normalized.split("_") if token)
    return normalized, tokens


_NEGATION_TOKENS = frozenset({
    "no", "non", "not", "without", "excluded", "excluding",
})

_COMPACT_ABBREVIATION_PREFIXES = frozenset({
    "candidate", "confirmed", "emerging", "new", "possible", "potential",
    "probable", "protocol", "reported", "risk", "suspected", "unreported",
})

_COMPACT_ABBREVIATION_SUFFIXES = frozenset({
    "alert", "assessment", "case", "category", "event", "finding", "flag",
    "indicator", "risk", "signal", "type",
})


def _token_is_negated(tokens: Tuple[str, ...], index: int) -> bool:
    return (
        bool(tokens) and tokens[0] in _NEGATION_TOKENS
    ) or (
        index > 0 and tokens[index - 1] in _NEGATION_TOKENS
    )


def _has_non_negated_token(tokens: Tuple[str, ...], marker: str) -> bool:
    return any(
        token == marker and not _token_is_negated(tokens, index)
        for index, token in enumerate(tokens)
    )


def _has_non_negated_sequence(
    tokens: Tuple[str, ...], sequence: Tuple[str, ...],
) -> bool:
    width = len(sequence)
    return any(
        tokens[index:index + width] == sequence
        and not _token_is_negated(tokens, index)
        for index in range(len(tokens) - width + 1)
    )


def _has_compact_abbreviation(
    tokens: Tuple[str, ...], marker: str,
) -> bool:
    """Recognize mixed/connected abbreviations without matching plurals or
    explicit negations (for example ``non_SAE`` and ``AESIs``).
    """
    compact = "".join(tokens)
    cursor = 0
    while True:
        index = compact.find(marker, cursor)
        if index < 0:
            return False
        prefix = compact[:index]
        suffix = compact[index + len(marker):]
        negated = (
            bool(tokens) and tokens[0] in _NEGATION_TOKENS
        ) or any(prefix.endswith(token) for token in _NEGATION_TOKENS)
        prefix_allowed = (
            not prefix
            or any(
                prefix.endswith(candidate)
                for candidate in _COMPACT_ABBREVIATION_PREFIXES
            )
        )
        suffix_allowed = (
            not suffix or suffix in _COMPACT_ABBREVIATION_SUFFIXES
        )
        if not negated and prefix_allowed and suffix_allowed:
            return True
        cursor = index + 1


_CHINESE_NEGATION_PREFIX_PATTERNS = (
    r"(?:并)?非",
    r"(?:并)?无(?:任何)?",
    r"没有(?:(?:发生|出现|发现|观察到|检测到)(?:任何)?|任何)?",
    r"未(?:判定为|识别为|发生|出现|发现|观察到|检测到|见|有)(?:任何)?",
    r"不(?:是|属于|含|包含|存在)",
)

_CHINESE_NEGATION_SUFFIX_PATTERNS = (
    r"(?:并)?不存在",
    r"(?:并)?未(?:发生|出现|发现|观察到|检测到)",
    r"(?:并)?没有(?:发生|出现|发现|观察到|检测到)",
)

_CHINESE_CLAUSE_BOUNDARY = re.compile(r"[，。；、,.;:：!?！？]")

_CHINESE_NEUTRAL_NEGATION_CONTEXT = re.compile(
    r"(?:"
    r"(?:截至)?(?:目前|当前|本次|迄今|至今|既往)"
    r"|尚"
    r"|(?:该)?(?:受试者|参与者|患者)"
    r"|(?:本)?(?:研究|项目|中心)"
    r"|(?:本|整个)?(?:研究|治疗|随访|观察)期间"
    r"|(?:本次)?访视"
    r"|(?:结果|资料|记录|数据|报告)显示"
    r"|经(?:核查|确认)"
    r"|(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]+"
    r")*"
)


def _has_explicit_prefix_negation(prefix: str) -> bool:
    """Accept a negator only after a neutral, clause-local context.

    This keeps uncertainty/double-negation such as ``不能确认没有`` and
    ``并非没有`` risk-positive while allowing ``截至目前尚未发生``.
    """
    for pattern in _CHINESE_NEGATION_PREFIX_PATTERNS:
        match = re.search(pattern + r"$", prefix)
        if match is None:
            continue
        clause_leader = _CHINESE_CLAUSE_BOUNDARY.split(
            prefix[:match.start()]
        )[-1]
        if _CHINESE_NEUTRAL_NEGATION_CONTEXT.fullmatch(clause_leader):
            return True
    return False


def _has_explicit_suffix_negation(prefix: str, suffix: str) -> bool:
    """Accept a postpositive negator only in a neutral local clause."""
    clause_leader = _CHINESE_CLAUSE_BOUNDARY.split(prefix)[-1]
    if not _CHINESE_NEUTRAL_NEGATION_CONTEXT.fullmatch(clause_leader):
        return False
    return any(
        re.match(pattern + r"(?:$|[，。；、,.;:：])", suffix)
        for pattern in _CHINESE_NEGATION_SUFFIX_PATTERNS
    )


def _has_non_negated_chinese_phrase(
    value: str, phrases: Tuple[str, ...],
) -> bool:
    """Accept only bounded, explicit absence/exclusion as negation.

    Ambiguous phrases such as ``未报告`` and ``未排除`` remain risk-positive.
    """
    compact = re.sub(r"\s+", "", value)
    for phrase in phrases:
        cursor = 0
        while True:
            index = compact.find(phrase, cursor)
            if index < 0:
                break
            prefix = compact[:index]
            suffix = compact[index + len(phrase):]
            prefix_negated = _has_explicit_prefix_negation(prefix)
            suffix_negated = _has_explicit_suffix_negation(prefix, suffix)
            if not prefix_negated and not suffix_negated:
                return True
            cursor = index + 1
    return False


def _clinical_risk_flags(*values: str) -> Tuple[str, ...]:
    flags = set()
    for value in values:
        _, ordered_tokens = _normalized_risk_terms(value)
        if (
            _has_non_negated_token(ordered_tokens, "sae")
            or _has_compact_abbreviation(ordered_tokens, "sae")
            or _has_non_negated_sequence(
                ordered_tokens, ("serious", "adverse", "event")
            )
            or _has_non_negated_chinese_phrase(
                value, ("严重不良事件", "严重的不良事件"),
            )
        ):
            flags.add("sae")
        if (
            _has_non_negated_token(ordered_tokens, "aesi")
            or _has_compact_abbreviation(ordered_tokens, "aesi")
            or _has_non_negated_sequence(
                ordered_tokens,
                ("adverse", "event", "of", "special", "interest"),
            )
            or _has_non_negated_chinese_phrase(
                value,
                (
                    "特别关注不良事件", "特别关注的不良事件",
                    "重点关注不良事件", "重点关注的不良事件",
                ),
            )
        ):
            flags.add("aesi")
    return tuple(sorted(flags))


def _severity_rank(value: str) -> int:
    """Conservative ordering used only to prevent lineage downgrades."""
    normalized, _ = _normalized_risk_terms(value)
    if normalized in _HIGH_SEVERITIES or _clinical_risk_flags(value):
        return 3
    if normalized in _MEDIUM_SEVERITIES:
        return 2
    if normalized in _LOW_SEVERITIES:
        return 1
    # An unrecognised confirmed severity is not silently treated as low.
    return 2


def _resolve_merge_severity(
    risk_instances: List[Any], requested_severity: str,
) -> str:
    if not risk_instances:
        raise RiskError("merge severity resolution requires source risks")
    source_severities = [instance.severity for instance in risk_instances]
    strongest = sorted(
        source_severities,
        key=lambda item: (-_severity_rank(item), _normalized_risk_terms(item)[0]),
    )[0]
    if not requested_severity:
        return strongest
    if _severity_rank(requested_severity) < _severity_rank(strongest):
        raise AdjudicationError(
            "merge cannot downgrade the strongest source-risk severity"
        )
    return requested_severity


def _merge_action_payload(
    risk_instances: List[Any], severity: str, classifier: str,
) -> Dict[str, str]:
    if type(classifier) is not str:
        raise DomainValidationError("merge classifier must be a string")
    return {
        "severity": _resolve_merge_severity(risk_instances, severity),
        "classifier": classifier,
    }


# ---------------------------------------------------------------------------
# Risk candidate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskCandidate:
    """An unverified risk signal (Design 10.1, 10.3).

    ``candidate_id`` is always ``cand-{content_hash}``.
    """

    schema_name: str = "risk_candidate"
    schema_version: str = "1"
    candidate_id: str = ""
    project_id: str = ""
    subject_ref: str = ""
    domain: str = ""
    source_snapshot_id: str = ""
    rule_activation_id: str = ""
    mapping_result_id: str = ""
    knowledge_pack_id: str = ""
    signal_type: str = ""
    severity_hint: str = ""
    confidence_hint: float = 0.0
    detail: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    content_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _RISK_VERIFIED,
    ) -> None:
        if not self.project_id:
            raise DomainValidationError("RiskCandidate.project_id is required")
        if not self.subject_ref:
            raise DomainValidationError("RiskCandidate.subject_ref is required")
        if not self.domain:
            raise DomainValidationError("RiskCandidate.domain is required")
        if not self.signal_type:
            raise DomainValidationError("RiskCandidate.signal_type is required")
        if not (0.0 <= self.confidence_hint <= 1.0):
            raise DomainValidationError(
                f"confidence_hint must be in [0,1], got {self.confidence_hint}")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "RiskCandidate requires verified construction; use from_signal(...)")
        object.__setattr__(self, "detail", deep_freeze_json(self.detail))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise DomainValidationError("content_hash mismatch")
        object.__setattr__(self, "content_hash", expected)
        derived_id = f"cand-{expected}"
        if self.candidate_id and self.candidate_id != derived_id:
            raise DomainValidationError(
                f"candidate_id {self.candidate_id!r} does not match the "
                f"deterministic derived id {derived_id!r}")
        object.__setattr__(self, "candidate_id", derived_id)

    @classmethod
    def from_signal(
        cls, project_id: str, subject_ref: str, domain: str, signal_type: str, *,
        source_snapshot_id: str = "", rule_activation_id: str = "",
        mapping_result_id: str = "", knowledge_pack_id: str = "",
        severity_hint: str = "", confidence_hint: float = 0.0,
        detail: Optional[Dict[str, Any]] = None, candidate_id: str = "",
        created_at: str = "", _authority_token: Any = _RISK_VERIFIED,
    ) -> "RiskCandidate":
        return cls(
            candidate_id=candidate_id, project_id=project_id,
            subject_ref=subject_ref, domain=domain,
            source_snapshot_id=source_snapshot_id,
            rule_activation_id=rule_activation_id,
            mapping_result_id=mapping_result_id,
            knowledge_pack_id=knowledge_pack_id, signal_type=signal_type,
            severity_hint=severity_hint, confidence_hint=confidence_hint,
            detail=detail or {}, created_at=created_at or now_iso(),
            _verified=_authority_token,
        )

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name, "schema_version": self.schema_version,
            "project_id": self.project_id, "subject_ref": self.subject_ref,
            "domain": self.domain, "source_snapshot_id": self.source_snapshot_id,
            "rule_activation_id": self.rule_activation_id,
            "mapping_result_id": self.mapping_result_id,
            "knowledge_pack_id": self.knowledge_pack_id,
            "signal_type": self.signal_type, "severity_hint": self.severity_hint,
            "confidence_hint": self.confidence_hint, "detail": self.detail,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Risk transition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskTransition:
    schema_name: str = "risk_transition"
    schema_version: str = "1"
    transition_id: str = ""
    risk_instance_id: str = ""
    project_id: str = ""
    from_state: str = ""
    to_state: str = ""
    transition_type: str = ""
    actor: str = ""
    reason: str = ""
    adjudication_id: str = ""
    is_machine_adjudicated: bool = False
    user_confirmed: bool = False
    lineage_refs: Tuple[str, ...] = ()
    coverage_snapshot_id: str = ""
    prev_hash: str = ""
    transition_hash: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.transition_id:
            raise DomainValidationError("transition_id required")
        if not self.risk_instance_id:
            raise DomainValidationError("risk_instance_id required")
        if not self.project_id:
            raise DomainValidationError("project_id required")
        if self.transition_type not in (
            RiskTransitionType.ESTABLISHED, RiskTransitionType.ESCALATED,
            RiskTransitionType.DEESCALATED, RiskTransitionType.CLOSED,
            RiskTransitionType.REOPENED, RiskTransitionType.IDENTITY_AMBIGUOUS,
            RiskTransitionType.SUPERSEDED, RiskTransitionType.NOT_EVALUABLE,
            RiskTransitionType.MERGED, RiskTransitionType.SPLIT,
        ):
            raise DomainValidationError(f"transition_type {self.transition_type!r} invalid")
        if not self.actor:
            raise DomainValidationError("actor is required")
        object.__setattr__(self, "lineage_refs", tuple(sorted(self.lineage_refs)))
        expected = self.compute_hash()
        if self.transition_hash and self.transition_hash != expected:
            raise DomainValidationError("transition_hash mismatch")
        object.__setattr__(self, "transition_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "risk_instance_id": self.risk_instance_id,
            "project_id": self.project_id, "from_state": self.from_state,
            "to_state": self.to_state, "transition_type": self.transition_type,
            "actor": self.actor, "reason": self.reason,
            "adjudication_id": self.adjudication_id,
            "is_machine_adjudicated": self.is_machine_adjudicated,
            "user_confirmed": self.user_confirmed,
            "lineage_refs": list(self.lineage_refs),
            "coverage_snapshot_id": self.coverage_snapshot_id,
            "prev_hash": self.prev_hash,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Adjudication evidence binding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdjudicationEvidenceBinding:
    candidate_id: str = ""
    risk_identity_id: str = ""
    source_revision_id: str = ""
    snapshot_id: str = ""
    rule_activation_id: str = ""
    mapping_result_id: str = ""
    model_analysis_hashes: Tuple[str, ...] = ()
    knowledge_pack_id: str = ""

    def __post_init__(self) -> None:
        for h in self.model_analysis_hashes:
            validate_sha256_hex(h, "model_analysis_hashes")
        object.__setattr__(self, "model_analysis_hashes", tuple(self.model_analysis_hashes))

    def has_evidence(self) -> bool:
        return bool(
            self.candidate_id or self.risk_identity_id
            or self.source_revision_id or self.snapshot_id
            or self.rule_activation_id or self.mapping_result_id
            or self.model_analysis_hashes or self.knowledge_pack_id
        )

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "risk_identity_id": self.risk_identity_id,
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "rule_activation_id": self.rule_activation_id,
            "mapping_result_id": self.mapping_result_id,
            "model_analysis_hashes": list(self.model_analysis_hashes),
            "knowledge_pack_id": self.knowledge_pack_id,
        }


# ---------------------------------------------------------------------------
# Adjudication record (service-issued)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdjudicationRecord:
    """Service-issued adjudication (Design 9.4).

    VETO 2: binds ``action`` and ``target_risk_identity_ids`` (the complete
    exact target set) so establish/transition/merge/split can verify the
    adjudication authorizes the intended action on the intended targets.
    """

    schema_name: str = "adjudication_record"
    schema_version: str = "1"
    adjudication_id: str = ""
    project_id: str = ""
    outcome: str = ""
    action: str = ""
    evidence: AdjudicationEvidenceBinding = field(default_factory=AdjudicationEvidenceBinding)
    actor: str = ""
    is_machine_adjudicated: bool = True
    user_confirmed: bool = False
    rationale: str = ""
    bound_candidate_id: str = ""
    target_risk_identity_ids: Tuple[str, ...] = ()
    target_risk_versions: Tuple[Tuple[str, str, str], ...] = ()
    action_payload_hash: str = ""
    issued_by_lifecycle_id: str = ""
    created_at: str = ""
    content_hash: str = ""
    _issued: InitVar[Any] = None

    def __post_init__(
        self, _issued: Any = None, _authority_token: Any = _ADJ_ISSUED,
    ) -> None:
        if _issued is not _authority_token:
            raise DomainValidationError(
                "AdjudicationRecord cannot be constructed directly; use "
                "RiskLifecycle.issue_adjudication(...) or "
                "RiskLifecycle.issue_user_adjudication(...)")
        if not self.adjudication_id:
            raise DomainValidationError("adjudication_id is required")
        if not self.project_id:
            raise DomainValidationError("project_id is required")
        if self.outcome not in AdjudicationOutcome.all_outcomes():
            raise DomainValidationError(f"outcome {self.outcome!r} invalid")
        if self.action not in _VALID_ACTIONS:
            raise DomainValidationError(f"action {self.action!r} invalid")
        if not self.actor:
            raise DomainValidationError("actor is required")
        if not self.evidence.has_evidence():
            raise DomainValidationError("requires bound evidence")
        if self.is_machine_adjudicated and self.user_confirmed:
            raise DomainValidationError(
                "machine adjudication cannot declare user_confirmed=True")
        if not self.rationale:
            raise DomainValidationError("rationale is required")
        object.__setattr__(self, "target_risk_identity_ids",
                           tuple(sorted(self.target_risk_identity_ids)))
        versions = tuple(sorted(tuple(item) for item in self.target_risk_versions))
        for item in versions:
            if len(item) != 3 or not all(item):
                raise DomainValidationError(
                    "target_risk_versions require identity, instance, and "
                    "transition hash"
                )
            validate_sha256_hex(item[2], "target_risk_versions.transition_hash")
        if tuple(item[0] for item in versions) != self.target_risk_identity_ids:
            raise DomainValidationError(
                "target_risk_versions must exactly bind target identities"
            )
        object.__setattr__(self, "target_risk_versions", versions)
        if self.action_payload_hash:
            validate_sha256_hex(
                self.action_payload_hash,
                "AdjudicationRecord.action_payload_hash",
            )
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise DomainValidationError("content_hash mismatch")
        object.__setattr__(self, "content_hash", expected)

    @property
    def masquerades_as_user_confirmation(self) -> bool:
        return self.is_machine_adjudicated and self.user_confirmed

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "adjudication_id": self.adjudication_id,
            "project_id": self.project_id, "outcome": self.outcome,
            "action": self.action, "evidence": self.evidence.canonical_payload(),
            "actor": self.actor,
            "is_machine_adjudicated": self.is_machine_adjudicated,
            "user_confirmed": self.user_confirmed, "rationale": self.rationale,
            "bound_candidate_id": self.bound_candidate_id,
            "target_risk_identity_ids": list(self.target_risk_identity_ids),
            "target_risk_versions": [list(item) for item in self.target_risk_versions],
            "action_payload_hash": self.action_payload_hash,
            "issued_by_lifecycle_id": self.issued_by_lifecycle_id,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Risk instance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskInstance:
    schema_name: str = "risk_instance"
    schema_version: str = "1"
    risk_instance_id: str = ""
    project_id: str = ""
    identity: RiskIdentity = None  # type: ignore[assignment]
    domain: str = ""
    source_snapshot_ids: Tuple[str, ...] = ()
    clinical_risk_flags: Tuple[str, ...] = ()
    established_adjudication_id: str = ""
    transitions: Tuple[RiskTransition, ...] = ()
    severity: str = ""
    confirmed_by_user: bool = False
    created_at: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _RISK_VERIFIED,
    ) -> None:
        if not self.risk_instance_id:
            raise DomainValidationError("risk_instance_id is required")
        if not self.project_id:
            raise DomainValidationError("project_id is required")
        if self.identity is None:
            raise DomainValidationError("identity is required")
        if type(self.identity) is not RiskIdentity:
            raise DomainValidationError("identity must be a verified RiskIdentity")
        if not self.domain:
            raise DomainValidationError("domain is required")
        source_snapshot_ids = tuple(sorted(set(self.source_snapshot_ids)))
        if not source_snapshot_ids or any(not item for item in source_snapshot_ids):
            raise DomainValidationError("source_snapshot_ids are required")
        object.__setattr__(self, "source_snapshot_ids", source_snapshot_ids)
        flags = tuple(sorted(set(self.clinical_risk_flags)))
        if any(flag not in ("sae", "aesi") for flag in flags):
            raise DomainValidationError(
                "clinical_risk_flags contain an unknown flag"
            )
        object.__setattr__(self, "clinical_risk_flags", flags)
        if not self.established_adjudication_id:
            raise DomainValidationError("established_adjudication_id is required")
        if self.identity.project_id != self.project_id:
            raise DomainValidationError("identity project_id mismatch")
        if self.identity.domain != self.domain:
            raise DomainValidationError("identity domain mismatch")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "RiskInstance requires verified construction; use "
                "RiskLifecycle.establish(...) -- direct construction is "
                "unavailable to public callers")
        transitions = tuple(self.transitions)
        if not transitions:
            raise DomainValidationError("RiskInstance requires an established transition")
        for index, transition in enumerate(transitions):
            if type(transition) is not RiskTransition:
                raise DomainValidationError("RiskInstance transitions must be RiskTransition records")
            if transition.risk_instance_id != self.risk_instance_id:
                raise DomainValidationError("transition risk_instance_id mismatch")
            if transition.project_id != self.project_id:
                raise DomainValidationError("transition project_id mismatch")
            if transition.to_state != _resolve_state(transition.transition_type):
                raise DomainValidationError("transition target state mismatch")
            if index == 0:
                if transition.transition_type != RiskTransitionType.ESTABLISHED:
                    raise DomainValidationError("first transition must establish the risk")
                if transition.from_state != "":
                    raise DomainValidationError("established transition must start from empty state")
                if transition.adjudication_id != self.established_adjudication_id:
                    raise DomainValidationError("established adjudication mismatch")
            else:
                previous = transitions[index - 1]
                if transition.from_state != previous.to_state:
                    raise DomainValidationError("risk transition chain is not continuous")
                if transition.transition_type not in _LEGAL_TRANSITIONS.get(previous.to_state, ()):
                    raise DomainValidationError("risk transition chain contains an illegal transition")
        if any(t.user_confirmed for t in transitions) and not self.confirmed_by_user:
            raise DomainValidationError("confirmed_by_user cannot discard prior user confirmation")
        object.__setattr__(self, "transitions", transitions)

    @property
    def current_state(self) -> str:
        if not self.transitions:
            return RiskLifecycleState.ESTABLISHED
        return self.transitions[-1].to_state

    @property
    def is_active(self) -> bool:
        return self.current_state in RiskLifecycleState.active_states()

    @property
    def risk_identity_id(self) -> str:
        return self.identity.risk_identity_id

    @property
    def ever_user_confirmed(self) -> bool:
        """VETO 2-14: if any transition was user-confirmed, this is True."""
        return self.confirmed_by_user or any(
            t.user_confirmed for t in self.transitions
        )


# ---------------------------------------------------------------------------
# Risk lifecycle service
# ---------------------------------------------------------------------------

class RiskLifecycle:
    """Sole authority over risk instance creation, transitions, and
    adjudication issuance.

    VETO 2: ``_verified_instance`` / ``_verified_adjudication`` are NOT methods
    on this class.  Issuance occurs through closure-only factories that are
    unreachable as class/module attributes.
    """

    _SUPPORTING_OUTCOMES = frozenset({
        AdjudicationOutcome.MERGED_SUPPORTED,
        AdjudicationOutcome.DISTINCT_SUPPORTED,
    })

    def __init__(
        self, identity_factory=None, local_user: Optional[str] = None,
    ) -> None:
        if identity_factory is None:
            from .identity import make_risk_identity
            identity_factory = make_risk_identity
        self._identity_factory = identity_factory
        self._local_user = local_user if local_user is not None else getpass.getuser()
        self._lifecycle_id = new_id("rlc-")
        self._instances: Dict[str, RiskInstance] = {}
        self._candidates: Dict[str, RiskCandidate] = {}
        self._candidate_instances: Dict[str, str] = {}
        self._adjudications: Dict[str, AdjudicationRecord] = {}
        self._chain_head: Dict[str, str] = {}
        self._source_acceptance_services: Dict[str, Any] = {}

    @property
    def local_user(self) -> str:
        return self._local_user

    @property
    def lifecycle_id(self) -> str:
        return self._lifecycle_id

    # -- candidate registration -------------------------------------------

    def register_candidate(self, candidate: RiskCandidate) -> RiskCandidate:
        if type(candidate) is not RiskCandidate:
            raise RiskError("register_candidate requires a RiskCandidate")
        existing = self._candidates.get(candidate.candidate_id)
        if existing is not None and existing.content_hash != candidate.content_hash:
            raise RiskError(
                f"candidate {candidate.candidate_id!r} already registered with "
                f"different content; same-ID/different-content rejected")
        if existing is not None:
            return existing
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def candidate(self, candidate_id: str) -> RiskCandidate:
        if candidate_id not in self._candidates:
            raise RiskError(f"unknown candidate {candidate_id!r}")
        return self._candidates[candidate_id]

    # -- adjudication issuance (VETO 2-11) --------------------------------

    def issue_adjudication(
        self, project_id: str, outcome: str, action: str,
        evidence: AdjudicationEvidenceBinding, *,
        candidate: Optional[RiskCandidate] = None,
        risk_instances: Optional[List["RiskInstance"]] = None,
        rationale: str = "", action_payload: Any = None, _issuer=None,
    ) -> AdjudicationRecord:
        """Issue a machine adjudication.

        VETO 2: validates action, binds the complete target set, and requires
        candidates/risks to be registered.
        """
        actor = self._local_user
        self._validate_issuance(
            project_id, action, evidence, actor,
            is_machine=True, candidate=candidate, risk_instances=risk_instances,
        )
        bound_cid = candidate.candidate_id if candidate else ""
        target_ids = tuple(
            ri.risk_identity_id for ri in (risk_instances or [])
        )
        target_versions = tuple(
            (
                ri.risk_identity_id,
                ri.risk_instance_id,
                ri.transitions[-1].transition_hash,
            )
            for ri in (risk_instances or [])
        )
        action_payload_hash = (
            content_hash(deep_freeze_json(action_payload))
            if action_payload is not None else ""
        )
        if action in (_ACTION_MERGE, _ACTION_SPLIT) and not action_payload_hash:
            raise AdjudicationError(
                f"{action} adjudication requires a bound action payload"
            )
        if _issuer is None:
            raise AdjudicationError("adjudication issuance authority is unavailable")
        adj = _issuer(
            adjudication_id=new_id("adj-"),
            project_id=project_id, outcome=outcome, action=action,
            evidence=evidence, actor=actor,
            is_machine_adjudicated=True, user_confirmed=False,
            rationale=rationale, bound_candidate_id=bound_cid,
            target_risk_identity_ids=target_ids,
            target_risk_versions=target_versions,
            action_payload_hash=action_payload_hash,
            issued_by_lifecycle_id=self._lifecycle_id,
            created_at=now_iso(),
        )
        self._adjudications[adj.adjudication_id] = adj
        return adj

    def issue_user_adjudication(
        self, project_id: str, outcome: str, action: str,
        evidence: AdjudicationEvidenceBinding, *,
        candidate: Optional[RiskCandidate] = None,
        risk_instances: Optional[List["RiskInstance"]] = None,
        rationale: str = "", user: Optional[str] = None,
        action_payload: Any = None, _issuer=None,
    ) -> AdjudicationRecord:
        """Issue a user-confirmed adjudication.

        VETO 2-11: ``user`` must equal the configured local user; an attacker
        cannot inject a different user.
        """
        actor = user if user is not None else self._local_user
        if actor != self._local_user:
            raise AdjudicationError(
                f"user {actor!r} does not match the configured local user "
                f"{self._local_user!r}; user-confirmed adjudication can only "
                f"be issued for the configured local user")
        self._validate_issuance(
            project_id, action, evidence, actor,
            is_machine=False, candidate=candidate, risk_instances=risk_instances,
        )
        bound_cid = candidate.candidate_id if candidate else ""
        target_ids = tuple(
            ri.risk_identity_id for ri in (risk_instances or [])
        )
        target_versions = tuple(
            (
                ri.risk_identity_id,
                ri.risk_instance_id,
                ri.transitions[-1].transition_hash,
            )
            for ri in (risk_instances or [])
        )
        action_payload_hash = (
            content_hash(deep_freeze_json(action_payload))
            if action_payload is not None else ""
        )
        if action in (_ACTION_MERGE, _ACTION_SPLIT) and not action_payload_hash:
            raise AdjudicationError(
                f"{action} adjudication requires a bound action payload"
            )
        if _issuer is None:
            raise AdjudicationError("adjudication issuance authority is unavailable")
        adj = _issuer(
            adjudication_id=new_id("adj-"),
            project_id=project_id, outcome=outcome, action=action,
            evidence=evidence, actor=actor,
            is_machine_adjudicated=False, user_confirmed=True,
            rationale=rationale, bound_candidate_id=bound_cid,
            target_risk_identity_ids=target_ids,
            target_risk_versions=target_versions,
            action_payload_hash=action_payload_hash,
            issued_by_lifecycle_id=self._lifecycle_id,
            created_at=now_iso(),
        )
        self._adjudications[adj.adjudication_id] = adj
        return adj

    def _validate_issuance(
        self, project_id: str, action: str,
        evidence: AdjudicationEvidenceBinding, actor: str, *,
        is_machine: bool,
        candidate: Optional[RiskCandidate],
        risk_instances: Optional[List["RiskInstance"]],
    ) -> None:
        if type(evidence) is not AdjudicationEvidenceBinding:
            raise AdjudicationError(
                "adjudication evidence must be an exact "
                "AdjudicationEvidenceBinding record"
            )
        if action not in _VALID_ACTIONS:
            raise AdjudicationError(f"action {action!r} invalid")
        # VETO 2: validate actor against local_user or system_policy.
        if actor != self._local_user and actor != "system_policy":
            raise AdjudicationError(
                f"actor {actor!r} is not the configured local user "
                f"{self._local_user!r} nor system_policy")
        if candidate is not None:
            if candidate.project_id != project_id:
                raise AdjudicationError(
                    "candidate project_id does not match adjudication project_id")
            if candidate.candidate_id not in self._candidates:
                raise AdjudicationError(
                    f"candidate {candidate.candidate_id!r} is not registered "
                    f"in this lifecycle")
            # VETO 2-12: evidence must bind this candidate; foreign-only
            # evidence cannot authorize issuance.
            if evidence.candidate_id and evidence.candidate_id != candidate.candidate_id:
                raise AdjudicationError(
                    f"evidence candidate_id {evidence.candidate_id!r} does "
                    f"not match the candidate {candidate.candidate_id!r}")
            if not evidence.candidate_id:
                raise AdjudicationError(
                    f"evidence does not bind candidate {candidate.candidate_id!r}; "
                    f"foreign-only evidence cannot authorize issuance")
            reference_pairs = (
                ("snapshot_id", candidate.source_snapshot_id),
                ("rule_activation_id", candidate.rule_activation_id),
                ("mapping_result_id", candidate.mapping_result_id),
                ("knowledge_pack_id", candidate.knowledge_pack_id),
            )
            for field_name, expected in reference_pairs:
                if expected and getattr(evidence, field_name) != expected:
                    raise AdjudicationError(
                        f"evidence {field_name} does not match candidate "
                        f"{field_name} {expected!r}"
                    )
        if risk_instances is not None:
            target_ids = []
            for ri in risk_instances:
                if type(ri) is not RiskInstance:
                    raise AdjudicationError("risk target must be a RiskInstance")
                if ri.project_id != project_id:
                    raise AdjudicationError(
                        "risk_instance project_id does not match adjudication project_id")
                if ri.risk_instance_id not in self._instances:
                    raise AdjudicationError(
                        f"risk_instance {ri.risk_instance_id!r} is not registered "
                        f"in this lifecycle")
                if self._instances[ri.risk_instance_id] != ri:
                    raise AdjudicationError(
                        f"risk_instance {ri.risk_instance_id!r} is not the "
                        "current registered lifecycle state"
                    )
                target_ids.append(ri.risk_identity_id)
            if len(target_ids) != len(set(target_ids)):
                raise AdjudicationError("risk target set contains duplicates")
            if len(target_ids) == 1 and evidence.risk_identity_id != target_ids[0]:
                raise AdjudicationError(
                    "evidence risk_identity_id does not match the target risk"
                )
            if len(target_ids) > 1 and evidence.risk_identity_id not in target_ids:
                raise AdjudicationError(
                    "merge evidence must bind one of the complete target set"
                )

    def adjudication(self, adjudication_id: str) -> AdjudicationRecord:
        if adjudication_id not in self._adjudications:
            raise RiskError(f"unknown adjudication {adjudication_id!r}")
        return self._adjudications[adjudication_id]

    def _verify_adjudication(
        self, adj: AdjudicationRecord, project_id: str, action: str,
        candidate: Optional[RiskCandidate] = None,
        target_risk_instances: Optional[List[RiskInstance]] = None,
    ) -> None:
        """Verify adjudication at use time: same lifecycle, stored hash,
        project, action, and complete target set."""
        if type(adj) is not AdjudicationRecord:
            raise AdjudicationError(
                "adjudication must be an exact service-issued "
                "AdjudicationRecord"
            )
        if adj.adjudication_id not in self._adjudications:
            raise AdjudicationError(
                f"adjudication {adj.adjudication_id!r} is not registered in "
                f"this lifecycle")
        stored = self._adjudications[adj.adjudication_id]
        if stored != adj or stored.content_hash != adj.content_hash:
            raise AdjudicationError(
                f"adjudication {adj.adjudication_id!r} content_hash mismatch")
        if adj.issued_by_lifecycle_id != self._lifecycle_id:
            raise AdjudicationError(
                f"adjudication was not issued by this lifecycle")
        if adj.project_id != project_id:
            raise AdjudicationError(
                f"adjudication project_id mismatch")
        if adj.action != action:
            raise AdjudicationError(
                f"adjudication action {adj.action!r} does not match required "
                f"action {action!r}")
        if candidate is not None:
            if adj.bound_candidate_id != candidate.candidate_id:
                raise AdjudicationError(
                    f"adjudication does not bind candidate "
                    f"{candidate.candidate_id!r}")
        if target_risk_instances is not None:
            expected = tuple(sorted(
                instance.risk_identity_id for instance in target_risk_instances
            ))
            if adj.target_risk_identity_ids != expected:
                raise AdjudicationError(
                    f"adjudication target_risk_identity_ids "
                    f"{adj.target_risk_identity_ids!r} do not match the "
                    f"required complete target set {expected!r}")
            expected_versions = tuple(sorted(
                (
                    instance.risk_identity_id,
                    instance.risk_instance_id,
                    instance.transitions[-1].transition_hash,
                )
                for instance in target_risk_instances
            ))
            if adj.target_risk_versions != expected_versions:
                raise AdjudicationError(
                    "adjudication target risk version is stale; issue a new "
                    "adjudication for the current risk state"
                )

    # -- establish --------------------------------------------------------

    def establish(
        self, candidate: RiskCandidate, adjudication: AdjudicationRecord, *,
        severity: str = "", scope: Optional[List[str]] = None,
        classifier: str = "", actor: str = "", acceptance_service=None,
        _issuer=None,
    ) -> RiskInstance:
        if type(candidate) is not RiskCandidate:
            raise RiskError("establish requires a RiskCandidate")
        if type(adjudication) is not AdjudicationRecord:
            raise RiskError("establish requires an AdjudicationRecord")
        if candidate.candidate_id not in self._candidates:
            raise RiskError(
                f"candidate {candidate.candidate_id!r} is not registered")
        if candidate.candidate_id in self._candidate_instances:
            raise RiskError(
                f"candidate {candidate.candidate_id!r} already established as "
                f"{self._candidate_instances[candidate.candidate_id]!r}"
            )
        # VETO 2-12: evidence must contain the registered candidate ID and
        # match the candidate's nonempty snapshot/rule/mapping references.
        if adjudication.evidence.candidate_id != candidate.candidate_id:
            raise AdjudicationError(
                f"adjudication evidence does not bind candidate "
                f"{candidate.candidate_id!r}")
        # VETO 2: foreign-only evidence fields cannot authorize.
        if not candidate.source_snapshot_id and not adjudication.evidence.snapshot_id:
            raise AdjudicationError(
                "candidate and adjudication evidence both lack snapshot_id; "
                "foreign-only evidence cannot authorize establishment")
        self._verify_adjudication(
            adjudication, candidate.project_id, _ACTION_ESTABLISH,
            candidate=candidate,
        )
        if adjudication.outcome != AdjudicationOutcome.DISTINCT_SUPPORTED:
            raise RiskError(
                f"adjudication outcome {adjudication.outcome!r} does not "
                f"support establishment")
        if not actor:
            raise DomainValidationError("establish requires an actor")
        # VETO 2: validate actor.
        if actor != self._local_user and actor != "system_policy":
            raise AdjudicationError(
                f"actor {actor!r} is not the configured local user nor system_policy")
        if not severity:
            raise DomainValidationError(
                "establish requires an explicit confirmed severity")
        from .acceptance import AcceptanceService, SnapshotAcceptanceState
        if type(acceptance_service) is not AcceptanceService:
            raise AdjudicationError(
                "establish requires the exact source AcceptanceService"
            )
        if not candidate.source_snapshot_id:
            raise AdjudicationError(
                "establish requires a candidate source_snapshot_id"
            )
        source_record = acceptance_service.get(candidate.source_snapshot_id)
        if (
            source_record.project_id != candidate.project_id
            or source_record.blocked
            or source_record.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE
        ):
            raise AdjudicationError(
                "candidate source snapshot must be an unblocked "
                "baseline-eligible full snapshot"
            )
        source_binding = acceptance_service.binding(candidate.source_snapshot_id)
        if (
            source_binding.project_id != candidate.project_id
            or source_binding.snapshot.snapshot_id != candidate.source_snapshot_id
        ):
            raise AdjudicationError("candidate source snapshot binding mismatch")
        effective_classifier = classifier or candidate.signal_type
        identity = self._identity_factory(
            project_id=candidate.project_id,
            subject_ref=candidate.subject_ref, domain=candidate.domain,
            scope=list(scope or ()), classifier=effective_classifier,
        )
        risk_instance_id = new_id("risk-")
        established_tr = self._make_transition(
            risk_instance_id=risk_instance_id, project_id=candidate.project_id,
            from_state="", to_state=RiskLifecycleState.ESTABLISHED,
            transition_type=RiskTransitionType.ESTABLISHED, actor=actor,
            reason=f"established from candidate {candidate.candidate_id}",
            adjudication_id=adjudication.adjudication_id,
            is_machine_adjudicated=adjudication.is_machine_adjudicated,
            user_confirmed=adjudication.user_confirmed,
        )
        if _issuer is None:
            raise RiskError("risk-instance issuance authority is unavailable")
        instance = _issuer(
            risk_instance_id=risk_instance_id, project_id=candidate.project_id,
            identity=identity, domain=candidate.domain,
            source_snapshot_ids=(candidate.source_snapshot_id,),
            clinical_risk_flags=_clinical_risk_flags(
                severity, candidate.signal_type,
            ),
            established_adjudication_id=adjudication.adjudication_id,
            transitions=(established_tr,), severity=severity,
            confirmed_by_user=adjudication.user_confirmed,
        )
        self._chain_head[candidate.project_id] = established_tr.transition_hash
        self._instances[risk_instance_id] = instance
        self._source_acceptance_services[risk_instance_id] = acceptance_service
        self._candidate_instances[candidate.candidate_id] = risk_instance_id
        return instance

    def get(self, risk_instance_id: str) -> RiskInstance:
        if risk_instance_id not in self._instances:
            raise RiskError(f"unknown risk instance {risk_instance_id!r}")
        return self._instances[risk_instance_id]

    def instances_for_project(self, project_id: str) -> List[RiskInstance]:
        return [i for i in self._instances.values() if i.project_id == project_id]

    @staticmethod
    def merge_action_payload(
        risk_instances: List[RiskInstance], *, severity: str = "",
        classifier: str = "",
    ) -> Dict[str, str]:
        """Build the exact severity/classifier payload a merge must bind."""
        if any(type(instance) is not RiskInstance for instance in risk_instances):
            raise RiskError("merge action payload requires verified risk instances")
        return _merge_action_payload(risk_instances, severity, classifier)

    # -- transitions ------------------------------------------------------

    def _check_legal(self, current: str, transition_type: str) -> str:
        legal = _LEGAL_TRANSITIONS.get(current, ())
        if transition_type not in legal:
            raise IllegalTransitionError(
                f"illegal transition {current!r} -> {transition_type!r}")
        return _resolve_state(transition_type)

    def transition(
        self, risk_instance_id: str, transition_type: str, *,
        actor: str = "", reason: str = "",
        adjudication: Optional[AdjudicationRecord] = None,
        acceptance_service=None, coverage_snapshot_id: str = "",
        lineage_refs: Optional[List[str]] = None, _issuer=None,
    ) -> RiskInstance:
        """Append a lifecycle transition.

        VETO 2-13: close reads a real nonblocked accepted coverage snapshot
        from a real AcceptanceService; no caller-asserted booleans.
        VETO 2-14: confirmed_by_user persists.
        """
        instance = self.get(risk_instance_id)
        if not actor:
            raise DomainValidationError("transition requires an actor")
        if actor != self._local_user and actor != "system_policy":
            raise AdjudicationError(
                f"actor {actor!r} is not the configured local user nor system_policy")
        current = instance.current_state
        to_state = self._check_legal(current, transition_type)

        # VETO 2: validate transition continuity (from_state == current_state).
        # Already done via _check_legal.

        if _REQUIRES_ADJUDICATION.get(transition_type, False):
            if adjudication is None:
                raise AdjudicationError(
                    f"transition {transition_type!r} requires a bound adjudication")
            required_action = _TRANSITION_ACTION.get(transition_type, "")
            self._verify_adjudication(
                adjudication, instance.project_id, required_action,
                target_risk_instances=[instance],
            )
            if adjudication.outcome not in _ACTION_ALLOWED_OUTCOMES.get(
                required_action, ()
            ):
                raise AdjudicationError(
                    f"adjudication outcome {adjudication.outcome!r} does not "
                    f"support transition action {required_action!r}"
                )
        elif adjudication is not None:
            self._verify_adjudication(
                adjudication, instance.project_id,
                _TRANSITION_ACTION.get(transition_type, adjudication.action),
                target_risk_instances=[instance],
            )

        # VETO 2-13: close requires real AcceptanceService.
        if transition_type == RiskTransitionType.CLOSED:
            from .acceptance import AcceptanceService, SnapshotAcceptanceState
            if type(acceptance_service) is not AcceptanceService:
                raise AdjudicationError(
                    "close requires a real AcceptanceService to verify the "
                    f"coverage snapshot")
            source_service = self._source_acceptance_services.get(risk_instance_id)
            if acceptance_service is not source_service:
                raise AdjudicationError(
                    "close requires the same AcceptanceService that verified "
                    "the risk source snapshot"
                )
            if not coverage_snapshot_id:
                raise AdjudicationError(
                    "close requires a coverage_snapshot_id")
            cov_rec = acceptance_service.get(coverage_snapshot_id)
            if cov_rec.project_id != instance.project_id:
                raise AdjudicationError(
                    f"coverage snapshot project_id mismatch")
            if cov_rec.blocked:
                raise AdjudicationError(
                    f"coverage snapshot is blocked")
            if cov_rec.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
                raise AdjudicationError(
                    f"coverage snapshot has not completed baseline-eligible "
                    f"source coverage "
                    f"(state={cov_rec.state.value})")
            if coverage_snapshot_id in instance.source_snapshot_ids:
                raise AdjudicationError(
                    "close coverage must be a subsequent full snapshot, not "
                    "a source snapshot"
                )
            coverage_registered_at = cov_rec.records[0].created_at
            for source_snapshot_id in instance.source_snapshot_ids:
                source_record = acceptance_service.get(source_snapshot_id)
                if (
                    source_record.project_id != instance.project_id
                    or source_record.blocked
                    or source_record.state
                    != SnapshotAcceptanceState.BASELINE_ELIGIBLE
                ):
                    raise AdjudicationError(
                        "risk source snapshot is not live and baseline eligible"
                    )
                if source_record.records[0].created_at >= coverage_registered_at:
                    raise AdjudicationError(
                        "close coverage must be registered after every risk "
                        "source snapshot"
                    )
            coverage_binding = acceptance_service.binding(coverage_snapshot_id)
            if (
                coverage_binding.project_id != instance.project_id
                or coverage_binding.snapshot.snapshot_id != coverage_snapshot_id
                or coverage_binding.snapshot.project_id != instance.project_id
            ):
                raise AdjudicationError("coverage snapshot binding mismatch")
            if adjudication.evidence.snapshot_id != coverage_snapshot_id:
                raise AdjudicationError(
                    "close adjudication evidence must bind the coverage snapshot"
                )
            if (
                adjudication.is_machine_adjudicated
                and adjudication.outcome
                != AdjudicationOutcome.REJECTED_BY_EVIDENCE
            ):
                raise AdjudicationError(
                    "machine close requires evidence that the risk is no "
                    "longer supported in the subsequent full snapshot"
                )
            # High-risk or ever-user-confirmed risks require user-confirmed.
            is_high = (
                _severity_rank(instance.severity) >= 3
                or bool(instance.clinical_risk_flags)
            )
            if (is_high or instance.ever_user_confirmed) and not adjudication.user_confirmed:
                raise AdjudicationError(
                    f"close blocked: risk severity {instance.severity!r} is "
                    f"high-risk or was ever user-confirmed; auto-close "
                    f"requires user-confirmed adjudication")

        adj_id = adjudication.adjudication_id if adjudication else ""
        is_machine = adjudication.is_machine_adjudicated if adjudication else True
        # VETO 2-14: confirmed_by_user persists once set.
        user_conf = adjudication.user_confirmed if adjudication else False
        new_confirmed = instance.confirmed_by_user or user_conf

        tr = self._make_transition(
            risk_instance_id=risk_instance_id, project_id=instance.project_id,
            from_state=current, to_state=to_state,
            transition_type=transition_type, actor=actor, reason=reason,
            adjudication_id=adj_id,
            is_machine_adjudicated=is_machine, user_confirmed=user_conf,
            coverage_snapshot_id=coverage_snapshot_id,
            lineage_refs=lineage_refs or [],
        )
        if _issuer is None:
            raise RiskError("risk-instance issuance authority is unavailable")
        new_instance = _issuer(
            risk_instance_id=instance.risk_instance_id,
            project_id=instance.project_id, identity=instance.identity,
            domain=instance.domain,
            source_snapshot_ids=instance.source_snapshot_ids,
            clinical_risk_flags=instance.clinical_risk_flags,
            established_adjudication_id=instance.established_adjudication_id,
            transitions=instance.transitions + (tr,),
            severity=instance.severity, confirmed_by_user=new_confirmed,
            created_at=instance.created_at,
        )
        self._chain_head[instance.project_id] = tr.transition_hash
        self._instances[risk_instance_id] = new_instance
        return new_instance

    # -- merge / split ---------------------------------------------------

    def merge(
        self, risk_instance_ids: List[str], *,
        adjudication: AdjudicationRecord, severity: str = "",
        classifier: str = "", actor: str = "", reason: str = "", _issuer=None,
    ) -> RiskInstance:
        """Merge multiple risk instances.  Prevalidates all inputs before
        any mutation.

        VETO 2-15: validates ALL target identities, not just the first.
        """
        if len(risk_instance_ids) < 2:
            raise RiskError("merge requires at least two risk instances")
        if len(risk_instance_ids) != len(set(risk_instance_ids)):
            raise RiskError("merge risk target set contains duplicate instances")
        if _issuer is None:
            raise RiskError("risk-instance issuance authority is unavailable")
        if not actor:
            raise DomainValidationError("merge requires an actor")
        if actor != self._local_user and actor != "system_policy":
            raise AdjudicationError(
                f"actor {actor!r} is not the configured local user nor system_policy")
        # Prevalidate ALL originals before any mutation.
        originals = sorted(
            (self.get(rid) for rid in risk_instance_ids),
            key=lambda item: (
                item.risk_identity_id, item.risk_instance_id,
            ),
        )
        projects = {o.project_id for o in originals}
        if len(projects) != 1:
            raise RiskError("merge requires all instances in one project")
        project_id = projects.pop()
        domains = {o.domain for o in originals}
        if len(domains) != 1:
            raise RiskError("merge requires all instances in one domain")
        subjects = {o.identity.subject_ref for o in originals}
        if len(subjects) != 1:
            raise RiskError(
                "merge cannot cross subjects; all instances must share "
                "the same subject_ref")
        for original in originals:
            self._check_legal(original.current_state, RiskTransitionType.MERGED)
        if adjudication.outcome != AdjudicationOutcome.MERGED_SUPPORTED:
            raise AdjudicationError(
                f"merge requires outcome 'merged_supported'")
        merge_payload = _merge_action_payload(originals, severity, classifier)
        if adjudication.action_payload_hash != content_hash(
            deep_freeze_json(merge_payload)
        ):
            raise AdjudicationError(
                "merge adjudication is not bound to the exact severity and "
                "classifier"
            )
        # VETO 2-15: adjudication must bind ALL target risk identities.
        all_target_ids = sorted(o.identity.risk_identity_id for o in originals)
        self._verify_adjudication(
            adjudication, project_id, _ACTION_MERGE,
            target_risk_instances=originals,
        )

        source_services = {
            id(self._source_acceptance_services.get(o.risk_instance_id))
            for o in originals
        }
        if None in (
            self._source_acceptance_services.get(o.risk_instance_id)
            for o in originals
        ) or len(source_services) != 1:
            raise RiskError(
                "merge requires risks verified by the same source "
                "AcceptanceService"
            )
        source_service = self._source_acceptance_services[originals[0].risk_instance_id]
        inherited_user_confirmation = (
            adjudication.user_confirmed
            or any(original.ever_user_confirmed for original in originals)
        )
        merged_source_snapshot_ids = tuple(sorted({
            snapshot_id
            for original in originals
            for snapshot_id in original.source_snapshot_ids
        }))
        merged_clinical_risk_flags = tuple(sorted({
            flag
            for original in originals
            for flag in original.clinical_risk_flags
        } | set(_clinical_risk_flags(
            merge_payload["severity"], merge_payload["classifier"],
        ))))
        merged_scope = tuple(sorted({
            scope_item
            for original in originals
            for scope_item in original.identity.scope
        }))

        # Prepare every transition and instance before committing any state.
        merged_identity = self._identity_factory(
            project_id=project_id, subject_ref=originals[0].identity.subject_ref,
            domain=originals[0].domain, scope=merged_scope,
            classifier=classifier, derived_from=all_target_ids,
        )
        risk_instance_id = new_id("risk-")
        chain_cursor = self._chain_head.get(project_id, "")
        established = self._make_transition(
            risk_instance_id=risk_instance_id, project_id=project_id,
            from_state="", to_state=RiskLifecycleState.ESTABLISHED,
            transition_type=RiskTransitionType.ESTABLISHED, actor=actor,
            reason=f"merged from {all_target_ids}",
            adjudication_id=adjudication.adjudication_id,
            is_machine_adjudicated=adjudication.is_machine_adjudicated,
            user_confirmed=adjudication.user_confirmed,
            lineage_refs=all_target_ids,
            prev_hash=chain_cursor,
        )
        chain_cursor = established.transition_hash
        instance = _issuer(
            risk_instance_id=risk_instance_id, project_id=project_id,
            identity=merged_identity, domain=originals[0].domain,
            source_snapshot_ids=merged_source_snapshot_ids,
            clinical_risk_flags=merged_clinical_risk_flags,
            established_adjudication_id=adjudication.adjudication_id,
            transitions=(established,), severity=merge_payload["severity"],
            confirmed_by_user=inherited_user_confirmation,
        )
        superseded: Dict[str, RiskInstance] = {}
        for o in originals:
            tr = self._make_transition(
                risk_instance_id=o.risk_instance_id, project_id=project_id,
                from_state=o.current_state, to_state=RiskLifecycleState.SUPERSEDED,
                transition_type=RiskTransitionType.MERGED, actor=actor,
                reason=f"merged into {risk_instance_id}",
                adjudication_id=adjudication.adjudication_id,
                is_machine_adjudicated=adjudication.is_machine_adjudicated,
                user_confirmed=adjudication.user_confirmed,
                lineage_refs=[risk_instance_id],
                prev_hash=chain_cursor,
            )
            chain_cursor = tr.transition_hash
            sup_inst = _issuer(
                risk_instance_id=o.risk_instance_id, project_id=o.project_id,
                identity=o.identity, domain=o.domain,
                source_snapshot_ids=o.source_snapshot_ids,
                clinical_risk_flags=o.clinical_risk_flags,
                established_adjudication_id=o.established_adjudication_id,
                transitions=o.transitions + (tr,),
                severity=o.severity,
                confirmed_by_user=o.confirmed_by_user or adjudication.user_confirmed,
                created_at=o.created_at,
            )
            superseded[o.risk_instance_id] = sup_inst
        self._chain_head[project_id] = chain_cursor
        self._instances[risk_instance_id] = instance
        self._instances.update(superseded)
        self._source_acceptance_services[risk_instance_id] = source_service
        return instance

    def split(
        self, risk_instance_id: str, child_specs: List[Dict[str, Any]], *,
        adjudication: AdjudicationRecord, actor: str = "", reason: str = "",
        _issuer=None,
    ) -> List[RiskInstance]:
        """Split one risk instance into multiple.  Prevalidates all child
        specs before any mutation.

        VETO 2-15: cannot cross subject/domain/project; validates all child
        specs before mutation.
        """
        if len(child_specs) < 2:
            raise RiskError("split requires at least two child specs")
        if _issuer is None:
            raise RiskError("risk-instance issuance authority is unavailable")
        if not actor:
            raise DomainValidationError("split requires an actor")
        if actor != self._local_user and actor != "system_policy":
            raise AdjudicationError(
                f"actor {actor!r} is not the configured local user nor system_policy")
        original = self.get(risk_instance_id)
        project_id = original.project_id
        parent_identity_id = original.identity.risk_identity_id
        if adjudication.outcome != AdjudicationOutcome.DISTINCT_SUPPORTED:
            raise AdjudicationError(
                f"split requires outcome 'distinct_supported'")
        child_specs_hash = content_hash(deep_freeze_json(child_specs))
        if adjudication.action_payload_hash != child_specs_hash:
            raise AdjudicationError(
                "split adjudication is not bound to the exact child specs"
            )
        self._verify_adjudication(
            adjudication, project_id, _ACTION_SPLIT,
            target_risk_instances=[original],
        )
        source_service = self._source_acceptance_services.get(risk_instance_id)
        if source_service is None:
            raise RiskError("split source AcceptanceService binding is missing")
        inherited_user_confirmation = (
            original.ever_user_confirmed or adjudication.user_confirmed
        )

        # VETO 2-15: prevalidate all child specs.
        child_severities: List[str] = []
        for spec in child_specs:
            if type(spec) is not dict:
                raise AdjudicationError("each split child spec must be a dict")
            child_subject = spec.get("subject_ref", original.identity.subject_ref)
            child_domain = spec.get("domain", original.domain)
            if child_subject != original.identity.subject_ref:
                raise AdjudicationError(
                    f"split cannot cross subjects; child spec subject "
                    f"{child_subject!r} differs from original "
                    f"{original.identity.subject_ref!r}")
            if child_domain != original.domain:
                raise AdjudicationError(
                    f"split cannot cross domains; child spec domain "
                    f"{child_domain!r} differs from original {original.domain!r}")
            child_severity = spec.get("severity", original.severity)
            if _severity_rank(child_severity) < _severity_rank(original.severity):
                raise AdjudicationError(
                    "split cannot downgrade the source-risk severity"
                )
            child_severities.append(child_severity)
        self._check_legal(original.current_state, RiskTransitionType.SPLIT)

        # Build all child identities first.
        child_identities = []
        for spec in child_specs:
            child_identity = self._identity_factory(
                project_id=project_id,
                subject_ref=spec.get("subject_ref", original.identity.subject_ref),
                domain=spec.get("domain", original.domain),
                scope=spec.get("scope", list(original.identity.scope)),
                classifier=spec.get("classifier", ""),
                derived_from=[parent_identity_id],
            )
            child_identities.append(child_identity)
        child_identity_ids = [identity.risk_identity_id for identity in child_identities]
        if len(child_identity_ids) != len(set(child_identity_ids)):
            raise AdjudicationError(
                "split child specs produce duplicate risk identities"
            )

        # Prepare all children and the superseded parent before committing.
        children: List[RiskInstance] = []
        child_ids: List[str] = []
        prepared_children: Dict[str, RiskInstance] = {}
        chain_cursor = self._chain_head.get(project_id, "")
        for idx, spec in enumerate(child_specs):
            child_identity = child_identities[idx]
            child_severity = child_severities[idx]
            child_flags = tuple(sorted(
                set(original.clinical_risk_flags)
                | set(_clinical_risk_flags(
                    child_severity, spec.get("classifier", ""),
                ))
            ))
            rid = new_id("risk-")
            established = self._make_transition(
                risk_instance_id=rid, project_id=project_id,
                from_state="", to_state=RiskLifecycleState.ESTABLISHED,
                transition_type=RiskTransitionType.ESTABLISHED, actor=actor,
                reason=f"split from {parent_identity_id}",
                adjudication_id=adjudication.adjudication_id,
                is_machine_adjudicated=adjudication.is_machine_adjudicated,
                user_confirmed=adjudication.user_confirmed,
                lineage_refs=[parent_identity_id],
                prev_hash=chain_cursor,
            )
            chain_cursor = established.transition_hash
            child = _issuer(
                risk_instance_id=rid, project_id=project_id,
                identity=child_identity, domain=spec.get("domain", original.domain),
                source_snapshot_ids=original.source_snapshot_ids,
                clinical_risk_flags=child_flags,
                established_adjudication_id=adjudication.adjudication_id,
                transitions=(established,),
                severity=child_severity,
                confirmed_by_user=inherited_user_confirmation,
            )
            prepared_children[rid] = child
            child_ids.append(rid)
            children.append(child)
        # Supersede the original.
        tr = self._make_transition(
            risk_instance_id=risk_instance_id, project_id=project_id,
            from_state=original.current_state, to_state=RiskLifecycleState.SUPERSEDED,
            transition_type=RiskTransitionType.SPLIT, actor=actor,
            reason=f"split into {child_ids}",
            adjudication_id=adjudication.adjudication_id,
            is_machine_adjudicated=adjudication.is_machine_adjudicated,
            user_confirmed=adjudication.user_confirmed,
            lineage_refs=child_ids,
            prev_hash=chain_cursor,
        )
        chain_cursor = tr.transition_hash
        sup_inst = _issuer(
            risk_instance_id=original.risk_instance_id,
            project_id=original.project_id, identity=original.identity,
            domain=original.domain,
            source_snapshot_ids=original.source_snapshot_ids,
            clinical_risk_flags=original.clinical_risk_flags,
            established_adjudication_id=original.established_adjudication_id,
            transitions=original.transitions + (tr,),
            severity=original.severity,
            confirmed_by_user=original.confirmed_by_user or adjudication.user_confirmed,
            created_at=original.created_at,
        )
        self._chain_head[project_id] = chain_cursor
        self._instances.update(prepared_children)
        self._instances[risk_instance_id] = sup_inst
        for child_id in child_ids:
            self._source_acceptance_services[child_id] = source_service
        return children

    # -- hash chain -------------------------------------------------------

    def _make_transition(
        self, risk_instance_id: str, project_id: str, from_state: str,
        to_state: str, transition_type: str, actor: str, reason: str,
        adjudication_id: str = "", is_machine_adjudicated: bool = True,
        user_confirmed: bool = False, coverage_snapshot_id: str = "",
        lineage_refs: Optional[List[str]] = None,
        prev_hash: Optional[str] = None,
    ) -> RiskTransition:
        chain_predecessor = (
            self._chain_head.get(project_id, "") if prev_hash is None else prev_hash
        )
        tr = RiskTransition(
            transition_id=new_id("rtr-"), risk_instance_id=risk_instance_id,
            project_id=project_id, from_state=from_state, to_state=to_state,
            transition_type=transition_type, actor=actor, reason=reason,
            adjudication_id=adjudication_id,
            is_machine_adjudicated=is_machine_adjudicated,
            user_confirmed=user_confirmed,
            lineage_refs=tuple(lineage_refs or ()),
            coverage_snapshot_id=coverage_snapshot_id,
            prev_hash=chain_predecessor, created_at=now_iso(),
        )
        return tr

    def verify_chain(self, project_id: str) -> bool:
        transitions: Dict[str, RiskTransition] = {}
        for inst in self._instances.values():
            if inst.project_id == project_id:
                for transition in inst.transitions:
                    existing = transitions.get(transition.transition_hash)
                    if existing is not None and existing != transition:
                        return False
                    transitions[transition.transition_hash] = transition
        by_predecessor: Dict[str, RiskTransition] = {}
        for transition in transitions.values():
            if transition.transition_hash != transition.compute_hash():
                return False
            if transition.prev_hash in by_predecessor:
                return False
            by_predecessor[transition.prev_hash] = transition
        prev = ""
        visited = 0
        while prev in by_predecessor:
            transition = by_predecessor[prev]
            prev = transition.transition_hash
            visited += 1
        return (
            visited == len(transitions)
            and prev == self._chain_head.get(project_id, "")
        )


# ---------------------------------------------------------------------------
# Seal + closure-captured factories (closure-only, not module/class attributes)
# ---------------------------------------------------------------------------

def _seal_risk_authority(authority_token: Any, adj_token: Any) -> None:
    candidate_post = RiskCandidate.__post_init__
    candidate_factory = RiskCandidate.from_signal.__func__
    instance_post = RiskInstance.__post_init__
    adj_post = AdjudicationRecord.__post_init__
    issue_adjudication = RiskLifecycle.issue_adjudication
    issue_user_adjudication = RiskLifecycle.issue_user_adjudication
    establish = RiskLifecycle.establish
    transition = RiskLifecycle.transition
    merge = RiskLifecycle.merge
    split = RiskLifecycle.split

    def checked_candidate_post(self, _verified: Any = None) -> None:
        return candidate_post(self, _verified, authority_token)

    def checked_candidate_factory(
        cls, project_id: str, subject_ref: str, domain: str,
        signal_type: str, **kwargs: Any,
    ) -> "RiskCandidate":
        return candidate_factory(
            cls, project_id, subject_ref, domain, signal_type,
            _authority_token=authority_token, **kwargs,
        )

    def checked_instance_post(self, _verified: Any = None) -> None:
        return instance_post(self, _verified, authority_token)

    def checked_adj_post(self, _issued: Any = None) -> None:
        return adj_post(self, _issued, adj_token)

    # Closure-captured factories: not reachable as class attributes.
    def _issue_instance(**kwargs: Any) -> RiskInstance:
        kwargs["_verified"] = authority_token
        return RiskInstance(**kwargs)

    def _issue_adjudication(**kwargs: Any) -> AdjudicationRecord:
        kwargs["_issued"] = adj_token
        return AdjudicationRecord(**kwargs)

    def service_issue_adjudication(self, *args: Any, **kwargs: Any) -> AdjudicationRecord:
        kwargs["_issuer"] = _issue_adjudication
        return issue_adjudication(self, *args, **kwargs)

    def service_issue_user_adjudication(
        self, *args: Any, **kwargs: Any,
    ) -> AdjudicationRecord:
        kwargs["_issuer"] = _issue_adjudication
        return issue_user_adjudication(self, *args, **kwargs)

    def service_establish(self, *args: Any, **kwargs: Any) -> RiskInstance:
        kwargs["_issuer"] = _issue_instance
        return establish(self, *args, **kwargs)

    def service_transition(self, *args: Any, **kwargs: Any) -> RiskInstance:
        kwargs["_issuer"] = _issue_instance
        return transition(self, *args, **kwargs)

    def service_merge(self, *args: Any, **kwargs: Any) -> RiskInstance:
        kwargs["_issuer"] = _issue_instance
        return merge(self, *args, **kwargs)

    def service_split(self, *args: Any, **kwargs: Any) -> List[RiskInstance]:
        kwargs["_issuer"] = _issue_instance
        return split(self, *args, **kwargs)

    RiskCandidate.__post_init__ = checked_candidate_post
    RiskCandidate.from_signal = classmethod(checked_candidate_factory)
    RiskInstance.__post_init__ = checked_instance_post
    AdjudicationRecord.__post_init__ = checked_adj_post
    RiskLifecycle.issue_adjudication = service_issue_adjudication
    RiskLifecycle.issue_user_adjudication = service_issue_user_adjudication
    RiskLifecycle.establish = service_establish
    RiskLifecycle.transition = service_transition
    RiskLifecycle.merge = service_merge
    RiskLifecycle.split = service_split


_seal_risk_authority(_RISK_VERIFIED, _ADJ_ISSUED)
del _seal_risk_authority
del _RISK_VERIFIED
del _ADJ_ISSUED
