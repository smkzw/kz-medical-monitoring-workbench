// Trend-chart scale for indicator points (design v2 §10: 真实数值域，缺失不画零，
// 同单位可比较，不能截顶把不同值画一样).
//
// Bars mode draws a zero-based linear scale: heightPercent = value / max(known values).
// Any known negative value or mixed point-level units breaks the shared zero baseline,
// so the series falls back to "values" mode — true numbers as text, no bars, no scale
// claim. Missing values never render a bar in either mode.

export const MONITORING_TREND_MODE_BARS = "bars";
export const MONITORING_TREND_MODE_VALUES = "values";

function knownValue(point) {
  const value = point?.value;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function pointUnit(point) {
  const unit = point?.unit;
  return typeof unit === "string" ? unit.trim() : "";
}

export function monitoringTrendScaleView(indicator) {
  const points = Array.isArray(indicator?.points) ? indicator.points : [];
  const unit = typeof indicator?.unit === "string" ? indicator.unit.trim() : "";
  const items = points.map((point, index) => ({
    index,
    date: typeof point?.date === "string" ? point.date : "",
    value: knownValue(point),
    displayValue: typeof point?.value === "string" ? point.value : knownValue(point),
    unit: pointUnit(point) || unit,
    heightPercent: 0,
  }));

  const knownValues = items.map((item) => item.value).filter((value) => value !== null);
  const mixedPointUnits = (() => {
    const units = new Set(items.map((item) => item.unit));
    return units.size > 1;
  })();

  const negative = knownValues.some((value) => value < 0);
  const maxValue = knownValues.length ? Math.max(...knownValues) : null;

  let mode = MONITORING_TREND_MODE_BARS;
  let reason = "";
  if (negative) {
    mode = MONITORING_TREND_MODE_VALUES;
    reason = "negative";
  } else if (mixedPointUnits) {
    mode = MONITORING_TREND_MODE_VALUES;
    reason = "mixed_units";
  } else if (maxValue === null) {
    mode = MONITORING_TREND_MODE_VALUES;
    reason = "no_known_values";
  }

  if (mode === MONITORING_TREND_MODE_BARS) {
    for (const item of items) {
      if (item.value === null) continue;
      const ratio = maxValue > 0 ? item.value / maxValue : 0;
      item.heightPercent = Math.min(1, Math.max(0, ratio)) * 100;
    }
    return {
      mode,
      reason,
      unit,
      max: maxValue,
      items,
    };
  }
  return {
    mode,
    reason,
    unit,
    max: null,
    items,
  };
}
