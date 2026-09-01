You are the execution manager reviewing a bounded medical-writing workbench repair.

Read first:
- `context/mw_pipeline_start_atomic_r9_context.md`
- `runs/hermes_mw_pipeline_start_atomic_r9.md`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- the backend research-pipeline start implementation and directly relevant tests.

Review only the conflict and risk points introduced by the two-file repair. Do not
re-audit the whole repository and do not edit files. Specifically determine:

1. Whether moving `research-pipeline/start` before journey application/callback is
   sufficient and semantically correct for the frozen release-r9 evidence.
2. Whether exactly-once/idempotency, stale-project switching, timeout/AbortController,
   retry behavior, failed-start snapshot retention, and setState-after-unmount create
   a regression.
3. Whether the three new tests actually constrain the intended behavior or are weak,
   global string-position checks that could pass for the wrong function.
4. The smallest additional deterministic test or code correction, if any, required
   before a clean release-r10 headed-browser rerun.

Hard boundaries:
- Frozen r9 evidence and databases are read-only.
- Do not weaken clinical, document, corpus, translation, PICOS or independent-AI
  gates.
- Do not synthesize downstream preparation or translation state in the frontend.
- Return delta-only findings with exact file/line locators and a clear verdict:
  ACCEPT, ACCEPT WITH REQUIRED FOLLOW-UP, or REJECT.

Output:
- `# Cursor Manager Review: mw_pipeline_start_atomic_r9`
- `## Verdict`
- `## Findings`
- `## Required Follow-up`
- `## Recheck Commands`
