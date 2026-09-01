import assert from "node:assert/strict";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

for (const page of ["monitoringProduct", "monitoring", "subjectTimeline", "patientProfile"]) {
  assert.equal(isMedicalMonitoringPage(page), true);
}
for (const page of ["overview", "writing", "eligibility", "safety", ""]) {
  assert.equal(isMedicalMonitoringPage(page), false);
}

console.log("medicalMonitoringRouteOutlet: route ownership passed");
