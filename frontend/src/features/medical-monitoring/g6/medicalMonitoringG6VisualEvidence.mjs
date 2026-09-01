import { validateG6CanonicalBundle } from "./medicalMonitoringG6Adapter.mjs";

export const G6_REQUIRED_MEASUREMENT_KEYS = Object.freeze([
  "page",
  "content",
  "core_action",
  "risk_summary",
  "flow_chart",
  "flow_table_first_row",
  "journey_axis",
  "subject_selector",
]);

export const G6_PRODUCTION_VIEWPORTS = Object.freeze([
  Object.freeze({
    viewport_id: "desktop-1920",
    css_width: 1920,
    css_height: 1080,
    dpr: 1,
    raw_width: 1920,
    raw_height: 1080,
    content_max_width: 1760,
    left_gutter: 80,
    right_gutter: 80,
    columns: 3,
    reading_column_width: 760,
    primary_chart_width: 1700,
  }),
  Object.freeze({
    viewport_id: "desktop-2560",
    css_width: 2560,
    css_height: 1440,
    dpr: 1,
    raw_width: 2560,
    raw_height: 1440,
    content_max_width: 2240,
    left_gutter: 160,
    right_gutter: 160,
    columns: 3,
    reading_column_width: 780,
    primary_chart_width: 2180,
  }),
  Object.freeze({
    viewport_id: "desktop-3840",
    css_width: 3840,
    css_height: 2160,
    dpr: 1,
    raw_width: 3840,
    raw_height: 2160,
    content_max_width: 3200,
    left_gutter: 320,
    right_gutter: 320,
    columns: 3,
    reading_column_width: 820,
    primary_chart_width: 3140,
  }),
]);

const ELEMENT_SELECTORS = Object.freeze({
  page: "[data-g6-synthetic-page]",
  content: "[data-g6-content]",
  core_action: "[data-g6-core-action]",
  risk_summary: "[data-g6-risk-summary]",
  flow_chart: "[data-g6-flow-chart]",
  flow_table_first_row: "[data-g6-flow-table] tbody tr:first-child",
  journey_axis: "[data-g6-journey-axis]",
  subject_selector: "[data-g6-subject-selector]",
});

function finite(value, fallback = null) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function round(value) {
  const number = finite(value);
  return number === null ? null : Math.round(number * 100) / 100;
}

function clone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function viewportValue(viewport, key, fallback = 0) {
  const value = finite(viewport?.[key]);
  return value === null ? fallback : value;
}

function rectSnapshot(element, viewport) {
  if (!element || typeof element.getBoundingClientRect !== "function") return null;
  const rect = element.getBoundingClientRect();
  const viewportWidth = viewportValue(viewport, "css_width");
  const viewportHeight = viewportValue(viewport, "css_height");
  const width = finite(rect?.width, 0);
  const height = finite(rect?.height, 0);
  const left = finite(rect?.left, 0);
  const top = finite(rect?.top, 0);
  const right = finite(rect?.right, left + width);
  const bottom = finite(rect?.bottom, top + height);
  const visibleWidth = Math.max(0, Math.min(right, viewportWidth) - Math.max(left, 0));
  const visibleHeight = Math.max(0, Math.min(bottom, viewportHeight) - Math.max(top, 0));
  const area = width * height;
  const visibleArea = visibleWidth * visibleHeight;
  return {
    left: round(left),
    top: round(top),
    right: round(right),
    bottom: round(bottom),
    width: round(width),
    height: round(height),
    visible_ratio: area > 0 ? round(Math.max(0, Math.min(1, visibleArea / area))) : 0,
  };
}

function requiredElement(root, selector, key) {
  if (!root || typeof root.querySelector !== "function") throw new TypeError("G6 measurement root must support querySelector");
  const element = root.querySelector(selector);
  if (!element) throw new Error(`g6_measurement_missing:${key}`);
  return element;
}

function scrollSnapshot(element) {
  return {
    scroll_left: round(finite(element?.scrollLeft, 0)),
    scroll_top: round(finite(element?.scrollTop, 0)),
    client_width: round(finite(element?.clientWidth, 0)),
    scroll_width: round(finite(element?.scrollWidth, finite(element?.clientWidth, 0))),
    client_height: round(finite(element?.clientHeight, 0)),
    scroll_height: round(finite(element?.scrollHeight, finite(element?.clientHeight, 0))),
  };
}

