# Codex Review: medical_monitoring_unclassified_structure_action_20260804

Date: 2026-08-04 (Asia/Shanghai)
Route: direct Codex; no delegated agent or conference

Hermes review-gate: this record is submitted to the local Hermes workflow guard for evidence
completeness; the guard is bookkeeping only and does not grant runtime or medical authority.

## Verdict

PASS — bounded source/static slice.

## Boundary Check

- No delegated agent was used.
- The change is limited to the existing monitoring warning/action style, its focused static test,
  and the stale Python contract assertion described below; no server, route, database, provider,
  runtime or medical-writing file was changed.
- Reserved ports 8911/5174/8910/4173 were not started.

## Codex Verification

- `node --test frontend/tests/monitoring_unavailable_state_qc.mjs`: 1/1 passed.
- `node --test frontend/src/features/medical-monitoring/medicalMonitoring*.test.mjs`: 31/31 suites passed.
- `.venv/bin/python -m pytest -q tests/test_frontend_monitoring_contract.py`: 30/30 passed.
- `npm run build`: Vite transformed 1951 modules and completed; only the existing large-chunk warning remains.
- Browser/Playwright and runtime authority checks were intentionally not run while the current gates
  and reserved-port boundary remain closed.

## Implementation Review

The new button keeps the visible unclassified-sheet count/examples and fail-closed wording, has a
keyboard-reachable native button with an accessible title, and calls only the existing
`toggleBatchWorkspace`. It does not claim mapping confirmation or create risk data. The Python test
was corrected because it still required the removed `monitoringWorkbenchInbox || workbenchInbox`
fallback; the current project-scoped inbox contract is the safer cross-project isolation behavior,
and the static test already rejects the fallback.

## Residual Risk

This review does not establish live visual acceptance, mapping correctness, independent-AI quality,
source-token/CAS authority, B6/C14 activation, or commercial readiness. B6 remains
`pending_review` and C14 remains `blocked_pending_b6_review`; keep 8911 stopped.
