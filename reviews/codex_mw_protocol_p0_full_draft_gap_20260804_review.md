# Codex independent challenge — Protocol P0 full-draft gap (2026-08-04)

## Challenge conclusion

The earlier “full Word” evidence was not a full-draft proof: it preserved a document skeleton and headings but did not establish substantive prose across applicable sections. Treat this as P0. A section-level revision candidate cannot be promoted to a project-level protocol claim.

## Required invariants checked

- Exact section identity/order is carried in trusted task context and checked at gateway and runner layers.
- Evidence IDs are required, unique, and bound to allowed sources; route/provider/model identity is server-resolved.
- Candidate generation is side-effect free; adoption is explicit, per-section CAS, version/binding checked, and idempotent.
- Deterministic chunk artifacts cover a worker reclaim/restart boundary so a valid completed chunk is reused rather than invoking the model again.
- Export gate blocks heading-only/short/placeholder greenfield or template bodies; source-backed original DOCX remains lossless.

## Residual challenge

The contract cannot by itself prove scientific completeness or native regulatory quality. A real provider and visible browser run must still confirm that each applicable chapter receives non-placeholder source-grounded prose and that the resulting DOCX renders with stable numbering, TOC, references, and cross-links. Until that evidence exists, no tester round is accepted and no P0–P4 consecutive-clean claim is allowed.

The first isolated visible run also exposed a possible framing write race: a user-visible submit returned `409 expected revision 3, current 4` while automatic research/prefill was still advancing the journey. Reloading and returning through the visible module allowed the commit, but the race remains a P1/P2 candidate until a deterministic reproduction and reconciliation behavior are added. The failed public-search terminal is not evidence of a full-draft defect and was not bypassed through an API write.

The role settings surface already separates the four execution roles and target providers/models. It still needs a durable thinking toggle/intensity contract for the comprehensive LLM and translation-support assistant, plus proof that those values reach the corresponding model envelopes. OCR and translation body must remain independently configured; oMLX lease/model ownership remains with the shared workload gate.

## Continuation challenge update (2026-08-04 11:35)

- The role-thinking gap is closed in code and deterministic checks: only the independent LLM and translation-support roles expose thinking/intensity controls; role defaults are frozen into durable task envelopes, while OCR/body translation retain their independent provider/model bindings. This is a contract result, not yet a live provider-quality result.
- A P1 operational defect was isolated and addressed: an unexpected downstream preparation exception could leave the journey indefinitely in `preparing`. The retry path now persists a truthful retryable failure, and status reconciliation can convert an already-terminal preparation batch to failed without re-running any download/OCR operation. Regression evidence is 119 focused checks plus 53 full-draft/greenfield/role/frontend checks.
- Visible recovery in the isolated project created one translation batch and entered `translating`; the durable job was still processing 2/20 items at the last observation. This is not a full-draft or Word acceptance. The strict model-identity and remote Paddle outcome gates remain fail-closed.
- The live batch later reached 15/20 projected terminal items; two NCT03907878 planning items failed closed with `response_model_mismatch` and the next document began planning. The adapter previously collapsed the observed model to the requested model in the immutable record, weakening diagnosis. The bounded repair preserves the observed/missing response identity while keeping the same terminal fail-closed code; the focused production-wiring regression is 28/28. Restart/replay of this isolated runtime must wait for its current worker terminal state.
- At 12:00–12:03 the visible projection reached 17/20 while the durable job remained leased and one DeepSeek call was still in TLS/proxy I/O. The discrepancy was traced to a progress-counting defect, not a second worker: heartbeat counted only successful/excluded items and omitted `failed_retryable`. The source/test repair counts non-pending/non-running items and passed the focused 1/1 regression; acceptance still requires a post-terminal restart proof, not this source result alone.
- P0 remains open until a substantive, source-bound, rendered Word is inspected. The multi-model/two-role matrix remains deliberately unstarted; no P0-P4 clean-round claim is made.

## Recommendation

Proceed to one isolated visible Playwright proof only after the deterministic suite remains green and the role-thinking contract is wired. Keep the final model/role matrix separate and serial; do not mix engineer and senior-medical-manager perspectives in one task. The PNH III exploration is a setup/race observation, not a passed round.

