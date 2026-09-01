# Codex Review: mw_protocol_p0_phase0b_postcorrective_acceptance_20260801

Date: 2026-08-01 23:15 CST  
Review mode: Codex final acceptance of current files/runtime; independent Hermes/main-venue review gate required for the next material transition.

## Verdict

`READY_FOR_ISOLATED_PREFILL_RUNTIME_REVIEW; NOT_READY_FOR_FORMAL_FRAMING_OR_UPSTREAM_RESEARCH`

## Acceptance Findings

## Verification

The current filesystem, focused tests, SQLite integrity, API readiness, frontend build manifest, and real Computer Use UI state were independently rechecked in the isolated clone. This review is evidence-based and does not rely on worker or manager confidence.

- Durable reservation and unknown-outcome protections are present in the current source and covered by 17 dedicated reservation tests plus the complete 625-test focused suite.
- The single-candidate route fails closed for pending/manual-only/insufficient/unsupported-substantive candidates; the frontend disables those actions and explains the composite/manual decision route.
- API restart and browser reload recovered the same target project, fact conversation, reviewer provenance and high-impact gaps. The clone remained at journey revision 8 with 3944 journey events, 1 reservation, 1 fact conversation, 4 fact events and 5 durable jobs.
- Rebuilding the frontend removed the previously observed stale runtime-contract warning. Both `runtime-build.json` and `/api/runtime-readiness` agree on `api-29ac0d262dd16d6d` and contract `medical-writing-api-2026-07-17.1`.
- The read-only impact preview correctly returned `requires_confirmation=true` and affected dependents while leaving all authoring/pipeline counters unchanged.

## Boundary And Residual Risk

- Formal framing remains incomplete and the `完成第一步`/impact-confirmation path was intentionally not clicked.
- The current corpus gate is still waiting for corpus admission; no public research, triage, download, OCR, translation or document generation was started.
- The later serial multi-model end-to-end/full-button acceptance requested by the user remains a subsequent release gate; this record does not claim it.
- The production test environment still has Python dependency-parity caveats noted in the Phase 0B review; current focused tests used the bundled Workbench `.venv`.

## Evidence Locators

- `runs/runtime_phase0b_postcorrective_20260801/evidence/ui_post_restart_rebuilt_frontend.txt`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/ui_post_restart_rebuilt_frontend.jpeg`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/impact_preview_readonly_after_restart.json`
- `runs/runtime_phase0b_postcorrective_20260801/medical_writing_authoring_journey.sqlite3`
- `runs/runtime_phase0b_postcorrective_20260801/medical_writing_fact_intake.sqlite3`
- `frontend/dist/runtime-build.json`

## Codex Decision

Accept the bounded corrective runtime proof for continuation inside Protocol P0. Keep the Goal active; the next transition must remain reviewer-visible and separately bounded. Do not treat this as final medical-writing release acceptance.

## Post-Fix Recheck — 2026-08-01 23:32–23:36 CST

The historical review above is superseded for current evidence by the independent challenge findings. Codex rechecked the fixes in the current filesystem:

- P1 build-contract drift is closed for this snapshot: `/api/runtime-readiness` and the served `runtime-build.json` both report `api-b1908b240f885d8a`; contract version remains `medical-writing-api-2026-07-17.1`.
- P2 force-supersede TOCTOU is closed at the persistence boundary: the read/re-key transaction is `BEGIN IMMEDIATE`, terminal status is checked, and the update requires a null-safe event-id/status CAS. The new completed-owner regression passes.
- P3 edit-state leak is closed in the current frontend source: both edit-confirmation paths use the current candidate's pending-like classification in their disabled condition.
- No new P0/P1/P2/P3 regression appeared in `626` backend focused tests, `18` reservation tests, `11` frontend candidate-panel tests, or the production build.

Evidence locators:

- `runs/runtime_phase0b_postcorrective_20260801/evidence/runtime_contract_post_blocker_fix.json`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/runtime_readiness_post_blocker_fix.json`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/runtime_build_post_blocker_fix.json`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/ui_post_blocker_fix_rebuilt_frontend.txt`
- `runs/runtime_phase0b_postcorrective_20260801/evidence/ui_post_blocker_fix_rebuilt_frontend.jpeg`
- `runs/runtime_phase0b_postcorrective_20260801/medical_writing_authoring_journey.sqlite3`

At the time this section was written, independent post-fix reviewer follow-up was still pending. The completed independent verdict is recorded below; the conservative pre-review verdict in this historical section is superseded by that final bounded verdict.

`READY_FOR_POST_FIX_INDEPENDENT_REVIEW; NOT_READY_FOR_FORMAL_FRAMING_OR_UPSTREAM_RESEARCH`

The formal framing/corpus gates, all upstream research/OCR/translation routes, and the later serial multi-model/full-button release gate remain unaccepted.

## Independent Post-Fix Verdict — 2026-08-01 23:40 CST

The same-session independent reviewer returned `READY` for the bounded post-fix isolated prefill/runtime slice. It independently confirmed closure of the prior P1/P2/P3 findings and found no new P0–P3 issue. The reviewer retained one P4 evidence caveat: no separate raw pytest/build/API request logs were saved for this recheck, and the dynamic stale-editor transition was not browser-exercised. The latter remains protected by the live frontend gate plus the backend fail-closed check.

Codex final bounded verdict:

`READY_FOR_POST_FIX_ISOLATED_PREFILL_RUNTIME; NOT_READY_FOR_FORMAL_FRAMING_OR_UPSTREAM_RESEARCH`

This is not release acceptance. Keep Goal active and keep `完成第一步`, impact confirmation, corpus admission, public research, OCR/translation, document generation, Synopsis/CSR and serial multi-model/full-button release testing outside this slice.
