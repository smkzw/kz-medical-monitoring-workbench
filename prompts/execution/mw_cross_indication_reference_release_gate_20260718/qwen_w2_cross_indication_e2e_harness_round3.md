# Qwen W2 Cross-Indication E2E Harness Round 3

Continue the same qwen3.7-plus execution session. Round 2 created four real
files and its 26 structural checks pass, but Codex source audit rejects the
harness as a live E2E instrument. Repair the actual executable workflow; do not
add assertions that merely approve the current file text.

Before acting, reread `/Users/smkzw/.hermes/SOUL.md`,
`/Users/smkzw/.codex/AGENTS.md`, project `AGENTS.md`, the task record, the
current four harness files, current `main.py`, current request/response models,
and the relevant frontend components. Treat the prior report as evidence, not
truth.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/quality_scorecard.schema.json`
- `frontend/tests/cross_indication_e2e_config.mjs`
- `frontend/tests/cross_indication_e2e_parent.mjs`
- `frontend/tests/cross_indication_e2e_child.mjs`
- `frontend/tests/cross_indication_e2e_harness_structure_qc.mjs`
- `frontend/tests/medical_writing_new_project_isolated_qc.mjs`
- `frontend/tests/medical_writing_end_to_end_continuation_qc.mjs`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`

## Codex-observed defects

1. The child calls nonexistent review/admission paths:
   - `/references/medical-review`
   - `/references/admission`
   Actual routes are translation-specific and require the real translation ID,
   revision, review revision and admission contract. Inspect source and use them.
2. Candidate generation is falsely sent to
   `POST /medical-writing/working-copies/{chapterId}`, which is a working-copy
   save route, not an AI candidate route. Use the actual revision-thread product
   workflow (`/api/projects/{project_id}/revision-threads` and current actions)
   with real section/working-copy setup. Generate 3-5 suggestions for at least
   two real document sections.
3. The child invents evidence after execution:
   - empty URL/SHA/bytes and fixed validation/extraction revisions;
   - fixed model lineage not read from product state;
   - hardcoded candidate scores of 4 and `unsupported_claim_count=0`;
   - fixed `average_score=4.0`;
   - fake chapter mapping from section IDs.
   This is prohibited. Every receipt, locator, hash, model, revision, mapping,
   candidate and count must come from product API/runtime state. If unavailable,
   emit an explicit gate failure and leave the corresponding artifact empty or
   marked `not_observed`; never fabricate a pass.
4. The parent claims to inherit production AI but the current Codex environment
   does not contain the required variables. The harness must load the existing
   permission-600 runtime file
   `$HOME/.config/cms-medical-workbench/ai-runtime.env` for the isolated API
   process without printing secret values. Preflight only variable presence and
   expected non-secret provider/model labels. Fail explicitly if absent.
5. The parent snapshots the wrong default stable runtime
   (`projectRoot/runtime`). Match the proven isolated harness and snapshot the
   real stable runtime at `path.resolve(projectRoot, "../..", "runtime")`,
   including SQLite, WAL/SHM and all stable files.
6. The child claims UI coverage but uses direct API for framing, competitor
   search and triage even though current UI controls exist. Use the visible UI
   for every stage with an implemented control; use API only for assertions or
   operations without a UI control. Record which surface performed each step.
7. The current structure test only proves strings exist. Add source-backed
   route/selector contract tests:
   - parse or inspect current `main.py` for every called route;
   - inspect current frontend source for every primary selector/label;
   - fail on any unverified route;
   - fail if output-building code contains synthetic fixed hashes, revisions,
     scores, model lineage or empty receipts presented as evidence.
8. A lane may terminate at the first genuine unavailable product gate, but no
   later stage may be reported as passed, scored or evidenced. Persist the
   observed gate, logs and preceding real evidence.
9. Create a genuine product document and working copies before candidate
   generation. Preserve working-copy content hash and revision before/after the
   revision-thread candidate request; do not treat 404/null==null as proof of
   immutability.
10. `quality_scorecard.json` must remain `pending_blind_review` until a medical
    reviewer or later blind-review runner supplies scores. It must not award
    itself a passing score.
11. Source selection must search freshly and retain a relevant official
    Protocol/SAP. Do not simply take the first NCT result. Verify indication,
    study phase, document role and official host. Record triage reasons.
12. All required screenshots must be recorded by path and state. Browser QC must
    distinguish expected gate HTTP failures from unexpected page/API failures.

## Required verification

- `node --check` all four files.
- Run the revised structure/source-contract QC.
- Add a dry-run/preflight mode that starts the isolated API/Vite with production
  AI environment, proves the real stable runtime snapshot target, creates one
  disposable project, and stops before external ClinicalTrials.gov download.
- Run that dry-run and prove stable runtime hashes are unchanged.
- Do not run the full three-indication external-model E2E until the CMS backend
  remediation is accepted by Codex.

## Hard boundaries

- Do not modify backend production source, stable runtime, credentials, real
  clinical files or unrelated frontend code.
- Do not print, copy or persist secrets.
- Do not invent endpoint names, selectors, evidence, scores or quality passes.
- Do not claim live three-indication E2E or visual release acceptance.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/qwen_w2_cross_indication_e2e_harness_round3.md`

Implementation files are authorized source edits in addition to that one report.
The report must include exact changed files, exact commands/results, dry-run
evidence, remaining gates and a compact loop trace.
