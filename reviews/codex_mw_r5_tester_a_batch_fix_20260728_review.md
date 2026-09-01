# Codex Review: mw_r5_tester_a_batch_fix_20260728

Date: 2026-07-28
Delegated-agent output: A1/A2/A3 bounded worker handoffs plus source changes
listed in `context/mw_r5_tester_a_batch_fix_20260728_assignments.md`.

## Verdict

Deterministic repair acceptance passed. Real visual release acceptance remains
blocked under immutable round `release-r6-20260728`.

## Boundary Check

- A1/A2/A3 workers remained inside their declared product/test write sets.
- Frozen `release-r5-20260727` evidence was not rewritten.
- Stable ports `8911/5174` and the shared product runtime were not used for
  repair testing.
- A1 preparation scope remains the locked `retained_candidate_ids`; no
  excluded-study or all-search-result prefetch was introduced.

## Codex Verification

- A1 combined backend regression: `66 passed`.
- A1/A2/A3 combined backend regression before the progress patch:
  `330 passed`.
- Frontend medical-writing source contract: `108 passed`.
- Focused React tests: `11 passed`.
- Standalone durable frontend state assertions: `52 passed`.
- Matrix/runtime harness tests plus frontend contract: `145 passed`.
- Vite isolated production build passed; only the existing large-chunk warning
  remains.
- Active product source scan found no `Hy-MT3` alias.
- `release-r6-20260728` froze 42 authoritative source receipts with input
  fingerprint
  `56b3f473fd9a910da9678628816a6d0e81aaa153e2d6119707f30e433e3fdded`.
- A1 lazy-writer visual E2E reached terminal `BLOCKED`: the truthful
  preparation-scope/progress repair passed, but AI triage timeout recovery
  produced a zombie parent pipeline and the UI exposed no failed/retry state.
- Isolated API `51364` and frontend `51365` were stopped and both ports were
  proven released.

## Delegated-Agent Output Review

- Rejected unsupported WAL/pool causality for the A2 timeout.
- Preserved exact A3 list-field contract rather than generalizing every field
  to a list.
- Preserved closed COPD equivalence rather than fuzzy indication matching.
- A1 progress now reports locked candidates, public documents, completed
  documents and current NCT/document from persisted batch state.
- Tester D identity is corrected for new rounds to exact
  `pi/google-antigravity/gemini-3.6-flash`; `high` remains a separate thinking
  level.

## Residual Risk

- A1 progress updates at document boundaries. A single document that blocks
  inside download/extraction has no finer substage pulse.
- Triage timeout -> retry -> review-ready is not implemented correctly.
- Complete protocol generation, DOCX/PDF/native Word gates and remaining A1
  engineer/A2/A3/Tester B/C/D runs are not yet accepted.
- No `PASS.md` may be created until all external gates pass.