## Independent challenge update — current-snapshot preparation (2026-08-04)

- The current journey and legacy research pipeline are on different immutable snapshots (`9e730…` vs `3bbd…`). This is a lineage risk, not permission to rewrite either row. The current snapshot had no downloaded artifacts, so the only defensible user action was one visible start of a new bounded preparation batch; old failed translation records remain excluded from retry.
- The translation preview raw `KeyError` was a P2 user-facing defect. The narrow repair maps only the missing preparation lookup to an actionable workflow error and leaves 404/terminal-state guards fail closed. The repair has deterministic unit evidence but still needs an isolated post-worker HTTP verification.
- The preparation UI had no visible control for the existing bounded stage transition, so a new current-snapshot batch could become stuck at `awaiting_stage_admission`. The added idempotent stage button is a necessary P1 usability/continuation repair; the API route itself already had atomic/idempotent semantics and was not changed.
- Current OCR execution is demonstrably pinned to the required official `PaddleOCR-VL-1.6` role. This is route identity evidence only, not proof that all OCR outputs pass content/medical QC.

P0 remains open: no substantive Word, no rendered document evidence, and no two-role/model matrix have been accepted.

## Independent challenge update — rich proof and strict final gate (2026-08-04)

- The rich isolated visible path is a valid diagnostic improvement over the earlier three-section proof: 12 applicable sections were loaded, nine substantive AI candidates were generated in one durable job, adopted once, and frozen section-by-section through visible controls. The candidate panel contained native Chinese prose and no internal transport markers.
- The first rich DOCX rendered successfully (8 pages, 3,379 body characters, one structured table, TOC field, 192 visible Chinese spans, CJK fonts). Visual/render evidence therefore exists, but the DOCX is not acceptable as a final protocol because the source fixture is incomplete and the assembled prose contains implementation vocabulary and unresolved review instructions.
- The new content-quality detector correctly found 15 open blocking findings in the assembled document (4 internal transport/test vocabulary and 11 unresolved drafting markers). A new export request failed closed at assembly with the exact content-quality error and produced no artifact. This is the expected safety result and closes the bypass concern exposed by the earlier diagnostic artifact.
- The temporary rich runtime now has an encrypted local Paddle credential materialized only inside its isolated directory, so `/api/ai-gateway/roles/status` reports Paddle `current_runnable=true`; no secret value is present in this record. This does not prove a live OCR call or OCR content quality. The previous no-key statement applies only to the old `mw-p0-word-proof.Q2YFFQ` runtime and is superseded for the rich clone.
- The tester matrix remains gated. A complete source/evidence fact packet is required before claiming a clean final Word; otherwise the correct user-facing behavior is an actionable missing-input blocker. Engineer and senior-medical-monitor user roles must remain separate tasks when the gate opens.
- The guard is now enforced twice: unresolved drafting markers are rejected at candidate validation and again at final export. This prevents a model retry or a manually saved working copy from moving the same incomplete language downstream.
- Visible browser recheck confirms the final export failure is understandable and actionable at the user surface (Word 导出失败…content quality); no silent download or success state was observed.
- The adoption path is now fail-closed for pre-guard candidate artifacts as well; a focused test mutating a persisted artifact to include internal/unresolved wording is rejected before any working-copy write.

## Independent challenge — lossless pause checkpoint (2026-08-04)

- The visible structured-design editor is a bounded usability repair: it converts existing study facts into reviewable controls while retaining fail-closed backend admission. Browser proof confirms persistence of randomized/double-blind/placebo/parallel-group, multi-center, systemic exposure, and injection dosage form as user-entered test facts.
- The evidence does not establish PICOS completion. After the visible confirmation flow the journey remained revision 33, `picos_complete=false`; the precise completion-state response still needs read-only inspection. This is the only active continuation defect at this boundary.
- The latest AI prefill response was not silently normalized: the unsupported composite schema was rejected and the package stayed partial. This is correct safety behavior, but design-package generation remains unproven.
- Build and focused frontend contract checks are green. They are not a substitute for a real provider run, substantive full protocol, DOCX unzip/render/link inspection, or role acceptance.
- No P0-P4 clean round, production readiness, or multi-model role acceptance may be claimed. Resume only from the saved current-snapshot state; do not retry old immutable batches or broaden into Synopsis/CSR.

