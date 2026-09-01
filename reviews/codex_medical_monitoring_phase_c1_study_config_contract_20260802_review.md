# Codex Review: medical_monitoring_phase_c1_study_config_contract_20260802

Date: 2026-08-02 00:15 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.

Changed source/test:
- `services/api/app/monitoring_study_config.py`
- `tests/test_monitoring_study_config.py`

## Verdict

**Pass for the isolated, project-neutral onboarding contract; runtime onboarding and
adapter migration remain explicitly unapproved follow-up work.**

## Boundary Check

- The C1 task context limits the slice to a pure validation/serialization contract and
  focused tests. No `main.py` registration, adapter replacement, service/browser run,
  runtime database access, AI call, or medical-writing path was used.
- The contract stores opaque source-registry references plus source revision and content
  SHA-256. Absolute and path-traversal-like local references fail closed; no local path
  is resolved by this module.
- The current `main.py` content hash is
  `0dabf52df865023a3e9f66c880462c3ec66775b1345c2e4a7fe796cdd1d104fc`, matching the
  latest recorded shared-workbench hash. Its filesystem mtime moved during the broader
  session, so mtime alone is not treated as an edit signal; C1 did not patch the file and
  a future integration slice must re-check the content hash before touching it.

## Contract Review

- Listing and protocol source kinds are both required; IDs are unique and source hashes
  are lowercase SHA-256-shaped values.
- Investigational product, concomitant medication, and background treatment roles are
  explicit and cannot alias. Existing mapping semantic validation is reused, including
  SDTM-role rejection, CM/IP separation, reference-only standards, and self-referential
  coded/derived lineage rejection.
- All eight shared monitoring capabilities are explicit. `limited` and `unavailable`
  states require limitation codes, so missing or degraded capability cannot silently
  become available.
- Canonical JSON serialization is hash-bound; round-trip parsing checks the declared
  hash and rejects malformed list/object payloads.

## Codex Verification

- Focused C1 tests: **12 passed**.
- B1-B6 risk-authority/reconciliation/mapping/approval/review/repository compatibility
  tests plus C1: **58 passed**.
- Full medical-monitoring frontend Node sweep: **13 files passed** (API 123, checklist
  20, daily-run gate 7, field mapping 6, models 44, project scope 14, project-switch
  isolation 23, protocol preparation 17, risk projection 16, route 40, rule release
  63, template recommendation 22, subject models passed).
- `python3 -m py_compile` passed for the new module and test. `python3 -m ruff check`
  passed for both files (`All checks passed`).
- No browser/runtime check was run because C1 is contract-only and the standing gate
  keeps ports 8911 and 5174 stopped; 18911 was not touched.

## Residual Risk

- This proves contract behavior only. It does not prove that real RUX/MY009/MGK10
  sources can be registered through this contract, that API adapters consume it, or that
  project/site/subject UI projections render correctly in the live workbench.
- B6 mapping outcomes remain pending and B4 residuals remain unresolved; therefore no
  dual-read, migration, disposition write, or production registration is permitted.
- C1 field mappings are intentionally a separate representation from existing active
  adapter registrations. A later controlled slice must define an explicit translation
  and approval boundary rather than silently replacing the legacy path.
