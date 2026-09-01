# OCR证据持久化与Flash→Pro分阶段升级设计审阅

日期：2026-07-25  
角色：医学写作子系统只读技术设计审阅  
状态：建议按两个独立切片实施；本轮未修改产品代码、运行库、服务或源文件，未启动模型或服务，未运行测试

## 1. 审阅结论

两个发布缺口都可以沿现有 artifact、extraction、不可变 plan/chunk/integration、durable job 和审计链做增量修复，不需要新建安全审批流，也不能靠改全局环境变量解决。

### A. OCR证据

最小正确改动是：

1. 仍由 `WritingReferenceExtractionService._recover_pages_with_ocr()` 顺序渲染选中页；
2. 对实际送入 GLM-OCR 的 PNG 计算 SHA-256，并按 artifact/extraction/page/hash 写成不可变文件；
3. 在现有 `WritingReferenceExtractionResult.ocr_recovery_pages` 中增加相对路径、PNG hash、像素尺寸、字节数、OCR字符数和结果状态；
4. 增加项目/文档/提取版本绑定的只读元数据和图片 API；
5. 复用现有 extraction review，在批准结构时绑定 page + PNG hash 的视觉核对结果，不增加“待医学批准”或来源授权审批。

不建议把 PNG 放入 SQLite BLOB，也不建议新建安全扫描、病毒扫描、rights 审批或逐页独立工作流。

### B. Flash→Pro

最小正确改动不是把 `_translation_ai_env()` 改成可读某个全局 Pro 开关，而是：

1. 建立服务器拥有的上层阶段枚举和阶段执行记录；
2. 默认阶段模型固定为 Flash，只有已有 Flash 阶段记录被服务器判为 `failed_escalatable` 或 `completed_degraded` 时，医学经理才能显式创建 Pro escalation；
3. escalation 请求不接受任意 target model，服务端固定目标为 `deepseek-v4-pro`；
4. planner/QC adapter 按本次阶段路由构造 provider，并持久化 provider、请求模型、响应模型、deployment profile、prompt、输入/输出 hash、父运行和失败分类；
5. Hy-MT2 chunk 合同和调用点保持不变，Pro 只能重跑章节规划、译后整合/QC，未来有真实语料选择调用点时才能用于语料选择建议。

现有代码把 `corpus_selection_support` 写在状态接口中，但真实语料策略当前主要是确定性筛选/打分，未找到与该状态声明对应的 Flash 调用和 lineage。因此本切片应先把状态改为逐阶段能力报告，并把语料选择标记为 `not_implemented`；不要为了填满枚举而虚构一个模型调用。

## 2. 直接观察到的当前实现

### 2.1 OCR路径

- `services/api/app/writing_reference.py:1736-1845`
  - `WritingReferenceExtractionService.extract()` 完成 PDF/DOCX 提取、OCR recovery、`save_extraction()` 和内容校验。
- `services/api/app/writing_reference.py:1847-2022`
  - `_recover_pages_with_ocr()` 合并 zero-text 和 anomaly 页；
  - PyMuPDF 在 `1904-1914` 将所有选中页顺序渲染为 `page_images: dict[int, bytes]`；
  - `1916-1932` 最多 8 路并发调用 OCR；
  - `1999-2013` 已持久化 page、DPI、model、profile digest、OCR文本 hash、span 和 selection reason；
  - PNG bytes 和 PNG hash 没有进入 extraction 结果或文件系统。
- `services/api/app/main.py:833-865`
  - `_writing_reference_ocr_runner()` 已校验精确模型、最低 DPI 和 PNG magic，并调用 `LocalOcrGateway`。
- `packages/contracts/workbench_contracts/models.py:7623-7644`
  - `WritingReferenceExtractionResult` 已有 additive `ocr_recovery_pages`，适合承载新增元数据，不必为 OCR 证据单独加 SQLite 表。
- `services/api/app/writing_reference_repository.py:1143-1238`
  - extraction 以完整 JSON payload 不可变保存；新字段天然随 extraction revision 落盘。
- `services/api/app/main.py:3116-3227`
  - workspace 不返回 extraction 结果；
  - spans API 只返回 spans，当前没有 OCR 证据列表或图片读取 API。

额外缺口：`_recover_pages_with_ocr()` 在 OCR 返回空文本时直接 `continue`，当前连“该选中页实际调用过 OCR 但返回空”的页级结果都不会进入 `ocr_recovery_pages`。实现 PNG 证据时应同时记录空文本页，不能只记录产生 span 的页。

