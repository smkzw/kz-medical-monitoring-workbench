# Known Issues

## Medical-Writing Source Content Quality

Status: active adjacent gap

The RUX-03-002 V1.3 original protocol contains the literal string `对于研究中具有生育能力的女性受试者：<0}` in Appendix 1, table 11 row 3 cell 1. The unchanged draft export and rendered PDF preserve the same source text. This is not a CJK font, encoding or Word-export defect.

The medical-writing pipeline currently preserves source fidelity but does not surface suspicious source-born residues such as unmatched angle/brace tokens as a separate content-quality warning. The next implementation must:

- detect suspicious tokens deterministically without silently rewriting the immutable source;
- show the exact source text and locator in the editor/content-review workflow;
- allow a medical user to classify the item as confirmed source text, correction needed or not an issue with an audit reason;
- block only medically approved/final output when an unresolved item is configured as approval-blocking; draft editing and source review must remain available;
- prove the rule on at least RUX plus two unaffected real protocols so it is not project-hard-coded.

## Source Registry Deployment Configuration

Status: deferred, tracked

Current local-single-machine build keeps `SOURCE_REGISTRY_CANDIDATES` and `allowed_roots` in backend source code. This is acceptable for the current private local prototype because the frontend now uses opaque candidate ids and public API payloads do not expose local paths.

Before any of the following, move the candidate mappings and allowed roots into a private deployment config:

- code distribution outside this workstation;
- multi-machine or private-network deployment;
- public repository push;
- shared demo build where frontend/backend source may be inspected by others.

Minimum acceptance for that future change:

- frontend still contains no `/Users/` paths in source or build output;
- backend public API still excludes `content_hash`, `preview_hash`, `storage_key`, `server_path`, and local paths;
- config file is excluded from distributable source bundles unless explicitly sanitized.

## RUX Medical Monitoring Integration

Status: active build, not complete

The additive backend service `services/api/app/rux_monitoring_service.py` can currently derive protocol rules, selected RUX real-data RiskCase anchors, and S01003 Subject Timeline/ANC trend from the original RUX listing/protocol. The subject-monitoring API now dispatches `proj_rux_03_002/S01003` to this real-data service.

Background Hermes/Codex review on 2026-07-08 accepted the following as required gates before further product-code landing:

- verify RUX source file freshness and parser/anchor baseline before inbox integration;
- write a red 404-baseline test for `GET /api/projects/proj_rux_03_002/workbench-inbox`;
- write the target failing 200 test before implementing RUX inbox projection;
- fix or explicitly test ECB `暂停用药` / `重新用药` semantics so protocol-aligned dose management is not surfaced as `protocol_deviation`;
- project listing/protocol source locators through `WorkbenchItemSourceRef.locator` without exposing `/Users/`, hashes, storage keys, or server paths;
- preserve demo inbox read-state, sorting, pagination/visible-selection behavior, and existing project behavior.

Before this can be treated as a commercialized 医学监查 workflow:

- expand RUX risk projection beyond the current verified P0 anchors into a governed full-subject workflow;
- expand canonical RUX dashboard integration beyond the current P0 monitoring anchors into complete cross-module aggregation;
- complete Patient Profile and broader Subject Timeline browser QC across 3-5 real RUX subjects and a second study;
- add frontend Subject Timeline renderer support for `dose_adjustment` events before any RUX timeline UI acceptance;
- implement prohibited concomitant medication classification through independent runtime AI plus protocol-sourced deterministic overrides;
- generate Patient Profile chart/trend views from RUX event/trend data, not from previous static HTML outputs;
- preserve source locators for every visible event, risk, trend point, and AI suggestion.

Current accepted P0 boundary:

- RUX workbench inbox projects only verified medical-monitoring risk anchors for S01017/S01003/S03040.
- It is explicitly not full 192-subject RUX monitoring and not cross-module RUX project management.
- Production expansion still needs cached/incremental parsing, listing-refresh-stable identifiers, and complete cross-module dashboard aggregation.

## Cross-Project Persistence And AI Policy

Status: active platform gap

Canonical project routing and module-package isolation were verified on 2026-07-10, but not every persistent store has qualified identifiers, restart recovery, idempotency, or collision tests. Before commercial acceptance:

- use a shared write envelope for risk, approval, source, evidence, AI run, handoff, writing revision, TFL review, and Safety/PV review;
- prove same-id isolation and restart recovery across at least two projects;
- resolve independent AI provider policy by project, task, data classification, and deployment profile;
- keep all modules explicitly blocked when their provider or source chain is unavailable.
