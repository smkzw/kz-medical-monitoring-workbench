# Codex Conference Review: medical_writing_table_ai_revision_20260714

Date: 2026-07-14

## Verdict

Pass with bounded implementation revisions. The implemented cell-level AI revision loop satisfies the conference's integrity goals while using a stronger typed anchor contract than the chair's JSON-only storage recommendation.

## Boundary Compliance

- `MiniMax-M3`, `deepseek-v4-pro`, and `glm-5.2` completed three rounds in the same recorded session.
- `mimo-v2.5` produced a substantive code-grounded Round 1. The runner then made no progress after output, and one controlled retry also failed to produce a corrected pass. The two sessions were recovered from the Hermes state database and archived after the chair explicitly recommended using Round 1 without another rerun.
- Participants remained read-only and did not claim production, browser, Word, clinical, or regulatory acceptance.
- Trailing Hermes MCP event-loop cleanup warnings occurred after successful output persistence for completed roles. They are retained in the stdout logs.

## Participant Outputs Reviewed

- `MiniMax-M3`: emphasized stable IDs, source-versus-working-copy separation, a single approved apply path, atomic persistence, and cell-level AI state indicators.
- `deepseek-v4-pro`: emphasized table-service routing, structural drift rejection, dual-representation consistency, and source-linked versus generated context labels.
- `mimo-v2.5` Round 1: provided the most code-specific analysis of the existing paragraph apply path, dual table representations, table-service cell edit support, frontend selection infrastructure, and the missing table context packet.
- `glm-5.2`: synthesized global CAS plus block hash, exact cell text and table version guards, pre-edit dual-representation validation, atomic audit/snapshot application, and persistent cell-level AI status.

## Main-Venue Codex Review

Accepted:

- One revision/acceptance/medical-approval/application chain for paragraphs and cells, with `anchor_type="table_cell"` as a strict server-validated branch.
- Stable block, table, row, column, and cell identity resolved against the current working copy; client text is a stale-selection assertion, not a locator.
- Global working-copy CAS, block SHA-256, table version, exact cell text, and stable hierarchy checks before application.
- `MedicalWritingTableService.apply_operations(edit_cell)` as the only cell mutator, followed by dual-representation validation.
- Strict separation of working-copy context from registered original protocol evidence in the independent AI request.
- Explicit accept, medical approval, and apply gates; one immutable snapshot and audit event per successful application; idempotent replay.
- Cell-level before/after diff and persistent AI marker in the existing writing rail and table designer.

Revised or rejected:

- Rejected JSON-only anchor data in `anchor_path`. A typed `MedicalWritingTableCellAnchor` is stored in the existing revision payload JSON, so no SQLite schema migration is required; `anchor_path` remains only a canonical five-ID compatibility representation.
- Rejected normalized or fuzzy cell-text matching. Exact current text is required because a false stale conflict is safer than applying a clinical writing change to the wrong cell.
- Rejected rebuilding raw rows without preserving source metadata. `to_table_block` now synchronizes top-level `rows` and `structured_table.rows` while retaining source-cell fields.
- Rejected presenting working-copy row or note context as evidence. Only separately registered sources may support evidence citations.

## Codex Independent Verification

- Two raw real protocol projects, RUX-03-002 and CMS-D001, completed cell selection, independent AI request, accept, medical approval, explicit apply, immutable snapshot, audit-chain verification, and Word draft-preview export.
- Real registered-source resolution exposed a locator mismatch between editor table cells and Source Registry paragraph locators. A fail-closed exact-quote plus unique-locator-prefix fallback was added; ambiguous matches remain rejected.
- Real RUX Word export exposed source-DOCX sparse grid positions after a legitimate cell edit. The table service now persists the original sparse-grid fingerprint, and the exporter repairs only an exact fingerprint match. Untyped version changes or altered hole sets still fail closed.
- Table/document exporter plus table-AI revision tests: 15 passed after the sparse-grid fix.
- Medical-writing and frontend contract regression: 231 passed.
- Full workbench regression: 864 passed with 12 existing dependency warnings (`SwigPy*` deprecations and `openpyxl` header/footer parsing warnings); no test failures.
- Frontend production build: 1,853 modules transformed; build passed with the pre-existing bundle-size warning.
- API restarted on `127.0.0.1:8911` with the current code. `/api/health` reported `status=ok`, SQLite `integrity_check=ok`, zero foreign-key violations, and zero audit-chain violations.
- Browser acceptance was not rerun in this slice because the prior structured-table slice already completed desktop browser acceptance and this slice did not receive a new browser run. The new AI marker and diff therefore have build/contract verification but no new pixel-level acceptance.
- All five temporary Hermes sessions, including the original and retry MiMo sessions, were exported to `records/hermes_session_exports/medical_writing_table_ai_revision_20260714/` and archived without deletion.

## Final Decision

Accept the implemented architecture and proceed. The review gate passed without warnings or errors. The remaining visual risk is limited to a future desktop-browser pass for the new cell marker and diff state; it does not weaken the backend approval, evidence, versioning, or Word-export boundaries.
