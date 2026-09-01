# Task Context: medical_monitoring_my009_source_inventory_recheck_20260802

Created: 2026-08-02 19:00:09
Objective: Read-only exhaustive inventory of MY009 listing-like workbook/archive candidates outside the prior bounded set; determine whether any provenance-bearing source can support legacy source-token revalidation without onboarding or runtime writes.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User's current authorization: read local project material and write only task evidence; do not modify real-project source files, runtime stores, or service state.
- Prior bounded qualification: `records/active_slices/medical_monitoring_rux_candidate_source_revalidation_20260802/TEST_EVIDENCE.md` and `context/medical_monitoring_rux_candidate_source_revalidation_20260802_context.md`.
- Current MY009 root: `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC` (read-only metadata/content qualification only).
- B6 source-token authority: `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json` and `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`.
- Product-side qualification contracts: `services/api/app/listing_file_parser.py` and `services/api/app/monitoring_source_classifier.py`.

## Scope

- In scope: exhaustive read-only filename/extension inventory under the MY009 project root and the containing Langlai document tree; exact byte size/SHA-256 for listing-like workbooks/archives; OOXML metadata/classification for candidate workbooks; comparison against the prior bounded candidate set.
- Out of scope: modifying any real project file, opening/writing SQLite, source registry or batch registration, adapter/API/provider/browser/service/runtime execution, medical reviewer outcome, source-token synthesis, baseline approval, or aggregate/CAS mutation.

## Success Criteria

- Every MY009 listing-like workbook/archive candidate discoverable in the authorized local tree is either recorded with deterministic metadata/classification or explicitly excluded with a reason.
- The report states whether any newly found candidate can prove the missing legacy source token `2ef9c8d72d74` against source bytes/lineage; it must not infer provenance from filenames or meaning tokens.
- B6/C14 remain unchanged and fail-closed; no production source or runtime state is changed.

## Risk Boundaries

- Real project files are read-only; only `context/`, `records/active_slices/`, `reviews/`, and `metrics/` under the workbench may be written.
- Do not persist subject-level values or identifiers; record file metadata and source-classification evidence only.
- Do not synthesize or close the legacy source token, B6 outcome, medical judgment, aggregate/CAS state, or release gate.
- Codex is the final authority; no delegated agent/provider/conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:00:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Prior bounded inventory listed only the two MY009 listing workbooks plus comparison/template variants; this recheck expands the read-only search to the full authorized local document tree and archive-like extensions.
