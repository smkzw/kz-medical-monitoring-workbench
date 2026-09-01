"""Read-only R5-S7 product projections.

The product boundary consumes one injected, typed authority packet.  The
synthetic packet in this module is available only when a caller explicitly
selects fixture mode; it is never a fallback for a missing authority packet.
No file, database, provider, model or frontend dependency is used here.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import date, timedelta
from functools import lru_cache
from hashlib import sha256
import json
import re
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple


PRODUCT_READ_SCHEMA = "medical-monitoring-r5-s7-product-read-model-v0.1"
R5_CONTRACT_SCHEMA = "medical-monitoring-r5-exact-contract-v0.3.1"
R5_CONTRACT_SHA256 = "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6"
SYNTHETIC_FIXTURE_MODE = "synthetic_offline"
SYNTHETIC_PROJECT_REF = "s7-synthetic-project-001"
SYNTHETIC_RUN_REF = "s7-run-current-001"
SYNTHETIC_CUTOFF_REF = "2026-03-31"
R5_FIXTURE_MODE_ENV = "WORKBENCH_R5_S7_FIXTURE_MODE"

DOMAINS = (
    "ae",
    "mh",
    "cm",
    "ip",
    "lab_exam",
    "hospital_procedure",
    "symptom_efficacy",
    "protocol_compliance",
)
DOMAIN_ENCODING = {
    "ae": {"event_shape": "rounded_rect", "line_style": "solid", "short_label_zh": "AE"},
    "mh": {"event_shape": "bookmark", "line_style": "dot_dash", "short_label_zh": "MH"},
    "cm": {"event_shape": "capsule", "line_style": "solid", "short_label_zh": "合并用药"},
    "ip": {"event_shape": "hexagon", "line_style": "step", "short_label_zh": "试验药"},
    "lab_exam": {"event_shape": "square", "line_style": "trend", "short_label_zh": "检验/检查"},
    "hospital_procedure": {"event_shape": "doorframe", "line_style": "solid", "short_label_zh": "住院/操作"},
    "symptom_efficacy": {"event_shape": "circle", "line_style": "trend", "short_label_zh": "症状/疗效"},
    "protocol_compliance": {"event_shape": "single_flag", "line_style": "bracket", "short_label_zh": "方案符合"},
}
SEVERITIES = ("critical", "high", "medium", "low")
DATE_STATES = ("exact", "partial", "conflicted", "missing")
VISIT_KINDS = ("nominal", "actual", "unscheduled")
CHANGE_KINDS = (
    "initial_current",
    "new",
    "upgraded",
    "continued",
    "downgraded",
    "resolved",
    "reopened",
    "superseded",
    "not_evaluable",
    "not_comparable",
)
CHANGE_CAUSES = (
    "data",
    "knowledge",
    "rule",
    "mapping",
    "model",
    "method",
    "coverage",
    "denominator",
    "population",
    "visibility",
    "mode",
    "user_decision",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Slice-07B subject flow contract (v0.2 + v0.3 §9). Flow records are optional
# packet members: legacy v0.3.1 packets keep their exact hash payload because
# empty flow fields are never added to the hash, while flow packets carry a
# dedicated authority contract version whose hash payload includes both fields.
FLOW_STAGE_KINDS = ("main", "branch_terminal", "unknown", "missing", "not_applicable")
FLOW_PATH_STATES = ("complete", "partial", "conflicted")
FLOW_STAGE_CHANGE_KINDS = (
    "initial",
    "new",
    "advanced",
    "returned",
    "corrected",
    "unchanged",
    "not_comparable",
)
FLOW_COVERAGE_BUCKETS = ("complete", "partial", "conflicted", "not_provided", "not_applicable")
FLOW_MAX_COLUMNS = 6
MID_HIGH_SEVERITIES = ("critical", "high", "medium")
R5_FLOW_AUTHORITY_CONTRACT_VERSION = "2026-08-28.1"
FLOW_NOT_PROVIDED_REASON_ZH = "本次数据未提供研究状态"
FLOW_SEVERITY_ZH = {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}


class R5ProductAdapterError(ValueError):
    """A typed authority or exact product projection cannot be used."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = code
        super().__init__(message or code)


