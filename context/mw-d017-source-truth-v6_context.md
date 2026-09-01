# Task Context: mw-d017-source-truth-v6

Created: 2026-07-25 00:13:31
Objective: 修复D017真实独立AI竞品筛选中完整ClinicalTrials.gov适应症条件被截断导致的理由矛盾，并将输出叙述限制为快照可支持事实；保持67候选完整、受限补偿和失败关闭语义。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/evidence/d017_competitor_triage_v4_20260724/search_snapshot.json`
- `runs/evidence/d017_competitor_triage_v5_20260724/run_response_02_final.json`
- `scripts/qc/d017_competitor_triage_v5_acceptance.py`
- `services/api/app/medical_writing_competitor_triage.py`
- Focused tests under `tests/test_medical_writing_competitor_triage*.py` and
  `tests/test_d017_competitor_triage_v5_acceptance.py`.
- Observed acceptance failure: 67/67 candidates and 5/5 chunks complete, but
  six reason contradictions and two unsupported high-risk claims.
- Root cause evidence: canonical model input retained only
  `trial.conditions[:5]`; independent acceptance used the complete frozen
  ClinicalTrials.gov condition list, where several PNH matches occurred after
  the fifth entry.
- External verification: the official ClinicalTrials.gov Search Areas
  documentation states that `query.cond` searches a weighted ConditionSearch
  area spanning Condition, titles, MeSH/ancestor terms, keywords and NCT ID.
  Therefore search retrieval is intentionally broader than an exact
  `conditions[]` match and requires deterministic post-retrieval condition
  reconciliation.

## Scope

- In scope:
  - Preserve the bounded missing-NCT repair and exact candidate coverage.
  - Add a compact, deterministic full-condition indication signal without
    sending unbounded condition lists to the model.
  - Regenerate reviewer-facing dimension text, evidence gaps and reason from
    explicit snapshot/project fields.
  - Bump prompt identity, add deterministic tests, restart the stable backend,
    and run a fresh D017 production-AI pass.
- Out of scope:
  - Confirming the competitor basket before all scientific acceptance checks
    pass.
  - Changing the ClinicalTrials.gov frozen snapshot.
  - Inferring modality, route, mechanism or design from medical prior
    knowledge not present in the snapshot.

## Success Criteria

- A fresh direct `deepseek/deepseek-v4-pro` run returns `review_ready`.
- Five chunks cover the same 67 unique NCT IDs with no unknown or duplicate ID.
- Full-condition PNH matches and non-PNH conditions produce classification and
  reason text that agree.
- Independent acceptance reports zero reason-consistency and unsupported-claim
  issues.
- Focused and adjacent deterministic tests plus Python compile pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 00:13:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25 00:18: Added v6 canonical indication facts
  (`project_indication_match`, `matching_conditions`, `condition_count`) and
  source-bounded reviewer narratives; initial adjacent test run reached
  209 passed with three expected stale-v5 assertions pending update.
- 2026-07-25 00:31: Focused/adjacent suite passed 241 tests. Stable backend
  restarted with build `api-41aabbd87cc18859`; direct production AI readiness
  is `deepseek/deepseek-v4-pro` with no Codex dependency. A fresh v6 run
  `ct_run_0a629f725d89d560e459` was created from the unchanged frozen snapshot.
- 2026-07-25 00:32: The fresh run completed 5/5 chunks and returned 67/67
  unique candidates. The independent deterministic acceptance report
  `runs/evidence/d017_competitor_triage_v6_20260725/acceptance_report.json`
  passed every identity, completeness, source, reason-consistency and
  unsupported-claim check. The stable backend was then genuinely restarted
  after terminating the orphaned pre-restart uvicorn process; build
  `api-efc983b8932ef508` marks v5 runs stale while v6 remains review-ready.
- 2026-07-25 00:40: Independent clinical review
  `reviews/d017_v6_independent_clinical_review.md` rejected basket
  confirmation despite the structural pass. It found three explicit PNH
  phase-II pharmacologic studies (`NCT05731050`, `NCT06978699`,
  `NCT07212426`) falsely excluded because the strict indication matcher did
  not recognize the common `PNH - Paroxysmal Nocturnal Hemoglobinuria`
  condition alias. The v6 run is preserved as audit evidence and must not be
  confirmed. A v7 bounded fix will support only independently delimited
  abbreviation/full-name aliases, add false-positive counterexamples, bump
  run identity, and require a fresh independent-AI run.
