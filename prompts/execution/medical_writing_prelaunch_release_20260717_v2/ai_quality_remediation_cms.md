# Same-session follow-up: substantive product AI and D017 confirmation gate

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`.

## Hard boundaries

- Work only inside the current workspace (`.`).
- Use disposable runtimes only. Do not touch stable ports, stable databases,
  credentials, or original clinical documents.
- Tools remain available and must not be disabled.
- Authorized product writes are limited to directly implicated medical-writing
  AI/prompt/orchestration backend files, directly related tests, and durable
  evidence under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/`.
- Do not edit frontend source.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/ai_quality_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `context/medical_writing_prelaunch_release_20260717_v2_execution_context.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_01.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`

Continue the original worker_01 session. The product must call the configured
DeepSeek supplier `deepseek-v4-pro` directly; do not substitute Hermes or your
own prose for product-AI output.

## Objective

Close the remaining AI usefulness and second real-project journey gaps without
rerunning already proven low-value fixtures.

## Required checks

1. In a disposable runtime, create a greenfield RA project via the public API
   and complete framing, full PICOS, corpus gate, and document creation.
2. Use a medically substantive source selection of at least two paragraphs
   covering design rationale, population, endpoint timing, or statistical
   handling. Do not use a confidentiality notice.
3. Through the workbench's production AI route, test every supported intent
   retained in the UI: 改写、监管语气、查一致性、补证据. For generative intents,
   request 3-5 genuinely different candidate versions. For review intents,
   verify the returned contract matches the intended review outcome.
4. Record candidate texts only in a redacted or synthetic RA context. Evaluate
   factual preservation, protocol/regulatory Chinese, consistency with PICOS,
   traceability, material difference, and whether a senior medical writer could
   directly select/refine them. Punctuation-only variants fail.
5. Apply one candidate, save, reload, stop/restart the owned backend, reload
   again, undo or restore where the contract supports it, and prove stale
   revision rejection.
6. Complete the CMS-D017 synopsis-import journey through user confirmation,
   not only upload: multipart `expected_revision`, parsing, review/confirm,
   framing and PICOS prefill, and next-step availability.
7. Confirm the competitor workflow uses plan then execute and that the frontend
   contract can satisfy required IDs. Do not call an unexecuted stage pass.

When output quality or orchestration fails, inspect prompts and routing. Search
official or mature prompt/evaluation guidance where useful before changing
product prompts. Make only a focused product fix and add regression tests.

Write durable structured evidence with PASS/FAIL/UNVERIFIED and the direct
provider/model route. Write the final report to:

`runs/execution/medical_writing_prelaunch_release_20260717_v2/ai_quality_remediation.md`

Use the required execution-report headings.
