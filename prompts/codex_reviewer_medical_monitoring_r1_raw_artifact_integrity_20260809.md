# MODE=CONFERENCE — isolated R1 raw artifact integrity review

You are an independent fresh-context verifier. Review the frozen isolated synthetic R1 slice only.
Remain read-only: do not modify files, start services, call endpoints, inspect credentials, read real
project data or touch the medical-writing subsystem. Return your report in the final response; do
not write the runner-owned path `runs/codex_medical_monitoring_r1_raw_artifact_integrity_20260809.md`.

Hard boundaries:

- Work only inside the current workbench and remain read-only.
- Runner-managed output path: `runs/codex_medical_monitoring_r1_raw_artifact_integrity_20260809.md`.
  Never write or edit it; return the report in your final response for parent consolidation.

## Read these files only

- `context/medical_monitoring_r1_raw_artifact_integrity_20260809_context.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/adapters.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_failure_injection.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`

## Frozen review objects

- `store.py`: `e47fa6b67cac709192886cf4f63dc42504df8b979a982d8076d1d2c1dfde83e7`
- `adapters.py`: `a60a2fbe374f49b23f411c6798d006607b7fe505e6ce7cc65f3bcd6e180d2c96`
- `test_capability_runtime.py`: `76c673b6cef78dba378d92948123b9c648939ee4cb30c42d28fb19263e3e4ba4`

Writable-root results after remediation: focused capability `47 passed in 0.69s`; full isolated R1
core `150 passed in 1.33s`; `store.py` and `adapters.py` compile successfully.

## Same-session remediation after the first VETO

The first pass correctly identified two defects. Recheck both against the new frozen objects:

1. A raw record deleted after its idempotency ledger entry existed could replay the stored version
   number. `put_domain_object` now verifies the exact raw record/version after idempotent execution
   and raises `StoreError` instead of restoring or reporting success. The new test deletes the row,
   replays the same request, asserts failure and proves the row remains absent.
2. A nested raw JSON value such as `NaN` could make `recover()` raise `ValueError` rather than
   report a violation. Domain and nested canonical hashing now translate noncanonical values into
   `StoreError`; the regression test proves typed load fails, recovery returns the violation and the
   damaged row is not repaired.

## Acceptance checks

1. `get_domain_object` must verify stored JSON against its recorded hash before returning data.
2. `adapter_raw_output` must be single-version immutable for one `raw_output_ref`; replay may
   dedupe only after validating stored content.
3. Typed raw loading must validate outer object hash, raw ref/run/hash identity, immutability and
   nested `raw_output_json` hash.
4. Any candidate artifact with a `raw-output:` evidence ref must fail `verify_artifact` when that
   raw record is missing or corrupted.
5. `recover()` must report corrupted domain/raw records and linked artifacts without deleting,
   overwriting or silently appending a repaired raw version.
6. Raw corruption must remain candidate-only and cannot acquire fact, acceptance, review,
   publication or user authority.
7. Existing artifact, journal, idempotency and recovery behavior must not regress.

Use static inspection, the focused/full pytest suites and bounded no-write/in-memory probes as
needed. Look for bypasses such as updating both `object_json` and its outer hash, deleting the raw
row, changing ref/run/hash fields, idempotency-ledger replay, direct `get_artifact` use, and recovery
crashes. Return exactly one verdict: `ACCEPT` or `VETO`, followed by concise findings, evidence and
residuals. Acceptance does not mean R1 is complete or that real data/provider use is authorized.
