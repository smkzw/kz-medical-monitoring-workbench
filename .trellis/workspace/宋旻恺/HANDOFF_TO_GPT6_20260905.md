# 医学监查子系统无损暂停与 GPT-6 接管文档

**编制日期**：2026-09-05
**工作区**：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
**当前 Trellis 任务**：`mm-phase-c-real-data`（`in_progress`）
**暂停性质**：无损暂停；不是项目完成、Phase C 完成、临床验收或用户验收
**接管对象**：GPT-6 及其后续受控执行链

---

## 1. 恢复来源与证据边界

1. 原父 Session lineage 为 `019fa175-9acf-7830-9742-a0a275db8da5`，其原始 JSONL 已删除。
2. 本续作最初由任务 `019fb615-3845-7033-96c4-f4a80553eda6` 委派进入证据恢复流程，随后以当前文件系统、Git、Trellis、SQLite、隔离运行目录和既存评审材料继续实施。
3. 因此，本文件是**基于现存工程证据重建的项目 handoff**，绝不声称恢复了原始逐条对话、原始隐藏推理或完整时间顺序。
4. 当前文件系统是工程事实真相；Git 提交与 tag 是版本/完整性权威；Trellis 是任务与工程日志权威；真实运行结论必须再由当前 SQLite、artifact、进程和端口状态核实。
5. 任何旧暂停文件、旧 G0–G8 门记录、旧模型会话或历史模型总结只能作为背景证据，不得覆盖当前设计、计划、Git 与实际运行状态。

## 2. 当前权威及优先顺序

接管时按以下顺序解释项目：

1. 用户最新明确要求及后续修订。
2. 当前文件系统和可重放的运行证据。
3. `reviews/medical_monitoring_ai_native_system_design_v1_2_amendment_20260901.md`。
4. `context/medical_monitoring_ai_native_implementation_plan_v2_20260901.md`。
5. `reviews/medical_monitoring_engineering_review_20260901.md`。
6. Git 历史与 tags：`mm-baseline-20260901`、`mm-consolidated`。
7. `.trellis/tasks/`、`.trellis/workspace/宋旻恺/journal-1.md` 和 `.trellis/spec/`。

明确废止：旧 R8 G0–G8 门序及其衍生的“真实资料/真实模型必须最后进入”、per-slice 冻结手账、digest 刷新仪式、optimizer/hash-seed 矩阵、clean-streak、多视口矩阵和外部 session 刚性续接。不要回读这些记录来重新施加旧约束。

## 3. 用户最终目标

为中文原生、资深但不熟悉计算机或 AI、视觉敏感、数据敏感、风险敏感且不愿进行大量机械核对的医学监察员，构建本地单用户医学经理工作台中的医学监查子系统。系统应由 AI 主动完成资料解构、字段理解、趋势识别与风险核查，用户主要查看、确认真正医学上有歧义的少数事项，而不是配置工程参数或逐列审表。

最终产品需要贯通：

- 日常医学监查：定期增量；关注当下录入数据的逻辑性、科学性、AE/MH/CM/研究药物/PD 等多模块深度核查、疗效趋势、安全性信号及前后增量变化。
- 锁库前医学监查：全量基础上的 query 后多轮修订增量，能够追踪变化与残留风险。
- 锁库后至 CFDI 核查前监查：固定总量、全量报告、受试者/中心整合、风险集中呈现和现场自查 checklist。

产品体验目标：

- AI lead，用户看结果、来源、趋势和建议，仅确认少数真正影响医学解释的歧义。
- 受试者层面采用按时间节点展开的 Patient Journey/访视轴，宽屏默认尽量完整显示；事件与融合风险在对应时间点直接标记。
- 中心与试验层面默认是看板，包含受试者“知情同意→筛选→治疗→研究状态”的 Sankey/流向图和可下钻表格。
- 风险融合可覆盖 AE/MH 漏报、禁用药相关 PD 漏报、入排标准违背、其他 PD 及其组合分级，但具体标准必须来自项目资料与通用框架，不得把当前项目特征硬编码进公共内核。
- 页面使用自然中文，不显示“正式事实”“候选信号”“只读 xx”、job/provider/hash/profile/manifest 等内部术语或临时日志标签。
- 对需要真实用户体验测试的页面，后续使用 ego(lite) 浏览器，并让具备视觉能力的模型以“真实医学监察员”角色实际操作；不能以组件能渲染、流程能跑通代替浏览器/用户验收。

