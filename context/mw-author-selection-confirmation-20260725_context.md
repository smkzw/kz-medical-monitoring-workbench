# Task Context: mw-author-selection-confirmation-20260725

Created: 2026-07-25 02:45:51
Objective: 统一医学写作主路径为作者选择或确认即完成项目层面确认，取消重复医学批准，同时保留来源、质量门、版本审计与历史状态兼容
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 用户要求：系统用户即医学经理；用户主动选择、采用、修订后采用或确认的内容即已完成项目层面确认，不再进入第二层“待医学批准”。
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/evidence_picos_workflow.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx`
- `frontend/src/features/writing-reference/`
- `frontend/src/App.jsx`
- `packages/contracts/workbench_contracts/models.py`
- 与上述路径直接对应的`tests/`合同、持久化、API与前端回归。

## Scope

- In scope:
  - 医学写作authoring/PICOS/章节候选/翻译语料准入主路径。
  - AI候选到作者选择/确认后的状态迁移、按钮文案、可继续动作和审计记录。
  - 旧`pending_medical_approval`、`accepted_pending_medical_approval`数据的只读兼容和迁移显示。
  - 来源、版本或研究定义变化后的失效/重新确认，不得伪装为永久批准。
  - 翻译事实忠实度门、文档类型/适应症基本校验、作者override、来源定位和版本审计继续保留。
- Out of scope:
  - 医学监查Query等确实需要公司内部审批的工作流。
  - 电子签名、医学总监独立复核、监管提交锁定。
  - 直接编辑稳定运行库或重启5174/8911。
  - 删除历史审计记录或破坏旧状态反序列化。

## Success Criteria

- 选用AI章节候选后可直接写入版本化工作副本，不再要求第二次医学批准。
- PICOS中作者选择并明确理由/确认后，可形成版本化写作交接快照；不再提交到审批中心。
- 翻译经事实忠实度检查并由作者确认后，可直接进入语料准入；不再出现“确认后仍待医学批准”。
- 当前主路径UI不再显示“待医学批准/提交医学批准/批准当前内容”等重复动作。
- 历史状态仍可读取，显示为历史候选/待迁移或等价兼容语义，不能误写成当前新增审批。
- 现有来源、质量、版本、幂等、冲突、失效和审计门保持或加强。
- 聚焦后端、前端合同和相邻回归通过；不得以修改测试规避真实状态机问题。

## Risk Boundaries

- 不直接写运行时SQLite；使用正式服务/迁移兼容。
- 不把“作者确认”误等同于电子签名、最终监管提交批准或跨角色公司审批。
- 不删除质量门；仅移除同一医学作者已经确认后的重复批准。
- 写范围限于上述源码、测试、review和本任务记录。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 02:45:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25 02:47: 主会场完成状态残留盘点；确认问题横跨PICOS、章节候选、翻译准入与旧审批中心，必须做状态迁移而非标签替换。
