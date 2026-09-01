You are Pi continuing the same Codex-controlled finite-code session
`019fba70-4de6-7000-b944-c145c409f6db`.

First, re-read and comply with `/Users/smkzw/.hermes/SOUL.md`. State whether
you read it fully in the returned report.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- This is one consolidated same-session recovery round.
- You may edit only:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
- Do not change prompt identity, legacy/cutover files, APIs, runtime databases,
  task records, frontend, medical-writing, or real-project material.
- Do not start services, workers, browsers, providers, ports 8911/5174, real
  projects, or a canary.
- Preserve all current filesystem changes; do not restore baseline files.
- Runner-managed output path:
  `runs/pi_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801_followup1.md`.
  Never write or edit that report path; return the report in your final
  response so the runner can persist it.

Read these files only:
- `context/monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801_context.md`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`
- `runs/pi_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801.md`

Current accepted pre-follow-up hashes:
- `services/api/app/monitoring_ai_service.py`:
  `7e5e06e099f5f1b2cae0d7eb34cd57359abe801408efb2f52864adf65c11cc5f`
- `tests/test_monitoring_ai_service.py`:
  `5162d96b2ab3cea8c0452bbc43bd0106db5fc02cf7ca8e28fcc9380b366237b7`

Codex review found the first pass is incomplete. All four phrases below are one
reschedule rule under the declared v8 semantic-role contract, but the current
classifier returns `reschedule + schedule`:

1. `访视窗口改期原则`
2. `若无法到访，应在访视窗口内重新安排访视。`
3. `在原访视窗口内重新安排访视。`
4. `未能按期到访时，需调整计划访视日期至访视窗口允许范围内。`

Task:
- Correct only this gap: schedule/window wording that serves as a reschedule
  title or the timing/target constraint of the reschedule action must remain
  reschedule-only.
- Add explicit focused positive tests for all four phrases.
- Add or retain negative tests proving no global reschedule precedence:
  independent schedule obligations must still produce both families, including:
  - `所有计划访视应在时间窗内完成；若无法到访，应重新安排。`
  - `访视窗口为±3天；若不能按期到访，需重新安排。`
  - `所有计划访视应在时间窗内完成，若无法到访应重新安排。`
  - `若受试者入组，计划访视必须在时间窗内完成；若无法到访，应重新安排。`
  - a week/day schedule plus `调整计划访视日期`.
- Preserve pure schedule, pure reschedule, pure unscheduled, schedule +
  unscheduled rejection, and all topic-boundary precedence.
- Do not solve this with unconditional “if reschedule then ignore schedule.”
  Determine whether the schedule/window match is governed by an independent
  schedule assertion or by the reschedule action/title. Normative words such as
  `应` or `需` can govern the reschedule action and therefore cannot by
  themselves prove an independent schedule obligation.
- Keep the change surgical and dependency-free.

Verification:
- Compile the two authorized files.
- Run the direct v8 visit tests and the full
  `tests/test_monitoring_ai_service.py` file.
- Return exact changed paths, hashes, commands/results, failed attempts,
  uncertainty, and Codex-owned recheck targets.
- Do not claim final acceptance, online/canary success, or medical correctness.

Output schema:
1. `# Pi Follow-up Report: monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Changed Files And Hashes`
5. `## Verification`
6. `## Failed Paths And Uncertainty`
7. `## Codex-Owned Recheck`
