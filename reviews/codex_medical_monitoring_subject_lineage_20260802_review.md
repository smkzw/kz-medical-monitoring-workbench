# Codex Review: medical_monitoring_subject_lineage_20260802

Date: 2026-08-02  
Delegated-agent output: none; Codex performed the bounded slice directly

## Verdict

**Pass for the declared offline source-lineage display slice.** The code makes provenance status more visible without upgrading any release, medical, or runtime authority. The commercial release gate remains blocked.

## Boundary Check

- No delegated agent, provider, service, API, browser, SQLite, migration, or real-project execution was used.
- Hermes workflow guard was used for local task initialization and review-gate validation only; no Hermes/provider session was dispatched.
- Product changes were limited to `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`, `MedicalMonitoringSubjectViews.jsx`, and the subject-model test. The protected `frontend/src/App.jsx` and `frontend/src/styles.css` hashes are unchanged.
- Task-scoped context/review/metrics/active-record, release-audit, coverage, and LOOP/roadmap evidence surfaces were updated. No medical-writing files or runtime state were changed.
- B6/C14 remain fail-closed: five candidates, zero outcomes, `pending_review` / `blocked_pending_b6_review`, with no write/migration/activation/event/projection permission.

## Codex Verification

- Source review confirmed the backend models expose explicit source revision/locator fields and the three real adapters report `source_revision()` through the registry stability boundary. `legacy` remains a demo/non-authoritative sentinel.
- `subjectEvidenceLineageSummary()` filters `legacy`, treats batch-only as partial, counts only explicit locators, and keeps empty/unbound states non-authoritative. It does not derive source identity from date, title, order, count, or free text.
- Subject model tests: **60 passed**; full medical-monitoring Node suite: **22/22 files passed**; focused frontend Python contracts: **64 passed**; Vite build: **1925 modules transformed**; source-revision tests: **7 passed**; release-gate regression: **7 passed**.
- Release audit and coverage were rebound after LOOP 4.08. Current audit SHA is `1ae750ae6650fcf08199966a50ddc82ffa339bf2b9b983eecc4ce56613c04d67`; coverage evaluator returns `blocked`, `release_ready=false`, `0/12/3/1`, decision SHA `2e0d5785847f6efa316aee0046c33d82cfdf581af4b4294d0f3882b20206d83d`.
- Browser/runtime, visual acceptance, full service imports, scientific validation, and real-project LOOP were not run. Service-import tests are collection-blocked by missing global `cryptography`; no dependency was installed.

## Delegated-Agent Output Review

There was no delegated output. Codex reviewed the implementation and adjacent contract surfaces directly. The helper is a presentation-layer warning/summary, not a source-authority implementation; it intentionally leaves backend source-token and B6 gates untouched. The only adjacent gap identified for later work is visible per-row locator detail and runtime/browser proof, both outside this bounded slice.

## Residual Risk

- A truthful `source_revision` still requires real source bytes and adapter revalidation; the UI cannot establish that itself.
- Missing locators remain possible in upstream payloads and are surfaced as partial, not repaired or inferred.
- No evidence here proves clinical correctness, completeness, trend comparability, scientific reviewer agreement, persistence/restart behavior, or commercial readiness.
- Next authorized sequence remains B6 outcome validation → aggregate/CAS replay → MY009 legacy source-token revalidation → approved-input dry-run → controlled runtime and three-project browser/science/UAT.
