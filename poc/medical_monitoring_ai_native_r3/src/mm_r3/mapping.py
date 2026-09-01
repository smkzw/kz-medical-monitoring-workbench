"""R3-B semantic mapping.

Maps listing field profiles to canonical target concepts (e.g. SDTM-like
target domains/variables) with:

* **explainable candidates** -- each candidate carries a score, evidence and
  a basis (name/role/value match);
* **explicit decisions** -- ``accepted`` / ``rejected`` / ``needs_confirmation``
  / ``not_evaluable``; a low-confidence candidate is *never* silently accepted
  (Design: 低置信度不被静默接受; LLM/Agent 只能提交候选 artifact);
* **field dependencies** -- a mapping may declare that it depends on another
  field's mapping (e.g. AE end date depends on AE start date);
* **user confirmation** -- high-confidence mappings may be auto-accepted only
  under an explicit approved system policy; any identity/scope/key mapping
  ambiguity surfaces as ``needs_confirmation`` and blocks baseline.

Design grounding: system design §§5,7,16 (mapping 候选/置信度/依赖/少量确认;
deterministic_service; 高置信度 mapping 可由已批准系统策略和确定性校验自动接受;
任何身份/来源范围/关键 mapping 歧义都进入 needs_user_attention); plan R3 step 5.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .listing import (
    FieldProfile,
    FieldRole,
    TableProfile,
)
from .primitives import content_hash, deep_freeze_json, new_id, validate_nonempty_str
from .schema_registry import default_registry

__all__ = [
    "MappingDecision",
    "MappingBasis",
    "MappingCandidate",
    "FieldMapping",
    "MappingResult",
    "TargetConcept",
    "SystemPolicy",
    "score_candidate",
    "map_field",
    "map_table",
    "auto_accept_under_policy",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class MappingError(Exception):
    """Semantic mapping violation."""


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MappingDecision:
    """Explicit decision on a mapping candidate.

    A candidate starts as ``needs_confirmation`` unless its score meets the
    auto-accept threshold *and* an approved system policy permits it.  A
    candidate is never silently promoted to ``accepted``.
    """
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NOT_EVALUABLE = "not_evaluable"


MAPPING_DECISIONS: Tuple[str, ...] = (
    MappingDecision.ACCEPTED,
    MappingDecision.REJECTED,
    MappingDecision.NEEDS_CONFIRMATION,
    MappingDecision.NOT_EVALUABLE,
)


class MappingBasis:
    """Why a candidate scored as it did (evidence terms)."""
    NAME_MATCH = "name_match"           # column name matched target synonym
    ROLE_MATCH = "role_match"            # inferred role matched target role
    VALUE_MATCH = "value_match"          # sample values matched expected shape
    DOMAIN_SCOPE = "domain_scope"        # target domain matched table domain hint
    POSITION_MATCH = "position_match"   # column position matched expected slot


# ---------------------------------------------------------------------------
# TargetConcept (the canonical thing a field maps *to*)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TargetConcept:
    """A canonical target concept (e.g. an SDTM-like variable).

    * ``concept_id`` -- stable id (e.g. ``"sdtm.ae.aestdtc"``);
    * ``label`` -- human label;
    * ``domain`` -- target domain (``AE``/``MH``/``CM``/``LB``/``DM``/...);
    * ``variable`` -- target variable name;
    * ``expected_roles`` -- roles that legitimately map here;
    * ``name_synonyms`` -- lowercased name synonyms used for name matching;
    * ``requires_confirmation`` -- when True, *always* needs user confirmation
      even at high score (e.g. key/identifier mappings).
    """
    concept_id: str
    label: str
    domain: str
    variable: str
    expected_roles: Tuple[str, ...] = ()
    name_synonyms: Tuple[str, ...] = ()
    expected_kind_hint: str = ""
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        validate_nonempty_str(self.concept_id, "TargetConcept.concept_id")
        validate_nonempty_str(self.label, "TargetConcept.label")
        validate_nonempty_str(self.domain, "TargetConcept.domain")
        validate_nonempty_str(self.variable, "TargetConcept.variable")
        object.__setattr__(self, "expected_roles", deep_freeze_json(self.expected_roles))
        object.__setattr__(self, "name_synonyms", deep_freeze_json(self.name_synonyms))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "label": self.label,
            "domain": self.domain,
            "variable": self.variable,
            "expected_roles": list(self.expected_roles),
            "name_synonyms": list(self.name_synonyms),
            "expected_kind_hint": self.expected_kind_hint,
            "requires_confirmation": self.requires_confirmation,
        }


# ---------------------------------------------------------------------------
# MappingCandidate (one (field, target) hypothesis with score + evidence)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MappingCandidate:
    """One hypothesis: field *f* maps to target *t* with score *s*.

    ``score`` is in ``[0.0, 1.0]``.  ``evidence`` is a tuple of
    :class:`MappingBasis` constants recording which matching rules fired.
    ``decision`` is the current explicit decision (never auto-promoted above
    ``accepted`` without a policy).
    """
    schema_name: str = "r3_mapping_candidate"
    schema_version: str = "1"
    candidate_id: str = ""
    field_name: str = ""
    target_concept_id: str = ""
    target_domain: str = ""
    target_variable: str = ""
    field_role: str = ""
    target_requires_confirmation: bool = False
    score: float = 0.0
    evidence: Tuple[str, ...] = ()
    decision: str = MappingDecision.NEEDS_CONFIRMATION
    notes: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.field_name, "MappingCandidate.field_name")
        validate_nonempty_str(self.target_concept_id, "MappingCandidate.target_concept_id")
        validate_nonempty_str(self.target_domain, "MappingCandidate.target_domain")
        validate_nonempty_str(self.target_variable, "MappingCandidate.target_variable")
        if not (0.0 <= self.score <= 1.0):
            raise MappingError(
                f"MappingCandidate.score must be in [0,1], got {self.score}"
            )
        if self.decision not in MAPPING_DECISIONS:
            raise MappingError(
                f"MappingCandidate.decision={self.decision!r} not in {MAPPING_DECISIONS}"
            )
        object.__setattr__(self, "evidence", deep_freeze_json(self.evidence))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "field_name": self.field_name,
            "target_concept_id": self.target_concept_id,
            "target_domain": self.target_domain,
            "target_variable": self.target_variable,
            "field_role": self.field_role,
            "target_requires_confirmation": self.target_requires_confirmation,
            "score": self.score,
            "evidence": list(self.evidence),
            "decision": self.decision,
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Content-only (excludes the random candidate_id)."""
        return {
            "field_name": self.field_name,
            "target_concept_id": self.target_concept_id,
            "target_domain": self.target_domain,
            "target_variable": self.target_variable,
            "field_role": self.field_role,
            "target_requires_confirmation": self.target_requires_confirmation,
            "score": self.score,
            "evidence": list(self.evidence),
            "decision": self.decision,
        }

    def content_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# FieldMapping (the resolved mapping for one field, with deps + decision)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldMapping:
    """The resolved mapping outcome for one field.

    Carries all candidates, the chosen candidate (if any), an explicit
    decision and optional dependencies on other field mappings.  When no
    candidate is strong enough, ``decision`` is ``needs_confirmation`` or
    ``not_evaluable`` and ``chosen_candidate_id`` is empty -- a field is
    never silently mapped.
    """
    schema_name: str = "r3_field_mapping"
    schema_version: str = "1"
    field_name: str = ""
    candidates: Tuple[MappingCandidate, ...] = ()
    chosen_candidate_id: str = ""
    decision: str = MappingDecision.NEEDS_CONFIRMATION
    depends_on: Tuple[str, ...] = ()
    resolved_by: str = ""
    uncertainty: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.field_name, "FieldMapping.field_name")
        if self.decision not in MAPPING_DECISIONS:
            raise MappingError(
                f"FieldMapping.decision={self.decision!r} not in {MAPPING_DECISIONS}"
            )
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "depends_on", deep_freeze_json(self.depends_on))
        if self.decision == MappingDecision.ACCEPTED and not self.chosen_candidate_id:
            raise MappingError(
                "an accepted FieldMapping must name a chosen_candidate_id"
            )
        if self.chosen_candidate_id:
            ids = {c.candidate_id for c in self.candidates}
            if self.chosen_candidate_id not in ids:
                raise MappingError(
                    "chosen_candidate_id is not among the field's candidates"
                )
        if self.decision == MappingDecision.ACCEPTED:
            chosen = self.chosen
            if chosen is None or chosen.decision != MappingDecision.ACCEPTED:
                raise MappingError(
                    "an accepted FieldMapping must have an accepted chosen candidate"
                )
            if not self.resolved_by:
                raise MappingError(
                    "an accepted FieldMapping must record who or what accepted it"
                )

    @property
    def chosen(self) -> Optional[MappingCandidate]:
        if not self.chosen_candidate_id:
            return None
        for c in self.candidates:
            if c.candidate_id == self.chosen_candidate_id:
                return c
        return None

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "candidates": [c.canonical_payload() for c in self.candidates],
            "chosen_candidate_id": self.chosen_candidate_id,
            "decision": self.decision,
            "depends_on": list(self.depends_on),
            "resolved_by": self.resolved_by,
            "uncertainty": self.uncertainty,
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Content-only: replaces candidate ids with their index + target, and
        records whether the i-th candidate is chosen, so the fingerprint is
        independent of random surrogate ids."""
        return {
            "field_name": self.field_name,
            "candidates": [c.content_fingerprint() for c in self.candidates],
            "chosen_index": next(
                (i for i, c in enumerate(self.candidates)
                 if c.candidate_id == self.chosen_candidate_id),
                -1,
            ),
            "decision": self.decision,
            "depends_on": list(self.depends_on),
            "resolved_by": self.resolved_by,
            "uncertainty": self.uncertainty,
        }

    def content_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# MappingResult (all field mappings for one table)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MappingResult:
    """The resolved mapping for one table/workbook.

    Content-addressed; binds to the source revision + table profile hash.
    """
    schema_name: str = "r3_mapping_result"
    schema_version: str = "1"
    result_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    table_name: str = ""
    table_profile_hash: str = ""
    field_mappings: Tuple[FieldMapping, ...] = ()
    n_accepted: int = 0
    n_rejected: int = 0
    n_needs_confirmation: int = 0
    n_not_evaluable: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.result_id, "MappingResult.result_id")
        validate_nonempty_str(self.project_id, "MappingResult.project_id")
        validate_nonempty_str(self.source_revision_id, "MappingResult.source_revision_id")
        validate_nonempty_str(self.table_name, "MappingResult.table_name")
        object.__setattr__(self, "field_mappings", tuple(self.field_mappings))
        # recompute decision tallies from the mappings (derived, never declared)
        accepted = sum(1 for m in self.field_mappings if m.decision == MappingDecision.ACCEPTED)
        rejected = sum(1 for m in self.field_mappings if m.decision == MappingDecision.REJECTED)
        needs = sum(1 for m in self.field_mappings if m.decision == MappingDecision.NEEDS_CONFIRMATION)
        ne = sum(1 for m in self.field_mappings if m.decision == MappingDecision.NOT_EVALUABLE)
        object.__setattr__(self, "n_accepted", accepted)
        object.__setattr__(self, "n_rejected", rejected)
        object.__setattr__(self, "n_needs_confirmation", needs)
        object.__setattr__(self, "n_not_evaluable", ne)
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise MappingError(
                f"MappingResult.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    @property
    def is_fully_accepted(self) -> bool:
        """True iff every field mapping is accepted (baseline-ready)."""
        return bool(self.field_mappings) and self.n_accepted == len(self.field_mappings)

    @property
    def blocks_baseline(self) -> bool:
        """True iff any mapping is not accepted (baseline-blocking)."""
        return not self.is_fully_accepted

    def field_mapping(self, name: str) -> Optional[FieldMapping]:
        for m in self.field_mappings:
            if m.field_name == name:
                return m
        return None

    def canonical_payload(self) -> Dict[str, Any]:
        """Full payload including the surrogate result_id (for audit)."""
        return {
            "result_id": self.result_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "table_name": self.table_name,
            "table_profile_hash": self.table_profile_hash,
            "field_mappings": [m.canonical_payload() for m in self.field_mappings],
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Content-only payload (excludes surrogate ids) so two mappings of
        the same fields/targets/decisions hash identically."""
        return {
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "table_name": self.table_name,
            "table_profile_hash": self.table_profile_hash,
            "field_mappings": [m.content_fingerprint() for m in self.field_mappings],
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())


