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


class R5AuthorityProvider:
    """Provider contract used by the router; it must return a typed packet."""

    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        raise NotImplementedError


class SyntheticR5AuthorityProvider(R5AuthorityProvider):
    """Explicitly isolated, deterministic S7 fixture provider."""

    fixture_mode = True

    @lru_cache(maxsize=16)
    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        return build_synthetic_r5_authority_packet(
            project_ref=project_ref,
            run_ref=run_ref,
            snapshot_ref=snapshot_ref,
            cutoff_ref=cutoff_ref,
        )


def _source(
    locator_ref: str,
    snapshot_ref: str,
    revision: str,
    excerpt: str,
    *,
    record_ref: Optional[str] = None,
) -> R5SourceRecord:
    content_hash = canonical_sha256({"revision": revision, "locator_ref": locator_ref, "excerpt": excerpt})
    location_labels = {
        "s7-source-pd-10008": ("方案执行 Data Listing 第 10008 行", "方案执行 Data Listing · 第 10008 行 · 访视日期单元格"),
        "s7-source-ae-06021": ("AE Data Listing 第 06021 行", "AE Data Listing · 第 06021 行 · 事件日期单元格"),
        "s7-source-ae-mh-06021": ("AE/MH 核查表第 06021 行", "AE/MH 核查表 · 第 06021 行 · 匹配关系"),
        "s7-source-date-001": ("日期核查表第 001 行", "日期核查表 · 第 001 行 · 日期状态单元格"),
        "s7-source-density-001": ("高密度验证清单", "高密度验证清单 · 事件与风险定位"),
    }
    human_record_ref, human_location = location_labels.get(locator_ref, ("合成验证记录", "合成验证来源"))
    return R5SourceRecord(
        locator_ref=locator_ref,
        snapshot_ref=snapshot_ref,
        source_file_ref=f"s7-synthetic-source-file:{revision}",
        source_revision_ref=revision,
        source_revision_content_hash=content_hash,
        record_ref=record_ref or human_record_ref,
        canonical_location=human_location,
        excerpt=excerpt,
        lineage=("本次数据版本", "来源文件", human_record_ref),
    )


def _risk(
    risk_instance_ref: str,
    *,
    risk_key: str,
    site_ref: str,
    subject_ref: str,
    spine_ref: str,
    domain: str,
    severity: str,
    risk_type_zh: str,
    event_ref: str,
    visit_ref: str,
    source_locator_ref: str,
    snapshot_ref: str,
    change_kind: str = "continued",
    change_cause: Optional[str] = None,
) -> R5RiskRecord:
    return R5RiskRecord(
        risk_ref=risk_key,
        risk_instance_ref=risk_instance_ref,
        risk_key=risk_key,
        site_ref=site_ref,
        subject_ref=subject_ref,
        spine_ref=spine_ref,
        domain=domain,
        severity=severity,
        risk_type_zh=risk_type_zh,
        date_state="exact",
        event_ref=event_ref,
        visit_ref=visit_ref,
        risk_anchor_ref=f"s7-anchor-{risk_instance_ref.removeprefix('s7-risk-')}",
        source_locator_refs=(source_locator_ref,),
        change_kind=change_kind,
        change_cause=change_cause,
        prior_snapshot_ref=("s7-snapshot-prior-001" if snapshot_ref != "s7-snapshot-current-001" else None),
    )


