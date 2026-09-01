# Task Context: medical_monitoring_patient_journey_research_20260809

Created: 2026-08-09 17:22:36
Objective: 调研并定义医学监查受试者 Profile 与 Timeline 共享访视轴的交互式 Patient Journey 面板，融合风险标记、证据回跳、中文原生和离线本地约束，并将结论回写 System Design v1.1 与 R0-R8 实施计划；不得触碰医学写作、产品、真实项目、服务或共享运行库
Task type: `competitive_intelligence`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/`
- `subject-timeline-builder`、`clinical-patient-profile-html`、`ae-risk-assessment` 当前技能合同及既有视觉 QC 产物
- OHDSI ATLAS、Rho Clinical Timelines、clinDataReview/patientProfilesVis、SafetyGraphics、EventFlow、TrialView 的官方仓库、文档或论文（完整 URL 见调研报告）

## Scope

- In scope: 外部实现与研究比较；共享访视轴、同步视窗、泳道、风险标记、证据回跳、中文原生和离线本地契约；回写设计/计划；为新隔离 R1 切片定义验收门。
- Out of scope: 医学写作、产品源码、服务、8911、共享运行库、旧已验收切片、五个真实项目、真实项目规则或数据。

## Success Criteria

- 明确是否应形成交互式 Patient Journey 及其与 Profile/Timeline 的边界；
- 至少比较三类外部临床时间轴/安全监查方案并核实采用候选许可证；
- 形成可实现的共享访视轴、泳道、风险锚点、证据联动、增量和可访问性合同；
- 更新 System Design v1.1 与 R0-R8 实施计划，保持领域权威与投影解耦；
- 形成下一隔离 R1 最小切片及真实浏览器验收条件。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 17:22:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 17:28:34: 完成外部两轮扫描、许可证核验、本地 Slice 3 与既有 Profile/Timeline 视觉基座对照。
- 2026-08-09 17:28:34: 形成 `reviews/medical_monitoring_patient_journey_research_20260809.md`，并回写 System Design v1.1 与实施计划 v1.1。
- 2026-08-09 23:18 CST: 在 Slice 4 已通过后重新核查 clinDataReview、patientProfilesVis、
  TrialView、OHDSI ATLAS/Pathways、Medication Timeline、Health Timeline、LabVis、Tendril Plot、
  vis-timeline、Apache ECharts 与 Section 508/WCAG 色彩规则；依据用户纠偏重写前台术语、
  八域轨道、域内风险标记、语义缩放和视觉密度合同。明确禁止“正式事实”“候选信号”
  “只读xx”和 provider/model/attempt/backend 等研发词进入前台。
- 当前决策：保留已验证的原生 SVG/DOM Slice 4 作为合同基座；R5 规模基准后才决定是否
  引入 vis-timeline（Apache-2.0 OR MIT）或 Apache ECharts（Apache-2.0），不提前安装。
- 下一安全动作：实现只读中文 audience progress projection，随后在 R3/R4 扩展 PD/入排/
  禁用药、疗效/PRO/PK 等八域自适应轨道；不得修改产品、医学写作或启动 8911。
