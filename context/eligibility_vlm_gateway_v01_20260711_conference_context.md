# Conference Context: eligibility_vlm_gateway_v01_20260711

Created: 2026-07-11 22:39:51
Objective: Review the independently runnable local/private eligibility VLM gateway, nonclinical security fixtures, privacy boundary, and no-fallback circuit breaker before any worker integration
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: Hermes custom provider `aishuo` / `MiniMax-M3`, per the user's binding route override. OpenCode Go/Buddy MiniMax routes are forbidden for this chair role.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.
- This is a code and contract review, not a visual conference. The generated Antigravity role is excluded and must not be run.

## Source Of Truth

- `records/active_slices/eligibility_next_slice_20260711/VLM_CLOSED_VOCABULARY_CONTRACT_V0_2.md`
- `records/active_slices/eligibility_next_slice_20260711/VLM_CONTRACT_KERNEL_V0_2.md`
- `services/api/app/vlm_gateway.py`
- `services/api/app/eligibility_vlm_contract.py`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/schemas/eligibility_visual_descriptor_v1.schema.json`
- `scripts/export_vlm_schema.py`
- `services/api/requirements-vlm.txt`
- `tests/test_vlm_gateway.py`
- `tests/test_eligibility_vlm_contract.py`
- Current focused verification: 26 tests passed; no local generative VLM is configured and no real clinical image was used.

## Scope

- In scope: local-only transport, fixed profile digest, image normalization, exact-container validation, strict structured response, privacy scanner, sanitized errors, response limit, no-fallback circuit breaker, and deterministic nonclinical tests.
- Out of scope: worker/database integration, real clinical image processing, medical interpretation, visual-QC approval, selecting or downloading a production VLM, frontend changes, external web research, and production activation.

## Success Criteria

- No P0/P1 defect remains in the bounded gateway slice before further implementation.
- Every finding cites an allowed source file and distinguishes implemented behavior from unimplemented worker/model gates.
- Chair route is verified as `aishuo/MiniMax-M3`; no silent substitution.
- Production remains `vlm_gateway_not_configured` and no real clinical image is processed.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-11 22:39:51: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Generated OpenCode Go chair route rejected before execution and replaced by `aishuo/MiniMax-M3`; generated Antigravity role excluded as non-visual and out of scope.
