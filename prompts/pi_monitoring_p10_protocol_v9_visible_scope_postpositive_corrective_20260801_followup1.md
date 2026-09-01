# Pi Same-Session Follow-up: v9 postpositive modal-role correction

Continue the existing Pi session `019fbaf4-a806-7000-95e6-a3e88e33e3e3`. Read the complete current `/Users/smkzw/.hermes/SOUL.md` before acting. This is one consolidated same-session corrective round, not a new broad exploration.

Read these files only:

- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`

Runner-managed output path: `runs/pi_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_followup1.md`.
Never write or edit that report path; return the complete handoff in your final response so the runner can persist it.

## Accepted scope

Edit only:

- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`

Do not edit prompt identity, legacy/cutover service, API tests, task records, frontend, medical-writing files, runtime databases, or any real-project material. Do not start services/workers/providers or ports 8911/5174. Do not run a real canary. Preserve all current filesystem changes.

Current accepted pre-follow-up hashes:

- `services/api/app/monitoring_ai_service.py`: `0ba6e317ece66f00248c4ae4ae9bac524b3c7bb75ea01abd5882f6b92201a501`
- `tests/test_monitoring_ai_service.py`: `5d38e5a80a96fc6c15bb1f5f370357295c42290e910ccf630b88e9405b39d42c`

Stop and report instead of editing if either hash differs.

Hard boundaries:

- Do not read or edit files beyond the explicit read/edit lists above.
- Do not start services, workers, provider calls, ports 8911/5174, or a real canary.
- Do not access real RUX, MY009, or other project data.
- Do not make candidate acceptance/rejection/adoption/activation decisions.
- Do not overwrite unrelated changes or create any file except through the two authorized edits.

## Reproduced acceptance defect

The current v9 classifier incorrectly returns `["reschedule", "schedule"]` for:

- `计划访视无法在窗口内完成时必须改期。`
- `计划访视无法在窗口内完成时应重新安排。`

The normative token governs the reschedule action, not the earlier schedule predicate `完成`. These must be `["reschedule"]`. This follows the task contract: a modal governing a reschedule action is not an independent schedule assertion.

Make the smallest semantic-role correction. Do not add a broad negation exemption or weaken fail-closed behavior.

## Required guardrails

These must remain mixed:

- `计划访视无法在窗口内完成时必须按原顺序执行；应改期。`
- `计划访视无法在窗口内完成时仍需完成本次计划访视；应改期。`
- `计划访视无法在窗口内完成时，访视窗口仍为±3天；应改期。`
- existing week/day, ordering, quantified, numeric-window, and independent normative schedule cases.

These must remain reschedule-only:

- `计划访视无法在窗口内完成时的改期安排`
- `计划访视无法在窗口内完成时必须改期。`
- `计划访视无法在窗口内完成时应重新安排。`

Update the new v9 tests so they encode this distinction; moving the two modal-reschedule cases out of the mixed guardrail set is required, not test weakening. Add direct coverage for both reschedule-only modal cases and the two independent normative mixed cases above.

Run:

- compile the edited implementation file;
- `python3 -m pytest -q tests/test_monitoring_ai_service.py`;
- a direct classifier matrix for all six phrases above.

Return a compact execution handoff with sources read, exact changes, commands/results, final hashes, residual risk, and next recommended action. Do not write the runner-owned output file.