def _required(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise R5ProductAdapterError("REQUIRED_VALUE", f"{field_name} is required")
    return text


def _sha(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise R5ProductAdapterError("DIGEST_INVALID", f"{field_name} must be lowercase SHA-256")
    return value


def _canonicalize(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _canonicalize(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_canonicalize(item) for item in value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _iso(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _date(value: Any, field_name: str, *, allow_none: bool = True) -> Optional[date]:
    if value is None and allow_none:
        return None
    if isinstance(value, date) and not isinstance(value, type(None)):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise R5ProductAdapterError("DATE_INVALID", f"{field_name} must be ISO date") from exc


def _unique(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    result = tuple(_required(value, field_name) for value in values)
    if len(result) != len(set(result)):
        raise R5ProductAdapterError("DUPLICATE_REFERENCE", f"{field_name} must be unique")
    return result


@dataclass(frozen=True)
class R5SourceRevisionPair:
    revision_id: str
    content_hash: str
    locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", _required(self.revision_id, "revision_id"))
        object.__setattr__(self, "content_hash", _sha(self.content_hash, "content_hash"))
        object.__setattr__(self, "locator_refs", _unique(self.locator_refs, "locator_refs"))


@dataclass(frozen=True)
class R5SourceRecord:
    locator_ref: str
    snapshot_ref: str
    source_file_ref: str
    source_revision_ref: str
    source_revision_content_hash: str
    record_ref: str
    canonical_location: str
    excerpt: str
    lineage: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "locator_ref",
            "snapshot_ref",
            "source_file_ref",
            "source_revision_ref",
            "record_ref",
            "canonical_location",
            "excerpt",
        ):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        object.__setattr__(
            self,
            "source_revision_content_hash",
            _sha(self.source_revision_content_hash, "source_revision_content_hash"),
        )
        object.__setattr__(self, "lineage", _unique(self.lineage, "lineage"))


@dataclass(frozen=True)
class R5EventRecord:
    event_ref: str
    subject_ref: str
    site_ref: str
    spine_ref: str
    domain: str
    subtype: str
    date_state: str
    start_date: Optional[date]
    end_date: Optional[date]
    visit_ref: Optional[str]
    risk_anchor_refs: Tuple[str, ...]
    source_locator_refs: Tuple[str, ...]
    label_zh: str

    def __post_init__(self) -> None:
        for name in ("event_ref", "subject_ref", "site_ref", "spine_ref", "label_zh"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.domain not in DOMAINS:
            raise R5ProductAdapterError("DOMAIN_UNKNOWN", f"unsupported domain: {self.domain}")
        if self.date_state not in DATE_STATES:
            raise R5ProductAdapterError("DATE_STATE_UNKNOWN", f"unsupported date state: {self.date_state}")
        if self.subtype not in {
            "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume",
            "lab", "exam", "hospitalization", "procedure", "symptom", "efficacy",
            "scale", "outcome", "trend", "protocol_deviation",
        }:
            raise R5ProductAdapterError("SUBTYPE_UNKNOWN", f"unsupported subtype: {self.subtype}")
        expected_domain = {
            "ae": {"ae"},
            "mh": {"mh"},
            "cm": {"concomitant_medication"},
            "ip": {"ip_dose", "ip_pause", "ip_resume"},
            "lab_exam": {"lab", "exam"},
            "hospital_procedure": {"hospitalization", "procedure"},
            "symptom_efficacy": {"symptom", "efficacy", "scale", "outcome", "trend"},
            "protocol_compliance": {"protocol_deviation"},
        }[self.domain]
        if self.subtype not in expected_domain:
            raise R5ProductAdapterError("DOMAIN_SUBTYPE_MISMATCH", self.subtype)
        if self.date_state == "exact" and self.start_date is None:
            raise R5ProductAdapterError("DATE_GEOMETRY_INVALID", "exact event requires start_date")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise R5ProductAdapterError("DATE_GEOMETRY_INVALID", "event date range is reversed")
        if self.visit_ref is not None:
            object.__setattr__(self, "visit_ref", _required(self.visit_ref, "visit_ref"))
        object.__setattr__(self, "risk_anchor_refs", _unique(self.risk_anchor_refs, "risk_anchor_refs"))
        object.__setattr__(self, "source_locator_refs", _unique(self.source_locator_refs, "source_locator_refs"))


@dataclass(frozen=True)
class R5VisitRecord:
    visit_ref: str
    subject_ref: str
    site_ref: str
    spine_ref: str
    visit_kind: str
    date_state: str
    actual_date: Optional[date]
    nominal_date: Optional[date]
    phase_ref: Optional[str]
    source_locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("visit_ref", "subject_ref", "site_ref", "spine_ref"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.visit_kind not in VISIT_KINDS:
            raise R5ProductAdapterError("VISIT_KIND_UNKNOWN", self.visit_kind)
        if self.date_state not in DATE_STATES:
            raise R5ProductAdapterError("DATE_STATE_UNKNOWN", self.date_state)
        if self.date_state == "exact" and self.actual_date is None and self.nominal_date is None:
            raise R5ProductAdapterError("DATE_GEOMETRY_INVALID", "exact visit requires a date")
        if self.phase_ref is not None:
            object.__setattr__(self, "phase_ref", _required(self.phase_ref, "phase_ref"))
        object.__setattr__(self, "source_locator_refs", _unique(self.source_locator_refs, "source_locator_refs"))


@dataclass(frozen=True)
class R5RiskRecord:
    risk_ref: str
    risk_instance_ref: str
    risk_key: str
    site_ref: str
    subject_ref: str
    spine_ref: str
    domain: str
    severity: str
    risk_type_zh: str
    date_state: str
    event_ref: Optional[str]
    visit_ref: Optional[str]
    risk_anchor_ref: str
    source_locator_refs: Tuple[str, ...]
    change_kind: str = "continued"
    change_cause: Optional[str] = None
    prior_snapshot_ref: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "risk_ref", "risk_instance_ref", "risk_key", "site_ref", "subject_ref",
            "spine_ref", "risk_type_zh", "risk_anchor_ref",
        ):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.domain not in DOMAINS:
            raise R5ProductAdapterError("DOMAIN_UNKNOWN", self.domain)
        if self.severity not in SEVERITIES:
            raise R5ProductAdapterError("SEVERITY_UNKNOWN", self.severity)
        if self.date_state not in DATE_STATES:
            raise R5ProductAdapterError("DATE_STATE_UNKNOWN", self.date_state)
        if self.change_kind not in CHANGE_KINDS:
            raise R5ProductAdapterError("CHANGE_KIND_UNKNOWN", self.change_kind)
        if self.change_cause is not None and self.change_cause not in CHANGE_CAUSES:
            raise R5ProductAdapterError("CHANGE_CAUSE_UNKNOWN", self.change_cause)
        for name in ("event_ref", "visit_ref", "prior_snapshot_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _required(value, name))
        object.__setattr__(self, "source_locator_refs", _unique(self.source_locator_refs, "source_locator_refs"))


@dataclass(frozen=True)
class R5SiteRecord:
    site_ref: str
    subject_refs: Tuple[str, ...]
    pattern_refs: Tuple[str, ...]
    individual_risk_refs: Tuple[str, ...]
    measure_refs: Tuple[str, ...]
    domain: str
    severity: str
    numerator: int
    denominator: Optional[int]
    coverage_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "site_ref", _required(self.site_ref, "site_ref"))
        object.__setattr__(self, "subject_refs", _unique(self.subject_refs, "subject_refs"))
        object.__setattr__(self, "pattern_refs", _unique(self.pattern_refs, "pattern_refs"))
        object.__setattr__(self, "individual_risk_refs", _unique(self.individual_risk_refs, "individual_risk_refs"))
        object.__setattr__(self, "measure_refs", _unique(self.measure_refs, "measure_refs"))
        if self.domain not in DOMAINS or self.severity not in SEVERITIES:
            raise R5ProductAdapterError("SITE_SEMANTIC_INVALID", self.site_ref)
        if type(self.numerator) is not int or self.numerator < 0:
            raise R5ProductAdapterError("NUMERATOR_INVALID", self.site_ref)
        if self.denominator is not None and (type(self.denominator) is not int or self.denominator < 0):
            raise R5ProductAdapterError("DENOMINATOR_INVALID", self.site_ref)
        if self.denominator is not None and self.numerator > self.denominator:
            raise R5ProductAdapterError("NUMERATOR_INVALID", self.site_ref)
        if self.coverage_state not in {"complete", "partial", "small_sample", "not_evaluable"}:
            raise R5ProductAdapterError("COVERAGE_STATE_UNKNOWN", self.coverage_state)


@dataclass(frozen=True)
class R5SiteAudienceRecord:
    """Audience-facing site name kept separate from frozen analytical site facts."""

    site_ref: str
    site_label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "site_ref", _required(self.site_ref, "site_ref"))
        object.__setattr__(self, "site_label", _required(self.site_label, "site_label"))


@dataclass(frozen=True)
class R5SubjectRecord:
    subject_ref: str
    site_ref: str
    spine_ref: str
    subject_label: str

    def __post_init__(self) -> None:
        for name in ("subject_ref", "site_ref", "spine_ref", "subject_label"):
            object.__setattr__(self, name, _required(getattr(self, name), name))


@dataclass(frozen=True)
class R5HistoryRecord:
    subject_ref: str
    candidate_ref: str
    later_fact_ref: Optional[str]
    event_kind: str
    match_state: Optional[str]
    from_snapshot_ref: str
    to_snapshot_ref: str
    identity_evidence_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("subject_ref", "candidate_ref", "from_snapshot_ref", "to_snapshot_ref"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.later_fact_ref is not None:
            object.__setattr__(self, "later_fact_ref", _required(self.later_fact_ref, "later_fact_ref"))
        if self.event_kind not in {"reminder_created", "match_decided", "withdrawn", "reappeared"}:
            raise R5ProductAdapterError("HISTORY_EVENT_UNKNOWN", self.event_kind)
        if self.match_state is not None and self.match_state not in {"exact", "ambiguous", "rejected"}:
            raise R5ProductAdapterError("MATCH_STATE_UNKNOWN", self.match_state)
        object.__setattr__(self, "identity_evidence_refs", _unique(self.identity_evidence_refs, "identity_evidence_refs"))


@dataclass(frozen=True)
class R5FlowStageRecord:
    """One protocol-defined stage of the subject flow catalog.

    The catalog is produced upstream per project; this module only receives,
    validates and projects it. ``unknown``/``missing``/``not_applicable``
    stages stay distinct and are never merged.
    """

    stage_ref: str
    stage_label_zh: str
    column_order: int
    row_order: int
    stage_kind: str
    is_entry: bool
    is_terminal: bool
    source_locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage_ref", _required(self.stage_ref, "stage_ref"))
        object.__setattr__(self, "stage_label_zh", _required(self.stage_label_zh, "stage_label_zh"))
        for name in ("column_order", "row_order"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise R5ProductAdapterError("FLOW_STAGE_ORDER_INVALID", f"{self.stage_ref}.{name}")
        if self.stage_kind not in FLOW_STAGE_KINDS:
            raise R5ProductAdapterError("FLOW_STAGE_KIND_UNKNOWN", self.stage_kind)
        for name in ("is_entry", "is_terminal"):
            if type(getattr(self, name)) is not bool:
                raise R5ProductAdapterError("FLOW_STAGE_FLAG_INVALID", f"{self.stage_ref}.{name}")
        object.__setattr__(self, "source_locator_refs", _unique(self.source_locator_refs, "source_locator_refs"))


@dataclass(frozen=True)
class R5SubjectFlowStep:
    """One ordered step of a subject's canonical flow path."""

    stage_ref: str
    entered_date: Optional[date]
    basis_date: Optional[date]
    date_state: str
    transition_reason_zh: str
    source_locator_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage_ref", _required(self.stage_ref, "stage_ref"))
        object.__setattr__(self, "entered_date", _date(self.entered_date, "entered_date"))
        object.__setattr__(self, "basis_date", _date(self.basis_date, "basis_date"))
        if self.date_state not in DATE_STATES:
            raise R5ProductAdapterError("DATE_STATE_UNKNOWN", self.date_state)
        if self.date_state == "exact" and self.entered_date is None:
            raise R5ProductAdapterError("DATE_GEOMETRY_INVALID", "exact flow step requires entered_date")
        object.__setattr__(self, "transition_reason_zh", _required(self.transition_reason_zh, "transition_reason_zh"))
        object.__setattr__(self, "source_locator_refs", _unique(self.source_locator_refs, "source_locator_refs"))


@dataclass(frozen=True)
class R5SubjectFlowPathRecord:
    """The single canonical flow path of one in-scope subject.

    ``spine_ref`` is intentionally absent: it is joined uniquely from the same
    packet's ``R5SubjectRecord`` by ``subject_ref`` and never duplicated here.
    """

    subject_ref: str
    site_ref: str
    steps: Tuple[R5SubjectFlowStep, ...]
    path_state: str
    stage_change_kind: str
    prior_run_current_stage_ref: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_ref", _required(self.subject_ref, "subject_ref"))
        object.__setattr__(self, "site_ref", _required(self.site_ref, "site_ref"))
        values = tuple(self.steps)
        if not values or any(type(item) is not R5SubjectFlowStep for item in values):
            raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED", "steps")
        object.__setattr__(self, "steps", values)
        if self.path_state not in FLOW_PATH_STATES:
            raise R5ProductAdapterError("FLOW_PATH_STATE_UNKNOWN", self.path_state)
        if self.stage_change_kind not in FLOW_STAGE_CHANGE_KINDS:
            raise R5ProductAdapterError("FLOW_STAGE_CHANGE_KIND_UNKNOWN", self.stage_change_kind)
        if self.prior_run_current_stage_ref is not None:
            object.__setattr__(
                self,
                "prior_run_current_stage_ref",
                _required(self.prior_run_current_stage_ref, "prior_run_current_stage_ref"),
            )


@dataclass(frozen=True)
class R5AuthorityPacket:
    """The only object accepted as a product authority dependency."""

    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_state: str
    cutoff_ref: Optional[str]
    project_label: str
    authority_contract_id: str
    authority_contract_version: str
    audience_contract_id: str
    visibility_decision_id: str
    visibility_decision_hash: str
    evaluation_content_identities: Tuple[str, ...]
    source_revision_content_pairs: Tuple[R5SourceRevisionPair, ...]
    sources: Tuple[R5SourceRecord, ...]
    sites: Tuple[R5SiteRecord, ...]
    subjects: Tuple[R5SubjectRecord, ...]
    events: Tuple[R5EventRecord, ...]
    visits: Tuple[R5VisitRecord, ...]
    risks: Tuple[R5RiskRecord, ...]
    histories: Tuple[R5HistoryRecord, ...] = ()
    flow_stages: Tuple[R5FlowStageRecord, ...] = ()
    subject_flow_paths: Tuple[R5SubjectFlowPathRecord, ...] = ()
    site_audience: Tuple[R5SiteAudienceRecord, ...] = ()
    synthetic: bool = False
    data_mode: str = "authority"
    aggregate_version: int = 0
    authority_hash: str = ""
    source_snapshot_sha256: str = ""

    def __post_init__(self) -> None:
        for name in (
            "project_ref", "run_ref", "snapshot_ref", "project_label",
            "authority_contract_id", "authority_contract_version", "audience_contract_id",
            "visibility_decision_id",
        ):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.cutoff_state not in {"present", "absent"}:
            raise R5ProductAdapterError("CUTOFF_STATE_UNKNOWN", self.cutoff_state)
        if self.cutoff_state == "present":
            object.__setattr__(self, "cutoff_ref", _required(self.cutoff_ref, "cutoff_ref"))
        elif self.cutoff_ref is not None:
            raise R5ProductAdapterError("CUTOFF_IDENTITY_MISMATCH", "absent cutoff cannot carry cutoff_ref")
        object.__setattr__(self, "visibility_decision_hash", _sha(self.visibility_decision_hash, "visibility_decision_hash"))
        object.__setattr__(
            self,
            "evaluation_content_identities",
            tuple(_sha(item, "evaluation_content_identity") for item in self.evaluation_content_identities),
        )
        if not self.evaluation_content_identities:
            raise R5ProductAdapterError("AUTHORITY_RECEIPT_INVALID", "evaluation identities are required")
        for name, item_type in (
            ("source_revision_content_pairs", R5SourceRevisionPair),
            ("sources", R5SourceRecord),
            ("sites", R5SiteRecord),
            ("subjects", R5SubjectRecord),
            ("events", R5EventRecord),
            ("visits", R5VisitRecord),
            ("risks", R5RiskRecord),
            ("histories", R5HistoryRecord),
            ("flow_stages", R5FlowStageRecord),
            ("subject_flow_paths", R5SubjectFlowPathRecord),
            ("site_audience", R5SiteAudienceRecord),
        ):
            values = tuple(getattr(self, name))
            if any(type(item) is not item_type for item in values):
                raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED", name)
            object.__setattr__(self, name, values)
        if not self.sources or not self.subjects or not self.risks:
            raise R5ProductAdapterError("AUTHORITY_PACKET_INCOMPLETE")
        if type(self.aggregate_version) is not int or self.aggregate_version < 0:
            raise R5ProductAdapterError("AGGREGATE_VERSION_INVALID")
        source_refs = {item.locator_ref for item in self.sources}
        subject_refs = {item.subject_ref for item in self.subjects}
        site_refs = {item.site_ref for item in self.sites}
        audience_site_refs = [item.site_ref for item in self.site_audience]
        if len(audience_site_refs) != len(set(audience_site_refs)) or not set(
            audience_site_refs
        ).issubset(site_refs):
            raise R5ProductAdapterError("AUTHORITY_MEMBER_MISMATCH", "site_audience")
        for risk in self.risks:
            if risk.subject_ref not in subject_refs or risk.site_ref not in site_refs:
                raise R5ProductAdapterError("AUTHORITY_MEMBER_MISMATCH", risk.risk_ref)
            if not set(risk.source_locator_refs).issubset(source_refs):
                raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND", risk.risk_ref)
        for event in self.events:
            if event.subject_ref not in subject_refs or event.site_ref not in site_refs:
                raise R5ProductAdapterError("AUTHORITY_MEMBER_MISMATCH", event.event_ref)
            if not set(event.source_locator_refs).issubset(source_refs):
                raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND", event.event_ref)
        for source in self.sources:
            if source.snapshot_ref != self.snapshot_ref:
                raise R5ProductAdapterError("SOURCE_SNAPSHOT_MISMATCH", source.locator_ref)
        if self.flow_stages or self.subject_flow_paths:
            # A flow packet must declare the dedicated flow authority contract
            # version; legacy packets keep their original version and hash.
            if self.authority_contract_version != R5_FLOW_AUTHORITY_CONTRACT_VERSION:
                raise R5ProductAdapterError(
                    "FLOW_CONTRACT_VERSION_MISMATCH", self.authority_contract_version
                )
            stage_refs = [item.stage_ref for item in self.flow_stages]
            if len(stage_refs) != len(set(stage_refs)):
                raise R5ProductAdapterError("FLOW_STAGE_DUPLICATE")
            for stage in self.flow_stages:
                if not set(stage.source_locator_refs).issubset(source_refs):
                    raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND", stage.stage_ref)
            for path in self.subject_flow_paths:
                for step in path.steps:
                    if not set(step.source_locator_refs).issubset(source_refs):
                        raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND", path.subject_ref)
        payload = self._hash_payload()
        expected_authority = canonical_sha256({"receipt": payload, "contract": R5_CONTRACT_SCHEMA})
        expected_source = canonical_sha256({"authority_hash": expected_authority, "payload": payload})
        if self.authority_hash and self.authority_hash != expected_authority:
            raise R5ProductAdapterError("AUTHORITY_DIGEST_MISMATCH", "authority_hash")
        if self.source_snapshot_sha256 and self.source_snapshot_sha256 != expected_source:
            raise R5ProductAdapterError("SOURCE_DIGEST_MISMATCH", "source_snapshot_sha256")
        object.__setattr__(self, "authority_hash", expected_authority)
        object.__setattr__(self, "source_snapshot_sha256", expected_source)
        if self.synthetic:
            if self.data_mode != SYNTHETIC_FIXTURE_MODE or not self.project_ref.startswith("s7-synthetic-"):
                raise R5ProductAdapterError("SYNTHETIC_IDENTITY_INVALID")

    def _hash_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "project_ref": self.project_ref,
            "run_ref": self.run_ref,
            "snapshot_ref": self.snapshot_ref,
            "cutoff_state": self.cutoff_state,
            "cutoff_ref": self.cutoff_ref,
            "project_label": self.project_label,
            "authority_contract_id": self.authority_contract_id,
            "authority_contract_version": self.authority_contract_version,
            "audience_contract_id": self.audience_contract_id,
            "visibility_decision_id": self.visibility_decision_id,
            "visibility_decision_hash": self.visibility_decision_hash,
            "evaluation_content_identities": self.evaluation_content_identities,
            "source_revision_content_pairs": self.source_revision_content_pairs,
            "sources": self.sources,
            "sites": self.sites,
            "subjects": self.subjects,
            "events": self.events,
            "visits": self.visits,
            "risks": self.risks,
            "histories": self.histories,
            "synthetic": self.synthetic,
            "data_mode": self.data_mode,
            "aggregate_version": self.aggregate_version,
        }
        # Legacy v0.3.1 packets must keep their original hash: empty flow
        # fields are never injected into the hash payload.
        if self.flow_stages:
            payload["flow_stages"] = self.flow_stages
        if self.subject_flow_paths:
            payload["subject_flow_paths"] = self.subject_flow_paths
        if self.site_audience:
            payload["site_audience"] = self.site_audience
        return payload

    @property
    def receipt_id(self) -> str:
        return f"r5:receipt:{self.project_ref}:{self.snapshot_ref}"

    def authority_receipt(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "authority_contract_id": self.authority_contract_id,
            "authority_contract_version": self.authority_contract_version,
            "audience_contract_id": self.audience_contract_id,
            "project_ref": self.project_ref,
            "run_ref": self.run_ref,
            "snapshot_ref": self.snapshot_ref,
            "cutoff_state": self.cutoff_state,
            "cutoff_ref": self.cutoff_ref,
            "authority_hash": self.authority_hash,
            "source_snapshot_sha256": self.source_snapshot_sha256,
            "visibility_decision_id": self.visibility_decision_id,
            "visibility_decision_hash": self.visibility_decision_hash,
            "evaluation_content_identities": list(self.evaluation_content_identities),
            "source_revision_content_pairs": [
                {
                    "revision_id": item.revision_id,
                    "content_hash": item.content_hash,
                    "locator_refs": list(item.locator_refs),
                }
                for item in self.source_revision_content_pairs
            ],
            "projectable": True,
            "synthetic": self.synthetic,
            "data_mode": self.data_mode,
        }


