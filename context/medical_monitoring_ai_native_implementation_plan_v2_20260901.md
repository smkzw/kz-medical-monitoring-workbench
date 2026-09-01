# 医学监查 AI 原生实施计划 v2.0

**日期**：2026-09-01
**状态**：`USER_APPROVED_EXECUTION_PLAN`
**替代关系**：本计划替代 `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（v1.1）作为执行指令。v1.1 及其"当前实施进度"条目转为历史档案，其中已接受的 R1–R7 工程资产是本计划的迁移来源。
**设计权威**：《System Design v1.1》＋ `reviews/medical_monitoring_ai_native_system_design_v1_2_amendment_20260901.md`（冲突处以 v1.2 修订案为准）。
**决策权威**：2026-09-01 用户决策，见 `reviews/medical_monitoring_engineering_review_20260901.md` 第一节。

---

## 1. 宏观目标（不变）

让用户本人在全部五个真实项目上真实使用医学监查系统：全量/增量 Monitoring Run、风险看板、Subject Workspace、来源下钻、Query 草稿、报告审阅、三模式输出、备份恢复。

## 2. 全局原则（精简后的完整清单）

**继续有效的硬边界（仅此四条）：**

1. 五个真实项目原始文件只读；分析一律使用隔离副本；输出进入隔离目录。
2. 医学写作子系统不动（`services/api/app` 相关路由与 assets）。
3. 医学语义合同不弱化：候选/事实分离、正交发布状态、风险身份与生命周期、中文原生、内部术语不外露、反过拟合红线（§19.1）。
4. 破坏性操作（删除归档数据、删除旧数据库表）先经用户确认。

**明确废止的过程护栏：**

- R8 G0–G8 门序，及"G7 前禁读真实项目、G8 前真实语义不进模型、G6 前不启动产品浏览器、8911/5174 停止令"等衍生约束；
- per-slice 合同冻结、多轮多模型会商、验收记录文书；
- 冻结哈希手账与 digest 刷新工序（git 替代）；
- "沿用同一 worker session"类会话续接要求；
- optimizer/hash-seed 矩阵门禁、clean-streak 机制、三视口视觉矩阵门。

**治理方式：** 阶段内 Codex 自验＋聚焦测试；阶段边界一次独立 fresh-context 评审（单 reviewer 即可）＋用户确认。进度记录写 Trellis journal 与 git commit message，不再向 `context/` 新增过程记录文件。

## 3. 阶段总览

| 阶段 | 内容 | 预估 | 完成门 |
|---|---|---|---|
| A | 现场止血：git、修复中断损伤、Trellis | 半天 | 语法完整＋git 基线＋Trellis 就位 |
| B | 整合归一：单一 package，删三线并存 | 1–2 周 | 测试绿＋产品可启动＋synthetic 冒烟＋独立评审 |
| C | 真实数据接入（确定性层） | 1 周 | 五项目 listing 解析完整＋用户抽查通过 |
| D | 真实模型纵切（单项目 AE/MH 端到端） | 1–2 周 | 用户真实使用一轮并确认 |
| E | 域扩展、报告审阅、三模式、其余四项目 | 按域迭代 | 五项目各≥1 次真实全量 Run＋用户验收清单 |
| F | 打包、备份演练、通知确认、磁盘清理 | 3–5 天 | 一键启动＋备份恢复演练通过 |

各阶段串行推进；阶段内任务可并行。下一阶段开工不需要仪式性授权，完成门通过即进。

---

## 4. 阶段 A：现场止血（立即执行）

1. `git init`；写 `.gitignore`（排除 `artifacts/ runs/ logs/ records/ metrics/ node_modules/ .venv/ dist/ __pycache__/ .pytest_cache/ .ruff_cache/ .playwright-*` 等）；首次提交**包含破损的 `g6_runtime.py`**（保留取证现场）；打 tag `mm-baseline-20260901`。
2. 修复 `deploy/medical_monitoring_local/g6_runtime.py`：删除第 236–241 行孤儿重复段（L225 起的 `_load_store` 新实现以 L235 `return value` 结束，其后为被 Ctrl-C 打断粘贴的旧版残段；顺手核对该方法 `@classmethod` 却以 `self` 作首参的写法）。验证四个候选文件 `py_compile` 通过；跑 `tests/test_medical_monitoring_r8_gate6_synthetic_ego.py`（此前单独运行为 9 passed）与 `tests/test_medical_monitoring_g6_synthetic_bundle_endpoint.py` 确认可收集。**预期 endpoint 文件仍有失败**：release digest 过期（`synthetic_ego.py`/`actual_app.py`/`g6_manifests.py`）＋ `entry_manifest.json` 缺 `entry_url` 字段——记录即可，**不要**刷新 digest 或补 manifest（整个平行应用阶段 B 删除）。commit。
3. `trellis init --codex --cursor --omp --grok --kimi --codebuddy -u "宋旻恺"`；把阶段 B–F 建为 Trellis tasks；把设计 v1.2 修订 7 的工程标准写入 `.trellis/spec/`。commit。

完成门：四文件语法完整；git 基线与 tag 存在；`.trellis/` 结构就位。无需独立评审。

## 5. 阶段 B：整合归一（用户已授权的专项重构）

**目标布局：**

```
packages/medical_monitoring/        # 唯一权威 Python package
  domain/        # 领域对象、状态机、身份、快照/diff（源自 R2）
  graph/         # graph IR、manifest、checkpoint、恢复（源自 R1）
  intelligence/  # 资料/listing 结构画像、mapping、规则（源自 R3）
  risks/         # D01–D10 风险域评估器（源自 R4）
  projections/   # 驾驶舱、中心图谱、Subject Workspace 投影（源自 R5）
  reports/       # 报告审阅、三模式输出（源自 R6）
  runtime/       # ExecutionProfile、harness adapter、后台执行、备份（源自 R7）
  api/           # FastAPI router（薄）
