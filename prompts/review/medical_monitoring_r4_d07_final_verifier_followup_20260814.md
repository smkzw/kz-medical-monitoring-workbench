# D07 反过拟合修订同会话复核

你是上一轮 D07 独立验收审阅者。继续同一只读会话，不修改任何文件。

Read these files only:

- `runs/review/medical_monitoring_r4_d07_final_verifier_20260814.md`
- `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_codebuddy_fallback.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_query.py`
- all `poc/medical_monitoring_ai_native_r4/tests/test_d07_*.py` files and `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`

## Hard boundaries

- 全程只读；不得修改源码、测试、合同、oracle、catalog、registry、生成器或医学写作子系统。
- 不启动服务或 8911，不运行任何真实临床项目，不调用真实医学数据或真实模型端点。
- 只可运行 synthetic/offline D07 及其相邻 R1-R4 回归和静态校验。
- 不创建上述唯一报告以外的持久文件；测试缓存必须禁用。

本轮只判断上一轮 `REVISE_D07_RUNTIME` 的三类缺口是否已被真实关闭：

1. Journey 来源目标必须按声明 schema、对象哈希、scope、locator 真实校验；未知 ID、错误 kind、篡改/缺失 hash 不得被回退或重写后放行。
2. Query 的 `source_jump_valid`、`visible_path_valid`、`scope_equal` 必须由上下文和目标证据推导；缺失 typed input 或 valid jumps 必须失败，不得以常量真值或降级路径通过。
3. evaluator 不得依赖挑战样例 ID 或固定 fixture 输出；保留的医学算法常量必须是冻结合同中未参数化的真正核不变量，并有离开原样例窗口、阈值、转换和端点组合的变异证据。

请独立执行最小但决定性的负向变异、全 D07/R4 代表性回归、生成器一致性检查；核对测试前后关键源码 SHA 是否稳定，并确认合同、catalog、generator 冻结锚未漂移。不得把已有通过日志当成验收替代品。

输出必须包含：

- `ACCEPT_D07_RUNTIME` 或 `REVISE_D07_RUNTIME`
- 逐项核验结论及命令/结果
- 若 REVISE，给出可复现的最小失败输入与精确修订边界
- 明确本验收仅覆盖 synthetic/offline D07，不代表产品 UI、真实项目、真实模型、R5 或医学写作子系统验收

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_final_verifier_followup_20260814.md

该文件由 runner 持久化；你只在最终回答返回完整报告，不自行写文件。
