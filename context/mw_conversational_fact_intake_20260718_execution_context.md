# Execution Context: mw_conversational_fact_intake_20260718

Created: 2026-07-19 00:23:59
Objective: 在医学写作子系统中实现IB可选的最小产品事实包与通用对话式事实采集：DeepSeek-v4-pro拆解用户自然语言，用户确认后写入版本化事实，缺少IB不阻断调研和写作，仅局部阻断依赖缺失事实的确定性条款。
Task type: `complex_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- User decisions and detailed acceptance direction:
  - `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`
  - `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/CODEX_DECISION_AND_IMPLEMENTATION_CONTRACT.md`
- Current contracts and authoring state machine:
  - `packages/contracts/workbench_contracts/models.py`
  - `packages/contracts/workbench_contracts/__init__.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/main.py`
- Current desktop interaction:
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - `frontend/src/styles.css`
- Existing tests:
  - `tests/test_medical_writing_authoring_journey.py`
  - `tests/test_user_project_authoring_bootstrap.py`
  - `frontend/tests/medical_writing_authoring_journey.spec.mjs`

## Required Behavior

- Project creation remains exactly three required facts: investigational product,
  indication and study phase. IB is optional and absence is a normal state, not
  a warning, blocker or approval task.
- DeepSeek V4 Pro is the independent runtime AI for natural-language fact
  decomposition. It must never be replaced by the coding/conference model.
- The AI may propose only allowlisted structured field paths. It must separate
  user-stated facts, AI inference, unknowns, conflicts and high-impact missing
  facts. It must not invent exact dose, escalation step, interval, exposure
  margin, threshold or monitoring window.
- Ask at most three current-turn questions, ordered by downstream impact.
  Unknown/not available/later is a valid answer.
- Preserve every user message, AI response, proposal, user adoption/edit/
  rejection, source/version and idempotency identity. A medical manager's
  explicit adoption is final project-level confirmation; no second
  "pending medical approval".
- The same conversation mechanism must support later scopes such as study
  framing and PICOS, not be hard-coded only to IB.
- Missing facts may locally block a deterministic clause that depends on them,
  but may not block competitor research, corpus preparation or unrelated
  chapter candidates.

## Success Criteria

- Old persisted authoring journeys remain readable.
- Backend has typed contracts, separate durable conversation state, optimistic
  revision checks and idempotent turn/apply operations.
- Production provider prompt is schema-bound and field-path allowlisted.
- Desktop UI presents "可选：研究者手册" and "暂未形成/稍后补充" without
  warning styling, plus a natural-language conversation area and confirm/edit/
  reject controls for extracted facts.
- No duplicate required fields after the initial three facts.
- Unit/API tests cover no-IB, repeated idempotency, stale revision, forbidden
  field path, unknown answer, and confirmed fact application.
- Browser test uses a clean project and verifies no "待医学批准" after the user
  adopts a suggestion.

## Risk Boundaries

- No stable runtime writes and no changes to the running 5174/8911 data.
- Worker 01 may edit only:
  - `packages/contracts/workbench_contracts/models.py`
  - `packages/contracts/workbench_contracts/__init__.py`
  - a new narrowly named service under `services/api/app/`
  - `services/api/app/main.py`
  - new or directly relevant Python tests under `tests/`
- Worker 02 may edit only:
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - `frontend/src/styles.css`
  - directly relevant frontend tests.
- Worker 03 is review/test only until worker 01 and 02 complete; it may create a
  new isolated QA test/report but must not modify production source.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Execution Order And Timeout

- Worker 01 and Worker 02 may run in parallel because their primary write sets
  do not overlap.
- Worker 03 starts only after both implementations are available.
- Manager starts only after all three worker reports exist.
- Hard wait per pass: 7200 seconds. Slow output remains pending; do not restart
  a healthy same-session run merely because it is slow.

## Work Items

1. 后端合同、独立AI提示词、持久化会话和幂等API
2. 桌面端无IB最小输入与对话式确认交互，移除重复必填
3. 多项目单元/API/浏览器测试与待医学批准语义审计

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
