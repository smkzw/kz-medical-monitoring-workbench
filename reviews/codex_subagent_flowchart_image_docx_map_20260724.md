# 医学写作子系统“研究流程图/图像型附件 -> DOCX”只读技术与验收地图审计

- 审计日期：2026-07-24
- 审计工作区：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- 审计性质：只读技术与验收地图，不修改生产代码，不做安全/漏洞审计
- 唯一写入：本报告

## 1. 执行摘要

### 1.1 总体结论

当前系统并非“完全没有流程图/附件导出”，而是存在三条实现成熟度不同的路径：

1. **系统生成的研究流程图**：语义模块化编辑、基于已确认研究设计事实的自动预填、确定性 SVG、PNG 回退、DOCX 嵌入、图编号、图目录和书签均已实现，且有两个真实项目的浏览器及 DOCX/PDF 证据。
2. **从源 DOCX 抽取的既有图片**：PNG/JPEG 抽取、编辑器可见、不可变保存、回嵌 DOCX、题注/编号/书签均已实现，并有真实 RUX 项目测试；不支持任意 MIME，也不是通用附件上传入口。
3. **用户上传的量表/评估工具 PDF**：PDF 导入、逐页 220 DPI PNG 化、DOCX 全页嵌入、纵横向和分页预算已实现；但产品界面只显示文件名/页数/DPI，不显示附件页本身，富文本编辑器也没有 `appendix_image` 节点，因此医学撰写人员不能在系统内逐页审阅附件。附件页被明确设计为不进入“图目录”、无图编号、无页级书签。

### 1.2 P0 判定

| P0 | 判定 | 直接证据 |
|---|---|---|
| P0-1 产品内附件不可视审阅 | **存在**。上传后仅显示元数据；写作编辑器没有 `appendix_image` 映射，附件页会落入普通空内容节点，而不是可见的只读图片节点。 | `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx:2075-2089,2160-2164`；`frontend/src/App.jsx:5850-5902` |
| P0-2 当前代码缺少“真实 9 页量表 + Word 原生”的最新回归 | **存在**。2026-07-22 r7 只用合成 9 页样本通过 LibreOffice/OpenXML；Word 原生仅跑了合成 2 页样本。2026-07-20 的真实 IBDQ Word 产物早于 r7，且实页复核发现标题页与图像页分离，不能作为当前分页实现的通过证据。 | `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md:318-340`；旧实页 `.../render_word_v2_200dpi/page-22.png` 与 `page-23.png` |

**最关键的 P0 缺口**：图像型量表虽然能进入 DOCX，但尚未形成“系统内逐页可见审阅 -> 当前代码导出 -> 真实 Word 原生保存/更新域/重开 -> 页面无拆分”的闭环。后端对象存在不等于医学撰写人员能在产品中确认它，也不等于当前分页代码已用真实量表在 Word 中验收。

## 2. 审计边界与来源

### 2.1 已读取的适用规则与任务记录

- 根规则：`AGENTS.md`
- 前端规则：`frontend/AGENTS.md`
- 当前总任务记录：`records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- 流程图专项：`records/active_slices/medical_writing_study_schema_v1_20260716/TASK_RECORD.md`
- 图/表目录与源 DOCX 图片专项：`records/active_slices/medical_writing_word_indexes_crossrefs_20260716/TASK_RECORD.md`
- 量表专项：`records/active_slices/medical_writing_scale_registry_20260717/TASK_RECORD.md`
- 流程图与量表 Word 原生验收记录：`records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`

### 2.2 实际检查范围

- 后端合同、流程图提议/渲染/投影、附件导入、DOCX 生成代码
- 前端流程图编辑器、量表 PDF 入口、富文本节点映射
- 聚焦单元/API/导出/分页/源保真测试
- 已有浏览器、DOCX、OpenXML、LibreOffice、Word 原生及 200 DPI 实页证据
- 公司参考方案：
  - `模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
  - `模版/方案模版/MG-K10-青少年AD-3期方案V1.0-20251105-clean.docx`
  - `模版/方案模版/CMS-D005-减重II期临床试验方案概要-V0.3-KZYY0525-clean-DIP0526-KZYY0526 (2).docx`
  - `CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`

### 2.3 本次现场验证

以禁止 pytest cache、禁止 Python bytecode 的方式执行以下 8 个聚焦测试文件：

