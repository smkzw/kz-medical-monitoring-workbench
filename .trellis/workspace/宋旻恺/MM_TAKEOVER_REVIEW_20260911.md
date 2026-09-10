# 医学监查子系统接管工程 Review（2026-09-11）

- 审阅者：ZCode 接管会话（GLM-5.3 主线程 + 2 只读探查子代理 + 1 独立审阅 worker 运行中）
- 锚定证据：Git HEAD db5543e（产品逻辑 1ce29f9）；正式 MG 库 paused=1（2026-09-06T00:30:13Z）；571 jobs / 321 候选 / 87 退休 g02；8911 未监听；710 项聚焦回归全部通过（18.7s，日志 runs/mm_takeover_review_20260911/focused_regression_20260911.log）。
- 本报告性质：工程审阅与行动计划输入；不是临床验收，不改变任何医学语义。

## 1. 现场核实结论

交接文档（HANDOFF_MEDICAL_MONITORING_20260911.md）全部关键声明经独立复核**属实**：Git/运行库/端口/队列状态一致；710 项回归通过（超出交接所述 561 项集合，因本批加了 repository/worker/api/bridge 四个文件）；v7 隔离 2 字段一致的证据链完整。交接质量高，无发现陈述失实。

## 2. 工程问题矩阵

按严重性排序。P0=阻断真实业务闭环；P1=显著工程债/风险；P2=清理与一致性。

### P0-1 正式组合根未启用新裁决合同
- 定位：services/api/app/main.py:3629-3638。`AdmissionMappingPipeline(...)` 未传 `adjudication_tool_reads / explicit_mapping_dependencies / visual_tool_reads / role_equivalence` 四标志，默认全 False（mapping_pipeline.py:278-281），对应 prompt 停在 v5/v3 旧合同（mapping_pipeline.py:321-335）。
- 影响：正式队列即使恢复，跑的也是旧语义合同；隔离试验的全部 v7 修复（严格解析、依赖声明、等价证书、前轮证明分离）对正式 MG 无效。
- 方案：四标志置 True 启用 tools-v7（v12/v10 prompt）。启用顺序：(a) v7 独立审阅收束；(b) 独立 runtime 验证确认/草稿/回执跨代不丢、不重生成首轮、不复活退休 g02；(c) 用 repository 接口只对未解决分片提交新工作单元。已确认标志间有依赖校验（v7 需逐级开启，构造器已强制）。

### P0-2 真实 facts → AE/MH → 看板 → Query 全链未接通（P3 核心）
- 现状：MG 正确来源链停在"首轮 1495 字段双路提交、696 分歧未复核"；facts_generated=false；下游 AE/MH 评估器、图执行、风险/投影/Query 全部是有离线合同的资产，无真实数据流。
- 方案：按交接 §14 步骤 3→4→5 顺序：有界恢复 MG 未解决分片 → 确认/激活 → 全批 preflight 物化 facts → SemanticRecordSet → AE/MH 双模型发现+反证 → 真实 publication → ego 验收。不缩减范围，但按"能力/依赖闭合的受限运行"组织，避免无关域字段阻塞 AE/MH 价值验证。

### P0-3 Query/报告工作区实际不存在
- 定位：交接 §6.4 声称"Query/报告工作区 | 真实编辑/保存/导出闭环仍需接通"，探查证实**前端无任何独立 Query（疑问单）或报告组件**——最接近的只有 Safety/PV 门禁复用的 MedicalMonitoringRiskChecklist.jsx（487 行，App.jsx:10943 内嵌），其"query"是列表查询参数，不是医学 Query 疑问单。
- 影响：这是三模式交付（日常/锁库前/锁库后）的用户侧硬缺口，比交接描述的"待接通"更严重——是从零新建。
- 方案：在 P3 闭环中一并设计实现：Query 工作区（依据—发现—请核实事项三段卡片、编辑/保存/筛选/导出草稿、版本绑定）+ 报告工作区（上传→原子主张→对照→批注副本）。前端挂在 product 路由下，与 RiskChecklist 的 Safety/PV 用途分离。

