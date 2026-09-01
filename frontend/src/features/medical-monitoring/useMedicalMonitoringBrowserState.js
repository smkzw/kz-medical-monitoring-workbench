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
    if (target.url && target.url !== currentUrl) {
      window.history.replaceState(window.history.state, "", target.url);
    }
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
