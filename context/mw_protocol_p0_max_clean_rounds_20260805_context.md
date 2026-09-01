# Task Context: mw_protocol_p0_max_clean_rounds_20260805

Created: 2026-08-05 11:13:29
Objective: 在固定 DeepSeek V4 Flash max、PaddleOCR-VL-1.6 与 oMLX Hy-MT2 配置下，串行完成分离的工程师与资深医学监察员 Protocol P0 干净克隆端到端验收；每一步追溯意外结果，直到正文/Word与P0-P4证据充分或记录真实阻断。
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Global contract: `/Users/smkzw/.codex/AGENTS.md` (read at 2026-08-05); workspace overlay: `AGENTS.md`.
- Protocol P0 continuation records: `context/mw_protocol_p0_resume_20260804_context.md`, `runs/MW_PROTOCOL_P0_FULL_DRAFT_GAP_RESUME_20260804.md`, `reviews/codex_mw_protocol_p0_full_draft_gap_20260804_review.md`, and `metrics/mw_protocol_p0_full_draft_gap_20260804_metrics.md`.
- Role prompt/report: `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_grok.md`, `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_grok.md`.
- Isolated runtime evidence only: `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/`; Grok session durable files under `~/.grok/sessions/.../a1e31091-cfce-4482-bc95-a0c841f9fbc3/`.
- Stable API/r42/v36/medical-monitoring data and historical lineages are out of scope and were not written.

## Scope

- In scope: one separated engineer-perspective, fixed-max, clean-clone Protocol P0 acceptance pass; capture every visible transition and root cause; preserve the exact resume point.
- Out of scope: the senior-medical-monitor user role, broad tester matrix, product-source edits in this pass, reuse of old lineages, and any claim of production/submission readiness.

## Success Criteria

- Configuration receipt must show DeepSeek `deepseek-v4-flash` thinking enabled/max for independent and translation-support LLM, official PaddleOCR-VL-1.6, and oMLX Hy-MT2 body translation.
- Visible Playwright path must be evidence-backed through the furthest reachable stage; no headings-only/placeholder Word may count.
- Every unexpected result must have a causal classification, durable locator, idempotency observation, and explicit skipped-stage uncertainty.
- After the user-requested pause, no test process or isolated service remains active; the clone/report/session evidence remains recoverable for a later same-session continuation.

## Risk Boundaries

- Do not write stable API, r42/v36, old batches, medical-monitoring DBs, or product source from the role pass.
- Do not treat Grok output as final authority; Codex owns verification, acceptance, and clean-streak accounting.
- Do not classify a stopped preparation stage as clean; do not fabricate translation, corpus, full draft, Word, TOC, hyperlink, or visual-QC evidence.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:13:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.

## 2026-08-05 engineer round 9 and no-loss pause checkpoint

- Grok Build route `grok/grok-build/grok-4.5`, high effort, fixed product receipt **PASS**: DeepSeek V4 Flash thinking/max for independent and translation-support; PaddleOCR-VL-1.6; oMLX Hy-MT2. Settings SHA `fd42ed4eb4c9e79695bcea282e6351dcf9a70721970b4d8c203c282b3a9be77e`; role bindings SHA `4e41a156649529b5c1f4cd5885ac0d45629ba6ebe9da62ebd5b046f451222f9d`; frozen route identity `9884032823a89613c2d730ec4881914540c7649404c49de39aadd44963dca66c`.
- Clean clone `/private/tmp/mw-p0-engineer-r9.vZbWIw`, project `proj_user_0e7ac527231c`, asthma Phase III, pipeline `mwpipe_a28fe3b181b0b20d1927`, prep batch `wref_prep_bfb5c55ce2eaf4b84445b3be`. Search 697; triage recovered to 26/26; retain 87/exclude 610; preparation reached 44 prepared, 4 fail-closed OCR failures, 39 deferred. Final durable state: `awaiting_preparation_admission` / `preparation_partial_failure_stage_admission_required`; translation, corpus, PICOS completion, full draft, freeze, and Word were not reached. Report verdict is **NOT_CLEAN**, clean streak remains 0.
- Findings: P0 no full Protocol Word path; P1 triage chunk missing top-level `results` (visible retry recovered it); P1 OCR `paddle_ocr_outcome_unknown` lacks safe poll diagnostics; P1/P2 high-friction repeated stage-admission CTA; P2 first Playwright event/deep-link harness mismatch; ChinaDrugTrials remained `reachable_no_api`. Fail-closed behavior and no duplicate prep batch were preserved.
- The requested pause control was prepared at `prompts/role_acceptance/mw_protocol_p0_20260805_round9_pause_grok.md`. The active Grok single-turn process could not receive stdin (`/dev/null`), so it was stopped with an authorized interrupt; the runner/fallback and isolated API/Vite/helper processes were then stopped. A same-session resume attempt using Grok session `a1e31091-cfce-4482-bc95-a0c841f9fbc3` encountered settings-interface network errors (`https://cli-chat-proxy.grok.com/v1/settings`, three attempts) before a pause acknowledgement; no new test action or product write occurred. The original Grok session transcript/summary and the role report remain on disk, so the resume boundary is recoverable even though the injected marker was not returned.
- No-loss state: preserve clone evidence, report, prompt, and Grok session files; do not delete them. On the next explicit continuation, restore only the isolated runtime if needed and resume the engineer pass from visible preparation admission; do not start the user role until the engineer path has a valid follow-through decision. Use the exact same Grok session ID only after network availability is re-established, or record a new controlled route if the runner cannot resume it.

