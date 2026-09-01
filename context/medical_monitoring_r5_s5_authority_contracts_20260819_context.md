# Task Context: medical_monitoring_r5_s5_authority_contracts_20260819

Created: 2026-08-19 19:54:42
Objective: 冻结并独立验收 R5-S5 两项上游公共权威合同，随后冻结 S5 实现合同并在门禁满足后实施 synthetic/offline S5
Task type: `stage_review_plan`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-sol` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `.hermes/plans/2026-08-19_1945-medical-monitoring-r5-s5-contract.md`
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md` and its accepted machine artifacts.
- `context/medical_monitoring_r5_s4_acceptance_record_20260819.md` plus the accepted S4 runtime/erratum evidence.
- Current R1/R4/R5 dataclasses, tests, canonical hashes and current filesystem; reference renderers and fixtures are not authority.
- The user-approved System Design v1.1 and R0-R8 implementation plan.

## Scope

- In scope: inventory and freeze `subject-temporal-public-v1` and `aemh-match-history-public-v1`; independent acceptance; then freeze and accept the exact S5 synthetic/offline renderer-neutral implementation contract; implement S5 only after all mechanical unlock gates pass.
- Out of scope: frontend, services, packages, runtime, browser/Playwright, port 8911, real project data, real models, clinical writeback, production, security-specialty work, and every medical-writing surface.

## Success Criteria

- Every S5 core leaf resolves to an exact accepted upstream leaf or the stage remains fail-closed; no fixture or local inference substitutes for authority.
- Independent verdicts `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1` and `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1` exist for immutable snapshots.
- The exact 64 inherited S5 challenge rows are pinned without a second quota ledger.
- `ACCEPT_R5_S5_CONTRACT` is issued only with zero deferred core authority leaves; runtime files do not exist before that verdict.
- Focused and adjacent normal/O2 tests, Ruff, fresh imports, SHA/path boundary checks and independent runtime acceptance pass before S5 closure.
- Port 8911 has no listener throughout this stage.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- R4, accepted R5 S1-S4, root `src/mm_r5/__init__.py`, `frontend/**`, `services/**`, `packages/**`, `runtime/**`, all real project roots, and every resolved medical-writing path are read-only protected surfaces.
- Public-authority contract and S5 contract/runtime paths are create-only and must be frozen before each corresponding independent review.
- 8911 must remain stopped; no service start is authorized in S5.
- Current worktree is not a Git repository; preservation is enforced by explicit pre/post SHA and path inventories.

### Public-authority contract stage create-only allowlist

- `reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/base_inputs.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json`
- `tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`

No public-authority runtime source or test file is unlocked by this allowlist. A separately frozen and independently accepted implementation contract is required before any producer/adapter/validator module is created.

### Starting protected anchors (2026-08-19 20:04 CST)

- R5 root init: `0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd`.
- Accepted R4/R5-S4 readonly manifest: `53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822`.
- Accepted R5 v0.3 exact contract: `3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`.
- S4 acceptance record: `1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e`.
- Medical-writing matched path inventory: 542 files across protected frontend/services/packages/runtime/deploy paths; aggregate `sha256(path + NUL + file_sha256 + newline)=feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`.
- Canonical protected product roots include `frontend/src/features/medical-writing`, `services/api/assets/medical_writing_corpus`, `services/api/assets/medical_writing_glossary`, `deploy/medical_writing_local`, and `runtime/medical_writing_synopsis_artifacts`; all resolve under the current workbench and existed at the starting snapshot.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-19 19:54:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-19 19:55 CST: Re-anchored latest global/workbench instructions and the accepted S5 plan. Confirmed the two required upstream public contracts are still named deferred; 8911 has no listener. Began read-only source inventory before any contract or runtime creation.
- 2026-08-19 20:03 CST: Two fresh read-only audits independently returned `REVISE_SUBJECT_TEMPORAL_PUBLIC_V1` and `REVISE_AEMH_MATCH_HISTORY_PUBLIC_V1`. Existing R1/R4/R5 objects provide reusable identity, visit, locator, risk and hash primitives, but no accepted public projection closes the required temporal member/date/visibility lineage or AE/MH cross-snapshot append-only match history. S5 runtime remains mechanically locked. The next bounded action is contract-only creation under the exact allowlist above.
- 2026-08-19 22:21 CST: After five bounded repair passes and six fresh isolated reviews, the stable public-authority contract snapshot received `ACCEPT_R5_S5_PUBLIC_AUTHORITY_CONTRACT`. Normal/O2 generator and verifier passed with 64 inherited cases and 194 public-authority gates (138 fully resealed); Ruff, protected pins, the 542-file medical-writing aggregate, no-runtime/no-test, stopped-8911 and start/end SHA checks passed. This verdict only unlocks a separately frozen public-authority implementation contract. It does not accept either producer and does not unlock the S5 contract/runtime.
- 2026-08-20 00:23 CST: Three implementation-contract review loops exposed a repeated template-self-proof failure: class-level path existence did not prove root reachability; previous/current output paths formed cycles; fixtures and mutation adapters were placeholders; validator/static gates could be satisfied without consuming authority. Following the LOOP stop rule, the strategy changed from incremental patching to a first-principles machine-contract rewrite. A fresh read-only architect froze the replacement design: structured source/previous/output/controlled/constant path grammar, root reachability and output DAG, constructible fixture graph, typed adapter DSL, reseal DSL, validator sensitivity gates, and closed reachable-call AST policy. Producer creation remains locked.

### Public-authority implementation-contract stage create-only allowlist

The read-only stage planner completed at 2026-08-19 22:33 CST. Contract creation is limited to:

- `context/medical_monitoring_r5_s5_public_authority_implementation_contract_20260819_context.md`
- `reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1_20260819.md`
- `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/public_api.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/source_join_matrix.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/invariant_error_matrix.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/test_matrix.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json`
- `tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py`

The workflow prompt and runner-owned review/metrics records may be created under their standard
`prompts/`, `reviews/`, `metrics/`, `.hermes/` and `runs/` task paths. No producer source/test/evidence
file may be created until a fresh reviewer returns
`ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT` on one stable snapshot.

### Producer implementation create-only allowlist after contract acceptance

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py`
- `poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py`
- `poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json`

All are create-only and remain locked until contract acceptance. Root `src/mm_r5/__init__.py` must
not be edited; consumers import by full module path. Acceptance of one producer never substitutes for
the other, and S5 remains locked until both producer tokens and `ACCEPT_R5_S5_CONTRACT` exist.
