const HASH = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
const HASH_2 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
const BACKEND_CONTRACT_SCHEMA = "medical-monitoring-r5-exact-contract-v0.3.1";
const BACKEND_CONTRACT_SHA256 = "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6";
const RECEIPT_ID = "r5:receipt:synthetic-project-r5-s7:synthetic-snapshot-r5-20260820";

export const WORKSPACE_SYNTHETIC_IDENTITY = Object.freeze({
  tenant_id: "synthetic-tenant-r5",
  project_ref: "synthetic-project-r5-s7",
  run_ref: "synthetic-run-r5-20260820",
  snapshot_ref: "synthetic-snapshot-r5-20260820",
  cutoff_state: "present",
  cutoff_ref: "2026-08-20",
  site_ref: null,
  subject_ref: null,
  risk_ref: null,
  risk_instance_ref: null,
  spine_ref: null,
  view: "overview",
  axis_mode: "calendar",
  window_start: null,
  window_end: null,
  visit_ref: null,
  event_ref: null,
  risk_anchor_ref: null,
  source_locator_ref: null,
  target_projection_content_hash: HASH,
  return_context_key: "synthetic-return-overview",
  authority_hash: HASH_2,
  source_snapshot_sha256: HASH,
  response_snapshot_sha256: "fbbb7b89456674e5680601fd068a6648a6bc98c898e2ff4388b5508eba52c2b3",
  principal_identity_hash: HASH,
  authorization_decision_sha256: HASH_2,
  audit_id: "synthetic-audit-r5-overview",
});

const DOMAIN_ENCODINGS = Object.freeze([
  { domain: "ae", event_shape: "rounded_rect", line_style: "solid", short_label_zh: "AE" },
  { domain: "mh", event_shape: "bookmark", line_style: "dot_dash", short_label_zh: "MH" },
  { domain: "cm", event_shape: "capsule", line_style: "solid", short_label_zh: "合并用药" },
  { domain: "ip", event_shape: "hexagon", line_style: "step", short_label_zh: "试验药" },
  { domain: "lab_exam", event_shape: "square", line_style: "trend", short_label_zh: "检验/检查" },
  { domain: "hospital_procedure", event_shape: "doorframe", line_style: "solid", short_label_zh: "住院/操作" },
  { domain: "symptom_efficacy", event_shape: "circle", line_style: "trend", short_label_zh: "症状/疗效" },
  { domain: "protocol_compliance", event_shape: "single_flag", line_style: "bracket", short_label_zh: "方案符合" },
  { domain: "uncategorized", event_shape: "circle", line_style: "dot_dash", short_label_zh: "未分类" },
]);

function domainEncoding(domain) {
  return DOMAIN_ENCODINGS.find((value) => value.domain === domain);
}

const RISK_ROWS = Object.freeze([
  {
    risk_ref: "synthetic-risk-ae-01",
    risk_instance_ref: "synthetic-risk-instance-ae-01",
    risk_key: "synthetic-risk-key-ae-01",
    site_ref: "synthetic-site-01",
    subject_ref: "synthetic-subject-001",
    spine_ref: "synthetic-spine-001",
    domain: "ae",
    severity: "high",
    severity_zh: "高",
    risk_type_zh: "不良事件记录需核对",
    subject_label: "受试者 001",
    date_state: "exact",
    change_kind: "new",
    change_cause: "data",
    event_ref: "synthetic-event-ae-01",
    visit_ref: "synthetic-visit-04",
    risk_anchor_ref: "synthetic-anchor-ae-01",
    source_locator_ref: "synthetic-locator-ae-01",
    source_locator_refs: ["synthetic-locator-ae-01"],
    authority_receipt_ref: RECEIPT_ID,
  },
  {
    risk_ref: "synthetic-risk-lab-01",
    risk_instance_ref: "synthetic-risk-instance-lab-01",
    risk_key: "synthetic-risk-key-lab-01",
    site_ref: "synthetic-site-02",
    subject_ref: "synthetic-subject-002",
    spine_ref: "synthetic-spine-002",
    domain: "lab_exam",
    severity: "medium",
    severity_zh: "中",
    risk_type_zh: "检验趋势需结合访视核对",
    subject_label: "受试者 002",
    date_state: "partial",
    change_kind: "continued",
    change_cause: "coverage",
    event_ref: "synthetic-event-lab-01",
    visit_ref: "synthetic-visit-04",
    risk_anchor_ref: "synthetic-anchor-lab-01",
    source_locator_ref: "synthetic-locator-lab-01",
    source_locator_refs: ["synthetic-locator-lab-01"],
    authority_receipt_ref: RECEIPT_ID,
  },
]);

