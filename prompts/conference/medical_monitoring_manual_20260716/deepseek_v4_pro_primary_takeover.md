你是 Reasonix/deepseek-v4-pro，现接管《医学监查子系统说明书》的主笔扩写。用户明确指出当前各章过于宽泛、细节不足、逻辑不强、正文真实示例不足、Mermaid 图和表格的丰富度与颗粒度不足。

先完整读取：
- `/Users/smkzw/.hermes/SOUL.md`
- `AGENTS.md`
- `context/medical_monitoring_manual_source_packet_20260716.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书.md`
- `runs/conference/medical_monitoring_manual_20260716/reasonix_deepseek_v4_pro_review.md`
- `logs/subsystems/medical_monitoring_log.md`

只写一个文件：`runs/conference/medical_monitoring_manual_20260716/deepseek_v4_pro_primary_manuscript.md`。不要修改现有说明书。使用 write_file 输出完整可替换 Markdown 正文，不要只输出审阅意见。

重写要求：
1. 保留正式说明书定位，形成厚重、章节清晰、能直接指导医学、产品、前端、后端和测试实施的正文。
2. 所有核心工作流拆成：触发、输入、前置校验、主路径、分支、失败/降级路径、输出、人工确认、审计和验收。
3. 每个风险族拆成：医学目的、数据域与最小字段、方案依赖、确定性规则、语义判断、排除/降级、严重度、置信度、来源证据、处置、局限、正文案例。
4. 每章至少在适用处插入一个正文案例，用 Markdown 斜体并以“示例：”开头。案例可基于真实临床工作模式但必须去标识化；写出日期、访视、数值、参考范围、变化、关联事件、系统展示和医学处置。
5. 增加足量 Mermaid：总体架构、日常监查序列、Diff 状态机、锁库前流程、统一风险对象、AE/MH 决策树、禁限用药匹配、跨表一致性、Subject Timeline 数据流、Patient Profile 数据流、人机审批、部署和测试闭环。图中中文简洁且可渲染。
6. 增加细颗粒表格：输入域字段、三模式差异、风险规则矩阵、基线规则、语义覆盖、CTCAE/非 CTCAE、IP/CM 边界、用药匹配、访视窗口、跨表规则、风险严重度/置信度、状态机、API、测试矩阵和验收证据。
7. CM 仅为非试验用药/治疗；IP 的暂停、减量、加量、停药、重启和依从性始终独立。
8. 所有阈值和时间容差区分方案明确值、项目批准配置和说明性示例；不得制造跨项目普适阈值。
9. 说明书需区分目标规范、已实现能力、尚待生产验证；不自动确认 AE/MH、PD 或监管结论。
10. 首次英文缩写使用“中文全称（English Full Name，ABBR）”。全文使用自然、严谨、科学中文，避免口号、空泛过渡和 AI 套话。

建议成稿不少于现稿两倍信息量。最终回复只报告写入路径、字符数、Mermaid 数、表格数、章节数和未决事项。