```text
tests/test_medical_writing_study_schema.py
tests/test_medical_writing_study_schema_api.py
tests/test_medical_writing_study_schema_figure_projection.py
tests/test_medical_writing_figure_exporter.py
tests/test_medical_writing_document_exporter.py
tests/test_medical_writing_instrument_appendix.py
tests/test_medical_writing_docx_pagination.py
tests/test_medical_writing_source_preserving_export.py
```

结果：**80 tests collected；本次聚焦执行无失败**。该结果证明代码级合同仍成立，不替代 Word 实页及产品端可用性验收。

## 3. 能力地图

| 能力 | 状态 | 结论 |
|---|---|---|
| 流程图研究部分/节点/关系模块化编辑 | 已实现 | 独立语义对象，不是自由画布 |
| 流程图自动预填 | 已实现但需准确命名 | 由已确认 StudyDefinition/装配计划确定性生成；不是流程图端独立 LLM 调用 |
| 流程图 SVG/矢量输出 | 已实现 | 确定性 SVG；DOCX 同时嵌入 SVG 和 PNG fallback |
| 流程图 DOCX 嵌入 | 已实现并测试 | 图题、`SEQ 图`、图目录、稳定书签均存在 |
| 流程图浏览器可见/编辑 | 已实现并测试 | PNH、D017 两真实项目通过普通/全屏/保存/重载 |
| PDF 量表导入 | 已实现 | 仅 PDF；1-100 页；最多 50 MB |
| PDF 页面分辨率 | 已实现并测试 | 最低 200 DPI，前端固定请求 220 DPI |
| PDF 页面 DOCX 嵌入 | 已实现 | 每页转 PNG，全页嵌入，保持宽高比 |
| PDF 页面纵横向/分页 | 代码和合成测试已实现 | r7 覆盖 1/2/9 页和横向页；真实 9 页 Word 当前代码回归缺失 |
| PDF 页面产品内可见性 | **未实现** | 只有文件名、页数、DPI；无缩略图/逐页预览；编辑器无附件图片节点 |
| PDF 页面图目录/图编号 | 明确未实现 | `indexed=False`；测试明确断言无 `SEQ 图`、无图目录 |
| PDF 页面书签 | 未实现 | 无页级或附件级书签 |
| 任意 PNG/JPEG 附件直接上传 | 未实现 | 当前上传入口只接受 PDF |
| 源 DOCX 中已有 PNG/JPEG 图片 | 已实现并测试 | 可抽取、编辑器可见、不可变保存、编号/书签后回嵌 |
| 源 DOCX 中 EMF/WMF/SVG 图片 | 未实现 | 当前回嵌只允许 PNG/JPEG |

## 4. 问题 1：研究流程图是否已有模块化编辑、AI 预填、SVG/矢量输出、DOCX 嵌入

### 4.1 模块化语义编辑：已实现

合同层将流程图拆为：

- `MedicalWritingStudySchemaPart`
- `MedicalWritingStudySchemaNode`
- `MedicalWritingStudySchemaEdge`
- `MedicalWritingStudySchemaDefinition`
- 独立的 `MedicalWritingStudySchemaPresentation`

证据：

- 图对象的 part/node/edge 数量、引用完整性、dose cohort 关系约束：`packages/contracts/workbench_contracts/models.py:3978-4024`
- 布局偏移独立于临床语义，范围限制为横向 ±48、纵向 ±32：`packages/contracts/workbench_contracts/models.py:4027-4049`
- 前端提供“研究部分/节点/关系”三个面板，可新增、删除、修改和确认：`frontend/src/features/medical-writing/StudySchemaEditor.jsx:469-580`
- 前端支持自动排布、缩放、最大化、撤销/重做、影响预览、插入/更新方案：`frontend/src/features/medical-writing/StudySchemaEditor.jsx:478-503`
- 节点位置只能做有限微调：`frontend/src/features/medical-writing/StudySchemaEditor.jsx:422-435,568`

该实现符合任务记录中的产品边界：“语义模型自动布局，允许有限拖动；不做自由画布”，见 `records/active_slices/medical_writing_study_schema_v1_20260716/TASK_RECORD.md:8-17`。

### 4.2 自动预填：已实现，但不是流程图端独立 LLM 生成

`propose_study_schema` 的输入来自已完成的 framing/PICOS 和已确认的装配计划投影；它按结构化事实确定性生成候选图：

