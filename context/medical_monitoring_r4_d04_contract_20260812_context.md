# Task Context: medical_monitoring_r4_d04_contract_20260812

Created: 2026-08-12 00:18:11
Objective: 冻结并独立审阅R4-D04入排、方案要求与潜在PD合成离线纵切合同
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`, frozen common R4 contract and D04 row.
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`.
- Accepted common R4 implementation contracts under `poc/medical_monitoring_ai_native_r4/src/mm_r4/` and D01-D03 contract/review evidence; reuse only, no implementation edit in this task.
- `clinical-eligibility-review` skill for official criterion numbering, phase selection, evidence hierarchy, rule-specific evidence gates, conservative OCR/EDC boundaries and pilot-first review.
- Current filesystem is authoritative. Official ICH/NMPA/FDA sources discovered in this task may inform the contract and will be recorded with exact URLs/access date.

## Scope

- In scope: define and independently challenge the R4-D04 synthetic/offline contract for protocol version applicability, inclusion/exclusion and other protocol control points, rule decomposition, subject-level evidence matching, L1 positive/negative/boundary/not_evaluable, counterevidence, Query wording, identity/lifecycle, incremental behavior and renderer-neutral outputs.
- Out of scope: source implementation, R5 UI, real-project data, OCR/VLM runs, formal PD submission/closure workflow, safety/security design/testing, product services and medical-writing files.

## Success Criteria

- Contract preserves official protocol criterion numbering/hierarchy and requires explicit phase/cohort/version applicability before evaluation.
- AI output never claims a formal PD; positive output is a concrete medical-monitoring issue to verify and a three-part Query draft.
- Aggregate IE/IEYN, missing rows, OCR success and model output are never promoted to rule-level evidence without rule-specific support.
- Exact evaluation-unit identity, partial dates, units, thresholds, retests, exceptions/waivers, cross-table evidence, N-to-N+1 lifecycle and Query/projection boundaries are frozen.
- Synthetic challenge matrix and implementation acceptance checks are specific enough for a separate execution task.
- Independent fresh-context reviewer returns ACCEPT after all blocking findings are closed; Codex review gate passes.

## Risk Boundaries

- Write only task context, D04 contract/review/metrics/prompts/runs. Do not edit R4 source or tests in this contract task.
- Keep 8911 stopped; do not start services or run any real project.
- Do not access or modify the medical-writing subsystem.
- Do not encode one study's criterion IDs, thresholds, drug names or data-listing layout as universal logic.
- External/model evidence is advisory; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-12 00:18:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- D03 accepted and archived; D04 is the next plan-ordered slice. Contract freeze must precede implementation.
- Drafted `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`; initial SHA `fb5adc12a36e0c3dbe1c709e7d0abfee0047b695895bb350c17cff5c0c8832b0`.
- Incorporated official-source method boundaries: project protocol remains the project authority; protocol applicability uses event/site-adoption time; China GCP method metadata is effective-date versioned; FDA 2024 document remains draft/advisory.
- Independent engineering challenge session `7a9ce30b-8e01-4f27-9672-de8975eac56e` required two same-session completion recoveries before returning a complete `REVISE`. It identified duplicate producer/D04 risk ownership, missing parent rollup, incomplete canonical identity, multi-version cardinality, waiver history, cross-domain join and machine-close flag gaps.
- Codex revised the draft. Grok's revised-snapshot recheck cancelled after the permitted recovery budget, so the declared Cursor fallback was used rather than treating fragments as acceptance.
- Cursor fallback session `32fea678-0077-442c-9696-bd68a863aa53` returned `REVISE` on current-surface conflicts, then the same session accepted the focused corrective at SHA `870b89d0c91d36ae8516204c6a1f9d7d6f3b6bb8687c3da3ab0ed3eb7fee441c`.
- Codex then found two additional main-venue executability issues: a fixed parent L1 precedence was incorrect for protocol AND/OR/AT_LEAST_N packages, and frozen R2 `RiskInstance` cannot persist arbitrary closure flags. Current draft SHA `927b79e9197fc28ed3a03426ebbc626e7452034ec3fc861c6760381f8a01d2ea` now uses an explicit parent issue expression over feasible uncertain assignments, and maps critical candidate flags to severity=high before R2 establishment so the existing high-risk close gate persists the prohibition without modifying R2.
- Current contract status remains `DRAFT_R4_D04_CONTRACT_V1_1`: the earlier engineering ACCEPT is evidence for the prior snapshot, not automatic acceptance of the current SHA. Independent clinical/protocol participant remains pending in its original session; after its findings are closed, the current final SHA must return to the same Cursor fallback session for a focused recheck. No implementation starts before both reviews accept the same immutable snapshot.
- Port 8911 remained stopped; no real project, service, R4 source/test or medical-writing file was touched.
- 2026-08-12 main-venue clinical conservatism pass: narrowed exception/waiver semantics so only a protocol-defined exception or an effective formal rule change can enter rule evaluation; a merely approved-looking, retrospective or explanatory record cannot rewrite an unmet eligibility/protocol requirement as compliant. Added a closed `exception_effect` classification and updated synthetic rows 25/26/61. Also made D03/D04 treatment-discontinuation ownership explicit, clarified that only D04-owned atomic components (including explicitly not-applicable components) enter D04 expected-set, and narrowed cross-domain challenge 31. Current draft SHA after these changes: `250b5ad6b29841f6fde67d1fb540f899613ce94cf560439e69d456dde163d042`.
- The clinical/protocol participant remains active in original Pi/Qwen session under runner PID 3218 / provider process PID 3437. Slow execution has not been treated as failure or redispatched. Because its initial pass began on an earlier draft, its completed report will be treated as challenge evidence and the same model session must recheck the final SHA after blockers are closed.
- 2026-08-12 second main-venue clinical pass: made Query wording conditional on evidenced enrollment context, so a confirmed screen failure in a person never randomized/enrolled/treated does not receive a PD-assessment sentence; unresolved enrollment state first asks for status/timing. Added challenges 75-76. Expanded protocol applicability with amendment transition/grandfathering, re-consent and control-point scope; site adoption alone cannot apply an amendment to every ongoing participant. Added challenges 77-78. Current draft is still unfrozen and now has SHA `b9a0cf84fc6d5efba1dadfa2bcaa45d89d7a4b2b14bebdf24523754aedd02eec` with a continuous 1-78 synthetic challenge matrix.
- 2026-08-12 closure: Pi/Qwen and Cursor accepted semantic SHA `4dce9df5e6416a7f8b8133af9b64cfb5dc8afd09c6949812d7e089204bf35baa` after the L0/L1 and Chinese-label corrective rechecks. The contract was frozen as `FROZEN_R4_D04_CONTRACT_V1_1`; status/freeze-record-only SHA is `6d0a7ee2fe507555f68f7a719c60dfa2cc92f995fcaf2c4a3825bbcb3bc6d6b5`. Challenge matrix is continuous 1-83. Port 8911 remained stopped and no implementation or real-project path was touched.
