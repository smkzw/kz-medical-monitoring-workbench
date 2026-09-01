# Codex Execution Plan: mm_r7_slice07c4_user_product_loop_implementation_20260829

Objective: 实现已冻结的 R7 Slice-07C-4 synthetic/offline 中文产品闭环；按后端公开身份桥、前端纯数据层、前端组件接线顺序完成，保护医学写作，不启动服务/真实项目/模型。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端公开身份桥：在 launch_registry additive 持久化不可重铸 result_context_token，增加一 in-flight 门禁、八字段历史 status_text、public_run_token progress 和三个 result-context R5 projection GET；复用既有 R5 provider/assembler，补 product/R7/R5 tests。 | `runs/execution/mm_r7_slice07c4_user_product_loop_implementation_20260829/worker_01.md` |
| `worker_02` | 前端纯数据层：新增 07C-4 setup/history/public progress/result-context API、公开 envelope 验证、selected-run/向导/idempotency/离页恢复纯状态投影及 Node tests；不得修改现有 internal R5 validateEnvelope，不碰 JSX/CSS。 | `runs/execution/mm_r7_slice07c4_user_product_loop_implementation_20260829/worker_02.md` |
| `worker_03` | 前端产品接线：在 R5 项目页实现紧凑本次监查工作条、四步中文向导、历史抽屉、selected-run progress/result 切换、公开结果看板/Journey 路由与非叠加身份条，补 render tests/CSS；只消费已实现的 API/纯状态模块，不用 fixture 冒充发布结果。 | `runs/execution/mm_r7_slice07c4_user_product_loop_implementation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Review each worker diff against the exact allowed paths and frozen v0.2 contract.
- Run focused product/R7/R5 Python tests, all medical-monitoring Node/render tests, Vite build and compileall.
- Confirm no internal run/authority/receipt/S4/R5 identities enter public browser route/envelope.
- Confirm no static fixture is accepted as a publication and 07C-3 available rows remain immutable.
- After implementation audit, initialize a separate visual conference and run ego(lite) at 1280/1440/1920 with
  8911 only in the isolated test lifecycle; stop it before acceptance.