export function measureG6Layout(root, viewport = {}, options = {}) {
  const requestedKeys = Array.isArray(options?.requiredKeys)
    ? [...new Set(options.requiredKeys)]
    : [...G6_REQUIRED_MEASUREMENT_KEYS];
  if (requestedKeys.some((key) => !G6_REQUIRED_MEASUREMENT_KEYS.includes(key))) {
    throw new TypeError("G6 measurement contains an unknown required key");
  }
  if (!requestedKeys.length) throw new TypeError("G6 measurement requires at least one required key");
  const normalizedViewport = {
    viewport_id: String(viewport.viewport_id || `${viewport.css_width || 0}x${viewport.css_height || 0}`),
    css_width: viewportValue(viewport, "css_width"),
    css_height: viewportValue(viewport, "css_height"),
    dpr: viewportValue(viewport, "dpr", 1),
    raw_width: viewportValue(viewport, "raw_width", viewportValue(viewport, "css_width")),
    raw_height: viewportValue(viewport, "raw_height", viewportValue(viewport, "css_height")),
    browser_zoom: viewportValue(viewport, "browser_zoom", 1),
  };
  if (normalizedViewport.css_width <= 0 || normalizedViewport.css_height <= 0) {
    throw new TypeError("G6 viewport dimensions must be positive");
  }
  const elements = {};
  for (const key of requestedKeys) {
    const selector = ELEMENT_SELECTORS[key];
    elements[key] = rectSnapshot(requiredElement(root, selector, key), normalizedViewport);
  }
  const journeyRequired = requestedKeys.includes("journey_axis");
  const journeyScroller = journeyRequired
    ? requiredElement(root, "[data-g6-journey-scroll]", "journey_scroll")
    : null;
  const pageRect = elements.page || null;
  const contentRect = elements.content || null;
  return {
    schema: "mm-r8-g6-visual-measurement-v1",
    source: "actual_dom_measurement",
    required_keys: requestedKeys,
    viewport: normalizedViewport,
    layout: {
      content_width: contentRect?.width ?? null,
      left_gutter: contentRect?.left ?? null,
      right_gutter: contentRect ? round(normalizedViewport.css_width - (contentRect.right || 0)) : null,
      column_count: finite(root.querySelector("[data-g6-column-grid]")?.dataset?.columns, null),
      page_width: pageRect?.width ?? null,
      primary_chart_width: elements.flow_chart?.width ?? null,
      reading_column_width: finite(root.querySelector("[data-g6-reading-column]")?.getBoundingClientRect?.()?.width, null),
    },
    elements,
    scroll: {
      journey: journeyScroller ? scrollSnapshot(journeyScroller) : null,
      page: scrollSnapshot(root),
    },
    selector_contract: clone(ELEMENT_SELECTORS),
  };
}

export function validateG6Measurement(measurement) {
  const errors = [];
  const viewport = measurement?.viewport;
  if (!viewport || viewport.css_width <= 0 || viewport.css_height <= 0) errors.push("viewport");
  const requiredKeys = Array.isArray(measurement?.required_keys)
    ? measurement.required_keys
    : G6_REQUIRED_MEASUREMENT_KEYS;
  for (const key of requiredKeys) {
    const box = measurement?.elements?.[key];
    if (!G6_REQUIRED_MEASUREMENT_KEYS.includes(key)) {
      errors.push(`element_unknown:${key}`);
      continue;
    }
    if (!box || !(box.width >= 0) || !(box.height >= 0) || !(box.visible_ratio >= 0 && box.visible_ratio <= 1)) {
      errors.push(`element:${key}`);
    } else if (box.width < 32 || box.height < 32) {
      errors.push(`element_too_small:${key}`);
    }
  }
  if (measurement?.viewport?.browser_zoom !== 1) errors.push("browser_zoom");
  return Object.freeze({ valid: errors.length === 0, errors });
}


export function expectedG6Measurement(viewport) {
  const frozen = G6_PRODUCTION_VIEWPORTS.find((item) => item.viewport_id === viewport?.viewport_id)
    || G6_PRODUCTION_VIEWPORTS.find((item) => item.css_width === Number(viewport?.css_width) && item.css_height === Number(viewport?.css_height));
  if (!frozen) throw new TypeError("unknown G6 production viewport");
  const pageWidth = frozen.css_width;
  const contentLeft = frozen.left_gutter;
  const contentWidth = frozen.content_max_width;
  const element = (left, top, width, height) => ({
    left,
    top,
    right: left + width,
    bottom: top + height,
    width,
    height,
    visible_ratio: 1,
  });
  return {
    schema: "mm-r8-g6-visual-measurement-v1",
    source: "frozen_layout_expectation",
    required_keys: [...G6_REQUIRED_MEASUREMENT_KEYS],
    viewport: { ...frozen, browser_zoom: 1 },
    layout: {
      content_width: contentWidth,
      left_gutter: contentLeft,
      right_gutter: frozen.right_gutter,
      column_count: frozen.columns,
      page_width: pageWidth,
      primary_chart_width: frozen.primary_chart_width,
      reading_column_width: frozen.reading_column_width,
    },
    elements: {
      page: element(0, 0, pageWidth, frozen.css_height),
      content: element(contentLeft, 0, contentWidth, frozen.css_height),
      core_action: element(contentLeft + contentWidth - 220, 100, 200, 40),
      risk_summary: element(contentLeft, 170, frozen.reading_column_width, 120),
      flow_chart: element(contentLeft, 320, frozen.primary_chart_width, 360),
      flow_table_first_row: element(contentLeft, 720, frozen.primary_chart_width, 48),
      journey_axis: element(contentLeft, 880, frozen.primary_chart_width, 360),
      subject_selector: element(contentLeft + contentWidth - 300, 880, 280, 40),
    },
    scroll: {
      journey: { scroll_left: 0, scroll_top: 0, client_width: frozen.primary_chart_width, scroll_width: frozen.primary_chart_width, client_height: 360, scroll_height: 360 },
      page: { scroll_left: 0, scroll_top: 0, client_width: pageWidth, scroll_width: pageWidth, client_height: frozen.css_height, scroll_height: frozen.css_height },
    },
    selector_contract: clone(ELEMENT_SELECTORS),
  };
}

