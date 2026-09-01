# Protocol P0 acceptance follow-up — same user session, current-source recheck

This is one targeted same-session recovery pass after your round-1 report. Remain only the senior medical-monitor user perspective; do not perform an engineer pass.

## Hard boundaries

- Runner-managed report path: `runs/role_acceptance/mw_protocol_p0_20260804_round1_user_grok_followup.md`. Write only that report through the runner. Do not edit product source or durable production data.
- Create a **new** isolated clone/runtime under `/private/tmp/` from the current workbench source; do not reuse `/private/tmp/mw-p0-user-r1.d5bf40` or any prior project.
- Start with zero projects. Use a real visible headful Playwright browser for every user action. API/backend reads are allowed only for read-only evidence after clicks.
- Preserve stable API `127.0.0.1:8900`, r42/v36 rows, old batches, and medical-monitoring data.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_resume_20260804_context.md`
- `runs/MW_PROTOCOL_P0_FULL_DRAFT_GAP_RESUME_20260804.md`
- `reviews/codex_mw_protocol_p0_full_draft_gap_20260804_review.md`
- `metrics/mw_protocol_p0_full_draft_gap_20260804_metrics.md`

## Targeted recheck

Codex repaired the source branch that previously converted a valid zero-result public search into `failed/search_no_results`. In the current source it must become `awaiting_corpus_admission` with `error_summary=no_public_protocol_results`, explicitly say that no download/OCR/translation started, and expose the shared-corpus/manual-upload or documented exception route. The compact summary must not claim that a study was retained when `returned_count=0`.

Use a new non-oncology Phase I/II/III indication and a plausible design, provide only natural starting facts, and let the AI lead. Exercise the visible path far enough to verify the corrected state and whether the fallback is genuinely actionable. If the route now permits continuation, proceed through PICOS, corpus admission, source processing, substantive full draft and formal Word as far as safely possible; inspect rendered text, tables, references and links. Do not fabricate facts or bypass evidence gates. If a different P0/P1/P2 appears, document it with exact UI text, state/error codes, screenshots and a concise retest expectation.

### First-principles root-cause rule

Do not accept a banner, disabled button, empty result or apparent completion at face value. For every unexpected response, investigate why: separate ClinicalTrials.gov connectivity/HTTP behavior from Chinese-vs-English alias/query normalization, filters and true source availability; compare the visible request contract with the persisted snapshot. Trace disabled controls to the missing journey fact and API guard, and verify any “complete” claim against durable rows, model/provider receipts and real text/Word output. Raw JSON, “0/4” activity during a wait, a blank design panel or headings-only output is evidence of an unresolved defect until its source is explained. Use bounded read-only checks after clicks, never an arbitrary backend write to force progress, and record the exact root cause and smallest safe retest repair.

## Report

Return a candid continuation report: study, clicks/confirmations/recoveries, whether the zero-result fallback is visible and usable, any remaining dead end, downstream Word evidence if reached, and a clean-round verdict. Do not claim clean or production readiness unless every required criterion is evidenced.
