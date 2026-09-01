# Codex Review: medical_monitoring_subject_locator_shape_20260802

Date: 2026-08-02
Delegated-agent output: none; direct Codex implementation and review. No external route was dispatched.

## Verdict

**Pass for this bounded Subject Timeline/Profile locator-shape guard; commercial release remains blocked.**

## Boundary Check

- No delegated agent, service, provider, browser, API, SQLite, real project or long task was started。
- Product edits are limited to `medicalMonitoringSubjectModels.mjs`, its test, and `MedicalMonitoringSubjectViews.jsx`；`App.jsx` and `styles.css` remain protected。
- 8911 and 5174 have no listening process；unrelated 18911/PID 43191 was not touched。

## Codex Verification

- The previous `String(item || "")` coercion path is removed. Locator state follows field shape, retains readable strings only, and marks malformed input explicitly。
- Timeline tooltip uses the state message; malformed locator rows are visible as `来源定位形状异常` and are not counted as fully bound lineage。
- Subject model passed; all medical-monitoring Node files **22/22** passed; focused frontend contracts **64 passed**; Vite **1925 modules transformed**; release-gate **7 passed**。
- Hermes workflow `review-gate --require-verification` is the final record-integrity check for this direct Codex slice。
- Audit/coverage hash replay after appending LOOP 4.16 passed; audit SHA `142d9658384fc4be669966b573e41235a838186ff429ccd83bf0b7d455237474`, coverage SHA `12c82028e7a23c4b93cf62960a55953a413ab4de6170b531173878374b18cc2a`, decision SHA `bf27a4878154b1fe19438af230a57e2d2272dd71d6fffbe7268b5568e87b5b04`; release remains blocked at `0/12/3/1`。

## Delegated-Agent Output Review

Not applicable. Direct Codex work was required by the user’s no-conference instruction. The change is limited to the existing Subject/Profile source-locator consumption boundary。

## Residual Risk

- A visible locator remains an index, not proof of source-byte/token authenticity or clinical correctness。
- B6 remains `pending_review` with five candidates and zero outcomes；C14 remains fail-closed；aggregate/CAS replay and MY009 source-token revalidation remain unresolved。
- Browser/runtime, real-project, UAT and service-import checks were not run；service imports remain blocked by missing global `cryptography` and no dependency was installed。