# ---------------------------------------------------------------------------
# SystemPolicy (approved auto-accept policy)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SystemPolicy:
    """An approved system policy that may auto-accept high-confidence mappings.

    * ``auto_accept_threshold`` -- minimum score to auto-accept (default 0.85);
    * ``require_confirmation_for_roles`` -- roles that always need user
      confirmation regardless of score (default: identifiers);
    * ``policy_id`` / ``policy_version`` -- for auditability.

    A policy *cannot* lower the confirmation bar for roles that require it,
    and *cannot* accept a mapping whose target concept is marked
    ``requires_confirmation``.
    """
    policy_id: str = "default-mapping-policy"
    policy_version: str = "1"
    auto_accept_threshold: float = 0.85
    require_confirmation_for_roles: Tuple[str, ...] = (FieldRole.IDENTIFIER,)
    allow_auto_accept: bool = True

    def __post_init__(self) -> None:
        validate_nonempty_str(self.policy_id, "SystemPolicy.policy_id")
        validate_nonempty_str(self.policy_version, "SystemPolicy.policy_version")
        if not (0.0 <= self.auto_accept_threshold <= 1.0):
            raise MappingError(
                "auto_accept_threshold must be in [0,1]"
            )
        object.__setattr__(
            self,
            "require_confirmation_for_roles",
            deep_freeze_json(self.require_confirmation_for_roles),
        )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

