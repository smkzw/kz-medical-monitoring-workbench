# Task Context: mw_r39_release_gate

Created: 2026-07-29 22:37:10
Objective: 修复医学写作 r38 结构准入、真实进度和综合AI冻结路由，并启动隔离r39复测
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `kimi-code` / `kimi-code/k3-256k` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/reviews/MW_INDEPENDENT_AI_ROLE_ROUTE_AUDIT_20260729.md`
- `records/execution/mw_final_5x3_release_r38_20260729/ROUND_STATUS.md`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_runtime_settings.py`
- `services/api/app/ai_role_runtime_settings.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_ai_execution_policy.py`
- `tests/test_ai_task_runner.py`
- Current filesystem is authoritative. The workspace is not a Git repository;
  preserve unrelated edits and report every changed path plus before/after SHA-256.

## Scope

- In scope for the delegated execution slice:
  - freeze one complete `independent_ai` route identity at policy resolution:
    profile id/revision, provider, model, transport, base URL, required response
    model, deployment profile, and deterministic identity hash;
  - make the default provider factory construct the provider only from that
    resolution, without a second dynamic route lookup;
  - fail closed if the created provider or returned response model differs from
    the frozen route;
  - persist the full frozen identity and actual response model on `AiTaskRun`;
  - add focused deterministic tests covering dynamic route mutation between
    resolution and provider creation.
- Writable paths for this slice:
  - `services/api/app/ai_execution_policy.py`
  - `services/api/app/ai_task_runner.py`
  - `services/api/app/ai_gateway.py` only if a narrow provider-construction
    adapter is essential;
  - `packages/contracts/workbench_contracts/models.py`
  - `tests/test_ai_execution_policy.py`
  - `tests/test_ai_task_runner.py`
  - new focused test files under `tests/` only when the existing files cannot
    express the regression cleanly.
- Out of scope:
  - `services/api/app/medical_writing.py`;
  - `services/api/app/medical_writing_synopsis_import.py`;
  - OCR, translation, progress, frontend, DOCX, corpus, and 5x3 harness code;
  - production deployment or acceptance claims.

## Success Criteria

- No default `AiTaskRunner` execution performs a second provider/model/profile
  selection after policy resolution.
- A route mutation after resolution cannot silently alter base URL, transport,
  profile revision, expected response model, or actual model.
- `AiTaskRun` contains auditable route identity fields and the provider's actual
  response model.
- Existing provider-injection tests remain supported without weakening
  production fail-closed behavior.
- Focused tests pass and the handoff lists commands, results, uncertainty,
  changed files, and SHA-256 evidence.

## Risk Boundaries

- This is local non-production source work; do not start or mutate a live 5x3
  runtime, role settings, credentials, or external services.
- Do not expose API keys, authentication material, or base URLs containing
  credentials in logs or reports.
- Do not broaden task route policy or add fallback behavior. Unknown or
  mismatched routes must fail closed.
- Do not write outside the explicit writable paths above.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 22:37:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 22:43 CST: Codex re-read global AGENTS, r38 status, and the
  independent-AI route audit. OCR structure recovery and true atomic progress
  fixes already pass focused tests; this delegated slice is limited to the
  generic route-freeze contract so Codex can separately wire chapter and
  Synopsis durable jobs without file overlap.
- 2026-07-29 22:48 CST: Prompt preflight passed with no warnings. Kimi Code
  `kimi-code/k3-256k` high started as the bounded generic route-freeze executor
  under session `27930`; no frequent polling. A separate 5.6-luna-high
  read-only subagent (`019fae52-a912-7730-9ad9-52e7c9f3c174`) is reviewing the
  non-overlapping chapter/Synopsis durable integration. Codex independently
  verified the four-role AI-settings contracts, OCR/M11/preparation progress
  slice (`62 passed`) and frontend production build.
- 2026-07-29 22:52 CST: The first Kimi dispatch failed before creating a model
  session because the runner was given the obsolete bare model token
  `k3-256k`; health check reported `config.invalid` and no tools or files were
  touched. This is dispatch evidence, not an implementation failure. Per the
  global route contract, Codex restarted the same route at max using the exact
  selector `kimi-code/k3-256k`; runner session `86035`, separate retry report,
  no high-frequency polling.
