# 当前工程与GitHub复审
日期2026-09-22，基线a7217af080b96896bdc4cbc9317cb139e4386569。

## 结论
不宜在当前基础上直接继续全量医学运行并称“V5 P0全关闭”。主要风险在跨层完整性而非缺少更多框架：项目选择、冻结版本、决策回放、医学命题、真实来源、公开DTO都出现“局部改了、消费者仍旧”的问题。
本轮核实专家九项并补五类重点；优先恢复可相信的版本和证据，再连接用户工作链。原始资料浏览和UI建设不必等真实模型重跑。

## 证据等级与范围
- GitHub main与本地同a7217af；相对专家07b6a09仅HANDOFF_ROUND6文档变更。无开放PR、未见近期Actions；这不证明历史CI从未运行。
- 相对db5543e的167变更路径见evidence/changed-files.tsv，含生产/测试/文档/删除项。主要生产调用链做深入检查，其余做变更范围和继承验收登记；不声称逐行审阅整个历史仓库。
- 专家18探针是selected-source-logic转录，不能算真实模块/API测试。本轮evidence/review_actual_modules.py调用当前模块，九反例均复现；临时合成数据，无真实医学判断和远程调用。
- 九文件既有集中回归143 passed、18 warnings（evidence/regression-batch.log）；未跑全仓，不把历史96failures重报为当前实测。
- 查阅轮6报告并查看final_B_verdict_panel历史1920宽屏截图：流程门与资料准备状态重复、技术/审批外围项可见；截图早于后续修复，不能证明当前运行UI相同。本轮没有现场浏览器E2E/新真实模型全量。

