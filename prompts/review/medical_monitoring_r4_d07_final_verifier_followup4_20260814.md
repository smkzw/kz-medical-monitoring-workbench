# D07 overlay 顶层哈希修订后的最终同会话裁决

继续同一 Luna verifier 会话。上一轮唯一阻断是 overlay 继承了陈旧 frozen 顶层 `content_hash`。现已改为显式 `frozen_content_hash` 与自洽 `overlay_content_hash`，并增加测试。全程只读。

Read these files only:

- `runs/review/medical_monitoring_r4_d07_final_verifier_followup3_20260814.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_challenge_matrix.py`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`

## Hard boundaries

- 不修改文件，不启动服务/8911，不运行真实项目/数据/模型。
- 仅 synthetic/offline D07 验收，不代表 UI、R5 或医学写作。
- 禁用缓存/bytecode，核对首尾 SHA。

独立验证：overlay 不含 `content_hash`；`frozen_content_hash` 等于冻结 catalog hash；`overlay_content_hash` 等于排除自身字段后的实际 overlay hash，且与 frozen hash 不同；冻结 catalog/registry identities 不变。抽查前述 Query/Journey/typed 阈值无回退，并运行决定性 D07/R4/generator/Ruff/8911 检查。

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_final_verifier_followup4_20260814.md

由 runner 持久化。仅以 `ACCEPT_D07_RUNTIME` 或 `REVISE_D07_RUNTIME` 开头。
