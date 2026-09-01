# Codex Execution Plan: medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809

Objective: 在隔离合成 POC 中实现 R1 AE/MH 受众看板，复用已验收数据合同，打通项目/中心/受试者风险、Profile/Timeline 共轴、证据与 Query 下钻，并完成真实浏览器与独立验收；不触碰医学写作、产品、真实项目或服务

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 构建只读 Slice1→window.MM_R1_DATA 投影生成器、合成来源索引与确定性合同测试 | `runs/execution/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/worker_01.md` |
| `worker_02` | 实现 file:// 可用的中文交互单页看板：变化优先项目/中心/风险视图、证据下钻、Profile/Timeline 共轴与 Query | `runs/execution/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/worker_02.md` |
| `worker_03` | 实现 Playwright 浏览器验收、无障碍/键盘/响应式/五项视觉 QC 验证及可复现截图证据 | `runs/execution/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `visual_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/manager.md` |

## Codex Acceptance

1. Confirm worker 01/02 changed only their declared disjoint files and integrate
   by regenerating `data/mm_r1_data.js` from the accepted synthetic core.
2. Run data-contract tests plus the entire accepted Slice 1 suite; compare the
   accepted source/test file hashes or current byte state and investigate any
   unexpected protected-path change without reverting concurrent user work.
3. Dispatch worker 03 only after the integrated `file://` app opens. Review its
   browser/QC output and request targeted same-session repair for actionable
   gaps; do not accept worker self-review as proof.
4. Dispatch the manager after all worker reports. The manager may perform only
   bounded remediation inside the authorized slice/output roots.
5. Codex reopens the actual `file://` runtime, inspects original-resolution
   screenshots, checks evidence/query/profile/timeline semantics, and reruns
   decisive tests in a fresh process.
6. Record clinical/visual/function residuals explicitly; pass the review gate,
   update R1 evidence/ADR only after acceptance, then archive execution records
   and move only task-created caches/temp files to a recoverable trash folder.

Stop conditions: any real-project access, medical-writing/product edit,
candidate-to-fact promotion, non-synthetic output, unresolved P0/P1/P2/P3/P4,
HTTP(S) runtime request, missing source locator, clipped text, or browser/QC
failure blocks Slice 3 acceptance.
