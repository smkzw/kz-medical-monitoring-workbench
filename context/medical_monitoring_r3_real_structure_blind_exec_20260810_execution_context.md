# Execution Context: medical_monitoring_r3_real_structure_blind_exec_20260810

Created: 2026-08-10 14:20:33
Objective: 在workbench隔离副本上实现并验证五项目XLSX结构盲测工具链，输出不含受试者级原始值的结构画像、映射/身份/归一化质量报告与隐藏挑战结果；不得访问或修改真实项目目录、冻结R1/R2/R3、医学写作子系统或产品源码，8911保持停止。
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

- `context/medical_monitoring_r3_real_structure_blind_20260810_context.md`：任务合同、原始源摘要基线、只读边界和完成标准。
- `runs/medical_monitoring_r3_real_structure_blind_20260810/isolated_inputs/project_a.xlsx` 至 `project_e.xlsx`：Codex 已复制并设为只读的唯一真实数据输入；执行角色不得访问任务合同中列出的外部原始路径。
- `poc/medical_monitoring_ai_native_r3/src/mm_r3/`：已冻结 R3 公开接口，只读复用，严禁修改。
- `poc/medical_monitoring_ai_native_r3/tests/`：已冻结合成回归，只读复用，严禁修改。
- `reviews/medical_monitoring_r3_external_solution_discovery_20260810.md`：当前技术选型记录；本轮无需重新进行网络调研。
- Python：`/Users/smkzw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`；已观察到 `openpyxl 3.1.5`、MIT License。不得安装新包。

唯一授权写入根目录：`runs/medical_monitoring_r3_real_structure_blind_20260810/`。执行角色不得写入 `poc/`、产品源码、医学写作子系统、真实项目目录或其他 `runs/` 目录。

## Risk Boundaries

- 原始项目目录和隔离输入均只读；不得修改、移动、重命名或清理。隔离输入摘要必须保持与任务合同一致。
- 结构提取必须使用 `openpyxl.load_workbook(read_only=True, data_only=True, keep_links=False)` 或证明等价的只读路径，不更新公式缓存、不创建锁文件。
- 内存中允许读取单元格以生成聚合指标；任何落盘 JSON/Markdown/日志/测试夹具不得包含受试者级原始值、姓名、筛选号、中心号或逐行记录。
- 工具和报告只能使用 `project_a` 至 `project_e`；不得将真实项目名、原始路径或专有 Sheet 名硬编码进公共规则。
- 不进行完整医学分析，不输出 AE/MH 漏报、禁用药、入排、PD、疗效或安全性结论。
- 不安装包，不处理凭据，不变更外部账户，不联网上传任何工作簿内容。
- 8911 保持停止；不启动产品、服务、浏览器或 Playwright。
- 缺少环境或接口时，保留失败证据并提出最小修复，不修改冻结 R3。
- Worker/manager 输出仅是 Codex 验收证据。

## Work Items

1. 核验五个只读隔离副本摘要，建立机器可读输入清单与确定性输出摘要，不写出任何受试者级原始值。
2. 实现通用只读XLSX结构提取器并复用R3公开接口生成工作簿/表/字段画像、映射与身份/日期/单位可评估指标。
3. 构造去文件名/项目名线索、隐藏或改写部分表头及相邻非listing Sheet的挑战夹具，执行抗过拟合测试并形成失败分类。

## Authorized Artifact Map

- worker_01 可写：
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/input_manifest.json`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/reports/isolation_verification.json`
- worker_02 可写：
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/tools/xlsx_structure_blind.py`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/tests/test_xlsx_structure_blind.py`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/structural_extracts/*.json`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/reports/structure_quality.json`
- worker_03 可写：
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/challenges/*.json`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/tests/test_hidden_challenges.py`
  - `runs/medical_monitoring_r3_real_structure_blind_20260810/reports/anti_overfit_quality.json`

worker_03 必须在 worker_02 完成并通过定向测试后执行，避免并发覆盖。manager 默认只审阅；若需修订，必须限于上述运行目录并逐项记录。

## Required Output Contract

- JSON 使用 UTF-8、`sort_keys=True`、固定缩进，不包含运行时间戳等非确定性字段；同一输入重复运行文件摘要必须一致。
- 字段名可以输出；`sample_values`、`distinct_values`、逐行记录和任何原始单元格值不得输出。
- 每个比例同时输出 `denominator`、`evaluated`、`not_evaluable` 和原因分布。
- 输出明确区分 `accepted`、`needs_confirmation` 与 `not_evaluable`；候选身份键不得自动宣称已确认。
- 失败是结果：不得加入项目专名、路径或固定 Sheet 名特例使测试变绿。
- 所有测试命令用明确的 `PYTHONPATH=poc/medical_monitoring_ai_native_r3/src`，且不得产生 `.pytest_cache`/`__pycache__`；测试后清理本任务产生的缓存。

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
