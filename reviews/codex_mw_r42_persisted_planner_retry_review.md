# Codex Review: mw_r42_persisted_planner_retry

Date: 2026-07-31
Independent review output: `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`

## Verdict

CODE AND RETRY-LINEAGE READY; PRODUCT RECOVERY PARTIAL. Persisted generation,
canonical-source/sibling behavior, and Pro eligibility passed independent
acceptance and isolated runtime proof. Three plans recovered; one planner and
the downstream Hy-MT2 route remain blocked.

## Boundary Check

- Current implementation is confined to the upper-layer contracts, executor,
  production adapter, repository audit payload, translation pipeline/batch,
  and directly related tests listed in the task context.
- No monitoring-subsystem file, product runtime SQLite store, OCR/download
  artifact, provider setting, role binding, or credential has been changed by
  this code-gate verification.
- Independent reviewer path/write compliance remains to be checked after it
  returns.

## Codex Verification

- Re-read current source for the persisted executor, adapter, validation-code
  mapping, batch propagation, and payload-only attempt lineage.
- Confirmed the persisted adapter discards the legacy `_invoke` callback, so
  the legacy outer retry cannot stack with the service-owned two-call Flash
  sequence.
- Final deterministic suite:
  `190 passed, 17 warnings in 8.59s` from the parent Codex run.
- One isolated API retry created exactly four generation-2 Flash source runs
  for four artifacts and no sibling planner run. Three plans succeeded and
  were saved; one Flash×2 plus Pro path retained
  `planner_duplicate_chapter_identity`.
- The three successful-plan items reached `translating_hy_mt2` and failed with
  internal `body translation model unavailable: HTTPError`.
- Original r42 SQLite still shows 2 `candidate_ready`, 13 `excluded`, and 5
  `failed_retryable`, attempt 1, with 23 stage runs.

## Independent Review

- Initial acceptance: READY, no P0/P1/P2.
- Legacy-source review: NOT READY because `interrupted` was accidentally
  excluded.
- Corrective re-review: READY; sole P1 closed. Focused independent result:
  `3 passed, 17 warnings in 2.34s`.

## Hermes / Route Review

This bounded finite-code repair used the current native Codex execution and
independent-review routes selected by the workflow guard. Hermes/aishuo was not
used for this code gate or runtime retry and is not represented as acceptance
evidence. The goal-level Hermes/aishuo and Reasonix multi-perspective product
acceptance remains a later pre-launch requirement after the current planner
and Hy-MT2 blockers are closed.

## Residual Risk

- The former duplicate-chapter and Hy-MT2 HTTP blockers are closed on the
  isolated clone. Attempt 3 ended `completed_with_blocked`, not unqualified
  full recovery: `4 candidate_ready / 15 excluded / 1 fidelity_blocked`.
- The remaining fidelity block was independently diagnosed as a general
  protocol-heading abbreviation false positive. The v0.30/v36 code and
  regression fix is READY, but the immutable blocked row has not been
  regenerated and must not be manually admitted.
- A future continuation must first design and verify a single-item,
  downstream-contract transition for the one blocked item. It must not assume
  the batch retry endpoint safely targets only that row, and it must not rerun
  the four candidate-ready or fifteen excluded rows.
- Original r42 remains unchanged and is evidence-only. No claim is made that
  the original five historical failures were modified or that deleted parent
  JSONL history was restored.

## Updated Verdict At No-loss Pause

PLANNER/TRANSLATION CONTRACT CODE READY; CLONE ATTEMPT 3 TERMINAL WITH ONE
KNOWN FALSE-POSITIVE BLOCK; V36 RUNTIME REMEDIATION NOT YET AUTHORIZED.

Decisive evidence:

- `runs/mw_r42_attempt3_controlled_recovery_20260731.md`
- `runs/codex_mw_r42_abbreviation_fidelity_diagnosis.md`
- `runs/codex_mw_abbreviation_stopword_contract_fix.md`
- `runs/codex_mw_abbreviation_test_evidence_rereview.md` — READY
- Parent gates: `232 passed` and `198 passed`, both with 17 existing warnings.
