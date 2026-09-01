# Reference OCR evidence core Codex 验收

日期：2026-07-25  
范围：代码与 fake adapter 回归，不代表真实 oMLX OCR 发布验收

## 结论

接受 OCR evidence core 进入后续接线。实现已固定`GLM-OCR-bf16`、200 DPI、最多8路并发，
并为恢复文本和`empty_text`页写入可复算、不可覆盖的PNG sidecar证据。没有新增逐页审批、
待医学批准、文件安全或来源权利硬门。

## Codex 独立审阅与修正

发现 OCR span 原实现会把恢复页统一追加到原生 spans 末尾，混合文档可能产生页码逆序，
影响章节规划与后续结构化提取。已将最终 spans 按物理页、块序、定位符和span id稳定排序，
并增加空白首页经OCR恢复、第二页保留native text的回归测试。

## 已验证行为

1. PNG实际写入后可从磁盘复算hash、字节数和尺寸。
2. 完全相同的重放不重复写；同路径不同hash失败关闭。
3. OCR调用失败时不发布任何最终sidecar。
4. 空OCR结果仍保留页级证据，不生成空span。
5. 异常页只有成功恢复文本时替换native span；空结果保留native text及lineage。
6. 并发峰值不超过8，输出按页码稳定。
7. 旧记录仍可按`legacy_metadata_only`读取，新写记录执行强校验。

## 验收证据

- `py_compile`通过。
- OCR、extraction、共享合同、chapter pipeline及writing reference组合回归：
  `121 passed`，仅有既有PyMuPDF/SWIG弃用告警。

## 尚未通过的发布门

- 未调用真实本地oMLX `GLM-OCR-bf16`。
- 未证明实际模型profile、空页、表/图页、并发和失败恢复。
- 未在CRSwNP `NCT02898454`及UC `NCT02819635`完整产品批次中验证。
- read-only evidence API和用户异常处置视图尚未接线。
