# Codex Review: mw_protocol_p0_phase0c_selected_hash_20260802

Date: 2026-08-02 CST  
Review mode: independent read-only challenge plus Codex final verification  
Verdict: `READY_FOR_BOUNDED_PHASE0C_CONTINUATION; NOT_READY_FOR_PROTOCOL_RELEASE`

## Boundary Check

- The patch stayed within the Protocol P0 Phase 0C selected-range identity
  slice and its task-scoped tests/records.
- r42/v36 frozen artifacts, upstream research/OCR/translation/download/retry
  state, immutable source rows, runtime services/databases, and the concurrent
  medical-monitoring lane were not modified.
- The r42 checkpoint remains SHA-256
  `d354eb0b4f8b98225c831d76f752b346315949e0e78983f24c6392c91d255130`, mtime
  `2026-07-31 16:11:13 +0800`, size `6516` bytes.

## Codex Verification

- Deterministic focused suite: `142 passed, 106 deselected in 117.94s`.
- Greenfield/blank subset: `3 passed, 15 deselected in 3.41s`.
- Changed Python files compile cleanly.
- No task listener was present on TCP 18905/18906.
- No service, browser/Playwright, Word/LibreOffice, real model, OCR,
  translation, download, or upstream workload was started.

## Independent Challenge

The independent challenge returned `READY` with no P0–P4 findings. It
confirmed: legacy missing-field backfill versus explicit mismatch fail-closed;
paragraph/table-cell/blank-greenfield authoritative re-resolution; applied
thread replay reaching only its exact immutable snapshot; no duplicate write
for a new key; legacy v1 apply fingerprints replaying exactly; missing snapshot
failing closed; and final-approval CAS working against a legacy SQLite payload.
The challenge used temporary databases and deterministic fakes and did not
modify the workbench.

## Residual Risk

`selected_hash` is an exact selected-text identity, not yet the full
`product/block/range/revision/claim/source/snapshot` identity graph. Broader
local diff/impact propagation, same-snapshot DOCX preview, production
security/validation gates, real browser/Word acceptance, Synopsis/CSR, and the
serial multi-provider/two-role release loop remain future gates. Legacy rows
without a hash can be deterministically backfilled but cannot prove the
pre-upgrade text history.

## Hermes Workflow Review Gate

This review is the required workflow-guard acceptance record. The bounded
slice has independent READY evidence and passed the decisive deterministic
checks. It is safe to proceed only to a separately tracked Phase 0C slice;
Protocol release and all frozen upstream work remain out of scope.
