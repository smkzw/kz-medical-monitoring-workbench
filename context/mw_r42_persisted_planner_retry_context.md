# Task Context: mw_r42_persisted_planner_retry

Created: 2026-07-31 12:02:00
Objective: Repair the r42 medical-writing translation planner persisted executor so deterministic structural failures receive one same-model corrective retry with durable attempt lineage and specific validation codes before Pro escalation, then verify without rerunning completed triage/download/OCR stages.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/mw_r42_a1_release_retest_context.md`
- `context/mw-protocol-progress-batch_context.md` lines 211-379
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/FIX_RETEST_LEDGER.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/TRANSLATION_PLAN_FAILURE_DIAGNOSIS_20260730.md`
- Current source and tests under `services/api/app/` and `tests/`; the filesystem is authoritative.
- Recovery lineage: original parent Session `019f92f7-8268-7f00-9544-9b7c61ae5128` was deleted. This is a reconstructed continuation and must not be described as restored verbatim history.

## Scope

- In scope: the persisted document-planning executor contract, production upper-layer adapter, durable stage-run attempt metadata, stable planner validation error codes, translation-batch propagation/retry behavior, and focused/adjacent deterministic tests.
- Allowed source paths: `services/api/app/chapter_translation_pipeline.py`, `services/api/app/writing_reference_upper_layer_execution.py`, `services/api/app/writing_reference_upper_layer_adapters.py`, directly required contracts/repository/schema files, and directly related tests.
- Allowed task-record paths: this context, the guard-owned review/metrics/run records, and a bounded decision/verification note if needed.
- Out of scope: frontend changes, OCR/download/preparation changes, monitoring-subsystem files, full corpus/document/DOCX/Word work, live service startup, and any product-runtime database mutation before the code review gate.
- External discovery decision: no new dependency, tool, model, architecture, or executable component is being adopted. The current diagnosis and existing in-repository durable executor are sufficient for this surgical repair; external discovery would not change the method.

## Success Criteria

- A deterministic Flash planner structural failure receives exactly one corrective retry on the same model before any Pro escalation.
- Both Flash calls preserve the same artifact, extraction revision, input/source hash, prompt contract, OCR lineage, owner, and stage-run identity; attempt metadata and provider call count remain durable and auditable.
- Successful second-attempt output becomes the active plan without Pro invocation.
- If both Flash attempts fail structurally, Pro escalation remains eligible and preserves the Flash failure lineage.
- Planner validation exposes stable primary/specific codes for missing chapters/role, gap, overlap, out-of-bounds, missing required boundary, duplicate identity, and unstructured output instead of collapsing to `deterministic_upper_layer_output_invalid`.
- Same-artifact sibling items retain derived-failure lineage; after the source plan succeeds on retry, all associated failed items can be reactivated without fabricated provider calls.
- Protocol-only, effective OCR, fidelity, and anchor-readiness gates remain unchanged.
- Diagnosis section 6 test groups pass, plus focused adjacent upper-layer and translation-batch regressions.
- No triage, download, OCR, live service, or five-item product rerun occurs during implementation verification.

## Risk Boundaries

