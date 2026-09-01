# Task Context: medical_writing_prelaunch_release_20260717_v2

Created: 2026-07-17 22:40:52
Objective: 完成医学写作子系统上线前全功能多模型实测、P0/P1修复、Word精确保真、Codex终验并发布到固定5174/8911
Task type: `complex_delivery_conference`
Risk: `critical`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

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

- 2026-07-17 22:40:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
