# Task Context: mw_release_r5_tester_a_consolidation_20260728

Created: 2026-07-28 06:18:45
Objective: 归并 release-r5 Tester A 六视角缺陷证据，区分产品缺陷、测试器缺陷和证据缺口，形成最小修复批次与验收标准
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-authorized evidence root:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/`
- Allowed evidence: A1/A2/A3 `lazy_medical_writer` and `engineer`
  `DEFECTS.md`, `EXTERNAL_TESTER_REPORT.md`, `FIX_RETEST_LEDGER.md`, plus
  necessary top-level JSON used to verify the named defects.
- Reports and tester interpretations are evidence, not authority; unsupported
  root-cause claims must remain hypotheses.

## Scope

- In scope: deduplicate by common root cause; classify product defects,
  tester defects, and evidence gaps; reconcile two-perspective conflicts; map
  minimum source/test scope; define repair batches and acceptance criteria.
- Out of scope: product-source reads or edits, model/service reruns, runtime
  database inspection, secret/config inspection, and release retesting.
- Allowed deliverable:
  `runs/execution/mw_final_4x3_harness_20260727/reviews/TESTER_A_CONSOLIDATED_20260728.md`

## Success Criteria

- A1 pipeline timeout/full-basket/false-progress evidence is consolidated.
- A2 synopsis timeout/terminal-state propagation evidence and conflict are explicit.
- A3 list 422/skip-all/refresh/duplicate-request evidence is consolidated.
- Every inferred root cause is marked as unverified unless directly supported.
- The report contains a minimal source/test map, ordered repair batches, and
  batch-level acceptance standards.
- Final report exists at the required path and passes a full reread/sanity check.

## Risk Boundaries

- Do not modify product source or runtime state.
- Do not rerun models, services, or product tests.
- Do not read credential-bearing runtime files.
- Codex owns the evidence classification and final report.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 06:18:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-28: Read the 18 authorized Markdown files and selected top-level JSON.
- 2026-07-28: Consolidated five release-blocking root causes and separated
  conditional findings, tester defects, and seven conflicts/evidence gaps.
- 2026-07-28: Wrote and reread the required report; checksum
  `3260f5045592d7755f4989c0c4d831e33e1c05cb851bcb99c03c1b53a4778940`.
