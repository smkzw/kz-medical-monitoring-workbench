# W2b-2：产品DeepSeek证据绑定候选与正式快照注入

执行前完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `reviews/codex_subagent_w2b_evidence_catalog_design_20260724.md`
- 已接受的W2b-1实现与报告
  `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b1_evidence_catalog_contract_builder_02.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_01.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## 角色与目标

你是非视觉复杂执行成员。把当前“裸registered_source_ids + 少数字段改写”的prefill adapter
升级为真正的AI-first候选生成路径：

1. 服务端从当前journey与不可变ClinicalTrials.gov快照建立W2b-1证据目录；
2. 正式产品`deepseek/deepseek-v4-pro`一次批量请求同时生成字段候选和
   population/intervention/outcomes/statistics四个PICOS组合候选；
3. 模型只能回传catalog entry引用，服务端按entry ID、source、locator、quote hash重绑原文；
4. 竞品观察只形成“可选设计”，不能证明本项目已随机、盲法、安慰剂、成人、某途径、
   某机制、某剂量、某终点或统计假设；
5. 正式prefill生成API必须把当前search plan绑定的最新不可变快照传入service/adapter。

本轮不实现W3组合采纳事务，不改前端，不启动真实D017 run，不用执行模型替代产品独立AI。

## Hard boundaries

允许写集：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- 可新建
  `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/main.py`
- 可新建
  `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`
- 可新建
  `tests/test_medical_writing_authoring_prefill_api_snapshot_injection.py`
- 仅因本轮权威行为替换时，最小修改：
  - `tests/test_medical_writing_authoring_prefill_ai.py`
  - `tests/test_medical_writing_authoring_prefill_ai_quality.py`
  - 相关main API聚焦测试

不得修改W2b-1合同/builder、确定性prefill、journey service、repository、竞品分诊、前端、
DOCX或其他功能。

## 必须实现

### A. 正式API快照注入

`POST .../prefill-package/generate`在构造AI enricher后：

1. 读取当前journey；
2. 从`journey.search_plan.latest_snapshot_id`取得精确snapshot ID；
3. 用`writing_reference_repository.search_snapshot(canonical_id, snapshot_id)`读取不可变快照；
4. 把snapshot传给`generate_prefill(..., snapshot=snapshot, ai_enricher=...)`。

若search plan声称有snapshot但repository缺失，失败关闭为无snapshot生成并保留
`search_snapshot_unavailable`部分失败，不得静默使用“最新其他snapshot”，不得把404伪装成
已有证据。revision竞争仍由journey service CAS处理。

### B. 有界证据目录投影

adapter调用W2b-1 `build_evidence_catalog(state, snapshot)`。DeepSeek请求必须含：

- `catalog_id`、`catalog_sha256`、journey revision、snapshot ID；
- 每个真正发送给模型的entry：
  `catalog_entry_id/source_kind/support_scope/source_id/source_revision/locator/quote/title/provenance`
  的必要子集；
- 当前确定性字段与四个PICOS package的target paths/待决定结构；
- 不再把裸`registered_source_ids`作为语义证据。

请求必须确定性有界，例如总证据文本不超过120000字符：

- 三个项目最小事实优先且不得因截断丢失；
- 已确认摘要事实优先于CT.gov观察；
- CT.gov按NCT和字段稳定排序；
- 单条quote可有上限，但不得修改catalog原文或hash；
- 记录发送entry ID集合；模型引用未发送entry必须拒绝。

### C. 输出schema

一次批量响应支持：

1. 英文`clinicaltrials_condition_term_en`候选；
2. `field_suggestions`；
3. `package_suggestions`，键至少：
   - `package.population`
   - `package.intervention`
   - `package.outcomes`
   - `package.statistics`

每个候选包含：

- `structured_value`
- 规范中文`preview`、`rationale`
- `recommendation_role`
- `clinical_tradeoffs`
- `evidence_gaps`
- `claim_bindings[]`：
  `target_path/value_pointer/catalog_entry_id/support_kind`

模型不得回显或决定source/locator/quote/hash；这些全部由服务器目录重绑。
每组最多5个候选；有足够来源时允许1个推荐+2至4个实质不同备选。来源不足时保留确定性
pending候选，不伪造凑数。

### D. 服务端逐主张验证与重绑

新增纯验证器或等价小模块：

1. catalog ID/hash必须与本次服务端catalog完全一致；
2. binding entry必须在实际发送给模型的entry集合；
3. entry ID存在；source ID、locator、quote hash均从服务器entry重绑；
4. binding target path必须属于候选field path或组合candidate target_paths；
5. `exact_fact`、`normalized_enum`只接受
   `support_scope=current_project_fact`且target path在entry的
   `supported_target_paths`中；
6. `competitor_option`只接受`competitor_observation`，并按CT.gov
   `provenance.field_key`与目标路径做最小语义映射：
   - randomization <- design_allocation
   - blinding <- design_masking
   - intervention model/design <- design_intervention_model/allocation/masking
   - population <- conditions/brief_summary/title
   - intervention/comparator <- intervention name/type/brief_summary/title
   - outcomes <- brief_summary/title；不得据此证明精确终点
   - statistics <- allocation/model/masking/enrollment；不得证明效应量、把握度、alpha、
     样本量假设或估计目标
7. 任何未知entry、hash漂移、跨target误绑、competitor observation冒充项目事实均拒绝该
   候选；不得仅降级后继续可选。
8. 服务器用真实entry生成`AuthoringPrefillClaimBinding`和
   `AuthoringPrefillEvidenceRef`，后者包含用户可直接阅读的真实原文及locator。
9. `evidence_status`由服务器计算，不能信任模型：
   - 全部需要的原子项目事实有current-project binding才为supported；
   - 有有效binding但仍有未证实项目决策为partially_supported；
   - 无有效binding为insufficient。
10. 本轮所有AI候选`adoption_mode=manual_only`。`recommendation_role=recommended`
    只表示推荐用户选择，不表示已确认；用户选择后由W3直接生效，不再二次“医学批准”。

### E. 语言与事实边界

- condition term之外，value/preview/rationale/tradeoff/gap均为中国方案监管中文；
- CMS-D017、PNH、PK/PD、SAD/MAD、NCT等必要缩写可保留；
- 保留现有逐字段语言门，不能让中文理由掩盖英文value；
- 无current-project binding的成人/随机/双盲/安慰剂/途径/机制/剂量/精确终点/统计参数，
  只能作为明确的`competitor_option`设计选择进入manual_only组合候选，不能进入普通
  framing/picos字段并伪装为项目事实；
- 用户可见文本不得出现`AI proposed`、开发标签或“待医学批准”。

### F. 模型身份和失败回退

- 仍只允许正式独立`deepseek/deepseek-v4-pro`；
- 一次bulk call，不按字段逐次调用；
- concrete production provider继续验证真实response model；
- fake provider仅用于测试；
- 模型/解析/证据验证失败时保留完整确定性pending包并记录partial failure，不能写半包事实。

## 必测反例

1. 正式API从`latest_snapshot_id`加载**精确**快照并传入adapter；无snapshot时不偷取最新其他项。
2. D017最小事实可以形成中文标题/英文检索词候选，但无来源的成人、随机、双盲、安慰剂、
   途径、机制不得成为普通项目事实候选。
3. CT.gov `RANDOMIZED/DOUBLE/PARALLEL`只可形成manual-only competitor option。
4. 模型引用未发送entry、未知entry、错误target、伪造hash/source/locator全部拒绝。
5. 即使模型返回quote/source/hash，服务器也忽略并重绑目录原文。
6. 适应症entry不能绑定到investigational_product；CT.gov随机不能绑定为本项目
   exact_fact。
7. package structured_value键必须与确定性target_paths完全一致。
8. 有3至5个有效实质候选时保留；重复值去重；无证据时不凑数并保留pending。
9. payload稳定、有界，项目三事实永不被CT.gov截断挤出。
10. generic provider缺/错response model失败关闭，产品provider路径保持一批一次。
11. 旧确定性prefill和旧候选JSON回归全绿。

## 验收

运行所有新增测试，以及：

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_ai.py \
  tests/test_medical_writing_authoring_prefill_ai_quality.py \
  tests/test_medical_writing_authoring_prefill_evidence_catalog.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py \
  tests/test_medical_writing_authoring_prefill.py \
  tests/test_medical_writing_authoring_prefill_picos_packages.py
python3 -m py_compile \
  services/api/app/medical_writing_authoring_prefill_ai.py \
  services/api/app/medical_writing_authoring_prefill_evidence_binding.py \
  services/api/app/main.py
```

报告必须列出实际修改文件、真实测试计数、payload上限、服务器证据判定规则、未纳入IB/
registered_source的边界及完整loop trace。不得声称W3、前端或真实产品AI医学QC已完成。

完成标记：
`HERMES_W2B2_DEEPSEEK_EVIDENCE_BOUND_CANDIDATES_01_COMPLETE`
