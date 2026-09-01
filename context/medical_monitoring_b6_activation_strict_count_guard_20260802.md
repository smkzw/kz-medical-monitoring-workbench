# B6 activation gate 严格计数边界（2026-08-02）

## 发现

`services/api/app/monitoring_b6_activation_gate.py` 已对权限字段要求真实 boolean，但在把只读 B6
JSON 适配为 `B6ActivationGateReport` 时仍使用 `int()` 转换 `candidate_count` 与 `outcome_count`。
这会让布尔、数字字符串或浮点值被误当成权威候选/审查计数，削弱 pending-review 门禁的证据完整性。

## 修订

- 新增 `_strict_nonnegative_int`，只接受明确的非负 Python/JSON integer；拒绝 boolean、字符串、浮点、
  负数和缺失值。
- B6 candidate/blocker/review ID 字段现在必须是字符串数组；不再把异常 scalar 通过 `tuple()` 拆成
  字符参与候选或阻断计数。
- C13 adapter 现在重算并比对 `report_content_sha256`（canonical JSON 去除自身哈希字段）；内容被
  篡改而未同步哈希时直接拒绝。
- `B6ActivationGateReport` 直接构造路径也复用严格整数校验，拒绝 Python `bool` 作为 `int` 子类绕过
  adapter。
- B6 adapter 在构造报告前严格验证 candidate/outcome count；正常的当前 B6 artifact（5 candidates、
  0 outcomes）不变。
- 未改变 `B6ActivationGateReport` 的 pending-review、全阻断 C13、无写入/迁移/激活权限约束。

## 验证

- `py_compile` 与 Ruff 通过。
- `tests/test_monitoring_b6_activation_gate.py` 新增 malformed count/array-shape/content-hash/direct-report
  cases；与 assurance、release gate、migration contract、AI release/evaluation 相邻回归合计 **75 passed**。
- 源/test SHA-256：
  - `services/api/app/monitoring_b6_activation_gate.py`：`5140d87bb0e137a552e57ac24b1d26812fc0c0f9cf69cb3dab73efe639b65c72`
  - `tests/test_monitoring_b6_activation_gate.py`：`bb0235db70bcc837076e0e7e77482f9cef6aff69235d28ec93292aa38d0c007b`
- 用当前磁盘上的 B6 JSON 与 C13 `ACTIVATION_PROJECTION_BLOCKED_REPORT.json` 做只读 replay：
  `blocked_pending_b6_review`、5 candidates、0 outcomes、C13 46/46 blocked，activation/event/
  projection 均为 `false`；生成的纯内存报告 SHA-256 为
  `33bedf8a7d5e1046a5a8bde321f7ebf99a02016172a003bc78b0e477be8f8e03`。

## 边界与发布意义

- 仅做纯内存 B6/C13 contract 测试及当前磁盘 JSON 的只读 replay；未读取或修改权威 SQLite，未启动
  API/8911/5174/浏览器，未调用 provider，未运行真实项目，医学写作未触碰，18911/PID 43191 未触碰。
- 当前 B6 仍 `pending_review`、5 candidates、0 outcomes、migration/write 权限均为 `false`；本修订
  只避免 malformed gate 被误判，不能替代 reviewer outcome、aggregate/CAS replay、source lineage
  revalidation 或商业发布证据。
