# 医学监查工程接管审阅（2026-09-06阶段结果）

## 本轮合同

用户要求先完整工程 review、必要测试、新设计、新计划与新 goal prompt，再设置 goal 并连续实施。本轮主线程直接执行及原生只读子代理；未调用外部执行/会商机制。本文记录工程审阅证据和缺口，不冒称全组件动态验证或临床验收。新设计、计划和goal prompt已单独成文，见文末。

- 基线：`d6a1a20`；首次 `git status --short` 无输出，工作区干净。
- 旧 goal 由工具核实为 paused；尚未更新或设置 goal，不把旧目标标成完成。
- 原文件只读、隔离输出、医学写作不动。暂停的真实模型队列不自动恢复。保留所有历史错配取证数据。
- 当前新请求允许必要测试；旧 G0–G8 不恢复。浏览器只用 ego(lite)，不启动真实队列来做页面检查。

## 审阅计划

1. [已做首轮] 对照当前文档、用户修订、handoff、Git、Trellis、运行库建立真实进展与需求差异；原已删对话无法逐条恢复。
2. [已做首轮] 主线程检查admission、文档解析、模型输出、双路裁决、facts、队列及下游；原生Plato完成前端静态审阅，Epicurus容量失败。逐组件动态验证仍未完成。
3. [已做聚焦] 行为测试、身份/PDF最小复现、合成产品入口浏览器检查及官方医学依据；完整真实医学E2E待后续阶段。
4. [已成文] 汇总问题并形成完整新设计、计划与goal prompt；没有假称用户已验收。
5. [实施中/goal受阻] 三文档齐备后尝试goal更新，工具被旧未完成goal阻挡；已实施第一批正确性修复，原目标不伪报complete。

## 初步已核实观察（不是全部 review 结论）

- v1.2 修订4仍是 ensemble_size=1；v2.0 阶段C仍含用户确认关键 mapping。当前 `.trellis/spec/medical-monitoring-engineering.md` 与后续用户指令已要求 MiniMax主分析+GLM全量盲核对、自主裁决、最少用户问题。新设计需消除权威文档漂移。
- `admission/pipeline.py:145–150` 使用双向 startswith 判研究身份。只执行纯函数，以合成标识验证 `TRIAL-01` 对 `TRIAL-010`、`TRIAL-01` 对 `T` 都输出 matched。此规则不能证明研究一致，是需修正的串研究风险；尚未改代码。
- `mapping_confirmation.py:847` 后第二轮分歧固定选 primary_item；没有显式 user_decision_required 且 rationale非问句便可 primary_retained。需核实独立证据裁决是否足够，不能将少打扰用户等价于默认主模型正确。
- `mapping_pipeline.py:1131` 选择最高已建代；仅等待 active 的补丁没有处理此前误建g02、局部失败全批重放和受控暂停。`test_mm_c3_mapping_bridge.py:60` 当前只测 helper布尔结果，未验证真实调度调用链。
- 巨型新文件：monitoring_ai_service.py 8601行，monitoring_ai_repository.py 2454行，document_authority.py 2034行，mapping_pipeline.py 1547行。B迁移后仍有明显单一职责和层次债务，不应机械拆分掩盖根因。

## 初期检查记录（均已终止或完成，非当前在途）

- 原生审阅：Plato `01a07247-37a0-7a62-aca4-c6c88fb68718`；Epicurus `01a07247-37e3-7d11-a64c-5480f03e4b7e`。均只读，不允许再派下级/服务/真实模型。
- 终端50198：合成身份复现已得到两个matched，后续运行43项mapping聚焦测试；等待结果。
- 终端97844：端口/进程/SQLite摘要与同一聚焦测试串行检查尚未输出；可能前置lsof慢，需核实，不据此声称端口/进程/DB已确认。
- 未写入产品源码或真实运行库；未声称浏览器、五项目或临床验收完成。

## 2026-09-06 补充验证

