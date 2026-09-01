# Codex Review: medical_monitoring_assurance_remediation_identity_20260806

Date: 2026-08-06
Delegated-agent output: `runs/codex_medical_monitoring_assurance_remediation_identity_20260806.md`
Workflow: Hermes guard initialized the tracked task; Codex performed the bounded route directly (no Hermes dispatch required).

## Verdict

Pass — offline remediation identity/display guard is implemented and verified. This is not runtime or medical/commercial acceptance.

## Boundary Check

- Changes are limited to the feature-owned remediation model/view/test and monitoring static-contract test plus task evidence. No backend, runtime, shared shell, real project, provider, or medical-writing path was changed.
- Product behavior remains read-only: no remediation status, closure evidence, source risk, or focus target was mutated; only ambiguous focus is withheld.

## Codex Verification

- Source: normalization now retains duplicate rows, source indices and explicit identity state; `assuranceRemediationDisplayKey` is display-only; sort order gets a source-index tie-breaker for deterministic rendering.
- View: rows no longer use `key={row.riskInstanceId}`; duplicate rows remain visible with “身份待核对” and “身份重复，仅可读”, and the focus callback is guarded/disabled for ambiguous identities.
- Tests: `node --test frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRemediation.test.mjs` passed; `node --test frontend/src/features/medical-monitoring/*.test.mjs` passed 38/38 subtests; `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_timeline_contract.py` passed 91; `npm run build` transformed 1,956 modules and passed with the existing >500 kB advisory.
- Boundary: `CURRENT_REAL_LOOP_GATE_AUDIT.json` remains `read_only`/`blocked`; authority flags remain false; ports 8911, 5174, 8910, 4173 are stopped. No browser/runtime/provider/API/real-project test was run because the gate prohibits it.
- Protected hashes unchanged: App `de942af37999e708d124c99e1beb47fcd2c405ff23ed83fee6dbcc4cf5e0beed`; styles `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd`; main `869dbab992b086a2c38ae8ab1d44ca9b7d0014ef4614b85a5154bc3fcebc8f05`.

## Delegated-Agent Output Review

- The pre-change direct key and duplicate early-return were directly observed in the named feature files; the patch retains source rows without creating a surrogate risk identity.
- Existing remediation severity/status/count semantics are retained for unique rows; duplicate rows are counted as shape-valid but the aggregate status becomes partial due to the explicit issue.
- Self-review is sufficient for this bounded static slice; independent conference/browser/scientific review remains unavailable and intentionally deferred under the active gate.

## Residual Risk

- Residual: client display/focus guard does not prove server risk identity uniqueness, matrix completeness, source validity, closure-evidence truth, clinical correctness, or focus resolver safety. P8 authority, B6/C14, real three-project LOOP, browser/scientific acceptance, and commercial release remain pending.