## 4. 用户需求与路由要求的演变

### 4.1 从人工核对转为系统自主理解

用户明确否定“让用户大量核对列”的产品路线。系统必须综合列名、列值分布、同表邻近字段、跨表关系、工作表语境、文档资料和整体数据结构推断字段含义。基本推断无误的项目自动接受；只有医学上仍有实质歧义且会影响下游结论时才向用户提一个直观的中文问题。

确认页面不得工程化。默认卡片应直接表达：系统认为这是什么、为什么、如果不是则选择哪个日常医学含义。不得要求用户理解 Excel 坐标、内部列码、模型角色、JSON、confidence 或系统状态机。

### 4.2 独立双 harness/模型机制

最终要求收敛为：

- 主分析：`cms-smk/MiniMax-M3`，高推理；对各 sheet、各列及全表关系进行完整分析。
- 全量盲核对：`zhipu-coding-plan/glm-5.3-flash`，高推理；在不知道主分析归属的前提下完整覆盖、主动寻找遗漏、反证与替代解释。
- 两个模型均由医学监查产品内置的独立 harness 通过裸 API 直接调用；不得再套 OMP。
- Codex/GPT 不参与最终产品运行时的字段解释或冲突裁决。冲突必须由产品自己的匿名双复核、确定性协调、证据闭包和受控再审机制解决。
- 只有 MiniMax 与 GLM 两条远程路线均有可审计的终态不可用证据时，才允许使用本地 `MTPLX/qwen3.8-next-flash`；本地路线是降级补充，不能伪装成双模型通过。
- 模型慢时给予长等待，不能随意判失败或擅自切换。

双 harness 不能只做字段命名，还应为后续临床层准备完整证据边界：CTCAE 匹配、IB/方案所载已知风险、AE/MH/CM/IP/PD 关系、疗效与安全趋势、风险发现及反证。注意：mapping 阶段仍只做字段语义和能力边界，不得提前产出 CTCAE 等级、风险结论、Query 或未经确认的跨表关联。

### 4.3 模型评审要求的变化

- 用户曾明确要求 `gpt-5.6-sol:high` 评估首次 listing 的双 harness 机制；该评审已驱动完整覆盖、稳定身份、盲核对、匿名冲突再审、来源闭包等修复。
- 用户后续要求一次性 `gpt-6-astra:high` 阶段深度 review。当前 live `native-admit --explicit-route` 当时拒绝该组合，报告 Astra 仅支持 low/medium。未降级 effort、未替换模型、未绕过 admission，因此这次 high review **尚未完成**。
- GPT-6 接管后可先重新核验当前 live model catalog/admission。如果 `gpt-6-astra:high` 已合法可用，可补做一次 fresh-context 阶段 review；仍不可用则如实保留未完成，不得冒充完成或暗中改用其他模型。

### 4.4 其他持续有效要求

- 五个真实项目原始文件只读；只在隔离副本上分析；所有索引、缓存、输出、数据库和日志进入隔离目录。
- 医学写作子系统，尤其 `services/api/app` 中医学写作路由与 assets，不得改动。
- 不设计、不实现、不测试任何安全功能；只保留防止临床源数据被误写所需的工程只读边界。
- 反过拟合：真实方案、listing、IB、eCRF、SAP 是通用解析与提示框架的挑战/证据，不是项目常量库。不得硬编码项目名、专有列名、药物、疾病、量表、阈值或风险模式。
- 进度写 Trellis journal 和 Git message；不要向 `context/` 新增暂停、验收、恢复文件。
- 破坏性清理、约 85 GB 历史产物归档/删除、旧数据库表删除均需用户单独确认。
- 当前及本次暂停期间，端口 8911 必须保持停止。

## 5. 阶段 A：现场止血（已完成）

完成事项：

