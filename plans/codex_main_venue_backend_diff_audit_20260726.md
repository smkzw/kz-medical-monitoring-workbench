# Codex Main-Venue Plan: backend_diff_audit_20260726

Date: 2026-07-26
Objective: Audit backend and contract differences against the pre-takeover baseline without modifying product code; produce evidence-backed findings in the designated handoff report

## Task Decomposition

1. Reconstruct the exact takeover diff from the four handoff records and the retained baseline.
2. Audit the shared contract model, every modified API module, and the four new 2026-07-26 modules.
3. Reproduce high-impact contract, state-machine, source-gate, idempotency, and recovery failures.
4. Run focused non-destructive tests over the changed backend surfaces.
5. Adjudicate independent objections and write only evidenced findings to the requested report.

## Source Packet

- `records/handoffs/CODEX_RESUME_P0_18_20260726.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/01_RECONSTRUCTED_DIFF_SUMMARY.md`
- `records/handoffs/codex_retake_20260726/02_EXACT_TAKEOVER_INVENTORY_DIFF.md`
- `/tmp/mw_agent1_baseline_20260725_retake1`
- Current `packages/contracts/workbench_contracts/models.py`
- Current modified/new files under `services/api/app`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/backend_diff_audit_20260726/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/backend_diff_audit_20260726/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/backend_diff_audit_20260726/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- All three roles completed one full pass with return code 0 and no timeout.
- No fallback route or targeted follow-up was needed.
- All outputs were available before final adjudication and were reviewed together.

## Codex Verification Checklist

- [x] Baseline/current file-level diff reconstructed.
- [x] Report findings independently checked against current source and line locators.
- [x] Focused tests run with the existing system Python; no dependency installation.
- [x] Unsupported speculation and unreachable failure paths excluded.
- [x] No product code modified.
- [x] Final report written to the requested evidence path.
