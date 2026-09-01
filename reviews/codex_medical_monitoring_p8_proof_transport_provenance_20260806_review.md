# Codex Review: medical_monitoring_p8_proof_transport_provenance_20260806

Date: 2026-08-06 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_p8_proof_transport_provenance_20260806.md` (Hermes task record; no delegated provider call)

## Verdict

**PASS — bounded transport contract only.**

## Boundary Check

- Work stayed inside the workbench. No external agent or provider was dispatched.
- Only the router and its focused test were changed; no runtime, database,
  medical-writing or production deployment path was touched.

## Codex Verification

- `.venv/bin/python -m pytest -q tests/test_monitoring_assurance.py tests/test_monitoring_assurance_principal_route.py tests/test_medical_monitoring_module_contract.py` → **194 passed**.
- `.venv/bin/python -m py_compile services/api/app/monitoring_assurance_router.py` → passed.
- `node --test frontend/src/features/medical-monitoring/*.test.mjs` → **37/37 files passed**.
- `npm run build` in `frontend/` → **1,956 modules transformed; build passed**;
  existing >500 kB advisory retained.
- No browser/runtime/provider/live authority check was run by design; the gate
  remains read-only/blocked and reserved ports are empty.

## Delegated-Agent Output Review

- The router adds a transport-only diagnostic based on the already audited
  implementation: six proof fields are risk-reader-derived while other fields
  remain caller-supplied. The persisted proof payload and `content_sha256` are
  untouched. Both POST and GET use the same helper, and the UI fail-closed guard
  now receives an explicit `mixed_provenance` status rather than a missing field.
- The patch does not claim source authority, medical approval or release.

## Residual Risk

- Evidence authority remains unresolved: choose either a server evidence-run
  ledger or signed manifest plus full server revalidation before enabling proof
  submission. B6/C14 and real-loop activation remain blocked.
