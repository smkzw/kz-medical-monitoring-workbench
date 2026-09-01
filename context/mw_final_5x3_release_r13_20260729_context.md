# Medical Writing Final 5x3 - release-r13-20260729

## Purpose

Run a completely fresh A1 lazy-medical-writer acceptance after the r12
pre-tester runtime-readiness failure was repaired.

## Governing Boundary

- r12 remains immutable and failed before any tester or product project.
- The comprehensive-AI role binding is the runtime source of truth.
- Legacy `active_profile_id` is a compatibility fallback only when no valid
  role binding exists.
- No product source may change while the r13 tester is active.
- The tester must use the real visible desktop UI. Hidden API mutation,
  skeleton prefill, corpus override, fabricated AI output, and tester-authored
  protocol prose cannot count as acceptance.

## Active Scope

- Slot/perspective: `A1/lazy_medical_writer`
- Tester: Codex subAgent `gpt-5.6-luna-high`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield
- Emphasis: AI-first lazy-writer flow, four AI role settings, truthful granular
  progress, competitor discovery and document preparation, complete protocol,
  DOCX/PDF export, and native Word inspection unless a material blocker is
  frozen first.

## Accepted Repair Evidence

- `tests/test_ai_runtime_settings.py`
- `tests/test_ai_role_runtime_settings.py`
- `tests/test_frontend_ai_role_settings_contract.py`
- `tests/test_contracts.py`
- Focused result: `48 passed`
- Python compilation: passed

## Loop Log

- 2026-07-29: created after r12 processes were proven stopped and the
  role-vs-active-profile conflict was reproduced.
- 2026-07-29 03:50 Beijing: matrix and harness validation passed (`69 passed`);
  r13 was prepared with input fingerprint
  `99b73c930a61b60b6045110989e53947add01a27e007fb55598eae28fc274342`.
- 2026-07-29 03:51 Beijing: isolated runtime started on backend `56438` and
  frontend `56439`. Runtime readiness is `ready`; project count is zero; all
  four role bindings are runnable; workload gate reports OCR 8, translation 8,
  total 16.
- 2026-07-29: A1 tester subAgent `019faa47-9602-7543-a3c6-1e60cdc8a601`
  (`gpt-5.6-luna`, high) was dispatched for the real visible-browser flow.
  Product source is frozen until it completes or freezes a material blocker.
- 2026-07-29 04:06 Beijing: the tester froze the run as `BLOCKED` after the
  visible competitor triage remained at `4/19` and `594/665` for about three
  minutes. The tester did not reach source preparation or any later protocol
  authoring/export gate.
- 2026-07-29 04:08 Beijing: Codex stopped the isolated runtime only after the
  tester returned. The shutdown path requeued the durable research-pipeline and
  competitor-triage jobs.
- Post-run database inspection disproved a triage deadlock. The first Qwen
  independent-AI chunk completed and was durably persisted before shutdown:
  the business run reached `5/19`; the durable triage job reached
  `已确定性处理594项；AI分诊批次 1/15`; five chunks were `succeeded` and fourteen
  AI chunks remained `pending`; neither durable job recorded a provider error.
- The r13 A1 result is therefore classified as an **invalid early blocker**,
  not a product pipeline failure. A single external Qwen chunk took materially
  longer than the tester's observation window.
- A real product observation remains open for batch repair after the serial
  tester wave: while a provider request is in flight, the visible UI stays at
  the last completed chunk and does not say which AI batch is currently
  running. The overall percent must remain factual, but the UI should surface
  the active batch and elapsed state from durable progress rather than looking
  frozen.

## Next Safe Action

Keep r13 immutable. Prepare a new clean r14 round with identical product source
and rerun A1 from zero. The tester must not classify a slow external-AI call as
stuck unless a terminal job/provider failure is visible, the parent pipeline's
900-second wait expires, the lease is lost, or no durable progress/timestamp
changes for at least 20 minutes. Product source remains frozen until the
serial tester wave is complete; the in-flight progress presentation issue is
queued for the later batch repair.
