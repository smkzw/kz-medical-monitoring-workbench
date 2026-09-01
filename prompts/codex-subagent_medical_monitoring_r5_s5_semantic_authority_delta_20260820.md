You are a Codex native subAgent running under a parent Codex task.

The parent Codex owns the project contract, source authority, final verification, protected-path boundary, and user delivery. Use `gpt-5.6-sol` with reasoning effort `high`. Read and comply with the latest applicable `AGENTS.md`; do not route through Hermes or another external Agent.

Hard boundaries:
- Work only inside the current workbench workspace.
- This is an append-only semantic-authority delta. Do not alter any accepted parent contract, rejected implementation-contract v0.1, existing R1-R5 source, root init, frontend, services, packages, runtime, deploy, medical-writing, or real-project file.
- Create or modify only these paths:
  - `context/medical_monitoring_r5_s5_semantic_authority_delta_20260820_context.md`
  - `reviews/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1_20260820.md`
  - `artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/schema.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/source_matrix_delta.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json`
  - `tools/generate_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py`
  - `tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py`
- Do not create producer/runtime/test/evidence/acceptance-record files. Do not start 8911, services, browsers, real projects, or models. Do not issue an acceptance verdict.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r5_s5_semantic_authority_delta_20260820.md`. Do not write that report path with tools; return the complete handoff and let the runner persist it.

Read these files only, fully before editing:
- `context/medical_monitoring_r5_s5_authority_contracts_20260819_context.md`
- `.hermes/plans/2026-08-19_1945-medical-monitoring-r5-s5-contract.md`
- `context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md`
- `reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md`
- all files under `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/`
- the accepted parent generator and verifier
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
- accepted S4 records and readonly manifest referenced by the parent contract
- typed R1/R2/R4/R5 sources referenced by the parent source matrix
- the rejected implementation-contract v0.1 human contract, machine artifacts, generator, verifier, and context as negative evidence only
- System Design v1.1 and R0-R8 implementation plan.

Problem to solve:
Fresh isolated review proved that four future subject-temporal leaves lack an accepted independent semantic value authority: `TemporalEvent.domain`, `TemporalEvent.subtype`, `TemporalRiskAnchor.risk_type_zh`, and `TemporalRiskAnchor.severity`. Existing R1/R4 strings may be raw evidence but are not accepted closed mappings; S4 is identity-join-only and must not transfer domain/severity value authority; examples are not authority. The rejected implementation contract mirrored candidate values and must not be used as a source of truth.

Create an append-only, exact, machine-verifiable delta that introduces:
- `SemanticPolicyAcceptanceReceipt` and `RawSemanticTokenEvidence`;
- `EventClassificationRulePackage`, exact-token/compound rules, and `EventClassificationAuthority`;
- `RiskTaxonomyPackage`, `SeverityPolicyPackage`, and `RiskClassificationAuthority`;
- a separate `RiskPresentationLexicon` for `zh-CN` labels.

Required semantics:
- AI may propose a package but only a content-hash-bound `accepted` receipt can authorize a future producer; synthetic packages are `synthetic_test_only` and never clinical truth.
- Event rules output exactly one of the frozen 16 subtypes. Domain is derived only by the frozen subtype-to-eight-domain relation. No fuzzy matching, implicit trim/casefold, OTHER, ninth domain, or seventeenth subtype. Unmapped/ambiguous tokens fail closed and produce no packet.
- Raw evidence is bound to owner type/ref, exact field path, raw token, source content identity, snapshot, source revisions, and locators. No bare string, fixture/case ID, or sentinel authority.
- Risk taxonomy yields a stable `risk_type_code`; `risk_type_zh` is exact-one lookup through an accepted `zh-CN` lexicon and is presentation metadata, not clinical fact. Domain-generic labels such as `AE风险` are forbidden fallback.
- Severity is independently normalized by an accepted policy. `high` never becomes `critical`; legacy severe/moderate/mild mappings are explicit; SAE/AESI flags do not silently promote severity; unmapped/conflict fails closed.
- S4 may contribute only risk/project/run/snapshot/cutoff/site/subject/spine identity joins and mismatch detection, never domain/severity/domain_zh values.
- Preserve the accepted 17/13 output schemas byte-for-byte. This delta is `append_only_semantic_authority_delta`, `rewrites_parent=false`, `invalidates_parent_acceptance=false`.

Freeze exact schemas, enums, cardinality/nullability, canonical-hash recipes, cross-object invariants, public API signatures, source paths/allowed roles/forbidden transfers, package/receipt lifecycle, error codes with deterministic priority, and future bundle integration. Pin every accepted parent artifact and protected aggregate; pin the rejected v0.1 implementation snapshot only as negative evidence and forbid in-place overwrite.

Create at least 28 explicit deterministic challenge cases covering all eight domains, all 16 subtypes across positive cases, owner/field-specific exact tokens, compound rules, ambiguous/unmapped, package/version/hash/receipt/provenance drift, cross-identity joins, taxonomy and lexicon mismatch, generic-label fallback, severity mappings/conflicts/promotion, S4 value-transfer attempts, parent SHA drift, original-path overwrite, example-as-authority, and acceptance-token leakage. Each case must contain one exact mutation, expected typed error, forbidden output, and a non-LLM oracle. The verifier must independently execute rule/taxonomy/lexicon/severity evaluation and canonical hashes; it must not decide by case ID, labels, expected code, fixture names, or generator semantic helpers.

Run generator `--check` and verifier under normal and `PYTHONOPTIMIZE=2`, multiple `PYTHONHASHSEED` values, exact no-cache Ruff, SHA stability, parent/protected pins, exact allow/deny paths, producer absence, and stopped 8911. If an independent authority still cannot be honestly frozen, stop and report the exact leaf/source gap rather than creating mirrored context or self-proof.

Only a later fresh reviewer may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_SEMANTIC_DELTA_V0_1`. This task does not accept or unlock the implementation contract, producers, S5, UI, browser, real project/model, product, or production.

Return a compact handoff with: boundary check, files created, object/invariant/challenge counts, active negative probes, normal/O2/cross-seed/Ruff/pin/absence/8911 evidence, final SHA list, uncertainty, and next action. Do not self-accept.
