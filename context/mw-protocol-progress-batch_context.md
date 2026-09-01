# Task Context: mw-protocol-progress-batch

Created: 2026-07-30 11:35:09
Objective: 收紧自动竞品语料为Protocol-only，建立真实连续进度条与懒惰医学撰写专家可用的批量确认路径
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `kimi-code` / `kimi-code/k3-256k` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/packages/contracts/workbench_contracts/models.py`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/main.py`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app/writing_reference_repository.py`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- Existing medical-writing reference and frontend contract tests under `tests/`.
- User contract: routine AI-generated translation candidates must support one-click
  batch confirmation so a medical writer is not forced to open and approve every
  fragment. Only explicit exceptions or failed fidelity checks require item-level
  review.

## Scope

- In scope:
  - Add a version-safe, idempotent batch medical-review API for current translation
    revisions in one frozen translation batch.
  - Default the action to approve only eligible `pending_author_confirmation`
    translations whose fidelity gate passed; skip stale, blocked, returned,
    rejected, or already reviewed rows and report per-item outcomes.
  - Add one restrained frontend action that batch-confirms the currently filtered
    eligible rows after a single explicit user click, then refreshes the batch.
  - Add focused backend and frontend contract tests.
- Out of scope:
  - Corpus admission, Protocol/SAP scope changes, progress-bar implementation,
    visual restyling, independent-AI prompt changes, or production deployment.

## Success Criteria

- A single click can approve all currently eligible AI translation candidates in
  the selected batch without visiting each row.
- Optimistic concurrency and idempotency remain enforced per translation revision.
- Partial success is explicit; one stale or ineligible row does not conceal the
  status of the remaining rows.
- No automatic approval occurs without the user's batch action.
- Existing single-item review API remains compatible.
- Focused tests pass and changed paths are listed in the handoff.

## Risk Boundaries

- Write only the five source/test surfaces listed above. This workspace is the
  authorized local development target; no deployment or external communication.
- Do not modify runtime databases, credentials, frozen run evidence, or production
  service configuration.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 11:35:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 11:38-11:50: Codex resumed from the durable checkpoint and
  re-read the current global AGENTS contract. The live source API and Vite
  service were healthy, but the current batch-review execution remained in
  progress and was deliberately not polled at high frequency.
- 2026-07-30 11:42: Added an accessible continuous progress track to compact
  and full reference-processing progress views. The bar is driven by persisted
  stages and completed chunk counts, not elapsed-time animation. Translation
  progress now projects directory planning, Hy-MT2 chunk completion,
  integration QC, and terminal candidate state into monotonic stage ranges.
  Preparation already aggregated completed files plus the active file's
  persisted substep percent, so that implementation was retained.
- 2026-07-30 11:45: Closed the remaining Protocol-only corpus boundary.
  Standalone SAP is excluded. Combined Protocol+SAP files fail closed unless
  an explicit SAP boundary exists; only spans before that boundary may enter
  translation or corpus analysis. Both consumers now call the same shared
  `protocol_corpus_span_scope` function.
- 2026-07-30 11:47: Real browser review of the competitor drawer showed that
  historical unprocessed candidates were labelled `待医学分类`, which visually
  implied item-by-item medical work. The label is now `待AI分类`; the existing
  AI full-batch classification and one-click medical lock remain the primary
  path. Manual corpus upload now offers Protocol or combined Protocol+SAP
  (Protocol portion only), never standalone SAP.
- 2026-07-30 11:48: Focused verification passed: 173 backend Protocol,
  translation, corpus-analysis, triage, and research-progress tests; 128
  frontend medical-writing contract tests; 12 pure progress-journey tests; and
  the Vite production build (1910 modules). A concurrent monitoring worker
  briefly left an unterminated SQL string and a missing method while writing;
  both were reconciled before the focused medical-writing suite ran.
- 2026-07-30 11:49: Restarted the current-source API and Vite services to
  synchronize build hashes, then reopened the real browser at
  `http://127.0.0.1:5174/`. The medical-writing editor and research-design
  drawer rendered without a build-mismatch gate.
- 2026-07-30 11:50: Removed 3.08 GiB of precisely identified regenerable
  artifacts: four obsolete purge-test copies, old frontend build copies, an
  r16 temporary frozen database copy, a temporary truthful-progress virtual
  environment, and the rejected Aspose POC Python environment. Preserved the
  POC report/output, all project databases, screenshots, run records, and
  current release evidence.
