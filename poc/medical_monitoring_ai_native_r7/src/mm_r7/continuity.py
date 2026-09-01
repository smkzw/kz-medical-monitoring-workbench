"""Stdlib-only Slice-08A continuity domain core.

R7 records bindings between already-authoritative runs.  R2 remains the sole
owner of risk lifecycle state and transitions; this module only validates and
projects R2 facts.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from types import MappingProxyType
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

SCHEMA_NAME = "r7_continuity"
SCHEMA_VERSION = "mm-r7-slice08a-continuity-v1"
MODES = ("daily", "pre_lock", "post_lock_pre_cfdi")
OBJECT_TYPES = ("risk_instance", "mode_output_item", "query_draft", "evidence_binding")
DISPOSITIONS = (
    "reuse_unchanged", "re_evaluate_changed_data", "re_evaluate_rule_change",
    "re_evaluate_prior_uncertain", "close_with_evidence", "blocked_incompatible",
)
DATA_CHANGE_KINDS = ("unchanged", "added", "revised", "deleted", "cannot_compare", "missing")
__all__ = [
    "SCHEMA_NAME", "SCHEMA_VERSION", "MODES", "OBJECT_TYPES", "DISPOSITIONS",
    "DATA_CHANGE_KINDS", "RiskChangeKind", "RuleScope", "DecisionBaseline",
    "CarryForwardItem", "CarryForwardPlan", "RiskTransition", "ContinuityError",
    "BaselineValidationError", "PlanValidationError", "RiskProjectionError",
    "canonical_json", "canonical_json_bytes", "canonical_digest", "build_decision_baseline",
    "validate_decision_baseline", "determine_disposition", "build_carry_forward_item",
    "build_carry_forward_plan", "validate_carry_forward_plan", "project_risk_change_kind",
    "project_risk_change",
]


class ContinuityError(ValueError):
    code = "continuity_invalid"
    def __init__(self, message: str, *, code: Optional[str] = None) -> None:
        self.code = code or self.code
        self.message = message
        super().__init__(f"{self.code}: {message}")
    def as_error_body(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class BaselineValidationError(ContinuityError):
    code = "invalid_decision_baseline"


class PlanValidationError(ContinuityError):
    code = "invalid_carry_forward_plan"


class RiskProjectionError(ContinuityError):
    code = "invalid_risk_projection"


class RiskChangeKind(str, Enum):
    NEW = "new"
    UPGRADED = "upgraded"
    CONTINUED = "continued"
    DOWNGRADED = "downgraded"
    CLOSED = "closed"
    REOPENED = "reopened"
    NEEDS_REJUDGMENT = "needs_rejudgment"
    @property
    def display_text(self) -> str:
        return {"new": "新增", "upgraded": "升级", "continued": "持续", "downgraded": "降级", "closed": "关闭", "reopened": "重开", "needs_rejudgment": "需重新判断"}[self.value]


# Input values mirror R2; these are not a second lifecycle implementation.
_R2_STATES = frozenset(("established", "escalated", "deescalated", "closed", "reopened", "identity_ambiguous", "superseded", "not_evaluable"))
_R2_TRANSITIONS = frozenset(("established", "escalated", "deescalated", "closed", "reopened", "identity_ambiguous", "superseded", "not_evaluable", "merged", "split"))
_SEVERITY = {"low": 1, "mild": 1, "medium": 2, "moderate": 2, "high": 3, "severe": 3, "serious": 3, "sae": 3, "aesi": 3, "life_threatening": 3}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise TypeError("canonical mappings require string keys")
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not accept non-finite numbers")
        return value
    payload = getattr(value, "canonical_payload", None)
    if callable(payload):
        return _jsonable(payload())
    raise TypeError("unsupported canonical value: %s" % type(value).__name__)


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise TypeError("immutable mappings require string keys")
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("unsupported immutable value: %s" % type(value).__name__)


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    payload = getattr(value, "canonical_payload", None)
    if callable(payload):
        return _plain(payload())
    return value


def _payload(obj: Any, omit: Iterable[str] = ()) -> Dict[str, Any]:
    skip = set(omit)
    return {f.name: _plain(getattr(obj, f.name)) for f in fields(obj) if f.name not in skip}


def _text(value: Any, name: str, error=ContinuityError) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise error(f"{name} must be a non-empty trimmed string")
    return value


def _optional_text(value: Any, name: str, error=ContinuityError) -> str:
    return "" if value in (None, "") else _text(value, name, error)


def _texts(value: Any, name: str, error=ContinuityError, *, sort: bool = True) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, Mapping)):
        raise error(f"{name} must be a sequence of strings")
    try:
        out = tuple(dict.fromkeys(_text(v, name, error) for v in value))
    except TypeError as exc:
        raise error(f"{name} must be a sequence of strings") from exc
    return tuple(sorted(out)) if sort else out


def _sha(value: Any, name: str, error=ContinuityError) -> str:
    if value in (None, ""):
        return ""
    text = _text(value, name, error).lower()
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise error(f"{name} must be a SHA-256 hex digest")
    return text


def _bools(values: Mapping[str, Any], error) -> None:
    for name, value in values.items():
        if type(value) is not bool:
            raise error(f"{name} must be boolean")


def _state(value: Any, name: str, error=RiskProjectionError) -> Optional[str]:
    if value in (None, ""):
        return None
    value = _text(value, name, error)
    value = "deescalated" if value == "de_escalated" else value
    if value not in _R2_STATES:
        raise error(f"{name} is not an R2 lifecycle state")
    return value


def _transition(value: Any, name: str = "transition_type") -> Optional[str]:
    if value in (None, ""):
        return None
    value = _text(value, name, RiskProjectionError)
    value = "deescalated" if value == "de_escalated" else value
    if value not in _R2_TRANSITIONS:
        raise RiskProjectionError(f"{name} is not an R2 transition type")
    return value


def _digest(value: Any, expected: str, name: str, error) -> str:
    if value not in (None, "") and value != expected:
        raise error(f"{name} does not match canonical payload")
    return expected


def _rank(value: Any) -> int:
    if not value:
        return 0
    return _SEVERITY.get(str(value).strip().casefold().replace(" ", "_"), 2)


@dataclass(frozen=True)
class RuleScope:
    governing_rule_revision_ids: Tuple[str, ...] = ()
    changed_applicable_rule_ids: Tuple[str, ...] = ()
    applicability_known: bool = True
    def __post_init__(self) -> None:
        object.__setattr__(self, "governing_rule_revision_ids", _texts(self.governing_rule_revision_ids, "governing_rule_revision_ids", PlanValidationError))
        object.__setattr__(self, "changed_applicable_rule_ids", _texts(self.changed_applicable_rule_ids, "changed_applicable_rule_ids", PlanValidationError))
        _bools({"applicability_known": self.applicability_known}, PlanValidationError)
    @property
    def changed_rule_applies(self) -> bool:
        return bool(self.changed_applicable_rule_ids) and (not self.applicability_known or bool(set(self.governing_rule_revision_ids) & set(self.changed_applicable_rule_ids)))
    def canonical_payload(self) -> Dict[str, Any]:
        return _payload(self)
    def as_dict(self) -> Dict[str, Any]:
        return self.canonical_payload()


@dataclass(frozen=True)
class DecisionBaseline:
    project_id: str = ""
    mode: str = ""
    source_run_id: str = ""
    source_snapshot_id: str = ""
    source_data_cutoff: str = ""
    source_rule_revision_ids: Tuple[str, ...] = ()
    source_decision_version: str = ""
    target_run_id: str = ""
    target_snapshot_id: str = ""
    target_data_cutoff: str = ""
    target_rule_revision_ids: Tuple[str, ...] = ()
    target_decision_version: str = ""
    r5_authority_digest: str = ""
    r6_publication_digest: str = ""
    r6_receipt_digest: str = ""
    source_publication_id: str = ""
    source_public_run_token: str = ""
    source_publication_state: str = "available"
    source_identity_closed: bool = True
    source_coverage_complete: bool = True
    created_at: str = ""
    baseline_digest: str = ""
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self) -> None:
        _text(self.project_id, "project_id", BaselineValidationError)
        if _text(self.mode, "mode", BaselineValidationError) not in MODES:
            raise BaselineValidationError("mode is unsupported")
        for name in ("source_run_id", "source_snapshot_id", "source_data_cutoff", "source_decision_version", "target_run_id", "target_snapshot_id", "target_data_cutoff", "target_decision_version", "r5_authority_digest", "r6_publication_digest", "r6_receipt_digest", "created_at"):
            _text(getattr(self, name), name, BaselineValidationError)
        if self.source_publication_state != "available":
            raise BaselineValidationError("source publication must be available", code="baseline_not_published")
        _bools({"source_identity_closed": self.source_identity_closed, "source_coverage_complete": self.source_coverage_complete}, BaselineValidationError)
        if not self.source_identity_closed or not self.source_coverage_complete:
            raise BaselineValidationError("source identity/coverage is incomplete", code="baseline_source_incomplete")
        if self.schema_name != SCHEMA_NAME or self.schema_version != SCHEMA_VERSION:
            raise BaselineValidationError("unsupported baseline schema")
        object.__setattr__(self, "source_rule_revision_ids", _texts(self.source_rule_revision_ids, "source_rule_revision_ids", BaselineValidationError))
        object.__setattr__(self, "target_rule_revision_ids", _texts(self.target_rule_revision_ids, "target_rule_revision_ids", BaselineValidationError))
        object.__setattr__(self, "source_publication_id", _optional_text(self.source_publication_id, "source_publication_id", BaselineValidationError))
        object.__setattr__(self, "source_public_run_token", _optional_text(self.source_public_run_token, "source_public_run_token", BaselineValidationError))
        object.__setattr__(self, "baseline_digest", _digest(self.baseline_digest, self.compute_digest(), "baseline_digest", BaselineValidationError))
    @property
    def digest(self) -> str:
        return self.baseline_digest
    def canonical_payload(self) -> Dict[str, Any]:
        return _payload(self, ("baseline_digest",))
    def compute_digest(self) -> str:
        return canonical_digest(self.canonical_payload())
    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = self.canonical_payload()
        if include_digest:
            body["baseline_digest"] = self.baseline_digest
        return body
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DecisionBaseline":
        try:
            return cls(**dict(value))
        except (TypeError, ValueError) as exc:
            raise BaselineValidationError("invalid baseline mapping") from exc
    @classmethod
    def from_publication(cls, publication: Mapping[str, Any], **target: Any) -> "DecisionBaseline":
        return build_decision_baseline(publication, **target)


def _first_present(mapping: Mapping[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return default
def _first(mapping: Mapping[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if mapping.get(name) not in (None, ""):
            return mapping[name]
    return default


def build_decision_baseline(
    publication: Mapping[str, Any], *, target_run_id: str, target_snapshot_id: str,
    target_data_cutoff: str, target_decision_version: str,
    target_rule_revision_ids: Sequence[str] = (), created_at: str = "",
) -> DecisionBaseline:
    if not isinstance(publication, Mapping):
        raise BaselineValidationError("publication must be a mapping")
    pub = dict(publication)
    if _first(pub, "publication_state", "state") != "available":
        raise BaselineValidationError("source publication must be available", code="baseline_not_published")
    return DecisionBaseline(
        project_id=_first(pub, "project_id"), mode=_first(pub, "mode"),
        source_run_id=_first(pub, "run_id", "source_run_id"),
        source_snapshot_id=_first(pub, "snapshot_id", "snapshot_token", "snapshot_ref"),
        source_data_cutoff=_first(pub, "data_cutoff", "source_data_cutoff"),
        source_rule_revision_ids=_first(pub, "rule_revision_ids", "rule_tokens", default=()),
        source_decision_version=_first(pub, "decision_version", "medical_decision_version"),
        target_run_id=target_run_id, target_snapshot_id=target_snapshot_id,
        target_data_cutoff=target_data_cutoff, target_rule_revision_ids=target_rule_revision_ids,
        target_decision_version=target_decision_version,
        r5_authority_digest=_first(pub, "r5_authority_digest", "r5_authority_packet_digest", "r5_packet_digest"),
        r6_publication_digest=_first(pub, "r6_publication_digest", "publication_fingerprint"),
        r6_receipt_digest=_first(pub, "r6_receipt_digest", "receipt_set_digest", "receipt_digest"),
        source_publication_id=_first(pub, "publication_id", "source_publication_id"),
        source_public_run_token=_first(pub, "public_run_token", "source_public_run_token"),
        source_publication_state=_first(pub, "publication_state", "state"),
        source_identity_closed=_first_present(pub, "identity_closed", "source_identity_closed", default=True),
        source_coverage_complete=_first_present(pub, "coverage_complete", "source_coverage_complete", "listing_complete", default=True),
        created_at=created_at or _first(pub, "created_at", "published_at"),
    )


def validate_decision_baseline(baseline: DecisionBaseline, *, project_id: Optional[str] = None, mode: Optional[str] = None) -> None:
    if not isinstance(baseline, DecisionBaseline):
        raise BaselineValidationError("expected DecisionBaseline")
    if project_id is not None and baseline.project_id != project_id:
        raise BaselineValidationError("baseline project mismatch", code="baseline_project_mismatch")
    if mode is not None and baseline.mode != mode:
        raise BaselineValidationError("baseline mode mismatch", code="baseline_mode_mismatch")
    if baseline.compute_digest() != baseline.baseline_digest:
        raise BaselineValidationError("baseline digest mismatch", code="baseline_digest_mismatch")


def determine_disposition(
    *, object_type: str, data_change_kind: str = "unchanged", current_present: bool = True,
    prior_risk_state: Optional[str] = None, prior_severity: Optional[str] = None,
    governing_rule_revision_ids: Sequence[str] = (),
    changed_applicable_rule_ids: Sequence[str] = (), rule_applicability_known: bool = True,
    prior_uncertain: bool = False, identity_compatible: bool = True,
    source_compatible: bool = True, output_contract_compatible: bool = True,
    source_publication_state: str = "available", same_project: bool = True,
    same_mode: bool = True, source_artifact_id: str = "", source_artifact_sha256: str = "",
    artifact_verified: bool = False, artifact_member_verified: bool = False,
    reuse_reviewed: bool = False, closure_evidence_refs: Sequence[str] = (),
    closure_allowed: bool = False, current_listing_complete: bool = False,
    baseline_eligible: bool = False, query_status: str = "draft",
    query_is_sent: bool = False, query_is_closed: bool = False,
    query_is_user_confirmed: bool = False,
) -> str:
    if object_type not in OBJECT_TYPES:
        raise PlanValidationError("unsupported object_type")
    _bools({"current_present": current_present, "rule_applicability_known": rule_applicability_known, "prior_uncertain": prior_uncertain, "identity_compatible": identity_compatible, "source_compatible": source_compatible, "output_contract_compatible": output_contract_compatible, "same_project": same_project, "same_mode": same_mode, "artifact_verified": artifact_verified, "artifact_member_verified": artifact_member_verified, "reuse_reviewed": reuse_reviewed, "closure_allowed": closure_allowed, "current_listing_complete": current_listing_complete, "baseline_eligible": baseline_eligible, "query_is_sent": query_is_sent, "query_is_closed": query_is_closed, "query_is_user_confirmed": query_is_user_confirmed}, PlanValidationError)
    change = _change_kind(data_change_kind, current_present)
    prior = _state(prior_risk_state, "prior_risk_state", PlanValidationError)
    governing = _texts(governing_rule_revision_ids, "governing_rule_revision_ids", PlanValidationError)
    changed = _texts(changed_applicable_rule_ids, "changed_applicable_rule_ids", PlanValidationError)
    if not (identity_compatible and source_compatible and output_contract_compatible and same_project and same_mode and source_publication_state == "available"):
        return "blocked_incompatible"
    if object_type == "query_draft" and (query_status != "draft" or query_is_sent or query_is_closed or query_is_user_confirmed):
        return "re_evaluate_prior_uncertain"
    if change in {"deleted", "missing"} or not current_present:
        return "re_evaluate_changed_data"
    if changed and (not rule_applicability_known or bool(set(governing) & set(changed))):
        return "re_evaluate_rule_change"
    if prior_uncertain or prior in {"identity_ambiguous", "not_evaluable"}:
        return "re_evaluate_prior_uncertain"
    if change in {"added", "revised", "cannot_compare"}:
        return "re_evaluate_changed_data"
    if closure_allowed and closure_evidence_refs and current_listing_complete and baseline_eligible:
        return "close_with_evidence"
    if change == "unchanged" and source_artifact_id and source_artifact_sha256 and artifact_verified and artifact_member_verified and reuse_reviewed:
        return "reuse_unchanged"
    return "re_evaluate_changed_data"


def _change_kind(value: Any, present: bool) -> str:
    if not present and value in (None, "", "unchanged"):
        return "missing"
    value = "unchanged" if value in (None, "") else _text(value, "data_change_kind", PlanValidationError)
    value = {"removed": "deleted", "absent": "missing"}.get(value, value)
    if value not in DATA_CHANGE_KINDS:
        raise PlanValidationError("unsupported data_change_kind")
    return value


@dataclass(frozen=True)
class CarryForwardItem:
    object_type: str = ""
    object_ref: str = ""
    disposition: str = ""
    ordinal: int = 0
    source_run_id: str = ""
    source_publication_id: str = ""
    source_public_run_token: str = ""
    target_run_id: str = ""
    source_object_id: str = ""
    target_object_id: str = ""
    source_identity: str = ""
    target_identity: str = ""
    source_project_id: str = ""
    target_project_id: str = ""
    source_mode: str = ""
    target_mode: str = ""
    source_publication_state: str = "available"
    source_artifact_id: str = ""
    source_artifact_sha256: str = ""
    artifact_verified: bool = False
    artifact_member_verified: bool = False
    data_change_kind: str = "unchanged"
    current_present: bool = True
    prior_risk_state: Optional[str] = None
    current_risk_state: Optional[str] = None
    prior_severity: Optional[str] = None
    current_severity: Optional[str] = None
    governing_rule_revision_ids: Tuple[str, ...] = ()
    changed_applicable_rule_ids: Tuple[str, ...] = ()
    rule_applicability_known: bool = True
    identity_compatible: bool = True
    source_compatible: bool = True
    output_contract_compatible: bool = True
    reuse_reviewed: bool = False
    evidence_summary: Any = field(default_factory=dict)
    evidence_refs: Tuple[str, ...] = ()
    closure_evidence_refs: Tuple[str, ...] = ()
    closure_allowed: bool = False
    current_listing_complete: bool = False
    baseline_eligible: bool = False
    reason: str = ""
    attribution: str = ""
    query_status: str = "draft"
    query_is_sent: bool = False
    query_is_closed: bool = False
    query_is_user_confirmed: bool = False
    r2_transition_type: str = ""
    risk_change_kind: Optional[str] = None
    item_digest: str = ""
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self) -> None:
        if self.object_type not in OBJECT_TYPES or not _text(self.object_ref, "object_ref", PlanValidationError) or self.disposition not in DISPOSITIONS:
            raise PlanValidationError("invalid carry-forward item identity/disposition")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise PlanValidationError("ordinal must be a non-negative integer")
        _bools({"current_present": self.current_present, "artifact_verified": self.artifact_verified, "artifact_member_verified": self.artifact_member_verified, "rule_applicability_known": self.rule_applicability_known, "identity_compatible": self.identity_compatible, "source_compatible": self.source_compatible, "output_contract_compatible": self.output_contract_compatible, "reuse_reviewed": self.reuse_reviewed, "closure_allowed": self.closure_allowed, "current_listing_complete": self.current_listing_complete, "baseline_eligible": self.baseline_eligible, "query_is_sent": self.query_is_sent, "query_is_closed": self.query_is_closed, "query_is_user_confirmed": self.query_is_user_confirmed}, PlanValidationError)
        change = _change_kind(self.data_change_kind, self.current_present)
        prior, current = _state(self.prior_risk_state, "prior_risk_state", PlanValidationError), _state(self.current_risk_state, "current_risk_state", PlanValidationError)
        transition = _transition(self.r2_transition_type)
        governing, changed = _texts(self.governing_rule_revision_ids, "governing_rule_revision_ids", PlanValidationError), _texts(self.changed_applicable_rule_ids, "changed_applicable_rule_ids", PlanValidationError)
        if self.source_publication_state != "available" and self.disposition != "blocked_incompatible":
            raise PlanValidationError("source publication must be available")
        _text(self.reason, "reason", PlanValidationError)
        if self.object_type == "query_draft" and (self.query_status != "draft" or self.query_is_sent or self.query_is_closed or self.query_is_user_confirmed):
            raise PlanValidationError("query drafts must remain draft-only")
        if self.disposition == "reuse_unchanged":
            if not (self.source_artifact_id and _sha(self.source_artifact_sha256, "source_artifact_sha256", PlanValidationError) and self.artifact_verified and self.artifact_member_verified and self.reuse_reviewed and self.current_present and change == "unchanged" and not RuleScope(governing, changed, self.rule_applicability_known).changed_rule_applies):
                raise PlanValidationError("reuse_unchanged requires explicit artifact/object/rule verification")
            if self.source_identity and self.target_identity and self.source_identity != self.target_identity:
                raise PlanValidationError("object identity changed")
            if not (self.identity_compatible and self.source_compatible and self.output_contract_compatible):
                raise PlanValidationError("incompatible object cannot be reused")
            if self.source_project_id and self.target_project_id and self.source_project_id != self.target_project_id:
                raise PlanValidationError("project identity changed")
            if self.source_mode and self.target_mode and self.source_mode != self.target_mode:
                raise PlanValidationError("mode identity changed")
        if self.disposition == "close_with_evidence" and not (self.closure_allowed and self.closure_evidence_refs and self.current_present and self.current_listing_complete and self.baseline_eligible and current in (None, "closed") and transition in (None, "closed")):
            raise PlanValidationError("close_with_evidence requires current R2 evidence")
        if self.risk_change_kind is not None:
            try: RiskChangeKind(self.risk_change_kind)
            except ValueError as exc: raise PlanValidationError("unsupported risk_change_kind") from exc
        if self.schema_name != SCHEMA_NAME or self.schema_version != SCHEMA_VERSION:
            raise PlanValidationError("unsupported item schema")
        for name in ("source_run_id", "source_publication_id", "source_public_run_token", "target_run_id", "source_object_id", "target_object_id", "source_identity", "target_identity", "source_project_id", "target_project_id", "source_mode", "target_mode", "source_artifact_id", "attribution"):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name, PlanValidationError))
        object.__setattr__(self, "source_artifact_sha256", _sha(self.source_artifact_sha256, "source_artifact_sha256", PlanValidationError))
        object.__setattr__(self, "data_change_kind", change); object.__setattr__(self, "prior_risk_state", prior); object.__setattr__(self, "current_risk_state", current); object.__setattr__(self, "r2_transition_type", transition or "")
        object.__setattr__(self, "governing_rule_revision_ids", governing); object.__setattr__(self, "changed_applicable_rule_ids", changed); object.__setattr__(self, "evidence_refs", _texts(self.evidence_refs, "evidence_refs", PlanValidationError, sort=False)); object.__setattr__(self, "closure_evidence_refs", _texts(self.closure_evidence_refs, "closure_evidence_refs", PlanValidationError, sort=False)); object.__setattr__(self, "evidence_summary", _freeze(self.evidence_summary)); object.__setattr__(self, "item_digest", _digest(self.item_digest, self.compute_digest(), "item_digest", PlanValidationError))
    @property
    def digest(self) -> str: return self.item_digest
    @property
    def rule_scope(self) -> RuleScope: return RuleScope(self.governing_rule_revision_ids, self.changed_applicable_rule_ids, self.rule_applicability_known)
    @property
    def absence_is_not_resolution(self) -> bool: return not self.current_present or self.data_change_kind in {"deleted", "missing"}
    def canonical_payload(self) -> Dict[str, Any]: return _payload(self, ("item_digest",))
    def compute_digest(self) -> str: return canonical_digest(self.canonical_payload())
    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = self.canonical_payload()
        if include_digest: body["item_digest"] = self.item_digest
        return body
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CarryForwardItem":
        try: return cls(**dict(value))
        except (TypeError, ValueError) as exc: raise PlanValidationError("invalid item mapping") from exc


def build_carry_forward_item(value: Mapping[str, Any], *, ordinal: Optional[int] = None) -> CarryForwardItem:
    if not isinstance(value, Mapping): raise PlanValidationError("item input must be a mapping")
    data = dict(value)
    if ordinal is not None: data["ordinal"] = ordinal
    if not data.get("disposition"):
        data["disposition"] = determine_disposition(**{k: data[k] for k in ("object_type", "data_change_kind", "current_present", "prior_risk_state", "governing_rule_revision_ids", "changed_applicable_rule_ids", "rule_applicability_known", "prior_uncertain", "identity_compatible", "source_compatible", "output_contract_compatible", "source_publication_state", "same_project", "same_mode", "source_artifact_id", "source_artifact_sha256", "artifact_verified", "artifact_member_verified", "reuse_reviewed", "closure_evidence_refs", "closure_allowed", "current_listing_complete", "baseline_eligible", "query_status", "query_is_sent", "query_is_closed", "query_is_user_confirmed") if k in data})
    data.pop("prior_uncertain", None); data.pop("same_project", None); data.pop("same_mode", None)
    return CarryForwardItem(**data)


@dataclass(frozen=True)
class CarryForwardPlan:
    project_id: str = ""
    mode: str = ""
    execution_basis: str = "full"
    target_run_id: str = ""
    target_snapshot_id: str = ""
    target_data_cutoff: str = ""
    target_rule_revision_ids: Tuple[str, ...] = ()
    target_decision_version: str = ""
    baseline: Optional[DecisionBaseline] = None
    baseline_source_run_id: str = ""
    baseline_source_publication_id: str = ""
    baseline_source_public_run_token: str = ""
    r5_authority_digest: str = ""
    r6_publication_digest: str = ""
    r6_receipt_digest: str = ""
    r6_output_set_digest: str = ""
    items: Tuple[CarryForwardItem, ...] = ()
    status: str = "staging"
    created_at: str = ""
    updated_at: str = ""
    plan_digest: str = ""
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self) -> None:
        project = _text(self.project_id, "project_id", PlanValidationError)
        mode = _text(self.mode, "mode", PlanValidationError)
        basis = _text(self.execution_basis, "execution_basis", PlanValidationError)
        if mode not in MODES or basis not in {"full", "incremental"} or self.status not in {"staging", "verified", "published", "blocked"}:
            raise PlanValidationError("invalid plan identity/status")
        if mode in {"pre_lock", "post_lock_pre_cfdi"} and basis != "full":
            raise PlanValidationError("mode requires full execution basis")
        for name in ("target_run_id", "target_snapshot_id", "target_data_cutoff", "target_decision_version", "created_at", "updated_at"):
            _text(getattr(self, name), name, PlanValidationError)
        if self.schema_name != SCHEMA_NAME or self.schema_version != SCHEMA_VERSION: raise PlanValidationError("unsupported plan schema")
        baseline = self.baseline
        if baseline is not None:
            validate_decision_baseline(baseline, project_id=self.project_id, mode=self.mode)
            if (baseline.target_run_id, baseline.target_snapshot_id, baseline.target_data_cutoff, baseline.target_decision_version) != (self.target_run_id, self.target_snapshot_id, self.target_data_cutoff, self.target_decision_version): raise PlanValidationError("baseline target identity mismatch")
        supplied_rules = _texts(self.target_rule_revision_ids, "target_rule_revision_ids", PlanValidationError)
        if baseline and supplied_rules and supplied_rules != baseline.target_rule_revision_ids:
            raise PlanValidationError("baseline rule scope mismatch")
        rules = supplied_rules or (baseline.target_rule_revision_ids if baseline else ())
        r5 = self.r5_authority_digest or (baseline.r5_authority_digest if baseline else ""); r6 = self.r6_publication_digest or (baseline.r6_publication_digest if baseline else ""); receipt = self.r6_receipt_digest or (baseline.r6_receipt_digest if baseline else "")
        for name, value in (("r5_authority_digest", r5), ("r6_publication_digest", r6), ("r6_receipt_digest", receipt)): _text(value, name, PlanValidationError)
        raw_items = tuple(self.items)
        if any(not isinstance(item, CarryForwardItem) for item in raw_items):
            raise PlanValidationError("items must contain CarryForwardItem records")
        items = tuple(sorted(raw_items, key=lambda item: (item.ordinal, item.object_type, item.object_ref)))
        if any(item.ordinal != i for i, item in enumerate(items)):
            raise PlanValidationError("items must have contiguous ordinals")
        if len({(item.object_type, item.object_ref) for item in items}) != len(items):
            raise PlanValidationError("duplicate object identity")
        for item in items:
            if item.target_run_id and item.target_run_id != self.target_run_id:
                raise PlanValidationError("item target run mismatch")
            if item.target_project_id and item.target_project_id != self.project_id:
                raise PlanValidationError("item target project mismatch")
            if item.target_mode and item.target_mode != self.mode:
                raise PlanValidationError("item target mode mismatch")
        object.__setattr__(self, "target_rule_revision_ids", rules)
        object.__setattr__(self, "r5_authority_digest", r5)
        object.__setattr__(self, "r6_publication_digest", r6)
        object.__setattr__(self, "r6_receipt_digest", receipt)
        r6_out = self.r6_output_set_digest or ""
        if r6_out:
            r6_out = _sha(r6_out, "r6_output_set_digest", PlanValidationError)
        object.__setattr__(self, "r6_output_set_digest", r6_out)
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "baseline_source_run_id", self.baseline_source_run_id or (baseline.source_run_id if baseline else ""))
        object.__setattr__(self, "baseline_source_publication_id", self.baseline_source_publication_id or (baseline.source_publication_id if baseline else ""))
        object.__setattr__(self, "baseline_source_public_run_token", self.baseline_source_public_run_token or (baseline.source_public_run_token if baseline else ""))
        object.__setattr__(self, "plan_digest", _digest(self.plan_digest, self.compute_digest(), "plan_digest", PlanValidationError))
    @property
    def digest(self) -> str: return self.plan_digest
    @property
    def counts(self) -> Dict[str, int]: return {d: sum(item.disposition == d for item in self.items) for d in DISPOSITIONS}
    def canonical_payload(self) -> Dict[str, Any]: return _payload(self, ("plan_digest",))
    def compute_digest(self) -> str: return canonical_digest(_payload(self, ("plan_digest", "status", "updated_at")))
    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = self.canonical_payload()
        if self.baseline is not None:
            body["baseline"] = self.baseline.as_dict()
        body["counts"] = self.counts
        if include_digest:
            body["plan_digest"] = self.plan_digest
        return body
    def validate(self) -> None:
        if self.compute_digest() != self.plan_digest: raise PlanValidationError("plan digest mismatch", code="plan_digest_mismatch")
        for item in self.items:
            if item.compute_digest() != item.item_digest: raise PlanValidationError("item digest mismatch", code="item_digest_mismatch")
    def with_status(self, status: str) -> "CarryForwardPlan":
        allowed = {"staging": {"staging", "verified", "blocked"}, "verified": {"verified", "published", "blocked"}, "published": {"published"}, "blocked": {"blocked", "staging"}}
        if status not in allowed[self.status]: raise PlanValidationError("illegal plan status transition")
        return replace(self, status=status, plan_digest="")
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CarryForwardPlan":
        data = dict(value); data.pop("counts", None); data["baseline"] = DecisionBaseline.from_mapping(data["baseline"]) if isinstance(data.get("baseline"), Mapping) else data.get("baseline"); data["items"] = tuple(i if isinstance(i, CarryForwardItem) else CarryForwardItem.from_mapping(i) for i in data.get("items", ()))
        try: return cls(**data)
        except (TypeError, ValueError) as exc: raise PlanValidationError("invalid plan mapping") from exc


def build_carry_forward_plan(*, project_id: str, mode: str, target_run_id: str, target_snapshot_id: str, target_data_cutoff: str, target_decision_version: str, items: Iterable[CarryForwardItem], baseline: Optional[DecisionBaseline] = None, target_rule_revision_ids: Sequence[str] = (), execution_basis: str = "full", r5_authority_digest: str = "", r6_publication_digest: str = "", r6_receipt_digest: str = "", r6_output_set_digest: str = "", status: str = "staging", created_at: str, updated_at: Optional[str] = None) -> CarryForwardPlan:
    return CarryForwardPlan(project_id=project_id, mode=mode, execution_basis=execution_basis, target_run_id=target_run_id, target_snapshot_id=target_snapshot_id, target_data_cutoff=target_data_cutoff, target_rule_revision_ids=target_rule_revision_ids, target_decision_version=target_decision_version, baseline=baseline, r5_authority_digest=r5_authority_digest, r6_publication_digest=r6_publication_digest, r6_receipt_digest=r6_receipt_digest, r6_output_set_digest=r6_output_set_digest, items=tuple(i if isinstance(i, CarryForwardItem) else CarryForwardItem.from_mapping(i) for i in items), status=status, created_at=created_at, updated_at=updated_at or created_at)


def validate_carry_forward_plan(plan: CarryForwardPlan) -> None:
    if not isinstance(plan, CarryForwardPlan): raise PlanValidationError("expected CarryForwardPlan")
    plan.validate()


def project_risk_change_kind(*, from_state: Optional[str], to_state: str, transition_type: Optional[str] = None, from_severity: Optional[str] = None, to_severity: Optional[str] = None, identity_ambiguous: bool = False, lineage_changed: bool = False, data_missing: bool = False) -> RiskChangeKind:
    before, after, transition = _state(from_state, "from_state"), _state(to_state, "to_state"), _transition(transition_type)
    _bools({"identity_ambiguous": identity_ambiguous, "lineage_changed": lineage_changed, "data_missing": data_missing}, RiskProjectionError)
    if after is None: raise RiskProjectionError("to_state is required")
    uncertain = data_missing or identity_ambiguous or lineage_changed or after in {"identity_ambiguous", "not_evaluable", "superseded"}
    if uncertain:
        if transition in {"closed", "reopened", "escalated", "deescalated"}:
            raise RiskProjectionError("uncertain risk cannot use a definitive transition")
        return RiskChangeKind.NEEDS_REJUDGMENT
    if before in {"superseded", "not_evaluable"}:
        if before == after and transition is None:
            return RiskChangeKind.NEEDS_REJUDGMENT
        raise RiskProjectionError("terminal R2 identity cannot be restaged")
    if before is None:
        if after != "established" or transition not in (None, "established"): raise RiskProjectionError("new risk requires R2 established")
        return RiskChangeKind.NEW
    if before == "closed":
        if after != "reopened" or transition != "reopened": raise RiskProjectionError("closed risk may only reopen through R2")
        return RiskChangeKind.REOPENED
    if transition:
        expected = {"established": "established", "escalated": "escalated", "deescalated": "deescalated", "closed": "closed", "identity_ambiguous": "identity_ambiguous", "not_evaluable": "not_evaluable", "superseded": "superseded", "merged": "superseded", "split": "superseded"}.get(transition)
        if transition == "reopened" or expected is None or expected != after: raise RiskProjectionError("R2 transition target mismatch")
        if transition == "established":
            if before != "identity_ambiguous": raise RiskProjectionError("established transition requires identity ambiguity resolution")
            return RiskChangeKind.NEEDS_REJUDGMENT
    if after == "closed":
        if transition != "closed": raise RiskProjectionError("closed projection requires R2 closed")
        return RiskChangeKind.CLOSED
    if after == "reopened": raise RiskProjectionError("reopened requires closed prior state")
    if transition == "escalated" or _rank(to_severity) > _rank(from_severity): return RiskChangeKind.UPGRADED
    if transition == "deescalated": return RiskChangeKind.DOWNGRADED
    if _rank(to_severity) < _rank(from_severity): return RiskChangeKind.NEEDS_REJUDGMENT
    if after == before and after in {"established", "escalated", "deescalated"}: return RiskChangeKind.CONTINUED
    return RiskChangeKind.NEEDS_REJUDGMENT


@dataclass(frozen=True)
class RiskTransition:
    risk_identity_id: str = ""
    project_id: str = ""
    from_state: Optional[str] = None
    to_state: str = ""
    transition_type: str = ""
    from_severity: Optional[str] = None
    to_severity: Optional[str] = None
    change_kind: str = ""
    reason_category: str = ""
    reason: str = ""
    current_source_ref: str = ""
    comparison_source_ref: str = ""
    evidence_refs: Tuple[str, ...] = ()
    identity_ambiguous: bool = False
    lineage_changed: bool = False
    data_missing: bool = False
    created_at: str = ""
    transition_digest: str = ""
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self) -> None:
        _text(self.risk_identity_id, "risk_identity_id", RiskProjectionError); _text(self.project_id, "project_id", RiskProjectionError); before, after, transition = _state(self.from_state, "from_state"), _state(self.to_state, "to_state"), _transition(self.transition_type); _text(self.reason_category, "reason_category", RiskProjectionError); _text(self.reason, "reason", RiskProjectionError); _text(self.current_source_ref, "current_source_ref", RiskProjectionError); _text(self.comparison_source_ref, "comparison_source_ref", RiskProjectionError); _text(self.created_at, "created_at", RiskProjectionError); _bools({"identity_ambiguous": self.identity_ambiguous, "lineage_changed": self.lineage_changed, "data_missing": self.data_missing}, RiskProjectionError); evidence = _texts(self.evidence_refs, "evidence_refs", RiskProjectionError, sort=False)
        try: kind = RiskChangeKind(self.change_kind)
        except ValueError as exc: raise RiskProjectionError("unsupported change_kind") from exc
        if project_risk_change_kind(from_state=before, to_state=after or "", transition_type=transition, from_severity=self.from_severity, to_severity=self.to_severity, identity_ambiguous=self.identity_ambiguous, lineage_changed=self.lineage_changed, data_missing=self.data_missing) != kind: raise RiskProjectionError("change_kind does not match R2 facts")
        if kind == RiskChangeKind.CLOSED and not evidence: raise RiskProjectionError("closed projection requires evidence")
        if self.schema_name != SCHEMA_NAME or self.schema_version != SCHEMA_VERSION: raise RiskProjectionError("unsupported transition schema")
        object.__setattr__(self, "from_state", before); object.__setattr__(self, "to_state", after or ""); object.__setattr__(self, "transition_type", transition or ""); object.__setattr__(self, "change_kind", kind.value); object.__setattr__(self, "evidence_refs", evidence); object.__setattr__(self, "transition_digest", _digest(self.transition_digest, self.compute_digest(), "transition_digest", RiskProjectionError))
    @property
    def risk_change_kind(self) -> RiskChangeKind: return RiskChangeKind(self.change_kind)
    @property
    def display_text(self) -> str: return self.risk_change_kind.display_text
    @property
    def absence_is_not_resolution(self) -> bool: return self.data_missing
    def canonical_payload(self) -> Dict[str, Any]: return _payload(self, ("transition_digest",))
    def compute_digest(self) -> str: return canonical_digest(self.canonical_payload())
    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = self.canonical_payload(); body["change_kind_text"] = self.display_text
        if include_digest: body["transition_digest"] = self.transition_digest
        return body
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RiskTransition":
        data = dict(value); data.pop("change_kind_text", None)
        try: return cls(**data)
        except (TypeError, ValueError) as exc: raise RiskProjectionError("invalid transition mapping") from exc


def project_risk_change(*, risk_identity_id: str, project_id: str, from_state: Optional[str], to_state: str, reason: str, current_source_ref: str, comparison_source_ref: str, created_at: str, transition_type: Optional[str] = None, from_severity: Optional[str] = None, to_severity: Optional[str] = None, reason_category: str = "", evidence_refs: Sequence[str] = (), identity_ambiguous: bool = False, lineage_changed: bool = False, data_missing: bool = False) -> RiskTransition:
    kind = project_risk_change_kind(from_state=from_state, to_state=to_state, transition_type=transition_type, from_severity=from_severity, to_severity=to_severity, identity_ambiguous=identity_ambiguous, lineage_changed=lineage_changed, data_missing=data_missing)
    return RiskTransition(risk_identity_id=risk_identity_id, project_id=project_id, from_state=from_state, to_state=to_state, transition_type=transition_type or "", from_severity=from_severity, to_severity=to_severity, change_kind=kind.value, reason_category=reason_category or kind.value, reason=reason, current_source_ref=current_source_ref, comparison_source_ref=comparison_source_ref, evidence_refs=evidence_refs, identity_ambiguous=identity_ambiguous, lineage_changed=lineage_changed, data_missing=data_missing, created_at=created_at)
