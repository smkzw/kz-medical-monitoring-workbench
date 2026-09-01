# 竞品分诊v4真实D017 run后的第06轮定点返修

继续同一session：`20260724_204518_3e5b86`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- 本轮真实run证据与当前允许写集源码、测试

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_06.md`

不得自行写runner报告；final response返回完整报告。

## 真实运行证据

D017真实产品`deepseek/deepseek-v4-pro` run：

- run `ct_run_681a3edb8f7d10cfe256`
- snapshot `wref_search_35f39994abfb89587948`
- 证据目录：`runs/evidence/d017_competitor_triage_v4_20260724/`
- `qc_scan.json`

67/67、5/5、provider/model、0 direct、项目未知modality/route/target保护及Protocol/SAP布尔值
均正确，但真实run暴露两项P0：

1. `_enforce_direct_competitor_downgrade()`只处理模型原始`direct_competitor`。模型原始
   `indirect_reference`不会重新验证“同适应症+显式药理学干预”，因此不同适应症或非药理学
   候选仍可能污染间接篮子。
2. `_derive_document_suitability()`保留模型`document_role`自由文本。NCT03053102的快照只
   显式提供Danicopan/DRUG、标题/摘要、设计和Protocol/SAP，模型却把document role写成
   “可用于参考口服补体抑制剂的设计”，引入快照没有的途径/机制事实。
3. `_sanitize_reason()`用中英文原始字符串包含关系判断适应症，D017中文PNH与英文
   `Paroxysmal Nocturnal Hemoglobinuria`被错误写成“适应症不同”。

## Hard boundaries

唯一允许写集：

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 仅因权威行为替换时最小修改
  `tests/test_medical_writing_competitor_triage.py`

不得修改其他文件，不启动新run，不确认D017篮子，不碰W2b/main/contracts/frontend。

## 必须修复

1. 对**所有**模型分类做服务端资格协调：
   - `direct_competitor`在项目technology/route/target任一未知时，只有同适应症且显式
     `DRUG/BIOLOGICAL/COMBINATION_PRODUCT`才降为indirect，否则excluded；
   - 模型原始`indirect_reference`也必须验证同适应症+显式药理学干预，任一不满足即excluded；
   - 模型原始`excluded`不自动提升。
2. 同适应症匹配必须通用且确定性，不只对D017硬编码：
   - 同时使用项目中文indication、英文clinicaltrials condition term；
   - 提取括号中的英文缩写（如PNH）并按完整token匹配；
   - 英文条件在去标点、归一空白后允许token集合等价或包含，支持
     `Paroxysmal Hemoglobinuria, Nocturnal`与
     `Paroxysmal Nocturnal Hemoglobinuria`的词序差异；
   - 短词和普通子串不得制造误匹配。
3. `_sanitize_reason()`必须复用同一服务端适应症判定，不能再独立用字面包含判断。
4. `document_role`完全服务端确定性生成，只基于public document type说明“有/无公开方案/
   统计分析计划”，不得保留模型自由文本，不得出现来源未给出的route/target/modality。
5. protected dimension仍保持unknown；不得为了修复显示文字而放宽证据门。

## 必测反例

- 原始indirect + 不同适应症 + DRUG => excluded。
- 原始indirect + 同适应症 + PROCEDURE/DEVICE/RADIATION/缺失type => excluded。
- 原始indirect + `PNH`条件 + DRUG => indirect。
- 原始indirect + `Paroxysmal Hemoglobinuria, Nocturnal` + DRUG => indirect。
- 相近但不同疾病、短词、普通子串不得误判同适应症。
- PNH中文项目与英文候选的重建理由为“适应症一致”，不得写“适应症不同”。
- 模型document role注入“口服补体抑制剂”后，最终只保留确定性公开文档说明。
- 既有110项及新测试全绿，py_compile通过。

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_06_COMPLETE`
