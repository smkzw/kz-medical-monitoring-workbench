You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- The runner working directory is the authorized workbench root. Work only inside it.
- Do not read or modify any real runtime database.
- This is the authorized edit round. Directly edit the shared workspace, but only:
  - new `services/api/app/monitoring_assurance_repository.py`
  - new `services/api/app/monitoring_assurance_service.py`
  - new `services/api/app/monitoring_assurance_router.py`
  - the minimum necessary import, dependency construction, and `include_router` lines in
    `services/api/app/main.py`
  - medical-monitoring-specific test files
  - `records/handoffs/monitoring_p8_assurance_backend_handoff_20260729.md`
  - `reviews/codex_monitoring_p8_assurance_backend_20260729_review.md`
  - `metrics/monitoring_p8_assurance_backend_20260729_metrics.md`
  Do not edit frontend, medical writing, shared AI, P7 field mapping/rule calculation,
  risk repository models, or any unrelated file.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_monitoring_p8_assurance_backend_20260729.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p8_assurance_backend_20260729_context.md`
- `context/monitoring_p8_assurance_backend_context.md`
- `context/monitoring_p7d_real_evidence_matrix_20260729.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书.md`
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`
- `services/api/app/monitoring_batch_repository.py`
- `services/api/app/monitoring_daily_run_repository.py`
- `services/api/app/medical_risk_repository.py`
- `services/api/app/medical_monitoring_summary.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/main.py`
- `tests/test_monitoring_daily_run_repository.py`
- `tests/test_monitoring_daily_run_router.py`
- `tests/test_monitoring_disposition_branches.py`
- `tests/test_monitoring_risk_contract_v2.py`
- `tests/test_monitoring_risk_index_api.py`
- `tests/test_medical_monitoring_module_contract.py`

Task:
Implement the real P8 pre-lock/pre-inspection backend end to end within the authorized files.

Required behavior:
1. Explicit task mode: `pre_lock` or `pre_inspection`; never infer from filenames.
2. Freeze batch, mapping, protocol, rule, dictionary, CTCAE, model, and risk snapshot
   identities. Any drift closes fail and requires a new task.
3. Durable SQLite repository with migration/restart idempotency, version CAS,
   idempotency-key replay/conflict semantics, recoverable state machine, and audit events.
4. Draft is persistable when readiness is incomplete, but completion must fail.
5. Pre-lock requires a complete full-recompute proof, never daily-incremental reuse:
   planned/actual subjects, sites, critical domains, and rules; per-domain planned/processed
   row counts; failures/skips/retries; a newly pinned risk snapshot; subject/site/trial
   reconciliation; open/high risks; closed risks lacking evidence; owner; lock impact.
6. Pre-inspection builds subject/site/trial rollups, distributions, remediation matrix,
   and evidence manifest from the same pinned risk snapshot. Store IDs/references only;
   never copy risk facts or evidence blobs.
7. Site clustering stores numerator, denominator, missing count/rate, method identity,
   sample adequacy, and signal status. Without a project-approved method or with inadequate
   sample, `signal_status` must be `descriptive_only`; never label a site abnormal/noncompliant.
8. Safety/PV is only an additional flag. CM and EX/EC/DA/IP must remain distinct in
   validation and rollups.
9. API: create/list/get task, readiness, record full-recompute proof, generate/read rollups,
   record medical review, and complete. Every write uses expected_version + idempotency key.
   Cross-project access returns 404; state/CAS/idempotency conflicts return 409; request
   models forbid extra fields. Public payloads must not expose local paths or internal logs.
10. Use only temporary SQLite for tests. Cover migration/restart, idempotent replay and
    different-meaning conflict, CAS conflict, drift, readiness gaps, incomplete recompute,
    exact three-level instance reconciliation, missing closure evidence, descriptive-only
    site handling, Safety/PV, CM versus study treatment, cross-project 404, status 409,
    extra forbid, and public-response redaction.
11. Run focused tests, adjacent monitoring regression, Python compilation, and scoped Ruff
    if available. Do not restart the API and do not touch real DB.
12. Write an accurate handoff and metrics record. The review file must clearly state this
    was delegated implementation pending Codex acceptance; do not impersonate Codex.

Implementation principles:
- Follow existing repository/router styles and error contracts.
- Prefer a coherent small design over speculative abstraction.
- Store frozen public identities, not local source paths or opaque internal logs.
- A newly pinned snapshot must be explicit in the proof; do not silently accept the current
  risk snapshot.
- Exact risk instance set equality is stronger than count equality and should be verified.
- Make service dependencies injectable so tests never need `main.py` or runtime DB.

Output schema:
1. `# Hermes Execution Handoff: monitoring_p8_assurance_backend_20260729`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Implemented Contracts`
5. `## Verification`
6. `## Failed Paths And Residual Risk`
7. `## Codex-Owned Acceptance`

Quality gates:
- Do not claim tests passed unless commands actually ran.
- Do not claim real runtime behavior was tested.
- Do not modify unauthorized surfaces.
- Keep all test databases in temporary directories.
- If an adjacent contract prevents a requirement, document it precisely rather than
  weakening the requirement.
