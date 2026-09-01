Continue the same `mw_a1_triage_finalize_r8` execution session. Read the
current versions of the files below because the Cursor execution manager made
two accepted remediations after your first pass.

Hard boundaries and writable scope remain exactly those in
`context/mw_a1_triage_finalize_r8_context.md`. Preserve:
- the manager's stale-finalized-snapshot correction in translation scope;
- the manager's distinct durable resume business key;
- all frozen r8 evidence as read-only.

Read these files only:
- `context/mw_a1_triage_finalize_r8_context.md`
- `runs/hermes_mw_a1_triage_finalize_r8.md`
- `runs/cursor_mw_a1_triage_finalize_r8_manager.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `tests/test_medical_writing_triage_recovery_api.py`
- `tests/test_medical_writing_research_pipeline_minimum_start.py`

Runner-managed output path:
`runs/hermes_mw_a1_triage_finalize_r8_followup.md`. Never write this report
path through tools; return the report and let the runner persist it.

Codex found one remaining P0 conflict that both prior reviews missed:

- `ResearchPipelineDurableExecutor.execute()` receives
  `resume_from == "awaiting_triage_confirm"` and comments that the basket is
  already confirmed.
- It then calls `continue_after_triage()`.
- `continue_after_triage()` unconditionally calls `_confirm_triage_basket()`.
- `_confirm_triage_basket()` can call `confirm_basket()` again using a different
  idempotency key and can recompute retained candidates from the AI
  recommendation/public-document subset.

That can reconfirm, conflict with, or overwrite the medical manager's exact
one-click batch decision. It violates the task contract even if the second
confirmation happens to fail and fall back.

Required repair:
1. A resume created by the successful basket-confirm endpoint must carry and
   consume the exact authoritative retained scope from that confirmation or
   its current locked-snapshot projection.
2. The already-confirmed resume path must not call `confirm_basket`,
   `_confirm_triage_basket`, or legacy `finalize_triage` again.
3. Thread the frozen retained IDs through both durable payload and synchronous
   fallback. Validate they still match the current locked-snapshot confirmed
   projection before beginning preparation.
4. Preserve medical-manager adjustments exactly; do not recalculate the basket
   from AI classifications or public-document preference.
5. Add behavioral tests proving:
   - a manager-adjusted retained set is passed unchanged into preparation;
   - the confirmed resume path never calls the confirmation/finalization
     helpers;
   - stale/mismatched projection is rejected;
   - repeat/reload remains idempotent.
6. Make the queued/wake transition truthful. If wake cannot be issued, do not
   leave a false `preparing` state that implies work started. Keep the smallest
   coherent state change and test it.
7. Run the focused suites. Do not start browser E2E or claim release acceptance.

Return:
# Hermes Execution Handoff: mw_a1_triage_finalize_r8_followup
## Boundary Check
## Files Changed
## Implementation
## Tests Run
## Failed Paths Or Uncertainty
## Codex-Owned Verification
## Next Recommended Action