### 2.2 Flash、Pro和Hy-MT2路径

- `services/api/app/chapter_translation_pipeline.py:36-50`
  - OCR、Hy-MT2、Flash planner/QC 模型和 prompt version 均为精确常量。
- `services/api/app/chapter_translation_pipeline.py:90-92`
  - body allowlist 只有 Hy-MT2；
  - `ALLOWED_FLASH_MODELS` 没有 Pro。
- `services/api/app/main.py:425-436`
  - `_translation_ai_env()` 每次强制 `deepseek-v4-flash`。
- `services/api/app/main.py:868-956`
  - `_flash_planner_adapter()` 使用上述固定环境，并把返回 lineage 写死为 Flash 常量。
- `services/api/app/main.py:959-1136`
  - `_hy_mt2_translator_adapter()` 独立调用本地 oMLX 精确 Hy-MT2；这是正文唯一翻译点。
- `services/api/app/main.py:1139-1262`
  - `_flash_qc_runner_adapter()` 使用固定 Flash；
  - `integrated_text` 必须逐字回显 Hy-MT2 对齐草稿。
- `services/api/app/ai_execution_policy.py:103-126`
  - `DOCUMENT_SECTION_EXTRACTION` 与 `REGULATORY_TRANSLATION_ZH` 已允许 direct Flash 或 Pro；
  - 当前缺的是调用点的阶段选择和 lineage，不是全局 policy allowlist。
- `services/api/app/ai_gateway.py:914-1008`
  - `OpenAICompatibleAiProvider` 已按 `expected_response_model` 校验实际响应模型；
  - adapter 目前没有把 `provider.response_model` 带入 plan/QC 数据结构。
- `services/api/app/writing_reference_translation_batch.py:2147-2282`
  - `_get_or_create_document_plan()` 按固定 Flash model 计算 planner fingerprint；
  - Flash结构失败后当前源码会尝试 deterministic fallback，并把失败码写入 plan ambiguity，而不是总是直接终止。
- `services/api/app/writing_reference_translation_batch.py:1804-2049`
  - integration 失败时可回退到确定性重组的 Hy 文本；
  - stage ledger 能记录模型和 hash，但只在完整 composite run 完成后保存，不能单独表达失败、升级父子关系或 deployment profile。
- `services/api/app/writing_reference_repository.py:427-442`
  - `writing_reference_chapter_integration_results` 当前唯一约束是 `(tenant_id, project_id, plan_id, chapter_id)`；
  - 同一 plan/chapter 不能同时持久化 Flash 和 Pro 两个整合结果。
- `services/api/app/main.py:1946-1962`
  - 状态接口只报告一个固定 Flash route，却同时宣称 `corpus_selection_support`。

当前 direct translation 和 batch translation 各自实现了一套 composite orchestration：

- `WritingReferenceTranslationService._generate_with_composite_pipeline()`：
  `services/api/app/writing_reference.py:1147-1721`
- `WritingReferenceTranslationBatchService._process_with_composite_pipeline()`：
  `services/api/app/writing_reference_translation_batch.py:1391-2145`

阶段路由和阶段 lineage 必须抽成同一服务供两者调用；只改 batch 会留下 direct translation 的行为分叉。

## 3. A切片：OCR页证据持久化

### 3.1 合同模型

在 `packages/contracts/workbench_contracts/models.py` 增加：

```python
class WritingReferenceOcrPageEvidence(WorkbenchModel):
    physical_page: int
    dpi: int
    image_media_type: Literal["image/png"] = "image/png"
    image_sha256: str
    image_size_bytes: int
    image_width_px: int
    image_height_px: int
    storage_relpath: str
    model: str
    ocr_profile_digest: str
    ocr_text_sha256: str
    ocr_character_count: int
    channel: Literal["ocr", "ocr_reconciled"]
    selection_reason: str
    ocr_result_status: Literal["text_recovered", "empty_text"]
    span_id: str = ""
```

将：

```python
WritingReferenceExtractionResult.ocr_recovery_pages:
    List[Dict[str, Any]]
```

改为：

```python
List[WritingReferenceOcrPageEvidence]
```

Pydantic 能把现有 dict payload 解析为新模型，但旧记录缺新必填字段。为兼容旧 extraction，新增字段第一版必须有安全默认值：

