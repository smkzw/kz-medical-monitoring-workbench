# Codex Review: medical_monitoring_phase_c2_adapter_translation_contract_20260802

Date: 2026-08-02 00:26 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.

Changed source/test:
- `services/api/app/monitoring_study_adapter_contract.py`
- `tests/test_monitoring_study_adapter_contract.py`

## Verdict

**Pass for the offline read-only translation contract; real adapter registration and
runtime onboarding remain out of scope and blocked by the existing authority gates.**

## Boundary Check

- C2 consumes the C1 `StudyMonitoringConfig` but creates no executable adapter object,
  registry write, local-path resolver, API route, service process, browser session or
  runtime database action.
- The only product/test files changed in this slice are the two listed above. `main.py`,
  existing project adapters, frontend, runtime data and medical-writing files were not
  patched. Current `main.py` content hash is
  `0dabf52df865023a3e9f66c880462c3ec66775b1345c2e4a7fe796cdd1d104fc`, matching the
  latest recorded shared-workbench hash; its mtime is not used as edit authority.

## Contract Review

- `StudyAdapterDescriptor` binds adapter identity to exact project/trial and C1
  `config_sha256`, declares selected source binding IDs and stays explicitly read-only.
- `translate_study_config_to_adapter_binding` rejects identity/hash mismatch, unknown
  source IDs and omitted required listing/protocol bindings before producing a binding.
- `StudySourceRegistrySnapshot` is immutable and deterministic; it deduplicates the same
  opaque registry identity even when study-local binding IDs differ, while conflicting
  kind/revision/content hashes fail closed. It carries no filesystem path.
- Adapter support gaps are made explicit: a C1 `full` capability becomes
  `unavailable/adapter_capability_missing` when the descriptor does not support it;
  existing `limited` capability states and their limitation evidence are preserved.
- The translated binding retains selected binding IDs, field mappings, distinct treatment
  roles, all eight explicit capabilities, config/source hashes and read-only state. Its
  canonical payload is bound to `binding_sha256`.

## Codex Verification

- C2 focused tests: **7 passed**.
- C1 + C2 config/translation tests: **19 passed**.
- B1-B6 risk-authority/reconciliation/mapping/approval/review/repository compatibility
  plus C1/C2: **65 passed**.
- Full medical-monitoring frontend Node sweep: all **13 files passed** (including risk
  projection 16); C2 did not change frontend code but the sweep checks downstream
  isolation.
- `python3 -m py_compile` and `python3 -m ruff check` passed for both C2 files.
- No browser/runtime check was run because C2 is contract-only; 8911 and 5174 remain
  stopped and 18911/PID 43191 was not touched.

## Residual Risk

- This is not proof that RUX, MG-K10 or MY009 adapters can consume the binding, that a
  source registry persists it, or that a fourth unseen project onboards without code.
- C2 does not translate fixed sheet/header/metric logic or create a unified clinical event
  layer; those remain C3/C4 work after the mapping and authority gates are authorized.
- B6 has no actual reviewer outcome and B4 has unresolved residuals, so no dual-read,
  migration, disposition write, real-project registration or service start is permitted.