def _build_base_records(snapshot_ref: str, cutoff_ref: str) -> tuple[
    tuple[R5SourceRecord, ...],
    tuple[R5SiteRecord, ...],
    tuple[R5SubjectRecord, ...],
    tuple[R5EventRecord, ...],
    tuple[R5VisitRecord, ...],
    tuple[R5RiskRecord, ...],
    tuple[R5HistoryRecord, ...],
]:
    subject_a = R5SubjectRecord("s7-subject-10008", "s7-site-010", "s7-spine-10008", "受试者 10008")
    subject_b = R5SubjectRecord("s7-subject-06021", "s7-site-006", "s7-spine-06021", "受试者 06021")
    subject_date = R5SubjectRecord("s7-subject-date-001", "s7-site-010", "s7-spine-date-001", "受试者 DATE-001")
    subjects = (subject_a, subject_b, subject_date)
    visits = (
        R5VisitRecord("s7-visit-06021-w2", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "actual", "exact", date(2026, 1, 31), None, "s7-phase-screening", ("s7-source-ae-mh-06021",)),
        R5VisitRecord("s7-visit-w3", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "actual", "exact", date(2026, 2, 28), None, "s7-phase-treatment", ("s7-source-ae-06021",)),
        R5VisitRecord("s7-visit-w2", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "actual", "exact", date(2026, 2, 15), None, "s7-phase-treatment", ("s7-source-pd-10008",)),
        R5VisitRecord("s7-visit-w4", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "actual", "exact", date(2026, 3, 15), None, "s7-phase-treatment", ("s7-source-pd-10008",)),
        R5VisitRecord("s7-visit-date-exact", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "actual", "exact", date(2026, 1, 10), None, "s7-phase-screening", ("s7-source-date-001",)),
        R5VisitRecord("s7-visit-date-pending", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "unscheduled", "missing", None, None, None, ("s7-source-date-001",)),
    )
    events = (
        R5EventRecord("s7-event-pd-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "protocol_compliance", "protocol_deviation", "exact", date(2026, 3, 15), date(2026, 3, 15), "s7-visit-w4", ("s7-anchor-pd-10008",), ("s7-source-pd-10008",), "方案执行偏离"),
        R5EventRecord("s7-event-ae-06021", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "ae", "ae", "exact", date(2026, 2, 28), date(2026, 3, 2), "s7-visit-w3", ("s7-anchor-ae-06021",), ("s7-source-ae-06021",), "不良事件记录"),
        R5EventRecord("s7-event-mh-06021", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "mh", "mh", "exact", date(2026, 1, 31), date(2026, 1, 31), "s7-visit-06021-w2", ("s7-anchor-ae-mh-06021",), ("s7-source-ae-mh-06021",), "既往病史记录"),
        R5EventRecord("s7-event-cm-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "cm", "concomitant_medication", "exact", date(2026, 2, 10), date(2026, 2, 12), "s7-visit-w4", (), ("s7-source-pd-10008",), "合并用药"),
        R5EventRecord("s7-event-ip-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "ip", "ip_dose", "exact", date(2026, 1, 15), date(2026, 3, 15), "s7-visit-w4", (), ("s7-source-pd-10008",), "试验药给药"),
        R5EventRecord("s7-event-lab-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "lab_exam", "lab", "partial", date(2026, 2, 20), None, "s7-visit-w4", (), ("s7-source-pd-10008",), "实验室检查"),
        R5EventRecord("s7-event-procedure-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "hospital_procedure", "procedure", "exact", date(2026, 2, 22), date(2026, 2, 22), "s7-visit-w4", (), ("s7-source-pd-10008",), "操作记录"),
        R5EventRecord("s7-event-symptom-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "symptom_efficacy", "symptom", "conflicted", date(2026, 2, 1), date(2026, 2, 10), "s7-visit-w4", (), ("s7-source-pd-10008",), "症状/疗效指标"),
        R5EventRecord("s7-event-date-exact", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "ae", "ae", "exact", date(2026, 1, 10), date(2026, 1, 10), "s7-visit-date-exact", (), ("s7-source-date-001",), "日期明确记录"),
        R5EventRecord("s7-event-date-partial", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "lab_exam", "lab", "partial", date(2026, 2, 1), None, "s7-visit-date-pending", (), ("s7-source-date-001",), "日期部分明确记录"),
        R5EventRecord("s7-event-date-conflicted", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "symptom_efficacy", "symptom", "conflicted", date(2026, 2, 15), date(2026, 2, 20), "s7-visit-date-pending", (), ("s7-source-date-001",), "日期冲突记录"),
        R5EventRecord("s7-event-date-missing", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "protocol_compliance", "protocol_deviation", "missing", None, None, "s7-visit-date-pending", (), ("s7-source-date-001",), "日期待核实记录"),
    )
    risks = (
        _risk("s7-risk-pd-10008", risk_key="s7-risk-key-pd-10008", site_ref=subject_a.site_ref, subject_ref=subject_a.subject_ref, spine_ref=subject_a.spine_ref, domain="protocol_compliance", severity="high", risk_type_zh="方案执行偏离", event_ref="s7-event-pd-10008", visit_ref="s7-visit-w4", source_locator_ref="s7-source-pd-10008", snapshot_ref=snapshot_ref, change_kind="new", change_cause="data"),
        _risk("s7-risk-ae-06021", risk_key="s7-risk-key-ae-06021", site_ref=subject_b.site_ref, subject_ref=subject_b.subject_ref, spine_ref=subject_b.spine_ref, domain="ae", severity="medium", risk_type_zh="不良事件与记录一致性", event_ref="s7-event-ae-06021", visit_ref="s7-visit-w3", source_locator_ref="s7-source-ae-06021", snapshot_ref=snapshot_ref, change_kind="continued", change_cause="coverage"),
        _risk("s7-risk-ae-mh-06021", risk_key="s7-risk-key-ae-mh-06021", site_ref=subject_b.site_ref, subject_ref=subject_b.subject_ref, spine_ref=subject_b.spine_ref, domain="ae", severity="high", risk_type_zh="AE/MH匹配历史", event_ref="s7-event-mh-06021", visit_ref="s7-visit-06021-w2", source_locator_ref="s7-source-ae-mh-06021", snapshot_ref=snapshot_ref, change_kind="upgraded", change_cause="data"),
    )
    events = tuple(
        event
        for event in events
        if event.subject_ref in {item.subject_ref for item in subjects}
    )
    histories = (
        R5HistoryRecord(subject_b.subject_ref, "s7-candidate-ae-mh-06021", "s7-later-fact-ae-mh-06021", "reappeared", "exact", "s7-snapshot-prior-001", snapshot_ref, ("s7-source-ae-mh-06021",)),
    )
    sources = (
        _source("s7-source-pd-10008", snapshot_ref, "s7-rev-pd-001", "参与者 10008；第 4 周访视；实际访视日期 2026-03-15；方案规定访视窗口 2026-03-08 至 2026-03-12。"),
        _source("s7-source-ae-06021", snapshot_ref, "s7-rev-ae-001", "AE记录与对应访视的原始定位片段。"),
        _source("s7-source-ae-mh-06021", snapshot_ref, "s7-rev-aemh-001", "AE/MH匹配历史的原始定位片段。"),
        _source("s7-source-date-001", snapshot_ref, "s7-rev-date-001", "日期状态记录：保留缺失日期，不推断主轴日期。"),
    )
    sites = (
        R5SiteRecord("s7-site-006", (subject_b.subject_ref,), ("s7-pattern-site-006",), ("s7-risk-key-ae-06021", "s7-risk-key-ae-mh-06021"), ("s7-measure-site-006",), "ae", "high", 2, 12, "complete"),
        R5SiteRecord("s7-site-010", (subject_a.subject_ref, subject_date.subject_ref), ("s7-pattern-site-010",), ("s7-risk-key-pd-10008",), ("s7-measure-site-010",), "protocol_compliance", "high", 1, 8, "complete"),
        R5SiteRecord("s7-site-small-001", (), ("s7-pattern-site-small-001",), (), ("s7-measure-site-small-001",), "protocol_compliance", "low", 0, 0, "small_sample"),
    )
    return sources, sites, subjects, events, visits, risks, histories


def _build_density_records(snapshot_ref: str) -> tuple[tuple[R5SourceRecord, ...], tuple[R5SiteRecord, ...], tuple[R5SubjectRecord, ...], tuple[R5EventRecord, ...], tuple[R5VisitRecord, ...], tuple[R5RiskRecord, ...], tuple[R5HistoryRecord, ...]]:
    subject = R5SubjectRecord("s7-subject-density-001", "s7-site-010", "s7-spine-density-001", "受试者 DENSITY-001")
    source = _source("s7-source-density-001", snapshot_ref, "s7-rev-density-001", "高密度 synthetic 事件定位片段。")
    sources = (source,)
    visits = tuple(
        R5VisitRecord(f"s7-visit-density-{index:04d}", subject.subject_ref, subject.site_ref, subject.spine_ref, "actual", "exact", date(2026, 1, 1) + timedelta(days=index - 1), None, "s7-phase-density", (source.locator_ref,))
        for index in range(1, 41)
    )
    density_labels = {
        "ae": "不良事件记录核查",
        "mh": "既往史记录核查",
        "cm": "合并用药核查",
        "ip": "试验药使用核查",
        "lab_exam": "检验检查异常核查",
        "hospital_procedure": "住院或操作记录核查",
        "symptom_efficacy": "症状与疗效趋势核查",
        "protocol_compliance": "方案执行核查",
    }
    events = tuple(
        R5EventRecord(
            event_ref=f"s7-event-density-{index:04d}",
            subject_ref=subject.subject_ref,
            site_ref=subject.site_ref,
            spine_ref=subject.spine_ref,
            domain=DOMAINS[index % len(DOMAINS)],
            subtype=("ae", "mh", "concomitant_medication", "ip_dose", "lab", "hospitalization", "symptom", "protocol_deviation")[index % 8],
            date_state="exact",
            start_date=date(2026, 1, 1) + timedelta(days=(index - 1) % len(visits)),
            end_date=None,
            visit_ref=visits[(index - 1) % len(visits)].visit_ref,
            risk_anchor_refs=(f"s7-anchor-density-{index:03d}",) if index <= 300 else (),
            source_locator_refs=(source.locator_ref,),
            label_zh=f"{density_labels[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 条记录",
        )
        for index in range(1, 1001)
    )
    risks = tuple(
        R5RiskRecord(
            risk_ref=f"s7-risk-key-density-{index:03d}",
            risk_instance_ref=f"s7-risk-density-{index:03d}",
            risk_key=f"s7-risk-key-density-{index:03d}",
            site_ref=subject.site_ref,
            subject_ref=subject.subject_ref,
            spine_ref=subject.spine_ref,
            domain=DOMAINS[index % len(DOMAINS)],
            severity=("high", "medium", "low")[index % 3],
            risk_type_zh=f"{density_labels[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 项",
            date_state="exact",
            event_ref=events[index - 1].event_ref,
            visit_ref=events[index - 1].visit_ref,
            risk_anchor_ref=f"s7-anchor-density-{index:03d}",
            source_locator_refs=(source.locator_ref,),
            change_kind="continued",
            change_cause="coverage",
        )
        for index in range(1, 301)
    )
    site = R5SiteRecord(subject.site_ref, (subject.subject_ref,), ("s7-pattern-density-001",), tuple(risk.risk_ref for risk in risks), ("s7-measure-density-001",), "ae", "high", 300, 1000, "complete")
    return sources, (site,), (subject,), events, visits, risks, ()


def _build_flow_records() -> tuple[tuple[R5FlowStageRecord, ...], tuple[R5SubjectFlowPathRecord, ...]]:
    """Deterministic Slice-07B synthetic flow catalog and canonical paths.

    The reserved missing entry exercises the partial-path bucket; the same
    column branch (治疗中 → 完成研究) and the next column branch (治疗中 →
    永久停药) are both legal per the frozen v0.3 §4 edge set.
    """

    flow_source_refs = ("s7-source-pd-10008",)
    stages = (
        R5FlowStageRecord("s7-flow-stage-consent", "已签署知情同意", 0, 0, "main", True, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-missing", "既往阶段数据未提供", 0, 1, "missing", True, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-screening", "筛选", 1, 0, "main", False, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-screen-fail", "筛选失败", 1, 1, "branch_terminal", False, True, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-treatment", "治疗中", 2, 0, "main", False, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-completed", "完成研究", 2, 1, "branch_terminal", False, True, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-stopped", "永久停药", 3, 0, "branch_terminal", False, True, flow_source_refs),
    )
    paths = (
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-10008",
            site_ref="s7-site-010",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-consent", date(2026, 1, 10), date(2026, 1, 10), "exact", "签署知情同意，进入筛选", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 1, 20), date(2026, 1, 20), "exact", "筛选通过，进入治疗", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-treatment", date(2026, 2, 1), date(2026, 2, 1), "exact", "入组治疗", flow_source_refs),
            ),
            path_state="complete",
            stage_change_kind="unchanged",
            prior_run_current_stage_ref="s7-flow-stage-treatment",
        ),
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-06021",
            site_ref="s7-site-006",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-consent", date(2026, 1, 5), date(2026, 1, 5), "exact", "签署知情同意，进入筛选", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 1, 12), date(2026, 1, 12), "exact", "筛选未通过", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screen-fail", date(2026, 1, 20), date(2026, 1, 20), "exact", "筛选失败，终止研究", flow_source_refs),
            ),
            path_state="complete",
            stage_change_kind="advanced",
            prior_run_current_stage_ref="s7-flow-stage-screening",
        ),
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-date-001",
            site_ref="s7-site-010",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-missing", None, None, "missing", "既往阶段数据未提供", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 2, 1), None, "partial", "补录筛选记录", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-treatment", date(2026, 2, 10), None, "partial", "进入治疗", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-completed", date(2026, 2, 20), None, "partial", "完成研究", flow_source_refs),
            ),
            path_state="partial",
            stage_change_kind="new",
        ),
    )
    return stages, paths


