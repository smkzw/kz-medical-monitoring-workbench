# Task Context: medical_monitoring_external_landscape_20260803

Created: 2026-08-03 00:08:36
Objective: 调研中英文AI/RBM医学监查平台与开源实现模式，提取可迁移的工作流、数据模型、AI证据链和验收模式，形成不替代本地验证的决策记录
Task type: `competitive_intelligence`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current local PRD/roadmap/spec sections covering RBM, three monitoring modes, source/risk ownership, independent AI and release gates.
- Official vendor/product documentation and official regulator/standards pages found during the bounded web scan.
- Official/open-source repository documentation only for any implementation candidate; popularity alone is not adoption authority.
- Current local code/contracts are the final fit and acceptance authority; this research does not change them.

## Scope

- In scope: compare selected English/Chinese RBM/central-monitoring/clinical-data platforms and open-source building blocks on workflow, data model, risk signals, AI evidence, integration, traceability and deployment fit; map useful patterns to this project and record rejected assumptions.
- Out of scope: procuring or adopting a proprietary platform, adding dependencies, copying vendor claims as evidence of local readiness, sending private project data to third parties, or changing product source/runtime.

## Success Criteria

- Each material claim has an official/primary source locator or is labeled inference.
- The comparison distinguishes commercial product marketing from verifiable implementation contracts.
- The output identifies concrete design patterns to retain, patterns to reject, and bounded follow-up tasks for this workbench.
- No product or runtime state changes.

## Risk Boundaries

- Use public sources only; do not include credentials, private project content, or sensitive identifiers in queries.
- Do not treat a vendor feature page or another model's claim as proof of clinical correctness or local product readiness.
- No executable component is adopted unless its license, maintenance and integration fit are independently verified; this slice is research only.
- The research output is a decision input, not regulatory, medical or commercial approval.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 00:08:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 00:08:50: External-tech-research skill read; bounded official-source landscape scan started.
- 2026-08-03: Re-read current global/workbench/product instructions and local monitoring contracts; confirmed this slice remains research-only and Codex-led.
- 2026-08-03: Verified FDA, ICH, NMPA and TransCelerate primary/methodology sources, then Oracle, CluePoints and 太美 official product documentation. Vendor claims were retained only as implementation-pattern evidence.
- 2026-08-03: Wrote `records/active_slices/medical_monitoring_external_landscape_20260803/EXTERNAL_LANDSCAPE_DECISION_RECORD.md`, `TASK_RECORD.md` and `TEST_EVIDENCE.md`. No source/runtime/provider/browser/project data changed.
- 2026-08-03: Decision: adopt risk-to-action, CtQ/KRI/QTL, centralized cross-level views, explicit roles and inspection-ready lineage as local design targets; reject external platform adoption and all unverified vendor performance/compliance claims.
- 2026-08-03: Next action remains gated by B6 accepted review → approved-input → source-token/CAS → controlled runtime; then consume reconciled project/source/prompt admission contract before any real LOOP.
