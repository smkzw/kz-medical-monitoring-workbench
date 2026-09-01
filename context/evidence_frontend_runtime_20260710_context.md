# Task Context: evidence_frontend_runtime_20260710

Created: 2026-07-10 20:19:07
Objective: 将证据调研与方案设计前端接入CRSwNP/PNH真实证据候选、审阅、PICOS医学批准、撰写交接和锚定式AI修订API，保持桌面端证据优先布局与跨项目隔离
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/AGENTS.md`
- `frontend/src/App.jsx`, `frontend/src/styles.css`
- `frontend/tests/evidence_design_manifest_qc.mjs`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`
- `services/api/app/evidence_review_workflow.py`
- `services/api/app/evidence_picos_workflow.py`
- `services/api/app/evidence_ai_revision.py`
- `runs/conference/evidence_picos_productization_20260710/participant_kimi_frontend.md`
- `runs/conference/evidence_picos_productization_20260710/participant_glm52_product.md`
- Visual baseline: `records/active_slices/canonical_project_context_20260710/visual_qc_pass7_verified_final/evidence_project_scoped.png`

## Scope

- In scope: CRSwNP/PNH package switching, paged candidate evidence, evidence detail, screening/extraction/appraisal, PICOS decisions, anchored AI revision, medical approval submission and protocol-writing handoff.
- In scope: desktop-first evidence-review and PICOS modes within the existing visual system, with stale-request protection and project/package-scoped unsaved state.
- Out of scope: backend/schema changes, direct approval inside this module, external model configuration, new unrelated pages, mobile-driven feature reduction, and changes to other subsystems.

## Success Criteria

- No `.slice(0, N)` truncation for candidate evidence; use backend paging and explicit totals.
- CRSwNP and PNH each load their own package, candidate types, candidate detail and PICOS language without cross-project leakage.
- Every evidence review action sends `expected_revision` and reports 409/stale-state errors without silent overwrite.
- AI proposals remain visibly anchored and require accept/reject/request-rewrite; accepting never mutates PICOS until the user explicitly applies the recommendation.
- Medical approval submission is gated by complete PICOS writing candidates; writing handoff is gated by a medically approved current snapshot.
- At 1600x1000 and wider desktop, the main evidence or PICOS task remains visible with dense, aligned panels and no page-level horizontal overflow.
- Existing shared styling and other subsystem behavior remain intact; build and focused/full regression pass before browser acceptance.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never render local source paths, provider names, lifecycle numbering, unsupported formal conclusions, or claims of regulatory approval.
- Use the exact 康哲 logo already imported by the application; do not recreate or approximate it.
- Use existing CSS variables/components and Lucide icons. No new visual theme, gradients, decorative cards, SVG/CSS artwork, or mobile-first simplification.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-10 20:19:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
