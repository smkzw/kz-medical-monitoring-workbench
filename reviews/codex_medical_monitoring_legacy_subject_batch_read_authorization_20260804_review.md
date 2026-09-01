# Codex Review: medical_monitoring_legacy_subject_batch_read_authorization_20260804

Date: 2026-08-04 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_legacy_subject_batch_read_authorization_20260804.md`

## Verdict

**PASS — direct Codex implementation and verification complete.** The five
legacy subject/batch/session read groups now use the existing
`READ_MONITORING` server-principal/ACL seam. Monitoring writes and unrelated
cross-module legacy surfaces remain unchanged.

## Boundary Check

- Work is limited to the workbench path; no external agent is dispatched.
- Production authentication, writes, runtime, browser, provider and real
  projects remain outside this slice.
- Test middleware only supplies a project-scoped principal in test ASGI state;
  it is not installed in production.

## Codex Verification

- `main.py` now authorizes before service/repository lookup for subject profile,
  batch list, batch detail, batch-diff and intake-session reads, using only the
  existing host principal and `READ_MONITORING` action.
- Dedicated focused suite: **42 passed, 17 existing warnings**.
- Identity/real-project/frontend adjacent suite: **162 passed, 20 existing
  warnings**.
- Full `tests/test_monitoring*.py`: **1937 passed, 25 existing warnings in
  514.90s**, exit code 0.
- `python -m py_compile` passed for `main.py` and all changed test modules.
- Hermes workflow guard review-gate with `--require-verification` is the final
  required check; browser/PPT/PDF/live checks are not applicable while
  P10/B6/C14 gates remain closed.

## Delegated-Agent Output Review

No delegated-agent output was used; Codex owns source authority and final
acceptance. The initial route inventory separated reads from writes, and the
implementation touches only the five named read groups. No new action, role,
client actor fallback or auth parser was introduced.

## Residual Risk

The host principal/session middleware remains absent, so production reads still
return 503 until an approved upstream adapter populates
`request.state.monitoring_principal`. All monitoring writes, dashboard,
workbench inbox, AI legacy surfaces, source registration and disposition
writes still need separate inventory/slices. B6/C14 and real-loop/commercial
UAT gates remain closed.
