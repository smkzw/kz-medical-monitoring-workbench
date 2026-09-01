# Codex Conference Review: mw_ai_first_prefill_postcorrective_runtime_challenge_20260801

Date: 2026-08-01

## Verdict

`NOT_READY / CORRECTIVE_EXECUTION_REQUIRED`

The chair confirmed one P2, three P3, and five P4 findings. No P0/P1 was
found. The bounded runtime slice is not accepted for continuation until the
P2-P4 set is corrected and rechecked.

## Boundary Compliance

- Read-only conference: no source/runtime edits, services, browser clicks,
  product model calls, OCR, translation, or adoption.
- r6 and the source runtime were queried read-only.
- Participants did not inspect each other's output.
- The exact native `gpt-5.6-luna` model was unavailable in the App-native
  subagent interface; an incorrectly offered Terra session was stopped before
  producing review output. The declared Kimi K3 fallback completed the Luna
  role. Pi/DeepSeek and Qwen chair used their declared primary routes.

## Participant Outputs Reviewed

- Kimi K3 fallback participant: `NOT_READY`; one P2, three P3, two P4.
- Pi/DeepSeek participant: `NOT_READY`; one P2, one P3, four P4, with a
  production-faithful composite-adoption probe.
- Both independently converged on the composite semantic-gate bypass and
  empty-recommendation frontend fallback.

## Hermes Sub-Venue Review

Qwen chair independently reconciled both reports and returned `NOT_READY`:

- P2: composite adoption accepts manual/insufficient/unsupported-gap
  evidence-bound candidates without per-path override/skip.
- P3: empty recommendation is overridden by frontend fallback; single-card
  UI exposes enabled actions that always 409; draft-divergent catalog state
  can fail closed with a misleading diagnosis.
- P4: reservation deadline owner race, failed-AI telemetry mislabeled
  completed, force-in-flight message, late replay revision, and manual-only
  recommendation inconsistency.

## Main-Venue Codex Review

Codex accepts the convergent P2/P3 evidence as actionable. The Pi participant
proved the server bypass with a crafted real-service probe in both verifier
modes; Kimi identified a reachable r6 gap candidate; the chair traced the
complete UI-to-server path.

Codex decisions:

1. Keep the single-card `manual_only`/`insufficient` fail-closed policy.
   Repair frontend button enablement, policy error handling, and reachability
   messaging; do not weaken the server gate.
2. Extend composite adoption with per-contributed-path override/skip
   requirements for manual-only, insufficient, and unsupported-gap
   candidates. Full audited overrides remain allowed.
3. Exclude `manual_only` from safe recommendation selection; do not weaken the
   corrective contract wording.
4. Correct the confirmed reservation P4s and add a draft-divergence-specific
   catalog recheck/diagnostic.

## Codex Independent Verification

The preceding r6 acceptance remains valid evidence for the contracts it
actually exercised: one transport/event, zero adoption, schema isolation,
nine-store equality, evidence deduplication, wording, negation, and OLE
preview. It cannot disprove the crafted composite path or draft-divergence
findings. The Pi participant independently reran 601 tests; those tests lack
the new composite-gap and frontend fixtures.

## Final Decision

Start a bounded corrective execution immediately. Final acceptance requires:

- composite gap/manual/insufficient candidate rejected without complete
  override/skip and accepted only with an audited full override;
- empty-slot frontend does not recommend or enable unsafe candidates;
- no enabled single-card action that deterministically policy-409s;
- draft divergence receives a correct diagnosis and safe recovery path;
- reservation owner/telemetry/message/replay tests pass;
- full focused suite remains green;
- fresh isolated-clone Computer Use and independent challenge find no P0-P4.
