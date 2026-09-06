import assert from "node:assert/strict";
import {
  MONITORING_COMPARISON_STATE_COMPARED,
  MONITORING_COMPARISON_STATE_INITIAL,
  MONITORING_COMPARISON_STATE_UNCERTAIN,
  monitoringComparisonState,
} from "./medicalMonitoringComparisonState.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

function counts(overrides = {}) {
  return {
    new: 0,
    upgraded: 0,
    continued: 0,
    downgraded: 0,
    closed: 0,
    reopened: 0,
    needs_rejudgment: 0,
    mid_high_total: 0,
    changed_subject_count: 0,
    ...overrides,
  };
}

// 后端 project_risk_change_kind：continued/downgraded/closed/reopened/upgraded 都要求
// 存在前序风险状态，因此任一计数 > 0 即证明本轮真实执行过基线比较——即使前端展示的
// 五个关键计数全部为 0（缺陷报告的“零变化被误标首次”场景）。
const onlyContinued = monitoringComparisonState({
  continuityCounts: counts({ continued: 3, mid_high_total: 2, changed_subject_count: 0 }),
  changes: [],
});
check(onlyContinued.state === MONITORING_COMPARISON_STATE_COMPARED, "continued-only round derives compared");
check(onlyContinued.basis === "continuity", "continued-only round uses the continuity basis");

for (const [key, value] of [["upgraded", 1], ["downgraded", 2], ["closed", 1], ["reopened", 1]]) {
  const state = monitoringComparisonState({ continuityCounts: counts({ [key]: value }), changes: [] });
  check(state.state === MONITORING_COMPARISON_STATE_COMPARED, `${key}>0 proves a compared round`);
}

// 首轮全量分析：新风险全部是 new（前序状态为空），不可能出现上述前序状态迁移计数。
// 仅凭计数无法与“比较后全为新增”区分，因此不得断言“已比较”，也不得断言“首次”。
const firstAnalysisShaped = monitoringComparisonState({
  continuityCounts: counts({ new: 4, needs_rejudgment: 1, mid_high_total: 3, changed_subject_count: 3 }),
  changes: [],
});
check(firstAnalysisShaped.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "first-analysis-shaped counts stay uncertain instead of claiming compared");
check(firstAnalysisShaped.basis === "continuity", "uncertain state still reports the continuity basis");

// 全零计数：比较后零变化与无基线空项目同形，既不能误标“首次”，也不能谎称“已比较”。
const allZero = monitoringComparisonState({ continuityCounts: counts(), changes: [] });
check(allZero.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "all-zero counts must not be labeled first version");

// 旧版 changeBands 信号保持不变：prior_snapshot_ref 仍直接证明已比较。
const legacy = monitoringComparisonState({
  continuityCounts: null,
  changes: [{ change_kind: "new", prior_snapshot_ref: "snapshot-1" }],
});
check(legacy.state === MONITORING_COMPARISON_STATE_COMPARED && legacy.basis === "legacy", "legacy prior_snapshot_ref still derives compared");

const legacyInitial = monitoringComparisonState({
  continuityCounts: null,
  changes: [{ change_kind: "new" }],
});
check(legacyInitial.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "no comparison evidence falls back to the legacy initial state");

const emptyInput = monitoringComparisonState({});
check(emptyInput.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "missing inputs derive the initial state");

const weirdCounts = monitoringComparisonState({ continuityCounts: [1, 2], changes: [] });
check(weirdCounts.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "array-shaped counts are not treated as a continuity record");

const stringCount = monitoringComparisonState({
  continuityCounts: counts({ continued: "3" }),
  changes: [],
});
check(stringCount.state === MONITORING_COMPARISON_STATE_UNCERTAIN, "non-numeric counts do not prove a comparison");

console.log(`medicalMonitoringComparisonState: ${passed} passed`);

assert.equal(monitoringComparisonState({continuityCounts: counts(), comparisonText: "已与上次监查结果比较"}).state, MONITORING_COMPARISON_STATE_COMPARED);
assert.equal(monitoringComparisonState({continuityCounts: counts({new: 4}), comparisonText: "本轮为首次全面分析，无比较基线"}).state, MONITORING_COMPARISON_STATE_INITIAL);
assert.equal(monitoringComparisonState({loading: true}).state, MONITORING_COMPARISON_STATE_UNCERTAIN);
