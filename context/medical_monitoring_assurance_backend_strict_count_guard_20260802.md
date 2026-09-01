# 医学监查全量重算证明后端严格计数防伪（2026-08-02）

## 发现

`services/api/app/monitoring_assurance_repository.py` 在保存全量重算证明时原先使用
`int(value)`/`bool(value)`。因此 `False` 可以被当作计数 `0`，`True` 可以被当作计数 `1`，
而字符串 `"false"` 会被当作真值；从持久化 JSON 读取时也直接信任这些字段。该行为会削弱锁库前
全量重算证明的 fail-closed 语义。

## 修订

- 新增 `_nonnegative_int`：只接受非负整数或明确的数字字符串；拒绝布尔、空白、浮点和负数。
- 新增 `_strict_bool`：只接受真正的 JSON boolean；缺失字段按现有兼容默认值 `False`，字符串不再
  静默转换。
- 保存证明和从持久化 JSON 恢复证明均经过同一组严格校验； malformed payload 直接抛出
  `MonitoringAssuranceError`，不会写入证明或推进任务版本。
- 未改变正常整数/数字字符串、既有风险 reader 自动重算和 idempotency 语义。

## 验证

- `py_compile`：repository、service、测试文件通过。
- Ruff：上述变更文件通过。
- `pytest -q tests/test_monitoring_assurance.py`：**26 passed**。
- 与 B6 activation、release gate、migration contract、AI release/evaluation 的相邻回归合计
  **64 passed**（同一轮命令）。
- 新增覆盖：`failures=false`、空白 `skips`、负数计划计数、`subject_reconciliation_ok="false"`
  均 fail-closed；篡改临时测试库中的持久化 `failures=false` 在读取时同样被拒绝。
- 当前源 SHA-256：
  - `services/api/app/monitoring_assurance_repository.py`：`118f2525127a86283129f387086cce1282f0a209bef34f514f94ee8685c501ce`
  - `tests/test_monitoring_assurance.py`：`842a5d5df45d9a4d9112927a55d0533f85fbf75c9df9ce00d7e7741f43fdd57a`

## 边界与发布意义

- 测试仅使用 pytest 临时 SQLite；未打开或修改权威运行库，未启动 API/8911/5174/浏览器，未调用
  provider，未接入真实项目，未修改医学写作文件；18911/PID 43191 未触碰。
- 该修订只提高锁库前证明对 malformed count/boolean 的防护，不产生风险事实、不授予写入/迁移权限，
  不能替代 B6 reviewer outcome、aggregate/CAS replay、真实三项目 LOOP、浏览器/科学性验收或商业
  release dossier。B6 仍为 `pending_review`（5 candidates、0 outcomes、2 blockers）。

## 下一安全动作

取得授权 B6 outcome 后，先做实际 aggregate/source-token replay 与 approved-input dry-run；在此之前
保持所有权威写入、迁移、真实 onboarding 和 8911/5174 启动停止状态。
