# B4 implementation plan

## 1. Inventory and freeze behavior

- [x] Map all current App/r5/r7/g6 imports, routes, state owners, tests and CSS dependencies.
- [x] Record which G6 behaviors are already present in the latest product page and which belong to B5 synthetic-profile work.
- [x] Run the focused pre-migration frontend behavior baseline.

## 2. Canonical product surface

- [x] Introduce generation-neutral feature entry points for the current workspace and product loop.
- [x] Rename/move their supporting route, progress, continuity and Journey modules into the feature root without changing behavior.
- [x] Update imports and behavior tests to the canonical entry points.
- [x] Remove the superseded r5/r7 implementation directories once no runtime import references them.

## 3. App boundary extraction

- [x] Extract medical-monitoring browser route parsing and serialization from `App.jsx`.
- [x] Extract monitoring project isolation, focus reset and route synchronization state.
- [x] Extract the medical-monitoring render switch and data-loading orchestration behind one feature component/hook.
- [x] Keep application-shell navigation and all medical-writing code in place.

## 4. Remove superseded frontend paths

- [ ] Remove the G6 parallel page after confirming its retained flow/Journey behavior exists in the canonical feature.
- [ ] Remove root-level monitoring components and state modules that are superseded by the canonical feature.
- [ ] Confirm no user-facing generation labels or runtime imports mention r5/r7/g6.

## 5. Acceptance

- [ ] All medical-monitoring frontend behavior and render tests pass.
- [ ] Protected medical-writing frontend contract tests pass and its files remain untouched.
- [ ] Vite production build passes.
- [ ] One medical-monitoring frontend generation remains and `App.jsx` delegates through one feature entry.
- [ ] Wide-screen Journey remains a chronological visit axis with typed markers, details and source drill-down.
- [ ] Trellis journal and git commits contain slice evidence and rollback points.
