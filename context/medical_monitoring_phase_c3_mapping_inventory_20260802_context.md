# Task Context: medical_monitoring_phase_c3_mapping_inventory_20260802

Created: 2026-08-02 00:33:00
Objective: Create and verify a review-only inventory contract for fixed sheet/metric surfaces in the existing RUX, MY009 and MG-K10 adapters without activation or runtime registration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/rux_monitoring_service.py` constants and read-only method references
- `services/api/app/my009_monitoring_service.py` sheet/metric constants and references
- `services/api/app/mgk10_sar_monitoring_service.py` sheet/metric constants and references
- C1/C2 contracts:
  `services/api/app/monitoring_study_config.py`,
  `services/api/app/monitoring_study_adapter_contract.py`
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase C
- Current filesystem is authoritative; source files are inspected only, not executed on
  real project data.

## Scope

- In scope: a review-only `StudyAdapterMappingObservation` and
  `StudyAdapterMappingPlan`, fixture inventory for observed fixed sheet/metric surfaces
  in RUX/MY009/MG-K10, deterministic hash and duplicate/path/semantic fail-closed tests,
  and a task-owned JSON evidence artifact.
- Out of scope: reading real listing/protocol bytes, invoking adapters, changing
  `main.py` or adapter code, activating mappings, source registry persistence, runtime/API
  writes, service/browser execution, AI calls, migration, and medical-writing changes.

## Success Criteria

- Each observation binds adapter/project identity, source sheet/field, capability,
  observation kind and code evidence locator; every item remains
  `observed_requires_medical_review`.
- Existing C1 mapping semantic rules continue to reject SDTM roles and CM/IP leakage.
- Duplicate IDs/surfaces, unknown capabilities, local paths, cross-project observations
  and non-review-only status fail closed.
- RUX, MY009 and MG-K10 fixture plans serialize deterministically and the inventory hash
  is reproducible without any runtime input.
- Focused/relevant tests, pycompile, Ruff and review gate pass without runtime writes.

## Risk Boundaries

- Codex direct only; no Hermes route, conference or sub-agent.
- Inventory observations are evidence for future mapping review, not active mappings and
  not proof of clinical correctness.
- Preserve `main.py`, existing adapters, medical-writing files and runtime data unchanged.
- Codex owns final verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:33:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 00:34: direct task contract filled; fixed sheet/metric surfaces will be
  represented from source-code constants/method references only, with no real-project
  execution or source-file reads.
- 2026-08-02 00:36: implemented review-only `StudyAdapterMappingObservation` /
  `StudyAdapterMappingPlan` and fixture builder. The generated inventory contains 3
  plans / 46 observations: RUX 11, MY009 18 and MG-K10 17. It is marked
  `review_only=true` and `source_code_constants_and_method_references_only`; inventory
  SHA-256 is `f395dc787910648362c41475266bfab80de171ab7615e68cdce904ddbe01807c`.
- 2026-08-02 00:36: the shared mapping semantic validator had a narrow false positive:
  literal `ip_` matching rejected the canonical `cm.non_ip_medication` role. A minimal
  token-aware correction now preserves that CM role and still rejects actual `ip_*`
  roles; the correction is covered by the semantic-quality regression set.
- 2026-08-02 00:36: verification passed: C3 focused **6 tests**; C1/C2/C3 plus semantic
  quality **159 tests**; inventory generation/path scan; pycompile; Ruff. Review gate
  remains to be run after this record is complete. No adapter invocation, real source
  read, runtime write, service or browser run occurred.
- 2026-08-02 00:36: artifact hashes: mapping-plan module
  `008769cb2f8398776682bb3c9bc30d430eca950a45723cbaab09124c8dbf1e5f`; test
  `2ffde1ac00c9fb88f526923c18fefb83c47a08dd581b5443adc35ed442c754f4`; shared validator
  `6ffb39bb87924e68162391ca1eb8c2cf100717906b195ec77f0802e9ab5a4b92`; inventory JSON
  `d68ca1d8c297807fd157afd31c48965214303b07e92ac4f6dfa83e9bd3c5a6f9`.
