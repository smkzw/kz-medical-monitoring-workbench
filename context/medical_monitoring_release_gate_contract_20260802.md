# 医学监查商业发布总门契约

**日期：** 2026-08-02  
**范围：** P0–P10 证据聚合的纯内存判定；不执行迁移、不写 SQLite/API、不激活 AI、不启动服务。

## 新增契约

新增 `services/api/app/monitoring_release_gate.py`，要求以下 16 个门必须各有唯一、带
SHA-256 的证据：

`source_authority`、`three_real_projects`、`continuous_full_snapshot`、
`daily_monitoring_loop`、`assurance_subject_site_trial`、`rule_family_coverage`、
`independent_product_ai`、`risk_disposition_authority`、`timeline_profile`、
`project_site_subject_rollup`、`source_traceability`、`total_system_consumers`、
`persistence_restart_recovery`、`browser_interaction_matrix`、
`medical_writing_protection`、`commercial_release_dossier`。

每个门只能为 `passed`、`partial`、`unproven` 或 `blocked`；缺门、重复门、未知门、缺少
证据摘要/证据哈希均 fail-closed。即使 16 门全部 `passed`，B6 仍必须同时为
`approved`、`write_permitted=true`、`migration_ready=true`、`migration_write_permitted=true`，否则总门不能 ready。该契约
只返回不可变判定，不授予任何写入或医学批准权限。

## 当前文件系统只读判定

以 `RELEASE_GATE_AUDIT_20260802.md` 为证据 bundle、读取当前
`B6_REVIEW_OUTCOME_GATE.json`，得到：

- `status=blocked`
- `release_ready=false`
- 16 个门全部列入 `unmet_gate_ids`（状态为 partial/unproven/blocked）
- B6：`pending_review`、5 candidates、0 outcomes、`migration_ready=false`、
  `write_permitted=false`、`migration_write_permitted=false`
- 通过 persisted B6 shape 的 strict adapter 后，in-memory decision SHA-256：
  `65cebad5f3cbccbb42a9889c15de8ff4a466fa45faad09bc2d6d79f606101301`

该结果与当前发布审计一致，证明总门不会因 v12 canary、局部 Node 测试或静态 UI 证据而
误报商业 ready。

## 验证

- 新增聚焦测试：5 个后扩展为 **7 passed**（含 B6 adapter 与三个 authority flag 必须为 boolean 的 fail-closed 回归）。
- B6 activation gate、release-gate、迁移、AI release/evaluation 相邻测试合计 **38 passed**；
  其中 B6 原有 `build_b6_activation_gate_report()` 也改为拒绝字符串权限字段的隐式转换。
- `py_compile` 通过；Ruff 通过。
- 源文件 SHA-256：
  - `services/api/app/monitoring_release_gate.py`：`4ca92f69f2752cce93688f0ff3593809e9ba7b4b7850f5fbb287c582104428a7`
  - `tests/test_monitoring_release_gate.py`：`9e7e80286b5a027b3edbdec4966425d5ec6b544cbf60dab04c266fa4cfc94fb1`
  - `services/api/app/monitoring_b6_activation_gate.py`：`59e9cd31ec240ca0b5738d6185a3ea5a933b19dcb27fbbee37b4afb6f272c07c`
  - `tests/test_monitoring_b6_activation_gate.py`：`33b4bd3b936f0b7e5b9a04a478184e01f1f7a5e2a9ea4ca984c3aacc426e2c66`

## 边界

该契约仍不替代 B6 reviewer outcome、真实 aggregate/CAS、三项目连续批次、产品 AI 科学性、
浏览器交互、总系统消费者或最终用户验收。它只保证“未满足时不能误报满足”。
