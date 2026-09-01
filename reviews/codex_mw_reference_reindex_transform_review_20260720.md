# 医学写作既有文献重索引物理变换主审

日期：2026-07-20

## 当前结论

物理OOXML变换器通过聚焦测试和一个真实可应用方案的
baseline-preserving验证，但尚未接入生产导出器，因此发布状态仍为
`HOLD`。

## 已验证能力

- 入口：`apply_source_reference_reindex(docx_bytes, manifest, decision)`。
- 变换前重新构建manifest，严格核对digest、完整dataclass内容、
  decision及物理XPath/字符locator。
- 仅`action=apply`可执行；`preserve_with_notice`和`block`均失败关闭。
- 支持document、header、footer、footnote、endnote和comment story。
- 支持分run上标、多引文和范围、显式参考文献编号、内部hyperlink、
  simple field和安全complex REF/HYPERLINK field。
- 对citation manager field、重复/缺失编号、source drift、嵌套域、
  单域绑定多文献和自动编号需改号等情况阻断。
- 仅重写目标story XML；relationships、media、custom XML及其他ZIP part
  的logical payload bytes保持不变。
- 变换结果重新扫描后重复执行为字节级幂等。

## Codex验证

- 聚焦测试：`40 passed`。
- Ruff：通过。
- compileall：通过。
- 真实判定矩阵：

| 文档 | refs | citations | 决策 | 主要原因 |
|---|---:|---:|---|---|
| CMS-D017 PNH摘要v0.2 | 0 | 0 | preserve | 无既有引文 |
| CMS-D005减重II期概要 | 6 | 0 | preserve | 全部未引用 |
| CMS-D017 I期方案 | 24 | 17 | block | citation manager、重复编号 |
| 1-3-4-1-2方案模板 | 55 | 47 | block | citation manager、重复编号、缺失anchor |
| MG-K10青少年AD三期 | 4 | 6 | apply | 无阻断问题 |

MG-K10变换只改变`word/document.xml`，非story part无漂移，二次执行字节
一致。Microsoft Open XML SDK 3.5.1在源文件和变换副本上均报告相同48个
既有错误签名，变换未新增OpenXML错误。

## 不得夸大的边界

- 真实模板库中尚未找到既`apply`又发生非identity改号的文档；真实文件
  目前只验证bookmark插入、绑定保真和幂等，非identity重排由合成测试覆盖。
- 变换器没有生产调用方，不满足“导入方案后自动重索引”的用户工作流。
- 被Zotero/EndNote等citation-manager管理的文档按设计阻断；后续应向
  用户显示原因并保留原文，而不是绕过管理域。
- baseline-preserving不代表原文零错误；MG-K10的48个错误来自原文件，
  需在独立源文档质量治理中处理。

## 下一安全步骤

1. 在source-preserving exporter内增加显式旧文献重索引阶段。
2. 把`apply/preserve_with_notice/block`状态写入导出审计结果并前端可见。
3. `apply`时使用物理变换结果作为后续受管引用合并输入，避免两套编号器
   各自改号。
4. 增加导出器级测试：纯旧引文、旧引文加新文献、表格/脚注引文、
   citation-manager阻断、并发重复导出和源digest漂移。
5. 使用Microsoft Word原生更新域、保存、重开及点击跳转作为最终门禁。
