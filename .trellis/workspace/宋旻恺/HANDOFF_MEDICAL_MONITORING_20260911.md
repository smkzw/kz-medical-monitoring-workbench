# 医学监查子系统完整交接文档

- 编制日期：2026-09-11（Asia/Shanghai）
- 接管对象：接替本任务的 Agent 及其受控执行、审阅节点
- 产品根目录：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- 当前 Trellis 主任务：`mm-product-rebaseline`（in_progress；运行暂停）
- 交接前 Git HEAD：`18ddfe3`；最新产品逻辑提交：`1ce29f9`
- 本文件性质：项目交接与当前证据索引，不是产品发布、临床验收或恢复运行的证明。

## 0. 接管者先读这一页

这是一个已经完成大规模迁移、但还没有完成正确真实项目医学业务闭环的本地医学监查子系统。不要从零重写，也不要把已有离线模块当成真实产品已经接通。

当前最短正确理解：

1. **用户要的是 AI 主导的日常、锁库前、锁库后至CFDI前全流程医学监查**，不是需要用户逐列核对的数据清洗工具。用户不懂AI/计算机、不愿机械核对，但高度重视来源、真实数值、风险与视觉质量。
2. **架构已经整合**：React/Vite + FastAPI + SQLite + `packages/medical_monitoring/`，单一前端 feature；旧平行应用和多棵POC已删除且Git可追溯。旧A/B为历史，不重做。
3. **当前权威是设计v2、计划v3**。旧设计v1.2、计划v2、9月5日handoff仅解释历史。旧G0–G8、clean-streak、digest仪式等已废止。
4. **主进度停在P2**。P1身份、偏置、调度、暂停、数值/零变化/导入等修复已有工程证据；正确MG的facts→真实AE/MH及反证→看板→旅程→来源→Query尚未完成。P3–P6不能标完成。
5. **最新修复**：tools-v7将前轮等价声明从本轮匿名选项中分离，避免模型抄用旧option_ids。561项受影响回归通过；隔离的剩余2字段由MiniMax和GLM独立完成并一致。仅此2字段，不是全1495字段或全MG验收，也未生成facts。
6. **独立工程审阅未完成**：9月8日ZCode/GLM审阅约17分钟后因用户明确“无损暂停”被中止，exit130，报告还是PENDING。不是模型质量失败，不是通过。恢复时先查可恢复会话；没有可恢复会话可对相同冻结版本重新独立审阅，不伪造原session。
7. **正式入口尚未切到新裁决配置**：[services/api/app/main.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/main.py>) 的 `_r7_admission_mapping_pipeline` 未传新工具/依赖/视觉/角色等价标志。隔离脚本显式开启了它们。不能直接运行旧助手，声称正式MG已使用新合同。
8. **当前运行仍暂停**：9月11日只读核实正式MG `paused=1`，8911未监听。本次仅写handoff，没有恢复构建或调用模型。接任者收到用户继续实施授权后，再按第14节行动。
9. **忽略文件不是垃圾**：正式/隔离SQLite、artifacts、失败回执和备份主要在被Git忽略的`runs/`；未跟踪的Trellis审阅目录也有重要证据。仅克隆Git不能完整接管。
10. **来源存在两个同名版本**：用户给过`9. DM`版本，当前冻结运行来自`13. CFDI核查/自查/评分SDV`版本。9月11日核实文件hash不同，差异检查见第8节和附件；不得仅按文件名替换冻结来源。

接管阅读顺序：本页 → 第1–3节权威/goal/需求 → 第5、7、9、10节状态与合同 → 第13–14节停滞与行动 → 按组件需要读取第6节源码。

## 1. 权威文档及冲突处理

### 1.1 当前有效权威

| 文档 | 完整地址 | 用途 |
|---|---|---|
| 当前系统设计v2 | [medical-monitoring-system-design-v2.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/spec/medical-monitoring-system-design-v2.md) | 产品范围、架构、来源、双模型、医学维度、看板、三模式与验收合同 |
| 当前PRD | [prd.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/prd.md) | 用户目标、任务交付与体验约束 |
| 当前实施计划v3 | [implement.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/implement.md) | P0–P6、历史继承、逐次修复与最新暂停点；追加记录按日期判断，旧“当前”标题不自动有效 |
| 当前任务元数据 | [task.json](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/task.json) | in_progress、负责人及状态注记；不等同运行队列状态 |
| Trellis日志 | [journal-1.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/journal-1.md) | 前后阶段演变和验证证据 |
| Trellis工作流 | [workflow.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workflow.md) | 项目任务管理规范 |
| 全局操作规范 | [AGENTS.md](/Users/smkzw/.codex/AGENTS.md) | 方法学、执行/会商、资源和证据要求；接管时重新读取 |
| 项目操作规范 | [AGENTS.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/AGENTS.md) | 项目/Trellis规范；包含过时条款，按下述冲突处理 |
| 当前goal工具快照 | [current-goal.json](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/handoff-evidence-20260911/current-goal.json) | 9月11日get_goal原始返回；本文件第2节逐字引用objective |

用户所说“本目录prd.md和implement.md”实际位于`.trellis/tasks/09-06-mm-product-rebaseline/`，不是仓库根目录。不要因此另建第二套PRD和计划。

### 1.2 重要的已知文档漂移

- 磁盘[goal-prompt.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/goal-prompt.md)仍有“本任务不用外部执行/会商机制”段落。这是历史文本，**已被后续用户指令和当前goal取代**，不得照抄执行。保留原文件供溯源，本handoff不静默改写它。
- 项目AGENTS中仍引用v1.2/v2为权威，并有旧通用LOOP/会商规则；用户已明确改用设计v2/计划v3、恢复当前全局执行/会商机制、废止旧门序。按当前用户指令解释，不重新施加旧约束。
- 9月5日handoff提出“五项目字段全部完成后再进入AE/MH”。新计划明确先形成正确MG真实纵向闭环，再扩到其余项目。最终五项目目标没有删除，顺序已改变。
- 9月5日工程review中“尚未修复”“goal替换受阻”等是当时状态；P1及后续提交已改变其中部分结论。当前goal工具实际能读到新目标，状态paused。
- `implement.md`保留多次暂停/恢复历史。最新运行停止点为2026-09-08；9月11日仅增加本次交接核验，不等于恢复实施。
- 文件系统、SQLite、Git证明“当前有什么”；用户和当前设计/计划规定“应当做什么”。旧日志和其他模型意见不能自行升级为授权。

### 1.3 历史权威与恢复证据

| 历史文件 | 地址 | 当前作用 |
|---|---|---|
| Fable工程review | [20260901 review](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/reviews/medical_monitoring_engineering_review_20260901.md) | 为什么需要拆除平行应用、废止旧门、开始A/B |
| 设计v1.2修订案 | [v1.2 amendment](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/reviews/medical_monitoring_ai_native_system_design_v1_2_amendment_20260901.md) | 早期设计与修订来源，不能覆盖v2 |
| 实施计划v2 | [v2 plan](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/context/medical_monitoring_ai_native_implementation_plan_v2_20260901.md) | A/B完成、旧C–F任务背景 |
| 9月5日handoff | [HANDOFF_TO_GPT6_20260905.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/HANDOFF_TO_GPT6_20260905.md) | A/B详细迁移史、来源选择、旧批次身份；下一步顺序已过时 |
| 9月6日接管review（文件名仍0905） | [MM_ENGINEERING_REVIEW_20260905.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/MM_ENGINEERING_REVIEW_20260905.md) | P0问题矩阵、前端/下游缺口和新计划缘由 |
| 最初续接提示 | [CONTINUE_MEDICAL_MONITORING.md](</Users/smkzw/Documents/AI Cache/Codex x Hermes/runs/medical_workbench_session_recovery_20260731/CONTINUE_MEDICAL_MONITORING.md>) | 仅解释删除父session后的证据恢复起点 |
| 恢复清单 | [RECOVERY_MANIFEST.md](</Users/smkzw/Documents/AI Cache/Codex x Hermes/runs/medical_workbench_session_recovery_20260731/RECOVERY_MANIFEST.md>) | 不得据此声称恢复原始逐条对话 |

原父lineage：`019fa175-9acf-7830-9742-a0a275db8da5`，原JSONL已删除；最初委派来源：`019fb615-3845-7033-96c4-f4a80553eda6`；当前续作任务ID：`019fb62b-5129-7aa1-86b9-e7da47b18ccd`。本交接根据现存用户消息、文件、Git、日志和数据库重建，不包含或声称恢复已删原对话/隐藏推理。

## 2. 目前goal原文与实际状态

2026-09-11调用`get_goal`：`status = paused`，未完成；未创建、替换或更新goal。Trellis任务仍in_progress是正常的，两者不矛盾。工具返回的累计tokens/time仅原样保存在JSON附件，不把它们解释为可靠的本批成本统计。

以下为工具中`objective`原文，包含原来的换行与首段末反斜杠；不是重新概括的prompt：

