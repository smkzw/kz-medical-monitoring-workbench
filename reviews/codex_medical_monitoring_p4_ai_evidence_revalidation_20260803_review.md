# Codex Review: medical_monitoring_p4_ai_evidence_revalidation_20260803

Date: 2026-08-03 CST
Route: direct Codex under Hermes (`codex/codex-main/high`); no delegated agent/provider.

## Verdict

**PASS for the bounded read-only P4 evidence revalidation contract; P4 and
commercial release remain blocked.**

## Review findings

- The new contract is deliberately outside the provider/queue/repository and
  only reopens the existing commercial coverage JSON plus its declared source
  files.
- It requires direct regular files, rejects traversal/symlinks, compares bytes
  and SHA-256, and surfaces coverage/status/authority drift.
- It does not equate `evidence_fresh` with AI quality: the current report is
  source-fresh but `product_ai_evidence_complete=false` because the three
  persisted P4 artifact identities are absent.
- An arbitrary existing JSON file cannot satisfy a required artifact identity;
  the contract reports it as unbound/invalid.

## Boundary Check

- Only the task-scoped module, tests, context, review, metrics and diagnostic
  artifact were changed. Product source, runtime, provider configuration,
  database and protected frontend/medical-writing surfaces were untouched.
- The persisted report keeps all authority flags false; `evidence_fresh` is not
  an approval signal.

## Verification

- Focused **8 passed in 0.04s**; adjacent `tests/test_monitoring_ai_*.py`
  regression **639 passed, 17 existing warnings in 14.96s**.
- py_compile, Ruff check and Ruff format check passed.
- Persisted artifact replay was exact: report `blocked`, 3 typed missing-artifact
  issues, report SHA
  `22009949d014a624db709e3a900c6f3dc7c09a91515c67e193d1345dce15a298`.
- No provider, browser, service, API login, SQLite/CAS/runtime or real-project
  action was attempted; 8911/5174 remain stopped.

## Residual risk

The contract proves only current evidence availability and source freshness. It
does not supply real AI observations, clinical/scientific accuracy, prompt/model
approval, human review, browser acceptance, B6 outcome, CAS replay or commercial
release. Those remain downstream controlled gates.
