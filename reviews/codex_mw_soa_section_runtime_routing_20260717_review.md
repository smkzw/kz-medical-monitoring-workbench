# Codex Review: mw_soa_section_runtime_routing_20260717

Date: 2026-07-17 11:51 CST
Primary record: `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/TASK_RECORD.md`

## Verdict

Passed for this bounded slice. M11 1.3 and recognized imported research-flow-table sections now open the existing SoA designer with explicit zero/one/multiple-candidate behavior, controlled mapping, working-copy persistence and deterministic DOCX export. The medical-writing programme remains active beyond this slice.

## Boundary Check

- No new table model, version island, dependency, project-specific rule or automatic mapping confirmation was introduced.
- Source DOCX and stable runtime were read-only during isolated E2E; their hashes were checked before and after.
- Kimi and Grok outputs were treated as evidence. Codex reviewed source, tests, browser states, original screenshots and Word output and retained final authority.

## Verification

- 105 focused frontend/backend contract and document-session tests passed.
- Vite production build passed; only the pre-existing chunk-size warning remains.
- Isolated D001, PNH and synthetic E2E passed with no skips, failures, console errors, page errors or HTTP failures.
- D001/PNH real source sessions exposed the SoA binding, opened source-native tables without mutating them, saved and reloaded version 1, and each exported 24 tables.
- Synthetic flow proved zero/one/multiple candidates, all dismissal paths, duplicate confirmation, idempotency, edited plan states, structured note persistence, DOCX output, CAS 409 and approval lock.
- Independent `python-docx` inspection found the edited `条件` cell and structured note in the synthetic Word output and no raw Markdown/HTML placeholders.
- Original-resolution 1920x1080 and 1440x900 review found no page overflow or incoherent overlap. Multi-candidate rows now include stable visible ordinals.
- Stable frontend and backend return HTTP 200; backend integrity, foreign key and audit checks pass. Stable D001 and PNH sessions expose M11 1.3 SoA semantics after restart.

## Execution Review

- Kimi remained responsive through extensive tool work but the resumed runner hit its external 3600-second limit before writing a final report. This is not classified as model failure or token exhaustion.
- Grok responded before a global `findskills` MCP package failure cancelled its host. The host defect was not mixed into product code.
- Future Kimi terminal connectivity/token failure uses the user-authorized `Hermes/aishuo/cms-model` fallback after a controlled retry; slow progress alone is not a fallback trigger.

## Residual Risk

- The production bundle remains large and should be addressed as a separate performance slice, not inside the SoA workflow fix.
- Source-native tables remain pending mapping until a medical user explicitly creates and confirms a mapping. This is an intentional governance boundary, not incomplete behavior.
- Broader medical-writing functionality remains under active development; this verdict covers only SoA chapter routing and persistence.