- 必须先完成 framing/PICOS：`services/api/app/medical_writing_authoring_journey.py:1186-1197`
- 读取已确认设计投影并计算当前事实哈希：`services/api/app/medical_writing_authoring_journey.py:1195-1207`
- I 期按选定 Parts 自动生成：`services/api/app/medical_writing_authoring_journey.py:1215-1228`
- 支持 SAD、MAD、食物影响、物质平衡、肝功能不全、肾功能不全、DDI、首次患者：`services/api/app/medical_writing_authoring_journey.py:3670-3710`
- SAD/MAD 自动建立筛选、剂量队列、安全审查门、后续剂量队列和随访：`services/api/app/medical_writing_authoring_journey.py:3782-3910`

因此应将其称为**“设计事实驱动的自动预填/候选图生成”**。上游研究框架可以由独立 AI 从摘要或调研资料预填，但本函数没有直接调用 LLM；这不是缺陷，反而减少了流程图拓扑被模型凭空补全的风险。若产品文案写“AI 生成流程图”，应明确 AI 作用在上游事实提取与建议，流程图本身由受控规则投影。

### 4.3 SVG 与 PNG：已实现

- SVG 根据排序后的 parts/nodes/edges 确定性生成：`services/api/app/medical_writing_study_schema.py:204-395`
- 支持多 Part、横/纵向布局、节点类型配色、关系类型与箭头、关系标签和注释：同上 `:212-394`
- 中英文节点文本做 East Asian Width 换行并限制 4 行：`services/api/app/medical_writing_study_schema.py:398-449`
- 服务器把受控 SVG 栅格化为 1x/2x/3x PNG fallback：`services/api/app/medical_writing_study_schema.py:452-552`

### 4.4 DOCX 嵌入、编号、目录、书签：已实现

DOCX 使用“PNG 作为 DrawingML 基础图 + `asvg:svgBlip` 指向 SVG part”的双载荷：

- SVG content type、SVG namespace、Office SVG extension namespace：`services/api/app/medical_writing_figure_exporter.py:21-24`
- 先插入 PNG，再添加 SVG part 和关系：`services/api/app/medical_writing_figure_exporter.py:36-87`
- 在 fallback `a:blip` 下写入 `a:extLst/a:ext/asvg:svgBlip`：`services/api/app/medical_writing_figure_exporter.py:218-246`
- 导出器校验 SVG/PNG 哈希后写入：`services/api/app/medical_writing_document_exporter.py:3198-3269`
- 生成 `SEQ 图`、稳定 bookmark 和图题：`services/api/app/medical_writing_document_exporter.py:3271-3299`
- 有图时生成图目录域：`services/api/app/medical_writing_document_exporter.py:3004-3053`
- 根据画布宽度和节点数量选择纵向或横向并按高宽比约束：`services/api/app/medical_writing_document_exporter.py:3716-3763`

关键测试：

- `test_document_target_embeds_svg_with_png_fallback_and_correct_ooxml_package`
- `test_governed_study_schema_exports_svg_png_caption_bookmark_and_figure_metadata`
- `test_governed_study_schema_figure_adds_only_relationship_content_type_and_media_parts`
- `test_multiple_governed_figures_receive_distinct_svg_parts_and_may_share_identical_png_fallback`
- `test_wide_flowchart_context_and_caption_share_one_landscape_layout_group`

### 4.5 既有真实证据

- PNH：7 节点、7 关系；D017 I 期：16 节点、28 关系；两者均正式投影成功，见 `records/active_slices/medical_writing_study_schema_v1_20260716/real_projects_qc/real_projects_api_qc.json`。
- 浏览器报告 `records/active_slices/medical_writing_study_schema_v1_20260716/browser_qc/browser_qc_report.json`：`passed=true`，PNH/D017 均完成初始、全屏、重载，运行时异常和控制台错误为空。
- DOCX/PDF 视觉报告：
  - D017：18 页，366/366 个中文文本 span 可见；
  - PNH：17 页，328/328 个中文文本 span 可见；
  - 证据分别为 `.../d017_render/visual_qc_report.json`、`.../pnh_render/visual_qc_report.json`。
- r7 Word 原生样本第 2 页实际显示流程图、图题和页眉页脚：`records/active_slices/medical_writing_production_rebaseline_20260722/docx_layout_qc/word_e5/rendered/page_02.png`。

## 5. 问题 2：图片型量表/附件的实现与测试状态

### 5.1 导入边界

当前产品入口是“已确认量表/评估工具的原始 PDF”，不是通用图片附件管理器：

