# R7 Slice-08B 实现独立验收上下文

## 目标

只读独立审阅 Slice-08B 的实际实现是否满足已冻结 v0.1 + v0.2 合同。输出必须是 `ACCEPT` 或 `REVISE`，并给出文件、行号、最小复现命令和修复建议。不得修改源码、不得启动服务、不得运行真实项目或模型。

## 必读

- `AGENTS.md`
- `reviews/medical_monitoring_r7_slice08b_authority_artifact_bridge_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice08b_authority_artifact_bridge_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice08b_contract_acceptance_record_20260829.md`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity_bridge.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py`
- `services/api/app/medical_monitoring_r7_product_router.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_continuity_bridge.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_continuity_registry.py`
- `tests/test_medical_monitoring_r7_product_router.py`
- 三份 execution worker 报告及 execution audit 结果。

## 已有确定性证据

- execution packet 的三名 worker 均已返回，`audit-execution` 为 ok。
- Codex 修正桥接器后，聚焦测试 `22 passed`。
- Codex 当前合并测试：R7 + 产品路由 `317 passed in 40.99s`。
- 当前范围为 synthetic/offline；8911/5174 必须停止，医学写作子系统必须不变。

## 必须重点挑战

1. 是否真正复用 R5 typed packet、R6 frozen validators、R1 Store，而不是复制第二套规则。
2. 四个 ModeOutput、post-lock output set、固定五条原子抽取路径和 R5 成员闭包是否 fail closed。
3. `r6_output_set_digest`、显式 artifact 成员集、item digest 是否使用合同指定 canonical；是否存在隐式按 run 枚举 artifacts。
4. R1 字节/证据验证、LaunchRegistry v4 additive migration、四摘要 CAS、available replay、故障回滚是否完整。
5. 产品路由是否伪造真实身份/版本字段，是否把 synthetic 测试默认值泄漏成实际产品语义；没有 R6 provider 时是否错误地宣称结果可用。
6. bridge 是否越权创建或吞掉 R1 Store 错误，失败后是否留下会被误认权威的状态。
7. Query 草稿与风险/受试者/中心闭包以及跨对象依赖是否满足合同。
8. 任何通过测试但不满足合同的缺口，尤其是脆弱导入、异常过宽捕获、孤儿 artifact、成员 JSON 篡改复核遗漏。

## 边界

- 只读，可运行最小 synthetic 测试。
- 不修改文件，不启动端口，不访问真实项目，不调用模型。
- 不审查 UI/视觉；这是后续 Slice。
- Codex 保留最终接受权。
