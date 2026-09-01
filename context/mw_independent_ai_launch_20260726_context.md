# Task Context: mw_independent_ai_launch_20260726

Created: 2026-07-26 15:57:07
Objective: 验证并修复医学写作工作台独立AI全链路，完成真实项目回归、语料泛化、清理和上线前多测试者矩阵
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/CODEX_RESUME_P0_18_20260726.md`
- `records/handoffs/AGENT_1_CURSOR_HANDOFF_20260725.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/01_NEXT_STAGE_EXECUTION_PLAN.md`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/PNH_V16_SCIENTIFIC_FAILURE.md`
- Current source under `services/api/app`, `frontend/src`, `packages/contracts`
  and focused tests under `tests/`.
- The real local runtime at `http://127.0.0.1:5174` and
  `http://127.0.0.1:8911`, using API contract
  `medical-writing-api-2026-07-17.1`.
- The immutable PNH ClinicalTrials.gov search snapshot
  `wref_search_2770fdd35e669d9e2e7d`.

## Scope

- In scope: independent-AI provider execution and prompt quality; evidence-bound
  competitor search/triage; document-content validation and explicit user
  override; source extraction/OCR/translation/corpus admission; indication-,
  phase-, purpose-, modality-, route- and design-specific corpus
  generalization; writing candidates; DOCX production; final multi-tester
  browser matrix; test-data cleanup after evidence preservation.
- In scope for external execution/conference: only assigned bounded write paths
  or listed evidence locators. Return compact conflict/risk deltas.
- Out of scope: security/backdoor audits, unrelated workbench subsystems,
  replacing the product AI with an external tester model, and re-auditing
  previously accepted surfaces without a propagation conflict.

## Success Criteria

- Product independent AI executes without Codex or tester substitution and
  passes real source-to-result scientific review.
- PNH v17 inspects complete condition sets and does not repeat the four v16
  false indication-mismatch conclusions.
- Corpus findings are typed as wording convention, clinical design requirement,
  or regulatory common structure and are assessed against a complete,
  explicitly sparse target layer; cross-indication clinical logic cannot
  become high-confidence reusable wording.
- Needs-review/mismatch document validation never auto-overrides; the user may
  explicitly override with retained warnings and then resume without repeating
  download/extraction.
- Gate B-D real workflows and final four-tester/twelve-indication browser matrix
  complete from clean projects through full DOCX export.
- Runtime readiness, focused regressions, real browser behavior, source-bound
  evidence and Word fidelity pass before launch.

## Risk Boundaries

- Production source writes are allowed only in the bounded paths assigned by
  Codex; every slice records changed files, SHA-256 and focused tests.
- Do not confirm or project the invalid PNH v16 basket.
- Do not use corpus override, skeleton output, deterministic fallback or an
  external tester's own medical content as PASS evidence.
- OCR and translation must use the shared oMLX workload gate. The gate-owned
  body model is `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`; no alternate or
  caller-owned body-model name may be introduced.
- Do not restart the API while a real independent-AI durable job is running
  unless recovery evidence shows the restart is required.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 15:57:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26 16:18:37: Restarted matching runtime and started PNH v17 real
  independent-AI run `ct_run_c2cc520378fc03a8d310` /
  `mwjob_6467e941ee84a15083814bf6`.
- 2026-07-26 16:20: Focused regressions passed: triage 378, corpus 36,
  document-validation gate 6. Two integration conflicts were returned to the
  original subagents for same-context bounded repair.