## Independent challenge update — guard and official OCR readiness (2026-08-04)

- The first substantive Word artifact is positive only for its isolated three-section boundary. Its leaked fixture/platform vocabulary is a release-quality defect; the new runner/prompt gate rejects the vocabulary before adoption rather than attempting silent cleanup. Five full-draft tests, nineteen greenfield runtime tests, and twenty-four exporter tests pass after the change.
- The requested independent role separation is present in the role schema and runtime binding. The temporary proof runtime has no configured `PADDLE_OCR_API_KEY`; its role status therefore remains `current_runnable=false` with `API Key 未配置`. This is an explicit external-runtime gate. Historical encrypted credential snapshots are evidence that a prior local runtime had a credential, not permission to copy or expose it; no copy was made in this checkpoint.
- A richer fixture is required before acceptance: the current proof has no structured tables or reference/index objects and its cached TOC remains Word-update-on-open. The next proof must show applicable-section coverage, clean native prose, table/reference XML, and the deterministic visual QC report. The engineer/user matrix remains unstarted and must remain serial and role-separated.

## Independent challenge update — export error UX (2026-08-04)

- The strict final-export block was rechecked through the visible page after restarting only the isolated API/Vite pair. The backend stopped assembly on 15 content-quality findings, and the browser produced no artifact.
- The raw `RuntimeStoreError`/section-locator message was unsuitable for a lazy, nontechnical senior medical monitor. `medicalWritingExportErrorText` now presents a concise next action naming the real `内容核查` control; raw detail remains available to diagnostics and is not the primary user message.
- Visual evidence `/private/tmp/mw-p0-rich-proof-20260804/final_export_blocked_user_plain_v2.png` shows the alert in the actual layout. Full frontend contract 120/120, backend focus 32/32, DOCX exporter 24/24, and Vite build passed. This reduces a P1/P2 usability risk but does not weaken the content gate or change the open final-quality verdict.

## Independent challenge update — source-bound complete-content rerun (2026-08-04)

- The former headings-only concern is now closed for a bounded source-bound isolated path, not globally: all 12 applicable sections produced substantive no-marker candidates in one visible DeepSeek run, were adopted once, frozen through visible controls, and exported to a rendered DOCX. This is materially stronger evidence than the earlier rich fixture, but the fact packet is synthetic and must not be treated as clinical evidence.
- The source-context expansion is directionally correct: confirmed design/product/PICOS facts are passed into the full-draft prompt, and the candidate/final-export guards reject future promises, missing numeric facts, post-confirmation wording, internal transport vocabulary, and unresolved references. No sanitization or silent coercion was used.
- The Word artifact is structurally substantive (8 tables, 3,988 extracted characters, update-on-open TOC, no marker hits) and visual QC passed on 9 pages with embedded CJK fonts. The cached TOC still shows Word's update-on-open placeholder and the OOXML has no explicit `w:hyperlink` elements; therefore multi-reference and cached TOC link completeness remains unproven and is a release gate.
- Evidence IDs: full-draft job `mwjob_0d887129c14c9a3a6bc47ea8`, export job `mwjob_0b065609bb68a96b20cae152`, candidate SHA-256 `02185ea311c93b3655c7e9f6a686837ed0b095e7854ac789f3d4995e6811a4f6`, DOCX SHA-256 `6e5204a4115e803de6068dc76bba2c9ae3f8f9a59d5d8e32d2c2c242a3d0da2a`, and visual report `/private/tmp/mw-p0-source-bound-completeness.ZY1mL6/word_render_qc/visual_qc_report.json`.
- Acceptance remains bounded: no tester round, no P0–P4 clean-round claim, no official Paddle live-call/content-quality claim, and no production clinical-submission readiness. The next review gate is route-policy validation and role-specific prompt/manifests; engineer and senior-medical-monitor tasks must stay separate and user-perspective actions must remain visible Playwright clicks.

## Independent challenge update — route/configuration gate (2026-08-04)