- 后端只接受 PDF，1-100 页、最多 50 MB：`services/api/app/medical_writing_instrument_appendix.py:13-16,76-120`
- 每页用 `pypdfium2` 按 DPI 转为 RGB PNG：`services/api/app/medical_writing_instrument_appendix.py:122-175`
- API 只允许写入已确认研究设计中的量表，并按语义章节定位：`services/api/app/main.py:4586-4640`
- 同一量表再次上传时替换既有页，不叠加：`services/api/app/main.py:4662-4700`
- 前端文件选择器明确只接受 PDF：`frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx:2160-2164`

结论：

- **PDF 量表/附件导入：已实现。**
- **直接上传 PNG/JPEG/TIFF 等图片附件：未实现。**
- **从源 DOCX 读取其既有 PNG/JPEG：另有独立路径，见 5.7。**

### 5.2 分辨率：已实现并测试

- 最低 DPI：200；默认：220：`services/api/app/medical_writing_instrument_appendix.py:13-16`
- 后端拒绝低于 200 DPI：`services/api/app/medical_writing_instrument_appendix.py:91-94,216-220`
- 前端固定提交 220 DPI：`frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx:2109-2133`
- `test_pdf_instrument_appendix_renders_each_page_above_200_dpi` 验证 220 DPI 两页图像均至少 1800 x 2500 像素：`tests/test_medical_writing_instrument_appendix.py:42-63`
- `test_pdf_instrument_appendix_rejects_low_dpi_and_non_pdf`：`tests/test_medical_writing_instrument_appendix.py:66-81`

### 5.3 DOCX 嵌入和页面布局：代码已实现

- 每页标题格式为“原始附件第 x/y 页”，标题与图像保持在一起：`services/api/app/medical_writing_document_exporter.py:3387-3453`
- 图片按可用宽度、页眉页脚边界、标题高度和宽高比计算尺寸：`services/api/app/medical_writing_document_exporter.py:3579-3693`
- 横图自动使用横向分节；纵图沿用正文纵向版式：同上 `:3591-3629`
- 导出 metadata 记录页码、DPI、源 PDF 哈希、图像哈希、方向和实际宽度：`services/api/app/medical_writing_document_exporter.py:3455-3470`

关键测试：

- `test_pdf_instrument_appendix_exports_as_unindexed_full_page_word_images`
- `test_appendix_pages_use_title_page_breaks_without_separator_paragraphs`
- `test_libreoffice_appendix_title_and_source_image_share_exactly_one_page`
  - 参数覆盖近方形 1 页、标准纵向 2 页、横向 1 页、标准纵向 9 页：`tests/test_medical_writing_docx_pagination.py:378-426`

### 5.4 可见性：产品闭环未完成

上传入口获取了完整 `appendix_image` blocks，但只保存第一页的文件名、页数、DPI 和状态：

- 工作副本中筛选到附件页：`frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx:2070-2079`
- 随后只提取元数据，没有保存/显示 `image_base64`：同文件 `:2080-2089`
- 页面只渲染文件名、页数、DPI：同文件 `:2160-2164`

富文本编辑器只专门识别 `source_docx_image` 和表格：

- `source_docx_image` 映射为可见图片节点：`frontend/src/App.jsx:5850-5865`
- 表格单独映射：`frontend/src/App.jsx:5867-5885`
- 其他 block（包括 `appendix_image`）统一落入 heading/paragraph/sourceBlock：`frontend/src/App.jsx:5886-5902`

因此，量表附件在后端工作副本和 DOCX 中存在，但医学撰写人员在系统写作界面中看不到实际页面。现有前端测试 `test_captioned_source_docx_images_render_as_immutable_document_blocks` 只验证源 DOCX 图片，不验证 `appendix_image`。

### 5.5 图目录、编号、书签：量表页明确没有

量表页合同将 `indexed` 固定为 `False`：

- block 创建：`services/api/app/medical_writing_instrument_appendix.py:32-73`
- 校验要求附件页不可编辑且不索引：`services/api/app/medical_writing_instrument_appendix.py:178-205`
- 导出 metadata 继续记录 `indexed=False`：`services/api/app/medical_writing_document_exporter.py:3455-3470`
- `test_pdf_instrument_appendix_exports_as_unindexed_full_page_word_images` 明确断言：
  - `figure_count == 0`
  - 无 `SEQ 图`
  - 无图目录域
  - 见 `tests/test_medical_writing_instrument_appendix.py:97-160`

判定：

- **量表页不应被误记为普通“图”**，当前“不进入图目录”是有意设计，不是漏写图编号。
- 但目前也没有“附件目录”、附件级书签或页级书签。若医学用户需要从正文或目录跳转到量表，宜增加一个**附件级书签/附件目录项**，而不是把 9 页量表编号为 9 张普通图。

