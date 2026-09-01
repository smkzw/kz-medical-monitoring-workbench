You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner's current workspace.
- Do not read or modify production paths.
- This is an explicitly authorized edit round. First verify the frozen hashes
  in the task context. You may edit only:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_startup_recovery.py`
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_v11_datagap_semantic_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_v11_datagap_semantic_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v10_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

Task:
Implement the complete offline v11 corrective described in the task context.
The proven defect is that `_visit_topic_view` loses `claim.kind` and treats a
legitimate DATA_GAP retrieval question as an operative schedule fact. Preserve
all full-boundary and evidence safety gates. Do not solve this with regex
expansion, global reschedule precedence, prompt-only wording, or by excluding
FACT/INFERENCE/RECOMMENDATION claims.

Required work:
1. Exclude only semantically valid DATA_GAP claim text from visit action-family
   counting; retain it in boundary/absence/evidence/anchor/conflict checks.
2. Add a fail-closed DATA_GAP kind-semantics rule so affirmative protocol
   actions/obligations cannot bypass family validation by changing claim kind.
3. Produce an auditable family trace sufficient for repair: candidate index is
   already provided by aggregate validation; add detected families and the
   relevant surface path/claim kind/matched span or an equivalently precise
   deterministic locator. Carry this into the repair validation-errors payload.
4. Advance the protocol prompt identity from v10 to v11. Add v10 to
   `PROTOCOL_RETIREMENT_AUDIT_PROMPT_VERSIONS`; keep
   `PROTOCOL_STATUS_LEGACY_PROMPT_VERSIONS` exactly v3-v8.
5. Add the focused and adjacent regressions from the context, including the
   exact full failed-canary candidate shape and exact frozen v10-to-v11
   same-business-key history preservation.
6. Run focused tests first, then the declared adjacent monitoring suite within
   the remaining time. Do not start any service/runtime/provider/real project.

Prefer the smallest coherent implementation. Preserve all unrelated current
changes. If the exact trace contract would require broad redesign, implement
the smallest deterministic string trace that makes the repair actionable and
state the residual limit rather than changing schemas or APIs.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_v11_datagap_semantic_corrective_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Files Changed`
5. `## Implementation`
6. `## Verification`
7. `## Failed Paths Or Residual Risk`
8. `## Codex-Owned Acceptance`

Quality gates:
- Do not claim access to sources not actually read.
- Report exact commands/results and final hashes.
- Do not claim runtime, clinical, release or final acceptance.
