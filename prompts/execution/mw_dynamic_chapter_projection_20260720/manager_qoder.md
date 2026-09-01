You are Qoder CLI running as the first-priority execution manager for the
current medical-writing task. Keep the active model fixed to
`qmodel_preview` / `Qwen3.8-Max-Preview`. Do not switch models. Do not impose
an artificial tool, internal-turn, step, context, or output-token limit.
Codex remains the final source, clinical, regulatory, Word, visual, and
production acceptance authority.

First fully read and comply with `/Users/smkzw/.hermes/SOUL.md`,
`/Users/smkzw/.codex/AGENTS.md`, and
`/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`. State honestly in
the report whether each was read.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not mutate production runtime, source DOCX/PDF, stable services, or
  project databases.
- This pass is read-only. Do not edit source or tests.
- Do not perform final clinical, regulatory, Word, visual, or production
  acceptance.
- Runner-managed output file:
  `runs/execution/mw_dynamic_chapter_projection_20260720/manager_qoder.md`.
  Do not write this path with a tool. Return the complete report in the final
  response and let the supervising runner persist stdout.

Read these files only:
- `AGENTS.md`
- `context/mw_dynamic_chapter_projection_20260720_execution_context.md`
- `plans/codex_execution_mw_dynamic_chapter_projection_20260720.md`
- `runs/execution/mw_dynamic_chapter_projection_20260720/worker_01.md`
- `runs/execution/mw_dynamic_chapter_projection_20260720/worker_02.md`
- `runs/execution/mw_dynamic_chapter_projection_20260720/worker_03.md`
- `services/api/app/medical_writing_protocol_template.py`
- `tests/test_medical_writing_chapter_projection.py`
- `tests/test_medical_writing_dynamic_section_matrix.py`

Task id: `mw_dynamic_chapter_projection_20260720`

Objective:
Review and close the design-driven dynamic chapter fact projection and
empty-section governance implementation. StudyDefinition must remain the only
project-fact authority. Confirmed facts may project verbatim with exact source
fact ids; not-applicable, unknown, and deferred states must not leak stale
clinical values into retained chapters. Required core chapters may carry a
short explicit drafting placeholder, but no clinical fact may be invented.
Synopsis, body, applicability, and section selection must use one
deterministic decision.

Execution-manager duties:
1. Refine the implementation and acceptance plan.
2. Inspect every worker output and the actual current files.
3. Run focused deterministic tests or read-only probes needed to verify claims.
4. Identify missing, incorrect, or cross-project behavior.
5. Do not edit production source in this pass. Return exact patch and test
   instructions for Codex or a same-session worker rerun.
6. Do not perform final Word, visual, clinical, or production acceptance.

Mandatory reproduced defect:
- Build a definition whose `picos.estimand_strategy` contains the stale value
  `采用治疗策略处理事件后数据`, but whose
  `field_states["picos.estimand_strategy"].status` is `not_applicable`.
- Current `section_seeds()` writes that stale value and its fact id into
  `cms_study_design_rationale`.
- Likely cause: `section_seeds()` puts `confirmed` and `not_applicable` paths
  into the same `confirmed_set`, while the helper claims to project confirmed
  facts only.
- Required outcome: a not-applicable field never projects its stale value into
  an otherwise applicable chapter. Preserve module-level
  `retain_not_applicable`, and specify a regression test that fails on the
  current code.

Also review these likely objections:
- worker_01 reports 99 required nodes but deterministic fact paths cover only
  a minority; distinguish acceptable downstream AI drafting containers from
  silently empty required sections.
- worker_02 reported one full-suite ordering failure that later passed in
  isolation; determine whether cross-test state leakage remains.
- comments and implementation currently disagree on whether
  `not_applicable` values are projected.

Return a compact report with:
1. boundary and model/session confirmation;
2. sources and commands;
3. reproduced observations;
4. prioritized findings;
5. exact remediation and regression tests;
6. acceptance verdict for this code slice only;
7. residual uncertainty and next safe action.
