# Task Context: mw_protocol_p0_phase0b_rebaseline_20260801

Created: 2026-08-01 08:46:13
Objective: Rebaseline and close the next Protocol P0 Phase 0B production slice: AI-first sparse-input safety and default complete reviewable protocol, without touching monitoring or replaying frozen r42 stages
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under this workbench; this is a non-git shared tree.
- `/Users/smkzw/.codex/AGENTS.md` Section 12 is the canonical current
  execution/conference route contract. The older project `AGENTS.md` applies
  only where it does not conflict with that global contract.
- `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`, especially
  Protocol Phase 0B and its exit gates.
- `runs/MW_R42_V36_CLONE_TRANSITION_SCOPE_DELTA_PAUSE_20260801_0058.md`
  plus its linked context/review/metrics, now recording
  `RUNTIME_ACCEPTED / PROTOCOL_PHASE_0A_CLOSED`.
- Current medical-writing product code, contracts, tests, frontend surfaces,
  and existing acceptance records. Old reports are leads; current code and
  reproducible observations take precedence.

## Scope

- In scope:
  - Rebaseline the current implementation against every Phase 0B step and
    exit gate.
  - Trace the smallest real end-to-end path from one-line need plus optional
    sources through known-fact reuse, dynamic minimum questions, decision
    proposals, complete applicable-section draft/blocking, and cross-section
    exception review.
  - Implement the smallest coherent missing Phase 0B slice only after
    read-only audit identifies exact connected files and tests.
  - Focused deterministic tests, then independent contradiction review and
    later real browser/product-AI evidence where the slice requires it.
- Out of scope:
  - Protocol Phase 0C/0D except checking interfaces needed to avoid a dead-end
    Phase 0B design.
  - Synopsis, CSR, final three-route release testing, and any other subsystem.
  - Replaying r42 POST/idempotency/model calls or any frozen triage, download,
    OCR, translation, attempt, ready, or excluded stage.
  - Medical-monitoring source, context, run, review, metric, SQLite, WAL, SHM,
    service, or task files.

## Success Criteria

- Produce a requirement-by-requirement Phase 0B evidence matrix with exact
  code/test/runtime locators and honest states: implemented, offline-tested,
  real-runtime-verified, or still open.
- Select the first missing production-critical slice by dependency order and
  prove it advances the real Phase 0B exit gates, not a narrower substitute.
- Before any product edit, freeze hashes of every connected file and identify
  concurrent-change detection/rollback.
- If implementation proceeds in this task, focused tests must prove:
  known facts are not asked again; unsupported high-impact facts never become
  silent document facts; every applicable section receives substantive draft
  or an actionable evidence block; repeated review/worker/restart is
  idempotent; unrelated projects and monitoring remain untouched.
- Persist context/review/metrics and a no-loss next action. No Phase 0B or
  release claim is allowed without real product-AI/browser/Word evidence at
  the scope required by the relevant gate.

## Risk Boundaries

- Initial pass is read-only outside this task's generated
  `context/`, `plans/`, `reviews/`, `metrics/`, and non-runner-owned `runs/`
  records.
- The guard-reserved
  `runs/codex_mw_protocol_p0_phase0b_rebaseline_20260801.md` and stdout file
  are runner-owned and must not be edited directly.
- Product/test writes require an exact connected-file list and baseline hash
  in this context first. Preserve all unrelated shared-tree changes.
- Never import/start full `main:app` for a strict isolated medical-writing
  check because it physically touches monitoring SQLite/SHM at startup.
- User granted routine in-scope operations and future bounded deltas, but that
  does not authorize destructive broad cleanup, replay of non-repeatable
  external effects, or overwriting concurrent work.
- Computer Use is required for user-facing permission dialogs and real Word
  or other GUI clicks. Source/API simulation cannot substitute for later
  user-view acceptance.
- Codex remains final authority; external execution/conference output is
  evidence only.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 08:46:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 08:45-08:47 CST: User accepted the bounded r42 runtime deltas.
  Existing r42 context/run/review/metrics were updated to close Phase 0A.
  Goal status was confirmed `active`. Next action: read-only Phase 0B
  requirement-to-code/test evidence map.
