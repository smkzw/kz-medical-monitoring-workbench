# Journal - 宋旻恺 (Part 1)

> AI development session journal
> Started: 2026-09-01

---

## 2026-09-01 — Phase A recovery and Trellis bootstrap

- Authority: engineering review, System Design v1.2 amendment, and implementation plan v2.0.
- Baseline commit `ea84833` includes the interrupted `g6_runtime.py`; annotated tag `mm-baseline-20260901` preserves the evidence state.
- Repair commit `0d580ae` removes the six orphan lines and normalizes the `_load_store` classmethod receiver.
- Verification: four G6 candidate files pass `py_compile`; the two focused G6 files collect and run with 17 passes plus the two expected `entry_url_mismatch` failures. Release digests and `entry_manifest.json` remain intentionally unchanged because Phase B removes the parallel application.
- Trellis initialized for Codex, Cursor, OMP, Grok, Kimi, and CodeBuddy. Phase B–F tasks and eight Phase B children created; medical-monitoring engineering and semantic constraints live in `.trellis/spec/medical-monitoring-engineering.md`.
- Next safe action: start B1 migration inventory, trace the live R7 product import graph, and write the dependency-safe migration order here before moving code.

## 2026-09-01 — B1 migration inventory

- Static traversal from the live R7/R5 product surfaces reaches 95 POC modules: R1 9, R2 5, R3 3, R4 39, R5 12, R6 5, R7 22.
- Product coupling confirmed: the 7,684-line R7 router inserts R2–R7 source roots dynamically; R5/R7 frontend generations import each other; G6 is a separate synthetic-only stack.
- Detailed module disposition and test ownership are in `.trellis/tasks/09-01-mm-b1-inventory/research/migration-inventory.md`.
- Chosen order: domain → graph/runtime primitives → intelligence → risks/projections → reports/harness → R7 runtime/API → product routes/frontend → synthetic/deletion/test cleanup.
- Next slice: move-only R1 domain/schema-shape plus the five R2 domain modules into the new package with package-native imports and focused compatibility tests.

## 2026-09-01 — B2 domain foundation

- Moved the R1 execution-domain/schema-shape authorities and complete R2 schema/entity/identity/acceptance/risk set into `packages.medical_monitoring.domain`.
- Old `mm_r1` and `mm_r2` paths are temporary compatibility shims only; package-native modules now own the implementation. No product router, frontend, model binding, fixture, or medical-writing surface changed.
- Preserved historical import behavior for R2 symbols that were public in practice but omitted from `__all__` (`ImmutableDict`, `make_record_identity`, `make_risk_identity`).
- Verification: new authorities and shims pass `py_compile`; package compatibility plus original R1/R2 focused suites pass `297 passed`.
- Next slice: migrate the R1 graph/store/controller foundation, preserving SQLite and graph behavior through compatibility shims before any runtime redesign.

## 2026-09-01 — B2 graph and store foundation

- Moved the framework-neutral graph engine and SQLite authoritative store into `packages.medical_monitoring.graph`; old imports remain temporary shims.
- Added temporary relative `packages` links inside the R1/R2 POC source roots so isolated legacy subprocesses resolve the consolidated authority without modifying `sys.path`.
- Compatibility review exposed one historical cross-module import (`RiskIdentity` from `mm_r2.risk`) that was public in practice but omitted from `__all__`; the shim now preserves it.
- Verification: consolidated graph/store and shims pass `py_compile`; package compatibility plus the complete R1 suite pass `329 passed`.
- `controller.py` remains in place until the capability runtime moves next, preventing the new package from depending backward on a POC runtime module.

## 2026-09-01 — B2 runtime primitives

