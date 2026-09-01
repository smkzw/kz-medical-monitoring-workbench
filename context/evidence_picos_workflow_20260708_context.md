# Task Context: evidence_picos_workflow_20260708

Created: 2026-07-08 02:24:01
Objective: Design and implement the Evidence Design PICOS interactive decision workflow bridging evidence research to medical writing, using business module names only and preserving independent AI/provider boundaries.
Task type: `complex_delivery_conference`
Risk: `high`
Selected Hermes route: `conference:minimax-m3-chair+participants+deepseek-supplier-flash+deepseek-supplier-pro` / `mixed:OpenCode default for chair/non-DeepSeek participants, DeepSeek supplier default for Flash participant, DeepSeek Pro maximum for main-venue review`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User requirements in this thread:
  - Build a local-first AI Medical Manager Workbench for medicine-related clinical development work.
  - Do not build first/fourth/fifth clinical-development links because they are not medicine-owned.
  - User-facing subsystem names must be business names only, without lifecycle/stage numbers.
  - Stage names such as `第几环节`, `阶段`, or `Stage N` must not appear in final subsystem names or visible UI.
  - Evidence design must support evidence-based research, competitor intelligence, and an interactive PICOS design workflow that can hand off to medical writing.
  - AI-generated content is allowed only as `待医学批准的正式内容` or candidate content; it cannot be represented as final, approved, or regulator-ready.
  - The product must run independently from Codex; any semantic AI work must go through an external provider gateway and preserve source boundaries.
- Current code and records:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/evidence_design_manifest.py`
  - `services/api/app/medical_writing_manifest.py`
  - `services/api/app/ai_task_runner.py`
  - `services/api/app/source_intake.py`
  - `services/api/app/main.py`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/evidence_design_manifest_qc.mjs`
  - `frontend/tests/medical_writing_manifest_qc.mjs`
- Codex maintains project logs outside this Hermes workspace; Hermes should not read or modify those logs in this round.
- Current verification baseline:
  - Backend `unittest discover` passed after module key migration.
  - Frontend build passed after module key migration.
  - Browser QC passed for overview, source registry, monitoring upload, evidence design, medical writing, TFL, safety/PV, and Patient Profile.

## Scope

- In scope:
  - Design a bounded PICOS workflow for `证据调研与方案设计`.
  - Bridge PICOS user decisions to `医学写作` as candidate inputs, not final protocol content.
  - Preserve evidence source references and quality gates.
  - Define backend contract/API shape, frontend interaction structure, states, and verification.
  - Identify pitfalls before Codex implements.
- Out of scope:
  - No code edits by Hermes in this round.
  - No external web claims by Hermes.
  - No formal clinical/regulatory conclusion.
  - No construction of first/fourth/fifth non-medical subsystems.
  - No assertion that an AI suggestion is approved, final, or regulator-ready.

## Success Criteria

- Hermes output gives a concrete, bounded implementation plan that Codex can verify against source files.
- Plan includes:
  - Contract models and endpoint recommendations.
  - Interaction flow for PICOS decisions and AI/user revision.
  - Business-name module key and visible copy constraints.
  - Persistence and audit approach for local single-user now, private network later.
  - Tests and browser QC cases.
  - Escalation triggers.
- Plan does not rely on Codex model capability for production semantics.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Hermes is not final authority; Codex owns verification and acceptance.
- Do not leak local absolute paths in user-facing payloads.
- Do not expose long source text in public API payloads unless bounded.
- Do not use or output `stage2/stage3/stage6/stage7/stage8/stage9` as current module keys.
- Do not introduce lifecycle/stage labels in UI copy.
- Any AI output must keep `codex_runtime_dependency=false`, `needs_medical_confirmation=true`, and explicit source references.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-08 02:24:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
