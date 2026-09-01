# Task Context: medical_monitoring_metric_candidates_20260805

Created: 2026-08-05 21:20:26
Objective: Add a project-neutral, fail-closed protocol/listing metric configuration candidate contract that preserves source lineage and requires medical confirmation; no runtime/provider activation.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` (P1-02)
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`
- `services/api/app/monitoring_protocol_rules.py` (`ProtocolFact`, source-bound facts)
- `services/api/app/monitoring_ai_field_profiler.py` (`MonitoringFieldProfileSnapshot`)
- `packages/contracts/workbench_contracts/models.py` (`SubjectTrendMetric` direction values)
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only blocked; no runtime/provider/browser activation)

No external executable dependency or provider is being adopted. The slice is a pure local contract built from existing source-bound models.

## Scope

- In scope: a deterministic, project-neutral candidate builder that accepts only medically confirmed efficacy/safety protocol facts with an explicit metric declaration and a frozen full field-profile snapshot; emits lineage-bound, pending-medical-confirmation candidates and explicit data gaps.
- In scope: strict schema validation, stable candidate/bundle digests, exact listing field matching, sparse-field review flags, and unit tests.
- Out of scope: AI/provider calls, runtime activation, API route wiring, adapter replacement, automatic medical confirmation, derived metrics from field names/labels, real project execution, browser/visual acceptance, or modifications to medical-writing surfaces.

## Success Criteria

- No candidate is emitted from an unconfirmed fact, an absent/ambiguous metric declaration, an unknown listing field, or a mismatched fact/listing project or protocol version.
- Candidate and bundle identities are deterministic and source-bound; status remains `pending_medical_confirmation`.
- Missing/invalid evidence is represented as explicit review gaps rather than inferred metrics.
- Focused Python tests pass and the existing medical-monitoring test suite/build remain green where run.
- Evidence and next safe action are recorded without changing the real-loop gate.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep source/test/evidence changes inside this workbench; do not start 8911, frontend services, browser sessions, external model calls, or real project runs while the gate is blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 21:20:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 21:42:00: Added the source-only metric candidate contract and eight focused tests. The candidate builder is explicitly bound to medically confirmed protocol facts, a declaration version, and a complete frozen field profile; no AI/runtime/medical confirmation path was added.
- 2026-08-05 21:42:00: Focused and adjacent regressions passed (59 tests); the nine-module monitoring regression passed (741 tests). A broad monitoring sweep reached 1900 passes but reproduced an existing MY008 persisted rule identity mismatch and was stopped after 808.81 seconds; the failing test also reproduces in isolation. This is recorded as residual risk, not silently repaired in this slice.
