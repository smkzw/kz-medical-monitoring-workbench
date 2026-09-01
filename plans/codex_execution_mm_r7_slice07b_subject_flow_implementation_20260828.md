# Codex Execution Plan: mm_r7_slice07b_subject_flow_implementation_20260828

Objective: 按已冻结的 v0.2 + v0.3 §9 合同实现 R7 Slice-07B synthetic 项目/中心受试者阶段流向看板。严格不运行真实项目、不启动 8911、不修改医学写作。实现后由 Codex 运行回归与 ego(lite) 验收。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端：在 R5 authority packet 中加入兼容旧 schema 的 typed flow stage/path records，构建守恒 subject_flow overview 投影、三态、中心范围和 Journey 跳转窗口；补充后端确定性测试。只改 services/api/app 下 R5 adapter/router 及其测试。 | `runs/execution/mm_r7_slice07b_subject_flow_implementation_20260828/worker_01.md` |
| `worker_02` | 前端数据与路由：严格规范化 subject_flow 三种形态，加入互斥 flow route keys、Journey 往返保留和 adapter/route tests。只改 frontend/src/features/medical-monitoring/r5 的 adapter、route-state 和对应测试，不改页面/CSS。 | `runs/execution/mm_r7_slice07b_subject_flow_implementation_20260828/worker_02.md` |
| `worker_03` | 前端视觉：在现有 R5 OverviewView 中实现全宽横向 SVG 受试者阶段流向、current/reached/link 筛选、风险摘要、折叠明细表、空态/阻断态、键盘隔离与中文 CSS；补充组件/合同测试。只改 R5 Page/CSS/fixtures/render tests，不启动服务或浏览器。 | `runs/execution/mm_r7_slice07b_subject_flow_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex 将逐文件复核三名 worker 改动，先运行聚焦测试再运行 R5/R7 与前端全量回归；只在
deterministic 门禁通过后启动隔离 synthetic fixture，并使用 ego(lite) 做 1280/1440/1920、
项目/中心/未提供/阻断、筛选、键盘和 Journey 往返验收。8911 与真实项目始终不启动。
