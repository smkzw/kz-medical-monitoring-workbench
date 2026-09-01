# D017竞品分诊v4真实产品AI医学QC

## 结论

当前run不确认，状态保持`review_ready`。v4已解决v3的大部分来源真值问题，但仍存在两项
用户可见P0，已发起同会话第06轮定点返修；修复后必须新建run重测，不能修改或确认旧run。

## 运行身份

- 项目：`proj_user_3ecb0bc287c0`，CMS-D017，PNH，II期
- journey revision：5
- snapshot：`wref_search_35f39994abfb89587948`
- run：`ct_run_681a3edb8f7d10cfe256`
- job：`mwjob_94caedeabb1a66a03e44d15a`
- provider/model：`deepseek/deepseek-v4-pro`
- prompt：`competitor_triage_deepseek_v4_source_truth`
- 状态：`review_ready`，未确认

## 已通过

1. 5/5 chunk全部成功，67个候选得到67个唯一结果，无缺失、重复或未知NCT。
2. 分布为52项间接参照、15项排除、0项直接竞品；在CMS-D017技术类型、给药途径和靶点
   均未知时，没有保留直接竞品。
3. 所有modality/route/target matching dimension均被服务端保护为unknown。
4. Protocol、SAP及`protocol_sap`的布尔值均按快照确定性派生，零不一致。
5. 现有52项间接参照均可由快照验证为PNH相关且至少有一个显式
   DRUG/BIOLOGICAL/COMBINATION_PRODUCT干预。

## P0缺陷

### 1. 间接参照未统一经过服务端资格门

源码只在模型原始分类为`direct_competitor`时执行“同适应症+显式药理学干预”降级逻辑；
模型原始`indirect_reference`不复验。因此本run虽未实际出现污染项，但其他适应症或快照
可能把不同适应症、器械、操作、放疗或干预类型缺失的研究保留为间接参照。

### 2. 用户可见来源文字仍含模型自由发挥

- `_sanitize_reason()`用中文项目适应症与英文候选条件做字面包含比较，导致几乎所有PNH研究
  都显示“适应症不同”，同时句尾又写“可作为同适应症药物研究参考”，内部自相矛盾。
- `_derive_document_suitability()`虽然确定性重建Protocol/SAP布尔值，却继续采用模型
  `document_role`。NCT03053102被显示为“可用于参考口服补体抑制剂的设计”，而本次送入模型
  的显式快照字段只有Danicopan/DRUG、标题、摘要、设计及公开文档，没有口服途径或补体
  机制字段。

## 修复门

1. 所有模型分类均由服务端复验：原始indirect若不满足同适应症+显式药理学干预，强制
   excluded；原始excluded不提升。
2. 同适应症比较统一使用中文indication、英文condition term、括号缩写和英文token集合，
   支持PNH及`Paroxysmal Hemoglobinuria, Nocturnal`词序差异，不能用短子串误匹配。
3. reason复用同一适应症判定。
4. document role只按公开文档类型确定性生成，不保留模型自由文本。
5. 新run再次通过67/67、0 direct、0非法indirect、0 protected dimension violation、
   0 unsupported term和0 document mismatch后，才进入医学经理人工确认。

## 证据

- `runs/evidence/d017_competitor_triage_v4_20260724/run_response.json`
- `runs/evidence/d017_competitor_triage_v4_20260724/search_snapshot.json`
- `runs/evidence/d017_competitor_triage_v4_20260724/qc_scan.json`
- `runs/evidence/d017_competitor_triage_v4_20260724/qc_scan.py`
