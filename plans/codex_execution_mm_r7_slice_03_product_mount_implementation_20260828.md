# Codex Execution Plan: mm_r7_slice_03_product_mount_implementation_20260828

Objective: 按冻结 SHA 23a01f90 的 R7 Slice-03 合同实现项目级医学监查 R7 产品挂载：局部中文响应、合法项目解析后打开每项目工作区、每请求关闭连接、MTPLX 默认/显式 DeepSeek、最小 main.py 接线与离线回归；不得启动服务/真实模型/真实项目，不得修改医学写作、前端或 R1-R6

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 services/api/app/medical_monitoring_r7_product_router.py：项目级薄适配、产品 DTO、局部中文错误、自动 scope、每请求生命周期；只改该新文件 | `runs/execution/mm_r7_slice_03_product_mount_implementation_20260828/worker_01.md` |
| `worker_02` | 实现 tests/test_medical_monitoring_r7_product_router.py：覆盖零导入写入、项目隔离、bootstrap、MTPLX、名称型 DeepSeek、scope、replay/conflict、中文错误与非 R7 错误不变；只改该新文件 | `runs/execution/mm_r7_slice_03_product_mount_implementation_20260828/worker_02.md` |
| `worker_03` | 完成 services/api/app/main.py 最小 import/include 接线并生成 Slice-03 离线 receipt/README 进度更新；不得触碰其他产品/前端/医写文件 | `runs/execution/mm_r7_slice_03_product_mount_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex will inspect all landed code, simplify speculative branches, run focused/full/adjacent tests and boundary hashes, then obtain an independent acceptance conference. No worker output is acceptance.