### P1-1 输入 payload 无内容寻址层（809M 字符问题）
- 定位：monitoring_ai_repository.py:164 `input_payload_json TEXT` 每 job 内嵌全文；三重放大：chunk 携带同域全表上下文（monitoring_ai_service.py:1992-2032）、bind_frozen_document_sources 每 chunk 重复绑定（evidence_tool_contract.py:46-79）、attempts 再存完整 envelope（repository:774-806）。读取端每次执行全量反序列化+sha256 重算。
- 影响：存储与恢复成本高；轮询/恢复慢；正是交接 §13.2 第5条停滞原因之一。
- 方案（分两步，不先建大抽象）：第一步把 chunk 间共享的 `read_only_table_context_profiles`/`document bindings` 提为 per-project 内容寻址 blob 表，job 存引用（sha256+行数），执行时 join；attempts 的 envelope 换为 input 引用+差异。第二步才考虑完整 artifact store。改 repository 需加迁移测试并保留旧库兼容读取（571 个历史 job 仍要可读）。

### P1-2 monitoring_ai_service.py 维护债（8881 行）
- 结构：三个 700+ 行方法（_build_prompt_envelope ~707、_validate_input_payload ~775、_validate_task_specific_output ~571）+ visit 校验器簇 ~1430 行；提交期与执行期校验语义重叠。
- 方案：设计 v2 §3 已定"渐进抽取"路线。**不在本批做**（避免与 MG 恢复/P3 闭环争抢上下文），但新增功能一律放新模块（如 query/report/task-specific 校验器独立文件），存量按"改哪块抽哪块"。

### P1-3 ProductLoop 术语泄漏（违反设计 v2 §10）
- 定位：MedicalMonitoringProductLoop.jsx:1265 "服务端范围"（设计明令禁用词）、:496/:513 "服务端推荐"、:527 "开始后由服务端确认"、:506 缺 dataCutoff 时直接显示 snapshotToken。
- 方案：文案改写为用户语言（如"系统推荐""开始后由系统确认"）；snapshotToken 兜底改为"数据版本待确认"。随 P3 前端批一并修，属小diff。

### P1-4 MG 同名来源差异（9.DM vs 评分SDV）
- 证据：交接 §8.1——5 个差异 sheet 的 cell 内容/公式/样式逐坐标无差异（含 sheet25 的 562,078 cell），差异仅在隐藏行（81+36 处）、筛选、definedName、视图元数据。
- 决策（本会话作出，工程权限内）：**保持当前冻结 SDV 版本为正式来源**。理由：1495 字段首轮证据全部绑定 SDV 的 SHA/manifest；切换需新 SourceRevision 且复用证明成本高；两者 cell 级等价使切换无临床信息增益。处置：在来源登记中将 9.DM 记为已核实的等价备选（保留 mg-source-comparison.json 证据）；隐藏行差异记入覆盖索引说明。仅当用户明确要求以 DM 目录为业务权威时才建新 SourceRevision 走复用证明。此决策记入 journal，不需要用户裁决（业务权威可由现存记录+等价证据决定）。

### P2-1 前端死代码链 ~5000+ 行
- 定位：MedicalMonitoringBatchPanel.jsx（784）→ DailyRunPanel(493)/RuleReleasePanel(911)/FieldMappingPanel(906)/ProtocolPreparationPanel(1235) → DailyAiCandidates/DailyAiEvidence/DailyDiffSummary/DailyRunEvidence；独立无引用的 AssurancePanel(840)+AssuranceRemediation、ScopeSummary、RiskEvidenceContext、RiskHistoryTrend。产品树零引用（仅测试引用）。hash/账本类术语泄漏全部集中在此链（如 DailyAiCandidates.jsx:88-98 渲染 sha256/提示词版本），但因离线用户不可见。
- 方案：列入阶段性清理清单（设计 v2 §12 允许"先替代再删，Git 可恢复"）。前提：P3 新前端不再复用这些组件；删除时连配套 .mjs 与测试一起删，单独提交便于回滚。

### P2-2 八轨标签不一致
- Workspace.jsx:53-62 与 medicalMonitoringWorkspaceApi.mjs:66-75 对 lab_exam/protocol_compliance 的中文标签不一致（"检验检查"vs"检验/检查"、"方案执行"vs"方案符合"）。统一为一处常量定义。

### P2-3 空 g6/ 目录
- frontend/src/features/medical-monitoring/g6/ 空目录，9月2日遗留，直接删除。

## 3. 功能建议（新增/删除/调整）

