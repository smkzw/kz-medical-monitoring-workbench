import { useCallback, useEffect, useMemo, useState } from "react";
import {
  G6SyntheticAdapterError,
  createG6SyntheticAdapter,
  fetchG6SyntheticBundle,
} from "./medicalMonitoringG6Adapter.mjs";
import {
  g6SeverityTone,
  selectG6FlowSubjects,
} from "./medicalMonitoringG6Projection.mjs";
import "./medicalMonitoringG6.css";

const FLOW_CANVAS_MIN_WIDTH = 1240;
const FLOW_CANVAS_HEIGHT = 300;
const RISK_LABELS = Object.freeze({ high: "高", medium: "中", low: "低", none: "无" });
const RECORD_STATE_LABELS = Object.freeze({
  available: "资料已收到",
  missing: "资料待补",
  conflict: "存在冲突",
  partial_failure: "部分返回",
  complete_failure: "未返回",
});

function text(value, fallback = "") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function errorText(error) {
  if (!error) return "";
  if (error instanceof G6SyntheticAdapterError) return error.message;
  return "合成演练资料暂不可用，已停止显示。";
}

function severityLabel(risk) {
  return RISK_LABELS[risk?.severity] || text(risk?.severity_label, "待确认");
}

function pathLabel(subject) {
  return (subject?.path_stage_labels || []).join(" → ") || "研究状态待确认";
}

function recordStateLabel(state) {
  return RECORD_STATE_LABELS[state] || "资料状态待确认";
}

function FlowLink({ link, nodePositions, onSelect }) {
  const from = nodePositions.get(link.from_stage_ref);
  const to = nodePositions.get(link.to_stage_ref);
  if (!from || !to) return null;
  const zero = link.count === 0;
  const midpointX = (from.x + to.x) / 2;
  const midpointY = (from.y + to.y) / 2;
  return (
    <g
      className={`g6-flow-link${zero ? " is-zero" : ""}`}
      data-flow-link={link.ref}
      data-flow-link-count={String(link.count)}
      role="button"
      tabIndex={0}
      aria-label={`${text(link.from_stage_label, "阶段")}到${text(link.to_stage_label, "阶段")}，${link.count}人`}
      onClick={() => onSelect(link)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(link);
        }
      }}
    >
      <line className="g6-flow-link-hitarea" x1={`${from.x}%`} y1={`${from.y}%`} x2={`${to.x}%`} y2={`${to.y}%`} />
      <line x1={`${from.x}%`} y1={`${from.y}%`} x2={`${to.x}%`} y2={`${to.y}%`} vectorEffect="non-scaling-stroke" />
      <text x={`${midpointX}%`} y={`${midpointY}%`} dy="-5" textAnchor="middle">{link.count}</text>
    </g>
  );
}

