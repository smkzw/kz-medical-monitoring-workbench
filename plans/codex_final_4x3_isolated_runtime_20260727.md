# Final 4x3 Isolated Runtime Plan

Status: implementation pending  
Authoritative live runtime:
`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime`

## Goal

Run every final tester perspective from a fresh writable runtime without
deleting or reusing the shared product runtime. The isolated runtime may inherit
system-level provider configuration, but it must contain no project state,
downloaded source, translation, project corpus, writing draft or export.

## Baseline Inputs

Copy only these system-level files from the verified live runtime:

- `ai_provider_settings.json`
- `ai_provider_secrets.json`
- `ai_provider_master.key`
- `ai_role_bindings.json`

The files remain local, mode `0600`, and are never embedded in evidence or
external-agent prompts. Record only path class, byte count and SHA-256.

Do not copy any SQLite, WAL, SHM, JSONL, source artifact, writing-reference
artifact, synopsis artifact, output, download, screenshot or export.

## Per-Run Creation

1. Create a new non-symlink runtime under the perspective evidence directory.
2. Copy the four system-level AI files and verify hashes and modes.
3. Start the product with:
   - `WORKBENCH_RUNTIME_DIR=<isolated runtime>`
   - `WORKBENCH_INCLUDE_REFERENCE_PROJECTS=false`
   - the normal stable AI environment and shared oMLX workload gate.
4. Let product startup create its schemas. Never seed a user project.
5. Verify the process environment resolves to the exact runtime.
6. Verify `GET /api/projects` is an empty JSON array.
7. Verify AI role status reports independent AI, OCR, body translation and
   translation support ready. The body model must be the gate-owned Hy-MT2
   identity.
8. Verify all project-bearing stores contain zero project rows and no project
   artifact directory has content.
9. Open the real desktop UI and prove the project selector has no project
   entries before clicking `新建项目`.
10. Write `CLEAN_STATE_RECEIPT.json`; project creation remains blocked until
    `clean_state_pass=true`.

## Failed-Round Isolation

- Stop the failed run cleanly.
- Preserve and hash its complete runtime, downloads, screenshots and exports.
- Never reset or reuse it.
- Create the next round from a new directory and recopy only the four
  system-level AI files.
- Use new browser profile, project ID, idempotency keys and download root.

## Release Boundary

The shared live runtime is read-only during final matrix runs. The four existing
user projects and their 4,217 matching rows are not deleted by this strategy.
After all release gates pass, production launch may point to a separately
verified clean runtime; switching the persistent production runtime is a later
explicit deployment action, not part of test preparation.