### Pause-injection correction

- The resumed Grok process later emitted additional retry groups at approximately 05:05 and 05:11 (each ending in `Settings fetch failed max_attempts=3`) before the controller session exited with code 130. These are repeated external settings-interface failures, not additional medical-writing actions. No model response, pause marker, browser click, provider call, or product/stable-data write followed the round-9 handoff.

## 2026-08-05 continuation — declared Cursor fallback

- User resumed the goal. Beijing route validation at 18:33:23 confirmed the declared `grok/grok-build/grok-4.5` primary plus `cursor/cursor-cli/auto` fallback; the night substitution was inactive. Grok health check returned `You are not authenticated`, so the primary is unavailable and no same-session Grok continuation was attempted.
- Cursor fallback health check passed without exposing a token: Cursor plan `pro`, JWT present/expiry valid, `cursor agent --print --trust --model auto` returned `CURSOR_ROUTE_OK` (session `ae59cd4b-87e1-4f70-b7ee-67868bad2fc5`). Prompt preflight passed for `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_fallback.md`.
- The existing clone was rehydrated read-only/operationally: API 8941 and Vite 5222 restarted against `/private/tmp/mw-p0-engineer-r9.vZbWIw/runtime`; persisted pipeline remains `mwpipe_a28fe3b181b0b20d1927`, stage `awaiting_preparation_admission`, 48/87 child projection and the same partial-failure evidence. No new search/triage/preparation call was made before fallback dispatch.
- Allowed writes for this continuation: clone logs/evidence and runner-owned `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_fallback.md` only. Stable product/source/r42/v36/medical-monitoring surfaces remain forbidden; user role stays separate and pending.

## 2026-08-05 follow-up4: discovery-gate repair accepted; stale-prefill race isolated

- Same Cursor session `095567b4-68c8-446b-a254-c92601765c16` completed follow-up4 with no fallback. Evidence: `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/r9fu4_final_summary.json`, `r9fu4_shepherd.json`, `r9fu4_admitted.png`, and report `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup4.md`.
- Real UI gate result: revision `6→7`; discovery projection `ct_conf_5a58cf6f7df9d416aadf` retained 87; candidate triage, 78 protocol structures, 16 regulatory-ZH translations and 16 medical admissions covered; `corpus_triage` remains pending by contract; only PICOS alignment is missing. No medical-review/search/OCR/translation/corpus-analysis writes occurred.
- A single visible `更新建议` request returned 409 after one physical prefill transport attempt. SQLite reservation is preserved as `expected_revision=6`, logical call `mwprefillcall_45363c651fdf467d8c7844ca`, `transport_attempt_count=1`, `status=unknown_outcome`, with generation-event-not-persisted/transport-dispatched failure note. The race was prefill on revision 6 versus delayed gate reconciliation to revision 7; the unknown outcome is immutable.
- Minimal source repairs now present and locally verified: readiness uses a valid pre-PICOS discovery projection as candidate-triage source while preserving final PICOS-gated `corpus_triage`; its source hash includes discovery. Prefill constant is `deepseek-v4-flash` and envelope effort is `max`. Parent batch settlement refreshes workspace, recalculates gate, then reloads authoritative journey. Authoring `更新建议` reloads the authoritative journey immediately before the single external call. Focused backend 110 tests, frontend contract tests, and Vite build passed; baseline pair remains 134/136 with 2 pre-existing frozen-scope failures.
- Next safe action: same-session follow-up5, one visible force retry only after confirming revision 7 and preserving the unknown row; if valid bulk evidence appears, proceed only with bound framing/PICOS candidates; otherwise stop at the exact provider/schema/lease boundary. Do not clear/delete the unknown reservation or rerun completed work.