function sourceRef(locatorRef, excerpt = null) {
  const source = {
    locator_ref: locatorRef,
    snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref,
    source_file_ref: `synthetic-file-${locatorRef}`,
    source_revision_ref: `synthetic-revision-${locatorRef}`,
    source_revision_content_hash: HASH,
    record_ref: `synthetic-record-${locatorRef}`,
    canonical_location: `synthetic-location:${locatorRef}`,
    lineage: [`synthetic-lineage-${locatorRef}`],
  };
  if (excerpt !== null) source.excerpt = excerpt;
  return source;
}

function envelope(identity, projection, counts = {}, sourceRefs = []) {
  const evidence = identity.view === "evidence";
  const surface = evidence ? "r5_source_evidence" : identity.view === "journey" ? "r5_subject_workspace" : "r5_overview";
  const action = evidence ? "read_source_evidence" : "read_monitoring";
  return {
    schema: "medical-monitoring-r5-s7-product-read-model-v0.1",
    contract_schema: BACKEND_CONTRACT_SCHEMA,
    contract_sha256: BACKEND_CONTRACT_SHA256,
    authority_receipt: {
      receipt_id: RECEIPT_ID,
      authority_contract_id: "r5-authority-receipt-kind-v1",
      authority_contract_version: "2026-08-26.1",
      audience_contract_id: "medical-monitoring-r5-exact-contract-v0.3.1",
      project_ref: identity.project_ref,
      run_ref: identity.run_ref,
      snapshot_ref: identity.snapshot_ref,
      cutoff_state: identity.cutoff_state,
      cutoff_ref: identity.cutoff_ref,
      authority_hash: identity.authority_hash,
      source_snapshot_sha256: identity.source_snapshot_sha256,
      visibility_decision_id: "synthetic-visibility-r5",
      visibility_decision_hash: HASH_2,
      evaluation_content_identities: [HASH],
      source_revision_content_pairs: [{ revision_id: "synthetic-revision-r5", content_hash: HASH, locator_refs: sourceRefs.map((source) => source.locator_ref) }],
      projectable: true,
      synthetic: true,
      data_mode: "synthetic_fixture",
    },
    identity,
    projection: { ...projection, content_hash: identity.target_projection_content_hash },
    counts,
    source_refs: sourceRefs,
    response_snapshot_sha256: identity.response_snapshot_sha256,
    read_handoff: {
      schema_version: "monitoring_read_action_contract_v1",
      surface,
      action,
      tenant_id: identity.tenant_id,
      project_id: identity.project_ref,
      principal_id: "synthetic-principal-r5",
      principal_identity_hash: identity.principal_identity_hash,
      request_id: "synthetic-request-r5",
      audit_id: identity.audit_id,
      authorization_decision_sha256: identity.authorization_decision_sha256,
      source_snapshot_sha256: identity.source_snapshot_sha256,
      read_only: true,
      persisted: false,
      mutation_applied: false,
      idempotency_key_sha256: HASH,
      cas_version: 7,
      route_context: {
        schema_version: "monitoring_runtime_route_context_v1",
        tenant_id: identity.tenant_id,
        project_id: identity.project_ref,
        principal_id: "synthetic-principal-r5",
        principal_identity_hash: identity.principal_identity_hash,
        validated_at: "2026-08-20T00:00:00+00:00",
      },
      audit_event_hash: HASH_2,
      contract_sha256: HASH_2,
      response_snapshot_sha256: identity.response_snapshot_sha256,
    },
    read_only: true,
    mutation_applied: false,
    persisted: false,
    aggregate_version_before: 7,
    aggregate_version_after: 7,
  };
}

