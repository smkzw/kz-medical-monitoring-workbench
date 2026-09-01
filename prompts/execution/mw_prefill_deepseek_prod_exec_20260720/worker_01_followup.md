Continue the same `worker_01` session. Read `/Users/smkzw/.hermes/SOUL.md`
fully again as required by the execution runtime.

Hard boundaries:
- Work only inside the current workspace root.
- Keep the original `worker_01` source write set.
- Do not edit tests, frontend, records, runtime databases, global
  configuration or credentials.
- Do not make a production deployment or stable database write.

Read these files only:
- `context/mw_prefill_deepseek_prod_exec_20260720_execution_context.md`
- `reviews/codex_prefill_deepseek_initial_review_20260720.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/QODER_AND_CTGV_BASELINE_20260720.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`

Runner-managed report path: `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_01_remediation.md`.

Return the complete report in final text; do not write that report directly.

Keep the original source write scope. Perform a targeted remediation of the
five Codex findings; do not broaden the architecture:

1. Replace the broad AI eligible-field set with an explicit minimal allowlist.
   AI must never rewrite product, indication, phase, protocol identity,
   version or target mechanism merely because those are writable by the user.
2. Add an enforceable exact-fact content gate for AI free-text candidates.
   Unsupported dose, regimen, visit timing, washout, threshold, endpoint,
   sample size, AESI or similar exact facts must be rejected/quarantined unless
   the candidate points to direct source IDs supplied in the input. Prompt
   text alone is not enforcement.
3. Do not label generated AI text as `study_definition` evidence and do not
   treat candidate text as its own evidence. Keep AI provenance separate from
   real StudyDefinition/snapshot evidence.
4. When an adopted field changes the competitor-search contract, rebuild the
   versioned search plan atomically (new plan id/revision) or fail closed.
   Specifically prove that adopting the English condition term replaces the
   original Chinese `registry_filter.condition_term`.
5. Do not pass the first five snapshot titles blindly. Apply deterministic
   minimum relevance screening using structured conditions, phase, study type
   and public Protocol/SAP availability; provide structured hints to the model.

Preserve:
- one bulk call;
- direct `deepseek-v4-pro` model identity;
- model call outside SQLite write transaction;
- deterministic full/partial fallback;
- user adoption as the single project-fact decision;
- optimistic conflict and idempotency behavior.

Run the focused tests that are available after worker_02 edits. If worker_02 is
still writing its test file, do not edit that file and limit yourself to source
tests plus a precise rerun request.

Output schema:
1. `# Remediation Output: mw_prefill_deepseek_prod_exec_20260720 - worker_01`
2. `## Boundary Check`
3. `## Codex Findings Resolved`
4. `## Files Changed`
5. `## Tests And Observations`
6. `## Remaining Risk`
7. `## Next Step`
