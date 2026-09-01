# Codex Review: monitoring_p10_loop316_protocol_typed_bundle_repair_20260801

Date: 2026-08-01 CST
Delegated-agent outputs:

- `runs/pi_monitoring_p10_loop316_protocol_typed_bundle_repair_20260801.md`
- `runs/pi_monitoring_p10_loop316_protocol_typed_bundle_repair_20260801_followup1.md`

## Verdict

**Pass for the offline typed structural-bundle implementation and regression gate.**

This does not pass the RUX protocol scientific gate, authorize a candidate decision,
or authorize MY009. No real v5 canary was started in this slice. The next live step,
after resumption, is at most one new single-topic v5 canary followed by read-only
scientific review.

## Boundary Check

- The Pi worker changed only the four authorized implementation/test paths in its
  initial pass and one same-session corrective pass.
- Codex identified that the provider-visible focus instructions had changed. Keeping
  prompt v4 would have violated job/candidate identity and could have collapsed a new
  result onto terminal v4 work. Codex therefore made the smallest coherent parent-owned
  extension:
  - current protocol prompt identity is v5;
  - v4 joins v3 as a terminal legacy version visible in status;
  - preparation tests cover both legacy versions and new v5 job creation.
- No API service, frontend service, real project, provider job, candidate decision,
  mapping action, draft assembly, confirmation or activation was started.
- 8911 and 5174 both had zero listeners at final inspection.
- No medical-writing business source was edited by this task. Concurrent writing files
  visible in the workspace were left untouched.
- This workbench has no Git metadata, so change attribution is based on the guard-owned
  runner records, current-file inspection and exact hashes rather than a Git diff.

## Codex Verification

- Re-read the repair helper, typed lineage models, repair union construction,
  group-specific structure validator, per-claim semantic-anchor gate, candidate-ID seed,
  v5 prompt identity and v3/v4 legacy visibility.
- Confirmed the repair union is ordered over structured IDs, conflict IDs and claim IDs;
  only same-row/header or one unique list ancestor title can be added; conflict and claim
  arrays remain unchanged; the final union is capped at 50 without truncation.
- Confirmed provider-supplied repair lineage is rejected before normalization and the
  persisted lineage is typed with a pinned repair schema version.
- Confirmed protocol candidate identity uses the server-normalized structured payload,
  while non-protocol candidate identity remains unchanged.
- Focused combined gate:
  `tests/test_monitoring_ai_source_packet.py`,
  `tests/test_monitoring_ai_service.py`,
  `tests/test_monitoring_protocol_preparation.py` -> **222 passed**.
- Full medical-monitoring selection:
  `pytest tests -q -k monitoring` -> **1185 passed, 4299 deselected,
  27 warnings, 0 failed** in 618.27 s.
- Medical-writing adjacent contract:
  five named writing/reference/frontend files -> **201 passed, 17 warnings,
  0 failed** in 3.60 s.
- Python compilation of the three changed service modules passed.
- Warnings were existing Python/FastAPI/openpyxl deprecations; no new failure signal was
  observed.

## Delegated-Agent Output Review

- The initial worker implementation covered the required negative matrix but missed
  five material identity boundaries: empty list ancestry, claim/conflict-only evidence
  in the repair union, claim-level original anchors, normalized candidate identity and
  typed lineage.
- Codex sent one consolidated follow-up to the same Pi session
  `019fb908-83d1-7000-9601-82dd441a70ca`; it corrected all five gaps and reran the
  authorized focused tests. There was no re-dispatch or fallback.
- The worker's initial conclusion that no prompt bump was required was rejected by
  Codex because focus wording and provider-visible evidence changed. The v5 correction
  is now covered by preparation tests.
- Runner stderr recorded plugin-handler timeouts, but both calls returned code 0 with
  complete reports and passing test evidence; no output truncation or provider fallback
  occurred.

## Hermes Execution Review

- The workflow guard selected `Pi / deepseek / deepseek-v4-flash / max` for the
  finite-code task and preflighted the bounded prompt.
- One runner session was launched and retained through one consolidated same-session
  correction. The parent used long hard waits, did not fixed-interval poll, did not
  duplicate dispatch and did not invoke a fallback.
- Codex independently inspected the current implementation, corrected the v5 identity
  boundary, ran the broader regressions and retained final acceptance.

## Residual Risk

- Offline tests cannot prove how the real provider will select anchors under v5.
- Repair applies to evidence-packet v2; legacy v1 behavior is intentionally unchanged.
- Packets with missing/empty/ambiguous structural identities fail closed; this can
  surface conservative false negatives but cannot be relaxed without new evidence.
- Table/list/paragraph mixtures remain allowed when every typed bundle closes exactly;
  a future scientific audit may require stricter topic-specific atomicity.
- The existing eight v4 candidates remain proposed/pending user confirmation; six v4
  failed jobs remain failed. They were not migrated, retried or decided.
- The protocol scientific gate remains blocked and MY009 remains blocked.

## Final File Hashes

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_source_packet.py` | `6263537d3443b1a2c477814f36c54abf10b67d0da7b39621652eb88132de1b98` |
| `services/api/app/monitoring_ai_service.py` | `c185d251b39151ff0598d231214d32ec59b2ffda4ff122552269f031e74fd955` |
| `services/api/app/monitoring_protocol_preparation_service.py` | `97f2a50c61e71d2bffbc90b33de3e1a9cc005df0542b759519cbea77d1938713` |
| `tests/test_monitoring_ai_source_packet.py` | `829401956c11326f200639c0dc016d38c8c8fbc15edbf358f219c8c94858fa05` |
| `tests/test_monitoring_ai_service.py` | `fdc3baa662dd377a532d222105ac2df8f004d6b2e223946b6ea3397796e9e97d` |
| `tests/test_monitoring_protocol_preparation.py` | `8c8cfae53e57dd50d7fb63fd8aaf4db8b2a08265518aa17ad2b8eec08c08d7e6` |
