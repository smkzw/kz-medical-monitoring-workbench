# Codex Conference Review: monitoring_source_revision_gate_20260713

Date: 2026-07-13

## Verdict

Pass after implementation, independent verification and one frontend defect fix.

## Boundary Compliance

- All four roles used the assigned provider/model, one resumable session and three rounds; no fallback was used.
- Participants did not edit production code or claim Codex-owned acceptance. MiniMax disclosed one narrow read of `monitoring_intake.py` outside the explicit read list; this was a boundary deviation but did not affect the accepted conclusions.
- `Unknown toolsets` and event-loop-close messages occurred after usable output. All twelve rounds returned code 0 and retained a session id.

## Participant Outputs Reviewed

- MiniMax-M3 correctly elevated cache invalidation, approval-source binding, real-project intake isolation and no-demographic-inference. Codex rejected its 60-second TTL because stale clinical data must not remain valid for a timed window.
- DeepSeek V4 Pro correctly identified the pre-implementation P0 set: missing content revision, generic rule-engine leakage and the two MY009 missing-DM crashes.
- MiMo V2.5 supplied the strongest test matrix, including 267/267 drilldowns, alias canonicalization, source mutation and unchanged demo intake.

## Hermes Sub-Venue Review

GLM-5.2 reviewed the shared workspace after implementation had already started. It therefore saw `monitoring_source_revision.py`, adapter invalidation and route guards that were absent when participants read the code, then incorrectly described the participant findings as hallucinations. This is a temporal-order error, not a participant-quality finding. Codex accepted the chair's later conclusions on 409 semantics, avoiding a new partial-status schema and treating 267/267 as blocking; the temporal criticism was rejected.

## Main-Venue Codex Review

- Public revision is content-derived and path/hash-free; path, size, mtime and ctime are only internal cache-detection inputs.
- Listing and protocol are read under a revision-aware cache. Registry, inbox generation and approval writes compare current revision before and after bounded work so a mid-request source change fails closed.
- Real-project JSON intake returns 409 before the generic engine. File intake first registers and content-validates the source, then returns structured 409; demo intake remains unchanged.
- Missing-DM subjects use DS/SV identity only. Sex and age remain absent; sparse drilldowns return their real visit event and explicit empty efficacy/safety states rather than invented values or a new schema.
- Risk disposition and approval identifiers are source-bound; source replacement invalidates old actions and pending approvals.
- Browser testing found a separate transition-state crash: before an uncached sparse profile arrived, `buildSubjectView` returned a catalog row without collection fields and `PatientProfilePage` called `risks.map`. The fallback contract and empty-risk display were fixed and tested.

## Codex Independent Verification

- Synthetic listing and protocol mutations change the public revision and reload adapter caches.
- All 241 RUX and 26 MY009 catalog subjects produce revision-bound drilldowns; all timeline/trend points expose public locators.
- S02002 and S16001 return 200 with one source-grounded visit, no trend metrics and no invented demographics.
- Real-project canonical ids and aliases reject generic intake; unconfirmed files preserve the content-confirmation gate; demo intake still executes.
- Focused frontend contracts: 24 passed. Frontend production build passed with only the pre-existing large-chunk warning.
- Chrome at 1600x1000 covered both projects, 8 timelines, 8 regular profiles and 2 sparse profiles. `failures=[]`, no horizontal overflow, and original-resolution screenshots were inspected.
- Full repository regression: 706 passed, 11 dependency/parser warnings, 317.39 seconds. JUnit evidence: `records/visual_qc_20260713/monitoring_source_revision/pytest_full.xml`.

## Final Decision

The monitoring source-revision gate is accepted. The implementation meets the source freshness, fail-closed intake, 267-subject drilldown, sparse-evidence, CAS/approval and desktop browser criteria. This decision closes this monitoring slice only; Safety/PV dual-project parity and the full commercial workbench objective remain active.
