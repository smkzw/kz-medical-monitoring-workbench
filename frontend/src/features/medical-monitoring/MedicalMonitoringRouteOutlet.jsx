import MedicalMonitoringPage from "./MedicalMonitoringPage.jsx";
import { isMedicalMonitoringPage } from "./medicalMonitoringRouteOutletState.mjs";

function SectionLoading() {
  return (
    <section className="panel empty-state" role="status" aria-live="polite">
      正在读取项目与模块配置，请稍候…
    </section>
  );
}

// R30-03：来源清单读取失败是「状态不可知」，不是「功能未配置」——
// 中间态/故障态不得渲染成未配置结论，也不得诱导对已配置项目重复激活。
function ManifestReadError({ onRetry, retryBusy }) {
  return (
    <main className="page">
      <section className="panel empty-state" role="alert">
        <p>项目模块配置读取失败，当前无法确认该项目是否已启用医学监查。请重试；若持续失败请检查服务状态。</p>
        <p style={{ marginTop: 12 }}>
          <button type="button" className="primary-button" onClick={onRetry} disabled={retryBusy}>
            {retryBusy ? "正在重试…" : "重试读取配置"}
          </button>
        </p>
      </section>
    </main>
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
  listReadFailed = false,
  manifestReadState = "none",
  onRetryManifestRead,
  manifestRetryBusy = false,
}) {
  if (!isMedicalMonitoringPage(activePage)) return null;
  if (!monitoringProjectId && activePage !== "monitoringProduct") {
    const listPending = !projectsLoaded && !listReadFailed;
    // R30-03：清单仍在读取（列表或来源清单任一在途）时不得以「功能未
    // 配置」错误态渲染——恢复期中间态曾被当成未配置，误导用户对已配
    // 置项目重复激活。
    if (listPending || manifestReadState === "pending") {
      return (
        <main className="page">
          <SectionLoading />
        </main>
      );
    }
    if (manifestReadState === "error") {
      return (
        <ManifestReadError
          onRetry={onRetryManifestRead}
          retryBusy={manifestRetryBusy}
        />
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
