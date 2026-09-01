# Conference Context: eligibility_vlm_contract_v01_20260711

Created: 2026-07-11 21:42:00
Objective: Review and adjudicate the closed-vocabulary VLM contract for eligibility visual evidence before any implementation or real clinical-image use
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: Hermes custom provider `aishuo` / `MiniMax-M3`. This is a binding user route. No OpenCode Go or Buddy MiniMax chair fallback is permitted.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.
- No Antigravity participant is dispatched in this bounded contract review. This is a text/architecture review with no image acceptance.

## Source Of Truth

- `records/active_slices/eligibility_next_slice_20260711/VLM_CLOSED_VOCABULARY_CONTRACT_V0_1.md`
- `reviews/codex_conference_eligibility_visual_qc_vlm_20260711_review.md`
- `metrics/eligibility_visual_qc_vlm_20260711_conference_metrics.md`
- `records/active_slices/eligibility_next_slice_20260711/REAL_VISUAL_QC_GATE_V11.md`
- External references are quoted and linked inside the contract. Delegated reviewers do not browse; Codex already checked the official sources.

## Scope

- In scope: closed-vocabulary schema, clinical-inference boundary, input normalization, prompt-injection defense, structured-output validation, profile digest, no-fallback semantics, privacy/logging, immutable persistence, F01-F20 nonclinical fixtures, and implementation exit criteria.
- In scope: decide whether `body_region`, `laterality`, `pairing`, and `possible_identifier_visible` belong in v1.
- Out of scope: production code edits, model selection by vendor claim, real clinical-image processing, live web research, visual acceptance, medical/eligibility conclusions, and automatic QC pass.

## Success Criteria

- Identify every P0/P1 ambiguity that could permit free text, medical inference, hidden fallback, PHI leakage, cross-project access, stale descriptor reuse, or accidental `sampled_pass`.
- Return an explicit accept/remove/change decision for each open schema field.
- Return exact changes required before implementation and exact fixture additions/removals.
- Keep the current production path fail-closed until Codex approves the revised contract.

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

- 2026-07-11 21:42:00: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Generated OpenCode Go chair route rejected before execution and replaced with the user-mandated `aishuo/MiniMax-M3` route. Antigravity was excluded as out of scope.
