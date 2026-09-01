"""Shared risk lifecycle vocabulary, validation helpers and value records."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .entities import (
    DomainValidationError, MmR2Error, content_hash, deep_freeze_json,
    new_id, now_iso, validate_sha256_hex,
)

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



__all__ = [
    "RiskError", "IllegalTransitionError", "AdjudicationError",
    "RiskTransition", "RiskLifecycleState", "RiskTransitionType",
    "AdjudicationOutcome", "AdjudicationEvidenceBinding",
    "CANDIDATE_AUTO_PROMOTE_FORBIDDEN",
]

