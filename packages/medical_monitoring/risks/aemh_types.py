"""Core semantic and medical types for the AE/MH risk domain."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..intelligence.normalization import NormalizedValue, normalize_partial_date
from .contracts import (
    CrossDomainEvidenceRef, CoverageValidationError,
    MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM, MONITORING_PRIORITY_UNKNOWN,
    SourceLocator, VALID_MONITORING_PRIORITIES,
)

# ---------------------------------------------------------------------------
# Semantic role constants (matrix §4 D01, frozen contract §7)
# ---------------------------------------------------------------------------

#: Minimum required semantic roles for D01 AE/MH evaluation.
REQUIRED_AEMH_ROLES: Tuple[str, ...] = (
    "reported_ae",
    "reported_mh",
    "subject_identity",
    "site_identity",
    "temporal_anchor",
)

#: Optional evidence-bearing roles that may surface under-reporting clues
#: or counterevidence (matrix §4 D01 "必需输入").
OPTIONAL_EVIDENCE_ROLES: Tuple[str, ...] = (
    "symptom_event",
    "cm_indication",
    "lab_finding",
    "exam_finding",
    "healthcare_encounter",
    "procedure",
    "ip_action",
    "seriousness_clue",
    "death_event",
    "visit",
)

#: All recognized D01 semantic roles.
AEMH_ROLES: Tuple[str, ...] = REQUIRED_AEMH_ROLES + OPTIONAL_EVIDENCE_ROLES


# ---------------------------------------------------------------------------
# Monitoring-priority constants (matrix §3.5) -- re-exported from contracts
# ---------------------------------------------------------------------------
#
# The ``MONITORING_PRIORITY_*`` constants and ``VALID_MONITORING_PRIORITIES``
# now live on the neutral common surface ``mm_r4.contracts`` (frozen D02
# contract §2) so the lifecycle adapter and every concrete domain result
# share one set of tokens.  This module re-exports them for backward
# compatibility with existing public imports (``from mm_r4.aemh import
# MONITORING_PRIORITY_HIGH``).

#: Private alias retained for the in-package ``MedicalGrading`` validation;
#: identical to the neutral ``VALID_MONITORING_PRIORITIES``.
_VALID_MONITORING_PRIORITIES: Tuple[str, ...] = VALID_MONITORING_PRIORITIES

#: Clinical-flag tokens that map to SAE/AESI seriousness criteria, NOT to
#: event intensity or monitoring priority (matrix §3.5).  These are kept in
#: candidate detail / projection, separate from severity_hint.
CLINICAL_FLAG_TOKENS: Tuple[str, ...] = (
    "sae",
    "aesi",
    "death",
    "life_threatening",
    "hospitalization",
    "disability",
    "congenital_anomaly",
    "other_important_medical_event",
)
# Backward-compatible private alias for in-package call sites.
_CLINICAL_FLAG_TOKENS = CLINICAL_FLAG_TOKENS

# Seriousness criteria that make an event SAE-like for R2's independent
# ``clinical_risk_flags`` projection.  AESI remains a separate flag and may
# coexist with SAE.
_SAE_CRITERIA_TOKENS: Tuple[str, ...] = tuple(
    token for token in CLINICAL_FLAG_TOKENS if token != "aesi"
)


#: NCS (not clinically significant) signal tokens -- recognized in record
#: ``clinical_significance`` or note text.  NCS is *combination* counter-
#: evidence only: it never absolutely excludes a clue by itself.
_NCS_TOKENS: Tuple[str, ...] = (
    "ncs",
    "not_clinically_significant",
    "not clinically significant",
)

#: Alternative-diagnosis signal tokens.  A confirmed alternative diagnosis
#: may act as source-linked counterevidence but never absolutely excludes.
_ALT_DIAG_TOKENS: Tuple[str, ...] = (
    "alternative_diagnosis",
    "alternative diagnosis",
    "alt_diagnosis",
    "confirmed_alternative_diagnosis",
)


def _has_token(text: str, tokens: Sequence[str]) -> bool:
    """Case-insensitive substring check for any token in text."""
    lower = text.strip().lower()
    if not lower:
        return False
    for token in tokens:
        if token.lower() in lower:
            return True
    return False

# ---------------------------------------------------------------------------
# Versioned protocol boundary and event-match strategy (matrix §4 D01)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConceptEquivalence:
    """Caller-supplied concept equivalence groups.

    Each group is a frozenset of concept strings treated as equivalent for
    matching purposes.  Common code provides NO project concept aliases
    (matrix §4 D01 "误报控制").

    Two concepts match when they are string-identical OR belong to the same
    caller-supplied equivalence group.
    """
    groups: Tuple[frozenset, ...] = ()
    version: str = ""

    def __post_init__(self) -> None:
        validated: List[frozenset] = []
        for grp in self.groups:
            if not isinstance(grp, (frozenset, set, tuple, list)):
                raise CoverageValidationError(
                    "ConceptEquivalence.groups entries must be iterables of "
                    "strings")
            frozen = frozenset(grp)
            if not frozen:
                continue
            for item in frozen:
                if not isinstance(item, str) or not item.strip():
                    raise CoverageValidationError(
                        "ConceptEquivalence group members must be non-empty "
                        "strings")
            validated.append(frozen)
        object.__setattr__(self, "groups", tuple(validated))
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "ConceptEquivalence.version is required and must be a "
                "non-empty string")

    def are_equivalent(self, concept_a: str, concept_b: str) -> bool:
        """True when both concepts are identical or in the same group."""
        if concept_a == concept_b:
            return True
        for grp in self.groups:
            if concept_a in grp and concept_b in grp:
                return True
        return False

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "groups": [sorted(g) for g in self.groups],
            "version": self.version,
        }


@dataclass(frozen=True)
class TemporalTolerance:
    """Caller-supplied temporal tolerance for event matching.

    ``same_day`` means two events on the same calendar day match temporally.
    ``tolerance_days`` defines a symmetric window; ``None`` means no
    day-based tolerance is applied -- the caller must rely on shared-date
    precision only.  Common code provides NO default day-gap window
    (matrix §4 D01 "误报控制").

    If ``tolerance_days`` is ``None``, two dates with no shared precision
    (e.g., one year-only, one full date from a different year) will fail
    closed into ``boundary`` or ``not_evaluable``.
    """

    tolerance_days: Optional[int] = None
    same_day: bool = True
    version: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.same_day, bool):
            raise CoverageValidationError(
                "TemporalTolerance.same_day must be a bool")
        if self.tolerance_days is not None:
            if not isinstance(self.tolerance_days, int) or isinstance(
                    self.tolerance_days, bool):
                raise CoverageValidationError(
                    "TemporalTolerance.tolerance_days must be a non-negative "
                    "int or None")
            if self.tolerance_days < 0:
                raise CoverageValidationError(
                    "TemporalTolerance.tolerance_days must be a non-negative "
                    "int or None")
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "TemporalTolerance.version is required and must be a "
                "non-empty string")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "tolerance_days": self.tolerance_days,
            "same_day": self.same_day,
            "version": self.version,
        }


@dataclass(frozen=True)
class EventMatchStrategy:
    """Versioned strategy for matching cross-source medical events to
    reported AE/MH records.

    Combines caller-supplied :class:`ConceptEquivalence` and
    :class:`TemporalTolerance`.  No project-specific thresholds, no default
    30-day rule, no hardcoded concept aliases (matrix §4 D01).
    """

    strategy_id: str
    version: str
    # Required and versioned: no silent empty ConceptEquivalence /
    # TemporalTolerance defaults (those raise without a version anyway).
    concept_equivalence: ConceptEquivalence
    temporal_tolerance: TemporalTolerance
    description: str = ""

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.strategy_id is required")
        if not self.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.version is required")
        if not isinstance(self.concept_equivalence, ConceptEquivalence):
            raise CoverageValidationError(
                "EventMatchStrategy.concept_equivalence must be a "
                "ConceptEquivalence")
        if not isinstance(self.temporal_tolerance, TemporalTolerance):
            raise CoverageValidationError(
                "EventMatchStrategy.temporal_tolerance must be a "
                "TemporalTolerance")
        if not self.concept_equivalence.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.concept_equivalence.version is required "
                "and must be non-empty")
        if not self.temporal_tolerance.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.temporal_tolerance.version is required "
                "and must be non-empty")

    def concepts_match(self, concept_a: str, concept_b: str) -> bool:
        return self.concept_equivalence.are_equivalent(concept_a, concept_b)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "concept_equivalence": self.concept_equivalence.canonical_payload(),
            "temporal_tolerance": self.temporal_tolerance.canonical_payload(),
            "description": self.description,
        }


@dataclass(frozen=True)
class ProtocolAEMHBoundary:
    """Versioned protocol reporting boundary for AE/MH (matrix §4 D01).

    Defines the study reference period (informed consent, first dose /
    randomization, treatment phase, reporting cutoff) and any protocol-
    specified exclusions.  The boundary is determined by the *protocol*,
    not globally hardcoded to the first dose date.

    ``reporting_start_anchor`` and ``reporting_end_anchor`` are versioned
    anchor descriptors (e.g., "icf_date", "first_dose_date", "cutoff_date",
    "end_of_treatment_plus_30d").  They are *descriptors*, not dates; the
    actual anchor dates are resolved from the subject's temporal anchor
    records via :class:`ProtocolAnchorDates` during evaluation.

    ``applicable`` (default ``True``) plus ``non_applicable_reason`` allows
    a versioned protocol to mark a unit as genuinely out of scope, yielding
    L1 ``not_applicable`` (finding 3).
    """

    boundary_id: str
    version: str
    reporting_start_anchor: str
    reporting_end_anchor: str
    protocol_exclusions: Tuple[str, ...] = ()
    description: str = ""
    applicable: bool = True
    non_applicable_reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.boundary_id, str) or not self.boundary_id.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.boundary_id is required")
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.version is required")
        if not isinstance(self.reporting_start_anchor, str) or not \
                self.reporting_start_anchor.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.reporting_start_anchor is required")
        if not isinstance(self.reporting_end_anchor, str) or not \
                self.reporting_end_anchor.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.reporting_end_anchor is required")
        if not isinstance(self.applicable, bool):
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.applicable must be a bool")
        frozen_excl = tuple(self.protocol_exclusions)
        for item in frozen_excl:
            if not isinstance(item, str) or not item.strip():
                raise CoverageValidationError(
                    "ProtocolAEMHBoundary.protocol_exclusions members must be "
                    "non-empty strings")
        object.__setattr__(self, "protocol_exclusions", frozen_excl)
        if not self.applicable:
            if not isinstance(self.non_applicable_reason, str) or not \
                    self.non_applicable_reason.strip():
                raise CoverageValidationError(
                    "ProtocolAEMHBoundary.non_applicable_reason is required "
                    "when applicable=False")

    def is_excluded_concept(self, concept: str) -> bool:
        """True when the protocol explicitly excludes this concept from
        AE collection."""
        return concept in self.protocol_exclusions

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "version": self.version,
            "reporting_start_anchor": self.reporting_start_anchor,
            "reporting_end_anchor": self.reporting_end_anchor,
            "protocol_exclusions": list(self.protocol_exclusions),
            "description": self.description,
            "applicable": self.applicable,
            "non_applicable_reason": self.non_applicable_reason,
        }

@dataclass(frozen=True)
class SemanticRecord:
    """One semantic-role record carrying row-level content and a source
    locator.

    ``role`` is a semantic role from the active mapping (e.g.
    ``reported_ae``, ``symptom_event``, ``lab_finding``), never a fixed
    SDTM table name.  ``concept`` is the normalized medical concept
    (e.g., a MedDRA PT code).  ``event_date_raw`` is the raw date string
    that will be normalized via frozen R3 ``normalize_partial_date``.

    ``intensity`` carries event severity/grade (mild/moderate/severe, or
    a CTCAE grade) -- it is NEVER confused with seriousness or monitoring
    priority (matrix §3.5).

    ``seriousness_criteria`` is a tuple of seriousness-criterion tokens
    (e.g., ``("sae", "hospitalization")``).  These are clinical flags,
    kept separate from ``intensity`` and from monitoring priority.

    ``ai_assertion`` marks whether this record originated from a model/AI
    source.  When ``True``, the record can only become evidence or a
    candidate -- never a reported source fact (matrix §3.6, contract §9).
    """

    role: str
    concept: str
    locator: SourceLocator
    event_date_raw: str = ""
    subject_ref: str = ""
    site_ref: str = ""
    intensity: str = ""
    seriousness_criteria: Tuple[str, ...] = ()
    intensity_scale: str = ""  # e.g., "ctcae_v5", "protocol_scale_v1"
    outcome: str = ""
    action_taken: str = ""
    visit_label: str = ""
    phase: str = ""
    ai_assertion: bool = False
    note: str = ""
    clinical_significance: str = ""
    alternative_diagnosis: str = ""
    alternative_diagnosis_confirmed: bool = False
    anchor_descriptor: str = ""
    cross_domain_content_hash: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.role, str) or not self.role.strip():
            raise CoverageValidationError("SemanticRecord.role is required")
        if not isinstance(self.concept, str) or not self.concept.strip():
            raise CoverageValidationError(
                "SemanticRecord.concept is required")
        if not isinstance(self.locator, SourceLocator):
            raise CoverageValidationError(
                "SemanticRecord.locator must be a SourceLocator")
        if self.role not in AEMH_ROLES:
            raise CoverageValidationError(
                f"SemanticRecord.role={self.role!r} is not a recognized D01 "
                f"semantic role; recognized={AEMH_ROLES}")
        object.__setattr__(
            self, "seriousness_criteria", tuple(self.seriousness_criteria))
        if not isinstance(self.ai_assertion, bool):
            raise CoverageValidationError(
                "SemanticRecord.ai_assertion must be an actual bool, "
                "not a string or other type (finding 3)")
        if not isinstance(self.alternative_diagnosis_confirmed, bool):
            raise CoverageValidationError(
                "SemanticRecord.alternative_diagnosis_confirmed must be "
                "an actual bool (finding 2)")
        if self.cross_domain_content_hash:
            try:
                valid_hash = (
                    len(self.cross_domain_content_hash) == 64
                    and int(self.cross_domain_content_hash, 16) >= 0
                )
            except ValueError:
                valid_hash = False
            if not valid_hash:
                raise CoverageValidationError(
                    "SemanticRecord.cross_domain_content_hash must be SHA-256")

    @property
    def is_reported_ae(self) -> bool:
        return self.role == "reported_ae"

    @property
    def is_reported_mh(self) -> bool:
        return self.role == "reported_mh"

    @property
    def is_reported_source(self) -> bool:
        """True when this record is an accepted reported AE/MH source.

        An AI assertion is NEVER a reported source fact, even if its role
        is ``reported_ae`` / ``reported_mh`` (finding 7)."""
        if self.ai_assertion:
            return False
        return self.role in ("reported_ae", "reported_mh")

    @property
    def is_evidence_role(self) -> bool:
        """True when this record is an optional evidence-bearing role."""
        return self.role in OPTIONAL_EVIDENCE_ROLES

    @property
    def has_seriousness_clue(self) -> bool:
        return bool(self.seriousness_criteria)

    @property
    def is_ncs(self) -> bool:
        """True when this record carries an explicit NCS determination
        (finding 6)."""
        return (
            bool(self.clinical_significance.strip())
            and _has_token(self.clinical_significance, _NCS_TOKENS)
        ) or _has_token(self.note, _NCS_TOKENS)

    @property
    def has_alternative_diagnosis(self) -> bool:
        """True when this record carries a *confirmed* alternative
        diagnosis (finding 2/6).  A non-empty tentative diagnosis alone
        must NOT suppress a clue."""
        return (
            bool(self.alternative_diagnosis.strip())
            and self.alternative_diagnosis_confirmed
        )

    @property
    def has_medical_action(self) -> bool:
        """True when this record indicates a medical action or treatment
        (finding 6: NCS alone is not exclusion if there is a symptom,
        action, seriousness clue, or repeat worsening)."""
        return bool(self.action_taken.strip())

    def normalized_date(self) -> Optional[NormalizedValue]:
        """R3 partial-date normalization of ``event_date_raw``."""
        if not self.event_date_raw:
            return None
        return normalize_partial_date(self.event_date_raw)


def _cross_domain_dedup_key(
    *, locator: SourceLocator, evidence_role: str, content_hash_value: str,
) -> Tuple[str, str, str, str]:
    return (
        locator.table_semantic,
        locator.record_id,
        evidence_role,
        content_hash_value,
    )


def consume_cross_domain_evidence_refs(
    active_mapping_records: Sequence[SemanticRecord],
    refs: Sequence[CrossDomainEvidenceRef],
) -> Tuple[SemanticRecord, ...]:
    """Consume D02 ``cm_indication`` refs with frozen dual-path dedup.

    The only dedup key is ``(table_semantic, record_id, evidence_role,
    content_hash)``.  Active ``cm_indication`` records without a canonical
    hash fail closed; changed clinical claims remain distinct.  This adapter
    carries source evidence only and never imports D02 lifecycle objects.
    """
    merged = list(active_mapping_records)
    seen: Set[Tuple[str, str, str, str]] = set()
    for record in active_mapping_records:
        if record.role != "cm_indication":
            continue
        if not record.cross_domain_content_hash:
            raise CoverageValidationError(
                "active cm_indication requires cross_domain_content_hash")
        seen.add(_cross_domain_dedup_key(
            locator=record.locator, evidence_role=record.role,
            content_hash_value=record.cross_domain_content_hash))

    for ref in refs:
        if (ref.consumer_domain != "D01_aemh"
                or ref.evidence_role != "cm_indication"):
            raise CoverageValidationError(
                "unsupported cross-domain evidence consumer or role")
        if not ref.verify_content_hash():
            raise CoverageValidationError(
                "cross-domain evidence content hash verification failed")
        key = _cross_domain_dedup_key(
            locator=ref.source_locator, evidence_role=ref.evidence_role,
            content_hash_value=ref.content_hash)
        if key in seen:
            continue
        payload = dict(ref.context_payload)
        concept = str(payload.get("indication_concept", "")).strip()
        subject_ref = str(payload.get("subject_ref", "")).strip()
        if not concept or not subject_ref:
            raise CoverageValidationError(
                "cm_indication handoff requires concept and subject_ref")
        merged.append(SemanticRecord(
            role="cm_indication", concept=concept,
            locator=ref.source_locator, subject_ref=subject_ref,
            site_ref=str(payload.get("site_ref", "")).strip(),
            note=str(payload.get("indication_text", "")).strip(),
            cross_domain_content_hash=ref.content_hash,
        ))
        seen.add(key)
    return tuple(merged)


@dataclass(frozen=True)
class RoleAvailability:
    """Immutable role-availability/coverage surface (finding 1).

    Distinguishes an *available but empty* semantic role (the mapped source
    was covered and had zero rows) from a *missing* role (the mapping or
    source was absent).  An empty-but-covered role satisfies the required-
    role contract; a missing role does not.
    """

    available_roles: Tuple[str, ...]
    empty_covered_roles: Tuple[str, ...]

    def is_available(self, role: str) -> bool:
        return role in self.available_roles

    def is_empty_covered(self, role: str) -> bool:
        return role in self.empty_covered_roles

    def is_satisfied(self, role: str) -> bool:
        """A role is satisfied when it is available (has records) or
        explicitly empty-but-covered."""
        return self.is_available(role) or self.is_empty_covered(role)

    def missing_required(self, required: Sequence[str]) -> Tuple[str, ...]:
        return tuple(r for r in required if not self.is_satisfied(r))


@dataclass(frozen=True)
class SemanticRecordSet:
    """A collection of :class:`SemanticRecord` values for one subject/scope.

    Carries an explicit :class:`RoleAvailability` surface so an empty-but-
    covered semantic role differs from a missing role (finding 1).  The
    record collection may be empty -- in that case a missing-subject slice
    evaluation returns a fail-closed result instead of crashing.

    Validates recognized semantic roles and rejects mixed subject/site
    records (finding 1).
    """

    records: Tuple[SemanticRecord, ...] = ()
    subject_ref: str = ""
    site_ref: str = ""
    scope_key: str = ""
    available_roles: Tuple[str, ...] = ()
    empty_covered_roles: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            object.__setattr__(self, "records", tuple(self.records))
        if not isinstance(self.subject_ref, str) or not \
                self.subject_ref.strip():
            raise CoverageValidationError(
                "SemanticRecordSet.subject_ref is required")
        if not self.scope_key.strip():
            object.__setattr__(self, "scope_key", self.subject_ref)
        # Validate recognized roles and subject/site consistency.
        for rec in self.records:
            if not isinstance(rec, SemanticRecord):
                raise CoverageValidationError(
                    "SemanticRecordSet.records entries must be "
                    "SemanticRecord")
            if rec.role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet contains unrecognized role "
                    f"{rec.role!r}")
            rec_subject = rec.subject_ref.strip()
            rec_site = rec.site_ref.strip()
            if rec_subject and rec_subject != self.subject_ref:
                raise CoverageValidationError(
                    f"SemanticRecordSet subject_ref={self.subject_ref!r} "
                    f"but record {rec.locator.record_id!r} has "
                    f"subject_ref={rec_subject!r}")
            if rec_site and self.site_ref and rec_site != self.site_ref:
                raise CoverageValidationError(
                    f"SemanticRecordSet site_ref={self.site_ref!r} but "
                    f"record {rec.locator.record_id!r} has "
                    f"site_ref={rec_site!r}")
        # F4: Validate role availability coherence.
        # 1. available_roles and empty_covered_roles must be recognized roles.
        for role in self.available_roles:
            if role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet.available_roles contains "
                    f"unrecognized role {role!r}")
        for role in self.empty_covered_roles:
            if role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet.empty_covered_roles contains "
                    f"unrecognized role {role!r}")
        # 2. No overlap between available and empty-covered.
        overlap = set(self.available_roles) & set(self.empty_covered_roles)
        if overlap:
            raise CoverageValidationError(
                f"SemanticRecordSet roles cannot be both available and "
                f"empty-covered: {sorted(overlap)}")
        # 3. Every role present in records must appear in available_roles.
        roles_in_records = set(r.role for r in self.records)
        missing_from_available = roles_in_records - set(self.available_roles)
        if missing_from_available:
            raise CoverageValidationError(
                f"SemanticRecordSet: roles present in records but not in "
                f"available_roles: {sorted(missing_from_available)}")
        # Freeze availability tuples.
        object.__setattr__(
            self, "available_roles",
            tuple(sorted(set(self.available_roles))))
        object.__setattr__(
            self, "empty_covered_roles",
            tuple(sorted(set(self.empty_covered_roles))))

    @property
    def role_availability(self) -> RoleAvailability:
        return RoleAvailability(
            available_roles=self.available_roles,
            empty_covered_roles=self.empty_covered_roles,
        )

    def by_role(self, role: str) -> Tuple[SemanticRecord, ...]:
        return tuple(r for r in self.records if r.role == role)

    @property
    def reported_ae_records(self) -> Tuple[SemanticRecord, ...]:
        return tuple(
            r for r in self.records
            if r.is_reported_source and r.role == "reported_ae")

    @property
    def reported_mh_records(self) -> Tuple[SemanticRecord, ...]:
        return tuple(
            r for r in self.records
            if r.is_reported_source and r.role == "reported_mh")

    @property
    def reported_source_records(self) -> Tuple[SemanticRecord, ...]:
        """Reported AE/MH source records, excluding any AI assertion
        (finding 7)."""
        return self.reported_ae_records + self.reported_mh_records

    @property
    def evidence_records(self) -> Tuple[SemanticRecord, ...]:
        """All non-source records that may surface clues.  An AI-asserted
        ``reported_ae``/``reported_mh`` is treated as evidence here, never
        as a reported source fact (finding 7)."""
        result: List[SemanticRecord] = []
        for r in self.records:
            if r.role in OPTIONAL_EVIDENCE_ROLES:
                result.append(r)
            elif r.ai_assertion and r.role in ("reported_ae", "reported_mh"):
                result.append(r)
        return tuple(result)

    @property
    def temporal_anchor_records(self) -> Tuple[SemanticRecord, ...]:
        return self.by_role("temporal_anchor")

    def roles_present(self) -> Tuple[str, ...]:
        return tuple(sorted(set(r.role for r in self.records)))

    def missing_required_roles(
        self, required: Sequence[str] = REQUIRED_AEMH_ROLES,
    ) -> Tuple[str, ...]:
        return self.role_availability.missing_required(required)


# ---------------------------------------------------------------------------
# Medical grading: intensity, seriousness, monitoring priority (matrix §3.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MedicalGrading:
    """The three independent medical dimensions, kept separate.

    * ``intensity``: event severity/grade (e.g., "moderate", "Grade 2").
    * ``seriousness_criteria``: SAE/AESI/IME criterion tokens.
    * ``monitoring_priority``: high/medium/low/unknown -- this is the ONLY
      dimension that projects to ``RiskCandidate.severity_hint``.

    A high CTCAE grade does NOT auto-promote to SAE, and SAE does NOT
    require ``intensity=severe`` (matrix §3.5).
    """

    intensity: str = ""
    intensity_scale: str = ""
    seriousness_criteria: Tuple[str, ...] = ()
    monitoring_priority: str = MONITORING_PRIORITY_UNKNOWN

    def __post_init__(self) -> None:
        if self.monitoring_priority not in _VALID_MONITORING_PRIORITIES:
            raise CoverageValidationError(
                f"MedicalGrading.monitoring_priority="
                f"{self.monitoring_priority!r} is not one of "
                f"{_VALID_MONITORING_PRIORITIES}")
        object.__setattr__(
            self, "seriousness_criteria", tuple(self.seriousness_criteria))

    @property
    def has_seriousness_clue(self) -> bool:
        return any(
            token in _CLINICAL_FLAG_TOKENS
            for token in self.seriousness_criteria)

    @property
    def is_high_priority(self) -> bool:
        return self.monitoring_priority == MONITORING_PRIORITY_HIGH

    @property
    def severity_hint(self) -> str:
        """The R2 ``RiskCandidate.severity_hint`` value.

        Only monitoring priority maps here (matrix §3.5).  Unknown stays
        unknown; it is never defaulted to zero or low.
        """
        return self.monitoring_priority

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "intensity": self.intensity,
            "intensity_scale": self.intensity_scale,
            "seriousness_criteria": list(self.seriousness_criteria),
            "monitoring_priority": self.monitoring_priority,
        }


def derive_monitoring_priority(
    intensity: str = "",
    seriousness_criteria: Tuple[str, ...] = (),
    ai_confidence: float = 0.0,
) -> str:
    """Derive a conservative monitoring priority from available signals.

    This is a *conservative* derivation, not a clinical conclusion.  SAE /
    AESI / death / important-medical-event seriousness clues raise priority
    to ``high``.  A known ``severe`` intensity raises to at least ``medium``.
    Everything else stays ``unknown`` rather than defaulting to ``low`` --
    unknown means unknown (matrix §3.5 "未知强度/优先级保持 unknown").

    The function never conflates intensity with seriousness: a ``severe``
    intensity with no seriousness criteria is ``medium``, not ``high``.
    """
    serious = set(seriousness_criteria) & set(_CLINICAL_FLAG_TOKENS)
    if serious:
        return MONITORING_PRIORITY_HIGH
    norm_intensity = intensity.strip().lower() if intensity else ""
    if norm_intensity in ("severe", "grade 3", "grade 4", "grade 5", "grade4", "grade5"):
        return MONITORING_PRIORITY_MEDIUM
    if norm_intensity in ("moderate", "grade 2", "grade2"):
        return MONITORING_PRIORITY_MEDIUM
    if norm_intensity in ("mild", "grade 1", "grade1"):
        return MONITORING_PRIORITY_LOW
    return MONITORING_PRIORITY_UNKNOWN
