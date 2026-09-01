# 医学监查保障面板严格计数显示（2026-08-02）

## 发现

前端 `MedicalMonitoringAssurancePanel.jsx` 在锁库前证明和核查前三级汇总中使用 `?? 0` 显示计数。
当后端字段缺失、类型错误或数组未返回时，界面会把“未知”显示成 `0`，与 assurance/rollup 的
fail-closed 证据语义冲突，也可能让医学经理误以为没有失败、跳过或整改项。

## 修订

- proof 的 failures、skips、open-high-risk、closed-without-evidence 统一经过既有
  `assuranceRollupNumber`；非法/缺失值显示 `—`。
- rollup 的 subject/site/evidence/remediation 数组只在确实为数组时计算长度；缺失或错误形状显示
  `—`，不生成零事实。
- 仅改变保障面板的显示归一化，不改变 API、任务状态、风险事实或写入权限。

## 验证

- `tests/test_frontend_monitoring_contract.py`：**22 passed**，新增断言覆盖 proof 与 rollup 的未知计数。
- `medicalMonitoringAssurance.test.mjs`：**20 passed**。
- `medicalMonitoringAssuranceRollup.test.mjs`：**16 passed**。
- `frontend/` 中 `npm run build`：Vite 1919 modules transformed，构建成功；仅保留既有 bundle >500 kB warning。
- 源/test/build SHA-256：
  - `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`：`9cd5b5f03fea01a6d17386c4949dd55e62213f2d31e918a99544ab6e32ffc55d`
  - `tests/test_frontend_monitoring_contract.py`：`728d003df8b6674960c32b657854e18ecb033e0a8d21fa9ac2c0c49750ba00d0`
  - `frontend/dist/index.html`：`11b19f418989fcd58eddba5daa88709c629eb5f7e7f52e502fbb0ead2cc5dae9`
  - `frontend/dist/runtime-build.json`：`1e9e527a6d584e6d74253c3db59ae0a44cdeb0c6a7d579194dc3a7e676992c8f`

## 边界

- 未启动 Vite 服务、8911、5174、浏览器、provider 或真实项目；构建为离线产物生成，未接入运行时。
- 未读取/修改权威 SQLite，未修改医学写作文件，18911/PID 43191 未触碰。
- 该修订提高未知证据的可见性，不能替代真实三项目浏览器验收、B6 reviewer outcome 或商业 release dossier。
