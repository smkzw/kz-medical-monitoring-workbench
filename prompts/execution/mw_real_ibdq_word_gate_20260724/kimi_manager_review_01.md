# Real IBDQ Word Gate：视觉执行经理复核

## Read these files only

完整读取：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `runs/hermes_mw_real_ibdq_word_gate_20260724.md`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/EVIDENCE_MANIFEST.json`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/ooxml/pre_word_package_check.json`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/ooxml/post_word_package_check.json`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/qc/page_level_visual_qc.json`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/rendered_200dpi/page_01.png`
  至`page_13.png`

Runner-managed output file:
`runs/execution/mw_real_ibdq_word_gate_20260724/kimi_manager_review_01.md`

不得自行写runner报告；在final response中返回完整报告，由runner持久化。

## Hard boundaries

- 这是只读视觉执行经理复核，不得修改任何源码、证据或Word文件。
- 必须逐页查看13张200 DPI原图，不能只复述Grok报告或QC JSON。
- 分开判定：IBDQ九页分页/可读性、流程图可读性、测试夹具其他版面质量、OOXML/Word原生链路。
- 不得声称最终接受；Codex保留最终Word、视觉和生产验收权。

## 任务

以资深医学撰写经理和Word交付审阅者视角，复核：

1. PDF第5–13页是否恰好对应IBDQ 1/9–9/9，顺序连续，无缺页/重复/孤立标题/图片溢出；
2. 每页标题与图片是否同页，问题、选框、版权、页码是否可读，有无裁切、重叠、页眉页脚碰撞；
3. 第3页研究流程图的节点、箭头、条件标签、注释、图题是否清楚，有无文字/线条/节点冲突；
4. 第1–4页是否存在不应被误判为产品通过的稀疏页、索引或测试夹具缺陷；
5. pre/post Word OOXML证据是否足以证明SVG主图与PNG fallback在Word往返后保留；
6. user原Word文档是否从日志证据看得到保留。

输出：

- 按严重度列出视觉发现和精确页码；
- 分别给出`IBDQ_PAGINATION_GATE`、`FLOWCHART_VISUAL_GATE`、
  `WORD_NATIVE_ROUNDTRIP_GATE`的建议PASS/FAIL；
- 若有失败，说明是测试夹具、流程图生成器、DOCX exporter还是Word沙盒链路，并给出最小后续
  写集/测试，不得直接修改。

完成标记：
`KIMI_REAL_IBDQ_WORD_MANAGER_REVIEW_01_COMPLETE`
