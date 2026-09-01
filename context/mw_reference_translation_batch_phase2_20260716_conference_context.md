# Conference Context: mw_reference_translation_batch_phase2_20260716

Created: 2026-07-16 08:14:40
Objective: 设计并实现医学写作竞品Protocol/SAP批量监管中文候选：仅处理内容confirmed或user_overridden且结构审核approved的当前有效片段；保留来源、版本、失败隔离、持久恢复和医学审核门禁；不得自动医学批准或语料准入
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Sub-venue chair: Hermes `buddy / glm-5.2`.
- Participants: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- Additional independent consultant required by the user: Grok Build `grok-4.5`; Grok is not the chair.
- Every participant and the chair run three rounds in the same session: independent analysis, skeptical challenge, and corrected final pass. The chair starts only after participant outputs are available and explicitly compares them.
- Codex remains the final authority for source interpretation, implementation, tests, browser/visual acceptance, clinical/regulatory conclusions, and production writes.
- The commands emitted by the initializer that reference Grok as chair or `deepseek-v4-flash` are obsolete for this task and must not be executed.

## Source Of Truth

- `AGENTS.md` and `/Users/smkzw/.codex/AGENTS.md` for current conference routing and execution rules.
- `records/active_slices/medical_writing_reference_batch_preparation_20260716/TASK_RECORD.md` and `SOFT_PAUSE_RESUME.md` for the accepted phase-1 boundary.
- `services/api/app/writing_reference_preparation_batch.py` for persistent batch orchestration patterns.
- `services/api/app/writing_reference_translation_service.py`, `writing_reference_repository.py`, `writing_reference.py`, and relevant routes in `main.py` for existing single-span translation, review, and admission contracts.
- `packages/contracts/workbench_contracts/models.py` for typed API/state contracts.
- `frontend/src/features/writing-reference/ReferencePreparationBatchPanel.jsx`, `WritingReferencePanel.jsx`, and `frontend/src/styles.css` for the existing authoring workspace.
- `tests/test_writing_reference_translation_service.py`, `tests/test_writing_reference_ai_contract.py`, `tests/test_writing_reference_api.py`, `tests/test_writing_reference_preparation_batch.py`, and `tests/test_frontend_medical_writing_contract.py` for executable requirements.
- Real accepted browser/API evidence: PNH project `proj_user_4bc29da4ac72`, RA project `proj_user_8c78cc4421b6`; participants may read recorded task evidence but may not write either runtime.

## Scope

- In scope: derive a batch only from current effective source artifacts and extraction revisions; select only spans whose document validation is `confirmed` or `user_overridden` and whose structure review is `approved`; create persistent, idempotent, source-bound regulatory Chinese candidate jobs; support partial success, failed-only retry, refresh/service-restart recovery, and transparent reasons for excluded spans; place the user workflow in authoring `译文审核`, not the main editor.
- Out of scope: auto-overriding file validation, auto-approving structure, auto-approving translations, auto-admitting corpus evidence, translating unapproved spans, changing the existing single-span medical review semantics, or adding a second generic AI writing surface.

## Success Criteria

- The server derives scope and gates; the browser never submits an arbitrary span list as authority.
- Every generated candidate remains bound to project, snapshot, NCT, source artifact, extraction revision, span ID, prompt version, provider/model run, fidelity result, and current-source state.
- Existing medically approved current translations are not regenerated; returned/failed/pending items have explicit state and retry behavior.
- One failed span does not roll back successful candidates; only failed items are retryable.
- Restart recovery does not duplicate AI runs or lose audit lineage.
- Frontend shows ready/excluded/running/failed/pending-medical-review counts and routes users into the existing review tools.
- PNH demonstrates eligible generation and medical-review pending behavior; RA demonstrates a valid zero-eligible/manual-upload branch.
- No path automatically changes medical review to approved or corpus admission to admitted.
- Focused tests, broad medical-writing regression, production build, and real desktop browser verification pass.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not read secrets, environment variables, raw model credentials, or unrelated project data.
- Do not edit source files in the conference. Conference outputs are advisory only.
- Do not infer regulatory approval or clinical correctness from a successful translation fidelity check.

## Loop Log

- 2026-07-16 08:14:40: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-16: Codex rejected the initializer's stale Grok-chair/Flash route and replaced it with the current global `AGENTS.md` panel plus the user-required independent Grok consultant.
