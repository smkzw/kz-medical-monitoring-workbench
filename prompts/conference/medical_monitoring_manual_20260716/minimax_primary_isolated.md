你是本任务指定的中文主笔 Hermes/aishuo/MiniMax-M3。完整阅读 `/Users/smkzw/.hermes/SOUL.md` 后，在隔离会话中完成医学监查子系统说明书的主笔工作。

Hard boundaries:
- 工作目录仅限当前 `.`。
- 只读取：`AGENTS.md`、`context/medical_monitoring_manual_source_packet_20260716.md`、`docs/medical_monitoring_manual/医学监查子系统说明书.md`、`logs/subsystems/medical_monitoring_log.md`。
- 不修改现有 Markdown，不读取其他会商模型输出。
- 只可写一个文件：`runs/conference/medical_monitoring_manual_20260716/minimax_primary_manuscript.md`。
- 使用 write_file 将完整替换稿写入该文件；最终回复只报告路径、字数、所读来源、主要增强点和未决风险。

Task:
以现有 36 章 Markdown 为骨架，重写并扩充为一份可直接作为正式说明书正文的完整中文稿，不是提纲、审阅意见或 README。保留全部必要章节，修正任何不严谨表述。重点加强：
1. 日常增量监查、锁库前全量监查、核查前总结性自查共享同一方案解构、规范化数据层、规则引擎和风险对象，但采用不同运行策略；
2. 每个风险族都写清目的、输入、前置、确定性触发、医学语义复核、排除/降级、严重度与置信度、源证据、处置、审计、局限和案例；
3. AE/MH、CS/NCS、CTCAE、基线决策和趋势判断；
4. 试验药物变更/剂量调整与 CM 绝对分域；
5. 禁限用药、时间窗、持续合格性、AE/SAE/AESI、疗效、跨表逻辑；
6. Subject Timeline 必须是访视/日期轴下的分类彩色泳道，Patient Profile 必须是方案驱动的疗效安全纵向图；
7. Checklist 七列、来源正文优先于定位、跨视图叠加交互；
8. 前后端契约、内容修订、幂等、并发、审计、私有化部署、两个以上真实项目端到端验证；
9. 丰富受试者级、中心级、项目级和批次变化示例。

首次缩写写“中文全称（English Full Name，ABBR）”。区分目标规范、已实现、项目配置和待医学复核候选。不得宣称自动确诊、自动判 PD 或零漏报。项目阈值只能是可配置示例。全文用自然、严谨、科学的中文，避免模板化口号和泛泛 AI 文风。
