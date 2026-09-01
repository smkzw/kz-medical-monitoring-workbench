# Task Context: mw_final_release_matrix_20260727

Created: 2026-07-27 05:06:53
Objective: 医学写作系统最终上线门：隔离运行时、独立AI/OCR/Hy-MT2翻译、DOCX精确导出、四测试者十二适应症真实浏览器端到端LOOP，全部通过后方可上线。
Task type: `complex_delivery_conference`
Risk: `critical`
Selected agent route: `mixed` / `conference:pi-qwen38-chair+pi-cms+codebuddy-deepseek-pro` / `mixed:Pi Qwen3.8 xhigh chair; Pi CMS and CodeBuddy DeepSeek V4 Pro participants`

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

- 2026-07-27 05:06:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
