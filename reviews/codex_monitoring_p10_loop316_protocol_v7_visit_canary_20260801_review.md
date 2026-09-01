# Codex Review: monitoring_p10_loop316_protocol_v7_visit_canary_20260801

Date: 2026-08-01
Delegated-agent output: `runs/codex-subagent_monitoring_p10_loop316_protocol_v7_visit_canary_20260801.md`
Terminal evidence:
`runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`

## Verdict

**FAIL CLOSED.** The runtime safety contract passed, but the functional/scientific
canary gate failed because the deterministic family classifier misclassified a
reschedule rule's necessary trigger context as a second schedule family.

Do not retry/reuse v7, salvage any raw candidate, expand to another topic/project,
or make a candidate decision. The next safe slice is an offline v8
reschedule-trigger-context corrective with a new prompt identity.

## Boundary Check

- One and only one POST created new v7 job
  `monai_d3c770a87e60007b47ad9a105091`; one attempt and one controlled repair
  occurred. No retry, repeat POST, other v7 topic, candidate decision or salvage.
- v4 remained 8 jobs / 8 attempts / 8 proposed candidates; v5 and v6 remained one
  failed attempt and zero candidates each.
- 8911 was started only through `scripts/start_stable_backend.zsh` and gracefully
  stopped immediately after terminal capture. 8911/5174 are stopped.
- The existing native Luna review session was reused read-only. No Hermes external
  dispatch or fallback was used.
- Medical-writing business source and all product source files were unchanged.

## Codex Verification

- Fresh rollback backup:
  `runtime/backups/pre_loop316_protocol_v7_visit_canary_20260801_0638CST/`;
  21 main DB copies, 18 immutable integrity OK, 3 empty byte-preserved.
- Readiness: 200/ready, schema 16, no missing capability; independent product AI
  `alibaba_token_plan/qwen3.8-max-preview`, no Codex runtime dependency.
- Terminal job: failed / `invalid_ai_output`, attempt 1, zero candidates.
- Attempt:
  `monattempt_18b55dba52eb47a69d42fa4e8bba402d`.
- Request SHA:
  `ff942e3b6c5b7d1f4604bd5bfbbab4d007bc916389efdc82eb248ae2292b4d05`;
  162,194 bytes.
- Response SHA:
  `2c5cd6496457db6ac2efba8b5d7705295820b4ac8036a4aecddbd78282477522`;
  14,037 bytes; initial + one repair.
- Initial repair diagnostics were complete, candidate-indexed and ordered. Repair
  removed every listed topic-boundary defect. Only repaired candidate 2 failed.
- Static replay proves candidate 2 matches schedule (`计划访视`, `访视窗`) and
  reschedule (`改期`, `重新安排`), despite having only one operative reschedule
  action.
- Post-canary focused suite: `336 passed in 9.56s`.
- Adjacent medical-writing suite: `200 passed in 2.52s`.

## Delegated-Agent Output Review

- Luna independently confirmed runtime fail-closed, full diagnostic delivery,
  one-repair enforcement and atomic zero persistence.
- All five repaired candidates are scientifically/topic coherent; candidate 2's
  source is a single condition-action reschedule rule.
- The reviewer challenged the opposite interpretation: provider did fail literal
  deterministic acceptability and could paraphrase around regexes. This does not
  make the candidate a real mixed-family clause; requiring lexical evasion would
  weaken source fidelity.
- Current tests cover pure and deliberately mixed families but omit schedule/window
  language used only as a reschedule trigger/object.
- The recommended correction is bounded semantic-role/context handling, not global
  reschedule precedence and not weakening the one-family fail-closed rule.

## Residual Risk

- Candidate 2 exposes a real validator/prompt mismatch; a new prompt identity is
  required before another run.
- `调整计划访视日期` is the same root class and belongs in the next corrective.
- Other prior adjacent phrases did not occur in this response and must not expand
  the next slice.
- No current response candidate may be recovered individually. v7 remains immutable
  terminal evidence. MY009 and other projects remain blocked.
