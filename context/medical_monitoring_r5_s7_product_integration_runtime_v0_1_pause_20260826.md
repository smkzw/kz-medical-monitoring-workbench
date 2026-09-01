# 医学监查 R5-S7 无损暂停检查点

暂停日期：2026-08-26

## 当前停止点

R5-S7 浏览器验收合同 v0.1 已冻结并接受；其下的离线产品集成运行时已完成两轮同会话纠偏，并由独立 verifier 返回 `ACCEPT_R5_S7_PRODUCT_RUNTIME_V0_1`。当前在启动任何真实服务或浏览器验收之前暂停。

## 本阶段已完成

1. 后端只读产品适配器、三个 GET-only 路由及 allowlist 门禁。
2. 前端 R5 产品页面、路由状态、严格投影适配、中文用户界面与聚焦测试。
3. source-evidence 窄表面校验、风险集合 fail-closed、权威变化分层计数、中心 exact identity 四项跨层纠偏。
4. 后端聚焦 22 passed、独立相邻 150 passed；前端聚焦三入口与独立相邻 41 passed；生产构建通过。
5. 独立验收、验收记录、Codex review、metrics 和受控 runner 证据已保留。
6. `hermes_workflow_guard.py audit-execution` 返回 `ok: true`，三名 worker 输出完整，无 warning/error。

## 当前 16 个产品运行时文件 SHA-256

```text
e64bf4af61ee3e07e6939e9ec7ebd5faf6e62cd8a93797f51f5c4ce90528a67c  services/api/app/medical_monitoring_r5_product_adapter.py
713529a1a1d296154b568bfd213b8e1c1b3e9f6bd4214313e7355a70e97cdfcd  services/api/app/medical_monitoring_r5_product_router.py
7e1517941511acbe34895d9ed87c91a289d768732fab433cc76002c06c33424a  services/api/app/main.py
c5a9dcb15128f3a4b3b592fa835640b7c69ca4172391941912939b2e8240649e  services/api/app/monitoring_read_action_contract.py
e9f79ced0beac9ec0f9f75cc1ff9ed859dff7d2499a7b3f08f21eb1ee0d2f728  tests/test_medical_monitoring_r5_product_adapter.py
bee1683a30b1609838ee21d009b92711f70145246ea057bb98406ae85c40e05e  tests/test_medical_monitoring_r5_product_router.py
8106f2ebe21dba37fff8a02bc8e3584dbaa79aef4c7166ba5ecece404341450d  tests/test_medical_monitoring_r5_product_allowlist.py
671791533bd9f6931fac86caf8d2c990eda7eeaaa280b72e7a7392da5dd7b202  frontend/src/App.jsx
803bd06b3550ce93785e7166be178a5f55ebb81fc16e32ec4f411560957bed8b  frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx
c15cdc9f031d33162e3bec0521b762101f008e7dbc9e46fdaf27f38379338a2f  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs
7622699a92010987b04f4ad91254d7da2c99a98ba2f99fd45bad2ee613304d7d  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs
2d517cba5c86f7349aa6688663dd876797db43b3819c0896634a032f74c89b1c  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css
4fe06f93347840844d1d9768aa19419602eea6ba6781d0fa12b10ece0fd7d417  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Fixtures.mjs
2fa87555e260d87d9858747399f99681e8ec28cd967e3d3b24d2af8feea98476  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.test.mjs
7ae85450b95145e5c0521867d11ed3ed8f8108e70af3b9a974e2bf89fd489569  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.test.mjs
2261e3c81113b4b0dfae140bd7a43a69aaaf9e22959cc96ceb9e649298474d19  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5ProductContract.test.mjs
```

## 保护边界与运行状态

- 医学写作子系统保护清单：542 files；aggregate SHA-256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911、5174：停止，无 LISTEN listener。
- 未启动浏览器、未运行真实项目、未调用真实模型。
- 6 个临时 follow-up prompt 已删除；基础 prompts、runner reports、合同和验收证据保留。

## 尚未完成

1. 合同矩阵中的 13 个状态 × 2 个视口尚未产生浏览器实测证据，矩阵仍应保持 `planned_unmeasured`，不得改称通过。
2. 视觉层级、中文原生表达、Patient Journey 访视轴、事件/风险标记、跳转和响应式体验尚未由 Codex 在真实浏览器逐项验收。
3. 尚未进行真实服务运行、真实项目、真实模型或医学内容准确性验收。

## 下一安全动作

恢复时先完整读取本检查点、R5-S7 合同、浏览器矩阵、运行时验收记录及最终 verifier 报告，并重新核对上述 16 个 SHA 与 8911/5174 停止状态。确认无漂移后，再单独初始化浏览器/视觉 acceptance packet；随后才可短时启动隔离服务，按 26 个矩阵行逐项采集可见证据。不得直接进入 R6，也不得把离线运行时接受表述为产品最终接受。
