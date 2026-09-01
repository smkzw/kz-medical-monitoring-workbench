# Codex Conference Review: medical_writing_domain_table_designers_20260714

Date: 2026-07-14

## Verdict

**PASS（实现与回归门禁）**。本结论不包含浏览器视觉验收，也不代表任何表格内容已获医学批准。

## Boundary Compliance

- 参与者仅阅读会议上下文允许的文件，未写生产源码、未执行浏览器或临床/监管最终判断。
- 三位参与者及唯一GLM主持均在同一session内完成独立分析、质疑和修正版三轮，无fallback或替代模型。
- Codex独立读取真实方案盘点、源码、测试和运行态，保留生产写入与最终裁决权。

## Participant Outputs Reviewed

- `aishuo/MiniMax-M3`：确认4个A级领域与1个受控B级领域；强调单一表格模型、单一Word链和无项目阈值。
- `buddy/deepseek-v4-pro`：补充映射状态必须持久化，且结构错误阻断保存、语义问题阻断批准但不阻断草稿。
- `opencode-go/mimo-v2.5`：支持profile registry，但建议增加`value_type`、`required`、行角色字段及Word隐藏书签；这些建议经主持和Codex复核后判定为当前切片的过度扩张。

## Hermes Sub-Venue Review

- `buddy/glm-5.2`完成同会话三轮主持复核，比较三份独立输出并明确建议：只增加`StructuredTableColumn.semantic_role`；profile实例状态保存在`word_layout["domain_profile"]`；拒绝隐藏Word书签、`value_type`、`required`和C级领域升级。
- 主持未要求任何参与者重跑；三份输出均可用，分歧已被显式保留而非伪装成一致。

## Main-Venue Codex Review

- 接受一个后端领域profile注册表和一个前端schema-driven面板，拒绝每个领域复制一套React组件。
- 接受`objectives_endpoints`、`treatment_dose`、`laboratory_panel`、`version_history`四个A级profile，以及明确区分试验用药与CM、且不内置阈值的`dose_modification`受控profile。
- 暂不增加独立行角色字段。“层级”等由现有列语义角色及单元格值表达，当前真实证据不足以证明需要第二层行schema。
- 原始竖排或矩阵表可使用`record_axis=semantic_only`只做字段映射；模板化逐行记录使用`record_axis=rows`做必填检查。
- 结构错误阻断保存；语义映射、必填值和项目依据缺失形成审批阻断项，仍允许保存草稿。
- 不新增第二文档模型、第二导出器、隐藏书签或项目特异阈值/分析物清单。

## Codex Independent Verification

- 真实证据：从8份原始DOCX、7个适应症重新解析192张表、10,726个单元格；证据与官方标准边界记录在本切片`REAL_PROTOCOL_TABLE_PATTERN_EVIDENCE.md`和`EXTERNAL_STANDARDS_NOTES.md`。
- 三真实项目：RUX-03-002、CMS-D001、MY008211A-PNH-3-01均完成5类模板插入、保存、冷重启、重载、语义角色保留和Word导出读取。
- 医学写作相关回归：`168 passed`；全工作台回归：`872 passed`，仅保留既有SWIG弃用与Excel页眉解析警告。
- 最后补充的profile驱动日期控件由48项聚焦前端契约测试及Vite生产构建复核通过。
- 后端`compileall`通过；新API运行态健康检查为`status=ok`、SQLite `integrity_check=ok`、schema v14，领域profile接口返回5项。
- 本轮未重新打开浏览器，原因是当前执行上下文明确要求不再使用浏览器；因此只接受逻辑/构建门禁，不声称桌面视觉验收通过。

## Final Decision

会议建议经Codex删减后落地并通过回归。该切片可进入后续浏览器桌面QC和更多真实表格映射LOOP；C级模板继续使用可见、可编辑、可Word输出的通用表格设计器，不伪称已有成熟专用设计器。