- Preserve the completed r42 state: project `MW-III-1A3A1248`, 19/19 outer triage, 665/665 candidate lock, 90 prepared Protocol/combined artifacts, 89 OCR pass plus one medically confirmed residual issue.
- Do not rerun triage, downloads, OCR, the full translation batch, or the five failed items during this code phase.
- Do not modify runtime SQLite stores, provider registries, role bindings, credentials, or monitoring-subsystem files.
- Do not weaken Protocol-only, OCR-effective, scientific, translation-fidelity, source-lineage, or anchor-readiness gates.
- Do not persist raw provider responses or sensitive clinical text merely to improve diagnostics; persist bounded structured metadata only.
- Codex is the final authority for code review, tests, product-runtime replay authorization, and user delivery.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-31 12:02:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-31 12:03: Re-anchored from the r42 recovery package and current source. Confirmed the persisted adapter discards the legacy `invoke` callback, the shared service retries only transient exceptions, and deterministic planner failures currently escalate after one Flash provider call.
- 2026-07-31 12:51: User explicitly resumed the paused goal. Re-read the current global and project `AGENTS.md`, the `mw-workbench-wave-audit` skill, this task record, and current source. The filesystem contains the persisted same-model structural-correction implementation and specific planner codes; no live r42 replay has occurred. The review and metrics records remain incomplete, so code acceptance and the controlled five-item replay are still pending.
- 2026-07-31 12:51: Current implementation files are dated 2026-07-31 12:06-12:16. The workbench directory is not a Git worktree, so acceptance must use direct source inspection, bounded file/path accounting, deterministic tests, and runtime evidence rather than a Git diff.
- 2026-07-31 12:53: Re-ran the six directly affected test modules against the current filesystem: `175 passed, 17 warnings in 7.21s`. The warnings are existing SWIG-type and FastAPI `on_event` deprecations; there were no test failures.
- 2026-07-31 12:54: Verified the production persisted adapter discards the legacy `_invoke` callback. Therefore `bounded_structural_retry` on the legacy path cannot stack with the new service-owned two-call Flash sequence. The current production sequence remains Flash attempt 1, Flash structural correction attempt 2, then eligible Pro escalation.
- 2026-07-31 12:57: Read-only SQLite verification of the authoritative r42 runtime still shows batch `wref_translation_batch_ad27f97d2f06c106b0c2a158` at `partial_failure`, attempt 1, with 2 `candidate_ready`, 13 `excluded`, and exactly 5 `failed_retryable`; its latest upper-layer stage run remains dated 2026-07-30. No product replay has occurred.
- 2026-07-31 12:58: Prepared and preflighted `prompts/codex_mw_r42_persisted_planner_retry_review.md`. An independent reviewer is restricted to the listed source/tests and one runner-owned report; product code, services, providers, SQLite, OCR, triage, translation, and the five failed items remain untouched during review.
- 2026-07-31 13:04: Independent review returned `NOT READY`. P1: a batch item retry does not enter the persisted upper-layer fingerprint, so any failure already written under the current invocation contract would replay forever. P2: document-planning deterministic input/manifest defects can be marked escalatable and invoke Pro without completing an eligible same-model correction. The controlled five-item replay remains blocked until both findings and their persisted-path tests pass.
- 2026-07-31 13:06: Preflighted a bounded remediation-proposal task at `prompts/codex_mw_r42_persisted_planner_retry_remediation.md`. The same native Codex reviewer may write only `runs/codex_mw_r42_persisted_planner_retry_remediation.md`; product code and runtime remain untouched during proposal generation.
- 2026-07-31 13:09-13:35: Implemented persisted retry generation, separate retry/escalation ancestry, canonical-source sibling protection, and planner-specific Pro eligibility. Independent review first exposed two blocking defects; remediation and a second acceptance pass closed both. The six-module offline gate reached `189 passed, 17 warnings`.
- 2026-07-31 13:35-14:00: Before any API retry, an isolated APFS clone exposed a legacy-r42 payload gap: the two-item artifact lacked additive source/derived fields. Added exact persisted Flash-owner inference with zero/multiple-candidate fail-closed behavior. Independent review then found an `interrupted`-parent compatibility regression; restored that status and added a modern explicit-lineage test. Final offline gate: `190 passed, 17 warnings`; independent re-review: READY.
- 2026-07-31 14:04-14:07: Started one backend against the isolated clone only. Startup preserved attempt 1, 23 stage runs, and `2 candidate_ready / 13 excluded / 5 failed_retryable`. Submitted exactly one retry request, idempotency key `r42-planner-generation2-20260731`; HTTP 202, batch attempt 2, durable job `mwjob_2d6bbc9bad1e71d030c3afa5`.
- 2026-07-31 14:07: Durable job ended failed at attempt 3/3 and batch returned to partial failure. Retry identity worked: four artifacts produced exactly four generation-2 Flash source runs with prior Flash parents; the two-item artifact used one canonical source and one derived sibling. Three Flash plans succeeded and were persisted. One artifact failed Flash correction and Pro with stable `planner_duplicate_chapter_identity`. The three successful-plan items then failed at `translating_hy_mt2` with internal `CompositePipelineUnavailableError` / `body translation model unavailable: HTTPError`; user-facing payload remained sanitized as `translation_generation_failed`.
- 2026-07-31 14:08: Isolated API shut down cleanly. Original r42 remained unchanged at attempt 1, 23 stage runs, and `2/13/5`. Durable replay evidence is in `runs/mw_r42_planner_retry_controlled_replay_20260731.md`. No further retry is allowed until the Hy-MT2 HTTP route and the remaining duplicate-identity planner case are independently diagnosed.
- 2026-07-31 14:08-15:33: Verified the user-identified complete local Hy-MT2 model at `/Users/smkzw/huggingface/hub/dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`; oMLX already served it on IPv4 `127.0.0.1:8000`. Stopped the mistakenly initiated duplicate download and moved its incomplete 4.5 GiB snapshot intact to the recoverable quarantine under `runs/execution/mw_r42_hymt2_model_recovery_20260731/`. A gate-owned marker smoke returned HTTP 200 with the exact model and left zero leases.
- 2026-07-31 14:20-15:33: Replaced provider-owned chapter identities with deterministic server-canonical IDs after all title/range/boundary/coverage gates. The prompt contract moved to `flash_toc_planning_v0_3_server_canonical_ids`. A separate, additive v2-to-v3 supersession/migration lineage was implemented because ordinary retry remains same-contract. Independent review found and then accepted an exact generation-1 root -> generation-2 v2 ordinary retry -> generation-3 v3 supersession fixture. Final six-module gate: `198 passed, 17 warnings`.
- 2026-07-31 15:38: After all preconditions passed, submitted exactly one clone-only retry using idempotency key `r42-planner-contract-v3-generation3-20260731`. Durable job `mwjob_50e0af0d6d78cb51e202efd1` completed on execution attempt 1/3. Clone terminal state: batch `completed_with_blocked`, attempt 3, `4 candidate_ready / 15 excluded / 1 fidelity_blocked / 0 failed`; 33 stage runs and 16 plans. Three v2 plans migrated with zero planner calls; the two-item artifact used one v3 planner root and one same-model structural correction, with no sibling planner call.
- 2026-07-31 15:39: Original r42 remained byte/state unchanged at batch attempt 1, `2 candidate_ready / 13 excluded / 5 failed_retryable`, 23 stage runs, and 9 plans. Ports 55342/55343 were closed and the oMLX gate returned to zero active/queued leases.
- 2026-07-31 15:45-16:09: Read-only diagnosis proved the remaining `unit_1:source_abbreviation_missing` was a product false positive: ordinary all-caps protocol words `VISIT` and `SCHEDULE` were treated as clinical abbreviations. Added only those two general stopwords; bumped Hy prompt to `hy_mt2_chapter_translation_v0_30_protocol_heading_abbreviation_stopwords` and alignment contract to `cms_seg_aligned_units_v36_protocol_heading_abbreviation_stopwords`, producing downstream fingerprint `c61a5e2d775c14302f3b0853ac09cc5785a230d3108e0b2f2d42cdf8aa6be79d`. Independent acceptance initially rejected one confounded ECG test, the fixture was corrected without product changes, and targeted re-review returned READY. Parent verification: two-module suite `232 passed, 17 warnings`; six-module suite `198 passed, 17 warnings`.
- 2026-07-31 16:09: User requested no-loss pause after the current subtask. No v36 runtime retry was authorized or performed. Detailed pause checkpoint: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.

## Pre-launch acceptance contract added by user

- Before production launch, run the requested routes serially: Grok Build `grok-4.5` (fallback Cursor CLI `auto`), Pi/DeepSeek `deepseek-v4-flash` at max, and native Codex subAgent `gpt-5.6-luna` at max during 08:00-22:00 Beijing time (outside that window fallback Pi/Alibaba `qwen3.8-max-preview`).
- Each route must test two roles: engineer and lazy but visually sensitive senior medical-writing expert.
- Each role/round covers at least three different non-oncology indications across phase I/II/III with different study designs. Each round starts from a clean dedicated test environment.
- Except the Pi/DeepSeek route, user-perspective testing must use visual Playwright and real clicks, not API-only substitution.
- Prompts must vary and remain realistic/open enough for genuine exploration. Continue test-review-fix-retest until every tester and every role has two consecutive rounds with zero P0/P1/P2/P3/P4 findings.
