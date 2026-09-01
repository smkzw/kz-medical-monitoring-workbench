# R4-D09 Worker02 projection 验收记录（2026-08-16）

## 结论

`ACCEPT_D09_WORKER02_PROJECTION`

D09 renderer-neutral audience projection、中心模式风险、分层计数、热点、
一跳来源、自然中文三分句 Query 草稿与 R2 handoff 已完成 synthetic/offline
实现和独立复核。Worker03 现可按串行计划解锁。

## 接受快照 SHA-256

- contract: `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- `d09_contracts.py`: `42fdda3b36e08e77810847f8dcea4cd13572c3d1a6f08eaea80a7eca0c14765f`
- `d09_evaluator.py`: `0b4aa08a51b84d0020133313ad30a886bcebdde67846d0efc639852e90c06743`
- `d09_projection.py`: `ee38df95707b43bffed010aa032171f12aa2277ce7627f964e1ef1ef23d88084`
- `test_d09_projection.py`: `44418ddc5094f28d3c4dfcc73b541cbf8818b4711be96a762c5edf6f70f90cf8`

## 决定性证据

- Codex 六组 D09/D08 相邻回归：`265 passed`；Ruff clean；AST compile OK。
- 独立 Luna/max verifier：focused `94 passed`；其扩展 D09/D08 集合
  `400 passed, 13 subtests`；首尾 SHA 稳定；最终 verdict 为
  `ACCEPT_D09_WORKER02_PROJECTION`。
- 65 条 Query 中只有两个精确 `pd_unreported + verify_pd` 用例包含
  “请核实是否为 PD”；其余 63 条不包含。
- 全隐藏与部分隐藏均只投影受众可见计数；全隐藏 positive 不形成受众
  payload、风险、热点、链路或 Query。
- Query 证据非空、完整、可定位并绑定 hash；locator/evidence 联合篡改失败。
- risk/gap/trend 缺失锚点均显示“来源暂无法定位”，不构造跳转。
- R2 handoff 对 prior/public/lineage/成员/计量/完整性/优先级/不自动关闭
  字段及 handoff/idempotency 联合伪造均 fail closed。
- source revision 输入顺序不改变 Query draft identity。
- TCP 8911 全程停止；未运行真实项目、真实模型或产品服务。

## 执行与审阅轨迹

- Worker02 初始及两次同会话纠偏：Pi/OpenCode Go
  `deepseek-v4-flash:max`，session `01a00649-e4d8-7000-b04b-ed28ef6082f9`，
  无 fallback。
- 末轮三个阻断由 Codex 在同一两文件边界内做最小修复并验证。
- 独立 verifier：Codex native `gpt-5.6-luna:max`，任务
  `/root/d09_artifact_freeze_review`，同一审阅会话逐轮复现、否决、复验。
- 最终审阅报告：
  `runs/review/medical_monitoring_r4_d09_worker02_projection_luna_followup3_20260816.md`。
- Runner 原 `worker_02.md` 只保存初始快照；本记录与 follow-up stdout/review
  是纠偏后权威证据，不把旧 runner 报告误称为当前状态。

## 边界与下一动作

本 ACCEPT 只覆盖 D09 Worker02 synthetic/offline projection，不接受
Worker03、D09 runtime 总体、D10、R5/UI、真实项目/模型、产品、生产或医学写作。
下一安全动作是 Worker03：仅补 D09 public exports、mutation/anti-overfit/
replay/closure tests，并运行 focused/adjacent/full regression；仍保持 8911 停止。
