Continue the same bounded session for the second and final recovery pass.
Do not restart or revisit already-green work.

Hard boundaries:

- Work only inside the current runner-provided workspace.
- Do not access or modify runtime, provider configuration, databases outside
  test temporaries, ports, browsers, real projects or production paths.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v10_terminal_audit_preservation_20260801_followup2.md`.
  Return the report; never write or edit that path directly.

Read these files only:

- `context/monitoring_p10_v10_terminal_audit_preservation_20260801_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

Authorized writable paths:

- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

Current frozen hashes are in the task context and must all match before edit.

Luna found one propagation-path P1 and two coverage gaps:

1. Production v9 and v10 protocol jobs share the exact business key.
   `_create_job()` creates a distinct stable v10 job, then calls
   `supersede_business_key_except()`. That method currently transitions every
   non-stale completed/failed same-key row, even if startup already
   marker-preserved it. It therefore overwrites the terminal v9 after the first
   real v10 start.
2. The decisive protocol test hides this by giving all terminal v9 rows
   suffixed business keys.
3. The failed fixture is `provider_timeout` with no response; it does not cover
   the real `failed/invalid_ai_output`, `invalid_output` attempt whose response
   contains initial and repair outputs. BLOCKED v9 is also not directly covered.

Implement the smallest coherent invariant:

- In `supersede_business_key_except`, a COMPLETED or FAILED row that already
  has a non-empty immutable `contract_retirement_code` remains marker-only:
  keep status, failure fields, retryable value, leases, timestamps, attempts
  and candidates unchanged. Its first retirement marker remains immutable.
- Unmarked terminal same-key rows retain the existing stale/superseded behavior.
- QUEUED, RUNNING and BLOCKED rows retain existing fail-closed transition
  behavior. Existing input-only stale compatibility remains unchanged.
- Add a generic repository regression for marker-preserved terminal rows
  followed by same-business-key supersession.
- Change the protocol v9→v10 regression so the representative failed v9 uses
  the exact production business key. Persist one realistic attempt with
  `outcome=invalid_output`, `failure_code=invalid_ai_output`, and a response
  object containing exactly initial+repair lineage; after v10 creation and
  completion prove that the entire attempt response/hash, terminal failure
  fields, `updated_at`, zero candidates and marker are unchanged.
- Add a protocol-specific BLOCKED v9 and prove it becomes stale, non-retryable
  and unclaimable.
- Keep the existing status-set/audit-set split and startup wiring unchanged
  unless a test-only import adjustment is needed.

Run compile, focused repository/protocol/startup tests, full repository and
protocol-preparation tests, plus the same adjacent service/API/worker suites.
Return only the delta: paths, exact commands/results/hashes and residual risk.
Do not claim runtime, canary or release acceptance.