- 43项 mapping bridge/confirmation、182项结构/关系/双路/证据/materialization、31项产品data admission测试通过；合计256项，不代表临床完成。
- Vite build成功，输出到 `/tmp/mm-review-20260906.FDz0Zv/frontend-dist`；主JS约1977.91kB、gzip573.30kB，CSS470.49kB。存在bundle大小告警，不能为消警删功能。
- SQLite只读统计与handoff吻合：首轮两路各151 completed；聚焦MiniMax7 completed、159 queued、2 running和6 failed；GLM4 completed、80 queued、1 running和2 failed。共571 job，其 input_payload_json 合计809,438,238字符，最大2,432,937字符。不是API token数或文件字节数。
- `list_jobs()`（monitoring_ai_repository.py:429）SELECT *，每行经 `_validated_job_inputs` (:2242) 解析及重新计算payload hash。轮询状态加载大量重复证据；应分开轻量状态投影与执行/接受时深校验，不得简单关闭接受校验。
- lsof因APFS stat卡住被取消（只取消自己的诊断），不能用其不输出证明停止。Python TCP connect_ex(127.0.0.1:8911)=61（连接拒绝）。未启动8911。
- PDF最小合成实验：1页内有文字页眉+大面积嵌入图片，候选解析返回1文字块、ocr_required_pages=[]；`monitoring_document_candidates.py:573`只检查文字块是否为空。该实验不含真实患者材料，证明混合页面检测缺口，不证明实际某一PDF已漏掉内容。
- `writing_reference_docx.py:extract_docx_sections`只遍历body直接p/tbl且返回page_count=1；监查调用它，但医学写作文件不得修改。监查需要独立的容器/图形/脚注覆盖检查及按需提取，不把逻辑页冒充物理页。
- 主线程使用ego(lite)（技能已完整读）创建空间1，产品本体合成profile、隔离runtime `/tmp/mm-review-20260906.FDz0Zv`，后端18911/前端15174。首次误传布尔0失败，改为文档要求false后启动成功。真实runtime从未接入。
- 浏览器1728×963已实际打开监查首页：两个近似起点“开始一次监查/开始数据接入”，技术说明“服务端范围与历史”，留白较多；“医学监查首页”点击跳往项目总览并返回HTTP404（本合成配置下）。截图 `/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/ego-browser-shot-34795-1.png` 已查看。并非完整Journey或真实E2E验收。

## 原生前端审阅与主线程复核

Plato已完成并关闭；未改文件，未进行浏览器验收。入口链为App→RouteOutlet→Page→Workspace→ProductLoop；Workspace仍含旧run_ref兼容读取。下列核心代码主线程已复核：

| 级别/问题 | 证据（frontend/src/features/medical-monitoring 下省略前缀） | 用户影响与方案 |
|---|---|---|
| P1 结构预览回调触发重挂载循环 | AdmissionWizard.jsx:679 onAdmitted；ProductLoop.jsx:1308条件卸载；WizardState.mjs:236恢复reading | 可能反复读取、丢操作上下文；预览只更新局部，facts完成再通知父层；挂载期交互回归，不能只测源码字符串 |
| P1 真实结果发布未接通 | main.py:3560/3708只为synthetic注入provider；publication_providers.py:115空provider报错 | 资料能进入不等于风险可看；补单一真实facts→域→QC→publication通路 |
| P1 趋势数值失真 | Workspace.jsx:1739 value×8裁剪14–92% | 高值同高、负值/零/缺失混淆；真实数值域/时间域、单位/参考区间、缺失留空 |
| P1 零变化误报首次 | Workspace.jsx:1403 liveContinuity要求计数>0 | 用比较状态而非非零数量判断是否已比较 |
| P1 前台触发发布，失败无重试 | ProductLoop.jsx:845 | 后台幂等整理结果，前台只展示/显式重试 |
| P1 Query只有文本 | Workspace.jsx:1480；旧API exportRiskSnapshot未进新链 | 补版本绑定的核查问题编辑、筛选、保存、草稿导出；不加外部发送/回复管理 |
| P2 访视轴不适配宽屏 | JourneyTimeline.mjs:49默认8px/日；ProductLoop固定zoomLevel=0 | 默认fit全周期，允许局部放大，真实日期不吸附名义访视 |
| P2 人为留白/自动跳页 | workspace.css:2061中心区加160px；ProductLoop.jsx:1117风险直接跳旅程 | 同页证据抽屉+显式进入旅程，删截图专用空白 |
| P2 未知被补为已核对 | AdmissionWizard.jsx:340；Workspace.jsx:1804固定定位成功 | 无计数显示未知；实际定位成功才显示完成 |

### 组件分工与处置

- RouteOutlet/Page/Workspace：保留外壳，拆清正常入口与兼容入口，避免双状态控制。
- ProductLoop：启动/历史/进度/结果/导航，保留；后台承担发布权威。
- AdmissionWizard：上传/文档/结构/双模型/疑点/整理，保留但合并用户动作到“添加资料”。
- WizardView/HistoryDrawer/Workbar：次级配置与历史，减少重复确认。
- ProgressSurface/ProgressPanelView：需恢复持久暂停/继续，不将内部任务失败转用户核对。
- OverviewView/SubjectFlowSection/ContinuityPanel：研究/中心看板、流向、变化，保留并修零变化语义。
- SubjectWorkspaceView/DomainTracks/DomainIcon/JourneyDrawer/EvidenceView：保留八类轨道、日期待定、来源；补忠实趋势与宽屏适配。
- BatchPanel、FieldMappingPanel、DailyRunPanel、ProtocolPreparationPanel、RuleReleasePanel及Daily*、Assurance*：旧入口资产，先列消费者，不扩建；不得误删Safety/PV仍使用的RiskChecklist。
- 新增真正Query工作区、报告审阅入口和模式输出领取；研究文件上传不等于报告审阅。

## 医学控制点的外部依据（只作为新设计依据，不替代项目方案）