```text
接管并连续构建 `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench` 中的医学监查子系统。遵循 `.trellis/spec/medical-monitoring-system-design-v2.md`、本目录 `prd.md` 和 `implement.md`（实施计划v3）。旧A/B为历史，旧C/D/E/F未完成目标按新计划承接，原父JSONL删除不声称恢复原对话。使用Trellis进行任务管理。\
遵循全局Agents.md的方法学、执行/会商机制（120min超长轮询，期间主线程静默）、token saving机制。任务完成前不要自行创造断点、暂停点，不要反复停下。定期进行阶段性清理，将不再使用的、旧版的过程文件、缓存文件、测试记录等等进行清理。
务必要从用户（懒惰、视觉敏感、数据敏感、风险敏感的资深医学监察员）视角去看问题、查问题、想如何构建、计划哪些功能、设计怎样的前端和交互、使用怎样的视觉设计等等等等的内容。最终AI能够非常详尽地解构各个类别各个药物的研究方案、熟悉适应症的疗效/安全性特点、熟悉药品的潜在疗效趋势和风险，并能让用户非常简便、直观、图形化地定位到每个受试者/每个研究中心/每个研究各个层面的历时性数据、趋势性数据、风险点、风险趋势，做到AI lead、用户查看与确认，打通日常医学监查（定期增量；重点在当下录入数据的逻辑核查、科学性核查、AE/MH/CM/研究药物使用/PD多模块深度核查、疗效分析与前后增量趋势更新、安全性信号评估合理性检查、安全性信号分析与前后增量趋势更新等等）、锁库前医学监查（总量、总量的基础上做query后多轮数据修订后的增量）、锁库后-CFDI核查前监查（固定总量；形成全量报告、整合每个受试者/每个研究中心的数据，做到风险集中呈现、个体/中心数据随时查看、个体中心/风险checklist辅助现场自查）的全流程AI医学监查工作。
研究/中心看板包含知情同意→筛选→治疗→研究状态流向与表格；受试者默认全宽访视轴、真实时间间隔、八类临床轨道、忠实数值趋势、风险定位、来源下钻。
产品内置独立harness经裸API运行MiniMax-M3主分析与GLM-5.3-flash全量盲核对，按冻结来源工具化补读Excel/PDF/Word，独立处理冲突。运行时不得由Codex/OMP替代语义解释或裁决；不能以主模型身份/多数票/无问号强行接受分歧。只有两条远程路线当前确不可用才允许指定MTPLX降级且不能称双核对通过。候选/原记录、AE强度/严重性/预期性/因果性/监查优先级分离，项目标准版本固定，未知与覆盖不足可见。

先修研究身份误匹配、裁决偏置、队列重复及暂停恢复、数值/零变化/导入交互错误；再补证据覆盖和工具循环；优先完成正确MG资料→facts→真实AE/MH分析/反证→看板→旅程→来源→Query闭环，然后扩域、真实兼容增量、报告和五项目。五个项目每项至少一次真实全量、存在兼容双快照时增量，完成用户验收清单；备份恢复、一键启动、性能基线完成后才可标完成。
```

补充边界：更晚的用户消息再次确认执行/会商机制有效、要求连续执行、不以“继续推进”收尾代替工作；9月8日“无损暂停”又明确中止运行。9月11日本次任务仅要求交接文档。下一位Agent正式获准继续后，应持续实施，只有真实决策/无法自主解决的阻塞/目标完成才结束；用户再次暂停时则保留状态并停止。

## 3. 用户要求的完整归纳及变化

### 3.1 用户画像与成功体验

- 中文原生资深医学监察员，熟悉医学判断，不熟悉计算机、AI、模型配置、数据工程。
- 不愿做重复、低价值核对；“懒惰”应被理解为产品需要主动承担机械分析工作。
- 视觉敏感：简洁、有重点、原生中文；不暴露job/provider/hash、临时log、“正式事实”“候选信号”“只读xx”等内部标签。
- 数据敏感：图值、日期、单位、分母、来源必须可信；缺失不是0，未知不是“已核对”。
- 风险敏感：风险须可解释、有依据、能查反证，能从研究/中心定位到受试者/事件/单元格/条款。
- 用户首要动作应是“添加研究资料”，然后查看整理进度、能力缺口与分析结果。技术失败由系统解决，不伪装成医学问题。
- 真正医学歧义用少量中文卡片解释“系统理解、影响、可选解释、相关原文”；允许暂不判断，仅限制依赖该歧义的分析。

### 3.2 医学功能合同

| 范围 | 必须交付的行为 |
|---|---|
| 方案/知识解构 | 各药物/疾病/适应症通用解构方案、IB/RSI、eCRF、SAP；提取入排、给药、救援/禁用药、访视、终点、AE窗、AESI、已知风险等有版本/来源/适用时段的知识 |
| 日常监查 | 定期增量；逻辑/科学性核查；AE/MH/CM/研究药物/PD深度联动；疗效和安全趋势及新增/变化风险 |
| 锁库前 | 全量基线 + Query后多轮修订增量，追踪残余风险与每轮变化 |
| 锁库后至CFDI前 | 固定版本全量、研究/中心/个例报告，风险集中展示，现场自查checklist，随时定位个体及中心数据 |
| AE/MH发现 | 从症状、检查、用药适应证、住院/操作、处置、死亡等寻找线索；同时查已记录AE/MH、时间不相容和替代解释，不把线索变成原始记录 |
| CTCAE | 项目规定版本固定；词条/条件/单位/ULN/LLN/基线/症状/干预可追溯，条件不足不给确定等级 |
| 判断分离 | AE强度/分级、严重性、预期性、因果性、监查优先级分离；IB有风险不等于个例因果成立，实验室异常不自动等于AE |
| 药物与PD | 研究药物、背景治疗、合并用药严格区分；禁用药/入排/访视等PD依据冻结方案，不按某个研究硬编码 |
| 风险聚合 | 多维组合风险保留各组件和依据；中心/研究显示人数、记录、暴露/随访分母及小样本限制，不做无解释综合分或惩罚性排名 |
| 增量 | 比较兼容的真实不同时间全量快照；区分新增、修改、消失、范围变化、不可比；规则/映射变化不冒充临床变化，消失不自动关闭风险 |
| Query | 依据—发现—请核实事项，编辑/保存/筛选/草稿导出、版本绑定；不自动向外部发送 |
| 外部报告 | 上传报告、提取原子主张、来源/遗漏对照、问题矩阵、批注副本和草稿；页表图脚注覆盖不足不称全文已审 |

### 3.3 看板与交互合同

- 研究与中心默认看板：知情同意→筛选→治疗→研究状态流向图（Sankey范式）+可筛选表格、风险变化、分母和覆盖。
- 受试者默认全宽访视轴，按真实时间间隔；可放大时间窗，不把实际日期吸附到名义访视。
- 八轨：AE、MH、CM、IP、检查、住院/操作、症状/疗效、方案符合性；事件与风险在时间点/区间定位。
- 缺日期、部分日期可见但不伪造；数值趋势使用真实尺度、真实单位/参考区间，缺失不连成0；禁止固定高度裁剪造成不同值同高。
- 风险可就地查看依据，再显式进入个例；返回保留筛选/滚动；来源下钻不能只显示“定位成功”固定标签。
- 用户验收前使用ego(lite)真实操作、宽屏查看、角色扮演医学监察员，不以源码字符串、组件render、Vite build、HTTP200代替使用体验。

### 3.4 模型、开发机制和授权的变化

| 早期要求 | 后续有效要求/处置 |
|---|---|
| GLM单主模型、DeepSeek备用能力 | 后续明确MiniMax主分析+GLM全量盲核对；DeepSeek不是当前默认核对或默认fallback |
| 只复核模型提出的问题 | 用户要求首次全sheet/全列盲核对，不能只看主模型疑问 |
| 让用户确认关键mapping | 系统先结合列值和全表语境独立判断；明确项自动接受；只询问真正医学歧义 |
| Codex可手工辅助解决分歧的模糊空间 | 用户明确禁止Codex/OMP参与产品运行时语义解释/裁决；只能改harness、提示和工程校验 |
| OMP/外层agent包产品调用 | 产品必须裸API接入自己的harness，开发执行/会商工具与产品运行时分开 |
| GLM不可用就本地Qwen | 两条精确远程路线当前都确不可用才准指定MTPLX降级；不能把降级称双核对通过 |
| 曾暂停外部执行/会商、只主线程或原生Agent | 已由用户明确废止；当前遵循最新全局AGENTS和live route/runner，不盲目固定gpt-5.6-sol |
| 用户曾指定gpt-5.6-sol:high机制评估 | 历史评估驱动双路/覆盖/独立裁决；不能代替最新工程和临床验收 |
| 用户曾指定gpt-6-astra:high阶段review | 早期准入当时拒绝，历史未完成；后来的平台支持可能已变化，接管时查当前可用性，不能沿用旧“不支持”作为永久事实 |
| 浏览器测试早期Playwright | 用户明确转ego(lite)；曾点名ZCode/GLM、Pi/MiniMax、Pi/Gemini视觉角色试用，实际可用型号/路由按当前核查，不静默冒称已完成 |
| 慢任务 | 120分钟级长等待，不因慢重派/降级；用户喜欢等待期静默。若宿主更高优先级要求短进度，保持最简，不以高频轮询生成大量日志 |
| 清理 | 定期清理已证明无用的旧组件/缓存；不删原数据、失败证据、恢复库、Codex session。历史大体量不可逆清理另行确认 |
| 一直连续执行 | 任务未完成不自造断点；但明确“无损暂停”必须执行，不能以continuous为由拒绝用户暂停 |

### 3.5 不做什么

不建设额外安全功能、多租户、第二套应用壳、独立平行验收应用、外部Query发送/回复管理、正式PD报送/电子签名；医学写作路由、assets和共享解析器不动。临床来源不误写、身份/证据正确性属于当前功能正确性，不能因为“不做安全功能”而取消这些合同。

