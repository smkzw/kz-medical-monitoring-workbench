# Task Context: medical_monitoring_my009_source_token_content_revalidation_20260802

Created: 2026-08-02 19:50:36
Objective: Perform a bounded read-only MY009 candidate-content scan for legacy source token 2ef9c8d72d74; retain not_proven unless direct provenance evidence appears
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_my009_source_inventory_recheck_20260802/SOURCE_INVENTORY.json`
- `records/active_slices/medical_monitoring_my009_archive_member_inventory_20260802/ARCHIVE_MEMBER_INVENTORY.json`
- The 13 absolute paths listed by `SOURCE_INVENTORY.json` as
  `listing_identity_candidates`; content is read in memory only.
- `services/api/app/monitoring_source_revision_compatibility.py` for the
  fail-closed source-token semantics.

## Scope

- In scope: bounded raw UTF-8/UTF-16 and OOXML/ZIP member scan for legacy token
  `2ef9c8d72d74`; read-only workbook shape observation; deterministic artifact
  stating whether direct token/provenance evidence was found.
- Out of scope: modifying/unpacking project files, synthesizing a source token,
  claiming source authenticity from filenames or sheet shapes, medical review,
  runtime/API/provider/browser/service execution or C14 activation.

## Success Criteria

- All 13 candidates are scanned without writing extracted members.
- Token hits and workbook/archive observations are explicit and reproducible.
- No direct evidence is treated as proof of non-existence; status remains
  `not_proven` unless a verifiable source-token lineage is present.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:50:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: 13/13 candidate content scan completed. Raw UTF-8/UTF-16 and
  ZIP/OOXML token hits are all zero. The listing-shaped workbook has 65 sheets
  and standard study headers but no token; qualified RARs have 10 members and
  zero listing-like members.
- 2026-08-02: Conclusion remains `source_token_revalidation_status=not_proven`;
  no source token was synthesized and no project file was modified.
- Evidence: `records/active_slices/medical_monitoring_my009_source_token_content_revalidation_20260802/SOURCE_TOKEN_CONTENT_REVALIDATION.json`,
  artifact SHA `c7dcb66c3adc4b0407ae6a391de64006b3eb506e899b7dcd08a52a9a82f92604`.
