# Codex Review: medical_monitoring_ai_candidate_fact_first_20260806

Date: 2026-08-06 (Asia/Shanghai)
Route: direct Codex (`hermes/codex/codex-main:high`); no delegated agent or external model was dispatched.

## Verdict

PASS — feature-owned AI candidate presentation now exposes explicit source quote before locator/provenance details. This is not full risk-dock or three-project acceptance.

## Boundary Check

- Product changes are limited to `MedicalMonitoringDailyAiCandidates.jsx/.css`, its Node contract and the focused frontend static contract.
- The normalized `evidence.quote` is rendered only as an explicit source snippet; missing quote is shown as `来源事实正文待核对`.
- No candidate status, risk conclusion, medical confirmation, accept/reject action, API call, actor, organization approval or persistence was added.
- No `App.jsx`, `styles.css`, `main.jsx`, medical-writing source, backend/API/schema/database, provider, browser or runtime file was changed. Protected hashes remain unchanged.

## Codex Verification

- Candidate Node contract: PASS; normalized quote remains available to the view.
- Focused monitoring/timeline Python contracts: PASS — 75 passed.
- Full Node suite: PASS — 44 subtests / 0 failures.
- Vite build: PASS — 1,956 modules transformed; existing >500 kB chunk advisory retained.
- Changed-file hashes: JSX `4c6658dd082c4b33d60560c1ab14db006882716b04d3eb993d07629bddd3f0fd`; CSS `199ca9679e526a2c05b07df36a2f95c98a2dc23fc075538c9fd849cf070e0b77`; candidate test `8f686cd2e7baf1b9532fb11f1c4e31f95f5ee4db53f5f2214e6486a0fa4b5d84`; static contract `25c690afd7b481a405f98863e65bf5037bcef3af7208aa944c5c27d5da394f06`.
- Protected shell hashes: App `de942af37999e708d124c99e1beb47fcd2c405ff23ed83fee6dbcc4cf5e0beed`; styles `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd`; main `869dbab992b086a2c38ae8ab1d44ca9b7d0014ef4614b85a5154bc3fcebc8f05`.
- Listener check: no listeners on 8911, 5174, 8910 or 4173.
- Hermes review-gate is required after this review is completed; the real-loop gate remains `read_only / blocked`.

## Interpretation

The card now follows a limited fact-first path: candidate text/claims, then the explicit source quote, then collapsed version/identity and locator details. The quote is a source-bound display field, not a verified medical finding; no inference is created when it is absent.

## Residual Risk

This slice covers only the daily AI candidate preview. The complete risk evidence dock, source API truth, browser visual acceptance, clinical/scientific correctness, independent-AI evidence, P8 authority, B6/C14, real-project LOOP and commercial readiness remain unverified or blocked. Keep 8911 and all runtime ports stopped.
