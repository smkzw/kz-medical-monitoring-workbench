# Codex Execution Plan: medical_monitoring_r3_nl_rule_adapter_exec_20260810

Objective: 在隔离新命名空间实现并验证中文自然语言风险规则到结构化 RuleDraft、确定性 Simulation、三范围建议和用户明确版本 Activation 的模型无关纵切，严格保护冻结 R1/R2/R3、产品、医学写作、真实项目和 8911。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 建立独立包、JSON Schema 2020-12 兼容合同、字段目录和值/操作符严格校验与中文结构化提示合同。 | `runs/execution/medical_monitoring_r3_nl_rule_adapter_exec_20260810/worker_01.md` |
| `worker_02` | 接通冻结 R1 CapabilityAttemptResult 和冻结 R3 RuleDraft/Simulation/Activation 公共合同，实现 partial/truncated/failed 阻断、范围建议和用户明确激活。 | `runs/execution/medical_monitoring_r3_nl_rule_adapter_exec_20260810/worker_02.md` |
| `worker_03` | 构建合成正例、阴性、歧义、未知字段、额外键、非 JSON、多 JSON、截断/partial/failed、陈旧模拟及范围版本反例，运行聚焦与冻结 R3 回归并形成紧凑证据。 | `runs/execution/medical_monitoring_r3_nl_rule_adapter_exec_20260810/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r3_nl_rule_adapter_exec_20260810/manager.md` |

## Codex Acceptance

1. Inspect every changed file under the isolated package and prove no writes outside the authorized execution records/package.
2. Challenge strict JSON, field-catalog binding, type/operator compatibility, R1 terminal/coverage/provenance gates, R3 draft/simulation/activation authority and three scope recommendations.
3. Run task-local and frozen R3 regression tests, verify frozen R1/R2/R3 digests, compile without persistent bytecode, remove task-generated caches and confirm 8911 remains stopped.
4. Obtain a fresh-context independent verifier decision after the implementation stops changing. Worker or manager self-review is not acceptance.
5. Update review, metrics, main R3 context/plan recovery point and archive execution process artifacts only after ACCEPT.
