# Task Context: medical_monitoring_r5_s3_20260818

Created: 2026-08-18 22:58:20
Objective: 冻结并实现R5-S3项目驾驶舱与中心图谱离线只读投影，严格引用R4 D09/D10权威，验证计数层守恒、分子分母成员、hidden不泄露、中心稳定排序与无排名字段；不触碰前端、8911、真实项目、医学写作或R4源码
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- `context/medical_monitoring_r5_contract_acceptance_record_20260818.md`
- `context/medical_monitoring_r5_s2_acceptance_record_20260818.md`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/**`（当前 R5 typed contract、S1 adapter、已接受 S2）
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_*`、`d10_*`（只读 public/typed authority）
- 当前文件系统是唯一当前事实；历史记录只作为定位索引。

## Scope

- In scope: 先冻结 S3 实施合同，再在 `poc/medical_monitoring_ai_native_r5/**` 内实现 renderer-neutral 的项目驾驶舱、当前风险集、变化带、分层定量度量与中心图谱；完成 focused、R5 全量、R4 相邻/全量门禁和独立验收。
- Out of scope: 前端/浏览器/S7、8911、真实项目资料、真实模型、产品或生产、医学写作子系统、R4 源码修改、安全专项、S4 Inspector 完整化、S5 Subject Workspace 完整化。
- Read-only imports: R4 D09/D10 public/typed objects and the accepted R5 S1/S2 surfaces.
- Writable allowlist: `poc/medical_monitoring_ai_native_r5/**`、本任务 `context/**`、`reviews/**`、`metrics/**`、`prompts/**`、`runs/**`、任务证据/归档。

## Success Criteria

- 每个 S3 audience leaf 可追到 exact R4/S2 authority unit 或具名 synthetic supplemental authority；旧 receipt/identity/hash 漂移 fail-closed。
- `R5CurrentRiskSet`：所有可见当前 high/medium risk identity 全量保留；low 仅聚合展示但 cluster 可展开至全部成员；resolved 不混入 current。
- `R5ChangeBand`：直接适配 D10 closed change kind/cause；首次全量不伪造新增/关闭；不可比较不写成临床改善/恶化。
- `R5QuantitativeMeasure`：分层引用 R4 count surface 和 typed numerator/denominator members，不在 R5 重算医学数值；zero/unknown/unclosed、coverage/cutoff/evaluation limits 均显式。
- `R5CenterMapProjection`：pattern 与 individual 两层不混淆；hidden member/site 零泄漏；stable site id 排序；无 score/rank/top-N/惩罚性序号字段。
- 计数层分别守恒（risk/query/clue/pattern/subject/site/signal 不相加），分子/分母成员可机械重建。
- focused、R5 全量与 R4 相邻/全量回归、R4 SHA 只读门、Ruff/compile 均通过；fresh reviewer 返回 `ACCEPT_R5_S3`。
- 8911 始终停止。

## Risk Boundaries

- 不得按 project/case/fixture/test id、文件名、synthetic sentinel、mutation class、index 或 hash 命名约定决定语义。
- 不得从 UI 行数或既有 R5 输出反推 R4 数值；不得将 hidden/unknown 当 0；不得把单个个体风险升级成中心模式。
- 不得修改 R4、前端或医学写作路径；不得启动服务或读取真实项目。
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-18 22:58:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-18 23:00: 已从 `ACCEPT_R5_S2` 重新锚定；确认 R4 D10 可直接提供 count surface、denominator/member refs、change section、center distribution，但完整多中心/current-risk 语义需在 S3 以多 authority-unit＋具名 synthetic supplemental authority 冻结，不能伪称现成 R4 public leaf。