## 4. 来龙去脉与重构历史

### 4.1 证据恢复与旧工程积累

早期工程有R1–R7、P10及多代运行/前端/测试门，之后父JSONL丢失；续作最初只授权只读重新锚定、核对身份/治疗边界、保持8911停止。后续用户明确进入新工程阶段，废止旧门序。旧恢复授权不能覆盖后来的构建授权；旧恢复文档也不能恢复已删对话。

### 4.2 阶段A：保留损坏现场后修复（已完成历史）

- 首次Git基线`ea84833`包含损坏的`deploy/medical_monitoring_local/g6_runtime.py`；tag `mm-baseline-20260901`。
- `0d580ae`删除`_load_store`后孤儿重复代码并纠正classmethod首参问题；四文件编译、两个G6测试可收集。
- 当时endpoint的release digest过期、entry_manifest缺entry_url只记录，没有刷新，因阶段B将删除平行应用。不要今日再回头“修复”这些旧门。
- `1eacd7d`初始化Trellis，建立B–F任务和工程标准。

### 4.3 阶段B：整合归一（已完成历史）

- B1依赖盘点；B2迁移到`packages/medical_monitoring/`，最终`20d4b85`切换产品imports；保留domain/graph/runtime/intelligence/risks/projections/reports/api。
- B3拆分大型R7、风险域、报告、Store等文件；保留单例/锁、兼容facade和路由顺序。
- B4统一`frontend/src/features/medical-monitoring/`，移除多代前端所有权。
- B5产品本体支持synthetic profile；B6删除平行deploy及八棵POC树，Git仍可恢复。
- B7删废止的SHA、optimizer/hash-seed等冻结门测试；B8产品synthetic冒烟和部分宽屏检查。
- 阶段B及B1–B8任务归档completed，tag `mm-consolidated`，复盘`62b75ed`。
- 迁移时有4396项原行为测试记录；这不是当前测试总数，更不是医学验收。9月6日review还发现迁移中部分有用下游行为测试缺失，见第12节。

### 4.4 阶段C：从单模型接入到双模型、资料权威和身份约束

- 先做确定性准入、结构画像、中文导入向导、单路字段解释、mapping确认和facts物化。
- 用户否定大量核对后，增系统理解、自动问题分流和独立裁决。
- 再明确MiniMax主/GLM全量盲核对：分开cohort、禁止旧GLM-only基线混入、匿名再审、append-only裁决receipt。
- 补sheet完整性、隐藏/空/表头表保留、稳定物理列身份、关系统计、来源和文档版本冻结、协议/IB/eCRF/SAP自动权威选择。
- 发现历史RUX资料与MG listing错绑。错配attempt已隔离为identity_conflict，曾产生的约395万facts不能计作任一项目完成。
- 正确MG在9月5日重建独立来源/文档权威和1495字段双路首轮；进入696个系统分歧聚焦处理，之后发现重复g02、失败/暂停恢复等工程问题。

### 4.5 9月6日接管重规划

用户要求完整工程review、必要测试、新设计/新计划/新goal先成文再设置goal。审阅发现：任意前缀身份匹配、二轮默认保留主模型、轮询读取大payload、暂停/增代问题、前端零变化/数值/重挂载失真，以及真实facts到临床分析/发布未接通。于是形成设计v2、实施计划v3、当前PRD。

P1优先止血；P2补完整证据与工具化harness；P3先做正确MG临床纵切。原C/D/E/F未完成目标分别承接到P2–P6；没有缩减最终五项目。

### 4.6 9月6–8日P2修复链

1. 冻结Excel分页/罕见值/邻列和文档正文补读；quote_ref从工具回执绑定原文。
2. 显式`dependency_fields`与`related_fields`说明分离；只明确reference_only的参考说明可不参与硬比较，结构化版本仍严格。
3. PDF区域/Word嵌图读取，产品专用裸API视觉传输；图片hash、局部覆盖、actual bytes绑定。
4. 逐字段角色等价证书；两个模型独立对匿名相同选项判断，不建全局医学同义词表。
5. 证据先物化再绑定证书，避免引用模型自报但最终不存在的evidence_id。
6. 比较策略v2修掉“角色字符串完全相同、只一路有有效可选证书”假分歧；不把单证书当第二票。
7. 严格外层JSON，捕捉真实`finish_reason=length`截断；一次受控修复，不能把内部片段当完整结果。
8. tools-v7移除新匿名选项中嵌入的前轮证明，防止旧option_ids抄入新轮。隔离剩余2字段一致；独立工程review因用户暂停未收束。

## 5. 当前完整计划：哪些完成，哪些没有

| 阶段 | 已实现/有证据 | 未完成/验收范围 | 下一步 |
|---|---|---|---|
| P0 接管与重规划 | 主要工程review、新设计v2/计划v3/PRD/goal、部分前端静态审阅、合成入口浏览器检查 | 没有逐行全仓审计；部分下游独立review失败/未完成；关键迁移行为测试覆盖待补 | 按真实链路补关键行为，不重建旧门矩阵 |
| P1 正确性 | 精确研究身份、禁止默认primary_retained、持久暂停、精确重试/重复代退役、用户答案/回执绑定、数值/零变化/导入修复 | 不代表所有UI或队列场景完美；正式数据恢复未验证新合同 | 保留修复，正式接线时测相邻行为 |
| P2 证据与harness | 分页/样本/正文工具、quote_ref、混合文档覆盖检测资产、图片读取传输、依赖合同、等价证书、严格JSON与v7选项修复、局部真实双路试验 | 最新独立review未完成；正式组合根仍旧配置；完整MG映射/facts未闭合；标准lookup、完整视觉/Word覆盖、第二异构项目挑战待补 | 第14节顺序恢复，不整批重跑 |
| P3 正确MG医学纵切 | AE/MH typed模型和评估器、图执行、风险/投影/Query资产存在 | 正确facts→SemanticRecordSet→真实发现/反证→发布→看板/旅程/来源→Query未端到端；不能用synthetic补空 | 优先于全五项目字段完工 |
| P4 扩域/增量 | CM/IP/PD/访视/疗效/D07安全等离线合同；快照/生命周期资产 | 当前数据和真实模型接线、版本标准、跨域反证、真实兼容双快照diff验收不足 | 逐域启用、可解释分母/能力限制 |
| P5 三模式/报告/五项目 | 模式输出和报告claim审阅等离线资产 | 用户入口、真实全量/增量、报告source闭合、五项目验收未完成 | 每项目至少一次真实全量，有兼容双快照则验证增量 |
| P6 交付 | backup/restore/launch等代码资产 | 真实备份恢复、一键启动停止、性能/调用/存储基线、本地通知/用户验收未完成 | 真实验证后才完成目标 |

“已实现”是模块或工程行为层；“完成阶段”还要求对应真实模型、来源、浏览器、用户证据。不能因为文件已存在或测试数多直接勾完P2–P6。

## 6. 工程组件地图：从输入到用户界面

以下地址均相对产品根目录`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`。它们是接管导航，不声称本次重新逐行审计所有模块。

### 6.1 核心后端

| 层/文件 | 当前职责与接手要点 |
|---|---|
| [services/api/app/main.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/main.py>) | FastAPI组合根、服务/worker/repository装配、router注册。约3629行`_r7_admission_mapping_pipeline`仍旧默认标志；约1249行工具factory已挂在主/核服务。改监查装配时别改写作路由/assets |
| [services/api/app/monitoring_ai_contracts.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_ai_contracts.py>) | 任务、状态、输入revision、候选等类型；不是医学知识来源 |
| [services/api/app/monitoring_ai_service.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_ai_service.py>) | 提交任务、构建prompt/schema、来源/身份校验、tool loop、一次修复、候选验证/持久化。大文件仍是维护债；不要再把所有功能塞进去，也不要为拆文件同时改变医学语义 |
| [services/api/app/monitoring_ai_repository.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_ai_repository.py>) | SQLite持久队列、lease、attempt、candidate、pause、重试和未执行重复代退役。状态查询与大payload执行读取分开；通过公开方法写状态 |
| [services/api/app/monitoring_ai_worker.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_ai_worker.py>) | 后台领取/执行/唤醒；暂停阻止新claim，在途结果允许落盘；重启不能越过持久暂停 |
| [services/api/app/monitoring_ai_router.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_ai_router.py>) | 薄API和队列控制，不应让GET创建/重试工作 |
| [packages/medical_monitoring/admission/pipeline.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/pipeline.py>) | staging→SourceRevision/ListingSnapshot→profile；研究身份精确归一比对，禁止任意startswith |
| [packages/medical_monitoring/admission/mapping_bridge.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/mapping_bridge.py>) | profile/字段/关系/文档证据映射为harness输入及来源身份；物理列标识不可按名称猜 |
| [packages/medical_monitoring/admission/mapping_pipeline.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/mapping_pipeline.py>) | 双cohort提交、当前代/分片、匿名聚焦输入、prompt版本；`_anonymous_review_rows`和`adjudication_prompt_versions`是最新修复点 |
| [packages/medical_monitoring/admission/mapping_reconciliation.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/mapping_reconciliation.py>) | 两路覆盖/证据/语义比较；接收明确comparison policy；输出agreed/diverged/blocked和自动接受边界，不生成facts |
| [packages/medical_monitoring/admission/mapping_comparison.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/mapping_comparison.py>) | 显式依赖/说明字段比较；reference_only不能吞掉结构化标准版本 |
| [packages/medical_monitoring/admission/role_equivalence.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/role_equivalence.py>) | 当前字段/来源/匿名选项绑定，五维角色等价声明，比较v1/v2；不充当医学同义词数据库 |
| [packages/medical_monitoring/admission/mapping_confirmation.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/mapping_confirmation.py>) | 草稿、双方再审receipt、用户已答内容、激活及重验证。禁止旧primary_retained自动放行；新旧prompt/policy回执必须隔离 |
| [packages/medical_monitoring/admission/fact_materialization.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/fact_materialization.py>) | 确认后全批preflight，确定性生成facts和定位索引；不是语义推断器；局部失败不应形成假完整基线 |
| [services/api/app/monitoring_mapping_semantic_quality.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_mapping_semantic_quality.py>) | mapping能力、治疗/对象/日期/量表等约束；审查旧启发式后处理是否污染新模型语义；系统可验证不能替模型改含义 |
| [services/api/app/monitoring_project_registry.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_project_registry.py>) | 项目服务与能力限制投影；未知/不可评估不能用空图或固定成功掩盖 |
| [services/api/app/project_source_manifest.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/project_source_manifest.py>) | 跨工作台项目/来源登记。包含demo及非本任务项目，也含旧产品说明；必须结合当前admission冻结manifest，不能只看登记名称 |