- Moved adapters, provider-neutral capability execution, capability work-unit controller, audience progress projection, and background progress into `packages.medical_monitoring.runtime`.
- Repaired background worker Store imports to the consolidated graph authority; no scheduling, persistence, progress wording, or model behavior changed.
- Capability/controller compatibility modules alias the authoritative module object so historical private test hooks and monkeypatch behavior remain exact during the transition.
- Verification: runtime authorities and shims pass `py_compile`; focused runtime/controller/background tests pass `77 passed`; the complete R1 suite plus compatibility tests pass `329 passed`.
- Next slice: migrate the R3 normalization, prompt, parser, challenge, workflow and schema-profiling intelligence authorities without embedding project-specific rules.

## 2026-09-01 — B2 normalization intelligence

- Moved the live R3 normalization, primitive hashing/freezing, and schema-registry authorities into `packages.medical_monitoring.intelligence`.
- Kept the broader experimental R3 knowledge/rule-AI modules in place because the B1 live import graph did not admit them into this migration slice; no dormant experiment was promoted into product authority.
- Compatibility modules alias the authoritative objects, and the R3 source root has the same temporary consolidated-package link used by R1/R2 subprocess tests.
- Verification: intelligence authorities and shims pass `py_compile`; compatibility plus the complete R3 suite pass `342 passed`.
- Next slice: migrate the live R4 risks/projections in dependency order, first separating executable code from embedded synthetic fixture payloads.

## 2026-09-01 — B2 shared risk foundation

- Moved R4 shared contracts, coverage ledger, lifecycle adapter, and multi-model ensemble contracts/evaluation into `packages.medical_monitoring.risks`.
- Retained fixture modules in the POC tree; no synthetic payload was promoted into product authority or hardcoded into executable risk logic.
- R4 compatibility imports deliberately avoid `sys` and `sys.path`, preserving the existing no-runtime-path-mutation contract.
- Verification: risk foundations and shims pass `py_compile`; the complete R4 suite reached `4397 passed` with three migration-test failures, then the corrected compatibility symbol and two no-`sys` AST gates pass `6 passed`. No behavioral R4 failure remained in the full run.
- Next slice: migrate evaluator/projection families one domain at a time, beginning with the low-coupling D08-D10 contract/evaluator groups while keeping fixtures separate.

## 2026-09-01 — B2 D08 risk/projection family

- Moved D08 cross-domain consistency contracts and evaluation into `risks`, and its renderer-neutral audience projection into `projections`.
- Added a temporary R4 compatibility bridge that preserves private legacy test probes while keeping the inspected D08 runtime shims limited to allowed `mm_r4` imports; it does not mutate `sys.path`.
- Verification: package and compatibility files pass `py_compile`; all D08 tests plus package compatibility pass `190 passed`.
- Next slice: repeat the same evaluator/projection separation for D09, then D10, without moving their challenge fixtures into product authority.

## 2026-09-01 — B2 D09 risk/projection family

- Moved the D09 center-pattern contracts/evaluator into `risks` and its audience/Query/hotspot/R2-handoff projection into `projections`.
- Preserved D09's closed denominator, count-surface, Query-draft and lifecycle-handoff behavior; no center threshold, disease rule, drug rule or listing column was introduced.
- Verification: D09 authorities and compatibility modules pass `py_compile`; the complete D09 suite passes `243 passed`.
- Next slice: migrate D10 adapter/contracts/evaluator/projection, then proceed through D07 and D01-D06 families while leaving frozen challenge catalogs outside product authority.

## 2026-09-01 — B2 D10 risk/projection family

- Moved D10 project-signal contracts/evaluator into `risks` and its audience/Query/hotspot/R2-handoff projection into `projections`.
- The initial move of `d10_adapter.py` exposed its frozen-catalog path dependency. Because the module is explicitly test-only, it was restored to the POC test boundary instead of teaching product code where challenge artifacts live.
- This correction keeps frozen catalogs, oracles, registries and quotas outside product authority and avoids encoding fixture layout into runtime logic.
- Verification after correction: D10 package modules and compatibility modules pass `py_compile`; the complete D10 suite passes `186 passed`.
- Next slice: migrate D07 safety contracts/evaluator/Journey/Query as one dependency-closed family, with `d07_fixtures.py` retained outside product authority.

