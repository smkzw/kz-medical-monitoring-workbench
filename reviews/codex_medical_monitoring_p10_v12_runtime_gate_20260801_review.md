# Codex Review: medical_monitoring_p10_v12_runtime_gate_20260801

Date: 2026-08-01 22:54 CST  
Review mode: Codex direct; no delegated agent or conference; Hermes route not used

## Verdict

**PASS for the A6 zero-submit gate and the one bounded RUX canary.** This is
runtime evidence for v12, not a commercial-release approval.

## Boundary Check

- All runtime writes stayed under
  `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/`.
- The source v11 clone was opened read-only for SQLite backup and remained
  hash-stable for all 21 source mains.
- 8911 was the only task-owned listener; 5174 was never started; PID 43191 on
  18911 was untouched.
- v9-v11 history was not retried, reused, salvaged, reclassified or decided.
- No browser/UI run, three-project run, authority migration or candidate
  adoption occurred.

## Codex Verification

### Zero-submit

- New clone: 21 SQLite mains, 18 `integrity=ok`, 3 source-empty, 0 foreign-key
  violations.
- Only health, runtime-readiness and RUX protocol status GETs were made before
  the canary; no POST/provider call occurred in the zero-submit phase.
- Protocol v12 jobs/attempts/candidates remained `0/0/0`; active jobs `0`.
- Attempts and candidates were byte/row invariant; v9-v11 frozen job rows were
  unchanged after excluding only the three retirement fields.
- 8911 was stopped immediately after the assertions.

### Canary

- Exactly one POST, RUX `visit_window_and_order`, returned `202`.
- Job `monai_343e98b4992acc36e0c60da30e98` used prompt v12, provider
  `alibaba_token_plan`, model `qwen3.8-max-preview`, source revision
  `mpr_40b82826a43e46342344841242e6`, and 173 evidence entries.
- Terminal: `completed`, one attempt, `success_repaired`, two provider outputs,
  three proposed candidates, zero active jobs.
- Initial output had exact boundary hits at
  `candidates[0].claims[1].uncertainty` (`回收`, `PK`) and
  `candidates[2].claims[1].user_action` (`安全性随访`); repaired output had zero
  hits across the full governed boundary.
- Candidate review found source locators and explicit uncertainties for partial
  visit windows, rescheduling and safety-driven unscheduled visits. No
  candidate was adopted.
- 8911 was stopped immediately after terminal observation.

## Source and product review

- v12 source/test hashes still match the offline checkpoint.
- The live result exercises the repaired contract on the actual product AI; it
  does not replace deterministic unit/core/adjacent/full regressions, which
  remain the acceptance evidence for validator scope.
- Candidate content is proposed only. A medical manager must confirm the full
  §1.2 flow table and operating procedures before any rule adoption.
- The response stores both provider outputs and candidates; the exact repair
  envelope is covered by offline tests, while the runtime artifact proves the
  observed initial-to-repaired transition.

## Residual Risk

- One successful RUX topic does not establish three-project generality,
  browser usability, restart recovery, performance, or release readiness.
- The source protocol evidence packet itself records a retrieval gap for the
  complete §1.2 flow table; the candidate uncertainty correctly preserves that
  gap and must not be converted into a deterministic rule without review.
- Full monitoring selector remains collection-blocked by the unrelated
  medical-writing private-symbol import; the accepted monitoring selector used
  only that known module exclusion.
- Phase B shared risk authority, concise project/site/subject UI and the
  Profile/Timeline/AE risk integration contract remain unimplemented work.
