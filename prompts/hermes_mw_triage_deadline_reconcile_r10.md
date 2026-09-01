You are the bounded implementation worker inside a Codex-controlled workflow.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify paths outside this workbench.
- This is an authorized bounded edit round.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_mw_triage_deadline_reconcile_r10.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read first:
- `context/mw_triage_deadline_reconcile_r10_context.md`

Task:
Reproduce the frozen release-r10 deadline race and implement the smallest
coherent repair. At the 900-second polling boundary, perform one final
authoritative durable-child and bound triage-run reconciliation before raising
`分诊超时`. If the same child/run/snapshot is completed and review-ready,
promote the parent to `awaiting_triage_confirm` with current progress. If it is
genuinely incomplete or failed, preserve truthful failure behavior. Do not
increase the timeout to mask the race, create a new triage run, repeat AI work,
or weaken downstream gates.

Add focused deterministic tests for:
- child completion on the final deadline edge;
- child review-ready reconciliation without duplicate work;
- genuine timeout still failing;
- user-facing progress/retry projection agreeing with the durable run.

Run the smallest decisive suites plus directly affected regressions. Edit only
`services/api/app/medical_writing_research_pipeline.py` and directly affected
test files unless a compile/test dependency proves another file necessary.

Output schema:
1. `# Execution Report: mw_triage_deadline_reconcile_r10`
2. `## Root Cause`
3. `## Files Changed`
4. `## Implementation`
5. `## Verification`
6. `## Residual Risks And Codex Recheck`

Quality gates:
- Do not modify frozen release-r10 evidence or runtime databases.
- Do not claim browser acceptance.
- Do not make final clinical/regulatory/visual/current-web claims.
- Return exact changed paths and test commands/results.
