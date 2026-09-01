# Codex Review — medical monitoring batch-panel initial-load lifecycle

## Review disposition

**Accepted for this bounded source slice.** The patch is narrow, preserves the existing project-scoped request contract, and addresses a concrete user-facing busy-state race in the real batch workspace.

## Verdict

Accepted for the declared source-only scope. This is not a B6 approval and does not authorize runtime activation.

## Reviewed source

- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectRequestScope.mjs`
- `tests/test_frontend_monitoring_contract.py`

## Findings

1. Before the patch, the initial effect created `initial-batch-load`, then `loadBatches()` created `batch-view`. Because request slots are independent by key, the first request was not the request whose completion represented the actual batch load. The first effect's `isCurrent` guard could therefore suppress its own `setBusy(false)` path.
2. The patch removes only the redundant first slot. `loadBatches()` remains the single source of batch-view requests and still finishes its own request in a `finally` block.
3. Cleanup now marks the effect unmounted before cancelling `batch-view`. This prevents abort/error callbacks from mutating an unmounted panel while preserving project switch isolation.
4. No code path changes the source authority, medical interpretation, approval, rule release, or runtime activation gates.

## Verification

- Static frontend contract: 31 passed.
- All 32 medical-monitoring Node contracts passed.
- Adjacent frontend Python contracts: 67 passed.
- Vite production build passed; only the pre-existing large-chunk warning remains.
- Required protected ports were empty.

## Hermes review-gate

The Hermes review-gate is the required local evidence check for this tracked slice. It must pass with `--require-verification` before the slice is appended to the LOOP ledger.

## Residual risk and boundary

No browser/runtime evidence was collected because the B6/C14 and real-loop gates remain closed. This review accepts the source change only; it does not imply release readiness, activation authority, or commercial acceptance.