export const WORKSPACE_SYNTHETIC_OVERVIEW = Object.freeze(envelope(
  WORKSPACE_SYNTHETIC_IDENTITY,
  {
    kind: "project_cockpit",
    project: {
      project_ref: WORKSPACE_SYNTHETIC_IDENTITY.project_ref,
      project_code: "S7-SYNTH",
      project_label: "医学监查示范项目",
      indication: "示范适应症",
      phase: "III期",
    },
    coverage: {
      coverage_state: "complete",
      numerator: 24,
      denominator: 24,
      label: "24/24 受试者",
    },
    change_bands: [
      { risk_ref: RISK_ROWS[0].risk_ref, change_kind: "new", change_cause: "data", prior_snapshot_ref: null, current_snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref, authority_receipt_ref: RECEIPT_ID },
      { risk_ref: RISK_ROWS[1].risk_ref, change_kind: "continued", change_cause: "coverage", prior_snapshot_ref: null, current_snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref, authority_receipt_ref: RECEIPT_ID },
    ],
    current_risks: RISK_ROWS,
    current_risk_set: {
      high_risk_refs: [RISK_ROWS[0].risk_ref],
      medium_risk_refs: [RISK_ROWS[1].risk_ref],
      low_risk_cluster_refs: [],
      resolved_history_refs: [],
      authority_receipt_ref: RECEIPT_ID,
      content_hash: HASH,
    },
    center_map: {
      stable_site_order: ["synthetic-site-01", "synthetic-site-02"],
      cells: [
        {
          site_ref: "synthetic-site-01",
          domain: "ae",
          severity: "high",
          pattern_refs: ["synthetic-pattern-site-01"],
          individual_risk_refs: [RISK_ROWS[0].risk_ref],
          measure_refs: ["synthetic-measure-site-01"],
        },
        {
          site_ref: "synthetic-site-02",
          domain: "lab_exam",
          severity: "medium",
          pattern_refs: ["synthetic-pattern-site-02"],
          individual_risk_refs: [RISK_ROWS[1].risk_ref],
          measure_refs: ["synthetic-measure-site-02"],
        },
      ],
      projection_instance: { opaque_run_ref: WORKSPACE_SYNTHETIC_IDENTITY.run_ref, opaque_snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref, replay_content_identity: HASH, authority_receipt_ref: RECEIPT_ID },
      content_hash: HASH,
    },
    measures: [
      { measure_ref: "synthetic-measure-site-01", site_ref: "synthetic-site-01", numerator: 1, denominator: 8, denominator_state: "closed_positive", rate_state: "closed", coverage_state: "complete", cutoff_ref: WORKSPACE_SYNTHETIC_IDENTITY.cutoff_ref, authority_receipt_ref: RECEIPT_ID },
      { measure_ref: "synthetic-measure-site-02", site_ref: "synthetic-site-02", numerator: 1, denominator: 7, denominator_state: "closed_positive", rate_state: "closed", coverage_state: "partial", cutoff_ref: WORKSPACE_SYNTHETIC_IDENTITY.cutoff_ref, authority_receipt_ref: RECEIPT_ID },
    ],
    subjects: [
      { subject_ref: "synthetic-subject-001", subject_id: "synthetic-subject-001", site_ref: "synthetic-site-01", spine_ref: "synthetic-spine-001", label: "受试者 001", subject_label: "受试者 001", authority_receipt_ref: RECEIPT_ID },
      { subject_ref: "synthetic-subject-002", subject_id: "synthetic-subject-002", site_ref: "synthetic-site-02", spine_ref: "synthetic-spine-002", label: "受试者 002", subject_label: "受试者 002", authority_receipt_ref: RECEIPT_ID },
    ],
    domain_encoding: DOMAIN_ENCODINGS,
  },
  { current_risk: { critical: 0, high: 1, medium: 1, low: 0, total: 2 }, change_band_count: 2, affected_subject: 2, center_pattern: 2, individual_risk: 2, project_signal: 2 },
  [sourceRef(RISK_ROWS[0].source_locator_ref), sourceRef(RISK_ROWS[1].source_locator_ref)],
));

export const WORKSPACE_SYNTHETIC_SITE_OVERVIEW = Object.freeze({
  ...WORKSPACE_SYNTHETIC_OVERVIEW,
  identity: {
    ...WORKSPACE_SYNTHETIC_OVERVIEW.identity,
    site_ref: "synthetic-site-01",
    response_snapshot_sha256: "06aec51700bc7d19c78bdf1573c1f32c15260a339c5ff37ca426549ad840cbe7",
  },
  response_snapshot_sha256: "06aec51700bc7d19c78bdf1573c1f32c15260a339c5ff37ca426549ad840cbe7",
  read_handoff: {
    ...WORKSPACE_SYNTHETIC_OVERVIEW.read_handoff,
    response_snapshot_sha256: "06aec51700bc7d19c78bdf1573c1f32c15260a339c5ff37ca426549ad840cbe7",
  },
});

