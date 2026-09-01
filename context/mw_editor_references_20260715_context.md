# Task Context: mw_editor_references_20260715

Created: 2026-07-15 14:18:29
Objective: 统一医学写作正文与表格富文本/全屏编辑，压缩主工作台信息密度，并实现项目级文献库、GB/T 7714-2015引文、自动参考文献、AI可追溯引用和Word导出闭环
Task type: `complex_delivery_conference`
Risk: `high`
Selected agent route: `mixed` / `conference:aishuo-gpt55-gpt55-chair+aishuo-minimax+opencode-go-deepseek-flash` / `mixed:Hermes default reasoning; qwen then mimo replacement order`

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

- 2026-07-15 14:18:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
