# 医学写作竞品语料自治链 P0 实现合同

Updated: 2026-07-20
Owner: Codex architecture and final acceptance
Status: ready for execution-manager decomposition

## Problem

产品已有 ClinicalTrials.gov 检索、快照、公开文档发现和下载服务，但下载
要求先存在逐研究相关性决策，语料准备又要求人工锁定候选篮子。当前
DeepSeek prefill 只读取确定性过滤后的 snapshot hints，不会生成或持久化
正式相关性分诊。因此真实生产仍依赖用户逐条操作或测试 harness 代填，违反
独立 AI 发布合同。

## Target User Flow

1. 医学经理只输入研究药物、适应症、分期；可选上传 IB/方案摘要。
2. 产品 DeepSeek Pro 生成并由用户确认 ClinicalTrials.gov 英文检索术语和
   检索策略。
3. 产品后端完成真实检索并冻结 search snapshot。
4. 产品 DeepSeek Pro 对 snapshot 中真实结构化候选做批量医学相关性分诊，
   生成可审阅候选篮子。
5. 医学经理一次确认/微调候选篮子。该动作即为确认，不再出现第二医学批准。
6. 产品后端按确认篮子批量下载公开 Protocol/SAP；仅重试失败项。
7. 文件基本信息/内容校验、OCR/章节识别、Hy-MT2翻译和Flash整合QC继续由
   产品任务链执行，最终形成可按章节调用的候选语料。

## Authority Boundaries

- DeepSeek不得浏览或下载。它只能读取产品提供的最小项目事实、冻结快照中的
  结构化候选和公开文档元数据。
- 检索、分页、API版本、公开文档发现、下载、hash和文件存储均由确定性后端
  完成。
- 模型返回的NCT必须是冻结快照子集；未知、重复或缺失NCT fail closed。
- 可写入的分类仅为`direct_competitor`、`indirect_reference`、
  `excluded`；每项必须包含维度化理由和不确定性。
- 执行/会商模型只能模拟点击和审阅，不能生成候选篮子、相关性理由或临床
  文本。

## Product Service Contract

新增产品内批量分诊run，而非在测试harness中串联：

- 输入：
  - project/journey/snapshot/revision/hash；
  - 最少项目事实；
  - 已确认的产品模态、给药途径、靶点/机制和设计压力（存在时）；
  - snapshot候选的NCT、适应症、分期、研究类型、干预、申办方、设计摘要、
    Protocol/SAP元数据。
- 输出：
  - run_id、provider、model、prompt_version、input/output hash；
  - 每个NCT的分类、置信度、适应症/分期/模态/途径/靶点/设计匹配维度、
    公开文档适用性、简短理由、缺口；
  - 推荐保留篮子和明确排除篮子；
  - chunk状态、失败原因和可重试项。
- 状态：
  `queued -> running -> review_ready | partial_failed | failed -> confirmed`
- 批处理：
  确定性分片、幂等、并发受控；仅重试失败chunk；输入snapshot或项目事实变化
  后旧run标记stale，不能确认。
- 用户确认：
  一次原子事务写入全部relevance decisions、确认的retained candidate ids、
  actor、revision、snapshot hash、时间和审计hash，并直接使preparation
  batch可启动。

## Prompt And Validation

- 固定DeepSeek供应商`deepseek-v4-pro`和版本化JSON schema。
- 提示词明确：
  - 不得新增NCT、药物、设计或文档；
  - 只能基于提供字段；
  - 相关性按适应症、分期、模态、给药途径、靶点/机制、设计压力和公开
    Protocol/SAP角色分别判断；
  - 直接竞品与间接设计参考必须区分；
  - 缺证据时降低置信度或排除，不得补写。
- 服务端验证：
  response model identity、schema、NCT全集/子集、枚举、重复、缺失、
  文档角色、输入hash和提示词版本。

## Frontend

- 竞品准备过程独立于写作编辑台，不常驻占用文档区域。
- 一个主动作：`AI批量评估竞品`；运行时显示检索、AI分诊、候选篮子、
  下载、解析、翻译、整合的医学语言进度。
- 审阅页默认显示推荐保留篮子，支持批量勾选、按维度筛选、查看理由和原始
  registry字段；用户点`确认并准备语料`后立即进入批处理。
- 不要求逐文件审批；失败文件可单独重试；用户可在内容角色/适应症提示后
  override，但须记录理由。

## Deterministic Acceptance

1. 未手工提供NCT时，产品能从最少事实创建真实search snapshot。
2. DeepSeek run的所有NCT均来自该snapshot，且run证据包含真实模型身份和
   prompt/hash。
3. 模型注入未知NCT、重复NCT、错误枚举或不完整响应时fail closed。
4. 用户一次确认后，relevance decisions与triage在同一事务落盘；无需逐项
   手工API或第二批准动作。
5. 确认后产品批量下载至少一份真实公开Protocol/SAP并验证PDF/hash。
6. 部分失败不回滚成功项，且仅重试失败chunk/文件。
7. 项目事实或snapshot改变后旧AI run不可确认。
8. 浏览器从最少输入走完整链；执行模型不注入NCT、医学判断或临床文本。
9. 稳定运行时、用户原件和其他项目hash不变。

## Rollback

- 新run和确认表采用可并存schema；旧逐条relevance API保留为兼容层，不在
  新UI暴露。
- 功能开关只允许回退到人工候选篮子审阅，不得回退到外部Agent代办。
- 回滚不删除审计run、search snapshot、已下载原件或用户确认记录。