```python
image_sha256: str = ""
image_size_bytes: int = 0
image_width_px: int = 0
image_height_px: int = 0
storage_relpath: str = ""
ocr_character_count: int = 0
ocr_result_status: Literal["text_recovered", "empty_text", "legacy_metadata_only"] = (
    "legacy_metadata_only"
)
```

新写入路径必须自行验证这些字段非空，不能因模型默认值而放宽生产写入。

在 `WritingReferenceExtractionReviewDecision` 和
`WritingReferenceExtractionReviewRequest` 增加：

```python
class WritingReferenceOcrPageReview(WorkbenchModel):
    physical_page: int
    image_sha256: str
    decision: Literal["confirmed", "returned"]
    comment: str = ""

ocr_page_reviews: List[WritingReferenceOcrPageReview] = []
```

这复用已有 extraction structure review。对含 OCR 页的 extraction，`decision="approved"` 时要求所有当前 evidence 的 `(physical_page, image_sha256)` 恰好各有一个 `confirmed`；非 OCR 文档保持旧行为。

同步导出：

- `packages/contracts/workbench_contracts/__init__.py`

### 3.2 文件位置和写入算法

新增小模块：

- `services/api/app/writing_reference_ocr_evidence.py`

职责：

```python
def build_ocr_evidence_relpath(
    artifact_storage_relpath: str,
    extraction_revision: str,
    physical_page: int,
    dpi: int,
    image_sha256: str,
) -> str

def write_immutable_ocr_png(
    artifact_root: Path,
    storage_relpath: str,
    image_bytes: bytes,
    expected_sha256: str,
) -> bool

def resolve_ocr_evidence_path(
    artifact_root: Path,
    storage_relpath: str,
) -> Path
```

建议相对路径：

```text
<artifact-parent>/ocr/<extraction_revision>/
  page_0143_200dpi_<first16-image-sha256>.png
```

其中 `<artifact-parent>` 直接取现有 document `storage_relpath` 的父目录；不在路径中暴露原始 project id，不复制源 PDF。

写入规则复用 `WritingReferenceDocumentService._write_immutable_file()` 的语义：

1. 先检查 PNG magic；
2. 计算 hash、width、height、bytes；
3. 用同目录 `.<name>.<uuid>.tmp`、`flush()`、`fsync()`、`os.replace()`；
4. 同名已存在时只接受 hash 一致；
5. 路径必须是 artifact root 下的相对路径，拒绝 absolute 和 `..`；
6. 不增加安全扫描、rights 检查或模型前审批。

### 3.3 `WritingReferenceExtractionService`改动

文件：

- `services/api/app/writing_reference.py`

函数：

- `WritingReferenceExtractionService.extract()`
- `WritingReferenceExtractionService._recover_pages_with_ocr()`

精确改动：

1. `extract()` 从 repository 取得 document `storage_relpath`，将其传给 `_recover_pages_with_ocr()`。
2. 渲染每页时立即计算 PNG hash和像素信息，但仍把 bytes 留在 `page_images` 供并发 OCR。
3. 所有 OCR futures 完成后，按页码顺序不可变写 PNG；模型调用失败时不写半批最终文件。
4. 每个 `pages_to_ocr` 都产生 evidence：
   - 有文本：`text_recovered`，带 span；
   - 空文本：`empty_text`，空 span，OCR text hash 为 SHA-256(empty bytes)，字符数 0。
5. 只有 `text_recovered` 创建/替换 span；不能把空文本页从 evidence 中丢掉。
6. `save_extraction()` 失败时无需删除已存在的 hash 命名文件；同 extraction revision 的幂等重试会复用。对本次新建而 DB 最终未注册的文件可做 best-effort 清理，但不能删除 hash 不一致或已被另一幂等请求注册的文件。

不改变：

- 200 DPI；
- 顺序渲染；
- 最大8路 OCR；
- 精确 `GLM-OCR-bf16`；
- anomaly 页替换 native span 的规则；
- 当前内容校验和 extraction review 门。

### 3.4 Repository和API

`services/api/app/writing_reference_repository.py` 增加只读方法：

```python
def document_extraction(
    project_id: str,
    artifact_id: str,
    extraction_revision: str,
) -> WritingReferenceExtractionResult
```

API 在 `services/api/app/main.py` 增加：

```text
GET /api/projects/{project_id}/medical-writing/references/
    documents/{artifact_id}/extractions/{extraction_revision}/ocr-evidence

GET /api/projects/{project_id}/medical-writing/references/
    documents/{artifact_id}/extractions/{extraction_revision}/ocr-pages/{physical_page}/image
```

