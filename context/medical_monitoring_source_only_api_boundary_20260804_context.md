# Task Context: medical_monitoring_source_only_api_boundary_20260804

Created: 2026-08-04 18:48:08
Objective: Fail closed at backend medical-monitoring routes when the canonical binding is source_manifest_only or otherwise unconfirmed, while preserving active and test bindings.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/project_source_manifest.py` — canonical module binding and implementation status.
- `services/api/app/medical_monitoring_router.py` — primary module API authorization boundary.
- `services/api/app/main.py` — legacy monitoring route authorization boundary.
- `services/api/app/monitoring_source_readiness.py` — new pure readiness contract.
- `tests/test_medical_monitoring_module_contract.py` and `tests/test_monitoring_source_readiness.py` — focused acceptance evidence.
- Formal runtime authority remains read-only: B6/C14 and the real-loop audit were not crossed.

## Scope

- In scope: make configured-but-unactivated medical-monitoring bindings fail closed at both primary
  module routes and legacy monitoring routes; preserve active/demo/test bindings; add deterministic
  contract coverage and redacted block details.
- Out of scope: source parsing, adapter activation, provider calls, browser/Playwright work, real
  project intake, database migration, listener startup, medical-writing routes and source files.

## Success Criteria

- `source_manifest_only` and unknown/unconfirmed monitoring bindings return a stable 409 block after
  the applicable identity decision and before snapshot/command work.
- Active statuses (`real_source_slice`, demo/legacy active states and focused `available` fixtures)
  retain prior behavior; projects with no monitoring binding retain existing not-configured handling.
- No block detail discloses internal paths, source rows, credentials or provider payloads.
- Focused backend, cross-module monitoring, existing frontend monitoring contract and read-only gate
  checks pass.

## Risk Boundaries

- Only the workbench backend contract, focused tests, and task evidence files may change.
- Do not start 8911/5174/8910/4173, APIs, providers, browser/Playwright, real project jobs or long
  loops; do not cross B6/C14/real-loop authority.
- Do not edit medical-writing source/runtime or supplied project files.
- The source-only guard must not fabricate readiness or replace existing not-configured behavior.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 18:48:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 18:50–18:53: Added the pure backend readiness resolver and redacted 409 detail contract.
  Primary module-router reads/writes and unconfigured writes now check readiness after identity
  authorization but before service execution. Legacy monitoring actions use the same contract; source
  evidence/catalog routes remain available for future structure parsing.
- 2026-08-04 18:53–18:57: Focused source/readiness tests, module-contract tests, risk export, project
  manifest, real-project intake, protocol-rule, rule-release, AI/shadow/readiness, batch preflight/
  repository tests and all medical-monitoring Node suites passed. No listener or runtime/provider work
  ran. One assertion initially checked SQLite file size; it was corrected to assert zero snapshot/risk
  rows, preserving the repository's normal schema initialization.
