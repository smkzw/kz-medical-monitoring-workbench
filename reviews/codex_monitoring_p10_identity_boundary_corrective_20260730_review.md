# Codex Review: monitoring_p10_identity_boundary_corrective_20260730

Date: 2026-07-31
Recovered execution session: `session_9756de42-2675-4916-909e-30e700505c69`

## Verdict

Pass for the four scoped corrective boundaries. Keep port 8911 stopped; this
review does not authorize runtime restart or real-project execution.

## Boundary Check

- The original parent JSONL was unavailable; this is evidence-based continuation,
  not restoration of the original turn-by-turn conversation.
- The interrupted Kimi session was resumed in place. Its pre-recovery history
  contained read/grep/test/todo operations and no unreported source write.
- Corrective source changes were limited to the eight monitoring/shared files
  named below. Existing unrelated medical-writing changes in `main.py` and the
  workspace were preserved.
- No `runs/hermes_monitoring_p10_identity_boundary_corrective_20260730.md` was
  fabricated. The recovered Kimi session and this Codex review are the execution
  evidence.
- No service was started and no runtime database was written. A read-only check
  observed `runtime/monitoring_protocol_rules.sqlite3` as a zero-byte file.

## Codex Verification

Accepted behavior:

1. Provider-assigned IP role/object identity and self-cited fields no longer
   self-anchor investigational-product identity. Prior/background/rescue/
   concomitant and non-study treatment context is neutralized unless an
   independent frozen-profile binding or medically confirmed domain-family hint
   exists.
2. Published project-effective identity aggregation fails closed for every empty
   or mixed member of the complete four-field identity.
3. Candidate confirmation, pack transitions, automatic/manual shadow paths and
   frozen-batch checks require one uniform non-empty four-tuple, including
   `effective_capabilities_sha256`.
4. Project-effective first execution re-resolves the published pack and compares
   pack revision plus all four identity fields with the frozen batch contract.
   Existing deterministic snapshot replay intentionally remains valid.
5. The legacy fact-confirm/compile path rejects missing immutable identity with
   HTTP 409 semantics.

Codex found and repaired two gaps left by the delegated implementation:

- first-execution validation initially checked the four current fields only for
  non-emptiness; it now compares each field with the frozen batch contract;
- shadow frozen-batch validation initially omitted `mapping_revision` from the
  contract comparison; it is now included.

Verification evidence:

- `test_monitoring_daily_run_service.py`: 20 passed.
- `test_monitoring_shadow_sample_service.py`: 36 passed.
- Adjacent medical-writing import/contract selection: 312 passed.
- Full `pytest tests/ -q -k monitoring`: 1119 passed and three legacy fixture
  failures. All three failures were caused by old test fixtures attempting to
  confirm identity-less candidate rules, which the new contract correctly
  rejects.
- After giving those fixtures deterministic complete identities, the exact three
  failed cases passed (3 passed). No product logic was relaxed.

## Changed Corrective Surfaces

Source:

- `monitoring_ai_service.py`
- `monitoring_mapping_semantic_quality.py`
- `main.py` (monitoring runtime identity locator only)
- `monitoring_protocol_rule_repository.py`
- `monitoring_shadow_sample_service.py`
- `monitoring_daily_run_service.py`
- `monitoring_rule_authoring_service.py`
- `monitoring_rule_templates.py`

Tests were updated only to cover the four boundaries and to align legacy
real-source fixtures with the new complete-identity confirmation contract.

## Residual Risk

- The final evidence is a complete full-suite pass set plus a targeted rerun of
  its only three failures, not a second eight-minute monolithic rerun after
  fixture-only changes.
- Port 8911 remains deliberately stopped. Browser/runtime acceptance and real
  project execution are outside this corrective checkpoint and remain
  unauthorized.
