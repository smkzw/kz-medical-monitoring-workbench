# Clean-State, Backup And Reset Checklist

Status: inventory and future procedure only. This preparation pass performed
no deletion, reset, service stop, database write or runtime copy.

## Current Authoritative Runtime Surface

Default runtime root is resolved by `services/api/app/main.py` from
`WORKBENCH_RUNTIME_DIR`, otherwise:

`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime`

The repository-local
`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runtime`
is not the default product runtime and must never be accepted as runtime
inventory evidence unless a specific launched process explicitly points
`WORKBENCH_RUNTIME_DIR` there. All `runtime/...` paths below are relative to
the resolved product runtime root, not the repository root.

Observed state-bearing files/directories include:

- `runtime/user_projects.sqlite3`
- `runtime/workbench_runtime.sqlite3` plus WAL/SHM
- `runtime/medical_writing_authoring_journey.sqlite3` plus WAL/SHM
- `runtime/medical_writing_greenfield.sqlite3` plus WAL/SHM
- `runtime/medical_writing_protocol_assembly_plan.sqlite3` when created
- `runtime/medical_writing_fact_intake.sqlite3` when created
- `runtime/medical_writing_shared_corpus.sqlite3` when created
- `runtime/writing_reference.sqlite3` plus WAL/SHM
- `runtime/medical_writing_literature.sqlite3` plus WAL/SHM
- `runtime/medical_writing_synopsis_import.sqlite3`
- `runtime/medical_writing_durable_jobs.sqlite3`
- `runtime/source_content_validations.sqlite3` plus WAL/SHM
- `runtime/source_registry.jsonl`
- `runtime/source_artifacts/` when created
- `runtime/writing_reference_artifacts/` when created
- `runtime/medical_writing_synopsis_artifacts/`
- `runtime/writing_reference_translation_ai_runs.jsonl` when created
- runtime logs and PID files

Other generated/test surfaces to inventory but not treat as product source:

- `frontend/output/`
- `output/`
- `evidence/`
- `artifacts/`
- `records/runtime_backups/`
- browser download directories used by the test runner
- Word/PDF export destinations

Do not reset or delete:

- product source under `services/`, `packages/`, `frontend/src/` or `tests/`;
- `services/api/assets/medical_writing_corpus/`;
- project records, handoffs and accepted evidence;
- global provider credentials or agent sessions;
- `/Users/smkzw/.codex/tools/omlx_workload_gate.py` or its shared lease database.

## Pre-Run Read-Only Inventory

- [ ] Confirm the orchestrator has issued a run authorization after current
  release prerequisites close.
- [ ] Record source/build hashes and current API/frontend versions.
- [ ] Record active process IDs, ports and `WORKBENCH_RUNTIME_DIR`.
- [ ] Query the visible project list and record project IDs/count without
  deleting them.
- [ ] Inventory all runtime DB, WAL, SHM, JSONL and artifact paths with size,
  modification time and SHA-256 where stable.
- [ ] Record active/queued oMLX leases; do not reset the global gate.
- [ ] Inventory incomplete durable jobs and active external-agent sessions.
- [ ] Record existing browser downloads, DOCX/PDF exports and screenshots.

## Backup Procedure For Future Execution

The runtime currently contains WAL/SHM files, so copying only the base SQLite
files while the API is live is not a valid backup.

- [ ] Pause new user actions and wait for active product jobs to reach a
  resumable boundary.
- [ ] Stop the API cleanly or use SQLite's online-backup mechanism for every
  database.
- [ ] Preserve each database with its WAL/SHM state or checkpoint it before
  file copying.
- [ ] Copy the complete runtime root and generated artifact directories to a
  timestamped backup.
- [ ] Write `BACKUP_MANIFEST.json` with file hashes, service state, source
  version and restore command/steps.
- [ ] Reopen the backup read-only and verify key database tables/project counts.
- [ ] Restart the original runtime and prove its project list is unchanged
  before any reset work.

## Preferred Clean-State Strategy

Use a dedicated runtime clone per slot and perspective rather than deleting
records from the shared runtime:

`<run_root>/<tester>/<slot>/<round>/<perspective>/runtime`

- [ ] Seed it from a verified empty product baseline containing schema and
  allowed static corpus assets, but no user projects, downloads, translations,
  admitted project corpus, working copies or exports.
- [ ] Point the API at that root through `WORKBENCH_RUNTIME_DIR`.
- [ ] Run slots sequentially on the normal desktop ports unless an isolated
  frontend/API pair has been explicitly validated.
- [ ] Give each perspective a fresh browser context and download directory.
- [ ] Confirm `/api/projects` contains no project from another slot.
- [ ] Confirm source, translation, corpus, working-copy and export stores are
  empty before project creation.
- [ ] Confirm the visible project list in the real browser is empty before the
  first click, and capture that state at original desktop resolution. A clean
  API result without the matching visible empty page is insufficient.
- [ ] Record zero counts for projects, source artifacts, downloaded documents,
  document plans, translation chunks, admitted project-corpus items, framework
  drafts, section candidates, working copies, references and exports. Static
  shared corpus assets are inventoried separately and are not counted as
  project state.
- [ ] Prove the runtime clone has a unique root and the browser has a unique
  profile/download directory; neither may resolve through a symlink to another
  slot's writable state.
- [ ] Confirm shared oMLX gate has no orphan lease; do not create a private
  semaphore.

## Reset Between Failed Rounds

- [ ] Preserve the failed runtime and evidence directory; never overwrite it.
- [ ] Stop the failed round's API cleanly.
- [ ] Hash and archive the failed runtime, browser evidence and exports.
- [ ] Create the next round from the original verified empty baseline, not
  from the failed project.
- [ ] Assign new project, browser-session, job and idempotency identifiers.
- [ ] Confirm no downloaded source, extraction, translation, corpus admission,
  candidate set or working copy is reused.
- [ ] Record the defect ID and repair version that caused the rerun.

## Required `CLEAN_STATE_RECEIPT.json`

The receipt must include:

- tester, slot, round and perspective;
- baseline manifest/hash;
- runtime root and browser profile/download root;
- project count before creation;
- visible empty-project screenshot/video locator;
- state-store inventory and explicit zero counts for every project-bearing
  store listed above;
- oMLX active/queued lease counts;
- product build/API contract;
- prior-round isolation check;
- resolved runtime/browser/download paths and symlink-isolation check;
- timestamp and verifier;
- final boolean `clean_state_pass`.

No tester may create the project until `clean_state_pass` is true.
