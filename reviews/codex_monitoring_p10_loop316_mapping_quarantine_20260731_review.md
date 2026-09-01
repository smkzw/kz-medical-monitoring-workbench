# Codex Review: monitoring_p10_loop316_mapping_quarantine_20260731

Date: 2026-07-31 CST
Delegated-agent output: `runs/pi_monitoring_p10_loop316_mapping_quarantine_20260731.md`

## Verdict

**Pass after bounded Codex audit refinement.**

The execution route implemented the required fail-closed draft transformations:
multi-action IP roles become a generic source-value role and incomplete standardized
coding claims are downgraded after whole-source-set verification. Immutable candidates
remain unchanged. Codex then corrected one remaining audit overreach: an implicit
same-domain/system `default` bucket is not an explicitly declared coding chain, so
different hierarchy levels may have different evidence strength. Partial
standardization now remains visible as a formal capability restriction; explicit
version/system or named-chain drift remains an error.

## Boundary Check

- Route: `Pi/deepseek/deepseek-v4-flash max`, one session, one round, no fallback.
- The delegated edits were confined to the four authorized source/test paths.
- The role did not inspect runtime SQLite, call the provider, start services, retry
  jobs, assemble a real draft or change candidate state.
- Codex's follow-up changed only the audit script and its test; no runtime candidate,
  mapping draft, confirmation or activation was written.

## Codex Verification

- Final focused/adjacent tests:
  `165 passed` across candidate audit, draft repository, semantic quality and AI API.
- Final full medical-monitoring regression:
  `1152 passed, 4299 deselected, 27 warnings, 0 failed`.
- RUX V16 controlled retry affected only the two original terminal jobs
  (`MHT:0004-of-0005`, `RAND:0001-of-0004`); both retained job identity and completed
  at attempt 2. Batch is now `175/175 completed`.
- Final read-only RUX candidate audit covers 175 jobs / 1,805 fields:
  `0 errors / 73 warnings / 8 observations`.
- Real 1,805-field in-memory projection through the current deterministic functions:
  - `DABMECO` and `DABMECO_UNIT` become `clinical.source_other`,
    `source_collected`, action `multi_action_ip_quarantined`;
  - semantic quality is `pass_with_warnings / activate_restricted`;
  - global blockers: 0;
  - `ip_exposure_adherence` and `standard_coding_rules` are
    `blocked_by_quality`.
- No real draft was assembled because the product endpoint requires accepting all
  175 proposed candidates first; that user decision was deliberately not simulated.

## Delegated-Agent Output Review

The handoff was traceable, reproduced the intended failure modes and correctly
preserved candidate immutability. Its remaining real-RUX chain-drift error exposed a
candidate-audit modeling issue rather than an assembly defect: the audit grouped all
MedDRA levels without an explicit `coding_chain_id`. Codex refined this boundary and
added a negative test proving explicit version drift remains an error.

## Hermes Execution Review

The Hermes runner report is accepted as bounded implementation evidence only. Codex
independently reviewed the current source, reran tests, regenerated the real RUX audit,
performed the real-candidate in-memory projection, and retained final acceptance
authority.

## Residual Risk

- All 175 mapping candidates remain `proposed`; no medical-manager decision exists.
- The mapping is eligible only for restricted activation after future explicit
  adoption/confirmation. Current capability blockers must not be hidden or converted
  to absence conclusions.
- Candidate warnings include unresolved IP action/accountability roles, incomplete
  coding/date/lab/scale lineage and must remain visible in the future draft UI.
- Protocol preparation remains a separate release blocker: 2 topics have proposed
  candidates and 6 failed structure gates.

Final SHA-256:

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_mapping_draft_repository.py` | `37dbb5f4a1ddc0dd18746f2416aff20560651d42332260c9d921e4f9dc544139` |
| `scripts/monitoring_mapping_candidate_audit.py` | `9daf008477dd3d31f4013c776e444000aa55be2bdcb6b2baa777c802680859b0` |
| `tests/test_monitoring_mapping_draft_repository.py` | `628d02c765459389d8d2e919e6da014d088ebb3f2eee9e188926daa317dcbbc7` |
| `tests/test_monitoring_mapping_candidate_audit.py` | `f8fcdaabf6b7d6d8be1ecef04d3a0b3b0dd54d6b9812bafeb333da0363274d78` |