## 2026-09-01 — B2 D07 safety/Journey/Query family

- Moved D07 clinical-safety contracts and evaluator into `risks`; moved its visit-axis Journey and structured Query projections into `projections`.
- Kept `d07_fixtures.py` outside product authority. The evaluator still consumes typed, source-bound inputs and produces candidate/projection outputs without hardcoded study, drug, disease or listing layouts.
- Verification: D07 authorities and compatibility modules pass `py_compile`; the complete D07 suite passes `1418 passed`.
- Next slice: migrate D01 AE/MH and its shared projection, then D02 CM and D03 IP families with fixture modules retained outside product authority.

## 2026-09-01 — B2 D01 AE/MH family

- Moved the AE/MH semantic-role evaluator into `risks` and its renderer-neutral Journey/Query projection into `projections`.
- Preserved compatibility monkeypatch semantics for the lifecycle adapter through a module-object alias implemented in the nested compatibility bridge; root R4 runtime files still contain no `sys` import or `sys.path` mutation.
- Verification: AE/MH authorities and shims pass `py_compile`; AE/MH plus lifecycle/projection tests produced `153 passed` with one compatibility-hook failure, and the corrected hook plus both no-private/no-`sys` gates pass `3 passed`.
- Next slice: migrate D02 CM evaluator/projection, leaving `cm_fixtures.py` outside product authority.

## 2026-09-01 — B2 D02 CM family

- Moved the concomitant-medication semantic evaluator into `risks` and its interval/overlap Journey projection into `projections`.
- `cm_fixtures.py` remains outside product authority; medication identity, prohibited-component and PD decisions remain typed inputs rather than drug-specific constants.
- Verification: CM authorities and compatibility modules pass `py_compile`; the complete CM suite passes `194 passed`.
- Next slice: migrate D03 IP evaluator/projection while retaining `ip_fixtures.py` outside product authority.

## 2026-09-01 — B2 D03 IP family

- Moved the investigational-product exposure/adherence/accountability evaluator into `risks` and its Journey/risk projection into `projections`.
- `ip_fixtures.py` remains outside product authority; treatment assignments, dose rules and accountability expectations stay source-derived typed inputs.
- Verification: IP authorities and compatibility modules pass `py_compile`; the complete IP suite passes `217 passed`.
- Next slice: migrate D04 protocol-compliance evaluator/projection while retaining `protocol_fixtures.py` outside product authority.

## 2026-09-01 — B2 D04 protocol family

- Moved protocol-compliance evaluation into `risks` and its Journey/PD/Query-facing projection into `projections`.
- `protocol_fixtures.py` remains outside product authority; inclusion/exclusion and protocol-deviation decisions remain driven by source-derived typed rules.
- Verification: protocol authorities and compatibility modules pass `py_compile`; the complete protocol suite passes `277 passed`.
- Next slice: migrate D05 visit-schedule evaluator/projection while retaining `visit_schedule_fixtures.py` outside product authority.

## 2026-09-01 — B2 D05 visit-schedule family

- Moved visit-schedule contracts/evaluation into `risks` and the visit-axis Journey projection into `projections`; challenge fixtures remain outside product authority.
- Relocation exposed a legacy anti-forgery check tied to the old Python module name. It now accepts only the old compatibility module or the new authoritative projection module while retaining exact dataclass/type/content-address checks.
- Verification: the initial visit suite had 331 passes and 11 relocation-identity failures; after the bounded module-identity correction, the complete visit-schedule suite passes `342 passed`.
- Next slice: migrate D06 efficacy contracts/evaluator/projection while retaining `efficacy_fixtures.py` outside product authority.

## 2026-09-01 — B2 D06 efficacy family