### 5.6 真实 Word 验收证据存在版本断层

#### 旧真实 IBDQ 验收件

`records/active_slices/mw_study_schema_scale_docx_20260720/acceptance_outputs/real_research_flow_and_ibdq_appendix.docx` 包含：

- 2 个 SVG；
- 11 个 PNG（2 个流程图 fallback + 9 个量表页）；
- 2 个 `asvg:svgBlip`；
- 11 个 DrawingML 图形。

其 Word 原生 PDF 和 200 DPI 页面证明真实 IBDQ 内容曾被嵌入。但本次逐页打开发现：

- `page-22.png`：只有“炎症性肠病问卷（IBDQ）（原始附件第 6/9 页）”标题，无量表图像；
- `page-23.png`：才出现 IBDQ 第 6/9 页内容。

这与 `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md:1266-1275` 中“第22页仍显示 IBDQ 原始附件第6/9页”的文字结论冲突。该旧产物应改判为**证明真实内容可嵌入，但分页失败**，不能作为发布通过证据。

#### 当前 r7 分页证据

- 2026-07-22 r7 合成 2 页与合成 9 页均在 LibreOffice/PDF 中做到标题和图片同页，9 页连续位于第 2-10 页；OpenXML Microsoft 365 ErrorCount=0：
  - `records/active_slices/medical_writing_production_rebaseline_20260722/docx_layout_qc/appendix_pagination_r7_acceptance_report.json`
  - `.../openxml_validation_r7_2page.json`
  - `.../openxml_validation_r7_9page.json`
- r7 Word 原生 E5 只覆盖合成 2 页，见 `TASK_RECORD.md:330-340` 和 `word_e5/rendered/page_03.png`、`page_04.png`。

所以当前正确表述是：

> 分页算法已在合成 1/2/9 页和横向页通过代码、LibreOffice 与 OpenXML 验证；当前 r7 已在 Word 原生通过合成 2 页，但尚未以真实 9 页 IBDQ 在 Word 中重新完成更新域、保存、关闭、重开及逐页视觉验收。

### 5.7 源 DOCX 图片是另一条已完成路径

源 DOCX 图片抽取：

- 读取 DrawingML 图片关系、字节、MIME、尺寸、替代文字和题注：`services/api/app/protocol_text_extractor.py:310-395`
- 物化为 `source_docx_image`：`services/api/app/medical_writing_document.py:470-504`
- 编辑器显示为不可编辑图片节点：`frontend/src/App.jsx:195-235,5850-5865`
- 导出器仅允许 PNG/JPEG 并生成编号/书签：`services/api/app/medical_writing_document_exporter.py:3315-3384`

真实测试：

- `test_parse_real_rux_protocol_extracts_title_related_source_text` 读取 RUX 的“表 8 SCORAD-主观症状评分”PNG：`tests/test_protocol_text_extractor.py:428-464`
- `test_rux_source_docx_image_table_is_immutable_and_survives_restart`：`tests/test_medical_writing_working_copy_persistence.py:1190-1285`
- `test_rux_static_table_list_is_replaced_by_dynamic_toc_and_seq_bookmarks` 验证图片回嵌和 `SEQ 表`：`tests/test_medical_writing_document_exporter.py:193-221`

边界：当前不支持源 DOCX 中的 EMF/WMF/SVG 回嵌；专项记录也明确只支持 PNG/JPEG，见 `records/active_slices/medical_writing_word_indexes_crossrefs_20260716/TASK_RECORD.md:71-75`。

## 6. 问题 3：当前 DOCX 生成路径对 SVG 的真实支持边界

### 6.1 实际 OOXML 机制

系统没有把 SVG 转成普通 PNG 后丢弃矢量信息，而是：

1. 通过 python-docx 插入 PNG，形成标准 `a:blip` fallback；
2. 在 DOCX package 中增加 `/word/media/imageN.svg`；
3. 增加 `image/svg+xml` content type；
4. 在 PNG blip 的扩展列表中增加 `asvg:svgBlip r:embed="..."`；
5. 现代 Word 使用 SVG；不识别该扩展的渲染器继续显示 PNG。

代码证据：`services/api/app/medical_writing_figure_exporter.py:36-87,218-246`。

### 6.2 Word 兼容性

Microsoft 官方支持页明确列出 Word for Microsoft 365、Word 2019、Word 2021、Word 2024 及对应 Mac 版本支持插入和编辑 SVG：

