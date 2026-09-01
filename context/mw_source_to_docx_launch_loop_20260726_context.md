# Task Context: mw_source_to_docx_launch_loop_20260726

Created: 2026-07-26 17:46:57
Objective: 在不重复已验收切片的前提下，完成医学写作系统从真实竞品Protocol检索、确认、下载、内容校验、解析、翻译、适应症特异语料准入、独立AI候选写作、编辑、引用、表图、研究流程图到原生DOCX导出的生产闭环，并形成四测试者十二适应症真人E2E上线矩阵的可执行实现与验证证据
Task type: `long_horizon_code`
Risk: `critical`
Selected agent route: `kimi-code` / `kimi-code/k3` / `high`

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

- 2026-07-26 17:46:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
