import { useEffect, useRef, useState } from "react";
import { serializeMedicalMonitoringRouteState } from "./medicalMonitoringRouteState.mjs";
import {
  activePageFromMonitoringRoute,
  clearMedicalMonitoringProductRouteState,
  initialMedicalMonitoringBrowserState,
  initialMedicalMonitoringProductBrowserState,
  medicalMonitoringBrowserTarget,
  parseMedicalMonitoringBrowserLocation,
} from "./medicalMonitoringBrowserRoute.mjs";

const MONITORING_PATH = "/monitoring";

export function useMedicalMonitoringBrowserState(defaultSubjectId = "") {
  const initialProductRouteRef = useRef(initialMedicalMonitoringProductBrowserState());
  const initialRouteRef = useRef(initialMedicalMonitoringBrowserState());
  const returnScopeRef = useRef(initialRouteRef.current.scope || "trial");
  const returnSiteIdRef = useRef(initialRouteRef.current.site_id || "");
  const [productRouteState, setProductRouteState] = useState(initialProductRouteRef.current);
  const [routeState, setRouteState] = useState(initialRouteRef.current);
  const [focusRiskId, setFocusRiskId] = useState(
    initialRouteRef.current.risk_instance_id || initialRouteRef.current.risk_key || "",
  );
  const [subjectViewFocusRiskId, setSubjectViewFocusRiskId] = useState("");

  return {
    initialProductRouteRef,
    initialRouteRef,
    initialActivePage: initialProductRouteRef.current.isProduct
      ? "monitoringProduct"
      : typeof window !== "undefined" && window.location.pathname === "/monitoring"
        ? activePageFromMonitoringRoute(initialRouteRef.current)
        : "overview",
    initialProjectId: initialProductRouteRef.current.canonical?.project_ref || "",
    initialSubjectId: initialRouteRef.current.subject_id || defaultSubjectId,
    returnScopeRef,
    returnSiteIdRef,
    productRouteState,
    setProductRouteState,
    routeState,
    setRouteState,
    focusRiskId,
    setFocusRiskId,
    subjectViewFocusRiskId,
    setSubjectViewFocusRiskId,
  };
}

// R28-08：导航身份——只有视图/项目/结果身份层面的变化才算一次「导航」，
// 入浏览器历史；同身份内的参数微调（滚动位置、流选择、筛选等）仍用
// replaceState，避免历史栈被高频参数刷屏。
function navigationIdentityOf(target, activePage) {
  if (target.kind === "product") {
    const c = target.canonical || {};
    return [
      "product",
      c.view || "",
      c.project_ref || "",
      c.public_run_token || "",
      c.result_context_token || "",
      c.site_ref || "",
      c.subject_ref || "",
      c.risk_instance_ref || "",
      c.source_locator_ref || "",
      c.event_ref || "",
    ].join("|");
  }
  if (target.kind === "legacy") {
    const r = target.routeState || {};
    return [
      "legacy",
      activePage,
      r.project_id || "",
      r.scope || "",
      r.subject_id || "",
      r.view || "",
      r.risk_instance_id || "",
      r.risk_key || "",
    ].join("|");
  }
  return `${target.kind}:${activePage}`;
}

export function useMedicalMonitoringBrowserSync({
  activePage,
  setActivePage,
  activeProjectId,
  setActiveProjectId,
  selectedSubject,
  setSelectedSubject,
  writingNavigationDirty,
  productRouteState,
  setProductRouteState,
  routeState,
  setRouteState,
  setFocusRiskId,
  returnScopeRef,
  returnSiteIdRef,
}) {
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const handlePopState = () => {
      const isMonitoringPath = window.location.pathname === "/monitoring";
      if (isMonitoringPath && activePage === "writing" && writingNavigationDirty) {
        const preservedSearch = clearMedicalMonitoringProductRouteState(window.location.search);
        window.history.replaceState(window.history.state, "", `/${preservedSearch}${window.location.hash}`);
        return;
      }
      if (!isMonitoringPath) {
        if (["monitoring", "monitoringProduct", "subjectTimeline", "patientProfile"].includes(activePage)) {
          setActivePage("overview");
        }
        return;
      }
      const parsedLocation = parseMedicalMonitoringBrowserLocation(window.location);
      if (parsedLocation.kind === "product") {
        setProductRouteState(parsedLocation.productRoute);
        if (parsedLocation.productRoute.canonical?.project_ref) {
          setActiveProjectId(parsedLocation.productRoute.canonical.project_ref);
        }
        setActivePage("monitoringProduct");
        return;
      }
      const nextRoute = parsedLocation.routeState || {};
      if (nextRoute.view === "checklist") {
        returnScopeRef.current = nextRoute.scope || "trial";
        returnSiteIdRef.current = nextRoute.site_id || "";
      }
      setRouteState(nextRoute);
      setFocusRiskId(nextRoute.risk_instance_id || nextRoute.risk_key || "");
      if (nextRoute.subject_id) setSelectedSubject(nextRoute.subject_id);
      if (nextRoute.project_id) setActiveProjectId(nextRoute.project_id);
      setActivePage(activePageFromMonitoringRoute(nextRoute));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [
    activePage,
    returnScopeRef,
    returnSiteIdRef,
    setActivePage,
    setActiveProjectId,
    setFocusRiskId,
    setProductRouteState,
    setRouteState,
    setSelectedSubject,
    writingNavigationDirty,
  ]);

  const lastNavigationSyncRef = useRef({ url: "", identity: "" });
  useEffect(() => {
    if (typeof window === "undefined") return;
    const target = medicalMonitoringBrowserTarget({
      activePage,
      activeProjectId,
      selectedSubject,
      routeState,
      productRouteState,
      currentPath: window.location.pathname,
      currentSearch: window.location.search,
      currentHash: window.location.hash,
    });
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    const identity = navigationIdentityOf(target, activePage);
    if (target.url && target.url !== currentUrl) {
      // R28-08：监查视图此前一律replaceState——历史栈不入监查视图，
      // 结果层按浏览器后退直接落出应用（实测退到chrome://新标签页）。
      // 现按导航身份区分：身份变化（换视图/换项目/换结果/进入监查）
      // pushState入栈（popstate已有处理器可复原），同身份参数微调仍
      // replace。URL未变时只记身份，不产生历史项。
      const enteringMonitoring = !currentUrl.startsWith(MONITORING_PATH)
        && target.url.startsWith(MONITORING_PATH);
      const meaningfulMove = identity !== lastNavigationSyncRef.current.identity || enteringMonitoring;
      if (meaningfulMove && lastNavigationSyncRef.current.url !== target.url) {
        window.history.pushState(window.history.state, "", target.url);
      } else {
        window.history.replaceState(window.history.state, "", target.url);
      }
    }
    lastNavigationSyncRef.current = { url: target.url || currentUrl, identity };
    if (target.kind !== "legacy") return;
    setRouteState((current) => {
      const currentSerialized = serializeMedicalMonitoringRouteState(current);
      const nextSerialized = serializeMedicalMonitoringRouteState(target.routeState);
      return currentSerialized === nextSerialized ? current : target.routeState;
    });
  }, [
    activePage,
    activeProjectId,
    productRouteState,
    routeState,
    selectedSubject,
    setRouteState,
  ]);
}