元数据响应：

```json
{
  "artifact_id": "...",
  "extraction_revision": "...",
  "evidence_state": "complete|legacy_metadata_only|none",
  "items": [
    {
      "physical_page": 143,
      "dpi": 200,
      "image_sha256": "...",
      "image_size_bytes": 123456,
      "image_width_px": 1654,
      "image_height_px": 2339,
      "model": "GLM-OCR-bf16",
      "ocr_profile_digest": "...",
      "ocr_text_sha256": "...",
      "ocr_character_count": 1234,
      "selection_reason": "zero_text_page",
      "ocr_result_status": "text_recovered",
      "span_id": "..."
    }
  ]
}
```

图片 API：

- 只能从 repository 中当前请求的 exact extraction evidence 解析相对路径；
- 不接受客户端 file path；
- 校验 project/artifact/extraction/page 绑定和 root containment；
- 返回 `image/png`、`ETag: "<image_sha256>"`、`Cache-Control: private, immutable`；
- 文件缺失返回 `409 ocr_evidence_file_missing`，旧记录无路径返回 `404 legacy_ocr_image_not_persisted`；
- 不在响应中返回 `storage_relpath` 或绝对路径。

### 3.5 A切片测试

扩展：

- `tests/test_writing_reference_extraction_service.py`
  - 混合 PDF 只为选中页写 PNG；
  - 写入 bytes 与实际送给 fake OCR runner 的 bytes 完全一致；
  - 200 DPI、PNG hash、模型、profile、页码、字符数和 span 一致；
  - OCR 空文本仍有 `empty_text` evidence，无 span；
  - 同 idempotency 重放不重复写；
  - re-extraction revision 分目录，旧证据保留；
  - OCR future 异常不生成完整 extraction，不留下部分“已完成”manifest。
- `tests/test_writing_reference_repository.py`
  - repository 重启后 exact extraction 能恢复 typed evidence；
  - v4/旧 JSON 缺 PNG字段时解析为 `legacy_metadata_only`。
- `tests/test_writing_reference_api.py`
  - 元数据 API 只返回 exact project/artifact/revision；
  - image API bytes/hash/ETag 正确；
  - 跨项目、错误页、错误 revision、缺文件失败关闭；
  - 响应不泄露绝对路径。
- `tests/test_writing_reference_extraction_service.py`
  - extraction `approved` 对 OCR 页要求 page+hash 视觉确认；
  - 非 OCR extraction 的旧 review 请求仍通过。

保留并继续运行：

- `tests/test_chapter_translation_pipeline.py` 中 DPI、并发、模型 allowlist；
- `tests/test_ocr_gateway.py` 中网关 PNG/模型合同。

## 4. B切片：上层阶段执行与显式Pro升级

### 4.1 阶段边界

新增阶段枚举：

```python
UpperLayerStage = Literal[
    "document_planning",
    "post_hy_mt2_integration_qc",
    "corpus_selection_support",
]
```

明确排除：

- `body_translation`
- `hy_mt2_translation`
- `source_extraction`
- `ocr`

允许模型：

```python
DEFAULT_UPPER_LAYER_MODEL = "deepseek-v4-flash"
ESCALATED_UPPER_LAYER_MODEL = "deepseek-v4-pro"
ALLOWED_UPPER_LAYER_MODELS = frozenset({
    DEFAULT_UPPER_LAYER_MODEL,
    ESCALATED_UPPER_LAYER_MODEL,
})
ALLOWED_BODY_TRANSLATION_MODELS = frozenset({
    "dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX",
})
```

不要删除现有 `ALLOWED_FLASH_MODELS`，先保留为 backward-compatible alias/测试合同；新代码只使用 `ALLOWED_UPPER_LAYER_MODELS`。

### 4.2 新合同数据结构

在 `packages/contracts/workbench_contracts/models.py` 增加：

