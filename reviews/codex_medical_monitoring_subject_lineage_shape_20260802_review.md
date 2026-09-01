# Codex Review: medical_monitoring_subject_lineage_shape_20260802

Date: 2026-08-02
Mode: direct Codex review; no delegated agent was dispatched.
Source record: `context/medical_monitoring_subject_lineage_shape_20260802_context.md`

## Verdict

**Pass for this bounded offline slice; not a release or runtime acceptance.**

## Boundary Check

- No delegated agent, service, provider, browser, API, SQLite, adapter, real project, B6/C14 authority or migration was used.
- Product changes are limited to the Subject model and its Node regression; `App.jsx`, `styles.css`, API/backend, runtime and medical-writing surfaces were not modified.
- 8911/5174 remain stopped; unrelated 18911/PID 43191 were not touched.

## Codex Verification

- Read V1.1说明书、PRD差距矩阵和分阶段 LOOP 计划 in full, then checked the current P10 ledger/release audit and B6/C14 gate.
- The previous implementation normalized lineage tokens with `String(...)`; the patch now accepts only non-empty strings, ignores explicit legacy/placeholders, and counts non-string fields in `malformedLineageFields`.
- The new regression proves numeric `source_revision` does not become a valid binding while a valid batch remains readable; the result is `partial` with `来源绑定形状异常`.
- `node frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`: passed.
- All `frontend/src/features/medical-monitoring/*.test.mjs`: 22/22 files passed (including 67 model assertions).
- Focused frontend contracts: 64 passed.
- `npm run build` from `frontend/`: Vite transformed 1925 modules and succeeded; existing >500 kB chunk warning remains.
- Release coverage was mechanically rebound to the new release-audit hash `61238b8b13fa5d5d77b624304b6fd45237a2e72a0003f24b3263c787ea399419`; coverage hash `7a29dedd81ee3e31f98fb1db3bae385fbc87ebb5d008ef7f84a497260dc7d16f`; decision hash `52d6955104fc1bd1b77ee3bf0f5faa0486ec92bb189111325cedaa85d0e47c65`. Both top-level and nested gate evidence rows bind the current audit hash.
- Final source hashes: Subject model `e4620c5cf3f29588cef30b5a6d75e3976cd5a9757c29e767129a2e58166e157a`; Subject test `8d1d3cd5c1680be5f304695eb59452b9b48af84408bab7f4bbe062bdfd7f7e0f`; SubjectViews `8e8f6930447fe2d92da6aad9c0a3462f63c4cf30cbea60b6977f7c821939d80e`.
- Release status remains `passed=0, partial=12, unproven=3, blocked=1`, `release_ready=false`; B6 remains `pending_review`, all write/migration flags false.
- Hermes workflow guard `review-gate --require-verification` is the task-record integrity check; it must pass after this review is updated. No Hermes/provider dispatch occurred.

## Delegated-Agent Output Review

Not applicable. Direct Codex retained final authority and did not use an external execution or conference route.

## Residual Risk

- This is a presentation/consumer shape guard, not proof that source bytes, source tokens, protocol facts or clinical mappings are correct.
- B6 reviewer outcomes, aggregate/CAS replay, MY009 legacy source-token revalidation, controlled runtime onboarding, three-project LOOP, browser/scientific/UAT and commercial release remain open.
- The first root-level `npm run build` failed only because `package.json` is under `frontend/`; the correct frontend build passed. No source changes resulted from the failed path.

## Next Safe Action

Maintain B6/C14 fail-closed and 8911/5174 stopped. The next authority-dependent step remains explicit B6 reviewer outcomes, followed by aggregate/CAS replay and legacy source-token revalidation; only then may approved-input dry-run and controlled runtime/real-project acceptance be considered.
