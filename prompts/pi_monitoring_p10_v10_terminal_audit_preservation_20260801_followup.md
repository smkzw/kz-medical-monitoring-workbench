Continue the same bounded terminal-audit preservation session. Do not restart
the task. The initial pass correctly stopped on a concurrent `main.py` hash
change and made zero edits.

Hard boundaries:

- Work only inside the current runner-provided workspace.
- Do not access or modify runtime, provider configuration, databases, ports,
  browsers, real projects or production paths.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v10_terminal_audit_preservation_20260801_followup.md`.
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

- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

The current hashes are now explicitly re-frozen:

- service:
  `08207529f0a17156c55843e2003d2c2746c9721154312dacd5783b0a7e2081ef`
- main:
  `3c5455b4123e8085df6a9470d734e6c432eabfdaac35a661cc4d9d42f1857ab4`
- preparation test:
  `0bb75558acca3e91e77fba7da5cdee4b38f8b5b679a495efe2e09c1a003d0d5d`
- startup test:
  `7290a4814a4511795cc784279e4f0fd42dedac52f0893fb92f6d70971767f2bf`

Preserve every current unrelated `main.py` change. Implement the design from
your initial report:

1. Keep `PROTOCOL_STATUS_LEGACY_PROMPT_VERSIONS` as v3-v8 only.
2. Add a distinct terminal-audit retirement set containing v3-v9.
3. Make startup pass that audit set to
   `supersede_prompt_versions_except`.
4. Update focused tests so completed/failed v9 retain status, failure
   code/message, retryable flag, created/updated timestamps, attempts and
   candidate content/status while gaining immutable retirement markers.
5. Keep queued/running/blocked v9 fail-closed as stale, reject late completion,
   claim and retry, keep v9 status-incompatible, and select a distinct v10 job.
6. Preserve all v3-v8 behavior and generic repository semantics.

Run compilation, focused preparation/startup tests, the full repository test,
and proportionate adjacent monitoring AI/API regressions. Return a delta-only
execution report with exact changed paths, commands, results, hashes and
residual risk. Do not claim runtime, canary or release acceptance.
