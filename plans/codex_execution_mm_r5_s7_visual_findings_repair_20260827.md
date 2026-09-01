# Codex Execution Plan: mm_r5_s7_visual_findings_repair_20260827

Objective: 按当前三模型真实浏览器发现，对R5-S7合成离线产品做最小纠偏：连续真实访视日期、八域轨道与可见语义缩放、受试者身份条一致、原始来源精确字段可见；保持GET-only、合成离线、医学写作542文件边界，不改安全实现；完成聚焦/相邻回归与build。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端与夹具：仅修改services/api/app/medical_monitoring_r5_product_adapter.py及对应tests/test_medical_monitoring_r5_product_adapter.py、tests/test_medical_monitoring_r5_product_router.py；修正40访视连续实际日期，确保来源evidence已有record_ref/canonical_location/excerpt可供前端直观呈现；不得修改鉴权、安全或医学写作。 | `runs/execution/mm_r5_s7_visual_findings_repair_20260827/worker_01.md` |
| `worker_02` | 前端体验：仅修改frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx、medicalMonitoringR5.css及同目录现有R5测试；实现八域分轨展示与+/-/0键盘及可见按钮语义缩放、身份条从canonical route回填项目/批次/版本、来源页展示原始定位/记录号/引文；保持中文原生与GET-only。 | `runs/execution/mm_r5_s7_visual_findings_repair_20260827/worker_02.md` |
| `worker_03` | 独立验证：只读核验前两项当前bytes，运行R5聚焦及相邻测试、production build、禁止词/GET-only/医学写作542文件摘要/8911和5174停止检查；输出ACCEPT或REVISE，不修改源码。 | `runs/execution/mm_r5_s7_visual_findings_repair_20260827/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
