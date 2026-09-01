You are Hermes aishuo/cms-model acting as the user-authorized fallback frontend implementation executor after Kimi Code/k3 terminated before work because the local model entry was not configured. First read and comply with `/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, and `frontend/AGENTS.md`.

Hard boundaries:
- Work only in the current workspace.
- Do not touch backend Python, stable runtime data, original documents, or production services.
- You are authorized to edit only the frontend and frontend contract-test files listed below.
- Do not call product AI. This is implementation, not a visual acceptance claim.

Read these files only:
- `AGENTS.md`
- `frontend/AGENTS.md`
- `context/mw_intervention_rules_implementation_20260717_context.md`
- `runs/execution/mw_intervention_rules_discovery_20260717/manager_resume.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `tests/test_frontend_medical_writing_contract.py`

Authorized product/test writes:
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/InterventionRulesEditor.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- optional new `frontend/tests/medical_writing_intervention_rules_isolated_qc.mjs` only if it can remain isolated and non-writing to stable runtime

Write exactly one output file: `runs/execution/mw_intervention_rules_implementation_20260717/frontend_worker.md`.

Task:
1. Implement section-accurate 6.4/6.9/6.10 routing and pass a `panel` target through the existing study-design modal.
2. Add the desktop-first `InterventionRulesEditor` over `picos.intervention_rules` using the exact frozen JSON shape. Existing broad intervention entry opens regimen. Section-specific routes open IP actions, non-IP, or CM.
3. Keep `intervention_summary` as the broad overview; rename the old dose textarea to routine dose/regimen only. Once the structured editor is used, set authority to structured and rely on backend legacy projections.
4. Use compact segmented controls, dense rows, clear IP/CM labels, add/remove controls with lucide icons, no persistent log/info cards, no mobile-driven feature removal.
5. Preserve impact preview/save behavior; no direct working-copy or DOCX writes.
6. Add focused source-contract tests, run them, and run the frontend build.

Do not use RUX/D001/PNH project facts as production defaults. Return files changed, commands, observations, and remaining risks. Do not claim Codex visual acceptance.
