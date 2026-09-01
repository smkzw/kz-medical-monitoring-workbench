# 医学写作子系统 Word 生成与导出引擎对比

日期：2026-07-18  
状态：技术选型与实物 POC 已完成；商业引擎正式否决；免费生产链已落地

## 1. 结论

当前链路并不是使用 LibreOffice 生成 DOCX：

- `python-docx + 直接 OOXML` 负责新建方案 DOCX、既有方案的定位修改和
  Word 字段、书签、关系部件等扩展；
- LibreOffice 仅用于无界面的 PDF/逐页 PNG 渲染和确定性视觉 QC；
- Microsoft Word 原生应用负责最终可打开性、是否触发修复、字段和实际
  分页验收。

商业引擎不得进入生产。Aspose.Words、Syncfusion DocIO、GemBox、
Telerik 等只完成了否决性 POC：其持续、无水印、无限制生产使用需要
额外商业许可，且本项目实测还出现了 schema 或格式漂移。docx4j 主库虽为
开源，但不能提供 Word 分页权威，当前也没有足以抵消新增 Java sidecar
复杂度的收益，因此不进入本轮生产链。

不建议把下列方案作为唯一生产生成器：

- **Open XML SDK**：适合作为严格 OOXML 结构生成/验证 sidecar，但没有
  Word 分页排版引擎，也不会替系统完成目录页码等版式依赖型字段结果；
- **Microsoft Word 自动化**：可作为本地发布终验金标准，但 Microsoft
  明确不支持无人值守服务端 Office 自动化，不适合未来内网多用户后端；
- **LibreOffice**：可继续做跨平台渲染烟测，但不能替代 Word 版式结论；
- **GemBox.Document**：官方文档明确指出，DOCX 输出中的 TOC 页码默认值
  为 1，页码自动更新主要发生在 PDF/XPS/图片输出，不适合作为本项目主
  生成器；
- **Telerik RadWordsProcessing**：支持更新的字段类型有限，其他字段主要
  依赖打开文档的客户端更新，不满足目录、图目录、表目录预生成要求。

最终架构是“双轨导出 + 免费结构门 + Word 桌面终验”：

- **既有 DOCX 导入项目**：继续使用当前源保真路径。未修改导出保持源包
  字节一致；修改仅落在目标段落、表格单元格及必要关系部件。任何第三方
  DOM 往返保存都必须先证明不会重写样式、编号、主题、页眉页脚、批注、
  域、书签、媒体和自定义 XML。
- **从零新建项目**：继续使用公司模板优先的
  `python-docx + 受控 OOXML` 组合、字段和样式生成。
- **结构验证**：增加 Open XML SDK `OpenXmlValidator` sidecar，专门发现
  Word 可能容忍或修复、但不符合 ISO/IEC 29500 的节点层级和包关系错误。
- **发布验收**：Microsoft Word 继续作为最终版式基准；LibreOffice 只保留
  为跨平台差异层，不拥有放行权。

## 2. 当前链路的实测基线

当前绿地 RA 生产候选：