- 2026-08-01 08:48-09:00 CST: Read-only Phase 0B rebaseline found:
  - conversational fact intake already has allowlisted durable facts,
    high-impact unknown/proposal handling, at most three dynamic questions,
    SQLite idempotency, and focused tests;
  - the current company template materializes all selected nodes, but a
    deterministic I/II/III fixture probe found respectively 82/74/74
    applicable non-front-matter/document-control body nodes with empty text;
  - the existing generic `待补充` paragraph covers only 20 core semantic IDs
    and is not an actionable machine-readable reason/missing-input/remediation
    contract;
  - some empty nodes are intentional structural containers, so treating every
    empty heading as a clinical blocker would be incorrect.
- External decision check used the official ICH M11 Step 4 final guideline and
  template adopted 2025-11-19. They support a common, complete and
  unambiguous protocol structure while explicitly allowing heading-only
  structural nodes and `Not applicable` handling. No external executable
  component is needed; keep the current typed Pydantic model and align the
  readiness semantics with those final documents.
- First missing production slice selected: typed per-section drafting
  readiness. An applicable node must resolve to substantive draft, structural
  content/container, or actionable blocker; a non-applicable node must be
  explicit. Actionable blockers keep their paragraph body blank so the
  existing greenfield blank-draft model path remains available.
- Connected-file baseline frozen before product edits:
  - `packages/contracts/workbench_contracts/models.py`
    `e2ae86cc7bff01459ee62cde9ec0392e88b87f565d05b2c14b221161c85f7ff6`
  - `services/api/app/medical_writing_protocol_template.py`
    `28969480d8bc77c7d1a96fb641177cd415b2d6d2c092b54a953cfcfa6ebea882`
  - `services/api/app/medical_writing_greenfield.py`
    `676f7b59f79cde0e2ae5d57693bd7fd56657800d6dfab6610790dc0117de3c80`
  - `tests/test_medical_writing_protocol_template.py`
    `726f12fcaf9925ace6391943e80a74980f7bf234995a415170f037c598d966c7`
  - `frontend/src/App.jsx`
    `a94e7bd795d236c7166c13b0e12fee90094975660feb0dc2594dbc0f6b1d7af1`
  - `frontend/src/styles.css`
    `458de7c071d60e1967db0fdf300bc7eff179126a15c69d6f84b6697c3abdda09`
- Baseline focused verification:
  `python3 -m pytest -q tests/test_medical_writing_protocol_template.py
  tests/test_medical_writing_fact_intake.py` -> `63 passed in 1.76s`.
  These tests do not import/start the full application and did not touch the
  monitoring runtime.
- Primary discovery sources:
  - ICH M11 Step 4 Final Guideline (2025-11-19):
    `https://database.ich.org/sites/default/files/ICH_Step4_M11_Final_Guideline_2025_1119.pdf`
  - ICH M11 Step 4 Final Template (2025-11-19):
    `https://database.ich.org/sites/default/files/ICH_Step4_M11_Final_Template_2025_1119.pdf`
- 2026-08-01 09:00-09:13 CST: Implemented the bounded slice:
  - added fail-closed typed drafting readiness fields to greenfield seeds and
    materialized protocol sections;
  - classified selected nodes as substantive draft, structural content,
    structural container, actionable blocker, or not applicable;
  - preserved actionable blocker body text as empty, propagated it as
    `blocked_missing_inputs`, and retained the existing blank-draft AI path;
  - surfaced the current section's actionable blocker compactly in the
    desktop editor with one `AI 先起草` action and expandable missing evidence.
- Post-change deterministic evidence:
  - I期: 110 nodes = 6 structural content, 19 structural containers,
    10 substantive drafts, 75 actionable blockers;
  - II期/III期: 102 nodes each = 6 structural content,
    19 structural containers, 10 substantive drafts, 67 actionable blockers;
  - applicable `unclassified` nodes = 0; blocker body pollution = 0.
  - `python3 -m pytest -q tests/test_medical_writing_protocol_template.py
    tests/test_medical_writing_fact_intake.py` -> `66 passed in 3.34s`.
  - Python compileall passed for all three changed backend modules.
  - `npm --prefix frontend run build` passed (1914 modules); the existing
    large-chunk warning remains non-blocking and unchanged in kind.
