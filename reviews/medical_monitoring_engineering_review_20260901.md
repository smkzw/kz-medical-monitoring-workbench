# 医学监查子系统工程 Review 与恢复指令

**日期**：2026-09-01
**审查者**：Cursor（独立工程复核，非原实施链会话）
**证据基线**：当前文件系统（2026-08-31 无损暂停后未改动）＋《System Design v1.1》＋《实施计划 v1.1》＋ `context/medical_monitoring_r8_gate6_engineering_revision_lossless_pause_20260831.md`
**配套文档**：`reviews/medical_monitoring_ai_native_system_design_v1_2_amendment_20260901.md`（设计修订案）、`context/medical_monitoring_ai_native_implementation_plan_v2_20260901.md`（实施计划 v2.0，替代 v1.1 作为执行指令）

---

## 一、用户权威决策（2026-09-01，优先级高于既有文档中的一切自设约束）

以下六条由用户在本次 review 会话中明确拍板，Codex 恢复后必须以此为准：

1. **G7 前禁读真实项目、G8 前禁止真实项目语义进入模型——这两条边界是 Codex 自设的，用户从未要求。** 真实项目资料（只读隔离副本）可以立即进入解析层和用户配置的模型。原始文件只读、输出隔离这两条保护继续有效。
2. **整个医学经理工作台最终是本地单用户应用。** 早期"多用户线上应用"的说法作废。医学监查仍是工作台的子系统，不需要独立的 MedicalMonitoring.app 产品壳。
3. **治理大幅精简**：只在阶段边界做一次独立评审；阶段内由 Codex 自验＋聚焦测试。per-slice 合同冻结、多轮多模型会商、验收记录文书全部停止。
4. **G6 大幅精简**：合成视觉验收降为一次冒烟级检查，验收力气留给真实项目。
5. **版本管理**：在现有 workbench 原地 `git init` ＋ `trellis init`。
6. **授权专项整合重构**：全部医学监查代码收敛为单一 package，删除历史 poc 树的工作副本（git 留档后删除）。

---

## 二、事实基线（本次审查逐项核实的数字）

### 代码规模与分布（三线并存）

| 位置 | 规模 | 性质 |
|---|---|---|
| `poc/medical_monitoring_ai_native_r1..r7`（8 棵树） | 339 个 py 文件，约 30.7 万行 | 每阶段独立实现＋测试；R4 一棵树 94 文件 12.5 万行 |
| `deploy/medical_monitoring_local` | 13 个 py 文件，约 1.39 万行 | G6 专用平行合成应用（runtime/observer/manifest/通知/分发全套） |
| `services/api/app`（产品） | 监查相关约 128 个文件、约 11.8 万行：新链 r5/r7 路由（`medical_monitoring_r7_product_router.py` 7684 行，router 工厂函数跨度约 5014 行）与旧 `monitoring_*`（旧 LOOP/assurance/daily-run）双轨并存；`main.py` 11331 行 | 挂在巨型 main.py 里，违反设计 §18；R7 路由**直接 `from poc...` import** poc 树 |
| `frontend/src/features/medical-monitoring` | 165 文件，约 5.56 万行 | root/r5/r7/g6 四代并存；`App.jsx` 单文件 16139 行集中挂路由/状态 |

单文件之最：`poc/.../mm_r4/protocol.py` 5816 行、`efficacy_evaluator.py` 5634 行、`deploy/.../synthetic_ego.py` 3565 行（147 KB，70 个 def/class，大部分为内嵌 fixture 数据）。

### 过程副产物

- 文档类：`context/` 1469 文件（medical_monitoring 相关 780 个）、`reviews/` 1260、`prompts/` 891、`metrics/` 1080、`plans/` 334。
- 磁盘类：`artifacts/` 53.6 GB、`runs/` 26.6 GB、`records/` 2.9 GB、`logs/` 1.8 GB，合计约 85 GB；对比全部产品代码约 74 MB。
- hash-pinning 测试：tests/ 与 poc 测试中约 30 个文件内含 64 位十六进制冻结哈希字面量；其中硬钉死整文件 SHA 的集中在 d08–d10 artifact generator 等 4 个文件，另有约 135 个文件做 digest 行为/形状断言（后者多数是合法行为测试）。tests/ 根目录监查相关测试合计约 159 文件、10.6 万行。

### 工程基础设施

- **无 git 仓库**，35 万行代码的版本管理完全依赖 markdown 手抄 SHA-256。
- **无 `.trellis/`**，任务管理靠 context/ 下自由生长的暂停记录与验收记录。

### 中断现场（已核实）

