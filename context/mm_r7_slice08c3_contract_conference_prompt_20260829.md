# Conference role: R7 Slice-08C-3 contract acceptance

只读独立挑战并验收：
`context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md`

必须对照：
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_1_20260829.md` §8；
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md` §19–20（冲突时 v0.2 胜出）；
- 当前 `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`、`medicalMonitoringR5Timeline.mjs` 与 `r7/MedicalMonitoringR7ProductLoop.jsx`；
- 已接受 08C-2 的 continuity validator/filter/route helper。

重点检查：是否保持唯一横向访视轴；是否避免第二条历史；continuity 是否严格绑定同一 project/result/site/subject/spine/window；event/risk 关联是否会误绑；关闭是否只清除选择而保留轴窗；overlay/push、焦点、Esc、backdrop、body lock、reduced-motion 是否可实施且不互相矛盾；抽屉内容顺序、严重度和中文是否符合医学监查；08C-3 与 08C-4 边界是否清楚。

只输出以下之一：
- `ACCEPT`，并列出可定位证据和实现前提；或
- `REVISE`，按 P0/P1/P2 列出必须修改的合同条款和原因。

不得修改文件，不得启动服务、浏览器、模型或真实项目，不得声称实现或视觉验收完成。
