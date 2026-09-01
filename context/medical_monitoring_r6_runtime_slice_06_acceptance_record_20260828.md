# R6 runtime slice-06 limited acceptance record

Date: 2026-08-28
Decision: `ACCEPT_R6_RUNTIME_SLICE_06_SYNTHETIC_OFFLINE`

## Accepted scope

The four `post_lock_pre_cfdi` fixed-total outputs in the isolated R6 POC: `full_project_report`, `site_materials`, `subject_materials`, and `checklist`. Acceptance covers shared locked identity, fixed population totals, nested content-addressed IDs, Profile/Timeline entry binding, project/site/subject/risk/checklist reconciliation, draft-only/no-send/no-sign/no-PD/no-overwrite boundaries, and bare/envelope set validation.

## Frozen candidate

- Source: `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py` — `58cbcb0f03961d8330fe71cf5530e4d63cf4120cf85202548c2241f7a6e17aa1`
- Tests: `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py` — `a9bc5a7dec7c3af5b1b4d0c51ceb0422fae6aad19e0f7f0f822f74eb5cb5abe0`
- Receipt: `poc/medical_monitoring_ai_native_r6/evidence/r6_post_lock_output_runtime_receipt.json` — `8372f0deb0883d224ade340df5357483e6c3739bc66a0faff0e964f6ba84dd81`
- Contract: `context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md` — `936b56a3885d544d5ba6c4733302da2b9064623f7ea0d60a822812ccc01bd666`

## Decisive evidence

- Focused `351 passed`; full R6 POC `728 passed`.
- Complete normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42` matrix: 9/9 cells, 351 per cell.
- Pi and Grok each used one original session across three passes. Both final verdicts: `accept_limited`.
- Medical-writing protected tree: 542 files, aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`, unchanged.
- Ports 8911 and 5174 remained stopped. No product service, browser, real project, OCR, model, or Harness execution occurred.

## Defects closed

Ghost subjects; checklist-only risks; payload/envelope lifecycle, PD, workflow, overwrite and external-report claims; project-summary drift; evidence-order identity instability; outer/inner kind mismatch; Profile/Timeline cross-subject and dual-key ambiguity; duplicate identities; total/count drift; project checklist scope; missing report/profile fields; check-ID coverage/conflict omissions; and envelope identity discarded by the public set gate.

## Explicit limitation

The set gate can prove cross-wrapper consistency and locked inner binding, but cannot authenticate a globally consistent wrapper-only model/version/algorithm digest replacement without an authoritative `MonitoringRun`. `validate_mode_output` with that authoritative run remains required and rejects such drift.

## Not accepted

Product/runtime integration, real project/report review, medical conclusions, document parsing/rendering, Query dispatch, PD registration/closure, user confirmation, signature/external dispatch, Agent Harness integration, R6 overall, R7, or R8.

## Next safe action

After governance audit/cleanup, freeze the next isolated R6/R7 adapter slice for ExecutionProfile/Agent Harness. It must default to `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`, preserve and later prove `deepseek/DeepSeek V4 flash:max`, and must not hard-code model selection into the R6 medical business objects.

## Governance closure and cleanup

- Both execution and conference review gates passed; conference validation for `mm_r6_runtime_slice_06_acceptance_20260828` passed.
- The original execution packet's metadata audit failure is preserved at `records/mm_r6_runtime_slice_06_original_execution_audit_failure_20260828.md`; it was not relabeled or reconstructed.
- Clean read-only verification packet `mm_r6_runtime_slice_06_final_verify_20260828` passed execution audit with three completed Cursor workers, no follow-ups, no fallback, and no errors.
- Both execution packets' prompts/runs/logs were moved recoverably to `archives/execution/`; product/runtime SHAs remained unchanged and 8911/5174 remained stopped.
- Non-blocking documentation debt: package `__init__.py` still says slice-06 is “in progress”; changing it is deferred because it is outside the frozen source/test/receipt candidate and is not a runtime gate.