const SUBJECT_IDENTITY = Object.freeze({
  ...WORKSPACE_SYNTHETIC_IDENTITY,
  site_ref: "synthetic-site-01",
  subject_ref: "synthetic-subject-001",
  spine_ref: "synthetic-spine-001",
  view: "journey",
  window_start: "2026-01-01",
  window_end: "2026-08-20",
  return_context_key: "synthetic-return-subject-001",
  target_projection_content_hash: HASH_2,
  response_snapshot_sha256: "b91d56fc038aa8b67af57e3a7aa97024d97b07bd379e0635de8552433e44c8a5",
  risk_ref: "synthetic-risk-ae-01",
  risk_instance_ref: "synthetic-risk-instance-ae-01",
  risk_anchor_ref: "synthetic-anchor-ae-01",
  event_ref: "synthetic-event-ae-01",
  visit_ref: "synthetic-visit-04",
});

export const WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE = Object.freeze(envelope(
  SUBJECT_IDENTITY,
  {
    kind: "subject_workspace",
    project: WORKSPACE_SYNTHETIC_OVERVIEW.projection.project,
    workspace_state: {
      active_view: "journey",
      axis_mode: "calendar",
      subject_ref: SUBJECT_IDENTITY.subject_ref,
      spine_ref: SUBJECT_IDENTITY.spine_ref,
      window_start: SUBJECT_IDENTITY.window_start,
      window_end: SUBJECT_IDENTITY.window_end,
      content_hash: HASH,
    },
    temporal_spine: {
      spine_ref: SUBJECT_IDENTITY.spine_ref,
      axis_mode: "calendar",
      window_start: SUBJECT_IDENTITY.window_start,
      window_end: SUBJECT_IDENTITY.window_end,
      event_refs: ["synthetic-event-ae-01", "synthetic-event-mh-01", "synthetic-event-ip-01", "synthetic-event-lab-01"],
      visit_refs: ["synthetic-visit-01", "synthetic-visit-04", "synthetic-visit-06"],
      pending_date_refs: ["synthetic-event-mh-01"],
      phase_band_refs: [],
      visits: [
        { visit_ref: "synthetic-visit-01", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, visit_kind: "actual", actual_date: "2026-01-10", nominal_date: "2026-01-10", date_state: "exact", phase_ref: "synthetic-phase-screening", source_locator_refs: ["synthetic-locator-ip-01"] },
        { visit_ref: "synthetic-visit-04", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, visit_kind: "actual", actual_date: "2026-04-10", nominal_date: "2026-04-10", date_state: "exact", phase_ref: "synthetic-phase-treatment", source_locator_refs: ["synthetic-locator-ae-01", "synthetic-locator-lab-01"] },
        { visit_ref: "synthetic-visit-06", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, visit_kind: "actual", actual_date: null, nominal_date: "2026-06-10", date_state: "missing", phase_ref: null, source_locator_refs: ["synthetic-locator-mh-01"] },
      ],
      pending_dates: [{ item_ref: "synthetic-event-mh-01", item_kind: "event", domain: "mh", date_state: "missing", candidate_date_refs: ["synthetic-date-candidate-01"], source_locator_refs: ["synthetic-locator-mh-01"] }],
      content_hash: HASH,
    },
    events: [
      { event_ref: "synthetic-event-ae-01", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, domain: "ae", encoding: domainEncoding("ae"), subtype: "ae", start_date: "2026-04-11", end_date: "2026-04-13", visit_ref: "synthetic-visit-04", date_state: "exact", label_zh: "头痛记录", risk_anchor_refs: ["synthetic-anchor-ae-01"], source_locator_refs: ["synthetic-locator-ae-01"], risk_overlay_shape: "double_chevron_badge" },
      { event_ref: "synthetic-event-mh-01", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, domain: "mh", encoding: domainEncoding("mh"), subtype: "mh", start_date: null, end_date: null, visit_ref: null, date_state: "missing", label_zh: "既往病史后续记录", risk_anchor_refs: [], source_locator_refs: ["synthetic-locator-mh-01"], risk_overlay_shape: "double_chevron_badge" },
      { event_ref: "synthetic-event-ip-01", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, domain: "ip", encoding: domainEncoding("ip"), subtype: "ip_dose", start_date: "2026-01-12", end_date: "2026-04-01", visit_ref: "synthetic-visit-01", date_state: "exact", label_zh: "试验药给药", risk_anchor_refs: [], source_locator_refs: ["synthetic-locator-ip-01"], risk_overlay_shape: "double_chevron_badge" },
      { event_ref: "synthetic-event-lab-01", subject_ref: SUBJECT_IDENTITY.subject_ref, site_ref: SUBJECT_IDENTITY.site_ref, spine_ref: SUBJECT_IDENTITY.spine_ref, domain: "lab_exam", encoding: domainEncoding("lab_exam"), subtype: "lab", start_date: "2026-04-10", end_date: "2026-04-10", visit_ref: "synthetic-visit-04", date_state: "exact", label_zh: "实验室检查", risk_anchor_refs: ["synthetic-anchor-lab-01"], source_locator_refs: ["synthetic-locator-lab-01"], risk_overlay_shape: "double_chevron_badge" },
    ],
    current_risks: [RISK_ROWS[0], RISK_ROWS[1]],
    risk_anchors: [RISK_ROWS[0], RISK_ROWS[1]],
    domain_tracks: DOMAIN_ENCODINGS.map((encoding) => ({ domain: encoding.domain, event_refs: [], risk_anchor_refs: [], encoding })),
    indicators: [
      { indicator_ref: "synthetic-indicator-1", label: "症状评分", unit: "分", value_kind: "authority_record_count", points: [{ point_ref: "synthetic-indicator-1:point:001", date: "2026-01-10", date_state: "exact", value: 3, record_refs: [], source_locator_refs: [], authority_receipt_ref: RECEIPT_ID }, { point_ref: "synthetic-indicator-1:point:002", date: "2026-04-10", date_state: "exact", value: 5, record_refs: [], source_locator_refs: [], authority_receipt_ref: RECEIPT_ID }], authority_receipt_ref: RECEIPT_ID },
      { indicator_ref: "synthetic-indicator-2", label: "检验指标", unit: "单位", value_kind: "authority_record_count", points: [{ point_ref: "synthetic-indicator-2:point:001", date: "2026-01-10", date_state: "exact", value: 12, record_refs: [], source_locator_refs: [], authority_receipt_ref: RECEIPT_ID }, { point_ref: "synthetic-indicator-2:point:002", date: "2026-04-10", date_state: "exact", value: 15, record_refs: [], source_locator_refs: [], authority_receipt_ref: RECEIPT_ID }], authority_receipt_ref: RECEIPT_ID },
    ],
    aemh_match_history: [
      { candidate_ref: "synthetic-aemh-01", later_fact_ref: "synthetic-later-record-01", event_kind: "reappeared", match_state: "ambiguous", from_snapshot_ref: "synthetic-snapshot-r5-prior", to_snapshot_ref: SUBJECT_IDENTITY.snapshot_ref, identity_evidence_refs: ["synthetic-locator-mh-01"] },
    ],
  },
  { current_risk: { critical: 0, high: 1, medium: 1, low: 0, total: 2 }, event: 4, affected_subject: 1, individual_risk: 2, risk_anchor: 2 },
  [sourceRef("synthetic-locator-ae-01"), sourceRef("synthetic-locator-mh-01"), sourceRef("synthetic-locator-ip-01"), sourceRef("synthetic-locator-lab-01")],
));