tests/medical_monitoring/           # 随代码迁移的行为测试
tests/fixtures/medical_monitoring/  # 合成数据（JSON 等数据文件）
frontend/src/features/medical-monitoring/   # 单代前端
```

**任务分解（建为 Trellis tasks）：**

1. **迁移盘点**：以 R7 最新链为骨架列出实际被产品路由引用的模块清单；R4/R5/R6 领域逻辑按 import 关系向下收集。注意产品路由**直接依赖 poc 树**（如 `medical_monitoring_r7_product_router.py` 中 `from poc.medical_monitoring_ai_native_r7.src.mm_r7 import ...`），这些 import 全部改指向新 package 是删除 poc 的前置条件。盘点结果决定迁移顺序，先写进 journal。
2. **后端迁移**：按 domain→graph→intelligence→risks→projections→reports→runtime→api 顺序搬迁。每搬一层：修 import、随迁测试、跑绿、commit。禁止边搬边重写逻辑——行为变更与搬迁分离。**旧链 `monitoring_*` 文件（旧 LOOP/assurance/daily-run，产品层约百余文件）不迁移、不删除、不重构**：按设计 §14 保持只读冻结，待阶段 E 五项目验收后由用户另行决定归档；仅当其路由与新链冲突时做最小隔离。
3. **巨型文件拆分**：`medical_monitoring_r7_product_router.py`（7684 行，其中 router 工厂函数单体约 5014 行）拆成按域路由模块；`main.py` 中医学监查挂载收敛为单一 include（医学写作路由与旧链 `monitoring_*` 挂载不动）；5000+ 行的 R4 评估器按风险域内聚拆分。单文件目标 ≤800 行。
4. **前端单代化**：以 r7＋g6 中最新可用实现为准合并到 feature 根目录，删除 r5/旧 root 组件中被取代的部分；医学监查相关路由/状态从 16139 行的 `App.jsx` 抽出到 feature 目录内（`App.jsx` 其余部分不动，全面重构不在本阶段范围）；跑前端测试与 Vite build。
5. **删除平行合成应用**：`deploy/medical_monitoring_local` 整目录删除（git 已留档）。`synthetic_ego.py` 等内嵌 fixture 抽为 `tests/fixtures/` JSON；产品增加 `--synthetic` 启动 profile 加载它。
6. **删除 poc 工作副本**：`poc/medical_monitoring_ai_native_r1..r7` 八棵树删除（git 已留档）。删除前确认第 2 步迁移的测试在新位置全绿。
7. **测试清理**：删除冻结哈希 pinning 断言（硬钉死整文件 SHA 的集中在 `test_d08/d09/d10_artifact_generator.py`、`test_monitoring_shadow_sample_service.py` 等约 4 个文件，含 64-hex 字面量的共约 30 个；digest 行为/形状断言多数是合法行为测试，保留）；删除 optimizer/hash-seed 矩阵跑法；删除依赖已删平行应用的测试。
8. **冒烟**：产品以 `--synthetic` profile 启动，医学监察员核心页面（驾驶舱、中心图谱、Subject Workspace/Journey、进度页）在用户主力分辨率截图存档。这次冒烟即是对原 G6 的全部替代。

**完成门**：迁移后测试全绿；产品本地启动正常；冒烟截图无 P0/P1 级视觉问题；一次独立 fresh-context 评审（重点：迁移是否丢失行为、医学语义合同是否保持）；用户确认。tag `mm-consolidated`。

## 6. 阶段 C：真实数据接入（确定性层）

1. 实现真实数据准入向导（最小版）：项目登记 → 只读隔离副本导入（校验原始文件 SHA 与只读属性）→ 结构画像预览。
2. 五个项目逐个走：SourceRevision → ListingSnapshot → 结构画像 → mapping 候选 → 用户确认关键 mapping → canonical facts。mapping 语义候选可按用户配置调用模型（真实数据允许进模型——2026-09-01 用户决策）。
3. 存在真实双快照的项目跑一次快照 diff。
4. 反过拟合检查：公共内核 grep 无项目名、专有列名、药物名常量。

**完成门**：五项目 listing 全部解析并生成 facts；用户抽查若干受试者的 mapping/facts 与原始 listing 单元格定位一致；独立评审＋用户确认。

## 7. 阶段 D：真实模型纵切（单项目端到端）

1. 项目选 MG-K10-SAR（基座最成熟）。用户配置真实 ExecutionProfile（内置 harness 默认目标沿用 R7 已验证配置）。
2. AE/MH 漏报域端到端：facts → 风险候选（真实模型）→ 反证 → 风险驾驶舱 → Subject Journey 锚定 → 来源下钻 → Query 草稿。既有 Profile/Timeline/漏报交付物作为 reference baseline 接入对照。
3. 后台执行、真实 manifest 进度、中断恢复在真实 Run 上验证一次。
4. 用户本人真实使用一轮：从启动 Run 到导出 Query 草稿。

**完成门**：用户确认"这个域我可以真实使用"；缺陷修复后回归受影响路径；独立评审＋用户确认。tag `mm-first-real-run`。

## 8. 阶段 E：域扩展、报告审阅与三模式

1. 其余风险域（CM/IP、方案/访视/PD、疗效、安全/实验室、多表、中心/项目聚合）按用户实际使用反馈排序，逐域在真实项目上开通。R4 已迁移的领域逻辑是实现基座，每域开通=接真实数据＋看板呈现＋用户抽查，不重跑合成矩阵。
2. 报告审阅接入产品 UI：上传外部报告 → claim 提取 → 问题矩阵 → 批注副本（R6 runtime 已有，补前端）。
3. 三模式（日常/锁库前/锁库后—CFDI 前）在真实项目上各跑通一次，输出四件套。
4. 其余四个项目铺开：每项目≥1 次真实全量 Run；有真实兼容双快照的追加增量 Run。

**完成门**：五项目验收清单（风险定位、来源下钻、Profile/Timeline、漏报对照、Query、报告审阅、模式输出）用户逐项确认；独立评审。tag `mm-five-projects`。

## 9. 阶段 F：打包、演练与清理

1. 工作台层面一键本地应用（启动/停止、无手工端口管理）；医学监查随工作台壳交付，不做独立 .app。
2. 真实项目数据上做一次完整备份 → 恢复 → 校验演练（§15.4 的真实验证）。
3. 本地通知在真实使用中手动确认一次。
4. 磁盘清理：`runs/ artifacts/ records/ logs/` 中 2026-08 医学监查过程产物归档或删除（约 85 GB，**执行前用户确认**）。
5. 性能基线：以真实项目数据记录全量/增量 Run 耗时与存储占用（替代原 R7-09D 合成容量结论）。

**完成门**：一键启动可用；备份演练通过；用户确认收尾。tag `mm-v1`。

## 10. 不做清单（防止复发）

- 不新建平行验收应用或验收专用 runtime/observer 栈；
- 不新增 per-slice 合同冻结、验收记录文书、多轮会商编排；
- 不新增冻结哈希 pinning 测试与 digest 手账；
- 不以合成 case 矩阵数量作为门禁；
- 不把工程状态绑定到外部 harness session 的续接；
- 不在设计 v1.2 之外重新引入 G 门或 clean-streak。

## 11. 风险登记

| 风险 | 缓解 |
|---|---|
| 阶段 B 迁移丢行为 | 测试随代码迁移先行跑绿；搬迁与重写分离；git 每层一 commit；独立评审专查行为等价 |
| 删除 poc/deploy 误删仍被引用代码 | 删除顺序放在迁移测试全绿之后；git 可恢复 |
| 真实数据进入模型的边界误用 | 只用隔离副本；adapter 审计记录 binding 与输入哈希（R7 已有机制） |
| main.py 收敛影响医学写作 | 只动医学监查挂载点；改动后跑医学写作相关路由测试 |
| 治理精简后质量下滑 | 阶段边界独立评审保留；医学语义合同列为评审必查项 |
