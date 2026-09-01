# Codex Main-Venue Plan: mm_r7_slice08d_implementation_acceptance_20260830

Date: 2026-08-30
Objective: 独立审阅R7 Slice-08D三模式synthetic综合回归实现与当前证据，逐项核对20格、独立oracle、30确定性子进程格、31故障钩子、CAS/重放/迟到回调、公开中文、相邻回归、R6医学写作保护基线纠偏和8911/5174停止；输出P0-P4及ACCEPT/REVISE，不修改文件

## Task Decomposition

1. Compare the frozen v0.1+v0.2 contract with current source, test collection, and Codex evidence.
2. Challenge the 20-cell matrix and confirm case keys do not drive oracle/product decisions.
3. Verify expected computation is stdlib-only and positive authority flags come only from the real verifier path.
4. Verify both 15-cell probes, 31 source-enumerated hooks, real PRAGMA reopen, CAS/replay/late callback and no-half-publication behavior.
5. Review public Chinese/08C non-regression, adjacent suites, R6 protection baseline re-anchor, ports, and medical-writing boundary.
6. Return exact P0-P4 counts and `ACCEPT_R7_SLICE_08D` or `REVISE_R7_SLICE_08D` without editing files.

## Source Packet

- Frozen contract v0.1 + v0.2.
- Current R7 continuity/bridge/registry/setup source and three changed 08D test files.
- R6 medical-writing guard test only.
- Three execution reports and worker evidence manifest.
- Codex combined verification JSON and current filesystem.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r7_slice08d_implementation_acceptance_20260830/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Completed on primary `pi/cms-router/minimax-m3:xhigh` in session `01a05064-95ca-7000-a8a8-6ec9eb578b3a`.
- Duration: 465.393 s. Fallback: none. Failure: none. No follow-up was required.
- The participant independently reran the decisive matrix, determinism, fault, adjacent, R6 guard and port checks and returned `ACCEPT_R7_SLICE_08D`.

## Codex Verification Checklist

- [x] All 20 keys and their minimum assertions are substantive, not a label-only table.
- [x] Oracle/actual are independent and verified booleans are not accepted as authority.
- [x] 30 determinism subprocess cells and 31 current source hooks are evidenced.
- [x] Reopen/busy-timeout/CAS/replay/late-callback/half-publication semantics are closed.
- [x] R6 baseline re-anchor preserves current medical-writing rather than concealing an 08D edit.
- [x] Public Chinese/08C adjacent contracts, compileall, path neutrality and ports are green.
- [x] P0-P4 and final bounded decision are explicit.