### 6.2 来源、模型工具和视觉

| 文件 | 职责/限制 |
|---|---|
| [packages/medical_monitoring/admission/document_evidence.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/document_evidence.py>) | 当前文档角色、绑定、来源packet，mapping阶段不输出CTCAE/风险/Query |
| [services/api/app/monitoring_document_candidates.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_document_candidates.py>) | 候选文档解析/覆盖、来源定位；历史“有文字即非扫描页”的缺口需看后续覆盖修复，不能从excerpt数量推全文完成 |
| [packages/medical_monitoring/admission/source_tools.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/source_tools.py>) | 冻结listing物理范围、全列画像、罕见/指定值原始行补读；工具只读取，不解释医学 |
| [services/api/app/monitoring_evidence_toolset.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_evidence_toolset.py>) | 每job工具组合：`sample_rows`、`read_source_region`、`get_column_profile`、`search_document`、`read_document_units`，可选PDF区域和Word嵌图；当前未提供lookup_standard |
| [services/api/app/monitoring_frozen_document_tools.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_frozen_document_tools.py>) | 冻结文档正文分页/范围读取，绑定project/revision/source，不把检索摘要当原文全集 |
| [services/api/app/monitoring_document_visual_regions.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_document_visual_regions.py>) | PDF页/区域、Word指定图片提取；局部覆盖与hash，不代表图中医学内容已理解 |
| [services/api/app/monitoring_evidence_tool_loop.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_evidence_tool_loop.py>) | 有界工具回合：模型请求→harness工具→同模型继续；budget耗尽与不可用可见；主/核上下文不混 |
| [services/api/app/monitoring_tool_evidence.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_tool_evidence.py>) | 用读取回执核对quote_ref/visual_ref/来源定位，拒绝伪造或未读引用 |
| [services/api/app/monitoring_visual_tool_bridge.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_visual_tool_bridge.py>) | 监查专属视觉provider和实际图片附加；共享写作gateway不改 |
| [services/api/app/monitoring_visual_transport.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/monitoring_visual_transport.py>) | 裸API文字/图像请求、精确返回模型身份；tools-v6/v7严格完整JSON；保留长度/finish_reason/hash/raw preview，无效正文保留供一次修复 |
| [packages/medical_monitoring/admission/evidence_tool_contract.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/medical_monitoring/admission/evidence_tool_contract.py>) | prompt版本集合与证据重验证规则；新版本须在提交、修复、复验、verifier分支一致登记 |

实际工具读取次数为0只说明模型本次未调用补读，不说明没有拿到冻结profile，也不能说明已看过整个原始工作簿/文档。

### 6.3 下游能力资产与未接通点

- `domain/`：稳定身份、值、快照和schema；`graph/`：Store/artifact/图IR及执行；`intelligence/`：画像/规范化/SemanticRecord等基础。
- `risks/aemh_types.py`、`risks/aemh_evaluation.py`：AE/MH类型与结构化评估入口。消费已提供的语义记录/方案边界/匹配策略，**不自动从Excel解构医学意义**。
- `risks/`的CM、IP、方案、访视、疗效、D07安全、跨表、中心/项目模块多数已有typed/离线行为。需要真实reader、知识包、model harness输出和反证链；不能把注入样例冒充独立运行。
- `projections/`：Journey、Query、dashboard、continuity和publication读模型；所有输出必须来自同一source/run/mapping/rule版本。
- `reports/`：外部报告claim审阅和三模式输出；当前有资产不等于用户上传/领取/草稿导出路径已接好。
- `runtime/`：profile、控制器、恢复、备份、启动、发布等。备份文件存在不等于真实恢复验证通过。
- `api/r7_product/`：细分路由与投影；`publication_providers.py`等需要真实provider。当前main仅在synthetic模式配置发布/模式输出provider；正式正确MG未完成真实发布链。

### 6.4 前端组件及用户含义

统一目录：`frontend/src/features/medical-monitoring/`。

| 组件/模块 | 用户角色与状态 |
|---|---|
| `MedicalMonitoringRouteOutlet.jsx` / Page / Workspace | 主入口与工作区；注意legacy run_ref兼容，不重复管理同一状态 |
| `MedicalMonitoringProductLoop.jsx` | 启动、历史、进度、结果及导航；后台应负责结果发布，离开页面不能丢任务 |
| `MedicalMonitoringAdmissionWizard.jsx` | 添加资料、结构预览、文档齐备、双路整理及少量疑点；导入回调重挂载问题已修，仍须真实挂载交互验收 |
| `MedicalMonitoringQueueControl.jsx` | 持久暂停/继续操作；不是让用户管理provider/job的工程面板 |
| `medicalMonitoringComparisonState.mjs` | 依据比较状态识别有效零变化，修掉“数量为0就是首次” |
| `medicalMonitoringTrendScale.mjs` | 真实数值尺度，修掉固定百分比裁剪；后续还要真实日期/单位/参考线和缺失可视化 |
| Overview/SubjectFlow/Continuity相关视图 | 研究/中心流向、风险/变化及表格；不以已有render证明真实数据发布接通 |
| SubjectWorkspace/DomainTracks/JourneyDrawer/Evidence相关视图 | 八轨、访视轴、风险/来源下钻；默认全宽、真实间距、上下文保留仍需真实验收 |
| Daily/Assurance/Batch/RuleRelease等旧组件 | 尚有兼容消费者；先盘点引用再删，不扩建第二套入口；RiskChecklist可能被Safety/PV共用 |
| Query/报告工作区 | 真实编辑/保存/导出闭环仍需接通；展示一段文本不算完整功能 |

## 7. 数据、运行目录与当前数据库快照

### 7.1 核心运行目录

| 位置（相对产品根） | 身份及用途 |
|---|---|
| `runs/phase_c_mgk10_authority_v2_20260905/` | 当前“研究身份正确”的MG正式隔离运行；不等于已完成医学验收 |
| 上述目录`runtime/medical_monitoring_ai.sqlite3` | 正式持久AI任务/attempt/candidate/pause；571 jobs、321候选封装，详见下表 |
| 上述目录`runtime/medical_monitoring_r7/proj_mgk10_sar_real/` | 当前MG workspace，含staging、source registry、文档候选、图Store/artifacts等 |
| `runs/phase_c_mgk10_authority_v1_20260905/` | 曾因旧V2.0 PDF四页OCR需求未满足而失败的诊断；保留，不冒充通过 |
| `runs/mm_p2_tool_trial_20260906/` | P2隔离小范围真实工具/裁决试验，不是正式MG队列 |
| 试验目录`trial-jobs.sqlite3` | 独立试验任务库，v4/v5/v6/v7失败及成功回执均留存 |
| 试验目录`authority-evidence.sqlite3`与`workspace/` | 从隔离资料构建的试验证据/来源/文档；不是可随意删的cache |
| `runtime/medical_monitoring_r7/proj_mgk10_sar_real/` | 可能存在更早旧合同workspace，不能混同当前正确运行根 |
| `.trellis/tasks/09-06-mm-product-rebaseline/*review*/`等 | 独立审阅冻结源码、prompt、manifest、receipt、报告；很多未跟踪，不能只用Git恢复 |

### 7.2 当前MG身份锚点

- project：`proj_mgk10_sar_real`
- admission attempt：`stg-e9d5050c73ef44be818e1f44920fdb5f`
- document authority batch：`mmbatch_36ec13f31591d1df23641ec5`
- draft：`monmapdraft_da52157f3ed6f42405d0de95d8be`
- 冻结listing SHA：`81f47614ca6ab96c3d0a3e45d72ec49c98690fb49e8b574b1dc6b06f7e8259e3`
- staging manifest hash：`d78556f3c7f500a56b2eec3f5bc1813b3a984acc4a2c5ed69a389518cd6fef5b`
- 历史已登记规模：1文件、62表、148788行、1495字段、62table bindings、360同表关系、256跨表关系；这些是结构画像，不是逐单元格医学理解验收。
- profile SHA：`f682d276bfe2cc11583cde2821351fce34287eaf665baa0daa2336dc67e6e50c`
- mapping input SHA：`e84cb67fe180dc8d08f97214c5f33e7050809fda85fb9512679e0c6d5d05100e`
- source binding revision：`39095cd5364559f20e8f9ddda49bb3fc260579d61860f785a889074f8786a36e`
- listing SourceRevision：`srcc1_bdd4dac3ea07fd7257ef4b08`
- 首轮两cohort各151任务包含确定性metadata任务；“1495 candidates”在旧文字里指字段条目覆盖，不能与SQLite候选结果封装记录数321直接相等。

