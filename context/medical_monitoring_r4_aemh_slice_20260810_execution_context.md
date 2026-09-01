# Execution Context: medical_monitoring_r4_aemh_slice_20260810

Created: 2026-08-10 20:50:54
Objective: 在新隔离 R4 包中实现冻结共同 coverage primitives 与 AE/MH 首条纵向核查，含 R2 生命周期、Query/医学旅程投影和合成确定性测试，保护产品、医学写作、真实项目与冻结 R1-R3，8911 保持停止
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3_256k` -> `pi` / `cms-smk` / `cms-model`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` (`FROZEN_R4_CONTRACT_V1`, SHA-256 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`).
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`, especially §§5, 9-11 and 16-17.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, R4 only.
- Frozen read-only contracts:
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`, `ae_mh.py`, `projections.py` and focused AE/MH tests, used only to understand the prior slice and avoid inheriting its fixed table/window/lifecycle simplifications.
  - `poc/medical_monitoring_ai_native_r2/src/mm_r2/identity.py`, `risk.py`, `acceptance.py` and focused tests. R2 `RiskLifecycle` is the sole L3 authority.
  - `poc/medical_monitoring_ai_native_r3/src/mm_r3/mapping.py`, `normalization.py`, `primitives.py` and focused tests. R3 partial-date normalization and semantic mapping are reused read-only.
- Official medical references are already recorded and adjudicated in the frozen matrix. No new web research is required for this slice unless an implementation decision would change.

## Allowed Output And Ownership

Create only `poc/medical_monitoring_ai_native_r4/**` plus guard-owned task records. Do not modify frozen R1-R3.

| Role | Owned implementation files | Owned tests |
|---|---|---|
| worker_01 | `src/mm_r4/contracts.py`, `src/mm_r4/coverage.py`, initial `src/mm_r4/__init__.py`, `README.md` sections for the common contract | `tests/conftest.py`, `tests/test_coverage_contract.py` |
| worker_02 | `src/mm_r4/aemh.py`, `src/mm_r4/projection.py`; append only its own README section if needed | `tests/test_aemh_slice.py` |
| worker_03 | `src/mm_r4/lifecycle.py`, `src/mm_r4/fixtures.py`; no edits to worker_01/02 files unless a failing public contract makes a minimal integration patch necessary and it is recorded | `tests/test_lifecycle_projection.py`, `tests/test_challenge_matrix.py` |
| manager | May make bounded integration corrections anywhere inside `poc/medical_monitoring_ai_native_r4/**` after reviewing all worker outputs | May add/update only R4 tests needed to prove integration |

Workers execute serially in numeric order. A later worker must use the current filesystem and must not undo an earlier verified artifact. Runner-owned reports/logs are not worker-editable.

## Frozen Implementation Contract

1. The R4 package is stdlib-only and imports frozen R2/R3 public APIs read-only; it must not copy or fork their lifecycle/normalization authority.
2. L0 execution coverage, exclusive L1 disposition, multi-valued L1b evidence polarity, L2 objects and R2-owned L3 lifecycle are separate types/fields and separate counts.
3. `EvaluationUnit.unit_id` and `expected_set_hash` are deterministic canonical hashes over the exact dimensions frozen in the matrix. Every expected unit receives exactly one L1 disposition.
4. The ledger must fail closed on duplicate/missing/unexpected units, invalid evidence joins, false complete coverage, or candidate/source-record/risk/Query count contamination.
5. AE/MH input is semantic-role driven. Minimum roles are `reported_ae`, `reported_mh`, subject/site identity and temporal anchor, with optional symptom, CM indication, lab, examination, encounter, procedure, IP action, seriousness, death and visit roles. No source table name is hardcoded.
6. The event-match strategy and protocol reporting boundary are explicit versioned inputs. No inherited fixed 30-day rule or project-specific threshold may exist in common code.
7. Partial dates use frozen R3 normalization and preserve raw value, normalized value, precision and uncertainty. Incomparable dates become L1 boundary/not-evaluable, never silently imputed exact dates.
8. Event intensity, seriousness criteria/SAE-AESI flags and monitoring priority are separate. Only monitoring priority projects to R2 `RiskInstance.severity`; clinical flags project separately.
9. A model/AI assertion, if represented, remains a traceable evidence assertion or candidate. It never becomes a reported source fact or established risk without deterministic verification and R2 adjudication.
10. Query projection has `basis + finding + action`, links source/EvaluationUnit/candidate or risk, and never means sent. Journey/Profile/Timeline output is projection data only: visit/temporal anchors, distinct AE/MH/CM/IP/etc. event categories, risk marker, source links and uncertainty.
11. R2 lifecycle integration must use public `RiskLifecycle`, `RiskCandidate`, `AdjudicationEvidenceBinding`, `AdjudicationOutcome` and real public `AcceptanceService` fixtures. Low/medium machine close requires a subsequent accepted full snapshot and rejected-by-evidence adjudication; high priority/SAE/AESI/user-confirmed risks must not machine-close.
12. Tests are synthetic/offline and must separately count source records, evaluation units, evidence items, candidates, established risks and Query drafts.

## Risk Boundaries

- No product/runtime, medical-writing, real-project or frozen R1-R3 writes.
- No package installation, credential handling, network/provider calls or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Port 8911 must remain stopped. Do not start any service.
- Do not design or test system security.
- Do not run the five real projects or use their files as fixtures.

## Work Items

1. 实现 R4 EvaluationUnit、L0/L1/L1b/L2/L3 分层、expected-set 与 join 不变量公共合同
2. 实现结构驱动的 AE/MH 多来源线索、反证、时间边界、医学分级与 Query/旅程投影纵切
3. 构建正向、负向、边界、不可评价、误报/漏报、增量生命周期合成夹具与聚焦/相邻回归

## Success Criteria

- R4 package imports cleanly with only stdlib plus frozen R2/R3 local source paths.
- Deterministic unit/expected-set hashes are input-order independent and change when any identity/lineage/version dimension changes.
- Coverage completeness is impossible when L0 has partial/truncated/failed/missing, L1 has not-evaluable, expected-set/join invariants fail, or required provenance is absent.
- AE/MH synthetic cases cover reported matches, suspected AE/MH under-reporting, NCS/confirmed alternative diagnosis, protocol boundary, partial-date ambiguity, seriousness clues, CM/lab/exam/encounter/procedure/IP evidence, and no fixed table names.
- Query and journey projections use Chinese-native audience labels but keep stable engineering codes internally.
- N→N+1 tests cover persistence, close-by-data mapping, high-risk carry-forward, reopen, identity ambiguity and supersession using R2 public lifecycle behavior.
- `pytest -q -p no:cacheprovider poc/medical_monitoring_ai_native_r4/tests` passes; Ruff/compile pass if available without installation.
- Focused adjacent R2 risk and R3 normalization/mapping tests pass with all source digests unchanged.
- Final independent review accepts a stable R4 snapshot; 8911 has no listener.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
