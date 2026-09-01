# Medical Writing Final 5x3 - release-r14-20260729

## Purpose

Repeat the clean A1 lazy-medical-writer acceptance after r13 was invalidated as
an early slow-call misclassification.

## Governing Boundary

- r13 remains immutable and does not count as PASS or a confirmed pipeline
  blocker.
- Product source is identical to r13 and must remain frozen while this tester
  is active.
- The tester uses the real visible desktop UI and product-owned independent AI.
- Hidden API mutation, skeleton prefill, corpus override, fabricated AI output,
  and tester-authored protocol prose cannot count as acceptance.
- A healthy but slow external model call is not a blocker. The tester must wait
  at least 20 minutes without durable progress before considering a no-progress
  finding, unless a terminal provider/job error, lease loss, or the
  parent-pipeline 900-second timeout appears first.

## Active Scope

- Slot/perspective: `A1/lazy_medical_writer`
- Tester: Codex subAgent `gpt-5.6-luna-high`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield
- Emphasis: AI-first lazy-writer flow, four AI role settings, truthful granular
  progress, competitor discovery and document preparation, complete protocol,
  DOCX/PDF export, and native Word inspection unless a material blocker is
  frozen first.

## Preparation Evidence

- Schedule:
  `runs/execution/mw_final_5x3_harness_20260728/plans/release-r14-20260729-schedule.json`
- Input fingerprint:
  `0c222b371e36dcf16104b39e978ac943f7c230d20fcdb16755c7d87f5594305e`
- Matrix validation: passed
- Product source drift gate: passed
- Prepared slot count: 15
- Prepared perspective count: 30

## Open Observation Deferred To Batch Repair

The progress UI does not currently expose the active external-AI batch during a
long in-flight request. Keep the completed percent factual; after all serial
tester evidence returns, consider adding an active-batch and elapsed-state
projection from durable progress.

## Next Safe Action

Start the isolated A1 runtime, verify zero product projects and all four
independent-AI roles, dispatch one fresh Luna-high subAgent, and wait sparsely.

## Loop Log

- 2026-07-29 04:14 Beijing: r14 preparation completed with input fingerprint
  `0c222b371e36dcf16104b39e978ac943f7c230d20fcdb16755c7d87f5594305e`.
- 2026-07-29 04:15 Beijing: isolated runtime started on backend `49391` and
  frontend `49392`; runtime identity
  `09418add9ad7a8792ccd60bf836927e61e627b153155e1ad8e152677196a953a`.
  Health and clean-state checks passed, project count was zero, and all four AI
  role bindings were runnable.
- 2026-07-29: A1 tester subAgent
  `019faa5d-ec93-7bc3-80da-0992a96e1bcc` (`gpt-5.6-luna`, high) was dispatched
  with the corrected long-wait blocker criteria. Product source is frozen until
  it reaches a terminal result.
- 2026-07-29 04:18 Beijing: Codex rechecked the isolated r14 runtime. Backend
  `49391` and frontend `49392` are still running; the A1 runtime project count
  is zero and no durable business job has been created yet. This is consistent
  with tester setup/input work and is not evidence of a product failure. Do not
  stop the run or modify product source on this signal.
- 2026-07-29 04:28 Beijing: The real headed browser created the clean A1
  project through the UI with only drug, indication and phase. Product search
  fixed 665 public studies and 138 Protocol/SAP sources. The first Qwen
  triage call was allowed to run for the long-wait window; durable progress
  advanced from 4/19 to 9/19 and then 11/19 while AI batches advanced to 8/15.
- 2026-07-29 04:51 Beijing: A1 was frozen at the first material blocker. The
  parent research pipeline recorded `error_summary=分诊超时` at its 900-second
  limit and the UI displayed `研究流水线失败` with parent `100%`, while the
  child competitor-triage job remained `running` at AI batch 8/15. This is a
  real parent/child lifecycle and progress-projection defect, not an early
  slow-call misclassification. Evidence is in the A1 slot directory:
  `BLOCKED.md`, `COMPLETION_STATUS.json`, `DEFECTS.md`,
  `BROWSER_ACTION_TRACE.json`, `pipeline_lineage.json`,
  `service_evidence/database_at_blocker.txt`, and the original-resolution
  screenshot. No product or test source was modified; services remain running.
