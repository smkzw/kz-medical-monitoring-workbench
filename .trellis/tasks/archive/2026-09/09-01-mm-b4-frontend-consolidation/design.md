# B4 frontend single-generation design

## Current shape

- `App.jsx` owns the application shell and medical-writing/editor code, but also carries medical-monitoring route state, API reads and legacy subject pages.
- The latest audience-facing monitoring surface is `r5/MedicalMonitoringR5Page.jsx`; it already embeds the R7 setup/progress/result loop and the R7 Journey continuity drawer.
- The G6 page is a parallel synthetic application. Its useful subject-flow/Sankey and compact progress patterns are already represented in the latest R5 surface; B5 will provide synthetic data through the product rather than retain a G6 page.
- Root-level monitoring files are an older product path. They remain only until the canonical feature shell owns the route and state contract.

## Target boundary

`frontend/src/features/medical-monitoring/` becomes one generation-neutral feature:

- `MedicalMonitoringPage.jsx` is the single mounted page.
- `MedicalMonitoringWorkspace.jsx` owns the overview, center, Journey/profile/timeline and evidence surfaces.
- `MedicalMonitoringProductLoop.jsx`, progress, continuity and Journey modules retain the current product behavior without generation prefixes.
- `medicalMonitoringRouteState.mjs` is the one browser/deep-link contract.
- `useMedicalMonitoringFeature.mjs` owns medical-monitoring route synchronization, project isolation and feature-level loading state extracted from `App.jsx`.
- `App.jsx` keeps the shared shell, global project selection and medical-writing subsystem, and delegates monitoring rendering through a small feature interface.

## Migration rules

1. Move behavior before redesign. Preserve tests while replacing generation-qualified imports with canonical feature imports.
2. Keep temporary compatibility facades only within the same slice; delete them before B4 acceptance so one implementation remains.
3. Do not copy medical-writing state or generic application-shell navigation into the feature.
4. Treat the backend projection as authoritative. The frontend may format and filter but may not manufacture risk identity, chronology or publication state.
5. Preserve the horizontal visit/time axis, typed event/risk markers, source jumps and subject-flow Sankey. Details open from markers; cards do not replace chronology.
6. Audience text stays native Chinese and generation-neutral. Internal labels, manifest/digest names and candidate/fact implementation terms remain hidden.

## Compatibility and rollback

- Existing query parameters are parsed into the canonical route state before old helpers are removed.
- Project changes clear subject/risk/event/source focus and prevent cross-project state reuse.
- Each slice is independently committed. A failed slice rolls back to its prior commit; no medical-writing file is rewritten as part of rollback.
- G6 fixtures are not migrated here; B5 externalizes synthetic fixtures and mounts the product synthetic profile.

## Verification

- Run focused route-state, adapter, product-loop, progress, Journey, continuity, subject-flow and render tests after each slice.
- Run the full medical-monitoring frontend test set and `npm run build` before acceptance.
- Run protected medical-writing frontend contract tests and verify the B4 diff does not touch `features/medical-writing` or writing assets.
- After deterministic checks pass, inspect the actual product at the user primary wide-screen resolution in `ego(lite)`; archive screenshots only at the Phase-B smoke task, not as a parallel G6 gate.
