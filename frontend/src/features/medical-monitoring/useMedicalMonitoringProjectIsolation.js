import { useCallback, useRef } from "react";
import {
  EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE,
  clearMedicalMonitoringProductRouteState,
} from "./medicalMonitoringBrowserRoute.mjs";

export function useMedicalMonitoringProjectIsolation({
  activeProjectId,
  setProductRouteState,
  setRouteState,
  setFocusRiskId,
  setSubjectViewFocusRiskId,
  setSelectedSubject,
  setWorkbenchInbox,
  setDataError,
  setSubjectRouteError,
  setProjectRouteError,
  returnScopeRef,
  returnSiteIdRef,
}) {
  const responseProjectIdRef = useRef(activeProjectId);
  responseProjectIdRef.current = activeProjectId;

  const resetProjectState = useCallback((nextPage) => {
    setProductRouteState(EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE);
    setRouteState({});
    setFocusRiskId("");
    setSubjectViewFocusRiskId("");
    setSelectedSubject("");
    setWorkbenchInbox(null);
    setDataError("");
    setSubjectRouteError("");
    setProjectRouteError("");
    returnScopeRef.current = "trial";
    returnSiteIdRef.current = "";
    if (typeof window === "undefined") return;
    const preservedSearch = clearMedicalMonitoringProductRouteState(window.location.search);
    const nextPath = ["monitoring", "subjectTimeline", "patientProfile"].includes(nextPage)
      ? "/monitoring"
      : window.location.pathname === "/monitoring" ? "/" : window.location.pathname;
    window.history.replaceState(
      window.history.state,
      "",
      `${nextPath}${preservedSearch}${window.location.hash}`,
    );
  }, [
    returnScopeRef,
    returnSiteIdRef,
    setDataError,
    setFocusRiskId,
    setProductRouteState,
    setProjectRouteError,
    setRouteState,
    setSelectedSubject,
    setSubjectRouteError,
    setSubjectViewFocusRiskId,
    setWorkbenchInbox,
  ]);

  return { responseProjectIdRef, resetProjectState };
}
