import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createMedicalMonitoringR7ProductApi,
} from "./medicalMonitoringProductApi.mjs";
import {
  projectR7History,
  projectR7PublicProgress,
  projectR7PublicProgressError,
  projectR7PublicResultError,
  projectR7ResultContext,
  projectR7ResultEntry,
  projectR7SetupOptions,
  R7_OPTIONS_REFRESH_TEXT,
  verifyR7PublicResultEnvelope,
} from "./medicalMonitoringProductProjection.mjs";
import {
  projectR7ContinuityError,
  safeVerifyR7ContinuityEnvelope,
} from "./medicalMonitoringContinuityProjection.mjs";
import {
  r7ContinuityRowJourneyTarget,
  r7ContinuityRowSourceTarget,
} from "./medicalMonitoringContinuityFilter.mjs";
import { r7JourneyDrawerClosePatch } from "./medicalMonitoringJourneyChanges.mjs";
import { MedicalMonitoringContinuityPanel } from "./MedicalMonitoringContinuityPanel.jsx";
import {
  R7_RESULT_ACTION_TEXT,
  R7_WIZARD_STEPS,
  advanceR7WizardStep,
  buildR7PrepareAndStartPayload,
  createR7IdempotencyController,
  createR7WizardState,
  projectR7ProductState,
  projectR7WizardState,
  setR7WizardSelection,
} from "./medicalMonitoringProductState.mjs";
import { r7RefreshBackoffMs } from "./medicalMonitoringProgressProjection.mjs";
import { R7ProgressPanelView } from "./MedicalMonitoringProgressPanel.jsx";
import { routeStateForMedicalMonitoringR5View } from "./medicalMonitoringWorkspaceRouteState.mjs";
import "./medicalMonitoringProductLoop.css";

const PRODUCT_RESULT_SUBJECT_VIEWS = new Set(["journey", "profile", "timeline"]);
const PRODUCT_RESULT_VIEWS = new Set(["overview", "site_overview", "journey", "profile", "timeline", "evidence"]);
const PUBLIC_RESULT_LOCATORS = Object.freeze([
  "site_ref",
  "subject_ref",
  "spine_ref",
  "window_start",
  "window_end",
  "risk_instance_ref",
  "risk_anchor_ref",
  "visit_ref",
  "event_ref",
  "source_locator_ref",
]);
const SEVERITY_LABELS = Object.freeze({ critical: "紧急", high: "高", medium: "中", low: "低" });
const DATE_LABELS = Object.freeze({ exact: "精确日期", partial: "日期部分明确", conflicted: "日期存在冲突", missing: "日期待确认" });
const COVERAGE_LABELS = Object.freeze({
  complete: "完整",
  partial: "部分覆盖",
  truncated: "截断",
  small_sample: "样本量较小，暂不评价",
  unknown: "覆盖待确认",
  not_applicable: "不适用",
});
const CHANGE_LABELS = Object.freeze({
  initial_current: "当前",
  new: "新增",
  upgraded: "升级",
  continued: "持续",
  downgraded: "降级",
  resolved: "关闭",
  closed: "关闭",
  reopened: "重开",
  needs_rejudgment: "需重新判断",
  superseded: "被替代",
  not_comparable: "暂不可比较",
});
const CHANGE_CAUSE_LABELS = Object.freeze({
  data: "新增或修订数据",
  coverage: "数据覆盖范围变化",
  rule: "监查规则变化",
  manual: "人工补充条件",
});

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function clean(value, fallback = "") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value).trim() || fallback;
}

function publicErrorText(error, fallback) {
  const detail = error && typeof error === "object" ? error.detail : null;
  const code = clean(detail?.code || error?.code);
  if (code === "global_default_missing" || code === "invalid_snapshot") return R7_OPTIONS_REFRESH_TEXT;
  const message = clean(detail?.message || detail?.text || error?.message || (typeof error === "string" ? error : ""));
  return /[\u4e00-\u9fff]/u.test(message) ? message : fallback;
}

function publicRunTokenFrom(value) {
  if (!isRecord(value)) return "";
  const token = clean(value.public_run_token || value.publicRunToken);
  if (token) return token;
  return publicRunTokenFrom(value.detail);
}

function projectionView(routeView) {
  if (routeView === "site_overview") return "overview";
  if (PRODUCT_RESULT_SUBJECT_VIEWS.has(routeView)) return "journey";
  if (routeView === "evidence") return "evidence";
  return "overview";
}

function domainEncoding(value, domain = "") {
  const source = isRecord(value) ? value : {};
  return {
    domain: clean(source.domain, domain),
    shortLabel: clean(source.short_label_zh || source.shortLabel || source.short_label, clean(domain, "域待确认")),
    shape: clean(source.event_shape || source.shape, ""),
    lineStyle: clean(source.line_style || source.lineStyle, ""),
  };
}

function normalizeMeasure(value = {}) {
  const source = isRecord(value) ? value : {};
  const coverageState = clean(source.coverage_state || source.coverageState, "unknown");
  return {
    ...source,
    numerator: source.numerator_value ?? source.numerator ?? null,
    denominator: source.denominator_value ?? source.denominator ?? null,
    coverageState,
    coverageLabel: COVERAGE_LABELS[coverageState] || "覆盖待确认",
    unit: clean(source.unit, "受试者"),
  };
}

function normalizeRisk(value = {}, domains) {
  const source = isRecord(value) ? value : {};
  const riskRef = clean(source.risk_key || source.risk_ref);
  const riskInstanceRef = clean(source.risk_instance_ref || source.risk_instance_id);
  const domain = clean(source.domain);
  const severity = clean(source.severity, "");
  const dateState = clean(source.date_state, "missing");
  const changeKind = clean(source.change_kind, "");
  const encoding = isRecord(source.domain)
    ? domainEncoding(source.domain, domain)
    : domains.get(domain) || domainEncoding(null, domain);
  const sourceLocatorRefs = Array.isArray(source.source_locator_refs)
    ? source.source_locator_refs.map((item) => clean(item)).filter(Boolean)
    : [];
  return {
    ...source,
    riskRef,
    riskInstanceRef,
    siteRef: clean(source.site_ref || source.site_id),
    subjectRef: clean(source.subject_ref || source.subject_id),
    spineRef: clean(source.spine_ref),
    domain,
    domainEncoding: encoding,
    domainStatus: "confirmed",
    severity,
    severityLabel: SEVERITY_LABELS[severity] || "风险等级待确认",
    riskType: clean(source.risk_type_zh || source.risk_type || source.title, "风险提示"),
    subjectLabel: clean(source.subject_label || source.subject_name),
    siteLabel: clean(source.site_label || source.site_name),
    dateState,
    dateLabel: DATE_LABELS[dateState] || "日期待确认",
    changeKind,
    changeLabel: CHANGE_LABELS[changeKind] || "变化待确认",
    changeCauseLabel: CHANGE_CAUSE_LABELS[source.change_cause] || "变化原因待确认",
    eventRef: clean(source.event_ref),
    riskAnchorRef: clean(source.risk_anchor_ref),
    sourceLocatorRefs,
    sourceLocatorRef: clean(source.source_locator_ref || sourceLocatorRefs[0]),
    evidenceSummary: source.evidence_summary || null,
    analysisDisagreement: source.analysis_disagreement || null,
    riskStatus: "confirmed",
  };
}

function normalizeEvent(value = {}, domains) {
  const source = isRecord(value) ? value : {};
  const domain = clean(source.domain);
  const encoding = isRecord(source.encoding)
    ? domainEncoding(source.encoding, domain)
    : domains.get(domain) || domainEncoding(null, domain);
  const sourceLocatorRefs = Array.isArray(source.source_locator_refs)
    ? source.source_locator_refs.map((item) => clean(item)).filter(Boolean)
    : [];
  return {
    ...source,
    eventRef: clean(source.event_ref),
    domain,
    domainEncoding: encoding,
    subtype: clean(source.subtype, "event"),
    start: source.start ?? source.start_date ?? null,
    end: source.end ?? source.end_date ?? null,
    dateState: clean(source.date_state, "missing"),
    dateLabel: DATE_LABELS[source.date_state] || "日期待确认",
    riskAnchorRefs: Array.isArray(source.risk_anchor_refs) ? source.risk_anchor_refs.map((item) => clean(item)).filter(Boolean) : [],
    sourceLocatorRefs,
    eventLabel: clean(source.event_label || source.label_zh || source.label, "医学事件"),
  };
}

