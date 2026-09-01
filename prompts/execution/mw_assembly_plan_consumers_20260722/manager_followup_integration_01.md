# Execution manager integration pass

Continue in the SAME manager session. Workers 01, 02 and 03 have completed; Codex independently ran the combined Worker 02/03 and adjacent suites: 171 passed, 6 subtests. Treat their reports as evidence, not acceptance.

Read the current source plus:
- `runs/execution/mw_assembly_plan_consumers_20260722/worker_01.md`
- `runs/execution/mw_assembly_plan_consumers_20260722/worker_02.md`
- `runs/execution/mw_assembly_plan_consumers_20260722/worker_03.md`
- `tests/test_worker02_plan_consumption_cross_projection.py`
- `tests/test_worker03_evidence_corpus_ai_plan_consumption.py`

Perform the authorized serial integration and bounded remediation now. You may write only:
- `services/api/app/main.py`
- `services/api/app/medical_writing_authoring_journey.py`
- the actual SoA/structured-table service or endpoint module, only after identifying the real production path
- narrowly necessary corrections in Worker 02/03 source files when an integration test proves a defect
- focused integration/API tests for this pass.

Mandatory outcomes:

1. Wire `medical_writing_plan_consumption_helper` into every production construction/call path introduced by Worker 02/03: protocol template, greenfield document service, revision/AI/evidence/corpus service and every DOCX exporter call. Avoid duplicate or early construction before the helper exists.
2. Make the real study-schema/flowchart workflow consume `study_schema_flowchart`, including proposal, commit/impact validation and projection/insertion into the document. A free helper function that no production service calls is not completion.
3. Locate the real Schedule of Activities / 研究流程表 structured-table creation, edit, projection and export path. Make the design-sensitive production path consume the `soa` projection from the same confirmed current plan. If the current product has no distinct SoA service, gate the canonical table-template/structured-table endpoint for `schedule_of_activities` and prove it with an API/service test. Do not gate unrelated tables.
4. Preserve one plan identity/revision/hash across synopsis, sections/TOC, SoA, flowchart, evidence/AI and DOCX. Missing, unconfirmed, stale or unresolved-blocking plans fail closed before creating design-driven content. `not_applicable` modules must not leak into generated sections, tables, flowcharts, evidence or AI context.
5. Prove real production consumers, not only direct helper calls. Add red-before/green-after integration tests that exercise service/API entrypoints for at least:
   - Phase I SAD + MAD + first-in-patient with transition dependencies;
   - interim analysis false;
   - active comparator;
   - complex background treatment;
   - non-oral modality/route;
   - stale plan and cross-project isolation;
   - SoA and study-schema projection/insertion;
   - DOCX export plan pin/fail-closed path;
   - revision AI task context carrying plan id/revision/hash.
6. Preserve source-DOCX fidelity, author-freeze semantics, citations, non-writing approvals and test-only provider policy. Do not claim E4/E5 or product release.

Use the existing Python 3.12 environment. For pagination tests requiring fitz, use `PYTHONPATH=/Users/smkzw/.local/lib/python3.12/site-packages`; do not install packages.

Run focused tests and a broad adjacent regression. Return:
- exact changed files and serial DI wiring;
- production call-site proof (`rg` plus tested entrypoints);
- commands and pass/fail counts;
- any worker claim rejected or corrected;
- residual gap, especially if a real SoA path cannot be proven;
- exact completion marker `MANAGER_INTEGRATION_COMPLETE` only if all mandatory outcomes pass.

Do not write the runner-managed report file yourself.
