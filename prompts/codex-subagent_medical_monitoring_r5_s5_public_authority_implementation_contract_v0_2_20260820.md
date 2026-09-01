You are a Codex native subAgent running under a parent Codex task.

The parent Codex owns source authority, final verification, protected-path boundaries, acceptance, and user delivery. Use `gpt-5.6-sol` with reasoning effort `high`. Read the latest applicable `AGENTS.md` and work directly in the current workbench; do not route through Hermes or another external Agent.

Hard boundaries:
- Create or modify only these nine v0.2 files:
  - `context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820_context.md`
  - `reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md`
  - `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/public_api.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/source_join_matrix.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/invariant_error_matrix.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/test_matrix.json`
  - `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/manifest.json`
  - `tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py`
  - `tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py`
- The rejected v0.1 implementation-contract snapshot is immutable negative evidence. Do not edit or overwrite any v0.1 file.
- Do not create producer/runtime/test/evidence/acceptance-record files. Do not modify R1-R5 source, root init, frontend, services, packages, runtime, deploy, medical-writing, real-project files, accepted parent artifacts, or the accepted semantic delta.
- Do not start 8911, services, browsers, real projects, or models. Do not issue an acceptance verdict.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md`. Do not write it with tools.

Read these files only, fully before editing:
- System Design v1.1 and R0-R8 implementation plan.
- `context/medical_monitoring_r5_s5_authority_contracts_20260819_context.md`
- `.hermes/plans/2026-08-19_1945-medical-monitoring-r5-s5-contract.md`
- the accepted public-authority parent contract, all of its artifacts/tools, and its acceptance record;
- the accepted semantic-authority delta, all eight files, and `context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md`;
- the rejected implementation-contract v0.1 nine-file snapshot as negative evidence;
- accepted R5 v0.3 exact contract, accepted S4 records/readonly manifest;
- all typed R1/R2/R4/R5 sources cited by the parent and semantic source matrices.

Task:
Create a new, immutable, exact machine-verifiable v0.2 implementation contract for `subject-temporal-public-v1` and `aemh-match-history-public-v1`. Preserve the accepted 17/13 output schemas without extra leaves. Reuse legitimate v0.1 work only after independently rebuilding it under the accepted semantic delta; do not copy its mirrored-context or fail-open reducer design.

Non-negotiable source-join architecture:
- Every target leaf has a real typed source path, previous/controlled/constant authority, or an exact deterministic derived recipe. Candidate-selected values and independent expected-authority inputs are distinct planes with real provenance. No RHS may be generated from the candidate/target output or mirror the same reference under a new container.
- Resolve all paths against real frozen dataclasses, including nested fields. No fixture/case/test/sentinel branching, nearest fallback, output backfill, or examples as authority.
- Execute each reducer to an exact target value: all_equal(_nullable), ISO parse/normalize, closed mapping, boolean, count, sorted unique, sequence/assembly, exact selection, stable IDs, canonical hashes, membership, receipts, packets. Type/nonempty/self-shape checks are insufficient. If a leaf lacks independent authority, mark it explicitly deferred and do not claim a constructible packet.
- The four semantic leaves must consume the accepted semantic delta only: `TemporalEvent.domain/subtype` from an externally pinned accepted synthetic-test event classification authority; `TemporalRiskAnchor.risk_type_zh/severity` from accepted taxonomy/lexicon/severity authorities. Candidate receipts cannot self-authorize. S4 contributes only the eight identity joins and never domain/severity values.
- Raw token evidence resolves actual typed source owner/ref/field/value/content/snapshot/revision/locator. `RiskInstance.clinical_risk_flags` may test SAE/AESI non-promotion only; no phantom fields.

Positive-output construction:
- All positive subject and AE/MH packets are built from transformed typed source + previous/controlled authorities through the same frozen join/reducer/reseal specification, never by patching a baseline expected output.
- Selectors must hit real baseline instances. Source changes that require coordinated updates use explicit exact linked operations; missing any linked operation fails closed.
- AE/MH uses accepted full exact recipes for entry/thread/membership/projection/receipt/packet IDs and hashes; non-empty state-appropriate identity evidence; later fact identity equals reachable `CanonicalFact.fact_hash`; previous prefix byte-identical; lifecycle/withdraw/reappear valid.

Runtime specification inventory:
- Preserve honest semantic deduplication: 231 distinct executable input specifications cover the accepted 236 case traces through exactly five declared same-input/same-lane/same-outcome aliases. Never claim 236 distinct executable specs.
- Keep 22 artifact-governance probes separate and actually executed by this contract verifier.
- Every spec has typed fixture, one exact mutation, expected code/success, forbidden output, future test locator, and non-LLM oracle. The contract stage freezes specifications and runs artifact/governance oracles only; it never claims the future producer/runtime executed.
- Retain the accepted 81-error union and deterministic priority unless the accepted semantic delta requires explicitly namespaced semantic errors; any union/delta and priority must be exact and justified.

Required active controls, in addition to prior gates:
- foreign RiskInstance scope plus resealed context must fail;
- reflected/mirrored authority-context reference must fail;
- target tampering for every reducer family must fail, including forged count, member refs, cutoff, locator, domain/subtype, risk label and severity;
- R5C-109 missing any linked cutoff operation must fail;
- changed rule/package/candidate receipt without external accepted-record change must fail;
- fuzzy/unmapped/ambiguous/extra-field/catastrophic/generic-label/S4-value-transfer attempts must fail;
- cross-owner raw evidence and wrong CanonicalFact identity must fail;
- package/registry/parent/rejected-v0.1/protected-pin drift must fail.

Verifier independence:
- Do not import generator semantic helpers or determine behavior from case ID, expected code, labels, fixture names, or sentinel values.
- Independently parse typed references, execute all reducers and accepted semantic policies, rebuild all positive packets, recompute hashes, validate exact schemas, and report zero unverified rows.
- Add active in-memory fully resealed controls for all historically demonstrated fail-open attacks.

Freeze exact future producer allowlist (the existing 11 paths) and keep it absent until a fresh reviewer returns `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_2`. Pin accepted parent, semantic-delta manifest/record, rejected v0.1 negative snapshot, protected typed sources, exact root init and deterministic 542-file medical-writing aggregate. Require 8911 stopped.

Run generator `--check` across at least three `PYTHONHASHSEED` values under normal/O2, verifier normal/O2, exact no-cache Ruff, SHA stability, pins, allow/deny, producer/bytecode absence, S5 lock, and port boundary. If the accepted semantic delta or typed sources still cannot honestly construct a leaf, stop and name the leaf/source gap; never create a mirrored or self-proving oracle.

Only a later fresh reviewer may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_2`. This task does not accept either producer, S5, UI/browser, real project/model, product, clinical authority, or production.

Return a compact handoff: boundary, files, counts, architecture, active attack outcomes, normal/O2/cross-seed/Ruff/pin/absence/8911 evidence, final nine SHA values, remaining uncertainty, and next action. Do not self-accept.
