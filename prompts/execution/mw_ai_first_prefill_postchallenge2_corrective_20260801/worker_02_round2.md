Continue the same worker_02 session. The first pass executed many tool calls,
but its final output was truncated by an OMP plugin handler timeout to only:
"Full suite run for final evidence:". That is not an auditable report.

Hard boundaries:
- Work only inside the current workspace `.`.
- Do not touch medical-monitoring, r4/r5/r6, or source-runtime evidence.
- Preserve worker_01 backend changes, especially its `main.py` policy response.
- Do not start a service or browser.
- Runner-managed report path:
  `runs/execution/mw_ai_first_prefill_postchallenge2_corrective_20260801/worker_02.md`;
  return the report and let the runner persist it.

Initial read set:
- `AGENTS.md`
- `context/mw_ai_first_prefill_postchallenge2_corrective_20260801_execution_context.md`
- `runs/execution/mw_ai_first_prefill_postchallenge2_corrective_20260801/worker_01.md`

Re-read the current shared tree and finish the original worker_02 assignment.
Confirm and, only if still needed, complete the real frontend and duplicated
QC/helper changes so that:
- an empty recommendation stays empty and never falls back to an unsafe
  candidate;
- manual_only, insufficient, unsupported-gap, and pending field/composite
  actions are disabled with accurate concise reasons;
- genuinely safe alternatives remain selectable;
- the dead single-card action is disabled rather than issuing a deterministic
  policy rejection;
- structured policy rejection is distinguished from revision conflict and
  never displays the misleading concurrency retry message.

Add or confirm focused frontend contract/QC tests for empty slot, unsafe
alternative, safe alternative, dead single-card action, and error mapping.
Re-read/hash worker_01-touched `main.py` before any edit and avoid editing it
unless strictly necessary to preserve the agreed structured error contract.
Run the focused frontend checks and the relevant combined suite needed to
report final evidence.

Return the complete seven-section Execution Output schema from the original
prompt, including:
- exact changed paths and final SHA-256 hashes;
- exact commands and pass/fail counts;
- whether the initial truncated pass had already made edits;
- preservation of worker_01 behavior;
- blockers, residual risk, and the next serial step.
Do not end with another progress sentence.
