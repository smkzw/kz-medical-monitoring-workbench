# Codex Review: medical_monitoring_risk_evidence_focus_20260802

Date: 2026-08-02  
Delegated-agent output: none; Codex performed the bounded slice directly

## Verdict

**Pass for the declared offline risk-association visibility slice.** Explicit relationship fields are now visible and unbound prompts are not silently presented as fully evidenced. The result does not grant risk authority or commercial release.

## Boundary Check

- Hermes workflow guard was used only for local task initialization and review-gate validation; no Hermes/provider session, worker, or sub-agent was dispatched.
- Code changes were limited to `medicalMonitoringSubjectModels.mjs`, `MedicalMonitoringSubjectViews.jsx`, `MedicalMonitoringRiskChecklist.jsx`, and their focused tests. `App.jsx`/`styles.css` protected hashes are unchanged.
- Task-scoped context/review/metrics/active-record, release-audit/coverage, and LOOP/roadmap records were updated; no backend/API/runtime/SQLite/medical-writing state was touched.
- B6/C14 remain `pending_review` / `blocked_pending_b6_review` with five candidates, zero outcomes and no write/migration/activation/event/projection authority.

## Codex Verification

- Contract review confirms `TimepointRiskPrompt` exposes `related_event_ids`, `related_metric_keys`, `related_risk_ids`, and `evidence_span_ids`; the helper reads those arrays only and deduplicates stable strings.
- Linked prompts show deterministic event/metric/evidence counts plus identifiers; no-link prompts show `未绑定关联事实` and a warning that this cannot establish no risk. Checklist rows show explicit locator/reference/malformed/missing badges using the same fail-closed rule.
- Model assertions: **63 passed**; all medical-monitoring Node tests: **22/22 files passed**; focused frontend contracts: **64 passed**; Vite build: **1925 modules transformed**; release-gate: **7 passed**.
- Current release audit SHA is `f517fd88b0bdf6af102edf4388a33a0c4b7a49bed04c46e793109c1f7b42beff`; coverage decision SHA is `45760e4b46c732b6f719c5f07a8f7ee5fa32bea79b659790212e0e17dd70373c`; evaluator remains blocked.
- No browser/runtime or real-project check was run by design. Service-import checks remain collection-blocked by missing global `cryptography`; no dependency was installed.

## Delegated-Agent Output Review

There was no delegated output. Adjacent Profile risk, PD/Query, and dense Checklist-row surfaces were checked together so the same explicit-link rule is not applied to only one card type. The display is a review aid, not a causal inference or automatic navigation authority.

## Residual Risk

- Upstream links may be absent, stale, or semantically wrong; this slice only makes their declared state visible.
- Counts and identifiers do not prove clinical relevance, source authenticity, completeness, or causality.
- Browser density/tooltip behavior, real payloads, B6 outcomes, aggregate/CAS/restart, source-token revalidation and commercial release remain unverified.
