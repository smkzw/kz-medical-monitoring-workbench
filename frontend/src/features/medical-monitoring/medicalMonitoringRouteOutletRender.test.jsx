// R30-03 regression fixture. 来源清单恢复期中间态不得渲染成「功能未配
// 置」，也不得诱导对已配置项目重复激活——在途=读取中；失败=诚实报错
// +重试入口；只有清单确实读到且无监查绑定时才落未配置结论。Bundled by
// medicalMonitoringRouteOutletRender.test.mjs via esbuild。
import { renderToStaticMarkup } from "react-dom/server";
import MedicalMonitoringRouteOutlet from "./MedicalMonitoringRouteOutlet.jsx";

function renderOutlet(props) {
  return renderToStaticMarkup(
    <MedicalMonitoringRouteOutlet
      activePage="monitoring"
      productRouteState={null}
      onProductRouteChange={() => {}}
      onProductReturn={() => {}}
      UnavailableComponent={({ moduleKey }) => (
        <div>{`功能未配置:${moduleKey}`}</div>
      )}
      monitoringProjectId=""
      activeProjectId="proj_user_test"
      onModuleEnabled={() => {}}
      projectsLoaded
      {...props}
    />,
  );
}

export const renders = {
  // 在途（清单尚未读到）：读取中，而非未配置。
  pending: renderOutlet({ manifestReadState: "pending" }),
  // 项目列表仍在读取：同样读取中。
  listPending: renderOutlet({ projectsLoaded: false, manifestReadState: "pending" }),
  // 清单读取失败：诚实报错+重试入口，而非未配置、不提供激活按钮。
  error: renderOutlet({ manifestReadState: "error" }),
  // 清单已读到且无监查绑定：才落未配置结论（真未配置）。
  unconfigured: renderOutlet({ manifestReadState: "ready" }),
  // 已解析出监查路由：正常渲染工作区出口（不走未配置）。
  routed: renderOutlet({ monitoringProjectId: "proj_user_test", manifestReadState: "ready" }),
};
