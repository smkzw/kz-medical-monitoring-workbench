# 竞品分诊第09轮：确定性来源真值升级后的新run身份

继续同一session：`20260724_204518_3e5b86`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- 第08轮prompt、报告、当前源码和测试

Read these files only:

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- `tests/test_medical_writing_competitor_triage.py`
- `prompts/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_followup_08.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_08.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v5_run_identity_09.md`

不得自行写runner报告；final response返回完整报告。

## 复现

第08轮确定性后处理已实质升级：所有indirect统一复验、严格同适应症完整token/可证明括号缩写、
显式药理学干预类型、确定性文档角色和理由。但生产常量仍为：

```text
competitor_triage_deepseek_v4_source_truth
```

后端重载后，用相同D017不可变snapshot和新的idempotency key创建run，API返回：

```json
{
  "run_id": "ct_run_681a3edb8f7d10cfe256",
  "job_id": "mwjob_94caedeabb1a66a03e44d15a",
  "reused": true
}
```

因此旧v4模型输出和旧确定性后处理结果被直接复用，新源码没有执行，不能形成新发布证据。

## Hard boundaries

允许写：

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- `tests/test_medical_writing_competitor_triage.py`

不得改repository、main、contracts、journey、prefill、前端、DOCX、运行库或证据目录。

## 必须修复

1. 将运行/提示身份提升为能明确表示当前来源真值合同的新版本，例如
   `competitor_triage_deepseek_v5_source_truth`。该版本必须进入chunk envelope、run记录、
   canonical_input_hash和provenance的现有路径。
2. 不能修改或删除旧v4 run；版本提升后，同一snapshot/material facts必须生成不同
   canonical_input_hash、run_id和durable business key，形成全新任务。
3. 更新所有只因权威版本变化而过时的测试断言，不放宽任何第08轮医学语义。
4. 新增回归证明：
   - 当前常量为v5；
   - canonical输入含v5；
   - v4与v5身份不相同，旧记录不能被当前创建路径复用；
   - provider/model仍严格为deepseek/deepseek-v4-pro；
   - 第08轮全部同适应症、干预类型、文档角色和理由测试继续通过。
5. 复跑新旧triage测试和py_compile，报告真实计数。

完成标记：
`HERMES_COMPETITOR_TRIAGE_V5_RUN_IDENTITY_09_COMPLETE`
