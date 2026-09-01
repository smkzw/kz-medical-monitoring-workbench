You are Hermes running a bounded code-review sub-venue under Codex authority.

Read and comply with `/Users/smkzw/.hermes/SOUL.md` in full.

Route:
- Provider/model: `aishuo` / `MiniMax-M3`
- If actual markers do not match, write only a route-failure report.

Hard boundaries:
- Read only the files below.
- Do not edit code, run tests, browse, inspect images, or authorize clinical-image use.
- Write exactly one output file: `runs/conference/eligibility_vlm_contract_v01_20260711/hermes_code_review_v02.md`.

Read these files only:
- `records/active_slices/eligibility_next_slice_20260711/VLM_CLOSED_VOCABULARY_CONTRACT_V0_2.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/eligibility_vlm_contract.py`
- `tests/test_eligibility_vlm_contract.py`
- `tests/test_eligibility_evidence_worker.py`

Task:
Review only the newly added EligibilityVlm enums/models, parser/outcome functions, exports and tests. Find concrete P0/P1/P2 defects, especially Pydantic coercion, duplicate JSON handling, missing invariants, enum-order logic, exception sanitization, schema closure, outcome confusion with visual-QC pass, and regressions against the fail-closed worker. Use file/line references. Do not propose product scope expansion.

Output:
1. `# Hermes Code Review: eligibility_vlm_contract_v02`
2. `## Route And Boundary`
3. `## Findings` ordered by severity
4. `## Missing Tests`
5. `## Recommendation To Codex`