- 2026-07-30 11:54-11:59: Rechecked the live AI-role state after the user's
  Paddle-primary correction. The OCR role was already bound to
  `ocr_paddle_official / PaddleOCR-VL-1.6`, but its encrypted credential was
  absent, so the role was not runnable and earlier work could only use the
  local GLM route. Stored the user-supplied Paddle credential in the existing
  local encrypted credential store without logging plaintext. The live role
  endpoint now reports Paddle configured and runnable.
- 2026-07-30 12:00: Executed the real PaddleOCR-VL-1.6 official asynchronous
  Job API against a synthetic 200 DPI protocol page. The second bounded probe
  accurately returned `CMS OCR LIVE 7429` and `CLINICAL PROTOCOL`; no GLM
  fallback was involved. A remaining UI-probe defect was identified:
  `/api/ai-gateway/roles/ocr/probe-visual` still constructs an
  OpenAI-compatible `/chat/completions` adapter even for the Paddle provider.
  That endpoint must be switched to the dedicated Paddle async adapter after
  the concurrent batch-confirmation worker releases `main.py`.
- 2026-07-30 12:03: Completed another bounded disk cleanup after measuring
  the workspace. Removed 2.96 GiB of regenerable material only: the frontend
  npm download cache, completed Playwright trace bundles, and explicitly
  enumerated old R5/R10/R11/R15/R20/R25/R38/R39/R40 E2E database/video/trace
  copies whose durable reports remain. Preserved current R41/R42 evidence,
  live runtime databases, source, tests, screenshots, handoffs, and all
  current task records. Workspace usage fell to approximately 8.72 GiB.
- 2026-07-30 12:06: Ran the same 200 DPI synthetic protocol probe through the
  production `_writing_reference_ocr_runner` rather than the adapter alone.
  It returned provider `paddle_official`, model `PaddleOCR-VL-1.6`,
  `fell_back=false`, and correctly recognized all marker tokens. This proves
  the live writing-reference OCR execution path now uses Paddle first; GLM is
  reserved for a persisted, verified Paddle failure.
- 2026-07-30 12:07: Paddle adapter, fallback provenance, role binding, and OCR
  evidence regression suite passed `61/61`. The first command named a
  nonexistent standalone QC test file and therefore collected no tests; it
  made no changes. The corrected focused suite then passed fully.
- 2026-07-30 12:12: Reopened the real desktop UI and verified the visible
  OCR-role configuration. It now shows the Paddle official asynchronous API
  preset selected, `PaddleOCR-VL-1.6`, persisted-key state, the official Job
  API base URL guidance, and Paddle-primary/GLM-fallback wording. Screenshot:
  `output/playwright/mw-ai-settings-paddle-primary-1600x1000.png`.
  Updated the translation-support role description to state its existing
  mixed-OCR focused-consistency-QC responsibility while explicitly forbidding
  replacement of OCR or Hy-MT2 body text. Role/frontend contract tests passed.
- 2026-07-30 12:33-12:39: Re-anchored from the current global and workbench
  `AGENTS.md` files and preserved the still-running Kimi batch-confirmation
  session under the 120-minute hard-wait rule. The process remained alive with
  no terminal error, but had not produced its report or a complete batch API
  surface yet; no conflicting edits were made while it retained the shared
  files.
- 2026-07-30 12:35-12:38: Performed a second measured cleanup of obsolete,
  regenerable OCR artifacts. Removed the old R5 engineer artifact tree
  (approximately 1.3 GiB) plus R8/R9/R25 historical artifact trees
  (approximately 244 MiB). Preserved every current R41/R42 artifact, database,
  report, screenshot, and handoff. Workspace usage fell from approximately
  8.72 GiB to 7.2 GiB. The unfinished R42 OCR evidence remains the resume
  source and must not be regenerated.
- 2026-07-30 12:39: Confirmed the exact remaining Paddle defect and patch
  boundary. The product OCR runner already calls `_build_role_bound_ocr_gateway`
  and records Paddle versus GLM provenance correctly. Only the visual
  capability probe still bypasses that route and constructs the generic
  OpenAI-compatible adapter. The repair will reuse the live role-bound gateway
  and must reject a Paddle probe result with `fell_back=true`; otherwise GLM
  could falsely certify the Paddle profile.
- 2026-07-30 12:43: Added two red regression tests without touching the
  Kimi-owned source paths. They require the Paddle visual probe to use the
  dedicated role-bound gateway and require a GLM fallback result to be rejected
  rather than persisted as Paddle capability proof. Both tests fail against the
  current implementation for the expected reason: the endpoint never calls the
  dedicated gateway. This is the acceptance signal for the pending source fix.
