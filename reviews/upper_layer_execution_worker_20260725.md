# Reference 上层 AI Flash→Pro 持久化与自动升级实施记录

日期：2026-07-25  
范围：bounded coding worker；仅上层执行服务、领域 repository 内加法式 schema/方法及聚焦测试  
状态：实现完成，聚焦与相邻回归通过；生产 API/翻译编排接线留给后续切片

## 1. 实现结论

1. 新增服务器拥有的 `WritingReferenceUpperLayerExecutionService`。调用方只提交业务
   stage、owner/source lineage、prompt、input 和幂等键，不提交 provider、model、
   base URL。
2. `document_planning` 与 `post_hy_mt2_integration_qc` 默认固定
   `deepseek-v4-flash`；仅 Flash 的确定性终态 `failed_escalatable` 或
   `completed_degraded` 自动且唯一创建 `deepseek-v4-pro` 子运行。
3. Flash transient 可在 Flash 内有界重试；不会因 timeout、429、5xx/连接类错误升级
   Pro。Pro transient 本轮只记录 `failed_retryable`，不做自动多次 Pro 调用。
4. Pro 只允许上述两个上层 stage。`post_hy_mt2_integration_qc` 要求调用前冻结
   Hy-MT2 target-map SHA-256，Flash/Pro 成功或降级结果必须回显同一 hash；不一致转为
   `failed_terminal`，输出不被采用。
5. `corpus_selection_support` 明确返回 `not_implemented`，执行入口直接拒绝调用，不伪造
   模型运行或 lineage。
6. stage run ID、Pro escalation ID、target run ID 和 execution fingerprint 均由服务器
   基于冻结语义确定性生成。prompt、input/output payload 与 SHA-256、请求/响应模型、
   deployment profile、parent run、escalation 和失败分类持久化，可在重启后复算。
7. Flash terminal run 与 escalation queued 先落盘，再调用 Pro。Pro 调用期间进程终止时，
   escalation 保留 `running` 租约；租约到期后新进程可恢复同一 target run，不创建第二条
   escalation。已落盘 target run 但尚未更新 escalation 时，可据持久 run 完成状态修复。
8. 同一请求的幂等重放不重复调用模型；不同幂等键但相同冻结语义也复用同一 deterministic
   run/escalation。若另一进程正持有 Pro 租约，不会提前把仅有 Flash 的中间结果写成最终
   幂等结果。

## 2. Repository 与 schema

项目不存在独立的 `services/api/app/repository.py` 或
`repository_schema.py`。现有 writing-reference 领域 schema 内嵌于
`services/api/app/writing_reference_repository.py`，因此在该真实等价文件中实施：

- `SCHEMA_VERSION`：4 → 5。
- 新表：
  - `writing_reference_upper_layer_stage_runs`
  - `writing_reference_upper_layer_escalations`
- stage run 设 immutable update/delete trigger。
- escalation 对 source run、target run 各有唯一约束；服务端以 claim token +
  lease expiry 做 CAS 恢复。
- stage run 保存时复算 prompt、input/output hash；读取时再次校验。
- escalation 保存时复算 Flash→Pro lineage hash；完成时校验 Pro run 的 model、
  parent run、escalation ID、stage 和持久存在性。
- v4 → v5 为加法式迁移；测试验证旧库标记数据保留、新表自动创建。

本切片没有改动既有 chapter integration 唯一键。按设计验收，
`(plan_id, chapter_id, integration_contract_fingerprint)` 的 route-specific 迁移应由
translation orchestration 接线切片完成，不能在本限定写集中顺带修改。

## 3. 测试证据

### 3.1 静态与聚焦

```text
python3 -m py_compile \
  services/api/app/writing_reference_upper_layer_execution.py \
  services/api/app/writing_reference_repository.py \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_repository.py
```

通过。

```text
python3 -m ruff check \
  services/api/app/writing_reference_upper_layer_execution.py \
  services/api/app/writing_reference_repository.py \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_repository.py
```

`All checks passed!`

```text
python3 -m pytest -q \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_upper_layer_contracts.py \
  tests/test_writing_reference_repository.py
```

`33 passed, 5 warnings in 0.87s`。告警均为既有 PyMuPDF/SWIG deprecated type。

覆盖：

- server-owned capabilities 与 `corpus_selection_support=not_implemented`；
- Flash success、transient retry/exhaustion、response/output hash；
- `failed_escalatable` 和 `completed_degraded` 自动升级；
- 同/不同幂等键只创建一次 Pro 子运行；
- Pro 失败时保留可用的 deterministic degraded Flash 输出；
- Pro transient 不自动重复调用；
- Hy-MT2 target-map mutation fail-closed；
- 进程中断、租约到期、repository 重启恢复；
- v4→v5 加法式迁移；
- stage run immutable trigger。

### 3.2 相邻回归

```text
python3 -m pytest -q \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_writing_reference_translation_batch.py \
  tests/test_writing_reference_translation_durable_jobs.py \
  --deselect=tests/test_writing_reference_translation_batch.py::\
WritingReferenceTranslationBatchTests::\
test_http_core_contract_and_span_injection_rejection
```

`109 passed, 1 deselected, 13 warnings in 5.72s`。除 SWIG 告警外，其余为既有 FastAPI
`on_event` deprecation。

被单独排除的测试已在完整组和 isolated 模式各复现一次：批次 POST 返回 202 后立即 GET，
状态为 `accepted`，测试旧预期为 `completed`。本切片未修改 `main.py`、
`writing_reference_translation_batch.py` 或 durable job，判定为既有异步完成时序/测试
假设，不在限定写集内修复。

最终将 3.1 与 3.2 合并复跑：`142 passed, 1 deselected, 13 warnings in 6.04s`；
`py_compile` 与 `ruff` 同轮通过。

## 4. 生产接线残余

1. `main.py` 需为 document planner 与 integration/QC 构造真实 DeepSeek adapter，
   并把 gateway 已验证的 exact `response_model` 转成
   `UpperLayerAdapterResult`。本 worker 没有伪造或接入生产模型。
2. direct translation 与 batch translation 需统一调用本服务；正文 Hy-MT2 调用点和
   allowlist 保持不变。
3. translation orchestration 切片需完成 route-specific chapter integration
   fingerprint/唯一键迁移，并证明 Pro integration 不新增 Hy-MT2 调用且正文 target map
   逐字不变。
4. API/status 切片需暴露只读 run/escalation/capability 状态和异常恢复 retry；请求合同仍
   不能接受 provider/model/base URL。
5. `failed_retryable` Pro 的人工“重试上层分析”接线尚未实现；repository 已保留同 route
   reclaim 能力，但不会由 restart recovery 自动重复 Pro。
6. 真实 DeepSeek Flash/Pro、稳定运行服务、浏览器进度和两个真实 Protocol 批次不属于本
   worker 验收，不能由 fake adapter 单元测试替代。

## 5. 修改文件

- `services/api/app/writing_reference_upper_layer_execution.py`（新增）
- `services/api/app/writing_reference_repository.py`
- `tests/test_writing_reference_upper_layer_execution.py`（新增）
- `tests/test_writing_reference_repository.py`
- `reviews/upper_layer_execution_worker_20260725.md`（本记录）
