# Codex Review: medical_monitoring_timeline_selection_identity_20260806

Date: 2026-08-06 (Asia/Shanghai)
Route: direct Codex (`hermes/codex/codex-main:high`); no delegated agent or external model was dispatched.

## Verdict

PASS — display-only Timeline selection keys now remain usable when source events omit or duplicate `event_id`; clinical/source/risk identity was not changed.

## Boundary Check

- Changes are limited to `medicalMonitoringSubjectModels.mjs`, its model test, `MedicalMonitoringSubjectViews.jsx` and the focused static contract.
- `timelineEventSelectionKey` namespaces explicit event/source identifiers and falls back to a lane/index token only for UI selection. Duplicate bases receive a deterministic `#2`, `#3` suffix within the lane.
- The original event object, `event_id`, source locator, risk IDs and API payloads remain untouched; selection keys are not sent to any service.
- No `App.jsx`, `styles.css`, `main.jsx`, medical-writing source, backend/API/schema/database, provider, browser, runtime or real project was changed.

## Codex Verification

- Subject-model Node contract: PASS, including missing/duplicate identity keys and explicit source-record fallback.
- Focused monitoring/timeline Python contracts: PASS — 76 passed.
- Full Node suite: PASS — 44 subtests / 0 failures.
- Vite build: PASS — 1,956 modules transformed; existing >500 kB chunk advisory retained.
- Changed-file hashes: models `c7c6a04777444e2412704e470bf07904b37bb3c9f848d8f288d0bcdb38fc7739`; model test `7de21c1696bdd7a8139e8fa42e551b5f354a8b64a3773a73ffb9f4c4ac06952d`; views `ef376643dda60d5619c5ff5b9b3c0074e50d90778667cf591dc9be67f7172784`; static contract `0ed376be20aa3050f785f72e3ea8e090a29b39196eaa38707fdf45105f59d74a`.
- Protected shell hashes: App `de942af37999e708d124c99e1beb47fcd2c405ff23ed83fee6dbcc4cf5e0beed`; styles `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd`; main `869dbab992b086a2c38ae8ab1d44ca9b7d0014ef4614b85a5154bc3fcebc8f05`.
- Listener check: no listeners on 8911, 5174, 8910 or 4173.
- Hermes review-gate is required after this review is complete; the real-loop gate remains `read_only / blocked`.

## Interpretation

This prevents UI selection/key collisions caused by malformed or structurally different source payloads. A fallback key is a local presentation identity only; it is not a substitute for a validated event ID, source identity, risk key or risk instance.

## Residual Risk

Real API identity guarantees, browser keyboard/visual acceptance, clinical/scientific correctness, source completeness, independent AI, P8 authority, B6/C14, three-project LOOP and commercial readiness remain unverified or blocked. Keep 8911 and all runtime ports stopped.
