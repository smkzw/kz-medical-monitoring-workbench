# P10 v11 Canary — 无损暂停检查点

Date: 2026-08-01 19:30 CST
State: **current stage evidence-closed; paused by user request**

## Completed In This Stage

- v11 offline corrective accepted after:
  - pycompile;
  - focused `17 passed`;
  - core `528 passed`;
  - adjacent `146 passed`;
  - full monitoring
    `1489 passed, 4455 deselected, 27 warnings in 590.48s`;
  - Luna final static review PASS/P0-P4 none.
- Fresh zero-submit clone accepted:
  - 21 SQLite mains, 18 integrity `ok`, 3 empty;
  - exact v9/v10 historical preservation;
  - zero v11 jobs/active jobs before submission;
  - Luna zero-submit review PASS.
- Exactly one v11 canary POST completed:
  - job `monai_3632c414655546ad250ce8bf7dbd`;
  - attempt `monattempt_564f58bf463c42758a4c394f190be9de`;
  - actual source revision `mpr_40b82826a43e46342344841242e6`;
  - 173 evidence spans;
  - terminal `failed/invalid_ai_output/retryable=0`;
  - two provider outputs, zero persisted candidates, zero active jobs.
- Luna terminal review: evidence PASS; P2 provider controlled-repair
  incompleteness, not a validator defect.

## Exact Failure And Decision

- Initial candidate-1 uncertainty referred to excluded
  `给药和药物分发` and `药物回收和PK采血` contexts.
- Repair removed most excluded wording but retained `药物回收相关段落`.
- The full visit boundary intentionally includes uncertainty and matches
  `回收`; terminal fail-closed behavior is correct.
- Do not weaken the boundary, remove uncertainty from validation, post-process
  the output, or salvage any current candidate.

## Frozen Artifacts

- Terminal evidence:
  `runs/execution/monitoring_p10_v11_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- Canary context:
  `context/monitoring_p10_v11_isolated_canary_20260801_context.md`
- Canary review:
  `reviews/codex_monitoring_p10_v11_isolated_canary_20260801_review.md`
- Canary metrics:
  `metrics/monitoring_p10_v11_isolated_canary_20260801_metrics.md`
- Zero-submit evidence:
  `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
- LOOP record:
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
  entries 3.20–3.21.

## Hard Pause Boundaries

- 8911 and 5174 must remain stopped.
- PID 43191/18911 remains an unrelated runtime and must not be touched.
- v9, v10 and v11 jobs must not be retried, reused, salvaged, reclassified or
  used for candidate decisions.
- Do not run a second topic/project or the three real projects.
- Do not migrate the isolated database into authoritative runtime.

## Next Safe Action

Start a new offline v12 corrective only after re-anchoring this checkpoint and
the current filesystem:

1. Add precise field-path and matched-token feedback for excluded boundary
   hits, for example
   `candidate[0].claims[2].uncertainty -> 回收`.
2. Require provider repair to regenerate the affected user-visible field;
   do not silently delete text after generation.
3. Add exact initial/repair regressions for uncertainty fields and preserve all
   existing boundary rules.
4. Run focused, adjacent and full monitoring regression plus independent
   Codex/Luna review.
5. Only after separate authorization, build a brand-new clone and repeat
   zero-submit before any future single canary.

No v12 implementation or runtime action has started.
