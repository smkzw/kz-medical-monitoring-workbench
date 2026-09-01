Continue the same `worker_02` session. Read `/Users/smkzw/.hermes/SOUL.md`
fully again as required by the execution runtime.

Hard boundaries:
- Work only inside the current workspace root.
- Edit only the original `worker_02` test write set.
- Do not edit production source, frontend, records, runtime databases, global
  configuration or credentials.
- Do not make a production deployment or stable database write.

Read these files only:
- `context/mw_prefill_deepseek_prod_exec_20260720_execution_context.md`
- `reviews/codex_prefill_test_review_20260720.md`
- `reviews/codex_prefill_deepseek_initial_review_20260720.md`
- `reviews/codex_prefill_source_acceptance_20260720.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_ai_gateway.py`

Runner-managed report path: `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_02_remediation.md`.

Return the complete report in final text; do not write that report directly.

Your first test pass returned green but Codex rejected it because several tests
proved only object shape or even endorsed invalid evidence. Perform a targeted
test remediation against the accepted worker_01 source:

1. Replace the unknown-source tests so fabricated/unregistered IDs are
   rejected or stripped. Never treat `ai_bulk_prefill` as registered source
   evidence. Prove generated text is not its own evidence.
2. Parameterize exact-fact leakage through eligible free-text fields. Cover at
   least dose/regimen, visit timing, washout, endpoint, threshold, sample size
   and AESI. Prove unsupported facts are rejected/quarantined. If supported
   facts are accepted, prove their source IDs are in the supplied allowlist.
3. Prove the production bulk adapter makes exactly one provider call for the
   whole package. Do not substitute the deterministic per-field ranking
   adapter for this assertion.
4. Instrument the actual SQLite boundary and prove production AI enrichment
   completes before `BEGIN IMMEDIATE`.
5. Prove adopting the English ClinicalTrials.gov condition candidate creates
   a new versioned search plan, updates
   `registry_filter.condition_term`, and clears stale snapshot binding.
6. Build mixed RA and PNH snapshots. Prove request hints exclude wrong
   condition, phase, study type and records without public Protocol/SAP.
7. Remove or rewrite any vacuous assertion that only checks a constant is a
   string, a field exists, or an evidence list is non-empty when the stated
   test name promises a stronger safety property.

Run the focused four-file regression and Ruff on the edited test set. Report
the exact passing/skipped/failing counts and any source defect exposed by the
stronger tests. Do not weaken production behavior to obtain green tests.

Output schema:
1. `# Remediation Output: mw_prefill_deepseek_prod_exec_20260720 - worker_02`
2. `## Boundary Check`
3. `## Rejected Assertions Replaced`
4. `## Files Changed`
5. `## Tests And Observations`
6. `## Remaining Risk`
7. `## Next Step`