- `deploy/medical_monitoring_local/g6_runtime.py` 第 236–241 行是被 Ctrl-C 打断的编辑留下的孤儿重复代码（`_load_store` 方法尾部重复粘贴），`IndentationError: unexpected indent`。另三个候选文件（`actual_app.py`、`g6_manifests.py`、`g6_observer.py`）语法完整。
- `tests/test_medical_monitoring_r8_gate6_synthetic_ego.py` 与 `tests/test_medical_monitoring_g6_synthetic_bundle_endpoint.py` 因 import 该损坏文件在 collection 阶段即失败。
- 暂停记录中"2 个 release-root 测试失败"源于 manifest digest 未刷新——测试断言的是冻结哈希，属 hash-pinning 问题本身的例证。

### 进度与价值

2026-08-09 设计批准 → 2026-08-31 暂停，约三周产出 35 万行代码、数千条合成测试（R4 一阶段"4396 passed + 11258 subtests"），但**五个真实项目一次都没有运行过，真实模型从未进入主流程**，当前全部力气花在给合成数据的平行应用做三视口视觉验收。

---

## 三、问题清单与解决方案

### P0-1 无版本管理

35 万行代码没有 git。所谓"无损暂停"靠手抄 SHA-256 到 markdown，既不能 diff、不能回滚，也无法审查变更来源；本次中断损坏文件无法用 `git diff` 定位，只能靠人工比对。

**解决**：立即 `git init`，写 `.gitignore`（排除 `artifacts/ runs/ logs/ records/ metrics/ node_modules/ .venv/ dist/ __pycache__/` 等大目录），做首次提交并打 tag `mm-baseline-20260901`。此后一切"冻结哈希/暂停记录/恢复锚点"由 git commit + tag 替代。

### P0-2 中断损坏文件阻塞测试收集

见上文事实基线。**解决**：删除 `g6_runtime.py` 第 236–241 行孤儿段（重复的 `_load_store` 尾部），四文件 `py_compile` 通过后再跑受影响测试。此修复应在 git 首次提交之后作为第二个 commit，保留破损现场的取证记录。原暂停记录要求"沿用 worker_01 同一 session 恢复"的约束随治理精简作废——这是一个六行的删除操作，Codex 直接修即可。

### P0-3 价值倒挂：真实数据被自设门禁挡在最后

R8 内套 G0–G8 九道门，真实项目排在 G7、真实模型排在 G8，前面全是合成验收机器。用户已确认该边界非其要求。三周内所有医学价值交付为零，而合成验收机器本身还在产生新的 P0（G5 评审发现多项目×多模式 binding 复用错误、四类 observer 只有 manifest 声明无实现——这些都是验收机器的缺陷，不是产品的缺陷）。

**解决**：废止 G0–G8 门序。按实施计划 v2.0 重排：先止血整合，然后真实数据直接进入确定性解析层（阶段 C），真实模型在单项目 AE/MH 纵切上端到端跑通（阶段 D）。

### P1-1 三线代码并存，无单一权威实现

poc 八棵树、deploy 平行应用、产品路由三处各有一份"当前实现"，前端四代并存；产品层内部还存在新链（`medical_monitoring_*`）与旧链（`monitoring_*`，旧 LOOP/assurance）双轨。同一领域概念（binding、manifest、lifecycle、notification）在 poc r7、deploy、services 中重复实现，`_require_mapping/_require_text/_require_id` 这类校验器在 deploy 各合成模块间复制粘贴。这正是 G5 评审发现"多项目×多模式错误复用 binding"这类缺陷的温床：改一处漏两处。另一个硬耦合：`medical_monitoring_r7_product_router.py` 直接 `from poc.medical_monitoring_ai_native_r7.src.mm_r7 import ...`——poc 树目前就是产品运行时依赖，删除 poc 前必须先把这些 import 改指向新 package。

**解决**（用户已授权）：专项整合为单一 package `packages/medical_monitoring/`（领域内核＋图＋风险域＋投影），`services/api/app` 只留薄路由挂载（目标 ≤500 行）；前端收敛为单代 feature 目录。迁移以 R7 最新链为骨架、向下吸收 R4/R5/R6 领域逻辑，测试随代码迁移。poc 树在 git 首次提交留档后从工作区删除。详见实施计划 v2.0 阶段 B。

### P1-2 治理过程失控，文书产出淹没工程产出

R7 一个阶段切出约 20 个 slice，每个都走"合同冻结→多轮多模型会商→验收记录"全流程；实施计划 v1.1 中"当前实施进度"条目已占全文一半以上，计划文档退化成 append-only 日志。context/reviews/prompts/metrics 四目录合计近 4700 个文件。每个 slice 还要跑"9 个 optimizer/hash 单元"确定性矩阵（normal/-O/-OO × 3 hash seeds）作为门禁。