def build_synthetic_r5_authority_packet(
    *,
    project_ref: str = SYNTHETIC_PROJECT_REF,
    run_ref: Optional[str] = SYNTHETIC_RUN_REF,
    snapshot_ref: Optional[str] = "s7-snapshot-current-001",
    cutoff_ref: Optional[str] = SYNTHETIC_CUTOFF_REF,
) -> R5AuthorityPacket:
    """Build an isolated S7 fixture; callers must explicitly opt into it."""

    if project_ref != SYNTHETIC_PROJECT_REF:
        raise R5ProductAdapterError("PROJECT_NOT_IN_SYNTHETIC_PACKET")
    if run_ref not in {None, SYNTHETIC_RUN_REF}:
        raise R5ProductAdapterError("RUN_NOT_IN_SYNTHETIC_PACKET")
    snapshot = snapshot_ref or "s7-snapshot-current-001"
    if snapshot == "s7-snapshot-density-001":
        cutoff = cutoff_ref or "2026-12-31"
        records = _build_density_records(snapshot)
    elif snapshot in {
        "s7-snapshot-current-001",
        "s7-snapshot-comparable-001",
        "s7-snapshot-not-comparable-001",
        "s7-snapshot-date-edge-001",
        "s7-snapshot-aemh-001",
    }:
        cutoff = cutoff_ref or SYNTHETIC_CUTOFF_REF
        records = _build_base_records(snapshot, cutoff)
    else:
        raise R5ProductAdapterError("SNAPSHOT_NOT_IN_SYNTHETIC_PACKET")
    flow_stages: tuple[R5FlowStageRecord, ...] = ()
    flow_paths: tuple[R5SubjectFlowPathRecord, ...] = ()
    if snapshot != "s7-snapshot-density-001":
        # The density fixture stays a legacy-shape packet on purpose so the
        # not_provided projection state stays reachable offline.
        flow_stages, flow_paths = _build_flow_records()
    if cutoff != cutoff_ref and cutoff_ref is not None:
        raise R5ProductAdapterError("CUTOFF_IDENTITY_MISMATCH")
    sources, sites, subjects, events, visits, risks, histories = records
    if snapshot == "s7-snapshot-aemh-001":
        subjects = tuple(item for item in subjects if item.subject_ref == "s7-subject-06021")
        events = tuple(item for item in events if item.subject_ref == "s7-subject-06021")
        visits = tuple(item for item in visits if item.subject_ref == "s7-subject-06021")
        risks = tuple(item for item in risks if item.subject_ref == "s7-subject-06021")
        sites = tuple(item for item in sites if item.site_ref == "s7-site-006")
    change_kind = "not_comparable" if snapshot == "s7-snapshot-not-comparable-001" else "continued"
    change_cause = "coverage" if change_kind == "not_comparable" else None
    if change_kind != "continued":
        risks = tuple(
            R5RiskRecord(
                risk_ref=item.risk_ref,
                risk_instance_ref=item.risk_instance_ref,
                risk_key=item.risk_key,
                site_ref=item.site_ref,
                subject_ref=item.subject_ref,
                spine_ref=item.spine_ref,
                domain=item.domain,
                severity=item.severity,
                risk_type_zh=item.risk_type_zh,
                date_state=item.date_state,
                event_ref=item.event_ref,
                visit_ref=item.visit_ref,
                risk_anchor_ref=item.risk_anchor_ref,
                source_locator_refs=item.source_locator_refs,
                change_kind=change_kind,
                change_cause=change_cause,
                prior_snapshot_ref="s7-snapshot-prior-001",
            )
            for item in risks
        )
    revision_pairs = tuple(
        R5SourceRevisionPair(
            revision_id=item.source_revision_ref,
            content_hash=item.source_revision_content_hash,
            locator_refs=(item.locator_ref,),
        )
        for item in sources
    )
    return R5AuthorityPacket(
        project_ref=project_ref,
        run_ref=run_ref or SYNTHETIC_RUN_REF,
        snapshot_ref=snapshot,
        cutoff_state="present",
        cutoff_ref=cutoff,
        project_label="S7 医学监查合成项目",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version=(
            R5_FLOW_AUTHORITY_CONTRACT_VERSION if flow_stages else "2026-08-26.1"
        ),
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id=f"s7-visibility:{snapshot}",
        visibility_decision_hash=canonical_sha256({"snapshot_ref": snapshot, "projectable": True, "source_count": len(sources)}),
        evaluation_content_identities=(canonical_sha256({"snapshot_ref": snapshot, "kind": "evaluation"}),),
        source_revision_content_pairs=revision_pairs,
        sources=sources,
        sites=sites,
        subjects=subjects,
        events=events,
        visits=visits,
        risks=risks,
        histories=histories if snapshot == "s7-snapshot-aemh-001" else (),
        flow_stages=flow_stages,
        subject_flow_paths=flow_paths,
        synthetic=True,
        data_mode=SYNTHETIC_FIXTURE_MODE,
    )


def build_synthetic_r5_authority_provider() -> SyntheticR5AuthorityProvider:
    return SyntheticR5AuthorityProvider()


def _public_source(source: R5SourceRecord, *, include_excerpt: bool = False) -> dict[str, Any]:
    result = {
        "locator_ref": source.locator_ref,
        "snapshot_ref": source.snapshot_ref,
        "source_file_ref": source.source_file_ref,
        "source_revision_ref": source.source_revision_ref,
        "source_revision_content_hash": source.source_revision_content_hash,
        "record_ref": source.record_ref,
        "canonical_location": source.canonical_location,
        "lineage": list(source.lineage),
    }
    if include_excerpt:
        result["excerpt"] = source.excerpt
    return result


def _with_content_hash(payload: Mapping[str, Any], field_name: str = "content_hash") -> dict[str, Any]:
    result = dict(payload)
    result[field_name] = ""
    result[field_name] = canonical_sha256(result)
    return result


def _change_band_records(risks: Sequence[R5RiskRecord]) -> tuple[R5RiskRecord, ...]:
    """Return only closed change-band rows represented by the authority packet."""

    return tuple(item for item in risks if item.change_kind != "continued" or item.change_cause is not None)


def _risk_payload(
    risk: R5RiskRecord,
    receipt_ref: str,
    *,
    subject_label: Optional[str] = None,
) -> dict[str, Any]:
    subject_name = subject_label or risk.subject_ref
    evidence_summary = {
        "why_reminded": f"{risk.risk_type_zh}可能影响受试者安全性评价或方案符合性判断，需要沿原始记录核实。",
        "basis": f"依据当前项目监查规则及已绑定的{risk.domain}域记录。",
        "finding": f"发现{subject_name}存在“{risk.risk_type_zh}”相关记录。",
        "action_item": "请核对原始记录、研究方案与数据录入情况，并确认是否需要发出数据核查问题。",
        "supporting_evidence": "已定位到支持该风险提示的原始记录。",
        "counter_evidence": "当前证据包未提供可直接排除该风险的记录。",
        "risk_history": {
            "new": "本次新增",
            "upgraded": "本次升高",
            "continued": "持续存在",
            "downgraded": "风险降低",
            "resolved": "本次解除",
            "reopened": "后续重新出现",
            "not_comparable": "本次暂不可比较",
        }.get(risk.change_kind, "本次状态待核对"),
        "query_draft": (
            f"依据当前项目监查规则；发现{subject_name}存在“{risk.risk_type_zh}”相关记录；"
            "请核实原始记录与医学判断是否一致，并按需补充说明或更正。"
        ),
    }
    if risk.risk_key == "s7-risk-key-pd-10008":
        evidence_summary.update({
            "why_reminded": "访视窗口与方案要求可能不一致，需确认是否构成方案偏离（PD）。",
            "basis": "依据研究方案规定的访视窗口及已绑定的访视记录。",
            "finding": f"发现{subject_name}的相关访视记录超出方案规定窗口。",
            "action_item": "请核实是否构成方案偏离（PD），并在数据系统中补充说明或更正。",
            "supporting_evidence": "访视日期和方案窗口均已定位，可直接复核。",
            "counter_evidence": "当前未见已获批准的窗口豁免或其他排除依据。",
            "query_draft": (
                f"依据研究方案规定的访视窗口；发现{subject_name}的相关访视记录超出方案规定窗口；"
                "请核实是否构成方案偏离（PD），并补充说明或更正。"
            ),
        })
    elif risk.risk_key == "s7-risk-key-ae-mh-06021":
        evidence_summary.update({
            "why_reminded": "既往疑似漏报记录在后续数据中出现匹配记录，需要保留前后匹配历史。",
            "basis": "依据 AE、MH 记录的时间、术语及受试者身份匹配结果。",
            "finding": f"发现{subject_name}原疑似 AE/MH 漏报在后续数据中已有补录记录。",
            "action_item": "请核实补录记录与原疑似漏报是否为同一医学事件，并确认当前 AE/MH 判定。",
            "supporting_evidence": "原疑似漏报与后续补录记录的受试者、时间及医学术语可匹配。",
            "counter_evidence": "若两条记录对应不同临床事件，则不应合并判定。",
            "query_draft": (
                f"依据 AE/MH 前后记录的时间及医学术语；发现{subject_name}原疑似漏报在后续数据中已有补录记录；"
                "请核实两者是否为同一医学事件，并确认 AE/MH 记录是否完整。"
            ),
        })
    result = {
        "risk_ref": risk.risk_ref,
        "risk_instance_ref": risk.risk_instance_ref,
        "risk_key": risk.risk_key,
        "risk_anchor_ref": risk.risk_anchor_ref,
        "site_ref": risk.site_ref,
        "subject_ref": risk.subject_ref,
        "spine_ref": risk.spine_ref,
        "domain": risk.domain,
        "severity": risk.severity,
        "severity_zh": {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}[risk.severity],
        "risk_type_zh": risk.risk_type_zh,
        "subject_label": subject_label,
        "date_state": risk.date_state,
        "event_ref": risk.event_ref,
        "visit_ref": risk.visit_ref,
        "source_locator_ref": risk.source_locator_refs[0] if len(risk.source_locator_refs) == 1 else None,
        "source_locator_refs": list(risk.source_locator_refs),
        "change_kind": risk.change_kind,
        "change_cause": risk.change_cause,
        "authority_receipt_ref": receipt_ref,
        "evidence_summary": evidence_summary,
    }
    if risk.risk_key == "s7-risk-key-ae-06021":
        result["analysis_disagreement"] = {
            "status_zh": "分析意见有分歧，暂不作为最终分析结论",
            "analysis_one": "现有 AE 记录与访视时间一致，支持继续保留风险提示。",
            "analysis_two": "现有记录可能已充分解释该事件，暂不支持提高风险等级。",
            "independent_check": "独立核对保留当前中风险入口，并要求同时展示支持与不支持证据。",
            "disagreement": "分歧集中在现有记录是否足以排除记录一致性风险。",
            "supporting_evidence": "AE 起止日期与访视记录已绑定。",
            "counter_evidence": "现有数据可能已有临床解释，但尚未形成可直接排除风险的完整证据链。",
        }
    return result