已选文档（来自9月5日promotion记录，接手时仍需当前source复验）：protocol V2.1 2025-09-19正文及修订；IB V7.0；eCRF V1.1及更新；II期SAP V1.0，不混III期/ISS SAP。6 verified source entries、11261 spans是当时解析索引规模，不自动证明图表/脚注/完整医学知识已理解。完整hash见9月5日handoff第9.2节和实际authority packet。

### 7.3 2026-09-11只读现场核实

正式MG queue_control：`('proj_mgk10_sar_real', 1, '2026-09-06T00:30:13.659860+00:00')`；8911 TCP未监听。

| provider / model | completed | failed | queued | running行 | blocked |
|---|---:|---:|---:|---:|---:|
| cms-smk / MiniMax-M3 | 158 | 6 | 72 | 2 | 87 |
| zhipu-coding-plan / glm-5.3-flash | 155 | 2 | 80 | 1 | 0 |
| workbench-system / deterministic-metadata-mapping-v1 | 8 | 0 | 0 | 0 | 0 |

合计571 jobs；候选封装321。87个blocked行带`contract_retirement_code=duplicate_unstarted_generation`，是已通过repository退休的误建g02，不能再当待运行队列恢复。`running`是持久状态行，**不是今天有活模型进程的证明**；恢复时检查lease，再由repository合法回收。

本次仅为确定性一致性比较只读访问工作簿内容，未输出或持久化患者行值，没有调用provider或启服务。9月8日本轮worker/runner及审阅子进程退出有暂停记录；接手当天仍应重新查本项目进程，不用整个机器的其他Agent状态推断本项目。

## 8. 五个真实项目、来源差异与隔离约束

五项目范围：MG-K10-SAR、RUX-03-002、MY009-UC、MY008211A-PNH-3-02、MY008211A-PNH-3-01。工作台中还有demo、CRSwNP、D001等登记，不能误当本次五项目清单。

| 项目/ID | 来源入口与注意事项 |
|---|---|
| MG / `proj_mgk10_sar_real` | 用户给过`/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR/9. DM/【锁库后Data Listing】MG-K10-SAR-001_FormExcelAllVersion_202601201126.xlsx`；当前隔离manifest实际来源为同名文件的`13. CFDI核查/自查/评分SDV`目录。两者差异见下 |
| RUX / `proj_rux_03_002` | `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD`；manifest登记`CFDI Inspection/准备阶段/RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx`及方案等。历史原始/处理后来源有区别，不把旧129-job GLM-only或错配MG数据当新双路证据 |
| MY009 / `proj_my009_uc` | `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC`；listing登记`S1安全性评价-202604/MY009-UC-2-01-MM Listing_20260408(已自动还原).xlsx`。自动还原/Comparison来源不能伪装未经加工原始导出；真实性与覆盖需单独核实 |
| MY008 3-02 / `proj_my008_pnh_3_02` | `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/原始数据/【3-02初治锁库后数据集】MY008211A-PNH-3-02-锁库后EXCEL数据集.xlsx`；方案路径在project_source_manifest.py约932行 |
| MY008 3-01 / `proj_my008_pnh_3_01` | `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）/原始数据/【3-01经治锁库后原始数据】MY008211A-PNH-3-01_锁库后EXCEL数据集.xlsx`；方案和TFL/CSR登记在manifest约1046行 |

以上除MG两个同名文件外，本次主要核对登记源码，未遍历其余原始目录或重新验证完整性。接任者不得把“已登记”写成“已真实全量通过”。原件只读，sidecar/cache/index/output全部进隔离目录。

### 8.1 9月11日新增的MG同名来源核查

| 文件 | bytes | SHA-256 |
|---|---:|---|
| 用户指出的`9. DM`版本 | 17014302 | `e711c52fa4b41ed77270bfadefa56018a9576afe42fd2ef051e2230c6e03f4a3` |
| 当前隔离manifest的`评分SDV`版本 | 17013973 | `81f47614ca6ab96c3d0a3e45d72ec49c98690fb49e8b574b1dc6b06f7e8259e3` |

只读ZIP部件比较：成员集合相同；不同部件为`docProps/core.xml`、`xl/workbook.xml`、sheet1/25/27/28/29 XML。其余部件逐字相同。

对不同的5个sheet逐cell坐标比较类型、子节点内容（值/公式/inline内容）和style：无新增/缺失cell、无内容/公式XML差异、无style差异。被比较cell数分别124、562078、27956、80556、9828。此为确定性结构对比，不是医学判断。

非cell结构有差异：修改时间、workbook视图/版本信息、两处definedName文本、部分视图选择、隐藏行/筛选等；sheet25的81处row.hidden、sheet28的36处row.hidden不同。某些根子节点数量变化，粗粒度结构比对没有进一步穷尽该子树。不得据此声称工作簿完全语义等价或可直接互换。

**恢复优先动作新增**：先明确产品当前选择哪个来源；用冻结manifest、隐藏/筛选/命名范围覆盖校验评估复用。若改用用户9.DM版本，应建立新的SourceRevision和受影响工作单元，旧证据可否复用需可重放的等价证明；不能改旧hash、改名或把两个文件默认为同源。无需让用户核对列值；只有来源业务权威无法由现存记录决定时才问一个明确的来源选择问题。

### 8.2 其他来源陷阱

- 错配RUX资料/MG listing曾得到62表、148788行、3950919数据项/locator round trips，已隔离为identity_conflict；数量再大也不能计作正确MG或RUX验收。
- 同一快照原始/处理后只能证明解析兼容，不能算时间增量。
- 历史RUX 2025-04-16→2025-06-12是潜在真实增量对线索；旧来源矩阵对加工属性有记录。新计划仍需重新核实兼容性、日期、范围和来源，不恢复旧门序。
- 已解构Timeline、Profile、自查手册、评分SDV结果只能作输出交叉对照，不可跳过原始资料准入/模型理解作为E2E起点。

## 9. 模型调用、真实试验与当前停止点

### 9.1 开发Agent与产品模型严格分开

产品：MiniMax-M3主分析，GLM-5.3-flash盲核对，自己的harness裸API，独立上下文、同冻结输入、匿名二轮。当前provider实际为`cms-smk`，用户常称`cms-router`；应核查具体runtime binding而不是随意字符串替换。高推理要求保留。

开发/审阅：Codex及全局route选择的ZCode/Pi/Cursor等，仅开发/挑战工程artifact，不能在产品运行时替模型填写语义。全局路由以`/Users/smkzw/.codex/tools/hermes_workflow_guard.py`、`route_policy.py`、`conference_session_runner.py`及live manifest为准；新工作边界重新选路由，健康长任务不改模型。

凭据位于本机runtime/provider配置，**不要复制到handoff、git、日志或新Agent消息**。只记录profile/model/来源/attempt身份；endpoint状态接手时验证，旧请求成功不证明今日可用。

本地MTPLX仅双远程当前确不可用时按指定路线降级；一次格式错误/质量失败不是两路不可用。9月7日用户问“为何加载Qwen”：oMLX日志确认约16:06加载、16:13卸载；未能证明具体调用者，不归因本产品。本工程未发起Qwen加载/重启，接手不得把这段当本地fallback已验证。

### 9.2 P2真实试验演变（不跨版本累计通过率）

| 合同/范围 | 实际结果 | 解释 |
|---|---|---|
| 早期12字段/聚焦 | 曾有3一致、随后部分聚焦新增一致 | 不同输入/版本，只作演进证据 |
| 显式依赖tools-v2 12字段 | 两路完成，3一致/9分歧；0补读 | 区分解释依赖与参考说明后仍需模型处理，不替它们填空 |
| tools-v4 9字段 | MiniMax格式/可选标准后修复不完整失败；GLM完成但无等价声明 | 未双路通过，未facts |
| tools-v5 9字段 | MiniMax `monai_a1fe2c38a262d51d8172e874623a` failed；GLM `monai_d2d0c293b8de3990ad207c5f53cd` completed | 仅保存解析后内部对象，无法据此知道raw外层是否截断，驱动严格解析 |
| tools-v6 9字段 | MiniMax `monai_df027cc76d76896a8abdb331fe58`与GLM `monai_44aa61170fb0972f3460059b361e` completed；7一致2分歧，0覆盖/合同违规 | `dual_model_pass=false`，剩AEENDAT/AEOUT依赖声明分歧，未facts |
| tools-v6剩余2字段 | MiniMax `monai_22fd3eff03918161fe88ccc51b01` failed；GLM `monai_a83b6306e70afae593beb8732517` completed | MiniMax修复后`role_equivalence_option_set_mismatch`；查到抄用前轮编号 |
| tools-v7剩余2字段 | MiniMax `monai_b78ea3123b3cd60b39ef6c3c6a8f`、GLM `monai_53547c1fbf2ab8c0374151eecc55` completed；2一致，0分歧/违规 | `dual_model_pass=true`仅此2字段，0工具读，`facts_generated=false` |

