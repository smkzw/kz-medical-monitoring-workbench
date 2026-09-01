# Codex Review: mw_candidate_projection_r11

Date: 2026-07-29
Delegated-agent output: `runs/pi_mw_candidate_projection_r11.md`
Workflow runner: Codex x Hermes execution contract, Pi/Alibaba primary route.

## Verdict

PASS for source integration; live acceptance remains assigned to the fresh
`release-r12-20260729` browser round.

## Boundary Check

- Product changes are confined to
  `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`,
  `frontend/src/features/writing-reference/WritingReferencePanel.jsx`, and the
  focused regression test
  `tests/test_frontend_competitor_drawer_refresh_contract.py`.
- No backend source, frozen r11 runtime database, r11 evidence, matrix receipt,
  or release state was changed by this slice. `frontend/dist` was regenerated
  by the required production build and is not acceptance evidence.

## Codex Verification

- Re-read the drawer open-transition wiring, panel workspace refresh,
  generation/snapshot stale-response guards, and loading/loaded-empty rendering.
- `python3 -m pytest tests/test_frontend_competitor_drawer_refresh_contract.py
  tests/test_frontend_medical_writing_pipeline_waiting_contract.py
  tests/test_frontend_medical_writing_contract.py -q`: 121 passed.
- `npm run build` from `frontend/`: Vite production build passed.
- Current source hashes:
  - drawer:
    `2c7a9e2a869389f573ab694fb6b643732e705f7475902891f47bf3750a9b010f`
  - panel:
    `51b68772193c824d7cbb00a2f6bd350c4f9bfb1fc79f5b0c28489c4672641303`
  - focused test:
    `80e694593e9bf42035f27c2b475454596c97fa9ca514b43764fe889c91d9c533`

## Delegated-Agent Output Review

The root-cause claim is consistent with the frozen r11 API log: reopening the
drawer recovered the authoring journey and triage state but did not request the
workspace, while the immutable snapshot retained 665 candidates. The repair
adds the missing closed-to-open refresh signal without changing triage or
admission semantics. The added loaded-empty distinction prevents unresolved
state from being reported as a real zero-candidate result.

## Residual Risk

- Source-level acceptance does not prove the real browser issues a fresh
  workspace request or renders the 665-candidate snapshot. That is a mandatory
  r12 E2E recheck, not a reason to mutate or reuse r11.
- The separate document-admission result (59 not admitted and 3 extraction
  failures in r11) remains unresolved by design.
- The existing bundle-size warning remains non-blocking and unrelated to this
  lifecycle defect.
