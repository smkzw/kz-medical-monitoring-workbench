# Task Context: monitoring_p10_loop316_protocol_typed_bundle_repair_20260801

Created: 2026-08-01 00:34:44
Objective: Implement an offline deterministic typed protocol structural-bundle repair that preserves provider semantic anchors, adds only exact table row/header context or unique list ancestor titles, records immutable repair lineage, keeps all existing clinical validators fail-closed, and adds the required negative test matrix without starting services or touching runtime data.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem is authoritative.
- Resume anchor:
  `context/monitoring_p10_loop316_protocol_v4_audit_pause_20260801.md`.
- Parent and independent audit:
  - `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.md`
  - `runs/codex-subagent_monitoring_p10_loop316_protocol_v4_audit_20260731.md`
- Current implementation:
  - `services/api/app/monitoring_ai_source_packet.py`
  - `services/api/app/monitoring_ai_service.py`
- Current tests:
  - `tests/test_monitoring_ai_source_packet.py`
  - `tests/test_monitoring_ai_service.py`
- Baseline SHA-256:
  - source packet:
    `f23be40c5e55bc6156f7f44252657cad15752c250bd3f1f327033dfc0a2d9745`
  - AI service:
    `210d90a19f72fdda307236f378083478222f14fe6cfa9e34983c4f2cdb47e80e`
  - source-packet tests:
    `b2db87dea0cb4343e6bd946a2db996130b85ab5615d71617413eaf648b73adca`
  - service tests:
    `67576b1e6943e86206eff261ef2b47c982e0ff68fbc509b3705b5211c30e5e47`
- Existing behavior to correct:
  - provider focus currently pulls every sibling item in a list group;
  - structure validation treats any list title and any list item globally as
    sufficient, so different lists can be mixed;
  - provider-selected table/list evidence is not deterministically augmented with
    separately labeled structural context and repair lineage before validation.

## Scope

- Writable paths are exactly the four implementation/test files listed above.
- In scope:
  - a pure typed structural-bundle helper;
  - deterministic provider-output normalization before protocol validation;
  - persisted server-generated repair lineage inside protocol structured payload;
  - group-specific table/list structure validation;
  - provider-focus wording/behavior consistent with the new boundary;
  - focused tests and negative matrix.
- Out of scope:
  - no provider prompt-version bump unless required by a changed provider-visible
    schema; stop and report if an identity migration is necessary;
  - no API/router/repository/database schema/frontend/medical-writing change;
  - no runtime SQLite read/write, service start, real job retry, candidate decision,
    mapping action, MY009 start or full test suite.

## Success Criteria

- Table:
  - a provider-selected non-header table cell may add only its exact same-row cells
    and available header path from the same frozen packet;
  - header-only evidence cannot select a row;
  - cross-row condition/action cannot be made valid by union;
  - ambiguous/missing table identity fails closed.
- List:
  - a provider-selected list item may add only its unique ancestor title;
  - a title alone does not add items;
  - sibling items are never auto-added merely because they share a parent;
  - different lists cannot satisfy one another;
  - missing/duplicate/ambiguous ancestry fails closed.
- Semantics:
  - provider original evidence IDs stay separately recorded and at least one original
    claim-relevant anchor remains;
  - automatically added context IDs do not enter claim evidence IDs;
  - candidate title/text/claims/topic/actor/action/condition/polarity/modality remain
    unchanged;
  - candidate structured payload persists deterministic repair lineage and the final
    expanded evidence IDs.
- Limits and invariants:
  - only IDs from the exact frozen packet may be added;
  - post-expansion union with conflict IDs must remain <=50; no truncation;
  - repeated inputs yield identical order and lineage;
  - all existing absence, conflict, eligibility, CM/IP and structure validators remain
    fail-closed.
- Focused tests pass and cover positive plus negative cases. No product runtime is
  started.

## Risk Boundaries

- Edit only the four explicitly authorized paths.
- Re-read each current file before editing and preserve unrelated changes.
- Do not use evidence adjacency as semantic endorsement.
- Do not mutate the persisted frozen job input.
- Provider must not be able to forge server repair lineage; reject provider-supplied
  lineage fields.
- Do not make or simulate a candidate decision.
- Do not relax a validator to make a fixture pass.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Required Repair Shape

Prefer a small pure helper in `monitoring_ai_source_packet.py` that returns:

- ordered original structured evidence IDs;
- ordered added structural-context IDs;
- ordered expanded structured evidence IDs;
- typed bundle bindings with stable table/list identities;
- deterministic repair schema/version.

Integrate it in `monitoring_ai_service.py` after provider payload schema validation
but before protocol clinical/structure validation. The server-generated lineage may
be persisted in an optional protocol-payload field, but raw provider output containing
that field must be rejected before normalization.

The existing provider focus must change from “whole list group” to:

- selected primary list items plus their unique ancestor title;
- selected title alone remains a title-only view;
- no sibling enumeration without an explicit whole-list identity (none exists in the
  current contract).

## Required Negative Matrix

At minimum test:

1. header selected without a data row;
2. condition from row A plus action from row B;
3. different tables/ambiguous table identity;
4. item adds one unique title but not sibling items;
5. title alone adds no items;
6. duplicate title or ambiguous/missing list ancestry;
7. title from list A plus item from list B;
8. automatically added evidence never appears in claim evidence IDs;
9. provider-forged repair lineage;
10. expansion >50 IDs;
11. added ID outside frozen packet;
12. deterministic/idempotent repeated output;
13. conflict/absence and CM/IP gates still reject representative invalid output.

## Discovery Decision

No external executable/library adoption is needed. This is a narrow correction to an
existing frozen evidence contract; the current source, real failed-job audit and
independent review already resolve the decisive design uncertainty. Do not add a
dependency or perform web research.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 00:34:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Codex re-read the current implementation and tests, confirmed both
  services remain stopped, fixed the typed repair contract and authorized one bounded
  edit round over four files.
- 2026-08-01: Pi/deepseek completed the initial edit and one consolidated correction
  in the same session `019fb908-83d1-7000-9601-82dd441a70ca`; no fallback or
  re-dispatch.
- 2026-08-01: Codex rejected the worker's no-bump conclusion because provider-visible
  focus behavior changed. Protocol prompt identity moved to v5; v4 was added to the
  terminal legacy visibility set, with v3/v4 cutover tests.
- 2026-08-01: Offline acceptance passed: 222 focused tests; 1185 medical-monitoring
  tests; 201 adjacent medical-writing contract tests; Python compilation passed.
  8911/5174 remained stopped and no real job or candidate decision occurred.
- 2026-08-01 01:27 CST: Current fine-grained task closed and paused without entering
  canary. Resume from
  `context/monitoring_p10_loop316_protocol_typed_bundle_repair_pause_20260801.md`.
