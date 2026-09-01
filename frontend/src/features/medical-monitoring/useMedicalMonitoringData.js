import { useCallback, useEffect, useRef, useState } from "react";
import { resolveMedicalMonitoringSubjectRoute } from "./medicalMonitoringRouteState.mjs";

function apiDetailText(payload, fallback = "") {
  const detail = payload?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") return detail.detail || detail.message || JSON.stringify(detail);
  return fallback;
}

async function readJsonOrThrow(response) {
  if (response.ok) return response.json();
  const payload = await response.json().catch(() => ({}));
  const error = new Error(apiDetailText(payload, `${response.status}`));
  error.status = response.status;
  error.payload = payload;
  const detail = payload?.detail;
  error.code = detail && typeof detail === "object"
    ? String(detail.code || detail.detail?.code || "").trim()
    : "";
  throw error;
}

function projectMismatch(message) {
  const error = new Error(message);
  error.code = "monitoring_response_project_mismatch";
  error.readSource = "contract";
  return error;
}

export function useMedicalMonitoringData({
  activeProjectId,
  monitoringProjectId,
  monitoringReady,
  isProductRoute,
  requestedSubjectId,
  selectedSubject,
  setSelectedSubject,
  defaultSubjectId = "",
}) {
  const responseProjectIdRef = useRef(activeProjectId);
  responseProjectIdRef.current = activeProjectId;
  const [workbenchInbox, setWorkbenchInbox] = useState(null);
  const [subjectCatalog, setSubjectCatalog] = useState([]);
  const [subjectProfiles, setSubjectProfiles] = useState({});
  const [dataError, setDataError] = useState("");
  const [subjectRouteError, setSubjectRouteError] = useState("");
  const [readError, setReadError] = useState(null);
  const [subjectReadError, setSubjectReadError] = useState(null);
  const [profileReadError, setProfileReadError] = useState(null);

  const refreshWorkbenchInbox = useCallback((payload) => {
    if (payload) {
      if (payload.project_id === responseProjectIdRef.current) {
        setWorkbenchInbox(payload);
        setReadError(null);
      }
      return;
    }
    if (!monitoringProjectId || !monitoringReady) {
      setWorkbenchInbox(null);
      setReadError(null);
      return;
    }
    setReadError(null);
    fetch(`/api/projects/${monitoringProjectId}/workbench-inbox`)
      .then(readJsonOrThrow)
      .then((data) => {
        if (data.project_id !== responseProjectIdRef.current) {
          setReadError(projectMismatch("医学监查工作收件箱响应项目身份不匹配，未更新当前页面。"));
          return;
        }
        setWorkbenchInbox(data);
        setReadError(null);
      })
      .catch(setReadError);
  }, [monitoringProjectId, monitoringReady]);

  useEffect(() => {
    if (isProductRoute || !monitoringProjectId || !monitoringReady) {
      setWorkbenchInbox(null);
      setReadError(null);
      return undefined;
    }
    let cancelled = false;
    setReadError(null);
    fetch(`/api/projects/${monitoringProjectId}/workbench-inbox`)
      .then(readJsonOrThrow)
      .then((data) => {
        if (cancelled) return;
        if (data?.project_id !== responseProjectIdRef.current) {
          setReadError(projectMismatch("医学监查工作收件箱响应项目身份不匹配，未更新当前页面。"));
          return;
        }
        setWorkbenchInbox(data);
        setReadError(null);
      })
      .catch((error) => {
        if (!cancelled) {
          setWorkbenchInbox(null);
          setReadError(error);
        }
      });
    return () => { cancelled = true; };
  }, [isProductRoute, monitoringProjectId, monitoringReady]);

  useEffect(() => {
    setSubjectProfiles({});
    setSubjectCatalog([]);
    setDataError("");
    setSubjectRouteError("");
    setSubjectReadError(null);
    if (isProductRoute || !monitoringProjectId || !monitoringReady) return undefined;
    let cancelled = false;
    fetch(`/api/projects/${monitoringProjectId}/monitoring/subjects`)
      .then(readJsonOrThrow)
      .then((data) => {
        if (cancelled) return;
        if (data?.project_id !== responseProjectIdRef.current) {
          setSubjectCatalog([]);
          setSubjectReadError(projectMismatch("受试者目录响应项目身份不匹配，已阻止写入当前项目。"));
          return;
        }
        const nextSubjects = Array.isArray(data.subjects) ? data.subjects : [];
        const resolution = resolveMedicalMonitoringSubjectRoute(
          requestedSubjectId,
          nextSubjects,
          "",
          defaultSubjectId,
        );
        setSubjectCatalog(nextSubjects);
        setSubjectReadError(null);
        setSubjectRouteError(
          resolution.status === "unavailable"
            ? `医学监查链接中的受试者“${requestedSubjectId}”当前项目目录中不存在。`
            : "",
        );
        setSelectedSubject((current) => (
          requestedSubjectId
            ? resolution.subjectId
            : resolveMedicalMonitoringSubjectRoute("", nextSubjects, current, defaultSubjectId).subjectId
        ));
      })
      .catch((error) => {
        if (!cancelled) {
          setSubjectCatalog([]);
          setSubjectRouteError("");
          setSubjectReadError(error);
        }
      });
    return () => { cancelled = true; };
  }, [defaultSubjectId, isProductRoute, monitoringProjectId, monitoringReady, requestedSubjectId, setSelectedSubject]);

  const selectedProfileKey = monitoringProjectId && selectedSubject
    ? `${monitoringProjectId}::${selectedSubject}`
    : "";
  const selectedSubjectProfile = selectedProfileKey ? subjectProfiles[selectedProfileKey] : null;

  useEffect(() => {
    if (isProductRoute || !monitoringProjectId || !selectedSubject || !monitoringReady) {
      setProfileReadError(null);
      return undefined;
    }
    if (selectedSubjectProfile) {
      setProfileReadError(null);
      return undefined;
    }
    let cancelled = false;
    const requestedProfileKey = `${monitoringProjectId}::${selectedSubject}`;
    setProfileReadError(null);
    fetch(`/api/projects/${monitoringProjectId}/subjects/${selectedSubject}/monitoring`)
      .then(readJsonOrThrow)
      .then((data) => {
        if (cancelled) return;
        if (data?.project_id !== responseProjectIdRef.current || data?.subject_id !== selectedSubject) {
          setSubjectProfiles((current) => {
            if (!(requestedProfileKey in current)) return current;
            const next = { ...current };
            delete next[requestedProfileKey];
            return next;
          });
          setProfileReadError(projectMismatch("受试者画像响应项目或受试者身份不匹配，已阻止写入当前个例。"));
          setDataError("受试者画像响应项目或受试者身份不匹配，已阻止写入当前个例。");
          return;
        }
        setSubjectProfiles((current) => ({ ...current, [requestedProfileKey]: data }));
        setProfileReadError(null);
      })
      .catch((error) => {
        if (!cancelled) setProfileReadError(error);
      });
    return () => { cancelled = true; };
  }, [isProductRoute, monitoringProjectId, monitoringReady, selectedSubject, selectedSubjectProfile]);

  return {
    workbenchInbox,
    setWorkbenchInbox,
    refreshWorkbenchInbox,
    subjectCatalog,
    selectedSubjectProfile,
    dataError,
    setDataError,
    subjectRouteError,
    setSubjectRouteError,
    readError,
    subjectReadError,
    profileReadError,
  };
}
