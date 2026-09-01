# Task Context: medical_monitoring_r4_d08_runtime_20260814

Created: 2026-08-14 16:23:51
Objective: 依据已接受D08 v0.6合同与冻结oracle，在R4 POC内实现synthetic/offline多表医学逻辑runtime、exact projection和定向/相邻回归；保持8911停止且不运行真实项目或触碰医学写作
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `cms-smk` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/medical_monitoring_r4_d08_contract_final_acceptance_20260814.md`.
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`, exact SHA-256 `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`.
- Frozen D08 catalog/oracle/registry and `tests/test_d08_artifact_generator.py`; they are read-only acceptance inputs, never runtime dependencies.
- Accepted D07 runtime modules/tests are engineering patterns only. D08 semantics come solely from the frozen D08 contract and oracle.
- Current filesystem is authoritative; this workbench is not a Git repository, so preserve before/after hashes and explicit file lists.

## Scope

- In scope: a deterministic stdlib-only synthetic/offline D08 runtime in `poc/medical_monitoring_ai_native_r4`, typed validation, exact evaluator output, fixture adapter, renderer-neutral Query/Journey projection, mutation/replay/challenge tests, root exports and adjacent isolated regressions.
- Out of scope: D09/D10, R5/UI/product integration, services/8911, real projects/patient data/models/providers, medical-writing, system-security design/testing, package installation and production writes.

## Success Criteria

- Runtime never imports/reads catalog, oracle, registry, generator, tests or case/fixture/oracle/manifest/test IDs; it branches only on typed clinical facts and frozen contract semantics.
- All 233 catalog typed inputs evaluate to exact oracle leaf sets and audience projections through a test-only adapter; integrity failures stop before medical/risk/Query/Journey output.
- Owner routing, cutoff priority, temporal direction, identity/duplicate, reverse cardinality, waiver covered-zero versus uncovered, n-ary RELID, propagation/correction, visibility and fanout gates match v0.6.
- D08-owned positive units produce risk and a Chinese three-part Query draft (`依据` + `发现` + `行动项`); PD wording remains outside D08 ownership. Query/Journey/source jumps expose only projectable evidence and preserve source traceability.
- Deterministic replay, order/surface anti-overfit, all declared mutation classes and stale-hash/oracle-coupling controls pass; no hard-coded case IDs or expected leaf payloads in runtime.
- Focused D08 tests, full R4 and R1-R3 regression, Ruff/compile pass; 8911 remains stopped. Independent fresh-context verifier owns final runtime acceptance.

## Risk Boundaries

- Allowed writes only under `poc/medical_monitoring_ai_native_r4/src/mm_r4/` for new D08 modules and root exports, `poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py`, plus runner-owned task records.
- Do not modify accepted D01-D07 implementations/tests, frozen D08 contract/catalog/oracle/registry/generator/test, product/frontend/service paths or medical-writing.
- No runtime dependency on acceptance artifacts. Test code may read frozen artifacts and adapt typed input.
- The delegated worker is not final authority; Codex reproduces tests and a fresh verifier decides acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-14 16:23:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-14: Codex replaced the generic template with the exact D08 runtime contract before dispatch. External discovery was not repeated because the accepted v0.6 contract already records the current architecture decision and this step is a faithful isolated implementation, not a new dependency or architecture choice.
- 2026-08-14: Pi/CMS-SMK worker session `019fff62-1955-7000-8e3e-09cbac6f32cd` completed implementation and two same-session remediation passes; worker recovery passes were then exhausted.
- 2026-08-14: Independent Luna session `019fff98-9f85-7ec2-ba80-63be3ef6ab1e` retained four successive REVISE decisions while finding additional fail-open, ordering, identity, projection and propagation defects. Codex reproduced and repaired only those bounded defects.
- 2026-08-14: Luna follow-up 4 returned `ACCEPT_D08_RUNTIME`; final gates were D08 `186 passed`, R4 `3843 passed`, R1-R3 `1264 passed`, generator `54 passed`, Ruff/compile pass and TCP 8911 stopped. Final authority record: `context/medical_monitoring_r4_d08_runtime_final_acceptance_20260814.md`.
