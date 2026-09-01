# Task Context: medical_monitoring_r4_d07_runtime_20260813

Created: 2026-08-13 23:09:44
Objective: 在隔离 R4 POC 中实现已冻结的 D07 临床安全性、实验室与检查运行时，覆盖 144 例独立 oracle 验证、中文 Query/Journey 投影、生命周期和相邻回归，不启动服务、不读取真实项目、不触碰医学写作。
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-pro` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`, frozen file SHA-256 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`, semantic SHA-256 `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`.
- `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md` and the accepted 144-case catalog/oracle/registry named there.
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json` is immutable typed input; runtime may consume the typed case payload but must not branch on case/test/fixture identifiers or expected values.
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json` and `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json` are test-side authorities only. Production runtime source must not import or read them.
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/` and `poc/medical_monitoring_ai_native_r4/tests/` are the only implementation/test roots. D01-D06 and R1-R3 are frozen adjacent behavior, not rewrite targets.
- Current filesystem is truth. If a file changes concurrently, re-read and preserve unrelated work.

## Scope

- In scope: new D07 runtime modules under `poc/medical_monitoring_ai_native_r4/src/mm_r4/`; focused D07 tests under the sibling tests directory; minimum root export and README update; deterministic evaluation, pre-evaluator integrity, five L1 dispositions, owner/query/handoff routing, priority, lifecycle binding, three-sentence Chinese Query, renderer-neutral Journey markers/source jumps/audience validation; 144-case raw-runtime/oracle/DSL evaluator; mutation checks; adjacent regressions.
- Allowed support edits: task-owned context/review/metrics/run records and precise cleanup of task-created caches.
- Out of scope: frozen D07 contract/catalog/oracle/registry/generator; semantic changes to D01-D06 or R1-R3; product source; R5 UI; medical-writing subsystem; port 8911 or any service; real project data; D09/D10 aggregation; regulatory reporting; sending Queries; system security design/testing.
- Clinical safety/laboratory/examination logic is in scope. The user's exclusion concerns system-security work, not the D07 clinical domain.

## Success Criteria

- Runtime source has no import/read dependency on oracle, manifest, registry, case numbers, fixture IDs or expected text; test adapters may read frozen validation artifacts.
- All 144 cases execute through runtime and match independent expected leaves through the frozen closed DSL, deterministically and without self-generation.
- Integrity order and first-failure fail-closed behavior precede all medical/priority/risk/Query/Journey outputs.
- Unit/range/grade/baseline/trend/CS-NCS/follow-up/organ-pattern/examination/priority contracts and typed D01/D04/D08 handoffs are implemented without duplicate ownership.
- Chinese audience payloads use concrete medical wording and reject internal labels such as “正式事实”“候选信号”“已记录事项”“通用风险点”.
- Journey output preserves the shared visit/time spine, typed event categories, risk anchors, reversible source jumps and exact scope/hash equality.
- Focused D07, all R4, and frozen R1-R3 adjacent tests pass; Ruff/compile/import/export checks pass; 8911 remains stopped.
- Independent fresh-context verifier accepts the immutable final snapshot with no P0-P4 within this synthetic/offline scope.

## Risk Boundaries

- Do not modify or run product paths, real projects, medical-writing code, or services. Do not start 8911.
- Do not edit frozen contracts or accepted validation artifacts to make runtime tests pass.
- Do not claim product, production, real-project, R4-total or R5-UI acceptance.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Work Decomposition

1. Core runtime: implement closed typed schemas, canonical hashes, integrity pipeline, scope/authority/correction/D05 gates, deterministic medical evaluation and owner/handoff/priority/lifecycle outputs.
2. Independent challenge harness: implement test-only artifact loader, closed DSL evaluator, all-144 exact raw result comparison, deterministic replay and mutation coverage without runtime/oracle reverse dependency.
3. Audience projection and integration: implement Chinese three-part Query, shared-spine Journey events/risk markers/source jumps/audience validators, public exports/README and focused/adjacent regression coverage.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-13 23:09:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
