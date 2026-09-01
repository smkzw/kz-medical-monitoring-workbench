# Codex Review: monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801

Date: 2026-08-01
Delegated-agent output: `runs/pi_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801.md`

## Verdict

**Pass for the offline v6 corrective slice.**

This is not authorization to start a v6 canary, accept any candidate, pass the RUX
protocol gate, or start MY009.

## Boundary Check

- Pi initial pass used session `019fb977-9636-7000-876b-15f3ea49de8a`, one round,
  no fallback. Codex found two in-scope gaps and resumed the same session once with
  one consolidated corrective prompt; no re-dispatch or route switch occurred.
- Pi changed only the six authorized implementation/test files. Codex later updated
  one adjacent API test fixture to supply the new required `fact_type`.
- No service, provider, browser, runtime DB, real project, candidate decision, v5
  retry, or v6 canary was started.
- 8911 and 5174 remained at zero listeners.

## Codex Verification

- Evidence packet is v3, structural repair lineage v2, and protocol prompt identity
  v6. Terminal legacy status compatibility now includes v3/v4/v5.
- Stable list identity is exact ancestor-title source identity; causal
  `parent_match_source_ids` is lineage only. Explicit items only, unmarked following
  paragraphs remain paragraphs, and term-based prose ending `。` cannot become a
  title.
- Provider focus retains a valid item's unique ancestor without siblings and omits a
  primary orphan/ambiguous item. Structural repair fails closed on untyped,
  ambiguous, cross-list, cross-row or cross-table selections.
- Protocol payload requires `fact_type` and validates it against
  `candidate_fact_types`.
- Visit candidates reject non-visit treatment/collection/withdrawal/safety/PK content
  and require exactly one visit action family.
- Conflict detection is exact topic/object paired: study-treatment/IP,
  concomitant-medication/non-IP; every other topic receives none.
- Protocol output schema omits `system_generated_evidence`; the instruction remains
  outside the schema.
- Codex focused run: **241 passed**, 0 failed.
- First full monitoring run exposed one adjacent stale API fixture. After adding its
  required fact type, the point test passed and the complete rerun was
  **1206 passed, 4299 deselected, 27 warnings, 0 failed**.
- Five-file medical-writing adjacent contract:
  **200 passed**, 0 failed.
- Python compilation of the three implementation modules passed.

## Delegated-Agent Output Review

- The initial Pi pass incorrectly left bundle-less primary list items in provider
  focus and allowed IP/CM conflict cross-contamination between the two medication
  topics. Codex rejected acceptance and the same-session follow-up corrected both
  with negative tests.
- The full 14-item v5 negative matrix is mapped in the initial Pi report; the
  follow-up tightens item #7 and adds exact topic/object conflict pairing.
- The API fixture change is contract maintenance only; no product behavior was
  weakened to satisfy the test.
- No external dependency or architecture adoption was needed; the defect was fully
  characterized by immutable v5 evidence and existing local contracts.

## Residual Risk

- Strict contiguous explicit-item detection may under-bind unconventional real DOCX
  lists; this is an intentional fail-closed direction and needs one future v6 canary.
- Conflict evidence IDs are preserved exactly. If such evidence is itself an orphan
  list item, candidate structural validation still fails closed rather than silently
  trimming the conflict set.
- Runtime startup/persistence and real provider behavior for v6 remain unverified.
- RUX protocol gate remains blocked; MY009 and the three-real-project sequence must
  not start until a fresh v6 canary and independent read-only review pass.