- Current connected-file SHA-256:
  - `models.py`
    `d2598e8377946e98b11f0241bb6fc3d01c6c6d96e62a13df96d8890565ad073c`
  - `medical_writing_protocol_template.py`
    `1c155634cb54ddc55036c7597925e9ba8f04d71fade3771ea46e902c4ead6802`
  - `medical_writing_greenfield.py`
    `d689226fd3e0e86b79461999bb2472d8390f826d0650609f3f87109957f7636b`
  - `test_medical_writing_protocol_template.py`
    `a7661b79c85b5a893a752c0a3bf006bd0642cb315b48e4f21f1f2d3518f583b6`
  - `frontend/src/App.jsx`
    `d6f4e8e6ce940d0c3f2773a7fa3e8d80d62f6baaea8956eef439f993bad692b0`
  - `frontend/src/styles.css`
    `168455d2f81e12ad33a326885a55bdc369ccbe7aa35eb0cf894d514b734dd38a`
- This is offline/build evidence only. No service, browser, product model,
  Word, or release gate was started or claimed. Next action is independent
  contradiction review under the current workflow guard.
- Independent conference result:
  - Luna and DeepSeek completed one read-only participant pass each on their
    declared primary routes; Qwen chair completed two rounds in the same
    session with no provider fallback.
  - Round 1 returned `REVISE`, chiefly because same-resolution updates mixed
    old content with new readiness and `model_copy` bypassed validators.
  - Codex added cross-field invariants, atomic readiness/content preservation,
    explicit post-merge revalidation, working-copy-aware blocker visibility,
    project-decision blank-anchor support, one-click blank drafting,
    user-readable labels, deterministic frontend retry identity, and
    document-control structural classification.
  - Chair round 2 returned slice-level `READY`; Phase 0B runtime gates remain
    open. Codex then closed the remaining low-risk backend semantic-hash gap
    and the P3 blank-draft intent label.
- Final verification after the last two fixes:
  - focused tests: `67 passed in 1.77s`;
  - Python compileall: passed;
  - frontend production build: passed;
  - no service, browser, product model, Word, or monitoring runtime used.
- Final connected-file SHA-256:
  - `models.py`
    `61e3dd4807162f37eb66a9e7a4b942e051df9a12bdc73397528e6d36e2f36d4a`
  - `medical_writing_protocol_template.py`
    `ee94cd4c2f73b8abae3478e3d8f4a3302f9732107cc9f5732df17038aefb2ad3`
  - `medical_writing_greenfield.py`
    `7023bc5f55ac927f434b911f1a4c2eb6f2633260e17ca86bcbcaa23f19d90d8f`
  - `test_medical_writing_protocol_template.py`
    `6b42aee397cd622a8be05d33cee70188bda2f62aa53183d389dc6c46b7adffdc`
  - `frontend/src/App.jsx`
    `0d8bbd89a94546905664ae5228ba0a063ca98f8536d82c71ca2aa00f589386d2`
  - `frontend/src/styles.css`
    `168455d2f81e12ad33a326885a55bdc369ccbe7aa35eb0cf894d514b734dd38a`
- Safe policy decisions for the next slice:
  - treat `drafting_status` as baseline scaffold/readiness metadata; current
    blocker visibility is derived from actual working-copy content;
  - keep unknown/deferred optional modules out of clinical text, but add a
    document-level unresolved readiness signal before any ready/freeze claim;
- 2026-08-01 10:50-10:53 CST: One event-driven Computer Use inspection of
  the existing isolated browser run showed material progress from triage
  chunk 3/6 to chunk 4/6, with 59 studies and 21 public Protocol documents
  unchanged. After one further long wait the accessibility tree was
  unchanged. This remains a healthy `running` state: no model re-dispatch,
  service restart, retry, or short-interval controller polling was performed.
  API session `50294` (port `18911`) and frontend session `87332` (port
  `15174`) remain live against `runtime_glm_retest4`. Next safe action remains
  a single inspection on terminal or explicit user-action event.
- 2026-08-01 10:54-11:08 CST: The same live triage advanced without retry
  from chunk 4/6 through 6/6 and reached `awaiting_triage_confirm`.
  Computer Use opened the actual basket drawer: AI had classified all 59/59
  studies, recommending 21 retained and 38 excluded, with one optional
  detail-edit path and one `确认并锁定全部59项` action. Codex used that one
  user-facing action; authoring version advanced from 4 to 5 and the same
  pipeline entered public-Protocol download/extraction. No API substitution
  or second confirmation was used.
