# Conference Context: rux_monitoring_approval_gate_20260708

Created: 2026-07-08 18:49:05
Objective: Create a real Approval Center linkage for RUX medical monitoring submitted internal approval while preserving ledger state, source privacy, and bounded clinical wording
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

- `records/soft_pause_20260708_lossless_handoff/CURRENT_SLICE_RUX_APPROVAL_GATE.md`
- `logs/subsystems/medical_monitoring_log.md`
- `services/api/app/workbench_inbox.py`
- `services/api/app/demo_repository.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `tests/test_workbench_inbox.py`
- `tests/test_approval_center.py`
- `frontend/tests/rux_monitoring_inbox_qc.mjs`

## Scope

- In scope:
  - Create/link a real `ApprovalGate` when a RUX medical-monitoring risk disposition reaches `submitted_for_approval`.
  - Preserve RUX risk-ledger state and source-version integrity.
  - Ensure Approval Center copy says internal Query draft/disposition recommendation approval only.
  - Add backend, frontend, and browser QC coverage.
- Out of scope:
  - Query external/site send.
  - Risk closure, archival, or regulatory completion.
  - Full 192-subject RUX monitoring.
  - Electronic signature and production approval chain.

## Success Criteria

- After RUX `提交内部审批`, `GET /api/projects/proj_rux_03_002/dashboard` exposes a pending approval.
- Approval row/detail are clinically readable Chinese and do not expose raw technical ids, local paths, hashes, or source locators.
- Approve/return/reject mutate only the approval object/audit trail, not the RUX risk state or Query external-send state.
- Browser QC proves monitoring -> approval center linkage and no overclaim: no `已发中心`, `正式批准`, `自动关闭`, `可直接归档`, or risk-closed wording.
- Full focused tests, frontend build, and RUX browser QC pass.

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

- 2026-07-08 18:49:05: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 18:57 CST: User requested a lossless pause before this conference was dispatched. Codex subagents completed read-only backend/frontend/clinical-governance reviews; their findings were consolidated in `records/soft_pause_20260708_lossless_handoff/CURRENT_SLICE_RUX_APPROVAL_GATE.md`. No Hermes participant prompts were run for this conference before pause.