- Moved efficacy contracts/evaluation into `risks` and its shared visit-axis Journey projection into `projections`.
- Kept `efficacy_fixtures.py` and the frozen challenge corpus outside product authority; efficacy endpoints, estimands, thresholds and disease/drug semantics remain typed source-derived inputs.
- The first relocation run exposed four stale same-package imports inside the projection. Updating them to the authoritative `risks.efficacy` path restored the unchanged runtime contract.
- Verification: package and compatibility files pass `py_compile`; the complete efficacy suite passes `920 passed`.
- Next slice: inventory the remaining top-level R4 POC modules, retain only fixture/test-bound artifacts there, run the complete R4 suite, and then begin R5 projection/product-adapter migration.

## 2026-09-01 — B2 R4 authority closure

- Reconciled every remaining top-level `mm_r4` file. Live domain/runtime files are now compatibility entries to `packages.medical_monitoring`; only synthetic fixtures, frozen challenge adapters/oracles and the legacy package entry remain physically test-bound.
- No fixture, hardcoded study/drug/disease rule, listing layout or challenge-path dependency was promoted into product authority.
- Verification: the complete original R4 suite passes `4396 passed` in 196.54 seconds; consolidated package compatibility adds `4 passed`. This closes the R4 behavioral boundary at `4400 passed` across the two declared commands.
- Next slice: inspect R5's live import closure, migrate renderer-neutral projections and the product adapter without pulling fixtures or presentation-specific constants into backend authority.

## 2026-09-01 — B2 R5 publication authority

- Moved the 12 R5 modules reachable from the live product graph into `packages.medical_monitoring.projections.publication`: canonical contracts, D10 authority receipt, S2 packet/thin slice, S4 Risk Inspector builder/projection/validator, publication bridge and package surface.
- Repaired R4 dependencies to the consolidated risk/projection authorities. Synthetic fixture builders remain explicit test-only paths; no challenge catalog, disease/drug rule or listing layout was promoted.
- Compatibility review found `mm_r4.ensemble` must alias the authoritative module object so downstream monkeypatch verification remains real; its old star export also omitted imported public contracts. The alias fixes both without runtime path mutation.
- Verification: foundation behavior `230 passed` with one obsolete old-module-name assertion deselected; S2 contracts/builders/challenges `136 passed`; S4 complete focused runtime `472 passed`; publication bridge `5 passed`. The separate S2 thin-slice file is blocked only by its abolished whole-file SHA autouse gate, which Phase B7 removes; its thin-slice challenge suite is included in the 136 passes.
- Next slice: move the live R5 product read-model adapter into the consolidated projection package, keep the API module as a temporary compatibility entry, and run product adapter/router behavior before product-wide import cutover.

## 2026-09-01 — B2 R5 product read model

- Moved the active R5 product read-model adapter from the API package into `packages.medical_monitoring.projections.product_adapter`; the old API module is now a temporary public re-export so route behavior stays unchanged until the final cutover.
- This is a mechanical move only. Existing explicitly selected synthetic-fixture behavior is retained for B5 separation and is not used as a missing-authority fallback.
- Verification: adapter, subject-flow and R5 product-router behavior pass `49 passed`; both authority and compatibility modules pass `py_compile`.
- Next slice: migrate the five live R6 report/harness modules, then R7 runtime dependencies, before cutting product routers directly to consolidated imports.

## 2026-09-01 — B2 R6 reports and harness

- Moved R6 contract loading, external-report review and three-mode output into `packages.medical_monitoring.reports`; moved the provider-neutral agent harness into `packages.medical_monitoring.runtime`.
- Updated the contract artifact root for the consolidated file location and kept old R6 imports as temporary compatibility entries. No model binding, medical rule, report wording or mode behavior changed.
- Verification: authorities and compatibility entries pass `py_compile`; focused R6 behavior produced `477 passed`. The seven failures are exclusively abolished whole-file SHA pins, old POC create-only allowlists, and a fixed medical-writing file-count pin; no report/mode/harness behavior test failed, and no medical-writing file changed.
- Next slice: migrate the R7 runtime/lifecycle/persistence modules in dependency order, beginning with schema/ledger and project lifecycle primitives before run execution and continuity.

## 2026-09-01 — B2 R7 runtime and thin API

