# Codex Review: patient_profile_page_v10_step

Date: 2026-07-07
Hermes output: not used; Codex implemented directly after local source review.

## Verdict

Pass.

## Boundary Check

- Source edits were limited to `frontend/src/App.jsx`, `frontend/src/styles.css`, `frontend/AGENTS.md`, and a frontend QC script at `frontend/tests/patient_profile_qc.mjs`.
- Browser evidence was written to `records/visual_qc_20260707/`.
- Backend services, contracts, and repository tests were not edited.
- `python3 scripts/generate_demo_data.py` refreshed the existing demo JSON used by the running API for browser verification.
- Hermes was not dispatched.

## Codex Verification

- `npm run build`: passed.
- `node tests/patient_profile_qc.mjs`: passed.
- Desktop screenshot: `records/visual_qc_20260707/patient_profile_v10_step_desktop.png`.
- Mobile screenshot: `records/visual_qc_20260707/patient_profile_v10_step_mobile.png`.
- Metrics: `records/visual_qc_20260707/patient_profile_v10_step_metrics.json`.
- Metrics confirmed desktop `docW=1425`, `innerW=1440`, `overflowX=false`; mobile `docW=390`, `innerW=390`, `overflowX=false`; both views rendered 4 trend charts.

## Hermes Output Review

Not applicable.

## Residual Risk

- Patient Profile still uses the current demo subject set exposed in the frontend and loaded subject drilldown API; it does not implement a full V10 data adapter or all V10 tables.
- The headless QC script depends on local Chrome and a running frontend/API server.
- Existing Vite bundle-size warning remains unchanged.
