// Overview comparison-note state, derived from the actual comparison evidence the
// product layer holds instead of guessing "first version" from counts.
//
// Real contract (packages/medical_monitoring/api/r7_product/continuity_service.py +
// runtime/continuity.py project_risk_change_kind): a continuity round whose counts
// prove prior-state transitions (upgraded/continued/downgraded/closed/reopened) has
// necessarily been compared against a baseline — those kinds are unreachable without
// a prior risk state. Counts alone canNOT separate "first analysis" from "compared
// round whose only changes are new/needs_rejudgment/none": both can carry new > 0 or
// an all-zero record. Those rounds derive "uncertain" — the note must not claim
// either baseline state, and the authoritative comparison_text stays in the
// continuity envelope (rendered verbatim by MedicalMonitoringContinuityPanel).

export const MONITORING_COMPARISON_STATE_COMPARED = "compared";
export const MONITORING_COMPARISON_STATE_UNCERTAIN = "uncertain";
export const MONITORING_COMPARISON_STATE_INITIAL = "initial";

// Change kinds that require a matched prior risk state, so any positive count
// proves the round ran a real comparison. `reopened` needs a prior closed state,
// `closed`/`continued`/`upgraded`/`downgraded` need any prior state.
const PRIOR_STATE_PROOF_KEYS = Object.freeze([
  "upgraded",
  "continued",
  "downgraded",
  "closed",
  "reopened",
]);

function positiveCount(record, key) {
  const value = record?.[key];
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

export function monitoringComparisonState({ continuityCounts = null, changes = [], comparisonText = "", loading = false } = {}) {
  if (loading) return { state: MONITORING_COMPARISON_STATE_UNCERTAIN, basis: "loading" };
  if (comparisonText === "已与上次监查结果比较") return { state: MONITORING_COMPARISON_STATE_COMPARED, basis: "continuity" };
  if (comparisonText === "本轮为首次全面分析，无比较基线") return { state: MONITORING_COMPARISON_STATE_INITIAL, basis: "continuity" };
  const legacyCompared = Array.isArray(changes)
    && changes.some((item) => Boolean(item && item.prior_snapshot_ref));
  if (legacyCompared) {
    return { state: MONITORING_COMPARISON_STATE_COMPARED, basis: "legacy" };
  }
  if (continuityCounts && typeof continuityCounts === "object" && !Array.isArray(continuityCounts)) {
    const compared = PRIOR_STATE_PROOF_KEYS.some((key) => positiveCount(continuityCounts, key));
    return compared
      ? { state: MONITORING_COMPARISON_STATE_COMPARED, basis: "continuity" }
      : { state: MONITORING_COMPARISON_STATE_UNCERTAIN, basis: "continuity" };
  }
  return { state: MONITORING_COMPARISON_STATE_UNCERTAIN, basis: "none" };
}