## 2026-08-05 follow-up5: race repair validation caught a prop-name P0 before POST

- Same Cursor session completed follow-up5 with no fallback; report `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup5.md`, evidence `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/r9fu5_*`.
- Baseline remained revision 7, pre-PICOS gate 4/5, 16 approved briefs, and the old revision-6 unknown reservation unchanged. The single visible `更新建议` click did not send a prefill POST: after the fresh GET, the new code raised `ReferenceError: onJourneyChange is not defined` because this component's actual prop is `onJourneyChanged`.
- This was a newly introduced P0 front-end typo, not a provider result or lease mutation. It is repaired to `onJourneyChanged?.(effectiveJourney)`; focused contract test passed and Vite build passed. No new logical call or transport attempt occurred.
- Next safe action: same-session follow-up6, one visible force `更新建议` after the prop fix, verifying fresh revision 7 on the wire; do not touch the old unknown row or completed data.

## 2026-08-05 follow-up6: fresh revision repair passed; max-reasoning prefill hit the provider wait boundary

- Same Cursor continuation session `095567b4-68c8-446b-a254-c92601765c16` completed follow-up6 with no fallback; report `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup6.md` and evidence `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/r9fu6_*`.
- The visible repair was correct: one forced `更新建议` click read authoritative revision **7** immediately before the external call, sent `expected_revision=7`, returned HTTP 200, and advanced the journey **7→8**. The revision-6 unknown reservation `mwprefillcall_45363c651fdf467d8c7844ca` stayed immutable.
- The new single logical call `mwprefillcall_f120b44838ff448c99a0ffb7` used one physical transport attempt, then timed out at the configured provider boundary: profile timeout 300 s plus the local 15 s grace, with no provider response observed. The durable event at revision 8 is fail-closed `ai_outcome=unknown_outcome`, `package_status=partial`, model `deterministic_registry_prefill`; no automatic redispatch occurred and no second click was made. This is a provider latency/budget boundary, not evidence of an HTTP error, model mismatch, or schema acceptance.
- Read-only SQLite reservation/event evidence is preserved. The event payload records `ai_transport_attempt_count=1`, no provider/run/output hash, and the exact failure package; both unknown rows remain unchanged. Current gate is still pre-PICOS 4/5: discovery-retained 87, valid Protocol structures 78, regulatory-ZH translations 16, medical admissions 16, only PICOS alignment missing; no framing candidate bindings, full draft, or Word exists.
- Minimal product repair is now authorized/in scope for the clone continuation (stable API/r42/v36/medical-monitoring data remain out of scope): `DeepSeekPrefillAdapter` now resolves a dedicated bounded prefill timeout, defaults to 900 s for max reasoning, honors `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS`, and applies the same value to the provider transport and local wait boundary. This removes the observed 300/315 s skew without changing the fixed DeepSeek Flash/max route, one-attempt reservation semantics, evidence gates, or unknown-outcome immutability.
- Offline validation: focused prefill timeout/reservation tests `3 passed`; complete prefill adapter/corpus-bridge/evidence-binding set `272 passed in 6.56s`. Clone API was restarted with `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS=900`; current journey reads revision 8 without contract mismatch.
- Verdict remains **NOT_CLEAN**, clean streak 0, P0 framing blocker remains. Next safe action: same-session follow-up7, one visible force retry only after confirming revision 8 and the new 900 s budget; preserve both prior unknown rows, do not rerun search/triage/OCR/translation/corpus, and stop if the provider remains unresolved or returns an invalid/unbound response.

## 2026-08-05 follow-up7: timeout repair live pass; framing/adoption contract remains blocked

