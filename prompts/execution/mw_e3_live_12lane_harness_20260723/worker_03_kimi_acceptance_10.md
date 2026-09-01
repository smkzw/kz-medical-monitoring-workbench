You are the next fallback execution worker because the user-mandated existing QoderVIP
session is occupied by an unrelated task and Kimi Code `k3` failed health preflight
without creating a session. Use Reasonix `deepseek-v4-flash`. Read
`/Users/smkzw/.codex/AGENTS.md`, the closest project
`AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`, and current files before editing.

Goal: repair the two remaining false-evidence defects in W3 without redoing accepted
work.

Read first:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_fresh_completion_09.md`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_behavior_helpers.mjs`
- `frontend/tests/final_release_12lane_behavior_acceptance_09.mjs`
- `frontend/tests/final_release_12lane_behavior_pydantic_acceptance_09.py`

The list is starting context, not a tool prohibition.

Hard boundaries:
- Allowed writes: the W3 files above plus a replacement
  `frontend/tests/final_release_12lane_behavior_acceptance_10.mjs` and focused
  backend parser/route tests if genuinely needed.
- Do not edit W1, W2, W4, fixtures, protocols, credentials, source inputs, stable
  runtime state or unrelated production code.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_reasonix_acceptance_10.md`.
  Return the report in final text; never write that file.

Observed residual defects:

1. `runResumableStages` and `CRASH_BOUNDARIES` are imported only by
   `behavior_acceptance_09.mjs`; `child.mjs` does not import or call the driver.
   Therefore the eight "crash/resume" tests exercise a parallel test workflow, not
   the executable child orchestration. Refactor the child's actual stages to use one
   exported stage driver, or extract the child's current stage orchestration into a
   shared driver invoked by both child and tests. Preserve actual pipeline calls,
   durable checkpoints, locators, receipts, source identity and all included-chapter
   traversal. Do not replace the real child flow with a simplified mock sequence.
2. Acceptance_09's first two import/call-graph tests read source text and use
   `includes(...)`. Source-string presence cannot prove runtime wiring. Replace them
   with behavioral instrumentation: dependency injection, exported call counters,
   or another runtime-observable mechanism showing the real child/shared
   orchestration calls the exact helpers/builders. Test-only counters must not alter
   product behavior and must reset deterministically.

Required acceptance:
- Add a runtime-controlled fault injection at each exact boundary:
  project creation, competitor search, preparation, translation, candidate
  generation, pre-adoption, post-adoption and post-evidence.
- Invoke the same stage engine used by `child.mjs`; persist checkpoint/locator state,
  instantiate a fresh client/engine, resume, and prove completed POSTs do not refire.
- Post-adoption and post-evidence must prove adoption/evidence commit occurs exactly
  once, not merely that a test counter increments.
- Keep the accepted independent export hash, real HTTP same-key adoption replay,
  evidence transaction and exact JS-builder-to-Pydantic checks.
- Acceptance_10 is the sole W3 count. Await every case and count each exactly once.
  Exclude acceptance_06/07/09 and all source-string tests.
- Red mode must fail behaviorally without source editing; green must pass.

Run syntax checks, acceptance_10 red/green, exact Pydantic tests and focused backend
route/parser tests. Report changed files, actual runtime call evidence, exact
commands/counts, eight boundary POST/commit outcomes and residual uncertainty.

End exactly:
`WORKER_03_REASONIX_ACCEPTANCE_10_COMPLETE`