- ICH E6(R3) 2025-01-06正式版：优先影响参与者保护和结果可靠性的关键数据/过程；风险相称的中央监查。设计推论：先展示关键风险与覆盖缺口，而非工程日志。来源 https://database.ich.org/sites/default/files/ICH_E6(R3)_Step4_FinalGuideline_2025_0106.pdf 。
- NCI CTCAE资源页同时提供v5与v6，且将AE记录/分级与因果性区分。设计推论：匹配项目规定版本、条款、单位和适用条件；不自动升级字典或把分级当因果性。来源 https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events （本轮已打开）。
- 这些支持通用产品边界，不构成五研究的医学结论；新系统不能承诺绝对无幻觉，只能报告证据覆盖与未能排除的解释。

## 下游架构审阅与保留测试缺口

- graph/engine.py提供通用节点执行及typed结果；不是医学理解器。aemh_evaluation.py消费调用者提供的SemanticRecordSet、方案边界与事件匹配策略；aemh_types.py区分来源事实与AI断言、强度与严重性。这些边界应复用，但尚无正确MG事实至真实模型风险再至发布的完成证据。
- d07_safety、ensemble及reports/report_review.py保有结构化评估、独立核对、报告claim/证据覆盖资产；大量接口是离线输入或注入worker结果。mode_output_core.py能生成模式输出并不等价于真实用户入口已接通。应保留合同、补真实输入和来源链，不用synthetic provider冒充上线。
- `git show --stat 87e2db9 -- '*test*aemh*' '*test*ensemble*'`显示迁移清理删除4份行为测试，共3667行：AE/MH slice1515、ensemble contract558、ensemble runtime1306、match-history public288。当前tracked测试未找到这些替代，也未找到evaluate_aemh直接调用；D07 artifact generator测试明确不导入D07 runtime。这是覆盖缺口，不能由接入链256项通过替代。下一步按行为合同恢复最小有用回归，不恢复废止的门序/矩阵。
- 原生下游审阅Epicurus因模型capacity失败、已关闭；此节由主线程代码检查完成，不声称独立复核。

## 第一批实施及验证（2026-09-06）

1. admission/pipeline.py：研究标识从任意前缀匹配改为规范化精确匹配，只移除明确环境括号后缀PROD/PRODUCTION/UAT/TEST/DEV；短标识、相似编号、未声明后缀、混合研究拒绝，无身份保持未知。schema升级v2。新增11项合成测试；未改真实registry、candidate、mapping或facts。
2. admission/mapping_confirmation.py：二轮持续分歧且不需医学补充时保持内部blocked，不改字段、不写已解决receipt、不增加用户问题。仅当前证据的adjudicated_mapping/escalated可用于确认，旧primary_retained和旧证据receipt保留为历史但不再自动放行。这里是阻止错误完成的修复，不是宣称已完成自主补证据裁决；P2还需工具化复核闭环。
3. 回归命令：`.venv/bin/python -m pytest tests/test_mm_c3_mapping_confirmation.py tests/test_mm_c3_mapping_bridge.py tests/test_mm_study_identity.py tests/test_medical_monitoring_r7_data_admission.py -q`，87 passed，30项既有FastAPI on_event弃用warning。与前述256存在重叠，不能相加冒充独立测试数。初次误用系统python无pytest，改回仓库venv；未安装依赖。
4. 临时后端18911已优雅退出，前端15174已停止，ego空间1关闭。无真实模型调用，无真实库写入，无清理历史文件；本轮没有启动8911。截图路径后来被导入页面截图覆盖，首页判断来自覆盖前已查看图像，不把当前文件当不可变首页证据。

## 新文档、当前状态与下一步

- 完整新设计：`.trellis/spec/medical-monitoring-system-design-v2.md`。
- 实施计划v3：`.trellis/tasks/09-06-mm-product-rebaseline/implement.md`；PRD同目录；新目标全文：`goal-prompt.md`。
- 已按用户要求在三文档成文后尝试create_goal，应用返回“cannot create a new goal because this thread has an unfinished goal; complete the existing goal first”。旧goal仍paused且确未完成，不能误标complete。已请用户在Goal界面替换；没有篡改受保护runtime状态。文档目标已更新，应用goal未更新，两者不得混称。
- P1仅身份和保守裁决完成第一批修复；旧receipt重新评估、用户已回答问题跨代继承、暂停/选择性重试及误建g02恢复仍需行为验证。没有恢复真实队列。
- 最终补充了保存用户回答不被覆盖的三组回归：聚焦合计90 passed；相邻九文件182 passed，两组不重叠共272。87项是此前中间结果。所有diff通过`git diff --check`，尚未提交git；无未识别的初始脏文件。
- 下一安全动作：补队列集成测试，验证混合失败/在途状态不增代，设计持久暂停和分片恢复；随后前端数值/零增量/导入重挂载，P2补证据工具，再P3正确MG风险→来源→Query真实闭环。持续实施不等于可越过尚未验证的真实数据发布边界。
