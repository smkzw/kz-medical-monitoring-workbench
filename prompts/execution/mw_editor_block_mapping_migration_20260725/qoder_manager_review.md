# 医学写作编辑持久化与旧导入迁移执行经理复核

你是现有 QoderVIP 可见 `qodercli` 会话中的执行经理。模型必须保持
`qwen3.8-max-preview`。不要新建或无头启动 Qoder；不要人为限制工具、内部轮次、
上下文或输出。Codex 是最终源码、浏览器、医学和生产验收人。

## 指令与工作区

先完整读取：

- `/Users/smkzw/.codex/AGENTS.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `/Users/smkzw/.hermes/SOUL.md`
- `context/mw_editor_block_mapping_migration_20260725_context.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`

产品工作区是当前 QoderVIP 目录中的 `medical-writing-current` 符号链接；先确认该链接
解析到医学经理工作台 `implementation/workbench`，再进入。不得把 QoderVIP 安装目录
误当产品源码。

Read these files only:

- `context/mw_editor_block_mapping_migration_20260725_context.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/editorSourceMapping.js`
- `frontend/tests/editor_source_mapping_qc.mjs`
- `frontend/tests/medical_writing_interaction_qc.mjs`
- `frontend/tests/medical_writing_editor_formatting_qc.mjs`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/main.py`
- `services/api/app/medical_writing_legacy_authoring_migration.py`
- `services/api/app/medical_writing_study_consistency.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_synopsis_import.py`
- `services/api/app/medical_writing_repository.py`
- `tests/test_medical_writing_legacy_authoring_migration.py`
- `tests/test_medical_writing_study_consistency.py`
- `tests/test_medical_writing_synopsis_import.py`
- `tests/test_frontend_medical_writing_contract.py`

这是起始读取清单，不是对验证真实调用链所需相邻源码和测试的绝对禁止；额外读取必须记录
文件及理由。

## Task

这是两个已经完成首轮实现后的执行经理复核，不是泛泛审计：

1. 复现并检查 TipTap 标题边界 `Enter`、正文输入、inline marks、保存和重载的块身份。
   标题来源块必须保持 heading-only；新正文必须进入合法 paragraph/body 来源块；
   paragraph boundary、bold/underline/superscript/subscript/font/color/highlight、
   citation mark、表格和图片身份不得丢失。
2. 检查旧导入 protocol/synopsis 的正式可编辑迁移链。不得 fake bind、不得覆盖原
   DOCX、不得把重安全扫描当门槛；迁移必须从来源、项目元数据和已有提取结果形成候选
   StudyDefinition/authoring journey，经现有作者确认语义后才解除 `unbound_legacy`。
3. 重点识别“测试只看 DOM、没有保存后 GET”“测试只断言状态码、没有断言来源块身份”
   “通过客户端状态掩盖后端数据错误”“旧导入项目仍永久只读”等假绿。
4. 运行最小但决定性的 focused tests；必要时可做有界源码修复，但只允许修改任务上下文
   声明的 frontend/backend/test 写入集合。不得写运行态数据库、真实项目正文、稳定端口、
   用户文档或其他子系统；不得重启 5174/8911。
5. 共享工作区可能有其他改动。保留并兼容，禁止 broad refactor、格式化全文件或回退
   不相关修改。

## Hard boundaries

- 不得写运行态SQLite、真实项目正文、稳定端口、用户文档或其他子系统。
- 不得重启5174/8911，不得绕过产品API直接清洗运行态数据。
- 不得覆盖共享工作区中的其他修改；源码写入只限任务上下文列明的允许集合。
- 不得进行安全、后门、渗透或依赖漏洞审计；只验证功能、数据语义和医学写作可用性。
- 不得用Qoder自身生成的医学内容代替工作台正式独立AI。

## 必须给出的证据

- 读取的源码与测试文件、实际执行轮次、观察与失败路径。
- 至少一个失败前或风险复现场景，以及修复后的保存/重载 payload 级断言。
- 旧导入迁移状态机、来源只读不变量、幂等/CAS/跨项目隔离证据。
- 运行的每条测试命令和结果；不能把源字符串断言当行为验收。
- 修改文件清单、残余不确定性和 Codex 下一步真实浏览器验收建议。

Write exactly one output file:
`runs/execution/mw_editor_block_mapping_migration_20260725/qoder_manager_review.md`

最后一行必须恰好为以下之一：

- `QODER_MW_EDITOR_MIGRATION_MANAGER_READY`
- `QODER_MW_EDITOR_MIGRATION_MANAGER_BLOCKED`
