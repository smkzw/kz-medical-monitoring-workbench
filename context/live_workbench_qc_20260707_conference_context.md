# Conference Context: live_workbench_qc_20260707

Created: 2026-07-07 21:00:21
Objective: 四个指定 Hermes/OpenCode 模型实际访问康哲 AI 医学经理工作台本地前后端，执行独立前后端验收并写入报告
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Requested independent live validators:
  - Buddy provider `minimax-m3`.
  - Buddy provider `kimi-k2.7-code`.
  - OpenCode Go provider `mimo-v2.5`.
  - OpenCode Go provider `qwen3.7-plus`.
- Each validator must independently access the running local workbench, inspect frontend and backend behavior, and write a bounded report.
- This is live QA, not source editing. No validator may modify source files.

## Source Of Truth

- Running frontend: `http://127.0.0.1:5173/`
- Running backend: `http://127.0.0.1:8910/`
- Health endpoint: `http://127.0.0.1:8910/api/health`
- Project id: `proj_mgk10_sar_demo`
- Key pages: 项目总看板、入排审核、医学监查、Subject Timeline、Patient Profile、医学写作、审批中心。
- Key local source files validators may read:
  - `README.md`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/AGENTS.md`
  - `services/api/app/main.py`
  - `services/api/app/monitoring_intake.py`
  - `services/api/app/eligibility.py`
  - `services/api/app/enrollment_adapter.py`
  - `packages/contracts/workbench_contracts/models.py`
  - `tests/test_contracts.py`
  - `tests/test_eligibility_adapter.py`
- Key logs validators may read:
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/system_build_log.md`
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/project_overview_log.md`
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/eligibility_review_log.md`
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/medical_monitoring_log.md`
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/medical_writing_log.md`
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/approval_center_log.md`

## Scope

- In scope:
  - Verify backend health and core API responses.
  - Verify frontend pages are reachable and interactive.
  - Verify dense clinical UI behaviors: no obvious overflow, labels are clear, Subject Timeline shows high-density visit-axis lanes, Patient Profile shows graphical trends, writing editor is editable, eligibility page uses real rule IDs and phase/subject data.
  - Record concrete bugs, reproduction steps, page/API evidence, and recommended priority.
- Out of scope:
  - Source edits.
  - Production deployment.
  - Real clinical/regulatory conclusions.
  - Real OCR/LLM invocation.
  - Web search.

## Success Criteria

- Each validator writes exactly one report file under `runs/conference/live_workbench_qc_20260707/`.
- Each report states provider/model, whether the model could access the running frontend/backend, commands or browser actions performed, concrete findings, and prioritized recommendations.
- Findings must separate direct evidence from inference.
- A route failure is itself recorded as a report or stdout evidence; no silent substitution.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-07 21:00:21: Conference initialized by `hermes_workflow_guard.py init-conference`.
