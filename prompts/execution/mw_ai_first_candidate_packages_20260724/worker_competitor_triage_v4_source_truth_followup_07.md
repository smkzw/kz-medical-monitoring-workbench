# 竞品分诊v4第07轮：修正缩写误匹配与全事实间接篮子旁路

继续同一session：`20260724_204518_3e5b86`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- 第06轮prompt、当前源码/测试和runner报告

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_07.md`

不得自行写runner报告；final response返回完整报告。

## Codex第06轮源码验收问题

第06轮暂不接受，只有两个单点缺陷：

1. `_candidate_indication_matches_project()`把“双方token集合只有一个共同2–8字符英文词”全部
   当作缩写匹配。由于tokens已经lowercase，`severe`、`chronic`、`disease`等普通词也满足，
   会把不同疾病误判同适应症。
2. `_enforce_classification_eligibility()`在项目technology/route/target三项都已知时直接
   信任模型原始`indirect_reference`，跳过“同适应症+显式药理学干预”复验。原合同要求所有
   原始indirect均复验，三项事实是否齐全只影响direct是否可保留。

## Hard boundaries

只允许修改：

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 必要时最小修改旧triage测试

## 必须修复

1. 缩写匹配只接受可证明的缩写：
   - 项目中文/英文事实中括号内的2–8位大写缩写；
   - 候选条件中相同括号缩写，或候选条件本身/独立大写token与项目已提取缩写完全一致；
   - 不得把任意lowercase普通单词当缩写。
2. 原始`indirect_reference`无论项目三项关键事实是否全部已知，都必须满足：
   同适应症 + 至少一个显式`DRUG/BIOLOGICAL/COMBINATION_PRODUCT`，否则excluded。
3. 原始direct只有三项项目事实全部已知才保留；有缺失时按相同资格降为indirect或excluded。
4. 原始excluded仍不提升。

## 必测

- 项目和候选只共享`severe`、`chronic`或`disease`任一普通词，不得匹配。
- 项目括号`(PNH)`/`（PNH）`与候选独立`PNH`或候选括号`(PNH)`匹配。
- PNH完整英文词序变化仍匹配。
- 三项项目事实全部已知 + 模型原始indirect + 不同适应症DRUG => excluded。
- 三项全部已知 + 原始indirect + 同适应症DEVICE/缺失type => excluded。
- 三项全部已知 + 原始indirect + 同适应症DRUG => indirect。
- 新旧分诊测试和py_compile全绿。

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_07_COMPLETE`
