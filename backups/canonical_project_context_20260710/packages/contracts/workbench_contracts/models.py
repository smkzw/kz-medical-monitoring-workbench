from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkbenchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ApprovalState(str, Enum):
    AI_DRAFT = "ai_draft"
    IN_MEDICAL_REVIEW = "in_medical_review"
    RETURNED_FOR_REVISION = "returned_for_revision"
    MEDICALLY_APPROVED = "medically_approved"
    LOCKED_FOR_SUBMISSION = "locked_for_submission"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    RETURN_FOR_REVISION = "return_for_revision"
    REJECT = "reject"
    VIEW_QUALITY_GATE = "view_quality_gate"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_REVIEW = "in_review"
    ACTION_REQUIRED = "action_required"
    ACCEPTED_NO_ACTION = "accepted_no_action"
    RESOLVED = "resolved"
    CLOSED = "closed"
    SUPERSEDED = "superseded"


class Project(WorkbenchModel):
    project_id: str
    project_code: str
    project_name: str
    indication: str
    product_name: str
    study_phase: str
    protocol_id: str
    protocol_version: str
    protocol_date: str
    status: str = "active"
    owner_user_id: str = "medical_manager"
    created_at: datetime
    updated_at: datetime


class EvidenceSource(WorkbenchModel):
    evidence_id: str
    project_id: str
    source_type: str
    title: str
    file_path: str
    file_hash: str = ""
    version_label: str = ""
    confidentiality: str = "internal"
    data_batch_id: Optional[str] = None
    created_at: datetime


class EvidenceSpan(WorkbenchModel):
    span_id: str
    evidence_id: str
    page: Optional[int] = None
    sheet: Optional[str] = None
    row: Optional[int] = None
    column: Optional[str] = None
    quote: str = ""
    normalized_value: str = ""
    confidence: float = 1.0


class DataBatch(WorkbenchModel):
    batch_id: str
    project_id: str
    batch_label: str
    extract_date: str
    uploaded_by: str
    status: str
    source_file_ids: List[str] = Field(default_factory=list)
    previous_batch_id: Optional[str] = None
    mapping_profile_id: str = "default_edc_listing_mapping"
    row_count: int
    subject_count: int
    site_count: int
    created_at: datetime


class RiskCase(WorkbenchModel):
    risk_id: str
    project_id: str
    module: str
    risk_type: str
    title: str
    subject_id: Optional[str] = None
    site_id: Optional[str] = None
    severity: RiskSeverity
    status: RiskStatus
    source_batch_id: Optional[str] = None
    rule_id: str
    evidence_span_ids: List[str] = Field(default_factory=list)
    rationale: str
    recommended_action: str
    owner: str = "medical_manager"
    created_at: datetime
    closed_at: Optional[datetime] = None
    closure_evidence: str = ""


class ApprovalGate(WorkbenchModel):
    approval_id: str
    project_id: str
    target_type: str
    target_id: str
    state: ApprovalState
    requested_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    review_comments: str = ""
    created_at: datetime
    updated_at: datetime


class ApprovalBlocker(WorkbenchModel):
    blocker_id: str
    blocker_type: str
    source_type: str
    source_id: str
    severity: RiskSeverity = RiskSeverity.HIGH
    message: str


class ApprovalActionRequest(WorkbenchModel):
    action: ApprovalAction
    actor: str = "medical_manager"
    comment: str = ""


class ApprovalDecisionRecord(WorkbenchModel):
    decision_id: str
    approval_id: str
    project_id: str
    action: ApprovalAction
    actor: str
    previous_state: ApprovalState
    new_state: ApprovalState
    comment: str = ""
    blocked: bool = False
    blockers: List[ApprovalBlocker] = Field(default_factory=list)
    audit_event_id: str
    created_at: datetime


class AiTaskRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AiTaskOutputValidationStatus(str, Enum):
    NOT_VALIDATED = "not_validated"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AiTaskSourceRef(WorkbenchModel):
    source_id: str
    source_type: str
    title: str
    locator: str
    text_preview: str = ""


class AiTaskRequest(WorkbenchModel):
    module: str
    task_type: str
    prompt_version: str
    allowed_sources: List[AiTaskSourceRef]
    forbidden_source_ids: List[str] = Field(default_factory=list)
    user_instruction: str = ""


class SourceRegistryEntry(WorkbenchModel):
    entry_id: str
    project_id: str
    module: str
    source_kind: str
    public_title: str
    content_hash: str
    size_bytes: int = 0
    parser_status: str = "parsed"
    parser_version: str = "source_registry_v0_1"
    span_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_key: str = Field(default="", exclude=True)
    server_path: str = Field(default="", exclude=True)
    created_at: datetime


class SourceRegistrySpan(WorkbenchModel):
    source_id: str
    entry_id: str
    project_id: str
    module: str
    source_type: str
    title: str
    locator: str
    text_preview: str = ""
    preview_hash: str = Field(default="", exclude=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SourceRegistrationResult(WorkbenchModel):
    entry: SourceRegistryEntry
    spans: List[SourceRegistrySpan] = Field(default_factory=list)


class AiTaskFromRegistryRequest(WorkbenchModel):
    module: str
    task_type: str
    prompt_version: str
    source_ids: List[str]
    forbidden_source_ids: List[str] = Field(default_factory=list)
    user_instruction: str = ""


class AiTaskEvidenceEntry(WorkbenchModel):
    evidence_id: str
    source_id: str
    locator: str
    quote: str = ""
    finding_ids: List[str] = Field(default_factory=list)


class AiTaskArtifact(WorkbenchModel):
    artifact_id: str
    artifact_type: str
    content_type: str = "application/json"
    payload: Dict[str, Any] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)


class AiTaskRun(WorkbenchModel):
    run_id: str
    project_id: str
    module: str
    task_type: str
    purpose: str
    status: AiTaskRunStatus
    provider: str
    model_name: str
    ai_gateway_status: str
    codex_runtime_dependency: bool = False
    prompt_version: str
    schema_version: str = "ai_task_output_v0_1"
    output_validation_status: AiTaskOutputValidationStatus = AiTaskOutputValidationStatus.NOT_VALIDATED
    input_sources: List[AiTaskSourceRef] = Field(default_factory=list)
    forbidden_source_ids: List[str] = Field(default_factory=list)
    artifacts: List[AiTaskArtifact] = Field(default_factory=list)
    evidence_entries: List[AiTaskEvidenceEntry] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    error_message: str = ""
    needs_medical_confirmation: bool = True
    created_at: datetime
    updated_at: datetime


