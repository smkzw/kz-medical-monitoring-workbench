# Conference Context: medical_workbench_lower_half_gap_baseline_20260708

Created: 2026-07-08 16:26:46
Objective: Audit the AI Medical Manager Workbench lower-half commercialization baseline, verify subsystem gaps against current code/logs/real-data evidence and recommend the next implementable product slice with risk/benefit record.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- Current synthesis packet:
  - `records/commercialization_audit_20260708/medical_workbench_current_state_and_gap_baseline.md`
  - `records/commercialization_audit_20260708/subagent_backend_api_audit.md`
  - `records/commercialization_audit_20260708/subagent_frontend_interaction_audit.md`
  - `records/commercialization_audit_20260708/subagent_records_closure_audit.md`
- Project operating instructions and scope guards:
  - `README.md`
  - `frontend/AGENTS.md`
  - `KNOWN_ISSUES.md`
- Logs and handoff records:
  - `logs/system_build_log.md`
  - `logs/subsystems/project_dashboard_log.md`
  - `logs/subsystems/medical_monitoring_log.md`
  - `logs/subsystems/medical_writing_log.md`
  - `logs/subsystems/data_analysis_tfl_log.md`
  - `logs/subsystems/safety_pv_log.md`
  - `logs/subsystems/module_scope_log.md`
- Key backend surfaces:
  - `services/api/app/main.py`
  - `services/api/app/ai_gateway.py`
  - `services/api/app/ai_task_runner.py`
  - `services/api/app/workbench_inbox.py`
  - `services/api/app/enrollment_adapter.py`
  - `services/api/app/evidence_design_manifest.py`
  - `services/api/app/evidence_picos_workflow.py`
  - `services/api/app/rux_monitoring_service.py`
  - `services/api/app/tfl_manifest.py`
  - `services/api/app/tfl_review_workbench.py`
  - `services/api/app/tfl_writing_handoff.py`
  - `services/api/app/medical_writing_manifest.py`
  - `services/api/app/medical_writing.py`
  - `services/api/app/safety_pv_manifest.py`
  - `services/api/app/safety_pv_review_workbench.py`
  - `services/api/app/demo_repository.py`
- Key frontend/QC surfaces:
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/overview_ai_gateway_qc.mjs`
  - `frontend/tests/medical_writing_manifest_qc.mjs`
  - `frontend/tests/rux_monitoring_inbox_qc.mjs`
  - `frontend/tests/rux_three_subject_drilldown_qc.mjs`
  - `frontend/tests/subject_timeline_ip_lane_qc.mjs`
  - `frontend/tests/tfl_manifest_qc.mjs`
  - `frontend/tests/safety_pv_manifest_qc.mjs`
- Conference/review metrics to consider for closure boundaries:
  - `metrics/medical_writing_revision_ui_20260708_conference_metrics.md`
  - `metrics/rux_monitoring_inbox_detail_20260708_conference_metrics.md`
  - `metrics/full_medical_workbench_commercialization_20260708_conference_metrics.md`
  - `metrics/safety_pv_review_workbench_20260708_conference_metrics.md`
  - `metrics/source_registry_frontend_boundary_review_20260708_conference_metrics.md`
- External evidence already captured in the baseline file only:
  - Medidata Clinical Data Studio official page title/description captured by Codex.
  - Clinical ink official page title/description captured by Codex.
  - Docuvera official page title/description captured by Codex.
  - CDISC DDF/CORE, COSMoS, pharmaverse/admiral/teal page titles captured by Codex.
- Do not read or modify original real-project folders for this review. The user has authorized reading original project files generally, but this conference is intentionally bounded to the workbench source packet above.

## Scope

- In scope:
  - Audit whether the current lower-half commercialization baseline is faithful to the workbench code/log/QC evidence.
  - Compare three candidate next slices:
    1. 医学写作独立AI Gateway最小闭环.
    2. RUX医学监查真实风险处置闭环.
    3. TFL真实数据审阅 -> 独立AI解释 -> 医学写作引用候选 -> 审批阻断.
  - Produce benefit/risk/verification analysis for each candidate.
  - Recommend one next implementable slice, with explicit fallback if provider/config blockers appear.
  - Identify records that must be cleaned before or during the next implementation loop.
- Out of scope:
  - Editing production code.
  - Running tests, browser QC, OCR/VLM, web browsing, or visual acceptance.
  - Treating any slice as full commercial completion.
  - Claiming final clinical/regulatory/PV/statistical conclusions.
  - Creating new non-medical lifecycle subsystems.

## Success Criteria

- Each participant writes exactly one output file under `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/`.
- Participant outputs separate evidence, inference, recommendation, and uncertainty.
- Hermes lead compares all available participant outputs, records unresolved conflicts, and recommends whether to rerun, ask the user, or implement a next slice.
- Main DeepSeek Pro review checks whether the recommendation is defensible and what Codex must verify before code landing.
- Codex can use the package to select a next implementation slice without losing user constraints:
  - independent AI capability must be product runtime, not Codex;
  - real project files must be parsed from source where claimed;
  - all AI outputs remain pending medical approval;
  - desktop-first UI;
  - no first/fourth/fifth non-medical subsystems;
  - no local-path leaks;
  - no overclaiming formal regulatory/PV/statistical outputs.

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

- 2026-07-08 16:26:46: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08: Codex added the current-state baseline, three read-only SubAgent audits, source packet, scope, and success criteria before dispatch.