**解决**（用户已拍板）：
- 治理降为"阶段边界一次独立评审＋用户确认"，阶段内 Codex 自验。
- Trellis 接管任务管理：每阶段一个 task（PRD＋task.json 状态），日常记录进 `.trellis/workspace/` journal，稳定合同进 `.trellis/spec/`。context/ 不再新增暂停/验收记录。
- optimizer/hash-seed 矩阵不再作为门禁，CI 一次 normal 运行即可。
- 实施计划 v2.0 是干净的前瞻计划，历史进度留在 v1.1 里归档。

### P1-3 G6 平行合成应用是过度建设

为了验收而建了第二个应用：独立 runtime（1176 行）、独立 observer（606 行）、独立 manifest 层（484 行）、3565 行内嵌 fixture、独立 .app 壳、独立打包 frontend/dist。其中"四类独立 observers/reconcilers"被独立评审判定只有 manifest 声明没有实现（P0）。验收基建本身成了缺陷来源和维护负担。

**解决**：整合阶段删除 `deploy/medical_monitoring_local` 整个平行栈。合成数据降级为产品的测试资产：fixture 从 Python 常量抽成 JSON 数据文件放 `tests/fixtures/`，产品增加 `--synthetic` 启动 profile 直接加载。视觉冒烟就在产品本体＋synthetic profile 上做，不再需要平行应用。

### P1-4 巨型文件违反设计 §18 与 Ponytail 约束

设计 v1.1 §18 明文"不把现有巨型 main.py/App.jsx 继续当作新控制图"，但 R7 把 7684 行的路由挂进了 11331 行的 main.py（该路由的工厂函数单体跨度约 5014 行）；前端 `App.jsx` 达 16139 行；poc 里 5000+ 行的单文件有四个。

**解决**：整合阶段拆分。工程标准（写入设计 v1.2 §21 并由 Trellis spec 固化）：单文件指导线 ≤800 行、硬上限 1500 行；fixture 数据不得以 Python 字面量内嵌超过 200 行，必须外置数据文件。

### P1-5 hash-pinning 测试制造自我维护负担

31 个测试文件断言冻结的 SHA-256 字面量。任何合法修改都触发"刷新 digest"工序（暂停记录里 2 个失败测试正是等待这道工序）。这类测试不验证行为，只验证"文件没变"，git 之后完全冗余。

**解决**：整合阶段删除 hash-pinning 断言，保留其所在文件中的行为断言。文件完整性由 git 负责。

### P2-1 会话续接刚性

多处记录要求"必须沿用同一 worker session ID、不得新开替代 session"。外部 harness 会话是易失资源，把工程正确性绑在会话续接上不可靠（HY3 会话因供应方 429 中断后，R5-S7 关闭被挂起数日即是例证）。

**解决**：治理精简后废止。工程状态的唯一权威是 git 工作树＋测试，任何 fresh context 都必须能从仓库现状继续工作。

### P2-2 合成 oracle 方法论成本高且已被证伪过一次

R4-D09 发生过评审后追认的过拟合事故：evaluator 靠读取 `mutation_context`、`SYN-*` 哨兵值分支才达成 179/179 parity，清除后仅 151/179 可从领域事实重建。流程最终抓住了它，但代价是整轮返工。数千条合成测试的边际价值递减，而真实数据的第一条反馈还没发生。

**解决**：保留已通过的领域行为测试（迁移时带走），停止新增大规模合成 oracle 矩阵。此后新功能的验证优先级：真实数据上的抽查 ＞ 有代表性的合成行为测试 ＞ 批量生成的 case 矩阵。

### P2-3 85 GB 过程副产物占据磁盘

`artifacts/` 53.6 GB ＋ `runs/` 26.6 GB 等主要是历次执行包和模型运行缓存。

**解决**：git 基线落定后，将 `runs/ artifacts/ records/ logs/` 中 2026-08 的医学监查过程产物移入外部归档卷或删除。**涉及不可逆删除，执行前需用户单独确认**（实施计划 v2.0 阶段 F 列入）。

---

## 四、功能层面建议（新增／删除／调整）

### 建议删除（连同其验收机器）