- 文件：
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/greenfield_ra_production.docx`
- SHA-256：
  `6e5c4d95188f98f5f5c332371ce3bd596d85030cfc87459b8aece0e1d392c5e6`
- LibreOffice：11 页；200 DPI 全页渲染；11/11 页页码正确；2 个横向页面；
  研究流程图可见；894/894 个中文文本 span 可见。
- Microsoft Word：10 页；`OpenAndRepair=false` 可打开；6 个字段、1 个目录
  域和 2 个图表目录域可识别。
- 已观察到 Word 与 LibreOffice 页数不同，因此 LibreOffice 不能作为分页
  与目录页码的最终依据。
- 近期曾发现 Word 字段的 `w:fldChar`/`w:instrText` 被直接写在 `w:p`
  下。LibreOffice 可容忍，但 Word 会拒绝或触发修复。修复为每个字段节点
  均置于 `w:r` 后，Word 原生无修复打开。这说明当前方案的主要短板不是
  段落、表格 API，而是复杂 OOXML 语义需要额外的标准验证和真实 Word
  验收。

## 3. 候选引擎能力矩阵

评分：5=高度匹配；4=较匹配但需实测；3=可用但有明显边界；2=需大量
补充；1=不适合作为该能力的主引擎。

| 引擎 | 复杂 DOCX DOM | 目录/图表目录/字段更新 | 自带分页渲染 | 中文字体可控 | 源 DOCX 往返保真 | 私有化后端 | 许可 | 项目结论 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 当前 `python-docx + OOXML` | 3 | 2 | 1 | 4 | 5（定位最小修改） | 5 | 开源 | 保留源保真路径；补标准验证 |
| Open XML SDK | 5 | 1 | 1 | 3 | 4 | 5 | 开源 | 作为验证/低层操作 sidecar |
| Aspose.Words | 5 | 5 | 5 | 5 | 3 | 5 | 商业 | 绿地主引擎首选 POC |
| Syncfusion DocIO | 5 | 5 | 4 | 4 | 3 | 5 | 商业 | 第二候选 POC |
| docx4j 11.5.4+ | 5 | 4 | 3 | 3 | 4 | 5 | 开源/部分商业扩展 | 开源备选 |
| GemBox.Document | 4 | 2 | 4 | 4 | 3 | 5 | 商业 | TOC 页码边界不匹配 |
| Telerik RadWordsProcessing | 4 | 2 | 3 | 4 | 3 | 5 | 商业 | 字段更新覆盖不足 |
| LibreOffice headless | 3 | 3 | 3 | 3 | 2 | 4 | 开源 | 只作渲染差异层 |
| Microsoft Word 原生自动化 | 5 | 5 | 5 | 5 | 5 | 1 | Office 许可 | 只作交互式终验 |

### 3.1 当前 `python-docx + OOXML`

优势：

- 与现有 Python/FastAPI 代码直接集成；
- 段落、样式、表格、节、页眉页脚等普通能力稳定；
- 可对既有 DOCX 执行最小粒度、可审计修改；
- 未修改源文档可直接字节透传，这是其他 DOM 往返引擎不自然具备的优势。

边界：

- 官方仅支持内联图片，浮动对象、复杂 DrawingML、字段和交叉引用等常需
  直接操作 OOXML；
- 不提供分页引擎，无法自行计算 Word 的真实页码、目录页码和跨页布局；
- 直接 OOXML 容易出现结构上可被部分软件容忍、却被 Word 拒绝的错误。

### 3.2 Open XML SDK

优势：

- Microsoft 官方、强类型、直接对应 ISO/IEC 29500；
- 适合构造和验证 package、part、relationship、WordprocessingML 节点；
- 很适合补上当前直接 OOXML 修改缺少严格 schema 验证的问题。

边界：

- 本质是 Open XML 包操作 SDK，不是 Word 排版引擎；
- 无法仅凭 SDK 得到与 Word 完全相同的分页、浮动对象布局和目录页码结果；
- 将当前 Python 服务改为 .NET 主导并不能自动解决视觉一致性。

项目定位：**验证 sidecar，而不是主生成器替换。**

### 3.3 Aspose.Words

优势：

- 完整文档 DOM，覆盖文字、段落、表格、节、页眉页脚、图片、形状、字段、
  书签和样式；
- `UpdateFields()` 可在服务端更新目录和其他字段；固定版式渲染时会更新
  PAGE/PAGEREF 等分页相关字段；
- 自带分页引擎并可输出 PDF、XPS 和逐页图片；
- 支持 .NET、Python via .NET、Java，支持 Linux/macOS 和 Docker；
- 提供字体目录、字体替换和替换告警机制，适合把公司中文字体显式打包。

风险：

- “接近 Word”是供应商实现，不等于 Microsoft Word 排版引擎；复杂中文
  字体度量、透明边框排版表、横向节、浮动图形仍需 Word 实测；
- 商业许可；未授权试用会加水印并限制文档规模；
- DOM 往返保存可能规范化或重写未触及的 OOXML，不能未经验证替换导入
  方案的源保真路径。

项目定位：**绿地方案首选影子 POC；通过后可承担组合、字段更新和渲染。**

### 3.4 Syncfusion DocIO

优势：

- 官方功能矩阵覆盖段落、表格、图片、形状、图表、节、页眉页脚、字段、
  TOC、PAGE/NUMPAGES 更新、Word 转 PDF/图片；
- .NET 跨平台后端可部署，功能覆盖与本项目高度匹配；
- 同厂 Document Editor 可作为未来更接近 Word 的浏览器编辑器候选，但
  不能因此假定 DOCX 导出就天然源保真。

风险：

- 需引入 .NET sidecar，增加运行栈和部署维护面；
- 复杂 DrawingML/VML、中文字体、透明布局表、公司编号样式及真实 Word
  分页尚无本项目实测；
- 商业许可和版本一致性需要单独治理。

项目定位：**第二候选 POC，与 Aspose 使用同一验收矩阵比较。**

### 3.5 docx4j

优势：

- Java 生态成熟，接近 OOXML 对象模型，适合深度操作 DOCX；
- 开源主库便于私有化；
- 11.5.4 已增加 Table of Figures（TOC `\c` switch 与 SEQ field）支持。

风险：

- 历史 TOC helper 对字段位置和 switch 支持有边界；必须按当前版本实测；
- Word 分页和 PDF 视觉一致性依赖其转换路径，不应只按“支持字段”放行；
- 为现有 Python 服务增加 Java sidecar，收益需明显高于 Open XML SDK
  验证 sidecar 才值得。

项目定位：**开源备选，不作为第一迁移目标。**

## 4. POC 验收设计

### 4.1 样本

至少使用以下四类真实/高难度样本，不使用已拆解后的半成品：

1. `CMS-D017-PNH-方案摘要_v0.2.docx`：最新高优先级公司摘要样式；
2. RUX-03-002 完整方案：长文档、来源保真、真实表格和文献；
3. CMS-D001 方案：另一适应症、另一研究设计和真实表格；
4. 从零构建 RA II 期方案：封面、摘要、目录、图/表目录、横竖节、SoA、
   流程矢量图、页眉页脚、参考文献。

补充边界样本可加入 MY004 RA 和公司最高权威 D005 模板。

### 4.2 每个候选必须完成的动作

1. 未修改打开并保存；
2. 修改一个普通段落；
3. 修改一个真实表格单元格；
4. 新增和删除一个标题，更新目录；
5. 新增图题、表题，更新图目录和表目录；
6. 更新 PAGE、NUMPAGES、SEQ、REF、PAGEREF 和正文引文书签；
7. 生成含 SVG 主图和 PNG fallback 的研究流程图；
8. 生成横向 SoA 节并恢复后续纵向节；
9. 使用指定中文/英文字体渲染 PDF 和 200 DPI PNG；
10. 在 Microsoft Word 中以 `OpenAndRepair=false` 打开、更新域、保存并重开。

### 4.3 硬门指标

- OOXML：
  - Open XML SDK validator 零错误；
  - package parts、relationships、content types、书签和字段闭合完整；
  - 未修改导出与源 SHA-256 相同，或逐部件白名单差异可解释；
  - 修改导出只改变目标内容和必要关系部件。
- Word 原生：
  - 无修复提示；
  - 目录、图目录、表目录在首次打开前已有可读结果，或产品明确执行了
    服务器端字段更新；
  - 页数、分页、横竖节、表格跨页、标题续排、图题和引用跳转正确；
  - 字体无非预期替换。
- 视觉：
  - 与公司权威模板逐页比较；
  - 200 DPI 下无文字裁切、重叠、越界、空白异常页或页眉页脚漂移；
  - Word 原生 PDF 为最终基准，其他引擎逐页与其做文字块、几何和像素差异。
- 工程：
  - 本地 macOS 和未来 Linux 内网容器均可复现；
  - 记录单文档耗时、峰值内存、并发策略、字体包和许可；
  - 任一引擎失败可回退到当前导出器，不改变项目数据模型和审批快照。

## 5. 实施顺序

1. 保留已通过 Word 无修复打开的当前导出器，完成目录、图目录、表目录、
   横竖节、研究流程图、SoA、参考文献和末页门禁。
2. 使用固定版本、MIT 许可的 Open XML SDK validator 做发布结构门。
3. 系统从零生成 DOCX 必须零错误；导入方案未修改透传必须字节一致，
   修改导出相对来源不得新增错误签名。
4. LibreOffice 只执行 PDF/PNG 辅助渲染，任何往返保存结果不得交付。
5. 使用 Microsoft Word 桌面端完成字段、真实分页、打印和可编辑性终验。
6. 发布构建扫描生产后端导入和前端依赖；命中商业 Word 引擎立即失败。

## 6. 主要官方资料

- Microsoft, [Open XML SDK overview](https://learn.microsoft.com/en-us/office/open-xml/open-xml-sdk)
- Microsoft, [Create an Open XML package](https://learn.microsoft.com/en-us/office/open-xml/general/how-to-create-a-package)
- Microsoft, [Considerations for server-side Automation of Office](https://support.microsoft.com/en-us/visio/considerations-for-server-side-automation-of-office)
- python-docx, [API basics](https://python-docx.readthedocs.io/en/latest/user/api-concepts.html)
- python-docx, [Pictures and shapes](https://python-docx.readthedocs.io/en/latest/user/shapes.html)
- python-docx, [Headers and footers](https://python-docx.readthedocs.io/en/latest/user/hdrftr.html)
- Aspose.Words, [Features](https://docs.aspose.com/words/net/features/)
- Aspose.Words, [Update fields](https://docs.aspose.com/words/net/update-fields/)
- Aspose.Words, [Rendering](https://docs.aspose.com/words/net/rendering/)
- Aspose.Words, [Fonts on Windows and non-Windows systems](https://docs.aspose.com/words/net/specifying-truetype-fonts-location/)
- Aspose.Words, [Docker deployment](https://docs.aspose.com/words/net/how-to-run-aspose-words-in-docker/)
- Aspose.Words, [Licensing](https://docs.aspose.com/words/net/licensing/)
- Syncfusion, [DocIO feature matrix](https://help.syncfusion.com/document-processing/word/word-library/net/feature-matrix)
- Syncfusion, [Supported and unsupported features](https://help.syncfusion.com/document-processing/word/word-library/net/supported-and-unsupported-features)
- docx4j, [Getting Started](https://www.docx4java.org/docx4j/Docx4j_GettingStarted.pdf)
- docx4j, [11.5.4 Table of Figures release note](https://www.docx4java.org/forums/announces/docx4j-11-5-4-and-importxhtml-11-5-4-released-t3153.html)
- GemBox.Document, [TableOfEntries](https://www.gemboxsoftware.com/document/docs/GemBox.Document.TableOfEntries.html)
- Telerik, [RadWordsProcessing fields](https://docs.telerik.com/devtools/document-processing/libraries/radwordsprocessing/concepts/fields/fields)

## 7. 2026-07-18 实测裁决更新

用户明确后续不会为 Word 生成/导出引擎额外付费。因此，Aspose.Words、
Syncfusion DocIO、GemBox.Document、Telerik 等需要商业许可才能无水印、
无限制运行的引擎均不进入生产代码或发布依赖。其试用版结果只保留为
技术能力和失败边界证据。

同一份从零构建的 RA II 期方案在修复 OOXML 子节点顺序后得到以下结果：

| 路径 | Microsoft365 Open XML 错误 | 字段/目录 | 版式或许可结论 |
|---|---:|---|---|
| 当前 `python-docx + 直接 OOXML` | 0 | 保留可更新字段 | 当前生产基线 |
| Aspose.Words 26.7 试用版 | 1 | 可生成目录 | 商业许可、水印、中文字体替换，否决 |
| Syncfusion DocIO 34.1 试用版 | 7 | 可生成目录 | 商业许可、水印、重写样式，否决 |
| LibreOffice DOCX 往返保存 | 66 | 未形成可用图/表目录 | 破坏 schema，有格式漂移，禁止回写 |
| Microsoft Word 原生更新并保存 | 0 | 目录、图目录、表目录均生成 | 10 页，最终桌面版式权威 |

Microsoft Word 实测副本执行全选更新域后：

- 目录 13 项、图目录 1 项、表目录 2 项均含正确页码和点引导符；
- PAGE/NUMPAGES 显示为 10 页；
- 保存后的 DOCX 仍通过 Open XML SDK 零错误验证；
- LibreOffice 对该 Word 保存副本的二次渲染为 11 页，371/371 个中文
  span 可见，进一步证明 LibreOffice 只适合作为跨引擎回归层。

docx4j 主库为 Apache-2.0，但其官方资料明确指出纯 Java 目录页码可能不
准确；准确路径仍依赖 Microsoft Word/documents4j 或转换渲染。当前环境
也没有 Java 运行时。增加 Java sidecar 不能提高最终 Word 页码权威性，
因此不安装、不进入本轮 POC。

### 最终免费生产路线

1. 绿地方案：继续使用公司模板优先的 `python-docx + 受控直接 OOXML`。
2. 导入方案：继续使用原始 DOCX package 透传和定位最小修改，不整体
   DOM 往返保存。
3. 结构门：引入 MIT 许可 Microsoft Open XML SDK 校验器；系统生成的
   DOCX 必须零错误。导入来源的既有错误单独记录，不允许校验器自动重写。
4. 渲染门：LibreOffice 仅生成 PDF/PNG 辅助回归，不把其页数当作最终
   Word 页数，也不将其保存结果交付用户。
5. 最终门：用户在 Microsoft Word 中更新全部字段并完成原生分页、
   可编辑性和打印预览验收。系统不得以无人值守 Office 自动化作为
   内网后端依赖。

该路线不引入新的商业许可，能在当前本地部署和未来私有化部署中复现，
同时保留对 Word 最终版式的真实权威边界。
