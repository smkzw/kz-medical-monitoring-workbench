# Task Context: source_registry_workbench_ui

Created: 2026-07-07 23:49:33
Objective: Design and implement a shared source registry workbench UI and local-file registration API for the medical manager workbench business entry points: 证据调研与方案设计、数据分析与TFL、安全信号与PV协同.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected Hermes route: `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- TODO: Add authoritative local files, extracts, datasets, screenshots, URLs, or user-provided materials.
- Do not add production paths unless the user has explicitly authorized reading them for this task.

## Scope

- In scope: shared source registry UI, local file/directory registration API, server-side source_id to AI task request resolution, independent AI provider boundary, browser QC for 证据调研与方案设计、数据分析与TFL、安全信号与PV协同.
- Out of scope: building non-medical clinical-development links; exposing lifecycle numbers in user-facing subsystem names; treating source registry preview rows as final medical conclusions.

## Success Criteria

- User-facing navigation and page titles use business names only and do not show 第几环节, 阶段编号, or Stage N.
- First/四/五 non-medical links are absent from module catalog and UI.
- Each of the three source-registry pages can register at least one real local source and prepare an AI task using source_ids.
- AI task preparation records blocked run when external provider is not configured; no Codex fallback is used.
- Public source list hides server paths and bounds preview payloads.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Hermes is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-07 23:49:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