```python
class WritingReferenceUpperLayerStageRun(WorkbenchModel):
    stage_run_id: str
    project_id: str
    owner_type: Literal["translation_batch_item", "direct_translation", "corpus_selection"]
    owner_id: str
    batch_id: str = ""
    item_id: str = ""
    artifact_id: str
    extraction_revision: str
    plan_id: str = ""
    chapter_id: str = ""
    stage: UpperLayerStage
    provider: Literal["deepseek"]
    transport: Literal["openai_compatible"]
    requested_model: Literal["deepseek-v4-flash", "deepseek-v4-pro"]
    response_model: str
    deployment_profile: str
    prompt_version: str
    input_hash: str
    output_hash: str = ""
    status: Literal[
        "succeeded",
        "completed_degraded",
        "failed_retryable",
        "failed_escalatable",
        "failed_terminal",
        "interrupted",
    ]
    failure_code: str = ""
    provider_call_count: int
    parent_stage_run_id: str = ""
    escalation_id: str = ""
    created_at: datetime
    completed_at: datetime

class WritingReferenceUpperLayerEscalationRequest(WorkbenchModel):
    source_stage_run_id: str
    actor: str = "medical_manager"
    reason: str
    idempotency_key: str

class WritingReferenceUpperLayerEscalation(WorkbenchModel):
    escalation_id: str
    project_id: str
    source_stage_run_id: str
    source_model: Literal["deepseek-v4-flash"]
    target_model: Literal["deepseek-v4-pro"] = "deepseek-v4-pro"
    stage: UpperLayerStage
    lineage_hash: str
    status: Literal["queued", "running", "completed", "failed_retryable", "failed_terminal"]
    durable_job_id: str = ""
    actor: str
    reason: str
    created_at: datetime
    updated_at: datetime
```

`WritingReferenceTranslationBatchItem` 增加摘要字段，旧字段继续保留：

```python
plan_model: str = ""
qc_model: str = ""
active_upper_layer_stage: str = ""
active_upper_layer_stage_run_id: str = ""
latest_upper_layer_stage_run_id: str = ""
upper_layer_escalation_available: bool = False
upper_layer_escalation_id: str = ""
```

旧 `flash_plan_model` / `flash_qc_model` 不删除。新写入同时填 actual model 到旧字段和新字段，旧客户端仍能显示；新客户端只读通用字段。

### 4.3 阶段执行服务

新增：

- `services/api/app/writing_reference_upper_layer_execution.py`

核心接口：

```python
class WritingReferenceUpperLayerExecutionService:
    def execute(
        self,
        *,
        stage: UpperLayerStage,
        owner: UpperLayerOwner,
        requested_model: str,
        prompt_version: str,
        input_hash: str,
        parent_stage_run_id: str = "",
        escalation_id: str = "",
        invoke: Callable[[str], UpperLayerCallResult],
    ) -> tuple[Any, WritingReferenceUpperLayerStageRun]

    def request_pro_escalation(
        self,
        project_id: str,
        request: WritingReferenceUpperLayerEscalationRequest,
    ) -> WritingReferenceUpperLayerEscalation
```

`execute()` 的职责：

1. 在外部调用前把 deterministic `stage_run_id` 写入 batch item 的 active stage 字段；
2. 调用按 model 构造的 planner/QC runner；
3. 读取已由 gateway 验证的 `response_model`；
4. 按结果持久化一条 terminal stage run；
5. 清 active id，写 latest id；
6. 异常只落安全 failure code，不落 provider 原始错误、密钥或完整正文。

进程在模型调用期间终止时，durable recovery 根据 batch item 的 active run id 和“没有 terminal run”事实补一条 `interrupted` 记录，再创建新 run；不能把新运行覆盖成旧 run。

### 4.4 Adapter改动

`services/api/app/main.py`：

```python
def _translation_ai_env(model_name: str = FLASH_MODEL) -> dict[str, str]

def _build_document_planner_adapter(model_name: str) -> FlashPlanner

def _build_integration_qc_adapter(model_name: str) -> FlashQcRunner
```

规则：

- `model_name` 必须来自 stage execution service，不能来自请求或任意环境覆盖；
- provider 始终 `deepseek`；
- transport 始终 `openai_compatible`；
- gateway 仍要求 exact response model；
- adapter 返回 `provider`、`transport`、`deployment_profile`、
  `requested_model`、`response_model`；
- Flash 和 Pro 复用同一结构/echo schema，prompt version 可共享内容合同，但 stage run 必须记录实际 model；
- status API 不再只返回一个 `model`，而返回逐阶段配置。

建议状态响应：