- 2026-07-29 23:18 CST: Targeted UX contract scan found the competitor triage
  already supports one bulk confirmation, but later source preparation,
  extraction, translation admission, shared Phase-I corpus and study-schema
  surfaces still contain per-item confirmation paths. Some are legitimate
  exception/override controls, but the absence of a bulk-accept path for
  automatically passed translation/extraction candidates conflicts with the
  latest "lazy senior medical writer" requirement. This is queued as a
  post-route-freeze P1 UX slice: AI-classify by default, show only material
  differences, allow one bulk confirm for all passed items, and retain
  per-item editing only as an optional drill-down. Do not mix it into the
  generic runner files currently being edited.
- 2026-07-29 23:51 CST: Resume re-anchored against the current global
  `~/.codex/AGENTS.md`, this task context, and the actual runtime/source tree.
  The four independent AI roles are now an explicit release contract, not a
  display-only preference:
  - `independent_ai`, `ocr`, `translation_body`, and `translation_support`
    each own an isolated provider profile, OpenAI-compatible Base URL, model,
    and local credential record;
  - OCR defaults to `GLM-OCR-bf16`; translation defaults to
    `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`; translation support defaults to the
    DeepSeek official `deepseek-v4-flash`; comprehensive AI uses
    `qwen3.8-max-preview` from 22:00 through 08:00 Beijing time and the
    DeepSeek official `deepseek-v4-pro` outside that product window;
  - tester models are independent reviewers and must never replace the
    product's comprehensive AI during research, corpus construction, prefill,
    drafting, or revision;
  - non-specialized OCR models remain allowed only after a real image/vision
    capability probe.
- 2026-07-29 23:51 CST: The release gate now also requires truthful,
  non-black-box progress for every long-running AI/download/OCR/translation
  path. Percentages must be derived from persisted weighted child units
  (study, document, page, chapter, chunk, validation, corpus and writing
  units), remain monotonic, and expose a concise current child label plus
  child percent. Timer-based fake progress and large unexplained jumps are
  release blockers. The UI must keep this compact and task-facing; logs,
  internal hashes, warnings, and routine risk metadata do not occupy the
  writing surface.
- 2026-07-29 23:51 CST: Two disjoint 5.6-luna-high implementation workers were
  dispatched for the remaining frozen-route durability gaps:
  chapter generation/revision (`019fae91-10d3-74c2-bbf3-abf5cffe5a45`) and
  Synopsis import/chunk recovery (`019fae91-349d-7a42-819c-90189936fcb8`).
  Codex will review only route-mutation, cold-recovery, audit-lineage, and
  compatibility risks before focused regression.
- 2026-07-29 23:56 CST: Current product runtime was queried through the public
  status/settings APIs, without reading credentials. The night-window route is
  `independent_ai__alibaba_qwen38 / qwen3.8-max-preview`; translation support
  is DeepSeek official `deepseek-v4-flash`; OCR and body translation are the
  exact local GLM-OCR and Hy-MT2 models. All four roles report
  `execution_binding_consumed=true` and runnable. The shared oMLX gate reports
  OCR 8, translation 8 and combined 16.
- 2026-07-29 23:58 CST: Baseline focused regression passed:
  - AI profile/role isolation, OCR visual admission, generic route freeze,
    OCR structure recovery and preparation progress: `83 passed`;
  - corpus indication-layering, cross-indication transfer restrictions,
    sparse-evidence anti-generalization and AI prefill evidence binding:
    `177 passed`.
  The corpus prompt already implements indication/phase/objective/modality/
  formulation/route/design layering, sponsor diversity and conflict
  preservation; no second speculative rewrite was made.
- 2026-07-29 23:59 CST: The 5x3 config is structurally present with 15 unique
  non-oncology indications, but validation correctly fails closed because the
  r38 source fingerprints no longer match the r39 OCR/progress/route files.
  Re-freeze only after all r39 code and frontend changes pass regression; never
  weaken or override the source-drift gate.
