import MedicalMonitoringPage from "./MedicalMonitoringPage.jsx";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

function SectionLoading() {
  return (
    <section className="panel empty-state" role="status" aria-live="polite">
      正在读取项目与模块配置，请稍候…
    </section>
  );
}

export default function MedicalMonitoringRouteOutlet({
  activePage,
  productRouteState,
  onProductRouteChange,
  onProductReturn,
  UnavailableComponent,
  monitoringProjectId,
  activeProjectId = "",
  onModuleEnabled,
  projectsLoaded = true,
}) {
  if (!isMedicalMonitoringPage(activePage)) return null;
  if (!monitoringProjectId && activePage !== "monitoringProduct") {
    if (!projectsLoaded) {
      // R5冲刺（R2-11）：项目清单仍在加载时不得以「功能未配置」错误态
      // 渲染——刷新回填期曾出现误导性的红/灰警示。
      return (
        <main className="page">
          <SectionLoading />
        </main>
      );
    }
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