#: weights for each evidence term
_WEIGHTS: Dict[str, float] = {
    MappingBasis.NAME_MATCH: 0.45,
    MappingBasis.ROLE_MATCH: 0.30,
    MappingBasis.VALUE_MATCH: 0.15,
    MappingBasis.DOMAIN_SCOPE: 0.10,
    MappingBasis.POSITION_MATCH: 0.05,
}


def _name_match_score(field_name: str, target: TargetConcept) -> float:
    """Name-match subscore in [0,1].

    Exact variable match -> 1.0; synonym containment -> 0.8; stem overlap ->
    0.4; else 0.0.  Case-insensitive.
    """
    fname = (field_name or "").strip().lower()
    var = (target.variable or "").strip().lower()
    if not fname or not var:
        return 0.0
    if fname == var:
        return 1.0
    # synonym containment (field contains a synonym or vice versa)
    for syn in target.name_synonyms:
        s = syn.lower()
        if not s:
            continue
        if s in fname or fname in s:
            return 0.8
    # stem overlap: shared token of length >= 3
    fname_tokens = {t for t in _re_tokens(fname) if len(t) >= 3}
    var_tokens = {t for t in _re_tokens(var) if len(t) >= 3}
    if fname_tokens & var_tokens:
        return 0.4
    return 0.0


