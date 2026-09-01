# Task Context: medical_monitoring_my008_p2_two_snapshot_revalidation_20260802

Created: 2026-08-02 10:12:06
Objective: Revalidate two current MY008 PNH 2-03 full listing snapshots and deterministic diff evidence without onboarding or runtime writes
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current read-only listing snapshot A:
  `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/交接资料/MY008 长期安全性研究/医学监查/回复_ MY008211A-PNH-2-03项目_34例受试者_数据列表_20250417的全部附件20250421/MY008211A-PNH-2-03_数据列表_20250417/MY008211A-PNH-2-03_数据列表_20250417.xlsx`.
- Current read-only listing snapshot B:
  `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/2-03/阶段性数据/【251202cut】MY008211A-PNH-2-03_冻结后数据列表_20251202_23_22.xlsx`.
- Historical source/validation and diff assertion to revalidate:
  `records/active_slices/medical_monitoring_goal_p2_20260729/MY008_REAL_TWO_BATCH_EVIDENCE.json`.
- Parser/classifier/diff implementation: `services/api/app/listing_file_parser.py`,
  `services/api/app/monitoring_source_classifier.py`, and
  `services/api/app/monitoring_batch_diff.py`.
- Current workbench AGENTS and P0/P2 requirements remain authoritative for the
  read-only boundary and the distinction between source evidence and runtime
  approval.

## Scope

- In scope: rehash both current workbooks; parse and classify each with the
  current parser/classifier; normalize rows with the current identity version;
  recompute the deterministic cross-snapshot row/field/schema diff; compare
  counts and identities with the historical P2 evidence; run focused engine
  regressions.
- Out of scope: Source Registry mutation, source confirmation, onboarding,
  mapping approval, clinical-event/risk creation, risk migration, aggregate or
  CAS writes, provider/AI calls, SQLite/runtime/service/browser, and any
  medical-writing file.

## Success Criteria

- Both current files hash to the P2 evidence anchors.
- Both parse with no warning, have the expected full-domain set, and classify
  as raw snapshot candidates without silently accepting derived comparison data.
- Deterministic diff reproduces the P2 row/field/schema/removal counts.
- Focused source-classifier/diff tests and Python compilation pass.
- Evidence clearly states what is revalidated and what remains unapproved.

## Risk Boundaries

- Original workbooks are read-only. Only the declared task evidence/context,
  review, and metrics paths may be written.
- Do not use the historical `full_snapshot_proven` boolean as a new approval;
  it is accepted only as the existing frozen-source assertion while current
  hashes and parser/diff outputs are independently rechecked.
- No delegated agent, provider, service, browser, 8911/5174, SQLite, B6/C13,
  runtime, or medical-writing surface is touched.
- Codex owns verification and acceptance; this task cannot create a formal
  reviewer outcome or activation authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 10:12:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 10:13-10:18 CST: Direct Codex read-only revalidation found the
  current hashes exactly match the historical P2 anchors. Both workbooks parse
  as 33 sheets/32 domains with no warnings and classify as
  `raw_full_snapshot_candidate`.
- 2026-08-02 10:18 CST: Current deterministic normalization/diff reproduced
  25,156 new rows, 1,258 changed rows, 7,401 persisting rows, 40 removed rows,
  5,295 field changes, zero schema diffs, and zero blocked removals; source
  domain sets are equal. The accepted full-snapshot assertion is the existing
  frozen Source Registry evidence in the P2 record, not a new approval.
- 2026-08-02 10:18 CST: Focused classifier/diff tests passed 30/30 with two
  existing parser-library warnings; py_compile passed. No production/runtime
  state changed. Evidence is ready for review-gate.
