# Translation upper-layer orchestration Codex acceptance

Date: 2026-07-25

## Accepted boundary

- The pipeline order is Flash document planning, Hy-MT2 body translation, then
  Flash integration/QC.
- Hy-MT2 remains the only body translator. Pro can rerun only the same
  upper-layer planning or integration/QC stage.
- Integration freezes the complete target map in the stage input, computes its
  canonical hash, reuses the same map for Flash and Pro, verifies the caller's
  map after execution, and rejects a passed result whose final body differs
  from deterministic reassembly of the frozen Hy-MT2 units.
- Selected and latest stage runs remain distinct, so a failed Pro run cannot
  be reported as a successful Pro-authored body.
- Batch progress exposes short medical-writer-facing labels instead of raw
  hashes or provider logs.
- Legacy deployments without the persisted executor remain source-compatible,
  but production wiring must not silently use that path when the durable
  composite pipeline is required.

## Codex checks

Codex inspected the persisted bridge, output decoding, target-map content
checks, Pro parent/escalation validation, batch projections, and focused tests.

Combined independent regression:

```text
279 passed, 1 deselected, 13 warnings in 6.38s
```

All added model executions in this slice use fakes. No real DeepSeek or Hy-MT2
success is claimed.

## Residual release boundary

- Production adapter/prompt/deployment-profile injection in `main.py`.
- Real Flash planning, Hy-MT2 translation, Flash QC, deterministic Pro
  escalation, persisted restart recovery, and browser progress.
- Two real Protocol batches beginning from product search/triage/preparation,
  not from pre-extracted tail-stage fixtures.

