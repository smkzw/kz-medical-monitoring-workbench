import {
  normalizeMedicalMonitoringWorkspaceRouteState,
  parseMedicalMonitoringWorkspaceRouteState,
  serializeMedicalMonitoringWorkspaceRouteState,
} from "./medicalMonitoringWorkspaceRouteState.mjs";

function productRouteResult(result) {
  return {
    isProduct: result.isWorkspace === true,
    status: result.status,
    valid: result.valid,
    canonical: result.canonical,
    reason: result.reason,
    unknownKeys: result.unknownKeys,
  };
}

export function parseMedicalMonitoringProductRouteState(input = "") {
  return productRouteResult(parseMedicalMonitoringWorkspaceRouteState(input));
}

export function normalizeMedicalMonitoringProductRouteState(input = {}) {
  return normalizeMedicalMonitoringWorkspaceRouteState(input);
}

export function serializeMedicalMonitoringProductRouteState(state = {}) {
  return serializeMedicalMonitoringWorkspaceRouteState(state);
}
