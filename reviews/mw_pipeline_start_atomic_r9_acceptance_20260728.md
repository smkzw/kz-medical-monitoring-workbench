# Pipeline Start Atomic Repair Acceptance

Date: 2026-07-28

## Verdict

Deterministic repair accepted for a clean release-r10 headed-browser rerun.
Release-r9 remains immutable `BLOCKED / FAIL`.

## Evidence

- Frozen failure context:
  `context/mw_final_5x3_release_r9_20260728_context.md`
- Execution report:
  `runs/hermes_mw_pipeline_start_atomic_r9.md`
  (`2af4dc84cebd4088ce2dec6dd3b8537b9e88826527c91f2872e83f4385af5908`)
- Manager review:
  `runs/cursor_mw_pipeline_start_atomic_r9_manager.md`
  (`5e9e02d4007fa85892f0a6e1a2652c5135f083a24b7b54561fa1cb4096368423`)
- Accepted implementation:
  `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  (`95156b6798d940fe1cd7b83444c7c3c4a76ac88ddba9b7e45276331fe84c5bea`)
- Accepted contracts:
  `tests/test_frontend_medical_writing_contract.py`
  (`79d066660db17d11c11c6fdfdb5171cc629c25e731ef3bb5dd8fb92a59f212e1`)

## Accepted Behavior

- A successful competitor search starts the durable parent research pipeline
  before any journey application or parent callback can remount the surface.
- The start request is not cancelled by frontend unmount.
- A valid search snapshot remains available and start failure remains
  retryable while the user stays on the same project.
- If the user switches project during the start request, the server operation
  may finish but the stale response cannot write into the new project UI.
- The frontend does not fabricate preparation, translation or corpus state.

## Verification

- `python3 -m pytest tests/test_frontend_medical_writing_contract.py -k
  'pipeline_start' -xvs`: 4 passed.
- Five directly affected suites together: 147 passed.
- `node frontend/src/features/medical-writing/durableJobState.test.mjs`:
  52 passed.
- JSX esbuild bundle: passed.

## Remaining Runtime Gate

Create a fresh release-r10 with refreshed receipts and a new clean project,
database, browser profile and ports. Accept only after the browser/API trace
proves the real parent pipeline and downstream translation batch exist.