1. 在保留损坏现场的前提下建立 Git 首次基线，提交 `ea84833 chore: capture pre-recovery workbench baseline`，tag `mm-baseline-20260901`。
2. 修复被 Ctrl-C 中断的 `deploy/medical_monitoring_local/g6_runtime.py`：删除 `_load_store` 后的孤儿旧代码段，并纠正 `@classmethod` 首参问题。提交 `0d580ae fix(g6): remove interrupted runtime fragment`。
3. 当时四文件可编译；两个 G6 测试文件可收集。endpoint 中 release digest 过期和 `entry_manifest.json` 缺 `entry_url` 被按计划记录，没有刷新，因为整个平行应用在 Phase B 删除。
4. 初始化 Trellis，建立阶段 B–F tasks 和 `.trellis/spec/medical-monitoring-engineering.md`，提交 `1eacd7d chore(trellis): establish medical monitoring work graph`。

## 6. 阶段 B：整合归一（已完成）

Phase B 总任务和 B1–B8 均已归档为 `completed`；tag `mm-consolidated` 存在。核心结果不是“重写所有逻辑”，而是把可用 R1–R7 行为机械迁入单一产品权威，再分层拆解和删除重复运行时。

### 6.1 B1 迁移盘点

- 以 R7 产品引用链为骨架，盘点 R1–R7、R4 D01–D10、R5 投影、R6 报告、R7 runtime/API 的实际依赖。
- 冻结 challenge fixture、oracle、项目专有规则、旧 LOOP/assurance/daily-run 链，不把它们提升为新产品权威。

### 6.2 B2 单一后端 package

形成唯一权威 `packages/medical_monitoring/`：

- `domain/`：领域对象、快照、身份和状态。
- `graph/`：图 IR、Store、manifest、checkpoint。
- `intelligence/`：规范化、listing 画像、mapping。
- `risks/`：AE/MH、CM、IP、方案、访视、疗效、安全、多表、中心、项目等风险域。
- `projections/`：Journey、Query、驾驶舱、中心/项目投影、发布读模型。
- `reports/`：外部报告审阅、三模式输出。
- `runtime/`：执行 profile、agent harness、生命周期、后台执行、备份恢复。
- `api/`：薄 API 权威。

主要迁移提交从 `b2f66da` 起，依次覆盖 domain、graph、runtime、intelligence、共享 risk、D08/D09/D10、D07、AE/MH、CM、IP、方案、访视、疗效、R5、R6、R7 和产品 import cutover，至 `20d4b85 refactor(monitoring): cut product routes to consolidated package`。

R4 迁移闭环曾验证 4,396 个原行为测试；产品路由与相邻医学写作路径也做过独立聚焦回归。历史测试数量是工程证据，不是医学或用户验收。

### 6.3 B3 巨型文件拆分

- 将 7,000+ 行 R7 路由按 contracts、continuity、backup、public text、result、error、legacy projection、runtime manifest、provider、setup/run/publication/project routes 等能力拆分。
- 拆分 AE/MH、CM、IP、方案、访视、疗效、D07/D09/D10、报告、图存储、mode output、backup/migration/runtime 等大型模块。
- 保留 facade 级 monkeypatch seams、单例 worker/lock、路由注册顺序和兼容对象身份，避免机械迁移改变行为。

### 6.4 B4 前端单代化

- 收敛到 `frontend/src/features/medical-monitoring/` 单一 feature。
- 从巨型 `App.jsx` 中抽出医学监查 route/state/feature ownership。
- 删除重复 g6/r5/r7 前端代际和前端 generation 标识，保留工作台其他功能。

### 6.5 B5 synthetic profile 与 B6 重复树删除

- 产品本体增加 `--synthetic` profile，fixture 外置为测试数据。
- 删除 `deploy/medical_monitoring_local` 平行应用。
- 删除八棵 `poc/medical_monitoring_ai_native_r1..r7` 工作副本；Git 基线可取证恢复。
- 产品路径不再依赖 POC `sys.path` 注入。

### 6.6 B7/B8 测试清理和冒烟

- 移除已废止的 whole-file SHA pin、optimizer/hash-seed 门、平行应用依赖和合成验收机器。
- 保留行为测试和医学语义合同。
- 产品 `--synthetic` 冒烟、关键宽屏截图及阶段评审完成；截图位于 `.trellis/workspace/screenshots/b8/`。
- Phase B 复盘提交 `62b75ed docs(monitoring): close phase b retrospective`。

