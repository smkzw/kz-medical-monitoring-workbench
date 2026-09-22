# 跨层实施合同（字段含义优先，复用现有类型）
本文件补足W01–W05交接面。优先扩现有类型/serializer，不要求创建同名新class。字段改变必须同时更新生产者、缓存、持久版本、API和前端，不再靠注释称已接通。

## 1. 结果读取Context
必须解析并校验的内容：project_ref、run_ref、snapshot_ref、cutoff_ref、fact_manifest_ref/hash、mapping_version、knowledge_version、analysis_policy_version、finding_artifact_ref/hash、source revision集合、schema_version。
解析顺序：token→持久publication→该版本manifest/artifact→一次校验→对象传下游。latest选择在最外层；下游不读active、不取第一provider、不默认SAR。row/meta/source同时使用同一个context。
缓存同一结果的只读对象，可按内容摘要复用；别用变动全目录max mtime。创建manifest和迁移属于写入/物化任务，不在GET解析执行。
错误：token未知、项目不符、schema不支持、绑定损坏、目标缺失、hash不符、来源不可达，保留明确码与用户文案；不能构造另一份成功结果。
已确认旧schema可只读迁移到显式legacy context；无证明则unverified，不能给占位版本/日期/验收hash。

## 2. DocumentDecision与PromotionReceipt
Decision最少语义：decision_id、revision、project_id、batch_id、candidate_manifest_hash、expected_prior_revision、actor_principal、timestamp、role selections（选定candidate或明确missing）、具体content-warning check codes及适用范围。
写入顺序：验证调用身份及项目→验证冻结batch/候选/合法角色/告警规则→CAS→原子持久化→推进。重复同决定返回原回执；不同决定基于旧revision冲突，不静默覆盖。
Receipt绑定decision_id/revision/hash及原模型job/output/source身份，登记主/补充关系。verify从receipt重放该决定，不能读取“最新决定”。旧receipt若没有决定，不伪造人工已确认记录。
missing是依赖未满足，不是替代文件；明确字段含义不再加角色同义词兜底。操作者是用户身份，不是medical_manager角色名。

## 3. PublicFinding与页面状态
复用已有finding_id/display_seq，要求：
- identity：同一result context、project/subject/site，稳定finding_id；
- medical：可读title/完整text、kind、监查priority、独立clinical severity/seriousness/expectedness/causality（缺失明确unknown）；
- claim：claim_id、side、kind、完整text、逐项evidence targets；同文合并保留来源元组，不压成独立集合丢关系；
- navigation：anchor_event_refs（唯一规范名称，若保留verified_event_refs需明确转换位置）、source locator targets、anchor_status及reason、解析总数/未解析数；不能把只解析一半写bound；
- state：finding核实状态与整个analysis读取/覆盖状态分开，未知enum显式显示合同缺口。

公开envelope中findings与findings_meta来自同一读：
read_state区分未运行/处理中/失败或不可读/完成零发现/完成有发现；coverage有适用人数与记录、已完成、缺口、失败、不适用及原因。
API可复用query_findings_meta名称，但ProductLoop必须normalize并传Workspace。空态以read_state/coverage驱动，不依据length独自显示“没有问题”。
每个claim点击目标要能解析同context下的event/source；不存在明确不可达，不默认首AE。窗口调整包含被定位事件，返回恢复用户原筛选/窗。

## 4. 医学知识与命题
Knowledge：研究文档角色+版本+内容hash+条款位置、适用中心/人群/时段、标准版本、控制点及引用、每维unknown/coverage。文件名/后缀/词频不是authority。
Clinical proposition至少表达：对象/事件/概念、时段、方向/否定、值及单位/参考/baseline、等级条件、依据与反证、规则版本；不是要求所有发现填不适用字段，不适用应显式解释。
配对是检索候选，accepted是验证结论，二者不共用词频布尔。合法零发现附适用范围及反证扫描回执；不可评估不自动制造风险/用户确认。
输出/工具记录和模型身份按现有schema版本化，旧批次不无提示换策略。

## 5. 最少相邻验证触发
- Context/manifest/缓存/发布变化：旧token＋双项目＋source＋mode/continuity读取。
- Decision/receipt变化：实际registry verifier＋DocumentEvidenceResolver＋mapping消费＋接入UI。
- Finding/enum/导航变化：公开API envelope＋前端normalize＋工作清单/旅程/来源空态。
- Gateway/模型身份变化：视觉与非视觉、SSE终态、回放与相邻共享消费者。
这些组一次完成关联修复后集中测，不逐字段跑；无需碰不相干全仓套件。

