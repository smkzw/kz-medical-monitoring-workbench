# Task Context: mw_ai_first_candidate_packages_20260724

Created: 2026-07-24 19:29:44
Objective: 扩展医学写作AuthoringPrefillPackage为AI-first组合候选设计包，覆盖证据支持的完整PICOS和原子采纳，并形成不重叠实施计划与医学/产品验收门
Task type: `complex_delivery_conference`
Risk: `high`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `reviews/medical_writing_ai_first_lazy_writer_gap_audit_20260724.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_design_projection.py`
- `services/api/app/medical_writing_protocol_assembly_plan.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`
- 已冻结并接受：动态设计 Slice A/B/C；竞品分诊最终分类原子确认。

## Scope

- In scope：扩展既有`AuthoringPrefillPackage`，支持field/module/design_package/table/
  chapter候选；完整PICOS；组合候选原子采纳；产品独立AI提示/结构化响应/证据门；前端
  “推荐先行、用户改/选/确认”主路径；确定性与真实独立AI验收。
- Out of scope：工程安全、后门、漏洞审计；修改已冻结动态设计语义；开发Agent替代产品
  独立AI；未确认精确事实直接写入正式StudyDefinition；本轮首轮计划阶段修改生产源码。

## Success Criteria

- 三个最小事实后，其余主链业务控件均有确定性默认、产品AI推荐、3–5个实质候选或有解释
  的待决定卡，不以空白文本框/空列表/空表格作为主路径。
- 精确剂量、阈值、终点、样本量、时间窗、AESI和洗脱期只在绑定已登记来源时形成候选，
  无证据时保留结构化缺口而非伪事实。
- 组合候选采纳原子更新所有目标路径、候选状态、journey revision和审计记录；故障注入无
  半写；幂等重放和同key冲突可验证。
- 产品运行时AI固定为独立`deepseek/deepseek-v4-pro`，不依赖Codex/Qoder/Hermes。
- 最终由至少三个非肿瘤适应症、从零与摘要导入、I期与III期复杂设计、真实浏览器和DOCX
  验收证明。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 不进行工程安全/后门/漏洞工作。
- 不把已冻结的`NormalizedDesignProjection`重新拆成并行事实源。
- 不改动或确认D017 v1分诊结果；后续v2必须使用产品独立AI重新运行。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 19:29:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-24 19:34:00: Codex补全来源、范围、成功标准与风险边界；首轮执行经理只读分解。
- 2026-07-24 20:19:05: 干净D017从零项目真实浏览器采用英文疾病词后，工作台自动创建
  `wref_search_35f39994abfb89587948`；67/67候选具有Brief Summary、干预和入组数，
  66/67具有随机、干预模型和盲法。检索后产品AI候选仍出现英文中国方案标题及无直接证据
  的成人PNH人群，故不得批量采用；本轮实现必须增加中国方案语言门、事实/设计候选边界和
  真实产品AI质量回归。
- 2026-07-24 20:11:00: 用户将Qoder替换边界更新为2026-07-25 01:00 Asia/Shanghai。
  此前不使用Qoder/qwen3.8-max-preview；原Hermes/aishuo/cms-model角色保持Hermes，
  Grok Build/grok-4.5仍按原执行经理路由使用。切换点只作用于新任务和续作。
- 2026-07-24 20:25:00: 真实浏览器确认检索结果已在建项第一步出现，但
  `WritingReferencePanel`仅由第三步语料准备组件渲染，第一步没有直接进入AI分诊/审核的
  产品入口。为继续v3科学质量测试，Codex只通过同一正式202 API启动产品作业；该操作不
  等于UI闭环通过。第一切片需增加检索完成后的独立竞品处理入口/抽屉，不把分诊常驻编辑器，
  也不要求用户先手工补完大量框架和PICOS才能处理已发现的竞品。
