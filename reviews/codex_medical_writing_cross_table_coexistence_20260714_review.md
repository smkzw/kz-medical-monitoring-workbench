# Codex Review: medical_writing_cross_table_coexistence_20260714

Date: 2026-07-14
Delegated-agent output: `runs/reasonix_medical_writing_cross_table_coexistence_20260714.md`

## Verdict

**PARTIAL ACCEPT for advisory findings; PASS for Codex-owned implementation and verification.** The delegated output is retained but is not a clean bounded review.

## Boundary Check

- Prompt preflight initially failed on a wrong exporter filename and an absolute workspace path. Both were fixed before dispatch; second preflight passed.
- Reasonix wrote the requested run file and did not edit source/tests, but it read `medical_writing_table_domain_profiles.py` after the prompt limited the read list to eight files. This is a read-list violation even though the file was inside the workspace and the action was read-only.
- The boundary violation prevents treating the delegated output as fully compliant third-party evidence. Codex independently re-read the relevant implementation before any edit or acceptance.

## Codex Verification

- Replaced the existing five-profile real-project test with a stronger three-project coexistence contract covering all 11 current table templates plus the original source blocks.
- RUX-03-002, CMS-D001 and MY008211A-PNH-3-01 each proved: source prefix unchanged; 11 generated tables preserve order; only one selected profile changes; ten siblings remain byte-equivalent at `structured_table`; profile/non-profile semantics remain separate after cold restart.
- Approval blockers resolve exactly to the five profiled table `block_id` values. Schedule of Activities and the five generic/C-grade templates receive no domain-profile blocker.
- Draft Word export preserves the 11 generated table order and visible header cells, with no Markdown separator leakage.
- Focused coexistence: 1 passed; related table/export set: 33 passed; medical-writing set: 168 passed; full repository: 872 passed with 12 existing warnings.
- Adjacent inspection after the first gate found that inline Tiptap edits updated only top-level table rows. Production code now synchronizes nested generated-table rows by stable `cell_id`, and repository save validation rejects stale dual representations for both source-linked and generated blocks when nested rows exist.
- Post-fix verification: focused synchronization 2 passed; document export/API 5 passed; frontend medical-writing contract 36 passed; medical-writing glob 147 passed; full repository 872 passed with the same 12 warnings; frontend production build and backend compile passed.
- Live runtime clarification: the MY008 imported SoA source table intentionally has only top-level rows, so it is outside the dual-representation contract. A validation probe changed its first cell and was immediately restored through the public API; audit revisions 1 and 2 remain visible. No generated-table live state was modified.
- API 8911 was restarted. Health, SQLite integrity/schema 14 and all five table-domain profiles were verified from the running service.
- Browser/visual DOCX acceptance was not run in this slice because the current execution context did not authorize further browser use. No visual-pass claim is made.

## Delegated-Agent Output Review

### Hermes / Reasonix Routing Note

This scoped patch-plan task was routed by the workflow guard to Reasonix rather than a Hermes conference because the previous Hermes conference had already settled the architecture. Reasonix remained advisory; Codex performed all production edits and verification.

Accepted:
- Correctly identified the missing SoA-plus-profile coexistence test and the need to assert blocker attribution per table.
- Correctly focused Codex verification on real SQLite restart, Word output and full regression.

Rejected or corrected:
- The output claimed profile instance state includes `evidence_grade`; actual `word_layout.domain_profile` does not store it. Evidence grade belongs to the profile catalog, not each table instance.
- The suggested `mwgenerated_` prefix assertion would hard-bind validation to an implementation naming convention without adding identity safety beyond existing uniqueness checks.
- Raw database tampering is not the right persistence test for this slice; cold restart through the public repository contract is authoritative.
- The output's no-collision conclusion was treated as a hypothesis until Codex ran the three-project all-template test.

## Residual Risk

- Desktop visual inspection of the combined editor state and generated DOCX remains pending for a later authorized browser/Word QC loop.
- This test validates all current template classes but not every future profile schema version; additions must extend the same coexistence contract.
- The frontend synchronization helper is protected by a source contract and end-to-end repository/export tests, but a browser keystroke-to-network payload visual run remains pending because browser use is outside this execution slice.