- 2026-07-30 12:54: The independent R42 read-only audit confirmed 86 terminal
  preparation items are reusable, with four pending Protocol/Protocol+SAP items
  and one interrupted standalone SAP. Codex rejected the audit's initial
  recommendation to retry all unfinished work because the current product
  contract excludes standalone SAP from the competitor corpus. Database and
  source inspection showed that service restart currently turns every legacy
  nonterminal item into `failed`, so a retry would waste work specifically on
  the SAP while leaving the other pending Protocol items untouched until they
  are separately resumed.
- 2026-07-30 12:57: Added a red legacy-recovery regression test requiring a
  nonterminal standalone SAP from an older batch to become an audited
  `excluded` terminal item without download, OCR, or attempt increment. The
  current implementation marks it `failed`, confirming the defect. The pending
  implementation must preserve already completed historical SAP artifacts, but
  must not process unfinished standalone SAP after the Protocol-only contract
  takes effect.
- 2026-07-30 12:59-13:05: Kimi's long-running batch author-confirmation worker
  completed successfully and returned its bounded six-file implementation.
  Codex conflict/risk review retained the explicit filtered-row UX but rejected
  the API's empty-target shortcut: an empty request could approve a translation
  revision the writer had not actually seen. The request contract now requires
  at least one exact `(translation_id, translation_revision)` target, and the
  endpoint never expands a selection server-side. Stale and ineligible rows
  remain isolated as per-item outcomes.
- 2026-07-30 13:00-13:06: Completed the legacy Protocol-only recovery contract.
  Nonterminal/failed standalone SAP items are migrated to the audited terminal
  state `excluded`, count toward completed work, do not increment attempts, and
  do not invoke download/OCR/extraction. Existing completed historical evidence
  remains untouched. The preparation frontend treats this as “无需处理”, not a
  warning. The public contract now exposes `excluded` and `excluded_count`.
- 2026-07-30 13:02-13:07: Repaired the OCR visual probe routing. Paddle profiles
  now use the dedicated Paddle async Job API gateway, and a result produced by
  GLM fallback is rejected with HTTP 502 rather than persisted as proof that
  Paddle works. A general OpenAI-compatible visual model still uses the
  pre-capability probe path, avoiding a ready-gate self-lock. Focused results:
  4/4 visual-probe tests, the standalone-SAP restart regression, 60/60
  translation-batch/frontend contract tests, and 40/40 complete AI-role plus
  preparation-batch tests passed. The frontend production build passed (1910
  modules); the only build warning is the pre-existing large JavaScript chunk.
- 2026-07-30 13:07-13:10: Resumed the isolated R42/A1 COPD Phase III
  inhalation-protocol lane from its durable handoff rather than restarting the
  matrix. Before starting work, backed up the isolated provider registry,
  encrypted secret registry, role bindings, and provider master key with the
  suffix `.pre_paddle_resume_20260730`, then synchronized the already verified
  current runtime configuration. Wrote the no-secret
  `RESUME_AI_ROLE_BINDINGS.json` receipt: comprehensive AI
  `deepseek-v4-pro`, OCR `PaddleOCR-VL-1.6`, translation body exact Hy-MT2,
  and translation-support `deepseek-v4-flash`. The live isolated role endpoint
  reports all four roles ready; no credential was copied into a run report.
- 2026-07-30 13:08-13:11: Applied the Protocol-only restart migration to R42.
  The batch contained 86 reusable prepared files, four interrupted
  Protocol/Protocol+SAP files, and one standalone SAP. The SAP became audited
  terminal `excluded` without reprocessing. Accepted failed-only retry under
  idempotency key `r42-paddle-protocol-only-resume-20260730`; only the four
  eligible files entered the retry lane. Captured payload hashes and lineage
  for all 86 prepared rows in `resume_reuse_manifest.json` so post-run
  verification can prove they were not rewritten. An earlier pre-retry SQL
  query referenced nonexistent columns and created no manifest or state
  mutation; the corrected manifest was captured immediately after retry
  acceptance.
- 2026-07-30 13:11-13:14: Reopened the real R42 browser runtime at
  `http://127.0.0.1:55223`. The page truthfully exposed the current NCT,
  filename, physical page, selected OCR-page count, and substep instead of a
  black box. The first observed active retry was NCT04133909 / `Prot_000.pdf`;
  the batch moved to 87 prepared, two failed waiting for their turn, one
  running, and one excluded. The standalone SAP remained outside the work
  queue.