## 7. Phase C 已完成的通用工程能力

Phase C 仍是 `in_progress`，但已完成大量通用基础设施。以下分组比逐提交罗列更适合接管；完整细节在 Trellis journal 和 2026-09-02 至 09-05 Git 历史。

### 7.1 确定性准入与结构画像

- 建立项目登记、隔离复制、源/副本 SHA 校验、SourceRevision、ListingSnapshot、结构画像和三步中文向导。
- 工作簿物理完整性 manifest 覆盖 sheet 顺序、隐藏状态、空/表头/数据分类、used range、隐藏行列、merged region、named table、autofilter、公式/缓存、number format、header 行。
- 解析失败、隐藏数据未覆盖、digest/顺序/分类矛盾会在模型前失败关闭。
- header-only sheet 被保留，不因无数据行静默遗漏。

### 7.2 稳定身份与关系证据

- 每个 table/field 绑定稳定的 source revision、物理 sheet index/name、table binding、column index 和内容修订。
- 同表提供去标识化的邻近字段、共现、缺失、cardinality、依赖和关系证据；跨表提供同名值域覆盖等候选信号。
- 只保留计数/比率/字段身份，不把原始患者值或值哈希写入关系证据。
- 修复了关系预算被前部表耗尽的问题，改为跨 domain 公平分配；聚焦再审保留所有触及目标字段的关系。

### 7.3 独立双模型 mapping 与冲突裁决

- 提交 `62faa43` 分离主/核对路线，`8965ef1` 强制双 cohort 全覆盖。
- MiniMax 与 GLM 收到同一冻结证据和完整字段覆盖；GLM 盲核对主动找遗漏、反证和替代解释。
- 一次初始 divergence 后，两个独立 harness 对匿名候选做第二轮复核；确定性协调器可采用主分析、核对结果或保守 unmapped。
- 只有持续存在的医学实质歧义才生成一个普通中文问题；缺失/失败/证据不闭合留在内部 blocked/running，不能转嫁给用户。
- 冲突结果用 append-only、输入修订绑定、job/candidate/evidence 闭合的 receipt 持久化；历史 receipt 不覆盖更新后的证据代际。
- mapping 阶段严格禁止 CTCAE 等级、风险结论、Query 和未经证实的 AE/MH/CM/IP/PD join。

### 7.4 模型输出修复和路由身份

- 修复大输出预算、JSON repair、严格 schema、locator 闭包、完整覆盖、匿名 critique、输出代际和重试身份。
- 远程路线必须实际返回配置模型身份；缺失或不匹配会以 `provider_runtime_error` 失败关闭。
- 本地 fallback 不再由环境变量授权，必须由两个精确远程 profile 的真实终态尝试 receipt 触发。

### 7.5 研究资料权威

- 支持 protocol、IB、eCRF、SAP 的候选发现、完整内容解析、locator index、版本/修订链、双模型分析、盲核对、匿名 critique、冲突裁决和原子 promotion。
- protocol/eCRF 是 mapping 必需角色；IB/SAP 缺失时保留明确下游能力限制，不伪造权威。
- 文档选择绑定当前 admission attempt；保存后刷新失败可重放，不要求重新上传。
- UI 只显示“研究文件是否齐备/缺什么/添加文件”，隐藏 registry/hash/locator/profile 等工程细节。

### 7.6 mapping 确认与 facts

- mapping revision 只有在双模型证据、裁决 receipt、来源重验证和语义质量门通过后才能确认。
- facts 生成是确定性批处理：先对所有表的 source/snapshot/digest/locator/complete mapping 做全批验证，再写任何 artifact，防止部分成功。
- 每个数据值都有原始工作表/行/列定位和 hash-bound round trip。
- UI 完成页只给医学监察员显示表数、记录数、数据项数和自动来源核对数，不显示内部 materialization 计数。

### 7.7 身份与治疗边界纠偏

- 修复 `SUBJSTA` exporter context 历史混型；通过 repository-owned、CAS/idempotency、system-only 的 atomic replay 修复旧 draft，不篡改候选证据。
- 将背景治疗/基础治疗实际给药与研究药物给药明确分离；未知 treatment identity 保持能力受限，不能强行归为 IP。
- closed role/catalog 增加必要通用语义别名，但不加入项目名、药名或专有列名。
- confirmation 重验证精确 `expected_job_ids`，避免后续聚焦再审 job 与初始 cohort 共享 profile hash 时污染 source slot。

