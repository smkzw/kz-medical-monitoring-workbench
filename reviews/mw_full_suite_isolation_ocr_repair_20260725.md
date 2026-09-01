# 医学写作全仓独立失败修复记录（2026-07-25）

## 目标与边界

修复全仓回归中三项彼此独立的失败，同时保持以下边界：

- 不放宽生产环境 DeepSeek 路由策略。
- OCR 异常页必须同时保留 `ocr_reconciled` 结果和原生文本通道。
- `/api/projects` 必须继续返回用户创建的动态项目，不删除或改写用户项目。
- 不修改结构化设计、前端 `App`、PICOS 或翻译状态机。
- 不写运行态 SQLite，不重启 `5174/8911` 服务。

## 复现

聚焦运行三项原始测试后：

1. `test_trusted_internal_policy_accepts_only_pinned_translation_context`
   被生产 DeepSeek 路由策略拒绝。该测试使用了虚构 provider/model，但未声明
   `test_only_provider_injection`，测试关注点与路由策略关注点混在一起。
2. `test_extracion_service_retains_dual_channel_for_anomaly`
   已实际生成 `WritingReferenceOcrPageEvidence(channel="ocr_reconciled",
   native_channel=[...])`，但测试仍把 Pydantic 模型当作字典执行
   `"native_channel" in rec` 和 `rec["native_channel"]`，因此误报失败。
3. `test_projects_api_returns_canonical_contexts_without_alias_duplicates`
   在本次聚焦复现时通过，但原断言要求 API 返回值严格等于静态内置项目全集。
   一旦运行态存在用户创建项目，该断言必然失败，与产品支持动态项目的合同冲突。

## 修复

### 1. AI policy 测试隔离

文件：`tests/test_writing_reference_ai_contract.py`

- 仅在该虚构 provider/model 的合同测试中显式设置
  `test_only_provider_injection=True`。
- 未修改 `AiExecutionPolicyResolver` 或 `TASK_AI_ROUTE_POLICIES`。
- 生产任务仍必须使用产品绑定的 DeepSeek provider、base URL 和允许模型。
- 生产路由约束继续由 `tests/test_medical_writing_direct_ai_policy.py` 覆盖。

### 2. OCR 双通道合同

文件：

- `services/api/app/writing_reference_ocr_evidence.py`
- `tests/test_mw_round5_backend_contract.py`

修复内容：

- Round 5 合同测试改为按类型化模型字段读取 `rec.channel` 和
  `rec.native_channel`。
- 增加异常页必须实际被识别的断言，避免空循环造成假通过。
- 新 OCR 证据校验器规定：`channel == "ocr_reconciled"` 时，
  `native_channel` 必须非空，并且每个原生通道记录必须完整保留：
  `span_id`、`source_locator`、`source_text_sha256`、`channel=native_text`。
- 新增约束只作用于新生成的 OCR 证据校验；旧提取记录仍由
  `WritingReferenceOcrPageEvidence` 的 legacy-safe 默认值读取，不改变旧数据。

### 3. canonical project 动态项目合同

文件：`tests/test_canonical_project_context.py`

- 内置 canonical 项目仍必须按确定顺序出现在 API 返回值前缀。
- API 返回的全部项目 ID 必须唯一，旧 alias 不得泄漏。
- 后续追加项目必须不是内置项目的重复项。
- 用户创建的动态项目被明确视为合法 API 内容，不再把真实用户项目误判为污染。
- 未修改 `/api/projects` 实现和用户项目存储。

## 验证

### 原始三项聚焦回归

```text
3 passed
```

### AI 路由与写作 AI 合同

```text
tests/test_writing_reference_ai_contract.py
tests/test_medical_writing_direct_ai_policy.py
21 passed
```

### OCR、持久化与 Round 5 后端合同

```text
tests/test_writing_reference_ocr_evidence.py
tests/test_writing_reference_upper_layer_contracts.py
tests/test_mw_round5_backend_contract.py
28 passed
```

覆盖异常页双通道、空 OCR 保留 native text、200 DPI、GLM-OCR-bf16、
不可变 PNG sidecar、重启后证据读取、失败批次不发布半成品以及并发上限。

### 项目清单与前端清单合同

```text
tests/test_canonical_project_context.py
9 passed

tests/test_project_source_manifest.py
6 passed

tests/test_frontend_source_manifest_contract.py
5 passed
```

### 编译检查

涉及的 Python 文件通过 `python3 -m compileall -q`。

## 结论

三项失败均已按各自根因修复。生产 DeepSeek 路由没有放宽；OCR
`native_channel + ocr_reconciled` 双通道由真实提取结果和新证据校验共同保证；
canonical 项目测试已与“内置项目 + 用户动态项目”的实际产品合同一致。
本轮未重启服务，未执行用户项目删除，也未对运行态 SQLite 进行写入。
