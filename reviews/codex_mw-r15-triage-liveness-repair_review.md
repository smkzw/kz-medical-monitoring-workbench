# Codex Review: mw-r15-triage-liveness-repair

## Accepted Change

- Replaced the fixed 900-second parent wait with:
  - 1200 seconds without monotonic business-progress advance;
  - a 7200-second absolute ceiling;
  - lease heartbeat retained as liveness evidence only.
- Added `TriageWaitTimeoutError` so this boundary does not create another
  parent attempt while the original competitor-triage child remains live.
- A timeout keeps the authoring journey at a recoverable `triaging` stage with
  the last real child projection instead of `failed` at 100%.
- Reclaiming a durable `retry_wait` row clears its stale `error_summary`.
- Reconciliation now persists the stage and child projection atomically, so
  repeated status reads are idempotent.

## Independent Review Adjudication

SubAgent `019faa9e-443e-7e73-beea-5a7b0587736a` performed a delta-only review.

- Accepted: use `time.monotonic()` for stall and absolute-ceiling arithmetic.
- Accepted: add real `DurableJobWorker` and inline-timeout coverage.
- Rejected for this repair: require the durable child row to be `completed`
  before accepting a `review_ready` domain run. The persisted triage run is the
  business-domain authority. A worker can lose its lease after committing the
  complete run but before the final job-row CAS; hard-binding recovery to that
  job row would strand valid results.
- Deferred P1: a separately observed `confirmed` run with a stale parent needs
  a dedicated resume semantic. Mapping it back to
  `awaiting_triage_confirm` would incorrectly ask an expert user to confirm an
  already final decision, while starting preparation from a read-only status
  call would add side effects. This does not occur in the r14 blocker path,
  whose child reaches `review_ready`.

## Verification

- Python compilation passed for both changed backend modules.
- 391 unique targeted regression tests passed across:
  - triage deadline and progress projection;
  - durable-job claim, lease, retry and worker behavior;
  - A1 batch repair and triage recovery API;
  - research-pipeline minimum-start and validation gates;
  - durable triage and frontend medical-writing contracts;
  - final 5x3 harness and isolated-runtime orchestration.
- Added deterministic coverage for:
  - progress continuing beyond the old 900-second edge;
  - live lease with no business progress;
  - absolute ceiling despite intermittent progress;
  - non-retryable parent detachment without terminal 100% journey projection;
  - inline recovery projection;
  - real worker terminal job behavior followed by domain-run reconciliation;
  - stale error removal on retry-wait reclaim.

## Residual Risk And Next Gate

- Deterministic tests do not prove the real Qwen triage latency path. The next
  required evidence is a completely new r15 A1 visible-browser run from a
  zero-project isolated runtime.
- The frontend still does not expose the exact active external-AI batch while a
  request is in flight. Preserve this as a non-blocking UX observation unless
  the r15 tester shows that it causes a false stuck/failure interpretation.

