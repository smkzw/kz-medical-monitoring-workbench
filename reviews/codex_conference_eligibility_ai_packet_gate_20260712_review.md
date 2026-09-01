# Codex Conference Review: eligibility_ai_packet_gate_20260712

Date: 2026-07-12

## Verdict

Pass after Codex P1 patch and focused aishuo follow-up. The original chair and main-venue reviews missed a reproducible false-completion defect; Codex added a failing-first test, fixed source coverage, and obtained exact-route `aishuo/MiniMax-M3` confirmation that the P1 is closed.

## Boundary Compliance

- Qwen and Mimo were read-only OpenCode Go participants.
- The required Hermes sub-venue chair and focused follow-up both ran on exact `aishuo/MiniMax-M3`; stdout verifies provider, model, completion and no fallback.
- DeepSeek Pro ran only through Reasonix CLI, never Hermes/Buddy/direct DeepSeek.
- Generated Buddy DeepSeek and GLM-chair prompts were excluded because they conflict with current project routing.
- Delegated models did not inspect original clinical folders, images, browsers or production data and made no source edits.

## Participant And Chair Findings

- Qwen correctly raised completeness/redaction concerns but made a factual error that packet digest omitted evidence locator; line-level source review refuted it.
- Mimo traced the full request and raised rate-limit/concurrency gaps. These are bounded P2 concerns for the local single-user profile; authentication and remote throttling remain production gates.
- The first aishuo chair correctly rejected several overclaims but incorrectly treated the six-subject matrix label as proof that code blocked incomplete source coverage.
- Reasonix DeepSeek Pro required Codex to inspect the workflow gate directly but still initially accepted the bounded implementation.

## Codex P1 Reproduction And Patch

Codex created a subject with two current file-level sources while only one source had a sampled-pass evidence span. The old `_subject_evidence_processing_state` counted only existing spans and returned `completed`; the packet builder therefore accepted a materially incomplete packet.

The fix now requires:

- every current source to contribute at least one sampled-pass evidence span; and
- every existing current span to be resolved before the aggregate can be `completed`.

The regression test failed before the patch and passed after it. A second test covers one source with both resolved and unresolved spans. The exact-route aishuo follow-up independently reclassified the defect as a real P1 and accepted the patch.

## Other Accepted Hardening

- Current rule text uses a per-criterion normalized-text digest rather than a protocol-wide file hash.
- Stale rule/source, forged locator/text, missing or non-QC evidence fail before provider call.
- Controlled artifact body is integrity checked, schema allowlisted, extraction-revision bound, UTF-8 strict JSON and size bounded.
- Packet digest and provider echo bind current revisions, criteria, evidence locator and evidence text hashes.
- Stable packet-level batch idempotency skips a second provider call after a committed batch.
- Public medical-action API rejects `save_ai_draft`; client actor is stored only as an unverified claim.
- Decisive provider results without evidence IDs now fail output validation before persistence.
- API integrity failures return sanitized 409 details.

## Codex Verification

- Failing-first source-coverage counterexample reproduced, then closed.
- Focused eligibility packet/AI/contract/workflow/store/API/matrix suite passed 47/47 after final lint cleanup.
- Ruff passed on all changed Python files.
- Authoritative backend regression passed 570/570 in 198.424 seconds.
- Frontend production build passed with the pre-existing >500 kB chunk warning.
- AI-disabled route remained fail-closed; no Codex fallback and no real provider call occurred in product tests.
- No real clinical image was sent to VLM. Browser/image/PPT checks were not relevant to this backend-only slice.

## Final Decision

Accept the bounded controlled-artifact eligibility AI packet and public API foundation. The reproduced P1 is closed.

Production remains blocked on authentication/RBAC/tenant identity, remote rate limiting, durable concurrent in-flight AI claim, page-level processing completeness, explicit `processed_no_relevant_evidence`, safe archive extraction, DOC/DOCX subject extraction, full visual QC and the six-subject real-project evidence pipeline. The matrix is a reproducible inventory and gate declaration, not proof that those flows are complete.
