# Codex Review: mw-w3-r04-live-evidence

Date: 2026-07-24
Delegated-agent output: `runs/codex_mw-w3-r04-live-evidence.md`

## Verdict

PASS. W3 composite adoption is accepted at source/API/test level and may be
loaded into the stable backend for real-project validation.

## Boundary Check

- Guard route selected Codex direct execution; no delegated model was used.
- Production changes are limited to the live verifier and API resolver.
- Test-only helper changes support real catalog entries without weakening
  production contracts.

## Codex Verification

- Public API accepts a valid two-path, evidence-bound AI package.
- API rejects deleted bound snapshot, search-plan snapshot switch, package
  journey revision drift, and complete catalog entry drift even when copied
  catalog ID/hash remain unchanged.
- Complete persisted and freshly rebuilt typed catalogs must match.
- The resolver requires exact project, journey revision, package snapshot,
  search-plan snapshot, and repository snapshot identity.
- Focused: 62 passed, 4 subtests passed.
- Full W3: 389 passed, 52 subtests passed.
- Flowchart adjacent regression: 30 passed.
- Python compilation and frontend production build passed.

## Delegated-Agent Output Review

W3 r03's 384 green tests did not prove a valid live API AI adoption or complete
catalog equality. The r04 tests directly cover those missing claims. No model
report is treated as acceptance authority.

## Residual Risk

Stable runtime has not yet been restarted on this accepted source. D017 v5 and
browser W4 acceptance therefore remain pending.