不能把v6的7/9加v7的2/2写成整个MG在v7已全量闭合；若复用前轮一致项，需要按来源/字段/prompt/比较策略和当前确认逻辑证明兼容。

### 9.3 真实截断的决定性证据

tools-v6 MiniMax首回：`strict_parse_status=truncated_fence`、`finish_reason=length`、22494字符；被拒收。一次受控修复：`ok`、`stop`、16566字符，完整schema通过。此前旧共享解析器能从坏外层提取完整内层dict；新监查专属严格路径拒绝这种误收。不要为提高通过率恢复宽松salvage。

### 9.4 精确暂停现场

最后正常产品逻辑提交`1ce29f9`，最新暂停记录提交`18ddfe3`。9月8日独立审阅runner会话句柄85988曾运行约17分钟，由用户暂停触发SIGINT，exit130；本任务相关PID49061/49087/49127/49191当时确认退出。PID与句柄只作历史，不在接手时盲目kill相同数字。

[当前未完成审阅目录](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/current-options-20260908)包含冻结`frozen-1ce29f9`、prompt、route manifest、health和PENDING输出。ZCode可恢复session ID尚未取得；接手先找已有receipt/session记录，没找到就如实重新独立审阅同一冻结artifact，不需把工程状态绑定某个外部会话才能继续。

## 10. 最新实现合同：接手不能破坏的细节

### 10.1 版本分层

- tools版本是prompt/证据工具/输入合同命名空间；比较策略版本是另一维。tools-v7当前比较策略仍为`mm-mapping-role-equivalence-v2`，不能把两个版本号当一回事。
- 主裁决tools-v7：`monitoring-listing-field-mapping-adjudication-v12-tools-v7`。
- 核裁决tools-v7：`monitoring-listing-field-mapping-adjudication-verifier-v10-tools-v7`。
- tools-v6严格版本为主v11/核v9；tools-v5证据闭合版本为主v10/核v8。旧集合保留用于历史复验，不在原job下静默替换prompt。
- 默认构造`AdmissionMappingPipeline()`不自动启用新工具；隔离试验显式设置`adjudication_tool_reads=True, explicit_mapping_dependencies=True, visual_tool_reads=True, role_equivalence=True`。正式main还没设。

### 10.2 证据、语义与说明

1. `dependency_fields`是解释该值/对象/单位/日期/编码等实际依赖，须显式、唯一、绑定冻结其他字段；缺失不能默认空。
2. `related_fields`是关联说明，不能用来建立join或代替依赖。双方说明留存，不因文字不同制造大量用户问题。
3. `standards_reference={}`仅规范为空；非空残缺标准必须拒绝。只有明确reference_only时部分名称/概念/不确定性说明可不参与硬比较；CTCAE版本等结构化键、未知键仍硬比较。
4. 对象身份、治疗/剂量、原值/编码、单位/日期、派生血缘、质量阻断、标准版本等实质差异不能被“同义”“高置信”“主模型”掩盖。
5. 模型自报evidence_id不能直接证明引用有效；先物化最终证据，再将证书轴引用绑定到最终可验证集合。
6. profile统计证据只证明收到的统计/语境，不冒充完整原始单元格或未读文档。tool quote_ref必须来自实际冻结读取回执。
7. 图片原字节经专属provider送出，hash/visual_ref和区域保存；视觉解释不当作原生逐字引文。

### 10.3 等价证书与v7修复

- 首轮保持真正盲核；仅匿名再审可见双方候选。
- 证书有equivalent/distinct/insufficient、两个当前option_id及五维依据/反证说明；绑定domain/source_field/source_scope/完整匿名选项内容。
- 两路等价且其他硬属性全等才可在原角色编码中选一个确定表示；不是创建全局同义词映射，更不是用工程词表替代医学判断。
- 比较v2仅允许“双方role逐字相同、其他硬属性一致、只有一路附有效同字段equivalent声明”不产生假分歧；不生成双路证明、不改role。大小写不同也不当逐字相同，distinct/insufficient/错绑定/硬差异仍阻断。
- v7新增`exclude_prior_proofs`：构造新匿名选项时只排除`semantic_verdict.role_equivalence`历史裁决说明；保持原记录不变、其他硬约束不变、当前投影重新计算option_id。
- 默认helper不排除历史证明以保留旧行为；新role_equivalence路径明确启用。交换primary/verifier后投影应完全相同；不得在排序、hash或文本中携带主模型优先权。
- 新增测试使用虚构OTHER/VALUE/UNIT，避免对AEENDAT/AEOUT硬编码修复。

### 10.4 严格回复与一次修复

- 只接受完整bare JSON或完整fenced JSON对象；禁止从截断外层截取内部对象。
- 记录生产诊断键：`strict_parse_status`、`strict_raw_preview`（上限8000字符）、`strict_raw_sha256`、`strict_raw_chars/bytes`、`strict_raw_truncated`、`strict_finish_reasons`。
- 无效正文以`invalid_response_text`完整保留；一次受控修复仍完整校验schema、字段覆盖、来源和选项绑定。二次失败不持久化伪候选。
- 曾遗漏二次失败分支的诊断，现已补齐；服务测试已对齐真实生产键。
- 旧tools-v5/default宽松共享行为保留，为保护其他工作台模块没有改共享写作gateway。新监查调用需真正启用strict，不能仅版本文字更新。

## 11. Git、审阅与证据索引

### 11.1 最近关键提交

| 提交 | 意义 |
|---|---|
| `51df9e8` | 新v2/v3文档、研究身份/保守裁决、持久暂停基础 |
| `b017261` | 有界分片恢复、暂停UI、重复未执行代退役 |
| `f1a2dc4` | 零变化、真实数值、导入交互等修复 |
| `3f7b9e2` | 工具接入恢复与opt-in证据裁决 |
| `4792bc5` | 显式依赖、保留模型语义 |
| `f768fd3` | 冻结PDF区域/Word图片 |
| `201260a` | 可选参考说明假missing-key差异 |
| `8f11114` | 真实裸API视觉证据工具链 |
| `2214961` | 字段局部独立角色等价证书 |
| `2b79e57` | 超大图像413停止无效重试、canonical草稿恢复 |
| `540d2c3` | 最终物化证据后绑定证书 |
| `5842540` | 同role可选证书比较v2，保留v1 |
| `47b3e7d` | 严格完整回复与失败/修复诊断 |
| `3f702c7` | 测试诊断字段与生产一致 |
| `1ce29f9` | v7本轮选项与前轮证明分离 |
| `18ddfe3` | 9月8日最新无损暂停记录（交接前HEAD） |

代码/文档以实际Git为准，当前并非每个历史问题都在这些提交中完整关闭。不要因commit里有“close”就忽略后来发现的缺口。

### 11.2 已完成审阅与未完成审阅

- `evidence-review-20260907/runs/conference/mm-p2-evidence-review-20260907/general_single_object.md`：540d2c3审阅，认可证据物化绑定；指出可选证书假分歧。它提出的R2首轮auto-pass丢证明后来确认前提不成立。
- 同目录`optional-proof-review.md`：冻结5842540，74项验证；接受v2边界，明确撤回上述R2。别重做已撤回的问题。
- 同目录`strict-response-review.md`：冻结47b3e7d，59项验证，无阻断；建议测试诊断键保真，已在3f702c7修正。
- 上述审阅使用Pi/Cursor `default`动态选择器，具体底层模型身份当时不可核实；不要把它描述成某个已验证具体模型的独立意见。
- `response-shape-20260907/runs/execution/mm-p2-response-shape-20260907/worker_01.md`：Pi/opencode-go/muse-spark-1.3-contributor:xhigh执行结果。主线程合并重复HTTP实现后独立验证；worker输出是实现输入，不能直接算最终接受。
- `current-options-20260908/runs/conference/mm-current-options-20260908/general_single_object.md`：**PENDING占位**，ZCode/GLM-5.3-Flash:max审阅用户中止；这是最近一项待收束工程证据。
- `.trellis/tasks/09-06-mm-product-rebaseline/tool-review/`保留此前GLM工具/证书审阅与冻结版本，按报告实际版本判断，不混用。

上列目录均在`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/`下。旧packet中可能有TODO metrics/review模板；不要填虚构工具次数/耗时/模型身份。真实runner receipt和报告才是运行证据。

### 11.3 关键隔离结果/日志

均在`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runs/mm_p2_tool_trial_20260906/`：

- `role_v6_reconciliation.json`：9字段7一致2分歧。
- `role_v7_reconciliation.json`：仅剩余2字段一致。
- `pause_20260907_strict_response_manifest.json`、`pause_20260908_manifest.json`：DB/结果/日志hash及暂停状态。
- `mm-role-v6-real-20260907.log`、`mm-role-v6-residue-20260907.log`：v6两阶段终态。
- `mm-role-v7-residue-20260908.log`：v7两字段终态。
- `mm-strict-service-regression-20260907.log`、`mm-v7-service-regression-20260908.log`：相关回归证据。
- `mm-current-options-review-20260908.log`：用户SIGINT/KeyboardInterrupt；不能据此判模型质量失败。
- `adjudicate_role_equivalence.py`、`adjudicate_role_residue.py`、`trial.py`：被忽略的隔离助手。会准备来源并提交/运行真实任务，**不是只读状态命令**。接手先读，不盲目执行。

重要：这些脚本通常`run_next`只消费一个当前匹配任务；以后库中有多个queued时，脚本名称/预期不证明实际执行哪个job，必须核对返回job_id和输入revision。

