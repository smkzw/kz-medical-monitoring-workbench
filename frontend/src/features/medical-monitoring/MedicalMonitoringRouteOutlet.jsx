import MedicalMonitoringPage from "./MedicalMonitoringPage.jsx";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

export default function MedicalMonitoringRouteOutlet({
  activePage,
  productRouteState,
  onProductRouteChange,
  onProductReturn,
  UnavailableComponent,
  monitoringProjectId,
}) {
  if (!isMedicalMonitoringPage(activePage)) return null;
  if (!monitoringProjectId && activePage !== "monitoringProduct") {
    return <UnavailableComponent moduleKey="medical_monitoring" />;
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