### 7.8 跨项目身份门

- 发现一次关键错误：RUX-03-002 文档权威与 MG-K10-SAR-001 listing 被绑定在同一隔离 attempt。
- 根因是原准入链分别验证文档和 listing，却未连接标准 study/project/protocol identifier。
- 新增通用身份门：从标准标识字段提取归一化身份，与项目 manifest 标识比较；允许 `[PROD]` 等环境后缀，拒绝跨研究值；只持久化计数和哈希。
- 错配 attempt 已被原位标为 `identity_conflict`，facts/status 均失败关闭；所有 mapping、facts、receipt 和源 artifact 保留取证，不删除、不改名、不提升。

## 8. 不能计为完成的证据

### 8.1 隔离的错配 RUX attempt

错配 attempt 曾产生：

- mapping revision `monmaprev_8097367d62d0b3c82fe59b24f0ee`
- 62 tables、148,788 rows、3,950,919 data items
- 3,950,919 个 locator round trip

但 listing 实际是 `MG-K10-SAR-001`，研究资料是 `RUX-03-002`。该 attempt 现为 `identity_conflict`，上述数量只能作为工程/取证证据，**绝不能算作 MG-K10-SAR、RUX、首项目、Phase C 或临床完成**。

### 8.2 历史旧合同 workspace

`runtime/medical_monitoring_r7/proj_mgk10_sar_real` 中可能存在旧合同 MG workspace，只能用于比较，不是当前双模型、当前文档权威或当前来源绑定的完成证据。

### 8.3 工程测试与 render 断言

测试数、Vite build、组件 render、SQLite status、生成文件和模型“高置信”都不是用户/临床/浏览器验收。Phase C 完成仍要求五项目、原单元格抽查、至少一个兼容双快照 diff、反过拟合检查、ego(lite) 宽屏真实操作、独立 fresh-context 评审和用户确认。

## 9. 当前正确的 MG-K10-SAR 隔离运行

### 9.1 路径与身份

- 运行根：`runs/phase_c_mgk10_authority_v2_20260905`
- runtime DB：`runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_ai.sqlite3`
- workspace：`runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_r7/proj_mgk10_sar_real`
- 项目：`proj_mgk10_sar_real`
- listing attempt：`stg-e9d5050c73ef44be818e1f44920fdb5f`
- document authority batch：`mmbatch_36ec13f31591d1df23641ec5`
- listing SHA-256：`81f47614ca6ab96c3d0a3e45d72ec49c98690fb49e8b574b1dc6b06f7e8259e3`

`runs/phase_c_mgk10_authority_v1_20260905` 也必须保留：它记录首个候选 cohort 因过时 V2.0 PDF 有 4 页需要 OCR、而当时 OCR 路线不可用，从而在模型前失败关闭的诊断。v2 运行仅省略被 V2.1 替代的 V2.0 完整 PDF，仍保留 V1.1→V2.0 修订和 V2.1 正文/修订的版本链。

### 9.2 已完成的资料权威

最终自动选定并推广：

- protocol V2.1（2025-09-19）及修订；主文件 SHA `9729629537ded3b9797eb03e5c60c4797006dae31f27f177cf7885528d38ffa1`，修订 SHA `8e31788d68b66c1ee83af4ecd7b4648c6a591a5cf1a14678292cb6c73ee3ada6`。
- IB V7.0；SHA `e6fc3eedd023bee832445ce7620186ca8b1e1d5dc7f824f85b71c11e261f2ae8`。
- eCRF V1.1 及更新记录；SHA 分别为 `bc93ca20212a3c93a363520fa52565d4cc02b299c5981ba8f5240343e3d03229`、`5c745d7411909876965127cdf37349deed6c9ddb78570c4d96930579f2d15a72`。
- II 期 SAP V1.0；SHA `53515969b487f6f50f652fcedee46dffebf040240486d2acc3f23058f5870699`。III 期/ISS SAP 未混入。

推广 receipt：`c9cf70d654d652798adf743aace96a81b8e4dc90e4a1471bfddb5cae34c9422b`。

