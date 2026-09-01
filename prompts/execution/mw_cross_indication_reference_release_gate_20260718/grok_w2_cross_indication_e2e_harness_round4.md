# Grok Cross-Indication Product E2E Harness Round 4

The Qwen Round 3 implementation is rejected. Its report claimed completion
before source changes and the current source still fabricates receipts,
lineage, scores and working-copy invariants. Replace the unsafe parts with a
source-backed isolated product harness. Do not preserve invalid code merely to
minimize the diff.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- project `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/SOURCE_GOLDEN_FACTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/quality_scorecard.schema.json`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CANDIDATE_BLIND_REVIEW_TEMPLATE.md`
- `services/api/app/main.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_translation_batch.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/medical-writing/AiRevisionCard.jsx`
- `frontend/tests/cross_indication_e2e_config.mjs`
- `frontend/tests/cross_indication_e2e_parent.mjs`
- `frontend/tests/cross_indication_e2e_child.mjs`
- `frontend/tests/cross_indication_e2e_harness_structure_qc.mjs`

Additional related source/test inspection is allowed and expected when a route,
request model, response field, selector or stage is not proven by this list.

## Codex source rejection evidence

The current child still:

- writes `final_url: ""`, `sha256: ""`, `bytes: 0`;
- writes fixed validation/extraction revisions and fixed model lineage;
- assigns every candidate six fixed scores of 4 and `average_score: 4.0`;
- treats two missing working copies (`null === null`) as proof of invariance;
- invents `medical_review_id: "e2e-review"` instead of using the actual review
  response;
- omits required translation revisions/expected revisions from review and
  admission calls;
- assumes an evidence-brief payload shape without checking the real API;
- does not load the permission-600 production AI environment file;
- labels API calls as UI coverage and does not prove selectors/actions;
- selects an arbitrary result instead of proving a fresh full product search
  found the intended relevant Protocol/SAP.

The parent currently has no genuine `--dry-run`/preflight mode and no
production-AI environment-file loader. The static test checks strings rather
than the actual route/request/response/UI contracts.

## Stress lanes

Each full lane must begin with a fresh product ClinicalTrials.gov search and
official product download. Expected targets are acceptance sentinels, not local
input files and not permission to bypass discovery:

| Lane | Query/indication | Expected relevant target | Required public document |
|---|---|---|---|
| AD | Atopic Dermatitis | NCT05923099 | `Prot_SAP_000.pdf` |
| PNH | Paroxysmal Nocturnal Hemoglobinuria | NCT04654468 | `Prot_002.pdf` |
| OBESITY | Obesity | NCT04707313 | `Prot_000.pdf` |

The product search snapshot must paginate to completion. The lane must show
that the expected study was found in the fresh snapshot and that the chosen
document role is Protocol or Protocol+SAP. Record the product's actual
snapshot/data timestamp, requested/final URL, redirect host, bytes, SHA-256,
content-validation revision and extraction revision.

## Required implementation

1. Read every used FastAPI decorator and Pydantic request/response contract.
   Build source-contract tests from the Python AST or another multiline-safe
   parser. Regex that misses multiline decorators is insufficient.
2. Read every UI selector from rendered component source. Prefer stable
   `aria-label`, role/name or `data-testid`; add a narrowly scoped stable
   selector only when none exists.
3. Use the UI for visible user actions, including project creation and fresh
   competitor search. API polling is allowed for asynchronous product state
   and immutable evidence capture. Never describe an API-only step as UI
   coverage.
4. Use the real translation medical-review response, its real review ID and
   all required optimistic-concurrency fields for admission.
5. Use the real revision-thread candidate workflow and action contract. Capture
   3-5 candidates exactly as returned. Candidate generation must not write the
   working copy.
6. Working-copy invariance is proven only when both before and after records
   exist, each has an actual content hash and revision, and the values match.
   Missing records are `not_observed`, never pass.
7. Emit only observed receipts and model/prompt lineage from product responses
   or immutable runtime records. Missing evidence blocks that lane and is
   represented as a finding; never replace it with empty/fixed placeholders.
8. `quality_scorecard.json` must conform to the current lifecycle schema:
   - `blocked_before_review` when upstream gates prevent a real review set;
   - `pending_blind_review` after real candidate sets exist;
   - never self-assign scores or `reviewed`;
   - average score and candidate scores stay null until an independent medical
     blind review fills them.
9. Load `$HOME/.config/cms-medical-workbench/ai-runtime.env` into child service
   environments without printing names/values that may expose credentials.
   Fail before external work if required product AI routes are unavailable.
10. Stable runtime default is
    `path.resolve(projectRoot, "../..", "runtime")`. Snapshot all stable
    SQLite/WAL/SHM and relevant immutable files before and after; any change is
    a hard failure.
11. Implement `--dry-run`:
    - random API/Vite/CDP ports;
    - isolated temporary runtime;
    - start real API and frontend;
    - create exactly one disposable project through the UI;
    - verify core reference-workspace route and selector contracts;
    - stop before ClinicalTrials.gov search/download and any production AI;
    - terminate services, run SQLite integrity, prove stable hashes unchanged,
      and remove temp runtime unless explicitly preserved.
12. A failed gate stops downstream lane stages and prevents later stages from
    being reported as passed.
13. Preserve screenshots only when they prove an actual rendered state. The
    main full E2E remains desktop-first at 1920x1080 with a 1600x1000 overflow
    check.

## Verification required in this pass

- `node --check` for all four harness modules.
- Static/source-contract tests must fail on each prohibited fabricated pattern
  above and pass only after it is removed.
- Run the real dry-run. Record its disposable project ID, ports, isolated
  runtime path/removal, service health, selector checks, SQLite integrity and
  stable-runtime before/after result.
- Do not start the external three-indication full run in this pass; backend
  document-level planning/chunking is a separate P1 gate still being repaired.

## Hard boundaries

- Do not touch stable 5174/8911 runtime state or real project rows.
- Do not use cached/local protocol PDFs or pre-extracted fragments as input.
- Do not expose environment values, credentials or full protocol text.
- Do not score medical quality, claim live full E2E, or claim release
  acceptance.
- Do not modify backend translation architecture in this worker.
- Source and test edits are authorized only for the isolated harness and a
  narrowly required stable UI selector.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_w2_cross_indication_e2e_harness_round4.md`

Include changed files, exact commands/results, dry-run evidence, remaining
risks, and a compact action/observation/evaluation/decision trace. Codex will
inspect source and rerun all checks.
