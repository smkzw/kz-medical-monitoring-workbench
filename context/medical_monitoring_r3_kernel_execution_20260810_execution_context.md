# Execution Context: medical_monitoring_r3_kernel_execution_20260810

Created: 2026-08-10 12:42:36
Objective: 在独立 poc/medical_monitoring_ai_native_r3 命名空间实现 R3 Study Intelligence 与异构 listing 合成数据基座，并以确定性测试证明来源权威、冲突、结构画像、mapping、identity、规范化、diff 与自然语言规则生命周期；不得修改 R1/R2、产品、医学写作、真实项目或启动 8911。
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

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，重点 §§2-8、15-20。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，重点 R3（§7）。
- `context/medical_monitoring_r3_study_intelligence_20260810_context.md`。
- `reviews/medical_monitoring_r3_external_solution_discovery_20260810.md`。
- `reviews/codex_execution_medical_monitoring_r2_batch_c_independent_accept_20260810.md` 与冻结的 `poc/medical_monitoring_ai_native_r2/README.md`、`src/mm_r2/domain.py`、`schema_registry.py`、`identity.py`、`diff.py`，只读用于上游合同兼容。
- 用户当前修订：中文原生、风险/变化/来源优先；前台禁止工程/日志标签；本阶段不做额外系统安全设计或安全测试。

## Risk Boundaries

- The only implementation write root is `poc/medical_monitoring_ai_native_r3/**`.
- This execution may update only its own `context/`, `plans/`, `prompts/`, `runs/`, `reviews/`, `metrics/` task records; runner-owned reports are written only by the runner.
- R1/R2 POCs, product/application source, medical-writing subsystem, real-project directories and all source documents are read-only; workers must not traverse real-project paths.
- Do not start a service or listener. Port 8911 remains stopped.
- Do not install packages. Use Python standard library and existing pytest only.
- Do not implement access control, encryption, attack resistance, penetration checks, or other system-security work. Functional study/snapshot/source/identity integrity remains in scope.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. R3-A：实现资料分类、来源版本/有效时间/范围、Knowledge Pack、claim authority 与 source conflict/resolution 合同及 fixtures/tests。
2. R3-B：实现 workbook/table/field 结构画像、语义 mapping 候选/置信度/依赖/少量确认、稳定 record identity、日期/单位/编码/部分日期/重复/缺失语义及 fixtures/tests。
3. R3-C：实现 snapshot diff 与临床影响传播、自然语言规则草稿/模拟/版本化激活/evaluation scope、三结构隐藏反过拟合挑战及集成 tests。

## File Ownership And Sequence

- Workers run **sequentially**, not in parallel, because later contracts depend on earlier package types.
- `worker_01` owns initial package scaffold plus `src/mm_r3/knowledge.py`, `src/mm_r3/fixtures.py`, `tests/conftest.py`, `tests/test_r3_a_knowledge.py`, and may create the initial `README.md`/`src/mm_r3/__init__.py`.
- `worker_02` may read all worker_01 artifacts and owns `src/mm_r3/listing.py`, `mapping.py`, `identity.py`, `normalization.py`, `tests/test_r3_b_*.py`; it may only append coherent public exports/documentation to `__init__.py`/`README.md`.
- `worker_03` may read all prior R3 artifacts and owns `src/mm_r3/snapshot_diff.py`, `rules.py`, `tests/test_r3_c_*.py`, hidden challenge fixtures/tests; it may only append coherent exports/documentation to `__init__.py`/`README.md`.
- No worker may overwrite a prior worker's implementation merely to simplify its own slice. If a shared-contract defect blocks work, report it with a minimal patch proposal for Codex or manager review.

## Acceptance Checks

- Each worker runs its focused tests with `PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider` and then all currently existing R3 tests.
- Domain objects are immutable/value-oriented where practical; every derived result retains source locator/raw value or source revision lineage and explicit uncertainty.
- Low-confidence/conflicting mapping is never silently accepted; source conflict is never silently overwritten; natural-language rules cannot become active without explicit versioned activation.
- Record identity is stable under row/column ordering and display-only changes, but does not collapse genuinely distinct records or ambiguous partial identities.
- At least three synthetic listing structures plus hidden renamed/reordered cases prove no project-name/path hardcoding.
- Manager inspects every worker report and runs the full R3 suite. Codex independently repeats decisive tests, compiles sources in memory, compares frozen R1/R2 digests, checks caches and confirms 8911 has no listener.

## Stop Conditions

- Stop a worker on an attempted out-of-bound write, need to read a real project, need to install a dependency, or a material shared-contract conflict; report the exact blocker rather than broadening scope.
- Slow execution is not failure. Each route receives the runner hard wait up to 120 minutes and same-session recovery before fallback.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
