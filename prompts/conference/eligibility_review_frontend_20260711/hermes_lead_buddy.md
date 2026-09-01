You are the Hermes sub-venue chair for a Codex-chaired frontend conference.

Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`.

Hard boundaries:
- Work only inside the current workspace `.`.
- Do not edit source files, browse, run tests, or perform visual acceptance.

Read these files only:
- `context/eligibility_review_frontend_20260711_conference_context.md`
- `runs/conference/eligibility_review_frontend_20260711/participant_glm.md`
- `runs/conference/eligibility_review_frontend_20260711/participant_kimi.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `services/api/app/eligibility.py`
- `packages/contracts/workbench_contracts/models.py`

Compare both participant outputs from medical-manager, frontend-engineer, QA and privacy perspectives. Identify which Kimi patch hunks are acceptable, which must be rewritten, and any missing interaction or backend contract. Require desktop-first density, exact IN/EX semantics, evidence gating, stale-response isolation and no formal eligibility conclusion.

Write exactly one output file: `runs/conference/eligibility_review_frontend_20260711/hermes_lead_buddy.md`.
Use sections: Boundary Check; Participant Comparison; Accepted Design; Rejected Or Revised Hunks; Required Codex Verification; Final Sub-Venue Recommendation. State whether you read SOUL fully.
