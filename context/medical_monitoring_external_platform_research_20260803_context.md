# Task Context: medical_monitoring_external_platform_research_20260803

Created: 2026-08-03 20:52:17
Objective: 对英文与中文 AI 医学监查/临床数据质量平台做有边界的官方资料复核，将可迁移工作流模式与不可采信的供应商宣传分开记录，不采用外部可执行依赖
Task type: `competitive_intelligence`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Official primary sources consulted during this bounded pass: FDA RBM Q&A, FDA Oversight of Clinical Investigations RBM guidance, FDA E6(R3) GCP (2025), and Medidata Clinical Data Studio official release.
- Chinese supplier pages consulted only as vendor self-description: Shanghai Spruce i-MR and CogniCRO.
- The durable research record is `records/active_slices/medical_monitoring_external_platform_research_20260803/RESEARCH_RECORD.md`.
- Current project sources remain the PRD/difference matrix, release audit, source/batch/risk contracts and the actual workbench filesystem; external material cannot override them.

## Scope

- In scope: a bounded English/Chinese platform landscape scan, primary-source verification, separation of transferable patterns from vendor claims, and a decision record for this project.
- Out of scope: vendor selection, procurement, adoption of closed-source tools or dependencies, real project data, clinical conclusions, source promotion, runtime/browser execution and release-gate changes.

## Success Criteria

- At least one English platform pattern and one Chinese public-platform pattern are recorded with source URLs and claim-quality labels.
- FDA/ICH principles are used to challenge product assumptions, not to claim local compliance.
- Concrete architecture/UI implications are written without changing code or authority state.
- Review and metrics records distinguish source-backed facts, vendor self-description, inference and residual uncertainty.

## Risk Boundaries

- Do not treat vendor marketing, search snippets or another model's confidence as product acceptance evidence.
- Do not introduce external executable dependencies or send private project data to third parties.
- Codex remains final authority; no release, source, medical or reviewer gate is changed by this research.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 20:52:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 20:53:00: Completed two-pass web review; verified FDA/ICH primary guidance and Medidata official release, and labelled Chinese vendor pages as self-described marketing evidence.
