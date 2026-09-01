# Task Context: medical_monitoring_phase_c2_adapter_translation_contract_20260802

Created: 2026-08-02 00:21:28
Objective: Define and test a read-only config-to-adapter translation and source-registry contract using the C1 StudyMonitoringConfig without registering real projects or touching runtime state
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_study_config.py` (C1 contract)
- `services/api/app/monitoring_raw_intake.py` and `services/api/app/monitoring_project_registry.py`
  (read-only adapter/intake boundary)
- `services/api/app/main.py` (read-only registration/path audit)
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase C
- Current filesystem is authoritative; runtime databases and services are out of scope.

## Scope

- In scope: immutable `StudyAdapterDescriptor`, config-to-adapter translation,
  source-registry snapshot/deduplication, explicit adapter capability degradation,
  deterministic serialization/hash, and focused tests.
- Out of scope: `main.py` changes, real project registration, adapter invocation,
  local path resolution, runtime/API/browser execution, database reads/writes, AI calls,
  migration, and medical-writing changes.

## Success Criteria

- Descriptor/config project-trial/hash identity is exact and fail-closed.
- Required source bindings are present, opaque and hash-consistent; conflicting duplicate
  registry identities fail closed.
- Adapter capability gaps are visible as explicit limited/unavailable states and cannot
  become an implicit full capability.
- The translated binding and registry snapshot are read-only, deterministic and hash-bound.
- Focused/relevant tests, pycompile, Ruff and the review gate pass without runtime writes.

## Risk Boundaries

- Codex direct only; no Hermes route, conference or sub-agent.
- This is a contract/validation slice; it must not be presented as real adapter onboarding.
- Preserve `main.py`, existing adapters, medical-writing files and runtime data unchanged.
- Codex owns final verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:21:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 00:22: direct task contract filled; C2 remains isolated from runtime
  registration, adapter execution and authoritative databases.
- 2026-08-02 00:26: implemented `StudyAdapterDescriptor`, immutable
  `StudySourceRegistrySnapshot`, `StudyAdapterBinding` and
  `translate_study_config_to_adapter_binding` in
  `services/api/app/monitoring_study_adapter_contract.py`. The translator checks exact
  project/trial/config hash identity, required source bindings and opaque registry
  identities; capability gaps become explicit unavailable states and the binding carries
  a deterministic `binding_sha256`.
- 2026-08-02 00:26: verification passed: C2 focused **7 tests**, C1+C2 **19 tests**,
  B1-B6 compatibility + C1/C2 **65 tests**, full medical-monitoring frontend Node
  sweep (13 files), pycompile and Ruff. Review gate remains to be run after this record
  is complete.
- 2026-08-02 00:26: artifact hashes: C2 module
  `d08215db5ff18a54176156c95a7a930ea72b06837ea59c6c1860c864b44dbaff`; C2 test
  `b63103a8f2ea17eab6845fa7da1f2d0e2bb2b2537ebfd9f755a71afa782adcfc`.
- 2026-08-02 00:26: C2 closes only an offline translation/registry contract. No real
  project was registered, no adapter was invoked, no registry/runtime/API write occurred,
  and B6/B4 authority blockers remain unchanged.
