# Codex Conference Review: commercial_platform_foundation_20260710

Date: 2026-07-10 CST
Review state: conference complete; architecture adjudicated; implementation acceptance remains test-gated.

## Verdict

Proceed with a narrow Option A implementation: standard-library `sqlite3`, explicit repository/Unit-of-Work boundary, versioned forward migrations, atomic state + audit + idempotency, and default-deny AI execution policy. Do not treat the foundation slice as commercialization completion.

The five independent participants unanimously selected Option A and deferred SQLAlchemy/PostgreSQL and Temporal. The Hermes chair package is substantive, but several of its additions exceed the smallest reliable first slice and require main-venue challenge before adoption.

## Boundary Compliance

- Five participant files and the Hermes chair file are substantive and workspace-bounded.
- Buddy Minimax and Buddy GLM-5.2 used the requested Buddy routes. Mimo/Qwen used OpenCode Go. DeepSeek Flash used Reasonix CLI, not Hermes/OpenCode.
- Qwen's first run completed without replacing the placeholder. The failure was preserved; one controlled serial retry wrote the required output successfully.
- Delegated outputs are advisory. Codex re-read the current contracts, RUX inbox/approval path, AI runtime, test harness, and current local runtime behavior.
- Original clinical-project source folders were not modified.

## Participant Outputs Reviewed

- `participant_qwen_plus.md`: Option A; broad traceability and migration controls; successful controlled retry.
- `participant_mimo.md`: Option A; detailed SQL/test inventory, but wider than a minimum first slice.
- `participant_ds_flash.md`: Option A; strongest current-code compatibility analysis and recommendation to separate persistence from AI-policy migration.
- `participant_buddy_minimax.md`: Option A with explicit warning that SQLite alone does not solve identity, privacy, or audit trust.
- `participant_glm52_product.md`: Option A with product and cross-module contract perspective.

## Hermes Sub-Venue Review

Accepted from the chair package:

- include `data_classification` in AI policy and AI-derived write metadata;
- distinguish server-generated request/event identity from client-provided idempotency key;
- scope idempotency by tenant + project + operation/key and hash the normalized request payload;
- server-resolve actor identity, while preserving a temporary compatibility alias because authentication is not yet implemented;
- use a controlled `reason_code` plus free-text comment for regulated state transitions;
- keep an outbox/job table in the same database instead of introducing Temporal;
- require corruption detection, migration tests, cross-project collision tests, and public-payload leakage tests.

Main-venue challenges:

1. Per-aggregate tables for every named domain are not required to prove the first transaction kernel. A small generic aggregate-state table plus typed repositories can be safer for the first vertical slice; schema specialization should follow measured query/index needs.
2. Adding `Handoff`, `SafetyEvent`, `Citation`, and `ModuleStateView` contracts now broadens the slice without proving transactional behavior. Keep these in the cross-module contract backlog unless the first vertical path needs one.
3. A second JSONL copy is not WORM and can create a second inconsistent write path. The first slice should deliver a tamper-evident hash chain and verified export format; immutable/WORM storage is a later deployment control.
4. Down migrations are not automatically safer. Production data migrations should be forward-only with backup/restore and explicit recovery; reversible schema-only tests may be used only where lossless.
5. UUID v7 is not available in Python 3.12 standard library. Do not add a dependency just for sortable IDs; use UUID v4 plus server timestamp or a small documented alternative.

## Main-Venue DeepSeek Pro Review

Reasonix DeepSeek Pro accepted Option A and supported the Codex challenges against a second JSONL audit writer, production down migrations, UUID v7 dependency and mixing persistence with AI-policy changes. It recommended a generic state kernel and four cross-module contract stubs; Codex does not adopt those two additions in Unit 1 because current-code fault injection identified a narrower typed RUX/approval transaction boundary that preserves the existing public API and directly closes the observed split-write defect.

The reviewer required explicit identity disclaimers, project-scoped idempotency with payload hashes, hash-chain audit integrity, rejection audit events and two sequential implementation units. Those controls are adopted within the boundary described in `ACCEPTED_FOUNDATION_DECISION.md`.

## Codex Independent Verification

- Current code still uses multiple JSONL/in-memory stores and has no common transaction boundary.
- Current write requests accept client-provided `actor`; this is not a trustworthy identity and must not be described as authentication or electronic signature.
- `AiTaskRequest.allowed_sources` remains client-provided on direct submission paths; current tests prove prompt-envelope behavior but not policy-governed real-provider execution.
- The RUX disposition path checks `expected_source_version`, then creates an approval gate and appends a separate disposition JSONL record. It is a suitable first vertical path because the current two-write sequence is not atomic.
- Baseline regression passed with the explicit Python 3.12 dependency path: 205 tests in 109.385 seconds. Two earlier attempts failed only because the default interpreters could not import `openpyxl`, `docx`, and then `xlrd`; those environment failures are recorded and not hidden.

## Final Decision

Final implementation boundary:

1. Land failing-first tests for the real RUX disposition submission and approval-action fault boundaries.
2. Add one shared typed `SqliteRuntimeStore`; migrate existing RUX runtime JSONL once and stop writing migrated JSONL files.
3. Prove atomic gate/disposition and gate/audit/decision commits, restart, collision handling, idempotency, rejection audit, hash-chain integrity and malformed-store diagnosis without changing visible clinical semantics.
4. Land the server-side AI policy resolver as the next sequential unit and close both the forged-source and cross-module-source bypasses before any independent provider is treated as governed.
5. Keep SQLAlchemy/PostgreSQL, Temporal, full RBAC/e-signature, WORM storage, cross-module contract expansion and broad frontend refactoring outside Unit 1.

Conference review is complete. Only implementation and verification evidence can close the active foundation slice.
