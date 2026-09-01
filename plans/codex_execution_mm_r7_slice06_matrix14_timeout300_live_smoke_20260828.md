# Codex Execution Plan: mm_r7_slice06_matrix14_timeout300_live_smoke_20260828

Objective: Run a new governed matrix-14 synthetic live-smoke after the accepted R7 bridge repair, using the existing R7 run-level timeout override to freeze MTPLX Qwen3.8 medium at 300 seconds with zero fallback and unchanged R1/R6 sources. Preserve all prior failures. Execute strictly serially: verify the profile override and fresh driver first, then one authentic MTPLX call, then only after Codex accepts an MTPLX PASS execute explicit DeepSeek V4 Flash max. No real project, service, browser, product write, or medical-writing change.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Read-only verify that a run-level timeout_seconds=300 override can be persisted and frozen through the current R7 profile-store/run-binding path while preserving exact MTPLX selector, medium effort, empty fallback chain and unchanged R1/R6 bytes; provide the precise driver recipe and assertions, no model call or file modification. | `runs/execution/mm_r7_slice06_matrix14_timeout300_live_smoke_20260828/worker_01.md` |
| `worker_02` | Only after Codex confirms worker01, use a fresh /tmp workspace and the complete RunEntry to RuntimeProgress to BackgroundRecovery to HarnessCapabilityRuntime to real OmpPrintAdapter chain for exactly one MTPLX medium synthetic unit with a frozen 300-second run timeout and no fallback. Wait long enough for the built-in single linked retry window, preserve terminal receipts, and do not rerun or substitute on failure. | `runs/execution/mm_r7_slice06_matrix14_timeout300_live_smoke_20260828/worker_02.md` |
| `worker_03` | Only after Codex accepts the MTPLX leg as PASS, use a separate fresh /tmp workspace and the same complete chain for exactly one explicit DeepSeek V4 Flash max synthetic unit, no fallback. Return terminal receipt and hashes; otherwise remain pending. | `runs/execution/mm_r7_slice06_matrix14_timeout300_live_smoke_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

### Serial gate status

- `worker_01`: accepted. The run-level override freezes `timeout_seconds=300`
  with the exact MTPLX selector, `medium` effort and an empty fallback chain.
- `worker_02`: accepted by Codex from the underlying frozen binding and runtime
  SQLite, not from the worker narrative alone. The successful workspace is
  `/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mm_r7_matrix14_4spl13_m`;
  the path named in the worker's artifact list was an earlier no-op workspace.
  The accepted run has one terminal `complete` attempt, control `finished`, work
  unit `passed`, exact synthetic coverage, `fallback_used=false`, and a real
  adapter duration of 156.852 seconds under the frozen 300-second timeout.
- `worker_03`: released only after the preceding independent acceptance. It may
  run one explicit DeepSeek V4 Flash max synthetic unit with no fallback.
  Completed and independently accepted: one terminal attempt, 16.461-second
  real adapter duration, exact synthetic coverage and `fallback_used=false`.

No real project, product service, browser, frontend or medical-writing source
was opened or changed. Ports 8911 and 5174 remain stopped.

Matrix-14's bounded live-smoke work items are complete. Remaining closure work
is the guard review/audit, durable receipt update and phase checkpoint.