def _role_match_score(field_role: str, target: TargetConcept) -> float:
    if not target.expected_roles:
        return 0.0
    if field_role in target.expected_roles:
        return 1.0
    return 0.0


def _value_match_score(field: FieldProfile, target: TargetConcept) -> float:
    """Value-shape subscore: does the field's kind hint match the target's?"""
    if not target.expected_kind_hint:
        return 0.0
    if field.normalization_kind_hint == target.expected_kind_hint:
        return 1.0
    return 0.0


def _domain_scope_score(table_domain_hint: str, target: TargetConcept) -> float:
    if not table_domain_hint:
        return 0.0
    if table_domain_hint.upper() == target.domain.upper():
        return 1.0
    return 0.0


def _position_match_score(field_index: int, n_fields: int, target: TargetConcept) -> float:
    """A mild positional prior; rarely decisive, never > 0.2."""
    # identifiers often first; measures often last. We keep this weak.
    return 0.0


import re as _re_module

_TOKEN_RE = _re_module.compile(r"[a-z0-9]+")


def _re_tokens(s: str) -> List[str]:
    return _TOKEN_RE.findall(s.lower())


def score_candidate(
    field: FieldProfile,
    target: TargetConcept,
    *,
    table_domain_hint: str = "",
    field_index: int = 0,
    n_fields: int = 0,
) -> Tuple[float, Tuple[str, ...]]:
    """Score one (field, target) hypothesis.

    Returns ``(score, evidence)``.  Score is the weighted sum of evidence
    terms, clamped to ``[0, 1]``.  Evidence is the tuple of basis constants
    that fired (score > 0 for that term).
    """
    evidence: List[str] = []
    total = 0.0
    nm = _name_match_score(field.name, target)
    if nm > 0:
        total += _WEIGHTS[MappingBasis.NAME_MATCH] * nm
        evidence.append(MappingBasis.NAME_MATCH)
    rm = _role_match_score(field.role, target)
    if rm > 0:
        total += _WEIGHTS[MappingBasis.ROLE_MATCH] * rm
        evidence.append(MappingBasis.ROLE_MATCH)
    vm = _value_match_score(field, target)
    if vm > 0:
        total += _WEIGHTS[MappingBasis.VALUE_MATCH] * vm
        evidence.append(MappingBasis.VALUE_MATCH)
    ds = _domain_scope_score(table_domain_hint, target)
    if ds > 0:
        total += _WEIGHTS[MappingBasis.DOMAIN_SCOPE] * ds
        evidence.append(MappingBasis.DOMAIN_SCOPE)
    pm = _position_match_score(field_index, n_fields, target)
    if pm > 0:
        total += _WEIGHTS[MappingBasis.POSITION_MATCH] * pm
        evidence.append(MappingBasis.POSITION_MATCH)
    return (max(0.0, min(1.0, total))), tuple(evidence)


