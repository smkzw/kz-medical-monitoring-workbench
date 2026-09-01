# Codex Review: medical_monitoring_ai_native_r1_poc_20260809

Date: 2026-08-09
Reviewed scope: `poc/medical_monitoring_ai_native_r1/`

## Verdict

**PASS — isolated synthetic R1 slice1 only.** This proves the first framework-neutral
domain/persistence/AE-MH vertical slice and its failure gates. It does not complete R1,
does not migrate the product, and is not evidence of UI, real-project, clinical,
regulatory, provider or commercial readiness.

## Boundary Check

- All implementation files are inside `poc/medical_monitoring_ai_native_r1/`; task
  records are confined to the declared `context/`, `plans/`, `prompts/`, `runs/`,
  `logs/`, `metrics/` and `reviews/` surfaces.
- No source/reference string for the five real projects, their local paths, 8911 or
  5174 exists in the POC. No network/provider/process-launch dependency exists in its
  source, scripts or tests.
- The workbench is not a Git repository, so isolation and explicit path inspection—not
  Git status—are the boundary evidence. Medical-writing/product paths were not read or
  modified during implementation or acceptance.

## Codex Verification

### Deterministic checks

- `.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests`
  → `103 passed in 0.62s`.
- Added final authority negatives for forged proof, Store rejection, competing export
  path, cross-project eligible snapshot reuse and same-project snapshot-version mismatch.
- Full POC scan found no real-project path/name or 8911/5174 reference and no Python
  provider/network/process module usage.

### Fresh demo/runtime evidence

- Fresh caller-owned temp directory produced `SYNTHETIC_R1_DEMO_OK` and
  `RUN_OUTPUT_STATE=draft_exportable`.
- SQLite: one Run with orthogonal states `complete/complete/not_required/draft_exportable`,
  manifest revision 1; both snapshots `baseline_eligible`; 3 canonical facts; 28 domain
  objects; 2 authoritative complete artifacts; 58 audit events.
- Progress is manifest-derived `completed=3,total=3,passed=3`; audit chain verified;
  recovery found zero incomplete runs, integrity violations or orphan artifacts.
- Every artifact file SHA-256 equals its content-addressed filename; both authoritative
  artifact IDs match those files.
- Candidate/fact separation is explicit: 3 reported AE/MH facts and 1 remaining
  under-reporting candidate; the candidate is not counted as reported. Profile and
  Timeline use the same subject temporal-spine id and expose evidence links and the
  three-part Query draft.
- Demo boundary flags: `service_started=false`, `provider_called=false`,
  `real_project_data=false`.

## Delegated-Agent Output Review

The tracked execution used Pi, Codex Luna CLI compatibility and Cursor manager routes;
Hermes was not used as an execution or acceptance venue for this slice.

- Worker_04 correctly exposed three authority defects rather than masking them. The first
  manager pass repaired artifact revalidation and rejected a bare boolean, but Codex
  rejected its claim that a public `SnapshotBaselineProof` was Store-bound: any caller
  could manufacture one. A same-session manager correction made proof projection-only
  and made `publish()` the only export path.
- Codex then found and repaired a second-order isolation defect: an eligible snapshot from
  another project (or the wrong version) could authorize lifecycle closure. Public
  vertical-slice authorization is now bound to live Store acceptance plus current project
  and snapshot version; merge/split also require one shared candidate project.
- Manager and worker reports are evidence, not acceptance. The verdict rests on current
  files, independent tests and fresh SQLite/JSON inspection.

## Residual Risk

- Not tested: OS-level kill/power loss, network partition, multiprocess SQLite locking,
  external graph engines, real model adapters, UI/browser behavior or real clinical data.
- `SnapshotBaselineProof` remains a portable projection, intentionally non-authoritative.
- R1 still needs isolated framework-adapter spikes, structured work-event broadcasting,
  stronger crash/concurrency experiments and a decision on the control-plane runtime.
- Product integration, the five real projects and all clinical/visual acceptance remain
  gated to later plan stages.

## Next Safe Action

Archive this accepted slice1 execution packet without deleting evidence. Start R1 slice2
in a new isolated POC sub-scope: validate GraphPort/CheckpointPort adapters against the
eligible open-source candidates in an isolated Python >=3.10 environment, preserve the
SQLite/domain authority, and add real manifest work-event streaming plus restart tests.
