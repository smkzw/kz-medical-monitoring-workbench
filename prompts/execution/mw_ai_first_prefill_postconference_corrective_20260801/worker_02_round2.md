Continue the same `worker_02` session. Codex inspected the current implementation and found
one remaining P2 failure window.

After `_mark_generation_reservation_dispatched` has recorded a transport attempt, any later
failure to persist the journey/event/result cannot be classified as a known `failed` outcome.
The upstream model may have completed successfully and its result may merely have been lost
before the local commit. The current outer exception block marks every non-timeout persist
failure as `failed`, and `_acquire_generation_reservation` automatically supersedes `failed`
without requiring `force`; this can dispatch a duplicate model call after restart.

Correct the state machine so:

1. once a reservation has been marked dispatched (`transport_attempt_count > 0`), every
   non-committed terminal path is `unknown_outcome`, regardless of whether the provider
   returned, raised, or the local event transaction failed;
2. non-force same-revision retry/restart never redispatches that unknown outcome;
3. only a provably pre-dispatch failure may be retryable as `failed`;
4. explicit force behavior may remain, but the prior logical call id, attempt count, status,
   and failure reason must remain auditable rather than being silently erased. If the current
   projection overwrites them, add the smallest append-only attempt-history representation.

Add deterministic tests for:
- successful enricher result followed by injected event/persist failure, fresh service
  instance, non-force retry: zero second enricher/provider invocation and unknown-outcome
  telemetry/history;
- provider terminal exception after the one physical attempt followed by local persist
  failure: same fail-closed behavior;
- same-key/different-key concurrency tests remain green;
- explicit force preserves the prior attempt lineage if it supersedes the same reservation
  key.

Preserve worker_01 adoption/catalog changes. Re-read shared files before editing. Run the
focused reservation, gateway, journey, adoption, and complete authoring-prefill suite. Return
the complete report schema with round-2 hashes and results.
