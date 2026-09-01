# Task Context: provider_selector_research_20260726

Created: 2026-07-26 12:57:54
Objective: Research and design a capability-driven model Provider selector architecture for the medical writing workbench, compare native registry, LiteLLM gateway, and hybrid routes, and write a source-grounded report without modifying product code
Task type: `complex_delivery_conference`
Risk: `medium`
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

- 2026-07-26 12:57:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
