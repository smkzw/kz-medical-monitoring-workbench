# Task Context: mw_omlx_role_gate_20260726

Created: 2026-07-26 15:30:58
Objective: Implement and verify OCR/translation role-binding consumption and shared oMLX 8+8 workload gate without touching the live 8911/5174 runtime
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `/Users/smkzw/.codex/codex_agent_mode_overlay.md`
- `/Users/smkzw/.codex/tools/omlx_workload_gate.py`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/evidence/SUBAGENT_AI_ROLE_SELECTOR.md`
- Existing OCR/translation adapters and their focused tests.

## Superseded Scope Note

This pre-runtime-ownership context is retained for audit only. Its former
alternate body-model assumption is invalid. The active contract is:
`dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`, selected exclusively by the shared gate.

## Scope

- In scope: shared gate client; OCR/body-translation/support-role binding
  consumption; OCR minimum 200 DPI; gate-owned Hy-MT2 execution;
  execution-readiness status; focused and 10+10
  concurrency tests; durable evidence.
- Allowed product paths are limited to the files named in the user's current
  request.
- Out of scope: competitor triage, research/corpus pipeline, frontend,
  changing the global gate tool, production model installation, and all
  operations against live ports 8911/5174.

## Success Criteria

- Every actual oMLX OCR or translation HTTP operation acquires the shared
  SQLite gate before transport, heartbeats while in flight, and releases in
  `finally`.
- OCR/body/support adapters resolve profile, base URL, model, credentials and
  enabled state from the role binding at call time.
- OCR below 200 DPI is rejected before HTTP.
- The gate-owned Hy-MT2 binding runs the validated body pipeline and records
  the actual leased model; callers cannot choose or override it.
- Status separates configured role, inventory availability, execution wiring
  and current runnability without returning secrets.
- A fake-transport 10 OCR + 10 translation pressure test observes OCR <= 8,
  translation <= 8 and total <= 16.
- Focused regression passes without restarting or probing the live runtime.

## Risk Boundaries

- Do not restart, stop, probe, browse or otherwise operate ports 8911/5174.
- Do not mutate the active PNH durable job or its research/triage state.
- Do not output credentials or private source contents.
- Do not treat model inventory or configuration visibility as an executed
  business-call pass.
- Codex owns final source review, focused regression and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 15:30:58: Task initialized by `tools/hermes_workflow_guard.py init-task`.
