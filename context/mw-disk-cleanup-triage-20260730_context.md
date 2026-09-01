# Task Context: mw-disk-cleanup-triage-20260730

Created: 2026-07-30 11:01:32
Objective: 只读分诊医学经理工作台 runs/ 中可安全再生或明确作废的缓存/过程文件，保留任务记录和 r42 恢复资产，输出清理建议报告，不执行清理
Task type: `unknown`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench root: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- Read-only target: `runs/`, especially `runs/execution/mw_final_5x3_harness_20260728/rounds/`
- Primary evidence: each A1 round's `COMPLETION_*`, `BLOCKED.md`, `DEFECTS.md`, `FIX_RETEST_LEDGER.md`, `HANDOFF.md`/`A1_HANDOFF.md`, screenshots, source receipts, and clean-state inventory.
- Deliverable: `context/mw_disk_cleanup_triage_20260730.md`
- Browser profiles were intentionally not opened; no credentials or secrets were read.

## Scope

- In scope: read-only size and reference triage for r11/r15/r20/r38/r39/r40/r42 and their largest A1 runtime subdirectories.
- Out of scope: all deletion, moving, compression, mutation, service restart, browser interaction, and secret/session inspection.

## Success Criteria

- Report contains exact paths, observed sizes, use/reference state, KEEP/ARCHIVE/DELETE_REGENERABLE recommendation, estimated release, pre-delete verification, rollback, and regeneration paths.
- r42 recovery assets and status/test/source evidence are explicitly protected.
- No cleanup operation is executed.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 11:01:32: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: Read-only scan completed; report written. Old-six-round `writing_reference_artifacts` deletion candidate is approximately 6.99GiB; r42 remains KEEP. No deletion/move/compression executed.
