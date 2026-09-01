# Medical Writing Final 5x3 - release-r9-20260728

## Goal

Resume the user-mandated five-tester visual E2E matrix after repairing
`MW-A1-002`. This round is immutable. It must not reuse any project, job,
database, browser profile or PASS claim from release-r8.

## Governing Contract

- Global AGENTS SHA-256:
  `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`
- Matrix: `scripts/qc/mw_final_5x3_matrix.json`
- Frozen source receipts: 57, all matching.
- Harness/runtime/baseline tests: 69 passed.
- Focused MW-A1 repair tests: 66 passed.
- Frontend triage presentation tests: 14 passed.
- Round input fingerprint:
  `5d787256352646b2608d8ccced2a930b7e925452babbcca5454db6e0f0a8fd5f`

## Frozen Prior Evidence

- `release-r8-20260728` remains a blocked run for `MW-A1-002`.
- It must never be resumed, rewritten, relabeled or counted as PASS.
- The accepted repair records are:
  - `runs/hermes_mw_a1_triage_finalize_r8.md`
  - `runs/cursor_mw_a1_triage_finalize_r8_manager.md`
  - `runs/hermes_mw_a1_triage_finalize_r8_followup.md`

## Active Run

- Slot/perspective: `A1/lazy_medical_writer`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield.
- Frontend: `http://127.0.0.1:51565`
- Backend: `http://127.0.0.1:51564`
- Runtime identity:
  `7ea35114464a8e92a627844b5cd6a1365a1769b8b4d8aa80b58eeac2746bb856`
- Clean state receipt:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/CLEAN_STATE_RECEIPT.json`
- Product source changes are forbidden while this run is active.

## A1 Acceptance Emphasis

- Operate only through the real rendered desktop page.
- Product independent AI must perform search, triage, source processing,
  evidence analysis and writing; the tester must not substitute its own text.
- Confirm the basket once through the visible bulk action.
- Make one evidence-supported manager adjustment when the UI supports it, so
  the run proves that the exact confirmed retained set is preserved.
- No second confirm/continue click, no duplicate confirmation, no recomputed
  AI-default basket, no duplicate download/extraction.
- Continue through complete protocol, DOCX, PDF and native Word inspection.
- Slow independent-AI work remains pending through the 120-minute hard wait;
  latency alone is not a blocker.

## Stop Rule

On a material product blocker, preserve exact browser/action/runtime evidence,
stop the isolated services, repair only the reproduced cause, refresh frozen
source receipts, and create another new round. On full acceptance, record PASS
only through the established per-slot schema, then start the A1 engineer
perspective from a separate clean runtime.

## Terminal Result

- Status: `BLOCKED / FAIL`, never PASS.
- Tester completed at the translation/corpus scope gate and was closed.
- Runtime services were stopped cleanly; ports 51564 and 51565 were released.
- Project: `proj_user_1511dd2045f2`.
- Snapshot: `wref_search_83cb7d74adc5e6250bcc`.
- Exact visible failure:
  `M11 结构范围（已选 0/0）` and
  `候选范围预览失败：'proj_user_1511dd2045f2/wref_search_83cb7d74adc5e6250bcc'`.
- The SAP was parsed into 7,087 spans and its structure review was approved,
  but no preparation batch or translation batch existed.
- The browser/API trace contains no
  `POST .../medical-writing/research-pipeline/start` after the successful
  competitor-search request. The journey therefore had a confirmed discovery
  projection but an empty `research_pipeline` object. The confirmation-time
  auto-advance correctly did nothing because no parent pipeline existed.
- The frontend currently applies the competitor-search journey response and
  calls the parent `onJourneyChanged` callback before it posts the pipeline
  start request. The project surface can remount during that state transition,
  so the intended start request is abandoned.
- Evidence root:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/`.

## Required Repair Boundary

- Preserve this round and its databases as immutable failure evidence.
- Make successful competitor search and research-pipeline startup one reliable
  orchestration transition. A user must not need to notice or repair the
  missing parent pipeline.
- Do not synthesize a preparation/translation batch in the UI and do not relax
  document, translation, corpus-admission or product-independent-AI gates.
- Add deterministic API/frontend regression evidence proving that a journey
  response/remount cannot suppress pipeline startup.
- Refresh frozen source receipts and create a clean `release-r10` round after
  acceptance.
