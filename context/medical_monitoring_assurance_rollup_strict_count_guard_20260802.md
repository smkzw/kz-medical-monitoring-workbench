# 医学监查三级汇总严格计数防伪（2026-08-02）

## 发现

`frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRollup.mjs` 的原始计数归一化使用 `Number(value)`。在 JavaScript 中，`false` 会变成 `0`、`true` 会变成 `1`，空白字符串也可能变成 `0`；对风险总数、开放数或三级守恒计数而言，这会把 malformed payload 显示成看似有效的数字。

## 修订

- 布尔值和空白字符串现在归一化为 `null`，由 `assuranceRollupNumber` 显示为 `—`。
- 守恒逻辑因此保持 fail-closed，不把无效计数当作项目/中心/个例风险事实。
- 没有改变正常数值、字符串数字、排序、页面布局或任何 API/SQLite 行为。
- 锁库前全量重算证明的 `failures`/`skips` 也改为严格接受数值 `0` 或字符串 `"0"`；布尔值、空白和缺失值不再被 `Number(...)` 静默当作零。

## 验证

- 定向：`node frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRollup.test.mjs` → `16 passed`；保障门测试 → `20 passed`。
- 医学监查全部 Node `.test.mjs`：16 个测试文件全部通过（包含新增 false/空白计数与 proof 计数断言）。
- 前端离线构建：在 `frontend/` 执行 `npm run build`，Vite `1919 modules transformed`、构建成功；仅有既有 bundle >500 kB 警告，没有编译错误。生成的 `dist/runtime-build.json` 保持当前 API/frontend build identity。
- 未启动 Vite、8911、5174、浏览器或真实项目；未调用 provider/API；未打开/写入 SQLite；医学写作文件未触碰。

## 当前发布意义

该修订只提高了项目→中心→个例汇总的坏输入防护，不能替代真实风险集合守恒、浏览器矩阵、B6 reviewer outcome、aggregate/CAS replay 或商业发布 dossier。B6 仍保持 `pending_review`、5 candidates、0 outcomes、所有写入/迁移权限为 `false`。
