You are the independent acceptance reviewer for the isolated R2-C functional
persistence foundation of the medical-monitoring subsystem. Work in a fresh
context. Do not rely on the worker's reasoning or confidence. Do not edit any
file.

Work in the current workbench workspace.

Hard boundaries:
- Review only; do not edit any source, test, context, review, plan, product,
  R1, medical-writing, or real-project file.
- Do not start any service or listener, including port 8911.
- Runner-managed report path:
  `runs/conference/medical_monitoring_r2_c_acceptance_20260810/independent_codex_luna.md`.
  Return the report in your final response; never write this path with tools.

Read these files only:
- `AGENTS.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`, sections 5, 12 and 15 as relevant
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, R2 only
- `prompts/execution/medical_monitoring_r2_kernel_execution_20260810/worker_03.md` for the exact functional acceptance boundary

Review this frozen R2 Python snapshot (combined SHA-256 manifest at dispatch:
`2931cd7a18d7b6fc6a527f4f415a8be401b6280ace741be59df95d5b306441e5`):
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/store.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/audit.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/migration.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/legacy_adapter.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/verification.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/artifacts.py`
- all `poc/medical_monitoring_ai_native_r2/tests/test_r2_c_*.py`
- `poc/medical_monitoring_ai_native_r2/tests/helpers_c.py`

Acceptance boundary:
- Functional user-data integrity only. Do not propose security hardening,
  access control, electronic signature, attack resistance, or a security test
  program.
- SQLite save/reopen must preserve the dashboard's run/source/snapshot/fact/
  risk/baseline/publication references and history.
- Artifact bytes must be content-addressed and hash-checked before atomic state
  and business-history commit. The current publication must resolve to a
  registered, complete, readable artifact.
- Same idempotency key/same request must replay the same result without extra
  history; different request must conflict. Pre-commit interruption and
  post-commit retry must be covered.
- Partial/truncated/not_evaluable/failed work must not replace the current
  completed publication.
- R1 adapter must remain synthetic and read-only, expose no write method, use
  only proven mappings, and surface matched/unmatched/ambiguous differences.
- Synthetic export/import/backup/restore/rollback must preserve current
  publication, history, identities, artifact bytes, and functional archive
  consistency.
- R1 digest must remain `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`.
- Product paths, medical-writing paths, real projects, services, and port 8911
  remain outside scope.

Codex already reproduced and repaired three defects: duplicate-content saves
now reuse the registered artifact ID, dashboard/rollback reads reject a missing
artifact, and the R1 adapter validates `monitoring_runs`; archive tables are
also checked against the archive hash before import. Challenge these repairs
instead of accepting their description.

Run focused non-mutating tests with `PYTHONDONTWRITEBYTECODE=1` and
`-p no:cacheprovider` where useful. You may create only process-local temporary
files under the test framework's temporary directory; do not modify source,
R1, product, or medical-writing files and do not start a service.

Return a compact report with:
1. exact files and contracts reviewed;
2. exact commands and results;
3. reproducible defects ordered P0-P4, with file/line locators and acceptance
   impact;
4. confirmed no-issue scope and residual limitations;
5. final `ACCEPT` or `VETO` for R2-C only.

VETO if any reproducible functional defect can publish/read an incomplete or
unreadable state, lose or duplicate committed history, break idempotent retry,
silently merge ambiguous R1/R2 identity, alter R1, or make migration/rollback
claim fidelity it does not preserve. Do not VETO for explicitly excluded
security features or for future R3+ product/UI work.
