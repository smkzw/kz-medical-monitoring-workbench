# Codex Conference Review: monitoring_my009_fullchain_20260710

Date: 2026-07-10

## Verdict

Revise, then implement under TDD. The sub-venue package is accepted as advisory input; production acceptance remains pending implementation, API checks, browser QC and full regression.

## Boundary Compliance

- Qwen, MiMo and Minimax ran through OpenCode Go with the assigned models; DeepSeek Flash ran through Reasonix CLI.
- Each participant wrote exactly one bounded output file and did not edit production code.
- All outputs distinguish evidence, inference, recommendation and uncertainty.
- Qwen/MiMo/Minimax emitted post-completion MCP event-loop cleanup warnings only after their output files were written; these are recorded but are not treated as model failures.
- No participant performed Codex-owned live web, browser, visual, clinical-final or production-write acceptance.

## Participant Outputs Reviewed

- `participant_qwen_plus.md`: accepted for L1-L5 interaction model, empty/loading/error/first-batch states, exact Chinese terminology and desktop browser assertions.
- `participant_mimo.md`: accepted for project-adapter contract, domain boundaries, cross-project tests and incremental implementation shape.
- `participant_ds_flash.md`: accepted for current-code defect locations, fail-closed ordering, MY009 route/raw-config mismatch and RUX-specific coupling risks.
- Codex rejected any unverified suggestion that MY009 rules can reuse RUX clinical rules. MY009 protocol anchors and source fields must be verified directly.

## Hermes Sub-Venue Review

The chair reconciled the three outputs without reruns. Codex accepts the additive adapter approach, the frozen RUX service boundary, strict CM versus investigational-product separation, source-locator privacy and explicit no-baseline wording. Codex does not accept the chair's proposed temporary second named service slot as a durable endpoint design; a small project-adapter registry is clearer and avoids a third-project rewrite, provided the RUX behavior remains unchanged through tests.

## Main-Venue DeepSeek Pro Review

Reasonix DeepSeek Pro completed through the required `deepseek-pro` alias. Codex accepts its amendments: explicit fail-closed non-demo branches; registry identity cross-checks; protocol-locator resolution that suppresses unsupported rules instead of substituting defaults; a canonical public listing label; registry-based inbox wiring; explicit frontend demo renames plus runtime gates; and separate API/browser/privacy acceptance records. Codex rejects its suggestion to use a structured empty subject catalog for an unregistered real service: subject-specific and subject-catalog monitoring routes will return 404 when no real adapter is registered, while list-style inbox routes may return a valid empty 200.

## Codex Independent Verification

- Live `GET /api/projects` confirms canonical MY009 id `proj_my009_uc`.
- Live `GET /api/projects/proj_my009_uc/monitoring/raw-intake` currently returns 404, while legacy alias `my009_uc_monitoring_raw` returns the real 61-sheet, 4,106-row, 26-subject, 12-site snapshot.
- Live `GET /api/projects/proj_my009_uc/monitoring/subjects` currently returns an empty demo-backed catalog (`subject_count=0`, `source_batch_id=demo_subject_monitoring_profiles`).
- Live `GET /api/projects/proj_my009_uc/workbench-inbox` currently returns zero items and zero module summaries.
- Codex parsed the original MY009 listing and directly verified the key field boundaries: CM/CM1/HBYY/JWYY are non-investigational medication/treatment; DA/EX/EX2/EX3 are investigational-product dispensing/exposure/change; SV is the visit axis; QS/QS1/QS2/QS3 contain efficacy/PRO candidates; LB1/LB2 include reference-range data.
- Codex parsed the original MY009 protocol and directly verified table 7 row 29 efficacy endpoints, table 7 row 30 concomitant-medication boundaries, AE collection paragraphs 1354-1356 and dose-action paragraphs 1495-1499.
- Pre-change baseline: `python3 -m unittest tests.test_rux_monitoring_service tests.test_monitoring_raw_project_intake tests.test_frontend_monitoring_contract tests.test_frontend_timeline_contract -v` passed 35/35 in 52.496s.
- Browser QC, MY009 implementation tests, independent-AI semantic execution and full cross-module regression are still pending and must not be represented as complete.

## Final Decision

Conference gate passed for implementation. Implement fail-closed routing and the MY009 adapter with failing-first tests; preserve RUX behavior unchanged; then wire inbox/dashboard/disposition/frontend. Do not enable MY009 efficacy conclusions until QS field mapping is source-verified, and do not mark the slice complete before itemised API, browser, privacy and full-regression evidence exists.
