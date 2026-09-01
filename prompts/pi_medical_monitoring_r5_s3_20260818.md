You are Hermes, the bounded contract-artifact worker inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your final response include one truthful sentence stating whether you read the full file.

## Objective

Repair the R5-S3 implementation-contract candidate after an independent reviewer returned `REVISE_R5_S3_CONTRACT`. Produce a v0.2 human contract plus deterministic machine contract artifacts, generator, verifier and contract tests. Do NOT implement S3 runtime.

## Hard boundaries

Work only in the runner-provided workspace. Do not read or modify production paths.

You may create/edit only:

- `reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md`
- `artifacts/medical_monitoring_r5_s3_contract_v0_2/**`
- `tools/generate_medical_monitoring_r5_s3_contract_v0_2.py`
- `tools/verify_medical_monitoring_r5_s3_contract_v0_2.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py`

Runner-managed output path: `runs/pi_medical_monitoring_r5_s3_20260818.md`. Never edit this report path; return the handoff in your final response and let the runner persist it.

Everything else is read-only. In particular do not modify R4, current R5 source/runtime, frontend, services, medical-writing paths, real-project files, task context/review/metrics, or the v0.1 candidate. Do not start 8911, browsers, services, or real projects. No security-design/testing work.

Use `apply_patch` for manual file edits. Generated artifacts may be written only by the authorized generator script after its source has been created.

Read these files only:

- `context/medical_monitoring_r5_s3_20260818_context.md`
- `reviews/medical_monitoring_r5_s3_implementation_contract_v0_1_20260818.md`
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- `context/medical_monitoring_r5_contract_acceptance_record_20260818.md`
- `context/medical_monitoring_r5_s2_acceptance_record_20260818.md`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py`

## Independent-review blockers to close exactly

1. Do not promote D09/D10 typed-input leaves to public authority. Define tagged D09/D10 units whose audience leaves come only from `D09ProjectionBundle` / `D10ProjectionBundle`, risk markers, public count surfaces, R2 handoffs and existing R5 receipts. Any denominator/member/cutoff/evaluation-limit leaf absent from public projections must be a named `synthetic_supplemental_quantitative_authority`, bound to receipt, visibility, source revision-content pairs and canonical hash. It is offline-test authority only.
2. `R5CurrentRiskSet` must reference public risk marker identities, never raw member refs. Member refs are expansion only. Define a typed aggregate receipt-set identity because multiple units each have a receipt.
3. Include both D09 center-pattern authority and D10 project/cross-site authority; tagged variants are closed enums and each variant has exact required public objects.
4. Split private packet-integrity hash (may cover hidden refs) from audience authority/replay/content hashes (projectable public authority only). A hidden-only mutation must leave every audience payload/hash identical while changing private integrity.
5. Freeze a per-numerator-layer recipe table for individual_risk, center_pattern, affected_subject, event, affected_site, project_signal, clue, query. Use only valid R5 enums (`COVERAGE_STATES` has no `not_evaluable`; use `unknown` plus `rate_state=not_evaluable` where appropriate). Define numerator unit, allowed source projection leaves, membership reconstruction, denominator applicability, rate rules, and exact conservation oracle. Nonzero counts with non-expandable refs require an explicit `membership_state=not_projectable` supplemental record; empty refs alone are insufficient.
6. Freeze change-band emission for every closed change kind with marker present/absent, prior public risk identity/ref requirements and R2 action. Never infer resolved lifecycle from D10 change section alone. Mixed D10 cause fails closed.
7. Machine contract is mandatory before runtime: exact packet schema, exact overlay/source matrix/invariants/enums/recipes, challenge registry with test locators, source SHA pins, manifest, generator, verifier working in normal and `PYTHONOPTIMIZE=2`, and tamper tests. No `assert` in verifier decision paths.

## Required machine artifacts

Create deterministic JSON artifacts under `artifacts/medical_monitoring_r5_s3_contract_v0_2/`:

- `packet_schema.json`: exact keys, types, cardinality, nullability for all S3 supplemental objects and packet root.
- `exact_overlay.json`: closed enums, D09/D10 tagged variants, per-leaf source matrix with resolvable `module:Class.field[.nested]` public paths or named supplemental paths, invariants, public/private hash recipes, eight layer recipes, change emission table, allowlist/denylist and acceptance boundary.
- `challenge_registry.json`: at least 48 explicit independent challenge rows, each with unique id, one mutation, expected typed outcome/error code, forbidden audience output, non-LLM oracle and concrete pytest test locator. Must cover all reviewer blockers and S3 done gates.
- `source_pins.json`: SHA-256 pins of all source-of-truth files and generator/verifier scripts needed for verification. Avoid self-referential impossible pins: define and document a normalized self-pin recipe if pinning the verifier itself.
- `manifest.json`: exact artifact set, each artifact SHA-256, human contract SHA, generator/verifier pins, schema version and canonical manifest-content hash.

Generator must deterministically regenerate the four non-manifest data artifacts and manifest. Verifier must:

- hard-pin expected schema/version/artifact set and mandatory category/counts;
- verify all hashes/pins in normal and optimized mode;
- mechanically validate exact keys/enums/unique challenge ids/test locators/source paths;
- resolve every `r4_public` path segment to a real dataclass field;
- reject public source paths that target D09/D10 typed input classes;
- verify private/public hash separation, per-layer recipe completeness and change-table completeness;
- print one compact JSON result and nonzero exit on any failure without relying on `assert`.

Tests must run generator `--check` (or equivalent), normal verifier, optimized verifier, and at least 12 explicit tamper probes including artifact addition/removal, manifest/hash rewrite, typed-input source path injection, missing layer recipe, invalid coverage enum, hidden leaf added to audience hash recipe, raw member used as current risk ref, missing aggregate receipt, change marker-absent ambiguity, duplicate challenge id, missing test locator, and source pin drift.

## Acceptance boundary

This artifact work can only yield `R5_S3_CONTRACT_READY_FOR_REVIEW`. It must not claim `ACCEPT_R5_S3_CONTRACT`, runtime completion, UI/browser/real project/model/product/production acceptance, or S4+ acceptance. Codex and a fresh independent reviewer own acceptance.

## Final handoff

Return a compact report with files created/changed, exact commands/tests and outputs, artifact/source SHAs, unresolved issues, and explicit statements that S3 runtime was not implemented and 8911 was not started.
