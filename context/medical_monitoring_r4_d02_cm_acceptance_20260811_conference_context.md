# Conference Context: medical_monitoring_r4_d02_cm_acceptance_20260811

Created: 2026-08-11 17:00:00
Objective: Independent acceptance review of frozen isolated synthetic R4-D02 CM engine, D01 cross-domain consumption, journey projection, 30-case matrix, lifecycle and regression evidence; ACCEPT or REJECT without modifying files
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md` at
  `FROZEN_R4_D02_CONTRACT_V1`, SHA-256 `adf6150e...e4cd7`.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` at
  `FROZEN_R4_CONTRACT_V1`, SHA-256 `6bb9f73a...92705`.
- `context/medical_monitoring_r4_d02_cm_slice_20260811_execution_context.md`,
  especially Gate 1-4 evidence and accepted boundaries.
- Current isolated source and tests under
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/` and
  `poc/medical_monitoring_ai_native_r4/tests/`.
- Frozen adjacent `poc/medical_monitoring_ai_native_r2/` and
  `poc/medical_monitoring_ai_native_r3/` are regression targets only.

## Scope

- In scope: read-only code/contract audit of D02 CM inputs, five L1
  dispositions, stable identity/versioned lineage, restricted-condition
  interpretation boundary, D02-to-D01 evidence handoff/dedup, Query wording,
  CM journey projection, 30-case matrix, N-to-N+1 lifecycle and current
  deterministic regression evidence.
- Out of scope: product/frontend/browser/real project, real dictionaries,
  provider calls, clinical conclusions, R5-R8, security design/testing,
  medical-writing subsystem, service start and port 8911 mutation.

## Success Criteria

- Each participant independently returns `ACCEPT` or `REJECT`, with exact
  file/line/test evidence for every material finding and no source edits.
- Acceptance requires executable proof for all 30 cases, including case 9(a)
  and case 27; exact D01 `224`, full R4, R2 and R3 regressions remain green;
  public imports are coherent; no prohibited user-facing/internal language is
  exposed by D02 audience labels; and 8911 remains stopped.
- A material contract, false-clean, identity, dedup, projection, lifecycle or
  evidence-provenance gap requires `REJECT` with a bounded remediation.
- Synthetic/offline scope is stated explicitly; no product or clinical
  readiness claim is accepted.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Participants are strictly read-only and may not repair defects.
- Do not read or modify `frontend/`, `backend/`, real-project folders,
  medical-writing files, provider configuration, or services.

## Loop Log

- 2026-08-11 17:00:00: Conference initialized by `hermes_workflow_guard.py init-conference`.
