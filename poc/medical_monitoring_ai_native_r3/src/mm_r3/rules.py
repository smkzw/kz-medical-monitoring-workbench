"""R3-C natural-language rule lifecycle: draft, simulation, versioned
activation, and evaluation scope.

Implements the Design §7 contract: natural-language rules must be broken
into a structured *draft*, *simulated* against synthetic facts, and can
only become active through *explicit versioned activation* with a frozen
evaluation scope.  A rule can never directly change existing conclusions
(Design: LLM/Agent only submit candidates, never auto-promote canonical
facts; 自然语言规则只能先形成结构化草稿并模拟；激活需显式版本与
evaluation scope).

Three evaluation scopes (plan R3 step 8):

* ``full_history`` -- re-evaluate all historical snapshots.
* ``current_snapshot`` -- evaluate only the current snapshot.
* ``future_only`` -- evaluate only future snapshots (no re-evaluation).

Design grounding: system design §§5.2,7,16 (activated rules; rule/knowledge
version frozen per Run; 规则、mapping、knowledge、identity 算法或来源
范围变化导致"不再命中"时，transition 使用 superseded 或 not_evaluable，
不得伪装为临床问题已解决); plan R3 step 8.

Contracts
---------
* :class:`EvaluationScopeKind` -- the three scope kinds.
* :class:`EvaluationScope` -- a frozen scope declaration (kind + bounds).
* :class:`RuleCondition` -- one structured condition extracted from NL.
* :class:`RuleDraft` -- a structured draft of a natural-language rule.
* :class:`SimulationOutcome` / :class:`RuleSimulation` -- simulation
  results proving a draft was exercised before activation.
* :class:`RuleActivation` -- the explicit, versioned activation instance.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .primitives import (
    content_hash,
    deep_freeze_json,
    new_id,
    now_iso,
    validate_iso_date,
    validate_nonempty_str,
    validate_sha256_hex,
)
from .schema_registry import default_registry

__all__ = [
    "EvaluationScopeKind",
    "EVALUATION_SCOPE_KINDS",
    "EvaluationScope",
    "ConditionOperator",
    "CONDITION_OPERATORS",
    "RuleCondition",
    "RuleDraft",
    "RuleDraftStatus",
    "RULE_DRAFT_STATUSES",
    "SimulationMatch",
    "SimulationOutcome",
    "RuleSimulation",
    "RuleActivation",
    "RuleActivationError",
    "simulate_rule",
    "activate_rule",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class RuleActivationError(Exception):
    """Natural-language rule lifecycle violation."""


_LIFECYCLE_VERIFIED = object()


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EvaluationScopeKind:
    """The three evaluation scopes for rule activation (plan R3 step 8).

    * ``full_history`` -- re-evaluate all historical snapshots.
    * ``current_snapshot`` -- evaluate only the current snapshot.
    * ``future_only`` -- evaluate only future snapshots.
    """
    FULL_HISTORY = "full_history"
    CURRENT_SNAPSHOT = "current_snapshot"
    FUTURE_ONLY = "future_only"


EVALUATION_SCOPE_KINDS: Tuple[str, ...] = (
    EvaluationScopeKind.FULL_HISTORY,
    EvaluationScopeKind.CURRENT_SNAPSHOT,
    EvaluationScopeKind.FUTURE_ONLY,
)


class ConditionOperator:
    """Comparison operators for structured rule conditions."""
    EQ = "eq"           # equals
    NE = "ne"           # not equals
    GT = "gt"           # greater than
    GE = "ge"           # greater than or equal
    LT = "lt"           # less than
    LE = "le"           # less than or equal
    CONTAINS = "contains"   # substring / list membership
    IN = "in"           # value in a set
    NOT_IN = "not_in"   # value not in a set
    IS_MISSING = "is_missing"
    IS_PRESENT = "is_present"


CONDITION_OPERATORS: Tuple[str, ...] = (
    ConditionOperator.EQ,
    ConditionOperator.NE,
    ConditionOperator.GT,
    ConditionOperator.GE,
    ConditionOperator.LT,
    ConditionOperator.LE,
    ConditionOperator.CONTAINS,
    ConditionOperator.IN,
    ConditionOperator.NOT_IN,
    ConditionOperator.IS_MISSING,
    ConditionOperator.IS_PRESENT,
)


class RuleDraftStatus:
    """Lifecycle status of a rule draft."""
    DRAFT = "draft"
    SIMULATED = "simulated"
    ACTIVATED = "activated"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


RULE_DRAFT_STATUSES: Tuple[str, ...] = (
    RuleDraftStatus.DRAFT,
    RuleDraftStatus.SIMULATED,
    RuleDraftStatus.ACTIVATED,
    RuleDraftStatus.SUPERSEDED,
    RuleDraftStatus.REJECTED,
)


def _validate_enum(value: str, allowed: Tuple[str, ...], field_name: str) -> str:
    if value not in allowed:
        raise RuleActivationError(f"{field_name}={value!r} not in {allowed}")
    return value


# ---------------------------------------------------------------------------
# EvaluationScope (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvaluationScope:
    """A frozen evaluation-scope declaration bound to one rule activation.

    Design §7: 更新先产生影响分析，再选择全历史、当前快照或仅未来范围.

    ``scope_kind`` selects the temporal extent.  ``domain_scope`` limits
    the rule to specific domains (e.g. ``("AE", "LB")``).  Empty
    ``domain_scope`` means "all applicable domains" -- but this is an
    *explicit* declaration, never a silent default that broadens scope.
    """
    schema_name: str = "r3_evaluation_scope"
    schema_version: str = "1"
    scope_kind: str = EvaluationScopeKind.CURRENT_SNAPSHOT
    domain_scope: Tuple[str, ...] = ()
    subject_scope: Tuple[str, ...] = ()
    valid_from: str = ""
    valid_until: Optional[str] = None
    notes: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        _validate_enum(self.scope_kind, EVALUATION_SCOPE_KINDS, "EvaluationScope.scope_kind")
        object.__setattr__(self, "domain_scope", tuple(sorted(set(self.domain_scope))))
        object.__setattr__(self, "subject_scope", tuple(sorted(set(self.subject_scope))))
        if self.valid_from:
            validate_iso_date(self.valid_from, "EvaluationScope.valid_from")
        if self.valid_until:
            validate_iso_date(self.valid_until, "EvaluationScope.valid_until")
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise RuleActivationError(
                "EvaluationScope.valid_until must be on or after valid_from"
            )
        if self.scope_kind == EvaluationScopeKind.FUTURE_ONLY and not self.valid_from:
            raise RuleActivationError(
                "future_only evaluation scope requires an explicit valid_from boundary"
            )

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "scope_kind": self.scope_kind,
            "domain_scope": list(self.domain_scope),
            "subject_scope": list(self.subject_scope),
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "notes": self.notes,
        }

    @property
    def is_full_history(self) -> bool:
        return self.scope_kind == EvaluationScopeKind.FULL_HISTORY

    @property
    def is_future_only(self) -> bool:
        return self.scope_kind == EvaluationScopeKind.FUTURE_ONLY

    def applies_to_domain(self, domain: str) -> bool:
        """True if this scope's domain filter admits ``domain``."""
        if not self.domain_scope:
            return True
        return domain.upper() in [d.upper() for d in self.domain_scope]

    def applies_to_subject(self, subject_id: str) -> bool:
        if not self.subject_scope:
            return True
        return subject_id in self.subject_scope


