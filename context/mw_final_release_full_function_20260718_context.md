# Task Context: mw_final_release_full_function_20260718

Created: 2026-07-18 11:25:26
Objective: 对当前5174/8911医学写作候选执行cms-model、Grok Build grok-4.5、Reasonix deepseek-v4-pro三路真实全功能测试，修复P0/P1并复测，完成Word精确保真和上线门禁
Task type: `complex_delivery_conference`
Risk: `critical`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/RELEASE_RUNBOOK.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/frontend_remediation_matrix.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/ai_apply_gate_results_v2.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/POC_SUMMARY.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/openxml_release_gate_production_v1.json`
- `research/medical_writing_word_engine_comparison_20260718.md`
- Current candidate: `http://127.0.0.1:5174/`
- Current API: `http://127.0.0.1:8911/`
- Company/clinical source files named by those records are read-only evidence.

## Scope

- In scope:
  - actual desktop login and user interaction on the current candidate;
  - one greenfield workflow and one imported-project workflow, using an
    isolated runtime for writes and the stable candidate read-only;
  - project creation, two-stage framing/PICOS, corpus and competitor
    preparation, editor, tables, literature/citations, AI candidates,
    save/reload/restart/concurrency, DOCX export and release behavior;
  - independent review of the already persisted browser, AI, Word and
    OpenXML evidence without repeating every expensive model call;
  - exact P0/P1 defect ledger and original-scenario rerun instructions.
- Out of scope:
  - medical monitoring or other workbench subsystems;
  - new feature ideation unrelated to a reproduced writer workflow blocker;
  - public Sites deployment;
  - product source writes in the first pass;
  - any paid Word generator, renderer or conversion engine.

## Success Criteria

- Each assigned role reads the current records and actually operates a live
  workbench surface, not only source code or API route inventory.
- Every visible or logical function is either directly exercised in the role,
  covered by current durable evidence that the role inspects, or explicitly
  listed as unverified.
- The three roles jointly cover all acceptance-contract sections, including
  two real projects and greenfield RA.
- No HTTP 200, self-report or test count alone is accepted as proof; user-visible
  post-state, persisted state and error/recovery behavior are required.
- P0/P1 defects have reproducible steps, exact evidence and a bounded owner.
- Word conclusions preserve the free-tool boundary:
  `python-docx + controlled OOXML`, source-package minimal edits, MIT Open XML
  SDK structural gate, LibreOffice render-only, Microsoft Word final authority.

## Risk Boundaries

- Stable RUX/D001/PNH documents and source files are read-only.
- Stable 5174/8911 may be used for read-only spot checks. Any write journey
  must use a disposable runtime/random ports or an explicitly named disposable
  QA project and must be recorded.
- Do not expose keys, protected prompts, full clinical source text or direct
  identifiers in reports/screenshots.
- Product AI evidence must come from the configured direct DeepSeek route, not
  from the testing Agent's own prose.
- Do not install or recommend a commercial Word engine that needs payment for
  unrestricted production use.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Per role hard timeout: 7200 seconds. Poll no more often than needed to
  distinguish genuine progress from terminal failure.

## Loop Log

- 2026-07-18 11:25:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-18 11:28 CST: Current 5174/8911 candidate started. Release verifier
  passed 31 capabilities, schema 16, SQLite/audit checks, frontend/backend
  contract, and direct DeepSeek `deepseek-v4-pro`.
- 2026-07-18 11:28 CST: Production OpenXML gate passed 7/7 cases: one
  greenfield zero-error document plus D001 and RUX passthrough/edited contracts.
