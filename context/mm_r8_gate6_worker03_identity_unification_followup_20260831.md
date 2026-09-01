# G6 Worker 03 Same-Session Follow-up — Consume The Canonical Actual-App Bundle

Continue the same `worker_03` execution session. Do not start a new session, service, browser, model, or network call.

## Hard boundaries

- Work only inside the current workbench and only on the allowed files below.
- Do not read or write any real project, medical-writing file, credential, external account, or path outside this workbench.
- Do not start services, browsers, models, network calls, or subprocess Agents.
- Do not claim final G6 or visual acceptance.

## Read these files only

- `context/mm_r8_gate6_synthetic_ego_implementation_20260831_execution_context.md`
- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_identity_followup.md`
- `deploy/medical_monitoring_local/synthetic_ego.py`
- `deploy/medical_monitoring_local/actual_app.py`
- `frontend/src/main.jsx`
- all current files under `frontend/src/features/medical-monitoring/g6/`
- current G6 frontend tests and `frontend/package.json`

## Observed blocker

The current frontend authors a second fixture with 58 events and binding `sha256:6bb510f8...`. The canonical Python generator owns 96 events, fixture digest `sha256:5cc67a...`, profile binding `sha256:1a8d6561...`, and bundle digest `sha256:5bed1d...`. The actual app now exposes the exact validated Python bundle at `GET /api/g6/synthetic-bundle`.

## Assigned repair

1. Remove the frontend-authored dataset as a runtime source. The audience page must fetch `/api/g6/synthetic-bundle` and render only after validating the canonical payload needed by the page.
2. Do not silently fall back to any static JavaScript fixture, generated example, localStorage value, real API, real model, or real project. Fetch/validation failure must show a concise Chinese fail-closed page state.
3. Add the smallest projection layer that maps the canonical Python schema to the existing overview, center flow, Patient Journey, run-progress, and risk UI contracts. Do not change the Python generator to match the old JS schema.
4. Preserve the frozen user experience: 2 projects, 3 centers, 12 subjects, 48 visits, 96 events, 8 event domains, three analysis modes, horizontal chronological Journey, project/center flow, and 13 user tasks. Use the canonical bundle's `journey`, `flow_nodes`, `flow_rows`, `risk_scenarios`, `analysis_cases`, and `section_15_4` rather than inventing disease/drug-specific logic.
5. Validate exact canonical fixture/profile binding/bundle digests, event count, synthetic/offline flags, provider/model/adapter identity. Any mismatch blocks rendering.
6. Update structural/render tests to inject or load a canonical-shaped bundle fixture produced from the same schema, without reintroducing an independent medical dataset. A checked-in generated JSON is not allowed unless it is deterministically generated from Python during tests/build and digest-equal.
7. Build `frontend/dist`; do not start a dev server or browser.

## Allowed files

- `frontend/src/main.jsx`
- current files under `frontend/src/features/medical-monitoring/g6/`
- focused frontend G6 tests/config only if required
- runner-managed worker report only

## Verification

Run all G6 frontend structural/render tests and the production build. Return exact counts, changed files, canonical identity assertions, removed static-runtime sources, residual risks, and the next manifest-refresh requirement. Do not claim visual acceptance.

## Output

Return one compact handoff to the runner-managed output file `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_03_identity_followup.md`. Do not write that report path directly through file tools.
