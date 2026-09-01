# Codex Conference Review: eligibility_vlm_contract_v01_20260711

Date: 2026-07-11

## Verdict

Pass for the v0.2 design contract and nonclinical implementation planning only. Production implementation and real clinical-image use remain blocked by the explicit v0.2 exit criteria.

## Boundary Compliance

- Prompt preflight passed for all dispatched roles after removing the generated production-like absolute workspace path.
- Qwen's first run produced substantive stdout but failed to replace the guard placeholder; the failure evidence was retained and a controlled same-route retry produced a substantive 177-line file.
- Mimo and Reasonix DeepSeek Flash produced substantive files on their assigned routes.
- The Hermes chair ran on the required `aishuo/MiniMax-M3` custom endpoint. Actual provider/model markers were observed; no chair fallback was used.
- No delegated model read clinical images, wrote production code, browsed, or authorized medical/eligibility conclusions.

## Participant Outputs Reviewed

- Qwen: remove `body_region`, `laterality`, and `pairing`; keep but narrow `possible_identifier_visible`. Flagged status ambiguity, incomplete cross-field rules, silent structured-output downgrade, Chinese/image-metadata injection gaps, retry bounds, consent provenance, logs and retention.
- Mimo: remove `body_region` and `laterality`; move temporal pairing server-side; keep `possible_identifier_visible` as a best-effort alert. Flagged normalization, exact denylist, retry/error taxonomy, canonical digest, audit schema and F10/F20 testability.
- DeepSeek Flash: remove `body_region` and `laterality`; replace temporal pairing with visual-only grouping; keep the identifier alert with explicit non-guarantee. Flagged model-set `rejected`, attention/status contradiction, complete metadata stripping and independent human fixture review.

## Hermes Sub-Venue Review

The 355-line `aishuo/MiniMax-M3` chair package is substantive. It converges on removing body region/laterality, preventing temporal pairing claims, keeping a narrowly framed identifier alert, and retaining fail-closed production behavior. It identifies twelve v0.2 P0 contract changes and a consolidated F21-F25 fixture extension. Codex has not yet accepted the chair's suggested exact pixel limit, retry count, retention period, or UI-signing wording; these require main-venue challenge and implementation-context verification.

## Main-Venue DeepSeek Pro Review

Reasonix DeepSeek Pro produced a substantive 297-line review. Codex accepted its schema-notation, server-derived provenance, orientation, circuit-breaker, identifier-alert and fixture clarifications. Codex rejected its claim that the Hermes chair violated the read allowlist by reading SOUL: Hermes prompts are required by the project workflow to read SOUL, while the no-SOUL rule applies to Reasonix. Codex also rejected universal image limits and an unrelated fixed retry count before the production model is benchmarked.

Because v0.2 removed the model-emitted status and removed pairing rather than retaining a visual-only variant, Codex requested a focused same-route follow-up. Verified `aishuo/MiniMax-M3` produced a substantive 334-line review and found no remaining P0. Codex applied its direct contract tightenings: document orientation semantics, positive prohibition of status/decision keys, visual-QC non-guarantee wording, deterministic F24a/F24b fixtures, versioned retention policy, and explicit authorization for later-profile requeue.

## Codex Independent Verification

- Codex checked official vLLM multimodal and structured-output documentation, OWASP LLM01/02/05, NIST AI 600-1, and ICH E6(R3) before drafting v0.1.
- Codex verified actual route markers in Hermes stdout for Qwen, Mimo and `aishuo/MiniMax-M3`, and the Reasonix route identity in the participant output.
- No production source was changed, no test regression was required for this design-only round, and no clinical image was inspected or processed.
- Codex compared v0.2 against the durable evidence job implementation: current jobs already persist configurable `max_attempts` (default 3 in current service paths), so v0.2 correctly reuses that contract rather than introducing an inconsistent fixed retry count.
- Codex verified v0.2 contains no model-emitted status, body region, laterality, pairing, fixture media class, undefined structured-document catch-all, or duplicate inference field.

## Final Decision

`VLM_CLOSED_VOCABULARY_CONTRACT_V0_2.md` is the accepted working contract for the next nonclinical implementation slice. No production or clinical-image authorization is granted. The product worker remains `vlm_gateway_not_configured` until the typed schema, policies, gateway, F01-F23/F24a/F24b/F25-F28, privacy scans, two-project regression, Codex visual check, and independent human fixture review pass.
