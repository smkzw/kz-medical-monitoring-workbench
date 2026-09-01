# Task Context: medical_monitoring_p8_evidence_provenance_ui_guard_20260806

Created: 2026-08-06 03:34:31
Objective: Make the P8 assurance UI fail closed unless server-returned full-recompute evidence declares an accepted provenance authority; preserve both future server-ledger and revalidated-signed-manifest routes without enabling submission or runtime.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §§11.2, 40.2, 40.5: assurance completion requires a saved full-recompute execution proof; evidence must remain traceable and cannot be promoted from a page or cached risk list.
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` §§2.2, 8: three run strategies share one evidence base; publication requires independent-AI and real-project evidence, not a UI-only claim.
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` §5.346: current full-recompute proof is mixed provenance; six risk-snapshot fields are server-derived while coverage/rule/failure/skip/retry fields are caller-supplied. The roadmap explicitly leaves the authority route open.
- `records/active_slices/medical_monitoring_p8_assurance_proof_provenance_audit_20260806/VERIFICATION.md`: proof submission must remain disabled until a server-generated evidence-run ledger or a signed manifest with server full-field revalidation is selected and implemented.
- Current runtime gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` is `read_only/blocked`; all runtime/provider/write authority booleans are false and ports are stopped.
- Product files are limited to the feature-owned assurance model/view/panel and their focused tests under `frontend/src/features/medical-monitoring/`; no backend or runtime mutation is in scope.

## Scope

- In scope: require an explicit accepted `provenance_status` on pre-lock full-recompute proof responses; accept the two documented future authority routes (`server_evidence_run_ledger` and `signed_manifest_server_revalidated`); surface unknown/mixed provenance as a blocking reason; prevent an existing but non-authoritative proof from being presented as ready or re-recordable in the feature policy; add focused view/model/panel contract tests and durable evidence.
- Out of scope: choosing the product/medical authority route; implementing either server ledger or signed manifest; changing backend schemas, repository persistence, runtime/SQLite, B6/C14, source-token/CAS, Safety/PV, medical writing, service startup, browser/Playwright, provider calls, API login, or real-project execution.

## Success Criteria

- The proof view normalizer rejects a missing, unsupported, or mixed provenance status before render-state commit.
- The assurance model reports accepted provenance only for the two explicitly named future routes and otherwise fails closed with a readable blocker.
- A present but non-authoritative proof is not treated as ready and does not expose the next evidence-recording action in the action policy.
- Focused model/view/static tests pass; no mutation/runtime/provider/browser path is invoked.
- Task records, hashes, verification, review and roadmap/ledger traceability state the authority decision remains open.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never infer or select the evidence authority route from this UI guard. The two enum values are contract placeholders for the future server response, not evidence that either route exists or has passed.
- Keep `read_only / blocked` and all four monitoring ports stopped throughout this slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 03:34:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Re-read latest global/workspace/workbench/frontend AGENTS, P10 checkpoint, v11 terminal/zero-submit evidence, LOOP 3.20-3.21, PRD/manual and roadmap. The authority fork remains genuinely unspecified; proceed only with a contract-level fail-closed consumer guard.
