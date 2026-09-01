# Task Context: agent_profile_poc_20260726

Created: 2026-07-26 13:43:50
Objective: Build and validate an isolated module-agent architecture POC for research, rewrite, and corpus tagging using the current Qwen default and retained DeepSeek route; compare OMP only for research; write a durable handoff to the main Agent without modifying production modules.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/evidence/SUBAGENT_PROVIDER_SELECTOR_RESEARCH.md`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_runtime_settings.py`
- `tests/test_ai_gateway.py`
- `tests/test_ai_runtime_settings.py`
- Live local status: `GET http://127.0.0.1:8911/api/ai-gateway/status`

## Scope

- In scope:
  - Isolated POC for a shared `AgentProfile` runtime.
  - Three profiles: bounded research Agent, direct rewrite Skill, deterministic
    corpus-tagging Workflow.
  - Synthetic Qwen 3.8 live run, retained DeepSeek connectivity smoke, and an
    OMP research comparison.
  - Deterministic permission, schema, step-limit, audit-redaction and
    fail-closed tests.
  - Durable report in the current Codex retake handoff.
- Out of scope:
  - Product API/frontend integration.
  - Production database or runtime settings mutation.
  - Real clinical, patient, protocol or confidential company data.
  - OCR and translation execution.
  - Any OMP write-capable production route.

## Success Criteria

- All deterministic POC contract tests pass.
- Qwen completes all three synthetic module profiles with exact model identity.
- DeepSeek retained route returns a minimal structured connectivity result.
- OMP reads the synthetic research fixture, returns a grounded result, and
  produces no filesystem mutation in the POC directory.
- Traces contain no raw secret or actual credential value.
- Main-Agent handoff records exact files, commands, outcomes and residual risk.

## Risk Boundaries

- Allowed writes:
  - `context/agent_profile_poc_20260726_context.md`
  - `runs/codex_agent_profile_poc_20260726.md`
  - `reviews/codex_agent_profile_poc_20260726_review.md`
  - `metrics/agent_profile_poc_20260726_metrics.md`
  - `records/handoffs/codex_retake_20260726/poc_agent_profiles/**`
  - `records/handoffs/codex_retake_20260726/evidence/agent_profile_poc_*`
  - `records/handoffs/codex_retake_20260726/03_SUBAGENT_AGENT_PROFILE_POC_HANDOFF.md`
- Do not modify `services/`, `packages/`, `frontend/`, product `tests/`, runtime
  state, settings, credentials, or current source artifacts.
- OMP receives only a synthetic fixture. Its working directory is hashed
  before and after the run.
- The delegated agent is evidence only; Codex owns final verification.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 13:43:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26 13:47: Current runtime reports active profile
  `alibaba_qwen38`, provider `alibaba_token_plan`, model
  `qwen3.8-max-preview`, and approved local-private deployment profile.
- 2026-07-26 13:47: Main-line Provider registry files changed after the prior
  research handoff. POC isolated from product source to avoid concurrent-write
  conflict.
- 2026-07-26 13:50: Eleven deterministic contract tests pass.
- 2026-07-26 13:52: Qwen live loop 1 exposed premature research completion:
  endpoint was cited, but the existing design source was not retrieved.
- 2026-07-26 13:53: Added required-aspect coverage to the profile contract.
  Qwen live loop 2 passed all three profiles; research used two read-only
  lookups and completed on step 3.
- 2026-07-26 13:54: DeepSeek Flash retained-route structured probe passed with
  exact response-model identity.
- 2026-07-26 13:55: OMP loop 1 failed before inference because the current
  configured provider ID is `alibaba-token-plan-cn`, not the older `alibaba`
  alias. Loop 2 used the discovered ID, called only `read`, returned the
  required grounded JSON, and left the POC tree hash unchanged.
- 2026-07-26 13:56: Secret scans clear. Core provider/settings tests passed
  (`49 passed`, `17 subtests`). Two API tests requiring import of the full
  product app were not independently rerun in the isolated environment because
  the existing application dependency chain was incomplete there.
