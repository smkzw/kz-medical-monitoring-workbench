# Task Context: b6_preflight_identity_chain_20260802

Created: 2026-08-02 18:30:09
Objective: 只读预审 B6 五个身份映射候选的 source-token 关系与 append-only disposition chain，产出可重放缺口证据，不授予 reviewer 或写入权限
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/MAPPING_REVIEW_AND_DRYRUN.json`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `services/api/app/monitoring_source_revision_compatibility.py` and its focused tests
- Existing bounded source-qualification records: `records/active_slices/medical_monitoring_rux_candidate_source_revalidation_20260802/` and `records/active_slices/medical_monitoring_source_preflight_20260802/`
- Current filesystem only; no runtime database, service, provider, browser or real-project input

## Scope

- In scope: read-only hash binding, source-token relation comparison for all five candidates, metadata-only append-only chain continuity/grouping, B6 snapshot and deterministic preflight report.
- Out of scope: reviewer outcome creation, medical approval/rejection, source-content selection, aggregate/CAS replay write, migration, SQLite/API/provider/runtime/browser, onboarding, real projects and protected App/styles or medical-writing surfaces.

## Success Criteria

- Recompute B3/B4/B6/source implementation hashes and bind them into one report.
- Show all five candidate fingerprints and zero reviewer outcomes.
- Reproduce 3 `legacy_source_revision_missing_same_meaning` rows and 2 `exact_after_identity` rows without inferring missing source bytes.
- Check chain references are identical within each identity group, transitions are continuous, timestamps monotonic, and explicitly label aggregate replay as not executed.
- Replay the report hash and assertions without writing runtime state; retain B6 `pending_review`, `write_permitted=false`, `migration_ready=false`.

## Risk Boundaries

- Do not create or infer reviewer outcomes, source-content identity, clinical disposition, aggregate state or migration authority.
- Do not write `B6_REVIEW_OUTCOME_GATE.json`, C14, SQLite, API/provider/runtime state, or protected frontend/medical-writing surfaces.
- Evidence report is a read-only preflight artifact; it never grants write or migration authority.
- No delegated agent or conference was used; Codex retains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 18:30:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Read B3/B4/B6 inputs and the source-revision compatibility implementation; no source or runtime write.
- 2026-08-02: Built metadata-only preflight report with 5 candidate fingerprints, source relations 2 exact/3 revalidation-required, and 2 structurally continuous identity groups.
- 2026-08-02: Report hash/source hash/chain assertions replayed successfully; B6 remains pending and non-writing.
- 2026-08-02: Existing source-qualification records were consulted as context only: MY009 candidates are restored/comparison workbooks and no provenance-complete pair was cleared; this does not close source-token revalidation.
