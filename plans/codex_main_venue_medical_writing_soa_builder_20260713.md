# Codex Main-Venue Plan: medical_writing_soa_builder_20260713

Date: 2026-07-13
Objective: 设计并产品化医学写作结构化表格引擎，以研究流程表为首个领域化设计器，覆盖文档内同步渲染、表格编辑、访视/程序/条件/结构化附注、版本审批和确定性Word表格导出。

## Task Decomposition

1. 建立三个本地协议库的可追溯文件目录并按项目/适应症/阶段/文件类型去重分层。
2. 从真实DOCX中提取研究流程表候选、表头、阶段、访视、程序行、符号和脚注，形成跨项目结构样本。
3. 定义通用表格契约、领域插件边界、SoA领域契约、来源角色、版本/审计和验证规则。
4. 完成临床/运营/数据/统计/前后端/Word导出多模型会商，Codex收敛实施规范。
5. 实现后端存储/API、文档编辑面板内同步表格、桌面矩阵编辑器、模块库、属性检查器、脚注台账和Word预览/导出。
6. 在RUX、D001、PNH及额外适应症真实方案上逐控件、逐逻辑点测试并LOOP。

## Immediate Deliverables

- `records/active_slices/medical_writing_soa_builder_20260713/protocol_source_inventory.jsonl`
- `records/active_slices/medical_writing_soa_builder_20260713/soa_structure_samples.json`
- `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`
- `reviews/codex_conference_medical_writing_soa_builder_20260713_review.md`
- 后续领域契约、API、前端和DOCX导出测试。

## Verification

- 来源目录数量、去重哈希、原路径、文件类型和解析状态可追溯。
- 至少六个不同项目/适应症的研究流程表结构样本。
- 所有交互数据保持结构化并可确定性导出。
- 源DOCX表格在编辑器中以真实HTML/富文本表格呈现，禁止Markdown或省略占位。
- 2048x1024内置浏览器视觉QC与真实控件交互。
- DOCX schema/内容/视觉检查以及跨项目全量回归。

## Authority

- Hermes参与者提供独立方案和批判；GLM-5.2主持子会场。
- Codex负责来源权威性、临床/监管边界、最终架构、浏览器和Word验收以及生产写入。
