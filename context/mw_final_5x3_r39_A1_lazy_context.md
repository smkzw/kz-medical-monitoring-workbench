# Task Context: mw_final_5x3_r39_A1_lazy

Created: 2026-07-30 00:18:47
Objective: A1 lazy_medical_writer black-box external test: COPD Phase III inhaled fixed combination greenfield through product AI pipeline and DOCX/Word gates; no source changes
Task type: `html_ppt_visual_browser`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

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

- 2026-07-30 00:18:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
