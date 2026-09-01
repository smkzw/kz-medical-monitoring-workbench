# Task Context: medical_monitoring_my009_archive_member_inventory_20260802

Created: 2026-08-02 19:09:02
Objective: Read-only list and classify the two MY009 RAR archive members to determine whether either contains a provenance-bearing full listing source for legacy token revalidation; do not extract to the real project or perform runtime writes.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User's current authorization permits local read-only qualification and task
  evidence writes, while real project bytes remain unchanged.
- RAR candidates recorded in
  `records/active_slices/medical_monitoring_my009_source_inventory_recheck_20260802/SOURCE_INVENTORY.json`:
  `MMP定稿文件-20250815 (2).rar` and `方案及配套资料/V2.0 final-附录修改0805.rar`.
- Existing B6/C14 authority reports are read-only context; this task cannot
  change them or synthesize the legacy source token.

## Scope

- In scope: use 7-Zip's read-only listing mode to enumerate archive members,
  record archive/member metadata, identify listing-like workbook/document
  members, and determine whether an archive member is a plausible
  provenance-bearing full listing source.
- Out of scope: extracting into the real project, modifying or repacking
  archives, persisting subject-level values, source registry/onboarding,
  parser/runtime/API/provider/browser/SQLite/service execution, medical or
  engineering reviewer outcomes, source-token synthesis, aggregate/CAS writes,
  and release closure.

## Success Criteria

- Both RAR files are either listed and classified or explicitly reported as
  unreadable/unsupported with evidence.
- Any workbook/document member is recorded by member path, size, and archive
  source; no member is called provenance-complete solely from its name.
- The legacy token `2ef9c8d72d74` remains unchanged unless exact provenance
  evidence is actually present; B6/C14 remain fail-closed.

## Risk Boundaries

- Read the real RAR bytes only; write only task-scoped context, records, review,
  and metrics under the workbench. Do not extract or write beside the source
  archives.
- This is direct Codex work; no delegated agent/provider/conference is used.
- Do not write the runner-managed report path.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:09:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Next bounded action is a read-only 7-Zip member inventory; stop
  after archive classification and do not silently promote a member to a
  source baseline.