# ---------------------------------------------------------------------------
# RuleCondition (one structured condition)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleCondition:
    """One structured condition extracted from a natural-language rule.

    A condition tests one ``field`` against a ``threshold`` using an
    ``operator``.  ``extracted_from`` preserves the source NL phrase so
    the human reviewer can audit how the NL became structured.
    """
    field: str
    operator: str
    threshold: Any = None
    extracted_from: str = ""

    def __post_init__(self) -> None:
        validate_nonempty_str(self.field, "RuleCondition.field")
        _validate_enum(self.operator, CONDITION_OPERATORS, "RuleCondition.operator")
        object.__setattr__(self, "threshold", deep_freeze_json(self.threshold))
        # IS_MISSING / IS_PRESENT must not declare a threshold
        if self.operator in (ConditionOperator.IS_MISSING, ConditionOperator.IS_PRESENT):
            if self.threshold is not None:
                raise RuleActivationError(
                    f"operator {self.operator!r} must not declare a threshold"
                )
        # IN / NOT_IN require a list/tuple threshold
        if self.operator in (ConditionOperator.IN, ConditionOperator.NOT_IN):
            if not isinstance(self.threshold, (tuple, list)):
                raise RuleActivationError(
                    f"operator {self.operator!r} requires a list/tuple threshold"
                )

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "threshold": self.threshold,
            "extracted_from": self.extracted_from,
        }

    def evaluate(self, value: Any) -> bool:
        """Evaluate this condition against a single value.

        Missing values are handled explicitly: ``is_missing`` and
        ``is_present`` test presence; all other operators return False
        against a missing value (a rule never silently fires on absent data).
        """
        from .normalization import is_missing

        missing = is_missing(value)
        if self.operator == ConditionOperator.IS_MISSING:
            return missing
        if self.operator == ConditionOperator.IS_PRESENT:
            return not missing
        if missing:
            return False

        if self.operator == ConditionOperator.EQ:
            return value == self.threshold
        if self.operator == ConditionOperator.NE:
            return value != self.threshold
        if self.operator == ConditionOperator.CONTAINS:
            if isinstance(value, str) and isinstance(self.threshold, str):
                return self.threshold in value
            if isinstance(value, (list, tuple)):
                return self.threshold in value
            return False
        if self.operator == ConditionOperator.IN:
            return value in list(self.threshold)
        if self.operator == ConditionOperator.NOT_IN:
            return value not in list(self.threshold)
        # ordering operators -- coerce numerics
        try:
            v = float(value)
            t = float(self.threshold)
        except (TypeError, ValueError):
            return False
        if self.operator == ConditionOperator.GT:
            return v > t
        if self.operator == ConditionOperator.GE:
            return v >= t
        if self.operator == ConditionOperator.LT:
            return v < t
        if self.operator == ConditionOperator.LE:
            return v <= t
        return False


