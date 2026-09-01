# Task Context: medical_monitoring_source_token_evidence_revalidation_20260803

Created: 2026-08-03 05:03:06
Objective: 为 MY009 legacy source-token content revalidation 证据增加 inventory/archive/artifact 的只读字节与 SHA 重验证；保持 source_token_revalidation_status=not_proven，不合成 token、不授予 B6/C14/CAS/写入/医学权限。
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_my009_source_token_content_revalidation_20260802/SOURCE_TOKEN_CONTENT_REVALIDATION.json`
- `records/active_slices/medical_monitoring_my009_source_inventory_recheck_20260802/SOURCE_INVENTORY.json`
- `records/active_slices/medical_monitoring_my009_archive_member_inventory_20260802/ARCHIVE_MEMBER_INVENTORY.json`
- Current B6/C14 and P10 evidence under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- This slice revalidates persisted evidence only; raw project content is not rescanned or mutated.

## Scope

- In scope: add a pure revalidation module/test; reopen the persisted content-scan artifact and
  its two inventory JSON inputs by safe relative path, exact bytes and SHA-256; recompute candidate,
  extension, archive and member summaries; persist a diagnostic-only report.
- Out of scope: raw MY009 rescans, archive extraction, source-token synthesis, source registry,
  B6/C14 outcomes, aggregate/CAS, provider/API/browser/service/runtime, real-project writes or
  medical conclusions.

## Success Criteria

- Current artifact and both inventory inputs replay with `evidence_fresh=true`, zero revalidation
  issues and matching inventory-derived counts.
- Preserve the underlying `source_token_revalidation_status=not_proven`,
  `source_token_synthesized=false`, `write_permitted=false`, `migration_ready=false`.
- Detect artifact/inventory bytes or SHA drift, summary tamper, direct-token evidence flag drift,
  authority mutations and unsafe paths.
- Focused/adjacent regression, py_compile, Ruff, artifact replay and Hermes review-gate pass;
  8911/5174 remain stopped.

## Risk Boundaries

- No source/project file, archive member, runtime/SQLite/CAS, source registry or authority state
  may be changed. Do not extract archives or call a provider/browser/API.
- This is direct Codex work; no delegated agent, conference or external model is used.
- Freshness of persisted evidence is not proof that the legacy source token existed or was revalidated.
- 8911 and 5174 must remain stopped.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 05:03:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 05:05-05:15: Reopened current artifact/inventory files and confirmed actual bytes/SHA;
  inventory-derived summary is 13 candidates, 2 archives, 10 members, 0 listing-like members.
- 2026-08-03 05:15-05:25: Added read-only revalidation module, six focused tests and a current
  evidence envelope. No raw MY009 file, archive member, provider or runtime was touched.
- 2026-08-03 05:25: Current report is fresh with zero revalidation issues, while underlying
  `source_token_revalidation_status=not_proven` remains unchanged; formal B6/CAS/source-token
  authority is not inferred.
- 2026-08-03 05:30: Added fail-closed handling for non-zero persisted token-hit counts; focused/
  adjacent regression was **7/166 passed**; py_compile/Ruff and Hermes review-gate also passed.
