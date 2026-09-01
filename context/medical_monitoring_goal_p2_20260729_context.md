# Task Context: medical_monitoring_goal_p2_20260729

Created: 2026-07-29 01:56:24
Objective: 建立医学监查项目中立的来源登记、不可变业务批次、完整性确认与真实全量listing结构/行/字段/医学语义差异链，使用真实连续项目文件验证且不触碰医学写作独占文件
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `医学监查子系统_分阶段实施与LOOP计划.md` P2。
- P0 `REAL_PROJECT_TEST_MATRIX.md`、`INTERFACE_AND_OWNERSHIP_MATRIX.md`。
- 当前 `monitoring_raw_intake.py`、`monitoring_batch_diff.py`、
  `project_source_manifest.py`、`medical_risk_repository.py` 及其真实项目测试。
- 原始项目文件本身；派生 Timeline/Profile/风险/TFL/人工 comparison 不作为输入。

## Scope

- In scope: 来源内容寻址、不可变批次、状态机、完整性/映射确认、结构/行/字段
  diff、幂等并发、真实连续批次和最小 API/前端摘要。
- Out of scope: P3 方案事实与规则编排、P4 AI 医学判断、P5 风险工作台重构。

## Success Criteria

- 至少一个真实项目两份完整全量 listing 无人工预处理完成批次链与逐字段差异。
- 每条差异回到旧/新原始值、文件、工作表和行定位。
- 相同内容重传幂等；同键不同内容冲突；冻结批次不可改。
- 缺失域、关键键缺失或来源不完整时不生成虚假的删除/解决。
- 结构漂移和单位/参考范围变化明确呈现。
- 医学写作冻结文件保持不变。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 01:56:24: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 外部发现：lakeFS/DVC 的不可变提交与内容寻址适合借鉴但部署过重；DuckDB/Polars
  许可和能力合格，但当前无依赖且规模可由 SQLite 承担。先使用 Python 标准库 +
  SQLite；只有性能基准失败才重新开工具决策。
- 2026-07-29：完成真实来源资格审阅。当前不存在一对可证明为原始全量连续快照
  的本地文件；RUX/MY009 连续候选仅作非门禁回归，PNH/RUX 原始包作单批泛化。
- 2026-07-29：完成物理行溯源、RUX 错误 dimension 恢复、跨 EDC 分层业务键、
  字段级 diff、来源分类和批次仓储核心。Codex 对委派仓储只审冲突/风险并修复：
  来源 locator 不参与语义指纹，diff 仅允许 frozen 批次。
- 2026-07-29：批次来源事实改为固定共享来源权威的 entry/validation revision，
  不允许批次库或医学 override 重新定义来源内容校验结果。