# ---------------------------------------------------------------------------
# Mapping entry points
# ---------------------------------------------------------------------------

def map_field(
    field: FieldProfile,
    targets: Sequence[TargetConcept],
    *,
    table_domain_hint: str = "",
    field_index: int = 0,
    n_fields: int = 0,
    policy: Optional[SystemPolicy] = None,
    depends_on: Sequence[str] = (),
) -> FieldMapping:
    """Map one field against candidate targets.

    Generates one :class:`MappingCandidate` per target (score > 0 only), then
    picks the highest-scoring candidate.  The decision is:

    * ``accepted`` -- only when a policy permits auto-accept *and* the top
      candidate's score >= threshold *and* neither the field role nor the
      target requires confirmation;
    * ``needs_confirmation`` -- a strong candidate exists but it does not meet
      the auto-accept bar (or requires confirmation);
    * ``not_evaluable`` -- no candidate scored above 0.
    """
    candidates: List[MappingCandidate] = []
    for tgt in targets:
        score, evidence = score_candidate(
            field, tgt,
            table_domain_hint=table_domain_hint,
            field_index=field_index,
            n_fields=n_fields,
        )
        if score <= 0.0:
            continue
        candidates.append(MappingCandidate(
            candidate_id=new_id("cand-"),
            field_name=field.name,
            target_concept_id=tgt.concept_id,
            target_domain=tgt.domain,
            target_variable=tgt.variable,
            field_role=field.role,
            target_requires_confirmation=tgt.requires_confirmation,
            score=score,
            evidence=evidence,
            decision=MappingDecision.NEEDS_CONFIRMATION,
            notes="",
        ))
    candidates.sort(key=lambda c: c.score, reverse=True)

    if not candidates:
        return FieldMapping(
            field_name=field.name,
            candidates=(),
            decision=MappingDecision.NOT_EVALUABLE,
            depends_on=tuple(depends_on),
            uncertainty="no target concept matched this field",
        )

    top = candidates[0]
    chosen_id = ""
    decision = MappingDecision.NEEDS_CONFIRMATION
    uncertainty = ""

    requires_confirm = (
        field.role in (policy.require_confirmation_for_roles if policy else (FieldRole.IDENTIFIER,))
        or _target_requires_confirmation(top)
    )
    threshold = policy.auto_accept_threshold if policy and policy.allow_auto_accept else 2.0  # impossible
    can_auto = (
        policy is not None
        and policy.allow_auto_accept
        and top.score >= threshold
        and not requires_confirm
    )
    if can_auto:
        chosen_id = top.candidate_id
        decision = MappingDecision.ACCEPTED
        uncertainty = ""
        candidates[0] = replace(top, decision=MappingDecision.ACCEPTED)
    else:
        if requires_confirm:
            uncertainty = (
                f"top candidate score {top.score:.2f} but field role "
                f"{field.role!r} requires user confirmation"
            )
        elif policy is None or not policy.allow_auto_accept:
            uncertainty = (
                f"top candidate score {top.score:.2f} but no auto-accept policy "
                f"is active"
            )
        else:
            uncertainty = (
                f"top candidate score {top.score:.2f} below auto-accept "
                f"threshold {threshold:.2f}"
            )

    return FieldMapping(
        field_name=field.name,
        candidates=tuple(candidates),
        chosen_candidate_id=chosen_id,
        decision=decision,
        depends_on=tuple(depends_on),
        resolved_by=(
            f"system_policy:{policy.policy_id}@{policy.policy_version}"
            if decision == MappingDecision.ACCEPTED and policy is not None
            else ""
        ),
        uncertainty=uncertainty,
    )


