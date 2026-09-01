# Codex 预填充 v4 生产实测验收记录

日期：2026-07-20

## 触发原因

Hermes worker 03 首轮真实 RA/PNH 实测确认：

- 独立产品路由确实调用 `deepseek-v4-pro`，没有使用 Codex 或会商模型；
- RA 与 PNH 调用分别约 66 秒、98 秒；
- 但两个项目均记录
  `deepseek_prefill_adapter: response missing prefill_suggestions`；
- 因此英文 ClinicalTrials.gov 条件词没有进入建议包，后续仍使用中文适应症。

根因不是模型身份或供应商连通性，而是提示词/解析器契约不一致：

- 提示词 `output_schema` 要求顶层返回
  `clinicaltrials_condition_term_en` 与 `field_suggestions`；
- 解析器与测试却只接受额外包装层 `prefill_suggestions`。

## 修复

- `medical_writing_authoring_prefill_ai.py`
  - 提示词版本升级为 `authoring_prefill_deepseek_v4`；
  - 直接顶层结构成为权威生产契约；
  - 旧 `prefill_suggestions` 包装仅保留兼容性；
  - 无关 JSON 继续失败关闭并进入确定性回退。
- `test_medical_writing_authoring_prefill_ai.py`
  - 新增真实顶层结构回归；
  - 保留旧包装兼容测试；
  - 更新 schema failure 断言；
  - RA/PNH 英文词测试改用真实生产返回形态。

## 确定性验证

- AI prefill tests：`51 passed`
- prefill + authoring journey + AI gateway：`87 passed`
- Ruff：通过
- frontend contract：`95 passed`
- frontend production build：通过

## 独立生产 AI 实测

测试均使用临时 SQLite 数据库与产品环境配置，不读取或打印密钥。

### RA II期

- 输入：`CMS-RA-QC`、`类风湿关节炎`、`II期`
- 实际模型：`deepseek-v4-pro`
- 提示词版本：`authoring_prefill_deepseek_v4`
- 推荐英文条件词：`Rheumatoid Arthritis`
- 中文确定性候选仍保留为备选
- provider/schema failure：无

### PNH III期

- 输入：`CMS-PNH-QC`、`阵发性睡眠性血红蛋白尿症`、`III期`
- 实际模型：`deepseek-v4-pro`
- 提示词版本：`authoring_prefill_deepseek_v4`
- 推荐英文条件词：`Paroxysmal Nocturnal Hemoglobinuria`
- 中文确定性候选仍保留为备选
- provider/schema failure：无

## ClinicalTrials.gov 产品服务实测

使用 `WritingReferenceDiscoveryService`、
`ClinicalTrialsGovClient` 与官方 API v2，不写入稳定数据库。

### RA II期

- 总返回：654
- `conditions` 精确包含 `Rheumatoid Arthritis`：422
- 精确匹配且公开 Protocol/SAP：48
- 示例：`NCT03233230`
- 实际下载 `Prot_000.pdf`：898004 bytes，`application/pdf`，
  PDF magic 有效

### PNH III期

- 总返回：49
- `conditions` 精确包含
  `Paroxysmal Nocturnal Hemoglobinuria`：30
- 精确匹配且公开 Protocol/SAP：15
- 示例：`NCT06578949`
- 实际下载 `Prot_000.pdf`：1751648 bytes，`application/pdf`，
  PDF magic 有效

## QC Harness 缺陷

worker 03 首轮脚本自行拼接了旧式
`area[ConditionSearch]...` 查询表达式，因此 HTTP 400。产品服务当前已使用
官方 `query.cond`，该 400 不能归因为产品后端。worker 03 的 harness
需要改为调用产品 discovery service 或严格复用 `search_url()`，不得再维护
第二套 ClinicalTrials.gov 查询实现。

## 尚未关闭

1. 首次建项仍需调整为：三项最小事实 -> AI prefill -> 英文检索词 ->
   自动竞品检索 -> 证据增强再 prefill。
2. 用户后来采用/修改英文条件词后，前端需自动执行新计划检索与再 prefill，
   并对项目切换、部分失败、409、双击和重试保持可恢复。
