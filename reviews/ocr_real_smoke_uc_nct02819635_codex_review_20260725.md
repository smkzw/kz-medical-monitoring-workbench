# UC NCT02819635 真实 oMLX OCR 单页窄门

日期：2026-07-25  
来源：M14-234 Protocol Amendment 7，物理页143  
模型：本地 oMLX `GLM-OCR-bf16`

## 结果

- 原生PDF文本字符数：0。
- 渲染：200 DPI，PNG `1700 × 2200`，1,281,729 bytes。
- PNG SHA-256：
  `0e9addc5e1ebda447355881ab64338d3ca5a740391629054dce881950932954d`。
- 模型：oMLX实际响应`GLM-OCR-bf16`。
- 耗时：约5.06秒。
- OCR字符数：1229。
- OCR文本SHA-256：
  `f2b83571b263e67f75a23f764165f8f58a81906d6bd149715e7b2bc10cf5dee5`。

证据目录：
`runs/evidence/ocr_real_smoke_uc_nct02819635_20260725/`。

## Codex 视觉与文本核对

识别正确覆盖：

- `6.1.4 Adverse Event Collection Period`；
- 给药开始至停药后30天的AE收集时窗；
- 知情同意后SAE及方案相关非严重AE的收集边界；
- Figure 5标题、主要时间节点、MACE及后续心血管事件段落。

仍需图表视觉核对：

- 二维时间轴/括号关系被OCR线性化，不能仅凭纯文本重建图中适用区间；
- 左右两组AE标签在纯文本中发生合并，版面关系不够明确；
- 重复页眉、公司标识及页码未完整保留，但这些不属于正文语义；
- 因此图/表页必须保留200 DPI PNG sidecar并标记视觉结构核对，OCR文本只能作为可检索
  候选，不得单独作为完整图义或直接准入依据。

## 窄门判定

真实本地模型、PNG data URL网关、200 DPI和英文Protocol OCR链路可用。该单页不证明：

- 12页完整批次并发与失败恢复；
- 页面级证据经产品repository重启后保持；
- OCR后章节规划、Hy-MT2翻译及Flash整合；
- 医学语料准入。
