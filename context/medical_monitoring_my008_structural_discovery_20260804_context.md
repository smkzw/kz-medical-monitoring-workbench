# Task Context: medical_monitoring_my008_structural_discovery_20260804

Created: 2026-08-04 13:25:11
Objective: 只读生成 MY008-3-01/3-02 的 adapter-neutral raw-intake structural discovery profile；不注册项目、不启动 provider/runtime/browser/真实 LOOP
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Existing raw-intake contract: `services/api/app/monitoring_raw_intake.py` and its parser/classifier dependencies.
- Candidate identity anchor: `records/active_slices/medical_monitoring_my008_candidate_source_contract_20260804/MY008_CANDIDATE_SOURCE_DESCRIPTOR.json`.
- User-authorized read-only roots and exact listing/protocol files are those recorded in the candidate descriptor.
- Candidate IDs remain `proj_my008_3_01_candidate` and `proj_my008_3_02_candidate`; no canonical project ID may be introduced.

## Scope

- In scope: call the existing raw-intake service with `ai_provider_configured=False` for the two exact candidate listing/protocol pairs; retain only aggregate structural summaries (sheet/row/subject/site counts, field names, domain groups, unclassified sheets, protocol counts/title) in a diagnostic artifact; test that the summaries remain project-code-neutral and provider-disabled.
- Out of scope: cell-level or subject-level extraction, medical interpretation, mapping approval, adapter/registry/prompt changes, source promotion, B6/C14 changes, database/CAS/source-token writes, provider/runtime/browser/Playwright/API login or real LOOP.

## Success Criteria

- Both candidate roots parse through the existing raw-intake path without borrowing a canonical adapter.
- The artifact contains no cell values, subject IDs, absolute path leaks in public summaries, or provider calls; authority flags stay false.
- Distinct listing structures are preserved as observable shape metadata, while unknown/unclassified sheets remain explicit rather than forced into a project-specific template.
- Focused/adjacent monitoring tests, compile/lint and review-gate pass; 8911 remains stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 13:25:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Candidate descriptor and full monitoring regression are current; this slice is read-only structural discovery only.
- 2026-08-04: Raw-intake discovery and exact artifact replay completed for both candidates; focused raw-intake test 9 passed, 18 warnings; review-gate returned `ok=true`.
