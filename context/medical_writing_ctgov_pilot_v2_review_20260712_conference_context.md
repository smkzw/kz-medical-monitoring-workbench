# Conference Context: medical_writing_ctgov_pilot_v2_review_20260712

Created: 2026-07-12 10:07:41
Objective: Review the completed ClinicalTrials.gov protocol corpus pilot v2 through pass7, challenge evidence completeness, safety, rights and production-integration boundaries, and determine the next bounded product step without exposing or translating source text.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- The user's project-specific override requires every future Hermes sub-venue review, synthesis and chair task to use exact `aishuo / MiniMax-M3`.
- Independent participants are Hermes `buddy / glm-5.2`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- The `aishuo / MiniMax-M3` chair runs only after the three participant outputs are available or explicitly terminally failed. No silent chair substitution is allowed.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/research/medical_writing_ctgov_protocol_corpus_20260711/PRODUCTION_FEATURE_DECISION.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/TASK_RECORD.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/run_pilot_v2.py`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/test_run_pilot_v2.py`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/reports/pilot_v2_manifest_pass7.json`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/reports/negative_path_observations.json`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/reports/atopic_dermatitis_phase2_query_index_pass5.json`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_v2/reports/pnh_phase3_query_index_pass5.json`
- The six bounded Markdown incident/correction logs under `pilot_v2/logs/`.
- Raw API bodies, downloaded PDFs, extracted source text and rendered pages are intentionally excluded from model read lists.

## Scope

- In scope: evidence completeness, genericity, deterministic replay, query pagination, document/version lineage, negative paths, security triage limits, rights gate, translation-admission boundary and next bounded product step.
- Out of scope: reading or translating protocol text, visual acceptance, medical competitor adjudication beyond recorded decisions, production code/UI/database integration, corpus/RAG admission and legal approval.

## Success Criteria

- Independently test the pass6 evidence against every `TASK_RECORD.md` success criterion.
- Identify reproducible P0/P1 defects and distinguish pilot-acceptable limitations from production blockers.
- Confirm whether two indications/phases and multiple sponsors/doc types were actually exercised without using first-pilot NCT inputs.
- Challenge whether any evidence supports production merge; reject unsupported rights, security, regulatory-Chinese or RAG claims.
- Return one bounded next-step recommendation with explicit exit criteria.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not expose raw protocol/SAP text, local source paths, extracted excerpts or rendered clinical pages in conference output.
- Public availability is not evidence of translation, model-processing, retention, corpus or redistribution rights.
- A static PDF token scan is not malware scanning or a production quarantine control.

## Loop Log

- 2026-07-12 10:07:41: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Generic initialization proposed a GLM chair; this was replaced before dispatch by the user's exact `aishuo/MiniMax-M3` sub-venue override.
- Two Codex SubAgent audits were attempted but failed before execution because the Codex subagent quota was exhausted. They are recorded as tool failures and provide no review evidence.
- The three participants completed three same-session rounds. MiMo and GLM reproduced a real pagination-total defect: the pilot read `totalCount` only from the final page even though ClinicalTrials.gov returned it on the first page.
- Codex fixed the defect before chair dispatch. Pass7 retains the first non-null total, rejects cross-page drift, fails if no total is supplied, adds an environment/script fingerprint and preserves immutable prior passes.
- Four pilot unit tests pass. Pass7 ran twice successfully from the immutable snapshots; AD now verifies 453 returned = 453 reported across five pages, PNH verifies 49 = 49 across one page. Manifest SHA-256 is `4e477844968c8dc6a113561f5634ed1cef3be5ca05feb4979cdc54b1115bc946`.
- Codex rejected GLM's 13-hour-gap concern as a cross-day continuation artifact, not a source-integrity defect. Codex also rejects treating failed SubAgent quota attempts as a product P0; they remain a review-process gap only.
