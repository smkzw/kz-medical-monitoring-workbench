# Task Context: mw_codex_retake_20260726

Created: 2026-07-26 12:42:03
Objective: Audit Cursor Agent #1 changes, validate and clean evidence, design provider selectors and concurrency architecture, then continue medical-writing production LOOP to launch readiness
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current workspace and runtime:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- Latest resume boundary:
  `records/handoffs/CODEX_RESUME_P0_18_20260726.md`
- Agent #1 original contract and durable records:
  `records/handoffs/AGENT_1_CURSOR_HANDOFF_20260725.md`
  and `records/handoffs/agent_1_cursor_20260725/`
- Agent #1 pre-change source baseline:
  `records/handoffs/agent_1_cursor_20260725/snapshots/baseline_20260725_1719/`
- Current claimed P0-18 evidence:
  `runs/execution/mw_systemic_e2e_loop_20260726/`
- Invalidated evidence sentinel:
  `runs/execution/mw_systemic_e2e_loop_20260725/WAVE5_INVALIDATED.md`
- Global and workspace instructions:
  `/Users/smkzw/.codex/AGENTS.md`,
  `/Users/smkzw/.codex/codex_agent_mode_overlay.md`,
  and the nearest workspace `AGENTS.md`.

## Scope

- In scope: reconstruct the real Agent #1 diff; review code and tests; run
  deterministic, API, browser, AI, corpus, DOCX and real-Word regression;
  classify and clean obsolete test assets only after preserving decisive
  evidence; design and, after the architecture gate, implement independent-AI,
  OCR and translation provider/model selection; verify oMLX shared
  concurrency; refine indication-aware corpus prompting; complete the required
  four-tester clean-state end-to-end launch matrix.
- Out of scope: unrelated medical-workbench subsystems; security or backdoor
  hunting; counting corpus-gate override, skeleton-only content, API-only
  inspection, or partial chapter generation as an end-to-end PASS.

## Success Criteria

- A complete SHA-based diff against the Agent #1 baseline exists and every
  material source change has been reviewed and tested.
- Known false-positive acceptance logic is repaired and historical invalid
  evidence cannot be promoted as a launch PASS.
- Runtime, API contract, browser workflows, independent product AI, corpus
  pipeline, rich editor, references, figures/tables/appendices, and DOCX/Word
  fidelity pass representative regression.
- The provider selector has an approved architecture, capability-driven
  adapters, explicit secret handling, and verified remote/local discovery.
- OCR and translation use the shared oMLX lease gate and measured concurrency;
  unavailable requested models fail closed rather than silently substituting.
- The four required external testers each complete three mutually distinct
  non-oncology, clean-state, real-browser projects through complete protocol
  generation, review, formatting, and export, with defects repaired and rerun.
- Launch status is based on evidence, not declarations.

## Risk Boundaries

- Preserve user work and current runtime data before destructive cleanup.
- Do not remove a record or test asset until its evidentiary value and
  replacement locator are recorded. Archive decisive invalidation evidence.
- Do not copy API keys into records, prompts, logs, or source control.
- Do not implement the material provider-selector architecture until the
  Product Design/architecture gate is presented and approved.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 12:42:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26: Latest global Pi/oMLX routing overrides and compact overlay read.
- 2026-07-26: Runtime observed online at 5174/8911, build
  `web-c0c4acd74a75175d` / `api-4f1d8ee1dc78b5fb`, contract
  `medical-writing-api-2026-07-17.1`; independent AI remains
  `deepseek/deepseek-v4-pro`.
- 2026-07-26: Agent #1 `07_DIFF_MANIFEST.md` found materially incomplete
  relative to its own changelog and stored diff artifacts. Reconstructing the
  diff from the 319-file baseline is mandatory.
- 2026-07-26: Found a false-positive acceptance defect:
  `wave_c_p018/cursor_selftest/SUMMARY_FINAL.json` contains a failed
  propionic-acidemia Phase I case while top-level `all_pass` is `true`.
  Prior Wave C evidence is therefore partial and cannot satisfy launch.