- The isolated runtime independently exposes the requested four AI roles and thinking controls. Readiness is auditable, but it is not a live Paddle OCR content-quality result and does not satisfy a user-acceptance round by itself.
- The executable route policy is authoritative. The Beijing night substitution is active at the recorded evaluation time; any DeepSeek Flash primary is replaced by Pi/Alibaba `qwen3.8-max:xhigh`, and exact Pi/Alibaba Qwen Preview nodes are rewritten to Qwen Max. This must be recorded in each later manifest rather than inferred by a caller.
- Two user-requested provider aliases are invalid under the current policy: `pi/xai-oauth/grok-4.5` and `pi/cms-router/minimax-m3`. Silent direct dispatch would violate fail-closed routing. The closest policy-valid nodes are Grok Build `grok/grok-build/grok-4.5` and CodeBuddy `codebuddy/codebuddy-cli/minimax-m3`; adopting them is a route substitution, not proof that the requested aliases were used.
- No tester matrix may start until role-specific prompts are separately preflighted, effective routes are validated, clean-clone reset/audit is defined, and the Word gate includes substantive sections plus explicit TOC/reference-link checks. Engineer and senior-medical-monitor perspectives must never be combined in one prompt/session.

## Independent challenge update — engineer role round 1 (2026-08-04)

- Grok's report is independently consistent with its isolated evidence: a clean new CSU Phase I project reached public search and triage, then stopped at an empty confirmed basket. The report did not claim a Word or clean round, and no stable/runtime boundary violation was found.
- The P0 is substantive, not a test-script artifact. A medically valid “none of the public candidates are suitable” decision currently terminal-fails the parent pipeline before the user can complete study definition/PICOS or choose a controlled shared-corpus/manual-upload exception. This contradicts the AI-first greenfield path and makes the required complete Word impossible for a legitimate indication.
- Codex applied the smallest safe repair: empty confirmed scope is a soft waiting state with immutable triage/error evidence; no download/OCR/translation is attempted; the UI explicitly directs the user to shared-corpus/manual-upload or the existing acknowledged exception gate. Heavy research lineage is not fabricated or retried.
- The repair suite is green (143 focused checks, py_compile, Vite build). It still requires visible user-role revalidation. The remaining P1/P2 usability and status-semantics findings should be rechecked after the P0 path is exercised, not silently declared fixed.
- Clean-round verdict: **fail**. This pass is a defect-finding round; it contributes zero to the required two-consecutive-clean streak for the engineer role.

## Independent challenge update — user role round 1 and zero-result repair (2026-08-04)

- The separate senior medical-monitor Grok pass is valid defect evidence: clean isolated clone, distinct Phase III ulcerative-colitis study, visible Playwright actions, and independently confirmed role bindings. It stopped before PICOS/corpus/full draft/Word and fails the round gate.
- The P0 is upstream of the earlier empty-confirmed-basket fix. A zero-result ClinicalTrials.gov snapshot still entered terminal `failed/search_no_results`, so the AI-first flow could not offer the documented shared-corpus/manual-upload path. The UI simultaneously claimed “公开研究检索已保留” despite `returned_count=0`, a P1 truthfulness/usability defect.
- Codex repaired only that branch: zero public results now use auditable `awaiting_corpus_admission` with `no_public_protocol_results`; no public source is fabricated and no download/OCR/translation batch is created. Frontend copy and error-code handling are aligned; genuine downstream failures remain terminal.
- Evidence after repair is deterministic: 163 focused tests, py_compile, and Vite build pass. The old user clone predates this repair, so the next decision is a fresh isolated user-role rerun, not a clean-round claim.

## Independent challenge update — user follow-up and query-term root cause (2026-08-04)

- The same-session follow-up is credible evidence for the repaired branch: a new clean clone, a different Phase II Crohn project, visible Playwright clicks, and read-only state checks. It verifies the waiting state and truthful no-heavy-work boundary, but does not satisfy the full Protocol Word acceptance bar.
- The remaining P0 is the practical continuation dead end: `语料准入` is not a user-facing shared-corpus/manual-upload/exception decision surface; it opens a 13-field raw JSON design form and leaves the user at “完成第一步” blocked on technology type. This is separate from the now-closed zero-result terminal-failure bug.
- The search anomaly is reproducible and not connectivity: official API HTTP 200 for Chinese and English requests; only the English base disease terms returned studies. The resolver's exact-only alias logic failed on severity/activity-qualified Chinese labels. Codex added deterministic longest-alias containment and tests for both observed IBD labels, without loosening evidence gates or inventing sources.
- Clean-round verdict remains **fail**. The next product repair should make the fallback a single explicit user action surface and provide an AI-recommended technology type confirmation; only then should a new role round assess download/OCR/translation/full-draft/Word.

