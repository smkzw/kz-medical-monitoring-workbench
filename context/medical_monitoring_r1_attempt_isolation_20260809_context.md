# Task Context: medical_monitoring_r1_attempt_isolation_20260809

Created: 2026-08-09 19:05:59
Objective: 为隔离R1实现可明确强制的合成harness执行边界与跨进程attempt journal、重启/迟到回调恢复；不得触碰产品、医学写作、服务、共享运行库或真实项目
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §9 and §12.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R1 steps 6/8.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` and `domain.py`.
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`.
- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- SQLite transactions/isolation/WAL: https://www.sqlite.org/lang_transaction.html,
  https://www.sqlite.org/isolation.html, https://www.sqlite.org/wal.html.
- Apple App Sandbox/inheritance/XPC guidance:
  https://developer.apple.com/documentation/security/app-sandbox and
  https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html.
- External candidate scan: `anthropic-experimental/sandbox-runtime` (research preview,
  macOS Seatbelt/Linux bubblewrap) and Apple `container` (macOS 26+, additional runtime).

## Scope

- In scope: application-owned SQLite attempt journal; immutable request identity; atomic claim;
  bounded lease; terminal result replay; expired-run recovery; stale/late completion rejection;
  restart/resume with a new attempt identity; synthetic harness process-envelope enforcement.
- Allowed writes: only isolated R1 POC source/tests/docs and this task's context/review/metrics.
- Out of scope: product source, medical writing, shared runtime/package/dependency changes,
  service/8911, credentials, real providers/harnesses, five real projects and product migration.
- No new sandbox dependency is adopted. `sandbox-exec` is present on the current macOS 26.5.1
  host but is deprecated and not promoted to an accepted product contract in this slice.

## Success Criteria

1. The same attempt ID and frozen request cannot be executed concurrently across two SQLite
   connections; conflicting identity fails closed.
2. A terminal result is immutable and can be replayed after reopening the database without
   dispatching transport again.
3. An expired running lease becomes `interrupted`; its late completion is rejected and audited.
4. Resume creates a new attempt with the same profile/input/version/manifest identity and an
   explicit `continued_from`; the interrupted history is preserved.
5. Harness receives only the frozen allowlisted environment, explicit argv, JSON stdin and fixed
   working directory; these are tested as enforced process-envelope properties, not claimed as
   general filesystem/network/tool sandboxing.
6. Focused and full R1 tests pass; candidate-only authority and protected subsystem boundaries
   remain unchanged.

## Risk Boundaries

- Do not write outside the allowed isolated paths above.
- The journal may contain full request input only because this POC Store rejects non-synthetic
  projects; real-data migration requires an approved encrypted/content-addressed reference design.
- A crashed/expired attempt is never re-executed under the same attempt ID; recovery requires a
  new attempt linked by `continued_from`.
- Environment/CWD/argv restrictions are not sufficient to claim OS-level filesystem, network or
  internal harness tool isolation. That remains OPEN until an eligible sandbox/XPC/container route
  is separately selected and verified.
- Independent fresh-context review owns acceptance; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 19:05:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09: Local/external scan compared current subprocess envelope, Apple App Sandbox/XPC,
  deprecated Seatbelt-based wrappers, research-preview `sandbox-runtime`, and Apple Container.
  Selected no new dependency: implement durable SQLite attempt semantics now and retain OS-level
  sandboxing as an explicit residual rather than making a false isolation claim.
- 2026-08-09: Implemented application-owned `capability_attempt_journal` with immutable request
  identity, `BEGIN IMMEDIATE` declaration/claim, bounded leases, terminal result replay, expired
  recovery, stale completion rejection and explicit new-attempt resume via `continued_from`.
- 2026-08-09: Added fixed harness process-envelope checks for explicit argv, `shell=False`,
  nonempty absolute existing cwd, frozen environment allowlist and JSON stdin/stdout. This does
  not claim OS-level filesystem/network/tool isolation.
- 2026-08-09: Fresh-context reviewer issued four actionable VETOs and the implementation was
  repaired in place: expired same-owner redispatch/late commit; resume preflight order and cwd;
  row-vs-request identity cross-checks; same-runtime cache bypass; and terminal status not being
  bound to the immutable result hash.
- 2026-08-09: Final frozen hashes: `capability_runtime.py`
  `296b95a29707ec6aeb091eabf7365bcc3cbb09a06b9b0afe7db336f6d6c9d6d1`, `store.py`
  `e8dc5d285c3578a8225887fcbfd64e01fb18fc5113072697a78287c9da352dbd`, and
  `test_capability_runtime.py`
  `499390a7aefe49084d5d96477602345f2b09b49d82dd594fcc0f63bf091be321`.
- 2026-08-09: Final writable-root verification: capability focused `44 passed`; isolated R1 core
  `147 passed`. The same persistent Luna reviewer session
  `019fe63e-92d5-7f40-8c6b-93799569db8c` independently reran both suites, reproduced corruption
  fail-closed, and returned `ACCEPT` for this isolated slice only.
- 2026-08-09: Protected boundaries held: no product source, medical-writing source, 8911/service,
  real endpoint/provider, credential or real project was accessed or changed. OS sandboxing,
  real process/subprocess-tree checkpoint recovery and raw artifact read-time integrity remain OPEN.
