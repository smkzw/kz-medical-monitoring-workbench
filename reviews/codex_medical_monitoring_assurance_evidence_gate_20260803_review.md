# Codex Review: medical_monitoring_assurance_evidence_gate_20260803

Date: 2026-08-03 CST
Delegated-agent output: `runs/codex_medical_monitoring_assurance_evidence_gate_20260803.md`

## Verdict

PASS — bounded fail-closed frontend contract correction; Hermes workflow review-gate
is required for this tracked task and is being run after final verification.

This is not a P8 completion or release approval.

## Boundary Check

- Codex performed the work directly inside the workbench; no delegated external agent
  was dispatched.
- Changed surfaces are limited to the existing assurance model/panel tests and the
  existing frontend contract test. No runtime database, service, provider, browser,
  real project, B6/C14 gate, or medical-writing surface was written.

## Codex Verification

- Source contract: P8 exit gate in
  `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` §12 requires
  three-level numerical consistency and verifiable closure/explanation evidence.
- Focused: `node frontend/src/features/medical-monitoring/medicalMonitoringAssurance.test.mjs`
  → **23 passed**.
- Adjacent frontend Node sweep: all **22** `frontend/src/features/medical-monitoring/*.test.mjs`
  passed.
- Python: `pytest -q tests/test_frontend_monitoring_contract.py tests/test_monitoring_assurance.py`
  → **48 passed**; Ruff check passed.
- Offline Vite build: **1926 modules transformed**, success; existing large chunk warning
  only. No service or browser was started.
- Boundary: App.jsx SHA `307cb7961790bcab39fb697ece22b7cef3e2fe1afef3283173bc8910b34a1b8c`
  and styles.css SHA `35f2e0119a0175d58d81775ca8140aa057a4ab6b01a8007ae9e2ec62764d3a43`
  remain unchanged; no listener on 8911/5174.

## Delegated-Agent Output Review

- The change reuses the existing deterministic `projectAssuranceRollup` projection and
  does not invent risk facts. It blocks non-conserved ids/counts, missing closure-evidence
  counts, incomplete rollups, and dirty pre-lock proofs. The user-facing banner now states
  the reason rather than reporting a generic ready-like state.
- No unsupported claim was found. The current B6/C14 state was rechecked and remains
  authoritative; this change does not infer approval from freshness or tests.

## Residual Risk

- Real project evidence, browser visual/UAT, backend POST workflows, formal B6 reviewer
  outcomes, aggregate/CAS version closure, source-token provenance, identity/RBAC,
  restart/performance/audit and commercial release gates remain unverified or blocked.
- The generated Vite bundle retains the existing >500 kB warning; this slice did not
  expand into code splitting.
