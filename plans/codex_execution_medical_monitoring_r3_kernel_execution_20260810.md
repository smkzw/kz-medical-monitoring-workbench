# Codex Execution Plan: medical_monitoring_r3_kernel_execution_20260810

Objective: 在独立 poc/medical_monitoring_ai_native_r3 命名空间实现 R3 Study Intelligence 与异构 listing 合成数据基座，并以确定性测试证明来源权威、冲突、结构画像、mapping、identity、规范化、diff 与自然语言规则生命周期；不得修改 R1/R2、产品、医学写作、真实项目或启动 8911。

## Work Items

| 顺序 | Worker | Assigned item | Authorized implementation files | Report |
|---|---|---|---|---|
| 1 | `worker_01` | R3-A：资料分类、版本/有效时间/范围、Knowledge Pack、claim authority、source conflict/resolution | scaffold；`knowledge.py`、`fixtures.py`、A tests | `runs/execution/medical_monitoring_r3_kernel_execution_20260810/worker_01.md` |
| 2 | `worker_02` | R3-B：workbook/table/field 画像、mapping 候选/置信度/依赖/确认、identity、日期/单位/编码/缺失语义 | `listing.py`、`mapping.py`、`identity.py`、`normalization.py`、B tests | `runs/execution/medical_monitoring_r3_kernel_execution_20260810/worker_02.md` |
| 3 | `worker_03` | R3-C：snapshot diff/影响传播、自然语言规则草稿/模拟/激活/scope、三结构隐藏挑战 | `snapshot_diff.py`、`rules.py`、C tests | `runs/execution/medical_monitoring_r3_kernel_execution_20260810/worker_03.md` |

Workers are dispatched sequentially. Every slice must leave all preceding R3 tests green before the next starts.

Current state: all three worker reports exist. Codex completed bounded remediation of functional contract defects discovered during source review; the independent baseline is 330 R3 tests passing. Execution-manager consolidation and fresh-context acceptance remain pending and own the next disposition.

## Standards And Environment

- Reference concepts: CDISC ODM/Define-XML/Dataset-JSON, SDTM general observation classes, DDF/USDM; no conformance claim.
- Runtime: Python standard library plus already available pytest. No package installation or external service.
- Source authority and detailed boundaries are in `context/medical_monitoring_r3_kernel_execution_20260810_execution_context.md`.

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r3_kernel_execution_20260810/manager.md` |

## Codex Acceptance

1. Inspect all diffs/current files and every worker/manager report.
2. Re-run focused and full R3 tests with caches disabled; compile all R3 Python sources in memory.
3. Verify hidden anti-overfitting cases, explicit uncertainty, no silent conflict/mapping/rule activation, and no project path/name hardcoding.
4. Verify R1/R2 frozen digests unchanged, no cache directories, no 8911 listener, and no out-of-bound writes.
5. Obtain fresh-context independent engineering/medical acceptance before freezing the R3 slice; no synthetic result may be described as real-project completion.
