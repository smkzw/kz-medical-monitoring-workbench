# D07 三项定向修订后的同会话最终复核

继续原 Luna verifier 会话。上一轮你返回 `REVISE_D07_RUNTIME`；实现方已定向修订。请只读复核，不能因测试全绿自动接受。

Read these files only:

- `runs/review/medical_monitoring_r4_d07_final_verifier_followup_20260814.md`
- `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_codebuddy_followup3.md`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_query.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_fixtures.py`
- all `poc/medical_monitoring_ai_native_r4/tests/test_d07_*.py` files and `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py`

## Hard boundaries

- 全程只读，不改文件、不启动服务/8911、不读真实项目/数据、不调用真实模型。
- 只验收 synthetic/offline D07；不代表产品 UI、R5、真实项目或医学写作接受。
- 禁用测试缓存和 bytecode。关键源码测试前后 SHA 必须一致。

必须独立复现并判断：

1. unknown ID、wrong kind、tampered/missing target hash、scope/locator mismatch 的 Journey 是否同时令 jump、audience、projection fail-closed。
2. 相同五类 malformed `valid_jumps` 是否令 Query source/visible/scope 或总体校验失败，且正常结构化 jumps 仍通过。
3. evaluator 中是否已无通用 `0.02`/`5` fallback；缺少 typed 字段是否 fail-closed；改变 typed 阈值是否真实改变行为。
4. 特别审查 `d07_fixtures.py` 在冻结 catalog hash 校验后注入字段并 rehash 的做法：它只能是 synthetic fixture adapter，不能伪装成生产 authority。判断其是否满足当前冻结 D07 POC 合同；若不满足，给出不改冻结 artifacts 的最小可行修订边界。
5. generator 三项、focused D07、R4、R1-R3、Ruff、8911 状态与源码/冻结锚首尾 SHA。

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_final_verifier_followup2_20260814.md

报告由 runner 持久化；返回 `ACCEPT_D07_RUNTIME` 或 `REVISE_D07_RUNTIME`，失败时给最小复现和精确边界。
