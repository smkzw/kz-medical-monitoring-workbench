# G6 Worker 01 Same-Session Follow-up — Freeze The Unified Release Identity

Continue the same `worker_01` execution session. Do not start a new session, service, browser, model, or network call.

## Hard boundaries

- Work only inside the current workbench and only on the allowed files below.
- Do not read or write any real project, medical-writing file, credential, external account, or path outside this workbench.
- Do not start services, browsers, models, network calls, or subprocess Agents.
- Do not claim final G6 or visual acceptance.

## Read these files only

- `context/mm_r8_gate6_synthetic_ego_implementation_20260831_execution_context.md`
- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_identity_followup.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_03_identity_followup.md`
- current files under `deploy/medical_monitoring_local/`
- current `frontend/dist/`
- `tests/test_medical_monitoring_g6_entry_lifecycle.py`
- `tests/test_medical_monitoring_g6_synthetic_bundle_endpoint.py`

## Observed blocker

The implementation now has one canonical Python audience bundle and one frontend endpoint consumer, but the frozen release identity is stale. `execution_boundary_manifest.json` still names the old binding, `entry_manifest.json` has old release-file hashes, and the built frontend exists only at workbench `frontend/dist` while the actual app resolves `frontend/dist` under its deployment release root.

## Assigned repair

1. Package the already-built production frontend into the actual release root at `deploy/medical_monitoring_local/frontend/dist` without editing the source build. The app must open this packaged copy, not a path outside its release root.
2. Freeze `execution_boundary_manifest.json` to the canonical synthetic profile identity from Python:
   - profile `synthetic-profile-cross-domain-g6-v1`
   - profile binding `sha256:1a8d65615d43535891b32948585a5d347caf8dfcb2b22fed68ab95a88896d956`
   - fixture digest `sha256:5cc67a088c3b43b430e2ab3433184ac2b68fa8323f24bf7d7c6d9c962b5be053` where the schema permits it.
   Do not substitute the selected run binding `sha256:1fbb3d...` for the profile binding.
3. Refresh `entry_manifest.json` deterministically after all release files are final. Its release inventory must close the actual-app runtime dependency set, including at minimum the app bundle, `actual_app.py`, `g6_manifests.py`, `canonical_evidence.py`, `synthetic_ego.py`, and every packaged frontend dist file. Do not leave an imported file outside the frozen inventory.
4. Refresh the app bundle directory/file digest, release digest, and all three manifest self-digests. Preserve the accepted viewport layout numbers unless a digest-only refresh is required.
5. Update `release_sources.json` so distribution includes the packaged frontend and all G6 runtime files, with no real project, cache, log, database, node_modules, or medical-writing content.
6. Add or strengthen focused tests proving:
   - packaged static root exists and is release-contained;
   - every runtime import/static file is frozen in entry release files;
   - boundary binding equals Python canonical profile binding;
   - endpoint bundle, boundary manifest, frontend identity constants, and release manifest agree;
   - no stale 58-event or old binding identity remains in runtime/release surfaces.
7. Run actual-app self-check and focused G6 tests without starting a listener.

## Allowed files

- current files under `deploy/medical_monitoring_local/`
- focused G6 lifecycle/manifest tests under `tests/`
- runner-managed worker report only

## Verification

Return exact manifest/release/app/static digests, canonical identity checks, test counts, changed/generated files, residual risks, and the remaining browser/notification acceptance gap. Do not claim visual acceptance.

## Output

Return one compact handoff to the runner-managed output file `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_01_manifest_followup.md`. Do not write that report path directly through file tools.
