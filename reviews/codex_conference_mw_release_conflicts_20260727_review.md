# Codex Conference Review: mw_release_conflicts_20260727

Date: 2026-07-27

## Verdict

Revise before tester launch. The conference found no new top-level
architecture fork, but confirmed three launch prerequisites: per-run physical
isolation, six built synopsis fixtures, and a DOCX gate that includes the
synopsis-import journey.

## Accepted findings

- A clean receipt is point-in-time evidence. Every slot and perspective needs
  a new isolated runtime, browser profile, download root and named receipt.
- The six synopsis fixtures are currently a release prerequisite, not merely a
  planning artifact.
- The representative greenfield DOCX validates an exporter component, not the
  complete synopsis-import product journey.
- Tester B cannot be started or followed up during the Beijing 00:00-08:30
  Aishuo blackout. A substitute does not count as Tester B.
- The historical 12-lane harness is not current launch evidence.

## Rejected or corrected findings

- `Hy-MT3` is not an active unresolved risk. Current product code, runtime
  roles and release tests use the exact gate-owned Hy-MT2 identity. Historical
  records retain the former typo only as audit evidence.
- The failed DOCX `expected_text_present` check cannot be interpreted without
  the actual expected string. The renderer now records that string in the JSON
  report.

## Main-venue decisions

The binding decisions are recorded in
`plans/mw_final_4x3_release_decisions_20260727.md`:

- one clean physical runtime per slot and perspective;
- B1 uses a single source-linked reconciliation view;
- C2 presents evidence-bounded options while preserving sponsor/medical
  confirmation for feasibility and study-specific decisions;
- every fixture has positive supplied-fact and negative leakage assertions.

## Remaining gates

1. Finish and validate all six synopsis fixtures.
2. Finish the runtime orchestrator and prove dirty-to-new-clean isolation.
3. Repair and re-render the representative DOCX until visual, field and native
   Word gates pass.
4. Complete one synopsis-import lead journey before launching the full matrix.
5. Run the four tester matrix with fresh route and product-AI receipts.

No conference output is accepted as a launch PASS.
