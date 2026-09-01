# 医学写作生产路径动态独立 AI 消费审计

**审计日期**：2026-07-27  
**审计范围**：仅核对医学写作产品中 `independent_ai` 角色选择器与生产调用路径之间的实际消费关系；不做泛安全审计。  
**默认绑定**：`alibaba_token_plan/qwen3.8-max-preview`  
**审计方式**：只读代码追踪、运行态只读查询、聚焦测试；未修改产品代码或测试。

## 结论

**总体判定：核心医学写作语义路径已消费动态独立 AI 路由，但仍有 2 项真实边界冲突。**

1. 竞品 AI 筛选、方案摘要结构化导入、绿地项目事实对话与设计预填、章节候选及各类修订意图、语料库泛化分析，均未在生产调用入口固定为 `deepseek-v4-pro`；当前会解析或冻结活动 provider profile，实际可运行到 `alibaba_token_plan/qwen3.8-max-preview`。
2. 生产启动脚本仍把 DeepSeek API Key 作为启动硬前置，并注入固定 DeepSeek 路由。活动 provider registry 会在应用内覆盖该环境值，因此当前实例实际运行 Qwen，但仅配置 Alibaba Token Plan、未配置 DeepSeek Key 的部署会在应用启动前被错误阻断。
3. `independent_ai.enabled=false` 尚未成为生产执行硬开关。多数生产服务读取活动 provider profile；角色绑定写入会同步活动 profile，但角色的 `enabled` 状态没有进入 provider factory 的拒绝逻辑。

## 实际冲突与未消费边界

### C1. 启动脚本仍要求 DeepSeek 凭据并注入固定 DeepSeek 路由

**严重度**：P1  
**是否构成当前实例阻塞**：否；当前实例已启动且活动 registry 覆盖为 Qwen。  
**是否构成可部署性阻塞**：是；Qwen-only 环境无法通过该启动脚本启动。

**实际行为**

- 启动脚本先查找 `DEEPSEEK_API_KEY`，找不到即退出。
- 随后固定注入 `WORKBENCH_AI_PROVIDER=deepseek` 和 `WORKBENCH_AI_MODEL=deepseek-v4-pro`。
- 应用内部 `runtime_ai_env()` 会读取持久化活动 profile 并覆盖这些环境值，所以当前运行实例仍实际使用 Qwen。

**证据**

- `runtime/start_medical_writing_backend_8911.zsh:10-39`：DeepSeek Key 是启动前硬门。
- `runtime/start_medical_writing_backend_8911.zsh:42-49`：固定注入 DeepSeek provider/model。
- `config/ai.env.example:1-6`：示例配置仍以 DeepSeek 为产品默认。
- `services/api/app/ai_runtime_settings.py:459-493`：活动 profile 被投影为实际运行环境。
- `services/api/app/ai_runtime_settings.py:511-512`：`runtime_ai_env()` 读取活动 profile。
- 运行态 `GET /api/ai-gateway/status`：`provider=alibaba_token_plan`、`model=qwen3.8-max-preview`、`active_profile_id=alibaba_qwen38`、`semantic_ai_tasks_enabled=true`。

**最小修复建议**

- 启动脚本不再要求特定供应商 Key，也不再固定注入 provider/model。
- 启动时仅启动 API；由 `ai_provider_settings.json` 的活动 profile 和本地凭据存储决定实际路由。
- 如需环境变量回退，只按活动 profile 的 `api_key_env` 查找对应凭据，不要求未选中的 DeepSeek Key。

### C2. `independent_ai.enabled` 未被生产 provider factory 消费

**严重度**：P1  
**是否构成默认 Qwen 路由阻塞**：否；当前绑定为 `enabled=true`。  
**冲突性质**：角色选择器呈现“可停用”，但生产调用以活动 profile 为准，停用角色后仍可得到可运行 provider。

**实际行为**

- 写入 `independent_ai` binding 时会激活相应 provider profile，因此 provider/model 选择可正确同步。
- `role_env()` 不检查 `binding.enabled`，仍返回 provider/model。
- 竞品筛选和语料分析直接读取活动 profile；预填、事实对话和通用 AI task runner 通过 `configured_ai_provider_from_env()` / `runtime_ai_env()` 读取活动 profile。
- 聚焦探针确认：在临时设置中将 `independent_ai.enabled=false` 后，活动 profile 仍为 enabled，`role_env()` 仍返回 `alibaba_token_plan/qwen3.8-max-preview`。

