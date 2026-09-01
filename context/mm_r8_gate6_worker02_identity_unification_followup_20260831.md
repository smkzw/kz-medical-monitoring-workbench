# G6 Worker 02 Same-Session Follow-up — Canonical Identity Unification

Continue the same `worker_02` execution session. Do not start a new session, service, browser, model, or network call.

## Hard boundaries

- Work only inside the current workbench and only on the allowed files below.
- Do not read or write any real project, medical-writing file, credential, external account, or path outside this workbench.
- Do not start services, browsers, models, network calls, or subprocess Agents.
- Do not claim final G6 acceptance.

## Read these files only

- `context/mm_r8_gate6_synthetic_ego_implementation_20260831_execution_context.md`
- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `deploy/medical_monitoring_local/actual_app.py`
- `deploy/medical_monitoring_local/synthetic_ego.py`
- `deploy/medical_monitoring_local/release_sources.json`
- `tests/test_medical_monitoring_g6_entry_lifecycle.py`
- `tests/test_medical_monitoring_r8_gate6_synthetic_ego.py`

## Observed blocker

Codex integration review found three divergent G6 identities:

- `execution_boundary_manifest.json` binding: `sha256:fb2399...`
- Python `synthetic_ego.py` canonical profile binding: `sha256:1a8d6561...`
- frontend static fixture binding: `sha256:6bb510f8...`

Python owns 96 events while the frontend fixture owns 58. This split-brain state fails the frozen G6 contract and blocks visual execution.

## Assigned repair

Make `deploy/medical_monitoring_local/synthetic_ego.py` the single canonical generator and expose its validated audience bundle through the actual local application without any external network, real project, model, or fallback.

1. Add the smallest deterministic actual-app endpoint needed by the frontend, preferably `GET /api/g6/synthetic-bundle`, returning `build_synthetic_audience_bundle()` only after `validate_synthetic_audience_bundle()` succeeds.
2. Bind the endpoint to the same loopback-only actual app already frozen by the boundary manifest. Do not add another process or port.
3. Ensure the response exposes the canonical fixture, binding, notification/task evidence needed by the page, with exact canonical digests and 96 events. Do not add a second JS-authored dataset.
4. Add focused offline handler/bundle tests that do not bind a port. They must prove deterministic identity, fail-closed validation, no real-provider/model/project path, and endpoint payload equality with the Python canonical bundle.
5. Add `synthetic_ego.py` to `release_sources.json`. Do not regenerate entry/release manifest hashes in this pass; worker_01 will do that after frontend integration.
6. Preserve all prior G4/G5 semantics and medical-writing boundaries.

## Allowed files

- `deploy/medical_monitoring_local/actual_app.py`
- `deploy/medical_monitoring_local/synthetic_ego.py` only if a minimal export seam is required
- `deploy/medical_monitoring_local/release_sources.json`
- focused G6 tests under `tests/`
- runner-managed worker report only

## Verification

Run the smallest focused Python tests for the new endpoint and existing G6 fixture/lifecycle. Return exact test counts, canonical fixture/profile binding/bundle digests, changed files, residual risks, and the frontend consumption contract. Do not claim G6 acceptance.

## Output

Return one compact handoff to the runner-managed output file `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_identity_followup.md`. Do not write that report path directly through file tools.