# ---------------------------------------------------------------------------
# RuleDraft (structured draft of a natural-language rule)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleDraft:
    """A structured draft of a natural-language monitoring rule.

    Design §7.4: 自然语言规则拆解、模拟、用户确认、版本化激活.  A draft
    is a *candidate* artifact: it cannot directly change existing
    conclusions.  ``natural_language`` preserves the original NL text;
    ``conditions`` hold the structured extraction; ``provenance`` binds
    the source revision the NL came from.
    """
    schema_name: str = "r3_rule_draft"
    schema_version: str = "1"
    draft_id: str = ""
    project_id: str = ""
    rule_name: str = ""
    natural_language: str = ""
    conditions: Tuple[RuleCondition, ...] = ()
    logical_combination: str = "all"  # "all" (AND) or "any" (OR)
    severity_hint: str = ""
    domain_hint: str = ""
    source_revision_id: str = ""
    status: str = RuleDraftStatus.DRAFT
    version: str = "1"
    created_at: str = ""
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.draft_id, "RuleDraft.draft_id")
        validate_nonempty_str(self.project_id, "RuleDraft.project_id")
        validate_nonempty_str(self.rule_name, "RuleDraft.rule_name")
        validate_nonempty_str(self.natural_language, "RuleDraft.natural_language")
        validate_nonempty_str(self.source_revision_id, "RuleDraft.source_revision_id")
        validate_nonempty_str(self.version, "RuleDraft.version")
        if not self.conditions:
            raise RuleActivationError("RuleDraft requires at least one condition")
        object.__setattr__(self, "conditions", tuple(self.conditions))
        if self.logical_combination not in ("all", "any"):
            raise RuleActivationError(
                f"logical_combination must be 'all' or 'any', got {self.logical_combination!r}"
            )
        _validate_enum(self.status, RULE_DRAFT_STATUSES, "RuleDraft.status")
        if self.status == RuleDraftStatus.ACTIVATED:
            raise RuleActivationError(
                "a RuleDraft cannot declare itself activated; use RuleActivation"
            )
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise RuleActivationError(
                f"RuleDraft.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "project_id": self.project_id,
            "rule_name": self.rule_name,
            "natural_language": self.natural_language,
            "conditions": [c.canonical_payload() for c in self.conditions],
            "logical_combination": self.logical_combination,
            "severity_hint": self.severity_hint,
            "domain_hint": self.domain_hint,
            "source_revision_id": self.source_revision_id,
            "version": self.version,
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Excludes draft_id (surrogate) and created_at (non-semantic)."""
        return {
            "project_id": self.project_id,
            "rule_name": self.rule_name,
            "natural_language": self.natural_language,
            "conditions": [c.canonical_payload() for c in self.conditions],
            "logical_combination": self.logical_combination,
            "severity_hint": self.severity_hint,
            "domain_hint": self.domain_hint,
            "source_revision_id": self.source_revision_id,
            "status": self.status,
            "version": self.version,
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())

    def matches_record(self, record: Mapping[str, Any]) -> bool:
        """Evaluate this draft's conditions against one record.

        ``logical_combination`` determines whether all ("all") or any
        ("any") condition must be satisfied.  Missing values never
        silently satisfy a condition.
        """
        results = []
        for cond in self.conditions:
            val = record.get(cond.field)
            results.append(cond.evaluate(val))
        if self.logical_combination == "all":
            return all(results)
        return any(results)


# ---------------------------------------------------------------------------
# Simulation types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SimulationMatch:
    """One record that matched (or explicitly did not match) during simulation."""
    record_id: str
    matched: bool
    field_values: Tuple[Tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        validate_nonempty_str(self.record_id, "SimulationMatch.record_id")
        object.__setattr__(self, "field_values", deep_freeze_json(self.field_values))


@dataclass(frozen=True)
class SimulationOutcome:
    """Aggregate outcome of simulating one rule against a set of records."""
    n_total: int = 0
    n_matched: int = 0
    n_not_matched: int = 0
    n_missing_field: int = 0
    matches: Tuple[SimulationMatch, ...] = ()

    def __post_init__(self) -> None:
        if self.n_total < 0 or self.n_matched < 0 or self.n_not_matched < 0:
            raise RuleActivationError("simulation counts must be non-negative")
        object.__setattr__(self, "matches", tuple(self.matches))
        if self.n_total != len(self.matches):
            raise RuleActivationError("simulation n_total must equal number of matches")
        if self.n_matched != sum(1 for m in self.matches if m.matched):
            raise RuleActivationError("simulation n_matched does not match records")
        if self.n_not_matched != sum(1 for m in self.matches if not m.matched):
            raise RuleActivationError("simulation n_not_matched does not match records")
        if self.n_matched + self.n_not_matched != self.n_total:
            raise RuleActivationError("simulation matched tallies must sum to n_total")
        if not (0 <= self.n_missing_field <= self.n_total):
            raise RuleActivationError("simulation n_missing_field must be within n_total")

    @property
    def match_rate(self) -> float:
        if self.n_total == 0:
            return 0.0
        return self.n_matched / self.n_total


@dataclass(frozen=True)
class RuleSimulation:
    """The result of simulating a :class:`RuleDraft` against synthetic facts.

    Design §7.4: 模拟.  A simulation exercises the draft against a set of
    records and records the outcome so activation can reference it.  The
    simulation binds to the draft content hash so it is reproducible.
    """
    schema_name: str = "r3_rule_simulation"
    schema_version: str = "1"
    simulation_id: str = ""
    project_id: str = ""
    draft_id: str = ""
    draft_content_hash: str = ""
    outcome: SimulationOutcome = None  # type: ignore[assignment]
    simulated_at: str = ""
    notes: str = ""
    content_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self,
        _verified: Any = None,
        _authority_token: Any = _LIFECYCLE_VERIFIED,
    ) -> None:
        _validate_schema(self)
        if _verified is not _authority_token:
            raise RuleActivationError(
                "RuleSimulation must be created by simulate_rule"
            )
        validate_nonempty_str(self.simulation_id, "RuleSimulation.simulation_id")
        validate_nonempty_str(self.project_id, "RuleSimulation.project_id")
        validate_nonempty_str(this := getattr(self, "draft_id", ""), "RuleSimulation.draft_id")
        validate_sha256_hex(self.draft_content_hash, "RuleSimulation.draft_content_hash")
        if self.outcome is None:
            raise RuleActivationError("RuleSimulation.outcome is required")
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise RuleActivationError(
                f"RuleSimulation.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "draft_id": self.draft_id,
            "draft_content_hash": self.draft_content_hash,
            "outcome": {
                "n_total": self.outcome.n_total,
                "n_matched": self.outcome.n_matched,
                "n_not_matched": self.outcome.n_not_matched,
                "n_missing_field": self.outcome.n_missing_field,
                "matches": [
                    {
                        "record_id": m.record_id,
                        "matched": m.matched,
                        "field_values": dict(m.field_values),
                    }
                    for m in self.outcome.matches
                ],
            },
            "simulated_at": self.simulated_at,
            "notes": self.notes,
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "draft_id": self.draft_id,
            "draft_content_hash": self.draft_content_hash,
            "outcome": self.canonical_payload()["outcome"],
            "notes": self.notes,
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())


# ---------------------------------------------------------------------------
# RuleActivation (explicit, versioned)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleActivation:
    """An explicit, versioned activation of a rule draft.

    Design §7: 激活需显式版本与 evaluation scope，不能直接改变既有结论.
    Design §5.2/§16: activated rules are versioned; their content hash
    and scope are frozen per Run so the same activation always produces
    the same effect.

    Invariants:

    * A draft must have status ``simulated`` before it can be activated
      (the simulation must be referenced).
    * ``activated_by`` records who or what activated the rule (system
      policy may activate only already-simulated drafts; a user
      activation sets ``user_confirmed=True``).
    * A machine activation (``is_machine=True``) cannot set
      ``user_confirmed``.
    * The evaluation scope is frozen at activation time; later scope
      changes require a new versioned activation.
    """
    schema_name: str = "r3_rule_activation"
    schema_version: str = "1"
    activation_id: str = ""
    project_id: str = ""
    draft_id: str = ""
    draft_content_hash: str = ""
    simulation_id: str = ""
    version: str = ""
    evaluation_scope: EvaluationScope = None  # type: ignore[assignment]
    activated_by: str = ""
    is_machine: bool = True
    user_confirmed: bool = False
    activated_at: str = ""
    supersedes: Tuple[str, ...] = ()
    content_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self,
        _verified: Any = None,
        _authority_token: Any = _LIFECYCLE_VERIFIED,
    ) -> None:
        _validate_schema(self)
        if _verified is not _authority_token:
            raise RuleActivationError(
                "RuleActivation must be created by activate_rule"
            )
        validate_nonempty_str(self.activation_id, "RuleActivation.activation_id")
        validate_nonempty_str(self.project_id, "RuleActivation.project_id")
        validate_nonempty_str(self.draft_id, "RuleActivation.draft_id")
        validate_sha256_hex(self.draft_content_hash, "RuleActivation.draft_content_hash")
        validate_nonempty_str(self.simulation_id, "RuleActivation.simulation_id")
        validate_nonempty_str(self.version, "RuleActivation.version")
        validate_nonempty_str(self.activated_by, "RuleActivation.activated_by")
        if self.evaluation_scope is None:
            raise RuleActivationError("RuleActivation.evaluation_scope is required")
        if not isinstance(self.evaluation_scope, EvaluationScope):
            raise RuleActivationError("evaluation_scope must be an EvaluationScope")
        if self.is_machine and self.user_confirmed:
            raise RuleActivationError(
                "a machine activation cannot declare user_confirmed=True"
            )
        if not self.is_machine and not self.user_confirmed:
            raise RuleActivationError(
                "a user activation must declare user_confirmed=True"
            )
        object.__setattr__(self, "supersedes", deep_freeze_json(self.supersedes))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise RuleActivationError(
                f"RuleActivation.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "activation_id": self.activation_id,
            "project_id": self.project_id,
            "draft_id": self.draft_id,
            "draft_content_hash": self.draft_content_hash,
            "simulation_id": self.simulation_id,
            "version": self.version,
            "evaluation_scope": self.evaluation_scope.canonical_payload(),
            "activated_by": self.activated_by,
            "is_machine": self.is_machine,
            "user_confirmed": self.user_confirmed,
            "activated_at": self.activated_at,
            "supersedes": list(self.supersedes),
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "draft_id": self.draft_id,
            "draft_content_hash": self.draft_content_hash,
            "simulation_id": self.simulation_id,
            "version": self.version,
            "evaluation_scope": self.evaluation_scope.canonical_payload(),
            "activated_by": self.activated_by,
            "is_machine": self.is_machine,
            "user_confirmed": self.user_confirmed,
            "supersedes": list(self.supersedes),
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())


# ---------------------------------------------------------------------------
# simulate_rule
# ---------------------------------------------------------------------------

def simulate_rule(
    draft: RuleDraft,
    records: Sequence[Mapping[str, Any]],
    *,
    simulation_id: str = "",
    notes: str = "",
    _authority_token: Any = _LIFECYCLE_VERIFIED,
) -> RuleSimulation:
    """Simulate a :class:`RuleDraft` against a sequence of records.

    Each record is evaluated against the draft's conditions.  The outcome
    records total/matched/not-matched/missing-field counts and a per-record
    match log.  ``record_id`` for each record is read from the
    ``"_record_id"`` key (or synthesized from the index).
    """
    if not isinstance(draft, RuleDraft):
        raise RuleActivationError("simulate_rule requires a RuleDraft")
    if draft.status in (
        RuleDraftStatus.REJECTED,
        RuleDraftStatus.SUPERSEDED,
        RuleDraftStatus.ACTIVATED,
    ):
        raise RuleActivationError(
            f"cannot simulate a draft with status {draft.status!r}"
        )

    matches: List[SimulationMatch] = []
    n_matched = 0
    n_not_matched = 0
    n_missing_field = 0

    from .normalization import is_missing

    seen_record_ids = set()
    for i, rec in enumerate(records):
        rid = rec.get("_record_id", f"rec-{i}") if isinstance(rec, Mapping) else f"rec-{i}"
        rid = str(rid)
        if rid in seen_record_ids:
            raise RuleActivationError(
                f"duplicate simulation record_id {rid!r}"
            )
        seen_record_ids.add(rid)
        # check if any condition field is missing in the record
        condition_fields = [c.field for c in draft.conditions]
        field_vals = tuple(
            (f, rec.get(f)) for f in condition_fields if isinstance(rec, Mapping)
        )
        any_missing = any(is_missing(rec.get(f)) for f in condition_fields) if isinstance(rec, Mapping) else True
        matched = draft.matches_record(rec) if isinstance(rec, Mapping) else False
        if matched:
            n_matched += 1
        else:
            n_not_matched += 1
        if any_missing:
            n_missing_field += 1
        matches.append(SimulationMatch(
            record_id=rid,
            matched=matched,
            field_values=field_vals,
        ))

    outcome = SimulationOutcome(
        n_total=len(records),
        n_matched=n_matched,
        n_not_matched=n_not_matched,
        n_missing_field=n_missing_field,
        matches=tuple(matches),
    )
    return RuleSimulation(
        simulation_id=simulation_id or new_id("sim-"),
        project_id=draft.project_id,
        draft_id=draft.draft_id,
        draft_content_hash=draft.content_hash,
        outcome=outcome,
        simulated_at=now_iso(),
        notes=notes,
        _verified=_authority_token,
    )


# ---------------------------------------------------------------------------
# activate_rule
# ---------------------------------------------------------------------------

def activate_rule(
    draft: RuleDraft,
    simulation: RuleSimulation,
    *,
    version: str,
    evaluation_scope: EvaluationScope,
    activated_by: str,
    is_machine: bool = True,
    user_confirmed: bool = False,
    supersedes: Sequence[str] = (),
    activation_id: str = "",
    _authority_token: Any = _LIFECYCLE_VERIFIED,
) -> RuleActivation:
    """Explicitly activate a simulated rule draft.

    Invariants enforced:

    * The draft must have been simulated (the simulation's draft_content_hash
      must match the draft's content_hash).
    * The version must be non-empty.
    * Machine activations cannot set ``user_confirmed``; user activations
      must set it.

    Design §7: a rule can never become active without explicit versioned
    activation.  This function is the *only* path to an activation.
    """
    if not isinstance(draft, RuleDraft):
        raise RuleActivationError("activate_rule requires a RuleDraft")
    if not isinstance(simulation, RuleSimulation):
        raise RuleActivationError("activate_rule requires a RuleSimulation")
    if not isinstance(evaluation_scope, EvaluationScope):
        raise RuleActivationError("activate_rule requires an EvaluationScope")
    if draft.status in (
        RuleDraftStatus.REJECTED,
        RuleDraftStatus.SUPERSEDED,
        RuleDraftStatus.ACTIVATED,
    ):
        raise RuleActivationError(
            f"cannot activate a draft with status {draft.status!r}"
        )
    if simulation.project_id != draft.project_id:
        raise RuleActivationError(
            "simulation project_id does not match the draft project_id"
        )
    if simulation.draft_id != draft.draft_id:
        raise RuleActivationError(
            "simulation draft_id does not match the draft being activated"
        )
    if simulation.draft_content_hash != draft.content_hash:
        raise RuleActivationError(
            "simulation was run against a different draft content hash; "
            "re-simulate before activating"
        )
    validate_nonempty_str(version, "activate_rule.version")
    validate_nonempty_str(activated_by, "activate_rule.activated_by")
    if is_machine and user_confirmed:
        raise RuleActivationError(
            "a machine activation cannot declare user_confirmed=True"
        )
    if not is_machine and not user_confirmed:
        raise RuleActivationError(
            "a user activation must declare user_confirmed=True"
        )

    return RuleActivation(
        activation_id=activation_id or new_id("act-"),
        project_id=draft.project_id,
        draft_id=draft.draft_id,
        draft_content_hash=draft.content_hash,
        simulation_id=simulation.simulation_id,
        version=version,
        evaluation_scope=evaluation_scope,
        activated_by=activated_by,
        is_machine=is_machine,
        user_confirmed=user_confirmed,
        activated_at=now_iso(),
        supersedes=tuple(supersedes),
        _verified=_authority_token,
    )


del _LIFECYCLE_VERIFIED
