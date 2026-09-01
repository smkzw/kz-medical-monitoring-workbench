# 医学监查 P10：方案监查准备候选决定前端闭环

日期：2026-07-30  
状态：前端实现、确定性回归与生产构建通过；真实候选态浏览器验收待队列产出

## 1. 目标与范围

在既有“方案监查准备”抽屉中补齐医学经理对结构化候选的接受/驳回闭环，并严格复用
`monitoring_p10_protocol_candidate_decision_closure_20260730.md` 已冻结的后端合同。

本切片只修改：

- `MedicalMonitoringProtocolPreparationPanel.jsx`
- `medicalMonitoringProtocolPreparation.mjs` 及测试
- `medicalMonitoringApi.mjs` 及测试
- `frontend/src/styles.css`
- 本记录与 P10 LOOP 账本

未修改后端、`main.py`、医学写作、字段映射、daily run、risk 或任何运行数据库。

## 2. 用户交互

1. 候选仍以“条款正文 → 结构化字段 → 方案原文 → 次级 locator”的顺序展示。
2. `proposed` 候选底部提供低噪声“接受 / 驳回”动作。
3. 单一 `allowed_fact_type` 不显示额外选择器，由后端按已冻结主题自动采用。
4. 多事实类型主题只显示中文语义下拉选项，例如“试验药物给药方案”“试验药物变更”；
   用户不接触 `fact_key`、内部枚举键或其他技术字段。
5. 驳回时展开单行理由输入，默认值为“该候选不适用于当前方案监查。”，用户可直接确认
   或简短修改。
6. 接受成功显示“已确认事实草稿”，驳回成功显示“已驳回”。用户的选择本身就是
   医学经理决定，不出现“待医学批准”，也不要求二次批准同一候选。
7. 决定成功后先在当前页面锁定候选状态，再读取服务器真实状态；相反动作不会重新开放。
8. 决定失败只显示一次候选级错误，不自动重试。用户修正或刷新后可主动再次操作。

## 3. 冻结身份参数

候选决定必须提交：

- `expected_input_revision_sha256`
- 当前主题 `source_revision`

当前方案准备紧凑状态返回 `job_id` 和 `source_revision`，但不直接返回输入修订哈希。前端
在用户决定时通过既有只读 `getMonitoringAiJob()` 获取该作业的当前
`input_revision_sha256`，核对同一候选仍为 `proposed`，再与主题状态中的
`source_revision` 一并提交。任何缺失或状态变化均停止写入并提示刷新，不猜测修订值。

新增客户端方法：

```text
decideProtocolPreparationCandidate(
  projectId,
  protocolVersionId,
  candidateId,
  payload
)
```

路径中的项目、方案版本和候选 ID 均逐段 URL 编码。

驳回请求只包含决定、操作者、理由和两项冻结修订，不携带事实类型、事实键、标题或
applicability，因此不会产生事实草稿字段。

## 4. 状态收敛

- 决定响应中的真实 candidate 状态先投影到当前页面。
- 若该主题不再存在 `proposed` 候选，主题从 `candidate_review` 收敛为 `reviewed`。
- 进度区只统计 `proposed` 候选，不再把已接受或已驳回候选显示为“等待用户确认”。
- 随后的状态刷新以服务器为最终真值；刷新失败不会撤销已成功返回的决定状态。

## 5. 验证

```text
node frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs
medicalMonitoringProtocolPreparation: 17 passed

node frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs
medicalMonitoringApi: 98 passed

cd frontend && npm run build
1906 modules transformed
build passed
```

确定性覆盖包括：

- 多类型中文选项；
- 单一/多类型事实类型请求边界；
- 当前作业输入修订解析；
- 接受请求冻结修订与类型；
- 驳回请求不含事实草稿字段；
- 多类型未选择时停止提交；
- 接受/驳回中文状态；
- 决定后的候选和主题状态收敛；
- 决定 API 路径编码、POST 方法和请求体透传。

Vite 仍报告既有主 bundle 大于 500 kB；构建成功，本切片未进行无关拆包。

## 6. 当前真实运行边界

2026-07-30 本轮只读核对：

- RUX-03-002：8/8 主题均为 `queued`，0 个候选；
- MG-K10-SAR：8/8 主题均为 `queued`，0 个候选；
- MY009：8/8 主题均为 `queued`，0 个候选。

因此本轮不伪造候选展开、接受、驳回的真实浏览器通过证据。真实候选态验收继续保留为
待办，至少应覆盖：

1. 单一事实类型接受；
2. 多事实类型中文选择后接受；
3. 驳回且不创建事实；
4. 决定后刷新及关闭/重开恢复；
5. 相反决定禁用和后端 409 冲突表现；
6. 试验药物与非试验用 CM 类型边界；
7. quote 忠实性、时间窗、阈值、例外和来源定位。

当前运行 API 未受控重启，OpenAPI 尚未加载新候选决定路由。这与后端闭环记录中的残余
边界一致。为避免打断仍在运行的产品独立 AI 队列，本前端切片没有重启 API；下次受控
重启后再执行真实候选态浏览器验收。

## 7. 文件 SHA-256

```text
443aa86e50d4142a6c095dad2ef9eed25c1ab0a9256b227122fb0a94c1ac17ff  MedicalMonitoringProtocolPreparationPanel.jsx
ff76a7d056a27238901a4af87a2e02771f71b325ac3aa3328fa5bc7c1659b985  medicalMonitoringProtocolPreparation.mjs
9141a55108e91c1b235220ed0f37496b0672050ea7819551a273474c58036924  medicalMonitoringApi.mjs
368a92b1656d04a472093e699dd6907208fbd680b920b408b40829a773995709  medicalMonitoringProtocolPreparation.test.mjs
459a153cd75d935704f4f9e1782ff2608a6f605ed9320552422588d7128b1ce7  medicalMonitoringApi.test.mjs
0b5b56bb8aa49272e8ed760ca6de83e037ee654ec3a37a0cf6538c7c6a98c975  styles.css
```