def _count_indicator(
    indicator_ref: str,
    label: str,
    records: Sequence[Any],
    *,
    date_getter: Callable[[Any], Optional[date]],
    date_state_getter: Callable[[Any], str],
    ref_getter: Callable[[Any], str],
    source_refs_getter: Callable[[Any], Sequence[str]],
    receipt_ref: str,
) -> dict[str, Any]:
    buckets: dict[Optional[date], dict[str, Any]] = {}
    for record in records:
        point_date = date_getter(record)
        bucket = buckets.setdefault(
            point_date,
            {"count": 0, "date_state": date_state_getter(record), "record_refs": [], "source_locator_refs": set()},
        )
        bucket["count"] += 1
        bucket["date_state"] = bucket["date_state"] if bucket["date_state"] == date_state_getter(record) else "conflicted"
        bucket["record_refs"].append(ref_getter(record))
        bucket["source_locator_refs"].update(source_refs_getter(record))
    points = []
    for index, point_date in enumerate(sorted(buckets, key=lambda value: (value is None, value or date.min)), start=1):
        bucket = buckets[point_date]
        points.append({
            "point_ref": f"{indicator_ref}:point:{index:03d}",
            "date": _iso(point_date),
            "date_state": bucket["date_state"],
            "value": bucket["count"],
            "record_refs": sorted(bucket["record_refs"]),
            "source_locator_refs": sorted(bucket["source_locator_refs"]),
            "authority_receipt_ref": receipt_ref,
        })
    return _with_content_hash({
        "indicator_ref": indicator_ref,
        "label": label,
        "unit": "记录数",
        "value_kind": "authority_record_count",
        "points": points,
        "authority_receipt_ref": receipt_ref,
    })


def _indicator_payloads(
    packet: R5AuthorityPacket,
    *,
    events: Sequence[R5EventRecord],
    risks: Sequence[R5RiskRecord],
) -> list[dict[str, Any]]:
    """Build deterministic record-count trends from the same typed packet.

    These are record-density indicators, not inferred clinical measurements.
    They are derived only from records already present in the typed packet;
    synthetic packets remain route-visible only through explicit fixture mode.
    """

    receipt_ref = packet.receipt_id
    event_by_ref = {item.event_ref: item for item in events}
    indicators = []
    if events:
        indicators.append(_count_indicator(
            "r5-indicator-event-record-count",
            "事件记录数",
            events,
            date_getter=lambda item: item.start_date,
            date_state_getter=lambda item: item.date_state,
            ref_getter=lambda item: item.event_ref,
            source_refs_getter=lambda item: item.source_locator_refs,
            receipt_ref=receipt_ref,
        ))
    if risks:
        indicators.append(_count_indicator(
            "r5-indicator-risk-anchor-count",
            "风险锚点记录数",
            risks,
            date_getter=lambda item: event_by_ref.get(item.event_ref).start_date if item.event_ref and event_by_ref.get(item.event_ref) else None,
            date_state_getter=lambda item: event_by_ref.get(item.event_ref).date_state if item.event_ref and event_by_ref.get(item.event_ref) else item.date_state,
            ref_getter=lambda item: item.risk_instance_ref,
            source_refs_getter=lambda item: item.source_locator_refs,
            receipt_ref=receipt_ref,
        ))
    return indicators


def _subject_rows(
    packet: R5AuthorityPacket,
    *,
    subjects: Optional[Sequence[R5SubjectRecord]] = None,
) -> list[dict[str, Any]]:
    rows = packet.subjects if subjects is None else subjects
    return [
        {
            "subject_ref": item.subject_ref,
            "subject_id": item.subject_ref,
            "label": item.subject_label,
            "subject_label": item.subject_label,
            "site_ref": item.site_ref,
            "spine_ref": item.spine_ref,
            "authority_receipt_ref": packet.receipt_id,
        }
        for item in rows
    ]


def _flow_edge_is_legal(from_stage: R5FlowStageRecord, to_stage: R5FlowStageRecord) -> bool:
    """Closed edge legality set from the frozen v0.3 §4 contract."""

    if from_stage.stage_kind == "main":
        if to_stage.stage_kind == "main":
            return to_stage.column_order == from_stage.column_order + 1
        if to_stage.stage_kind == "branch_terminal":
            return to_stage.column_order in (from_stage.column_order, from_stage.column_order + 1)
        return False
    if from_stage.stage_kind == "missing":
        # The reserved missing entry may only connect to the first known main.
        return to_stage.stage_kind == "main"
    # branch_terminal / unknown / not_applicable stages have no outbound step.
    return False


def _flow_coverage_bucket(path: R5SubjectFlowPathRecord, current_stage: R5FlowStageRecord) -> str:
    if len(path.steps) == 1 and current_stage.stage_kind in {"missing", "not_applicable", "unknown"}:
        return {
            "missing": "not_provided",
            "not_applicable": "not_applicable",
            "unknown": "conflicted",
        }[current_stage.stage_kind]
    return path.path_state