const EVIDENCE_IDENTITY = Object.freeze({
  ...SUBJECT_IDENTITY,
  view: "evidence",
  source_locator_ref: "synthetic-locator-ae-01",
  return_context_key: "synthetic-return-evidence-01",
  response_snapshot_sha256: "d4d5a95124265fc9545f2cf45713c484b09bd8d1aefb98c891aff5d7057d3b61",
});

export const WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE = Object.freeze(envelope(
  EVIDENCE_IDENTITY,
  {
    kind: "source_evidence",
    risk_ref: RISK_ROWS[0].risk_ref,
    risk_instance_ref: RISK_ROWS[0].risk_instance_ref,
    source_locator_ref: EVIDENCE_IDENTITY.source_locator_ref,
    evidence: {
      excerpt: "此处为隔离示范来源片段，用于验证精确定位与返回上下文。",
      record_ref: "synthetic-record-synthetic-locator-ae-01",
      canonical_location: "synthetic-location:synthetic-locator-ae-01",
      lineage: ["synthetic-lineage-synthetic-locator-ae-01"],
      source_revision_ref: "synthetic-revision-synthetic-locator-ae-01",
      source_revision_content_hash: HASH,
    },
    authority_receipt_ref: RECEIPT_ID,
  },
  { current_risk: { critical: 0, high: 1, medium: 0, low: 0, total: 1 }, source_locator: 1, project_signal: 1 },
  [sourceRef(EVIDENCE_IDENTITY.source_locator_ref, "此处为隔离示范来源片段，用于验证精确定位与返回上下文。")],
));