def _target_requires_confirmation(cand: MappingCandidate) -> bool:
    """A candidate whose *target concept* is marked requires_confirmation.

    The target's declared contract is copied into the candidate when it is
    created; identifier-like naming conventions are not used as a substitute
    for that explicit declaration.
    """
    return cand.target_requires_confirmation


def map_table(
    table: TableProfile,
    targets: Sequence[TargetConcept],
    *,
    project_id: str,
    source_revision_id: str,
    policy: Optional[SystemPolicy] = None,
    dependencies: Optional[Mapping[str, Sequence[str]]] = None,
) -> MappingResult:
    """Map every field in a table to canonical target concepts.

    ``dependencies`` maps field-name -> list of field-names it depends on.
    """
    validate_nonempty_str(project_id, "map_table.project_id")
    validate_nonempty_str(source_revision_id, "map_table.source_revision_id")
    deps = dependencies or {}
    n_fields = len(table.fields)
    field_mappings: List[FieldMapping] = []
    for i, f in enumerate(table.fields):
        fm = map_field(
            f, targets,
            table_domain_hint=table.domain_hint,
            field_index=i,
            n_fields=n_fields,
            policy=policy,
            depends_on=deps.get(f.name, ()),
        )
        field_mappings.append(fm)
    return MappingResult(
        result_id=new_id("map-"),
        project_id=project_id,
        source_revision_id=source_revision_id,
        table_name=table.name,
        table_profile_hash=table.content_hash,
        field_mappings=tuple(field_mappings),
    )


# ---------------------------------------------------------------------------
# Auto-accept helper (explicit policy application)
# ---------------------------------------------------------------------------

def auto_accept_under_policy(
    mapping: FieldMapping,
    policy: SystemPolicy,
) -> FieldMapping:
    """Return a new :class:`FieldMapping` with the policy applied.

    This is an explicit, auditable operation: it re-evaluates the top
    candidate under ``policy`` and may flip ``needs_confirmation`` ->
    ``accepted``.  It *never* overrides a field whose role requires
    confirmation, and *never* accepts a target that requires confirmation.
    """
    if mapping.decision == MappingDecision.ACCEPTED:
        return mapping
    if not mapping.candidates:
        return mapping
    top = max(mapping.candidates, key=lambda c: c.score)
    if top.score < policy.auto_accept_threshold:
        return mapping
    if not policy.allow_auto_accept:
        return mapping
    if top.field_role in policy.require_confirmation_for_roles:
        return mapping
    if _target_requires_confirmation(top):
        return mapping
    accepted_top = replace(top, decision=MappingDecision.ACCEPTED)
    accepted_candidates = tuple(
        accepted_top if c.candidate_id == top.candidate_id else c
        for c in mapping.candidates
    )
    return FieldMapping(
        field_name=mapping.field_name,
        candidates=accepted_candidates,
        chosen_candidate_id=top.candidate_id,
        decision=MappingDecision.ACCEPTED,
        depends_on=mapping.depends_on,
        resolved_by=f"system_policy:{policy.policy_id}@{policy.policy_version}",
        uncertainty="",
    )
