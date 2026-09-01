# Task Context: medical_monitoring_my008_3_02_crosswalk_revalidation_20260803

Created: 2026-08-03 03:44:46
Objective: Revalidate the current MY008-3-02 protocol-table visit schedule against record-level listing VISIT/VISTOID identities with an explicit blocked crosswalk report; never activate mapping or grant medical/runtime authority.
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current canonical MY008-3-02 protocol/listing files and their read-only bytes.
- Existing pure crosswalk contract `services/api/app/monitoring_visit_crosswalk.py`.
- Existing source/mapping review under
  `records/active_slices/medical_monitoring_my008_mapping_review_20260802/`.
- Protocol table `docx:table:11` (方案表1研究流程表) and listing fields
  `VISTOID`/`VISIT`.

## Scope

- In scope: reparse the current protocol/listing, construct the explicit V1–V17
  and observed-visit crosswalk, and persist the deterministic blocked report.
- Out of scope: source registration, mapping activation, clinical events/risk,
  provider/runtime/browser work, endpoint inference, or medical confirmation.

## Success Criteria

- Current source SHA/size and parser warning count are recorded.
- D70/V10 and D98/V12 missing coverage and V10–V15 ordinal conflicts are
  explicit typed findings; UNS/WITHDRAW/COMMON remain non-scheduled.
- Artifact replay exactly reproduces the crosswalk report digest and keeps
  activation/medical/runtime flags false.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never silently renumber listing OIDs, treat missing D70/D98 as proven absence,
  or infer PK/PD/primary endpoint values from visit labels.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 03:44:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Current listing replay produced 59 sheets, 82,583 rows, 24
  observed visit pairs and zero parser warnings; protocol table 11 produced 17
  visits. Existing crosswalk contract returned blocked with 2 blockers and 6
  ordinal review findings. No mapping activation or runtime authority was
  exercised.
- 2026-08-03: Raw OOXML recheck found `D70±2` and `D98±2` in the EC2 form's
  `ECTPT`/“给药时间点” field and Code_List options. The corresponding records
  have `VISTOID=COMMON` and `VISIT=公共页`; they are not record-level scheduled
  V10/V12 identities. Evidence is preserved in
  `records/active_slices/medical_monitoring_my008_3_02_crosswalk_revalidation_20260803/EC2_D70_D98_SOURCE_NOTE.md`.
  The V10/V12 crosswalk blockers remain; source review must reconcile the
  common-page treatment-timepoint representation without substituting it for
  `VISTOID`/`VISIT`.