export const WORKSPACE_SYNTHETIC_IDENTITY_NEGATIVE = Object.freeze({
  ...WORKSPACE_SYNTHETIC_OVERVIEW,
  identity: {
    ...WORKSPACE_SYNTHETIC_OVERVIEW.identity,
    project_ref: "synthetic-project-other",
    response_snapshot_sha256: "f04ab0dd28d45dc2fbc5fe5bf6739be51bf2f6929692fc483ed40503936cdda3",
  },
  response_snapshot_sha256: "f04ab0dd28d45dc2fbc5fe5bf6739be51bf2f6929692fc483ed40503936cdda3",
  read_handoff: {
    ...WORKSPACE_SYNTHETIC_OVERVIEW.read_handoff,
    response_snapshot_sha256: "f04ab0dd28d45dc2fbc5fe5bf6739be51bf2f6929692fc483ed40503936cdda3",
  },
});

export const medicalMonitoringWorkspaceSyntheticDomains = DOMAIN_ENCODINGS;

// ---------------------------------------------------------------------------
// Slice-07B 受试者阶段流向 synthetic fixtures。
// 12 人守恒示例（合同 §7）：12 进入、筛选失败 2、治疗中 5、完成 3、永久停药 2；
// 入口 12，当前停留合计 12，各节点 reached = current + outbound。
// ---------------------------------------------------------------------------

