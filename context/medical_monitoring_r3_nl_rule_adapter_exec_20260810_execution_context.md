# Execution Context: medical_monitoring_r3_nl_rule_adapter_exec_20260810

Created: 2026-08-10 16:21:27
Objective: 在隔离新命名空间实现并验证中文自然语言风险规则到结构化 RuleDraft、确定性 Simulation、三范围建议和用户明确版本 Activation 的模型无关纵切，严格保护冻结 R1/R2/R3、产品、医学写作、真实项目和 8911。
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

- `context/medical_monitoring_r3_nl_rule_adapter_20260810_context.md` — project contract, source authority, success criteria and exact boundaries.
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` — approved R3 behavior and recovery point.
- Read-only frozen public contracts: `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`, `poc/medical_monitoring_ai_native_r1/src/mm_r1/adapters.py`, `poc/medical_monitoring_ai_native_r1/src/mm_r1/__init__.py`, `poc/medical_monitoring_ai_native_r3/src/mm_r3/rules.py`, `poc/medical_monitoring_ai_native_r3/src/mm_r3/__init__.py` and directly relevant tests.
- `reviews/medical_monitoring_r3_nl_rule_adapter_external_discovery_20260810.md` — dependency/standards decision; no new third-party runtime dependency in this slice.
- Frozen anchors before execution: R1 full tree `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`; R2 Python `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`; R3 root-relative Python `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`.

## Risk Boundaries

- Implementation writes only under `poc/medical_monitoring_ai_native_r3_rule_ai/**`; records only in this execution packet. Workers may read frozen R1/R3 but must not modify them.
- Do not read or modify product/application source, medical-writing subsystem, real-project sources or isolated real inputs. Do not start services or listeners; 8911 stays stopped.
- Use synthetic fixtures only. Do not call a real API/model/harness. Do not install packages, handle credentials or make external account changes.
- Do not design or test system security; version/identity/type/status constraints required for medically correct functional behavior remain in scope.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. 建立独立包、JSON Schema 2020-12 兼容合同、字段目录和值/操作符严格校验与中文结构化提示合同。
2. 接通冻结 R1 CapabilityAttemptResult 和冻结 R3 RuleDraft/Simulation/Activation 公共合同，实现 partial/truncated/failed 阻断、范围建议和用户明确激活。
3. 构建合成正例、阴性、歧义、未知字段、额外键、非 JSON、多 JSON、截断/partial/failed、陈旧模拟及范围版本反例，运行聚焦与冻结 R3 回归并形成紧凑证据。

## File And Sequence Contract

1. Run workers serially in order. Worker 01 creates the contract/parser package; worker 02 reads that exact snapshot and adds the R1/R3 workflow bridge; worker 03 reads both and adds challenge tests. No concurrent writes.
2. Target namespace: `poc/medical_monitoring_ai_native_r3_rule_ai/` with `src/mm_r3_rule_ai/`, `tests/` and a short README. File names may be refined, but implementation must remain entirely in this root.
3. Worker 01 owns JSON schema, immutable field catalog, request/response types, strict single-object parser, prompt payload and deterministic hashes. It may create initial tests for its own contracts.
4. Worker 02 owns consumption of public `CapabilityAttemptResult`, parse-status/coverage gates, conversion to frozen R3 `RuleDraft`, local simulation, three fixed scope recommendations and explicit user-confirmed activation. It may minimally adjust Worker 01 exports/contracts and add focused workflow tests.
5. Worker 03 owns adversarial/hidden tests and evidence. It may make only the smallest in-root remediation needed to satisfy the frozen contract, and must list each source change separately from test additions.
6. Required terminal checks: task-local focused/full tests, frozen R3 `339 passed`, in-memory compile or equivalent no-bytecode check, R1/R2/R3 anchor verification, no cache residue, and proof 8911 is not listening.

## Functional Contract

- Accept exactly one JSON object. Markdown fences, prose wrappers, concatenated/multiple JSON values and incomplete JSON are blocking parse failures; do not salvage a substring.
- Reject all undeclared keys at every schema level. Validate scalar/list types without Python bool-as-int ambiguity, finite numeric values, allowed operators, logical combination and field/operator/value compatibility.
- Every condition must bind to one frozen catalog field and preserve a nonempty Chinese source phrase in `extracted_from`. Unknown or invented fields are blocking; no implicit aliasing.
- R1 `complete` plus complete coverage is necessary but not sufficient; `partial`, `truncated`, `failed`, `timeout`, `cancelled`, missing raw provenance or malformed candidate payload cannot yield an R3 draft.
- Model output is candidate-only. Conversion creates `RuleDraft`, never `RuleActivation`. Simulation is local and deterministic. Activation requires user identity, `is_machine=False`, `user_confirmed=True`, nonempty version and one explicit R3 EvaluationScope.
- Scope recommendations are exactly `current_snapshot`, `full_history`, `future_only`, ordered by a deterministic user-facing policy with current snapshot normally first; each has a Chinese title, concise reason and local simulation impact summary. A recommendation is not a selection.
- Public business logic contains no project names, absolute project paths, vendor/model selectors or listing-specific field names.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