- The new isolated project then completed its first 64-page public Protocol
  and started the second of 21. For the first document, 63 pages required
  OCR and visible progress advanced 0/63 -> 21/63 -> 46/63 -> complete.
  The second 87-page document required OCR on only 15 pages, proving native
  text pages were reused rather than all pages being blindly OCRed.
- Live oMLX evidence at this boundary:
  - `/Applications/oMLX.app/Contents/MacOS/oMLX` and `omlx-server` running;
  - gate model `GLM-OCR-bf16`;
  - 8 active OCR leases, 0 queued OCR, 0 translation, 0 reclaimed expired;
  - every active lease owner was `medical-writing-api:ocr`, PID `43191`;
  - source contract enforces `WRITING_REFERENCE_OCR_MIN_DPI=200` and new OCR
    evidence rejects non-200-DPI rendering.
- The retained drawer showed every retained study as `间接参照`, including
  efgartigimod studies. Read-only source review found this is expected
  fail-closed behavior, not a label-mapping defect: direct-competitor status
  is downgraded whenever technology type, administration route, or target
  mechanism remains unknown. The current project still lacks technology
  type, so no product change was made.
- 2026-08-01 11:08-11:13 CST: The unchanged preparation job continued
  through the third retained Protocol without retry. `NCT04951622 /
  Prot_000.pdf` contained 151 pages and 64 OCR-needed pages; visible progress
  advanced 12/64 -> 25/64 -> 49/64 -> complete. The pipeline then entered
  the fourth of 21 (`NCT02301624 / Prot_000.pdf`, 115 pages, 21 OCR-needed
  pages) at 21% overall. No user action, re-confirmation, OCR re-run, model
  re-dispatch, or service restart occurred.
  - keep legacy seeds fail-closed while they remain accepted;
  - do not broaden this slice into final export gating or Phase 0C.
- 2026-08-01 09:15-10:07 CST: Closed the document-level optional-module
  readiness aggregation slice:
  - `_quality_gates` now emits one document-level `动态章节适用性` gate for any
    `unknown`/`deferred` optional module;
  - `_approval_blockers` adds exactly one aggregate module blocker while
    retaining unresolved project decisions;
  - baseline state and all connected frontend transitions use the same
    aggregate blocker count, and the title action renders `待审核 N 项`;
  - focused protocol/fact-intake/frontend-contract tests passed:
    `182 passed in 2.01s`; Python compileall and frontend production build
    passed, with only the pre-existing large-chunk warning.
- Authoritative post-aggregation SHA-256 (supersedes the earlier final-hash
  block above):
  - `packages/contracts/workbench_contracts/models.py`
    `61e3dd4807162f37eb66a9e7a4b942e051df9a12bdc73397528e6d36e2f36d4a`
  - `services/api/app/medical_writing_protocol_template.py`
    `ee94cd4c2f73b8abae3478e3d8f4a3302f9732107cc9f5732df17038aefb2ad3`
  - `services/api/app/medical_writing_greenfield.py`
    `290b0bc5e89cfef4d54858a41c1983a1e9289d1fe4c9372c31383e044fd28023`
  - `tests/test_medical_writing_protocol_template.py`
    `fb8f3b797fec4604d3b9258a2768ee40fbb0273212f0df052dbcb8c61ed6352b`
  - `frontend/src/App.jsx`
    `5dc42a9f27eef6ac39f65311bea159b660ba44f4314dcf8695e2b45aede46c86`
  - `frontend/src/styles.css`
    `168455d2f81e12ad33a326885a55bdc369ccbe7aa35eb0cf894d514b734dd38a`
  - `tests/test_frontend_medical_writing_contract.py`
    `d41c491d896e6b2289c8d5bf16e2130d14db0115b1553d884f7ac4d920065570`
