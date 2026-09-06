import assert from "node:assert/strict";
import {
  MONITORING_TREND_MODE_BARS,
  MONITORING_TREND_MODE_VALUES,
  monitoringTrendScaleView,
} from "./medicalMonitoringTrendScale.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

// 真实数值域：20/100/300 必须画成不同高度（旧实现 ×8 后裁剪到 14–92%，三者同高）。
const realScale = monitoringTrendScaleView({
  label: "症状评分",
  unit: "分",
  points: [{ date: "2026-01-10", value: 20 }, { date: "2026-02-10", value: 100 }, { date: "2026-03-10", value: 300 }],
});
check(realScale.mode === MONITORING_TREND_MODE_BARS, "plain non-negative series uses bars mode");
check(realScale.max === 300, "scale max equals the largest known value");
check(realScale.unit === "分", "indicator unit passes through");
const heights = realScale.items.map((item) => item.heightPercent);
check(new Set(heights).size === 3, "distinct values keep distinct bar heights");
check(Math.abs(heights[0] / heights[1] - 0.2) < 1e-12 && heights[2] === 100, "heights are proportional on a zero-based linear scale");

// 零值是真实数据：保留数值且高度为 0，不虚画小柱。
const withZero = monitoringTrendScaleView({
  points: [{ date: "a", value: 0 }, { date: "b", value: 50 }],
});
check(withZero.mode === MONITORING_TREND_MODE_BARS, "zero-containing series stays in bars mode");
check(withZero.items[0].heightPercent === 0 && withZero.items[0].value === 0, "true zero maps to a zero-height bar, not a stub");

// 缺失不画零：缺值点保留位置与“待确认”素材，但不产生柱高，也不进入标尺计算。
const withMissing = monitoringTrendScaleView({
  points: [{ date: "a", value: 10 }, { date: "b", value: null }, { date: "c", value: 30 }],
});
check(withMissing.mode === MONITORING_TREND_MODE_BARS, "missing values do not force the fallback mode");
check(withMissing.items[1].value === null && withMissing.items[1].heightPercent === 0, "missing values carry no bar height");
check(withMissing.max === 30, "missing values do not distort the scale max");

// 负值：零基线向上的柱无法如实表达，回退为逐点数值列出。
const negative = monitoringTrendScaleView({
  points: [{ date: "a", value: -5 }, { date: "b", value: 10 }],
});
check(negative.mode === MONITORING_TREND_MODE_VALUES && negative.reason === "negative", "negative values fall back to values mode");
check(negative.max === null, "values mode claims no scale");

// 单位不可比不合并：同一指标内各点单位不一致时不得共用一把标尺。
const mixedUnits = monitoringTrendScaleView({
  unit: "",
  points: [{ date: "a", value: 1, unit: "mg/L" }, { date: "b", value: 2, unit: "g/L" }],
});
check(mixedUnits.mode === MONITORING_TREND_MODE_VALUES && mixedUnits.reason === "mixed_units", "mixed point units fall back to values mode");

const sameUnits = monitoringTrendScaleView({
  points: [{ date: "a", value: 1, unit: "mg/L" }, { date: "b", value: 2, unit: "mg/L" }],
});
check(sameUnits.mode === MONITORING_TREND_MODE_BARS, "consistent point units keep bars mode");

// 全缺失/空输入：无可绘制数值时明确回退，不虚构标尺。
const allMissing = monitoringTrendScaleView({
  points: [{ date: "a", value: null }, { date: "b" }],
});
check(allMissing.mode === MONITORING_TREND_MODE_VALUES && allMissing.reason === "no_known_values", "all-missing series reports no known values");

const empty = monitoringTrendScaleView(null);
check(empty.mode === MONITORING_TREND_MODE_VALUES && empty.items.length === 0, "null indicator degrades to an empty values view");

// 非数值（如文本）视为缺失，不参与标尺。
const nonNumeric = monitoringTrendScaleView({
  points: [{ date: "a", value: "12" }, { date: "b", value: 24 }],
});
check(nonNumeric.mode === MONITORING_TREND_MODE_BARS && nonNumeric.max === 24, "non-numeric values are treated as missing");
check(nonNumeric.items[0].value === null, "string values are not coerced into the scale");

// 顺序与日期保留，供视图逐点渲染。
check(realScale.items.map((item) => item.date).join(",") === "2026-01-10,2026-02-10,2026-03-10", "points keep their order and dates");

console.log(`medicalMonitoringTrendScale: ${passed} passed`);

assert.equal(monitoringTrendScaleView({unit:"mg/L", points:[{value:1},{value:2,unit:"g/L"}]}).mode, MONITORING_TREND_MODE_VALUES);
assert.equal(mixedUnits.items[0].unit, "mg/L");
assert.equal(mixedUnits.items[1].unit, "g/L");
assert.ok(monitoringTrendScaleView({points:[{value:0.001},{value:100}]}).items[0].heightPercent > 0);

assert.equal(monitoringTrendScaleView({points:[{value:"<5"}]}).items[0].displayValue,"<5");
