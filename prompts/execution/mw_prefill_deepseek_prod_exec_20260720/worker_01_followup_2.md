Continue the same `worker_01` session. Read `/Users/smkzw/.hermes/SOUL.md`
fully again as required by the execution runtime.

Hard boundaries:
- Work only inside the current workspace root.
- Keep the original `worker_01` source write set.
- Do not edit tests, frontend, records, runtime databases, contracts, global
  configuration or credentials.
- Do not make a production deployment or stable database write.

Read these files only:
- `context/mw_prefill_deepseek_prod_exec_20260720_execution_context.md`
- `reviews/codex_prefill_deepseek_initial_review_20260720.md`
- `reviews/codex_prefill_test_review_20260720.md`
- `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_01_remediation.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/ai_gateway.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_ai_gateway.py`

Runner-managed report path: `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_01_remediation_2.md`.

Return the complete report in final text; do not write that report directly.

Codex has not accepted the first remediation. Fix these remaining production
boundary defects without broadening the feature:

1. AI generation provenance is not source evidence. Do not create an
   `AuthoringPrefillEvidenceRef` with `source_id="ai_proposed"` or any other
   pseudo-source. Use candidate state/rationale/limitations for AI provenance.
   The condition-term candidate may cite only the original
   `framing.indication` input; its source text must be the original indication.
2. A model-returned source ID is not sufficient unless that exact ID was
   supplied in the bulk request. Add a compact `registered_source_ids` input
   contract when IDs exist. If an exact-fact candidate cites an allowed ID,
   attach that real ID as the candidate's evidence ref; otherwise quarantine
   it. Never leave an accepted exact-fact candidate with only AI provenance.
3. Expand the content gate to Chinese regulatory writing, covering at least:
   剂量/频次/给药间隔、主要或关键次要终点、AESI/特别关注不良事件、
   样本量/例受试者、洗脱期、数值阈值/上下限、筛选期/基线/第N周/
   第N天/访视时间窗. Parameterizable detection is preferred to a single
   fragile regex.
4. Public Protocol/SAP availability is a hard relevance gate, not a recorded
   bonus. Use `WritingReferencePublicDocument.document_type` values
   (`protocol`, `sap`, `protocol_sap`) as the primary structured check; filename
   is only a fallback. Exclude a trial with no qualifying public document.
5. Do not synthesize successful model identity with
   `result.setdefault("_response_model", expected)`. For the configured
   `OpenAICompatibleAiProvider`, rely on its completed strict HTTP response
   identity validation and mark the adapter result from that verified provider
   path. For generic injected providers, require an explicit exact
   `_response_model`; missing or mismatched identity must fall back.
6. Preserve the accepted F1 allowlist and F4 atomic search-plan rebuild.

Run syntax checks and the three source-owned regression files. Worker_02's test
file is expected to remain red until its separate remediation; do not edit or
weaken it.

Output schema:
1. `# Remediation Output 2: mw_prefill_deepseek_prod_exec_20260720 - worker_01`
2. `## Boundary Check`
3. `## Remaining Defects Resolved`
4. `## Files Changed`
5. `## Tests And Observations`
6. `## Remaining Risk`
7. `## Next Step`
