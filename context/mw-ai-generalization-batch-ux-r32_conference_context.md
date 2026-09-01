# Conference Context: mw-ai-generalization-batch-ux-r32

Created: 2026-07-29 19:25:14
Objective: 独立审阅医学写作工作台当前综合AI提示词的跨适应症精确泛化、避免项目过拟合，以及正常用户路径中的批量确认/逐项确认边界；仅报告增量冲突和高风险，不修改源码，不重复A1真实E2E测试
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/execution/mw_final_5x3_release_r32_20260729/ROUND_STATUS.md`
- `records/execution/mw_async_progress_loop_20260729/LOOP_STATUS.md`
- `records/reviews/MW_AI_ROLE_AND_PROGRESS_CONTRACT_REVIEW_20260729.md`
- `services/api/app/medical_writing_corpus_policy.py`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_fact_intake.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/src/features/medical-writing/StudySchemaEditor.jsx`
- Existing tests directly exercising the files above.
- The running r32 A1 E2E project is out of bounds: do not open its browser, mutate
  its runtime, or duplicate its tester work.

## Scope

- In scope:
  - Identify prompt defects that can cause cross-indication or single-project
    overfitting, evidence leakage, unsupported numeric copying, or failure to
    adapt wording to indication, phase, modality, route and study design.
  - Identify normal-path UI or API behavior that requires repetitive
    item-by-item medical confirmation where AI default classification plus one
    batch review is sufficient.
  - Distinguish legitimate exceptional confirmation from redundant approval.
    Content/type mismatch override, source conflict, material evidence
    contradiction and destructive replacement may retain explicit review.
  - Return only defects not already closed in the two review/status records,
    with exact file/line evidence and a minimal remediation/test contract.
- Out of scope:
  - Source edits, browser E2E, broad security audit, unrelated subsystems,
    clinical acceptance of generated protocol content, and restating already
    closed progress/DOCX findings.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No source or running tester state is modified; Codex retains final acceptance.
- Every reported issue distinguishes the normal happy path from an exceptional
  override/reconciliation path.
- Every prompt finding states the failed invariant and names a deterministic or
  provider-backed test that can prove remediation.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not infer product behavior from labels alone. Trace actual reachability,
  default state, API transition and existing test coverage before classifying a
  per-item confirmation as a release defect.
- Do not recommend a single universal indication style. The target is
  hierarchical generalization: regulatory invariant, phase/design/modality
  pattern, indication convention, project fact, and source-specific wording
  remain distinguishable and traceable.

## Loop Log

- 2026-07-29 19:25:14: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-29 19:30 CST: Codex populated the source authority, narrowed scope to
  unresolved deltas, excluded the running A1 runtime, and defined the
  batch-confirmation exception boundary.
- 2026-07-29 19:34 CST: All three prompts passed workflow preflight. Independent
  participants started through the declared routes; runner sessions remain
  pending under the 120-minute hard wait and will not be polled frequently.
- 2026-07-29 19:36 CST: Codex ran the non-overlapping deterministic contract
  bundle for corpus generalization, corpus AI validation, evidence-bound
  prefill, package adoption, study schema and structured tables:
  `349 passed, 10 warnings`. Warnings are the already-known FastAPI lifespan
  deprecations.
