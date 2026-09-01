You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Do not read or modify production paths.
- This is the single Codex-authorized edit round. You may edit only the six writable
  paths listed below. Do not edit the runner-owned report.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Do not start 8911, 5174, any service, provider, browser, real project, sub-agent, or
  long-lived background process. Do not read or write runtime databases or backups.
- Do not retry/reuse v5, create a v6 canary, salvage provider prose, or make any
  candidate decision.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_context.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v5_visit_canary_20260801.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`

Writable paths:
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`

Task:
Implement the complete bounded v6 offline corrective described in the task context.
Start by verifying the six baseline hashes. Preserve current style and make the
smallest coherent change.

Required implementation outcomes:

1. Evidence packet v3 and structural repair v2.
2. Stable typed list bundle identity derived from exact detected ancestor-title
   source identity. `parent_match_source_ids` remains lineage only and must never
   define list identity. Ambiguous multiple bundle membership fails closed.
3. Strict list roles: explicit item syntax only; short colon-ending titles allowed;
   term-based prose ending `。` cannot be a title; unmarked following paragraphs
   remain paragraphs.
4. Provider focus includes a selected item's stable ancestor or omits/fails closed
   on the orphan, and never adds siblings.
5. Structural/typed repair groups by stable bundle identity.
6. Required provider `fact_type`, validated against `candidate_fact_types`.
7. Deterministic visit-topic boundary and one-family atomicity gate exactly as stated
   in the context.
8. Topic-scoped source conflicts: medication-action conflicts only for study-treatment
   and concomitant-medication topics, never visit.
9. Protocol output schema omits candidate-level `system_generated_evidence` while its
   instruction remains outside the schema; other prompt identities stay unchanged.
10. Prompt v6 and legacy terminal status set v3/v4/v5.
11. Regression tests for every one of the independent review's 14 required negative
    behaviors.

Do not weaken fail-closed checks to make tests pass. Do not infer every paragraph
after a title as a list item. Do not change `main.py` or repository startup logic.

Run only:
- `.venv/bin/python -m pytest -q tests/test_monitoring_ai_source_packet.py tests/test_monitoring_ai_service.py tests/test_monitoring_protocol_preparation.py`
- `.venv/bin/python -m py_compile services/api/app/monitoring_ai_source_packet.py services/api/app/monitoring_ai_service.py services/api/app/monitoring_protocol_preparation_service.py`

If a focused test exposes a pre-existing failure unrelated to this slice, record it
without broadening scope. Stop after one implementation/proof pass and return a
compact handoff; Codex owns any follow-up and broader regression.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801`
2. `## Boundary Check`
3. `## Sources And Baseline`
4. `## Work Performed`
5. `## Files Changed`
6. `## Verification`
7. `## Failed Paths Or Uncertainty`
8. `## Codex-Owned Verification`
9. `## Recommended Next Action`

Quality gates:
- State whether the full `/Users/smkzw/.hermes/SOUL.md` was read.
- List final SHA-256 hashes for all six writable files.
- Map tests to the 14 required negative behaviors.
- Include exact focused test and compilation results.
- Do not claim final clinical, regulatory, runtime, or release acceptance.
- Do not write the runner-owned report path yourself.