## Independent challenge — current-source UX/root-cause repair (2026-08-04)

- The repair addresses the observed causal chain without hiding evidence: stale progress is reset at the backend projection boundary; the user-facing fallback gets a direct navigation CTA; and the existing exception route can reach document creation only after a version-bound StudyDefinition.
- Relaxing the initial technology-type UI guard is contract-aligned because backend `creation_minimum_complete()` requires only product/indication/phase; unknown product facts remain unresolved and must not be used to fabricate downstream content.
- Raw JSON is a presentation defect in the composite candidate panel, not a reason to loosen adoption policy. Human-readable formatting was isolated to the UI formatter; fail-closed per-path confirmation remains intact.
- Verification is deterministic (168 focused checks, py_compile, Vite build). No clean-round credit is granted until a fresh visible user pass proves the corrected state reaches substantive full draft and Word or reports the next root cause.

## Independent challenge update — user role round 2 and response-shape repair (2026-08-05)

- The isolated user pass is valid defect evidence, not a script-only failure: it used a clean clone, a distinct IgA nephropathy Phase III indication, visible Playwright controls, real ClinicalTrials.gov HTTP 200 retrieval, Protocol download, native extraction, OCR, and Hy-MT2 translation. The failure was isolated to the synthesis boundary.
- The decisive persisted error shows a malformed top-level JSON shape: a complete finding object appeared where the analysis envelope was required. This is a provider-contract mismatch; it is not evidence that the source spans, OCR, translation, or numerical guards should be weakened. No Word or clean-round credit is granted.
- The repair is appropriately narrow if it remains auditable: exact single-finding roots are wrapped only with server-derived identity fields, the original response is retained, a versioned normalization event is persisted, and all downstream finding/evidence validation still runs. Unknown or partial roots remain rejected. A future real run must prove the wrapper does not mask omitted modules or unsupported claims.
- The retry UX repair is necessary: a failed-but-retryable pipeline must surface the idempotent downstream-only retry in the compact toolbar, not leave a lazy medical manager to expand a hidden detail panel. The copy now distinguishes schema/JSON failure from registry or heavy-stage failure and names the retained evidence boundary.
- Independent acceptance remains open. Re-run from a new clean clone and verify analysis persistence, `response_normalization.status`, no duplicate preparation/translation records, complete substantive Word output, and no P0–P4 findings before crediting any streak.

## Independent challenge update — user role round 3 and preparation-stage CTA (2026-08-05)

- The SLE Phase II pass is valid first-principles evidence: source lookup, triage, real downloads, native extraction, and official Paddle OCR all occurred in a clean clone. The pause is not a connectivity or model-route excuse; the persisted state is a legitimate bounded admission stage.
- The P0 is a user-reachability defect. The backend has the correct stage-advance transition and idempotency boundary, but the only visible button was inside a collapsed progress details element. A lazy medical monitor could not discover or invoke the next-stage admission from the compact workbench surface.
- The narrow fix is appropriate: surface the existing transition in the toolbar, keep completed items immutable/reused, and preserve the pause when deferred work remains. Do not auto-admit all 49 items or bypass the OCR/content gate.
- The child OCR failure for `NCT02265744` remains a separate P1/P2 visibility and recovery concern. The next user run must confirm that the visible stage button works, then inspect how the UI explains the failed file and whether the user can continue with clean sources without silently treating unusable OCR as evidence.
- No clean-round credit is granted; substantive Word, reference-link, and two-consecutive-clean requirements remain open.

## Independent challenge update — user role round 4 and partial-failure status race (2026-08-05)

