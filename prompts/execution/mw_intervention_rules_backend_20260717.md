You are Hermes aishuo MiniMax-M3 acting as a bounded backend implementation executor. First read and comply with `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`.

Hard boundaries:
- Work only in the current workspace.
- Do not touch stable runtime databases, original DOCX files, frontend files, or production services.
- You are authorized to edit only the backend contract and test files listed below.
- Do not call product AI or browse.

Read these files only:
- `AGENTS.md`
- `context/mw_intervention_rules_implementation_20260717_context.md`
- `runs/execution/mw_intervention_rules_discovery_20260717/manager_resume.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_medical_writing_study_consistency.py`

Authorized product/test writes:
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `tests/test_medical_writing_intervention_rules_contract.py`
- minimal directly related updates to `tests/test_medical_writing_authoring_journey.py` only if required

Write exactly one output file: `runs/execution/mw_intervention_rules_implementation_20260717/backend_worker.md`.

Task:
1. Implement the frozen additive `picos.intervention_rules` contract exactly as specified.
2. Preserve legacy payload validation and existing required-field behavior.
3. When structured authority is active, deterministically project structured regimen/non-IP rules to the four legacy compatibility fields. Do not project IP action rules into CM fields.
4. Add impact routing for the new structured paths while retaining legacy routes.
5. Add failure-first tests for IDs, links, no-planned-adjustment, protocol-defined rules, legacy round-trip, and D001-like CM-dose vs rescue-to-IP-link separation.
6. Run focused pytest and py_compile. Keep changes surgical.

Return a complete report with files changed, commands, observations, failures, and remaining risks. Do not claim Codex acceptance.
