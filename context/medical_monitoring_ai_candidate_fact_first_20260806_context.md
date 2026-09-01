# Task Context: medical_monitoring_ai_candidate_fact_first_20260806

Created: 2026-08-06 05:57:39
Objective: 在 feature-owned 日常 AI 候选卡中按事实正文优先原则展示显式 evidence.quote，并保持定位、版本身份和医学确认边界不变
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

PRD P1-03 requires source facts to precede rationale and locator. The daily AI candidate model already preserves an explicit `evidence.quote`, but the feature-owned card rendered only candidate text, claims and source identifiers/locators. A senior medical monitor therefore had to open a separate source path before seeing the quoted fact. This bounded correction improves the read order without changing candidate status or adding an action.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P1-03 (事实正文→方案依据→规则理由→定位折叠).
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.mjs` explicit `quote` normalization and `MedicalMonitoringDailyAiCandidates.jsx/.css` feature-owned card.
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.test.mjs` and `tests/test_frontend_monitoring_contract.py` consumer contracts.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked).

## Scope

- In scope: display at most the first two explicit `evidence.quote` values before locator/provenance details, show an explicit unknown when a quote is absent, add compact feature CSS and focused contract assertions.
- Out of scope: candidate normalization changes, backend/API/schema/database, source registry, provider/service/browser/Playwright/API login, real projects, runtime/SQLite/CAS/B6/C14/source-token/P8/Safety-PV, shared `App.jsx`/styles/main, medical-writing or any accept/reject/approval action.

## Success Criteria

- A candidate with an explicit quote exposes it in a labelled source-fact block before source locator/provenance details.
- Missing quotes remain `来源事实正文待核对`; no quote, risk, medical confirmation or no-risk conclusion is invented.
- The card remains read-only and status-aware; all focused/static/full Node, Python and Vite checks remain green, with 8911/5174/8910/4173 stopped.
- Evidence records state that this slice covers the AI candidate preview only, not full risk-dock/source-panel or three-project acceptance.

## Risk Boundaries

- Only feature-owned candidate source, its test/style and the focused static contract may change; preserve App/styles/main and medical-writing hashes.
- Render only explicit normalized `quote` text; do not derive facts from candidate claims/title/locator or relabel quotes as confirmed risk.
- No backend/API/runtime/provider/browser/real-project/SQLite/CAS/B6/C14/source-token/P8/Safety-PV/medical-writing or write-authority action; keep the real-loop gate and ports stopped.
- Direct Codex is final authority; no delegated agent or external model is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 05:57:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 05:58:xx: Source audit confirmed explicit quote is normalized but not rendered in the candidate card; selected a feature-owned presentation-only correction.
