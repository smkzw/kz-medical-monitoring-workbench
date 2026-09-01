# MODE=CONFERENCE — same-session repair verification

Continue the existing read-only review of the isolated R1 capability journal/process-envelope slice. Review the repaired current filesystem only; do not modify files, start services, call real endpoints, or inspect real project data.

## Hard boundaries

- Work only inside the current workbench and remain read-only.
- Do not edit source, tests, evidence, task records, or the runner-managed output path `runs/codex_medical_monitoring_r1_attempt_isolation_20260809.md`; return the review in your final response for parent consolidation.
- Do not start a service, invoke a real endpoint, read a real project, inspect credentials, or touch the medical-writing subsystem.

## Read these files only

- `context/medical_monitoring_r1_attempt_isolation_20260809_context.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`

## Frozen review objects

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
  SHA-256 `296b95a29707ec6aeb091eabf7365bcc3cbb09a06b9b0afe7db336f6d6c9d6d1`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
  SHA-256 `e8dc5d285c3578a8225887fcbfd64e01fb18fc5113072697a78287c9da352dbd`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
  SHA-256 `499390a7aefe49084d5d96477602345f2b09b49d82dd594fcc0f63bf091be321`

Root verification in a writable local test environment after the repair:

- focused: `44 passed in 0.67s`
- full isolated R1 suite: `147 passed in 1.37s`

## Previous vetoes that must be rechecked

1. An expired lease must never permit same-owner redispatch or late terminal commit, even if explicit recovery has not run first.
2. `resume` must rederive and validate profile/input/version/manifest identity before declaring, claiming, or dispatching a new attempt.
3. Harness `working_directory` must be a non-empty absolute existing directory, remain valid at dispatch, and never fall back to inherited cwd.
4. Journal completion must accept only terminal adapter statuses; terminal status and result must be immutable.
5. The journal must cross-check request JSON against row-level JSON-RPC method, attempt id, run id, node id, manifest revision, continued-from, profile identity, and input identity before resume or dispatch. The prior `manifest_mismatch DISPATCHED ['new']` reproduction must now fail closed with zero transport calls and zero new attempt.
6. When a durable journal is configured, same-runtime cached attempts must not bypass journal validation. The prior same-runtime reproduction (`transport_calls=2`, new row created) must now fail before a second transport call and before a new row.
7. The terminal row status must be covered by the immutable result hash. The prior direct SQLite mutation from `complete` to `failed` must now make `get_capability_attempt` and replay fail closed; it must not return a stored `failed` status with a replayed `complete` adapter result.

Check the repair implementation and the new regressions. If your read-only environment still cannot create pytest temp files, do not treat that infrastructure limit as a product veto; use static inspection and no-write probes where useful, and report it as verifier residual. Return exactly one final verdict for this slice: `ACCEPT` or `VETO`, followed by concise evidence and residuals. Acceptance is not permission for a real endpoint and does not mean R1 is complete.