- This is valid first-principles defect evidence: the user used a clean clone, a distinct non-oncology Phase III project, real visible admission, real Protocol retrieval/extraction, and official PaddleOCR-VL-1.6. The compact CTA repair itself passed; the round stops before translation/full draft/Word and remains non-clean.
- The single OCR failure is correctly represented at item level (`Paddle OCR completed with unusable text`); the batch correctly retains clean and deferred items. The P0 is the parent projection: while the synchronous resume continues, status polling sees `preparing + partial_failure` and `_reconcile_stale_preparation_state` writes terminal `failed`, making a valid resumable path look dead. This is a race caused by stale parent-state reconciliation, not a reason to weaken OCR or admit unusable text.
- The repair is appropriately narrow: an active-resume lease prevents status writes until the continuation persists its result; after restart, persisted batch counts determine an explicit waiting stage (`awaiting_preparation_admission` when deferred evidence remains, otherwise `awaiting_translation_scope`). The failed item stays immutable/failed, and no retry or source substitution is hidden.
- Recheck targets: a fresh visible user pass must exercise concurrent status polling during admission, prove no duplicate preparation/translation rows or model calls, show the failed file and clean-evidence continuation clearly, and then inspect AI analysis response normalization, substantive section coverage, DOCX TOC/reference links, and internal-marker scans. No clean-round credit is granted.

## Independent challenge update — user role round 5 and search/start contract (2026-08-05)

- The MS Phase II pass is valid defect evidence: clean clone, visible user clicks, real registry retrieval and DeepSeek triage, and a persisted confirmation. It does not count as clean because no downstream source or Word artifact exists.
- The decisive trace is a missing transition, not an assumed provider failure: the captured API block contains `competitor-search` 200 followed by refresh/status GETs and no `research-pipeline/start`; no start status/body or error copy exists. The post-confirm journey and durable store have no parent pipeline, while the UI claims source download is in progress. Classify as P0 false success/dead end and P1 frontend state/transition contract mismatch.
- The likely stale/remount token early return is explicitly an inference; the product fix is still first-principles because it removes an unnecessary same-project gate while preserving project-switch cancellation and idempotent server keys. Confirmation now displays backend truth and preserves an actionable failure explanation.
- Recheck target: prove a fresh source run emits exactly one start request, persists the parent through confirmation, creates no duplicate triage/model work, and reaches the existing preparation admission boundary. No clean-round credit until the substantive Word, internal-marker, reference-link, and full P0–P4 checks pass.

## Independent challenge update — user role round 6 and route blocker (2026-08-05)

- This pass is valid transition evidence: a zero-project clone, distinct rheumatoid-arthritis Phase II project, visible Playwright, HTTP 200 search, and a single HTTP 200 pipeline-start request with durable IDs. It confirms the round-5 frontend start repair; it does not reach a substantive Word and is not a clean round.
- The 4/22-success, 18/22-failure triage result is not to be misread as a product continuation bug. The active night route selected Alibaba Qwen Preview and each failed chunk recorded provider HTTP 403. The two visible retries were idempotent in effect and did not create confirmation, preparation, or downstream rows. This classifies as an external route/runtime blocker (operational P1/P2), while preserving the product's fail-closed behavior.
- The correct acceptance action is time-windowed revalidation with the effective DeepSeek daytime route, not a product bypass or a policy edit. Recheck must retain request counts, retry/job IDs, SQLite row counts, and the full Word/evidence gate; no clean streak credit is granted for round 6.

## Independent challenge update — deterministic regression after round 6 (2026-08-05)

- The current source passes 869 focused tests across the touched contracts. This supports the narrow repairs but is not independent real-browser acceptance: no model call, service, OCR, download, translation, or Word export occurred in this check. The acceptance gate therefore remains open with clean streak `0`.

## Independent challenge update — user role round 7 and provider-response boundary (2026-08-05)

