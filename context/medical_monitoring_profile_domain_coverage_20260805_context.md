# Task Context: medical_monitoring_profile_domain_coverage_20260805

Created: 2026-08-05 21:02:01
Objective: 把 Patient Profile 的来源域覆盖状态提升为清晰且不推断风险的用户可见数据覆盖条带，并用模型测试与前端构建验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md`
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `packages/contracts/workbench_contracts/models.py` (`SubjectDomainAvailability` contract)
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- Current workbench filesystem; no live project runtime is an acceptance source while the real-loop gate is blocked.

## Scope

- In scope: add a deterministic model helper that exposes explicit source-domain coverage states; render a compact Patient Profile coverage strip with clear labels and a no-inference disclaimer; add focused model tests; run focused/full frontend checks that do not require starting the app.
- In scope: preserve the existing evidence-lineage and capability-restriction semantics, and keep absent/unmapped/unsupported distinct from available.
- Out of scope: backend contracts, App.jsx ownership cleanup, shared/global CSS, API/provider calls, services, browser login/Playwright, real clinical projects, and medical disposition.

## Success Criteria

- Missing `domain_availability` is surfaced as declaration missing; metric arrays never infer availability.
- Each declared domain is represented with a stable Chinese label and an explicit status; unknown/malformed records are visible as needing verification rather than silently coerced.
- Patient Profile places the coverage information near the summary, with an explicit statement that coverage is a source/mapping declaration and not evidence of no risk.
- Focused model tests and the existing medical-monitoring frontend test/build checks pass; no production runtime is started.
- Task evidence, review gate, and LOOP ledger/checkpoint are updated without overstating commercial or clinical readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The authoritative real-loop gate is currently `blocked` (`activation_allowed=false`, `medical_approval_granted=false`, `write_permitted=false`); keep ports 8911/5174/8910/4173 stopped and do not run live projects or provider calls.
- This source/UI slice cannot be used to claim Timeline/Profile clinical correctness, independent-AI readiness, or commercial release.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 21:02:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 21:05: Implemented `profileDomainCoverage()` and the Patient Profile source-domain coverage strip. The helper preserves missing, empty, explicit absent, unmapped, unsupported, unknown and malformed states; it never reads trend arrays to infer availability.
- 2026-08-05 21:06: Focused model test passed; all 33 medical-monitoring frontend pure test modules passed; Vite production build passed (1954 modules transformed, existing >500 kB main-chunk warning). Live browser/runtime checks remain prohibited by the real-loop gate.
- 2026-08-05 21:08: Closed the normalization edge: `profileDomainCoverage()` now upgrades `profile_shape_warnings` for `domain_availability` into a visible malformed/partial-declaration state instead of treating normalized `[]` as an empty declaration. Focused and all-33/build regressions passed again.
- 2026-08-05 21:10: Added the explicit available/declared count to the strip; the final all-33 pure-module regression and Vite build both passed. Final gate recheck still shows `read_only/blocked`, and all four reserved ports are empty.