def _subject_flow_projection(
    packet: R5AuthorityPacket,
    *,
    selected_site_refs: set[str],
    site_ref: Optional[str],
) -> dict[str, Any]:
    """Build the conserved ``projection.subject_flow`` overview subtree.

    Nodes, links, detail rows and risk counts are all aggregated from the same
    scoped path records, so the four-way reconciliation holds by construction
    and is re-checked defensively before ``matched`` is emitted.
    """

    scope = {
        "project_ref": packet.project_ref,
        "run_ref": packet.run_ref,
        "snapshot_ref": packet.snapshot_ref,
        "cutoff_state": packet.cutoff_state,
        "cutoff_ref": packet.cutoff_ref,
        "site_ref": site_ref,
    }
    if not packet.flow_stages and not packet.subject_flow_paths:
        # Legacy v0.3.1 packet: flow fields absent or both empty.
        return {
            "availability": "not_provided",
            "reason_zh": FLOW_NOT_PROVIDED_REASON_ZH,
            "scope": scope,
            "reconciliation": {"state": "not_applicable"},
        }

    def _blocked(*gaps: str) -> dict[str, Any]:
        ordered: list[str] = []
        for gap in gaps:
            if gap and gap not in ordered:
                ordered.append(gap)
        return {
            "availability": "available",
            "visual_kind": "path_throughput_sankey",
            "scope": scope,
            "reconciliation": {
                "state": "blocked",
                "total_subjects": len(scope_subjects),
                "gap_zh": "；".join(ordered),
                "gaps_zh": ordered,
            },
        }

    scope_subjects = tuple(item for item in packet.subjects if item.site_ref in selected_site_refs)
    scope_subject_refs = {item.subject_ref for item in scope_subjects}
    subject_by_ref = {item.subject_ref: item for item in packet.subjects}
    scope_paths = tuple(item for item in packet.subject_flow_paths if item.subject_ref in scope_subject_refs)
    stage_by_ref = {item.stage_ref: item for item in packet.flow_stages}

    if not packet.flow_stages:
        return _blocked("路径数据缺少阶段目录")
    if len({item.column_order for item in packet.flow_stages}) > FLOW_MAX_COLUMNS:
        return _blocked("受试者阶段列数超过当前看板容量")

    # Packet-level structural checks: a defective authority packet blocks the
    # page in every scope instead of silently rendering partial data.
    path_subject_counts: dict[str, int] = {}
    orphan = site_mismatch = unknown_stage = False
    for path in packet.subject_flow_paths:
        path_subject_counts[path.subject_ref] = path_subject_counts.get(path.subject_ref, 0) + 1
        subject = subject_by_ref.get(path.subject_ref)
        if subject is None:
            orphan = True
            continue
        if path.site_ref != subject.site_ref:
            site_mismatch = True
        if any(step.stage_ref not in stage_by_ref for step in path.steps):
            unknown_stage = True
    duplicate = any(count > 1 for count in path_subject_counts.values())
    missing_members = scope_subject_refs - set(path_subject_counts)
    if orphan or duplicate or site_mismatch or unknown_stage or missing_members:
        return _blocked(
            "规范路径引用了范围外的受试者" if orphan else "",
            "同一受试者存在多条规范路径" if duplicate else "",
            "路径与受试者中心归属不一致" if site_mismatch else "",
            "规范路径引用了未定义的阶段" if unknown_stage else "",
            "受试者缺少规范路径记录" if missing_members else "",
        )

    repeated = any(
        len({step.stage_ref for step in path.steps}) != len(path.steps)
        for path in packet.subject_flow_paths
    )
    entry_invalid = any(
        not stage_by_ref[path.steps[0].stage_ref].is_entry
        or any(stage_by_ref[step.stage_ref].is_entry for step in path.steps[1:])
        for path in packet.subject_flow_paths
    )
    continuity_invalid = any(
        not _flow_edge_is_legal(stage_by_ref[from_step.stage_ref], stage_by_ref[to_step.stage_ref])
        for path in packet.subject_flow_paths
        for from_step, to_step in zip(path.steps, path.steps[1:])
    )
    if repeated or entry_invalid or continuity_invalid:
        return _blocked(
            "规范路径中阶段重复" if repeated else "",
            "规范路径入口不合法" if entry_invalid else "",
            "规范路径阶段连续性校验未通过" if continuity_invalid else "",
        )

    reached: dict[str, set[str]] = {stage.stage_ref: set() for stage in packet.flow_stages}
    current: dict[str, set[str]] = {stage.stage_ref: set() for stage in packet.flow_stages}
    link_members: dict[tuple[str, str], set[str]] = {}
    for path in scope_paths:
        subject_ref = path.subject_ref
        refs = [step.stage_ref for step in path.steps]
        for ref in refs:
            reached[ref].add(subject_ref)
        current[refs[-1]].add(subject_ref)
        for from_ref, to_ref in zip(refs, refs[1:]):
            link_members.setdefault((from_ref, to_ref), set()).add(subject_ref)

    scoped_risks = tuple(item for item in packet.risks if item.site_ref in selected_site_refs)
    mid_high_risks = tuple(item for item in scoped_risks if item.severity in MID_HIGH_SEVERITIES)
    mid_high_subject_refs = {item.subject_ref for item in mid_high_risks}

    outbound_total = {stage.stage_ref: 0 for stage in packet.flow_stages}
    inbound_total = {stage.stage_ref: 0 for stage in packet.flow_stages}
    for (from_ref, to_ref), members in link_members.items():
        outbound_total[from_ref] += len(members)
        inbound_total[to_ref] += len(members)

    node_ok = True
    for stage in packet.flow_stages:
        ref = stage.stage_ref
        if len(reached[ref]) != len(current[ref]) + outbound_total[ref]:
            node_ok = False
        if stage.is_entry and inbound_total[ref] != 0:
            node_ok = False
        if not stage.is_entry and inbound_total[ref] != len(reached[ref]):
            node_ok = False
    link_ok = sum(len(members) for members in link_members.values()) == sum(
        len(path.steps) - 1 for path in scope_paths
    )
    if not (node_ok and link_ok):
        return _blocked("节点或连线人数守恒校验未通过")

    stage_order = {stage.stage_ref: (stage.column_order, stage.row_order) for stage in packet.flow_stages}
    stages_payload = [
        {
            "stage_ref": stage.stage_ref,
            "stage_label_zh": stage.stage_label_zh,
            "column_order": stage.column_order,
            "row_order": stage.row_order,
            "stage_kind": stage.stage_kind,
            "is_entry": stage.is_entry,
            "is_terminal": stage.is_terminal,
            "reached_count": len(reached[stage.stage_ref]),
            "current_count": len(current[stage.stage_ref]),
            "current_mid_high_risk_count": len(current[stage.stage_ref] & mid_high_subject_refs),
        }
        for stage in sorted(packet.flow_stages, key=lambda item: (item.column_order, item.row_order))
    ]
    links_payload = [
        {
            "link_ref": f"r5-flow-link:{from_ref}:{to_ref}",
            "from_stage_ref": from_ref,
            "to_stage_ref": to_ref,
            "count": len(members),
            "current_mid_high_risk_count": len(members & mid_high_subject_refs),
        }
        for (from_ref, to_ref), members in sorted(
            link_members.items(),
            key=lambda item: (stage_order[item[0][0]], stage_order[item[0][1]]),
        )
    ]

    cutoff_date = _date(packet.cutoff_ref, "cutoff_ref") if packet.cutoff_ref is not None else None
    visits_by_subject: dict[str, list[R5VisitRecord]] = {}
    for visit in packet.visits:
        if visit.subject_ref in scope_subject_refs:
            visits_by_subject.setdefault(visit.subject_ref, []).append(visit)
    events_by_subject: dict[str, list[R5EventRecord]] = {}
    for event in packet.events:
        if event.subject_ref in scope_subject_refs:
            events_by_subject.setdefault(event.subject_ref, []).append(event)

    def _usable_jump_dates(subject_ref: str) -> list[date]:
        # Journey windows come only from same-packet visits/events clipped to
        # the current cutoff; path entered/basis dates never substitute.
        values: list[date] = []
        for visit in visits_by_subject.get(subject_ref, ()):
            values.extend(value for value in (visit.actual_date, visit.nominal_date) if value is not None)
        for event in events_by_subject.get(subject_ref, ()):
            values.extend(value for value in (event.start_date, event.end_date) if value is not None)
        if cutoff_date is not None:
            values = [value for value in values if value <= cutoff_date]
        return sorted(set(values))

    rows: list[dict[str, Any]] = []
    bucket_counts = {f"{bucket}_count": 0 for bucket in FLOW_COVERAGE_BUCKETS}
    for path in scope_paths:
        subject = subject_by_ref[path.subject_ref]
        refs = [step.stage_ref for step in path.steps]
        last_step = path.steps[-1]
        prior_step = path.steps[-2] if len(path.steps) > 1 else None
        current_stage = stage_by_ref[refs[-1]]
        prior_stage = stage_by_ref[prior_step.stage_ref] if prior_step is not None else None
        bucket = _flow_coverage_bucket(path, current_stage)
        bucket_counts[f"{bucket}_count"] += 1

        subject_risks = sorted(
            (item for item in mid_high_risks if item.subject_ref == subject.subject_ref),
            key=lambda item: (SEVERITIES.index(item.severity), item.risk_ref),
        )
        spine_unique = sum(1 for item in packet.subjects if item.subject_ref == subject.subject_ref) == 1
        usable_dates = _usable_jump_dates(subject.subject_ref)
        jump_enabled = bool(usable_dates) and spine_unique and bool(subject.spine_ref)
        top_risk = subject_risks[0] if subject_risks else None
        rows.append({
            "subject_ref": subject.subject_ref,
            "site_ref": subject.site_ref,
            "subject_label": subject.subject_label,
            "spine_ref": subject.spine_ref,
            "path_state": path.path_state,
            "coverage_bucket": bucket,
            "path_stage_refs": refs,
            "path_link_refs": [f"r5-flow-link:{from_ref}:{to_ref}" for from_ref, to_ref in zip(refs, refs[1:])],
            "current_stage_ref": current_stage.stage_ref,
            "current_stage_label_zh": current_stage.stage_label_zh,
            "prior_stage_ref": prior_stage.stage_ref if prior_stage is not None else None,
            "prior_stage_label_zh": prior_stage.stage_label_zh if prior_stage is not None else None,
            "entered_date": _iso(last_step.entered_date),
            "basis_date": _iso(last_step.basis_date),
            "date_state": last_step.date_state,
            "transition_reason_zh": last_step.transition_reason_zh,
            "stage_change_kind": path.stage_change_kind,
            "prior_run_current_stage_ref": path.prior_run_current_stage_ref,
            "date_pending": any(step.date_state != "exact" for step in path.steps),
            "current_mid_high_risk": bool(subject_risks),
            "current_mid_high_risk_count": len(subject_risks),
            "mid_high_risk_top_severity": top_risk.severity if top_risk else None,
            "mid_high_risk_top_severity_zh": FLOW_SEVERITY_ZH[top_risk.severity] if top_risk else None,
            "risk_summary_zh": (
                f"{FLOW_SEVERITY_ZH[top_risk.severity]} · {top_risk.risk_type_zh}" if top_risk else None
            ),
            "risk_change_kind": top_risk.change_kind if top_risk else None,
            "journey_jump_enabled": jump_enabled,
            "journey_jump_state_zh": "可跳转" if jump_enabled else "时间窗待确认",
            "jump_window_start": usable_dates[0].isoformat() if usable_dates else None,
            "jump_window_end": usable_dates[-1].isoformat() if usable_dates else None,
        })
    rows.sort(key=lambda row: (
        0 if row["current_mid_high_risk"] else 1,
        0 if row["date_pending"] else 1,
        stage_order[row["current_stage_ref"]],
        row["subject_ref"],
    ))

    return {
        "availability": "available",
        "visual_kind": "path_throughput_sankey",
        "scope": scope,
        "stages": stages_payload,
        "links": links_payload,
        "subjects": rows,
        "coverage": {
            "total_subjects": len(scope_subjects),
            **bucket_counts,
        },
        "reconciliation": {
            "state": "matched",
            "total_subject_count": len(scope_subjects),
            "entry_count": len(scope_paths),
            "current_stay_count": sum(len(current[stage.stage_ref]) for stage in packet.flow_stages),
            "detail_count": len(rows),
            "node_conservation_matched": node_ok,
            "link_conservation_matched": link_ok,
            "membership_ok": True,
            "continuity_ok": True,
            "gaps_zh": [],
        },
    }


