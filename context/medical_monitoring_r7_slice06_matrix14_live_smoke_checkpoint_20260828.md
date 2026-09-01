# R7 Slice-06 Matrix-14 Live Smoke Checkpoint — 2026-08-28

## Current outcome

Matrix-14 is not accepted. The default MTPLX medium path reached an authentic
OMP/model invocation only after an R7 bridge repair, then timed out. The
explicit DeepSeek max leg has not run because the declared serial gate remains
closed.

## Immutable history

1. Worker02 first run used the complete R7 background chain and failed before
   subprocess spawn with `invalid_invocation_id` because R1 attempt IDs contain
   colons while the frozen R6 adapter does not allow them.
2. Codex repaired only R7: deterministic `r7_` plus 128-bit SHA-256 invocation
   IDs, symmetric receipt classification, and a deterministic JSON/coverage
   output contract. R1 and R6 were not edited.
3. Independent Pi/Gemini and Grok Build reviews accepted the repair. Grok's
   real-R6 grammar-test gap was fixed before live retry.
4. One controlled retry used a fresh temp workspace and the same MTPLX medium
   profile. Attempt-1 reached OMP, timed out at 120.046 seconds and sealed a
   timeout receipt. The automatic linked attempt-2 was left without an active
   process when the outer 180-second evidence reader ended and was recovered as
   interrupted after lease expiry. No third attempt is allowed.

## Decisive evidence

- Frozen profile digest:
  `ea3ab9033f8b682cdc58929b90ba4c4abc67cb8ef9b5a33651ae4b255fb101bc`.
- Retry invocation ID: `r7_654744ba491a20b97ffa8dd6a91fa6b1`.
- Attempt-1: `timeout`, terminal, `state=timed_out`, `parse_state=unparsed`,
  `analysis_complete=false`, `fallback_used=false`, exit code 143.
- Attempt-2: `interrupted`, nonterminal R1 journal row, linked to attempt-1;
  control state `interrupted`, public text “本项分析未完成，已达到本次重试上限。”
- No active OMP process. Ports 8911 and 5174 remain stopped (`connect_ex=61`).
- Offline gates after final repair: focused 34; R7 158; product 33; R1 311
  with 4 deselected; R6 758 with 5 deselected; compileall PASS.
- Conference `review-gate` passes. `validate-conference` retains one guard
  inconsistency: it requires `cursor-cli`, while the same initializer generated
  only Pi/Gemini and Grok roles. Execution audit correctly remains failed
  because serial-gated worker03 was not dispatched.

## Boundaries

No real project, product service, frontend/browser, production path or medical
writing source was used or modified. Only the synthetic target
`SYN-MATRIX14-001` was supplied. DeepSeek was not used as fallback.

## Next safe action

Do not dispatch DeepSeek under the current matrix-14 packet and do not silently
rerun MTPLX. First make a recorded route decision about the fixed 120-second
MTPLX profile timeout and about whether a fresh matrix run may use a longer
frozen timeout while preserving exact model identity and zero fallback. After
that decision, create a new governed live-smoke packet; retain this checkpoint
and both failed attempts as prior evidence.
