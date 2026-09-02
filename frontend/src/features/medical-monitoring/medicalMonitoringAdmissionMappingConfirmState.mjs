// Pure helpers for C3 admission mapping confirmation inside the wizard.
// Keeps Chinese product copy and candidate/fact separation outside transport.

import { semanticQualityPresentation } from "./medicalMonitoringFieldMappingState.mjs";

export const MAPPING_FOCUS_CRITICAL = "critical";
export const MAPPING_FOCUS_ALL = "all";

export function createAdmissionMappingConfirmState() {
  return {
    phase: "idle", // idle | loading | ready | adopting | drafting | confirming | confirmed | failed
    focus: MAPPING_FOCUS_CRITICAL,
    payload: null,
    draft: null,
    revision: null,
    selectedKey: "",
    fieldForm: null,
    confirmationReason: "",
    message: "",
    error: null,
  };
}

export function confidencePercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number * 100)}%`;
}

export function mappingCandidateKey(item) {
  return `${item?.domain || ""}::${item?.source_field || ""}`;
}

export function mappingDraftMissingAdviceCount(draft) {
  const fields = Array.isArray(draft?.fields) ? draft.fields : [];
  return fields.filter((field) => !String(field?.user_action || "").trim()).length;
}

export function projectMappingCandidates(payload) {
  const summary = payload?.summary || {};
  const candidates = Array.isArray(payload?.candidates) ? payload.candidates : [];
  return {
    state: String(payload?.state || ""),
    confirmationStatus: String(payload?.confirmation_status || "pending_confirmation"),
    factsGenerated: Boolean(payload?.facts_generated),
    summaryText: [
      `共 ${Number(summary.candidate_count) || 0} 条字段对应建议`,
      `重点关注 ${Number(summary.critical_count) || 0} 条`,
      `当前显示 ${Number(summary.displayed_count) || candidates.length} 条`,
    ].join(" · "),
    candidates: candidates.map((item) => ({
      domain: String(item.domain || ""),
      sourceField: String(item.source_field || ""),
      recommendedRole: String(item.recommended_role || ""),
      fieldKind: String(item.field_kind || ""),
      confidence: item.confidence,
      uncertainty: String(item.uncertainty || ""),
      userAction: String(item.user_action || ""),
      attentionReason: String(item.attention_reason || ""),
      needsAttention: Boolean(item.needs_attention),
      evidenceSummary: Array.isArray(item.evidence_summary) ? item.evidence_summary : [],
      confirmationStatus: String(item.confirmation_status || "pending_confirmation"),
    })),
    raw: payload,
  };
}

export function admissionMappingConfirmReducer(state, action) {
  switch (action?.type) {
    case "focus-change":
      return {
        ...state,
        focus: action.focus === MAPPING_FOCUS_ALL ? MAPPING_FOCUS_ALL : MAPPING_FOCUS_CRITICAL,
        error: null,
      };
    case "load-start":
      return { ...state, phase: "loading", error: null, message: "正在加载字段对应建议…" };
    case "load-ready":
      return {
        ...state,
        phase: "ready",
        payload: projectMappingCandidates(action.payload),
        message: action.payload?.state === "generating"
          ? "字段对应建议生成中，请刷新进度。"
          : action.payload?.state === "needs_attention"
            ? "部分字段建议尚未完成，请先处理未完成部分。"
            : "请先查看重点字段，再采用建议进入修订。",
        error: null,
      };
    case "adopt-start":
      return { ...state, phase: "adopting", error: null, message: "正在采用字段对应建议…" };
    case "adopt-ready":
      return {
        ...state,
        phase: "drafting",
        payload: action.candidatePayload
          ? projectMappingCandidates(action.candidatePayload)
          : state.payload,
        draft: action.payload,
        selectedKey: "",
        fieldForm: null,
        message: "建议已进入可修订草稿。确认前不会生成可用于监查的数据。",
        error: null,
      };
    case "select-field":
      return {
        ...state,
        selectedKey: action.key,
        fieldForm: action.form,
        error: null,
      };
    case "field-form-change":
      return {
        ...state,
        fieldForm: { ...(state.fieldForm || {}), ...(action.patch || {}) },
      };
    case "save-field-ready":
      return {
        ...state,
        phase: "drafting",
        draft: action.payload,
        selectedKey: "",
        fieldForm: null,
        message: "字段修订已保存。",
        error: null,
      };
    case "confirm-start":
      return { ...state, phase: "confirming", error: null, message: "正在整体确认字段对应…" };
    case "confirm-ready":
      return {
        ...state,
        phase: "confirmed",
        revision: action.payload,
        message: "字段对应已确认。可用于监查的数据尚未生成，需在后续步骤单独生成。",
        error: null,
      };
    case "reason-change":
      return { ...state, confirmationReason: String(action.value || "") };
    case "draft-error":
      return {
        ...state,
        phase: "drafting",
        error: action.error || { serverText: "字段对应修订未能完成。" },
        message: "",
      };
    case "error":
      return {
        ...state,
        phase: "failed",
        error: action.error || { serverText: "字段对应确认未能完成。" },
        message: "",
      };
    case "reset":
      return createAdmissionMappingConfirmState();
    default:
      return state;
  }
}

export function admissionMappingPrimaryAction(state) {
  if (!state) return { key: "noop", label: "请稍候", disabled: true };
  if (state.phase === "loading" || state.phase === "adopting" || state.phase === "confirming") {
    return { key: "busy", label: state.message || "处理中…", disabled: true };
  }
  if (state.phase === "confirmed") {
    return { key: "finish", label: "完成接入", disabled: false };
  }
  if (state.phase === "drafting" && state.draft) {
    const quality = semanticQualityPresentation(state.draft.semantic_quality);
    const missingAdviceCount = mappingDraftMissingAdviceCount(state.draft);
    return {
      key: "confirm",
      label: "整体确认字段对应",
      disabled: quality.blocksConfirmation
        || missingAdviceCount > 0
        || String(state.confirmationReason || "").trim().length < 10,
    };
  }
  if (state.phase === "ready" && state.payload?.state === "candidates_ready") {
    const summary = state.payload.raw?.summary || {};
    if ((Number(summary.displayed_count) || 0) === 0) {
      if ((Number(summary.candidate_count) || 0) > 0) {
        return { key: "show-all", label: "查看全部建议", disabled: false };
      }
      return { key: "noop", label: "暂无字段建议", disabled: true };
    }
    return { key: "adopt", label: "采用建议并进入修订", disabled: false };
  }
  if (state.phase === "ready" && state.payload?.state === "generating") {
    return { key: "reload", label: "刷新生成进度", disabled: false };
  }
  if (state.phase === "failed") {
    return { key: "reload", label: "重新加载建议", disabled: false };
  }
  return { key: "reload", label: "加载字段对应建议", disabled: false };
}
