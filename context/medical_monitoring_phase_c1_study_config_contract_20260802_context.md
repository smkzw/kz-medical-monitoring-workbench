# Task Context: medical_monitoring_phase_c1_study_config_contract_20260802

Created: 2026-08-02 00:08:00
Objective: Define and test a project-neutral StudyMonitoringConfig onboarding contract that uses source-registry references, explicit CM/IP treatment identity, versioned mappings and capability degradation without changing runtime registration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_raw_intake.py`
- `services/api/app/monitoring_mapping_contract.py`
- `services/api/app/monitoring_mapping_activation.py`
- `services/api/app/monitoring_project_registry.py`
- `services/api/app/main.py` project registration/path boundary (read-only audit)
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase C and §7.4
- Current filesystem is authoritative; runtime databases, services and `main.py` are
  read-only in this slice.

## Scope

- In scope: a pure, versioned `StudyMonitoringConfig` contract with source-registry
  bindings, field mappings, explicit CM/IP treatment identity, capabilities and display
  labels; deterministic serialization/hash and strict validation.
- In scope: tests proving project-neutral references, mapping semantic checks, capability
  degradation, round-trip serialization and fail-closed identity boundaries.
- Out of scope: changing `main.py`, registering real projects, moving files, reading or
  writing runtime databases, service/browser execution, AI calls, or replacing existing
  adapters in this slice.

## Success Criteria

1. A config binds listing and protocol through opaque source-registry references with
   source revision/content SHA-256; absolute local paths are rejected.
2. CM, investigational product and protocol background treatment roles are explicit and
   cannot alias one another.
3. Mapping entries reuse existing semantic validation, remain versioned and unique, and
   cannot introduce SDTM as a source role or self-referential derivations.
4. Capabilities are explicit (`full`, `limited`, `unavailable`); unavailable states
   carry limitations and missing capabilities never silently become available.
5. Serialization is deterministic and hash-bound; round-trip preserves the contract.
6. Focused tests, pycompile/Ruff and the workflow review gate pass without runtime writes.

## Risk Boundaries

- Codex direct only; no external agent, conference, service, browser or real-project run.
- This is a contract/validation slice; it must not be presented as project-neutral runtime
  onboarding until adapters and API registration are migrated and verified.
- Preserve `main.py`, existing adapters, medical-writing files and runtime data unchanged.
- Codex owns final review and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:08:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 00:09: direct task contract filled; implementation remains isolated from
  runtime registration and authoritative databases.
- 2026-08-02 00:16: implemented `StudyMonitoringConfig` and focused tests. The contract
  binds required listing/protocol sources to opaque registry references, preserves
  explicit CM/IP/background roles, reuses mapping semantic validation, requires all
  shared capabilities to be explicit, and binds deterministic serialization to a
  SHA-256. Local-path-like registry references and malformed payloads fail closed.
- 2026-08-02 00:16: verification passed: C1 **12 tests**, B1-B6 compatibility set plus
  C1 **58 tests**, full medical-monitoring frontend Node sweep (13 files), pycompile,
  and `python3 -m ruff check`. Review gate passed with `--require-verification`.
- 2026-08-02 00:16: changed artifact hashes: module
  `4d527be93919dfe79bf305ecd769d5680e3ec207dc551e95f971ae2fccfbb39e`; test
  `16f28ef7c3afe64472a87eaf897b49eb6585d7db72c17e6d1c820f868888542c`.
- 2026-08-02 00:16: C1 is complete only as an offline contract slice. Runtime adapter
  registration, migration, browser acceptance, real-project onboarding, and any
  disposition write remain pending B6/B4 authority gates and were not attempted.
