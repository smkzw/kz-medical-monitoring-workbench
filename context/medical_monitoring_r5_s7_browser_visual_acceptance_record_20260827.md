# R5-S7 浏览器与视觉核心验收记录（2026-08-27）

Decision: `ACCEPT_R5_S7_BROWSER_VISUAL_CORE_WITH_HY3_REPLAY_PENDING`

## 接受范围

接受当前 synthetic/offline R5 产品页面的用户可见核心：项目风险概览、中心风险图谱、风险证据、多模型分歧、受试者医学旅程、日期边界、AE/MH 匹配历史、来源一跳定位与返回上下文。接受基于当前文件、真实 Playwright 双视口截图、Codex 逐图复核和聚焦/相邻回归，不代表真实项目、真实医学结论、生产发布或 R5-S7 全合同关闭。

## 当前实现锚点

- 后端产品投影：`services/api/app/medical_monitoring_r5_product_adapter.py`，SHA-256 `96aa9754c10f52eb4c5605de4a07c1761aafaeb18572198afc63f554a2bf7679`
- 后端产品路由：`services/api/app/medical_monitoring_r5_product_router.py`，SHA-256 `130e963af034c5e983197b095d9183b2d9eb657fcc87ddceeb5d17958b32fd3b`
- 页面：`frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`，SHA-256 `cee0f3f748cb718cf16c1a9ff83e755b5f67d2e735c3db398259016e3bf2fd83`
- 前端适配器：`frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`，SHA-256 `057824c777845c522b9af06b7400ab2b70f1504e53b35155f8dff161530d8944`
- 路由状态：`frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs`，SHA-256 `a004e71db25dced4bc26cc5c8254d59610c2e3303d429f7867faff4b09664393`
- R5 样式：`frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css`，SHA-256 `24abf6221bbc80190cf18ce32a11b5abcc6541321d1aeb32c2f079029712ae26`
- 路由测试：`frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.test.mjs`，SHA-256 `1dcdcb77c8d421ad4d1b3d07c1b75920fb15e2f4fd6a4bc4dd6a56e8440fa213`
- 后端聚焦测试：`tests/test_medical_monitoring_r5_product_adapter.py`，SHA-256 `2d62d6ac9d2bdc5db5670ac796bf69531189d6855cc0ea308001077620e50303`
- 前端产品合同测试：`frontend/src/features/medical-monitoring/r5/medicalMonitoringR5ProductContract.test.mjs`，SHA-256 `dd3d91d74f81ead49507f30e5947c554552c471b7e5d455aa00c4e3230979b4d`
- Codex 测量 runner：`artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/run_measurement.mjs`，SHA-256 `a1ee0d9ddd50551dfd4be4b56888d16e64ce089404858dc472bdb1151813418d`

## 决定性证据

- 聚焦后端回归：`22 passed`。
- 前端：route state `28 checks passed`，adapter `41 checks passed`，产品合同通过。
- Vite production build：1960 modules transformed；仅既有大 chunk 非阻断 warning。
- MiniMax-M3 在原会话完成 26 行全矩阵 Playwright；修订后再次执行 9 场景 × 2 viewport，最终 `P0/P1/P2/P3/P4 = 0`。最终报告 SHA-256 `c97abbfaf0037b14725edc51739edf9913555840b060ab7f4cce06179c02417d`。
- Gemini 3.7 Flash 在原会话完成 26 行全矩阵 Playwright；修订后再次执行 9 场景 × 2 viewport，最终 `P0/P1/P2/P3/P4 = 0`。最终报告 SHA-256 `d473fb46e83b31d62a15d1caf02fd20105b51fc887cdd23132670cf59711687f`。
- Codex 逐图复核最新 1440×900 证据，确认风险徽标与标题不叠压、高密度事件使用临床中文、小样本不显示 0/0、返回后恢复 cutoff/start/end/risk 并清除受试者范围。
- Codex 自有 runner 已完成合同规定的 26 行测量：`26/26 passed`，26 张两视口截图齐全；browser/identity/network/performance 原始证据 SHA-256 分别为 `e617d245ee3058eddca70bb71abd577567b00f12acd13c1d64efb81dda1f01c4`、`5dd9417c2b55f0dfaaffaf9db02de9b37ccb380829d3bfb196ec0754dfde6845`、`24e02eee975545848c8e64044fb1d9f1b68caee633861b33c7493a79301b55b7`、`77565e1f90e093158af348b919dba030c5acd1364cc94862b7cdf41d4b084b0f`。
- 测量统计：cold p95 `969.56 ms`、warm p95 `953.22 ms`、交互 p95 `44.60 ms`、连续平移 FPS p05 `107.53`、首屏最大 `964 ms`；140 个网络记录均为 GET，失败、外部请求、console error/warning、page error 与非 GET 均为 0。
- 医学写作保护清单复算仍为 542 files，aggregate SHA-256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 最终停止证据：8911、5174 均无 LISTEN listener。

## 已关闭问题

1. 风险键、风险实例、spine、visit 与一跳定位保持一致。
2. 小样本明确显示“暂无法计算”及原因，不以 0/0 或 0% 暗示安全。
3. 证据面板显示为什么提醒、依据、发现、行动项、正反证、风险历史和三段式核查问题草稿。
4. 多模型分歧独立呈现，明确“暂不作为医学结论”。
5. 精确、部分、冲突、缺失日期及不确定访视归属均保留；访视间事件不强制吸附。
6. AE/MH 原疑似漏报、后续补录、匹配关系和 Query 草稿共享同一旅程。
7. 来源位置、版本/修订身份、风险时间窗与来源一跳状态可见。
8. 返回项目概览保留 cutoff/start/end/risk，清除 site/subject/spine 并恢复原风险证据。
9. 风险徽标、标题和域形状不叠压；高密度测试语料不再把“高密度风险 N”等测试命名暴露给用户。

## 尚未关闭的精确边界

- CodeBuddy CLI / HY3(max) 原会话的最终聚焦重放在完成 B01、B04、B05、B06、B08、B10 后遇到供应方 `429`，提示 2026-08-27 21:31:55 CST 后恢复。不得把该中断写成 HY3 最终零缺陷。
- Codex 最终测量包已经闭合，不再是阻断项；本记录仍不发布 `ACCEPT_R5_S7` 总关闭标记，唯一原因是 HY3 原会话最终重放尚未完成。
- 该边界不阻止已经完成的 R6 合同与挑战矩阵冻结；在进入 R6 runtime 实现前，必须先完成 HY3 同会话重放并由 Codex 复核其原始结果。

## 下一动作

1. 保持 8911/5174 停止。
2. 在 HY3 限流解除后复用 session `1d2324eb-0ec4-4466-a8e4-73c47aed9378` 完成剩余 B11/B12/B13 与两视口最终结论，不新建 HY3 会话。
3. Codex 核对 HY3 原始报告；只有其最终结论满足合同且无未处置问题时，才签发 R5-S7 总关闭标记并解锁 R6 runtime 第一条 synthetic/offline 纵切。
