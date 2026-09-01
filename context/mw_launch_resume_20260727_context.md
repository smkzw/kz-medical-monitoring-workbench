# Task Context: mw_launch_resume_20260727

Created: 2026-07-27 08:02:11
Objective: Close remaining medical-writing launch gates: Word-native visual acceptance, six synopsis fixtures, independent-product-AI readiness, and verified four-tester 4x3 E2E loops
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/NO_LOSS_PAUSE_20260727_0618.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `evidence/mw_docx_release_gate_20260727/PAUSE_CHECKPOINT.md`
- `runs/execution/mw_final_4x3_harness_20260727/input_fixtures/PAUSE_CHECKPOINT.md`
- `scripts/qc/mw_final_4x3_matrix.json`
- `prompts/final_4x3_e2e_20260727/`
- Current global `/Users/smkzw/.codex/AGENTS.md` and compact route overlay.
- The live product runtime at `127.0.0.1:8911` and `127.0.0.1:5174`.

## Scope

- In scope: product functionality and clinical/scientific correctness for the
  medical-writing release; independent-AI/OCR/translation route readiness;
  exact DOCX/Word output; concise desktop UX; isolated real-browser E2E; test
  evidence and recovery records.
- Out of scope: unrelated workbench subsystems, broad security/backdoor audit,
  mobile-first compromises, synthetic PASS artifacts, corpus-gate override,
  and using an external tester's own prose as product AI output.

## Success Criteria

- No active frontend/backend/build/config/deploy reference to the invalid
  `Hy-MT3` alias; exact guard test passes.
- Product independent AI is dynamically bound, directly runnable without
  Codex/Hermes/tester assistance, and used by all semantic writing paths.
- OCR/translation calls respect the shared gate: OCR 8, translation 8, total
  16; the body translator is the gate-owned Hy-MT2 model.
- Word-native output passes structure, field, typography, table/figure,
  attachment and visual checks against the authoritative Chinese references.
- Six synopsis-import fixtures and greenfield paths are exercised from clean,
  isolated runtimes without project leakage.
- All four exact tester identities complete their locked three-indication
  matrix through the visible UI to complete protocol DOCX output, with
  engineering and lazy-writer perspectives and remediation loops.
- No launch PASS is declared until all decisive gates have evidence.

## Risk Boundaries

- Product writes are limited to reproducible launch blockers and their focused
  tests. Existing user documents, stable runtime data and unrelated changes
  must remain untouched.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Aishuo is forbidden from 00:00 through 08:30 Beijing time. Tester A is
  preferred from 22:00 through 06:00. Exact tester identities fail closed.
- Historical failure evidence is retained. Clearly obsolete task-created
  temporary artifacts are cleaned only after their evidence has been recorded.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-27 08:02:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-27 08:03-08:06: Hy-MT3 guard broadened and passed; Tester D
  Antigravity Gemini identity proven and matrix updated; focused independent
  AI and oMLX regression passed 157 tests after correcting one stale test
  isolation contract.
