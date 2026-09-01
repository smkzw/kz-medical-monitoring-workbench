# B3 giant-file split design

## Invariants

- Preserve every public route, request/response DTO, Chinese audience string, authorization check, error code and persistence transaction.
- Split by capability boundary; do not redesign behavior while moving code.
- Keep medical-writing routes and assets byte-for-byte unchanged.
- Keep candidate/fact state, publication state, accepted snapshot/baseline, risk identity/lifecycle and provenance semantics orthogonal.
- Do not move fixture catalogs or study/drug/disease/listing-specific data into product authority.

## Router target

`services.api.app.medical_monitoring_r7_product_router` becomes a thin compatibility and mounting entry. Capability routers live under `packages.medical_monitoring.api` and share an explicit dependency/context object rather than one 5,000-line closure.

Initial extraction order minimizes coupling:

1. Pure request/response DTOs, public text maps and projection helpers.
2. Project lifecycle, backup and restore routes.
3. Setup, special-risk rule and profile routes.
4. Run preparation/execution/progress routes.
5. Publication, public result and continuity routes.
6. Thin root factory mounts the capability routers and retains unmatched-route behavior.

## Evaluator target

- Split files above 1,500 lines into cohesive contract, normalization, evaluation and materialization modules.
- Keep public imports stable through explicit package re-exports during B3.
- Start with the 5,816-line protocol module and 5,634-line efficacy evaluator after the router boundary is stable; then address remaining oversized runtime registries and evaluators by descending impact.

## Verification

- After each extraction, run `py_compile`, the directly affected focused tests and `git diff --check`.
- Keep facade-level monkeypatch seams late-bound: `_synthetic_setup_inputs`, `_build_r5_publication_packet`, `_read_publication_gate`, and startup `RecoveryCoordinator` must not become inert re-exports.
- Keep the backup/restore worker registry and lock as one shared object, and register the catch-all route only after every capability router.
- Legacy `populate(vars())` shims require eager explicit re-exports; do not use module `__getattr__` for moved evaluator symbols.
- After each router capability group, rerun both R5/R7 product-route tests and an adjacent medical-writing route/contract sample.
- After each evaluator family, rerun its complete original behavior suite.
- A move is accepted only when the authoritative package no longer imports the extracted implementation backward from the old giant module.

## Rollback

Each cohesive extraction is one git commit. Revert that commit to restore the previous module boundary; no persistent project data migration is part of B3.
