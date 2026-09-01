# Reference Translation 上层阶段编排 Worker 记录

日期：2026-07-25  
范围：`chapter_translation_pipeline`、`writing_reference_translation_batch` 及聚焦测试  
状态：bounded coding 完成；真实运行时装配尚未在本写集内执行

## 目标与边界

- DeepSeek Flash 负责目录/章节规划与 Hy-MT2 后整合/QC。
- Hy-MT2 是正文分块翻译的唯一模型。
- Pro 只能由服务器上层阶段服务按确定性条件自动升级，且只重跑相同上层阶段。
- Pro 不得修改、替换或重新翻译 Hy-MT2 target map。
- 不修改 contracts、`main.py`、repository、`writing_reference.py`、上层 execution service、前端和运行配置。
- 不伪造真实模型成功；所有新增测试使用 fake adapter/service。

## 已实现

### 1. 统一上层阶段入口

在 `chapter_translation_pipeline.py` 增加：

- Flash/Pro 上层模型 allowlist；正文 allowlist 仍只有 Hy-MT2。
- `UpperLayerStageOwner`、`UpperLayerStageExecutionResult` 和最小
  `UpperLayerStageExecutor` 注入协议。
- `PersistedUpperLayerStageExecutorAdapter`，可将当前 pipeline 协议接到
  `WritingReferenceUpperLayerExecutionService`。adapter 不决定模型，只负责构造
  server-internal request、解码持久化结果并校验 hash/lineage。
- `execute_document_planning_stage()` 和 `execute_integration_qc_stage()`。
- 未注入上层服务时继续使用既有 Flash planner/QC，保持旧部署兼容。

### 2. 路由与 lineage 校验

每次上层阶段结果校验：

- stage、requested/response model、prompt version；
- canonical input/output hash；
- selected run、latest run、parent run 和 escalation ID；
- Pro 只能来自 `failed_escalatable` 或 `completed_degraded`；
- `failed_retryable` 等 transient 状态不能形成合法 Pro escalation lineage。

`PersistedUpperLayerStageExecutorAdapter` 将实际 prompt 交给共享上层服务持久化。
prompt 文本由运行时 `prompt_resolver` 提供，避免在 pipeline 内复制生产提示词。

### 3. Hy-MT2 target-map 不变性

- integration 前冻结 Hy-MT2 target map，并计算 canonical SHA-256。
- Flash/Pro 只接收冻结后的 source-unit/target-map payload。
- 上层调用后再次校验原 target map 未变。
- 通过的上层结果必须逐字等于从冻结 target map 重组的正文。
- Pro 的 drift/body mutation 不能成为候选正文。
- Pro 重跑路径不调用 `hy_mt2_translator`，不重建 translation chunk。

### 4. Batch 接线与产品进度

- 文档规划与普通/窗口化 integration 均改用同一 pipeline 上层阶段入口。
- batch item 同时投影兼容字段与通用字段：
  `flash_*_model`、`plan_model`、`qc_model`、latest stage run、
  escalation ID/status。
- plan 保存 provider、transport、deployment profile、response model 和 stage run。
- integration 保存 route-specific fingerprint 与 selected stage run。
- composite ledger 保存实际模型、prompt version、input/output hash。
- 用户进度只显示：
  “正在识别目录与章节”“正在按章节翻译正文”
  “正在核对译文结构与章节衔接”“翻译完成，可核对并使用”等短文案，
  不显示原始日志、hash 或内部错误。
- Pro 失败而保留 Flash/Hy 输出时，selected run 与 latest failed Pro run 分开记录，
  避免把回退结果误报为 Pro 成功。

## 新增测试覆盖

- 上层 allowlist 包含 Flash/Pro，正文 allowlist 不包含 Pro。
- 自动 Pro integration：
  - Flash 调用 1 次；
  - Pro 调用 1 次；
  - Hy-MT2 调用 1 次；
  - target-map hash 不变；
  - 最终正文逐字等于 Hy-MT2 target map；
  - parent/escalation lineage 完整。
- Pro 缺少 Flash parent lineage 时失败关闭。
- transient Flash 状态伪装成 Pro escalation 时失败关闭。
- 共享持久层 adapter 的 prompt、input/output hash 和 run lineage round-trip。
- 使用真实 `WritingReferenceUpperLayerExecutionService` 配合 fake model adapter，
  验证 pipeline bridge、SQLite stage run 与输出解码可以端到端接通。
- batch 持久 chunk 的 `unit_targets`、chunk 译文、Pro integration 译文一致。
- batch 通用模型、stage run、escalation 和短进度文案正确投影。

## 验证

通过：

```text
python3 -m py_compile \
  services/api/app/chapter_translation_pipeline.py \
  services/api/app/writing_reference_translation_batch.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py
```

通过：

```text
python3 -m pytest -q \
  tests/test_writing_reference.py \
  tests/test_writing_reference_translation_durable_jobs.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_mw_v11_translation_alignment.py \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_upper_layer_contracts.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py \
  -k 'not test_http_core_contract_and_span_injection_rejection'
```

结果：`328 passed, 1 deselected`。

目标两文件不排除运行结果：`64 passed, 1 failed`。唯一失败是既有 HTTP 测试在
POST 返回 `202` 后立即要求 batch 为 `completed`，而当前 `main.py` 的 durable
异步接口实际返回 `accepted`。本 worker 未修改 `main.py` 或该 API 测试；此处不以
越界修改掩盖同步/异步合同差异。

相邻 repository 全套测试另有一个既有版本断言仍期待 schema 4，而当前 repository
已是 schema 5；本 worker 未修改 repository 或该测试。

## 残余接线

1. `main.py` 需创建真实 `WritingReferenceUpperLayerExecutionService`，并以
   `PersistedUpperLayerStageExecutorAdapter` 注入 direct 与 batch 共用的
   `ChapterTranslationPipeline`。
2. 运行时必须提供：
   - 实际 Flash/Pro planner 与 QC adapter factory；
   - 精确生产 prompt resolver；
   - deployment profile；
   - adapter 输出的稳定结构化 payload。
3. 需要在 API/worker 接线层统一修订上述 HTTP 测试：若接口维持 durable async，
   应断言 `accepted` 后等待 job terminal；不能继续假定 POST 内同步完成。
4. 尚未运行真实 DeepSeek/Hy-MT2。本记录仅证明编排、hash、lineage、target-map
   不变性及兼容回归，不代表真实模型或稳定服务验收。

## 修改文件

- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `reviews/translation_upper_layer_orchestration_worker_20260725.md`