- 2026-07-30 00:18 CST: The generic comprehensive-AI route-freeze executor and
  the three disjoint integration slices have returned and were reviewed at
  their shared trust boundary rather than accepted by agent confidence:
  - the generic runner resolves one complete profile identity and constructs
    the provider from that frozen resolution; provider identity and actual
    response model are checked, and the credential-free route snapshot is
    exposed through one canonical resolver method;
  - chapter generation/rewrite persists the complete snapshot in generation
    context, validates it at creation/pre-AI/pre-commit, and compares the
    resulting `AiTaskRun.route_identity_hash` before any revision thread or
    audit commit;
  - Synopsis import persists the parent snapshot/hash, binds every chunk to the
    same hash, rejects mixed-route merge, and treats missing/changed route
    identity during cold recovery as a non-retryable failure;
  - the research pipeline now projects persisted study/chunk, document/page,
    translation chapter and corpus-analysis units into monotonic parent/child
    progress; failed or waiting states do not fabricate completion.
- 2026-07-30 00:18 CST: Codex focused regression results:
  - chapter generation/revision context and progress: `76 passed`;
  - Synopsis import route/cold-recovery/merge: `33 passed`;
  - research pipeline and compact waiting/progress UI: `22 passed`;
  - generic route freeze plus four-role settings/visual OCR admission:
    `27 passed`.
  The apparent duplicate `_project_stage_percent` call in one truncated tool
  transcript was disproved by a numbered source read; no speculative edit was
  made. FastAPI `on_event` deprecation warnings remain unrelated to this gate.
- 2026-07-30 00:18 CST: Residual route behavior is explicit. If a long durable
  job reaches a later chunk after the active comprehensive-AI profile changes,
  the current chapter/Synopsis integrations fail closed instead of silently
  mixing models. This preserves evidence and audit identity but may require a
  user-visible retry/new attempt at the new profile. The first isolated r39
  runtime must verify that this recovery experience is acceptable; no fallback
  or route mixing may be added to hide the condition.
- 2026-07-30 00:18 CST: Current authoritative SHA-256 evidence:
  - `ai_execution_policy.py`:
    `c3235a0fce53b3b26e3c93a6ad7b08cf79bf6345e193815aa606de95ccc1e324`
  - `ai_task_runner.py`:
    `771535965af185685d8b972cbd299260435ec5426452a72c618ad6f4848c9b15`
  - `ai_gateway.py`:
    `a4170e329d595e2dd788aaf3f01899f2516b4667e0f85e75734bf9f0ef41f9a3`
  - `models.py`:
    `15779607e2cad2e95d4ed7ea89575ca200d8ae512e250d4e85777e304e36e2d1`
  - `medical_writing.py`:
    `2253d0a256c914a76ff0c939fa9c219f87e54ef020c26c9d57e5a1e6cf8478c7`
  - `medical_writing_synopsis_import.py`:
    `570f88f5841d81b47271fb916a7dc266775c260c019b59ad69a41ddd0ace565f`
  - `medical_writing_research_pipeline.py`:
    `432268115bcecde54beba8652d465b516206f9ee0d376b6d0820ea8a5b9b99b8`
  - `MedicalWritingAuthoringJourneySetup.jsx`:
    `c7c9cdf90db78cb543a270e84536f270b26d5d379420c4955be071a89072bac4`
  - `ReferencePreparationBatchPanel.jsx`:
    `bdaf726cf295461fe8e3724cdeab150965cb7e6843edaaedbd8c4f4ed2174545`
- 2026-07-30 00:25 CST: Expanded propagation regression initially produced
  `860 passed / 18 failed`. All 18 failures were stale test fixtures that did
  not yet satisfy the new frozen-route contract: one gateway assertion
  expected a mismatched actual response model to be discarded, three
  direct-SQL Synopsis merge fixtures omitted parent/chunk route hashes, and
  fourteen async fake runners omitted route snapshots/run hashes. The test
  fixtures were upgraded to provide a complete credential-free fake identity;
  production fail-closed code was not weakened. One quote typo introduced
  while updating the test call was caught at collection, corrected, and is
  retained as test-maintenance evidence rather than a product defect.
