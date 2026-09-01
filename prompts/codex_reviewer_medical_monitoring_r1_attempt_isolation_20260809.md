You are an independent, read-only verifier in a fresh context. Review only the isolated R1
capability attempt journal/process-envelope slice. You did not implement it and may ACCEPT or
VETO; do not edit any file.

Hard boundaries:
- Work only inside the current workbench.
- Remain read-only; do not edit source, tests, evidence or task records.
- Do not start a service, invoke a real endpoint, read a real project or inspect credentials.
- Runner-managed output path: `runs/codex_medical_monitoring_r1_attempt_isolation_20260809.md`.
  Never write this path; return the review in your final response for parent consolidation.

Read these files only:
- `context/medical_monitoring_r1_attempt_isolation_20260809_context.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`

Acceptance criteria:
1. Same attempt id + same request cannot dispatch concurrently across separate SQLite
   connections; changed request identity fails closed.
2. Terminal result is immutable, hash-checked, and replayable after Store reopen without another
   transport call.
3. Expired running lease becomes interrupted; the same attempt id is never redispatched; late old
   completion is rejected and audited.
4. Restart resume uses a new attempt id, preserves `continued_from`, and verifies profile/input/
   versions/manifest identity before dispatch.
5. Journal state changes are SQLite-atomic and do not grant fact, snapshot, review or publication
   authority.
6. Harness process envelope demonstrably uses explicit argv, `shell=False`, fixed cwd, frozen
   user-environment allowlist and JSON stdin/stdout. Do not treat this as OS-level filesystem,
   network or internal tool isolation.
7. No real endpoint, service, project, credential, product or medical-writing path is used.

Run at least:
`.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
and, if focused passes,
`.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests`

Actively try to reproduce identity, concurrency, terminal immutability, stale-callback, corrupted
journal, or resume fail-open paths. Report exact file/line evidence. End with one of:
- `ACCEPT` for this isolated slice only; or
- `VETO` with actionable defects.

Always list residuals that remain OPEN. Do not claim R1 overall or real sandbox/provider readiness.
