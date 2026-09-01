# Codex Review: monitoring_protocol_evidence_packet_v2

Date: 2026-07-30
Run record: `runs/monitoring_protocol_evidence_packet_v2_20260730.md`.
Delegated-agent output was not used; implementation and acceptance were
performed directly by Codex in an isolated workspace.

## Verdict

Pass for the requested backend/test slice. Not a runtime release approval.

## Boundary Check

- Product changes are limited to three monitoring backend modules, one existing
  backend binding in `main.py`, and three monitoring tests.
- No frontend, medical-writing, runtime configuration, runtime database or real
  candidate decision was changed.
- Seven accidental root-level copies created during mechanical promotion were
  detected and removed before acceptance.

## Codex Verification

- Real RUX source re-parsed read-only: 2,005 spans.
- Study-treatment query: 50 direct hits, 200 bounded expanded spans.
- One same-condition required/optional stop conflict detected.
- Required and optional source locators were both present.
- Three table-4 row-2 cells were bound together.
- Focused isolated tests: 153 passed.
- Adjacent isolated tests: 237 passed.
- Adjacent main-workspace tests: 239 passed.
- Ruff and F821 checks passed.
- Python compilation passed.
- Promoted target files were byte-identical to isolated accepted files.

## Delegated-Agent Output Review

No delegated output was used. The initial workflow route selected by the guard
was ineligible during the 00:00-08:30 aishuo exclusion window and was not
dispatched through Hermes. Codex reviewed only deterministic implementation
evidence and the authorized real-source probe.

## Residual Risk

- Existing v1 candidates remain scientifically invalid until regenerated under
  the v2 packet and re-audited.
- Section/list detection is heuristic because persisted spans do not yet carry
  complete Word style hierarchy.
- Complex merged/multirow tables require further real-project validation.
- MG-K10 and MY009 cross-project v2 candidate audits remain pending.
- Runtime cutover/restart was deliberately outside this slice.