- Moved all 21 executable R7 modules into `packages.medical_monitoring.runtime` and the thin run-entry FastAPI surface into `packages.medical_monitoring.api`; the legacy `mm_r7` package now resolves them through temporary compatibility entries.
- Removed R7's dynamic POC `sys.path` injection and repaired all consolidated risk modules that still imported `mm_r1`/`mm_r2`/`mm_r3`, so the new package resolves its own domain, intelligence, risk, projection, report and runtime chain.
- Downstream compatibility exposed the old R1 Store star export omitting `_runtime_schema_shape`; the legacy Store path now aliases the authoritative module object, preserving both the private migration probe and monkeypatch semantics.
- Verification: dependency/runtime/API focused suite `143 passed`; profile/run binding/entry after standalone-package import repair `65 passed`. The complete original R7 suite produced `492 passed`, `1 skipped`, `19 failed`: 15 explicitly abolished optimizer/hash-seed matrix cells, one R6 whole-file SHA pin, one POC allowlist, and two old-source AST/text location assertions. No runtime behavior failure remained outside those Phase B7 removals.
- Next slice: cut the product routers from POC imports and dynamic path insertion to `packages.medical_monitoring`, then run product-route and adjacent medical-writing route checks before closing B2.

## 2026-09-01 — B2 product import cutover and phase closure

- Cut both live medical-monitoring product routers directly to `packages.medical_monitoring`; removed R7 router POC source-root insertion and changed lazy R5/R6/R7 publication, continuity and harness imports to consolidated authorities.
- Migrated the active R5/R7 product test helpers to package-native imports. R7 legacy modules remain temporary relative compatibility entries only; no product path needs a top-level `mm_r*` package or POC path mutation.
- Product-route behavior passes `141 passed`; consolidated authorities and routers pass `py_compile`; `services.api.app.main` imports with 352 registered paths and retains both medical-writing and medical-monitoring route families.
- Adjacent medical-writing checks pass `127 passed` across the manifest and frontend writing contracts. The diff contains no medical-writing source or asset file.
- Final R4 closure rerun after all consolidated import repairs passes `4396 passed` in 199.51 seconds. `git diff --check` passes.
- B2 is complete: domain, graph, intelligence, risks, projections, reports, runtime and thin API now have one package authority. Compatibility shims stay until B6; abolished frozen SHA/path/allowlist gates remain assigned to B7.
- Next safe action: enter B3 and split the oversized product/API modules by capability without changing routes, payloads, Chinese audience wording or medical semantics.

## 2026-09-01 — B3 planning and request-contract extraction

- Activated the B3 Trellis task and recorded the route/evaluator decomposition, rollback and verification contract. A governed three-work-item execution review completed on `zcode/GLM-5.3-Flash:max`; execution audit passed with all three workers completed and no fallback.
- Source and test evidence identified four hard compatibility constraints: facade-level monkeypatch seams must remain late-bound, backup worker state must remain a single object, the catch-all route must register last, and legacy `populate(vars())` shims require eager re-exports.
- First bounded extraction moved all R7 request DTOs plus `ProductPublicationError` into `packages.medical_monitoring.api.r7_product.contracts`; the facade re-exports the same class objects and its runtime closure is unchanged.
- Verification: new contract/facade files pass `py_compile`; R5/R7 product router behavior passes `100 passed`; no medical-writing source or asset changed.
- Next slice: extract continuity DTOs and pure projection helpers while leaving publication seams and all I/O-bearing nested route functions in the facade.

## 2026-09-01 — B3 continuity contracts

- Moved continuity audience labels, response DTOs, severity normalization, risk-state semantic validation and deterministic row ordering into `packages.medical_monitoring.api.r7_product.continuity_contracts`.
- The facade eagerly re-exports all 16 contract/helper symbols, preserving class/function identity; the public-text sanitizer remains in the facade until its shared secret-field rules move as one unit.
- Verification: package and facade pass `py_compile`; facade identity check passes for all 16 exported symbols; R5/R7 product routes plus adjacent medical-writing checks pass `227 passed`; `git diff --check` passes.
- Next slice: extract shared public-text sanitization and remaining module-level projection helpers without moving any I/O-bearing route closure or patch seam.

