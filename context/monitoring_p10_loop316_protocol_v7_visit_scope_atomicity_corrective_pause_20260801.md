# 医学监查 P10 LOOP 3.16 — v7 访视主题边界/原子性纠偏无损暂停

Date: 2026-08-01
State: offline corrective accepted; runtime canary not started

## Goal And Hard Boundaries

- Overall P0-P10 Goal remains active; this checkpoint closes only the offline v7
  corrective slice.
- Candidate decisions remain user-owned. No accept/reject/adopt/confirm/activate.
- v6 is terminal evidence only: no retry, reuse, claim, or prose salvage.
- MY009 and the other real projects remain blocked.
- 8911 and 5174 must remain stopped until a future bounded canary slice is
  deliberately started.
- Medical-writing business source remains untouched.

## Completed

- Active protocol prompt is v7; v3-v6 terminal history remains visible while active
  legacy work fails closed.
- Full topic-boundary and operative-family views are separated.
- Visit medication/dispensing-PK/withdrawal/safety/collection/family precedence is
  deterministic.
- All provider candidates are validated before the single controlled repair with
  candidate-indexed ordered errors; response persistence is atomic.
- Exact C1-C5, C3 8→15 structural closure, blocker order, one-repair and v6
  queued/failed cutover are directly tested.
- Final lexical corrective covers the known medication, timing, withdrawal,
  collection, CMV, unscheduled and reschedule phrases.
- Same Luna review session returned final PASS for the offline gate.

## Final Evidence

- SHA-256:
  - `services/api/app/monitoring_ai_service.py`:
    `d62ff1162794f65cc8894d313d84c5c25c7d043641589608118146de5cb20aba`
  - `services/api/app/monitoring_protocol_preparation_service.py`:
    `1e43424adb7076fd6a7acf17e933833cde2f942dbd8778b5af03e47262ca1798`
  - `tests/test_monitoring_ai_service.py`:
    `7e0fb132f2bfd081e1f860422d563fbdd9594aea3f833b29b61d7c16a2234cb5`
  - `tests/test_monitoring_protocol_preparation.py`:
    `9ad21eb72141f58ced1ce265b98779a851af98b32ac859cdb68c8da59dc0ef1c`
  - `tests/test_monitoring_ai_api.py`:
    `52691a1ec1f6a35cf4359bdea4aad41d50b1fd2f90f4ad80f48f6d35710768a2`
- `py_compile`: passed.
- Focused: `336 passed in 9.51s`.
- Medical-writing adjacent: `200 passed in 2.44s`.
- Full monitoring: `1331 passed, 4299 deselected, 27 warnings, 0 failed in
  615.38s`.
- 8911/5174: no listeners at final check.
- Review:
  `reviews/codex_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_review.md`.
- Independent final recheck:
  `runs/codex-subagent_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_final_recheck.md`.

## Process Notes

- Pi session: `019fb9e0-eb37-7000-98a3-8c186dc03b89`; initial pass plus two
  same-session recoveries, no Pi provider fallback.
- Pi read three supporting implementation files beyond its explicit read-only list.
  No unauthorized write or runtime action was observed; acceptance relies on current
  filesystem, Codex verification and independent final review.
- The full `-k monitoring` regression includes offline tests that read frozen
  RUX/MY009 source shapes. It did not execute a real-project workflow, create
  candidates/jobs, or call a provider.
- Pi's report hashes/test count predate the native Codex lexical fallback and must
  not be used as final-state evidence.

## Residual Observations

- Explicitly inspect future canary output for `研究者无法联系受试者`,
  subjectless/`未能联系受试者`, `临时的访视`, `调整计划访视日期`, and contextual
  false positives from standalone lowercase `cm`.
- These do not block one bounded canary; any material occurrence blocks expansion
  and returns the task to lexical hardening.

## Exact Next Safe Action

On the next user instruction to continue:

1. Re-read current global/workspace AGENTS and this checkpoint; confirm the five
   hashes above and that 8911/5174 are still stopped.
2. Inspect current task/review/ledger state and confirm no unreported local change
   overlaps the five governed files.
3. If the offline review gate still passes, initialize a separate controlled slice
   for exactly one new-ID RUX v7 `visit_window_and_order` canary.
4. Start only the required 8911 service for that slice; do not start 5174. Make one
   POST, never retry/reuse v6, use long hard waits without fixed-interval polling,
   and stop 8911 immediately after terminal evidence is captured.
5. Verify complete indexed diagnostics, exactly one repair, atomic zero-partial
   persistence on failure, scientific/topic correctness, and all residual
   observations above. Reuse the same Luna reviewer for read-only acceptance.
6. Do not proceed to MY009 or other projects without a separate passed gate.

This is a deliberate no-loss pause. No service or long task is left running.