def _event_payload(event: R5EventRecord) -> dict[str, Any]:
    return {
        "event_ref": event.event_ref,
        "subject_ref": event.subject_ref,
        "site_ref": event.site_ref,
        "spine_ref": event.spine_ref,
        "domain": event.domain,
        "subtype": event.subtype,
        "date_state": event.date_state,
        "start_date": _iso(event.start_date),
        "end_date": _iso(event.end_date),
        "visit_ref": event.visit_ref,
        "risk_anchor_refs": list(event.risk_anchor_refs),
        "source_locator_refs": list(event.source_locator_refs),
        "label_zh": event.label_zh,
        "encoding": dict(DOMAIN_ENCODING[event.domain]),
        "risk_overlay_shape": "double_chevron_badge",
    }


def _strip_response_digest(value: Any, *, parent_key: str = "") -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_response_digest(item, parent_key=str(key))
            for key, item in value.items()
            if key != "response_snapshot_sha256"
            and not (parent_key == "read_handoff" and key == "contract_sha256")
        }
    if isinstance(value, (list, tuple)):
        return [_strip_response_digest(item, parent_key=parent_key) for item in value]
    return value


def response_snapshot_sha256(envelope_without_response_digest: Mapping[str, Any]) -> str:
    """Hash canonical response bytes while excluding the self-referential digest."""

    return canonical_sha256(_strip_response_digest(envelope_without_response_digest))


