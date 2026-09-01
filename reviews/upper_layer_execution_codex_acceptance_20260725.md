# Upper-layer execution Codex acceptance

Date: 2026-07-25

## Accepted boundary

- The server owns provider/model routing. The request contract contains no
  client-selectable provider, model, base URL, or transport.
- `document_planning` and `post_hy_mt2_integration_qc` default to
  `deepseek-v4-flash`.
- Only deterministic `failed_escalatable` or `completed_degraded` Flash
  outcomes create a `deepseek-v4-pro` child run. Exhausted transient Flash
  errors remain `failed_retryable` and do not escalate.
- Flash stage runs, Pro escalation lineage, prompt/input/output hashes,
  response model identity, deployment profile, parent run, and lease state are
  durably persisted in the additive schema v5 repository.
- A source run has at most one escalation and one target Pro run. Restart
  recovery reuses the persisted target identity.
- `corpus_selection_support` remains explicitly `not_implemented`; no model
  success is fabricated.

## Codex checks

Codex inspected the execution service, schema, repository save/read/hash
checks, escalation claim/lease/finalization path, and the focused tests.

Combined independent regression:

```text
279 passed, 1 deselected, 13 warnings in 6.38s
```

The deselected historical HTTP test assumes synchronous completion immediately
after an accepted async POST. It is not evidence of a model or lineage defect,
but its API expectation still needs a separate correction.

## Residual release boundary

This acceptance is not a production-AI or stable-runtime pass.

- `main.py` still needs the real direct DeepSeek Flash/Pro adapter and the
  persisted stage executor injected into direct and batch pipelines.
- The adapter must verify the exact response model and preserve the actual
  frozen Hy-MT2 target-map content, not merely trust a caller-supplied hash.
- A failed-retryable upper-layer run has durable state but no user-facing
  retry action yet.
- Real Flash/Pro calls, restart recovery, browser progress, and two real
  Protocol batches remain unverified.