- <https://support.microsoft.com/en-US/Office/graphics-visuals/edit-svg-images-in-microsoft-365>

需要区分：

- `ASVG_NAMESPACE` 中出现 `2016` 是 OOXML 扩展命名空间的一部分，**不能单凭该字符串推断所有 Word 2016 产品版本都原生渲染 SVG**。
- 本系统的发布安全边界来自 PNG fallback；即使 SVG 扩展不被识别，图仍应作为 PNG 显示。
- 现有 Word 原生证据来自当前 macOS 上的 Microsoft Word/Microsoft 365，不等于 Windows 各版本、WPS、Pages 或所有第三方渲染器都已实测。

### 6.3 当前仅支持受控流程图 SVG，不是通用 SVG 附件

- 流程图 SVG 由服务器自己的受控模板生成，元素主要为 `svg/defs/marker/rect/path/text/g`。
- PNG rasterizer只处理本系统所需的矩形、路径和文字，并明确拒绝 `image/use/script/foreignObject` 及外部引用：`services/api/app/medical_writing_study_schema.py:452-552`。
- DOCX figure exporter虽做通用 XML/引用检查，但上层只允许 `figure_kind == "study_schema"` 的受治理图对象：`services/api/app/medical_writing_document_exporter.py:3198-3214`。
- 当前没有“用户上传任意 SVG 并嵌入 DOCX”的产品能力。

### 6.4 字体与视觉边界

- SVG 中声明 `Times New Roman, SimSun, Songti SC` 字体栈：`services/api/app/medical_writing_study_schema.py:24-29`。
- PNG fallback 在本机用宋体候选与 Times New Roman 栅格化：`services/api/app/medical_writing_study_schema.py:574-606`。
- SVG 本身不嵌入字体文件；现代 Word 的矢量文字视觉仍依赖目标机器实际字体和 Word 的 fallback 行为。

现有 PNH/D017 PDF 视觉报告证明当前 Mac 环境可见，但尚无 Windows Word 的字体/矢量一致性矩阵。该项为 P1 兼容性扩展，不阻断本地 Mac 使用；PNG fallback 仍需保留。

## 7. 参考模板核对结果

### 7.1 D017 I 期方案

`CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`：

- 正文有“图 1.研究设计概况”；
- OOXML 中研究设计内容位于方案摘要大表格内，由多个 Drawing/VML 对象组合，不是单一 SVG；
- 这与当前系统“语义对象 -> 单一受治理矢量图”实现方式不同，但语义上均表达 SAD/MAD Parts、剂量组、哨兵、安全审查和随访。

因此，参考模板应控制**信息结构、图题和公司视觉层级**，不应反向要求系统复刻不可维护的 VML 拼图。

### 7.2 MG-K10 青少年 AD III 期方案

OOXML 实际观察：

- “图 1.研究设计示意图”为 1286 x 456 PNG；
- 附录量表含 606 x 91 JPEG、617 x 806 PNG、617 x 170 PNG；
- 同一量表可能由多张不同高度图片组成。

这证明附件验收不能只测标准 A4 纵向页；至少要覆盖：

- 极宽流程图；
- 近方形图片；
- 很矮的横条图片；
- 单个量表由多张图片组成；
- 版权/来源文字在页底且必须可读。

### 7.3 D005 与 PNH 方案摘要

两份摘要未形成可直接复用的流程图图片；不应因缺少图形而硬生成无依据拓扑。流程图候选仍应由已确认研究设计事实驱动。

## 8. 问题 4：最小实现切片与精确文件写入范围

以下为后续建议，不属于本次只读审计的实际修改。

### Slice P0-A：让附件页在产品内可见、只读、可逐页审阅

**目标**：上传或重开项目后，医学撰写人员能看到所有附件页缩略图，点击查看原分辨率页面，并在写作编辑器相应章节看到不可编辑附件页；不改变现有后端 block 合同。

**最小生产写入范围**：

1. `frontend/src/App.jsx`
   - 增加 `appendix_image` 到 TipTap 只读图片节点的映射；
   - 保存时保持 block 原始 payload，不把附件节点当普通段落；
   - 节点属性至少包含 `sourceBlockId/instrumentId/pageNumber/pageCount/title/src/alt`。
