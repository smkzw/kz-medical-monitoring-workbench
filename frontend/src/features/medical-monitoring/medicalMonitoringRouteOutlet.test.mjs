import assert from "node:assert/strict";
import { isMedicalMonitoringPage, monitoringRouteProjectIdFrom } from "./medicalMonitoringRouteOutletState.mjs";

for (const page of ["monitoringProduct", "monitoring", "subjectTimeline", "patientProfile"]) {
  assert.equal(isMedicalMonitoringPage(page), true);
}
for (const page of ["overview", "writing", "eligibility", "safety", ""]) {
  assert.equal(isMedicalMonitoringPage(page), false);
}

assert.equal(
  monitoringRouteProjectIdFrom(null, {
    modules: [{ module: "medical_monitoring", route_project_id: "synthetic-project", implementation_status: "synthetic_product_profile" }],
  }),
  "synthetic-project",
);
assert.equal(
  monitoringRouteProjectIdFrom(null, {
    modules: [{ module: "medical_monitoring", route_project_id: "real-project", implementation_status: "real_source_slice" }],
  }),
  "",
);
assert.equal(
  monitoringRouteProjectIdFrom({ route_bindings: { medical_monitoring: { route_project_id: "manifest-project" } } }, null),
  "manifest-project",
);

console.log("medicalMonitoringRouteOutlet: route ownership passed");