- Grok primary was unavailable (`You are not authenticated`); the declared Cursor fallback used a new Agent session `34058146-390e-4431-8850-7fbfb9aa71d4` with route `cursor/cursor-cli/auto`, high effort, bypass permissions. The older continuation session `095567b4-68c8-446b-a254-c92601765c16` was permanently Ask-mode: two follow-up attempts (including the force flag) returned no action and created no reservation. Those attempts are harness capability evidence only.
- The new session performed a real headful/visible Playwright pass. It found an initial Vite/API build mismatch, aligned Vite-only to API build `api-6c5f8ea8e7fe4fba`/web `web-4a805d0a224c584a`, and kept the already-running API intact. A macOS `setsid` attempt failed; a Python `start_new_session` Vite start kept the UI alive. This is harness/runtime evidence, not a product data result.
- Exactly one visible `更新建议` force request was sent at authoritative revision 8. It returned HTTP 200 after about 298.3 s under the 900 s budget. New reservation `mwprefillcall_d4b093096491417690b618f0`, expected revision 8, transport attempt 1, completed; persisted event `mwjourney_event_e64837b8f3c973b4634a44bf`. Journey advanced 8→9, stage remains `framing`, `corpus_triage` remains pending, and gate remains 4/5. No second click or automatic redispatch occurred.
- The two prior unknown reservations remain immutable and unchanged: revision-6 `mwprefillcall_45363c651fdf467d8c7844ca` and revision-7 `mwprefillcall_f120b44838ff448c99a0ffb7`. No search, triage, OCR, translation, corpus, or medical-monitoring data was rerun or rewritten. No full draft, Word, TOC, reference-link, or render evidence exists.
- AI lineage is auditable: provider `deepseek`, model `deepseek-v4-flash`, run `mwprefillrun_b264419414ef3c6b3d7bde38`, input/output hashes recorded in the event, 702-entry evidence catalog `45e6ad8c9cf2c04398022f723f6747e1` (SHA recorded in evidence), prompt v7, completed outcome, one transport attempt, package `partial`.
- Candidate review is fail-closed and must not be converted into project facts: `framing.design_pattern` has only unbound/insufficient deterministic candidates; `framing.intrinsic_objectives` has no candidates; bound `picos.design_archetype` alternatives are registry observations with `manual_only` and `partially_supported`/`pending_decision` status. The single-candidate endpoint correctly blocks pending/manual-only/insufficient candidates; no unsupported adoption was attempted. This explains the remaining PICOS gate rather than proving a complete protocol.
- Evidence: `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/r9fu7ns_baseline.json`, `r9fu7ns_generate_response.json`, `r9fu7ns_final_summary.json`, `r9fu7ns_shepherd.json`, screenshots, and `logs/cursor_followup7_new_session.stdout`; role report `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7_new_session.md`.
- Verdict remains **NOT_CLEAN**, clean streak 0. Next safe action is a read-only inspection of the front-end review/adoption entry and the composite per-path override/skip contract. Do not force another prefill generation, do not adopt an unbound or insufficient candidate, do not edit immutable rows, and do not start the senior-monitor role.

## 2026-08-05 follow-up8 and bounded project-fact adoption repair

- Same Cursor Agent session `34058146-390e-4431-8850-7fbfb9aa71d4` completed a visible diagnosis pass; no prefill generation and no adoption were submitted. Evidence: `/private/tmp/mw-p0-engineer-r9.vZbWIw/evidence/r9fu8_final_summary.json`, `r9fu8_shepherd.json`, `r9fu8_override_ux_probe.json`, screenshots, and report `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup8.md`.
- Visible result: revision 9, stage `framing`, package partial, 0 `batch_allowed+supported` candidates; six module cards are pending scaffolds (“待AI基于语料生成”). The design module exposes 13 per-path override/skip controls; adopt is disabled before decisions and becomes enabled after all 13 skips, but the skip-only action was not submitted. The two supported `framing.document_title` project-fact candidates were visible in the advanced field drawer but their `采用` and `修改后采用` actions were disabled by `manual_only` and neither candidate belongs to a composite package.
- Root cause is a real product-contract deadlock: the fixture supplies confirmed product/indication/phase facts, but evidence-bound field candidates are unconditionally manual-only, so the user must retype an already proven project identity to proceed. This is separate from the correct fail-closed treatment of competitor observations and incomplete design facts.
- Minimal source repair: `services/api/app/medical_writing_authoring_prefill_evidence_binding.py` now marks only a field candidate whose complete bindings all resolve to `current_project_fact`, whose status is `supported`, whose role is not pending, and whose evidence gaps are empty as `batch_allowed`. Mixed/competitor/corpus/partial/pending candidates and all composite packages remain manual-only. No immutable runtime row was rewritten.
- Validation: new project-fact-vs-competitor regression `2 passed`; prefill/bridge/evidence/single-gate/PICOS/package-contract set `237 passed`; complete `tests/test_medical_writing_authoring_prefill*.py` set `575 passed, 17 warnings`; frontend Vite build passed (1954 modules). The first system-Python run was environment-blocked by missing `cryptography`; rerun with the workbench `.venv` (`cryptography 49.0.0`) passed and no dependency was installed.
- The isolated clone API was restarted only to load the source repair (PID 77555, API 8941, existing runtime and project unchanged); the persisted package at revision 9 is intentionally not regenerated, so live UI evidence for the new mode is pending a future controlled generation. No search/triage/download/preparation/OCR/translation/corpus/medical-monitoring data was touched.
- Verdict remains **NOT_CLEAN**, clean streak 0. Next safe action: run a fresh isolated, clean UI pass with one visible prefill generation to verify the new project-fact mode and single-candidate adoption, while proving competitor candidates still fail closed. Do not reuse or mutate the existing revision-9 package/unknown reservations and do not start the senior-monitor role.

