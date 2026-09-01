import assert from "node:assert/strict";
import {
  EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE,
  activePageFromMonitoringRoute,
  clearMedicalMonitoringProductRouteState,
  initialMedicalMonitoringBrowserState,
  initialMedicalMonitoringProductBrowserState,
  medicalMonitoringBrowserTarget,
  monitoringViewFromActivePage,
  parseMedicalMonitoringBrowserLocation,
} from "./medicalMonitoringBrowserRoute.mjs";

assert.equal(activePageFromMonitoringRoute({ view: "timeline" }), "subjectTimeline");
assert.equal(activePageFromMonitoringRoute({ view: "profile" }), "patientProfile");
assert.equal(monitoringViewFromActivePage("monitoring"), "checklist");

const productLocation = {
  pathname: "/monitoring",
  search: "?project_id=p1&run_id=r1&snapshot_id=s1&cutoff=2026-09-02&view=overview",
};
const parsedProduct = parseMedicalMonitoringBrowserLocation(productLocation);
assert.equal(parsedProduct.kind, "product");
assert.equal(parsedProduct.productRoute.canonical.project_ref, "p1");
assert.equal(initialMedicalMonitoringProductBrowserState(productLocation).isProduct, true);
assert.deepEqual(initialMedicalMonitoringBrowserState(productLocation), {});

const legacyLocation = {
  pathname: "/monitoring",
  search: "?project_id=p1&scope=subject&subject_id=s01&view=checklist",
};
const parsedLegacy = parseMedicalMonitoringBrowserLocation(legacyLocation);
assert.equal(parsedLegacy.kind, "legacy");
assert.equal(parsedLegacy.activePage, "monitoring");
assert.equal(initialMedicalMonitoringBrowserState(legacyLocation).subject_id, "s01");
assert.deepEqual(initialMedicalMonitoringProductBrowserState(legacyLocation), EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE);

assert.equal(
  clearMedicalMonitoringProductRouteState("?project_id=p1&result_context_token=secret&source_locator_ref=l1&keep=1"),
  "?keep=1",
);

const productTarget = medicalMonitoringBrowserTarget({
  activePage: "monitoringProduct",
  activeProjectId: "p2",
  productRouteState: parsedProduct.productRoute,
  currentHash: "#risk",
});
assert.equal(productTarget.kind, "product");
assert.match(productTarget.url, /^\/monitoring\?/);
assert.match(productTarget.url, /project_id=p2/);
assert.match(productTarget.url, /#risk$/);

const legacyTarget = medicalMonitoringBrowserTarget({
  activePage: "patientProfile",
  activeProjectId: "p1",
  selectedSubject: "s02",
  routeState: { scope: "trial", view: "checklist", site_id: "site1" },
  currentSearch: "?unrelated=kept",
});
assert.equal(legacyTarget.kind, "legacy");
assert.equal(legacyTarget.routeState.scope, "subject");
assert.equal(legacyTarget.routeState.subject_id, "s02");
assert.equal(legacyTarget.routeState.site_id, "");
assert.match(legacyTarget.url, /unrelated=kept/);

const leaveTarget = medicalMonitoringBrowserTarget({
  activePage: "overview",
  currentPath: "/monitoring",
  currentSearch: "?result_context_token=secret&keep=1",
});
assert.equal(leaveTarget.url, "/?keep=1");

console.log("medicalMonitoringBrowserRoute: browser route ownership passed");
