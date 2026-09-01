# Task Context: medical_monitoring_current_gate_audit_hash_rebind_20260804

Created: 2026-08-04 20:43:00
Objective: Refresh the current read-only real-loop gate audit so its formal reviewer package file and canonical package hashes match the current filesystem after the approved provenance refresh; preserve blocked authority and all other observations.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — current read-only gate audit.
- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json` — current formal package bytes and canonical package hash.
- `records/active_slices/medical_monitoring_b6_packet_freshness_20260803/B6_REVIEW_PACKET_REFRESH_REVALIDATION.json` — current packet/package/source replay evidence.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json` — current release coverage; remains blocked.
- Current filesystem and applicable AGENTS files; no runtime or external system is an authority for this slice.

## Scope

- In scope: update only the two formal-package identity fields in the current gate-audit source observation; recompute and record the audit artifact hash; re-read authority/status and binding evidence.
- Out of scope: B6 outcomes, C14, release coverage, formal package content, refresh packet content, source-token/CAS/approved-input decisions, runtime/provider/browser/API/Playwright, real projects, databases, and medical-writing.

## Success Criteria

- Current audit package file SHA and canonical package SHA equal the actual current formal package declarations.
- All existing blocked/authority-safe observations remain unchanged.
- Read-only consistency checks and Hermes review-gate pass; required ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:43:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Rebound the current audit's two formal-package identity fields to current bytes/hashes; 68 relevant tests passed; review-gate passed; blocked authority unchanged.