- 2026-07-30 00:25 CST: The exact expanded suite then passed:
  `878 passed, 15 warnings in 117.38s`. The frontend production build also
  passed (`1903 modules transformed`); only the pre-existing Vite large-chunk
  advisory remains. The three updated legacy-fixture files are:
  `tests/test_ai_gateway.py`,
  `tests/test_medical_writing_synopsis_merge_integrity.py`, and
  `tests/test_synopsis_async_real_chunks.py`.
- 2026-07-30 00:27 CST: The final 5x3 source-drift gate was re-frozen by an
  explicit allowlist, not a blanket hash refresh. Thirteen reviewed changed
  receipts were updated, and fifteen previously unlocked core route/chapter/
  Synopsis/OCR/progress implementation and test surfaces were added. The
  matrix now locks 101 authoritative sources. Validation result:
  `VALID / 5 testers / 15 slots / 15 unique indications`; harness/runtime
  contract regression: `48 passed`. Matrix SHA-256:
  `56c8955653046eaa68a8b109140841906114e44258eb2d5a6983dbaa1246ad1e`.
- 2026-07-30 00:29 CST: A new preparation-only round was created:
  `release-r39-20260730`, input fingerprint
  `f857ab2debff6ed3e7bca2a7329d5754238b6dc34652e0f523809fb298e0f3af`.
  It has a new runtime/database/frontend snapshot and does not reuse any r38
  COPD project, candidate, source, corpus, working copy or export. A1
  `lazy_medical_writer` services are running at backend `127.0.0.1:55202` and
  frontend `127.0.0.1:55203`; runtime identity
  `4eea7af6ee1b29aef0cc8a81356074a14b178ce7e2554bdaa4d80420d29d3f96`.
  The public product status endpoint confirms the comprehensive AI is
  `alibaba_token_plan / qwen3.8-max-preview`, with no Codex runtime dependency.
  OCR is `GLM-OCR-bf16`, body translation is exact Hy-MT2, and translation
  support is DeepSeek official `deepseek-v4-flash`; all four roles are wired
  and runnable.
