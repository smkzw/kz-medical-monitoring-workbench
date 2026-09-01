# 医学写作竞品方案参照交互与产品基准调研

日期：2026-07-12
范围：只用于当前医学写作竞品方案语料与证据抽屉设计，不替代后续完整商业产品调研。

## 第一性问题

医学撰写人员需要的不是一个“搜索结果列表”，而是在不离开当前章节、不丢失文档上下文的情况下，完成来源筛选、版本判断、译文复核、证据批准、引用选择和 AI 改写约束。产品必须同时满足：写作连续性、来源可追溯、人工审批、版本失效可见、AI 不得静默注入。

## 外部产品与官方资料

### Certara CoAuthor

官方产品页：<https://www.certara.com/coauthor/>

- 将监管/医学写作能力直接放入 Microsoft Word，而不是让作者在独立知识库与编辑器之间频繁切换。
- 强调结构化内容、模板、版本控制、实时预览和协作审阅。
- 官方描述的 RAG 边界是仅引用用户允许的来源，并提供直接引用和追溯。

官方产品说明：<https://www.certara.com/wp-content/uploads/2024/11/2024-11-22-Fact-Sheet-CoAuthor-Interactive.pdf>

- 明确提出 prompt referencing，使作者能够把 AI 生成内容快速回查到源数据。

批判性借鉴：保留“编辑器内使用”“来源显式选择”“生成结果可回查”三项；不照搬 Word 插件形态，因为当前工作台还承担项目级数据、审批和跨子系统联动。

### Veeva Vault

官方 Clinical Operations 与 RIM 连接 FAQ：<https://www.veeva.com/resources/faq-veeva-vault-clinical-operations-to-rim-connection/>

- 对文档流转强调明确的 source vault；一般将文档实际创作所在 Vault 作为权威来源。
- 跨系统连接用于交换文档和数据，但不应产生两个不清楚谁为主的可编辑副本。

批判性借鉴：竞品公开文档必须是只读来源事实；工作台只能生成受控译文和写作参照，不把公开 PDF 当作可编辑正式方案，也不能让引用副本脱离来源版本。

### ClinicalTrials.gov

官方 API：<https://clinicaltrials.gov/data-api/api>

- 官方说明数据通常在周一至周五每日刷新，并建议使用 `/api/v2/version` 的 `dataTimestamp` 判断本轮数据刷新是否完成。

官方 Study Data Structure：<https://clinicaltrials.gov/data-api/about-api/study-data-structure>

- `LargeDoc` 提供上传文档信息；`LargeDocHasProtocol`、`LargeDocHasSAP` 和文档类型字段可用于识别方案/SAP。
- 官方将上传文档描述为数据提供方提交的 PDF/A 文档。

官方 Results Data Element Definitions：<https://clinicaltrials.gov/policy/results-definitions>

- Protocol、SAP、ICF 和组合文档具有不同定义；文档日期表示最近更新日期，并要求封面包含试验正式标题、NCT 号（如适用）和日期。

产品含义：检索快照必须显示 API 版本、数据时间戳和检索条件；文档卡必须显示 NCT、文档类型、日期、文件 hash、当前/已失效状态；版本替代后，既有译文和批准引用不能继续以“当前有效”出现。

## 对当前交互的约束

1. 编辑器和 AI 对话保持主区域，竞品证据作为 AI rail 内的独立“证据”工作面或临时侧层，不能增加永久第四列。
2. 证据必须经过“发现候选→医学相关性→文档隔离/解析→译文忠实度→医学审核→批准入库”状态链；状态不能只靠颜色表达。
3. “加入本次 AI 证据包”必须是显式动作，只允许 `approved_current`；点击不能直接改写或插入正文。
4. 每条批准证据需要 NCT、文档、页/块 locator、文档 hash、span hash、词汇表版本和医学审核记录。
5. 搜索快照与来源版本变化需要在页面上可见；失效来源保留历史，但退出默认检索和 AI 上下文。
6. 真实产品不能把页面刷新后的医学审核状态留在前端临时内存，因此 workspace API 必须返回当前 review projection 和失效历史。

## 本轮发现的实现缺口

- 旧 workspace API 返回不可变 artifact payload，来源失效后仍显示 `source_current=true`。
- 旧 workspace API 不返回当前医学审核 projection，用户刷新页面后无法重建“已批准/退回/拒绝”的当前状态。
- 旧 workspace API 只返回当前批准 brief，不返回失效历史，无法解释引用为何消失。

上述三项已进入后端 TDD 修复，不改变不可变事实记录；只新增状态投影和历史读取面。
