# Conference Context: mw_pnh_v18_corpus_conflict_20260726

Created: 2026-07-26 16:44:06
Objective: 仅审查PNH v18绑定检索条件词修复、文档校验用户权限边界、语料适应症特异类型化集成的冲突和残余风险，不重复全量审计
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
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/PNH_V17_SCIENTIFIC_FAILURE.md`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/pnh_v16_search_snapshot.json`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/pnh_v17_run_final.json`
- Latest `pnh_v18_run_*.json`, `pnh_v18_job_*.json` and scientific
  inspection evidence in the same directory when present.
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/PNH_V18_SCIENTIFIC_FAILURE.md`.
- Latest `pnh_v19_run_*.json`, `pnh_v19_job_*.json` and scientific
  inspection evidence in the same directory when present.
- `services/api/app/medical_writing_competitor_triage.py`, limited to the v18
  bound-search-condition propagation, the v19 strict controlled
  comma-inverted condition-label repair, and their focused tests.
- `services/api/app/medical_writing_corpus_policy.py`,
  `services/api/app/medical_writing_corpus_analysis_ai.py`, and
  `records/handoffs/codex_retake_20260726/evidence/CORPUS_STRICT_GATE_PRODUCTION_INTEGRATION_20260726.md`.
- `services/api/app/medical_writing_research_pipeline.py`,
  `services/api/app/main.py`,
  `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`,
  `frontend/src/features/writing-reference/WritingReferencePanel.jsx`, and
  the accepted focused validation/resume evidence report when present.
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`.

## Scope

- In scope:
  1. whether v18 safely reuses the exact condition term already bound to the
     immutable search plan only when the authoring framing term is absent;
  2. whether v18 fixed the four source-false PNH indication statements; if
     not, whether v19's exact comma-inverted controlled-label rule fixes the
     remaining failure without hard-coding PNH, forcing relevance or
     suppressing unresolved bilingual review;
  3. whether corpus findings are typed and assessed against the current
     project's explicitly sparse eight-axis layer, with indication-specific
     wording and clinical-design logic protected from cross-indication
     transfer;
  4. whether document validation remains an explicit user-authority boundary
     and resume reuses completed download/extraction work without auto-override.
- Out of scope: broad repository or security audit, unrelated frontend
  redesign, repeating accepted OCR/translation concurrency tests, creating
  medical content, confirming the PNH basket, or editing source.

## Success Criteria

- Every objection cites a file/line, run/candidate ID or focused test.
- Scientific correctness is distinguished from technical completion.
- The panel returns only conflicts, residual risks, required rechecks and a
  go/revise recommendation for each bounded question.
- No participant edits source or substitutes its own medical judgment for the
  product independent-AI result. Codex retains final acceptance.

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
- Do not inspect the whole repository. Follow only listed propagation paths
  and open an adjacent file only when a cited dependency requires it.
- Treat PNH v16 and v17 as invalid scientific evidence; do not confirm or
  project either basket.
- Do not infer that a unit-test pass proves the real independent-AI or
  user-authority workflow.

## Loop Log

- 2026-07-26 16:44:06: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-26: All three role prompts passed preflight after replacing the
  generator's rejected absolute workspace wording with the runner-provided
  relative workspace boundary. Conference packet validation passed.
- 2026-07-26: Started Pi/Aishuo CMS and CodeBuddy/DeepSeek Pro participants in
  parallel after the real v18 run began. The chair remains pending until both
  participant outputs and terminal v18 scientific evidence are available.
- 2026-07-26: Both participant reports completed. Pi/Aishuo primary routing
  failed before a resumable session and the runner used the declared
  Hermes/Aishuo fallback; CodeBuddy/DeepSeek Pro completed its primary route.
- 2026-07-26: The real v18 run completed technically but failed one of four
  predeclared source-truth probes (`NCT00566696`) because the registry uses
  `Hemoglobinuria, Paroxysmal Nocturnal (PNH)`. No basket was confirmed.
- 2026-07-26: Added a generic v19 strict comma-inverted controlled-label rule;
  focused and full regression passed.
- 2026-07-26: Real v19 run `ct_run_6614e8c3594035033341` reached
  `review_ready`: 8/8 chunks, 67 candidates, exact
  `alibaba_token_plan/qwen3.8-max-preview` AI route, and no AI fallback. All
  four predeclared PNH probes now pass; `NCT00566696` preserves the source
  label `Hemoglobinuria, Paroxysmal Nocturnal (PNH)` and is retained as a
  mixed-population indirect reference. The basket remains unconfirmed.
- 2026-07-26: Terminal evidence is available in
  `evidence/independent_ai/PNH_V19_SCIENTIFIC_ACCEPTANCE.md` and the linked
  v19 JSON files. Chair synthesis may now proceed.
