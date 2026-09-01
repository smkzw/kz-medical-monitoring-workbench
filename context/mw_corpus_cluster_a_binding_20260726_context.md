# Task Context: mw_corpus_cluster_a_binding_20260726

Created: 2026-07-26 19:17:08
Objective: 以红灯负例证明并修复语料分析G1/G2/G7：复合事实、非数字途径模态陈述和多轴组合必须在单一binding内共现；只做窄门不重构tuple数据模型，保持现有v7与PNH行为
Task type: `finite_code_task`
Risk: `critical`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/CORPUS_V7_GENERALIZATION_GAP.md`
- `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_corpus_policy.py`, read-only
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_generalization_policy.py`, regression
  read/run only
- accepted baseline evidence:
  - `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_strict_gate_codex_acceptance.log`
  - `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_generalization_codex_acceptance.log`

## Scope

- In scope:
  - add three targeted negative tests for G1, G2 and G7;
  - first prove each test fails on the pinned implementation and preserve that
    red-before-fix output;
  - implement the smallest deterministic single-binding/co-observability
    guard in `medical_writing_corpus_analysis_ai.py`;
  - reject or force medical review when one coherent binding cannot support
    the finding's composite statement and layer tuple;
  - run targeted tests and the existing corpus 49/40 regression surfaces.
- Out of scope:
  - full per-binding tuple schema/data-model refactor;
  - changes to corpus policy, PNH triage, prompts outside v7, browser,
    translation/OCR, runtime binding, DOCX or deployment;
  - runtime restart or real AI rerun;
  - broad lint/refactor or unrelated legacy corpus surfaces.

## Success Criteria

- New tests demonstrate:
  1. numbers/route/frequency split across separate bindings cannot produce a
     high-confidence composite finding;
  2. a nonnumeric route/modality statement inconsistent with all bound source
     evidence is rejected or requires medical review;
  3. independently observed axis values cannot create an unobserved
     phase/route/modality tuple.
- Tests are red before the fix and green after it.
- Existing v7 fixtures and accepted fail-closed behavior remain green.
- The implementation does not require schema migration and does not claim
  natural-language semantic equivalence beyond deterministic controlled
  facets.
- Changed files, hashes, red/green logs and residual limitations are returned.

## Risk Boundaries

- Writable production path:
  `services/api/app/medical_writing_corpus_analysis_ai.py`.
- Writable test path:
  `tests/test_medical_writing_corpus_analysis_ai.py`.
- All other listed source and tests are read/run only.
- Do not restart the shared runtime while Slice B browser execution is active.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 19:17:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26: Conference resolved G1/G2/G7 into Cluster A and selected a
  narrow single-binding guard for the launch slice. Full tuple refactor is
  deferred.