- Conference-boundary correction:
  - the Qwen chair report claimed no `main:app` import, but also recorded an
    18-test run of `tests/test_medical_writing_greenfield_runtime.py`; that
    module directly imports `services.api.app.main as app_main` at line 72.
    The no-main/no-monitoring claim is therefore false.
  - A read-only comparison against the 00:20 r42 pre-run snapshot found
    `integrity_check=ok` for all four monitoring stores, but not a global
    logical-zero delta: assurance remains identical; AI, batches, and
    daily-runs differ in schema and/or rows. AI row timestamps extend through
    09:10:55 CST and belong to the separately running monitoring lane; batch
    rows predate this conference. Because there is no immediate
    pre-conference monitoring snapshot, the conference import's exact logical
    contribution cannot be isolated from concurrent authorized monitoring.
  - The only defensible conclusion is a conference boundary deviation and
    unresolved causal attribution, not a monitoring logical-zero claim. The
    read-only SQLite audit itself refreshed SHM physical metadata/mtime; it
    did not alter logical rows or schema.
- This deviation does not change the seven-file Protocol product result:
  the bounded readiness/aggregation layer remains offline READY. It does
  block any claim that the conference was fully boundary-compliant and
  reinforces that the next runtime gate must use an isolated
  medical-writing-only runtime/entrypoint before browser, product-model, or
  Word acceptance.
- 2026-08-01 10:07-10:12 CST: Isolated full-import gate proved the safe
  short-term runtime route without editing product source:
  - The existing `scripts/qc/mw_isolated_runtime_baseline.py` copied only its
    four allowlisted AI configuration files into a new system-temp runtime.
  - A child process imported `services.api.app.main` with explicit
    `WORKBENCH_RUNTIME_DIR=<isolated runtime>` and
    `WORKBENCH_INCLUDE_REFERENCE_PROJECTS=false`.
  - Child observation: resolved runtime matched exactly, 326 routes loaded,
    and 12 monitoring SQLite/WAL/SHM files were created only inside the
    isolated runtime.
  - Stable monitoring boundary: raw size/mtime/SHA-256 fingerprints for all
    12 existing monitoring SQLite/WAL/SHM files were identical before and
    after; `shared_changed_files=[]`.
  - The first preparation attempt failed closed before application import
    because macOS `/var` is a symlink. Re-running under the resolved
    `/private/var/...` system-temp root passed without weakening the guard.
- Architecture decision:
  - current runtime gate uses explicit process-environment isolation, which
    Python's subprocess contract supports and this repository already tests;
  - long-term, split the monolithic application into documented FastAPI
    `APIRouter` modules, but do not mix that larger refactor into Phase 0B
    runtime acceptance.
  - Primary references:
    `https://docs.python.org/3/library/subprocess.html` and
    `https://fastapi.tiangolo.com/tutorial/bigger-applications/`.
- Next action: start an isolated local API/frontend pair, verify clean state
  and product AI role identity, then use Computer Use for real user-view
  Protocol browser acceptance. The stable runtime remains out of scope.
- 2026-08-01 10:12 CST onward: Isolated browser gate started on
  API `127.0.0.1:18911` and frontend `127.0.0.1:15174`.
  - Initial clean-state verification failed closed because the copied stable
    OCR role was `paddle_official / PaddleOCR-VL-1.6`, conflicting with the
    current global oMLX/GLM OCR contract.
  - Using Computer Use in the real UI, Codex selected the existing
    `本机 oMLX · OCR AI · omlx` connection with `GLM-OCR-bf16` and saved it
    only inside the first temp runtime.
  - Because that legitimate UI change invalidated the immutable baseline
    manifest, Codex stopped the temp API, used the first temp runtime as a
    whitelist-only source, prepared a second new temp runtime, and restarted.
  - Second startup gate passed:
    `CLEAN_STATE_VERIFIED`, project count 0, project-bearing rows 0, server PID
    30597, all four locked role identities ready. Stable configuration was
    never edited.
  - Computer Use created one clean I期 non-oncology project:
    `CMS-MG-101 / 全身型重症肌无力`; the UI entered
    `研究方案智能设计与写作` and automatically initiated public competitor
    search/research-pipeline work. No API or DOM click substituted for these
    user actions.
