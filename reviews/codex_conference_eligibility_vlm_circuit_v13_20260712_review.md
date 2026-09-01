# Codex Conference Review: eligibility_vlm_circuit_v13_20260712

Date: 2026-07-12

## Verdict

Pass after Codex patch. The conference reproduced one bounded P1 timing defect; Codex corrected it and closed the associated P2 test gaps. No remaining bounded v13 P0/P1 was reproduced. Production VLM remains fail-closed.

## Boundary Compliance

- Participants, chair and main reviewer were read-only and did not run tests or inspect clinical images.
- Qwen and Mimo ran through OpenCode Go as bounded participants.
- The required Hermes chair ran on exact `aishuo/MiniMax-M3`; stdout verifies the requested route, completion and no fallback.
- DeepSeek Pro ran only through Reasonix CLI, never through Hermes/buddy/direct DeepSeek.
- Generated generic conference roles were not used because they conflicted with the user's active aishuo-chair route and the standing Reasonix-only DeepSeek rule.
- Antigravity was excluded because this was a nonvisual backend review.

## Participant Outputs Reviewed

- Qwen found no P0/P1 and identified retention, partial-migration and backward-clock P2 issues.
- Mimo found the decisive P1: closed-state permit TTL reused the 120-second half-open probe lease while the request timeout was also 120 seconds, allowing slow/timeout outcomes to expire before circuit recording.
- Qwen's claim that a frozen dataclass caches the `profile_digest` property was rejected. The property recomputes; `frozen=True` prevents normal mutation but does not cache properties. This error did not affect the circuit verdict.

## Hermes Sub-Venue Review

The 130-line exact-route `aishuo/MiniMax-M3` chair package independently traced worker admission, artifact read, normalization, transport and record timing. It correctly accepted Mimo's P1 and retained Qwen's valid P2 findings. It did not authorize production VLM or close any clinical/identity gate.

The chair repeated the nonmaterial property-caching error. Codex rejects that statement as source evidence.

## Main-Venue Review

Reasonix `deepseek-pro` produced a 278-line independent review and confirmed the P1 execution path. It recommended patching the permit timing, checking rejected circuit outcomes, aligning backward-clock behavior, adding partial-migration recovery coverage and rerunning focused/full regression.

## Codex Patch And Independent Verification

- Decoupled closed-state outcome lease from half-open probe lease.
- Closed permits now derive a lease of `request_timeout_seconds + 30s`; half-open probe lease must be at least that long.
- Added persisted `closed_permit_lease_seconds` policy matching so processes cannot disagree.
- Durable breaker now treats a rejected outcome receipt as a sanitized runtime failure instead of silently discarding it.
- `VlmCircuitCall` marks itself complete before persistence so a persistence exception is not recorded twice on context exit.
- Backward clock on outcome recording now raises the same integrity error as permit acquisition.
- Added production-default timing-margin, partial-migration recovery and F19 provider-retry-exhaustion tests.
- Focused durable-circuit/VLM-worker suite passed 41/41.
- Ruff passed on changed Python files.
- Authoritative backend regression passed 554/554 in 204.737 seconds.
- Frontend production build passed with the pre-existing >500 kB chunk warning.
- No real clinical image, real subject data or production VLM profile was used.
- Browser/PPT/PDF/image checks were not relevant to this backend-only nonclinical slice.

## Final Decision

Accept v13 as the bounded durable-circuit foundation. The conference P1 and its related P2 test gaps are closed.

Production remains fail-closed behind authentication/tenant isolation, approved profile and capability probe, clinical-image authorization, in-flight revocation semantics, human visual QC, no-evidence-span boundary, and permit/outcome archival-retention governance. F20 conflict-rejection audit coverage remains a later operational audit requirement and is not claimed complete.