## 2026-09-01 — B3 backup and restore projections

- Moved backup status/step/impact labels and the pure backup, restore and preflight audience projections into `packages.medical_monitoring.api.r7_product.backup_projections`.
- The single process-wide backup worker registry and lock remain untouched in the facade; no background worker, persistence, route or recovery behavior moved in this slice.
- Verification: new module and facade pass `py_compile`; R5/R7 product routes pass `100 passed`.
- Next slice: move launch/publication and public-result pure projections, keeping facade patch seams and I/O orchestration in place.

## 2026-09-01 — B3 public-text sanitization

- Moved the shared secret-field vocabulary, audience-output denylist, secret-value detector, continuity text sanitizer and generic projection sanitizer into `packages.medical_monitoring.api.r7_product.public_text`.
- All six symbols remain eager facade re-exports. Secret filtering, internal-term suppression and error class identity are unchanged; no endpoint or route closure moved.
- Verification: package and facade pass `py_compile`; R5/R7 product routes pass `100 passed`.
- Next slice: extract launch/publication and public-result pure projections, then rerun the combined product and adjacent medical-writing gate.

## 2026-09-01 — B3 result projections

- Moved publication audience wording, launch/publication state projections, public-result locator vocabulary and authority-field stripping into `packages.medical_monitoring.api.r7_product.result_projections`.
- The facade retains error-envelope helpers, request parsing and all publication provider/bridge seams; no I/O orchestration or endpoint body moved.
- Verification: package and facade pass `py_compile`; R5/R7 product plus adjacent medical-writing checks pass `227 passed`.
- Next slice: extract request/error helpers and legacy read-only projections, then close the module-level pure-projection checklist before introducing capability route contexts.

## 2026-09-01 — B3 error envelopes

- Moved error-code groups, Chinese authorization/runtime messages, HTTP status mapping, validation error handling and stable JSON error envelopes into `packages.medical_monitoring.api.r7_product.errors`.
- A first mechanical boundary selected two lines beyond the intended constants and was corrected before commit; the process-wide backup/restore worker registry, lock and terminal sets remain a single facade-owned object.
- Verification: package/facade pass `py_compile`; all 13 error symbols preserve facade identity; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `git diff --check` passes.
- Next slice: extract legacy read-only profile/binding/run/risk/progress projections and setup/execution projections.

## 2026-09-02 — B3 legacy read-only and execution projections

- Moved legacy profile, binding, launch, risk and progress projections plus setup/execution audience adapters into `packages.medical_monitoring.api.r7_product.legacy_projections`.
- Kept read-only view/store opening, mutable runtime construction, backup worker state and all endpoint closures in the facade. The nine moved symbols are eager facade re-exports, preserving compatibility identity.
- Verification: package and facade pass `py_compile`; all nine facade identities match the extracted authority; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `git diff --check` passes.
- Next slice: extract public-result request parsing and publication-manifest/provider-neutral metadata helpers, then begin capability route-context separation while retaining facade patch seams.

## 2026-09-02 — B3 public-result requests and runtime manifest

- Moved strict body/query/date parsing and comparison-range wording into `public_result_requests`; moved manifest identity/digest plus read-only runtime metadata/audit inspection into `runtime_manifest`.
- The route factory still resolves all nine helpers through eager facade bindings, so endpoint monkeypatch boundaries and route order are unchanged. No provider, publication bridge, mutable store or medical semantic logic moved.
- Verification: both authorities and facade pass `py_compile`; all nine facade identities match; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `git diff --check` passes.
- Next slice: isolate provider-neutral invocation adapters while keeping `_build_r5_publication_packet` and `_read_publication_gate` late-bound in the facade, then start capability route-context extraction.

## 2026-09-02 — B3 publication provider adapters

