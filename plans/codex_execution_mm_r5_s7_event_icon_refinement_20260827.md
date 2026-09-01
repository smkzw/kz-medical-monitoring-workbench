# Codex Execution Plan: mm_r5_s7_event_icon_refinement_20260827

Objective: 将R5 Patient Journey八类事件的丑陋文字形状标签纠偏为统一、可辨识、中文原生且适合高密度时间轴的图标体系，并完成测试、构建与浏览器视觉验收，不触碰医学写作。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 只读审查现有八域事件标签、尺寸、无障碍与高密度时间轴约束，给出最小图标映射和验收点，不修改文件。 | `runs/execution/mm_r5_s7_event_icon_refinement_20260827/worker_01.md` |
| `worker_02` | 基于项目既有lucide-react实现统一DomainIcon组件，替换事件图例、泳道头、时间轴事件、风险徽标和事件行中的文字形状标签；保留语义和风险等级。 | `runs/execution/mm_r5_s7_event_icon_refinement_20260827/worker_02.md` |
| `worker_03` | 对实现进行独立代码与视觉合同审阅，检查八域辨识度、中文标签、紧凑/标准/详细缩放、风险叠加、无障碍和医学写作边界。 | `runs/execution/mm_r5_s7_event_icon_refinement_20260827/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Accepted after Codex source review, 7/7 focused Node tests, production build, 1600×1000 normal/density browser checks, and same-session independent visual review. Final icon mapping is `ShieldAlert / BookOpenText / Pill / Syringe / TestTube2 / Hospital / TrendingUp / ClipboardCheck`.
