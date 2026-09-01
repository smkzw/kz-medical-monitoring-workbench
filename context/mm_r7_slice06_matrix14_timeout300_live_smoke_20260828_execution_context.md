# Execution Context: mm_r7_slice06_matrix14_timeout300_live_smoke_20260828

Created: 2026-08-28 18:11:20
Objective: Run a new governed matrix-14 synthetic live-smoke after the accepted R7 bridge repair, using the existing R7 run-level timeout override to freeze MTPLX Qwen3.8 medium at 300 seconds with zero fallback and unchanged R1/R6 sources. Preserve all prior failures. Execute strictly serially: verify the profile override and fresh driver first, then one authentic MTPLX call, then only after Codex accepts an MTPLX PASS execute explicit DeepSeek V4 Flash max. No real project, service, browser, product write, or medical-writing change.
Task type: `low_risk_critique_smoke_test`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `lowrisk_critique_executor_cms` -> `codebuddy` / `codebuddy-cli` / `hy3-x`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. Read-only verify that a run-level timeout_seconds=300 override can be persisted and frozen through the current R7 profile-store/run-binding path while preserving exact MTPLX selector, medium effort, empty fallback chain and unchanged R1/R6 bytes; provide the precise driver recipe and assertions, no model call or file modification.
2. Only after Codex confirms worker01, use a fresh /tmp workspace and the complete RunEntry to RuntimeProgress to BackgroundRecovery to HarnessCapabilityRuntime to real OmpPrintAdapter chain for exactly one MTPLX medium synthetic unit with a frozen 300-second run timeout and no fallback. Wait long enough for the built-in single linked retry window, preserve terminal receipts, and do not rerun or substitute on failure.
3. Only after Codex accepts the MTPLX leg as PASS, use a separate fresh /tmp workspace and the same complete chain for exactly one explicit DeepSeek V4 Flash max synthetic unit, no fallback. Return terminal receipt and hashes; otherwise remain pending.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
# Codex MTPLX acceptance checkpoint

The MTPLX serial leg is accepted from direct SQLite and frozen-binding
inspection. The successful fresh workspace is
`/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mm_r7_matrix14_4spl13_m`.
It contains one terminal attempt only:
`r7-capability:matrix14-mtplx-run:1:ai-1:attempt-1`, status `complete`, control
`finished`, work unit `passed`, and no linked retry. The raw R6 receipt records
`state=complete`, `parse_state=parsed`, `analysis_complete=true`, exit code 0,
`fallback_used=false`, exact coverage of `subject:SYN-MATRIX14-001`, mapped
invocation `r7_9a1aababc709935a59ed1229968a07b1`, profile digest
`86f744ca7b8b9800d75761ac82849e584d46d6791fb41529eba3b708f0aad058`,
and 156.852 seconds duration under the frozen 300-second timeout.

The worker report's initially listed workspace ending in `w23e14ng` is not the
successful run; it is an earlier no-op driver attempt and must not be cited as
completion evidence. The corrected success path above is authoritative.

Source hashes remain unchanged from the accepted repair checkpoint. No active
OMP process was found, and ports 8911/5174 returned `connect_ex=61`.

## Next safe action

The DeepSeek leg has now run exactly once and passed Codex's direct SQLite and
binding inspection. Its workspace is
`/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mm_r7_matrix14_ds_csqz_ebu`.
The single attempt is terminal `complete`; control is `finished`; the work unit
is `passed`; the raw receipt is parsed and complete with exact synthetic
coverage and `fallback_used=false`. The frozen profile is explicit
`deepseek/deepseek-v4-flash`, effort `max`, timeout 300 seconds and no fallback.

Next run the execution review-gate and audit, update the Slice-06 durable
receipt/stage record, then archive only the governed process packet. Preserve
all prior failed-run evidence and do not delete either successful SQLite
workspace until the durable evidence record is closed.