class WorkbenchItemAction(str, Enum):
    MARK_READ = "mark_read"


class WorkbenchItemActionRequest(WorkbenchModel):
    action: WorkbenchItemAction
    actor: str = "medical_manager"
    comment: str = ""


class RuxRiskDispositionAction(str, Enum):
    REVIEWED = "reviewed"
    QUERY_DRAFT = "query_draft"
    SUBMITTED_FOR_APPROVAL = "submitted_for_approval"


class RuxRiskDispositionActionRequest(WorkbenchModel):
    action: RuxRiskDispositionAction
    actor: str = "medical_manager"
    comment: str = ""
    expected_source_version: str
    query_draft_text: str = ""


class WorkbenchItemSourceRef(WorkbenchModel):
    source_type: str
    source_id: str
    label: str
    locator: str = ""


class RuxRiskDispositionRecord(WorkbenchModel):
    record_id: str
    project_id: str
    item_id: str
    risk_id: str
    subject_id: str
    rule_id: str
    action: RuxRiskDispositionAction
    previous_state: str
    new_state: str
    actor: str = "medical_manager"
    comment: str = ""
    query_draft_text: str = ""
    approval_ref: str = ""
    source_version: str
    source_refs_snapshot: List[WorkbenchItemSourceRef] = Field(default_factory=list)
    created_at: datetime


class WorkbenchItem(WorkbenchModel):
    item_id: str
    project_id: str
    module: str
    module_label: str
    item_type: str
    source_type: str
    source_id: str
    title: str
    summary: str
    priority: str
    status: str
    unread: bool = True
    needs_action: bool = True
    owner_role: str = "医学经理"
    action_label: str = "查看"
    target_page: str = "overview"
    target_id: str = ""
    source_version: str
    source_refs: List[WorkbenchItemSourceRef] = Field(default_factory=list)
    updated_at: datetime
    boundary_note: str = ""


class WorkbenchModuleInboxSummary(WorkbenchModel):
    module: str
    module_label: str
    open_count: int = 0
    unread_count: int = 0
    blocked_count: int = 0
    handoff_count: int = 0
    needs_action_count: int = 0


class WorkbenchInboxActionRecord(WorkbenchModel):
    record_id: str
    project_id: str
    item_id: str
    action: WorkbenchItemAction
    actor: str = "medical_manager"
    source_version: str
    comment: str = ""
    created_at: datetime


class WorkbenchInboxResult(WorkbenchModel):
    project_id: str
    generated_at: datetime
    total_open_count: int
    unread_count: int
    handoff_count: int
    items: List[WorkbenchItem] = Field(default_factory=list)
    module_summaries: List[WorkbenchModuleInboxSummary] = Field(default_factory=list)


class AiRun(WorkbenchModel):
    ai_run_id: str
    project_id: str
    module: str
    purpose: str
    provider: str
    model_name: str
    ai_gateway_status: str = "not_configured"
    llm_connected: bool = False
    prompt_version: str = ""
    schema_version: str = ""
    output_validation_status: str = "not_validated"
    input_refs: List[str] = Field(default_factory=list)
    output_refs: List[str] = Field(default_factory=list)
    status: str = "completed"
    created_at: datetime


class ModuleManifest(WorkbenchModel):
    module: str
    label: str
    lifecycle_step: Optional[int] = None
    medical_role: str
    implementation_status: str
    route_key: str = ""
    primary_user_role: str = "医学经理"
    source_inputs: List[str] = Field(default_factory=list)
    ai_task_types: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    acceptance_status: str = "not_started"
    visible_in_dashboard: bool = True
    note: str = ""


class ModuleCatalog(WorkbenchModel):
    project_id: str
    generated_at: datetime
    modules: List[ModuleManifest] = Field(default_factory=list)


class AuditEvent(WorkbenchModel):
    audit_id: str
    project_id: str
    actor: str
    action: str
    target_type: str
    target_id: str
    detail: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ApprovalActionResult(WorkbenchModel):
    approval: ApprovalGate
    decision: ApprovalDecisionRecord
    audit_event: AuditEvent
    blockers: List[ApprovalBlocker] = Field(default_factory=list)