- Moved lazy R5/R6 type loading, signature-aware provider invocation, mode-output acquisition and R5 packet validation into `publication_providers`.
- Kept `_build_r5_publication_packet` and `_read_publication_gate` in the facade as required late-bound seams; provider selection and injected bridge/factory ownership remain unchanged.
- Verification: authority and facade pass `py_compile`; all eight facade identities match; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `git diff --check` passes.
- Next slice: define an explicit capability dependency context and extract the first cohesive route family without changing route paths, registration order, request/response payloads or audience wording.

## 2026-09-02 — B3 setup, risk-rule and profile route family

- Introduced `SetupRouteContext` and moved six contiguous route closures—run setup options, special-risk preview/append/list, and execution-profile append/read—into `setup_routes` while registering them at their original point in router order.
- The package route module imports no service-layer module. Authorization enum and all factory-local lifecycle/store dependencies are injected explicitly; request/response models, Chinese audience wording and legacy read-only projections remain unchanged.
- The first complete product run exposed one omitted context dependency (`_workspace_dir`) in the two profile routes. After adding it to the explicit context, the five affected tests pass and the full gate is green.
- Verification: package and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; no `services.api` or `mm_r*` import exists in the extracted module; `git diff --check` passes.
- Next slice: extract the run preparation/execution/progress family behind a second explicit context, preserving the process-wide worker objects and facade-level publication seams.

## 2026-09-02 — B3 run launch, execution and progress routes

- Introduced one immutable `RunRouteContext` and moved nine run-facing endpoints into three registration groups placed at their original order boundaries: launch/list before publication, bind/execution/progress after publication, and run detail after public-result routes.
- The split retains facade-local lifecycle, store and publication-overlay ownership through explicit injected dependencies. It does not move publication packet construction, receipt gates, worker state or the final catch-all route.
- Verification: extracted route module and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; the extracted package imports no service-layer or POC module.
- Next slice: extract publication/result/continuity route registration while keeping `_build_r5_publication_packet`, `_read_publication_gate` and provider selections facade-late-bound; then split project lifecycle/backup routes.

## 2026-09-02 — B3 publication, result and continuity routes

- Added `PublicationRouteContext` and moved publication status/write routes plus overview, subject, source-evidence, continuity and result-entry routes into two registration groups at their original order boundaries.
- `_build_r5_publication_packet` and `_read_publication_gate` remain facade-late-bound through call-time wrappers, so tests or runtime overrides still resolve the facade symbols after router construction. Provider/bridge selection stays factory-owned.
- Verification: extracted module (under the 1,500-line hard limit) and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; no service-layer or POC import exists in the extracted package module.
- Next slice: extract project open/upgrade/backup/restore routes and their worker orchestration behind explicit contexts while retaining one facade-owned worker registry and lock; then reduce the root factory to wiring.

## 2026-09-02 — B3 project lifecycle, backup and restore routes

- Added `ProjectRouteContext` and moved project open/audit, schema upgrade, backup, restore and workspace bootstrap endpoints into `project_routes`, registered at the original pre-setup position.
- The facade still owns the single backup-worker registry/lock and all migration/recovery worker helpers. Route code receives those operations explicitly, so this slice does not duplicate process state or alter lifecycle authority.
- Verification: extracted module and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; no service-layer or POC import exists in the package route module.
- Next slice: decompose the remaining factory-local lifecycle/backup and publication/result helper clusters so the root file becomes dependency wiring, then start oversized backend-domain modules.

## 2026-09-02 — B3 publication services and facade seams