function normalizeIndicator(value = {}, index = 0) {
  const source = isRecord(value) ? value : {};
  const rawPoints = source.points ?? source.trend_points ?? source.values;
  const points = Array.isArray(rawPoints)
    ? rawPoints.map((point) => {
      const row = isRecord(point) ? point : {};
      return { ...row, date: clean(row.date || row.event_date || row.x), value: row.value ?? row.y ?? null };
    })
    : [];
  return {
    ...source,
    indicatorRef: clean(source.indicator_ref || source.metric_ref || source.id, `indicator-${index + 1}`),
    label: clean(source.label || source.label_zh || source.indicator_label, "指标待确认"),
    points,
  };
}

function normalizePublicR5Payload(resultContext) {
  const identity = isRecord(resultContext?.identity) ? resultContext.identity : {};
  const raw = isRecord(resultContext?.projection) ? resultContext.projection : {};
  const domainValues = raw.domain_encodings
    || raw.domain_encoding
    || raw.audience_encoding?.domain_items
    || raw.encoding_registry?.domain_items
    || (Array.isArray(raw.domain_tracks) ? raw.domain_tracks.map((track) => ({ ...(track.encoding || {}), domain: track.domain })) : []);
  const domains = Array.isArray(domainValues)
    ? domainValues.map((value) => domainEncoding(value, value?.domain)).filter((value) => value.domain)
    : [];
  const domainMap = new Map(domains.map((value) => [value.domain, value]));
  const currentRisks = (Array.isArray(raw.current_risks) ? raw.current_risks : []).map((value) => normalizeRisk(value, domainMap));
  const risksByRef = new Map(currentRisks.map((value) => [value.riskRef, value]));
  const measures = Array.isArray(raw.measures) ? raw.measures.map(normalizeMeasure) : [];
  const measuresByRef = new Map(measures.map((value) => [clean(value.measure_ref), value]));
  const centerValues = Array.isArray(raw.center_map)
    ? raw.center_map
    : Array.isArray(raw.center_map?.cells)
      ? raw.center_map.cells
      : Array.isArray(raw.centers)
        ? raw.centers
        : [];
  const centersBySite = new Map();
  for (const value of centerValues) {
    const source = isRecord(value) ? value : {};
    const siteRef = clean(source.site_ref || source.site_id);
    if (!siteRef) continue;
    const existing = centersBySite.get(siteRef) || {
      ...source,
      siteRef,
      siteLabel: clean(source.site_label || source.site_name, `中心 ${siteRef}`),
      measures: [],
      risks: [],
    };
    const cellMeasures = Array.isArray(source.measures)
      ? source.measures.map(normalizeMeasure)
      : Array.isArray(source.measure_refs)
        ? source.measure_refs.map((ref) => measuresByRef.get(clean(ref))).filter(Boolean)
        : [];
    const cellRisks = Array.isArray(source.risks)
      ? source.risks.map((risk) => normalizeRisk(risk, domainMap))
      : (Array.isArray(source.individual_risk_refs) ? source.individual_risk_refs.map((ref) => risksByRef.get(clean(ref))).filter(Boolean) : []);
    existing.measures.push(...cellMeasures);
    existing.risks.push(...cellRisks);
    existing.coverageState = clean(source.coverage_state || source.coverageState, existing.coverageState || "unknown");
    existing.coverageLabel = COVERAGE_LABELS[existing.coverageState] || "覆盖待确认";
    centersBySite.set(siteRef, existing);
  }
  const identityForR5 = {
    project_ref: clean(identity.project_ref),
    public_run_token: clean(identity.public_run_token),
    snapshot_token: clean(identity.snapshot_token),
    data_cutoff_text: clean(identity.data_cutoff_text),
    view: clean(identity.view),
  };
  for (const key of PUBLIC_RESULT_LOCATORS) {
    if (identity[key] !== undefined && identity[key] !== null && clean(identity[key])) identityForR5[key] = identity[key];
  }
  const temporal = isRecord(raw.temporal_spine) ? raw.temporal_spine : isRecord(raw.spine) ? raw.spine : {};
  const events = (Array.isArray(raw.events) ? raw.events : Array.isArray(temporal.events) ? temporal.events : [])
    .map((value) => normalizeEvent(value, domainMap));
  const visits = Array.isArray(raw.visits) ? raw.visits : Array.isArray(temporal.visits) ? temporal.visits : [];
  const pendingDates = raw.pending_dates ?? raw.date_pending_refs ?? temporal.pending_dates ?? [];
  const sourceEvidence = raw.source_evidence || raw.evidence || null;
  const normalizedSourceEvidence = isRecord(sourceEvidence)
    ? { ...sourceEvidence, sourceLocatorRef: clean(sourceEvidence.source_locator_ref || identity.source_locator_ref) }
    : null;
  const rawCounts = isRecord(raw.counts) ? raw.counts : {};
  const rawCurrentRisk = rawCounts.current_risk || rawCounts.currentRisk || {};
  const counts = Object.keys(rawCounts).length
    ? {
      ...rawCounts,
      currentRisk: rawCurrentRisk,
      changeBand: rawCounts.change_band_count ?? rawCounts.changeBand ?? null,
    }
    : {};
  return {
    publicResultContext: true,
    identity: identityForR5,
    result_context_token: resultContext.resultContextToken,
    counts,
    source_refs: Array.isArray(raw.source_refs) ? raw.source_refs : [],
    projection: {
      raw,
      project: raw.project || raw.project_identity || raw.project_summary || {},
      coverage: raw.coverage || raw.coverage_summary || {},
      cutoff: clean(raw.cutoff),
      changeBands: raw.change_bands || raw.changes || [],
      currentRisks,
      centers: [...centersBySite.values()].map((center) => ({
        ...center,
        risks: [...new Map(center.risks.map((risk) => [risk.riskInstanceRef || risk.riskRef, risk])).values()],
        measures: [...new Map(center.measures.map((measure) => [measure.measure_ref || `${center.siteRef}:${measure.numerator}:${measure.denominator}`, measure])).values()],
      })),
      domains,
      subjects: Array.isArray(raw.subjects) ? raw.subjects : Array.isArray(raw.subject_options) ? raw.subject_options : [],
      subjectFlow: raw.subject_flow || null,
      temporalSpine: {
        ...temporal,
        spineRef: clean(temporal.spine_ref || identity.spine_ref),
        axisMode: clean(temporal.axis_mode, "calendar"),
        windowStart: temporal.window_start ?? identity.window_start ?? null,
        windowEnd: temporal.window_end ?? identity.window_end ?? null,
        visits,
        pendingDates,
      },
      events,
      riskAnchors: Array.isArray(raw.risk_anchors) ? raw.risk_anchors.map((value) => normalizeRisk(value, domainMap)) : currentRisks,
      domainTracks: raw.domain_tracks || raw.tracks || [],
      indicators: raw.indicators === undefined && raw.trends === undefined && raw.metrics === undefined
        ? null
        : (raw.indicators || raw.trends || raw.indicator_trends || raw.metrics || []).map(normalizeIndicator),
      aemhHistory: raw.aemh_history || raw.aemh_match_history || raw.ae_mh_history || [],
      sourceEvidence: normalizedSourceEvidence,
      workspaceState: raw.workspace_state || raw.subject_workspace_state || {},
    },
  };
}
export { normalizePublicR5Payload };

function selectedSubjectWindow(payload, subject, route) {
  const flowRows = payload?.projection?.subjectFlow?.subjects || payload?.projection?.subjectFlow?.rows || [];
  const subjectRef = clean(subject?.subject_ref || subject?.subjectRef || subject?.subject_id);
  const flow = flowRows.find((row) => clean(row?.subject_ref || row?.subjectRef || row?.subject_id) === subjectRef) || {};
  const start = clean(route?.window_start || subject?.window_start || subject?.jump_window_start || flow?.window_start || flow?.jump_window_start || payload?.projection?.temporalSpine?.windowStart);
  const end = clean(route?.window_end || subject?.window_end || subject?.jump_window_end || flow?.window_end || flow?.jump_window_end || payload?.projection?.temporalSpine?.windowEnd);
  return { start, end };
}

