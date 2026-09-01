# Conference Context: rux_p0_backend_review_20260708

Created: 2026-07-08 11:08:44
Objective: Review the current RUX-03-002 medical monitoring P0 backend implementation and the planned unified inbox integration before any further product-code changes. Identify concrete defects, conflicts, source-boundary issues, test gaps, and safe next changes. Do not edit files.
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

- `context/rux_p0_backend_review_20260708_review_packet.md`
- `records/rux_monitoring_profile_20260708/rux_p0_verification_gates_20260708.md`
- `logs/system_build_log.md`
- `logs/subsystems/medical_monitoring_log.md`
- `KNOWN_ISSUES.md`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/main.py`
- `services/api/app/workbench_inbox.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_rux_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `context/hermes_soul_working_copy.md`

Hermes participants should not read original RUX project folders directly in this advisory pass. Codex already performed the source precheck and recorded row/table anchors in the workbench packet.

## Scope

- In scope: static advisory review of the current RUX P0 backend implementation, source-locator contract, FastAPI dispatch, and planned RUX unified inbox integration.
- In scope: product/workflow terminology review for the next RUX inbox slice.
- Out of scope: file edits, tests, browser/visual acceptance, direct original-source parsing, clinical/regulatory final conclusions, and any frontend visual implementation.

## Success Criteria

- Hermes outputs identify concrete accepted/contested risks with file-backed evidence.
- Hermes separates current defects from deferred commercialization gaps.
- Hermes recommends a TDD next step for RUX inbox integration or explicitly blocks it with evidence.
- Codex can decide whether to land a small next patch without rediscovering context.

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

- 2026-07-08 11:08:44: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 11:10 CST: Codex added the real RUX P0 backend review packet, current code/test/log read list, and GLM-5.2 product-review lane.