## R01 · P0 · 多项目修复没有覆盖组合根消费者
证据：专家01；实际静态调用链。定位：[services/api/app/main.py:3778](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/services/api/app/main.py#L3778)。

问题：惰性provider仅覆盖部分freshness路径，setup仍get，adapter复制旧dict，mode固定SAR、domains取首个provider；冷启动无历史或新增第二项目可能失效/串线。

处理：统一请求作用域的project/result解析，所有消费者取同一不可变context；删除固定SAR/first-provider生产分支，不重建全局框架。 工作包：W01。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R02 · P0 · 人工文件角色决策未冻结进promotion回执
证据：专家02；promotion→verify→SourceRegistryService消费者静态核对。定位：[services/api/app/monitoring_document_authority_jobs.py:865](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/services/api/app/monitoring_document_authority_jobs.py#L865)。

问题：promotion传入用户选择，但receipt无决策版本，verify重放未传同一选择。前端promoted不等于正式文档可用；后续DocumentEvidenceResolver可拒绝。

处理：先冻结合法决策，promotion与verifier共用同一决策版本；旧回执显式兼容/不可重验状态，不使用最新选择覆盖历史。 工作包：W02。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R03 · P0 · 结果指针与冻结读不完整
证据：专家03；两个实际模块探针复现。定位：[packages/medical_monitoring/api/r7_product/facts_mode_outputs.py:479](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/api/r7_product/facts_mode_outputs.py#L479)。

问题：坏binding变{}后读legacy；显式目标缺失返回missing。public_findings/meta分别读active，旧token的输出还可能被新结果覆盖。

处理：结果句柄解析一次；行、meta、事实、来源同版本；坏/缺目标明确read_failed，legacy只允许显式历史迁移。 工作包：W01。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R04 · P0 · 命题方向相反仍能accepted
证据：专家04；实际adjudicate反例accepted=1。定位：[packages/medical_monitoring/analysis/ae_mh_cross_analysis.py:402](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/analysis/ae_mh_cross_analysis.py#L402)。

问题：共同EID/实体和positive词频、分级集合交集不足以确认方向、时间或分级配对。ALT升高与降低被接受，控制测试却通过。

处理：词频至多用于找潜在同一问题；接受需版本化命题、原值/时序/单位、支持与反证及独立核验闭合。 工作包：W04。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R05 · P1 · 公开Finding DTO丢失事件导航信息
证据：专家05；实际public_findings返回键验证＋UI读取链。定位：[packages/medical_monitoring/api/r7_product/facts_mode_outputs.py:333](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/api/r7_product/facts_mode_outputs.py#L333)。

问题：前端Workspace:1854与ProductLoop:1166消费anchor_event_refs；公开findings没有。内部mode DTO补了锚点不能自动传到此公开路径。

处理：单一公开Finding契约，typed schema→publication→API→normalize→列表/旅程/source均消费；partial/unbound明示。 工作包：W05。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R06 · P1 · 选择先落盘后校验，毒化重复resolve
证据：专家06；无效选择拒绝后仍持久化的实际探针。定位：[services/api/app/monitoring_document_authority_workflow.py:432](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/services/api/app/monitoring_document_authority_workflow.py#L432)。

问题：同角色新选覆盖，actor为角色名，固定tmp；缺项目校验/版本CAS。机器收敛后不同人工选择静默忽略。

处理：验证候选/批次/角色/项目后原子写版本；真实principal、幂等同选择、不同选择明确冲突，损坏不当空选择。 工作包：W02。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R07 · P1 · 被阻断的主文档仍被补充文档引用
证据：专家07；事务循环静态复核。定位：[services/api/app/monitoring_document_authority_jobs.py:1010](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/services/api/app/monitoring_document_authority_jobs.py#L1010)。

问题：blocked primary continue后后续supplement引用缺失entry_id_by_claim，可能KeyError回滚；没有有序依赖结果。

处理：先判定整批依赖及允许项，再按已知关系登记，缺主项补充项进入可解释等待，不捏造主登记。 工作包：W02。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R08 · P1 · 确认页面要求用户盲目背书且泄漏术语
证据：专家08；实际组件＋轮6历史截图/报告。定位：[frontend/src/features/medical-monitoring/MedicalMonitoringAdmissionWizard.jsx:86](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/frontend/src/features/medical-monitoring/MedicalMonitoringAdmissionWizard.jsx#L86)。

问题：按钮我已核对直接提交，展示role/content_status/use_status，没有差异原文/预期/影响。异步batch切换与失败状态须合同验证。

处理：解释型文档差异卡、只允许确认规定警告、实际动作反馈；generation/request隔离，旧响应不覆新文件批。 工作包：W02。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R09 · P1 · 域覆盖、代价与工作清单仍是假完整
证据：专家09；原函数/前端静态核对。定位：[packages/medical_monitoring/analysis/ae_mh_cross_analysis.py:67](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/analysis/ae_mh_cross_analysis.py#L67)。

问题：固定AE/MH/CM/EX2/4/5/7及至少两域，单域排除和异构EX/LB覆盖缺口；按人反复全表hash；UI map完整卡片、双cohort术语与两套风险视图。

处理：语义域适用清单、全人/域覆盖与无发现状态、按源版本缓存；中文列表详情、去重复风险真相。 工作包：W03/W04/W05。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R10 · P0 · 方案画像违背反过拟合和固定标准合同
证据：本轮新增；两实际模块探针＋完整函数核对。定位：[packages/medical_monitoring/analysis/protocol_profile.py:29](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/analysis/protocol_profile.py#L29)。

问题：疾病名→预置药物风险；docx权重3且CTCAE/MedDRA按频次/较大版本投票；扫描未登记candidate目录，PDF限60页却无完整覆盖证明。unknown可被风险关键词掩盖；workspace缓存不绑定知识代。

处理：移除医学启发式作为权威输出；复用既有资料工具，由独立harness从已登记角色/版本提取知识。显式标准、适用时间、证据与未知；旧画像不当新代可复用证据。 工作包：W03。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R11 · P0 · 事实快照和来源凭证尚非真实冻结
证据：本轮新增；两实际模块探针＋完整get_packet/_locator核对。定位：[packages/medical_monitoring/projections/facts_publication.py:413](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/projections/facts_publication.py#L413)。

问题：坏manifest会重新扫描并吸入新LB；get_packet忽略run/cutoff，任意历史snapshot标签套当前事实。source hash为表名hash而非字节，run固定、若干凭证占位。

处理：从物化阶段冻结真实manifest与来源定位，查询只读；历史snapshot必须存在且匹配；缓存内容/版本键。移除默认假凭证，明确旧结果证据等级。 工作包：W01/W03。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R12 · P1 · 事实投影绕过已接受语义，事件被风险化
证据：本轮新增；投影_build及定义静态核对。定位：[packages/medical_monitoring/projections/facts_publication.py:494](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/packages/medical_monitoring/projections/facts_publication.py#L494)。

问题：依SUBJID、表名/列签名、日期后缀推断；治疗域按EX映射；_add_event每事件创建risk。mode把critical/medium译重度/中度，混淆优先级/AE强度。

处理：已接受mapping作为消费者输入；普通事件/观察与分析发现分离；真实治疗暴露与随机化分开；分级六维字段独立。 工作包：W03/W05。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R13 · P1 · 收尾仍依赖临时脚本与/tmp哨兵
证据：继承WP5/6；脚本入口及存储路径静态复核。定位：[scripts/dualvlm_finalize.py:414](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/scripts/dualvlm_finalize.py#L414)。

问题：scoped CAS已有改善，但/tmp丢失/并发/重启、脚本绕API写作业和wake仍需生产持久闭环。现有804发布不证明重复恢复可靠。

处理：复用现有job repository与图收尾状态，绑定project/input/policy/artifact，atomic发布；保留脚本受控兼容后退出主路径。 工作包：W04/W07。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## R14 · P1 · 文档与goal路由漂移，验收历史表述过强
证据：新旧goal/设计/当前交接与git比对。定位：[scripts/test_round6/HANDOFF_ROUND6.md:7](https://github.com/smkzw/kz-medical-monitoring-workbench/blob/a7217af080b96896bdc4cbc9317cb139e4386569/scripts/test_round6/HANDOFF_ROUND6.md#L7)。

问题：当前goal仍paused MiniMax/GLM；旧goal文件是deepseek/本地；设计不同段落不同路由，轮6声称mimo/deepseek。V5全部落地与P0实测反例冲突，96失败未完成对账。

处理：W00脱敏读取当前有效绑定/请求与观测回执，形成单一冻结路线；保留历史但不恢复旧路线。按证据等级重新立账，不能删除违规EX问题假装完成。 工作包：W00/W07。运行影响为代码/限定探针推断，未执行的实际API/浏览器路径仍列入验收。

## 已有有效成果应保留
流式SSE终止/错误/截断保护、reasoning隔离、observed_response_model独立列、全表类型保留digest、0/False处理、来源字节hash检查、未知域不默认PD、事件结束日期、原始记录号、scoped收尾防重、真实双路与定向核实历史均有可复用资产。它们不是全部产品完成；不因新增问题整体推倒。

## 停滞原因与取舍
1. 验证停在helper/伪造类型fixture，未连接builder→公开API→UI→来源；造成反复局部P0补丁。
2. 版本/角色/路由规则分散在main、profile、receipt、projection和临时脚本，同一合同有多个真相。
3. 一边修改输入/模型/策略一边继续旧批次，成功数、候选数、覆盖数和可发布数混用；真实推理耗时被重复试验放大。
4. 用户机械确认负担由工程不确定性产生，新增按钮不等于降低负担。
5. 全量模型结果已出现，但完整资料→新项目→facts→用户路径仍未证明；不能拿旧804条替代新完整项目验收。

选择：已有架构内收口context、decision和公开Finding三个关键契约；替换知识启发式与词频接受，不建立新的通用平台。工作包按业务链集中修改验证；真实全量只在输入与策略冻结后运行。

## 未决但不阻止规划交付
新路线有效绑定与授权观测需W00读取实际配置/回执，当前仅有交接记载；专家不授权回切。文档未齐先医学分析的边界未决定，默认不扩；当前功能继续按可用证据范围实现。真实验收、性能和历史96失败分类均未完成。