- 2026-07-30 00:30 CST: External tester A1 lazy was dispatched as exact
  `gpt-5.6-luna / high`, agent
  `019faeab-01d9-77a2-a0cc-9b448fd9bb1b`. It must use visible desktop controls,
  enter only minimum COPD III inhaled fixed-combination facts, keep tester and
  product AI identities separate, and write all evidence under
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r39-20260730/slots/A1/lazy_medical_writer/`.
  It may not change source, use API/database/DOM actions for product decisions,
  paste tester-authored medical content, use corpus override, or create
  `PASS.md`. Polling remains deliberately sparse.
- 2026-07-30 02:36 CST: A1 `lazy_medical_writer` stopped correctly at a
  reproducible product blocker and did not modify source or create `PASS.md`.
  The real product path searched 665 studies, AI-classified all candidates,
  retained 53 studies, prepared 99 public Protocol/SAP documents and reached
  persisted preparation progress `99/99 · 100%`. It then remained at
  `awaiting_document_validation / 58%` and did not unlock design/PICOS.
  Evidence is preserved in
  `rounds/release-r39-20260730/slots/A1/lazy_medical_writer/DEFECTS.md`,
  `FIX_RETEST_LEDGER.md`, the browser trace and original-resolution screenshot.
- 2026-07-30 02:42 CST: Codex reproduced the backend state with the required
  API contract header and isolated the single exception. Of 99 documents,
  99 basic content validations were already `confirmed`, 98 structure reviews
  were approved, and only `NCT02727660 / Prot_000.pdf` lacked an ICH M11
  chapter anchor. The state machine incorrectly promoted that one
  corpus-unusable document to a project-wide human content-validation gate;
  its displayed override instruction was impossible because content override
  cannot create structure anchors.
- 2026-07-30 02:50 CST: The bounded repair changes public-document admission
  semantics only. When at least one clean public document remains, document
  exceptions are retained as `document_admission_exclusions` and do not hold
  the corpus hostage. Structure-anchor/review failures are always exclusions,
  not content-override requests. Content conflicts still fail closed when no
  clean public source remains. If no document is structurally usable, the
  pipeline moves to `awaiting_translation_scope`, not the misleading content
  validation stage. The frontend shows exclusions as a collapsed one-line
  summary with traceable reasons rather than a warning card or per-item
  confirmation queue. Focused regression after the repair: `34 passed`.
- 2026-07-30 03:18 CST: A repository-wide `/usr/bin/python3 -m pytest -q`
  completed `5006 passed / 18 failed`. The first attempted bare `pytest`
  resolved to an unrelated Homebrew Python 3.12 and failed collection for
  missing dependencies; no package was installed and the authoritative rerun
  used the same Python 3.9 environment as the isolated product runtime.
  The 18 completed-suite failures were triaged rather than treated as one
  product regression:
  - medical-monitoring/project-catalog fixture drift accounted for the
    unrelated RUX/MY009/inbox/monitoring failures;
  - four writing tests had stale exact-shape fixtures after earlier persisted
    progress enrichment;
  - one writing test exposed a real bootstrap issue: generic server defaults
    such as `随机、双盲` were being counted as user-confirmed framing.
- 2026-07-30 03:24 CST: The writing bootstrap now stores only the user's
  minimum three facts (investigational product, indication, phase) as confirmed
  at project creation. It no longer fabricates generic population, design or
  objective fields and no longer marks stage 1 complete before the independent
  AI research/prefill plus user adoption. `effective_authoring_values` now
  safely reads typed states and test doubles. OCR page progress now derives
  `unit_type` and `current_substep_percent` from the active persisted batch
  progress when item-local progress is absent.
- 2026-07-30 03:32 CST: Targeted writing/state/progress regression:
  `65 passed`. Expanded launch-relevant writing suite:
  `2898 passed, 17 warnings in 359.19s`. Frontend production build:
  `1903 modules transformed`, successful; the only warning remains the
  pre-existing large Vite chunk advisory. No r40 source freeze or runtime is
  created until the delta-only independent review returns.
- 2026-07-30 post-review: Delta-only independent reviewer
  `019faf4c-1eba-7951-831a-0d269ee869b4` found no P0/P1 blocker and isolated
  two P2 risks. Both are now repaired without broadening the UI:
  - legacy/narrow journey draft objects and absent framing/PICOS paths return
    confirmed values or `None` instead of raising an attribute error;
  - non-blocking public-document exclusions remain collapsed, but their
    expanded view now preserves the validation check label plus observed and
    project-expected values.
  Mixed clean-plus-mismatched source coverage proves that a mismatch remains a
  traceable corpus exclusion while the clean document proceeds. Focused
  regression: `53 passed`; frontend production build: successful.
- 2026-07-30 post-review: The expanded launch-relevant writing suite passed
  `2901 passed, 17 warnings in 366.84s`. The warnings are unchanged FastAPI
  lifecycle and SWIG deprecations. The final-5x3 harness/runtime contract
  regression passed `48 passed`.
- 2026-07-30 post-review: The source freeze was updated by explicit reviewed
  receipts only. It now also locks
  `test_medical_writing_research_pipeline_validation_gate.py` and
  `test_medical_writing_authoring_prefill.py`. Concurrent medical-monitoring
  drift in shared `models.py`, `App.jsx`, and `styles.css` was not attributed
  to this writing repair; it was accepted only after the complete 2901-test
  writing suite and frontend production build passed against that exact state.
  Matrix validation is `VALID / 5 testers / 15 slots / 15 unique indications`;
  matrix SHA-256:
  `fad03bdd861fe69c052a452ff2ac40be4038a5f792da58b5dc8acb13ba631db0`.
- 2026-07-30 r40: A new preparation-only round
  `release-r40-20260730` was created from the reviewed freeze; input
  fingerprint:
  `38b3e7fc94573c4e82aed0cce9af399c36e14b3c7dd356f6bbad6b7396ee2fdd`.
  A1 `lazy_medical_writer` is running from a new isolated runtime at backend
  `127.0.0.1:55212` and frontend `127.0.0.1:55213`; runtime identity:
  `5654bdf758fd8abb9a2c0ac1b8f2c7668df714f098500acdb25d7cb755fe734b`.
  The clean-state receipt was verified before the immutable frontend started.
  The product comprehensive AI is independently configured as
  `alibaba_token_plan / qwen3.8-max-preview`; OCR is `GLM-OCR-bf16`, body
  translation is exact Hy-MT2, and translation support is DeepSeek official
  `deepseek-v4-flash`.
- 2026-07-30 r40: Tester A1 lazy was dispatched as
  `gpt-5.6-luna / high`, agent
  `019faf5d-7b15-7820-ba53-477c1d14c579`. It must use only visible browser
  controls, create a fresh COPD III inhaled fixed-combination project from the
  minimum three facts, and continue through the product's own independent-AI
  workflow. It may not modify source, use API/database/DOM shortcuts, paste
  tester-authored medical content, use corpus override, or create acceptance
  evidence without completing the locked contract. The primary repair target
  is the former 99/99 documents, one no-anchor file, 58% validation deadlock.
- 2026-07-30 r40 A1 outcome: The same fresh project completed independent-AI
  triage (`665/665`, retained `54`) and one bulk confirmation, then visibly
  advanced through real document/substep progress to `99/100`. It did not
  reach document admission. After the last observed SAP completed validation,
  the parent pipeline failed. A1 evidence is preserved under
  `rounds/release-r40-20260730/slots/A1/lazy_medical_writer/`, including action
  trace through seq 108 and original-resolution screenshots 074-077. No
  `PASS.md` was created.
- 2026-07-30 r40 diagnosis: The visible secondary message
  `latest writing-reference preparation batch is not terminal` was a
  consequence, not the root cause. The persisted pipeline error is
  `UnboundLocalError: local variable 'substep' referenced before assignment`.
  All 100 preparation items were already `prepared`, with zero pending,
  running, failed, or review-required items and persisted batch progress
  `completed / 100/100 / 100%`; the batch row alone remained `running`.
  `_run_items` emits one progress callback after the last item and before its
  final batch-status refresh. At that exact terminalization window,
  `_preparation_progress_projection` had no `current` item but still referenced
  `substep`, which had only been assigned inside the current-item branch. The
  callback exception prevented the final `running -> completed` status write.
- 2026-07-30 r40 bounded repair: `_preparation_progress_projection` now
  initializes the substep from durable batch progress before selecting a
  current item. When all documents are terminal (`completed >= total`), it
  reports `原文准备已完成` even during the short pre-refresh `running` window.
  A regression reproduces the exact two-prepared-items/status-running/
  completed-progress shape. Focused pipeline regression: `50 passed`.
  Expanded launch-relevant writing regression: `2902 passed, 17 warnings in
  366.43s`; frontend production build passed. r40 services were then stopped
  cleanly and both ports released. A delta-only independent review was
  dispatched before any r41 freeze.
- 2026-07-30 r40 independent review and service hardening: Delta-only reviewer
  `019fafe0-c42f-7353-96a3-3ba872625063` confirmed that the projection repair
  covers the reproduced last-item terminalization window and found no adjacent
  uninitialized progress variable. It identified one P1 service-layer
  residual: any future progress-observer exception could still skip the final
  batch-status refresh. `WritingReferencePreparationBatchService._emit_progress`
  now isolates and logs observer failures because progress projection is
  non-authoritative and must not strand durable source processing. A real
  service integration regression raises from the callback after the last item
  but before refresh and proves that the batch still reaches
  `completed_with_review_required`, with zero pending/running items. Targeted
  regression: `73 passed, 17 warnings`. Expanded launch-relevant writing
  regression against the exact concurrent source state:
  `2903 passed, 17 warnings in 359.43s`; frontend production build passed
  (`1908 modules transformed`, existing large-chunk advisory only).
- 2026-07-30 r41 pre-freeze: The seven drifted receipts were updated only after
  the preceding regression evidence. Concurrent medical-monitoring changes in
  shared `main.py`, `App.jsx`, and `styles.css` remain preserved and are
  accepted here only as the exact state covered by the writing regression and
  build; they are not attributed to the writing repair. Matrix validation is
  `VALID / 5 testers / 15 slots / 15 unique indications`; harness/runtime
  contract regression is `48 passed`. New matrix SHA-256:
  `bd282d611c2da2990bd0b09a497a76cc118f7f5466c3f90587398250cebf49b4`.
  The r40 runtime remains `STOPPED` with both receipt process identities absent.
- 2026-07-30 r41: A new preparation-only round
  `release-r41-20260730` was created from that reviewed freeze; input
  fingerprint:
  `27fecd64e95146aee510bbb621b2aa529b54755b4dd1c56f01237dbdb3030cd1`.
  A1 `lazy_medical_writer` is running from a new isolated runtime at backend
  `127.0.0.1:55222` and frontend `127.0.0.1:55223`; runtime identity:
  `2be9ac31ef17fba3dd2139eedcb36e4cfd98bc0d1c64f3950a5a9eb41ae80292`.
  Clean state was verified before the immutable frontend started. Direct
  health reports SQLite integrity `ok`, zero foreign-key violations, and an
  18-item shared corpus. The product routes are independently runnable:
  comprehensive AI `alibaba_token_plan / qwen3.8-max-preview`, OCR
  `GLM-OCR-bf16`, body translation exact
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`, and translation support DeepSeek
  official `deepseek-v4-flash`. The workload gate reports
  OCR `8`, translation `8`, combined `16`.