function normalizeMeasurement(measurement) {
  const validation = validateG6Measurement(measurement);
  if (!validation.valid) throw new Error(`g6_measurement_invalid:${validation.errors.join(",")}`);
  return clone(measurement);
}

export function buildG6EvidencePack({
  bundle,
  measurements = [],
  domSnapshots = [],
  interactions = [],
  adapterLedger = [],
} = {}) {
  const canonical = validateG6CanonicalBundle(bundle);
  const fixture = canonical.fixture;
  const binding = canonical.binding;
  const normalizedMeasurements = measurements.map(normalizeMeasurement);
  const productionViewports = new Map(G6_PRODUCTION_VIEWPORTS.map((item) => [item.viewport_id, item]));
  const measuredKeysByViewport = new Map();
  const unknownViewportIds = new Set();
  for (const measurement of normalizedMeasurements) {
    const viewportId = measurement.viewport?.viewport_id;
    if (!productionViewports.has(viewportId)) {
      unknownViewportIds.add(viewportId || "unknown");
      continue;
    }
    const keys = Array.isArray(measurement.required_keys) ? measurement.required_keys : G6_REQUIRED_MEASUREMENT_KEYS;
    const measuredKeys = measuredKeysByViewport.get(viewportId) || new Set();
    keys.forEach((key) => measuredKeys.add(key));
    measuredKeysByViewport.set(viewportId, measuredKeys);
  }
  if (unknownViewportIds.size) throw new Error(`g6_measurement_unknown_viewport:${[...unknownViewportIds].join(",")}`);
  const missingMeasurementKeys = G6_PRODUCTION_VIEWPORTS.flatMap((viewport) => {
    const measuredKeys = measuredKeysByViewport.get(viewport.viewport_id) || new Set();
    return G6_REQUIRED_MEASUREMENT_KEYS.filter((key) => !measuredKeys.has(key)).map((key) => ({ viewport_id: viewport.viewport_id, key }));
  });
  const missingViewports = G6_PRODUCTION_VIEWPORTS
    .filter((viewport) => missingMeasurementKeys.some((item) => item.viewport_id === viewport.viewport_id))
    .map((viewport) => viewport.viewport_id);
  return {
    schema: "mm-r8-g6-structural-evidence-pack-v1",
    acceptance_state: "not_evaluable_without_ego_lite",
    evidence_scope: "frontend_structural_support_only",
    execution: {
      browser_started: false,
      actual_app_started: false,
      visual_execution: "deferred_to_governed_packet",
      network_calls: 0,
      real_projects_read: false,
      real_model_calls: 0,
    },
    identity: {
      bundle_digest: canonical.bundle_digest,
      fixture_digest: fixture.fixture_digest,
      profile_binding_digest: fixture.profile_binding_digest,
      binding_digest: binding.binding_digest,
      app_version: canonical.app_version,
      contract_version: canonical.contract_version,
      synthetic_profile_id: fixture.synthetic_profile_id,
    },
    required_viewports: clone(G6_PRODUCTION_VIEWPORTS),
    missing_viewports: missingViewports,
    missing_measurement_keys: missingMeasurementKeys,
    measurements: normalizedMeasurements,
    dom_snapshots: clone(domSnapshots),
    interactions: clone(interactions),
    adapter_ledger: clone(adapterLedger),
    notes: [
      "本包只保存前端结构化测量和合成适配器账本，不能替代 ego(lite) 实际入口、视觉或生命周期证据。",
      "任何未完成的三视口测量或关键结构测量都保留为缺失项，不改写为通过。",
    ],
  };
}

export function serializeG6EvidencePack(pack) {
  return `${JSON.stringify(pack, null, 2)}\n`;
}