- The r7 pass is valid first-principles evidence: a clean clone, distinct Phase II atopic-dermatitis project, visible Playwright, HTTP 200 registry retrieval, real triage retry, 15 visible preparation-admission transitions, Paddle OCR and Hy-MT2 activity, and durable SQLite inspection. The initial observer mismatch (API port versus Vite proxy) was proven harness-only and corrected before judging product state.
- The source path correctly failed closed on 13 OCR outcome-unknown/unusable documents and did not admit them as evidence. The remaining observability gap is material: the Paddle adapter persists only a generic outcome, so HTTP status/content type/poll count/body hash cannot currently explain which upstream boundary failed. This is a P1/P2 follow-up, not permission to retry or accept bad text.
- Translation idempotency is sound in this pass: 20 distinct records and 20 composite runs at attempt 1; the visible continuation created a zero-chunk reuse batch and no duplicate model calls. The corpus-analysis failure is isolated to the provider/parser contract: a JSON response had empty `message.content` while `reasoning_content` existed, and no raw response diagnostics were durable.
- Narrow repair is accepted for recheck: v11 prompt identity with explicit `message.content`/`reasoning_content` separation and complete envelope example; output cap 32,768; safe provider response-shape diagnostics only; durable child-context projection; compact continuation buttons for both waiting stages. It preserves fail-closed JSON/evidence validation and never persists raw provider content.
- Verdict remains **not ready**: no corpus-analysis artifact, substantive full draft, Word, reference-link check, or two-round P0–P4 clean streak. Daytime r8 must prove the new diagnostics and compact reachability before any clean credit.

## Independent challenge update — fixed max configuration and r8 boundary (2026-08-05)

- The product requirement is now unambiguous: role-level configuration is fixed to DeepSeek V4 Flash at `max` (not `xhigh`) for comprehensive and translation-support LLM roles; OCR and body translation remain PaddleOCR-VL-1.6 and oMLX Hy-MT2 respectively. The global harness route policy was not weakened or edited.
- The isolation repair is sound: the new independent profile is distinct from translation support, and migration copies only the encrypted local DeepSeek credential into that profile. No secret appears in JSON, prompts, reports, or browser payloads. Stable active-profile behavior remains Alibaba Qwen for legacy consumers, while explicit role resolution selects the writing binding.
- Deterministic checks support the contract (`69` role/gateway tests, `134` frontend contracts, compile and build); they do not prove live provider availability or document quality. The r8 receipt is xhigh and therefore fails the requested configuration gate regardless of downstream progress. Clean streak stays `0`.
- Acceptance remains open. A fresh max-receipt clone must independently prove provider connectivity, real OCR/translation, corpus analysis in `message.content`, complete factual sections, DOCX output, TOC/reference hyperlinks, internal-marker scan, and two consecutive P0–P4-clean rounds for each role before any release claim.

## Independent challenge update — r8 wrong-kind rejection and v12 boundary (2026-08-05)

- The r8 error is a real provider semantic mismatch: server-side evidence validation observed `module=structure` or `regulatory_commonality` paired with a supported non-regulatory kind. This is neither a missing field from the adapter nor an over-strict cross-indication policy. Fail-closed rejection is the correct safety outcome.
- The v12 prompt repair is bounded and auditable; it does not coerce output into a regulatory pattern. The added diagnostics make the reason durable while retaining no raw provider text. The deterministic fake must continue to prove wrong-kind rejection and zero corpus rows.
- The isolated post-restart max readiness check is only a configuration/connection observation (GET, no model call); it cannot make r8 clean because all preceding upper-layer calls were xhigh-era and no max corpus attempt happened. Clean streak remains 0.

## Independent challenge update — engineer round 9 and no-loss pause (2026-08-05)

- Round 9 is **not clean**: fixed-max receipt passed, but the visible clean clone stopped at `awaiting_preparation_admission` with 44 prepared, 4 fail-closed OCR items, and 39 deferred. No substantive full draft or Word artifact exists; clean streak remains 0.
- Findings are P0 no Word path, P1 triage missing-`results` schema recovery, P1 weak OCR outcome diagnostics, and P1/P2 high-friction staged admission. The report confirms no duplicate prep batch and no stable/product-source mutation.
- User-requested pause was handled by an authorized interrupt because Grok stdin was `/dev/null`; runner/fallback/helper/isolated services were stopped. The same-session pause prompt was then blocked before model response by three Grok settings-interface network errors. The report, clone evidence, and session transcript remain durable; no literal pause marker is claimed.
- Acceptance stays open. On resume, revalidate max and continue the same isolated engineer clone from visible preparation admission; user role remains undispatched.

Pause-network correction: the blocked resume continued to retry the Grok settings endpoint in later groups near 05:05 and 05:11 before exit 130. These retries are external harness noise only; no product transition followed.
