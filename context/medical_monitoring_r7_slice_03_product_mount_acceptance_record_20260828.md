# R7 Slice-03 产品挂载受限验收记录

日期：2026-08-28

## 结论

R7 Slice-03 以“产品接缝、隔离离线、受限范围”通过 Codex 验收。

本结论只覆盖项目级产品路由、canonical 项目工作区、显式 bootstrap、ExecutionProfile 读写、Run 绑定/读取、MTPLX medium 默认与显式 DeepSeek V4 Flash max 配置能力，以及 `main.py` 的最小挂载。它不代表真实模型已调用、后台任务与进度恢复已完成、真实项目已运行、三种监查模式端到端通过、前端已接入或 R7 整体完成。

## 会商发现与纠偏

- 工作区就绪改为同时要求配置库与 Run 绑定库；非 bootstrap 路径不再补建缺失数据库。
- 项目层 scope 先经宿主 resolver 规范化，别名与 canonical URL 均落到同一项目工作区和配置层。
- R7 未知子路径和错误 method 由 router 局部返回中文 `{code,message}`；非 R7 错误合同不变。
- 产品边界不再转发 RunEntry 动态详情，只保留稳定错误码与中文文案。
- 回归直接检查临时 frozen profile，证明项目层确实生效，且名称型 DeepSeek 冻结为 `max`、无自动 fallback。

## 决定性证据

- 产品聚焦：15 passed；Grok 同会话独立复跑：15 passed。
- R7 全套：93 passed。
- 相邻 R6：763 passed。
- 相邻产品/principal/route-context：132 passed。
- 改动文件 Ruff、compileall：通过。
- 两席独立会商均为同 session 两轮且无 fallback；Grok 首轮发现经修订，续轮关闭；无剩余 P0-P2。
- 8911、5174 均无监听；医学写作边界为 542 文件，聚合 SHA256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 未启动服务、未调用真实模型、未运行真实项目、未修改前端或医学写作子系统。

## 已知边界

- `poc...mm_r7` namespace 是当前合同允许的过渡复用方式，正式分发打包后续处理。
- 本切不包含 Run 执行、队列、精确进度、继续/重试/取消、真实 harness 调用或浏览器交互。
- 完整 `main.py` Ruff 有并行医学写作区域既有告警，本切未越界修复；本切新增文件的 Ruff 已通过。

## 下一安全动作

进入 R7 下一纵切前先做 R7 阶段复盘并冻结合同。下一纵切优先建立后台 Run 生命周期与可恢复进度事实面，继续保持模型与真实项目关闭，直到离线状态机、幂等、恢复和产品中文投影受限验收通过。
