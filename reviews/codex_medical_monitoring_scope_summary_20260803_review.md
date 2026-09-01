# Codex Review｜medical_monitoring_scope_summary_20260803

## Review result

**Verdict:** `accepted_for_offline_code_scope`

This was a direct Codex implementation/review pass; no Hermes worker was dispatched. The guard-created Hermes task context remains the durable scope contract, not acceptance evidence.

The change is limited to a read-only frontend projection of the already declared `riskIndex.rollup`. It adds no medical conclusion, no risk mutation, no new authority path and no runtime dependency. The model is explicit-value based: malformed counts and malformed collections remain blocked/partial, and absent site/subject identities cannot be used for focus navigation.

## Evidence inspected

- `services/api/app/medical_monitoring_summary.py::_risk_rollup` confirms the consumed keys are `trial`, `sites`, `subjects`, with `risk_count`, `needs_action_count`, `unread_count`, and explicit distribution maps.
- `frontend/src/App.jsx` confirms the existing `onRiskScopeChange(scope, target)` route callback and current risk snapshot lifecycle.
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` confirms compact project/site/subject navigation and source-first boundaries.
- `records/active_slices/medical_monitoring_scope_summary_20260803/TEST_EVIDENCE.md` records focused and full frontend evidence.

## Acceptance checks

- **Verification:** Codex directly inspected the source contract, mount seam, model behavior and task evidence before acceptance.
- Focused model: pass (19 assertions).
- All medical-monitoring Node contracts: pass (24 files).
- Vite production build: pass (1930 modules transformed); only existing chunk warning.
- Port boundary: 8911/5174/8910/4173 empty.

## Not accepted as proof

This review does not promote the commercial release gate. Real three-project source batches, continuous full snapshots, scientific gold cases, formal B6 outcomes, aggregate/CAS replay, independent product AI, Playwright/browser matrix, restart/performance and final user sign-off remain pending or blocked exactly as recorded in the release audit.

## Next review target

After authority and real-source gates are eligible, reopen the actual desktop runtime and verify the new summary with a real risk snapshot, empty snapshot, sparse subjects, malformed payload, site/subject focus return state and cross-project data conservation.
