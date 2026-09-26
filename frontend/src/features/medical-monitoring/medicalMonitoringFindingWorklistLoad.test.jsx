// E1工作列表负载fixture（由 medicalMonitoringFindingWorklistLoad.test.mjs
// 经esbuild打包运行）。用真实QueryWorkspaceView渲染合成Finding工作列表，
// 导出渲染markup与耗时；排序/筛选/规范化由真实buildFindingCards
// （MedicalMonitoringProductLoop.jsx导出）在runner里计时。
// 合成DTO为正式Finding冻结DTO字段形态（finding_id/subject/site/状态/
// 分类型claims/逐条source refs），0模型调用、0真实SAR结果依赖。
import { renderToStaticMarkup } from "react-dom/server";
import { QueryWorkspaceView } from "./MedicalMonitoringWorkspace.jsx";
import { buildFindingCards } from "./MedicalMonitoringProductLoop.jsx";

const baseProjection = {
  subjects: [],
  currentRisks: [],
  aiQueryFindings: [],
  domains: [],
  temporalSpine: {},
  aggregation: null,
};

export function renderWorklist(raw) {
  const started = performance.now();
  const findingCards = buildFindingCards(raw);
  const normalizedMs = performance.now() - started;
  const renderStarted = performance.now();
  const markup = renderToStaticMarkup(
    <QueryWorkspaceView
      payload={{
        publicResultContext: true,
        projection: {
          ...baseProjection,
          findingCards,
          queryDraftRows: [],
          queryFindingsMeta: {
            shape: "finding_dto_v1",
            state: "completed_with_findings",
            total: findingCards.length,
            gaps: 0,
            queryDrafts: [],
          },
        },
      }}
      route={{ view: "queries" }}
      onSubjectSelect={() => {}}
      onSource={() => {}}
      onFindingSelect={() => {}}
      onBack={() => {}}
    />,
  );
  const renderMs = performance.now() - renderStarted;
  return { markup, findingCards, normalizedMs, renderMs };
}