class EligibilityRuleType(str, Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class EligibilityRuleVerdict(str, Enum):
    PASS = "pass"
    PASS_VERIFY = "pass_verify"
    FAIL = "fail"
    INSUFFICIENT = "insufficient"
    INVESTIGATOR = "investigator"
    NA = "na"
    NEEDS_EVIDENCE = "needs_evidence"
    NOT_REVIEWED = "not_reviewed"
    PARSE_ERROR = "parse_error"


class EligibilityCandidateStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    ERROR = "error"
    READY_FOR_REVIEW = "ready_for_review"
    ACTION_REQUIRED = "action_required"
    AWAITING_SITE_RESPONSE = "awaiting_site_response"
    READY_FOR_RANDOMIZATION = "ready_for_randomization"
    SCREEN_FAILED = "screen_failed"


class EligibilityOverallConclusion(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT = "insufficient"
    INVESTIGATOR = "investigator"
    NEEDS_EVIDENCE = "needs_evidence"
    NOT_REVIEWED = "not_reviewed"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING_INFORMATION = "pending_information"
    MEDICAL_REVIEW_REQUIRED = "medical_review_required"


class EligibilityEvidence(WorkbenchModel):
    evidence_id: str
    rule_id: str = Field(pattern=r"^(IN|EX)-\d{2}[A-Za-z0-9_.-]*$")
    source_type: str
    source_title: str
    source_domain: str = ""
    source_record_id: str = Field(default="", exclude=True)
    evidence_span_id: Optional[str] = None
    field_path: str = ""
    quote: str = ""
    normalized_value: str = ""
    collected_at: Optional[datetime] = None
    confidence: float = 1.0


class EligibilityActionItem(WorkbenchModel):
    item_id: str
    rule_id: str = Field(pattern=r"^(IN|EX)-\d{2}[A-Za-z0-9_.-]*$")
    item_type: str
    severity: RiskSeverity = RiskSeverity.MEDIUM
    title: str
    detail: str
    owner: str = "medical_manager"
    status: str = "open"
    due_date: Optional[str] = None
    recommended_action: str = ""


class EligibilityRuleReview(WorkbenchModel):
    rule_id: str = Field(pattern=r"^(IN|EX)-\d{2}[A-Za-z0-9_.-]*$")
    rule_type: EligibilityRuleType
    rule_label: str
    criterion_text: str
    verdict: EligibilityRuleVerdict
    verdict_label: str
    severity: RiskSeverity = RiskSeverity.LOW
    rationale: str
    evidence: List[EligibilityEvidence] = Field(default_factory=list)
    missing_information: List[EligibilityActionItem] = Field(default_factory=list)
    medical_confirmation: List[EligibilityActionItem] = Field(default_factory=list)
    reviewed_by: str = "system"
    reviewed_at: datetime
    source_phase_id: str = ""
    source_phase_label: str = ""
    source_report_path: str = Field(default="", exclude=True)
    source_raw_path: str = Field(default="", exclude=True)
    verification_type: str = ""


class EligibilityCandidate(WorkbenchModel):
    candidate_id: str
    project_id: str
    subject_id: str
    site_id: str
    screening_number: str
    source_system: str = "workbench"
    source_project_code: str = ""
    source_path: str = Field(default="", exclude=True)
    study_stage: str = ""
    active_phase_id: str = ""
    active_phase_label: str = ""
    document_count: int = 0
    phase_reviews: List[Dict[str, Any]] = Field(default_factory=list)
    status: EligibilityCandidateStatus
    overall_conclusion: EligibilityOverallConclusion
    overall_rationale: str
    review_priority: RiskSeverity
    age: Optional[int] = None
    sex: str = ""
    screening_visit_date: str
    randomization_target_date: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    rule_reviews: List[EligibilityRuleReview] = Field(default_factory=list)
    missing_information: List[EligibilityActionItem] = Field(default_factory=list)
    medical_confirmation_items: List[EligibilityActionItem] = Field(default_factory=list)
    audit_event_ids: List[str] = Field(default_factory=list)


class EligibilityReviewPhase(WorkbenchModel):
    phase_id: str
    name: str
    stage: str = ""
    study_stage: str = ""
    visit: str = ""
    study_week: str = ""
    day_window: str = ""
    description: str = ""
    required_items: List[str] = Field(default_factory=list)
    included_document_phases: List[str] = Field(default_factory=list)


class EligibilitySubjectPhaseReview(WorkbenchModel):
    phase_id: str
    name: str
    visit: str = ""
    day_window: str = ""
    status: str = "not_reviewed"
    verdict: str = ""
    summary: str = ""
    has_report: bool = False
    has_raw_response: bool = False
    evidence_bundle_exists: bool = False
    report_path: str = Field(default="", exclude=True)
    raw_response_path: str = Field(default="", exclude=True)
    evidence_bundle_path: str = Field(default="", exclude=True)
    updated_at: str = ""


class EligibilitySubjectRow(WorkbenchModel):
    subject_id: str
    project_code: str
    center_code: str = ""
    center_name: str = ""
    status: str = ""
    overall_verdict: str = ""
    doc_count: int = 0
    last_updated: str = ""
    icf_date: str = ""
    first_dosing_date: str = ""
    birth_date: str = ""
    phase_reviews: Dict[str, EligibilitySubjectPhaseReview] = Field(default_factory=dict)
    evidence_bundle_exists: bool = False
    report_exists: bool = False
    can_open_report: bool = False


class EligibilityRuleDefinition(WorkbenchModel):
    rule_id: str = Field(pattern=r"^(IN|EX)-\d{2}[A-Za-z0-9_.-]*$")
    rule_type: EligibilityRuleType
    rule_label: str
    criterion_text: str
    source_path: str = Field(default="", exclude=True)


class EligibilityPoolSummary(WorkbenchModel):
    total_candidates: int
    counts_by_status: Dict[str, int]
    counts_by_overall_conclusion: Dict[str, int]
    rules_with_findings: List[str] = Field(default_factory=list)
    open_missing_information_count: int = 0
    open_medical_confirmation_count: int = 0


class EligibilityTaskEntry(WorkbenchModel):
    module: str = "eligibility_review"
    module_label: str = "入排审核"
    source_system: str = "enrollment-review-app"
    source_project_code: str
    default_phase_id: str = ""
    selected_subject_id: str = ""
    selected_phase_id: str = ""
    source_project_path: str = Field(default="", exclude=True)


class EligibilityProjectStats(WorkbenchModel):
    total_subjects: int
    counts_by_status: Dict[str, int] = Field(default_factory=dict)
    counts_by_overall_verdict: Dict[str, int] = Field(default_factory=dict)
    counts_by_phase_status: Dict[str, int] = Field(default_factory=dict)
    subjects_with_reports: int = 0
    subjects_with_evidence_bundles: int = 0
    criteria_rule_count: int = 0


class EligibilityAuditSummary(WorkbenchModel):
    audit_ledger_path: str = Field(default="", exclude=True)
    event_count: int = 0
    recent_events: List[Dict[str, Any]] = Field(default_factory=list)


class EligibilityAvailableAction(WorkbenchModel):
    action_id: str
    label: str
    target_type: str
    target_id: str = ""
    enabled: bool = True
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EligibilityReviewDataset(WorkbenchModel):
    project_id: str
    module: str = "eligibility_review"
    module_label: str = "入排审核"
    source_system: str = "enrollment-review-app"
    source_project_code: str = ""
    source_path: str = Field(default="", exclude=True)
    protocol_id: str
    protocol_version: str
    source_batch_id: str = ""
    study_stage: str = ""
    active_phase_id: str = ""
    task_entry: Optional[EligibilityTaskEntry] = None
    project_stats: Optional[EligibilityProjectStats] = None
    review_phases: List[EligibilityReviewPhase] = Field(default_factory=list)
    subject_rows: List[EligibilitySubjectRow] = Field(default_factory=list)
    criteria_rules: List[EligibilityRuleDefinition] = Field(default_factory=list)
    criteria_rule_ids: List[str] = Field(default_factory=list)
    generated_at: datetime
    summary: EligibilityPoolSummary
    candidates: List[EligibilityCandidate] = Field(default_factory=list)
    selected_candidate: Optional[EligibilityCandidate] = None
    audit_events: List[AuditEvent] = Field(default_factory=list)
    audit_summary: Optional[EligibilityAuditSummary] = None
    available_actions: List[EligibilityAvailableAction] = Field(default_factory=list)


class ProtocolSection(WorkbenchModel):
    section_id: str
    document_id: str
    parent_id: Optional[str] = None
    heading: str
    ich_m11_anchor: str = ""
    completion_status: str = "not_started"
    approval_state: ApprovalState = ApprovalState.AI_DRAFT
    evidence_coverage: float = 0.0
    risk_count: int = 0
    content_blocks: List[Dict[str, Any]] = Field(default_factory=list)


class ProtocolDocument(WorkbenchModel):
    document_id: str
    project_id: str
    document_type: str = "clinical_study_protocol"
    template_version: str = "protocol_template_v0_1"
    protocol_id: str
    version: str
    status: str = "draft"
    sections: List[ProtocolSection] = Field(default_factory=list)
    quality_gates: List[Dict[str, Any]] = Field(default_factory=list)


class RevisionSuggestion(WorkbenchModel):
    suggestion_id: str
    proposal_text: str
    diff_patch: str
    rationale: str
    evidence_span_ids: List[str] = Field(default_factory=list)
    uncertainty: str = ""
    user_decision: str = "pending"


class RevisionAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    REQUEST_REWRITE = "request_rewrite"


class RevisionThread(WorkbenchModel):
    thread_id: str
    project_id: str
    document_id: str
    section_id: str
    anchor_type: str
    anchor_path: str
    selected_text: str
    user_instruction: str
    intent: str
    ai_run_id: str
    suggestions: List[RevisionSuggestion] = Field(default_factory=list)
    status: str = "open"
    created_at: datetime
    resolved_at: Optional[datetime] = None


class MedicalWritingRevisionRequest(WorkbenchModel):
    document_id: Optional[str] = None
    section_id: str
    anchor_type: str = "paragraph"
    anchor_path: str = ""
    selected_text: str = ""
    user_instruction: str
    intent: str = "medical_writing_revision"
    requested_by: str = "medical_manager"


class MedicalWritingRevisionResult(WorkbenchModel):
    thread: RevisionThread
    suggestion: RevisionSuggestion
    approval_state: ApprovalState = ApprovalState.IN_MEDICAL_REVIEW
    audit_event: AuditEvent


class RevisionActionRequest(WorkbenchModel):
    action: RevisionAction
    suggestion_id: Optional[str] = None
    actor: str = "medical_manager"
    comment: str = ""
    rewrite_instruction: str = ""


class RevisionActionResult(WorkbenchModel):
    thread: RevisionThread
    action: RevisionAction
    suggestion: Optional[RevisionSuggestion] = None
    audit_event: AuditEvent


class SubjectTimelineEventType(str, Enum):
    VISIT = "visit"
    MEDICAL_HISTORY = "medical_history"
    CONCOMITANT_MEDICATION = "concomitant_medication"
    DOSE_ADJUSTMENT = "dose_adjustment"
    LAB = "lab"
    EFFICACY_SCORE = "efficacy_score"
    ADVERSE_EVENT = "adverse_event"
    PROTOCOL_DEVIATION = "protocol_deviation"
    QUERY = "query"


class SubjectTrendDomain(str, Enum):
    EFFICACY = "efficacy"
    SAFETY = "safety"


class SubjectTrendDirection(str, Enum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    STABLE_RANGE = "stable_range"


class SubjectOverview(WorkbenchModel):
    project_id: str
    subject_id: str
    site_id: str
    screening_number: str
    randomization_number: Optional[str] = None
    treatment_arm: str
    enrollment_status: str
    first_dose_date: Optional[str] = None
    baseline_visit_date: Optional[str] = None
    latest_visit_code: str
    latest_visit_label: str
    latest_visit_date: str
    key_medical_context: List[str] = Field(default_factory=list)


class SubjectTimelineEvent(WorkbenchModel):
    event_id: str
    project_id: str
    subject_id: str
    module: str = "medical_monitoring"
    module_label: str = "医学监查"
    event_type: SubjectTimelineEventType
    event_date: str
    study_day: int
    visit_code: Optional[str] = None
    visit_label: str = ""
    source_domain: str
    source_record_id: str
    source_locator: str = ""
    title: str
    detail: str
    result_value: Optional[str] = None
    clinical_interpretation: str = ""
    related_risk_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def fill_legacy_source_locator(self) -> "SubjectTimelineEvent":
        if not self.source_locator:
            self.source_locator = f"{self.source_domain}:{self.source_record_id}"
        return self


class SubjectTrendPoint(WorkbenchModel):
    point_id: str
    visit_code: str
    visit_label: str
    assessment_date: str
    study_day: int
    value: float
    baseline_value: Optional[float] = None
    change_from_baseline: Optional[float] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    normality: str = "not_applicable"
    risk_flag: bool = False
    source_domain: str
    source_record_id: str
    source_locator: str = ""
    note: str = ""

    @model_validator(mode="after")
    def fill_legacy_source_locator(self) -> "SubjectTrendPoint":
        if not self.source_locator:
            self.source_locator = f"{self.source_domain}:{self.source_record_id}"
        return self


class SubjectTrendMetric(WorkbenchModel):
    metric_key: str
    metric_label: str
    domain: SubjectTrendDomain
    unit: str = ""
    direction: SubjectTrendDirection
    clinically_meaningful_change: Optional[float] = None
    points: List[SubjectTrendPoint] = Field(default_factory=list)


class TimepointRiskPrompt(WorkbenchModel):
    prompt_id: str
    project_id: str
    subject_id: str
    module: str = "medical_monitoring"
    module_label: str = "医学监查"
    visit_code: str
    visit_label: str
    prompt_date: str
    study_day: int
    severity: RiskSeverity
    status: RiskStatus
    risk_type: str
    title: str
    prompt_text: str
    trigger_domains: List[str] = Field(default_factory=list)
    related_event_ids: List[str] = Field(default_factory=list)
    related_metric_keys: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    evidence_span_ids: List[str] = Field(default_factory=list)
    query_id: Optional[str] = None
    pd_id: Optional[str] = None
    recommended_action: str


class SubjectMonitoringDrilldown(WorkbenchModel):
    project_id: str
    subject_id: str
    module: str = "medical_monitoring"
    module_label: str = "医学监查"
    generated_at: datetime
    subject: SubjectOverview
    timeline: List[SubjectTimelineEvent] = Field(default_factory=list)
    efficacy_trends: List[SubjectTrendMetric] = Field(default_factory=list)
    safety_trends: List[SubjectTrendMetric] = Field(default_factory=list)
    risk_prompts: List[TimepointRiskPrompt] = Field(default_factory=list)
    review_focus: List[str] = Field(default_factory=list)


class ListingSheetPayload(WorkbenchModel):
    sheet_name: str
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class MonitoringIntakeRequest(WorkbenchModel):
    batch_label: str = "原始数据 listing Batch 004"
    extract_date: str
    previous_batch_id: Optional[str] = None
    uploaded_by: str = "medical_manager"
    mapping_confirmations: Dict[str, str] = Field(default_factory=dict)
    sheets: List[ListingSheetPayload] = Field(default_factory=list)


class FieldMappingCandidate(WorkbenchModel):
    sheet_name: str
    source_field: str
    standard_field: str
    confidence: float
    status: str
    note: str = ""


class ListingDiffSummary(WorkbenchModel):
    previous_batch_id: Optional[str] = None
    new_batch_id: str
    added_row_count: int = 0
    changed_row_count: int = 0
    removed_row_count: int = 0
    subject_count: int = 0
    site_count: int = 0
    sheet_row_counts: Dict[str, int] = Field(default_factory=dict)
    new_subject_ids: List[str] = Field(default_factory=list)
    changed_subject_ids: List[str] = Field(default_factory=list)


class RuleRunSummary(WorkbenchModel):
    total_rules: int
    generated_risk_count: int
    generated_query_count: int
    blocked_by_mapping: bool = False
    messages: List[str] = Field(default_factory=list)


class MonitoringIntakeResult(WorkbenchModel):
    session_id: str
    project_id: str
    mapping_status: str
    batch: DataBatch
    field_mappings: List[FieldMappingCandidate] = Field(default_factory=list)
    diff_summary: ListingDiffSummary
    generated_risks: List[RiskCase] = Field(default_factory=list)
    rule_run: RuleRunSummary
    audit_preview: List[AuditEvent] = Field(default_factory=list)


class ClinicalDatasetSummary(WorkbenchModel):
    dataset_id: str
    dataset_name: str
    standard: str
    package_role: str = ""
    domain: str = ""
    label: str = ""
    class_name: str = ""
    purpose: str = ""
    structure: str = ""
    source_package: str
    relative_path: str
    file_format: str
    parser_status: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    key_variables: List[str] = Field(default_factory=list)
    sample_variables: List[str] = Field(default_factory=list)
    define_linked: bool = False
    define_source: str = ""
    size_bytes: int = 0


class TflOutputSummary(WorkbenchModel):
    output_id: str
    display_id: str
    output_type: str
    domain_hint: str = ""
    title_hint: str = ""
    source_package: str
    relative_path: str
    file_format: str
    parser_status: str
    paired_file_id: Optional[str] = None
    size_bytes: int = 0


class TflPackageSummary(WorkbenchModel):
    package_id: str
    package_label: str
    project_id: str
    module: str = "data_analysis_tfl"
    module_label: str = "数据分析与TFL"
    generated_at: datetime
    dataset_root_label: str
    tfl_root_label: str
    define_xml_count: int = 0
    define_itemgroup_count: int = 0
    dataset_count_by_standard: Dict[str, int] = Field(default_factory=dict)
    dataset_count_by_role: Dict[str, int] = Field(default_factory=dict)
    dataset_count_by_format: Dict[str, int] = Field(default_factory=dict)
    tfl_count_by_type: Dict[str, int] = Field(default_factory=dict)
    datasets: List[ClinicalDatasetSummary] = Field(default_factory=list)
    outputs: List[TflOutputSummary] = Field(default_factory=list)
    traceability_notes: List[str] = Field(default_factory=list)
    parser_warnings: List[str] = Field(default_factory=list)


class TflManifestResult(WorkbenchModel):
    project_id: str
    module: str = "data_analysis_tfl"
    module_label: str = "数据分析与TFL"
    generated_at: datetime
    package_count: int = 0
    total_datasets: int = 0
    total_outputs: int = 0
    packages: List[TflPackageSummary] = Field(default_factory=list)
    parser_notes: List[str] = Field(default_factory=list)


class TflReviewAction(str, Enum):
    MARK_REVIEWED = "mark_reviewed"
    REQUEST_STATISTICAL_REVIEW = "request_statistical_review"
    CREATE_WRITING_CANDIDATE = "create_writing_candidate"
    RETURN_FOR_DATASET_CHECK = "return_for_dataset_check"
    RESET_REVIEW = "reset_review"


class TflReviewActionRequest(WorkbenchModel):
    action: TflReviewAction
    actor: str = "medical_manager"
    comment: str = ""


class TflReviewRecord(WorkbenchModel):
    record_id: str
    project_id: str
    package_id: str
    output_id: str
    output_display_id: str
    action: TflReviewAction
    actor: str
    previous_status: str
    new_status: str
    comment: str = ""
    created_at: datetime


class TflReviewQualityGate(WorkbenchModel):
    gate_id: str
    gate_label: str
    status: str
    detail: str
    source_refs: List[str] = Field(default_factory=list)


class TflReviewWorkbenchResult(WorkbenchModel):
    project_id: str
    module: str = "data_analysis_tfl"
    module_label: str = "数据分析与TFL"
    generated_at: datetime
    package_id: str
    package_label: str
    selected_output_id: str
    selected_output: Optional[TflOutputSummary] = None
    paired_dataset: Optional[ClinicalDatasetSummary] = None
    current_status: str = "待医学审阅"
    review_records: List[TflReviewRecord] = Field(default_factory=list)
    quality_gates: List[TflReviewQualityGate] = Field(default_factory=list)
    candidate_outputs: List[TflOutputSummary] = Field(default_factory=list)
    dataset_context: List[ClinicalDatasetSummary] = Field(default_factory=list)
    available_actions: List[TflReviewAction] = Field(default_factory=list)
    formal_output_boundary: str = "当前仅形成待医学确认的数据审阅和写作引用候选，不生成正式监管TFL。"
    needs_medical_confirmation: bool = True
    codex_runtime_dependency: bool = False


class TflWritingCitationCandidate(WorkbenchModel):
    candidate_id: str
    project_id: str
    source_module: str = "data_analysis_tfl"
    source_module_label: str = "数据分析与TFL"
    target_module: str = "medical_writing"
    target_module_label: str = "医学写作"
    package_id: str
    package_label: str
    output_id: str
    output_display_id: str
    output_type: str
    domain_hint: str = ""
    title_hint: str = ""
    paired_dataset_id: str = ""
    paired_dataset_name: str = ""
    paired_dataset_standard: str = ""
    paired_dataset_domain: str = ""
    paired_dataset_row_count: Optional[int] = None
    review_record_id: str
    reviewer: str
    review_comment: str
    review_created_at: datetime
    recommended_writing_sections: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    citation_boundary: str = "仅作为待医学确认的写作引用候选；正式写入前需核对CSR/SAP/统计输出和版本。"
    needs_medical_confirmation: bool = True
    codex_runtime_dependency: bool = False


class TflWritingCitationManifestResult(WorkbenchModel):
    project_id: str
    module: str = "medical_writing"
    module_label: str = "医学写作"
    source_module: str = "data_analysis_tfl"
    source_module_label: str = "数据分析与TFL"
    generated_at: datetime
    total_candidates: int = 0
    candidates: List[TflWritingCitationCandidate] = Field(default_factory=list)
    quality_gates: List[TflReviewQualityGate] = Field(default_factory=list)
    formal_output_boundary: str = "当前仅汇总TFL写作引用候选，不自动生成或改写正式医学写作正文。"
    needs_medical_confirmation: bool = True
    codex_runtime_dependency: bool = False


class SafetySourceDocumentSummary(WorkbenchModel):
    document_id: str
    document_type: str
    project_code: str
    public_title: str
    source_package: str
    relative_path: str
    file_format: str
    parser_status: str
    size_bytes: int = 0
    role_hint: str = ""
    key_topics: List[str] = Field(default_factory=list)


class SafetyListingDomainSummary(WorkbenchModel):
    domain_id: str
    sheet_name: str
    domain: str
    domain_label: str
    safety_relevance: str
    row_count: int = 0
    subject_count: int = 0
    site_count: int = 0
    key_fields: List[str] = Field(default_factory=list)
    parser_status: str = "parsed"
    parser_notes: List[str] = Field(default_factory=list)
    source_package: str = ""


class SafetySignalCandidate(WorkbenchModel):
    signal_id: str
    signal_type: str
    signal_label: str
    title: str
    severity: RiskSeverity
    source_package: str
    source_domains: List[str] = Field(default_factory=list)
    evidence_locators: List[str] = Field(default_factory=list)
    subject_id: Optional[str] = None
    site_id: Optional[str] = None
    observation: str
    medical_pv_boundary: str
    recommended_next_step: str
    confirmation_status: str = "待医学/PV确认"


class SafetyReviewAction(str, Enum):
    MARK_MEDICAL_REVIEWED = "mark_medical_reviewed"
    REQUEST_PV_CONFIRMATION = "request_pv_confirmation"
    RETURN_FOR_SOURCE_CHECK = "return_for_source_check"
    ACCEPT_NO_ACTION = "accept_no_action"
    RESET_REVIEW = "reset_review"


class SafetyReviewActionRequest(WorkbenchModel):
    action: SafetyReviewAction
    actor: str = "medical_manager"
    comment: str = ""


class SafetyReviewRecord(WorkbenchModel):
    record_id: str
    project_id: str
    package_id: str
    signal_id: str
    signal_label: str
    action: SafetyReviewAction
    actor: str
    previous_status: str
    new_status: str
    comment: str = ""
    created_at: datetime


class SafetyQualityGate(WorkbenchModel):
    gate_id: str
    gate_label: str
    status: str
    owner: str
    detail: str
    source_refs: List[str] = Field(default_factory=list)


class SafetySourcePackageSummary(WorkbenchModel):
    package_id: str
    package_label: str
    project_code: str
    source_root_label: str
    package_role: str
    listing_domains: List[SafetyListingDomainSummary] = Field(default_factory=list)
    documents: List[SafetySourceDocumentSummary] = Field(default_factory=list)
    signal_candidates: List[SafetySignalCandidate] = Field(default_factory=list)
    quality_gates: List[SafetyQualityGate] = Field(default_factory=list)
    parser_warnings: List[str] = Field(default_factory=list)


class SafetyPvManifestResult(WorkbenchModel):
    project_id: str
    module: str = "safety_pv"
    module_label: str = "安全信号与PV协同"
    generated_at: datetime
    package_count: int = 0
    total_listing_domains: int = 0
    total_documents: int = 0
    total_signal_candidates: int = 0
    quality_gate_count: int = 0
    packages: List[SafetySourcePackageSummary] = Field(default_factory=list)
    parser_notes: List[str] = Field(default_factory=list)


class SafetyReviewWorkbenchResult(WorkbenchModel):
    project_id: str
    module: str = "safety_pv"
    module_label: str = "安全信号与PV协同"
    generated_at: datetime
    package_id: str
    package_label: str
    selected_signal_id: str
    selected_signal: Optional[SafetySignalCandidate] = None
    current_status: str = "待医学/PV确认"
    review_records: List[SafetyReviewRecord] = Field(default_factory=list)
    quality_gates: List[SafetyQualityGate] = Field(default_factory=list)
    candidate_signals: List[SafetySignalCandidate] = Field(default_factory=list)
    listing_context: List[SafetyListingDomainSummary] = Field(default_factory=list)
    document_context: List[SafetySourceDocumentSummary] = Field(default_factory=list)
    available_actions: List[SafetyReviewAction] = Field(default_factory=list)
    formal_output_boundary: str = "当前仅形成待医学/PV确认的安全信号审阅和PV交接候选，不生成最终药物警戒结论或监管递交动作。"
    needs_medical_pv_confirmation: bool = True
    codex_runtime_dependency: bool = False


class SafetyPvHandoffCandidate(WorkbenchModel):
    candidate_id: str
    project_id: str
    source_module: str = "safety_pv"
    source_module_label: str = "安全信号与PV协同"
    package_id: str
    package_label: str
    signal_id: str
    signal_label: str
    signal_type: str
    title: str
    severity: RiskSeverity
    source_domains: List[str] = Field(default_factory=list)
    evidence_locators: List[str] = Field(default_factory=list)
    review_record_id: str
    reviewer: str
    review_comment: str
    review_created_at: datetime
    recommended_handoff_sections: List[str] = Field(default_factory=list)
    handoff_boundary: str = "仅作为待医学/PV确认的协同交接候选；最终安全性结论、报告性判断和监管递交流程仍需PV流程确认。"
    needs_medical_pv_confirmation: bool = True
    codex_runtime_dependency: bool = False


class SafetyPvHandoffManifestResult(WorkbenchModel):
    project_id: str
    module: str = "safety_pv"
    module_label: str = "安全信号与PV协同"
    generated_at: datetime
    total_candidates: int = 0
    candidates: List[SafetyPvHandoffCandidate] = Field(default_factory=list)
    quality_gates: List[SafetyQualityGate] = Field(default_factory=list)
    formal_output_boundary: str = "当前仅汇总待医学/PV确认的协同交接候选，不生成最终药物警戒结论或监管递交动作。"
    needs_medical_pv_confirmation: bool = True
    codex_runtime_dependency: bool = False


class EvidenceSourceDocumentSummary(WorkbenchModel):
    document_id: str
    document_type: str
    public_title: str
    drug_name: str = ""
    trial_identifier: str = ""
    source_package: str
    relative_path: str = ""
    file_format: str = ""
    parser_status: str = "inventory_only"
    primary_source_type: str = ""
    primary_source_id: str = ""
    primary_source_date: str = ""
    verification_status: str = ""
    evidence_level: str = ""
    role_hint: str = ""


class CompetitiveProductSummary(WorkbenchModel):
    product_id: str
    drug_name: str
    target: str = ""
    sponsor: str = ""
    trial_count: int = 0
    phase_summary: Dict[str, int] = Field(default_factory=dict)
    region_summary: Dict[str, int] = Field(default_factory=dict)
    highest_evidence_level: str = ""
    approval_status_hint: str = ""


class CompetitiveTrialDesignSummary(WorkbenchModel):
    trial_id: str
    drug_name: str
    target: str = ""
    sponsor: str = ""
    registry: str = ""
    registry_id: str = ""
    trial_acronym: str = ""
    phase: str = ""
    trial_status: str = ""
    region: str = ""
    design_type: str = ""
    sample_size: str = ""
    treatment_group: str = ""
    comparator: str = ""
    dose: str = ""
    route: str = ""
    dosing_frequency: str = ""
    treatment_period: str = ""
    background_treatment: str = ""
    key_population: str = ""
    primary_endpoint: str = ""
    primary_timepoint: str = ""
    key_secondary_endpoint: str = ""
    protocol_available: str = ""
    sap_available: str = ""
    publication_available: str = ""
    verification_status: str = ""
    evidence_level: str = ""


class CompetitiveResultEndpointSummary(WorkbenchModel):
    result_id: str
    result_kind: str
    trial_id: str
    drug_name: str
    trial_identifier: str = ""
    endpoint_name: str
    endpoint_type: str = ""
    timepoint: str = ""
    treatment_group: str = ""
    comparator: str = ""
    sample_size: str = ""
    effect_summary: str = ""
    source_type: str = ""
    source_locator: str = ""
    verification_status: str = ""
    evidence_level: str = ""
    medical_boundary: str = "待医学确认，不构成跨试验疗效或安全性判断"


class EvidencePicosQuestion(WorkbenchModel):
    question_id: str
    picos_domain: str
    question: str
    evidence_status: str
    current_evidence_summary: str
    required_user_decision: str
    source_refs: List[str] = Field(default_factory=list)
    handoff_to_writing: bool = True


class EvidencePicosDecisionAction(str, Enum):
    SELECT_OPTION = "select_option"
    SAVE_RATIONALE = "save_rationale"
    MARK_WRITING_CANDIDATE = "mark_writing_candidate"
    RETURN_FOR_EVIDENCE = "return_for_evidence"
    RESET_DECISION = "reset_decision"


class EvidencePicosDecisionOption(WorkbenchModel):
    option_id: str
    label: str
    design_summary: str
    evidence_summary: str
    medical_rationale_prompt: str
    writing_target_section: str = ""
    source_refs: List[str] = Field(default_factory=list)
    risk_notes: List[str] = Field(default_factory=list)
    candidate_rank: int = 0


class EvidencePicosDecisionRecord(WorkbenchModel):
    record_id: str
    project_id: str
    package_id: str
    question_id: str
    action: EvidencePicosDecisionAction
    actor: str = "medical_manager"
    option_id: str = ""
    user_rationale: str = ""
    comment: str = ""
    from_status: str = ""
    to_status: str = ""
    created_at: datetime


class EvidencePicosWorkflowStep(WorkbenchModel):
    question_id: str
    picos_domain: str
    question: str
    evidence_status: str
    current_evidence_summary: str
    required_user_decision: str
    source_refs: List[str] = Field(default_factory=list)
    handoff_to_writing: bool = True
    options: List[EvidencePicosDecisionOption] = Field(default_factory=list)
    selected_option_id: str = ""
    user_rationale: str = ""
    decision_status: str = "待用户确认"
    writing_handoff_status: str = "暂不可流转"
    writing_target_section: str = ""
    quality_gate_status: str = "blocked"
    revision_thread_id: str = ""
    ai_task_type: str = "picos_design_coach"
    ai_gateway_status: str = "not_configured"
    codex_runtime_dependency: bool = False
    needs_medical_confirmation: bool = True
    audit_trail: List[EvidencePicosDecisionRecord] = Field(default_factory=list)


class EvidencePicosActionRequest(WorkbenchModel):
    action: EvidencePicosDecisionAction
    option_id: str = ""
    user_rationale: str = ""
    comment: str = ""
    actor: str = "medical_manager"


class EvidencePicosWorkflowResult(WorkbenchModel):
    project_id: str
    package_id: str
    module: str = "evidence_design"
    module_label: str = "证据调研与方案设计"
    workflow_label: str = "PICOS 决策工作台"
    generated_at: datetime
    decision_count: int = 0
    writing_candidate_count: int = 0
    blocking_gate_count: int = 0
    ai_gateway_status: str = "not_configured"
    codex_runtime_dependency: bool = False
    needs_medical_confirmation: bool = True
    formal_output_boundary: str = "所有PICOS输出均为待医学批准的正式内容候选，不代表已完成医学批准。"
    steps: List[EvidencePicosWorkflowStep] = Field(default_factory=list)
    quality_gates: List[EvidenceQualityGate] = Field(default_factory=list)
    parser_notes: List[str] = Field(default_factory=list)


class EvidenceQualityGate(WorkbenchModel):
    gate_id: str
    gate_label: str
    status: str
    owner: str
    detail: str
    source_refs: List[str] = Field(default_factory=list)


class EvidenceDesignPackageSummary(WorkbenchModel):
    package_id: str
    package_label: str
    indication: str
    source_root_label: str
    package_role: str
    products: List[CompetitiveProductSummary] = Field(default_factory=list)
    trial_count_by_phase: Dict[str, int] = Field(default_factory=dict)
    trial_count_by_status: Dict[str, int] = Field(default_factory=dict)
    document_count_by_type: Dict[str, int] = Field(default_factory=dict)
    endpoint_count_by_name: Dict[str, int] = Field(default_factory=dict)
    safety_row_count: int = 0
    documents: List[EvidenceSourceDocumentSummary] = Field(default_factory=list)
    trial_designs: List[CompetitiveTrialDesignSummary] = Field(default_factory=list)
    efficacy_results: List[CompetitiveResultEndpointSummary] = Field(default_factory=list)
    safety_results: List[CompetitiveResultEndpointSummary] = Field(default_factory=list)
    picos_questions: List[EvidencePicosQuestion] = Field(default_factory=list)
    quality_gates: List[EvidenceQualityGate] = Field(default_factory=list)
    parser_warnings: List[str] = Field(default_factory=list)


class EvidenceDesignManifestResult(WorkbenchModel):
    project_id: str
    module: str = "evidence_design"
    module_label: str = "证据调研与方案设计"
    generated_at: datetime
    package_count: int = 0
    total_products: int = 0
    total_trials: int = 0
    total_documents: int = 0
    total_result_rows: int = 0
    picos_question_count: int = 0
    quality_gate_count: int = 0
    packages: List[EvidenceDesignPackageSummary] = Field(default_factory=list)
    parser_notes: List[str] = Field(default_factory=list)


class WritingSourceDocumentSummary(WorkbenchModel):
    document_id: str
    document_type: str
    project_code: str
    public_title: str
    source_package: str
    relative_path: str
    file_format: str
    parser_status: str
    content_hash: str = ""
    size_bytes: int = 0
    paragraph_count: int = 0
    table_count: int = 0
    span_count: int = 0
    section_count: int = 0
    image_count: int = 0
    has_revision_marks: bool = False
    has_fields: bool = False
    style_summary: Dict[str, int] = Field(default_factory=dict)
    protocol_identifier: str = ""
    protocol_version: str = ""
    protocol_date: str = ""
    indication_hint: str = ""
    role_hint: str = ""


class WritingSectionSummary(WorkbenchModel):
    section_id: str
    source_document_id: str
    section_number: str = ""
    heading: str
    heading_level: int = 1
    anchor_path: str
    source_locator: str
    paragraph_count: int = 0
    table_count: int = 0
    word_count: int = 0
    ich_m11_area: str = ""
    writing_status: str = "待医学审阅"
    evidence_status: str = "待补来源定位"
    medical_approval_status: str = "待医学批准"
    ai_task_ready: bool = False
    extraction_confidence: float = 0.0
    requires_human_mapping: bool = True
    evidence_coverage_percent: int = 0
    revision_thread_count: int = 0
    risk_count: int = 0
    text_preview: str = ""
    source_refs: List[str] = Field(default_factory=list)


class WritingTableSummary(WorkbenchModel):
    table_id: str
    source_document_id: str
    table_index: int
    source_locator: str
    title_hint: str = ""
    row_count: int = 0
    column_count: int = 0
    nonempty_cell_count: int = 0
    merge_detected: bool = False
    headers: List[str] = Field(default_factory=list)
    role_hint: str = ""
    parser_status: str = "parsed"
    linked_section_id: str = ""
    quality_notes: List[str] = Field(default_factory=list)


class WritingQualityGate(WorkbenchModel):
    gate_id: str
    gate_label: str
    status: str
    owner: str
    detail: str
    source_refs: List[str] = Field(default_factory=list)


class WritingSourcePackageSummary(WorkbenchModel):
    package_id: str
    package_label: str
    project_code: str
    indication: str
    source_root_label: str
    package_role: str
    source_span_count: int = 0
    evidence_coverage_percent: int = 0
    revision_thread_count: int = 0
    pending_medical_approval_count: int = 0
    blocking_gate_count: int = 0
    can_generate_review_docx: bool = False
    formal_export_status: str = "不可生成正式导出包"
    ai_revision_boundary: str = "AI 修订建议是待医学批准的正式内容候选；独立模型未接入前不可生成生产写作结论。"
    documents: List[WritingSourceDocumentSummary] = Field(default_factory=list)
    sections: List[WritingSectionSummary] = Field(default_factory=list)
    tables: List[WritingTableSummary] = Field(default_factory=list)
    quality_gates: List[WritingQualityGate] = Field(default_factory=list)
    parser_warnings: List[str] = Field(default_factory=list)


class MedicalWritingManifestResult(WorkbenchModel):
    project_id: str
    module: str = "medical_writing"
    module_label: str = "医学写作"
    generated_at: datetime
    package_count: int = 0
    total_documents: int = 0
    total_sections: int = 0
    total_tables: int = 0
    total_source_spans: int = 0
    quality_gate_count: int = 0
    packages: List[WritingSourcePackageSummary] = Field(default_factory=list)
    parser_notes: List[str] = Field(default_factory=list)


class ModuleStatus(WorkbenchModel):
    module: str
    label: str
    status: str
    completion_rate: float
    open_risk_count: int
    pending_task_count: int
    pending_approval_count: int


class DashboardSummary(WorkbenchModel):
    project: Project
    modules: List[ModuleStatus]
    latest_batch: Optional[DataBatch]
    risk_counts_by_severity: Dict[str, int]
    pending_approvals: List[ApprovalGate]
    recent_risks: List[RiskCase]