3. 本记录只验收模型响应契约和注册库底层能力，不代表全部候选的医学、
   监管或最终生产验收。

## 2026-07-20 增量：再调研后的确认态保持

真实浏览器 QC 进一步证明 RA/PNH 的英文词采用、计划换版、公开研究检索
和快照绑定均已成功；当时仅有的两项失败来自强制再生成建议包后，已采用
的英文检索词从 `user_confirmed` 回落为 `ai_proposed`。

根因位于版本化建议包重生成，而非前后端连接或 ClinicalTrials.gov：
新包正确重建候选，却没有把仍与当前项目事实一致的用户确认态合并回来。

当前修复：

- 重生成后，只在原确认值仍与当前 `framing`/`picos` 项目事实一致时继承
  `user_confirmed`；
- 候选 ID 或 AI 排序变化时按规范化值匹配，确认项成为该字段的推荐项；
- 新包未包含等值候选时，可在该字段现有候选组中恢复原确认项，但不跨
  动态适用性已消失的字段追加；
- 如果项目事实后来被修改，旧确认态不继承；
- 设计类候选通过其映射后的当前项目状态判定，不以旧包存在本身作为依据。

确定性复核：

- prefill、生产 AI prefill、authoring journey、AI gateway 相邻测试：
  `141 passed`；
- 新增生产顶层响应结构下的
  `Rheumatoid Arthritis` 采用、计划换版、强制再生成、确认态保持测试；
- 新增已确认方案号在当前事实未变时保持、当前事实改变时不保持的正反
  测试；
- Ruff：通过；
- 前端合同：`95 passed`；
- 前端生产构建：通过，仅保留既有 bundle 大小提示。

当前剩余边界收窄为：使用最新源码重跑同一 RA/PNH 真实生产 AI 浏览器
脚本，确认机器证据中的两项
`*-condition-adoption-research-chain-failed` 消失。

## 2026-07-20 增量：最新源码浏览器闭环通过

最新源码隔离运行时已完成 RA II期与 PNH III期全链路重跑，机器证据：

`records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/condition_term_research_qc_20260720/evidence_latest_backend_rerun/prefill_frontend_qc.json`

结果为 `passed: true`、`failures: []`，并同时证明：

- RA 采用 `Rheumatoid Arthritis` 后，研究定义确认态、建议包候选态与
  前端展示三层一致，建议包状态为 `user_confirmed`；
- PNH 采用 `Paroxysmal Nocturnal Hemoglobinuria` 后同样保持
  `user_confirmed`；
- 两项目均生成新的检索计划与不可变快照，真实检索分别返回654项和49项
  公开研究，公开Protocol/SAP分别为164份和37份；
- 方案号与方案标题低风险批量采用后刷新仍保留，随机化未被越权确认；
- 总体设计11项均显示临床中文，未泄露内部枚举；
- 人为制造陈旧revision后，首次采用收到409并重新读取，第二次采用成功；
- 1920与2560桌面视口无页面或字段横向溢出，React错误边界未触发。

Codex还直接检查了1920像素下英文检索词采用页和2560像素下总体设计页。
该轮确认交互链路和主要桌面布局可用；最终美学与全系统视觉发布仍需合并
Qoder/Kimi的独立审阅，不以本轮机器通过替代视觉终审。

相邻确定性验证进一步覆盖“用户修改候选值后采用”的真实语义：系统会
生成新的 `user_confirmed` 候选及人工来源，而不是错误地把原AI候选标成
已采用；该值在强制再生成后仍保持。当前相邻后端回归为
`142 passed`，Ruff、前端合同 `95 passed` 和生产构建均通过。

至此，本记录中“采用英文条件词 -> 检索计划换版 -> 真实公开检索 ->
证据增强再预填 -> 确认态持久化”的 RA/PNH 产品链路已关闭。剩余发布
边界转为两个真实项目的全新DOCX生成、Word原生更新/保存/PDF视觉验收，
以及多模型全功能发布审阅。
