You are continuing the same Pi session for one Codex-requested corrective pass.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. State honestly
whether you read it in full.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Continue the same task and edit only the six previously authorized writable files.
- Runner-managed output path:
  `runs/pi_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_followup1.md`.
  Do not write this report directly; return the delta report in your final response.
- Do not start 8911, 5174, services, providers, browsers, real projects, sub-agents,
  or long-lived processes. Do not read or write runtime DBs/backups.
- Do not retry v5, create a v6 canary, salvage prose, or decide candidates.

Read these files only:
- `context/monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_context.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_protocol_preparation.py`

Codex found two acceptance gaps in the initial pass. Fix only these gaps:

1. Provider-focus orphan fail-closed behavior
   - The requirement is: a selected list item must retain its exact stable ancestor,
     otherwise the orphan item must be omitted from the provider-facing focused
     packet (or the focus operation must fail closed).
   - Current `test_v3_focus_keeps_stable_ancestor_and_orphan_gets_no_ancestor`
     incorrectly asserts that the bundle-less orphan remains focused. Change the
     implementation and tests so a primary `list_item` lacking a stable bundle, or
     lacking exactly one typed ancestor title in that bundle, is not retained in the
     provider-focused packet.
   - Keep valid primary items plus their unique ancestor. Do not add siblings.
   - Keep frozen source packet lineage unchanged; this correction is only the
     provider-facing focus behavior and its proof.

2. Exact topic/object conflict pairing
   - `study_treatment` may receive only `investigational_product` medication-action
     conflicts.
   - `concomitant_medication_policy` may receive only
     `concomitant_non_investigational` medication-action conflicts.
   - All other topics receive no medication-action conflicts.
   - Add negative tests proving a CM conflict is absent from a study-treatment job and
     an IP conflict is absent from a concomitant-medication job, while each matching
     topic/object pair remains detected with the exact evidence set.

Run only:
- `.venv/bin/python -m pytest -q tests/test_monitoring_ai_source_packet.py tests/test_monitoring_ai_service.py tests/test_monitoring_protocol_preparation.py`
- `.venv/bin/python -m py_compile services/api/app/monitoring_ai_source_packet.py services/api/app/monitoring_ai_service.py services/api/app/monitoring_protocol_preparation_service.py`

Return a compact delta report with changed files, exact tests, final hashes,
uncertainty, and Codex-owned verification. Do not broaden or claim final acceptance.
