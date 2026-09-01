import MedicalMonitoringPage from "./MedicalMonitoringPage.jsx";
import {
  PatientProfilePage,
  SubjectTimelinePage,
} from "./MedicalMonitoringSubjectViews";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

export default function MedicalMonitoringRouteOutlet({
  activePage,
  productRouteState,
  onProductRouteChange,
  onProductReturn,
  WorkspaceComponent,
  workspaceProps,
  ReadUnavailableComponent,
  sourceManifestError,
  UnavailableComponent,
  monitoringProjectId,
  monitoringReady,
  monitoringReadinessMessage,
  subject,
  subjectRouteError,
  setSelectedSubject,
  onNavigateWorkspace,
  subjectCatalog,
  subjectViewFocusRiskId,
  metricConfigurationContext,
}) {
  if (!isMedicalMonitoringPage(activePage)) return null;
  if (activePage === "monitoringProduct") {
    return (
      <MedicalMonitoringPage
        routeState={productRouteState}
        onRouteChange={onProductRouteChange}
        onReturn={onProductReturn}
      />
    );
  }
  if (activePage === "monitoring") {
    if (sourceManifestError) {
      return <ReadUnavailableComponent surface="monitoring_source_manifest" error={sourceManifestError} />;
    }
    if (!monitoringProjectId) return <UnavailableComponent moduleKey="medical_monitoring" />;
    return <WorkspaceComponent key={monitoringProjectId} {...workspaceProps} />;
  }

  if (!monitoringProjectId || !monitoringReady) {
    return (
      <UnavailableComponent
        moduleKey="medical_monitoring"
        message={monitoringReadinessMessage || "当前项目医学监查来源尚未达到可读取条件。"}
      />
    );
  }
  if (!subject) {
    const viewName = activePage === "subjectTimeline" ? "Subject Timeline" : "Patient Profile";
    return (
      <UnavailableComponent
        moduleKey="medical_monitoring"
        message={subjectRouteError || `当前项目尚无可用于${viewName}的真实受试者数据。`}
      />
    );
  }
  if (activePage === "subjectTimeline") {
    return (
      <SubjectTimelinePage
        subject={subject}
        setSelectedSubject={setSelectedSubject}
        onNavigate={onNavigateWorkspace}
        subjectCatalog={subjectCatalog}
        focusRiskId={subjectViewFocusRiskId}
        metricConfigurationContext={metricConfigurationContext}
      />
    );
  }
  return (
    <PatientProfilePage
      subject={subject}
      setSelectedSubject={setSelectedSubject}
      onNavigate={onNavigateWorkspace}
      subjectCatalog={subjectCatalog}
      focusRiskId={subjectViewFocusRiskId}
    />
  );
}
