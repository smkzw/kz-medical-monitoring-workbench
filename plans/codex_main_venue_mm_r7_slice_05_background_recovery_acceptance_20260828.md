# Codex Main-Venue Plan: mm_r7_slice_05_background_recovery_acceptance_20260828

Date: 2026-08-28
Objective: Independently audit R7 Slice-05 synthetic/offline background execution and interruption recovery against the frozen contract and current filesystem; identify concrete P0-P4 defects, boundary violations, missing concurrency/recovery tests, product-language leakage, and accept only evidence-backed behavior. Do not edit files, start services/models, or run real projects.

## Task Decomposition

1. Independently inspect contract, source, tests, receipt and execution reports.
2. Reproduce participant P0-P2 findings before disposition.
3. Repair only confirmed Slice-05 defects and add focused regression tests.
4. Rerun R7, R1 core, R6 functional, product, compile and port gates.
5. Reuse reviewer sessions for repaired-byte checks and freeze a limited record.

## Source Packet

- Contract and erratum under `context/`.
- R7 source/tests/receipt under `poc/medical_monitoring_ai_native_r7/`.
- Product router and its focused test.
- Linked worker reports and runner logs.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_05_background_recovery_acceptance_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_05_background_recovery_acceptance_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Both routes completed without fallback or timeout. Grok was continued in the
same session for repaired-byte checks; Pi was continued in its original
session. Only current, reproducible findings were incorporated.

## Codex Verification Checklist

- Confirm exact control schema and state transitions.
- Reproduce expiry, stop, continue, final-unit and failed-dependency cases.
- Verify product permissions, native Chinese copy and leak scans.
- Run current-byte focused/full adjacent tests and isolated compile.
- Confirm ports closed and forbidden boundaries untouched.
