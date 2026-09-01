import {
  normalizeMedicalMonitoringR5RouteState,
  parseMedicalMonitoringR5RouteState,
  serializeMedicalMonitoringR5RouteState,
} from "./medicalMonitoringR5RouteState.mjs";

function productRouteResult(result) {
  return {
    isProduct: result.isR5 === true,
    status: result.status,
    valid: result.valid,
    canonical: result.canonical,
    reason: result.reason,
    unknownKeys: result.unknownKeys,
  };
}

export function parseMedicalMonitoringProductRouteState(input = "") {
  return productRouteResult(parseMedicalMonitoringR5RouteState(input));
}

export function normalizeMedicalMonitoringProductRouteState(input = {}) {
  return normalizeMedicalMonitoringR5RouteState(input);
}

export function serializeMedicalMonitoringProductRouteState(state = {}) {
  return serializeMedicalMonitoringR5RouteState(state);
}