- Moved R5 packet assembly and runtime receipt-gate validation into `publication_services`; retained thin facade wrappers for `_build_r5_publication_packet` and `_read_publication_gate`, preserving call-time patchability required by the router contract.
- Moved request/workspace helpers into `route_utils`. Moved the deterministic setup fixture into a clearly marked temporary compatibility module with a facade wrapper; it remains excluded from product authority and assigned for deletion in B5 rather than being generalized or promoted.
- The first full product run failed broadly from one removed import pair (`PROFILE_DB_NAME`/`RUN_BINDING_DB_NAME`) still used by facade compatibility checks. Restoring that import pair recovered three representative tests and the complete product gate.
- Verification: new modules and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`.
- Next slice: split the remaining factory-local project-operation/common-context helper clusters, keeping startup recovery and the single backup worker registry/lock facade-owned until their explicit state object is introduced.

## 2026-09-02 — B3 result-context and continuity services

- Moved accepted R5 publication-context reconstruction into `result_context_service` with explicit dependencies and call-time wrappers for the two facade publication seams.
- Moved the 565-line continuity reconstruction/validation pipeline into `continuity_service`; the facade retains only a root-bound adapter passed to the public-result route context. DTO validation, source-artifact verification, risk lifecycle semantics and 200-row audience cap are unchanged.
- Verification: both service modules and facade pass `py_compile`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`.
- Next slice: extract remaining publication overlay/error helpers and then the project-operation/common factory helpers; target is a root router file below the hard limit with only dependency construction and route registration.

## 2026-09-02 — B3 project operations and thin R7 facade

- Moved publication overlay, setup-input, failure-response and result-envelope helpers into `publication_view_helpers`; moved startup recovery, maintenance gating, backup/restore workers, registry/catalog/launch helpers and project compatibility operations into the dependency-injected `project_operations` authority.
- The process-wide backup worker dictionary and lock remain the same facade-owned injected objects. Startup `RecoveryCoordinator` and the temporary synthetic setup seam remain call-time facade wrappers, preserving the existing monkeypatch and recovery boundaries.
- Reduced `medical_monitoring_r7_product_router.py` from the original 7,669 lines to 959 lines; both newly extracted authoritative modules remain below the 1,500-line hard limit.
- Verification: R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; package/facade `py_compile`, whitespace scan and diff checks pass.
- Next slice: decompose oversized backend authorities for protocol risk evaluation, efficacy evaluation and launch/publication continuity while preserving DTOs, publication semantics and store ownership.

## 2026-09-02 — B3 protocol risk-domain decomposition

- Split the 5,816-line D04 authority into contracts, applicability/routing, evidence/expected-set expansion, component evaluation, risk/query projection and materialization modules behind the existing `risks.protocol` facade.
- Kept the original public exports and the one historically tested private evaluation-window helper. The first injected-authority run exposed three slice-boundary decorators and one forward class dependency; both were restored before acceptance without changing evaluation logic.
- Every protocol source file is now below 1,500 lines (largest: `protocol_evidence.py`, 1,369 lines). Candidate/fact separation, applicability gates, cross-domain evidence identity, risk identity, three-part Chinese Query and audience-language contracts remain covered.
- Verification: original D04 protocol, projection, challenge-matrix and shared-domain suites pass `339 passed`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `py_compile` and diff checks pass.
- Next slice: split efficacy validation/resolution/engine/output gates, preserving fixture-schema failures and deterministic risk/output contracts.

## 2026-09-02 — B3 efficacy engine decomposition

- Split the 5,634-line D06 evaluator into fixture/contracts, output gates, normalization/resolution and four cohesive engine mixins (pipeline, unit strategies, TTE/query/lifecycle, audience/output) behind the existing `EfficacyEngine` and module entrypoints.
- The public engine class remains defined in `efficacy_evaluator`; its method behavior is inherited from the extracted mixins. Restored the historically imported private decimal canonicalizer as a facade compatibility seam after the first complete suite identified it.
- Every D06 evaluator source is below 1,500 lines (largest: `efficacy_unit_mixin.py`, 1,420 lines). No challenge-id branch, drug/disease constant or listing-layout hardcode was added.
- Verification: original D06 contract, challenge-matrix and mutation suites pass `824 passed`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `py_compile`, whitespace and diff checks pass.
- Next slice: split launch registry records, publication state and continuity-plan persistence while retaining one SQLite authority and transaction boundary.
