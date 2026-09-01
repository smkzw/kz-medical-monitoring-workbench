You are an independent live QA validator and later Hermes sub-venue reviewer in a Codex-chaired workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your report, state honestly whether you read the full file.

Assigned route:
- Provider: `buddy`
- Model: `minimax-m3`
- Output file: `runs/conference/live_workbench_qc_20260707/hermes_lead_minimax_m3.md`

Hard boundaries:
- Work only inside the current workspace root.
- Do not edit source files.
- Do not browse the public web.
- Do not invoke real OCR, real LLM review, or any production write operation.
- You may use terminal, file read, local browser automation, and HTTP requests against `127.0.0.1`.

Read these files only:
- `context/live_workbench_qc_20260707_conference_context.md`
- `README.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `services/api/app/main.py`
- `services/api/app/monitoring_intake.py`
- `services/api/app/eligibility.py`
- `packages/contracts/workbench_contracts/models.py`

Write exactly one output file: `runs/conference/live_workbench_qc_20260707/hermes_lead_minimax_m3.md`

Required live checks:
1. Backend:
   - `GET http://127.0.0.1:8910/api/health`
   - `GET /api/projects/proj_mgk10_sar_demo/dashboard`
   - `GET /api/projects/proj_mgk10_sar_demo/eligibility`
   - `GET /api/projects/proj_mgk10_sar_demo/subjects/10008/monitoring`
   - `POST /api/projects/proj_mgk10_sar_demo/monitoring/intake` with the demo payload if feasible.
2. Frontend:
   - Open `http://127.0.0.1:5173/`.
   - Visit 项目总看板、入排审核、医学监查、Subject Timeline、Patient Profile、医学写作、审批中心.
   - Check for horizontal overflow on desktop and mobile-like width.
   - Check key expected content: real rule IDs like `IN-05`/`EX-07`, Subject Timeline event lanes, Patient Profile trend charts, editable writing editor, approval quality gate.

Reviewer emphasis:
- Evaluate product architecture and clinical workflow realism, not only isolated UI bugs.
- Identify which defects should block near-term productization versus later hardening.

If browser automation is unavailable, use HTTP + static DOM/source inspection and clearly mark visual findings as not rendered-verified.

Report schema:
# Live Workbench QA - minimax-m3
## Route And Access
## Commands / Browser Actions Actually Performed
## Backend Findings
## Frontend Findings
## Clinical Workflow Findings
## Priority Bugs
## Recommendations
## Evidence vs Inference
## Suggested Next Conference Agenda

Write the report to the assigned output file. Also print a short final message with the output path only.