- 2026-08-01 10:27-10:46 CST: The first browser project exposed two
  fail-closed consistency defects and one registry-recall defect:
  - terminal `failed` was simultaneously described as
    `公开研究处理已完成`;
  - neutral nested scaffolds such as `{"planned": false}` and
    `{"src": false, "dmc": false}` were treated as completed AI decisions;
  - the ClinicalTrials.gov request sent the Chinese indication
    `全身型重症肌无力` directly to `query.cond`, returning 0 and then asking
    the user to supply an English term that the UI does not collect.
- Minimal product corrections:
  - `AuthoringCandidatePackagePanel.jsx` now requires recursively meaningful
    composite values and ignores `available_*` choice catalogs; neutral false,
    empty strings/lists and empty nested objects remain unresolved;
  - `MedicalWritingAuthoringJourneySetup.jsx` distinguishes failed,
    cancelled and completed public-research terminal states;
  - the existing controlled condition resolver now maps
    `重症肌无力` and `全身型重症肌无力` to ClinicalTrials.gov-compatible
    English terms. No new translation service or architecture was introduced.
- Verification:
  - 122 frontend source-contract checks passed;
  - 3 resolver tests passed;
  - 4 focused runtime assertions for nested composite values passed;
  - frontend production build passed with only the pre-existing large-chunk
    warning;
  - official ClinicalTrials.gov API probes under the same PHASE3 and
    INTERVENTIONAL filters returned 0 for the Chinese condition, 59 for
    `generalized myasthenia gravis`, and 11 when additionally filtered by
    `efgartigimod`.
- Runtime retest:
  - a strict fourth isolated runtime passed `CLEAN_STATE_VERIFIED` with 0
    projects and 0 project-bearing rows; backend/frontend build fingerprints
    matched;
  - Computer Use created
    `艾加莫德α注射液 / 全身型重症肌无力 / III期`;
  - the product searched the English condition, retained 59 candidate studies
    and 21 public Protocol documents, and entered AI triage (6 chunks);
  - the III-phase neutral design scaffold correctly remained at 13 unresolved
    decisions with adoption disabled.
- Additional boundary note: one mistyped pytest node selector collected
  `tests/test_medical_writing_authoring_journey.py`, whose imports include the
  full application. No target test ran. The new resolver assertions were moved
  to a pure module test and the full-app test was not repeated. As with the
  earlier conference deviation, no causal shared-monitoring logical-zero claim
  is made.
- Current changed-file SHA-256:
  - `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`
    `cc871387e3996452666a5f37afc3ff7bd6310bb944c306d23c87d050baff7bbf`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
    `6dc4c46456036a9f80a5d95b58aee268cb1874f058ca8f6a3a8a75014455c441`
  - `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.test.jsx`
    `ad5cfa68de007c7648b790076b2fa386c513a6eff0ef87606db7c527806d91e0`
  - `tests/test_frontend_medical_writing_pipeline_waiting_contract.py`
    `2b89052e98c666f3c6a8955536f7e7175033c962f60f5b7c0529266c166599c8`
  - `services/api/app/medical_writing_condition_term_resolver.py`
    `a100e854010a92d0004b53e6e1888255b82cd86a872b577fe82dab836a8483ec`
  - `tests/test_medical_writing_condition_term_resolver.py`
    `39dda2b678e1d1e7de4c64b1c17213bef22fc16eceb811595c48822fe5895b91`
- The single AI-triage run remains pending. Do not re-dispatch or short-poll;
  inspect only after its next terminal or user-action waiting event.

## OCR Route Correction And File-Bound Cutover — 11:24 CST

- User corrected the testing route: use the official Paddle API with
  `PaddleOCR-VL-1.6`; any document that had already begun GLM OCR must finish
  with GLM. The active Goal remains `active`.
- Official-source verification:
  - PaddleOCR's current primary repository and PaddleOCR-VL documentation
    identify `PaddlePaddle/PaddleOCR-VL-1.6` and structured Markdown/JSON
    document output.
  - The configured hosted endpoint
    `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs` exists and rejects
    GET with 405, matching its POST-only asynchronous job contract.
  - A real 200-DPI image request using the existing encrypted
    `ocr_paddle_official` credential completed in 2.786 seconds, returned
    model `PaddleOCR-VL-1.6`, one page, and correctly recognized the fixed
    probe token; no GLM fallback was accepted as Paddle evidence.