## 12. 测试证据、执行方式与尚缺验证

### 12.1 已有验证

| 批次 | 证据 | 不能推导什么 |
|---|---|---|
| B迁移历史 | 4396旧行为测试、synthetic冒烟/部分截图 | 当前完整测试覆盖、真实医学通过 |
| P0接管 | 256准入链测试、Vite build、身份/PDF最小复现、部分ego入口检查 | 完整UI或真实AE/MH运行 |
| P1修复 | 身份、裁决、队列/答案恢复、数值/零变化/导入针对性回归和部分浏览器证据 | 全部临床域和五项目 |
| 540d2c3批次 | 692项受影响回归（历史日志），证据闭合修复 | 新版本独立review或所有真实数据通过 |
| 5842540 | 100比较/确认相关回归；独立74项 | 所有模型语义都正确 |
| 47b3e7d | 517项相关回归；独立59项；生产诊断键后2项 | 正式MG已切strict、全量映射闭合 |
| 1ce29f9 | 561项服务/角色/确认回归；含73项先行聚焦 | 独立审阅已完成、正确facts/风险已经发布 |
| 真实双路 | 视觉小图传输通过、正文quote_ref补读通过、v7剩余2字段一致 | 全文/全单元格医学覆盖、五项目或临床验收 |

这些集合有重叠，不相加形成“总共通过多少”。9月11日为handoff做了源文件/数据库/链接与状态核查，**未重新运行上述全部测试**。

### 12.2 恢复后的实用命令（先明确scope再运行）

在产品根目录使用仓库`.venv/bin/python`，不要默认系统python含pytest或兼容现有依赖。无需为handoff安装新库。

```sh
git status --short
git log -15 --oneline
git tag -l 'mm-*'
git show --stat 1ce29f9
git diff --check
```

影响v7投影或证据服务时的已用聚焦集合：

```sh
.venv/bin/python -m pytest tests/test_monitoring_role_equivalence.py tests/test_mm_c3_mapping_confirmation.py -q
.venv/bin/python -m pytest tests/test_monitoring_ai_service.py tests/test_monitoring_role_equivalence.py tests/test_mm_c3_mapping_confirmation.py -q
```

改正式装配/队列再按影响加入：[tests/test_monitoring_ai_repository.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_monitoring_ai_repository.py>)、[tests/test_monitoring_ai_worker.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_monitoring_ai_worker.py>)、[tests/test_monitoring_ai_api.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_monitoring_ai_api.py>)、[tests/test_mm_c3_mapping_bridge.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_mm_c3_mapping_bridge.py>)、准入/确认/物化测试。测试输入用合成独立runtime；不要让测试环境误接正式MG库。

前端检查使用现有脚本和Vite的独立输出目录；浏览器使用ego(lite)，产品[services/api/app/__main__.py](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/__main__.py>)是启动入口参考。此处不提供一条可误启动正式服务/模型的复制即运行命令。

### 12.3 仍需补的验证

- 新v7独立工程review及当前装配应用验证；新旧prompt与旧receipt兼容，不能复用未知来源job。
- 新源码是否能正确处理正式696分歧，而不仅2个样本；兼容重试只处理目标分片，不重放首轮或退休g02。
- 混合PDF/图表Word/异常Excel真实工具覆盖；0工具调用的profile一致不算这些完成。
- 9月6日review发现迁移删掉4份AE/MH/ensemble/历史匹配测试、约3667行，当前无同等行为覆盖证明。应恢复最小关键行为测试，而非旧门/巨矩阵。
- 正确MG事实与至少多个相距较远表的原单元格round-trip；来源hash差异处置先于正式接受。
- 真实模型AE/MH发现+反证、风险身份/状态/分母、真实publication、浏览器旅程/来源/Query。
- 每个最终研究真实全量、适用的兼容增量、三模式报告、备份恢复/一键启动/性能基线和真实用户验收。

## 13. 停滞分析：事实、原因和本Agent的反思

### 13.1 直接暂停原因（事实）

最新停止是用户2026-09-08明确“无损暂停”，并非我判定项目已完成。两字段真实运行当时已终态；独立工程review还在运行，被按用户指令中止。因此目前缺一个最新修复的独立审阅结论，以及正式装配/数据恢复验证。

### 13.2 为什么长期停在接入与P2（工程事实）

1. **前期来源身份错配**：RUX文档配MG listing的错误使既有大量facts不能用作医学完成。必须重建正确来源链；这个成本不是可用代码量能抵消的。
2. **“少问用户”曾被实现为默认主模型正确**：新review发现二轮仍分歧却primary_retained的偏置，需要改回证据驱动。这暴露真实分歧量，而不是产品突然变差。
3. **字段解释与说明、依赖、角色编码混在一起**：两模型意思可能接近但输出结构不一致；若宽松合并会吞掉实质差异，若全部严格文字比对又有假阻断。因此经历显式依赖、reference_only、角色证书等版本化修复。
4. **任务层缺陷放大调用成本**：在g01仍active时误建87个g02；失败/暂停/用户答案/恢复需保持可追溯，不能删库重新跑掩盖。
5. **大输入/大输出和诊断不足**：历史571 job的input_payload_json合计约809M字符（不是token数）；状态读取曾反复解析hash。真实输出截断却被宽松parser截内部对象，最初无法判根因，直到保留raw/finish_reason才得到证据。
6. **等价证明本身造成输入污染**：前轮proof/option_ids嵌进本轮选项，模型复用旧编号被拒；v7通过投影分离修复，而不是放宽绑定。
7. **大量资产缺真正接线**：下游typed评估器、图、发布、报告存在；真实source→语义→风险→用户仍欠reader/知识包/provider/交互接线。工程迁移/测试通过不自动缩短最后一段业务集成。
8. **文档和配置漂移**：旧goal文件、项目AGENTS、旧handoff、main默认配置与隔离试验版本不同；每次接手都可能走错代际。
9. **来源同名文件问题仍需明确**：9月11日发现用户DM与当前SDV版本hash不同。cell内容比对未发现差异，但隐藏/筛选/范围变动影响“冻结来源相同”的说法；不是这次能静默换掉的细节。

### 13.3 本Agent的工作方式也造成了摩擦（分析与自我纠偏）

- 太多精力消耗在局部合同、提示版本、孤立小样本反复裁决；这些修复有必要，但没有及时把已可靠的能力接到一条用户可见真实纵向流程。不能继续让所有非关键域的字段成为AE/MH价值验证的无限前置条件。
- 保守阻断防住错误接受，却尚未充分形成“哪些能力已可运行、哪些因证据不足受限”的产品路径。结果容易变成系统内部长时间等待，而用户仍看不到价值。
- 独立审阅和真实模型长任务多，输出往往结束后才收集，导致等待期间缺少可用进度；本线程也发送了过多重复“仍在等待”消息，与用户静默/token saving偏好不佳。以后用实际状态变化更新，并遵守宿主更高优先级通信要求。
- 每次批次有测试/文档提交，但完整阶段未闭合。接任者应围绕阶段验收收束，不把“提交新版本/下一安全动作”当终点；用户没有叫停时继续处理完成回执和下一依赖。
- 有些“审阅指出问题”其实前提不成立，例如已撤回R2。必须回到源码和调用链验证，不能因review语气确定就扩大改动。
- 原始raw诊断应更早加入，避免在模型输出形状上凭解析后对象猜测。以后先分清传输、截断、schema、证据、真实语义不确定，再决定重试/修改。

### 13.4 建议的改进，不擅自替用户改范围

- 保持设计v2/计划v3，优先MG AE/MH纵切。可以设计按能力/依赖闭合的受限运行，使无关域不拖住已验证域；但这是需要源追踪、工程测试与明确UI限制的实现任务，不能直接绕过当前全批facts preflight。
- 模型输入采用内容寻址冻结证据及必要切片，避免每job重传全文/前轮证明；输出以最小结构化内容为主，解释和证据通过稳定引用保留，减少截断。不得以压缩名义丢掉关键语义/反证。
- 修复已有队列/回执，不再创建平行task runtime；每次新版本明确affected work units、旧成功证据复用规则和接受版本。
- 独立review聚焦真实未解决判断及变更消费者；一个必要review起步，不为了流程凑多个节点。长期等待可并行做真正独立、不影响冻结artifact的工作。
- 整理当前文档中的失效声明，保持一份当前计划和一个handoff入口；历史记录保留但清楚标历史。
- 定期清理纯重复源码冻结副本/缓存前，确认对应Git提交、review及receipts完整且不再被活跃审阅引用；先做清单，不能把ignored数据库当缓存。

这些是接管建议，尚未实施；不是授权改写医学事实或缩减五项目/三模式目标。

## 14. 接任Agent的详细行动顺序与验收信号

### 步骤0：接收授权、重新锚定

读当前全局AGENTS、本handoff、设计v2、task PRD/implement；检查Git和ignored证据都在。不要重建A/B，不读废止门序找旧约束。若用户只是让你审阅交接，不自行启模型；若已明确继续构建，就持续执行，不再次询问已授权的常规工作。

核实当前goal仍未完成、任务in_progress、原MG持久pause、8911和本项目进程。保留前次失败和原数据。记录机制选择到现有plan：必要的独立工程review，及有明确收益时的执行节点；不是重新造管理层。

### 步骤1：收束v7独立工程审阅

