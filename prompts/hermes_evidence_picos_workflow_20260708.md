You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current Codex-provided workspace.
- Do not read or modify production paths.
- Do not edit files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/hermes_evidence_picos_workflow_20260708.md`.

Read these files only:
- `context/evidence_picos_workflow_20260708_context.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/evidence_design_manifest.py`
- `services/api/app/medical_writing_manifest.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/source_intake.py`
- `services/api/app/main.py`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/tests/evidence_design_manifest_qc.mjs`
- `frontend/tests/medical_writing_manifest_qc.mjs`

Task:
Review the task context and listed source files. Produce a concrete design-review package for a PICOS interactive decision workflow that bridges `证据调研与方案设计` to `医学写作`. This is a read-only design/review round; do not edit code.

Output schema:
1. `# Hermes Task Plan: evidence_picos_workflow_20260708`
2. `## Boundary Check`
3. `## Existing Code Fit`
4. `## Recommended Backend Contract And Endpoints`
5. `## Recommended Frontend Interaction`
6. `## Persistence And Audit`
7. `## Tests And Browser QC`
8. `## Chinese Clinical Copy And Forbidden Wording`
9. `## Codex-Owned Verification`
10. `## Proposed Next Execution Slice`
11. `## Escalation Triggers`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Keep the plan scoped to Hermes execution, not Codex final review.
- Do not use `stage*` module keys as current design.
- Do not propose first/fourth/fifth non-medical subsystems.
- Do not represent AI output as approved, final, or regulator-ready.
