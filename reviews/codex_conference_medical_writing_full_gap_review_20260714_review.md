# Codex Conference Review: medical_writing_full_gap_review_20260714

Date: 2026-07-14

## Verdict

`PASS WITH CODEX CORRECTIONS`。四个角色均完成同一会话内的三轮分析，输出足以支持产品取舍；但MiMo越过指定只读清单、GLM最终Markdown被工具写成diff样式，因此生产结论以Codex对本地代码、运行时、原始M11材料和JSON逐轮输出的复核为准。

## Boundary Compliance

- MiniMax-M3：遵守指定只读清单；其代码现状判断只能作为待核验假设。
- deepseek-v4-pro：遵守指定只读清单；提出的CQRS/decorator等命名架构不采纳，避免把模式名称当目标。
- MiMo-v2.5：主动读取了未授权给该角色的补充代码；其代码特定结论不作为独立证据。
- GLM-5.2 chair：完成三轮同会话裁决；最终run文件出现diff格式污染，Codex改读JSON中的逐轮原始输出，并独立完成最终裁决。

## Participant Outputs Reviewed

| Role | Accepted contribution | Rejected or constrained contribution |
|---|---|---|
| MiniMax-M3 | 跨章节一致性、estimand与统计联动、sponsor overlay、横向切片验证 | 未经代码核验的缺口判断；把过多实现细节升级为用户决策 |
| deepseek-v4-pro | 按章节性质自适应0/1/3-5候选、稳定对象ID驱动编号与引用 | warning-only语料门；CQRS/decorator等过度架构化建议 |
| MiMo-v2.5 | 旧平面章节模型迁移风险、现有文档适配需要显式映射 | “尚无CT.gov能力”的错误判断；所有越界代码结论 |
| GLM-5.2 chair | 正确纠正CT.gov现状、语料硬门、边界污染和过度架构 | 被污染的最终Markdown不直接作为可交付报告 |

## Hermes Sub-Venue Review

会商共识可信的部分是：现有编辑器不是主要瓶颈，目标应从“AI在线Word”转向“结构化研究设计事实驱动的中文M11方案”；先形成StudyDefinition和项目旅程，再把摘要、正文、SoA、流程图、目录和Word输出绑定到同一组稳定对象。不同意见主要集中在语料门强度、AI候选数量和用户需要决策的范围。

## Main-Venue Codex Review

1. 语料准备必须默认阻断正式写作。允许有理由的医学override，但不得把未就绪状态伪装成就绪，且必须保留缺口、理由、人员、时间和受影响章节。
2. ClinicalTrials.gov搜索、公开文件下载、解析、翻译、医学审阅和准入已有基础。缺口是Stage 1触发的检索计划、候选篮子、人工分诊、项目级覆盖度和手工上传同轨，不是重建爬取能力。
3. AI候选数量按节点语义自适应：结构化事实不生成候选；标准条款优先一个已批准中文条款；只有真正存在科学或运营取舍的叙述才生成3-5个可比较候选。
4. 研究流程图采用受约束的语义对象与自动布局，允许有限位置调整，不建设自由画布。
5. M11采用当前ICH Step 4与CDE 2026中文映射，并保留公司/项目覆盖层。用户提供的阶段3草案用于中文措辞和规则对照，不冻结为当前权威模板。
6. 用户决策只保留会改变日常工作流或治理边界的8项；其余法规、数据和工程事实由架构直接落实。

## Codex Independent Verification

- 原始材料：读取用户PDF并提取60页/56,043字符；核对ICH Step 4与CDE 2026中文指导原则、技术规范和模板包。
- 当前代码：核对绿地建稿、CT.gov语料链、翻译/审阅、富文本、结构化表格、版本、审批和DOCX导出实现。
- 自动测试：当前医学写作相关测试`233 passed, 5 warnings`。
- 运行时：发现并修复`5174`前端与`8911`旧后端路由漂移；重启后schema 16、SQLite完整性、外键和审计链均正常。
- 浏览器：在1600x1000、1920x1080、2048x1024完成当前绿地流程，建稿、版本、结构化表格、AI修订和Word输出通过；该结果只证明底座，不证明新目标已实现。

## Final Decision

会商通过，不再追加同题重跑。采纳“StudyDefinition + ProtocolAuthoringJourney + 当前M11模板注册表 + 语料就绪门”的主线；保留现有编辑、表格、审批和导出底座；将8项真实产品边界交由用户在决策页集中选择，随后进入实现LOOP。