const FLOW_STAGE_ROWS = Object.freeze([
  { stage_ref: "flow-stage-consent", stage_label: "已签署知情同意", column_order: 0, row_order: 0, stage_kind: "main", is_entry: true, is_terminal: false, reached_count: 12, current_count: 0, mid_high_risk_count: 0, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-screening", stage_label: "筛选", column_order: 1, row_order: 0, stage_kind: "main", is_entry: false, is_terminal: false, reached_count: 12, current_count: 0, mid_high_risk_count: 0, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-enrolled", stage_label: "入组/随机", column_order: 2, row_order: 0, stage_kind: "main", is_entry: false, is_terminal: false, reached_count: 10, current_count: 0, mid_high_risk_count: 0, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-screen-fail", stage_label: "筛选失败", column_order: 2, row_order: 1, stage_kind: "branch_terminal", is_entry: false, is_terminal: true, reached_count: 2, current_count: 2, mid_high_risk_count: 1, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-treatment", stage_label: "治疗", column_order: 3, row_order: 0, stage_kind: "main", is_entry: false, is_terminal: false, reached_count: 10, current_count: 5, mid_high_risk_count: 2, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-completed", stage_label: "完成研究", column_order: 4, row_order: 0, stage_kind: "branch_terminal", is_entry: false, is_terminal: true, reached_count: 3, current_count: 3, mid_high_risk_count: 0, source_locator_refs: ["synthetic-locator-flow-01"] },
  { stage_ref: "flow-stage-withdrawn", stage_label: "永久停药", column_order: 4, row_order: 1, stage_kind: "branch_terminal", is_entry: false, is_terminal: true, reached_count: 2, current_count: 2, mid_high_risk_count: 1, source_locator_refs: ["synthetic-locator-flow-01"] },
]);

const FLOW_LINK_ROWS = Object.freeze([
  { link_ref: "flow-link-01", from_stage_ref: "flow-stage-consent", to_stage_ref: "flow-stage-screening", count: 12, mid_high_risk_count: 4 },
  { link_ref: "flow-link-02", from_stage_ref: "flow-stage-screening", to_stage_ref: "flow-stage-screen-fail", count: 2, mid_high_risk_count: 1 },
  { link_ref: "flow-link-03", from_stage_ref: "flow-stage-screening", to_stage_ref: "flow-stage-enrolled", count: 10, mid_high_risk_count: 3 },
  { link_ref: "flow-link-04", from_stage_ref: "flow-stage-enrolled", to_stage_ref: "flow-stage-treatment", count: 10, mid_high_risk_count: 3 },
  { link_ref: "flow-link-05", from_stage_ref: "flow-stage-treatment", to_stage_ref: "flow-stage-completed", count: 3, mid_high_risk_count: 0 },
  { link_ref: "flow-link-06", from_stage_ref: "flow-stage-treatment", to_stage_ref: "flow-stage-withdrawn", count: 2, mid_high_risk_count: 1 },
]);

const FLOW_JUMP_START = "2026-01-10";
const FLOW_JUMP_END = "2026-08-20";

function flowSubject(number, siteRef, siteLabel, pathRefs, currentRef, options = {}) {
  const subjectId = `synthetic-subject-${String(number).padStart(3, "0")}`;
  return {
    subject_ref: subjectId,
    subject_label: `受试者 ${String(number).padStart(3, "0")}`,
    site_ref: siteRef,
    site_label: siteLabel,
    spine_ref: `synthetic-spine-${String(number).padStart(3, "0")}`,
    path_stage_refs: pathRefs,
    current_stage_ref: currentRef,
    entered_date: options.enteredDate ?? "2026-06-01",
    basis_date: options.basisDate ?? options.enteredDate ?? "2026-06-01",
    date_state: options.dateState ?? "exact",
    transition_reason_zh: options.reason ?? "随机化后开始治疗",
    stage_change_kind: options.stageChange ?? "initial",
    risk_change_kind: options.riskChange ?? "",
    path_state: "complete",
    mid_high_risk: Boolean(options.riskSummary),
    risk_summary_zh: options.riskSummary ?? "",
    jump_window_start: options.noJump ? "" : FLOW_JUMP_START,
    jump_window_end: options.noJump ? "" : FLOW_JUMP_END,
  };
}

const CONSENT_PATH = ["flow-stage-consent", "flow-stage-screening"];
const FAIL_PATH = [...CONSENT_PATH, "flow-stage-screen-fail"];
const TREAT_PATH = [...CONSENT_PATH, "flow-stage-enrolled", "flow-stage-treatment"];
const DONE_PATH = [...TREAT_PATH, "flow-stage-completed"];
const STOP_PATH = [...TREAT_PATH, "flow-stage-withdrawn"];

const FLOW_SUBJECT_ROWS = Object.freeze([
  flowSubject(1, "synthetic-site-01", "中心 1", FAIL_PATH, "flow-stage-screen-fail", { enteredDate: "2026-07-02", reason: "筛选失败：不符合入排标准", riskSummary: "高风险 · 不良事件需核对", riskChange: "new" }),
  flowSubject(2, "synthetic-site-01", "中心 1", FAIL_PATH, "flow-stage-screen-fail", { enteredDate: "2026-07-05", reason: "筛选失败：不符合入排标准" }),
  flowSubject(3, "synthetic-site-01", "中心 1", TREAT_PATH, "flow-stage-treatment", { enteredDate: "2026-06-20", dateState: "conflicted", reason: "随机化后开始治疗" }),
  flowSubject(4, "synthetic-site-01", "中心 1", TREAT_PATH, "flow-stage-treatment", { enteredDate: "2026-06-01" }),
  flowSubject(5, "synthetic-site-01", "中心 1", TREAT_PATH, "flow-stage-treatment", { enteredDate: "2026-06-11" }),
  flowSubject(6, "synthetic-site-01", "中心 1", TREAT_PATH, "flow-stage-treatment", { enteredDate: "2026-06-15", riskSummary: "中风险 · 检验趋势需结合访视核对", riskChange: "upgraded" }),
  flowSubject(7, "synthetic-site-01", "中心 1", TREAT_PATH, "flow-stage-treatment", { enteredDate: "2026-06-18", dateState: "partial", riskSummary: "中风险 · 合并用药需核对", riskChange: "continued" }),
  flowSubject(8, "synthetic-site-02", "中心 2", DONE_PATH, "flow-stage-completed", { enteredDate: "2026-07-21", reason: "完成研究访视" }),
  flowSubject(9, "synthetic-site-02", "中心 2", DONE_PATH, "flow-stage-completed", { enteredDate: "2026-07-25", reason: "完成研究访视", noJump: true }),
  flowSubject(10, "synthetic-site-02", "中心 2", DONE_PATH, "flow-stage-completed", { enteredDate: "2026-07-30", reason: "完成研究访视" }),
  flowSubject(11, "synthetic-site-02", "中心 2", STOP_PATH, "flow-stage-withdrawn", { enteredDate: "2026-08-02", reason: "研究者评估后永久停药" }),
  flowSubject(12, "synthetic-site-02", "中心 2", STOP_PATH, "flow-stage-withdrawn", { enteredDate: "2026-08-05", reason: "研究者评估后永久停药", riskSummary: "高风险 · 不良事件需核对", riskChange: "new" }),
]);

export const WORKSPACE_SYNTHETIC_SUBJECT_FLOW = Object.freeze({
  availability: "available",
  visual_kind: "path_throughput_sankey",
  scope: {
    project_ref: WORKSPACE_SYNTHETIC_IDENTITY.project_ref,
    run_ref: WORKSPACE_SYNTHETIC_IDENTITY.run_ref,
    snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref,
    cutoff_ref: WORKSPACE_SYNTHETIC_IDENTITY.cutoff_ref,
    site_ref: null,
  },
  stages: FLOW_STAGE_ROWS,
  links: FLOW_LINK_ROWS,
  subjects: FLOW_SUBJECT_ROWS,
  coverage: { complete_count: 12, partial_count: 0, conflicted_count: 0, not_provided_count: 0, not_applicable_count: 0 },
  reconciliation: { state: "matched", subject_total: 12, entry_total: 12, current_total: 12, detail_total: 12 },
});

export const WORKSPACE_SYNTHETIC_SUBJECT_FLOW_NOT_PROVIDED = Object.freeze({
  availability: "not_provided",
  reason_zh: "本次运行未提供阶段路径数据。",
  scope: {
    project_ref: WORKSPACE_SYNTHETIC_IDENTITY.project_ref,
    run_ref: WORKSPACE_SYNTHETIC_IDENTITY.run_ref,
    snapshot_ref: WORKSPACE_SYNTHETIC_IDENTITY.snapshot_ref,
    cutoff_ref: WORKSPACE_SYNTHETIC_IDENTITY.cutoff_ref,
    site_ref: null,
  },
  stages: [],
  links: [],
  subjects: [],
  reconciliation: { state: "not_applicable" },
});

export const WORKSPACE_SYNTHETIC_SUBJECT_FLOW_BLOCKED = Object.freeze({
  ...WORKSPACE_SYNTHETIC_SUBJECT_FLOW,
  reconciliation: { state: "blocked", subject_total: 12, entry_total: 12, current_total: 14, detail_total: 14, gap_zh: "筛选阶段到达人数与路径记录相差 2 条，无法核对。" },
});

export const WORKSPACE_SYNTHETIC_SUBJECT_FLOW_EMPTY = Object.freeze({
  ...WORKSPACE_SYNTHETIC_SUBJECT_FLOW,
  stages: FLOW_STAGE_ROWS.map((stage) => ({ ...stage, reached_count: 0, current_count: 0, mid_high_risk_count: 0 })),
  links: [],
  subjects: [],
  coverage: { complete_count: 0, partial_count: 0, conflicted_count: 0, not_provided_count: 0, not_applicable_count: 0 },
  reconciliation: { state: "matched", subject_total: 0, entry_total: 0, current_total: 0, detail_total: 0 },
});

function flowOverviewEnvelope(subjectFlow) {
  const envelope = {
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    identity: { ...WORKSPACE_SYNTHETIC_OVERVIEW.identity },
    projection: { ...WORKSPACE_SYNTHETIC_OVERVIEW.projection, subject_flow: subjectFlow },
    read_handoff: { ...WORKSPACE_SYNTHETIC_OVERVIEW.read_handoff },
  };
  const digest = {
    ready: "3edf3f9a45928c92ab7a7f25f2fa9cea5bcb6e25507d901a79ef830ce2bb5a04",
    not_provided: "41b34911fd3c1d919aa86f17a8d9202630c79a2199ee5b71e121be41b879dcf0",
    blocked: "ea6e09c6526f10742c0e61b0ab244bd095d07954e3bdb144a8f01bcabaaf040d",
    empty: "93f82f42a52b11d9752b881fab46d2c181e402d24992c063012fa352d5d1209e",
  }[subjectFlow.availability === "available" ? (subjectFlow.reconciliation?.state === "matched" ? (subjectFlow.subjects.length ? "ready" : "empty") : "blocked") : "not_provided"];
  envelope.response_snapshot_sha256 = digest;
  envelope.identity.response_snapshot_sha256 = digest;
  envelope.read_handoff.response_snapshot_sha256 = digest;
  return Object.freeze(envelope);
}

export const WORKSPACE_SYNTHETIC_FLOW_OVERVIEW = flowOverviewEnvelope(WORKSPACE_SYNTHETIC_SUBJECT_FLOW);
export const WORKSPACE_SYNTHETIC_FLOW_OVERVIEW_NOT_PROVIDED = flowOverviewEnvelope(WORKSPACE_SYNTHETIC_SUBJECT_FLOW_NOT_PROVIDED);
export const WORKSPACE_SYNTHETIC_FLOW_OVERVIEW_BLOCKED = flowOverviewEnvelope(WORKSPACE_SYNTHETIC_SUBJECT_FLOW_BLOCKED);
export const WORKSPACE_SYNTHETIC_FLOW_OVERVIEW_EMPTY = flowOverviewEnvelope(WORKSPACE_SYNTHETIC_SUBJECT_FLOW_EMPTY);