function FlowChart({ flow, selection, onSelectNode, onSelectLink }) {
  const nodePositions = useMemo(() => {
    const map = new Map();
    const columns = Math.max(...(flow?.nodes || []).map((node) => Number(node.column) || 0), 0) + 1;
    const rows = Math.max(...(flow?.nodes || []).map((node) => Number(node.row) || 0), 0) + 1;
    (flow?.nodes || []).forEach((node) => {
      map.set(node.ref, {
        x: ((Number(node.column) || 0) + 0.5) / columns * 100,
        y: ((Number(node.row) || 0) + 0.5) / rows * 100,
      });
    });
    return map;
  }, [flow]);
  if (!flow || flow.state === "blocked") {
    return <p className="g6-inline-blocked">阶段人数暂无法核对，请检查本次数据范围。</p>;
  }
  return (
    <div className="g6-flow-canvas" data-g6-flow-chart style={{ minWidth: FLOW_CANVAS_MIN_WIDTH, minHeight: FLOW_CANVAS_HEIGHT }}>
      <svg className="g6-flow-lines" width="100%" height="100%" aria-label="研究状态流向连线">
        <title>研究状态流向连线</title>
        {(flow.links || []).map((link) => <FlowLink key={link.ref} link={link} nodePositions={nodePositions} onSelect={onSelectLink} />)}
      </svg>
      <div className="g6-flow-nodes" aria-label="研究状态流向节点">
        {(flow.nodes || []).map((node) => {
          const active = selection?.nodeRef === node.ref;
          return (
            <button
              type="button"
              key={node.ref}
              className={`g6-flow-node${active ? " is-selected" : ""}${node.current_count === 0 ? " is-zero" : ""}`}
              data-flow-node={node.ref}
              data-flow-node-count={String(node.current_count)}
              style={{ gridColumn: Number(node.column) + 1, gridRow: Number(node.row) + 1 }}
              aria-pressed={active}
              onClick={() => onSelectNode(node)}
            >
              <span className="g6-flow-node-label">{node.label}</span>
              <strong>{node.current_count}</strong>
              <small>当前人数 · 到达 {node.reached_count}</small>
              {node.risk_count > 0 ? <em>{node.risk_count} 名需关注</em> : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MetricCard({ label, value, note, tone = "quiet" }) {
  return (
    <article className={`g6-metric-card ${tone}`} data-g6-metric={label}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

function RunProgress({ progress, onLeave }) {
  if (!progress) return null;
  const running = progress.state === "running";
  const complete = progress.state === "complete";
  return (
    <section className={`g6-run-progress ${running ? "is-running" : ""}`} data-g6-progress={progress.state} aria-label="本轮分析进度">
      <div className="g6-run-progress-head">
        <div>
          <span className="g6-eyebrow">本轮分析</span>
          <h2>{complete ? `本轮分析已完成 · ${progress.terminal_label}` : running ? "正在整理本轮资料" : "已准备本轮分析"}</h2>
        </div>
        <div className="g6-run-progress-actions">
          {onLeave ? <button type="button" className="g6-button quiet" onClick={onLeave}>离开进度页</button> : null}
        </div>
      </div>
      <div className="g6-progress-row">
        <div className="g6-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progress.percent}>
          <span style={{ width: `${progress.percent}%` }} />
        </div>
        <strong>{progress.percent}%</strong>
      </div>
      <p className="g6-progress-detail" aria-live="polite">{progress.detail}</p>
      <ol className="g6-progress-steps">
        {(progress.steps || []).map((step) => <li key={step.key} className={`is-${step.state}`}><span aria-hidden="true" />{step.label}</li>)}
      </ol>
    </section>
  );
}

function RiskList({ risks, subjects, onOpenSubject }) {
  const subjectByRef = new Map((subjects || []).map((subject) => [subject.subject_ref, subject]));
  return (
    <section className="g6-risk-summary" data-g6-risk-summary data-g6-reading-column aria-labelledby="g6-risk-heading">
      <div className="g6-section-heading">
        <div>
          <span className="g6-eyebrow">优先阅读</span>
          <h2 id="g6-risk-heading">中高风险与本轮变化</h2>
        </div>
        <span className="g6-section-count">{risks.length} 条</span>
      </div>
      {risks.length ? (
        <ul className="g6-risk-list">
          {risks.map((risk) => {
            const subject = subjectByRef.get(risk.subject_ref);
            return (
              <li key={risk.risk_ref} className={`g6-risk-row ${g6SeverityTone(risk.severity)}`}>
                <span className="g6-risk-dot" aria-hidden="true" />
                <div className="g6-risk-copy">
                  <strong>{risk.title}</strong>
                  <span>{subject?.subject_label || "受试者"} · {risk.state_label}</span>
                </div>
                <span className="g6-risk-level">{severityLabel(risk)}</span>
                <button type="button" className="g6-button small" onClick={() => onOpenSubject(subject?.subject_ref)}>查看旅程</button>
              </li>
            );
          })}
        </ul>
      ) : <p className="g6-empty-copy">当前项目没有需要优先阅读的风险提示。</p>}
    </section>
  );
}

function FlowTable({ flow, selection, onClear }) {
  const selectedSubjects = selectG6FlowSubjects(flow, selection || {});
  return (
    <section className="g6-flow-table-wrap" data-g6-flow-table aria-labelledby="g6-flow-table-heading">
      <div className="g6-section-heading compact">
        <div>
          <span className="g6-eyebrow">同源明细</span>
          <h3 id="g6-flow-table-heading">当前筛选下的受试者</h3>
        </div>
        <div className="g6-table-tools">
          <span>{selectedSubjects.length} 人</span>
          {selection && (selection.nodeRef || selection.linkRef || selection.centerRef) ? <button type="button" className="g6-text-button" onClick={onClear}>清除筛选</button> : null}
        </div>
      </div>
      <div className="g6-table-scroll">
        <table>
          <thead><tr><th>受试者</th><th>中心</th><th>当前状态</th><th>流向路径</th><th>风险</th></tr></thead>
          <tbody>
            {selectedSubjects.map((subject) => (
              <tr key={subject.subject_ref}>
                <td>{subject.subject_label}</td>
                <td>{subject.center_label}</td>
                <td>{subject.current_stage_label}</td>
                <td>{pathLabel(subject)}</td>
                <td>{subject.risk_state === "none" ? "无风险" : text(subject.risk_label_zh, "需关注")}</td>
              </tr>
            ))}
            {!selectedSubjects.length ? <tr><td colSpan="5">当前筛选没有受试者。</td></tr> : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Journey({ journey, selectedEvent, onSelectEvent }) {
  if (!journey || journey.state === "blocked") {
    return <section className="g6-journey-panel is-blocked"><p>{journey?.notice || "当前受试者无法确认，请返回项目总览。"}</p></section>;
  }
  const eventMap = new Map((journey.events || []).map((event) => [event.event_ref, event]));
  return (
    <section className="g6-journey-panel" data-g6-journey aria-labelledby="g6-journey-heading">
      <div className="g6-section-heading">
        <div>
          <span className="g6-eyebrow">受试者医学旅程</span>
          <h2 id="g6-journey-heading">按时间查看事件与风险</h2>
          <p>时间从左到右；同一访视的多域事件并列保留，不以卡片顺序代替时间顺序。</p>
        </div>
        <span className="g6-section-count">{journey.events.length} 条事件</span>
      </div>
      <div className="g6-journey-layout">
        <div className="g6-journey-scroll" data-g6-journey-scroll tabIndex="0" aria-label="可横向滚动的访视轴">
          <div className="g6-journey-axis" data-g6-journey-axis style={{ minWidth: `${Math.max(920, journey.visits.length * 184)}px` }}>
            <div className="g6-journey-axis-head">
              <span className="g6-journey-lane-label">访视</span>
              <div className="g6-journey-visits">
                {journey.visits.map((visit) => <div className="g6-journey-visit" key={visit.visit_ref}><strong>{visit.label}</strong><small>{visit.date_label}</small></div>)}
              </div>
            </div>
            <div className="g6-journey-lanes">
              {(journey.domains || []).map((domain) => (
                <div className="g6-journey-lane" data-g6-journey-lane={domain.key} key={domain.key}>
                  <span className="g6-journey-lane-label"><b className={`g6-domain-swatch ${domain.tone}`}>{domain.shortLabel}</b>{domain.label}</span>
                  <div className="g6-journey-lane-events">
                    {journey.visits.map((visit) => (
                      <div className="g6-journey-cell" key={`${domain.key}:${visit.visit_ref}`}>
                        {(visit.events || []).filter((event) => event.domain === domain.key).map((event) => {
                          const selected = selectedEvent?.event_ref === event.event_ref;
                          return (
                            <button type="button" key={event.event_ref} className={`g6-event-marker ${event.shape} ${event.tone}${selected ? " is-selected" : ""}`} data-g6-event-marker={event.event_ref} aria-pressed={selected} aria-label={`${domain.label}：${event.label}`} onClick={() => onSelectEvent(event)}>
                              <span aria-hidden="true" /><small>{event.label}</small>
                            </button>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <aside className="g6-event-detail" data-g6-event-detail aria-live="polite">
          {selectedEvent ? (
            <>
              <span className="g6-eyebrow">事件详情</span>
              <h3>{selectedEvent.label}</h3>
              <dl>
                <div><dt>事件类别</dt><dd>{selectedEvent.domain_label}</dd></div>
                <div><dt>发生时间</dt><dd>{selectedEvent.date_label}</dd></div>
                <div><dt>资料状态</dt><dd>{recordStateLabel(selectedEvent.record_state)}</dd></div>
                <div><dt>记录类型</dt><dd>合成资料记录</dd></div>
              </dl>
              <p className="g6-source-note">来源记录已定位，可在当前受试者范围内继续核对。</p>
            </>
          ) : <p className="g6-empty-copy">点击访视轴上的事件，查看详情与资料状态。</p>}
          {journey.risks.length ? <div className="g6-journey-risk-list"><strong>相关风险</strong>{journey.risks.map((risk) => <span className={`g6-risk-chip ${g6SeverityTone(risk.severity)}`} key={risk.risk_ref}>{risk.severity_label} · {risk.title}</span>)}</div> : null}
        </aside>
      </div>
      {journey.unassigned_events?.length ? <p className="g6-inline-blocked">有事件尚未绑定到访视，时间轴保留当前范围并提示待核对。</p> : null}
      <div className="g6-journey-footnote">当前旅程窗口：{journey.axis.start} 至 {journey.axis.end} · 共 {eventMap.size} 条事件</div>
    </section>
  );
}

function CenterSummary({ centers, selectedCenterRef, onSelect }) {
  return (
    <section className="g6-center-summary" aria-labelledby="g6-center-heading">
      <div className="g6-section-heading compact">
        <div><span className="g6-eyebrow">中心范围</span><h3 id="g6-center-heading">中心分布</h3></div>
        <span className="g6-section-count">{centers.length} 个中心</span>
      </div>
      <div className="g6-center-grid">
        {(centers || []).map((center) => (
          <button type="button" key={center.center_ref} className={`g6-center-card${selectedCenterRef === center.center_ref ? " is-selected" : ""}${center.subject_count === 0 ? " is-zero" : ""}`} aria-pressed={selectedCenterRef === center.center_ref} onClick={() => onSelect(selectedCenterRef === center.center_ref ? "" : center.center_ref)}>
            <span>{center.center_label}</span>
            <strong>{center.subject_count}</strong>
            <small>{center.risk_count ? `${center.risk_count} 名需关注` : "当前无优先风险"}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function PageShell({ children, state = "ready", onBack }) {
  return (
    <main className="g6-synthetic-page" data-g6-synthetic-page data-g6-load-state={state} aria-label="合成医学监查工作台">
      <header className="g6-page-header">
        <div className="g6-header-copy"><span className="g6-eyebrow">医学监查 · 受众演练</span><h1>合成医学监查工作台</h1><p>使用隔离演练资料，核对从项目总览到受试者旅程的阅读路径。</p></div>
        <div className="g6-header-actions"><span className="g6-local-badge"><i aria-hidden="true" />本地演练资料</span><button type="button" className="g6-button quiet" onClick={onBack}>返回工作台</button></div>
      </header>
      <div className="g6-page-content" data-g6-content>{children}</div>
    </main>
  );
}

export function MedicalMonitoringG6SyntheticPage({ bundle: injectedBundle = null, adapter: providedAdapter = null, initialView = "overview" }) {
  const [bundle, setBundle] = useState(injectedBundle);
  const [loadState, setLoadState] = useState(() => (providedAdapter || injectedBundle ? "ready" : "loading"));
  const [loadError, setLoadError] = useState("");
  const [loadNonce, setLoadNonce] = useState(0);

  useEffect(() => {
    if (providedAdapter || injectedBundle) return undefined;
    let active = true;
    setLoadState("loading");
    setLoadError("");
    fetchG6SyntheticBundle()
      .then((nextBundle) => {
        if (!active) return;
        setBundle(nextBundle);
        setLoadState("ready");
      })
      .catch((error) => {
        if (!active) return;
        setLoadState("blocked");
        setLoadError(errorText(error));
      });
    return () => { active = false; };
  }, [injectedBundle, loadNonce, providedAdapter]);

  const adapterState = useMemo(() => {
    if (providedAdapter) return { adapter: providedAdapter, error: null };
    if (!bundle) return { adapter: null, error: null };
    try {
      return { adapter: createG6SyntheticAdapter({ bundle }), error: null };
    } catch (error) {
      return { adapter: null, error };
    }
  }, [bundle, providedAdapter]);
  const adapter = adapterState.adapter;
  const projects = useMemo(() => adapter?.listProjects() || [], [adapter]);
  const initialProject = projects[0] || null;
  const initialOverview = useMemo(() => initialProject && adapter ? adapter.getOverview(initialProject.ref) : null, [adapter, initialProject]);
  const initialSubject = initialOverview?.subjects?.[0]?.subject_ref || "";
  const initialJourney = useMemo(() => initialProject && initialSubject && adapter ? adapter.getJourney(initialProject.ref, initialSubject) : null, [adapter, initialProject, initialSubject]);
  const [projectRef, setProjectRef] = useState(initialProject?.ref || "");
  const [overview, setOverview] = useState(initialOverview);
  const [flow, setFlow] = useState(initialOverview?.flow || null);
  const [centerRef, setCenterRef] = useState("");
  const [flowSelection, setFlowSelection] = useState({});
  const [subjectRef, setSubjectRef] = useState(initialSubject);
  const [journey, setJourney] = useState(initialJourney);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [progress, setProgress] = useState(null);
  const [mode, setMode] = useState("full");
  const [view, setView] = useState(initialView === "journey" ? "journey" : "overview");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!adapter || projectRef || !projects[0]) return;
    const firstProject = projects[0];
    const nextOverview = adapter.getOverview(firstProject.ref);
    const nextSubject = nextOverview.subjects?.[0]?.subject_ref || "";
    setProjectRef(firstProject.ref);
    setOverview(nextOverview);
    setFlow(nextOverview.flow);
    setSubjectRef(nextSubject);
    setJourney(nextSubject ? adapter.getJourney(firstProject.ref, nextSubject) : null);
  }, [adapter, projectRef, projects]);

  const loadProject = useCallback((nextProjectRef) => {
    try {
      const nextOverview = adapter.getOverview(nextProjectRef);
      const nextSubject = nextOverview.subjects?.[0]?.subject_ref || "";
      setProjectRef(nextProjectRef);
      setOverview(nextOverview);
      setFlow(nextOverview.flow);
      setCenterRef("");
      setFlowSelection({});
      setSubjectRef(nextSubject);
      setJourney(nextSubject ? adapter.getJourney(nextProjectRef, nextSubject) : null);
      setSelectedEvent(null);
      setView("overview");
      setError("");
    } catch (caught) {
      setError(errorText(caught));
    }
  }, [adapter]);

  const loadSubject = useCallback((nextSubjectRef) => {
    try {
      setSubjectRef(nextSubjectRef);
      setJourney(adapter.getJourney(projectRef, nextSubjectRef));
      setSelectedEvent(null);
      setView("journey");
      setError("");
    } catch (caught) {
      setError(errorText(caught));
    }
  }, [adapter, projectRef]);

  const loadCenter = useCallback((nextCenterRef) => {
    try {
      setCenterRef(nextCenterRef);
      setFlow(adapter.getFlow(projectRef, nextCenterRef));
      setFlowSelection(nextCenterRef ? { centerRef: nextCenterRef } : {});
      setError("");
    } catch (caught) {
      setError(errorText(caught));
    }
  }, [adapter, projectRef]);

  const selectFlowNode = useCallback((node) => setFlowSelection({ nodeRef: node.ref }), []);
  const selectFlowLink = useCallback((link) => setFlowSelection({ linkRef: link.ref }), []);

  const startAnalysis = useCallback(() => {
    try {
      const prepared = adapter.prepareRun({ projectRef, mode });
      setProgress(adapter.startRun(prepared.run_ref));
      setView("progress");
      setError("");
    } catch (caught) {
      setError(errorText(caught));
    }
  }, [adapter, mode, projectRef]);

  useEffect(() => {
    if (!progress || progress.state !== "running") return undefined;
    const timer = globalThis.setInterval(() => {
      try {
        const next = adapter.readProgress(progress.run_ref);
        setProgress(next);
        if (next.state === "complete") {
          setOverview(adapter.getResult(next.run_ref));
          setFlow(adapter.getFlow(projectRef, centerRef));
        }
      } catch (caught) {
        setError(errorText(caught));
      }
    }, 180);
    return () => globalThis.clearInterval(timer);
  }, [adapter, centerRef, progress, projectRef]);

  const selectedProject = projects.find((project) => project.ref === projectRef) || initialProject;
  const subjects = overview?.subjects || [];
  const modes = adapter?.getModes() || [];
  const currentMode = modes.find((item) => item.key === mode);
  const pageError = loadError || errorText(adapterState.error);
  const onBack = () => { globalThis.location.href = "/"; };

  if (loadState === "loading" && !adapter) {
    return <PageShell state="loading" onBack={onBack}><section className="g6-progress-guidance"><h2>正在载入合成演练资料</h2><p>正在核对当前演练范围，请稍候。</p></section></PageShell>;
  }
  if (pageError || !adapter || !projects.length) {
    return <PageShell state="blocked" onBack={onBack}><section className="g6-progress-guidance" role="alert"><h2>合成演练资料暂不可用</h2><p>{pageError || "当前演练范围无法确认，已停止显示。"}</p>{!providedAdapter && !injectedBundle ? <button type="button" className="g6-button primary" onClick={() => setLoadNonce((value) => value + 1)}>重新载入</button> : null}</section></PageShell>;
  }

  return (
    <main className="g6-synthetic-page" data-g6-synthetic-page data-g6-load-state="ready" aria-label="合成医学监查工作台">
      <header className="g6-page-header">
        <div className="g6-header-copy"><span className="g6-eyebrow">医学监查 · 受众演练</span><h1>合成医学监查工作台</h1><p>使用隔离演练资料，核对从项目总览到受试者旅程的阅读路径。</p></div>
        <div className="g6-header-actions"><span className="g6-local-badge"><i aria-hidden="true" />本地演练资料</span><button type="button" className="g6-button quiet" onClick={onBack}>返回工作台</button></div>
      </header>
      <div className="g6-page-content" data-g6-content>
        <section className="g6-control-strip" aria-label="分析范围">
          <label className="g6-project-picker"><span>项目</span><select value={projectRef} onChange={(event) => loadProject(event.target.value)} data-g6-project-selector>{projects.map((project) => <option value={project.ref} key={project.ref}>{project.label}</option>)}</select></label>
          <div className="g6-mode-picker" role="group" aria-label="分析模式"><span>分析范围</span><div>{modes.map((item) => <button type="button" key={item.key} className={mode === item.key ? "is-selected" : ""} aria-pressed={mode === item.key} onClick={() => setMode(item.key)}>{item.label}</button>)}</div></div>
          <div className="g6-control-action"><span>{currentMode?.description || "请选择分析范围"}</span><button type="button" className="g6-button primary" data-g6-core-action onClick={startAnalysis} disabled={!projectRef || progress?.state === "running"}>开始本轮分析</button></div>
        </section>
        {error ? <div className="g6-alert" role="alert"><strong>当前操作未完成</strong><span>{error}</span><button type="button" onClick={() => setError("")}>知道了</button></div> : null}
        {progress ? <RunProgress progress={progress} onLeave={() => setView("overview")} /> : null}
        <nav className="g6-view-tabs" aria-label="工作区视图"><button type="button" className={view === "overview" ? "is-selected" : ""} aria-pressed={view === "overview"} onClick={() => setView("overview")}>项目总览</button><button type="button" className={view === "journey" ? "is-selected" : ""} aria-pressed={view === "journey"} data-g6-subject-selector onClick={() => setView("journey")}>受试者旅程</button>{view === "progress" ? <span className="g6-current-view">本轮进度</span> : null}</nav>
        {view === "progress" ? <section className="g6-progress-guidance"><p>你可以离开此页，分析仍会继续；完成后返回项目总览即可阅读结果。</p><button type="button" className="g6-button primary" onClick={() => setView("overview")}>返回项目总览</button></section> : null}
        {view === "overview" && overview ? (
          <>
            <section className="g6-overview-intro"><div><span className="g6-eyebrow">当前项目</span><h2>{selectedProject?.label || "项目总览"}</h2><p>{selectedProject?.focusText || "查看本轮风险、研究状态流向和中心分布。"}</p></div><span className="g6-result-badge">结果可阅读</span></section>
            <div className="g6-metric-grid" data-g6-column-grid data-columns="3"><MetricCard label="高风险" value={overview.metrics.highRisk} note="优先核对" tone={overview.metrics.highRisk ? "attention" : "quiet"} /><MetricCard label="中风险" value={overview.metrics.mediumRisk} note="结合事件阅读" tone={overview.metrics.mediumRisk ? "attention" : "quiet"} /><MetricCard label="受试者" value={overview.metrics.subjects} note="本轮覆盖" /><MetricCard label="中心" value={overview.metrics.centers} note="有受试者记录" /><MetricCard label="资料覆盖" value={`${overview.metrics.coverageComplete}/${overview.metrics.coverageTotal}`} note="完整或可读范围" /></div>
            <div className="g6-overview-grid"><RiskList risks={overview.risks} subjects={subjects} onOpenSubject={loadSubject} /><CenterSummary centers={overview.centers} selectedCenterRef={centerRef} onSelect={loadCenter} /></div>
            <section className="g6-flow-section" aria-labelledby="g6-flow-heading"><div className="g6-section-heading"><div><span className="g6-eyebrow">项目中心流向</span><h2 id="g6-flow-heading">知情同意 → 筛选 → 治疗 → 研究状态</h2><p>点击节点或连线筛选下方同源明细；零值分支也保留，便于核对范围。</p></div><span className="g6-section-count">{flow?.reconciliation?.subject_total || 0} 人</span></div><div className="g6-flow-scroll" data-g6-flow-scroll><FlowChart flow={flow} selection={flowSelection} onSelectNode={selectFlowNode} onSelectLink={selectFlowLink} /></div><FlowTable flow={flow} selection={flowSelection} onClear={() => setFlowSelection(centerRef ? { centerRef } : {})} /></section>
          </>
        ) : null}
        {view === "journey" && overview ? (
          <>
            <section className="g6-subject-toolbar"><label data-g6-subject-selector><span>选择受试者</span><select value={subjectRef} onChange={(event) => loadSubject(event.target.value)}>{subjects.map((subject) => <option value={subject.subject_ref} key={subject.subject_ref}>{subject.subject_label} · {subject.center_label}</option>)}</select></label><div className="g6-subject-context"><strong>{subjects.find((subject) => subject.subject_ref === subjectRef)?.subject_label || "受试者"}</strong><span>保留当前项目与中心范围</span></div></section>
            <Journey journey={journey} selectedEvent={selectedEvent} onSelectEvent={setSelectedEvent} />
          </>
        ) : null}
      </div>
      <footer className="g6-page-footer"><span>合成资料仅用于操作路径与结构阅读演练。</span><span>医学判断仍需依据经核对的真实来源。</span></footer>
    </main>
  );
}

export const G6SyntheticWorkbench = MedicalMonitoringG6SyntheticPage;
export default MedicalMonitoringG6SyntheticPage;
