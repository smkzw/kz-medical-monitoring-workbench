# D07 最后两个接口边界修订后的同会话裁决

继续同一 Luna verifier 会话。上一轮只剩 Query 物化 jump 接口和 frozen/overlay fixture 身份两个缺口；现已定向修订。全程只读。

Read these files only:

- `runs/review/medical_monitoring_r4_d07_final_verifier_followup2_20260814.md`
- `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_codebuddy_followup4.md`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_query.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- all `poc/medical_monitoring_ai_native_r4/tests/test_d07_*.py` files and `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py`

## Hard boundaries

- 不修改任何文件，不启动服务/8911，不运行真实项目/数据/模型。
- 仅 synthetic/offline D07 验收，不代表产品 UI、R5 或医学写作。
- 禁用缓存/bytecode，首尾 SHA 必须稳定。

独立验证：

1. raw `target_object_id` 与 materialized `target_ref` 正常路径均通过；并存冲突、缺失和五类 target 变异全部 fail-closed。
2. `build_indexes()` 的 `catalog`/`frozen_catalog` 保持 on-disk 冻结内容与 substantive hashes；overlay 深拷贝、单独命名与单独 hashes；runtime case 只来自 overlay；调用者不再把 overlay 当冻结 catalog。
3. 前两轮已通过的 Journey、typed 阈值 fail-closed 不得回退；generator、D07/R4、R1-R3、Ruff、8911、冻结锚复核。

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_final_verifier_followup3_20260814.md

由 runner 持久化。返回且仅以 `ACCEPT_D07_RUNTIME` 或 `REVISE_D07_RUNTIME` 开头；若拒绝，必须给新的最小复现和精确边界。