## 2026-08-05 follow-up9: fresh project-fact live probe and second repair

- Fresh empty runtime `/private/tmp/mw-p0-engineer-r10.1RQ2UD` was verified by
  health/read-only project count (`0`) before a visible headful Playwright
  pass. Cursor created exactly one project through the UI: `QZ-ASTHMA02` /
  `中重度哮喘` / `III期`, project `proj_user_10e0d9956107`, journey
  `mwjourney_575052cf1d560bdc7690`, visible code `MW-III-4AC9991F`.
- One automatic creation-time prefill POST (`force=true`, expected revision 1,
  HTTP 200 in about 40 ms) used the deterministic registry path and created no
  AI reservation. The product then automatically attached a 697-row
  ClinicalTrials.gov snapshot (journey revision 3) even though the harness did
  not click search/triage. No OCR, translation, corpus, PICOS, draft, Word, or
  prior-r9 data was touched.
- The title cards were visible but all three remained `manual_only` /
  `insufficient` with zero claim bindings; `采用` and `修改后采用` were
  disabled. The existing repair correctly covers only AI candidates that
  already have validated bindings, so deterministic `_candidate()` titles were
  outside its coverage. A deterministic `framing.design_pattern` candidate
  also leaked `batch_allowed` while `insufficient` and unbound.
- Narrow source repair now adds
  `bind_deterministic_project_fact_candidates`: only the exact three
  creation-minimum title templates are rebound to the immutable product,
  indication, and phase catalog entries, with catalog ID/SHA, three
  `current_project_fact` claim bindings, `evidence_status=supported`, and
  `batch_allowed`. It does not touch protocol ID, condition normalization,
  design/PICOS, product-profile, competitor, mixed, partial, pending, or any
  composite candidate. A separate safety change routes deterministic
  `framing.design_pattern` through the pending/manual-only scaffold so no
  phase-only design heuristic is one-click adoptable.
- Source tests: targeted new tests `5 passed`; complete
  `tests/test_medical_writing_authoring_prefill*.py` `578 passed, 17 warnings`;
  frontend build `1955 modules transformed` passed. The r10 API was not
  regenerated after this source change, so live proof of the new binding is
  intentionally still pending; r10's project and runtime remain evidence-only.
- Findings: P0/P1 AI-first identity adoption remains open until live proof;
  P1 deterministic design-mode leak is repaired at source/test level; P1
  greenfield auto-search side effect and P2/P3 AI-role receipt visibility
  remain product observations. Clean-round credit remains **0**.
- Next safe action: new isolated r11 pass, create a different project via
  visible UI, allow the automatic initial prefill/search to settle, then click
  visible `更新建议` exactly once against the attached snapshot and prove one
  title single-adoption receipt plus competitor/design fail-closed behavior.
  Preserve r9/r10 rows; do not start the senior-monitor role.

## 2026-08-05 follow-up10: r11 build-align recovery and live project-fact adoption

- The first r11 pass was blocked before authoring by a real Vite/API build
  receipt race (`web-d219846e6438bad4` expected `api-0d5a53ccca8751e1`, while
  the already-running API reported `api-8940d3cd38b56011`). Shared monitoring
  files were still changing, so the API was not restarted. A test-only frozen
  Vite snapshot under `/private/tmp/mw-p0-engineer-r11.GoQYbK/vite-snapshot/`
  was served with the expected backend receipt explicitly aligned to the live
  API. No product source, stable API, r42/v36, or monitoring data was changed
  by this alignment.
