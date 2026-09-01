# Codex Review: monitoring_p10_loop316_protocol_v8_visit_canary_20260801

Date: 2026-08-01
Delegated-agent output: `runs/codex-subagent_monitoring_p10_loop316_protocol_v8_visit_canary_20260801.md`

## Verdict

**FAIL CLOSED.**

The runtime safety contract passed, but the functional/scientific v8 canary gate
did not. Do not retry/reuse v8, salvage any raw candidate, expand to another
topic/project, make a candidate decision or enter MY009.

## Boundary Check

- Exactly one POST created new v8 job
  `monai_06e9dd4e1b18677ff748ed792445`; one attempt and one controlled repair
  occurred. There was no repeat POST, retry, other v8 topic, candidate decision
  or salvage.
- v4 remained 8 jobs / 8 attempts / 8 proposed candidates; v5-v7 remained one
  attempt and zero candidates each.
- 8911 was started only through `scripts/start_stable_backend.zsh` and gracefully
  stopped immediately after terminal capture. 8911/5174 are stopped.
- The existing native Luna reviewer session `/root/rux_protocol_v4_audit` was
  reused read-only after prompt preflight. No new reviewer or fallback was used.
- No product or medical-writing source was edited by this canary task.
- A concurrent medical-writing source edit at 09:13 CST was preserved and not
  repaired or reverted.

## Codex Verification

- Fresh rollback backup:
  `runtime/backups/pre_loop316_protocol_v8_visit_canary_20260801_0859CST/`;
  21 main DB copies, 18 immutable integrity OK, 3 empty byte-preserved.
  Backup monitoring-AI DB SHA-256:
  `db8d057d054b972b227c2fe281e31388effed2cbf6cacbe85d1a8bcbb5a0d350`.
- Readiness: 200/ready, schema 16, no missing capability; product AI
  `alibaba_token_plan/qwen3.8-max-preview`, no Codex runtime dependency.
- Active prompt:
  `monitoring-protocol-clause-structuring-v8`.
- Terminal job: failed / `invalid_ai_output`, attempt 1, zero candidates.
- Attempt:
  `monattempt_e635a4f195ae4784b825a9be12399e8b`.
- Request SHA-256:
  `87bfc229bf678d11dfd8fc330f2609c9998be7c6dae596228a4c92ab6f3a9488`;
  193,622 bytes.
- Response SHA-256:
  `aba303673d7585e9aa620b44cb70b8129e080f94bc50fd9f6f8eeed01a40e234`;
  21,585 bytes; initial plus one repair.
- Repaired deterministic result:
  - candidates 1-2 use negative scope disclaimers that name reschedule and
    unscheduled families, creating mixed-family lexical hits;
  - candidate 3 is scientifically a single postpositive-trigger reschedule
    clause but retains off-topic dispensing/return uncertainty and
    withdrawal/lost-to-follow-up guidance; its schedule-family hit is also a
    bounded semantic-role false positive;
  - candidate 4 is scientifically unscheduled-only but names safety follow-up in
    a negative scope disclaimer;
  - candidate 5 is deterministic-valid but cannot be split from the invalid
    whole response.
- Whole-response atomicity correctly persisted zero candidates.
- Post-canary tests:
  - focused monitoring: `376 passed in 13.46s`;
  - adjacent medical-writing: `200 passed in 3.14s`;
  - standard `pytest tests -q -k monitoring`: blocked before monitoring
    execution by concurrent medical-writing collection drift
    (`_REQUIRED_CORE_BODY_SEMANTIC_IDS` removed from source but still imported
    by `test_medical_writing_dynamic_section_matrix.py`);
  - bounded monitoring rerun excluding only that unrelated collection file:
    `1371 passed, 4283 deselected, 27 warnings in 731.00s`.
- The five governed v8 product/test hashes were unchanged by the canary.

## Hermes / Delegated-Agent Output Review

- Luna independently returned **FAIL CLOSED** and separated scientifically
  coherent single-topic cores from executable-contract noncompliance.
- The reviewer confirmed that removing uncertainty/user guidance from the full
  boundary would weaken off-topic protection.
- It also rejected broad negation exceptions and global reschedule precedence:
  both could hide genuine prohibitions or true mixed-family clauses.
- The smallest safe future direction is provider-contract wording that forbids
  repeating excluded topic/family names in all user-visible fields, plus a
  separately bounded postpositive-trigger semantic-role correction.
- Reviewer source hashes match the exact preflighted prompt, context, terminal
  evidence and validator source.

## Residual Risk

- v8 remains functionally unaccepted. The current terminal output is immutable
  evidence only and must not be reused, retried or salvaged.
- A future corrective must preserve medication, dispensing/PK, withdrawal,
  safety, collection, full-boundary and exactly-one-family gates.
- Any provider-visible wording change requires a fresh prompt identity, offline
  negative matrix, full regression and independent review before another
  single-topic canary.
- The standard full-monitoring command is currently collection-blocked by
  concurrent medical-writing source/test drift. This task proved monitoring
  behavior with a one-file exclusion but did not and must not claim the standard
  repository-wide selector is green.
