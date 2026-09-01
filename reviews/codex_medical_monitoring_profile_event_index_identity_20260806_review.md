# Codex Review: medical_monitoring_profile_event_index_identity_20260806

Date: 2026-08-06 (Asia/Shanghai)
Delegated-agent output: direct Codex; no delegated-agent output
Workflow: Hermes guard initialized the tracked task; direct Codex performed the bounded patch and acceptance.

## Verdict

PASS — bounded feature-owned offline repair.

## Boundary Check

- Direct Codex stayed inside the declared feature-owned view/test and task evidence paths.
- No App shell, backend, runtime, provider, browser, real project or medical-writing path was changed.

## Codex Verification

- `python3 -m pytest tests/test_frontend_monitoring_contract.py tests/test_frontend_timeline_contract.py -q`: PASS (79 tests).
- `node --test frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`: PASS.
- `node --test $(find frontend/src -name '*.test.mjs' -print | sort)`: PASS (44/44 subtests).
- `npm run build` from `frontend/`: PASS; Vite transformed 1,956 modules; existing >500 kB advisory remains.
- Protected `App.jsx`, `styles.css`, and `main.jsx` hashes unchanged.
- Ports 8911/5174/8910/4173 stopped. Real LOOP/provider/browser/project execution not run because current gate is read-only/blocked.

## Delegated-Agent Output Review

- The finding is traceable to the two Patient Profile lists at `MedicalMonitoringSubjectViews.jsx` lines formerly using `key={event.event_id}`.
- The repair reuses the already-reviewed display-only helper and appends the local list index; it makes no claim about server event identity.

## Residual Risk

Residual risk: if source events reorder, keys may remount display rows; this is preferable to colliding identity. Browser visual/keyboard behavior, source completeness, formal medical review, P8 authority, B6/C14, three-project LOOP and commercial readiness remain pending.