```json
{
  "runtime_scope": "medical_writing_reference_translation",
  "body_translation": {
    "model": "dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX",
    "provider": "local_omlx",
    "deepseek_allowed": false
  },
  "upper_layer_stages": {
    "document_planning": {
      "implemented": true,
      "default_model": "deepseek-v4-flash",
      "escalation_model": "deepseek-v4-pro"
    },
    "post_hy_mt2_integration_qc": {
      "implemented": true,
      "default_model": "deepseek-v4-flash",
      "escalation_model": "deepseek-v4-pro"
    },
    "corpus_selection_support": {
      "implemented": false,
      "reason": "no_product_stage_owner"
    }
  }
}
```

### 4.5 planner、integration和corpus的升级判据

#### Document planning

Flash内部仍可做一次有界纠正。分类：

- provider timeout/429/5xx/连接失败：`failed_retryable`，同模型重试，不升级 Pro；
- source/extraction/manifest lineage 变化：`failed_terminal`；
- Flash结构输出无效，但可信 deterministic fallback 成功：
  `completed_degraded`，保存 fallback 及 Flash失败 run；不自动升级；
- Flash结构输出无效且 deterministic fallback 也不能形成连续全覆盖 plan：
  `failed_escalatable`，允许显式 Pro；
- Pro仍结构无效：`failed_terminal`，不得继续模型级升级。

规划 Pro escalation 第一版只允许在该 artifact 尚无 Hy-MT2 chunk 时执行。若原 fallback plan 已被下游消费，返回 `409 stage_output_already_consumed`；不要在同一 patch 中实现计划重分支和已翻译章节重映射。

#### Post-Hy-MT2 integration/QC

- Hy-MT2、chunk、unit target 和 source hash 都不变；
- Flash返回结构合规并通过：`succeeded`；
- Flash的 echo/marker/QC 输出失败，但 deterministic Hy 文本仍完整：
  `completed_degraded`，candidate 可继续医学复核，同时显式提供 Pro escalation；
- provider运行失败：`failed_retryable`，先重试 Flash；
- Pro escalation 只重跑 integration/QC，必须复用现有 Hy chunks，且 Pro
  `integrated_text` 仍必须逐字回显 Hy target map；
- Pro改写正文、改变数字/单位/否定/时间窗、改变 unit map：
  `failed_terminal`，保留原 Hy candidate，不得采用 Pro正文。

#### Corpus selection

当前不接模型。`medical_writing_corpus_policy.py` 的确定性筛选/分面/打分继续工作，医学 review/admission 继续由现有 API 管理。

只有未来出现真实 `WritingReferenceCorpusSelectionService`，并能冻结 candidate IDs、translation revisions、project facts 和 input hash 后，才能：

1. 用 Flash给出非绑定排序建议；
2. Flash结构失败时显式升级 Pro；
3. Pro结果仍不得自动 admission；
4. 医学经理选择/确认继续构成最终决定。

### 4.6 持久层与唯一约束迁移

`services/api/app/writing_reference_repository.py`：

- `SCHEMA_VERSION = 5`
- 新表：
  - `writing_reference_upper_layer_stage_runs`
  - `writing_reference_upper_layer_escalations`
- 两表保留 immutable record；escalation current status 可使用独立 state projection。

`ChapterIntegrationResult` 增加：

```python
integration_contract_fingerprint: str = ""
upper_layer_stage_run_id: str = ""
parent_integration_id: str = ""
```

新的 fingerprint 至少包含：

```text
translation_contract_fingerprint
+ plan_id
+ chapter_id
+ stage
+ requested_model
+ prompt_version
+ exact input_hash
```

必须迁移 `writing_reference_chapter_integration_results`，因为当前
`UNIQUE (tenant_id, project_id, plan_id, chapter_id)` 会阻断同章 Pro 结果。

SQLite v5 migration：

1. `BEGIN IMMEDIATE`；
2. 将旧表改名为 `_v4`；
3. 建新表，唯一键改为
   `(tenant_id, project_id, plan_id, chapter_id, integration_contract_fingerprint)`；
4. 复制旧行，列值 `integration_contract_fingerprint=''`；
5. 删除旧表并重建 no-update/no-delete trigger；
6. 插入 schema migration 5；
7. `PRAGMA foreign_key_check` 和 `PRAGMA integrity_check`；
8. commit。

旧 payload 内已有 `translation_contract_fingerprint`，但 DB 新列保持空值可清楚表示 legacy row；repository 读取时仍从 payload 恢复旧数据。新 route-specific 查询只匹配非空 exact fingerprint，因此不会静默复用旧 Flash-only identity。

`DocumentStructurePlan` 增加：