class R5ProductAdapter:
    """Project typed authority into the three closed R5 read surfaces."""

    def __init__(self, authority_provider: Optional[Any], *, synthetic_fixture_mode: bool = False) -> None:
        if synthetic_fixture_mode:
            if authority_provider is not None and not getattr(authority_provider, "fixture_mode", False):
                raise R5ProductAdapterError("SYNTHETIC_PROVIDER_MISMATCH")
            authority_provider = authority_provider or build_synthetic_r5_authority_provider()
        self.authority_provider = authority_provider
        self.synthetic_fixture_mode = synthetic_fixture_mode

    def _packet(
        self,
        project_ref: str,
        run_ref: Optional[str],
        snapshot_ref: Optional[str],
        cutoff_ref: Optional[str],
    ) -> R5AuthorityPacket:
        if self.authority_provider is None:
            raise R5ProductAdapterError("AUTHORITY_PACKET_UNAVAILABLE")
        provider = self.authority_provider
        try:
            if hasattr(provider, "get_packet"):
                packet = provider.get_packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
            elif callable(provider):
                packet = provider(project_ref, run_ref, snapshot_ref, cutoff_ref)
            else:
                raise R5ProductAdapterError("AUTHORITY_PROVIDER_INVALID")
        except R5ProductAdapterError:
            raise
        except Exception as exc:
            raise R5ProductAdapterError("AUTHORITY_PACKET_UNAVAILABLE") from exc
        if type(packet) is not R5AuthorityPacket:
            raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED")
        if self.synthetic_fixture_mode and not packet.synthetic:
            raise R5ProductAdapterError("SYNTHETIC_AUTHORITY_REQUIRED")
        if packet.project_ref != project_ref:
            raise R5ProductAdapterError("PROJECT_IDENTITY_MISMATCH")
        for name, expected in (("run_ref", run_ref), ("snapshot_ref", snapshot_ref), ("cutoff_ref", cutoff_ref)):
            if expected is not None and getattr(packet, name) != expected:
                raise R5ProductAdapterError("AUTHORITY_IDENTITY_MISMATCH", name)
        return packet

    def get_authority_packet(
        self,
        *,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        """Expose the validated packet for one route-level identity handoff."""

        return self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)

    def overview(
        self,
        *,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
        site_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        if site_ref is not None:
            site_ref = _required(site_ref, "site_ref")
        selected_sites = tuple(item for item in packet.sites if site_ref is None or item.site_ref == site_ref)
        if site_ref is not None and not selected_sites:
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        selected_site_refs = {item.site_ref for item in selected_sites}
        selected_subjects = tuple(item for item in packet.subjects if item.site_ref in selected_site_refs)
        selected_events = tuple(item for item in packet.events if item.site_ref in selected_site_refs)
        selected_visits = tuple(item for item in packet.visits if item.site_ref in selected_site_refs)
        selected_risks = tuple(item for item in packet.risks if item.site_ref in selected_site_refs)
        receipt_ref = packet.receipt_id
        subject_labels = {item.subject_ref: item.subject_label for item in packet.subjects}
        high = tuple(item for item in selected_risks if item.severity in {"critical", "high"})
        medium = tuple(item for item in selected_risks if item.severity == "medium")
        low = tuple(item for item in selected_risks if item.severity == "low")
        current_risks = [
            _risk_payload(item, receipt_ref, subject_label=subject_labels.get(item.subject_ref))
            for item in selected_risks
        ]
        current_risk_set = _with_content_hash({
            "high_risk_refs": [item.risk_ref for item in high],
            "medium_risk_refs": [item.risk_ref for item in medium],
            "low_risk_cluster_refs": [item.risk_ref for item in low],
            "resolved_history_refs": [],
            "authority_receipt_ref": receipt_ref,
        })
        center_cells = []
        for site in selected_sites:
            for domain in DOMAINS:
                site_risks = tuple(item for item in selected_risks if item.site_ref == site.site_ref and item.domain == domain)
                if not site_risks and domain != site.domain:
                    continue
                center_cells.append({
                    "site_ref": site.site_ref,
                    "domain": domain,
                    "severity": max((item.severity for item in site_risks), default=site.severity, key=SEVERITIES.index),
                    "pattern_refs": list(site.pattern_refs),
                    "individual_risk_refs": [item.risk_ref for item in site_risks],
                    "measure_refs": list(site.measure_refs),
                })
        # Canonical center_map shape is an object, never a bare cell array:
        # {stable_site_order, cells, projection_instance, content_hash}; every
        # cell carries site/domain/severity/pattern/risk/measure references.
        center_map = _with_content_hash({
            "stable_site_order": [site.site_ref for site in selected_sites],
            "cells": center_cells,
            "projection_instance": {
                "opaque_run_ref": packet.run_ref,
                "opaque_snapshot_ref": packet.snapshot_ref,
                "replay_content_identity": canonical_sha256({"packet": packet.source_snapshot_sha256, "surface": "overview"}),
                "authority_receipt_ref": receipt_ref,
            },
        })
        change_band_records = _change_band_records(selected_risks)
        changes = [
            {
                "risk_ref": item.risk_ref,
                "change_kind": item.change_kind,
                "change_cause": item.change_cause,
                "prior_snapshot_ref": item.prior_snapshot_ref,
                "current_snapshot_ref": packet.snapshot_ref,
                "authority_receipt_ref": receipt_ref,
            }
            for item in change_band_records
        ]
        measures = [
            {
                "measure_ref": measure_ref,
                "site_ref": site.site_ref,
                "numerator": site.numerator,
                "denominator": site.denominator,
                "denominator_state": "closed_positive" if site.denominator else "closed_zero",
                "rate_state": "closed" if site.denominator else "not_evaluable",
                "coverage_state": site.coverage_state,
                "cutoff_ref": packet.cutoff_ref,
                "authority_receipt_ref": receipt_ref,
            }
            for site in selected_sites
            for measure_ref in site.measure_refs
        ]
        coverage_numerator = sum(site.numerator for site in selected_sites)
        coverage_denominator = sum(site.denominator or 0 for site in selected_sites)
        coverage_state = "complete" if all(site.coverage_state == "complete" for site in selected_sites) else "partial"
        subject_flow = _subject_flow_projection(
            packet,
            selected_site_refs=selected_site_refs,
            site_ref=site_ref,
        )
        # Surface-specific contract: evidence binds one risk to one source.
        # The eight-domain registry belongs to overview/subject projections;
        # it is intentionally absent here and must not be added generically.
        projection = _with_content_hash({
            "kind": "project_cockpit",
            "projection_instance": {
                "opaque_run_ref": packet.run_ref,
                "opaque_snapshot_ref": packet.snapshot_ref,
                "replay_content_identity": canonical_sha256({"packet": packet.source_snapshot_sha256, "surface": "overview"}),
                "authority_receipt_ref": receipt_ref,
            },
            "project": {"project_ref": packet.project_ref, "project_label": packet.project_label},
            "subjects": _subject_rows(packet, subjects=selected_subjects),
            "current_risks": current_risks,
            "current_risk_set": current_risk_set,
            "center_map": center_map,
            "change_bands": changes,
            "measures": measures,
            "coverage": {
                "numerator": coverage_numerator,
                "denominator": coverage_denominator,
                "coverage_state": coverage_state,
                "label": "当前范围覆盖",
                "authority_receipt_ref": receipt_ref,
            },
            "subject_flow": subject_flow,
            "domain_encoding": [dict({"domain": domain}, **DOMAIN_ENCODING[domain]) for domain in DOMAINS],
            "risk_overlay_shape": "double_chevron_badge",
        })
        selected_source_refs = {
            locator_ref
            for item in (*selected_events, *selected_visits, *selected_risks)
            for locator_ref in item.source_locator_refs
        }
        source_refs = [
            _public_source(item)
            for item in packet.sources
            if site_ref is None or item.locator_ref in selected_source_refs
        ]
        counts = self._counts(
            packet,
            events=selected_events,
            risks=selected_risks,
            change_band_records=change_band_records,
        )
        return_context_key = f"r5:return:overview:{packet.snapshot_ref}"
        if site_ref is not None:
            return_context_key = f"{return_context_key}:{site_ref}"
        identity_overrides = {"site_ref": site_ref} if site_ref is not None else None
        return self._result(
            packet,
            projection,
            counts,
            source_refs,
            view="overview",
            return_context_key=return_context_key,
            identity_overrides=identity_overrides,
        )

    def subject_workspace(
        self,
        *,
        project_ref: str,
        subject_ref: str,
        run_ref: str,
        snapshot_ref: str,
        cutoff_ref: str,
        site_ref: str,
        spine_ref: str,
        window_start: date,
        window_end: date,
        risk_instance_ref: Optional[str] = None,
        risk_anchor_ref: Optional[str] = None,
        visit_ref: Optional[str] = None,
        event_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        if window_start > window_end:
            raise R5ProductAdapterError("WINDOW_INVALID")
        subject = next((item for item in packet.subjects if item.subject_ref == subject_ref), None)
        if subject is None or subject.site_ref != site_ref or subject.spine_ref != spine_ref:
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        events = tuple(item for item in packet.events if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        visits = tuple(item for item in packet.visits if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        risks = tuple(item for item in packet.risks if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        if risk_instance_ref is not None:
            if not any(item.risk_instance_ref == risk_instance_ref for item in risks):
                raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if risk_anchor_ref is not None:
            if not any(item.risk_anchor_ref == risk_anchor_ref for item in risks):
                raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if visit_ref is not None and not any(item.visit_ref == visit_ref for item in visits):
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if event_ref is not None and not any(item.event_ref == event_ref for item in events):
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        receipt_ref = packet.receipt_id
        subject_labels = {item.subject_ref: item.subject_label for item in packet.subjects}
        event_payloads = [_event_payload(item) for item in events]
        risk_payloads = [
            _risk_payload(item, receipt_ref, subject_label=subject_labels.get(item.subject_ref))
            for item in risks
        ]
        visit_payloads = [
            {
                "visit_ref": item.visit_ref,
                "subject_ref": item.subject_ref,
                "site_ref": item.site_ref,
                "spine_ref": item.spine_ref,
                "visit_kind": item.visit_kind,
                "date_state": item.date_state,
                "actual_date": _iso(item.actual_date),
                "nominal_date": _iso(item.nominal_date),
                "phase_ref": item.phase_ref,
                "source_locator_refs": list(item.source_locator_refs),
            }
            for item in visits
        ]
        pending_date_payloads = [
            {
                "item_ref": item.event_ref,
                "event_ref": item.event_ref,
                "domain": item.domain,
                "date_state": item.date_state,
                "source_locator_refs": list(item.source_locator_refs),
                "authority_receipt_ref": receipt_ref,
            }
            for item in events
            if item.date_state != "exact"
        ]
        domain_tracks = [
            {
                "domain": domain,
                "event_refs": [item.event_ref for item in events if item.domain == domain],
                "risk_anchor_refs": [item.risk_anchor_ref for item in risks if item.domain == domain],
                "encoding": dict(DOMAIN_ENCODING[domain]),
            }
            for domain in DOMAINS
        ]
        pending_date_refs = [item.event_ref for item in events if item.date_state != "exact"]
        spine = _with_content_hash({
            "spine_ref": subject.spine_ref,
            "subject_ref": subject.subject_ref,
            "cutoff_ref": packet.cutoff_ref,
            "axis_mode": "calendar",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "event_refs": [item.event_ref for item in events],
            "visit_refs": [item.visit_ref for item in visits],
            "pending_date_refs": pending_date_refs,
            "phase_band_refs": [],
            "events": event_payloads,
            "visits": visit_payloads,
            "risk_anchors": risk_payloads,
            "pending_dates": pending_date_payloads,
        })
        workspace = _with_content_hash({
            "subject_ref": subject.subject_ref,
            "spine_ref": subject.spine_ref,
            "active_view": "journey",
            "axis_mode": "calendar",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "selected_event_ref": event_ref,
            "selected_risk_ref": risk_instance_ref,
            "selected_visit_ref": visit_ref,
        })
        history = [
            {
                "candidate_ref": item.candidate_ref,
                "later_fact_ref": item.later_fact_ref,
                "event_kind": item.event_kind,
                "match_state": item.match_state,
                "from_snapshot_ref": item.from_snapshot_ref,
                "to_snapshot_ref": item.to_snapshot_ref,
                "identity_evidence_refs": list(item.identity_evidence_refs),
            }
            for item in packet.histories
            if item.subject_ref == subject_ref
        ]
        projection = _with_content_hash({
            "kind": "subject_workspace",
            "subject": {
                "subject_ref": subject.subject_ref,
                "site_ref": subject.site_ref,
                "spine_ref": subject.spine_ref,
                "subject_label": subject.subject_label,
            },
            "temporal_spine": spine,
            "workspace_state": workspace,
            "events": event_payloads,
            "visits": visit_payloads,
            "current_risks": risk_payloads,
            "risk_anchors": risk_payloads,
            "domain_tracks": domain_tracks,
            "indicators": _indicator_payloads(packet, events=events, risks=risks),
            "aemh_match_history": history,
            "pending_dates": pending_date_payloads,
            "date_pending_refs": pending_date_refs,
            "risk_overlay_shape": "double_chevron_badge",
        })
        source_locator_refs = set()
        for item in events:
            source_locator_refs.update(item.source_locator_refs)
        for item in risks:
            source_locator_refs.update(item.source_locator_refs)
        for item in visits:
            source_locator_refs.update(item.source_locator_refs)
        source_refs = [_public_source(item) for item in packet.sources if item.locator_ref in source_locator_refs]
        if len(source_refs) != len(source_locator_refs):
            raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND")
        counts = self._counts(
            packet,
            events=events,
            risks=risks,
            indicators=projection["indicators"],
        )
        target_risk = next((item for item in risks if item.risk_instance_ref == risk_instance_ref or item.risk_anchor_ref == risk_anchor_ref), None)
        identity = {
            "site_ref": site_ref,
            "subject_ref": subject_ref,
            "spine_ref": spine_ref,
            "risk_ref": target_risk.risk_ref if target_risk else None,
            "risk_instance_ref": target_risk.risk_instance_ref if target_risk else risk_instance_ref,
            "risk_anchor_ref": target_risk.risk_anchor_ref if target_risk else risk_anchor_ref,
            "visit_ref": visit_ref,
            "event_ref": event_ref,
            "source_locator_ref": None,
        }
        return self._result(packet, projection, counts, source_refs, view="journey", return_context_key=f"r5:return:subject:{subject_ref}:{spine_ref}", identity_overrides=identity, window_start=window_start, window_end=window_end)

    def source_evidence(
        self,
        *,
        project_ref: str,
        run_ref: str,
        snapshot_ref: str,
        cutoff_ref: str,
        risk_instance_ref: str,
        source_locator_ref: str,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        risk = next((item for item in packet.risks if item.risk_instance_ref == risk_instance_ref), None)
        if risk is None or source_locator_ref not in risk.source_locator_refs:
            raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND")
        source = next((item for item in packet.sources if item.locator_ref == source_locator_ref and item.snapshot_ref == snapshot_ref), None)
        if source is None:
            raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND")
        projection = _with_content_hash({
            "kind": "source_evidence",
            "risk_ref": risk.risk_ref,
            "risk_instance_ref": risk.risk_instance_ref,
            "source_locator_ref": source.locator_ref,
            "evidence": {
                "excerpt": source.excerpt,
                "record_ref": source.record_ref,
                "canonical_location": source.canonical_location,
                "lineage": list(source.lineage),
                "source_revision_ref": source.source_revision_ref,
                "source_revision_content_hash": source.source_revision_content_hash,
            },
            "authority_receipt_ref": packet.receipt_id,
        })
        counts = self._counts(packet, events=(), risks=(risk,))
        return self._result(
            packet,
            projection,
            counts,
            [_public_source(source, include_excerpt=True)],
            view="evidence",
            return_context_key=f"r5:return:evidence:{risk.risk_instance_ref}:{source.locator_ref}",
            identity_overrides={
                "site_ref": risk.site_ref,
                "subject_ref": risk.subject_ref,
                "spine_ref": risk.spine_ref,
                "risk_ref": risk.risk_ref,
                "risk_instance_ref": risk.risk_instance_ref,
                "risk_anchor_ref": risk.risk_anchor_ref,
                "source_locator_ref": source.locator_ref,
            },
        )

    def _counts(
        self,
        packet: R5AuthorityPacket,
        *,
        events: Sequence[R5EventRecord],
        risks: Sequence[R5RiskRecord],
        indicators: Sequence[Mapping[str, Any]] = (),
        change_band_records: Optional[Sequence[R5RiskRecord]] = None,
    ) -> dict[str, Any]:
        current_risk = {
            "critical": sum(item.severity == "critical" for item in risks),
            "high": sum(item.severity == "high" for item in risks),
            "medium": sum(item.severity == "medium" for item in risks),
            "low": sum(item.severity == "low" for item in risks),
            "total": len(risks),
        }
        result = {
            "query": len(risks),
            "clue": len(events),
            "center_pattern": len(packet.sites),
            "individual_risk": len(risks),
            "affected_subject": len({item.subject_ref for item in risks} or {item.subject_ref for item in events}),
            "event": len(events),
            "affected_site": len({item.site_ref for item in risks} or {item.site_ref for item in events}),
            "project_signal": len(tuple(item for item in risks if item.severity in {"critical", "high", "medium"})),
            "indicator": len(indicators),
            "risk_anchor": len(risks),
            # Each severity remains a separate authority count; there is no
            # frontend-derived scalar that conflates current risk levels.
            "current_risk": current_risk,
        }
        if change_band_records is not None:
            # This is a closed count of rows emitted from the same authority
            # packet; the frontend must not count projection rows.
            result["change_band_count"] = len(change_band_records)
        return result

    def _result(
        self,
        packet: R5AuthorityPacket,
        projection: Mapping[str, Any],
        counts: Mapping[str, Any],
        source_refs: Sequence[Mapping[str, Any]],
        *,
        view: str,
        return_context_key: str,
        identity_overrides: Optional[Mapping[str, Any]] = None,
        window_start: Optional[date] = None,
        window_end: Optional[date] = None,
    ) -> dict[str, Any]:
        identity = {
            "tenant_id": None,
            "project_ref": packet.project_ref,
            "run_ref": packet.run_ref,
            "snapshot_ref": packet.snapshot_ref,
            "cutoff_state": packet.cutoff_state,
            "cutoff_ref": packet.cutoff_ref,
            "site_ref": None,
            "subject_ref": None,
            "risk_ref": None,
            "risk_instance_ref": None,
            "spine_ref": None,
            "view": view,
            "axis_mode": "calendar",
            "window_start": _iso(window_start),
            "window_end": _iso(window_end),
            "visit_ref": None,
            "event_ref": None,
            "risk_anchor_ref": None,
            "source_locator_ref": None,
            "target_projection_content_hash": projection["content_hash"],
            "return_context_key": return_context_key,
            "authority_hash": packet.authority_hash,
            "source_snapshot_sha256": packet.source_snapshot_sha256,
            "response_snapshot_sha256": "",
            "principal_identity_hash": "",
            "authorization_decision_sha256": "",
            "audit_id": "",
        }
        if identity_overrides:
            identity.update(identity_overrides)
        return {
            "packet": packet,
            "projection": dict(projection),
            "counts": dict(counts),
            "source_refs": [dict(item) for item in source_refs],
            "identity": identity,
            "authority_receipt": packet.authority_receipt(),
        }


def build_response_envelope(
    result: Mapping[str, Any],
    *,
    read_handoff: Mapping[str, Any],
    read_handoff_builder: Optional[Callable[[str], Mapping[str, Any]]] = None,
    tenant_id: str,
    principal_identity_hash: str,
    authorization_decision_sha256: str,
    audit_id: str,
) -> dict[str, Any]:
    """Bind route identity and read handoff into the exact response envelope."""

    packet = result.get("packet")
    if type(packet) is not R5AuthorityPacket:
        raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED")
    identity = dict(result["identity"])
    identity.update(
        {
            "tenant_id": _required(tenant_id, "tenant_id"),
            "principal_identity_hash": _sha(principal_identity_hash, "principal_identity_hash"),
            "authorization_decision_sha256": _sha(authorization_decision_sha256, "authorization_decision_sha256"),
            "audit_id": _required(audit_id, "audit_id"),
        }
    )
    handoff = dict(read_handoff)
    handoff["response_snapshot_sha256"] = ""
    envelope: dict[str, Any] = {
        "schema": PRODUCT_READ_SCHEMA,
        "contract_schema": R5_CONTRACT_SCHEMA,
        "contract_sha256": R5_CONTRACT_SHA256,
        "authority_receipt": dict(result["authority_receipt"]),
        "identity": identity,
        "projection": dict(result["projection"]),
        "counts": dict(result["counts"]),
        "source_refs": [dict(item) for item in result["source_refs"]],
        "response_snapshot_sha256": "",
        "read_handoff": handoff,
        "read_only": True,
        "mutation_applied": False,
        "persisted": False,
        "aggregate_version_before": packet.aggregate_version,
        "aggregate_version_after": packet.aggregate_version,
    }
    digest = response_snapshot_sha256(envelope)
    if read_handoff_builder is not None:
        envelope["read_handoff"] = dict(read_handoff_builder(digest))
        if response_snapshot_sha256(envelope) != digest:
            raise R5ProductAdapterError("RESPONSE_DIGEST_UNSTABLE")
    envelope["response_snapshot_sha256"] = digest
    envelope["identity"]["response_snapshot_sha256"] = digest
    envelope["read_handoff"]["response_snapshot_sha256"] = digest
    return envelope


__all__ = [
    "CHANGE_CAUSES",
    "CHANGE_KINDS",
    "DOMAINS",
    "DOMAIN_ENCODING",
    "FLOW_COVERAGE_BUCKETS",
    "FLOW_MAX_COLUMNS",
    "FLOW_NOT_PROVIDED_REASON_ZH",
    "FLOW_PATH_STATES",
    "FLOW_SEVERITY_ZH",
    "FLOW_STAGE_CHANGE_KINDS",
    "FLOW_STAGE_KINDS",
    "MID_HIGH_SEVERITIES",
    "PRODUCT_READ_SCHEMA",
    "R5AuthorityPacket",
    "R5AuthorityProvider",
    "R5_FLOW_AUTHORITY_CONTRACT_VERSION",
    "R5_CONTRACT_SCHEMA",
    "R5_CONTRACT_SHA256",
    "R5EventRecord",
    "R5FlowStageRecord",
    "R5HistoryRecord",
    "R5ProductAdapter",
    "R5ProductAdapterError",
    "R5RiskRecord",
    "R5SiteAudienceRecord",
    "R5SiteRecord",
    "R5SourceRecord",
    "R5SourceRevisionPair",
    "R5SubjectFlowPathRecord",
    "R5SubjectFlowStep",
    "R5SubjectRecord",
    "R5VisitRecord",
    "SEVERITIES",
    "SYNTHETIC_CUTOFF_REF",
    "SYNTHETIC_FIXTURE_MODE",
    "SYNTHETIC_PROJECT_REF",
    "SYNTHETIC_RUN_REF",
    "SyntheticR5AuthorityProvider",
    "build_response_envelope",
    "build_synthetic_r5_authority_packet",
    "build_synthetic_r5_authority_provider",
    "canonical_json",
    "canonical_sha256",
    "response_snapshot_sha256",
]
