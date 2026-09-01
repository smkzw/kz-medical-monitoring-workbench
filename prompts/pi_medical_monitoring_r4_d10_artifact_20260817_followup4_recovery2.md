继续原 session 与当前文件状态。上一轮已经定位到 `measure_origin` builder 并开始修改；现在立即完成剩余补丁，不再解释计划。

Hard boundaries:
- Work only inside current runner workspace `.`.
- 仅编辑 D10 三个 generator、独立 verifier、D10 artifact tests 与五个 D10 synthetic JSON；不得触碰 D09、`src/mm_r4`、UI/服务、真实项目、医学写作或 8911。
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260817_followup4_recovery2.md`; do not write it with tools.

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

必须在本轮完成五项门、重生成全部工件、重签 pins、运行四项 check、完整 D10 tests、D09 99 tests 和 8911 检查。若某补丁失败，立即读取准确上下文改用正确 anchor 后继续。最终报告实际 SHA/测试/探针结果；不得只报告下一步，也不得自称 ACCEPT。
