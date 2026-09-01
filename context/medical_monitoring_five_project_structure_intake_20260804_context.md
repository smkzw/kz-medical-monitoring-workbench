# Task Context: medical_monitoring_five_project_structure_intake_20260804

Created: 2026-08-04 15:12:07
Objective: Read-only structure-driven intake preflight for the five canonical monitoring projects; preserve unknown/ambiguous listing structures as explicit gaps, do not run services/providers/browser/medical AI or grant B6/C14 authority.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_raw_intake.py` and `tests/test_monitoring_raw_project_intake.py`.
- `records/active_slices/medical_monitoring_source_batch_five_project_alignment_20260803/`.
- User-authorized read-only project roots: MG-K10-SAR, Ruxolitinib-AD, MY008-3-02,
  MY008-3-01, and MY009-UC-2-01.
- Current B6/C14 and real-loop gate reports remain authoritative for activation; this task
  cannot supersede them.

## Scope

- In scope: select deterministic protocol/listing candidates per canonical project, run the
  existing raw-intake parser without AI/provider/runtime access, and retain only aggregate
  counts, domain/group names, unclassified-sheet counts/names, and file fingerprints.
- In scope: identify missing/ambiguous source candidates and prove that unknown listing shapes
  remain explicit rather than silently mapped.
- Out of scope: source promotion, batch creation, database/API writes, B6/C14 decisions,
  source-token/CAS evidence fabrication, host attestation, services, ports 8911/5174/8910/4173,
  browser/Playwright, AI calls, medical conclusions, or raw subject-level data persistence.

## Success Criteria

- Five project rows are evaluated or explicitly marked unavailable with a typed reason.
- Each evaluated row records protocol/listing file names, byte sizes and SHA-256 values, parser
  status, sheet/row/subject/site aggregates, recognized domain groups, and unclassified sheets.
- No subject-level identifiers or raw cell values are persisted in the task artifact.
- Existing B6/C14/approved-input authority remains unchanged and the reserved ports remain stopped.
- A focused parser check and the workflow review gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:12:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 15:13:00: Completed latest workbench `AGENTS.md` read in eight bounded chunks; no route
  or authority change.
- 2026-08-04 15:15:57: Existing raw-intake parser evaluated one deterministic protocol/listing
  candidate for each of the five authorized project roots with `ai_provider_configured=False`;
  only aggregate metadata was retained.
