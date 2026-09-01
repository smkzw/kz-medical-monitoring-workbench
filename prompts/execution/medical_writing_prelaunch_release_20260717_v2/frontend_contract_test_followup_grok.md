# Same-session follow-up: repair stale frontend contract test

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`, the latest
`/Users/smkzw/.codex/AGENTS.md`, and applicable workspace/frontend AGENTS
files. Continue Grok Build session
`e8f7f967-4b82-46bc-a048-157bdf4ea655`.

## Hard boundaries

- Work only inside the current workspace.
- Do not touch stable ports/databases, credentials, backend source, clinical
  files, or unrelated frontend behavior.
- Codex owns final acceptance.
- Authorized writes are limited to
  `tests/test_frontend_medical_writing_contract.py`, and only if source review
  confirms the failure is a stale implementation-string assertion.
- Do not weaken behavior requirements to make the test green.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`

## Exact failure

Codex ran:

`python3 -m pytest -q tests/test_frontend_medical_writing_contract.py tests/test_medical_writing_working_copy_persistence.py tests/test_medical_writing_revision_application.py`

Result: `1 failed, 120 passed`.

Failure:

`FrontendMedicalWritingContractTests.test_document_blocks_and_tables_share_one_tiptap_editing_flow`

It asserts that `App.jsx` contains the removed implementation string:

`const trailingNodes = rawEditorNodes.slice(currentBlocks.length)`

The current implementation intentionally loops over trailing top-level nodes
and strips only effectively empty extras, while preserving the imported
source-block count contract and folding greenfield non-empty Enter paragraphs.

## Required action

1. Inspect the complete test and current `onUpdate` mapping. Confirm this is a
   stale white-box assertion, not a missing behavior.
2. Replace only the stale assertions with durable contract assertions for:
   - raw editor nodes are mapped against current source blocks;
   - only extra effectively empty trailing nodes are discarded;
   - imported non-empty top-level growth remains rejected;
   - greenfield non-empty Enter nodes are folded into stable multi-paragraph
     rich text without new random block IDs;
   - table blocks stay in the same TipTap editing flow.
3. Run the exact failing test, then the full three-file command above.
4. Append the exact change and results to the existing frontend report. Do not
   overwrite prior evidence with a shorter report.

Stop and report if the current product implementation fails any of those
behavioral contracts.
