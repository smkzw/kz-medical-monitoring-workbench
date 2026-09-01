export const G6_SYNTHETIC_ROUTE = "/medical-monitoring/synthetic";

export function isG6SyntheticRoute(location = globalThis.location) {
  const pathname = location?.pathname || "";
  if (pathname === G6_SYNTHETIC_ROUTE) return true;
  if (pathname !== "/" && pathname !== "") return false;
  const search = typeof location?.search === "string" ? location.search : "";
  return new URLSearchParams(search).get("g6") === "synthetic";
}

export function g6SyntheticRouteUrl() {
  return G6_SYNTHETIC_ROUTE;
}