- Same Cursor session `c8236237-d9b5-4998-b7fb-2a6167ae278b` resumed with
  route `cursor/cursor-cli/auto`, no fallback. Existing project
  `proj_user_d0192cbe211f`, journey `mwjourney_37e2da88b6d05246109e`,
  QZ-CRSNP03 / 慢性鼻窦炎伴鼻息肉 / II期 was used; no new project was made.
  Build gate cleared and the API role receipt was the required DeepSeek V4
  Flash thinking/max (independent + translation support), PaddleOCR-VL-1.6,
  and oMLX Hy-MT2 configuration.
- Live visible evidence proves the second repair: automatic mount prefill
  rev1→2; one automatic search snapshot (`wref_search_e35abff6fdac05a9ad22`,
  43 candidates); exactly one visible `更新建议` rev3→4; three exact
  deterministic title candidates are `supported` + `batch_allowed`, each has
  three complete `current_project_fact` bindings to one catalog ID/SHA; one
  actual visible `采用推荐` on `mwprefillcand_37f3d4b98beaf58e` returned HTTP
  200 and advanced rev4→5. Audit event:
  `mwjourney_event_9fe251e2041c5ce599d032cd`.
- `framing.design_pattern` is now `pending_decision`/`manual_only` with zero
  bindings and no single-adopt control. 26 design/PICOS/competitor-like
  candidates remain manual-only/insufficient. Reservations and physical AI
  attempts are zero; r9/r10 project and reservation IDs were read back
  unchanged. No OCR, translation, corpus, PICOS completion, full draft, or
  Word artifact exists.
- Unexpected side effect requiring follow-up: the automatic search pipeline
  emitted `research_pipeline_progress` triage events and ended
  `failed/competitor_triage_stale` without a user triage click; no model
  reservation or source-data rewrite accompanied it. This is recorded as an
  automatic pipeline/harness contract issue, not silently accepted as a
  successful competitor pass. Evidence is in
  `/private/tmp/mw-p0-engineer-r11.GoQYbK/evidence/r11ba_final_summary.json`,
  `r11ba_post_adopt_readback.json`, `codex_events_readback.json`, and the
  follow-up report
  `runs/role_acceptance/mw_protocol_p0_20260805_round11_engineer_cursor_agent_build_align_followup.md`.
- Verdict remains **NOT_CLEAN**, clean streak 0: the focused identity contract
  is live-accepted, but full Protocol/Word acceptance is not. Next safe action
  is read-only first-principles diagnosis of the stale triage transition and a
  minimal offline repair if justified; do not rerun triage/OCR/translation or
  start the senior-monitor role until that boundary is understood.

## 2026-08-05 follow-up12: live stale-revision proof

- Fresh r12 API `8944` loaded the repaired source (`api-02c8acaa783980b7`);
  Vite `5225` used a temporary frozen snapshot with a matching receipt. The
  declared Cursor route resumed the same session
  `c8236237-d9b5-4998-b7fb-2a6167ae278b` and used visible Playwright.
- The intended first project was `proj_user_923a5927aba7` / journey
  `mwjourney_c4ef3a5e37fc36286605` (QZ-UC04 / 溃疡性结肠炎 / I期). Its fresh
  search returned 193 candidates; automatic triage completed once with 2
  deterministic + 4 DeepSeek V4 Flash chunks, 6/6 succeeded, status
  `review_ready`, no retry. One visible `更新建议` and one field-level
  `采用推荐` adopted the exact current-project-fact title, rev4→5.
- Live stale proof: before and after adoption the same run
  `ct_run_a72c6fdb691d3ca33d6e` remained `review_ready`, `stale_reason` empty,
  snapshot unchanged, material-facts hash unchanged, while captured run
  revision stayed 3 and journey revision advanced 4→5. Title binding audit
  shows 3/3 current-project-fact bindings and `supported`/`batch_allowed`;
  design remains `manual_only`/`insufficient`. This is live acceptance of the
  stale-revision repair, not a full Protocol acceptance.
- Harness issue: the shepherd's first create-form selector timed out, then its
  debug retry created a second test project `proj_user_d5634f5129e5`. The
  accepted claims use the first project only; the extra project is test-created
  evidence and is a P1/P2 cleanliness/harness finding, not hidden or deleted.
  r9/r10/r11 were not mutated; r12 API/Vite were stopped after evidence.
- No OCR, translation, corpus-admission, PICOS, full draft, or Word artifact
  was attempted. Overall clean streak remains 0. Next safe action is a fresh
  clean r13 engineer runtime with a corrected create-form shepherd, then the
  complete Protocol path; do not reuse the contaminated r12 project store or
  dispatch the senior-monitor role yet.

## 2026-08-05 follow-up11: stale-triage root cause and offline repair

