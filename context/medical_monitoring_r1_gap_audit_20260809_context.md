# Task Context: medical_monitoring_r1_gap_audit_20260809

Created: 2026-08-09 18:38:27
Objective: 审计隔离R1当前API/harness adapter、三模式、报告覆盖、打包与耐久性实现，选择并实施下一最小闭环；继续保护产品、医学写作、8911、共享运行库和真实项目
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/`
- `poc/medical_monitoring_ai_native_r1/tests/`
- `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`
- `poc/medical_monitoring_ai_native_r1/docs/R1_EVIDENCE.md`
- Entry baseline: R1 core `103 passed`; AE/MH audience `18 passed`; Patient Journey `16 passed`.
- Current deterministic evidence after this slice: R1 core `128 passed` (including 25 capability-runtime tests); audience/browser suites remain 18 and 16 from their accepted slices.
- External design checks: Python `subprocess` documentation, JSON-RPC 2.0 specification, OpenAI Responses lifecycle reference and OWASP command-injection guidance; these inform the transport boundary but do not become runtime dependencies.

## Scope

- In scope: audit what already exists for API/harness adapters, three ModeContracts, report ClaimCoverageLedger, progress, packaging and durability; record exact open gaps; choose the next smallest coherent R1 slice.
- Authorized implementation path after audit: only `poc/medical_monitoring_ai_native_r1/` source/tests/docs plus this task's context/review/metrics.
- Out of scope: product source, medical-writing, shared runtime/package changes, services/8911, credentials, provider calls, five real projects and product integration.

## Success Criteria

1. Distinguish implemented/tested contracts from aspirational matrix rows.
2. Select the next slice from the real filesystem, not the stale recovery summary.
3. Any implementation remains provider/model neutral and takes the user's configured profile as frozen input.
4. API and harness paths share one request/result schema; harness execution never uses a shell and API transport remains injectable/offline-testable.
5. Raw output, request identity, profile fingerprint, input/version fingerprint, timeout/error/partial/truncated and coverage states are explicit and fail closed.
6. New deterministic tests plus the expanded core suite pass; no protected subsystem is touched.

## Risk Boundaries

- Writes are limited to the isolated R1 POC and this task's durable records.
- Do not install packages, invoke a real provider/harness, start a service, read a real project or change the shared `.venv`.
- Do not store credential values; a future profile may carry only an opaque credential reference.
- The adapter remains candidate-only and cannot promote facts, accept snapshots, confirm users or publish.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 18:38:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09: Filesystem audit found three immutable ModeContracts and report ClaimCoverageLedger already implemented/tested. `adapters.py` contains only `ScriptedAdapter`; `docs/R1_ADAPTER_FAILURE_MATRIX.md` correctly leaves real API/harness transport scenarios OPEN.
- 2026-08-09: Bounded external check supports a transport-neutral JSON request/response identity, explicit correlation/error objects, `subprocess` argument arrays with `shell=False`, timeouts and allowlisted executable/profile configuration.
- 2026-08-09: Selected next slice: provider-neutral AI Capability Runtime with one common envelope, injected API transport and explicit-argv harness transport, all validated with synthetic/offline fixtures.
- 2026-08-09: Implemented `ExecutionProfile`, shared JSON-RPC-shaped request/result identity, injected API transport, explicit-argv `shell=False` harness, mandatory manifest revision reader, pre/post revision checks, candidate-only raw-first persistence and exact coverage reconciliation.
- 2026-08-09: Independent verifier VETO 1 identified fail-open coverage, optional manifest/recovery checks, API timeout/cancel gaps, nonterminal deadlock, raw truncation/persistence order, identity and sensitive-argument weaknesses. These were repaired and regression-tested.
- 2026-08-09: Independent verifier VETO 2 reproduced a denominator-classification gap that could turn `not_evaluable` into complete/publishable. Expected coverage is now restricted to unique scope/key units with no status/reason and `expected=true`; rejection occurs before transport.
- 2026-08-09: Independent verifier third pass ACCEPTED only the isolated capability-runtime slice at frozen source/test hashes. Focused tests were `25 passed`; expanded R1 core was `128 passed`. After acceptance, only a behavior-neutral persistence-order docstring was corrected; final commands are rerun during task closeout.
- 2026-08-09: R1 remains incomplete. Open work includes real tool/context isolation, cross-process attempt journal/restart/checkpoint/late-callback recovery, raw corruption-on-read, complete crash atomicity, real endpoint/fallback/keychain integration, ensemble/adjudication, and token/cost semantics.
- Next safe action: implement the smallest synthetic/offline execution-isolation plus durable-attempt-recovery slice without touching product, medical writing, 8911, shared runtime or real projects.
