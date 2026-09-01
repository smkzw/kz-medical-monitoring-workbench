# Codex Main-Venue Plan: mw_r42_v36_single_item_transition_review_20260731

Date: 2026-07-31
Objective: Independently challenge the implemented single-item v36 downstream-contract transition for r42: prove source immutability, exact target scope, current-contract identities, abbreviation fail-closed behavior, and duplicate/restart model-call safety; return READY only if no P0-P4 defect remains

## Task Decomposition

1. Each participant independently traces the single-item transition from HTTP
   request through immutable intent, child batch/plan, durable payload, exact
   executor claim, external-call ledger, result persistence, restart
   reconciliation, and terminal state.
2. Each participant attacks source immutability and the 4-ready/15-excluded
   non-interference claim using SQL constraints and test snapshots.
3. Each participant attacks downstream identity separation and abbreviation
   preflight behavior.
4. Each participant returns only independently verified P0-P4 deltas or READY;
   no source edits are authorized.
5. The sub-venue chair compares both reports and challenges contradictions.
6. Codex reproduces every actionable finding, repairs if needed, reruns focused
   evidence, and alone decides final readiness.

## Source Packet

- `context/mw_r42_v36_single_item_transition_review_20260731_conference_context.md`
  is the authoritative read/scope packet.
- Read the listed changed and connected files directly. Use `rg`, structure
  reconnaissance, and bounded raw reads; do not inspect runtime DBs.
- Test evidence is a lead, not acceptance. Re-run only deterministic local
  unit tests if needed; never start an API service or call a model.
- Required output for every finding:
  severity P0-P4, exact locator, executable failure path, affected invariant,
  concrete smallest remedy, and focused recheck.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/mw_r42_v36_single_item_transition_review_20260731/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/mw_r42_v36_single_item_transition_review_20260731/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_r42_v36_single_item_transition_review_20260731/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-07-31 23:40 CST.
- Initial participants completed once; both returned NOT READY with
  complementary findings.
- Actionable repairs were implemented by Codex; each participant reused its
  original session/handle for one delta-only recheck and returned READY.
- Chair started only after both READY rechecks and completed one pass at
  2026-08-01 00:20 CST with READY.
- Parent will use one hard wait per declared route/session and will not
  redispatch or fixed-poll due to latency.
- Same-session follow-up is allowed only for a completed report with one
  actionable evidence gap.
- No fallback was activated.

## Codex Verification Checklist

- Verify no participant read either runtime.
- Reproduce every P0-P4 finding against current files.
- Confirm all changed files and preserved-file hashes.
- Confirm focused/full related suites and audit-chain assertions.
- Confirm source batch/item/raw immutable rows remain byte-equivalent in the
  deterministic proof.
- Confirm target batch contains exactly one item and all target downstream
  identities are new.
- Confirm `model_call_outcome_unknown_after_restart` is terminal/non-retryable
  and the persisted-output restart path performs zero extra model calls.
- Confirm API OpenAPI path and durable payload carry transition/target IDs.
- Do not mark READY until chair recommendation and Codex evidence agree.

Final checklist result: all items passed; `258` related tests passed; chair
and Codex agree on READY with zero unresolved P0-P4.
