# Task Context: mw_pipeline_validation_gate

Created: 2026-07-26 16:01:54
Objective: 修复医学写作研究流水线文档校验越权自动 override，仅允许 confirmed 或真实用户 user_overridden 文档进入翻译，并补回归测试
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_preparation_batch.py`
- Direct regression tests under `tests/`.

## Scope

- In scope: remove pipeline-owned content-validation override; gate translation
  on `confirmed`/`user_overridden`; preserve mismatch details; separate clean
  structure approval; add recoverable waiting states; add direct tests.
- Out of scope: API restart, live PNH jobs, runtime databases, project records,
  heavy file security scanning, frontend changes, unrelated refactors.

## Success Criteria

- No `override_document_validation` call remains in the research pipeline.
- `confirmed` and prior explicit `user_overridden` documents may proceed.
- `needs_review`/`mismatch` documents remain unchanged and block translation.
- Unresolved structure review cannot be cleared by content admission.
- User override followed by continuation resumes without re-extraction.
- Translation-scope failure does not continue to round-1 analysis.
- Direct and writing-reference regression suites pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 16:01:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26 16:05: Direct validation-gate tests passed 5/5.
- 2026-07-26 16:07: Added explicit translation-scope waiting state after
  self-review found a neighboring swallowed `ValueError`.
- 2026-07-26 16:09: Final direct tests passed 6/6; writing-reference and corpus
  regression suite passed 278/278; Ruff passed.