- Read-only SQLite evidence identified the exact transition: the frozen triage
  run was created at journey revision 3 with material-facts hash
  `b85ae37f...`; the title adoption advanced the journey to revision 5, while
  `_material_facts_hash` included `journey_revision` even though the adopted
  `framing.document_title` is not a relevance-driving triage fact. The run was
  therefore marked `stale` by the status read. The run's deterministic chunks
  themselves are truthful (`explicit_non_pharmacologic_intervention` /
  `no_public_protocol`) and no AI reservation exists; this is not a registry
  no-results claim.
- Minimal source repair in
  `services/api/app/medical_writing_competitor_triage.py`: when journey CAS
  revision differs, recompute material facts at the run revision before
  comparing hashes. Revision-only derived identity adoption is therefore
  allowed to keep the frozen run; any product/indication/phase, design,
  mechanism, product-profile, population, PICOS, or search-condition change
  still changes the hash and remains stale/fail-closed. Immutable stale rows
  are not rewritten.
- Offline proof: new title-only revision regression plus the existing stale
  tests `32 passed`; research-pipeline/recovery `29 passed`; full competitor
  triage + durable suite `438 passed, 17 warnings`. r11 API has not been
  restarted and its already-stale run remains evidence-only; live proof needs
  a fresh isolated runtime loaded with the repair.
- Next safe action: create one fresh isolated r12 engineer runtime, load the
  patched source before automatic search/triage, and repeat only the bounded
  create→snapshot→single title adoption probe to prove the triage run remains
  non-stale. Do not mutate r11, r9, r10, frozen upstream rows, or start the
  senior-monitor role.

## Follow-up13–15 — durable waiting repair, planner root cause, and r15 boundary

- r13 isolated an orphan `preparing` projection after visible preparation
  admission. Waiting resumes now enqueue exactly one idempotent durable
  continuation and never fall through to a fresh `execute_stages` run;
  focused recovery/waiting/preparation tests passed (`68`).
- r14 proved that continuation but exposed `awaiting_stage_admission` missing
  from parent reconciliation. The bounded repair projects that state to
  `awaiting_preparation_admission` with an enabled CTA when deferred items
  remain; focused validation passed (`101`). No stable or immutable rows were
  rewritten.
- Fresh r15 (`/private/tmp/mw-p0-engineer-r15.FWUf2T`) used API 8947/Vite 5228
  with the required DeepSeek V4 Flash thinking/max, PaddleOCR-VL-1.6, and
  Hy-MT2 role receipts. Visible Playwright created one project
  `proj_user_2a9462823af5` / `MW-II-84674160` (QZ-SLE05, SLE, II期). Search
  returned 343 candidates and 76 public docs; one visible triage confirmation
  retained 18/18 successful chunks (3 deterministic + 15 DeepSeek), with 56
  retained and 287 excluded. Preparation used PaddleOCR-VL-1.6; 55/58 were
  prepared and 3 unusable OCR outputs failed closed. Six visible admission
  actions proved the waiting-stage repair without duplicating completed OCR.
- r15 reached translation/corpus admission. Hy-MT2 completed 18 chunks; only
  `wref_translation_item_907ea10c473d85fa2cdd8591` (NCT02349061,
  `Prot_000.pdf`) remained `failed_retryable`. Audit and item payload show
  `document_plan_failed` with `chapter_176_duplicate_title` and
  `planner_duplicate_chapter_identity`; no provider-connectivity failure was
  recorded. Replaying its 1,614 OCR spans found fallback chapters 173 and 177
  titled `REFERENCES` and `References`; exact-string dedupe missed the
  casefold collision, while the validator correctly failed closed.
- Minimal repair in `services/api/app/chapter_translation_pipeline.py` now
  deduplicates fallback titles using normalized whitespace + casefold, matching
  the validator. A focused regression passed (`5`); direct r15-span replay now
  yields 178 unique-title fallback chapters with complete ordered coverage.
  The full round8 file was `37 passed, 1 failed`; the lone failure is the known
  older batch-retry expectation (`failed_retryable` versus current
  candidate/fidelity statuses), not caused by this normalization change.
- r15 first stopped at `awaiting_corpus_admission` with no substantive draft
  or Word. The same Cursor session `5e4e7130-acf7-4fef-89be-e945e8c33213` was
  resumed once at the explicit actionable boundary using the one-item retry
  prompt. Only that failed item may mutate, followed by source-grounded
  medical/PICOS admission and full Protocol/Word verification. The
  continuation is pending a natural runner terminal result; no fixed polling
  or redispatch is used.

