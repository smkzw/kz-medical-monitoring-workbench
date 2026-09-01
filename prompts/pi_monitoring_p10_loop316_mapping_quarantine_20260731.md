You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Do not read or modify production paths.
- This is an authorized bounded edit round. Edit only the four writable paths listed
  in the task context. Preserve unrelated changes.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_loop316_mapping_quarantine_20260731.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_loop316_mapping_quarantine_20260731_context.md`
- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.json`
- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.md`
- `services/api/app/monitoring_mapping_draft_repository.py`
- `services/api/app/monitoring_mapping_semantic_quality.py`
- `scripts/monitoring_mapping_candidate_audit.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_candidate_audit.py`

Task:
Implement and test the smallest project-neutral fail-closed correction for the two RUX
V16 candidate-audit error families described in the task context.

Required invariants:
- Preserve immutable AI candidates and all source/evidence identity.
- Multi-action IP roles must not be resolved to a preferred action. Quarantine the
  assembled field to a closed generic source-value role and explicitly block action-
  specific use.
- Incomplete standardized coding claims must be downgraded to source-collected after
  whole-source-set MedDRA anchoring; never invent coding system/version/lineage.
- Existing complete MedDRA chains must remain standardized.
- Candidate-audit severity may become warning only for shapes guaranteed to be
  quarantined by draft assembly; uncovered unsafe shapes must remain errors.
- Use no RUX-specific field-name logic.
- Do not run the full suite, start services, inspect runtime SQLite, call providers,
  retry jobs, assemble a real draft, or modify any candidate state.

Output schema:
1. `# Hermes Execution Handoff: monitoring_p10_loop316_mapping_quarantine_20260731`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Work Performed`
5. `## Files Changed`
6. `## Focused Verification`
7. `## Observations And Failed Paths`
8. `## Residual Risk`
9. `## Codex-Owned Verification`
10. `## Next Recommended Action`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Include exact test commands and counts.
- Do not claim the real RUX audit is clean; Codex must regenerate it after review and
  after the two missing jobs are resolved.
