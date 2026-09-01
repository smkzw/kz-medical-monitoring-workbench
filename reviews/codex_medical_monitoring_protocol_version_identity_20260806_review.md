# Codex Review: medical_monitoring_protocol_version_identity_20260806

Date: 2026-08-06 (Asia/Shanghai)
Route: direct Codex; no delegated-agent output

## Verdict

PASS for this offline protocol-version display/selection guard; not a release, source-authority, browser, or clinical acceptance.

## Boundary Check

- Work stayed in feature-owned protocol-preparation model/view/test/static-contract files.
- Shared `App.jsx`, `styles.css`, `main.jsx`, backend/API, runtime, provider, browser, real-project, B6/C14/P8, Safety/PV and medical-writing paths were not changed.
- The Hermes real-loop gate remains `read_only / blocked`; 8911/5174/8910/4173 remain stopped.
- No protocol version was renamed, deduplicated, approved, parsed, or sent through a new API path.

## Codex Verification

- `confirmedProtocolVersions` retains confirmed rows, counts `protocol_version_id` identities and adds display-only source index/state/issue/key metadata; sorting remains date/label based with source-index tie-break.
- The version selector uses the display key. Missing/duplicate rows are labelled “身份待核对” and disabled; automatic current/fallback selection only chooses a ready version. Unique versions preserve the existing status/polling path.
- `node --test frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs`: **32 assertions passed**.
- `python3 -m pytest tests/test_frontend_monitoring_contract.py tests/test_frontend_timeline_contract.py -q`: **90 passed**.
- `node --test $(find frontend/src -name '*.test.mjs' -print | sort)`: **44/44 subtests passed**.
- `npm run build` from `frontend/`: **1,956 modules transformed; build passed**; existing >500 kB chunk advisory remains.
- Protected hashes unchanged: App `de942af37999e708d124c99e1beb47fcd2c405ff23ed83fee6dbcc4cf5e0beed`, styles `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd`, main `869dbab992b086a2c38ae8ab1d44ca9b7d0014ef4614b85a5154bc3fcebc8f05`.
- Ports 8911, 5174, 8910 and 4173 are stopped.

## Independent Review Boundary

No external reviewer/provider was dispatched because the gate forbids provider/runtime activation and this is a bounded, deterministic, feature-owned offline patch. The Hermes workflow guard is the process record; Codex performed final source/test acceptance.

## Residual Risk

The guard prevents client-side version-list key/selection ambiguity only. It does not prove server protocol identity, version-content/source completeness, status-response binding, browser visual/keyboard behavior, clinical/scientific quality, independent-AI generalization, P8 authority, B6/C14, the three-project LOOP, or commercial readiness. The next safe action remains offline auditing; gate release still requires the five formal reviewer outcomes plus source-token/CAS revalidation.
