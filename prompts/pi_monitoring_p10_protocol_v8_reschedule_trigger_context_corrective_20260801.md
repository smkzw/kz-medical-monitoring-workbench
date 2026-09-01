You are Pi running inside a Codex-controlled finite-code workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- This is one explicitly authorized edit round, limited to:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py` only if a direct prompt-version or
    cutover assertion requires it.
- Do not modify any other product, test, runtime, task-record, medical-writing,
  frontend, or real-project file.
- Do not start services, workers, browsers, ports 8911/5174, or any canary.
- Do not read or modify runtime databases or backups.
- Tools are available and must not be disabled. Use only the local
  read/search/edit/test tools needed for this bounded implementation.
- Codex remains final acceptance authority.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801_context.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`
- `context/monitoring_p10_loop316_protocol_v7_visit_canary_pause_20260801.md`
- `runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v7_visit_canary_20260801.md`
- `reviews/codex_monitoring_p10_loop316_protocol_v7_visit_canary_20260801_review.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`

Task:
Implement the offline v8 corrective and its focused regression tests.

Required behavior:
1. Change the active prompt identity to
   `monitoring-protocol-clause-structuring-v8`. Add v7 to the explicit terminal
   legacy set without losing v3-v7 history, stale-job behavior, or cutover
   semantics.
2. Make visit-family classification semantic-role aware. Schedule/window terms
   used only in the title, trigger, or action object of one reschedule rule must
   not create a separate schedule family. Do not implement global reschedule
   precedence.
3. The exact v7 repaired candidate must be reschedule-only and valid:
   - title: `计划访视改期原则`
   - text: `若受试者无法在研究流程图规定的访视窗口期内前往研究中心，可在另一时间重新安排访视；应尽一切努力重新安排尽可能接近原始访视日，受试者不应因排程困难而错过方案规定的访视。`
4. `调整计划访视日期` must be reschedule-only. A phrase such as
   `计划访视改期原则` must not create a schedule family by itself. Trigger
   clauses introduced by `若` / `如果` / `无法` / `未能` and containing
   `访视窗口` / `访视窗` / `计划访视` must not count as schedule unless
   there is a separate independent schedule assertion.
5. True mixed-family content must still fail, including:
   `所有计划访视应在时间窗内完成；若无法到访，应重新安排。`
   An independent week schedule plus `调整计划访视日期` must also fail.
6. Preserve pure schedule, reschedule, and unscheduled classification and all
   existing negative combinations.
7. Preserve boundary precedence medication -> dispensing/PK -> withdrawal ->
   safety -> collection -> visit family.
8. Preserve complete candidate-indexed deterministic errors, exactly one
   controlled repair, whole-response atomicity, C1-C5, C3 8-to-15,
   structure/evidence blockers, and user-owned candidate decisions.
9. Update both initial and repair provider-visible contracts so they say that
   a reschedule candidate may retain plan/window language only as trigger or
   object, whereas an independent schedule obligation plus reschedule action
   must be split.

Implementation guidance:
- Prefer a small helper that evaluates semantic roles per clause/segment rather
  than a single concatenated-family regex or global precedence.
- A segment with an independent normative schedule assertion (`应`, `必须`,
  `需`, `所有`, week/timing rule, or equivalent) remains schedule even when a
  separate reschedule segment exists.
- Keep changes surgical and consistent with nearby style. Do not add a
  dependency or refactor unrelated logic.
- Inspect current files before editing and preserve unrelated user changes.
- Use the safest precise editing mechanism available.

Focused verification:
- Add explicit positive and negative tests for the examples above, including
  an exact regression for the v7 repaired candidate.
- Run Python compile checks for edited Python modules.
- Run the narrowest decisive tests that cover visit classification, prompt
  initial/repair text, version history/cutover, indexed repair atomicity, and
  topic-boundary precedence.
- Do not run the full monitoring suite or medical-writing suite; Codex owns
  those broader acceptance checks.

Output schema:
1. `# Pi Execution Report: monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Work Performed`
5. `## Changed Files`
6. `## Verification`
7. `## Observations And Failed Paths`
8. `## Uncertainty And Codex-Owned Checks`
9. `## Next Recommended Action`

Quality gates:
- Report exact changed paths and exact commands/results.
- If any authorized file differs from the context hash before your edit,
  inspect it and preserve the current filesystem; flag the difference rather
  than restoring or overwriting it.
- Do not claim final acceptance, online behavior, canary success, or medical
  correctness.
- If the required behavior cannot be achieved within the authorized paths,
  stop without expanding scope and report the blocker.