- The continuously running batch advanced while the route was being verified.
  At the safe cutover decision, item
  `wref_prep_item_678a208936e6185af10a7555`
  (`NCT04980495 / Prot_000.pdf`) had already resolved GLM and therefore
  remained GLM through its `prepared` terminal state.
- An event-driven SQLite VNODE watcher, not a fixed polling loop, waited for
  that exact immutable item boundary. After terminal commit it changed the
  isolated runtime OCR role once to
  `ocr_paddle_official / PaddleOCR-VL-1.6`; the role endpoint returned 200.
- The next document `NCT05681715 / Prot_000.pdf` resolved Paddle at file
  start and reached 30/31 OCR pages with the role still ready and bound to the
  official provider. Its persisted extraction evidence is checked only after
  the item terminal event.
- Product hardening:
  - `services/api/app/main.py` now accepts the extraction service's
    document-pinned OCR model and resolves the corresponding configured
    specialized profile even if the live OCR role changes later.
  - Unknown pinned models and missing/disabled/mismatched profiles fail
    closed.
  - This removes the old per-page live-binding mismatch failure while
    preserving per-page actual provider/model/fallback provenance.
- Focused verification: 70 tests passed across role/gate integration,
  Paddle-primary fallback, and AI role settings; Python compileall passed.
- No API/frontend restart, preparation retry, candidate re-lock, duplicate
  download, or prior-document OCR replay occurred.
- First post-cutover terminal evidence:
  - `NCT05681715 / Prot_000.pdf` reached `prepared`;
  - document profile `PaddleOCR-VL-1.6`, 200 DPI, 31 OCR pages;
  - 28 pages were produced by `paddle_official / PaddleOCR-VL-1.6`;
  - 3 pages (physical 2, 13, 18) received HTTP 429 at Paddle submit and were
    transparently produced by `omlx_glm / GLM-OCR-bf16`;
  - all fallback pages retained `primary_model=PaddleOCR-VL-1.6` and
    credential-safe `fallback_reason`; no provider/model relabeling occurred;
  - mixed-model QC ran once and returned `review_required`, specifically
    preserving table-X distribution questions for source verification.
- Follow-up product hardening, for the next runtime without replaying the
  active batch:
  - Paddle hosted calls are capped at four concurrent requests inside the
    existing eight-worker extraction pool;
  - submit HTTP 429 receives up to four bounded attempts with
    Retry-After-aware exponential backoff before GLM fallback;
  - ambiguous HTTP 5xx responses are not retried because the official service
    has no caller-provided idempotency token proving that a job was not
    accepted before the error;
  - the retry test proves delays 0.25 then 0.5 seconds before a successful
    third submit.
- Updated focused suite: 72 passed, including explicit proof that HTTP 503 is
  attempted once and never retried; compileall passed. The already-running
  process is intentionally not restarted, so its remaining documents retain
  the previous immediate-fallback behavior and immutable evidence.

## Preparation, Translation Retry, And Admission — 12:09 CST

- The unchanged isolated runtime completed all 21/21 public-Protocol
  preparation items on attempt 1. The first-round corpus analysis also
  completed 4/4, and the authoring journey persisted
  `round1_material_ready=true`.
- The translation batch initially settled `partial_failure` with
  1 `candidate_ready`, 13 `excluded`, 2 `failed_retryable`, and
  4 `fidelity_blocked`. The two retryable items belonged to the same
  NCT04963270 artifact and shared the failed document-plan lineage.
- Code inspection proved that the visible `仅重试失败项` path freezes the exact
  failed item IDs, creates a new durable job and a new document-plan lineage,
  and cannot select ready, excluded, or fidelity-blocked rows. Computer Use
  clicked it once.
- Durable job `mwjob_8b3d427d578656d029e468c1` completed once. Only the two
  frozen failed IDs advanced to attempt 2. A new immutable
  `docplan_f3ab93d0fedade2688b7ba6d` and new stage runs were created; all
  other 18 batch items retained attempt 1 and their earlier timestamps.
- The terminal batch is `completed_with_blocked`: 2 `candidate_ready`,
  14 `excluded`, 4 `fidelity_blocked`, 0 failed. No blocked row was rewritten
  or silently admitted.
- Computer Use then clicked `一键确认合格候选（2）` once. Both machine-passed
  candidates became `author_confirmed_admitted`; all four fidelity-blocked
  candidates remained blocked and unadmitted.
