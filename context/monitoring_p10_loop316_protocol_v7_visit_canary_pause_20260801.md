# P10 LOOP 3.16 v7 Visit Canary 无损暂停

Date: 2026-08-01
State: canary failed closed; v8 offline corrective required

## Current Gate

- v7 canary functional/scientific gate: **NO-GO**.
- Runtime safety contract passed: one job, one attempt, one controlled repair,
  complete indexed diagnostics, zero partial persistence.
- v7 job and response are immutable terminal evidence. No retry, reuse, claim or
  candidate salvage.
- Candidate decisions remain user-owned.
- MY009 and every other real project remain blocked.
- 8911 and 5174 must remain stopped.

## Runtime Evidence

- Job: `monai_d3c770a87e60007b47ad9a105091`
- Attempt: `monattempt_18b55dba52eb47a69d42fa4e8bba402d`
- Prompt: `monitoring-protocol-clause-structuring-v7`
- Source revision: `mpr_40b82826a43e46342344841242e6`
- Terminal: failed / `invalid_ai_output`
- Provider outputs: initial + one repair
- Candidates persisted: 0
- Request SHA:
  `ff942e3b6c5b7d1f4604bd5bfbbab4d007bc916389efdc82eb248ae2292b4d05`
- Response SHA:
  `2c5cd6496457db6ac2efba8b5d7705295820b4ac8036a4aecddbd78282477522`
- Backup:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v7_visit_canary_20260801_0638CST/`
- 8911/5174: zero listeners.

## Root Cause

- Initial response had four indexed problem candidates; the single repair addressed
  all of them.
- Four repaired candidates are deterministic-valid and scientifically coherent.
- Repaired candidate 2 `计划访视改期原则` is semantically one reschedule rule:
  unable to attend within the existing window → reschedule → stay close to original
  visit date.
- Current classifier counts `计划访视/访视窗` in the title/trigger condition as a
  second schedule family in addition to `改期/重新安排`.
- Splitting or deleting the necessary trigger condition would damage source fidelity.
  The defect is role/context-insensitive family counting.

## Verification

- Focused monitoring: `336 passed in 9.56s`.
- Adjacent medical-writing: `200 passed in 2.52s`.
- Independent review:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v7_visit_canary_20260801.md`.
- Terminal extract:
  `runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`.
- Codex review:
  `reviews/codex_monitoring_p10_loop316_protocol_v7_visit_canary_20260801_review.md`.

## Exact Next Safe Action

On the next Goal continuation:

1. Re-read latest global/project AGENTS and this checkpoint; confirm 8911/5174
   remain stopped, v4-v7 job/attempt/candidate counts are unchanged, and the five
   v7 implementation/test hashes have no unreported overlap.
2. Initialize a new offline task, suggested ID:
   `monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801`.
3. Keep writable product scope limited to the protocol prompt/classifier and direct
   tests required for:
   - reschedule title/object language (`计划访视改期原则`);
   - schedule/window inside `若/如果/无法/未能` trigger clauses;
   - exact current candidate 2 as reschedule-only positive;
   - a true independent schedule assertion + reschedule action as mixed negative;
   - `调整计划访视日期` and its combination with an independent week schedule.
4. Do not implement global reschedule precedence. Preserve boundary precedence,
   one-family fail-closed, candidate-indexed aggregation, one repair and atomic
   persistence.
5. Because provider-visible semantics change, use a new prompt identity v8 and add
   v7 to terminal history; never retry/reuse current v7.
6. Run focused, full monitoring and adjacent medical-writing regressions, then
   independent read-only review. Do not start 8911/5174 or a new canary during the
   offline corrective.

This is a deliberate no-loss pause. No service, worker, provider call, subtask or
long-running process is left active.
