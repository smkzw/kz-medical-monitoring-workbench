import assert from "node:assert/strict";

import {
  normalizeMedicalMonitoringProductRouteState,
  parseMedicalMonitoringProductRouteState,
  serializeMedicalMonitoringProductRouteState,
} from "./medicalMonitoringProductRouteState.mjs";

const parsed = parseMedicalMonitoringProductRouteState(
  "?project_id=project-01&run_id=run-01&snapshot_id=snapshot-01&cutoff=2026-09-02"
    + "&view=journey&site_id=site-01&subject_id=subject-01&spine_id=spine-01"
    + "&start=2026-01-01&end=2026-09-02",
);
assert.equal(parsed.isProduct, true);
assert.equal(parsed.valid, true);
assert.equal(parsed.canonical.project_ref, "project-01");
assert.equal(parsed.canonical.subject_ref, "subject-01");

const normalized = normalizeMedicalMonitoringProductRouteState(parsed.canonical);
assert.equal(normalized.view, "journey");
assert.match(serializeMedicalMonitoringProductRouteState(normalized), /project_id=project-01/);

console.log("medicalMonitoringProductRouteState: canonical facade passed");
