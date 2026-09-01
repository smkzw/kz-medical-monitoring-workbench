# Task Context: medical_monitoring_structure_driven_intake_20260804

Created: 2026-08-04 08:55:59
Objective: 让 raw listing/domain 识别优先使用可解释的字段结构而非项目名或固定 sheet 名；未知/歧义结构显式暴露并 fail-closed，完成聚焦、相邻与全量验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md`; current
  `services/api/app/monitoring_raw_intake.py` and its raw-intake/source-classifier
  tests; current five-project/anti-overfit records.
- User requirement: different protocols, drugs and data-listing layouts must be
  recognized without project-name or one-listing overfit.
- Current filesystem and B6/C14 artifacts remain authoritative.

## Scope

- In scope: add a conservative header-shape fallback for previously unknown
  listing sheet/domain names, expose unclassified sheets instead of silently
  dropping them, and test recognized, ambiguous and unknown synthetic shapes.
- Out of scope: real project execution, source registration, provider/AI calls,
  database/API route changes, B6/C14, runtime, browser, medical conclusions,
  and broad refactors of existing CDISC/domain rules.

## Success Criteria

- Known domain-code/sheet rules remain unchanged.
- Unknown sheet names can be classified only when at least two explicit
  structure-header signatures agree on one domain; ambiguous or under-specified
  sheets are returned in `unclassified_sheet_names` and not assigned a domain.
- No project ID, project label or filename is used by the fallback classifier.
- Focused, adjacent and clean full monitoring tests pass; no service or reserved
  port is started.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Preserve existing domain precedence and source-domain boundaries; a fallback
  must never merge concomitant medication with study-drug administration or
  turn ambiguous rows into clinical facts.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 08:55:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 08:56:00: Static audit found `_domain_group_key` depended on a
  fixed code/sheet-name list and silently dropped unknown sheets; this slice
  will add a conservative structure-header fallback and explicit unknown output.
- 2026-08-04 17:10:00: Implemented the header-shape fallback and
  `unclassified_sheet_names`; focused 27 passed and full monitoring 1957
  passed. A targeted stop restored reserved ports 8911/5174 to empty after
  unrelated workbench listeners appeared during the focused run.
