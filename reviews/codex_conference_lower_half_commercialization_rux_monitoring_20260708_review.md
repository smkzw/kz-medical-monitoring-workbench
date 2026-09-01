# Codex Conference Review: lower_half_commercialization_rux_monitoring_20260708

Date: 2026-07-08 10:32 CST

## Verdict

Status after main-venue DeepSeek Pro: advisory review complete, not ready for code landing.

Codex has not accepted any product-code changes from this conference. The accepted use of the conference output is advisory planning only: backend-first RUX medical monitoring data dictionary / protocol rule / normalized subject event layer is the convergent next implementation direction, with small frontend honesty/QC fixes as a possible later parallel non-contract-breaking patch after Codex confirms the exact scope.

## Boundary Compliance

- Original RUX, D001, and other project source folders remain read-only.
- Product source code was not modified in this review loop.
- New/updated files are conference records, route notes, compact prompt, logs, and this review/metrics material inside the workbench workspace.
- Kimi first full-context failure is recorded as a route/size incident, not a product finding. Compact Kimi retry succeeded and is used as the valid frontend Buddy participant output.
- Codex remains final authority for browser/visual QC, source-boundary decisions, production writes, and clinical/regulatory conclusions.

## Participant Outputs Reviewed

Completed participant outputs:

- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_qwen_plus.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_mimo.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_ds_flash.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_glm52_product.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry.md`

Supporting subagent reports:

- `runs/subagents/module_maturity_audit_current_20260708.md`
- `runs/subagents/monitoring_frontend_interaction_audit_20260708.md`
- `runs/subagents/rux_monitoring_rule_layer_review_20260708.md`

## Hermes Sub-Venue Review

Completed at:

- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/hermes_lead.md`

Hermes chair conclusion:

- No reruns required.
- All five valid participants and three subagents converge on a backend-first RUX medical monitoring slice.
- The next implementation should start from original RUX listing/protocol through a data dictionary, protocol rule set, normalized subject event layer, and deterministic rule engine.
- RUX-data-coupled frontend changes should wait for backend contracts/data.
- Small frontend honesty/QC fixes can run in parallel if Codex accepts them: demo/fallback labeling, disabling non-persistent action controls, precise clinical Chinese labels, upload-gate truthfulness, read/unread semantics, and QC assertions.

## Main-Venue DeepSeek Pro Review

Completed at:

- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/main_deepseek_pro.md`

DeepSeek Pro main-venue critique:

- Accepts the backend-first RUX direction, but treats it as conditional on Codex-only source verification and TDD.
- Confirms the current `monitoring_intake.py`/demo path must not be patched into a fake RUX rule engine.
- Identifies `sheet_name == "LB"` style assumptions as a likely correctness defect for RUX `LBHEMA`/`LBCHEM` sheets, pending direct Codex code verification.
- Requires a contract decision for `source_locator` before tests are written, because Subject Timeline, Patient Profile, TFL, Safety/PV, and Writing may all consume the event layer.
- Reclassifies prohibited concomitant medication review as AI-primary with protocol-sourced deterministic overrides, not keyword-only or deterministic-primary matching.
- Flags frontend dispatch as a hidden implementation risk: Codex must decide between project-aware shared endpoints and a separate RUX endpoint before real RUX data is wired.
- Requires row-level RUX anchors from subagents to be independently verified by Codex before becoming canonical test fixtures.

## Codex Independent Verification

Completed in this loop:

- RUX corrected parser profile generated using `services.api.app.listing_file_parser.parse_listing_file`, saved under `records/rux_monitoring_profile_20260708/`.
- Pitfall recorded: direct first-row workbook profiling is wrong because RUX listing sheets have a Chinese label row plus a second EDC variable-code row.
- Backend baseline with project system Python:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_listing_file_parser tests.test_protocol_text_extractor tests.test_contracts -v`
  - Result: 32 OK.
- Kimi route smoke:
  - `logs/conference/lower_half_commercialization_rux_monitoring_20260708/kimi_route_smoke_stdout.txt`
  - Result: `KIMI_ROUTE_OK`.

Not yet completed:

- Direct Codex verification of RUX protocol Table 4 / Table 7 completeness.
- Direct Codex verification of `SubjectTimelineEvent` source locator contract decision.
- Direct Codex verification of the RUX row-level test anchors proposed by subagents.
- Direct Codex decision on frontend dispatch for demo vs RUX project data.
- Any product-code implementation or browser visual QC after new edits.

## Final Decision

No code landing from this conference yet.

Accepted soft-pause state:

1. Use the Hermes/subagent/DeepSeek Pro consensus as the starting point after user resumes, not as final source authority.
2. Resume with Codex-only verification gates against original RUX files, current contracts, and current code.
3. Only after those gates, write failing TDD tests for the RUX backend P0 slice.
4. Do not land frontend RUX rewiring until the backend event layer and source locators exist.
5. Do not classify prohibited concomitant medication with keyword-only logic; bind this workflow to an independent runtime AI route plus protocol-sourced deterministic overrides.
