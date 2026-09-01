# OCR 与上层 AI 路由共享合同 Codex 验收

日期：2026-07-25  
范围：共享合同与兼容性测试，不代表真实 OCR、真实模型、API 或浏览器验收

## 结论

接受本轮 additive contract，允许后续 OCR core、上层运行持久化和翻译编排在互不重叠的
写集内接线。合同没有新增逐页人工确认、待医学批准、文件安全或来源权利审批流程。

## 已验收边界

1. 新 OCR 页证据可记录 200 DPI PNG sidecar、图像与文本 hash、尺寸、相对路径、
   `GLM-OCR-bf16` profile、选择原因和 `empty_text`；旧记录缺少 PNG 字段时只解析为
   `legacy_metadata_only`，不得宣称存在新证据。
2. 上层阶段限定为文档规划、Hy-MT2 翻译后整合/QC、语料选择支持；不包含正文翻译。
3. Flash/Pro 路由由服务端决定。Pro 成功运行必须引用 Flash 父运行和自动升级 lineage；
   客户端 retry 合同不接受 model、provider 或 base URL。
4. Hy-MT2 仍是正文翻译唯一模型，不能进入 `plan_model` 或 `qc_model`。
5. `corpus_selection_support` 可诚实返回 `not_implemented`，不得同时宣称模型或升级能力。
6. 旧 extraction、batch item 与 chapter pipeline payload 继续可读；新增字段均有兼容默认。

## 验收证据

- `python3 -m py_compile packages/contracts/workbench_contracts/models.py packages/contracts/workbench_contracts/__init__.py tests/test_writing_reference_upper_layer_contracts.py`
- `python3 -m pytest -q tests/test_writing_reference_upper_layer_contracts.py tests/test_chapter_translation_pipeline.py tests/test_writing_reference.py`

验收通过后，后续实现仍必须分别证明：

- OCR PNG sidecar 真实落盘、hash 可复算、200 DPI、空文本页不丢证据；
- Flash→Pro 状态机的幂等、恢复和持久 lineage；
- Pro 只重跑规划或整合/QC，复用且逐字保持 Hy-MT2 target map；
- 真实 API、稳定运行服务和用户可见进度不依赖开发日志。
