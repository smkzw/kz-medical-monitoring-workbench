import {
  clearMedicalMonitoringRouteState,
  parseMedicalMonitoringRouteState,
  serializeMedicalMonitoringRouteState,
} from "./medicalMonitoringRouteState.mjs";
import {
  normalizeMedicalMonitoringProductRouteState,
  parseMedicalMonitoringProductRouteState,
  serializeMedicalMonitoringProductRouteState,
} from "./medicalMonitoringProductRouteState.mjs";

const MONITORING_PATH = "/monitoring";
const LEGACY_MONITORING_PAGES = new Set(["monitoring", "subjectTimeline", "patientProfile"]);
const PRODUCT_ROUTE_KEYS = Object.freeze([
  "public_run_token",
  "result_context_token",
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

export const EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE = Object.freeze({
  isProduct: false,
  status: "legacy",
  valid: false,
  canonical: Object.freeze({}),
});

export function activePageFromMonitoringRoute(routeState) {
  if (routeState?.view === "timeline") return "subjectTimeline";
  if (routeState?.view === "profile") return "patientProfile";
  return "monitoring";
}

export function monitoringViewFromActivePage(activePage, fallback = "checklist") {
  if (activePage === "subjectTimeline") return "timeline";
  if (activePage === "patientProfile") return "profile";
  if (activePage === "monitoring") return "checklist";
  return fallback;
}

export function clearMedicalMonitoringProductRouteState(search = "") {
  const params = new URLSearchParams(clearMedicalMonitoringRouteState(search).replace(/^\?/, ""));
  PRODUCT_ROUTE_KEYS.forEach((key) => params.delete(key));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function parseMedicalMonitoringBrowserLocation(location = {}) {
  if (location.pathname !== MONITORING_PATH) {
    return Object.freeze({ kind: "outside", activePage: "overview" });
  }
  const productRoute = parseMedicalMonitoringProductRouteState(location.search || "");
  if (productRoute.isProduct) {
    return Object.freeze({ kind: "product", activePage: "monitoringProduct", productRoute });
  }
  const routeState = parseMedicalMonitoringRouteState(location.search || "");
  return Object.freeze({
    kind: "legacy",
    activePage: activePageFromMonitoringRoute(routeState),
    routeState,
  });
}

export function initialMedicalMonitoringBrowserState(location = globalThis.window?.location) {
  const parsed = parseMedicalMonitoringBrowserLocation(location || {});
  return parsed.kind === "legacy" ? parsed.routeState : {};
}

export function initialMedicalMonitoringProductBrowserState(location = globalThis.window?.location) {
  const parsed = parseMedicalMonitoringBrowserLocation(location || {});
  return parsed.kind === "product" ? parsed.productRoute : EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE;
}

export function medicalMonitoringBrowserTarget({
  activePage,
  activeProjectId = "",
  selectedSubject = "",
  routeState = {},
  productRouteState = EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE,
  currentPath = "",
  currentSearch = "",
  currentHash = "",
} = {}) {
  if (productRouteState?.isProduct || activePage === "monitoringProduct") {
    const canonical = normalizeMedicalMonitoringProductRouteState({
      ...(productRouteState?.canonical || {}),
      project_ref: activeProjectId || productRouteState?.canonical?.project_ref || "",
    });
    return Object.freeze({
      kind: "product",
      canonical,
      url: `${MONITORING_PATH}${serializeMedicalMonitoringProductRouteState(canonical)}${currentHash}`,
    });
  }

  if (!LEGACY_MONITORING_PAGES.has(activePage)) {
    if (currentPath !== MONITORING_PATH) return Object.freeze({ kind: "outside", url: "" });
    return Object.freeze({
      kind: "leave",
      url: `/${clearMedicalMonitoringProductRouteState(currentSearch)}${currentHash}`,
    });
  }

  const subjectView = activePage === "subjectTimeline" || activePage === "patientProfile";
  const scope = subjectView ? "subject" : routeState.scope || "trial";
  const nextRouteState = {
    ...routeState,
    project_id: activeProjectId || routeState.project_id,
    scope,
    site_id: scope === "site" ? routeState.site_id || "" : "",
    subject_id: scope === "subject" ? selectedSubject || routeState.subject_id || "" : "",
    view: monitoringViewFromActivePage(activePage, routeState.view),
  };
  return Object.freeze({
    kind: "legacy",
    routeState: nextRouteState,
    url: `${MONITORING_PATH}${serializeMedicalMonitoringRouteState(nextRouteState, currentSearch)}${currentHash}`,
  });
}
