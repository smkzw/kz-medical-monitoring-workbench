# Codex Execution Plan: medical_monitoring_r3_real_structure_blind_exec_20260810

Objective: 在workbench隔离副本上实现并验证五项目XLSX结构盲测工具链，输出不含受试者级原始值的结构画像、映射/身份/归一化质量报告与隐藏挑战结果；不得访问或修改真实项目目录、冻结R1/R2/R3、医学写作子系统或产品源码，8911保持停止。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 核验五个只读隔离副本摘要，建立机器可读输入清单与确定性输出摘要，不写出任何受试者级原始值。 | `runs/execution/medical_monitoring_r3_real_structure_blind_exec_20260810/worker_01.md` |
| `worker_02` | 实现通用只读XLSX结构提取器并复用R3公开接口生成工作簿/表/字段画像、映射与身份/日期/单位可评估指标。 | `runs/execution/medical_monitoring_r3_real_structure_blind_exec_20260810/worker_02.md` |
| `worker_03` | 构造去文件名/项目名线索、隐藏或改写部分表头及相邻非listing Sheet的挑战夹具，执行抗过拟合测试并形成失败分类。 | `runs/execution/medical_monitoring_r3_real_structure_blind_exec_20260810/worker_03.md` |

## Sequence And Ownership

1. Codex 已完成五项目候选选择、源摘要基线、隔离复制和只读权限设置。
2. worker_01 只创建输入清单与隔离校验，不读取单元格内容。
3. worker_02 在隔离副本上实现通用读取器、结构画像和聚合质量度量；不得修改冻结 R3。
4. Codex 运行定向测试并确认 worker_02 产物不含原始值后，才启动 worker_03。
5. worker_03 用合成/结构化挑战验证表头缺失、表头改写、相邻非 listing Sheet 和去文件名线索；不得复制真实行到夹具。
6. manager 审阅三份报告、工具、测试、输出契约和失败分类；需要修复时给出同会话精确返工指令。
7. Codex 复跑定向测试与完整 R3 回归、复核输出摘要、扫描硬编码/数据泄露、复核源摘要和 8911 状态，最后决定 ACCEPT/REJECT。

## Tool And Environment

- Python：`/Users/smkzw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`。
- XLSX 解析：现有 `openpyxl 3.1.5`（MIT），严格只读、`data_only=True`、`keep_links=False`；不安装依赖。
- R3 公开接口：`profile_workbook/profile_table`、`map_table`、`IdentityAlgorithm/resolve_rows`、`normalize_value`；只读复用。
- 测试：`python -m pytest -q -p no:cacheprovider`，显式设置 `PYTHONPATH`；禁止网络、服务和浏览器。

## Acceptance Checks

- 五份隔离副本摘要与任务合同一致，且源文件任务前后摘要不变。
- 五个工作簿均产生确定性画像；至少三类异构结构被明确识别。
- 聚合报告没有受试者级值；字段名、表名和聚合计数是允许的结构证据。
- 映射/身份/日期/单位指标包含分母、不可评估数和原因；身份键保持需确认。
- 隐藏挑战同时度量遗漏和误纳入，且失败不被项目特例覆盖。
- `rg` 扫描公共规则无真实项目名、外部路径、`project_a` 至 `project_e` 或专有 Sheet 名硬编码。
- 本阶段定向测试、完整 R3 339+ 回归通过；任务目录无缓存。
- R1/R2/R3 冻结摘要、医学写作边界和 8911 停止状态保持不变。

## Stop Conditions

- 任一写入越出授权根目录；任一源或隔离输入摘要变化；受试者级原始值进入落盘产物；8911 被启动；冻结 R3 被修改。
- 发生上述情况立即停止并 REJECT，不进行“顺手修复”。

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r3_real_structure_blind_exec_20260810/manager.md` |

## Codex Acceptance

Codex 负责核对实际文件、测试、摘要、源边界、数据最小化、硬编码扫描和 8911 状态。worker 与 manager 不拥有完成权；本阶段不涉及渲染界面、临床风险结论或产品迁移。
