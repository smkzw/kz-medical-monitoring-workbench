继续原 session，直接执行你上一轮已经完整形成的 A-E 修订计划；不要再次分析或复述计划。

Hard boundaries:
- Work only inside current runner workspace `.`.
- 只可编辑 D10 三个 generator、独立 verifier、D10 artifact test 与五个 D10 synthetic JSON；禁止 D09、`src/mm_r4`、UI/服务、真实项目、医学写作和 8911。
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260817_followup4_execute.md`; do not write it with tools.

Read these files only:
- `prompts/pi_medical_monitoring_r4_d10_artifact_20260816_followup4.md`
- `tools/generate_d10_fixture_authority.py`
- `tools/generate_d10_challenge_registry.py`
- `tools/generate_d10_expected_oracle.py`
- `tools/verify_d10_artifacts.py`
- `tests/test_d10_artifact_generator.py`
- `reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_typed_fixture_catalog_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json`

现在立即使用工具完成 measure-origin、Query、hidden subject-site pair、accepted source membership、ModelEvidence 五项修订，重生成工件并运行四项 check、完整 D10 tests、D09 99 tests、8911 检查。任何失败都在同一轮修到通过。最终只返回实际改动、固定 SHA、测试结果与残余风险，不得自称 ACCEPT。