- Paddle cutover hardening now includes a durable per-document pin,
  accepted-job outcome-unknown taxonomy, double exclusion from retry/claim,
  conservative restart recovery, 1..4 hosted concurrency bound, 429-only
  capped retry, and invalid-JSONL-page-index fail-closed classification.
  The four focused suites now pass 106 tests; compileall passes.
- The real UI has started one `更新建议` action using the product's independent
  AI. Do not click it again while it remains in progress.

## AI-first design suggestion terminal and recovery hardening — 12:38 CST

- The single Computer Use `更新建议` request completed once through
  `alibaba_token_plan / qwen3.8-max-preview`, AI run
  `mwprefillrun_dcc0f862603b34d78a813d2e`, package
  `mwprefill_c9dda751f902c673a122`, with terminal status `partial`.
- The UI exposed 27 suggested fields but still left 13 key design items for
  user completion. The persisted design scaffold remained empty despite
  21/21 prepared Protocols and the completed 4/4 corpus analysis. This fails
  the AI-first review-only target and is not accepted as product readiness.
- Root cause: the generation and composite-adoption paths built their model
  evidence catalog from framing facts, confirmed Synopsis spans, and registry
  fields only. They did not load the persisted, source-bound round-1 Protocol
  corpus-analysis findings. No second `更新建议` request is allowed before the
  bridge is implemented and accepted in a fresh isolated runtime.
- Tracked execution `mw_ai_first_corpus_prefill_bridge_20260801` was
  initialized through the workflow guard. Source authority, allowed paths,
  fail-closed identity/hash rules, conservative target-path mapping, and
  generation/adoption catalog parity are recorded in its context and prompts.
  Worker 1 was dispatched once through the declared Pi/DeepSeek route and
  remains in the same hard-wait session; there has been no redispatch,
  fixed-interval polling, or fallback.
- The Paddle conference chair returned `READY` for the bounded cutover. Its
  P3 challenge identified a crash window after extraction persistence but
  before preparation-stage completion. A narrow repository replay lookup now
  returns the already-committed extraction before any OCR work when the same
  project/artifact/idempotency key is replayed.
- A deterministic scanned-PDF crash/restart test proves that a GLM-pinned item
  makes exactly one OCR call across the commit-window crash and retry. The
  four focused suites now pass 107 tests; all 17 warnings are the existing
  FastAPI/PyMuPDF deprecation warnings.

## AI-first corpus candidate final clone — 14:23 CST

- The accepted corpus bridge was exercised in four serial disposable clones;
  each clone received exactly one real Computer Use generation action and was
  never retried.
- Runtime counterexamples closed in order: 200-entry projection starvation,
  hidden insufficient-support gaps, and provider nondeterminism.
- The final server contract gives current-project facts first projection
  priority, verified round-1 Protocol findings second priority, and provides a
  deterministic review-only extraction fallback after a successful real
  provider call. It can surface only controlled design terms explicitly
  present in a verified sent quote; it cannot establish current-project facts.
- Final focused suite: 480 passed with 17 baseline warnings; compilation
  passed.
- Final clean clone
  `/tmp/mw-ai-first-prefill-runtime-r4-1eQtHYQD`, API 18915 / Vite 15178:
  one UI click created revision 7, one new generation event, and AI run
  `mwprefillrun_cb543a82aeeea2a345af5ce7`.
- Real UI accepted evidence:
  `竞品Protocol观察：开放标签、随机、平行分组`; exactly those three values are
  non-empty, ten decisions remain blank, the original NCT04735432 Protocol
  quote and seven limitations are visible, and adoption remains disabled.
- Source/clone audit proves all non-target journeys and nine non-authoring
  writing stores are logically identical; the only clone-only event is the
  target generation event. No OCR, translation, triage, preparation,
  admission, or candidate adoption occurred.
- Current status:
  `RUNTIME_CORE_READY / INDEPENDENT_CONTRADICTION_REVIEW_PENDING`.
- Latest OCR rule remains file-bound: future not-yet-started testing files use
  official API `PaddleOCR-VL-1.6`; a file already started with GLM completes
  with GLM. This runtime slice made zero OCR calls.