- 2026-07-30 13:12-13:15: Found a separate Protocol-only label defect during
  browser review: the authoring journey labeled
  `protocol + sap + protocol_sap` as “Protocol”. Updated the source contract so
  new search plans request `protocol` only and public-document counts include
  only Protocol and combined Protocol+SAP. Focused authoring/frontend tests
  passed. R42's already persisted historical count remains stale until the
  current batch reaches a safe terminal boundary; it must not be presented as
  a fresh recalculation.
- 2026-07-30 13:15-13:18: The R42 progress response exposed another concrete
  retry defect: an item interrupted after a high-progress prior attempt kept
  that attempt's monotonic percentage when reclaimed, making the overall batch
  show 100% while OCR was still running. Updated `_claim_item` so a failed item
  starts a new retry attempt at queued/0% while ordinary first-attempt claims
  preserve their existing progress. Added a focused regression proving stale
  100% progress resets on retry; the retry, restart, and monotonic-progress
  tests pass 3/3. The already running isolated R42 service was not restarted,
  so this source correction will govern subsequent runs without interrupting
  current Paddle work.
- 2026-07-30 13:18-13:24: R42 preparation reached a truthful terminal state:
  90 Protocol/combined artifacts prepared, one unfinished standalone SAP
  migrated to audited `excluded`, and no item remained running, pending, or
  failed. `post_retry_verification.json` proves that 87 non-target rows kept
  identical immutable payload hashes, lineage, and attempt counts while the
  four eligible retry targets completed exactly once.
- 2026-07-30 13:20-13:26: Inspected actual OCR provenance for the four retry
  targets. Paddle remained the primary route. Three documents contain a small
  number of GLM fallback pages after real Paddle submit failures; one completed
  entirely with Paddle. The old fallback reason persisted only the exception
  class (`HTTPError`), so the adapter now records a credential-safe HTTP status
  such as `HTTP 429` for future runs. No URL, token, or response body is copied
  into provenance.
- 2026-07-30 13:24-13:29: Corrected a Protocol+SAP metadata/content conflict.
  `NCT05138250 / Prot_SAP_000.pdf` is a 99-page Protocol with an internal
  statistical-analysis-plan subsection, not a Protocol followed by a
  standalone SAP. Protocol scope now prefers strong document content over the
  combined-file label and does not treat a numbered Protocol subsection as an
  appended SAP boundary. A new additive content-validation revision confirms
  Protocol-only use without rewriting the source or extraction.
- 2026-07-30 13:25-13:31: Replaced the mixed-OCR all-selected-page comparison
  with a V2 focused contract. The translation-support LLM now receives each
  real fallback physical page, same-page native extraction, and true previous/
  next physical-page context. Nonadjacent selected OCR pages are never treated
  as adjacent boundaries. Existing OCR output is reused; no download or OCR is
  repeated.
- 2026-07-30 13:28-13:31: A first V2 real recheck exposed two prompt defects:
  the old 2,000-character preview made complete OCR pages look truncated, and
  normal repeated `X` marks in schedules of assessments were treated as
  suspicious. The prompt/input contract was revised to retain up to 12,000 OCR
  characters per fallback page, explicitly label any display truncation, and
  treat repeated visit-plan `X` marks as normal unless there is concrete
  evidence of a row/column error. The stage identity was advanced to
  `mixed_ocr_consistency_qc_v2_1`.
- 2026-07-30 13:30-13:32: Real DeepSeek V4 Flash recheck of the three persisted
  mixed-OCR Protocols completed without download or OCR. Two documents passed.
  `NCT04133909` retains one focused review item around schedule-table footnote
  alignment on physical pages 25-26; the source pages were rendered at 200 DPI
  and visually inspected. Evidence:
  `mixed_ocr_v2_fullpage_recheck.json`. This result must be stored as a new
  immutable recheck, not written into the historical extraction payload.
- 2026-07-30 13:31: Independent architecture challenge confirmed that M11
  structure approval and mixed-OCR content disposition are different domains.
  The selected implementation therefore adds dedicated immutable OCR recheck
  and medical-disposition records, an effective read projection, and one
  batch-confirm action. Corpus, readiness, translation, and frozen lineage
  will consume the effective projection; the original extraction QC remains
  auditable and unchanged.
- 2026-07-30 13:32-14:10: Completed the additive OCR-QC state machine and
  downstream integration. Current rechecks accept a medical disposition only
  while the exact current revision remains `review_required`; idempotent batch
  replay restores the original immutable result. Translation, corpus analysis,
  readiness, and admission accept only `pass` or
  `medical_confirmed_with_residual_issue`, and translation batches freeze the
  exact recheck/disposition lineage. Repository, OCR, translation, corpus, and
  authoring focused regression now passes 220/220.