function R7ProductWorkbar({ state, onAction, omitComparisonClaim = false }) {
  const workbar = state?.workbar;
  const selectedRun = state?.selectedRun;
  const details = selectedRun
    ? [
      selectedRun.dataCutoffText,
      omitComparisonClaim ? "" : selectedRun.comparisonRangeText,
    ].filter(Boolean).join(" · ")
    : "当前项目尚无已选择的监查记录";
  const invoke = (target) => {
    if (!target) return;
    onAction?.(target);
  };
  return (
    <section className="r7-product-workbar" data-r7-product-workbar data-r7-workbar-state={state?.kind || "loading"} aria-label="本次监查">
      <div className="r7-product-workbar-copy">
        <strong>{selectedRun?.modeText ? `${selectedRun.modeText}（本次）` : "医学监查工作区"}</strong>
        <small>{details}</small>
      </div>
      <div className="r7-product-workbar-actions" role="group" aria-label="本次监查操作">
        {workbar?.mainAction ? <button type="button" data-r7-workbar-main className="r7-product-button is-primary" onClick={() => invoke(workbar.mainTarget)}>{workbar.mainAction}</button> : null}
        {workbar?.secondaryAction ? <button type="button" data-r7-workbar-secondary className="r7-product-button" onClick={() => invoke(workbar.secondaryTarget)}>{workbar.secondaryAction}</button> : null}
        {workbar?.otherAction ? <button type="button" data-r7-workbar-other className="r7-product-button is-quiet" onClick={() => invoke(workbar.otherTarget)}>{workbar.otherAction}</button> : null}
      </div>
    </section>
  );
}

export { R7ProductWorkbar };

export function R7PublicResultIdentityStrip({ identity = {}, siteScopeText = "" }) {
  // Workbar already shows modeText; repeating it here reads as “日常监查 日常监查”.
  return (
    <aside className="r7-public-result-identity" data-r7-result-identity aria-label="本次结果范围">
      <strong>本次结果范围</strong>
      <span>数据截止 {clean(identity.data_cutoff_text || identity.dataCutoffText, "待确认")}</span>
      <span>{clean(siteScopeText || identity.site_scope_text || identity.siteScopeText, "中心范围待确认")}</span>
    </aside>
  );
}

