# 竞品分诊v4第08轮：移除疾病名称模糊词重叠假阳性

继续同一session：`20260724_204518_3e5b86`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- 第07轮prompt、当前源码/测试和runner报告

Read these files only:

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- `tests/test_medical_writing_competitor_triage.py`
- `prompts/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_followup_07.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_07.md`

Runner-managed output file: `runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_08.md`

不得自行写runner报告；final response返回完整报告。

## Codex第07轮源码验收问题

第07轮修正了普通英文词被当缩写及indirect旁路，但
`_candidate_indication_matches_project()`仍把“至少两个token且覆盖较小集合60%”视为同适应症。
这会把真实不同疾病误判为相同，例如项目
`Paroxysmal Nocturnal Hemoglobinuria`与候选
`Paroxysmal Nocturnal Dyspnea`共享2/3 token，当前返回True。

ClinicalTrials.gov的`conditions`是结构化疾病名称；竞品篮子的“同适应症”资格必须失败关闭，
不能用模糊词相似度推断。

## Hard boundaries

只允许修改：

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 必要时最小修改旧triage测试

## 必须修复

1. 分别构造项目`indication`与`clinicaltrials_condition_term`的规范化token集合，不得先合并
   中英文集合后比较。
2. 同适应症只允许：
   - 候选某一condition的规范化token集合与项目任一非空术语的规范化token集合完全相等
     （因此仅词序/标点变化可匹配）；或
   - 第07轮已建立的“项目可证明括号缩写 ↔ 候选相同括号缩写/独立全大写缩写”。
3. 删除“子集/60%词重叠”判断。不要引入编辑距离、通用模糊搜索或模型自由判断替代。
4. 第07轮所有indirect无条件复验、explicit pharmacologic gate及direct规则保持不变。

## 必测

- PNH项目与`Paroxysmal Nocturnal Dyspnea`不得匹配。
- RA项目与`Rheumatoid Lung Disease`不得匹配。
- `Paroxysmal Hemoglobinuria, Nocturnal`与
  `Paroxysmal Nocturnal Hemoglobinuria`仍应因完整token集合等价而匹配。
- 项目`阵发性睡眠性血红蛋白尿症（PNH）`与候选独立`PNH`、候选括号`(PNH)`仍匹配。
- 第07轮新增反例、全部v4与旧triage测试、py_compile全绿。

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_08_COMPLETE`