**证据**

- `services/api/app/ai_role_runtime_settings.py:289-309`：绑定写入会激活 profile。
- `services/api/app/ai_role_runtime_settings.py:324-335`：`role_env()` 未检查角色启用状态。
- `services/api/app/ai_role_runtime_settings.py:390-426`：停用状态只进入公开状态计算；`execution_binding_consumed` 对 independent AI 固定为真。
- `services/api/app/ai_gateway.py:1255-1286`：默认 provider factory 从活动运行环境创建 provider。
- `services/api/app/medical_writing_competitor_triage.py:4149-4172`：竞品筛选冻结活动 profile。
- `services/api/app/medical_writing_corpus_analysis_ai.py:468-477`：语料分析冻结活动 profile。

**最小修复建议**

- 增加一个唯一的 `independent_ai` 运行时解析入口：先读取角色 binding，若角色或 profile disabled 则返回 disabled/阻断；否则从该 binding 对应 profile 构建环境。
- 预填、事实对话、AiTaskRunner、竞品筛选、语料分析统一使用该入口。
- `execution_binding_consumed` 应由真实执行解析结果计算，不应仅因 `role_id == independent_ai` 固定为真。

## 生产路径逐项核对

| 生产路径 | 真实调用入口 | 动态绑定结论 | `deepseek-v4-pro` 硬编码判定 | 证据 |
|---|---|---|---|---|
| ClinicalTrials.gov 竞品检索 | `WritingReferenceDiscoveryService.create_search_snapshot()` 直接调用 CT.gov API | 不需要消费独立 AI；检索是确定性数据获取 | 无冲突 | `services/api/app/main.py:6050-6064`；`services/api/app/writing_reference.py:546-630` |
| 竞品 relevance 筛选/triage | `_resolve_triage_provider()` → `VerifiedTriageProvider` → durable frozen profile | **已动态消费**；当前可冻结 Qwen profile | `TRIAGE_MODEL_NAME` 仅用于 test-only 注入和兼容默认值；生产校验同时允许固定产品 Qwen/DeepSeek 路由，不构成生产硬编码 | `services/api/app/main.py:6375-6405`；`services/api/app/medical_writing_competitor_triage.py:246-350`、`4149-4172`、`4266-4295` |
| 竞品文档下载与原文解析 | `WritingReferenceDocumentService` 下载；`WritingReferenceExtractionService` 原生解析，异常页走 OCR 角色 | 不应消费独立 AI；OCR 属于独立 `ocr` 角色 | 无冲突 | `services/api/app/main.py:886-894`；`services/api/app/writing_reference.py:1766-1794`、`1881-1926` |
| 方案摘要导入结构化 | `MedicalWritingSynopsisImportService` → `AiTaskRunner.submit_internal(protocol_synopsis_structuring)` | **已动态消费**；AiTaskRunner 每次解析运行时 route | 测试中的 DeepSeek fixture 不构成生产固定 | `services/api/app/main.py:757-760`；`services/api/app/medical_writing_synopsis_import.py:1351-1366`；`services/api/app/ai_execution_policy.py:391-465` |
| 摘要/最小事实导入后的预填 | `generate_prefill` → `_build_prefill_ai_enricher()` → `build_prefill_ai_adapter()` | **已动态消费**；factory 从活动 profile 创建 provider，并把真实 model 写入 adapter | `DEEPSEEK_PREFILL_MODEL` 是直接构造 adapter 的兼容默认；生产 factory 会用 provider 的真实 model 覆盖，不构成阻塞 | `services/api/app/main.py:553-562`、`6131-6162`；`services/api/app/medical_writing_authoring_prefill_ai.py:1625-1642` |
| 绿地项目自然语言事实采集 | `MedicalWritingFactIntakeService.run_turn()` → `configured_ai_provider_from_env()` | **已动态消费** | 无生产模型常量 | `services/api/app/medical_writing_fact_intake.py:910-923`、`1236-1267` |
| 绿地项目设计建议 | 确定性 prefill 基线 + 上述 AI enricher | **已动态消费**；确定性基线不应被误认为 AI 路由 | `deterministic_registry_prefill` 是基线生成器身份，不是 LLM model | `services/api/app/medical_writing_authoring_prefill.py:2990-3037`；`services/api/app/medical_writing_authoring_prefill_ai.py:1625-1642` |
| 章节候选生成（包括空白章节起草） | `MedicalWritingRevisionService._run_revision_ai()` → `AiTaskRunner.submit_internal/submit_registered()` | **已动态消费** | 无生产模型常量 | `services/api/app/medical_writing.py:288-319`、`1065-1113`、`1167-1237`；`services/api/app/ai_task_runner.py:2051-2078` |
| 改写、监管语气、一致性、补证据 | 所有 intent 先形成不同 task context，再进入同一 revision AI 调用链 | **已动态消费**；intent 不改变 provider/model | 允许的 DeepSeek Pro 仅为显式产品回滚路由，不是 intent 专属硬编码 | `services/api/app/medical_writing_revision_prompts.py:60-140`；`services/api/app/medical_writing.py:1065-1237`；`services/api/app/ai_execution_policy.py:128-148` |
| 扩写/缩写/进一步重写 | 作为 revision 用户指令或 rewrite durable action，再进入同一 `_run_revision_ai()` | **已动态消费** | 无单独模型硬编码 | `services/api/app/main.py:8110-8146`；`services/api/app/medical_writing.py:1690-1706`、`3000-3042` |
| 语料库适应症分层与泛化分析 | research pipeline 启动时 `freeze_active_route()`；执行时按冻结 route `analyze()` | **已动态消费**，且 durable 期间不会被后续 profile 切换静默改道 | 无 DeepSeek 固定；当前测试明确使用 Qwen | `services/api/app/medical_writing_research_pipeline.py:407-415`、`458-470`、`2046-2071`；`services/api/app/medical_writing_corpus_analysis_ai.py:468-490`、`598-645` |