export function R7HistoryDrawer({ history, selectedPublicRunToken = "", onSelect, onClose }) {
  const rows = Array.isArray(history?.rows) ? history.rows : [];
  return (
    <div className="r7-product-overlay" role="presentation">
      <aside className="r7-history-drawer" role="dialog" aria-modal="true" aria-label="监查历史" data-r7-history-drawer>
        <header className="r7-drawer-head">
          <div><span className="r5-eyebrow">监查记录</span><h2>历史</h2><p>按服务端顺序显示最近记录。</p></div>
          <button type="button" className="r7-icon-button" aria-label="关闭历史" onClick={onClose}>关闭</button>
        </header>
        <div className="r7-history-list">
          {rows.length === 0 ? <p className="r7-product-muted">尚无历史监查记录。</p> : null}
          {rows.map((row) => (
            <article className={`r7-history-row${row.publicRunToken === selectedPublicRunToken ? " is-selected" : ""}`} key={row.publicRunToken} data-public-run-token={row.publicRunToken}>
              <div className="r7-history-row-head"><strong>{row.modeText}</strong><span>{row.resultAvailable ? "结果可用" : "结果尚未整理"}</span></div>
              <p>{row.dataCutoffText}</p>
              <p>{row.comparisonRangeText}</p>
              <p className="r7-history-status">{row.statusText}</p>
              <button type="button" className="r7-product-button is-small" onClick={() => onSelect?.(row)}>{row.mainAction}</button>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

export function R7WizardView({
  wizard,
  previewText = "",
  previewBusy = false,
  previewOpen = false,
  onClose,
  onSelect,
  onAdvance,
  onPreviewTextChange,
  onPreview,
  onClosePreview,
  onConfirmPreview,
  canConfirmPreview = false,
}) {
  const step = Number.isInteger(wizard?.step) ? wizard.step : 1;
  const currentData = wizard?.currentData || {};
  const dataBatches = Array.isArray(wizard?.dataBatches) ? wizard.dataBatches : [];
  const selectedData = dataBatches.find((item) => item.snapshotToken === wizard?.currentSnapshotToken) || currentData;
  const selectedMode = wizard?.modeOptions?.find((item) => item.mode === wizard.mode);
  const preview = wizard?.preview;
  const candidates = Array.isArray(preview?.candidates) ? preview.candidates.slice(0, 5) : [];
  const setField = (field, value) => onSelect?.(field, value);
  return (
    <div className="r7-product-overlay" role="presentation">
      <section className="r7-product-dialog" role="dialog" aria-modal="true" aria-label="开始一次监查" data-r7-wizard data-r7-wizard-step={step}>
        <header className="r7-dialog-head">
          <div><span className="r5-eyebrow">本次监查</span><h2>开始一次监查</h2><p>在当前项目内确认监查方式、数据范围和特殊关注。</p></div>
          <button type="button" className="r7-icon-button" aria-label="关闭向导" onClick={onClose}>关闭</button>
        </header>
        <ol className="r7-wizard-steps" aria-label="监查设置步骤">
          {R7_WIZARD_STEPS.map((item) => <li key={item.key} className={item.number === step ? "is-active" : item.number < step ? "is-complete" : ""}><span>{item.number}</span><strong>{item.label}</strong></li>)}
        </ol>
        <div className="r7-wizard-body">
          {step === 1 ? (
            <section className="r7-wizard-section" aria-labelledby="r7-wizard-mode-heading">
              <div className="r7-wizard-section-head"><div><span className="r5-eyebrow">第 1 步</span><h3 id="r7-wizard-mode-heading">选择监查方式</h3></div><p>{wizard?.recommendationReason || ""}</p></div>
              <div className="r7-mode-grid">
                {(wizard?.modeOptions || []).map((mode) => (
                  <button type="button" key={mode.mode} className={`r7-mode-card${mode.mode === wizard.mode ? " is-selected" : ""}`} disabled={mode.available !== true} onClick={() => setField("mode", mode.mode)} data-mode={mode.mode}>
                    <span className="r7-mode-card-marker" aria-hidden="true" />
                    <strong>{mode.label || "监查方式"}</strong>
                    <p>{mode.description}</p>
                    {mode.recommended ? <small>服务端推荐：{mode.recommendationReason}</small> : null}
                    {mode.available !== true ? <small className="is-disabled">{mode.disabledReason || "当前不可用"}</small> : null}
                  </button>
                ))}
              </div>
            </section>
          ) : null}
          {step === 2 ? (
            <section className="r7-wizard-section" aria-labelledby="r7-wizard-scope-heading">
              <div className="r7-wizard-section-head"><div><span className="r5-eyebrow">第 2 步</span><h3 id="r7-wizard-scope-heading">确认数据范围</h3></div><p>{selectedMode?.description || ""}</p></div>
              {dataBatches.length > 1 ? <label className="r7-data-picker"><span>数据版本</span><select value={wizard.currentSnapshotToken} onChange={(event) => setField("currentSnapshotToken", event.target.value)}>{dataBatches.map((batch) => <option value={batch.snapshotToken} key={batch.snapshotToken}>{batch.dataCutoff || batch.snapshotToken} · {batch.scopeDescription || "数据范围"}</option>)}</select></label> : null}
              <dl className="r7-wizard-facts">
                <div><dt>当前数据</dt><dd>{selectedData.scopeDescription || "当前完整数据"}</dd></div>
                <div><dt>数据截止</dt><dd>{selectedData.dataCutoff || "待确认"}</dd></div>
                <div><dt>记录数量</dt><dd>{selectedData.rowCount ?? "待确认"}</dd></div>
              </dl>
              <fieldset className="r7-option-fieldset"><legend>执行基础</legend><div className="r7-choice-grid">{(wizard?.basisOptions || []).map((option) => <label key={option.value} className={`r7-choice-card${option.value === wizard.executionBasis ? " is-selected" : ""}`}><input type="radio" name="r7-execution-basis" value={option.value} checked={option.value === wizard.executionBasis} disabled={option.available !== true} onChange={() => setField("executionBasis", option.value)} /><span><strong>{option.label || "当前选项"}</strong>{option.disabledReason ? <small>{option.disabledReason}</small> : null}</span></label>)}</div></fieldset>
              {wizard.executionBasis === "incremental" ? <fieldset className="r7-option-fieldset"><legend>比较基线</legend><div className="r7-baseline-list">{(wizard?.baselineOptions || []).map((option) => <label key={option.baselineToken} className={`r7-baseline-row${option.baselineToken === wizard.baselineToken ? " is-selected" : ""}`}><input type="radio" name="r7-baseline" value={option.baselineToken} checked={option.baselineToken === wizard.baselineToken} disabled={option.selectable !== true} onChange={() => setField("baselineToken", option.baselineToken)} /><span><strong>{option.scopeDescription || option.modeText || "已发布基线"}</strong><small>{option.dataCutoff || "截止时间待确认"}{option.recommended ? " · 服务端推荐" : ""}</small></span>{option.selectable !== true ? <em>{"当前不可用"}</em> : null}</label>)}</div></fieldset> : null}
            </section>
          ) : null}
          {step === 3 ? (
            <section className="r7-wizard-section" aria-labelledby="r7-wizard-rules-heading">
              <div className="r7-wizard-section-head"><div><span className="r5-eyebrow">第 3 步</span><h3 id="r7-wizard-rules-heading">选择特殊关注</h3></div><p>沿用已确认的项目规则；取消选择不会删除项目规则。</p></div>
              <div className="r7-rule-list">{(wizard?.ruleRevisions || []).map((rule) => <label key={rule.revisionToken} className={`r7-rule-row${wizard.riskRuleTokens.includes(rule.revisionToken) ? " is-selected" : ""}`}><input type="checkbox" checked={wizard.riskRuleTokens.includes(rule.revisionToken)} onChange={(event) => setField("riskRuleTokens", event.target.checked ? [...wizard.riskRuleTokens, rule.revisionToken] : wizard.riskRuleTokens.filter((token) => token !== rule.revisionToken))} disabled={rule.selectable !== true} /><span><strong>{rule.summary}</strong><small>{rule.applicableScope} · {rule.startingRun}</small></span></label>)}</div>
              <button type="button" className="r7-product-button is-outline" onClick={onPreview}>增加特殊关注</button>
              {previewOpen ? <section className="r7-preview-panel" aria-label="增加特殊关注预览"><div className="r7-preview-head"><strong>增加特殊关注</strong><button type="button" className="r7-link-button" onClick={onClosePreview}>关闭预览</button></div><textarea rows={3} value={previewText} onChange={(event) => onPreviewTextChange?.(event.target.value)} placeholder="例如：关注感染、发热相关事件" /><div className="r7-preview-actions"><button type="button" className="r7-product-button is-small" disabled={previewBusy || !previewText.trim()} onClick={onPreview}>{previewBusy ? "正在生成" : "生成关注方向"}</button></div>{preview ? <div className="r7-preview-result"><p>{preview.reason || (preview.state === "ready" ? "请确认以下关注方向。" : "请选择一个关注方向后继续。")}</p>{candidates.map((candidate) => <label key={candidate.candidate_id} className={`r7-candidate-row${candidate.candidate_id === wizard.previewCandidateId ? " is-selected" : ""}`}><input type="radio" name="r7-preview-candidate" checked={candidate.candidate_id === wizard.previewCandidateId} onChange={() => setField("previewCandidateId", candidate.candidate_id)} /><span><strong>{candidate.subject}</strong><small>{candidate.condition}</small><em>{candidate.explanation}</em></span></label>)}{candidates.length > 0 ? <button type="button" className="r7-product-button is-small is-primary" disabled={!canConfirmPreview} onClick={onConfirmPreview}>确认并保存到项目</button> : null}</div> : null}</section> : null}
            </section>
          ) : null}
          {step === 4 ? (
            <section className="r7-wizard-section" aria-labelledby="r7-wizard-confirm-heading">
              <div className="r7-wizard-section-head"><div><span className="r5-eyebrow">第 4 步</span><h3 id="r7-wizard-confirm-heading">确认并开始</h3></div><p>开始后将进入本次监查进度；离开页面不会停止本次监查。</p></div>
              <dl className="r7-confirm-summary"><div><dt>监查方式</dt><dd>{wizard?.summary?.modeText || "待确认"}</dd></div><div><dt>数据范围</dt><dd>{wizard?.summary?.scopeDescription || currentData.scopeDescription || "待确认"}</dd></div><div><dt>数据截止</dt><dd>{wizard?.summary?.dataCutoffText || currentData.dataCutoff || "待确认"}</dd></div><div><dt>比较基线</dt><dd>{wizard?.summary?.comparisonRangeText || "不使用上次结果"}</dd></div><div><dt>中心数量</dt><dd>{wizard?.serverSummary?.centerCount ?? "开始后由服务端确认"}</dd></div><div><dt>受试者数量</dt><dd>{wizard?.serverSummary?.subjectCount ?? "开始后由服务端确认"}</dd></div><div><dt>特殊关注</dt><dd>{wizard?.summary?.selectedRuleCount ?? wizard?.riskRuleTokens?.length ?? 0} 项</dd></div><div><dt>工作项总数</dt><dd>{wizard?.serverSummary?.workItemCount ?? "开始后由服务端确认"}</dd></div></dl>
            </section>
          ) : null}
          {wizard?.errorText ? <p className="r7-wizard-error" role="alert">{wizard.errorText}</p> : null}
        </div>
        <footer className="r7-dialog-foot"><button type="button" className="r7-product-button is-quiet" onClick={step > 1 ? () => onAdvance?.(-1) : onClose}>{step > 1 ? "上一步" : "取消"}</button><button type="button" className="r7-product-button is-primary" onClick={() => onAdvance?.(1)}>{step === 4 ? "确认并开始监查" : "下一步"}</button></footer>
      </section>
    </div>
  );
}

export function R7PublicProgressSurface({ progress, error, loading = false, onRefresh, onBack, onOpenResult }) {
  const view = progress
    ? {
      ...progress,
      runStatusText: progress.publicationStatusText || progress.runStatusText,
      actions: [],
    }
    : null;
  const panel = {
    view,
    empty: !loading && !view && error && error.kind !== "forbidden" ? { text: error.text } : null,
    notice: error && (view || error.kind === "forbidden") ? { kind: error.kind, text: error.text } : null,
    actionsHidden: true,
    pendingAction: null,
    confirmStop: false,
  };
  return (
    <section className="r7-product-progress-surface" data-r7-public-progress>
      <R7ProgressPanelView panel={panel} onRefresh={onRefresh} />
      <div className="r7-progress-route-actions">
        {progress?.resultAvailable ? <button type="button" className="r7-product-button is-primary" onClick={onOpenResult}>{R7_RESULT_ACTION_TEXT}</button> : null}
        <button type="button" className="r7-product-button is-quiet" onClick={onBack}>返回项目风险概览</button>
      </div>
    </section>
  );
}

function ProductRouteTabs({ route, resultLoaded, onOverview }) {
  const resultToken = clean(route?.result_context_token);
  // URL may keep view=overview with site_ref; treat that as site_overview for chrome.
  const onSiteOverview = route?.view === "site_overview" || (route?.view === "overview" && Boolean(clean(route?.site_ref)));
  const onProjectOverview = route?.view === "overview" && !clean(route?.site_ref);
  return (
    <nav className="r7-product-route-tabs" aria-label="医学监查结果导航">
      {resultLoaded && onProjectOverview ? <button type="button" className="is-active" onClick={onOverview}>项目风险概览</button> : null}
      {resultLoaded && onSiteOverview ? <button type="button" className="is-back" onClick={onOverview}>返回项目风险概览</button> : null}
      {resultToken && !["overview", "site_overview"].includes(route.view) ? <button type="button" className="is-back" onClick={onOverview}>返回项目风险概览</button> : null}
    </nav>
  );
}
export function MedicalMonitoringProductLoop({
  projectId,
  route = {},
  onRouteChange,
  onReturn,
  OverviewView,
  SubjectWorkspaceView,
  EvidenceView,
  api: providedApi,
}) {
  const api = useMemo(() => providedApi || createMedicalMonitoringR7ProductApi(), [providedApi]);
  const [setup, setSetup] = useState(null);
  const [history, setHistory] = useState(null);
  const [setupHistoryLoading, setSetupHistoryLoading] = useState(true);
  const [setupHistoryError, setSetupHistoryError] = useState(null);
  const [refreshEpoch, setRefreshEpoch] = useState(0);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizard, setWizard] = useState(null);
  const [wizardError, setWizardError] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [ruleConfirmOpen, setRuleConfirmOpen] = useState(false);
  const [ruleConfirmBusy, setRuleConfirmBusy] = useState(false);
  const [progress, setProgress] = useState(null);
  const [progressLoading, setProgressLoading] = useState(false);
  const [progressError, setProgressError] = useState(null);
  const [resultContext, setResultContext] = useState(null);
  const [resultPayload, setResultPayload] = useState(null);
  const [resultLoading, setResultLoading] = useState(false);
  const [entryLoading, setEntryLoading] = useState(false);
  const [resultError, setResultError] = useState(null);
  const [resultRetryEpoch, setResultRetryEpoch] = useState(0);
  // Slice-08C-2 continuity read: never blocks the existing result boards.
  const [continuityResult, setContinuityResult] = useState(null);
  const [continuityLoading, setContinuityLoading] = useState(false);
  const idempotencyRef = useRef(null);
  const previousProgressAvailableRef = useRef(false);
  const normalizedProjectId = clean(projectId);
  const resultToken = clean(route.result_context_token);
  const publicRunToken = clean(route.public_run_token);
  const routeView = PRODUCT_RESULT_VIEWS.has(route.view)
    ? route.view === "overview" && route.site_ref ? "site_overview" : route.view
    : "overview";
  const productState = useMemo(() => projectR7ProductState({
    projectId: normalizedProjectId,
    options: setup,
    history,
    resultContext,
    selectedPublicRunToken: publicRunToken,
    selectedResultContextToken: resultToken,
    route,
    loading: setupHistoryLoading,
    error: setupHistoryError,
  }), [history, normalizedProjectId, publicRunToken, resultContext, resultToken, route, setup, setupHistoryError, setupHistoryLoading]);

  useEffect(() => {
    if (!normalizedProjectId) {
      setSetup(null);
      setHistory(null);
      setSetupHistoryLoading(false);
      setSetupHistoryError({ text: "当前项目无法确认，请返回项目概览。" });
      return undefined;
    }
    const controller = new AbortController();
    let cancelled = false;
    setSetup(null);
    setHistory(null);
    setSetupHistoryLoading(true);
    setSetupHistoryError(null);
    Promise.all([
      api.getSetupOptions(normalizedProjectId, { signal: controller.signal }),
      api.listRuns(normalizedProjectId, { signal: controller.signal }),
    ]).then(([setupPayload, historyPayload]) => {
      if (cancelled) return;
      const projectedSetup = projectR7SetupOptions(setupPayload, { projectId: normalizedProjectId });
      const nextHistory = projectR7History(historyPayload, { projectId: normalizedProjectId });
      if (projectedSetup?.kind === "invalid") throw new Error(projectedSetup.error || "监查范围响应暂不可用");
      if (nextHistory?.kind === "invalid") throw new Error(nextHistory.error || "监查历史响应暂不可用");
      const rawCurrentData = isRecord(setupPayload?.current_data) ? setupPayload.current_data : {};
      const serverSummary = {
        centerCount: setupPayload?.center_count ?? rawCurrentData.center_count ?? null,
        subjectCount: setupPayload?.subject_count ?? rawCurrentData.subject_count ?? null,
        workItemCount: setupPayload?.work_item_count ?? rawCurrentData.work_item_count ?? setupPayload?.total_work_units ?? rawCurrentData.total_work_units ?? null,
      };
      const nextSetup = { ...projectedSetup, serverSummary };
      setSetup(nextSetup);
      setHistory(nextHistory);
      setSetupHistoryLoading(false);
    }).catch((error) => {
      if (cancelled || error?.name === "AbortError") return;
      setSetup(null);
      setHistory(null);
      setSetupHistoryLoading(false);
      setSetupHistoryError({ text: publicErrorText(error, "监查范围暂不可用，请稍后重试。"), code: error?.code || "" });
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [api, normalizedProjectId, refreshEpoch]);

  useEffect(() => {
    if (!resultToken) {
      setResultContext(null);
      setResultPayload(null);
      setResultLoading(false);
      setResultError(null);
      return undefined;
    }
    const controller = new AbortController();
    let cancelled = false;
    setResultContext(null);
    setResultPayload(null);
    setResultLoading(true);
    setResultError(null);
    const expectedView = projectionView(routeView);
    let request;
    try {
      if (expectedView === "overview") {
        request = api.getResultOverview(normalizedProjectId, resultToken, { siteRef: route.site_ref, signal: controller.signal });
      } else if (expectedView === "evidence") {
        request = api.getResultSourceEvidence(normalizedProjectId, resultToken, {
          riskInstanceRef: route.risk_instance_ref,
          sourceLocatorRef: route.source_locator_ref,
          signal: controller.signal,
        });
      } else if (route.site_ref && route.subject_ref && route.spine_ref && route.window_start && route.window_end) {
        request = api.getResultSubject(normalizedProjectId, resultToken, route.subject_ref, {
          siteRef: route.site_ref,
          spineRef: route.spine_ref,
          windowStart: route.window_start,
          windowEnd: route.window_end,
          riskInstanceRef: route.risk_instance_ref,
          riskAnchorRef: route.risk_anchor_ref,
          visitRef: route.visit_ref,
          eventRef: route.event_ref,
          signal: controller.signal,
        });
      } else {
        throw new Error("public result target incomplete");
      }
    } catch (error) {
      setResultLoading(false);
      setResultError(projectR7PublicResultError(error));
      return undefined;
    }
    request.then(async (payload) => {
      if (cancelled) return;
      const verified = await verifyR7PublicResultEnvelope(payload, {
        projectId: normalizedProjectId,
        resultContextToken: resultToken,
        view: expectedView,
      });
      if (cancelled) return;
      const projected = projectR7ResultContext(verified, {
        projectId: normalizedProjectId,
        resultContextToken: resultToken,
        view: expectedView,
      });
      if (projected.kind === "invalid") {
        setResultError(projectR7PublicResultError({ code: projected.code, message: projected.error }));
        setResultLoading(false);
        return;
      }
      setResultContext(projected);
      setResultPayload(normalizePublicR5Payload(projected));
      setResultLoading(false);
    }).catch((error) => {
      if (cancelled || error?.name === "AbortError") return;
      setResultLoading(false);
      setResultError(projectR7PublicResultError(error));
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [api, normalizedProjectId, resultRetryEpoch, resultToken, route.site_ref, route.source_locator_ref, route.spine_ref, route.subject_ref, route.view, route.window_end, route.window_start, routeView]);

  // Slice-08C-2/08C-3: project/site and subject continuity reads. The
  // project/center dashboards read exactly as in 08C-2; the
  // journey/profile/timeline subject views read only when the full public
  // identity is present next to the project and result context
  // (site_ref + subject_ref + spine_ref + window_start + window_end). The
  // request itself still passes only the public site_ref; same-subject
  // same-window filtering happens client-side on the verified rows. Switching
  // project, result context, center, subject, spine, axis window or view
  // aborts the in-flight request and clears the old comparison so stale
  // subject changes never flash back; loading and failures never block the
  // existing result boards or the Patient Journey.
  useEffect(() => {
    const subjectViewIdentityReady = PRODUCT_RESULT_SUBJECT_VIEWS.has(routeView)
      && Boolean(route.site_ref && route.subject_ref && route.spine_ref && route.window_start && route.window_end);
    if (!normalizedProjectId || !resultToken || ((routeView !== "overview" && routeView !== "site_overview") && !subjectViewIdentityReady)) {
      setContinuityResult(null);
      setContinuityLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    let cancelled = false;
    setContinuityResult(null);
    setContinuityLoading(true);
    api.getResultContinuity(normalizedProjectId, resultToken, {
      siteRef: route.site_ref,
      signal: controller.signal,
    }).then(async (payload) => {
      if (cancelled) return;
      const expected = { projectId: normalizedProjectId, resultContextToken: resultToken };
      if (route.site_ref) expected.siteRef = route.site_ref;
      const result = await safeVerifyR7ContinuityEnvelope(payload, expected);
      if (cancelled) return;
      setContinuityResult(result);
      setContinuityLoading(false);
    }).catch((error) => {
      if (cancelled || error?.name === "AbortError") return;
      setContinuityResult(projectR7ContinuityError(error));
      setContinuityLoading(false);
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [api, normalizedProjectId, resultToken, route.site_ref, route.subject_ref, route.spine_ref, route.window_start, route.window_end, routeView]);

  useEffect(() => {
    if (!publicRunToken || resultToken) {
      setProgress(null);
      setProgressLoading(false);
      setProgressError(null);
      previousProgressAvailableRef.current = false;
      return undefined;
    }
    let disposed = false;
    let timer = null;
    let failures = 0;
    let inFlightController = null;
    const readProgress = async (isInitial = false) => {
      if (disposed || (typeof document !== "undefined" && document.hidden)) return;
      if (isInitial) setProgressLoading(true);
      inFlightController?.abort();
      inFlightController = new AbortController();
      try {
        const payload = await api.getPublicProgress(normalizedProjectId, publicRunToken, { signal: inFlightController.signal });
        if (disposed) return;
        const projected = projectR7PublicProgress(payload, { publicRunToken });
        if (projected.kind !== "public_progress") throw new Error(projected.error || "进度响应暂不可用");
        const wasAvailable = previousProgressAvailableRef.current;
        previousProgressAvailableRef.current = projected.resultAvailable;
        setProgress(projected);
        setProgressError(null);
        setProgressLoading(false);
        failures = 0;
        if (projected.resultAvailable && !wasAvailable) setRefreshEpoch((value) => value + 1);
        if (projected.poll.active) timer = setTimeout(() => readProgress(false), projected.poll.intervalMs);
      } catch (error) {
        if (disposed || error?.name === "AbortError") return;
        setProgressLoading(false);
        failures += 1;
        const projectedError = projectR7PublicProgressError(error);
        if (projectedError.kind === "unavailable") setProgress(null);
        setProgressError(projectedError);
        if (projectedError.kind === "error" || projectedError.kind === "refresh_options") {
          timer = setTimeout(() => readProgress(false), r7RefreshBackoffMs(failures));
        }
      }
    };
    const handleVisibility = () => {
      if (document.hidden) {
        if (timer) clearTimeout(timer);
        timer = null;
      } else {
        if (timer) clearTimeout(timer);
        timer = null;
        readProgress(false);
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    readProgress(true);
    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
      inFlightController?.abort();
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [api, normalizedProjectId, publicRunToken, resultToken]);

  const refreshAll = useCallback(() => setRefreshEpoch((value) => value + 1), []);
  const navigate = useCallback((view, patch = {}) => {
    const next = routeStateForMedicalMonitoringR5View(route, view, patch);
    onRouteChange?.(next);
  }, [onRouteChange, route]);
  const goToProgress = useCallback((token = "") => {
    const fallback = resultToken
      ? productState?.selection?.otherInFlightRun?.publicRunToken || productState?.selection?.inFlightRun?.publicRunToken
      : publicRunToken || productState?.selectedPublicRunToken;
    const target = token || fallback;
    if (!target) return;
    navigate("overview", { public_run_token: target, result_context_token: "" });
  }, [navigate, productState?.selectedPublicRunToken, productState?.selection?.inFlightRun?.publicRunToken, productState?.selection?.otherInFlightRun?.publicRunToken, publicRunToken, resultToken]);
  const openResult = useCallback(async (token = productState?.selectedPublicRunToken) => {
    if (!token) return;
    setEntryLoading(true);
    try {
      const payload = await api.getResultEntry(normalizedProjectId, token);
      const entry = projectR7ResultEntry(payload, { projectId: normalizedProjectId, publicRunToken: token });
      if (entry.kind === "invalid") throw new Error(entry.error || "本次结果暂不可查看，请返回进度页");
      navigate("overview", { result_context_token: entry.resultContextToken, public_run_token: "" });
    } catch (error) {
      setResultError(projectR7PublicResultError(error));
    } finally {
      setEntryLoading(false);
    }
  }, [api, navigate, normalizedProjectId, productState?.selectedPublicRunToken]);
  const retryPage = useCallback(() => {
    setResultError(null);
    if (resultToken) {
      setResultRetryEpoch((value) => value + 1);
      return;
    }
    if (productState.kind === "result_available" && productState.selectedPublicRunToken) {
      openResult(productState.selectedPublicRunToken);
      return;
    }
    refreshAll();
  }, [openResult, productState.kind, productState.selectedPublicRunToken, refreshAll, resultToken]);
  const openWizard = useCallback(() => {
    if (!setup || setup.kind !== "setup") return;
    const nextWizard = createR7WizardState(setup, { projectId: normalizedProjectId });
    idempotencyRef.current = createR7IdempotencyController({ initialState: { selection: nextWizard } });
    setWizard(projectR7WizardState({ ...nextWizard, idempotencyKey: idempotencyRef.current.getState().key }, setup));
    setWizardError("");
    setPreviewText("");
    setPreviewOpen(false);
    setRuleConfirmOpen(false);
    setWizardOpen(true);
  }, [normalizedProjectId, setup]);
  const closeWizard = useCallback(() => {
    setWizardOpen(false);
    setPreviewOpen(false);
    setRuleConfirmOpen(false);
    setWizardError("");
  }, []);
  const changeWizard = useCallback((field, value) => {
    setWizardError("");
    setWizard((current) => {
      if (!current || !setup) return current;
      const changed = setR7WizardSelection(current, field, value, setup);
      const idem = idempotencyRef.current?.syncSelection(changed);
      return projectR7WizardState({ ...changed, idempotencyKey: idem?.key || current.idempotencyKey }, setup);
    });
  }, [setup]);
  const advanceWizard = useCallback((direction) => {
    setWizard((current) => {
      if (!current || !setup) return current;
      const moved = advanceR7WizardStep(current, setup, direction);
      return projectR7WizardState(moved, setup);
    });
  }, [setup]);
  const executePrepare = useCallback(async (currentWizard) => {
    if (!currentWizard) return null;
    const payload = buildR7PrepareAndStartPayload(currentWizard, setup);
    idempotencyRef.current?.markAttempt();
    return api.prepareAndStart(normalizedProjectId, payload);
  }, [api, normalizedProjectId, setup]);
  const finishPrepare = useCallback((response) => {
    const token = publicRunTokenFrom(response);
    if (!token) throw new Error("prepare response missing public run token");
    closeWizard();
    refreshAll();
    navigate("overview", { public_run_token: token, result_context_token: "" });
  }, [closeWizard, navigate, refreshAll]);
  const submitWizard = useCallback(async () => {
    if (!wizard || !setup) return;
    setWizardError("");
    try {
      const response = await executePrepare(wizard);
      finishPrepare(response);
    } catch (error) {
      const returnedToken = publicRunTokenFrom(error);
      if (returnedToken) {
        finishPrepare({ public_run_token: returnedToken });
        return;
      }
      const code = clean(error?.code || error?.detail?.code);
      const timedOut = error?.name === "AbortError" || error?.name === "TimeoutError" || code === "timeout" || code === "ETIMEDOUT" || /timeout|timed out|超时/i.test(clean(error?.message));
      if (timedOut && idempotencyRef.current) {
        const outcome = idempotencyRef.current.handleTimeout();
        if (outcome.action === "retry_same_key") {
          try {
            const retryResponse = await executePrepare(wizard);
            finishPrepare(retryResponse);
            return;
          } catch (retryError) {
            const retryOutcome = idempotencyRef.current.handleTimeout({ publicRunToken: publicRunTokenFrom(retryError) });
            if (retryOutcome.action === "lookup_public_run") {
              finishPrepare({ public_run_token: retryOutcome.publicRunToken });
              return;
            }
            error = retryError;
          }
        } else if (outcome.action === "lookup_public_run") {
          finishPrepare({ public_run_token: outcome.publicRunToken });
          return;
        }
      }
      setWizardError(publicErrorText(error, "本次监查未能开始，请保留当前设置后重试。"));
    }
  }, [executePrepare, finishPrepare, setup, wizard]);
  const requestPreview = useCallback(async () => {
    if (!previewText.trim()) return;
    setPreviewBusy(true);
    try {
      const payload = await api.previewRiskRule(normalizedProjectId, {
        source_text: previewText.trim(),
        applicable_scope: "项目内全部适用范围",
        starting_run: "本次确认后明确选择的运行",
      });
      const candidates = Array.isArray(payload?.candidates) ? payload.candidates.slice(0, 5) : [];
      const selected = candidates.length === 1 ? clean(candidates[0].candidate_id) : "";
      setWizard((current) => current ? projectR7WizardState(setR7WizardSelection(setR7WizardSelection(current, "preview", { ...payload, candidates }, setup), "previewCandidateId", selected, setup), setup) : current);
      setPreviewOpen(true);
    } catch (error) {
      setWizardError(publicErrorText(error, "特殊关注预览暂不可用，请稍后重试。"));
    } finally {
      setPreviewBusy(false);
    }
  }, [api, normalizedProjectId, previewText, setup]);
  const confirmPreview = useCallback(() => {
    if (!wizard?.previewCandidateId) return;
    setRuleConfirmOpen(true);
  }, [wizard?.previewCandidateId]);
  const confirmRule = useCallback(async () => {
    if (!wizard?.preview || !wizard.previewCandidateId) return;
    setRuleConfirmBusy(true);
    try {
      const revision = await api.confirmRiskRule(normalizedProjectId, {
        preview: wizard.preview,
        candidate_id: wizard.previewCandidateId,
      });
      const revisionToken = clean(revision?.revision_token);
      if (!revisionToken) throw new Error("rule revision response missing public revision");
      const normalizedRevision = {
        projectId: clean(revision.project_id, normalizedProjectId),
        revision: revision.revision,
        revisionToken,
        summary: clean(revision.summary || revision.subject, "已确认特殊关注"),
        applicableScope: clean(revision.applicable_scope, "项目内全部适用范围"),
        startingRun: clean(revision.starting_run, "本次确认后明确选择的运行"),
        selectable: revision.selectable !== false,
        recommended: false,
        createdAt: clean(revision.created_at),
      };
      const nextSetup = {
        ...setup,
        ruleRevisions: [...(setup.ruleRevisions || []).filter((item) => item.revisionToken !== revisionToken), normalizedRevision],
      };
      setSetup(nextSetup);
      setWizard((current) => {
        if (!current) return current;
        const withRule = setR7WizardSelection(current, "riskRuleTokens", [...current.riskRuleTokens, revisionToken], nextSetup);
        const idem = idempotencyRef.current?.syncSelection(withRule);
        const clearedPreview = setR7WizardSelection(setR7WizardSelection(withRule, "preview", null, nextSetup), "previewCandidateId", "", nextSetup);
        return projectR7WizardState({ ...clearedPreview, idempotencyKey: idem?.key || current.idempotencyKey }, nextSetup);
      });
      setRuleConfirmOpen(false);
      setPreviewOpen(false);
    } catch (error) {
      setWizardError(publicErrorText(error, "特殊关注尚未保存，请保留当前设置后重试。"));
    } finally {
      setRuleConfirmBusy(false);
    }
  }, [api, normalizedProjectId, setup, wizard]);
  const onWorkbarAction = useCallback((target) => {
    if (target === "wizard") openWizard();
    else if (target === "history") setHistoryOpen(true);
    else if (target === "progress") goToProgress();
    else if (target === "result") openResult();
    else if (target === "overview") navigate("overview", { public_run_token: "", result_context_token: "" });
  }, [goToProgress, navigate, openResult, openWizard]);
  const selectHistoryRow = useCallback((row) => {
    setHistoryOpen(false);
    if (!row?.publicRunToken) return;
    if (row.resultAvailable === true) openResult(row.publicRunToken);
    else goToProgress(row.publicRunToken);
  }, [goToProgress, openResult]);
  const selectResultSubject = useCallback((subject) => {
    if (!resultPayload) return;
    const window = selectedSubjectWindow(resultPayload, subject, route);
    navigate("journey", {
      site_ref: subject.site_ref || subject.site_id,
      subject_ref: subject.subject_ref || subject.subject_id,
      spine_ref: subject.spine_ref || subject.spineRef,
      window_start: window.start,
      window_end: window.end,
    });
  }, [navigate, resultPayload, route]);
  const selectResultRisk = useCallback((risk) => {
    if (risk?.__view) {
      navigate(risk.__view);
      return;
    }
    if (!resultPayload || !risk) return;
    const subject = (resultPayload.projection.subjects || []).find((item) => clean(item.subject_ref || item.subject_id) === clean(risk.subjectRef || risk.subject_ref)) || {
      subject_ref: risk.subjectRef,
      site_ref: risk.siteRef,
      spine_ref: risk.spineRef,
    };
    const window = selectedSubjectWindow(resultPayload, subject, route);
    navigate("journey", {
      site_ref: risk.siteRef || risk.site_ref,
      subject_ref: risk.subjectRef || risk.subject_ref,
      spine_ref: risk.spineRef || risk.spine_ref,
      window_start: window.start,
      window_end: window.end,
      risk_instance_ref: risk.riskInstanceRef || risk.risk_instance_ref,
      risk_anchor_ref: risk.riskAnchorRef || risk.risk_anchor_ref,
      event_ref: risk.eventRef || risk.event_ref,
      visit_ref: risk.visitRef || risk.visit_ref,
    });
  }, [navigate, resultPayload, route]);
  const selectResultCenter = useCallback((center) => navigate("site_overview", { site_ref: center.siteRef || center.site_ref }), [navigate]);
  const selectResultEvent = useCallback((event) => navigate(routeView, {
    event_ref: event.eventRef || event.event_ref,
    visit_ref: event.visitRef || event.visit_ref,
    risk_anchor_ref: event.riskAnchorRefs?.[0] || event.risk_anchor_refs?.[0],
    risk_instance_ref: "",
  }), [navigate, routeView]);
  const selectResultContinuityRow = useCallback((row) => {
    if (!row || typeof row !== "object") return;
    const patch = {
      risk_instance_ref: row.risk_instance_ref || "",
      risk_anchor_ref: row.risk_anchor_ref || "",
      event_ref: row.event_ref || "",
      visit_ref: row.visit_ref || "",
    };
    navigate(routeView, patch);
  }, [navigate, routeView]);
  const backFromPublicEvidence = useCallback(() => {
    const canReturnToJourney = route.site_ref && route.subject_ref && route.spine_ref && route.window_start && route.window_end;
    navigate(canReturnToJourney ? "journey" : "overview");
  }, [navigate, route.site_ref, route.spine_ref, route.subject_ref, route.window_end, route.window_start]);
  const openResultSource = useCallback((risk) => navigate("evidence", {
    risk_instance_ref: risk.riskInstanceRef || risk.risk_instance_ref,
    source_locator_ref: risk.sourceLocatorRef || risk.source_locator_ref || risk.sourceLocatorRefs?.[0],
  }), [navigate]);
  // Slice-08C-2 same-identity routing: continuity rows reuse the public
  // journey/evidence routes; the gates live in the pure filter helpers.
  const selectContinuityJourney = useCallback((row) => {
    const target = r7ContinuityRowJourneyTarget(row, resultPayload);
    if (!target) return;
    navigate("journey", target);
  }, [navigate, resultPayload]);
  const selectContinuitySource = useCallback((row) => {
    const target = r7ContinuityRowSourceTarget(row);
    if (!target) return;
    navigate("evidence", target);
  }, [navigate]);
  const jumpResultFlowSubject = useCallback((row) => navigate("journey", {
    subject_ref: row.subjectRef || row.subject_ref,
    site_ref: row.siteRef || row.site_ref,
    spine_ref: row.spineRef || row.spine_ref,
    window_start: row.jumpStart || row.jump_window_start,
    window_end: row.jumpEnd || row.jump_window_end,
  }), [navigate]);
  const selectResultFlowStage = useCallback((stageRef, metric) => navigate(routeView, {
    flow_stage_ref: stageRef,
    flow_node_metric: metric === "reached" ? "reached" : "current",
    flow_link_ref: "",
  }), [navigate, routeView]);
  const selectResultFlowLink = useCallback((linkRef) => navigate(routeView, {
    flow_link_ref: linkRef,
    flow_stage_ref: "",
    flow_node_metric: "",
  }), [navigate, routeView]);
  const selectResultFlowMetric = useCallback((metric) => navigate(routeView, {
    flow_node_metric: metric === "reached" ? "reached" : "current",
  }), [navigate, routeView]);
  const toggleResultFlowRisk = useCallback(() => navigate(routeView, {
    flow_risk_band: route.flow_risk_band === "mid_high" ? "" : "mid_high",
  }), [navigate, route.flow_risk_band, routeView]);
  const clearResultFlow = useCallback(() => navigate(routeView, {
    flow_stage_ref: "",
    flow_node_metric: "",
    flow_link_ref: "",
    flow_risk_band: "",
  }), [navigate, routeView]);
  const continuityUnavailableText = continuityResult && !continuityResult.ok ? continuityResult.text : "";
  const suppressVersionClaim = Boolean(continuityUnavailableText);
  const continuityCounts = continuityResult?.ok
    ? (continuityResult.value?.comparison?.change_counts || null)
    : null;
  const currentResultView = resultPayload && resultContext ? (
    routeView === "overview" || routeView === "site_overview"
      ? OverviewView ? <OverviewView payload={resultPayload} route={route} selectedRiskInstanceRef={route.risk_instance_ref} onRiskSelect={selectResultRisk} onCenterSelect={selectResultCenter} onSubjectSelect={selectResultSubject} onSource={openResultSource} onFlowStageSelect={selectResultFlowStage} onFlowLinkSelect={selectResultFlowLink} onFlowMetricSelect={selectResultFlowMetric} onFlowRiskToggle={toggleResultFlowRisk} onFlowClear={clearResultFlow} onFlowSubjectJump={jumpResultFlowSubject} suppressVersionClaim={suppressVersionClaim} flowTableOpen continuityCounts={continuityCounts} /> : null
      : PRODUCT_RESULT_SUBJECT_VIEWS.has(routeView)
        ? SubjectWorkspaceView ? <SubjectWorkspaceView payload={resultPayload} route={route} view={routeView} zoomLevel={0} onRiskSelect={selectResultRisk} onEventSelect={selectResultEvent} onSource={openResultSource} onDrawerClose={() => onRouteChange?.(r7JourneyDrawerClosePatch(route))} onJourneyRowSelect={selectResultContinuityRow} continuityResult={continuityResult} continuityUnavailable={continuityUnavailableText} continuityLoading={continuityLoading} /> : null
        : routeView === "evidence"
          ? EvidenceView ? <EvidenceView payload={resultPayload} route={route} onBack={backFromPublicEvidence} /> : null
          : null
  ) : null;
  const loadingBody = setupHistoryLoading || resultLoading || entryLoading;
  const unavailableText = resultError?.text || setupHistoryError?.text || "本次结果暂不可查看，请返回进度页";
  const effectiveHeading = routeView === "site_overview" ? "中心风险图谱" : PRODUCT_RESULT_SUBJECT_VIEWS.has(routeView) ? "受试者医学旅程" : routeView === "evidence" ? "风险证据" : "项目风险概览";
  const resultLoaded = Boolean(resultPayload && resultContext);
  const resultSiteScopeText = route.site_ref
    ? clean(
      resultPayload?.projection?.centers?.find((center) => clean(center.siteRef || center.site_ref) === clean(route.site_ref))?.siteLabel
        || resultPayload?.projection?.raw?.subject?.site_label
        || resultPayload?.projection?.raw?.subject?.site_name,
    )
    : "";
  const workbar = { ...(productState?.workbar || {}) };
  if (routeView === "site_overview") {
    if (workbar.mainTarget === "wizard") {
      workbar.mainAction = "";
      workbar.mainTarget = "";
    }
    if (workbar.secondaryTarget === "wizard") {
      workbar.secondaryAction = "";
      workbar.secondaryTarget = "";
    }
    if (resultToken) {
      // Exactly one return control: ProductRouteTabs owns “返回项目风险概览”.
      workbar.secondaryAction = "";
      workbar.secondaryTarget = "";
      workbar.otherAction = "";
    } else if (workbar.mainTarget === "progress") {
      workbar.secondaryAction = "返回项目风险概览";
      workbar.secondaryTarget = "overview";
      workbar.otherAction = "";
    }
  }
  const displayState = { ...productState, workbar };
  const productStatus = resultError || setupHistoryError ? "unavailable" : loadingBody ? "loading" : productState.kind;
  const startSurfaceTitle = routeView === "site_overview"
    ? "当前中心暂无本次结果"
    : productState.kind === "result_available"
      ? "本次结果已可查看"
      : productState.kind === "active_run"
        ? "本次监查正在进行"
        : "从上方开始本次监查";
  const startSurfaceCopy = routeView === "site_overview"
    ? productState.kind === "active_run"
      ? "当前中心不启动新监查，请返回项目概览查看本次进度。"
      : "当前中心结果仅在打开本次已发布结果后显示。"
    : productState.kind === "result_available"
      ? "使用“查看本次结果”打开本次已发布结果；如有正在进行的监查，可从工作条返回进度。"
      : productState.kind === "active_run"
        ? "工作条中的“查看本次进度”进入真实进度页面。"
        : "工作条中的操作会读取服务端范围与历史，不使用本地示例结果。";
  return (
    <main className="r5-page r7-product-page" data-r5-view={routeView} data-r7-product-state={productStatus} data-r7-product-view={routeView}>
      <header className="r5-page-header r7-product-header">
        <div><span className="r5-eyebrow">医学监查</span><h1>{effectiveHeading}</h1><p>从本次监查进入项目风险、中心范围与受试者医学旅程。</p></div>
        <div className="r5-page-actions"><button type="button" className="r5-back-button" onClick={onReturn}>医学监查首页</button></div>
      </header>
      <R7ProductWorkbar state={displayState} onAction={onWorkbarAction} omitComparisonClaim={suppressVersionClaim} />
      {resultLoaded ? <R7PublicResultIdentityStrip identity={resultContext.identity} siteScopeText={resultSiteScopeText} /> : null}
      <ProductRouteTabs route={route} resultLoaded={resultLoaded} onOverview={() => navigate("overview")} />
      {wizardOpen && wizard ? <R7WizardView wizard={{ ...wizard, dataBatches: setup?.dataBatches || [], serverSummary: setup?.serverSummary || {}, errorText: wizardError || wizard.errorText }} previewText={previewText} previewBusy={previewBusy} previewOpen={previewOpen} onClose={closeWizard} onSelect={changeWizard} onAdvance={(direction) => direction > 0 && wizard.step === 4 ? submitWizard() : advanceWizard(direction)} onPreviewTextChange={setPreviewText} onPreview={requestPreview} onClosePreview={() => { setPreviewOpen(false); changeWizard("preview", null); changeWizard("previewCandidateId", ""); }} onConfirmPreview={confirmPreview} canConfirmPreview={Boolean(wizard.previewCandidateId)} /> : null}
      {!loadingBody && (resultError || setupHistoryError) ? <section className="r7-product-state-panel is-unavailable" role="alert"><strong>当前内容暂不可用</strong><span>{unavailableText}</span><button type="button" className="r7-product-button is-small" onClick={retryPage}>重新读取</button></section> : null}
      {!loadingBody && !resultError && !setupHistoryError && publicRunToken && !resultToken ? <R7PublicProgressSurface progress={progress} error={progressError} loading={progressLoading} onRefresh={() => setRefreshEpoch((value) => value + 1)} onBack={() => navigate("overview", { public_run_token: "" })} onOpenResult={() => openResult(publicRunToken)} /> : null}
      {!loadingBody && !resultError && !setupHistoryError && resultLoaded ? (
        <div className="r7-product-result-body">
          {/* Tamper/unavailable continuity must lead the first screen with the exact fail-closed copy.
           * Comparable overviews keep flow+table first, then continuity. */}
          {suppressVersionClaim && (routeView === "overview" || routeView === "site_overview") ? (
            <MedicalMonitoringContinuityPanel
              key={`${resultToken}:${route.site_ref || ""}:lead`}
              continuity={null}
              unavailable={continuityUnavailableText}
              loading={continuityLoading}
              resultPayload={resultPayload}
              onJourney={selectContinuityJourney}
              onSource={selectContinuitySource}
            />
          ) : null}
          {currentResultView}
          {!suppressVersionClaim && (routeView === "overview" || routeView === "site_overview") ? (
            <MedicalMonitoringContinuityPanel
              key={`${resultToken}:${route.site_ref || ""}`}
              continuity={continuityResult?.ok ? continuityResult.value : null}
              unavailable={continuityUnavailableText}
              loading={continuityLoading}
              resultPayload={resultPayload}
              onJourney={selectContinuityJourney}
              onSource={selectContinuitySource}
              omitCounts={Boolean(continuityCounts)}
            />
          ) : null}
        </div>
      ) : null}
      {!loadingBody && !resultError && !setupHistoryError && !resultLoaded && !publicRunToken ? <section className="r7-product-start-surface"><strong>{startSurfaceTitle}</strong><span>{startSurfaceCopy}</span></section> : null}
      {historyOpen ? <R7HistoryDrawer history={history} selectedPublicRunToken={productState.selectedPublicRunToken} onSelect={selectHistoryRow} onClose={() => setHistoryOpen(false)} /> : null}
      {ruleConfirmOpen ? <div className="r7-product-overlay" role="presentation"><section className="r7-rule-confirm-dialog" role="dialog" aria-modal="true" aria-label="确认保存特殊关注"><span className="r5-eyebrow">再次确认</span><h2>确认后将保存为本项目规则</h2><p>即使关闭本次向导，该规则也会保留。确认后返回第 3 步并默认勾选。</p><div className="r7-dialog-foot"><button type="button" className="r7-product-button is-quiet" disabled={ruleConfirmBusy} onClick={() => setRuleConfirmOpen(false)}>取消</button><button type="button" className="r7-product-button is-primary" disabled={ruleConfirmBusy} onClick={confirmRule}>{ruleConfirmBusy ? "保存中" : "再次确认并保存"}</button></div></section></div> : null}
    </main>
  );
}

export default MedicalMonitoringProductLoop;