- 2026-07-30 r41 A1 dispatch: Fresh tester
  `019fafee-99ee-7530-9478-e1b3cc4cbf80` (`gpt-5.6-luna / high`) was assigned
  the COPD III fixed-dose inhaled-combination greenfield scenario. It must use
  only visible browser controls, enter only product/indication/phase, use the
  product's real independent-AI path, avoid API/database/DOM/source shortcuts
  and corpus override, poll long operations sparsely, and continue toward the
  full protocol and DOCX acceptance points. The first locked recheck is that
  the final preparation item can no longer strand a `running` batch and that
  unusable documents remain collapsed traceable exclusions while usable
  evidence continues.
- 2026-07-30 06:50 CST user-requested no-loss pause: A1 created only the
  minimum-fact project `MW-III-E88B5113` and reached visible competitor triage
  `14/19 / 74%`, with `644/665` suggestions returned and current object
  `ct_chunk_7607054613471764b872`. The basket remains disabled until full
  return. This is neither PASS nor a confirmed product defect. The independent
  API and immutable frontend remain intentionally running on ports
  `55222/55223`; receipt PIDs `91379/91401` and listener identities match,
  API/SQLite/corpus health is `ok`, and the browser state is preserved. Do not
  restart triage or create another project on resume; first read the latest
  persisted page state because background triage may continue during the
  pause. The complete recovery contract is:
  `records/handoffs/CODEX_SOFT_PAUSE_R41_A1_20260730.md`.
- 2026-07-30 r41 resumed diagnosis and repair: the persisted retry job and
  parent research pipeline both reached 19/19 while only the outer authoring
  toolbar/banner remained at 17/19. The defect was isolated to a missing
  drawer-to-parent status propagation path, not backend triage completion.
  Hermes/aishuo/cms-model session `20260730_083026_a3ef67` implemented the
  bounded callback chain; Codex accepted the data boundary after `26` focused
  and `175` broader frontend contract tests plus a successful production
  build. A mixed hot-reload frontend against the old r41 backend was correctly
  rejected by the runtime contract, so r41 remains immutable FAIL evidence.
- 2026-07-30 r42 pre-freeze full-workspace regression: the exact concurrent
  source completed `5142 passed / 9 failed / 29 warnings in 1317.47s`.
  All writing-status synchronization and medical-writing frontend tests passed.
  The nine failures are confined to concurrently changed monitoring project
  catalog/risk seed assumptions and two monitoring-button explanation
  contracts; they are recorded as shared monitoring residuals and were not
  repaired from the writing slice. The five drifted shared/writing source
  hashes and the new triage-propagation regression hash were then updated in
  the fail-closed 5x3 matrix before preparing r42.