解析/来源闭包：

- 6 个 verified source entries，11,261 个 document spans。
- protocol locators 3,009 + 1 supplement。
- IB locators 4,143。
- eCRF locators 2,829 + 1 supplement。
- SAP locators 1,240。
- mapping context ready = true。
- listing-bound document packet SHA：`d8c19be36898bdd8bfd48da92fa760c33d66651cf1f59770a4d67be35759d2ae`。

### 9.3 已完成的 listing 准入与冻结 profile

- admission state：`profile_ready`
- project identity：`matched`
- 1 file、62 tables、148,788 rows
- 1,495 fields
- 62 table bindings
- 360 same-table relationships
- 256 cross-table relationships
- profile SHA：`f682d276bfe2cc11583cde2821351fce34287eaf665baa0daa2336dc67e6e50c`
- mapping input SHA：`e84cb67fe180dc8d08f97214c5f33e7050809fda85fb9512679e0c6d5d05100e`
- source binding revision：`39095cd5364559f20e8f9ddda49bb3fc260579d61860f785a889074f8786a36e`
- listing source revision：`srcc1_bdd4dac3ea07fd7257ef4b08`

### 9.4 当前双模型批次暂停状态

每个首轮 cohort 共 151 个 mapping jobs，其中含四个 cohort 内的 `workbench-system/deterministic-metadata-mapping-v1` 任务。`run_mapping_cohorts.py` 是被忽略的隔离运行助手，只负责唤醒现有产品 worker 并等待当前 cohort，不是产品源码。第一次 120 分钟等待结束后，脚本被修正为只有两边均为 `candidates_ready` 才退出，不能因部分 `needs_attention` 而提前终止。

首轮现已完整完成：

- MiniMax 主分析：`151/151`、`candidates_ready`、1,495 candidates。
- GLM 全量盲核对：`151/151`、`candidates_ready`、1,495 candidates。
- 首次终态失败为 MiniMax 3 个、GLM 12 个。15 个 job 均通过 `MonitoringAiRepository.retry_terminal()`、基于不变 input revision 精确重试并全部恢复；没有 SQL 改状态、模型替换、fallback 或放宽校验。
- 首轮 runner 以 exit code 0 正常退出，当前无首轮 runner。

系统随后组装 draft `monmapdraft_da52157f3ed6f42405d0de95d8be` version 1。首轮投影为 1,495 fields、3 个直接医学问题、1,492 个 system-adopted mappings。全量双路 reconciliation 找到 696 个实质语义差异，需要产品内部匿名聚焦复核；这是 **696 个系统复核项，不是 696 个用户问题**。

聚焦复核为 MiniMax v5 与 GLM v3 各创建 87 个 g01 job。一个 MiniMax g01 早期失败暴露出通用调度缺陷：g01 仍有 queued/running 时，代码错误创建了 87 个 MiniMax g02 job。产品代码已改为：当前代只要存在 `queued` 或 `running` 就必须继续等待，即使同代另有 failed；43 个 mapping bridge/confirmation 测试通过。误建 g02 完整保留，不删除，也不能算作已完成复核。

最终暂停时没有 runner/worker 进程。聚焦复核精确状态为：

- MiniMax g01：7 completed、3 `invalid_ai_output`、1 `provider_runtime_error`、2 `worker_lease_expired`、72 queued、2 个已过期但因 `attempt_count < max_attempts` 仍表示为 running 的可回收租约。
- MiniMax g02：87 queued、0 completed；来自现已修复的过早开代缺陷。
- GLM g01：4 completed、1 `invalid_ai_output`、1 `worker_lease_expired`、80 queued、1 个已过期但可回收的 first-attempt running lease。
- `expire_exhausted_leases()` 已将三个 final-attempt 过期租约转为可审计的 `worker_lease_expired` 失败。其余三个 first-attempt 过期租约按 repository 设计由下一次 `claim_next()` 回收，不能手工伪造终态。
- adjudication 仍为 `running`；尚无 reconciliation receipt、正确项目 mapping confirmation、facts 或 fact summary。

## 10. GPT-6 接管后的下一安全动作

### 10.1 先重新锚定，不启动产品服务

