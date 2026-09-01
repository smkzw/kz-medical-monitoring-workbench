# Task Context: medical_monitoring_ai_generalization_contract_20260804

Created: 2026-08-04 08:39:23
Objective: 为独立医学监查 AI 增加方案结构、药物/干预结构、data listing 结构的哈希绑定抗过拟合证据契约，并让 release gate 缺失或不完整时 fail-closed；完成聚焦、相邻、全量验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `AGENTS.md` (global and workspace/workbench overlays), the current
  `monitoring_ai_evaluation_matrix.py`, `monitoring_ai_release_gate.py`, their
  tests, and the existing Phase F/P4 records.
- User requirement in the active goal: independent AI must recognize different
  protocol, drug/intervention, and data-listing structures instead of overfitting
  to one project.
- Current filesystem and current B6/C14 gate artifacts remain authoritative.
- No real project roots, provider, queue, database, runtime, browser, or
  reserved port may be used in this slice.

## Scope

- In scope: add an immutable, hash-bound offline generalization evidence
  contract; validate explicit protocol-structure, drug/intervention-structure,
  and listing-structure classes; require real-project diversity and a
  non-duplicate unseen holdout; bind evidence to evaluator and observation
  revisions; make the independent-AI release gate block when evidence is absent
  or incomplete; add focused tests and update only directly affected records.
- Out of scope: provider calls, prompt/model activation, AI queue or runtime,
  source ingestion, database/API changes, actual project execution, browser or
  Playwright tests, B6/C14 changes, medical conclusions, and modifications to
  parallel medical-writing routes.

## Success Criteria

- A deterministic evidence builder rejects malformed/placeholder profiles,
  exposes missing/duplicate/low-diversity/holdout issues, and produces a stable
  snapshot hash without inferring classes from project names.
- `build_independent_ai_release_gate` requires this evidence and returns
  `blocked` with explicit reasons when it is absent, revision-mismatched, or
  incomplete; a complete fixture can still reach only the existing offline
  `READY_FOR_CONTROLLED_ACTIVATION` status with runtime/provider/write flags
  false.
- Focused, directly adjacent, and clean full `tests/test_monitoring*.py`
  suites pass; no reserved port or service is started.
- Review gate has no verification errors and the loop ledger records the
  bounded change, evidence, and residual risk.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Preserve the existing matrix/release evidence semantics: generalization
  evidence is structural anti-overfit evidence only, never clinical correctness,
  model quality, release approval, runtime permission, or write authority.
- Do not treat fixture labels as real project evidence; real five-project
  evidence remains blocked until B6/C14 and the source/CAS sequence are formally
  satisfied.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 08:39:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 08:40:00: Static audit found the existing matrix covers only
  project×task cells; release gate had no explicit protocol/drug/listing
  structure evidence and therefore could not detect structural overfit.
- 2026-08-04 16:58:00: Added the immutable generalization evidence contract and
  fail-closed release-gate binding. Focused 21 passed, adjacent 754 passed, and
  full monitoring 1956 passed; reserved ports remained empty. Awaiting review
  gate closure before moving to the next offline slice.