## 合理保留的 DeepSeek 标识

以下命中不构成 independent AI 动态绑定阻塞：

1. `services/api/app/ai_gateway.py:63`：DeepSeek Pro 产品路由常量，用于显式可选/回滚 profile。
2. `services/api/app/ai_execution_policy.py:128-148`：医学写作语义任务允许 Qwen 3.8 和受控 DeepSeek 路由；默认并未固定为 DeepSeek。
3. `services/api/app/medical_writing_authoring_prefill_ai.py:125`：兼容直接构造 adapter 的默认参数；生产 factory 在 `1625-1642` 使用动态 provider/model 覆盖。
4. `services/api/app/medical_writing_competitor_triage.py:83`：test-only provider 严格夹具和兼容默认；生产路径在 `301-318`、`4149-4172` 使用活动产品 profile。
5. `services/api/app/chapter_translation_pipeline.py:45` 与 `services/api/app/writing_reference_upper_layer_execution.py:21`：属于翻译上层整合/升级模型，不是 `independent_ai` 写作角色。

## 验证证据

### 运行态只读验证

- `GET /api/ai-gateway/status`：
  - `configured=true`
  - `provider=alibaba_token_plan`
  - `model=qwen3.8-max-preview`
  - `semantic_ai_tasks_enabled=true`
  - `active_profile_id=alibaba_qwen38`
- `GET /api/ai-gateway/roles/status`：
  - `independent_ai.provider=alibaba_token_plan`
  - `independent_ai.model=qwen3.8-max-preview`
  - `enabled=true`
  - `ready=true`
  - `current_runnable=true`

### 聚焦测试

使用隔离的 Python 3.12 依赖路径运行，禁用 pytest cache 与字节码写入：

- `tests/test_ai_role_runtime_settings.py`
- `tests/test_medical_writing_direct_ai_policy.py`
- `tests/test_medical_writing_revision_prompts.py`
- 竞品 durable frozen-route 3 项
- 语料分析动态 Qwen、适应症泛化边界与冻结 route 4 项
- 方案摘要导入并发独立 AI 1 项

**结果：30 passed，11 subtests passed。**  
仅出现 FastAPI `on_event`/test client 弃用警告，与本次动态路由消费结论无关。

### 生产 factory 只读探针

当前活动配置下：

```text
provider=alibaba_token_plan
model=qwen3.8-max-preview
prefill_adapter=DeepSeekPrefillAdapter
prefill_model=qwen3.8-max-preview
```

这证明 adapter 的历史类名没有把生产调用固定回 DeepSeek。

## 最小修复优先级

1. **P1：修复启动脚本的 DeepSeek Key/route 硬前置。**
2. **P1：建立真正消费 `independent_ai.enabled` 的统一运行时解析入口。**
3. 无需重写已动态消费 Qwen 的竞品筛选、摘要导入、预填、章节候选、修订和语料泛化链路。
