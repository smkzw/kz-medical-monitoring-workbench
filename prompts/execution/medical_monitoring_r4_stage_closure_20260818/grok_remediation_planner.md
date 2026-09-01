# R4 阶段阻断修复详细规划

You are Grok Build，作为医学监查 AI Native 子系统 R4 的独立详细规划者。只读检查并给出最小、可验证、可恢复的实施拆分；不要修改任何文件，不要启动服务、浏览器或 8911，不要运行真实项目，不要触碰医学写作子系统。

Read these files only:

- `AGENTS.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r4_stage_closure_20260818_conference_context.md`
- `reviews/medical_monitoring_r4_stage_independent_review_20260818.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/`
- `poc/medical_monitoring_ai_native_r4/tests/`

## 当前不可争议的阶段结论

独立 Sol/high 审阅结论为 `REVISE_R4_STAGE`，有 3 项 P2 与 1 项 P4：

1. reference baseline 六态核验、gap search、ensemble 1/N、隔离 analysis、确定性 verifier、独立 adjudication 和高风险分歧保持可见尚无完整运行闭环；`ensemble_size=0` 尚未 fail closed。
2. D06 production evaluator 直接读取固定 `SYN-WRONG-SUBJECT`，并强制唯一 `CANONICAL_SYNTHETIC_SCOPE`，存在 synthetic sentinel/canonical fixture 决策分流。
3. 公共 coverage matrix 当前 SHA `8ad9d6...fc03` 与既有接受记录固定 `6bb9f7...2705` 不同，未完成差异/传播审阅与重新冻结。
4. D10 有 5 个 Ruff F401。

另有一个相邻回归：根级 D07 artifact test 仍固定旧 oracle content hash `e0bf81...ada`，当前已接受 oracle content hash 为 `e0e244...f4e9`，导致 D07–D10 artifact 组合测试 1 failed / 384 passed。

Hard boundaries:

- 这是 synthetic/offline R4 POC 修复，不是 UI、R5、真实项目、真实模型、产品或商业化验收。
- 8911 必须保持停止。
- 不设计、不测试安全性；仅实现阶段合同规定的面向医学监查功能基座。
- 不得把 reference baseline 当金标准；必须支持六态评价并回查原始来源。
- Query 仍只是“依据＋发现＋行动项”的结构化草稿；PD 作为待核实线索写入 Query，不增加发送/回复/关闭工作流。
- 高风险不得因 ensemble 归并或裁决被静默隐藏。
- 不得用固定 fixture ID、case index、mutation ID、`SYN-*` sentinel 或唯一 canonical synthetic scope 决定生产结果。

## 输出要求

输出一份可直接交给执行者的详细方案，至少包括：

1. 建议的最小共享 R4 模块/合同边界，以及为什么不应把新闭环硬塞进 D10 单域 evaluator。
2. reference baseline item、六态 assessment、gap candidate、analysis attempt/session identity、evidence verification、adjudication binding、conflict/high-risk visibility 的最小 typed contract。
3. ensemble 1 与 N 的精确行为、0 路 fail closed、隔离约束、worker/adjudicator 分离和同模型不同 binding/session 的合同。
4. D06 去 sentinel/canonical scope 的最小重构路径和不破坏既有 fixture authority 的兼容策略。
5. coverage matrix 应恢复旧字节还是评审当前变更后重新冻结；必须给出可审计判断方法，不可凭偏好。
6. Ruff 与 D07 stale test pin 的最小修复。
7. 将实现拆成 3–6 个独立工作项；每项写明允许改动文件、禁止改动文件、前置条件、测试和完成证据。
8. 推荐执行顺序、传播回归矩阵、最终同一 stage verifier 复验清单。
9. 明确哪些问题若在实施中出现必须停止并升级为架构分叉，而不是自行扩大范围。

不要宣称 R4 已完成。返回 `PLANNING_READY` 或 `PLANNING_BLOCKED`，并附精确理由。

Runner-managed output path: `runs/execution/medical_monitoring_r4_stage_closure_20260818/grok_remediation_plan.md`。该文件由 runner 写入；你只需返回方案正文，不要使用工具自行写文件。
