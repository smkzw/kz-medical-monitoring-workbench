# Task Context: mw-word-native-visual-qc-20260725

Created: 2026-07-25 00:39:49
Objective: 对Microsoft Word原生导出的13页PDF渲染图做只读视觉验收，并写逐页PASS/FAIL报告
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- TODO: Add authoritative local files, extracts, datasets, screenshots, URLs, or user-provided materials.
- Do not add production paths unless the user has explicitly authorized reading them for this task.

## Scope

- In scope: TODO
- Out of scope: TODO

## Success Criteria

- TODO

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 00:39:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