Current verdict remains **NOT_CLEAN**, clean streak `0`: waiting-stage
reconciliation is live-proven and the planner root cause has a minimal
offline repair, but substantive Protocol and Word acceptance is not shown.
Do not start the senior role until the engineer route reaches a clean full
route.

## Follow-up16–17 — semantic span repair and current no-loss pause boundary

- Follow-up16 added `_research_span_cap_rank` to prefer explicit anchor
  headings and complete substantive passages, while down-ranking references/
  TOC, generic cross-references, heading-only fragments, abbreviation walls,
  and oversized HTML tables. Both span-cap call sites use the semantic key.
  Focused readiness tests passed (`12`); the translation-batch/chapter-
  pipeline set passed (`100%`); and the research-pipeline minimum/
  validation/progress set passed (`58`). No r42/v36 or product runtime data
  was changed by this offline repair.
- Fresh r17/r18 engineer route used isolated runtime
  `/private/tmp/mw-p0-engineer-r18.fWUe1r`, API `8950`, Vite `5230`, matching
  build `api-5607f2bcd758c68e` / web `web-e3cd9e93be9339b7`, and Cursor/auto
  session `5e4e7130-acf7-4fef-89be-e945e8c33213`. Initial project count was
  zero; visible Playwright created exactly one project
  `proj_user_a6ee76a0258b` (`QZ-AST04`, 哮喘, II期), journey
  `mwjourney_f32404c5313e80be7343`, and translation batch
  `wref_translation_batch_8f99dd27d00d690c693e295e`.
- Build/role receipts passed: independent and translation-support DeepSeek
  `deepseek-v4-flash`, thinking enabled/max; official `PaddleOCR-VL-1.6`;
  body translation `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`. Search returned `770`
  records and `87` public Protocol documents. Visible triage first reached
  `20/21`; one visible continuation recovered it to `21/21`. The basket
  confirmation locked `770` candidates (`69` retained, `701` excluded),
  and preparation completed `68` items through visible admissions.
- Final translation state was `completed_with_blocked`: `20` items, `5`
  `candidate_ready`, `11` `fidelity_blocked`, and `4` `excluded`. All four
  anchors were represented and no reference/TOC/`CCI`/`无`/`包含：` winner was
  observed. The semantic rank nevertheless allowed an eligibility intro
  (`44` Chinese characters; no criterion list) and a heading-only objectives
  candidate; stronger eligibility/objectives passages were fidelity-blocked
  (unit/numeric/abbreviation/comparison/controlled-term codes).
- The medical gate rejected the inspected incomplete eligibility item, but a
  later visible batch-confirm path admitted `5` items including that thin
  eligibility brief. Final read-only DB state: one project, one journey at
  revision `7`, five approved/admitted medical-review records, and no
  `objectives_endpoints` admitted. The pipeline remained
  `awaiting_corpus_admission` at `90%`; PICOS and writing controls stayed
  disabled. A visible `更新建议` returned `409` because its prefill call was
  still in flight. No substantive draft or `.docx` was produced or opened.
- Verdict is **NOT_CLEAN**. The primary blocker is incomplete/fidelity-blocked
  evidence; the additional P1/P2 contract finding is that one-click batch
  confirmation can admit a candidate carrying
  `incomplete_eligibility_criterion` despite the substantive medical gate.
  The `409` is an idempotent in-flight outcome, not a provider outage. The
  China registry probe was reachable without a stable public API and yielded
  no trial hints.
- At the user-requested no-loss pause boundary (2026-08-06 08:58 +0800), the
  r17 runner terminated normally (`rounds_completed=1`, fallback `null`,
  failure `null`). API session `42521` and Vite session `77232` were stopped;
  health requests subsequently timed out, confirming the isolated services
  are down. Evidence remains under
  `/private/tmp/mw-p0-engineer-r18.fWUe1r/evidence/`; the runner report is
  `runs/role_acceptance/mw_protocol_p0_20260805_round17_engineer_cursor_full_protocol_semantic_span_selection.md`.
- No senior role, second clean engineer round, Synopsis/CSR work,
  r42/v36 clone, medical-monitoring file, or production service was started.
  Exact resume point: the r17 report plus the read-only final DB state above.
  Next safe action: repair the substantive span/medical-admission contract
  (or obtain complete fidelity-passed eligibility and objectives through the
  allowed visible retry) in a fresh isolated route; only after a substantive
  Protocol Word is opened and accepted may the senior role or clean-round loop
  resume.
