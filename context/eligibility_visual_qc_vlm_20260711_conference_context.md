# Conference Context: eligibility_visual_qc_vlm_20260711

Created: 2026-07-11 20:07:30
Objective: Design and critically review the production architecture for immutable eligibility visual-QC decisions, effective evidence projection, and an independently runnable clinical-photo VLM gateway using real D001 and MY009 source boundaries; no clinical conclusion generation and no production write before Codex review.
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: Hermes provider `aishuo`, model `MiniMax-M3`, per the user's current project-wide routing override. Historical OpenCode Go Minimax runs are not the active route.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- Current durable evidence schema and store: `services/api/app/sqlite_runtime_store.py`.
- Current evidence orchestration and public projection: `services/api/app/eligibility_evidence_tasks.py`.
- Current worker, OCR boundary and controlled artifact store: `services/api/app/eligibility_evidence_worker.py`, `services/api/app/ocr_gateway.py`, `services/api/app/eligibility_artifact_store.py`.
- Current eligibility review/effective-state boundary: `services/api/app/eligibility_review_workflow.py` and `packages/contracts/workbench_contracts/models.py`.
- Current focused tests: `tests/test_sqlite_eligibility_evidence_tasks.py`, `tests/test_eligibility_evidence_worker.py`, `tests/test_sqlite_eligibility_review_store.py`.
- Real-project safe execution records: `records/active_slices/eligibility_next_slice_20260711/REAL_OCR_WORKER_LOOP_V8.md` and `records/active_slices/eligibility_next_slice_20260711/REAL_PDF_PAGE_PIPELINE_V8.md`.
- D001 and MY009 current source identity/inventory is authoritative only through the current project source manifest and raw intake services. Do not read clinical source bodies or infer subject eligibility in this architecture conference.

## Scope

- In scope: immutable visual-QC records; compare-and-set current QC pointer; effective evidence status projection without evidence mutation; reviewer identity/reason/audit; sampled pass/fail/manual-review semantics; clinical-photo media classification and independently deployable VLM gateway contracts; PHI-safe request/response/logging; retry/idempotency/model-version/source-version controls; D001/MY009 isolation; adversarial and restart tests.
- Out of scope: clinical eligibility conclusions; diagnosis or lesion-severity conclusions; randomization release; VLM model selection based only on vendor claims; production writes by delegated agents; frontend implementation; mobile design; browsing; direct inspection of clinical images; changes to current source files.

## Success Criteria

- Produce a minimal implementable schema and state machine that never mutates an evidence span or equates visual QC with medical confirmation.
- Define effective projection rules for `needs_visual_qc`, `sampled_pass`, `sampled_fail`, and `manual_review_required`, including stale QC after source/extraction/model drift.
- Define API/CAS/idempotency/privacy boundaries and exact conditions that reject cross-project, stale, tampered, duplicate, or unauthenticated writes.
- Define an independent VLM gateway request/response schema, media routing, fail-closed behavior, model/profile/version capture, and no-PHI logs.
- Define D001/MY009 real-project test probes and synthetic adversarial tests without exposing or reusing legacy conclusions.
- Identify conflicts and hard production gates. Recommendations remain advisory until Codex verifies and authorizes code changes.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-11 20:07:30: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Generated OpenCode Go chair route was rejected before execution and replaced with the user-mandated `aishuo/MiniMax-M3` route. Actual provider/model markers remain mandatory evidence.
- 2026-07-11: Three bounded participant runs completed. Qwen experienced two transient HTTP 500 responses and recovered within its controlled retry; no silent substitution occurred. Mimo and Reasonix DeepSeek Flash completed on their assigned routes.

## Codex Supplemental Audit Observations For Chair Review

These observations were produced by three read-only Codex SubAgents after the participant packet was launched. They are not participant consensus and must be independently challenged by the chair:

1. Current medical review commit validates evidence ownership/current source revision but does not require an effective visual-QC pass. A `sampled_fail` or unreviewed span may therefore support a decisive medical action today. The AI batch path checks processing state but not an effective QC record. Treat this as P0 until disproved from current code.
2. Evidence spans have an immutable UPDATE trigger but no DELETE trigger. Additive migration should protect both operations; historical spans must not be repaired in place.
3. `evidence_processing_state` is client-submitted in the medical action contract. Server-side effective evidence projection must be authoritative; a client cannot self-assert completion.
4. PDF render parent success and complete OCR-child creation must be atomic. Parent/child/artifact project, subject, source revision, page, profile and hash identities must be checked in the same SQLite transaction; an expired lease owner must not finalize.
5. Current worker launcher can configure OCR model and profile independently. The implemented route must bind profile name to an immutable profile digest/model/prompt/gateway contract and fail closed on mismatch.
6. The legacy enrollment app has external OCR fallback, partial-result continuation and PHI-bearing logging/cache patterns. None of those patterns may be copied. The new workbench currently fails VLM jobs closed and must keep doing so until an independently runnable, audited gateway passes controlled tests.
7. Delegate suggestions that `manual_review_required` evidence may be used through a generic override, or that a VLM model may silently fall back, are presumptively unsafe. Require a separate human visual-QC record that reaches `sampled_pass`; never reinterpret `manual_review_required` as pass.
8. VLM outputs must be bounded to media/capture quality and controlled descriptors. They must not output diagnosis, lesion severity, efficacy, protocol deviation, eligibility or treatment recommendations. PHI-bearing image bytes must not transit Hermes/Reasonix/OpenCode logs or external fallback routes.

## Chair Route Runtime Status

- `aishuo/MiniMax-M3` was invoked twice on the required route. The actual aishuo custom endpoint and `MiniMax-M3` model markers were observed in both stdout logs.
- Both the initial run and one delayed controlled retry exhausted three attempts with HTTP 529 cluster overload. The generated chair file therefore remains a placeholder and is not accepted.
- No fallback chair was used. Completed participant outputs are retained; a future same-route chair retry can resume from this packet. QC/VLM production writes remain gated until chair and main-venue review complete.
- A later same-route retry recovered and produced the substantive chair package in `runs/conference/eligibility_visual_qc_vlm_20260711/hermes_lead.md`. The two HTTP 529 runs remain retained; no fallback chair was used.
- Since the participant packet was frozen, Codex completed the separate SQLite v10 PDF parent-child workstream: D001 1 page and MY009 14 pages atomically produced 30 GLM/Paddle children, all succeeded and all remained `needs_visual_qc/not_reviewed`. Chair statements that page-child expansion is still missing are therefore stale and must not be carried into main-venue conclusions.
