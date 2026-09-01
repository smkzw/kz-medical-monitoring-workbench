# Codex Execution Plan: medical_monitoring_r4_aemh_slice_20260810

Objective: 在新隔离 R4 包中实现冻结共同 coverage primitives 与 AE/MH 首条纵向核查，含 R2 生命周期、Query/医学旅程投影和合成确定性测试，保护产品、医学写作、真实项目与冻结 R1-R3，8911 保持停止

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 R4 EvaluationUnit、L0/L1/L1b/L2/L3 分层、expected-set 与 join 不变量公共合同 | `runs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_01.md` |
| `worker_02` | 实现结构驱动的 AE/MH 多来源线索、反证、时间边界、医学分级与 Query/旅程投影纵切 | `runs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_02.md` |
| `worker_03` | 构建正向、负向、边界、不可评价、误报/漏报、增量生命周期合成夹具与聚焦/相邻回归 | `runs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_03.md` |

Workers run serially: worker_01 common contract → worker_02 AE/MH/projection → worker_03 lifecycle/challenge fixtures → manager integration review. File ownership and acceptance are defined in the execution context.

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_aemh_slice_20260810/manager.md` |

## Codex Acceptance

- [ ] Common coverage contract and hashes satisfy the frozen matrix.
- [ ] AE/MH semantic-role slice has no fixed table names, project thresholds or 30-day match rule.
- [ ] R2 lifecycle and R3 partial-date APIs are reused without modifying/forking them.
- [ ] Query and journey projection payloads are source-linked, Chinese-native and not mislabeled as R5 UI acceptance.
- [ ] Focused R4 plus adjacent R2/R3 regression, Ruff and compile checks pass.
- [ ] Independent reviewer accepts the stable digest.
- [ ] No out-of-scope file changed and 8911 remains stopped.
