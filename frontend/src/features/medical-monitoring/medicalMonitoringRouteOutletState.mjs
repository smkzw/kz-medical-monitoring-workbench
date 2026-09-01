const MONITORING_PAGES = new Set([
  "monitoringProduct",
  "monitoring",
  "subjectTimeline",
  "patientProfile",
]);

export function isMedicalMonitoringPage(activePage) {
  return MONITORING_PAGES.has(activePage);
}
