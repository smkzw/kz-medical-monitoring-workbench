# 医学写作 DOCX 发布前静态缺口复核

日期：2026-07-20

## 结论

当前生产导出链具备完整的 OOXML 基础，但发布保持 `HOLD`。本轮只读复核
与 Codex 聚焦回归确认了以下边界。

## 必须修复

### 导入方案既有文献重索引

当前 source-preserving 导出在文档未修改时直接复用原包；发生修改时，也
只有检测到新增“受管引用”才构建 citation plan 并重写参考文献。纯旧引文
场景不会无条件重新索引，与用户“导入方案后原有文献也要重新进行索引”的
明确要求冲突。

关键实现：

- `services/api/app/medical_writing_document_exporter.py:123`
- `services/api/app/medical_writing_document_exporter.py:202`
- `services/api/app/medical_writing_document_exporter.py:346`
- 现有测试只锁定新增受管引用后的重排：
  `tests/test_medical_writing_source_preserving_export.py:391`

修复必须从导入文档识别既有正文引文与参考文献条目，建立可审计的旧编号到
新编号映射，再按首次出现顺序重排；不能仅按文本正则静默改号，也不能破坏
原文超链接、脚注、域和表格内引用。

### 方案摘要目的/终点对象

已直接解包三个公司权威 DOCX 并按 OOXML 复核：

- 最高优先级 `CMS-D017-PNH-方案摘要_v0.2.docx`：
  `T1/R3-R8` 是同一张 18×3 外层表的六行，左列以 `vMerge` 跨六行；
  目标区域没有嵌套 `w:tbl`；
- 较低优先级 D005 减重 II期概要：单元格内确有 6×2 子表；
- 较低优先级 D017 I期方案摘要：单元格内确有 7×2 子表。

因此生产实现的“三列主表 + 六行 + 左列纵向合并”核心结构符合最高权威，
不应为了字面满足“表格中的表格”改成嵌套 `w:tbl`。当前与最高权威的
真实差异是：

1. 列宽应从当前 `1800/3600/3600` 调整为约
   `17.1%/33.0%/49.8%`；
2. 字面 `•` 应改为可在 Word 中继续编辑的真实 `w:numPr` 编号/项目符号；
3. 目标六行不应全部 `cantSplit`，长目的/终点需允许自然跨页；
4. 内容单元格应顶部对齐；
5. 应补齐权威的段前、段后、固定行距和最小行高；
6. 应采用100%页宽和显式 `single/4/auto` 边框，不依赖主题
   `Table Grid`样式。

最高权威目标表的列宽为 `1554/2993/4514`；目标区没有
`pageBreakBefore`或显式分页符。主要目的/终点无列表编号，次要和探索性
条目混合使用真实十进制 Word 编号与少量手工编号。生产实现应按语义类别
映射，不应对全部单元格统一插入同一项目符号。

## 不应粗暴全局覆盖

### 颜色

默认正文和表格必须为黑色，不能再出现无用户意图的蓝色标题或蓝色表格。
但编辑器已按用户要求支持文字颜色和标黄，因此显式 `textStyle.color`
属于医学经理的格式决策，导出时必须保留。发布门应区分：

- 模板/AI/默认内容不得带非黑颜色；
- 用户明确设置的颜色可以保留并在审计数据中可识别。

### 正文首行缩进

Greenfield 正文默认 `firstLineChars=200`；source-preserving 路径保留源
文档格式；富文本段落设置允许用户覆盖。发布门应检查所有“普通正文且用户
未显式覆盖”的段落均为首行两字符，而不是无条件改写标题、表格单元格、
列表、附注和用户明确设置的段落。

## 已锁定基础

- 中文 `宋体`、ASCII/HAnsi/数字 `Times New Roman` 的 XML 字体归一化；
- Greenfield Heading 1-4、多级编号和 TOC 1-4；
- 摘要三列、六行目的/终点分组、项目符号和合并关系；
- GBT 7714-2015、首次出现顺序编号、上标超链接、表格内引用和缺失文献
  失败关闭；
- Greenfield Open XML 零错误与 source-preserving 无新增错误签名门。

Codex直接复跑 exporter、source-preserving、style profile、protocol
template、citation export 和 OpenXML gate 六个测试文件，结果
`82 passed in 53.95s`。

## Word 原生发布门

两个全新真实项目均必须完成：

1. 导出前与 Word 保存后 Open XML 验证；
2. Microsoft Word 无修复弹窗，更新全部域、保存、重开；
3. 首页与公司权威模板逐项视觉对照；
4. Heading 1-4、父子编号、TOC/图目录/表目录逐项点击；
5. 摘要大表、目的/终点分点与分组结构跨页检查；
6. 正文默认首行两字符，字体与默认颜色全篇扫描；
7. 所有分节页眉页脚及 PAGE/NUMPAGES；
8. 既有引文重索引、新增引文、表图 SEQ/REF 更新后跳转。

D017 v9 的既有 Word 验收只能作为基线，不能替代当前 AI-first 合并后的
双项目新鲜验收。

## 2026-07-20进展补充

- 既有文献manifest/decision之后的纯OOXML物理变换器已经实现并通过
  `40 passed`聚焦回归；真实MG-K10方案验证仅改变
  `word/document.xml`，非story ZIP part无漂移，二次执行字节级幂等。
- 源MG-K10和变换副本的Open XML SDK错误签名完全一致，均为48个原文件
  既有错误；没有新增错误。详细主审见
  `reviews/codex_mw_reference_reindex_transform_review_20260720.md`。
- 该能力仍未接入source-preserving exporter，不能视为发布缺口已关闭。
- D017 PNH真实`deepseek-v4-pro`摘要结构化v0.7、确认和111-section动态
  模板导出已完成，Open XML SDK为0错误；但harness使用corpus override，
  不等价于完整语料准备链。
- Word 16.111已证明能从临时目录打开D017验收副本并识别213个field和
  1个TOC。当前macOS处于`loginwindow`锁屏，文件访问授权模态无法确认，
  因此Word字段更新、保存、重开和PDF视觉检查仍未完成。
