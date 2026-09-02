const MONITORING_PAGES = new Set([
  "monitoringProduct",
  "monitoring",
  "subjectTimeline",
  "patientProfile",
]);

export function isMedicalMonitoringPage(activePage) {
  return MONITORING_PAGES.has(activePage);
}

export function monitoringRouteProjectIdFrom(manifest, project) {
  const bound = manifest?.route_bindings?.medical_monitoring?.route_project_id;
  if (bound) return bound;
  const synthetic = (project?.modules || []).find(
    (module) => module?.module === "medical_monitoring"
      && module?.implementation_status === "synthetic_product_profile",
  );
  return synthetic?.route_project_id || "";
}
