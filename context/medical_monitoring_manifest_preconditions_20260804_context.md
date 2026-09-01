# Task Context: medical_monitoring_manifest_preconditions_20260804

Created: 2026-08-04 19:08:38
Objective: Add a read-only five-project medical-monitoring source-manifest precondition contract for structure parsing, without activation, adapter, provider, runtime, medical-writing or source writes.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Source Of Truth

- `services/api/app/project_source_manifest.py` and its public manifest contract.
- The five user-supplied monitoring project identities currently represented by
  the source manifest: MG-K10-SAR, Ruxolitinib-AD, MY008-3-02, MY008-3-01 and
  MY009-UC-2-01.
- Existing structure-driven intake and project-source reconciliation evidence.
- Current B6/C14/real-loop gates, which remain authoritative and closed.

## Scope

- In scope: a pure mapping-based validator that checks whether a public
  `medical_monitoring` manifest has the minimum source references for a future
  structure parse: explicit binding, supported implementation status, listing
  and protocol primary sources, referenced source existence/availability and
  deterministic identity/duplicate checks.
- Out of scope: opening source workbooks or protocols, parsing rows, field
  mapping, adapter registration, source promotion, AI/provider calls, runtime,
  database writes, B6/C14/real-loop changes, browser/Playwright, medical
  judgment, and medical-writing assets.

## Success Criteria

- Valid public manifests for all five supplied projects produce a diagnostic
  `ready_for_structure_parse` report while retaining `activation_allowed=false`
  and all write/provider/medical flags false.
- Missing binding, unsupported status, missing/unknown/duplicate source IDs,
  missing listing or protocol primary source, and unavailable source are
  reported with stable issue codes and no exception-based bypass.
- The contract remains independent of local paths, source row data, adapters,
  providers and runtime state.

## Risk Boundaries

- Only the new pure contract, focused tests and this task's evidence may change.
- Do not modify canonical source IDs/aliases or promote candidate IDs used by
  the frozen real-loop acceptance contract.
- Keep 8911/5174/8910/4173 stopped; do not start services, browsers, providers,
  external testers or real-project execution.

## Loop Log

- 2026-08-04 19:08:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Current five public manifests were re-opened read-only. Three
  bindings are `real_source_slice`; MY008-3-01 and MY008-3-02 are
  `source_manifest_only`. All declared primary/supplemental source refs were
  available, but no adapter or structure parser is implied.

## Trigger Reason

This tracked task covers a bounded multi-file contract and deterministic
regression. Codex handles it directly; no delegation or conference was needed.

## Timeout Policy

No external runner was launched. Focused commands were allowed to finish; no
runtime polling or provider wait was used.

## Acceptance Boundary

Codex owns final acceptance. A `ready_for_structure_parse` result is only a
declarative handoff condition and does not authorize parsing, source admission,
adapter activation, provider calls, database writes, medical confirmation or
commercial release.

## Continuation 5.123 — persisted structure-profile contract

The same tracked task now also contains a pure validator for the persisted
candidate-only MY008 structure profile:
`services/api/app/monitoring_structure_profile_contract.py`. It validates
aggregate profile shape and identity boundaries without reopening source files:
schema, authority/processing flags, candidate IDs, basename-only anchors,
hash/count types, listing row-count sums, protocol counts, domain-sheet groups,
and complete classified/unclassified sheet partition. The clean status is
`ready_for_mapping`, an offline handoff label only; all parse/adapter/provider/
runtime/write/medical flags remain false.

Evidence:
`records/active_slices/medical_monitoring_manifest_preconditions_20260804/`
and the dedicated
`reviews/codex_medical_monitoring_structure_profile_contract_20260804_review.md`
and metrics file. Final proof was 13 focused tests plus the complete related
selection at 117 passed with 18 existing warnings; compile and Ruff passed.

No source workbook/protocol, service, listener, provider, browser/Playwright,
API login, real project, database or medical action occurred. B6 is still
`pending_review`; C14 and real-loop remain blocked; 8911/5174/8910/4173 stay
stopped. Candidate IDs remain distinct from canonical MY008 IDs.

Next safe action is another offline adapter-neutral precondition only after
rechecking the B6/C14/real-loop, source-token/CAS, approved-input and
host-attestation gates. `ready_for_mapping` must not be treated as activation
or clinical readiness.
