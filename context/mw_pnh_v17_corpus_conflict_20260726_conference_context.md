# Conference Context: mw_pnh_v17_corpus_conflict_20260726

Created: 2026-07-26 16:22:07
Objective: 仅审查PNH v17完整condition修复、文档校验用户权限边界、语料适应症特异类型化集成的冲突和残余风险，不重复全量审计
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/evidence/independent_ai/PNH_V16_SCIENTIFIC_FAILURE.md`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/pnh_v16_search_snapshot.json`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/pnh_v17_triage_start.json`
- Latest `pnh_v17_run_status_*.json` and `pnh_v17_job_status_*.json` in the
  same evidence directory.
- `services/api/app/medical_writing_competitor_triage.py`, limited to the v17
  complete-condition prompt/input changes and their focused tests.
- `services/api/app/medical_writing_corpus_policy.py`,
  `services/api/app/medical_writing_corpus_analysis_ai.py`, and the compact
  corpus-generalization evidence report.
- `services/api/app/medical_writing_research_pipeline.py`,
  `services/api/app/main.py`,
  `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`,
  `frontend/src/features/writing-reference/WritingReferencePanel.jsx`, and
  focused validation/resume tests.
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`.

## Scope

- In scope:
  1. whether v17's complete condition evidence eliminates the four documented
     source-false PNH indication mismatch statements without inflating
     relevance;
  2. whether corpus findings are typed and assessed against the current
     project's explicitly sparse eight-axis layer, with indication-specific
     wording/clinical logic protected from cross-indication transfer;
  3. whether document validation remains a user-authority boundary and the
     waiting/resume path reuses completed work without auto-override.
- Out of scope: broad repository or security audit, unrelated frontend
  redesign, repeating already accepted OCR/translation concurrency tests,
  creating medical content, confirming the PNH basket, or editing source.

## Success Criteria

- Every objection cites a file/line, run/candidate ID, or focused test.
- The panel distinguishes scientific correctness from technical completion.
- The panel returns only conflicts, residual risks, required rechecks and a
  go/revise recommendation for each of the three bounded questions.
- No participant edits source or substitutes its own medical judgment for the
  product independent AI result. Codex retains final acceptance.

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
- Do not inspect the entire repository. Follow only the listed propagation
  paths and open extra files only when a cited dependency requires it.
- Treat PNH v16 as invalid evidence; do not confirm or project its basket.
- Do not infer that a passing unit test proves a real independent-AI or
  user-authority workflow.

## Loop Log

- 2026-07-26 16:22:07: Conference initialized by `hermes_workflow_guard.py init-conference`.
