# 医学监查 P8 保障工作区形状防护（LOOP 3.82）

**时间：** 2026-08-02 08:05 CST  
**范围：** 前端锁库前/核查前保障工作区的任务列表、任务详情、全量重算证明、三级汇总和创建回执；不启动服务、不调用 API/provider、不打开浏览器、不运行真实项目、不写权威运行库。

## 结论

保障工作区此前把列表 `items`、任务详情、proof/rollup 回执交给宽松默认值处理。跨项目、错误任务身份、缺失冻结身份、错误生命周期、scalar collection、boolean/string 计数或错误证据身份可能被当成空列表/空证据继续展示，或使旧任务状态留在当前项目页面。

本 LOOP 新增 `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.mjs`，并让 `MedicalMonitoringAssurancePanel` 在所有读取和创建状态提交前统一校验：

- 任务必须绑定当前项目、合法保障模式/生命周期、正整数版本、完整九字段 frozen identity、更新时间和严格布尔医学复核标记；
- 列表必须是当前项目的数组，且不能混入另一保障模式或 malformed task；
- 详情必须与请求的 task id 相同；
- pre-lock proof 必须绑定项目/任务、proof id，且失败/跳过/开放风险计数为显式非负整数，三级对账为严格布尔值；
- pre-inspection rollup 必须绑定项目/任务、risk snapshot，保留 subject/site/trial、distribution、remediation/evidence manifest 和 content hash 的数组/对象边界；
- 创建回执必须先验证 project/task/mode/replayed，再刷新列表；
- 形状异常会清空旧任务/证据状态并显示错误，不把异常响应伪装成“暂无任务”或“证据已完成”。

这只是 P8 前端输入和项目隔离安全合同，不改变 assurance 后端状态机、authority 写入许可、B6 gate 或医学事实。

## 验证

- `node frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.test.mjs`：**18 passed**；
- 原有 `medicalMonitoringAssurance.test.mjs`：**20 passed**；
- `medicalMonitoringProjectSwitchIsolation.test.mjs`：**66 passed**；
- 全部 `frontend/src/features/medical-monitoring/*.test.mjs`：**22 个文件全部通过**；
- `python3 -m pytest -q tests/test_monitoring_assurance.py tests/test_frontend_monitoring_contract.py`：**48 passed, 1 warning**；
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_unified_risk_workbench_contract.py tests/test_frontend_timeline_contract.py`：**54 passed**；
- `npm run build`（工作目录 `frontend/`）：Vite **1925 modules transformed**，构建成功；仅既有大 bundle warning。

关键 SHA-256：

- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.mjs`：`6964ea456e95b1f632c25bc34546ccef606c73a73a949c084e931a4281aa372b`；
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.test.mjs`：`a4760cb02dfc37a38af840f12bf569e5119424f444fae97b34b20eef425a0c54`；
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`：`7ec1778d9ea6860f5bb71ac57ada6325fc28e25befb8d166acfd591e5207b0a5`；
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：`3d5719f4d0d18483f9cd5b2b9d80045a9a92ee08536ea8b2b6ab95bc90c45f54`；
- `frontend/dist/assets/index-Bj_UipZO.js`：`fc47dd35b3164a3940c05e86030365b3c6f7e593a81b451ac2480bc2ab273a47`；
- `frontend/dist/assets/index-Byy1M7Be.css`：`b5c1a6ff0be5aa31c4d57825796880dbb13c24b93914b19d4ba1e420cd8ed6ca`；
- `frontend/dist/index.html`：`0759b34f9231e11e3d6df68813f3fada548871d4fe111c839e4af5976c0f8305`；
- `frontend/dist/runtime-build.json`：`1060c50395e28c9f8e16e21c655838f78a27260eb1939346bdbd1aa9fe6e4d61`。

## 边界与未证明项

本切片不代表真实 pre-lock/pre-inspection 任务创建、proof/rollup 生成、三项目 assurance、浏览器视觉/交互验收、B6 authority、aggregate/CAS、source-token lineage、运行时迁移或商业发布。B6 仍为 `pending_review`（5 candidates、0 outcomes、2 unresolved blockers、`migration_ready=false`、`write_permitted=false`）；C13 仍 3 个 schema-only reports 且 `activation_allowed=false`。8911/5174 保持停止，18911/PID 43191 未触碰。

下一安全顺序仍为：授权 B6 reviewer outcome → 实际 aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run；在此之前不得 API POST、真实 onboarding、Timeline/Profile runtime activation、迁移或 dual-write。