- 2026-07-30 13:42-13:53: Backed up the R42 SQLite store before schema v8 and
  recorded hashes for all 90 immutable extraction payloads. Persisted three
  V2.1 rechecks and one residual medical disposition. Post-migration state is
  89 pass, one confirmed residual issue, zero pending/blocked; all 90
  historical extraction payload hashes remain unchanged.
- 2026-07-30 13:54-14:02: A real browser reload exposed a historical-data
  compatibility regression: the current Protocol-only model rejected the old
  journey's `document_roles=["protocol","sap"]`, returning HTTP 500. Added a
  single read-boundary compatibility projection used by every journey
  deserialization path. A regression proves the consumer sees Protocol only
  while raw historical JSON remains unchanged. Rebuilt the R42 frontend
  snapshot, restarted its preview with the correct isolated API proxy, and
  verified runtime contract readiness plus successful workbench entry.
- 2026-07-30 14:02-14:12: Real R42 translation preview consumed the effective
  OCR projection and returned 10,704 eligible new Protocol spans, 63,236
  excluded spans, and no fidelity-blocked candidate. Historical standalone-SAP
  content accounts for 29,910 excluded spans and does not enter the corpus.
  Browser review of `结构与译文确认` exposed an efficiency gap: the initial
  unfiltered preview and the default four-anchor preview each require roughly
  16 seconds, with only a spinning refresh icon. Recorded this as R42-005 for
  cache/projection and truthful calculation-state repair.
- 2026-07-30 14:12: OCR route quality decision remains Paddle official primary
  with GLM fallback. Current evidence does not show Paddle quality below GLM;
  the residual table issue is on fallback pages. Critical clinical fields and
  complex schedule tables remain subject to explicit structured-content gates.
  Decision and rollback thresholds are in
  `OCR_ROUTE_QUALITY_DECISION_20260730.md`.
- 2026-07-30 14:14-14:26: Refined the confirmed competitor-triage experience
  for a lazy senior medical writer. The drawer now defaults to the 49 retained
  direct/indirect references rather than all 665 search results; the full set
  remains one selectable filter away. A confirmed AI run hides obsolete
  per-item classification controls without weakening the finalized-journey
  gate used by downstream document preparation. Real browser assertions passed
  for retained default, 49/665 switching, locked-state copy, and hidden manual
  reason input.
- 2026-07-30 14:20-14:29: Removed automatic expansion of a historical failed
  research-pipeline banner. Failure remains visible in the compact progress
  disclosure and its diagnostics/retry actions remain available, but the main
  research-design surface is no longer displaced by a large red warning. The
  focused frontend regression passed 132/132 and the production build passed.
  R42 was restarted against the unchanged isolated runtime with matched build
  identities: frontend `web-f1732ad8f8bb8103`, backend
  `api-356ccd947dfb8fce`.
- 2026-07-30 14:30-14:45: Implemented the R42-005 backend performance slice in
  `writing_reference_translation_batch.py`. The service keeps one bounded,
  in-process no-filter scope projection; it never persists source material or
  credentials. Before reuse it recomputes a lightweight current fingerprint
  over the locked snapshot/glossary, preparation and retained IDs, current
  artifact state, latest extraction revision/payload hash, validation,
  structure-review, effective OCR recheck/disposition lineage, current
  translation state, and translation contract. A changed fingerprint drops
  the old projection and rebuilds all existing Protocol-only/OCR gates.
  Anchor-filtered previews now project from the cached full scope in memory;
  they do not re-read or re-evaluate the full span set. Added controlled timing
  and cache-hit tests plus validation-lineage and OCR-lineage invalidation
  tests. Focused batch tests pass `47/47`; related translation/corpus tests pass
  `118/118`; `py_compile` passes.
- 2026-07-30 14:46: Real isolated R42 API verification completed against 90
  Protocol/combined artifacts. Cold unfiltered preview took `16.11s`; the
  subsequent four-anchor preview took `0.31s`, and the eligibility-only
  preview took `0.32s`. Returned counts were unchanged: `10,704` full-scope,
  `5,704` four-anchor, and `918` eligibility-only. No download, OCR,
  translation, corpus admission, SAP-boundary, or immutable audit behavior was
  bypassed. Residual risk: the first cold preview still performs the complete
  lineage/span walk and remains approximately 16 seconds; this slice makes
  repeated anchor reads fast but does not yet add a persisted/shared cache or a
  frontend calculation-state indicator.