1. 读取本 handoff、三份当前权威文档、`.trellis/tasks/09-01-mm-phase-c-real-data/` 和 journal 尾部。
2. `git status --short`、`git log --oneline -10`、`git tag --list 'mm-*'`。
3. 确认无 `run_mapping_cohorts.py`、worker 或其他本项目残留进程。
4. 确认 `lsof -nP -iTCP:8911 -sTCP:LISTEN` 无输出。除非用户后来明确进入浏览器验收步骤，否则保持停止。
5. 查询上述 runtime DB 的 `monitoring_ai_jobs`，按 `provider/requested_model/status/failure_code` 核实是否与暂停快照一致。

### 10.2 收束当前 MG mapping 批次

1. 首轮已完成；不要再次运行 `run_mapping_cohorts.py`，也不要重建首轮 cohort。
2. 用 `runs/phase_c_mgk10_authority_v2_20260905/run_mapping_reconciliation.py` 恢复现有聚焦复核。三个显示为 running 的 first-attempt lease 已过期，可由 repository 安全回收；禁止 SQL 手改。
3. MiniMax g02 已存在。不要创建 g03、删除 g01/g02 或给代际改名。修复后的代码会等待所选当前代的 active jobs；让既存 job 终态后再检查 pipeline 实际选择的完整 cohort。
4. 对终态失败逐 job 检查 `attempt_count/max_attempts`、failure code、input revision 和响应身份。不得打印患者值、prompt 全文或凭据。
5. 只通过 `MonitoringAiRepository.retry_terminal(project_id, job_id, current_input_revision_sha256=...)` 精确重试，禁止 SQL 手改状态。
6. MiniMax/GLM 的 `invalid_ai_output` 可做一次边界清楚的同输入重试；重复无效时保留失败，不降低 schema。
7. GLM“response did not include configured model name”若再次出现，先诊断真实 provider response identity/caller/endpoint/binding；不能把缺模型名响应接受为 GLM。
8. 不得因单路失败直接切 MTPLX；本地 fallback 需要 MiniMax 与 GLM 两条精确远程路线的当前、终态、可审计不可用 receipt，并且仍不能替代 GLM blind-pass 语义。
9. 两个聚焦 cohort 完整后，让 `adjudicate_draft()` 确定性处理 696 个 divergence、持久化 receipts、更新 draft，并只报告真正残留的用户问题。
10. 只有真正医学实质歧义才产生最少量中文问题。优先由匿名双 harness 二次复核自动采用主结果、核对结果或保守 unmapped。

### 10.3 mapping 质量、确认与 facts

1. 核查 semantic quality：全局一致性、closed role/catalog、来源身份、治疗身份、日期/实验室/量表能力边界。
2. 对历史 draft 需要归一化时，只使用 repository-owned atomic replay；不得修改候选证据、receipt 或 field source provenance。
3. 若 mapping 可 `activate` 或 `activate_restricted`，保留真实能力限制，不为通过门而发明 treatment identity、单位、join 或 standards reference。
4. 确认时必须重验证 exact expected source jobs、当前文档 packet、listing source/hash、profile/input revision 和裁决 receipts。
5. 生成 facts 前运行全批 preflight；任何一张表不完整则零写入。
6. facts 完成后做两层核对：持久化总量/manifest 重开；跨至少三个相隔较远的表抽取确定性 exact-cell 样本并 round trip，但不要在日志/handoff 中写原值。
7. 只有上述正确 MG 隔离 workspace 的结果才可记作 MG 工程 baseline；它仍不是临床或用户验收。

### 10.4 Phase C 后续

1. 做 MG 首项目阶段复盘，核对反过拟合 grep 和 acceptance checklist。
2. 根据 Phase C 任务设计逐个处理其余四项目；不要批量启动五项目，也不要把错配 RUX evidence 重贴标签。
3. 找到至少一个真实兼容双快照项目，做一次完整 snapshot diff（新增/修改/删除/不可可靠比较）。
4. 五项目均形成正确 facts 后，安排 ego(lite) 宽屏实际操作、来源下钻和少量原单元格抽查。
5. 阶段边界补独立 fresh-context review；如 Astra high 合法可用，再完成用户点名的一次性深度 review。
6. 用户确认 Phase C 后才能把 task 设为 completed；随后按计划进入 Phase D 的 MG-K10-SAR AE/MH 真实模型纵切。