```python
planner_provider: str = ""
planner_transport: str = ""
planner_deployment_profile: str = ""
planner_response_model: str = ""
upper_layer_stage_run_id: str = ""
parent_plan_id: str = ""
```

planner fingerprint 已含 model；Pro plan 可与 Flash/fallback plan 并存，不需要重建 plan 表唯一键。

### 4.7 显式升级API和durable恢复

新增：

```text
GET /api/projects/{project_id}/medical-writing/references/
    upper-layer-stage-runs/{stage_run_id}

GET /api/projects/{project_id}/medical-writing/references/
    translation-batches/{batch_id}/upper-layer-stage-runs

POST /api/projects/{project_id}/medical-writing/references/
    upper-layer-stage-runs/{stage_run_id}/pro-escalations
```

POST body：

```json
{
  "actor": "medical_manager",
  "reason": "Flash在有界纠正后仍无法形成连续章节计划。",
  "idempotency_key": "..."
}
```

服务端检查：

1. exact project 和 stage run；
2. source run 的 model 必须是 Flash；
3. status 必须是 `failed_escalatable` 或 `completed_degraded`；
4. stage 必须在上层阶段 allowlist；
5. source/extraction/plan/chunk lineage 仍当前；
6. 没有 active/completed child escalation；
7. planning 输出尚未被 Hy chunk 消费；
8. request 不能携带 target model、provider、base URL 或 body stage。

成功返回 `202` 和 `durable_job_id`。复用现有 durable worker，但增加 payload mode：

```json
{
  "mode": "upper_layer_stage_escalation",
  "escalation_id": "..."
}
```

`WritingReferenceTranslationDurableExecutor.execute()` 按 mode 分派：

- 现有 `pending/retry` 行为保持；
- escalation job 只重跑指定 stage；
- integration Pro重跑复用已完成 Hy chunks；
- retryable Pro运行通过统一 job `/retry` 重试同一 Pro route；
- source lineage stale 时 escalation terminal，不能回退重建来源；
- cancel/lease loss 继续使用现有 ownership guard，旧 owner 不得晚写。

### 4.8 B切片测试

扩展：

- `tests/test_medical_writing_direct_ai_policy.py`
  - Flash/Pro只允许上层 stage；
  - revision/synopsis仍按现有 Pro policy；
  - Hy body不进入 direct DeepSeek policy。
- `tests/test_ai_gateway.py`
  - Flash和Pro exact response model均验证；
  - mismatch失败且不产生成功 stage run。
- `tests/test_chapter_translation_pipeline.py`
  - upper-layer allowlist含精确 Flash/Pro；
  - body allowlist仍只有Hy-MT2；
  - Pro planner/QC不能改写 body；
  - same Hy target map 在 Flash和Pro integration后 hash不变。
- `tests/test_writing_reference_translation_batch.py`
  - 正常路径仍 Flash；
  - Flash transient failure只能同模型 retry；
  - planner无fallback时标为 escalatable；
  - degraded integration可显式升级；
  - Pro integration复用 chunk，Hy fake调用次数不增加；
  - Pro body mutation失败关闭并保留Hy；
  - direct和batch均使用相同 stage execution service；
  - batch item返回通用 model/run/escalation字段。
- `tests/test_writing_reference_translation_durable_jobs.py`
  - escalation job创建/幂等/取消/租约丢失/重启恢复；
  - active run无terminal记录时恢复为 interrupted；
  - stale owner不能保存Pro结果；
  - retry只重跑指定stage，不重跑Hy chunk。
- `tests/test_writing_reference_repository.py`
  - v4→v5 migration保留旧plan/chunk/integration；
  - 同一plan/chapter可存不同integration fingerprint；
  - exact fingerprint查询不复用legacy空值；
  - stage run和escalation跨重启、跨项目隔离、审计链有效。
- `tests/test_writing_reference_api.py`
  - stage run查询；
  - 合法Pro escalation返回202；
  - client自带model/provider/body stage被 `extra="forbid"` 拒绝；
  - Flash成功、Pro来源、跨项目、陈旧lineage和已消费plan均返回409/422。
- `tests/test_writing_reference_translation_service.py`
  - 历史 legacy Pro run 仍不被当作当前分阶段Pro lineage；
  - direct translation走相同显式升级合同。

## 5. 互斥写集

为避免并行实现互相覆盖，建议按以下写集分派。每个文件只归一个实施单元。

### W1：OCR核心

可写：

