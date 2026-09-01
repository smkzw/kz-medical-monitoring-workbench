# Task Context: mw_launch_retake_20260726

Created: 2026-07-26 14:50:56
Objective: 接管医学写作工作台，优先使独立AI预填、竞品Protocol分诊/语料分析和章节写作达到真实可用，再完成回归、清理与上线验收
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/CODEX_RESUME_P0_18_20260726.md`
- `records/handoffs/AGENT_1_CURSOR_HANDOFF_20260725.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `runs/execution/mw_systemic_e2e_loop_20260726/LOOP_STATUS.md`
- Current source and runtime under this workbench; audience runtime is
  `http://127.0.0.1:5174/` with API `http://127.0.0.1:8911/`.
- Real project sources already registered in the workbench and the user-provided
  local protocol/synopsis/IB/reference files remain clinical source authority.

## Scope

- In scope: independent-AI runtime selection and real product calls; evidence
  grounded authoring prefill; CT.gov competitor Protocol/SAP discovery,
  triage, preparation, OCR, translation and corpus analysis; chapter revision;
  corpus generalization; editor/DOCX/runtime regression; historical test-residue
  classification and cleanup; final four-tester browser matrix.
- Out of scope: security/backdoor hunting, stages 1/4/5 of the broader clinical
  workbench, new non-writing modules, and any corpus-gate override or
  skeleton-only PASS.

## Success Criteria

- Independent AI runs without Codex/conference-model dependency and produces
  evidence-bound, scientifically usable product artifacts for prefill,
  competitor research/corpus analysis and chapter writing.
- No unsupported clinical facts, numeric thresholds, cross-indication disease
  logic or single-source high-confidence conclusions enter writing candidates.
- OCR and translation routes are explicit, versioned, capacity-gated and do not
  silently substitute an unavailable required model.
- Focused and adjacent regression pass; real browser and DOCX/Word output pass
  audience-facing acceptance.
- Final Pi/Qwen, Pi/CMS, CodeBuddy/Hy3 and Cursor/auto tester matrix completes
  full protocols from clean state with distinct non-oncology indications.
- Durable records clearly separate accepted evidence from invalidated historical
  test claims.

## Risk Boundaries

- Local implementation/runtime writes are authorized. Do not deploy externally
  or treat the system as launched until Codex review gates pass.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Preserve source documents; never overwrite originals. Do not use corpus
  override, unbound skeleton content or another Agent's own writing in place of
  the configured product AI.
- Tests must use `env -u PYTHONPATH python3` to avoid mixed Python environments.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 14:50:56: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26 14:51: Independent AI Qwen prefill v7 passed fail-closed product
  execution; Protocol-level research and corpus analysis remain the next gate.
- 2026-07-26 14:51: Real 652-study competitor triage is running but the current
  44-call sequential design is recorded as a production-throughput blocker.