### 10.5 Phase D–F 前瞻

- Phase D：MG-K10-SAR 单项目 AE/MH 端到端，facts→风险候选→反证→看板→Journey→来源下钻→Query；验证真实后台执行、中断恢复和一次用户真实使用。完成 tag `mm-first-real-run`。
- Phase E：按真实反馈开通 CM/IP、方案/访视/PD、疗效、安全/实验室、多表、中心/项目聚合；接入报告审阅 UI；跑通日常/锁库前/锁库后-CFDI 前三模式；其余四项目各至少一次真实全量 Run。完成 tag `mm-five-projects`。
- Phase F：工作台一键启动/停止、一次真实备份恢复校验、一次本地通知确认、真实性能/存储/成本基线；历史约 85 GB 产物只在用户另行确认后归档或删除。完成 tag `mm-v1`。

## 11. 当前 Git/Trellis 状态

- 最新产品提交（handoff 前）：`6e04d7e chore(monitoring): quarantine mismatched project evidence`。
- 紧邻关键提交：
  - `1284a5f fix(monitoring): block cross-study listing admission`
  - `2a26137 chore(monitoring): record first-project fact baseline`
  - `5e5b918 fix(monitoring): separate background treatment identity`
  - `30bd2a5 fix(monitoring): revalidate exact mapping source jobs`
  - `0b396e3 fix(monitoring): reopen only stale escalations`
  - `67a1cf3 fix(monitoring): preserve source-valid mapping cohorts`
  - `253b1e0 fix(monitoring): re-review upgraded mapping evidence`
- Phase B 及 B1–B8：completed/archived。
- Phase C：in_progress。
- Phase D、E、F：planning。
- `00-bootstrap-guidelines` 显示 `in_progress` 是 Trellis 引导任务，不代表产品阶段。
- 隔离 `runs/` 受 `.gitignore` 管理，不因未进入 Git 就可删除；它们承载当前 SQLite、artifact、receipt 与取证证据。

## 12. 暂停完成条件

本次无损暂停只有在以下均满足后成立：

- 不存在残留 worker/runner。first-attempt 过期租约可以按 repository 设计仍表示为 `running`，但必须在 handoff 中明确列出，不能冒充有活进程。
- SQLite 当前状态与本 handoff 最终快照一致。
- 8911 无监听。
- Git 工作树除 handoff/journal 预期改动外无未知改动；handoff 和 journal 已提交。
- `py_compile`、`git diff --check` 及相关轻量校验通过。
- 没有删除 v1/v2 run roots、错配 evidence、失败 jobs、receipts、fact artifacts 或任何真实源文件。
- 没有把未完成双核对、工程 baseline、旧合同 workspace、错配 facts 或 render 测试写成临床/用户完成。

## 13. 接管时最容易犯的错误

1. 把错配的 3,950,919 facts 当作首项目完成。
2. 看到 GLM provider response 有内容就忽略返回模型身份缺失。
3. 重新生成整个 1,495 字段 cohort，覆盖或重复当前完成证据。
4. 用 SQL 改 failed/queued 状态，破坏 attempt history 和 fallback receipt。
5. 为消除 capability limitation 强行把背景治疗或未知 EX 绑定成研究药物。
6. 在 mapping 阶段提前做 CTCAE/风险/Query。
7. 把真实项目列名、药名、疾病或当前表结构写进公共代码。
8. 让用户逐列确认，或向用户显示 provider/job/hash/内部状态。
9. 启动 8911、批量跑其余项目或进行浏览器验收，却没有用户当前明确指令。
10. 向 `context/` 新增暂停/恢复文件，或清理 ignored run roots。
11. 修改医学写作路由/assets，或顺手开展安全功能。
12. 在 `gpt-6-astra:high` 不可用时静默降级/替换并声称完成点名 review。

---

本文件应与 `.trellis/workspace/宋旻恺/journal-1.md` 的最终暂停条目、Git 提交以及当前 SQLite 一起使用。若三者有差异，先以文件系统和数据库重新核验，再用新的 Trellis journal/Git commit 明确修订；不要静默覆盖历史。