- 读取`current-options-20260908`的冻结1ce29f9、prompt和route manifest；确认只是用户中止，不是模型失败。
- 查ZCode已有会话/receipt；兼容可恢复则原会话继续，实际型号/effort按当前全局政策。不存在可恢复会话则新鲜上下文review相同冻结artifact，并记明上下文/模型独立性限制。
- 审阅重点：历史proof排除不丢硬约束/原证据；当前option_id生成和验证一致；primary/verifier交换不改变投影；旧prompt复验兼容；新version名单完整。
- 只修实际发现。已有561回归和真实2字段证据可复用；源码/合同变了才重测受影响集合和对应真实输入。
- 验收信号：真实非空报告、可定位结论、与冻结提交绑定、问题逐项主线程判断；PENDING/启动成功不算。

### 步骤2：先处理来源与正式接线的前置事实

- 核对第8节DM/SDV来源差异、当前staging manifest、隐藏/过滤/命名范围coverage；不让同名文件自动替代。必要时建立新SourceRevision和兼容复用证明。
- 检查正式`_r7_admission_mapping_pipeline`与隔离flags/prompt/policy差异；工具factory虽已存在，也不代表当前正式裁决启用。
- 新配置启用前用独立runtime验证确认/草稿/receipt跨代、用户已答内容不丢、任务不会重新生成全首轮或重复代。不要从字面复制flags后直接放正式队列。
- 检查readonly状态接口无创建副作用；旧助手`run_mapping_reconciliation.py`会wake worker并调用adjudicate_draft，不是状态查询。
- 验收信号：通过产品组合根创建的任务确为期望provider/prompt/来源，旧成功和退休g02保留，输出能被当前confirm/receipt消费者接受。

### 步骤3：有界恢复正确MG未解决工作

- 先完整一致备份AI库及相关mapping/store/artifact引用；参考既存`recovery/20260906-before-queue-repair.sqlite3`，使用SQLite backup等一致性方式，不在活跃WAL时只拷主文件。
- 清点571任务：首轮成功不重跑；87退休重复g02不恢复；旧running按lease判断，不改SQL伪状态。
- 使用repository pause/resume/claim/retry_terminal/retire接口和当前版本化pipeline；新prompt语义变更建受影响的新工作单元，不把新prompt塞旧job。
- 列出哪些旧7/9等局部证据能合法复用、哪些需要新双路；不能人工合并成“9/9全通过”。
- 模型独立补读/裁决；对工程失败按原因修复，对真实语义分歧保留能力限制。只有额外医学背景确能消除歧义才问用户，不派696个确认问题。
- 验收信号：当前源/字段范围覆盖闭合、双路完成、真实引用和必要依赖一致、无默认主模型偏置、确认receipt可重放。

### 步骤4：正确facts与P2收束

- 通过正式mapping确认/激活和全批preflight生成facts；不能手写字段意义或放宽治疗身份等阻断。
- 比较manifest/计数，重开facts，选择至少几个相距较远表做exact-cell round-trip；日志只保留结果/定位，不输出患者原值。
- 补混合PDF/Word图表/脚注等coverage和工具挑战；标准lookup绑定项目版本/冻结来源。mapping阶段不越权生成CTCAE等级和风险。
- 用第二异构项目做有界反过拟合挑战，不先并发跑五个全量。
- 若决定按已闭合能力先行，先明确并验证partial facts/依赖范围/不可评估投影的产品合同；不能擅改既有全批零写入原则。
- 阶段复盘从用户视角说明现在能自动完成什么、还缺什么，不以测试数或模型高置信代替真实能力。

### 步骤5：P3正确MG AE/MH纵向闭环

1. 将当前fact-set明确读入Subject/Site/Event身份和SemanticRecordSet，来源/时间/单位可回查。
2. 产品harness从当前方案/IB/eCRF等生成带版本的知识控制点，不由Codex填医学规则。
3. MiniMax独立发现AE/MH线索，GLM盲核对，双方能够工具化查原记录、反证和替代解释；候选/原记录严格区分。
4. 现有AE/MH评估器消费真实typed输入；图节点推进、coverage/QC、稳定风险身份和生命周期。
5. 真实publication provider输出同版本研究/中心看板、旅程和来源，不借synthetic provider填空。
6. Query依据/发现/核实事项可编辑、保存、筛选、导出草稿；不发送。
7. ego(lite)以医学监察员角色操作研究风险→中心/受试者→访视/事件→原记录/条款→Query，检查全宽时间轴、真实数值/日期、分母、缺口、返回上下文。
8. 记录工程、真实模型、来源、浏览器和用户五层证据；明确未处理域不可评估。

### 步骤6：P4–P6连续完成，不缩水

- P4按资料适用性接CM/IP/背景治疗、PD/入排/访视、疗效、安全/CTCAE、跨域与聚合；标准版本和证据依赖固定。兼容双快照新增/修改/消失/不可比，以及风险/Query变化对照。
- P5三模式和报告审阅用户入口；其余四研究逐个真实全量，有兼容快照时做增量；五项目共同验收清单记录来源、覆盖、风险、看板/个例/Query/报告和模式。
- P6真实备份恢复、一键启动/停止、持久暂停重启、本地通知按计划核验、性能/调用/存储基线、阶段清理；用户最终验收状态真实记录。
- 只有所有要求实际完成才可标goal complete。若只剩用户业务选择，呈现具体可审结果再问，不用一串工程问题推回用户。

## 15. 交接文件、清理与转移注意事项

### 15.1 本次交接交付

- 本文：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/HANDOFF_MEDICAL_MONITORING_20260911.md`。
- [current-goal.json](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/handoff-evidence-20260911/current-goal.json>)：get_goal原始返回，目标全文与状态。
- [current-state.json](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/handoff-evidence-20260911/current-state.json>)：交接时Git/任务/队列/隔离结果/端口及权威文件摘要，不含凭据和患者行。
- [mg-source-comparison.json](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/handoff-evidence-20260911/mg-source-comparison.json>)：两个同名文件的只读ZIP/单元格/结构差异及限制。
- [validation.json](</Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/handoff-evidence-20260911/validation.json>)：本文链接、关键文件及目标原文一致性等交接校验。

历史handoff和plan不覆盖。本文件是今天接管入口；继续构建后将实质变化合并Trellis plan/journal/Git，避免同时维护多份“最新暂停点”。

### 15.2 同机交接与跨机转移

- 同机新Agent应直接打开指定产品根目录；当前协调cwd `Documents/AI Cache/Codex x Hermes`不是产品源码根，所有命令显式指定workdir。
- 跨机/新checkout不仅要Git，还要当前正确MG run、P2试验run、相关来源副本/注册/文档/Store/artifacts/备份和审阅回执；路径绑定可能需要受控迁移复验，不能批量文本替换hash/identity。
- provider密钥单独通过受控本机配置供新Agent使用，不放附件。本文没有打包临床数据或凭据，没有自动向另一个Agent/外部服务发送资料。
- 环境runtime依赖读取本机配置；仓库`.venv/bin/python`曾可用，接手当天核验。不要升级大量依赖或迁移数据库来“清理环境”。

### 15.3 清理的可做与不可做

可先列清单：已不再引用的测试cache、临时构建产物、可从Git精确重建且无活跃review引用的冻结源码副本。保留报告、receipt、prompt、route和版本关联后再处理。

不可一般清理：原始五项目、隔离真实来源/数据库/artifacts、失败模型输出、错配证据、备份、Codex会话/归档/状态库。历史约85GB只是旧记录中的规模，未重新计量也未获得本次删除授权。不要把“定期清理”当作删除所有ignored文件的许可。

## 16. 可复制给接任Agent的开场任务

> 接管 `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench` 中的医学监查子系统。先完整读取 `.trellis/workspace/宋旻恺/HANDOFF_MEDICAL_MONITORING_20260911.md`，尤其权威冲突、当前goal原文、P0–P6状态、第8节同名MG来源差异、第13节停滞原因及第14节行动顺序；再读当前设计v2、Trellis主任务PRD/implement与最新全局AGENTS。旧A/B不重做，旧C–F按v3承接，原父JSONL已删不声称恢复。核对文件系统、Git、ignored证据、正式队列pause与端口后，从未完成的v7独立审阅、来源选择/复用和正式组合根接线继续；不要重跑已完成首轮或恢复退休g02。产品MiniMax主+GLM盲核经裸API独立解释、补读和裁决，Codex/开发Agent不能替它们填医学语义。最终完成正确MG facts→AE/MH及反证→看板/旅程/来源→Query，再扩域/增量/报告/五项目和交付验证。用户不逐列核对、内部术语不外露、来源/数值/时间/覆盖必须真实。已获继续实施授权时持续工作，不以“继续推进”结束；真正决策/阻塞/完成才停，用户明确暂停则无损保存。

## 17. 本次交接自身的验证与限制

本次重新读取当前global AGENTS、设计/任务/历史handoff/review、get_goal、Git及相关源码；只读查询正式AI库和隔离结果，核对8911，比较两个MG同名文件的hash与工作簿部件。未启服务、未调用医学模型、未修改产品代码/原文件/运行库、未重新跑全部产品测试、未完成此前中止的独立审阅。

本文解释历史和下一步，不保证无遗漏的原始对话还原；对临床/来源完成的描述以明确证据范围为限。所有旧统计均标历史或限定批次，当前现场统计单列。新接任者必须根据当时文件系统检查漂移，不能因为handoff措辞完整就跳过验证。