- `services/api/app/writing_reference_ocr_evidence.py`（新）
- `services/api/app/writing_reference.py`
- `tests/test_writing_reference_extraction_service.py`

不可写：

- contracts、repository、main、translation pipeline/batch。

### W2：上层阶段领域与持久层

可写：

- `services/api/app/writing_reference_upper_layer_execution.py`（新）
- `services/api/app/writing_reference_repository.py`
- `tests/test_writing_reference_repository.py`

不可写：

- contracts、main、writing_reference.py、translation batch/pipeline。

### W3：translation orchestration

可写：

- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_durable_jobs.py`
- `tests/test_writing_reference_translation_service.py`

不可写：

- contracts、repository、main、OCR模块。

### W4：共享合同与API接线

此单元必须串行，最后接线。

可写：

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/main.py`
- `tests/test_writing_reference_api.py`
- `tests/test_medical_writing_direct_ai_policy.py`
- `tests/test_ai_gateway.py`

不可写：

- W1-W3文件。

推荐顺序：W4先落 additive contracts；W1/W2/W3在合同稳定后并行；W4最后只做 main/API 接线和组合回归。若不能两次进入 W4，则先以独立 contract-only commit 完成 models/__init__，再把 main/API 分给单独 W5，保持文件所有权互斥。

## 6. 迁移和兼容策略

### OCR

- 旧 extraction JSON 不重写；
- 缺 PNG字段的旧记录返回 `legacy_metadata_only`；
- 不从原 PDF 静默回填旧 PNG；
- 需要完整证据时显式 re-extract，形成新 extraction revision；
- 新 OCR证据使用相对路径，运行目录搬迁不破坏引用。

### Translation/API

- 保留现有 batch create/retry、job status/result/cancel/retry API；
- 新 escalation 是附加资源，不把 model 字段加到现有 batch create request；
- 保留旧 `flash_plan_model`/`flash_qc_model` 响应字段和默认值；
- 新 stage fields 全部 additive，旧 batch item JSON 可解析；
- 历史 Pro AI run 不等于新阶段 escalation，不能自动迁移或复用；
- 旧 integration 可读不可当新 route-specific current result；
- Hy-MT2 chunk identity和正文 translation model不变。

### 失败时回滚

- A切片回滚：停止写新 evidence 字段/API；hash命名 PNG 可保留为未引用不可变文件，后续按 extraction manifest 做精确清理，不能广泛删除 artifact 目录。
- B切片回滚：关闭 escalation API/worker mode；默认 Flash path仍可运行；新 stage run记录和v5 integration表保留只读，不回退schema或删除审计证据。

## 7. 实施验收顺序

1. contracts 兼容测试：旧 extraction、旧 batch item、旧 integration payload 可读取。
2. OCR单元/服务/API：证明送模PNG = 落盘PNG = hash对应PNG。
3. repository v4→v5迁移测试和双integration identity测试。
4. Flash正常路径回归：现有 planner/Hy/QC行为不变。
5. Flash transient retry、semantic escalatable、explicit Pro、Pro失败恢复。
6. 证明 integration Pro重跑没有新增 Hy-MT2 调用，正文 hash不变。
7. direct translation 与 batch translation 同一阶段服务组合测试。
8. durable restart/cancel/ownership loss。
9. 状态接口逐阶段报告；语料选择不得再宣称已实现模型支持。
10. 最后才运行两个真实项目批次；真实模型、浏览器、OCR页视觉核对仍由产品验收，不由单元测试替代。

## 8. 明确不纳入本设计

- sponsor confidentiality / rights 审批；
- 新安全扫描、病毒扫描、后门审计；
- 新“待医学批准”状态；
- Protocol候选重新盘点；
- 全扫描 PDF 页内标题切分；
- 自动语料 admission；
- Flash/Pro正文翻译；
- 通过全局环境变量把整个批次切成 Pro；
- 启动模型、服务或写入运行库。

## 9. 最终判定

A切片可以做到无数据库schema变更：PNG写入现有
`writing_reference_artifacts`，typed metadata继续保存在 immutable extraction JSON，
现有 extraction review承接页级视觉核对。

B切片需要数据库schema v5：阶段run/escalation记录是新增表；同一章节保存Flash与Pro整合结果必须解除旧的 `(plan_id, chapter_id)` 唯一身份，并以 route-specific integration fingerprint替代。任何不处理这个唯一约束、只在 batch item 上加 `model="pro"` 的方案都会产生不可审计覆盖、冲突或假lineage，不应实施。