### 新增（按用户价值排序）
1. **Query 工作区**（P0-3 方案）——医学监查的核心产出物，三模式共用。
2. **整理进度"能力面板"**：设计 v2 §2 要求"读到了什么、完成到哪、哪些分析可以进行、还有什么实质缺口"，当前 AdmissionWizard 只展示字段识别进度；建议补一屏"当前能自动完成什么/什么受限及原因"，直接回应用户"懒惰+风险敏感"画像（交接 §13.3 第2条自我反思的落地）。
3. **风险定位"一跳回看"**：风险行→受试者访视轴→原记录的下钻路径已有组件基础（EvidenceView/JourneyDrawer），但缺从研究/中心看板风险行的显式"进入个例"按钮与返回保留（设计 v2 §10）。P3 闭环时补。
4. **锁库后模式的现场自查 checklist 导出**：RiskChecklist 已有基础，扩为按中心分组的自查包（设计 v2 §9 锁库后合同）。

### 删除
- P2-1 死代码链（前提成立后）。
- runs/mm_p2_tool_trial_20260906 下的 /tmp 日志副本可清（正式副本已在隔离目录）；冻结源码副本 frozen-1ce29f9（45 项文件）在对应审阅收束且 Git 提交完整后可清（交接 §15.3 清单制）。

### 技术路线调整
1. **输入 payload 内容寻址化**（P1-1 方案）先于五项目扩域做——否则 RUX/MY009/MY008 全量会把存储问题放大 5 倍。
2. **受限运行组织**：MG 恢复时按"已闭合能力的字段子集先走 facts→AE/MH 纵切"组织（设计 v2 §11 已授权此顺序），不要让 696 分歧全量复核阻塞第一条临床价值。具体：优先复核 AE/MH/CM/IP/PD 相关域字段，非关键域延后。
3. **不调整**：双模型裸API harness、SQLite+graph IR 架构、ego(lite) 验收路线——均已验证且符合用户约束。

## 4. 用户视角评估（懒惰/视觉敏感/数据敏感/风险敏感）

- **懒惰**：当前首要动作"添加研究资料"已成立（AdmissionWizard 4 步向导+后台整理+持久暂停）。缺口：整理完成后用户看不到"接下来系统会自动做什么、我什么时候需要看什么"——能力面板（建议2）补此断点。
- **视觉敏感**：ProductLoop 术语泄漏（P1-3）是直接违反；八轨标签不一致（P2-2）属小刺。整体布局（工作条+进度面+三视图）符合简洁要求。
- **数据敏感**：trendScale/comparisonState 的真实数值/零变化修复已在；快照 token 兜底显示（P1-3）违背"不暴露内部标识"。
- **风险敏感**：Query 工作区缺失（P0-3）使风险发现无法转为可核实事项——这是风险敏感用户的最大断点；来源下钻链路（EvidenceView）有组件但需真实 publication 才有内容。

## 5. 测试证据

- 710 passed（7 文件聚焦集：ai_service/role_equivalence/mapping_confirmation/repository/worker/api/c3_bridge），18.69s，无失败。SWIG DeprecationWarning 5 项为既有噪音。
- v7 独立工程审阅：zcode/GLM-5.3-Flash:max 新鲜会话运行中（原 9-08 会话被用户中止 exit130，无恢复句柄；重派记录于 current-options-20260908/logs/zcode_v7_review_rerun_20260911.log），完成后其结论并入本报告后续版本。
- 未运行：前端 Vite build、ego 浏览器交互（留给 P3 批次与接线后验证）。

## 6. 行动结论

接管确认无阻塞性意外。执行顺序（对交接 §14 的落实，无变更）：
1. 收束 v7 独立审阅（运行中）→ 处置实际意见。
2. MG 来源决策已定（P1-4，保持 SDV+等装备选登记）；组合根四标志接线+独立 runtime 验证。
3. 有界恢复 MG：备份→清点→repository 接口恢复未解决分片（优先 AE/MH/CM/IP/PD 域）→ 双路复核。
4. facts 物化→P3 纵切→Query 工作区新建→ego 验收。
5. 阶段性清理按 P2 清单执行。

计划/goal 更新：implement.md 追加 2026-09-11 接管段；goal-prompt.md 的过时"不用外部执行/会商"段落以新版本替换（保留历史于 Git）；task.json notes 追加接管记录。
