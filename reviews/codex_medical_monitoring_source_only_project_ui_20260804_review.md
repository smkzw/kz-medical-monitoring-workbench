# Codex review: medical_monitoring_source_only_project_ui_20260804

Date: 2026-08-04

## Verdict

**Pass for the declared offline frontend/read-contract slice.**

The change prevents a source-manifest-only project from being presented as
activated or from initiating child monitoring reads, while preserving the
existing active/demo/legacy behavior.

## Boundary check

- Production change is limited to `frontend/src/App.jsx` and the new
  `medicalMonitoringSourceReadiness.mjs`; tests and records are scoped to this
  contract.
- `frontend/dist` was refreshed only by the verification build and is recorded
  as derived output, not a separate source-of-truth change.
- No backend/API/adapter/runtime/provider/browser/Playwright or user project
  source was touched. Medical-writing source and registries were preserved.
- No upload, risk, batch, subject, or AI action was started or persisted.
- B6, C14, and real-loop gates remain closed; all reserved listeners stayed
  stopped.

## Verification

- Readiness model: **25 assertions passed**.
- Static UI QC: **10 assertions passed**.
- All 32 medical-monitoring Node suites passed.
- Frontend monitoring Python contract: **30 passed**.
- Vite build: **1952 modules transformed, PASS**; only the existing chunk-size
  advisory remains.
- Hermes review-gate is run after this review and metrics file are complete.

## Review notes

- A binding must be positively active before monitoring reads or actions are
  exposed; missing/unknown/planned states do not get coerced into readiness.
- Source-only projects show the reason and next prerequisites in plain Chinese,
  matching the data-sensitive senior-monitor user perspective.
- Demo/legacy statuses are explicitly retained as active so this hardening does
  not regress the existing demo path.

## Residual risk

No real runtime, browser, scientific, independent-AI, or commercial-release
evidence exists for this slice. Formal B6/C14, source-token/CAS,
approved-input/host-attestation, five-project LOOP, and visual acceptance remain
required before activation.