1. **G6 平行合成应用全套**（见 P1-3）。
2. **十三项 §15.4 应用内任务状态机、九终态×四能力矩阵、六类失效导航**等验收专用编排。注意：§15.4 备份/迁移**功能本身保留**（R7 slice-09A/09B 已实现），删的只是围绕它的合成验收机器；真实验证放在阶段 F 用真实项目数据做一次演练。
3. **macOS presented/点击双通道通知验收**。通知功能保留，验收降为真实使用中的一次手动确认。
4. **四类独立 observers/reconciliation**：只有 manifest 声明、没有实现，直接删除声明，不补实现。

### 建议调整

1. **五项目完成门**：原"双角色×连续两轮零 P0-P4×五项目＋clean-streak 重置"是商业出厂级门槛，对单用户内部工具过重。调整为：每项目至少一次真实全量 Run ＋ 用户本人按验收清单确认。P0-P4 语义保留作缺陷分级语言，clean-streak 机制取消。
2. **视觉验收边界**：原 1920×1080–4K 三视口矩阵降为用户主力分辨率一档＋关键页截图存档。
3. **ensemble/adjudication**：设计保留，默认 `ensemble_size=1`，多模型裁决作为用户可选配置，不作为任何门禁。
4. **workbench AGENTS.md 的执行模块/会商条款**：与本次治理精简冲突（要求 per-slice 会商编排）。建议用户在 Trellis 初始化后，把该文件中医学监查工程部分的路由要求改为"阶段边界评审"口径；此文件为用户所有，本 review 不代改。

### 建议新增（都很小）

1. **真实数据准入向导**：项目登记＋只读隔离副本导入＋结构画像预览。这是原 R8-0 source admission 的精简版，是阶段 C 的入口，也是用户第一个真实可用的功能。
2. **`--synthetic` 启动 profile**：产品本体加载 `tests/fixtures/` 合成数据启动，用于开发和视觉冒烟（替代平行应用的全部职能）。
3. **报告审阅 UI 接入**：R6 已有完整 runtime（三件套、ClaimCoverageLedger），但从未接到产品界面。放在阶段 E，医学监察员真实工作流里价值很高。

### 明确保留（纠偏不动医学语义）

设计 v1.1 的领域模型（§5）、正交状态与发布语义（§5.1）、快照接受链与双基线（§6）、风险身份与生命周期（§10）、Query 三段式（§10.2）、AE/MH 漏报语义（§10.3）、中文原生与内部术语不外露（§3）、反过拟合红线（§19.1，禁止项目专有列名/药物/量表进公共内核）——这些是用户 D1-D39 批准的核心资产，整合重构中不得弱化。

---

## 五、给 Codex 的下一步指示（按序执行）

恢复后立即按以下顺序执行，不要重读 G0–G8 门记录寻找旧约束——旧门序已废止：

1. **读三份文档**：本 review、设计 v1.2 修订案、实施计划 v2.0。以它们为当前权威。
2. **git 基线**（阶段 A）：`git init` → 写 `.gitignore` → 首次提交（含破损的 g6_runtime.py，保留取证现场）→ tag `mm-baseline-20260901`。
3. **修复中断损伤**：删除 `deploy/medical_monitoring_local/g6_runtime.py` 第 236–241 行孤儿重复段（L225 起的 `_load_store` 新实现以 L235 `return value` 结束，其后是被打断粘贴的旧版残段；顺手核对该方法 `@classmethod` 却以 `self` 作首参的可疑写法），四文件 `py_compile` 通过，跑两个 G6 测试文件确认可收集。**预期 endpoint 测试仍有失败**：release digest 过期（`synthetic_ego.py`/`actual_app.py`/`g6_manifests.py`）＋ `entry_manifest.json` 缺 `entry_url` 字段导致 `entry_url_mismatch`——记录即可，不要去刷新 digest 或补 manifest，阶段 B 会删除整个平行应用。commit。
4. **Trellis 初始化**：`trellis init --codex --cursor --omp --grok --kimi --codebuddy -u "宋旻恺"`；把实施计划 v2.0 的阶段 B–F 建为 Trellis tasks；工程标准写入 `.trellis/spec/`。
5. **进入阶段 B（整合归一）**，按实施计划 v2.0 §阶段 B 的任务分解执行。
6. 此后一切进度记录写 Trellis journal 与 git commit message，**不再向 `context/` 新增暂停/验收/恢复记录文件**。

继续有效的硬边界（只剩这四条）：
- 五个真实项目原始文件只读，分析一律用隔离副本，输出进隔离目录；
- 医学写作子系统（`services/api/app` 中相关路由与 assets）不动；
- 候选/事实分离、内部术语不外露等医学语义合同（见"明确保留"清单）；
- 破坏性操作（删除 85 GB 归档、删除旧数据库表）先经用户确认。
