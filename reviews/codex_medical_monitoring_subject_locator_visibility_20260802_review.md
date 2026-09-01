# Codex Review: medical_monitoring_subject_locator_visibility_20260802

Date: 2026-08-02  
Delegated-agent output: none; Codex performed the bounded slice directly

## Verdict

**Pass for the declared offline locator-visibility slice.** The records now expose the explicit source locator at the same point where a medical monitor reads the fact. This does not establish source authenticity, clinical validity, B6 authority, or commercial readiness.

## Boundary Check

- Hermes workflow guard was used for local task initialization and review-gate validation only; no Hermes/provider session, worker, or sub-agent was dispatched.
- Code changes were limited to `medicalMonitoringSubjectModels.mjs`, `MedicalMonitoringSubjectViews.jsx`, and their focused test. Protected `App.jsx`/`styles.css` hashes are unchanged.
- Only task-scoped context/review/metrics/active-record, release-audit/coverage, and LOOP/roadmap evidence surfaces were updated. No backend, runtime, SQLite, medical-writing, or source-registry state was touched.
- B6/C14 remain fail-closed: `pending_review` / `blocked_pending_b6_review`, five candidates, zero outcomes, no write/migration/activation/event/projection authority.

## Codex Verification

- Source review confirms the helper reuses explicit provenance fields already accepted by the Subject Timeline/Profile contracts; it does not synthesize locators from display text or dates.
- Timeline detail, metric point detail, PD/Query cards, risk prompts, and source-event index now display the locator or a visible missing marker. Existing metric values, flags, tooltips, lane mapping, and clinical interpretation remain unchanged.
- All medical-monitoring Node tests: **22/22 files passed**; focused frontend contracts: **64 passed**; Vite build: **1925 modules transformed**; release-gate: **7 passed**.
- Current release audit SHA is `fab507b07abe2c6195b98fe061311a6b67a6780d3b9c3d8481bbcd1f581098d9`; coverage replay remains blocked with decision SHA `d1de410a6e9dd9f1b8fafbb2fcf1fad08eaa074d409b4cc06e5ff3b3be6df7b0`.
- No browser/runtime or real-project check was run by design. Service-import checks remain collection-blocked by missing global `cryptography`; no dependency was installed.

## Delegated-Agent Output Review

There was no delegated output. The adjacent surfaces were checked for the same source contract: Timeline rows, trend points, PD/Query, risk prompts, and event index all use the same helper. The display is intentionally a locator label, not a clickable or authoritative source resolver; runtime navigation remains a later acceptance task.

## Residual Risk

- A displayed locator can still point to a stale or misclassified source; only backend source-byte/source-token validation can establish lineage.
- Missing locator markers improve detection but do not recover evidence or prove completeness.
- Browser layout/tooltip density, real three-project payloads, scientific review, B6 outcomes, aggregate/CAS/restart, and commercial release dossier remain unverified.
