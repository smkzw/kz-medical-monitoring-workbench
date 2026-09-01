# Conference Context: lower_half_commercialization_rux_monitoring_20260708

Created: 2026-07-08 10:05:52
Objective: Resume AI medical manager workbench build toward commercial-ready product across all medical-related modules; decide and start the next implementation slice, prioritizing RUX-03-002 real-data medical monitoring rule/event layer while preserving full-module roadmap.
Task type: `complex_delivery_conference`
Risk: `critical`
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

- User-provided active objective in this Codex goal.
- `context/lower_half_commercialization_rux_monitoring_20260708_review_packet.md`
- `logs/SOFT_PAUSE_20260708_0958_CST.md`
- `logs/system_build_log.md`
- `frontend/AGENTS.md`
- `README.md`
- `context/rux_monitoring_source_precheck_20260708.md`
- Current backend/frontend/tests under `services/api/app`, `packages/contracts/workbench_contracts`, `tests`, and `frontend`.
- Original RUX source paths are authorized for Codex read-only inspection and summarized in the review packet. Hermes participants should not directly open large external original files unless Codex adds them to a role-specific read list.

## Scope

- In scope: all medical-related workbench modules already approved by the user: 项目总看板, 证据调研与方案设计, 入排审核, 医学监查, 数据分析与TFL, 医学写作, 安全信号与PV协同, 审批中心.
- Immediate decision scope: determine and start the next commercial-readiness implementation slice, with strong priority on RUX-03-002 real-data medical monitoring data dictionary / protocol rule set / normalized event layer.
- In scope for the conference: architecture critique, risk-benefit analysis, schema/test plan, sequencing with D001/TFL/writing/Safety/PV/approval, and frontend implications.
- Out of scope: building standalone non-medical lifecycle subsystems; editing original project folders; claiming formal medical/regulatory conclusions from advisory model output; treating prior Subject Timeline/Patient Profile HTML or skill-generated outputs as source truth.

## Success Criteria

- Participants independently evaluate the packet and current state without editing production code.
- Hermes sub-venue identifies consensus, disagreements, missing work, and whether reruns are needed.
- Main DeepSeek Pro review evaluates whether the recommended next build slice is safe, commercial-aligned, and testable.
- Codex can translate the accepted recommendation into a test-first implementation loop and persistent record.
- No recommendation violates user boundaries: source-first, no original-file mutation, independent AI runtime, no non-medical modules, no lifecycle-numbered UI labels, and Codex final authority.

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

- 2026-07-08 10:05:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 10:20 CST: Codex filled conference context with current workbench state, RUX source precheck, active module boundaries, and decision questions.
