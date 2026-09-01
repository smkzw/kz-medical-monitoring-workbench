# Codex Execution Plan: mm_r7_slice07c4_ego_visual_execution_20260829

Objective: 在隔离 synthetic/offline 主机使用 ego(lite) 验收 R7 Slice-07C-4 中文产品闭环的 1280/1440/1920 桌面视觉与交互，不接触真实项目、真实模型或医学写作，并在结束后关闭所有测试监听。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 构建只读隔离 07C-4 HTTP fixture：服务 frontend/dist 与冻结公开 setup/history/progress/result-context 合成响应，补 fixture contract tests；不得修改产品源码。 | `runs/execution/mm_r7_slice07c4_ego_visual_execution_20260829/worker_01.md` |
| `worker_02` | 使用 ego(lite) 真实操作 1440 宽主流程：工作条、四步向导、历史、进度、发布结果、中心流向与 Journey/Profile/Timeline/证据跳转，记录截图与 DOM/网络证据。 | `runs/execution/mm_r7_slice07c4_ego_visual_execution_20260829/worker_02.md` |
| `worker_03` | 使用 ego(lite) 复核 1280/1920 布局、中文文案、焦点/溢出、公开 URL 身份和离页恢复，汇总缺陷分级与停止端口证据。 | `runs/execution/mm_r7_slice07c4_ego_visual_execution_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Fixture contract tests pass without protected ports or real data/model use.
- Ego(lite) evidence covers 1440 core flow plus 1280/1920 layout and interaction.
- Confirm workbar <= 56px, four-step Chinese wizard, history drawer, progress-to-result transition, single result identity strip, project/center flow board, Journey/Profile/Timeline/source navigation, URL/network public identity, visibility/leave-return behavior and page-level no-overflow.
- Codex reopens the screenshots and DOM/network evidence, classifies defects, performs any required product repair with focused regression, then reruns the affected ego scenarios.
- Final listener evidence shows 8911, 5174 and the isolated fixture port stopped.
