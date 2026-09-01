# Codex Review: r41 Triage Status Synchronization

## Verdict

Accepted for clean-runtime retest. This is not a product PASS.

## Hermes

Hermes/aishuo/cms-model session `20260730_083026_a3ef67` implemented the
bounded repair. Codex independently reviewed the changed data flow and ran the
verification below.

## Observed Defect

- Persisted retry job `mwjob_cfd820cde520a7a25e040ced` completed at 19/19,
  returned all 665 recommendations, and reached `review_ready`.
- The persisted parent pipeline also reported
  `awaiting_triage_confirm`, child 19/19, and 100%.
- The writing-reference drawer showed the terminal recommendations and enabled
  bulk locking, while the outer authoring toolbar/banner remained at 17/19.
- Root cause: the drawer recovered a newer parent-pipeline payload into local
  state, but the outer authoring page's poll had already stopped at a stable
  waiting stage and did not receive that newer snapshot.

## Accepted Change

- `WritingReferencePanel` emits the guarded current pipeline payload after its
  existing recovery fetch.
- `AuthoringCompetitorDrawer` forwards the callback.
- `MedicalWritingAuthoringJourneySetup` merges only the nested pipeline into
  its current parent status, preserving parent-owned sibling fields.
- Active non-terminal/non-waiting stages restart parent polling.
- Project and snapshot stale-response guards remain in force.

## Verification

- Focused status/drawer/waiting contracts: `26 passed`.
- Broader medical-writing frontend contract slice: `175 passed`.
- Production frontend build: passed, 1910 modules transformed.
- Existing large-chunk advisory remains; it is not introduced by this patch.

## Residual Risk And Retest Boundary

The added regression is primarily a source-contract test. A hot-reload frontend
could not be validly paired with the preserved r41 backend because current
source also contains post-r41 backend changes; the runtime contract correctly
blocked that mixed build. No bypass was used.

Acceptance requires a clean immutable r42 runtime and a real visible-page retry
through the same A1 COPD III scenario. The outer page must visibly converge to
the drawer's terminal count and permit the one-click bulk review path.
