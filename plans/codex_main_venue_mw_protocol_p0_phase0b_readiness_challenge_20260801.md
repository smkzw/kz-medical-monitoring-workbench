# Codex Main-Venue Plan: mw_protocol_p0_phase0b_readiness_challenge_20260801

Date: 2026-08-01
Objective: Independently challenge the Protocol P0 Phase 0B typed drafting readiness slice for blank-draft compatibility, fail-closed clinical semantics, AI-first UX, idempotency, and medical-monitoring boundary preservation

## Task Decomposition

1. Independently audit typed readiness, blank-draft reachability, update
   invariants, idempotency, AI-first UX, and the monitoring boundary.
2. Synthesize severity disagreements and issue READY/REVISE.
3. If actionable defects are found, allow one bounded Codex remediation and
   re-audit it in the same chair session.

## Source Packet

- Conference context and parent Phase 0B context/review/metrics.
- Six connected source/test files plus the existing blank-greenfield runtime
  evidence identified in the conference context.
- Official ICH M11 final guideline/template locators from the parent context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/mw_protocol_p0_phase0b_readiness_challenge_20260801/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/mw_protocol_p0_phase0b_readiness_challenge_20260801/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_protocol_p0_phase0b_readiness_challenge_20260801/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Luna and DeepSeek were launched once in parallel and waited to terminal
  completion; both primary routes succeeded and no late output was discarded.
- Chair's first generated command failed before session creation because the
  installed runner rejected redundant `--participant-stdout` flags. Removing
  only those unsupported flags started the declared chair route.
- Chair completed round 1, then one same-session round 2 after Codex's bounded
  remediation. No fallback route was used.

## Codex Verification Checklist

- Check exact changed-file hashes and monitoring exclusion.
- Reproduce focused tests and build.
- Verify P1 merge/validator paths and P2 frontend behavior from source.
- Keep browser/product-model/Word/runtime gates explicitly open.
