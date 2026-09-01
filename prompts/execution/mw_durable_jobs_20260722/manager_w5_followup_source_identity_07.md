Continue the same Grok execution-manager session `23209f5d-d713-4c40-ae71-f4f1f6e98b27`. Codex independently reproduced one real-project regression and one false Source Registry identity claim after acceptance follow-up 06. Fix only these concrete defects and their tests; do not reopen the broad W5 scope.

Read these files only as the initial set; additional directly relevant in-workspace reads are allowed and must be recorded:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `prompts/execution/mw_durable_jobs_20260722/manager_w5_followup_acceptance_06.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_acceptance_06.md`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_greenfield.py`
- `services/api/app/source_intake.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_generation_context_v2.py`
- `tests/test_medical_writing_registered_sources.py`

## Hard boundaries

- Codex is final authority. Do not claim E3/E4/E5, browser, DOCX, release or launch.
- Work only in this workspace except for the explicit instruction reads.
- Write scope: `services/api/app/medical_writing.py` and directly affected tests only. Modify no frontend, durable store, clinical logic, product AI algorithm, translation, source documents, runtime data, prompts or records.
- Run with `permission-mode=bypassPermissions`.
- Write exactly one output file: `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_source_identity_07.md`. It is runner-managed; do not edit it with tools. Return the complete report in final text.

## Reproduced failures

### 1. Greenfield durable candidate generation is incorrectly blocked

Current `_source_registry_descriptor()` treats `require_registered_sources=True` as proof that a static `protocol_source_paths[project_id]` and Source Registry entry are required. That does not mirror the actual production `_run_revision_ai` branch:

- `CompositeMedicalWritingDocumentService.source_mode(project_id)` returns `greenfield_project_decision` for from-zero projects;
- that branch consumes authoritative `greenfield_state()` / working-copy selection via `submit_internal`, and intentionally does not consume original protocol Source Registry;
- the new descriptor currently fails at `protocol source path is required` before product AI, breaking the user’s primary from-zero workflow.

Make descriptor source identity mirror the actual generation branch:

- Resolve `document_service = self._effective_repo.document_service` and its authoritative `source_mode(project_id)` when available.
- For `greenfield_project_decision`, record a deterministic explicit source descriptor from `greenfield_state(project_id)` including the authoritative baseline id/revision/hash fields actually returned, plus the current generated selection/working-copy identities already present elsewhere in the descriptor. Do not require Source Registry or protocol path. Fail closed if the greenfield state identity is partial.
- For `original_protocol_docx`, resolve the actual immutable source path from `self.protocol_source_paths` **or** the document service’s `original_protocol_path(project_id)`; do not restrict dynamic imported projects to the three hard-coded IDs in `main.py`. The descriptor and `_run_revision_ai` must use the same path resolver so a newly imported real project can operate.
- For a lightweight/demo path, keep an explicit not-consumed state.
- Unknown real source modes fail closed with a precise error.

### 2. Source Registry content-validation identity is materially incomplete

`SourceContentValidationRecord` has authoritative fields `validation_id`, `revision`, `technical_status`, `content_status`, `use_status`, `file_sha256`, `expected_context_hash`, `validator_version`, checks, confirmation reason/codes and created_at. Current descriptor reads nonexistent generic `status`/`overall_status`, so every present validation becomes only `assessed`; it omits revision/id/file hash and cannot detect material validation changes. It also records only span IDs while claiming complete span/content identity.

For the registered-source branch:

- include deterministic entry identity (`entry_id`, module, kind, content hash, parser status/version, span count);
- include deterministic span identities for that entry at least `source_id`, source_type, locator and a stable preview/content hash (derive canonical SHA-256 from the authoritative stored span fields if the excluded `preview_hash` is unavailable); do not store raw full text;
- include current validation identity: validation_id, revision, technical/content/use status, file_sha256, expected_context_hash, validator_version, deterministic checks digest, confirmation/acknowledgement identity and created_at where it is part of immutable record identity;
- fail closed on partial identity when validation exists;
- include only entries/spans actually eligible/consumed for the current medical-writing source, rather than unrelated project uploads, if the existing registration path can identify them deterministically. At minimum bind the resolved original protocol path/content hash and current medical-writing registration entry/span used by `_register_revision_source`.

### 3. Behavioral tests, not path-only false proof

The current `source_path` mutation test sets `require_registered_sources=False`, so it only changes a not-consumed path string and does not prove Source Registry identity. Add tests that execute:

- a real greenfield service with `require_registered_sources=True`: canonical descriptor succeeds without static protocol path/registry, identical state is stable, baseline revision/hash mutation changes digest, partial state fails closed;
- an original/imported real service whose path is obtained from `document_service.original_protocol_path()` rather than the static map;
- a real Source Registry entry with spans and a real `SourceContentValidationRecord`: entry content/parser change, span locator/content change, validation revision/status/file/context/checks change each changes digest; partial validation identity fails closed;
- missing required original source/registry still fails before product AI.

Run focused tests and the full generation-context/registered-source/durable-revision subset. Report exact commands, counts and warnings. Return `MANAGER_W5_SOURCE_IDENTITY_COMPLETE` only if both defects and behavior tests are closed; otherwise return `MANAGER_W5_SOURCE_IDENTITY_BLOCKED` with exact recovery boundary.
