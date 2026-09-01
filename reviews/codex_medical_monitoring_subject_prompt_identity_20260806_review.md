# Codex Review: medical_monitoring_subject_prompt_identity_20260806

Date: 2026-08-06
Delegated-agent output: `runs/codex_medical_monitoring_subject_prompt_identity_20260806.md`

## Verdict

**Pass — offline presentation contract only.** The repair is bounded to Patient Profile risk-prompt display identity. It does not activate the real-loop gate or change clinical/risk authority.

## Boundary Check

- Direct Codex work stayed within the workbench feature, its Node test, and the static frontend contract test, plus this task's context/review/metrics records.
- No service, provider, browser, API login, real project, SQLite/CAS, Safety/PV, or medical-writing path was touched.
- No production runtime write was performed; the real-loop gate remains `read_only=true`, `activation_allowed=false`, `provider_call_permitted=false`.

## Codex Verification

- Source review found both direct prompt-key uses in `MedicalMonitoringSubjectViews.jsx`; malformed/duplicate prompt IDs can otherwise collide or be mistaken for a stable display identity.
- `riskPromptDisplayRows` preserves rows and source order, marks `ready`/`duplicate`/`missing`, and creates `risk-prompt:<identity>:<sourceIndex>` display keys. `riskPromptDisplayKey` never mutates or substitutes the source `prompt_id`.
- UI uses the helper in the PD/Query and Risk sections and visibly renders `身份重复` or `身份待核对`; no focus, request, confirmation, or disposition callback is added.
- `node frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`: passed.
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_timeline_contract.py`: **94 passed**.
- All 38 `frontend/src/features/medical-monitoring/*.test.mjs` files: **38/38 passed**.
- `npm run build --prefix frontend`: passed; Vite transformed 1956 modules. Existing chunk-size advisory remains; no new build error.
- Ports 8911, 5174, 8910, 4173: no listening process observed.

## Delegated-Agent Output Review

- No delegated-agent output was used. The task route was direct Codex because the guard selected `codex/codex-main/high` and no conference was required for this bounded local audit; **Hermes dispatch was not used**.
- The adjacent `referenceRiskCards` summary intentionally remains source/display-only and has no action path; changing its selection semantics would exceed the confirmed defect scope.

## Residual Risk

- Browser/runtime visual acceptance and real-project semantic acceptance remain unverified because the current gate explicitly forbids activation. The next runtime phase still requires the five formal reviewer outcomes, source-token-byte revalidation, and CAS expected-version check.
- The existing Vite chunk-size advisory remains unrelated to this patch.
