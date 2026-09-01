# Medical Writing Final 5x3 - release-r15-20260729

## Purpose

Run a completely new A1 lazy-medical-writer acceptance after repairing the
r14 parent/child triage wait contradiction.

## Frozen Boundary

- Round: `release-r15-20260729`
- Slot/perspective: `A1/lazy_medical_writer`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield
- Tester: Codex subAgent `gpt-5.6-luna`, reasoning `high`
- Input fingerprint:
  `661ecca2fce5f4beb1521852ce7f16376aa7db270c0e478f59e16d6d893e3db4`
- r14 is immutable defect evidence and cannot be reused.
- No corpus override, skeleton prefill, hidden API mutation, tester-authored
  protocol prose or historical project data can count.
- Product source is frozen while the visible tester is active.

## Repair Evidence

- `context/mw-r15-triage-liveness-repair_context.md`
- `reviews/codex_mw-r15-triage-liveness-repair_review.md`
- 391 unique targeted tests passed.

## Product AI Contract

- Comprehensive AI: `alibaba_token_plan/qwen3.8-max-preview`
- OCR AI: `omlx/GLM-OCR-bf16`
- Translation AI:
  `omlx/dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`
- Translation-support LLM: `deepseek/deepseek-v4-flash`

The tester model is not the product AI and may not substitute for any of these
stages.

## Long-Wait Adjudication

- Progress beyond 900 seconds is healthy when completed triage chunks continue
  advancing.
- A blocker requires a terminal provider/job error, the 1200-second monotonic
  business-stall condition, the 7200-second absolute ceiling, or another
  reproducible material product failure.
- Sparse polling is required; do not infer a blocker from an in-flight model
  call without durable evidence.

## Loop Log

- 2026-07-29 05:36 Beijing: r15 preparation created 15 slots / 30
  perspectives with all frozen source receipts matching.
- 2026-07-29 05:39 Beijing: isolated runtime started on backend `56570` and
  frontend `56571`; runtime identity
  `032bdbb11023309868bc98cb3f8b727909b95ecfeb0160b35118601d2443d103`.
  API health, zero project count and both process identities passed.
- 2026-07-29 05:40 Beijing: all four product AI roles reported
  `current_runnable=true`: Qwen 3.8 comprehensive AI, GLM-OCR, Hy-MT2 body
  translation and DeepSeek V4 Flash translation support. The shared oMLX gate
  reported OCR 8 / translation 8 / total 16 with no active or queued leases.
- 2026-07-29: A fresh A1 tester subAgent
  `019faaa9-af71-7fb1-9e4f-140f71840209` (`gpt-5.6-luna`, high) was dispatched
  for the real visible-browser run. Product source is frozen until terminal
  tester evidence returns.
- 2026-07-29: A1 completed 665-study discovery, 19/19 competitor-triage
  chunks, one batch lock/confirmation, and preparation of 70 public
  Protocol/SAP documents. It then reached the first material blocker:
  `references/workspace` did not return within 120 seconds, so the 11
  structure-admission exceptions could not be displayed or batch-reviewed.
  The tester wrote `BLOCKED.md`; r15 remains failed and has no `PASS.md`.
- 2026-07-29: Codex stopped the isolated runtime after evidence freeze.
  Profiling a copy of the real database isolated the timeout to
  `WritingReferenceRepository.source_span_counts()`: 56,691 source spans were
  joined to the latest extraction per artifact without the required composite
  indexes. All other workspace components were fast.
- 2026-07-29: schema v7 added additive latest-extraction and
  artifact/revision span indexes. A copy of the frozen v6 database migrated in
  0.47 seconds; complete workspace assembly took 0.029 seconds and the actual
  FastAPI response (1.68 MB) returned HTTP 200 in 0.082 seconds. A combined
  1,029-test regression suite passed.

## Next Safe Action

Complete the read-only delta review, wait for the concurrent monitoring writer
to release shared `main.py` and `App.jsx`, refresh their authoritative hashes,
validate the harness, then prepare a new clean round and rerun A1 from zero.
Do not reuse the r15 project or its corpus state.
