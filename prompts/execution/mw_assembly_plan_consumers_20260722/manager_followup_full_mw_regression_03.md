# Full medical-writing regression repair

Continue in the SAME execution-manager session. Codex ran every `tests/test_medical_writing*.py` test using bundled PDF dependencies. Result: 804 passed, 99 subtests, 15 failures. Keep production fail-closed policy and current author-freeze semantics. Repair the regression baseline by cause, not by weakening product behavior.

Failure groups:

## A. Managed DOCX API plan fixtures (3 failures)

File: `tests/test_medical_writing_document_export_api.py`

Failing tests:
- draft preview mixes saved/source sections;
- authoritative greenfield cover facts;
- final export freeze snapshot/tamper.

These tests patch source mode to `greenfield`, so they exercise the managed exporter and must create/refresh/confirm a project ProtocolAssemblyPlan in setup (or a scoped fixture) and assert its pin. Do not bypass `plan_consumption_helper`. Keep actual `original_protocol_docx` source-preserving export un-gated as current production main.py does.

## B. Fake-provider fixtures must be explicit test-only (policy failures)

Files:
- `tests/test_medical_writing_real_project_flow.py`
- `tests/test_medical_writing_registered_sources.py`
- `tests/test_medical_writing_synopsis_contract_v09.py`

Any custom fake provider that is intended to run must set `test_only_provider_injection=True` on its `AiExecutionPolicyResolver`. Do not change production route policies. Preserve negative tests that intentionally prove a missing/incorrect production provider fails closed; update their expected boundary only when the test setup was accidentally relying on an unauthorized fake route. Change stale `待医学批准` fixture instructions to author-candidate/author-confirmation wording.

## C. Retired writing ApprovalGate in real-project flow

File: `tests/test_medical_writing_real_project_flow.py`

Migrate the remaining working-copy approval flow to author selection/freeze/history/readiness. Do not restore `ensure_working_copy_approval_gate`, `record_approval_action`, `medically_approved` writing statuses, or an extra medical-director approval. Distinguish revision-thread `author_selected` from section current-version freeze.

## D. Word heading expectation

File: `tests/test_medical_writing_style_profile.py`

The exporter intentionally writes complete authoritative visible numbers into Heading paragraphs while suppressing paragraph-level inherited numbering to avoid Word/LibreOffice duplicate/truncated numbering. Update the test to find `1 方案概要`, `1.1 方案摘要`, `1.1.1 主要和次要目的及估计目标`, `1.1.1.1 主要目的`; retain assertions for native Heading 1-4 style, black text, TOC navigation, style visibility and paragraph-level suppression/no duplicate numbering. Do not remove visible numbering or degrade Word styles.

Allowed writes: only the four test files above, plus a narrowly proven production defect if a focused counterexample requires it. Do not touch product policy, author-freeze implementation, plan helper or exporter semantics merely to satisfy old assertions.

Run:
1. all previously failing tests;
2. all `tests/test_medical_writing*.py` using
   `PYTHONPATH=/Users/smkzw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages:/Users/smkzw/.local/lib/python3.12/site-packages`;
3. Worker 01-03 and manager integration suites.

Return exact changed fixtures/assertions, test counts and remaining failures. End with `MANAGER_FULL_MW_REGRESSION_COMPLETE` only if the full medical-writing suite is green. Do not write the runner report directly.
