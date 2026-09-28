import MedicalMonitoringPage from "./MedicalMonitoringPage.jsx";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

export default function MedicalMonitoringRouteOutlet({
  activePage,
  productRouteState,
  onProductRouteChange,
  onProductReturn,
  UnavailableComponent,
  monitoringProjectId,
  activeProjectId = "",
  onModuleEnabled,
}) {
  if (!isMedicalMonitoringPage(activePage)) return null;
  if (!monitoringProjectId && activePage !== "monitoringProduct") {
    return (
      <UnavailableComponent
        moduleKey="medical_monitoring"
        projectId={activeProjectId}
        onModuleEnabled={onModuleEnabled}
      />
    );
  }
  return (
    <MedicalMonitoringPage
      routeState={activePage === "monitoringProduct"
        ? productRouteState
        : { project_ref: monitoringProjectId, view: "overview" }}
      onRouteChange={onProductRouteChange}
      onReturn={onProductReturn}
    />
  );
}
