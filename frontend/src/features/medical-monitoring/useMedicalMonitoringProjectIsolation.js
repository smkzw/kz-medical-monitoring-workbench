import { useCallback } from "react";
import {
  EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE,
  clearMedicalMonitoringProductRouteState,
} from "./medicalMonitoringBrowserRoute.mjs";

export function useMedicalMonitoringProjectIsolation({
  setProductRouteState,
  setRouteState,
  setFocusRiskId,
  setSubjectViewFocusRiskId,
  setSelectedSubject,
  setProjectRouteError,
  returnScopeRef,
  returnSiteIdRef,
}) {
  const resetProjectState = useCallback((nextPage) => {
    setProductRouteState(EMPTY_MEDICAL_MONITORING_PRODUCT_ROUTE);
    setRouteState({});
    setFocusRiskId("");
    setSubjectViewFocusRiskId("");
    setSelectedSubject("");
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
    setFocusRiskId,
    setProductRouteState,
    setProjectRouteError,
    setRouteState,
    setSelectedSubject,
    setSubjectViewFocusRiskId,
  ]);

  return { resetProjectState };
}
