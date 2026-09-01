你是独立只读 verifier，使用全新上下文。完整读取 `/Users/smkzw/.codex/AGENTS.md` 与工作台 `AGENTS.md`。

Read these files only:

- `AGENTS.md`
- `context/medical_monitoring_r4_d07_oracle_erratum_decision_20260814.md`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_challenge_matrix.py`
- `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_followup2.md`

## Hard boundaries

- 只读；禁止修改任何文件。
- worker 报告仅是待验证声明，不能作为结论。
- 独立运行只读命令，比较 case 002 与 030。
- 中和所有 case-specific 合成 ID、locator、引用及由其派生的 hash 后，判断 typed input 是否语义完全相同。
- 精确比较两者 oracle 的 expected leaf、trace、source；从合同与同族 cases 001/002/003/031/073 判断哪一侧 source-jump 规则一致。
- 禁止按 case ID 建议运行时分支，禁止放宽 exact-leaf 校验。

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_case030_verifier_20260814.md

该文件由 runner 持久化；你只在最终回答返回完整报告，不自行写文件。

报告必须包含：读取源、实际命令、语义归一化方法与结果、oracle 差异、合同推导、结论、允许修改的精确叶、残余不确定性。最终 verdict 只能是 `ACCEPT_ORACLE_ERRATUM_CASE030`、`REJECT` 或 `INCONCLUSIVE`。