2. `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
   - 保留已读取的 `pages`；
   - 增加页缩略图、页码、点击放大和上传后立即预览；
   - 不复制内部 block id 到主界面。
3. `frontend/src/styles.css`
   - 增加附件页网格、缩略图、全屏查看、不可编辑态样式；
   - 桌面端优先，保证 1440 x 900 和 1920 x 1080。
4. 可选新文件：`frontend/src/features/medical-writing/AppendixImageNode.js`
   - 若不继续扩大 `App.jsx`，将 TipTap node 独立封装。

**测试写入范围**：

1. `tests/test_frontend_medical_writing_contract.py`
   - `appendix_image` 必须映射为图片节点；
   - 保存不能删除/改写图像 payload；
   - 量表页不能错误进入普通 figure index。
2. 新增 `tests/test_medical_writing_instrument_appendix_api.py`
   - 使用真实 HTTP 路由测试 PDF 上传、替换、重开、错误章节拒绝、并发 revision。
3. 新增浏览器验收脚本/证据目录时，只允许写入对应 active slice 的 `browser_qc/`，不得混入生产代码目录。

**后端生产代码**：本切片原则上不需要修改。现有 API 已返回完整 working copy 和附件页 payload。

### Slice P0-B：用当前 r7 代码重新完成真实 9 页量表的 Word 原生发布门

**目标**：证明当前代码，而不是 2026-07-20 旧产物，能把真实 IBDQ 9 页连续输出为 9 个标题+图像同页的附件页。

**生产代码写入范围**：无；先作为验收切片执行。

**验收产物写入范围**：

- 新建一个独立 active slice，例如：
  - `records/active_slices/medical_writing_real_scale_word_e5_20260724/`
- 只写：
  - 当前代码生成的 DOCX；
  - Word 更新域、保存、关闭、重开后的 DOCX；
  - Word 原生 PDF；
  - 200 DPI 页面；
  - OpenXML 验证 JSON；
  - 页级验收 JSON 与 TASK_RECORD。

**失败时才允许修改**：

- `services/api/app/medical_writing_document_exporter.py`
- `tests/test_medical_writing_docx_pagination.py`
- `tests/test_medical_writing_instrument_appendix.py`

禁止在没有复现当前代码失败前继续改分页算法。

### Slice P1：附件级导航，不把量表页伪装成普通图

**目标**：为整份量表建立一个稳定书签和可选“附件目录”条目；不为每页生成 `SEQ 图`。

**精确生产写入范围**：

- `services/api/app/medical_writing_document_exporter.py`
- `packages/contracts/workbench_contracts/models.py`（仅在确需正式附件索引合同字段时）
- `frontend/src/App.jsx`（仅在需要正文插入附件交叉引用时）

**测试范围**：

- `tests/test_medical_writing_instrument_appendix.py`
- `tests/test_medical_writing_document_exporter.py`
- `tests/test_medical_writing_docx_pagination.py`

### Slice P1：可选的直接图片附件导入

只有在产品确认需要跳过 PDF、直接上传 PNG/JPEG 时再做。当前真实方案显示同一量表可由多张图片组成，因此需先确定：

- 多张图的顺序；
- 每张图是否独立成页；
- 是否保留源像素/DPI；
- 是否需要用户输入页标题；
- TIFF/EMF/WMF 是否转换。

不要把该能力与已完成的 PDF 量表入口混改。

## 9. 验收测试矩阵

| 编号 | 对象 | 场景 | 必须验证 | 当前状态 |
|---|---|---|---|---|
| F-01 | 流程图 | D017 I 期 SAD+MAD 多 Part | 节点/关系/安全门、全屏、保存重载、横向 Word | 已有 |
| F-02 | 流程图 | PNH 随机平行研究 | 分臂、随访、纵向 Word、保存重载 | 已有 |
| F-03 | 流程图 | 转组 + OLE | 继续治疗与转组关系不混淆，未知条件不被批量确认 | 代码/测试已有；建议加入最终 E2E |
| F-04 | 流程图 | 相同事实和布局重复生成 | SVG 字节和哈希完全相同 | 已有单测基础 |
| F-05 | 流程图 | SVG 主图 + PNG fallback | DOCX 同时有 SVG/PNG、关系和 content type 正确 | 已有 |
| F-06 | 流程图 | Word Microsoft 365 Mac | SVG 可见、缩放不失真、图题同页、目录/书签可跳转 | 部分已有；跳转需最终整包 E5 |
| F-07 | 流程图 | 不识别 SVG 扩展的渲染器 | PNG fallback 可见 | LibreOffice/PDF 已有 |
| A-01 | PDF 附件 | 1 页近方形 | 标题与图同页，无空白页 | 已有合成 |
| A-02 | PDF 附件 | 2 页纵向 | 连续 2 页、页眉页脚、后续正文恢复 | Word 合成 E5 已有 |
| A-03 | PDF 附件 | 1 页横向 | 自动横向、后续正文恢复纵向 | LibreOffice 合成已有 |
| A-04 | PDF 附件 | 9 页纵向 | 连续 9 页、每页标题+图同页、无孤立标题/空白页 | LibreOffice 合成已有；真实 Word 当前代码缺失 |
| A-05 | PDF 附件 | 真实 IBDQ 9 页 | 题号、复选框、版权、页码均可读；Word 保存重开后不拆页 | **P0 未完成** |
| A-06 | PDF 附件 | 产品内上传后重开 | 缩略图齐全、逐页放大、顺序正确、替换后刷新 | **P0 未实现** |
| A-07 | PDF 附件 | 低于 200 DPI/非 PDF/超页数/超大小 | 明确失败，不生成半成品 | 单元边界部分已有；API E2E 待补 |
| A-08 | PDF 附件 | 图目录/编号 | 不产生 `SEQ 图`；若启用附件导航，只生成附件级书签 | 前半已测试；附件级书签未实现 |
| S-01 | 源 DOCX 图片 | RUX PNG 表格图片 | 抽取、编辑器可见、不可变、回嵌、表编号/书签 | 已有真实项目测试 |
| S-02 | 源 DOCX 图片 | JPEG | 抽取和回嵌 | 代码支持，需保留样例 |
| S-03 | 源 DOCX 图片 | EMF/WMF/SVG | 明确提示不支持或受控转换 | 未实现 |
| R-01 | 参考模板 | MG-K10 宽流程图 | 宽图可读、图题规范 | 待纳入最终 E2E |
| R-02 | 参考模板 | 多张不同高度量表图 | 顺序、分页、版权文字、可见性 | 待纳入最终 E2E |
| W-01 | Word 字段 | 目录/图目录/书签 | 更新域后页码正确，可点击跳转 | 流程图对象级已有；最终整包 E5 待补 |
| W-02 | Word 兼容 | Microsoft 365 Mac + Windows | SVG 主图、字体、fallback 一致 | Mac 部分已有；Windows 未测 |

## 10. 发布门建议

### 必须先关闭

1. `appendix_image` 在写作编辑器和量表入口中逐页可见。
2. 当前 r7 代码用真实 IBDQ 9 页完成 Word 原生更新域、保存、关闭、重开、PDF 和 200 DPI 逐页验收。
3. 验收明确证明 9 个附件源页对应 9 个连续 Word 页面；不存在标题空页、图片独立页或额外空白分隔页。

### 可以后置

1. Windows Word 的跨平台 SVG 字体矩阵。
2. 源 DOCX 的 EMF/WMF/SVG 转换。
3. 通用 PNG/JPEG 多图上传。
4. 附件级目录和正文交叉引用。

## 11. 最终判定

### 对问题 1 的直接回答

- 模块化编辑：**是**。
- AI 预填：**有设计事实驱动的自动预填；流程图端不是独立 LLM 调用**。
- SVG/矢量输出：**是**。
- DOCX 嵌入：**是，SVG 主图 + PNG fallback，并有图编号、图目录、书签**。

### 对问题 2 的直接回答

- PDF 导入：**是**。
- 产品内实际页面可见性：**否，仅显示元数据**。
- 分辨率：**是，最低 200 DPI，默认 220 DPI**。
- 分页：**代码和合成测试已实现；当前真实 9 页 Word 回归未闭环**。
- 图目录/图编号/书签：
  - 流程图：**已实现**；
  - 量表附件页：**明确不进入图目录、无图编号、无书签**。

### 对问题 3 的直接回答

当前 DOCX 对 SVG 的真实支持是：**受控服务器 SVG 作为 Office SVG 扩展嵌入，PNG 作为标准 DrawingML fallback**。现代 Word 2019/2021/2024/Microsoft 365（含 Mac）有官方 SVG 支持；其他渲染器依赖 PNG。该能力不是通用任意 SVG 上传器，字体也未嵌入 SVG。

### 对问题 4 的直接回答

最小实现应先做两个 P0：

1. 仅补前端附件页可见审阅，不改后端合同；
2. 不先改生产代码，直接用当前 r7 对真实 9 页 IBDQ 重跑 Word 原生发布门，复现失败后才限定修改导出器与对应分页测试。

