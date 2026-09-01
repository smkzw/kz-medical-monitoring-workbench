# OCR / 上层 AI 路由共享合同实施记录

日期：2026-07-25  
切片：contracts-only additive worker  
状态：完成并通过聚焦回归

## 修改文件

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `reviews/ocr_upper_layer_contracts_worker_20260725.md`

未修改 `main.py`、repository、`writing_reference.py`、translation
pipeline/batch、服务配置、数据库或运行库；未启动或重启任何服务。

## 合同决策

1. `WritingReferenceOcrPageEvidence` 类型化页级 OCR 证据，覆盖物理页、DPI、
   PNG media type/hash/字节数/尺寸/相对路径、OCR model/profile、文本 hash/字符数、
   channel、selection reason、结果状态和 span。旧 `source_text_sha256` 与
   `native_channel` 保留兼容；缺 PNG 新字段的旧 extraction 解析为
   `legacy_metadata_only`，不伪造 sidecar 证据。
2. OCR 合同没有新增逐页人工审批、逐页 confirmed 或“待医学批准”状态。新写入的完整性
   校验属于后续 OCR core/service 自动门控，不由默认值替代。
3. 新增 `WritingReferenceUpperLayerStageRun`，仅允许
   `document_planning`、`post_hy_mt2_integration_qc`、
   `corpus_selection_support` 三个上层阶段，以及 DeepSeek Flash/Pro 路由。
   成功/降级完成记录要求 response model 与 requested model 精确一致；Pro 运行必须带
   Flash parent run 与 escalation lineage。
4. 新增服务器创建的
   `WritingReferenceUpperLayerEscalationLineage`（兼容导出名
   `WritingReferenceUpperLayerEscalation`）。升级只能是 Flash→Pro，触发状态只能是
   `failed_escalatable` 或 `completed_degraded`，`created_by` 固定为
   `server_orchestrator`。未提供客户端“选择 Pro”请求合同。
5. 新增 `WritingReferenceUpperLayerStageCapability` 与 capability 集合；
   `corpus_selection_support` 可明确报告 `status="not_implemented"`，且该状态禁止同时
   宣称默认模型、升级模型或自动升级能力。
6. 新增 `WritingReferenceUpperLayerRetryRequest`，只表达异常恢复意图。所有请求模型继承
   `extra="forbid"`；`model`、`provider`、`base_url` 等客户端路由字段均被拒绝。
7. batch item 新增通用 `plan_model`、`qc_model`、active/latest stage run 与自动升级状态
   摘要；其中 plan/QC model 只允许空值、Flash 或 Pro，正文 Hy-MT2 模型不能进入新增
   上层摘要。旧 `flash_plan_model` / `flash_qc_model` 保留。
8. `DocumentStructurePlan` 与 `ChapterIntegrationResult` 增加 provider/transport/
   deployment/response model、stage run、parent 与 route-specific integration
   fingerprint 等 additive lineage 字段，旧 payload 默认空值继续可读。

## 测试证据

- `python3 -m py_compile packages/contracts/workbench_contracts/models.py packages/contracts/workbench_contracts/__init__.py tests/test_writing_reference_upper_layer_contracts.py`
  - 通过。
- `python3 -m pytest -q tests/test_writing_reference_upper_layer_contracts.py tests/test_writing_reference_extraction.py tests/test_chapter_translation_pipeline.py`
  - `56 passed, 5 warnings in 0.55s`。
  - 5 个告警均为既有 PyMuPDF/SWIG deprecated type 告警。
- 包入口导出自检：8 个新增公共符号均存在于 `__all__` 且可导入。
- 上层合同文本扫描未发现 Hy-MT2 模型 ID或 `body_translation` stage。

## 残余接线点

1. OCR core/service：生成并不可变写入 PNG sidecar；为 `empty_text` 页也创建证据；新写入
   必须强校验 PNG/hash/DPI/尺寸/相对路径和自动内容门，不得依赖 legacy 默认值。
2. repository/upper-layer execution：新增 stage run 与 escalation 持久层、自动
   Flash→Pro 状态机、幂等、重启恢复和 route-specific integration 唯一约束迁移。
3. translation orchestration：direct 与 batch 共用服务器阶段执行服务；Pro 仅重跑上层
   planning 或 integration/QC，复用并逐字保持 Hy-MT2 target map。
4. API/status：只读 OCR evidence/image、stage run 查询、异常恢复 retry 和逐阶段 capability
   状态；不得接受客户端 model/provider/base URL，且 corpus selection 必须继续显示
   `not_implemented`。
5. 本 worker 未执行真实 OCR、真实模型、数据库迁移、API、浏览器或 Word 验收；这些证据不能
   由本合同测试替代。
