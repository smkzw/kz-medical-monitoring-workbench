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

## 2026-09-02 — B5 product-native synthetic profile

- Externalized the deterministic R5 authority data, R7 setup data and run seed into validated JSON fixtures under `tests/fixtures/medical_monitoring`; product Python now contains assembly and derivation only. R5 packet identities across all six variants and R7 opaque tokens remained unchanged.
- Added one product startup command, `python3 -m services.api.app --synthetic`, which selects the synthetic profile before the real app imports, scopes the synthetic principal to the synthetic project, and idempotently seeds a two-step deterministic run through the actual R7 product routes. The old environment-variable seam was removed.
- Deleted `deploy/medical_monitoring_local` and all 10 tests whose only subject was that parallel G6 application. The wider dependency scan corrected the planning-time five-file estimate; no live product consumer remains.
- Verification: governed execution audit passed on three `zcode/GLM-5.3-Flash:max` workers without fallback; focused product set `161 passed`; medical-monitoring regression `315 passed`; all 62 medical-monitoring frontend node suites passed; Vite build passed; Codex reran compilation plus the fixture/startup/adapter/allowlist gate with `28 passed` and a clean residual-reference scan.
- Two medical-writing contract failures and one medical-writing collection error were independently reproduced as pre-existing and remain untouched under the subsystem protection boundary. They do not arise from B5.
- Next safe action: close and archive B5, then start B6 to remove remaining POC compatibility shims and the temporary R6 import bridge without changing routes, payloads or medical semantics.

## 2026-09-02 — B6 POC authority closure

- Closed the last executable `mm_r4`/`mm_r6`/`mm_r7` imports in the product package. R7 continuity and R6 harness now resolve package-native authorities; the synthetic D10 path uses a pure structural mapping converter without importing frozen catalog/SHA/oracle machinery; the `--synthetic` startup no longer inserts a POC path.
- Moved the deterministic R7 fake harness and S4 runtime fixture into `tests/medical_monitoring`, rewired the product router suite to package-native imports, and removed the compatibility-identity-only test.
- Deleted all eight versioned POC work trees (R1–R7 plus R3 rule-ai): 392 tracked files and 188,278 lines. Commit history is the recovery path; no executable POC import remains in `packages/`, `services/`, `frontend/src/` or current tests.
- Verification: governed execution audit passed for three `zcode/GLM-5.3-Flash:max` workers without fallback; package-native focused regression `157 passed`; wider medical-monitoring selection `311 passed`; all 62 frontend medical-monitoring node suites and Vite build passed. Codex independently reran the product-native synthetic startup gate and residual import scan successfully.
- The only remaining POC-path references are 30 uncalled frozen slice-era generator/verifier scripts assigned to B7. Historical docstrings and the `mm_r7:project_audit:genesis:v1` digest-domain constant remain intentionally unchanged.
- Medical-writing remained untouched. Its two stale translation source-contract assertions and one pre-existing collection import error were reproduced but not repaired across the subsystem boundary.
- Next safe action: enter B7, remove obsolete frozen-SHA/optimizer/hash-seed/generator gates and stale uncalled POC scripts while retaining behavioral digest and shape assertions.

## 2026-09-02 — B7 lossless pause during integrated verification

- B7 planning is committed (`d012644`). Static classification completed: whole-file historical SHA pins are confined to the D07–D10 artifact-generator tests; runtime content-address, source SHA, CAS, identity/lifecycle, snapshot and behavioral digest assertions are explicitly retained.
- Cleanup implementation is committed (`deee6eb`): removed 35 uncalled R5 S3–S6 POC-era generator/verifier scripts (including all remaining optimizer/hash-seed matrix machinery) and surgically removed historical whole-file pins from D07–D10 while retaining structure, self-consistency, tamper rejection, determinism and domain behavior coverage.
- Completed evidence before pause: affected D07–D10 suite `370 passed`; full collection succeeds for 8,137 tests when excluding the already-known unrelated medical-writing collection error. No product or medical-writing source changed in B7.
- User requested immediate lossless pause while the third governed worker was running integrated verification. The runner was interrupted with exit 130 before it produced a result; no uncommitted product/test change exists. B7 remains active and is not accepted or archived.
- Resume exactly here: initialize/reuse a governed B7 verification pass, run medical-monitoring focused/integration regression, all 62 frontend medical-monitoring node suites, Vite build, protected medical-writing subset and residual scans; then Codex audit, decide whether to delete the now-orphaned existing D10 raw-SHA anchor artifact, journal the result, and archive B7. Do not redo the committed classification or cleanup.

## 2026-09-02 — B4 frontend single-generation closure

- Lifted the medical-monitoring product, progress, continuity, Journey, browser-route, project-isolation and data-read ownership into generation-neutral feature modules; `App.jsx` now delegates rendering through one `MedicalMonitoringRouteOutlet` and one `MedicalMonitoringPage` mount.
- Removed the complete parallel G6 frontend (`b20dd02`), then removed the 2,000-line legacy App monitoring workspace, its separate Profile/Timeline generation and the obsolete feature data hook (`af4a3e9`). Canonical setup/progress/result/Journey behavior remains the only mounted medical-monitoring path.
- Preserved the product result contracts: horizontal shared visit/time axis, typed event/risk markers, marker detail drawer, center/subject flow, source drill-down, project isolation and candidate/fact separation. No medical-writing source or asset file changed.
- Verification: 64 medical-monitoring Node suites pass; protected medical-writing durable-state contract reports 52 passed and 0 failed; Vite production build passes with 1,931 modules. The existing >500 kB chunk warning remains non-blocking; final browser/visual acceptance stays assigned to the Phase-B ego(lite) smoke task.
- The production bundle decreased from about 2.37 MB JS / 526 KB CSS after G6 removal to about 1.93 MB JS / 458 KB CSS after legacy-path removal. B4 was archived by Trellis after acceptance.
- Next safe action: start B5 and externalize synthetic product profiles so synthetic evidence enters through the canonical product without reviving a parallel application or hardcoding study/drug/disease/listing behavior.

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

## 2026-09-02 — B3 launch, publication and continuity registry decomposition

- Split the 4,713-line registry into canonical records/serialization plus mixins for lifecycle and launch reservation, publication reservation/retrieval, publication transitions/finalization, continuity persistence, and continuity/run-state transitions behind the existing `LaunchRegistry` facade.
- Retained one SQLite connection, one transaction/failure-injection boundary and one public registry class. Replaced the former top-level class callback used by publication fingerprinting with the same pure alias-coalescing helper, shared by the facade mixin and fingerprint function.
- Initial focused runs exposed three omitted `@staticmethod` decorators at mechanical slice boundaries; restored them before acceptance. Every registry source is below 1,500 lines (largest: `launch_registry_contracts.py`, 1,166 lines after the shared helper).
- Verification: authoritative launch/continuity tests pass `53 passed, 1 skipped`; the single excluded POC-only case is the implementation-plan-obsolete optimizer/hash-seed subprocess matrix. R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `py_compile`, whitespace and diff checks pass.
- Next slice: inventory and split the remaining authoritative files above the hard limit by cohesive domain, starting with visit-schedule and safety/risk evaluators before projection/runtime support files.

## 2026-09-02 — B3 D07 safety evaluator decomposition

- Split the 4,551-line D07 evaluator into typed contracts plus mixins for integrity/admission, observation and trend evaluation, follow-up obligations, organ-pattern/priority/lifecycle resolution, output assembly and risk/source jumps behind the existing `D07SafetyEvaluator` class.
- Preserved the class-owned frozen trace orders and the public `evaluate_safety` entrypoint. The focused suite exposed one self-recursive class-name reference and one omitted helper at a slice boundary; both were restored without changing safety-domain rules.
- Every D07 evaluator source remains below 1,500 lines (largest extracted evaluator mixin: 1,180 lines; existing `d07_safety.py`: 1,330 lines).
- Verification: original D07 runtime, challenge, mutation, Query/Journey and replay suites pass `1418 passed`; R5/R7 product routes pass `100 passed`; adjacent medical-writing checks pass `127 passed`; `py_compile` and diff checks pass.
- Next slice: decompose visit-schedule evaluation while explicitly resolving its orchestration/evaluation/output helper cycle.

## 2026-09-02 — B3 visit-schedule evaluator decomposition

- Split the 4,674-line D05 authority into contracts, visit/activity assignment, expected-set expansion, result contracts, output helpers, unit evaluation and orchestration modules behind the existing `risks.visit_schedule_evaluator` facade.
- Resolved the former evaluation/output helper cycle by placing evidence construction with output helpers and making unit evaluation consume it explicitly. Preserved the historically imported private Query action helper through the facade.
- The first package-injected run exposed two missing private imports (`_action_suffix` and `_evidence_items`); both were restored without changing the D05 decision logic. Every D05 evaluator source is below the 1,500-line hard limit (largest: `visit_schedule_unit_evaluation.py`, 1,199 lines).
- Verification: original D05 slice, projection and challenge-matrix suites pass `173 passed`; the broader R5/R7 product surface passes `141 passed`; the protected medical-writing manifest/frontend adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass. A deliberately broader writing scan also observed two pre-existing translation-batch contract failures in the parallel subsystem; this slice did not touch or repair that protected surface.
- Next slice: split the remaining oversized monitoring authorities, starting with report mode output and graph store, while preserving report publication and graph transaction boundaries.

## 2026-09-02 — B3 mode-output report decomposition

- Split the 4,482-line R6 mode-output authority into a common ModeContract/Run-gate core, pre-lock payload authority, post-lock/pre-CFDI fixed-total payload authority and cross-mode envelope orchestration behind the existing `reports.mode_output` facade.
- Preserved the single ModeOutput identity/envelope, Query draft-only boundary, authority/cutoff/revision bindings and post-lock cross-output reconciliation. The common payload dispatcher retains call-time mode-specific resolution without creating an import cycle.
- Every mode-output source is below the 1,500-line hard limit (largest: `mode_output_core.py`, 1,428 lines). The facade eagerly retains all public and historical private symbols, including the two private helpers used by the original R6 suite.
- Verification: the behavior-bearing original mode-output suite passes `349 passed, 2 deselected`; the two deselected cases are the v2.0-obsolete POC whole-file SHA and create-only allowlist gates. R7 continuity/bridge/registry checks pass `66 passed, 1 skipped`; the broader R5/R7 product surface passes `141 passed`; the protected medical-writing adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `graph/store.py` around schema/serialization, immutable read projections and transaction-owned write operations while retaining one SQLite connection and transaction boundary.

## 2026-09-02 — B3 authoritative graph-store decomposition

- Split the 4,399-line SQLite authority into common schema/contracts plus mixins for base transaction and run state, manifests, capability work units, node/attempt journals, and artifacts/facts/domain objects/checkpoints/recovery behind one `graph.store.Store` class.
- The concrete Store still constructs exactly one SQLite connection and shares the same `_txn` implementation across every mixin. No second store, schema, transaction owner or publication pointer was introduced; `_RuntimeAttemptJournal` remains the narrow private mutation facade.
- Every store source is below the 1,500-line hard limit (largest: `store_base.py`, 1,016 lines). The facade preserves the original public domain imports and private schema-shape symbols required by compatibility checks.
- Verification: the complete R1 suite passes `326 passed, 1 skipped`; R7 schema/backup/verifier/continuity/progress/harness checks yield `244 passed, 1 skipped` plus one obsolete POC source-text assertion against the now-intentional `launch_schema` compatibility shim; the broader product surface passes `141 passed`; the protected medical-writing adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `risks/ip.py`, preserving exposure/accountability identity, deterministic evidence binding and Query/PD draft semantics without drug- or study-specific constants.

## 2026-09-02 — B3 D03 investigational-product decomposition

- Split the 4,128-line D03 authority into typed/source-derived inputs, temporal assignment and exposure-day resolution, risk identity/expected-set/result construction, plan/adherence evaluation, action/accountability evaluation, and slice orchestration behind the existing `risks.ip` facade.
- Preserved distinct exposure-day versus treatment-span semantics, fail-closed assignment binding, six independent control items, source-bound evidence, draft-only three-part Chinese Query wording and the rule that a suspected PD is never presented as confirmed.
- Every D03 source is below the 1,500-line hard limit (largest: `ip_types.py`, 1,172 lines). No drug, indication, study, threshold or listing-layout constant was introduced; those remain typed source-derived inputs.
- Verification: original D03 slice, projection, challenge-matrix and shared-domain suites pass `279 passed`; the broader product surface passes `141 passed`; the protected medical-writing adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `risks/visit_schedule.py` typed contracts and deterministic schedule primitives, then continue through remaining files above the hard limit.

## 2026-09-02 — B3 D05 visit-schedule domain decomposition

- Split the 3,939-line D05 domain authority into immutable plan/type contracts, actual-record and cutoff/bundle logic, assignment and typed-anchor binding, and gate/evaluation-unit/Journey value-object modules behind the existing `risks.visit_schedule` facade.
- Preserved the dual snapshot/cutoff boundary, stable identity versus lineage hashes, exact typed producer-anchor matching, closed gate accounting, and separate planned/actual/risk Journey marker schemas.
- Every D05 domain source is below the 1,500-line hard limit (largest: `visit_schedule_types.py`, 1,382 lines). The first focused run exposed one private regex group omitted from the extracted imports and the original late `ScheduleGate` lookup; both were restored without changing contract behavior.
- Verification: original D05 slice, projection and challenge-matrix suites pass `173 passed`; the broader product surface passes `141 passed`; the protected medical-writing adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/project_backup.py` or the next dependency-safe oversized authority, preserving archive validation and one restore transaction boundary.

## 2026-09-02 — B3 project backup and atomic-restore decomposition

- Split the 3,062-line project backup authority into the frozen contract/ledger support surface, shared manager and workspace-snapshot base, deterministic archive/preflight mixin, and atomic restore/rollback mixin behind the existing `runtime.project_backup.ProjectBackupManager` facade.
- The concrete manager still owns one operation ledger, one maintenance gate route and one live-workspace switch/rollback sequence. Archive format, manifest validation, project identity reconciliation, artifact-closure checks, idempotency behavior and Chinese result/error wording are unchanged.
- Every project-backup source is below the 1,500-line hard limit (largest: `project_backup_base.py`, 927 lines). Public aliases, helper entrypoints and historically visible module constants remain available from the facade.
- Verification: backup and adversarial archive/restore suites pass `80 passed`; project audit, schema migration, independent verifier, R5/R7 product routes and the protected medical-writing adjacent gate pass `344 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `projections/d10.py`, preserving D10 gate/result identity and user-facing projection semantics without adding study-specific rules.

## 2026-09-02 — B3 D10 renderer-neutral projection decomposition

- Split the 3,057-line D10 projection authority into audience/count core, projection identity and source-jump surfaces, native-Chinese Query drafting, change/center/trend/warning surfaces, and R2 handoff/project orchestration behind the existing `projections.d10` facade.
- Preserved the single authoritative D10 result binding, hidden-member/site suppression, separated count planes, high-risk hotspot visibility, one-hop source positioning, draft-only three-sentence Query, replay-stable R2 handoff, and renderer-neutral project projection. No study, drug, indication, threshold or listing-layout rule was added.
- The first complete run exposed four original forward lookups that crossed the new module boundaries; the facade now performs the same explicit late binding for risk markers, hotspots, deep links and Query drafts, while the shared measure-ledger identity helper lives with projection identity. Every D10 projection source is below the 1,500-line hard limit (largest: `d10_core.py`, 1,193 lines).
- Verification: original D10 adapter, mutation, projection, replay, runtime-closure, runtime-contract, verifier-probe and ensemble suites pass `245 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/migration.py`, retaining one migration ledger, resume/rollback semantics and schema-verification boundary.

## 2026-09-02 — B3 schema-migration coordinator decomposition

- Split the 3,043-line migration authority into immutable contracts and the root-ledger extension, workspace/database/artifact oracles, marker-last SQLite migration steps, coordinator setup/inspection, backup/staging/member execution, and atomic switch/recovery/rollback modules behind the existing `runtime.migration.MigrationRunner` facade.
- Retained one root migration ledger, the 09A backup-manager seam, maintenance-gate ownership, source fingerprint recheck, sibling staging workspace, marker-last per-member commits, restartable step digests, same-device directory switch and fail-closed rollback/triage behavior.
- Every migration source is below the 1,500-line hard limit (largest: `migration_contracts.py`, 912 lines). Public functional entrypoints, failure-hook matrix and historically visible internal schema/DDL bindings remain available through the facade.
- Verification: focused migration and continuity suites pass `54 passed, 1 skipped`; R1 authoritative-progress coverage passes `40 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass. A broader legacy scan still reports only the v2.0-obsolete launch-schema source-text assertion and optimizer/hash-seed subprocess gate; neither was refreshed or restored.
- Next slice: split `projections/publication/s4_contracts.py`, preserving publication-state orthogonality, Query draft-only semantics and audience-language isolation.

## 2026-09-02 — B3 S4 publication-contract decomposition

- Split the 2,714-line S4 contract authority into canonical/hash/grammar and frozen-vocabulary core, packet/audience/audit/history contracts, externally accepted authority-anchor contracts, and runtime input/build-state contracts behind the existing `publication.s4_contracts` facade.
- Restored the original deliberately closed `__all__` surface instead of exposing implementation helpers. Preserved the accepted-authority anchor as a separate input, six-node packet hash DAG, append-only history semantics, source-locatable/unavailable boundary, Query draft-only contract and distinct audience versus audit planes.
- The first complete run exposed the original forward lookup from `R5S4ModelEvidenceRef` to the later `S4SourceRevisionPair`; the facade now binds that exact type after module loading. Every S4 contract source is below the 1,500-line hard limit (largest: `s4_packet_contracts.py`, 1,186 lines).
- Verification: S4 contracts, authority builder, projection, validator, challenge matrix and publication authority pass `477 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `risks/cm.py`, preserving medication-episode identity, temporal overlap, protocol prohibition and suspected-PD Query semantics without medication-specific hardcoding.

## 2026-09-02 — B3 D02 concomitant-medication decomposition

- Split the 2,648-line D02 CM authority into medication/rule/episode contracts and stable identity, expected-set/interval/rule matching, result/Query/evidence/Journey helpers, unit/rule evaluation, and slice aggregation modules behind the existing `risks.cm` facade.
- Preserved compound ingredient-resolution units, versioned dictionary and protocol-rule inputs, exact/category/product-type rule granularity, temporal-window uncertainty, treatment-indication and AE/MH linkage checks, suspected-PD three-part Query wording, cross-domain evidence and episode rollups. No medication, disease, protocol or listing-layout rule was hardcoded.
- The first focused run exposed the original forward lookup from Query construction to record-field labels/value extraction; those presentation helpers now live with the Query builder. Every CM source is below the 1,500-line hard limit (largest: `cm_evaluation.py`, 1,027 lines).
- Verification: original CM slice, projection and challenge-matrix suites pass `194 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `risks/aemh.py`, preserving AE/MH candidate-versus-recorded separation, cross-domain evidence, temporal logic and Journey/Query contracts.

## 2026-09-02 — B3 D01 AE/MH risk-domain decomposition

- Split the 2,429-line D01 authority into semantic/protocol/medical types, protocol-boundary and partial-date evaluation, result/risk-identity construction, reported-event matching/Journey/Query helpers, and unit/slice orchestration behind the existing `risks.aemh` facade.
- Preserved the separation between recorded AE/MH source facts, evidence assertions and risk candidates; versioned concept-equivalence and temporal-tolerance inputs; source-stable R2 identity; NCS/alternative-diagnosis counterevidence; draft-only three-part Query wording; and distinct AE/MH/CM/IP/examination/hospitalization/procedure/symptom Journey categories. No study, drug, disease, threshold or listing-layout rule was added.
- The first focused runs exposed two extraction-boundary omissions: the `SemanticRecord` dataclass decorator and the shared normalized-concept helper import. Both were restored without changing evaluation behavior. Every AE/MH source is below the 1,500-line hard limit (largest: `aemh_types.py`, 804 lines).
- Verification: the original AE/MH slice passes `84 passed`; AE/MH plus lifecycle, protocol projection, shared-domain and CM cross-domain suites pass `372 passed`; R5/R7 product, mapping semantic-quality and protected medical-writing adjacent suites pass `440 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/background_recovery.py`, preserving one recovery ledger, worker ownership, resume/retry semantics and crash-consistent project state.

## 2026-09-02 — B3 background execution and recovery decomposition

- Split the 2,381-line background-recovery authority into a 1,106-line durable control/lease/progress support layer and a 1,349-line run-level adapter/worker layer. The existing `runtime.background_recovery` module remains the public adapter surface.
- Preserved the single SQLite control row, manifest-revision and generation CAS, lease/heartbeat recovery, at-least-once synthetic execution boundary, R1 idempotent callback authority, AI capability-attempt continuation/retry rules, maintenance gate and process-local thread registry. No second progress denominator, recovery ledger or worker authority was introduced.
- Verification: background recovery and harness integration pass `53 passed`; project lifecycle behavior passes `29 passed, 1 deselected`; R5/R7 product routes plus protected medical-writing adjacent checks pass `297 passed`; `py_compile` and `git diff --check` pass.
- A deliberately broader legacy scan reported only already-classified v2.0-obsolete optimizer/hash-seed subprocess probes, pinned-source/create-only checks and source-text facade inspection; they were not refreshed or restored.
- Next slice: split `projections/product_adapter.py`, preserving the single renderer-neutral product projection and all audience-language, source-jump and risk-count contracts.

## 2026-09-02 — B3 R5 product read-model decomposition

- Split the 2,282-line product projection authority into immutable authority/read-model contracts, explicitly isolated synthetic fixture builders, pure renderer-neutral projection helpers, and the three-surface product adapter/envelope facade.
- Preserved exact authority packet identity and hash rules, distinct event domains and visual encodings, subject-flow conservation and coverage states, source-jump bindings, independent risk/change/count planes, read-only response digest and the rule that synthetic data is available only through explicit fixture mode.
- The first focused run exposed one fixture dependency omitted at the extraction boundary (`canonical_sha256`); the import was restored without changing fixture or authority semantics. Every product projection source is below the 1,500-line hard limit (largest: `product_types.py`, 695 lines).
- Verification: R5 product adapter, subject-flow and route suites pass `49 passed`; the R7 product route suite passes `92 passed`; the protected medical-writing adjacent gate passes `156 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/project_verifier.py`, preserving independent read-only verification, closure evidence and fail-closed verdict boundaries.

## 2026-09-02 — B3 independent project-verifier decomposition

- Split the 2,280-line verification authority into canonical/read-only inspection and audit-bridge core, fixed-order project verification, accepted backup/migration recovery coordination, and the existing public facade.
- Preserved the independent verifier event pair, public R1 audit-chain reuse, stable workspace fingerprint, fixed source-to-run-to-publication-to-continuity order, minimal Chinese DTO, fail-closed anomaly/recovery distinction, and delegation of filesystem recovery to the accepted 09A/09B runners.
- The first focused run exposed two extraction-boundary omissions: `inspect_project_schema` in verification and recovery coordination, plus stale public aliases copied into the internal recovery module. These were corrected without changing verifier or recovery behavior. Every verifier source is below the 1,500-line hard limit (largest: `project_verifier_core.py`, 985 lines).
- Verification: the complete independent project-verifier suite passes `15 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- The old R8 parallel-release inventory tests still require a static file list that excludes the new internal modules. Stage B removes that parallel application and its release gate, so the obsolete inventory was not refreshed.
- Next slice: split `projections/publication/contracts.py`, preserving publication-state orthogonality, immutable receipts, accepted-snapshot authority and audience/audit separation.

## 2026-09-02 — B3 R5 publication-contract decomposition

- Split the 2,123-line exact publication contract into canonical constants/invariants, immutable typed objects, canonical registration/audience registries, and the existing `publication.contracts` public facade.
- Preserved the accepted-snapshot authority receipt, immutable content identities, publication-state orthogonality, deferred-leaf honesty, audience/audit separation, closed enums and deterministic canonical validation. The historical explicit `SourceRevisionContentPair` import remains available even though the original deliberately closed `__all__` omitted it.
- The first focused collection exposed that explicit import as a facade-only compatibility edge; it is now re-exported directly while `__all__` stays byte-for-byte equivalent in membership to the original contract surface. Every publication-contract source is below the 1,500-line hard limit (largest: `contracts_objects.py`, 1,060 lines).
- Verification: the live package facade compiles, all 95 declared public exports resolve, and the core contract/authority/S2 behavior run passes `291 passed` with one obsolete POC module-name assertion; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`. The old S2/S4 pinned-source/hash inventory reports expected drift and was not refreshed because stage B removes that static parallel-release gate.
- Next slice: split `domain/risk.py`, preserving stable risk identity, lifecycle state transitions, candidate/fact separation and source provenance without adding study-specific rules.

## 2026-09-02 — B3 risk lifecycle authority decomposition

- Split the 1,978-line R2 risk authority into a shared 578-line lifecycle vocabulary/semantic-validation/value-record module and a 1,425-line candidate/adjudication/instance/lifecycle authority module.
- Kept closure-only candidate, adjudication and risk-instance issuance together with the lifecycle service, so no public constructor token or second mutation authority was introduced. Preserved candidate-versus-established-risk separation, stable identity and lineage, complete-target adjudication binding, accepted-snapshot evidence, user-confirmation persistence, conservative severity inheritance and append-only transition-chain verification.
- The shared module contains only closed lifecycle/action vocabularies, transition legality, multilingual SAE/AESI negation-aware semantic helpers and immutable transition/evidence records. No study, drug, indication, score, threshold or listing-layout rule was added.
- Verification: original R2 risk authority passes `148 passed`; compatibility shims pass `4 passed`; R4 lifecycle plus AE/MH, CM, visit-schedule, protocol and shared-domain suites pass `538 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `reports/report_review.py`, preserving source-locatable external-report findings, candidate/fact separation, Chinese-native review wording and draft-only action semantics.

## 2026-09-02 — B3 external-report review decomposition

- Split the 1,947-line R6 report-review runtime into a 1,292-line immutable report-source/object construction surface and a 669-line coverage-accounting/full-review eligibility surface behind the existing `reports.report_review` import path.
- Preserved raw-byte content identity, report lineage and parent revision linkage, report-unit/claim/issue many-to-many identity, source-locatable evidence, distinct run versus report source revisions, accumulated blocking reasons and the two independent gates: accounting coverage closure versus full-report-reviewed eligibility.
- The coverage module reuses the source/object validators and canonical hashing rather than introducing a second identity or evidence framework. No external report statement is promoted to a monitoring fact, and no Query/PD send, close or user-confirmation action was added.
- Verification: report source/object/coverage behavior passes `60 passed`; report bundle and three-mode output behavior passes `409 passed` with one obsolete medical-writing file-count pin; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass. Old POC source hashes, create-only allowlists and aggregate file counts were not refreshed under stage B.
- Next slice: split `projections/publication/s2_contracts.py`, preserving frozen authority bindings, renderer-neutral projections and accepted-snapshot dual-baseline semantics.

## 2026-09-02 — B3 S2 authority-packet invariant decomposition

- Split the 1,913-line S2 authority-packet contract into a 992-line exact typed/canonical packet surface and a 939-line frozen cross-object invariant validator, with the existing `publication.s2_contracts` path retaining all 59 declared exports.
- Preserved nonrecursive packet identity, imported-object exact-key validation, immutable receipt/project/center/temporal/source/inspector bindings, accepted authority receipt linkage, exact-date/fallback-none source semantics, isolated worker evidence and all 21 fail-closed invariant codes. `R5S2AuthorityPacket.__post_init__` still invokes the one invariant validator after the packet types are loaded.
- No synthetic case identifier, study/drug/disease feature, filename convention or listing-layout branch was added. The invariant layer consumes the same typed packet and canonical helpers rather than creating a parallel authority.
- Verification: all 59 public exports resolve; S2 exact-contract and adversarial invariant behavior passes `75 passed`; the adjacent thin-slice suite is blocked only by its pre-existing obsolete frozen-source fixture (`37` setup errors) and was not repinned; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `projections/d09.py`, preserving risk lifecycle/publication-state separation, accepted-current-state authority and renderer-neutral audience projections.

## 2026-09-02 — B3 D09 audience-projection decomposition

- Split the 1,829-line D09 renderer-neutral projection into a 392-line Chinese audience-vocabulary/visibility core and a 1,460-line projection surface for counts, center-pattern risk markers, hotspots, source jumps, Query drafts and R2 handoff.
- Preserved evaluation-versus-projectable member separation, hidden-member suppression, non-summed count planes, high-priority hotspot visibility, verified one-hop source positioning, draft-only three-sentence Query, stable public risk identity and no-auto-close R2 handoff semantics. Risk lifecycle state, publication state and audience presentation state remain distinct.
- Audience language remains native Chinese and rejects internal/backend vocabulary; no project, study, disease, drug, threshold, case identifier or listing-layout branch was introduced.
- Verification: the complete D09 adapter, mutation, projection, replay, runtime-closure, runtime-contract and verifier-probe suites pass `243 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/project_audit.py`, preserving one append-only project audit chain, verification evidence and fail-closed continuity semantics.

## 2026-09-02 — B3 project-audit ledger decomposition

- Split the 1,625-line project audit runtime into a 600-line schema/vocabulary/canonical-validation support module and a 1,046-line single-ledger append/read/verify authority module.
- Preserved one root SQLite store, one CAS hash chain per canonical project, immutable event identity, replay-safe boundary events, principal/authorization hashes, atomic operation projection updates, append-only verification and fail-closed chain inspection. The concrete `ProjectAuditLedger` remains the only writer and owns its transaction boundary.
- Payload allowlists and forbidden nested content remain closed; the ledger stores opaque lifecycle references and digests rather than medical payloads, project files or user-facing report text.
- Verification: project-audit behavior passes `8 passed`; project verifier, assurance-principal route and SQLite runtime-store adjacency pass `82 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; `py_compile` and `git diff --check` pass.
- Next slice: split `runtime/capability.py`, retaining one capability attempt/state authority, provider-neutral contracts and exact retry/terminal semantics.

## 2026-09-02 — B3 capability runtime isolation decomposition

- Split the 1,603-line capability runtime into a 1,391-line provider-neutral attempt/runtime authority and a 250-line harness-isolation/vocabulary module.
- Preserved one capability-attempt lifecycle, canonical request hash, durable journal, exact retry and terminal semantics, frozen profile identity, API/harness neutrality and candidate-only clinical output boundary. No model-specific medical rule, study feature or listing-layout branch was added.
- The extraction exposed two direct dependencies (`_path_within` and `_SANDBOX_EXEC_PATH`) and a late-bound test/runtime identity edge. The main profile verifier now checks the current sandbox executable identity, and command construction receives that verified path explicitly, retaining the prior fail-closed behavior when the backend disappears after profile freeze.
- Verification: capability runtime, product capability guard and R7 harness runtime pass `90 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; both modules pass `py_compile`, and `git diff --check` passes.
- Next slice: split `projections/d07_journey.py`, preserving the chronological visit axis, typed event/risk markers, source jumps and renderer-neutral Chinese audience semantics.

## 2026-09-02 — B3 D07 journey audience-contract decomposition

- Split the 1,535-line D07 Journey projection into a 1,328-line chronological visit-axis/source-binding projection and a 205-line closed audience-schema/validation module, while keeping the existing `d07_journey` import surface compatible for R4 consumers.
- Preserved the shared visit/time spine, deterministic event ordering, typed event and risk markers, one-hop source jumps with reverse bindings, exact-key payload contracts, risk anchors, audience visibility gating and Chinese-native lexicon checks. Internal object names and candidate/fact terms remain blocked from audience labels.
- The split is renderer-neutral and adds no card-layout assumption, study/drug/disease feature, score threshold or listing-format branch; the later interactive Patient Journey remains free to render the same ordered projection as one horizontal visit axis.
- Verification: D07 Query/Journey, runtime-contract, mutation, replay, challenge-matrix and artifact-generator suites pass `1,543 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; all three D07 modules pass `py_compile`, and `git diff --check` passes.
- Next slice: split the slightly oversized `runtime/agent_harness.py`, preserving one model-routing and invocation authority and the configured provider-neutral harness contract.

## 2026-09-02 — B3 agent-harness audience vocabulary decomposition

- Reduced the 1,508-line agent harness authority to 1,489 lines by extracting its 19-line audience-safe progress vocabulary into a dependency-free module. Model alias resolution, layered profile freeze, catalog/preflight, invocation, receipt and completion authority remain together in the original adapter.
- Preserved provider-neutral invocation semantics, exact profile identity, no automatic fallback, durable receipt coverage and Chinese business-facing progress projection. The split does not expose provider/model/selector/attempt or transport terms to users and does not add medical inference logic.
- Verification: the live agent-harness behavior excluding obsolete static/optimizer gates passes `24 passed`; R7 harness-runtime and run-binding adjacency passes `58 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate passes `297 passed`; both modules pass `py_compile`, and `git diff --check` passes.
- The full historical R6 file reports 11 expected obsolete failures: nine isolated optimizer/hash-seed probes cannot import the post-consolidation `packages` authority from their frozen POC-only path, one frozen medical-writing file count is stale, and one create-only file allowlist is stale. These stage-B removal targets were recorded and not repinned.
- Next slice: split the final oversized `risks/d10_evaluator.py`, preserving the single D10 evaluation authority, candidate/fact separation and provider-independent evidence contracts.

## 2026-09-02 — B3 D10 result-contract decomposition

- Split the final 1,504-line D10 evaluator into a 1,412-line single evaluation/decision authority and a 99-line immutable result-record module, with all six result types still re-exported from `risks.d10_evaluator` for existing consumers.
- Preserved contract-ordered fail-closed gates, expected-set evaluation, exact numerator/denominator planes, change-cause derivation, visibility algebra, query redundancy, stable content identity and deterministic replay. Candidate evidence remains distinct from established facts, and result records add no mutation or publication authority.
- The result contract contains no study, indication, drug, score threshold, project identifier or listing-format branch; D10 evaluation continues to consume only closed typed inputs and the explicit evaluation authority.
- Verification: the complete D10 adapter, mutation, projection, replay, runtime-closure, runtime-contract, verifier-probe and artifact-generator suites pass `293 passed`; R5/R7 product routes plus the protected medical-writing adjacent gate pass `297 passed`; both D10 modules pass `py_compile`, and `git diff --check` passes.
- Authoritative Python inventory is now clear: no file under `packages/medical_monitoring` exceeds the 1,500-line hard limit; the largest is `risks/d08_evaluator.py` at 1,493 lines. Next action: close B3 acceptance with the consolidated behavior and protected-boundary evidence, then begin B4.

## 2026-09-02 — B3 full-scope acceptance

- B3 closes after 45 incremental commits: 152 authoritative Python files were moved or split by cohesive domain, and all 152 compile from the current consolidated package. The authoritative inventory has zero files above 1,500 lines; the largest is 1,493 lines.
- Public R7 route behavior and the protected medical-writing contract gate pass `297 passed`. Across the complete B3 diff, the only file under `services/api/app` is the monitoring-only `medical_monitoring_r7_product_router.py`; no medical-writing route or asset was changed.
- Every split was checked with its focused behavior/risk suite and recorded above. Frozen hash, optimizer, isolated-POC source-layout, file-count and create-only allowlist failures remain explicitly classified as B7 removal targets rather than refreshed acceptance gates.
- Updated the engineering spec with the reusable compatibility-facade rule and the prohibition on repinning obsolete POC layout gates. B3 acceptance criteria are satisfied; next active child is B4 frontend single-generation consolidation.

## 2026-09-02 — B4 pre-migration inventory and baseline

- Current product entry is `App.jsx -> r5/MedicalMonitoringR5Page.jsx`; that page already composes the R7 setup/progress/result/continuity runtime and the horizontal Journey drawer. The R5 overview also already carries the G6-equivalent subject-flow/Sankey, selection and drill-down behavior.
- `main.jsx` alone mounts the G6 synthetic page as a parallel root. Its standalone bundle/digest adapter and synthetic route belong to B5 replacement/removal, not the canonical product surface. Root-level monitoring components are the older App path; R5/R7 are the newer path that must be renamed and merged before those older components can be removed.
- Pre-migration JavaScript behavior baseline: `61` medical-monitoring test files pass; only the two G6 tests fail on the already-stale frozen bundle digest/render expectation that B4/B5 remove rather than refresh. Vite production build passes with 1,986 modules and the existing large-chunk advisory.
- Python frontend contracts pass `248 passed`; two source-text assertions are already stale before B4 (`clearMedicalMonitoringRouteState(window.location.search)` literal and an old RUX subject-switcher literal). They are behavior-migration debt and will be replaced by feature-boundary assertions rather than preserved as App source pins.
- B4 route: make the current R5+R7 product surface generation-neutral first, then extract App route/state ownership, and only then remove G6 and superseded root paths. Medical-writing code remains outside the edit boundary.


## Session 1: B4 canonical monitoring frontend entry

**Date**: 2026-09-02
**Task**: B4 canonical monitoring frontend entry
**Branch**: `main`

### Summary

Introduced generation-neutral application and route entry points without changing the current product behavior; removed tracked npm debug-log noise.

### Main Changes

- App now mounts MedicalMonitoringPage through monitoringProduct state and product route facades.
- Added focused canonical route and product-entry contract coverage; medical-writing paths remained untouched.
- Ignored frontend/.npm-cache and removed two previously tracked debug logs.

### Git Commits

| Hash | Message |
|------|---------|
| `031f1d9` | (see git log) |
| `d6c8575` | (see git log) |

### Testing

- [OK] Four focused medical-monitoring Node contract suites passed.
- [OK] Vite production build passed with 1988 transformed modules; only the pre-existing large-chunk warning remains.

### Status

[OK] **Completed**

### Next Steps

- Move the R5/R7 implementation into generation-neutral feature-root modules, update imports/tests, and then remove empty generation directories.


## Session 2: B4 canonical frontend surface

**Date**: 2026-09-02
**Task**: B4 canonical frontend surface
**Branch**: `main`

### Summary

完成医学监查前端目录与命名归一：R5/R7 实现移至单一 feature root，组件、状态、样式及可见错误文案去代际化；冻结线协议字段与后端传输路径保持不变。

### Main Changes

- 移除已跟踪 npm 缓存并保留本地忽略缓存。
- 建立单一产品入口，提升 workspace、进度、连续性与 Patient Journey 模块至 feature root。
- 将组件符号、CSS 选择器和展示名称改为产品职责命名，示范项目名称重绑定响应摘要。

### Git Commits

| Hash | Message |
|------|---------|
| `1f66f98` | (see git log) |
| `6faed01` | (see git log) |
| `375c1ab` | (see git log) |
| `912f88d` | (see git log) |
| `7d5f039` | (see git log) |

### Testing

- [OK] 医学监查 feature root 62 个 Node 测试套件全部通过。
- [OK] Vite 生产构建通过（1988 modules；仅保留既有大 chunk 警告）。
- [OK] services/api/app、medical-writing frontend 与 assets 无改动。

### Status

[OK] **Completed**

### Next Steps

- 抽离 App.jsx 中医学监查浏览器路由、项目隔离与渲染编排。

## 2026-09-02 — B7 integrated verification closure

- Resumed from the clean `deee6eb` checkpoint without repeating the committed classification or cleanup. The first integrated run exposed 114 setup errors from three Python source-text suites that still opened the B4-deleted `MedicalMonitoringSubjectViews.jsx`; the current 64 feature-root Node suites already exercise the replacement Journey, Profile, timeline, risk-workbench, project-isolation and fail-closed contracts. Removed those three obsolete generation-bound suites instead of restoring a superseded component.
- The same run found one live adjacent behavior regression: Safety/PV risk selection entered the consolidated monitoring home but dropped the exact risk identity. The product route now carries the current project, `risk_ref`, `risk_instance_ref` and a return-context key, so a senior medical monitor does not have to find the same risk again after cross-module navigation. The focused Safety/PV contract passes `9 passed`.
- Kept the independent D10 behavior verifier, but removed its contract/generator/artifact/verifier raw-file SHA and self-hash gates plus the test that required a fully self-consistent re-sign to fail only because an old digest changed. Schema identities, embedded content-hash self-consistency, authority/case comparison, closed fields, tamper rejection and independent outcome reconstruction remain; the complete D10 suite passes `102 passed`.
- Final verification: package/product/risk focused integration selection `859 passed`; all `64/64` medical-monitoring Node suites pass; Vite build passes with `1931` modules and only the existing large-chunk advisory; protected medical-writing manifest/frontend subset `127 passed`; current test tree collects `8022` tests when excluding the pre-existing protected `test_medical_writing_dynamic_section_matrix.py` import error. `git diff --check` passes, and no medical-writing route, frontend source or asset changed.
- Residual executable scans find no POC/deleted-deploy imports, optimizer/hash-seed subprocess matrix, D10 raw source/artifact pin, or forbidden generated recovery/acceptance record. B7 is complete. Next task is B8 product-native synthetic startup, ego(lite) wide-screen smoke and independent Phase-B review; no real project source is used in B8.

## 2026-09-02 — B8 product-native synthetic smoke implementation

- Closed the product loop for explicit `--synthetic` mode: completed runs now publish through the existing R5/R6 authority and mode-output contracts, the frontend automatically requests publication once analysis completes, and an unpublished completed run no longer traps the workbar. Empty S4 membership remains accepted only for the explicit synthetic R5 packet; real/non-synthetic publication still fails closed.
- Rebound the R7 setup fixture to the accepted R5 synthetic identity and added one synthetic authority/output provider. All three modes now build their four contract-defined outputs; pre-lock retains project/site/subject checks and post-lock retains fixed-total, material and checklist identity instead of relaxing the output contract.
- Corrected the public center projection: coverage inherits from the referenced measure, center counts derive from the center's accepted risks, and synthetic site tokens render as native `中心 6/10` labels. No medical conclusion, candidate/fact boundary or publication authority was moved into the browser.
- Product startup now exposes an exact `npm run dev:monitoring-synthetic` frontend command bound to backend 8911. Ego(lite) at 1600×1000 completed a new daily run, observed 12/12 work items and automatic publication, then opened project risk, center risk and Patient Journey. Evidence is under `.trellis/workspace/screenshots/b8/`; no real-project source was opened.
- Verification: `115 passed` for synthetic fixture/publication plus R5/R7 product routes; all `62` feature-root Node suites pass; Vite production build passes with 1,931 modules and the existing large-chunk advisory; changed Python modules compile and `git diff --check` passes. The protected medical-writing adjacent selection reports `127 passed, 2 failed`; both failures are pre-existing translation-batch source-text assertions, and no medical-writing route, frontend source or asset is in this diff.
- B8 remains in progress pending fresh-context independent review and explicit user confirmation. Do not create `mm-consolidated` until that confirmation.

## 2026-09-02 — B8 independent review remediation and confirmation gate

- Fresh-context visual review completed with `pi/google-antigravity/gemini-3.7-flash:high` and `pi/cms-router/minimax-m3:high`. Both independently found the user-visible synthetic center identifiers; MiniMax also found that the synthetic profile was not reachable from the ordinary project selector. Findings about authentication/authorization were excluded from remediation because the current task explicitly excludes security design and testing. The requested native `zcode/glm-5.3-flash:max` pass produced no review result after repeated account-level provider rate-limit failures; it was stopped without substituting or mislabeling another model.
- Remediation keeps the real-project manifest boundary unchanged while exposing one monitoring-only project entry in explicit synthetic mode. Selecting it from the ordinary project selector and clicking `医学监查` now opens the canonical project risk overview. Regular startup still exposes no synthetic project.
- Removed remaining internal center identifiers from the result scope strip and refreshed the 1600×1000 project and Patient Journey evidence. The shared visit axis now reserves label clearance inside its existing minimum width; ego(lite) confirmed both endpoint visit labels remain fully visible in the default wide-screen viewport.
- Final verification: synthetic/publication and R5/R7 focused regression `133 passed`; all `62` medical-monitoring frontend Node suites passed; Vite production build passed with 1,931 modules and the existing large-chunk advisory; changed Python modules compiled and `git diff --check` passed. The final diff contains no medical-writing route, source, asset or new `context/` record.
- B8 implementation and remediation are ready for user confirmation. Keep task `09-01-mm-b8-smoke-review` in progress and do not create tag `mm-consolidated` until explicit confirmation. After confirmation, archive B8, tag the confirmed Phase-B state, complete the Phase-B retrospective and begin Phase C from the implementation plan.

## 2026-09-02 — Phase C pre-start plan under the B8 confirmation gate

- Re-read the current global `AGENTS.md` and implementation plan v2.0. Phase B still requires user confirmation before `mm-consolidated`; therefore no Phase C product code, service, real-project read or project-source mutation started.
- Refined the existing Phase C Trellis task into five bounded slices: deterministic admission contract, user-facing admission wizard, one-project fact-location pilot, four-project rollout, then dual-snapshot/anti-overfit/stage review. The plan now treats the lazy, visually/data/risk-sensitive medical monitor as the primary operator and keeps internal object names in technical details only.
- Current code reconnaissance confirms reusable authorities already exist for `SourceRevision`, `ListingSnapshot`, snapshot content storage, normalization, mapping/fact identities and read-only project inspection. The first implementation slice should close only the real-file isolated-copy and structure-profile product gaps instead of creating a second importer or parallel application.
- Next safe action remains explicit user confirmation of Phase B. On confirmation: archive B8, create `mm-consolidated`, move Phase C from `planning` to `in_progress`, then execute C1 without starting the other four projects.

## 2026-09-02 — Phase B confirmed and retrospective closed

- The user explicitly confirmed Phase B after reviewing the B8 checkpoint. The stage evidence remains: single authoritative backend package and frontend generation, deleted duplicate POC/deploy trees, product-native synthetic profile, 133 focused Python checks, all 62 medical-monitoring frontend suites, Vite build, 1600×1000 ego(lite) project/center/subject/progress smoke, and fresh-context visual review remediation. No unresolved P0/P1 user-facing finding remains.
- User-view retrospective: consolidation now gives one obvious medical-monitoring entry, project/center/subject risk navigation, a readable visit-axis Patient Journey and no exposed internal center tokens. The remaining limitation is deliberate: synthetic evidence proves the product loop, not real listing interpretation, fact provenance or clinical usability.
- Engineering retrospective: migration preserved candidate/fact and publication boundaries while removing parallel authorities. The highest-risk Phase C transition is no longer architecture consolidation; it is preventing real source mutation, preserving exact cell locators and resisting project-specific parser or prompt branches.
- Phase C starts with one deterministic admission contract and generated files only. It will not open all five projects at once: first close isolated-copy/hash/profile/locator behavior, then add the user-facing wizard, then pilot one real project before the other four.

## 2026-09-02 — Phase C started

- Archived B8, the remaining completed B2 task and the Phase B parent after user confirmation. Tag `mm-consolidated` points to the confirmed Phase B retrospective commit.
- Validated the Phase C PRD, technical design, implementation plan and Trellis context manifests, then moved `09-01-mm-phase-c-real-data` from `planning` to `in_progress`.
- Active implementation unit is C1 only: deterministic isolated-copy admission using generated non-real files, existing source/snapshot/store authorities and exact cell locators. No service, browser, model or real project starts until this contract is implemented and committed.

## 2026-09-02 — Phase C C1 deterministic admission contract

- Added one product-bound admission path for generated CSV/XLSX fixtures: stream-hashed isolated staging, atomic completion, deterministic structure profiles, per-table full snapshots and exact source-cell locator indexes. The existing `SourceRevision`, `ListingSnapshot` and `Store` remain authoritative; no parallel importer, application or database authority was introduced.
- Relaxed the former synthetic-only Store guard only where provenance is explicit. A real snapshot must belong to a real project, a synthetic snapshot must belong to a synthetic project, and an existing synthetic project identity rejects real-data admission instead of being silently converted. Re-admission of identical bytes reuses revision/snapshot identity while creating a distinct attempt.
- Added project-scoped create/status/profile endpoints and bound the default parser-backed pipeline in the existing R7 monitoring mount. Public summaries answer file/table/row/column/possible-key questions in Chinese; paths, hashes and internal identities remain under technical details. Admission produces candidates and source evidence only, never canonical medical facts.
- Verification used generated non-real fixtures only: C1 focused suite `44 passed`; source-revision/compatibility/module contracts `112 passed`; R7 product/synthetic-startup regression `93 passed`; protected medical-writing backend `12 passed`; implementation modules compiled and `git diff --check` passed. Shared-kernel scans found no named real project, drug, disease or indication constants. No service, browser, model or real-project source was started or opened.
- Governed three-worker execution completed on the declared GLM route and passed Codex review; its temporary prompts/logs/reports were archived and untracked process records were removed. C1 is ready to commit. Next safe unit is C2 only: add the concise three-step Chinese admission wizard, keep technical detail collapsed, verify frontend tests/build, then use ego(lite) at 1600 px before any real project pilot.

## 2026-09-02 — Phase C C2 admission wizard accepted

- Added one inline three-step Chinese data-admission wizard on the existing monitoring start surface: 选择数据 → 查看系统识别结果 → 核对系统识别. The default interaction is a browser-native folder picker; manual directory entry is retained only as a collapsed fallback. The browser streams selected files to the existing C1 admission pipeline, which applies the same isolated copy, hash, profile and Store authority before deleting the short-lived upload intake.
- User-facing projection remains summary-first. Table/row/column summaries and possible data meanings are visible; paths, hashes and internal identities remain inside collapsed technical details. Completion still creates source/profile candidates only and explicitly states that no monitoring analysis occurs before later field mapping confirmation.
- Visual review found the original path-first interaction too technical. Codex replaced it with the folder picker, renamed step 3, added a selected-folder/file-count summary, made the disabled import action visually quiet with an explicit next-step hint, and removed engineering language from the演示项目 refusal. Requests to expose unconfigured real projects or make the synthetic project accept real data were deferred to C3 because they would cross the staged identity boundary. Pre-existing 医学监查首页 routing and start-run overlay stacking remain adjacent backlog, not C2 changes.
- Verification used generated non-real files only: focused Python admission `46 passed`; frontend API/state/render/integration `89/71/89/42`; adjacent Python/source/protected-writing selection `333 passed`; product-loop/continuity `39/94`; all feature-root medical-monitoring Node suites and the Vite production build pass, with only the existing large-chunk advisory. ego(lite) at 1600×1000 verified the final picker, collapsed fallback, selected-folder summary, disabled state, upload request and native-Chinese synthetic boundary. 8911 and 5174 were stopped after acceptance.
- The governed execution audit, review gates and visual conference validation passed. Temporary C2 context/plan/review/metrics/prompt/run/log files were removed after their gates; guard-managed execution evidence remains archived. No real project source was opened, no medical-writing file changed, and no new progress/recovery record was added under `context/`.
- Phase C remains `in_progress`. Next safe unit is C3 only: identify one first real project and its isolated output root read-only, record a non-sensitive inventory, copy one listing batch into isolation, generate its profile, then pause for the user's critical mapping confirmation before creating facts or running any medical risk model.

## 2026-09-02 — Phase C C3 first-project profile and mapping bridge checkpoint

- Admitted the first authority-ordered project, MG-K10-SAR, from its read-only listing into the project-scoped isolated runtime. The accepted attempt contains 1 file, 62 non-empty tables, 148,788 rows and 1,495 fields; source bytes and metadata remained unchanged. No other real project was opened.
- Added a thin C1-profile adapter into the existing `MonitoringAiService` field-mapping candidate repository instead of introducing a second mapper. The bridge preserves 62 distinct table/snapshot bindings, sends bounded field statistics only, redacts 203 subject-identifier fields before model submission, and exposes no confirmation or fact-materialization method.
- Rejected the first delegated prototype because it called deterministic metadata rules while presenting the result as harness output, bound all tables to the first snapshot and retained identifier samples. Independent review identified the multi-table defect; the corrected generated two-sheet regression proves distinct snapshot identities and pre-model redaction.
- The product route can start/read field suggestions, but submission now fails closed before transmitting data unless the active runtime is exactly `zhipu-coding-plan/GLM-5.3-flash`. Live inspection shows the current shared independent-AI binding is still `deepseek/deepseek-v4-flash`; therefore no real model job was created and no DeepSeek substitution was allowed. DeepSeek remains supported by the existing adapter for a future explicit configuration, not as an automatic fallback.
- Verification: C3/C1 focused selection `31 passed`; complete MonitoringAiService suite `451 passed`; R7 product/AI route/candidate-audit selection `141 passed`; changed modules compile and `git diff --check` passes. The real isolated profile reshapes deterministically to 62 unique snapshots and 1,495 fields without emitting row content.
- C3 remains in progress at a safe configuration gate. Next action: configure and verify a product-owned direct GLM profile at high reasoning, then start only the candidate jobs for this admitted attempt. After completion, present only critical ambiguous mappings for user confirmation; do not create canonical facts or run medical risk logic beforehand.

## 2026-09-02 — Phase C C3 direct GLM mapping candidates ready

- Added a product-owned `medical_monitoring_ai` role so the medical-monitoring harness defaults to direct `zhipu-coding-plan/glm-5.3-flash` at high reasoning without changing the shared comprehensive-AI/medical-writing binding. DeepSeek V4 Flash remains an explicit supported profile; credentials stay in the local encrypted runtime store and are not versioned.
- Added the exact Coding Plan endpoint/preset and a single mapping gate contract. Corrected the C1 admission revision resolver so immutable accepted admission profiles are revalidated from their isolated workspace instead of being looked up as legacy monitoring batches. The original source was not rewritten.
- The no-data connectivity probe passed with exact response-model identity. The isolated MG-K10-SAR mapping run then completed all 151 chunks after four contract-invalid outputs passed one explicit retry; response identities were only `glm-5.3-flash` plus the deterministic metadata mapper. The result contains 1,495 evidence-bound field candidates, all still pending confirmation. No canonical facts or medical risk logic ran.
- An initial cross-runtime-root trial created 151 non-current records in the default runtime; all were marked `stale_input` by exact business-key prefix, with no deletion. The accepted 151/151 completed run exists only in the C3 isolated runtime. Port 8911 remained stopped.
- Verification: focused role/C3/MonitoringAiService gate `492 passed`; product router and protected medical-writing adjacent gate `99 passed`; changed Python modules compile and `git diff --check` passes. Next safe slice is the product-native critical-mapping review/confirmation UI and durable draft adoption; facts remain blocked until user confirmation.

## 2026-09-02 — Phase C C3 mapping confirmation interface ready

- Added the product-native critical-first mapping review on the existing admission wizard. It shows original table/field, aggregate non-empty/type evidence and specific Chinese review advice; raw sample values and technical role values stay out of the default list. Medical monitors can switch between critical/all suggestions, filter by table, search, edit one field in a side panel and provide a ten-character overall confirmation note.
- Reused the durable mapping-draft repository for adopt/edit/confirm. Candidate adoption creates only an editable draft; confirmation creates only a mapping revision. Neither action creates canonical facts, activates monitoring capabilities or runs medical risk logic. Draft and edit requests are bound to the exact C3 attempt.
- Confirmation now fails closed for semantic blockers and for any blank Chinese `user_action`. Incomplete advice is marked `建议不完整`, remains visible in the critical list, disables the UI action and returns an actionable 422 Chinese API error if the frontend is bypassed. Empty critical views cannot trigger blind adoption.
- Codex inspected the wide-screen ego(lite) fixture states and completed a same-session independent visual review. All previous P1 findings were closed: 1600px list/editor layout, visible blocker, generating/empty/completion copy, candidate/fact separation, raw-sample hiding and incomplete-advice gating. This was an isolated fixture review, not live real-project confirmation.
- Final verification: backend C3/product/repository selection `713 passed`; frontend mapping state/API/render checks and Vite production build passed (existing large-chunk advisory only); protected medical-writing `14 + 7 passed`; compile, diff, anti-overfit and protected-path scans passed. Port 8911 remained stopped.
- C3 remains `in_progress`. The isolated real run still has 1,495 pending field candidates; no draft was adopted and no facts were generated in this slice. Next safe action requires the user to review and confirm the critical mappings through the product interface before any deterministic fact materialization is implemented or run.

## 2026-09-02 — Phase C C3 read-only confirmation readiness audit

- Re-opened the authoritative C3 runtime read-only after commit `3454300`. The accepted attempt still has 151/151 completed mapping jobs and 151 proposed candidate records: 147 direct `zhipu-coding-plan/glm-5.3-flash` jobs plus 4 deterministic metadata jobs. No provider substitution appeared.
- Aggregated the candidate JSON without printing row/sample values. The 1,495 field mappings contain 507 attention items across all 62 domains: 407 low-confidence, 97 unmapped and 3 medication-boundary items. All 1,495 candidates contain non-empty Chinese `user_action`; the public mapping projection contains no raw `sample_values`.
- The authoritative repositories still contain zero mapping drafts, zero confirmed mapping revisions, zero active project mapping state, zero canonical facts and zero monitoring runs for this isolated pilot. The original source was not opened or written during this audit.
- Confirmed the only product route is the existing workbench: stable backend script on 8911, stable frontend on 5174, project selector → `医学监查` → `数据接入` → critical mapping review. No parallel application or C3-only launcher is needed. Both ports remained stopped.
- Decision: no further code or fact generation is safe before the user performs the explicit mapping-confirmation step. When authorized, start the stable workbench, open `proj_mgk10_sar_real`, let the user review the 507 attention items, and only after confirmed revision evidence exists implement/run deterministic fact materialization and locator spot checks.

## 2026-09-02 — Phase C C3 live confirmation handoff repaired

- Reopened the existing stable workbench against the C3 isolated runtime and found four live-product blockers that the read-only route audit had not exposed: the stable backend launcher had drifted to an incompatible host Python, the local single-user product lacked its server-owned OS user/device principal, real admitted projects were still offered synthetic run setup, and the admission wizard could not resume the accepted C3 attempt.
- Kept one product and one runtime authority. The launcher now uses the repository virtual environment and enables the explicit local single-user host profile; the principal is derived server-side from OS user/device plus the server project catalog, never from browser input. Real admitted projects fail closed with `run_data_not_ready`, return no synthetic run history and expose the existing data-admission workflow instead of synthetic baselines.
- Added a newest-attempt read route and wizard resume path. Live ego(lite) at 1600×1000 now reaches the accepted MG-K10-SAR attempt through the ordinary product route and shows 1 file, 62 tables, 148,788 rows, 1,495 field suggestions and 507 attention items. Raw samples remain hidden by default. The user action is still pending at the enabled `采用建议并进入修订` boundary; no draft, confirmed revision, canonical fact or risk run was created.
- During diagnosis, one call to the legacy parent-runtime workspace bootstrap created empty execution-profile, run-binding and risk-rule SQLite files under the real-project runtime directory. They contain no mapping/fact/run output and were preserved because deletion requires explicit user confirmation. The live review uses the same stable application with `WORKBENCH_RUNTIME_DIR` pointed at the existing C3 isolated runtime; no parallel application was introduced.
- Verification: focused backend admission/product/principal/synthetic selection `127 passed`; protected medical-writing regression `127 passed`; all medical-monitoring frontend Node suites passed after updating the continuity integration contract for the admission-only state; Vite production build passed with the existing large-chunk advisory. Changed Python modules compile and `git diff --check` passes.
- Phase C remains `in_progress` at C3. Next safe action is the user's review and explicit confirmation of the 507 attention items. Only after durable confirmed-revision evidence exists may C3 proceed to deterministic fact materialization and source-locator spot checks.

## 2026-09-03 — Phase C C3 harness-led semantic triage and low-burden review

- Replaced the 507-item engineering review burden with a harness-owned semantic triage contract. Each mapping chunk now receives bounded full-column statistics, original column order, desensitized representative same-row neighbours, the rest of the same table and same-named fields from other tables. The independent model must decide whether ambiguity is medically substantive and would change downstream analysis; low confidence, missing enum/CRF labels or incomplete advice alone no longer creates user work.
- The direct runtime policy remains product-owned: default `zhipu-coding-plan/glm-5.3-flash` at high reasoning, direct `cms-router/minimax-m3` supported as the remote alternate, and local `mtplx/mtplx-flash-next-optimized-speed` admitted only when the runtime explicitly records both remote routes unavailable. No OMP wrapper was introduced.
- The accepted v18 real-project cohort completed `151/151` jobs and covers all `1,495` fields. After system normalization of repeated export context, the durable draft `monmapdraft_743f77b9a144a1010a66df0e78e2` is version 69: `1,483` fields are system-owned and `12` medically consequential ambiguities remain across 10 tables. Historical v16/v17 cohorts remain auditable as `stale_input` and no longer distort current UI status.
- The user-facing review now shows one concrete Chinese question at a time, collapses table summaries and technical evidence, and uses the plain actions `系统判断正确` / `实际情况不同`. The real 1600×1000 ego(lite) DOM session verified the `1,495 / 12` summary and one-card flow. Browser screenshot capture repeatedly timed out in the active ego environment, so no fresh screenshot is claimed; stale C3 screenshots and temporary execution packet files were moved recoverably to `/Users/smkzw/.Trash/mm-c3-cleanup-20260903-0154`.
- Candidate/fact separation remains closed: there is no confirmed mapping revision, active mapping state, canonical fact or monitoring run. The original MG-K10-SAR Excel file was not modified. The system-only decision flag is repository-enforced and covered by a focused test, so a normal user edit cannot silently bypass an unresolved question.
- Verification: focused backend mapping/admission regression `639 passed` with 18 existing FastAPI deprecation warnings; all `80` medical-monitoring Node suites passed; Vite production build passed with 1,936 modules and only the existing large-chunk advisory; changed Python modules compiled; `git diff --check` and protected medical-writing path scan passed. The governed three-worker audit returned `ok: true`, followed by Codex source/runtime review and guard-managed cleanup.
- C3 remains `in_progress`. The next safe slice is a second-pass system clarification for the remaining 12 questions where evidence permits, then user review only for residual medically material ambiguity. Deterministic facts and locator spot checks remain blocked until a confirmed mapping revision exists; do not expand to the other real projects yet.

## 2026-09-03 — Phase C C3 independent second-pass clarification

- Added a focused second-pass adjudication path inside the existing medical-monitoring harness. It reuses the current AI job, candidate and mapping-draft authorities, submits only unresolved fields with bounded same-table/cross-table context, and permits at most two generations. No second mapper, database or task type was introduced.
- The system may clear a question only when the independent result keeps the first-pass role and field kind, supplies a non-question rationale and explicitly says user confirmation is unnecessary. Saved user answers always win. Malformed output remains a question, and both the product route and the legacy confirmation route now share a repository-level unanswered-question gate.
- The real MG-K10-SAR draft completed 19 direct `zhipu-coding-plan/glm-5.3-flash` jobs across two focused generations. Four of the original 12 questions were resolved from available context; eight medically material ambiguities remain across seven tables. Draft version is 73, mapping revisions remain zero, and no fact or monitoring run was created.
- Real ego(lite) use verified the low-burden flow: the system hides questions while it is deciding, then shows `1,495 / 8`, reports the system-completed items, and presents one residual Chinese question at a time with `系统判断正确` / `实际情况不同`. The live semantic interaction passed; screenshot capture timed out, so no screenshot acceptance is claimed.
- Verification: focused backend selection `676 passed`; all `81` medical-monitoring frontend Node test files passed; Vite production build passed with the existing large-chunk advisory; `git diff --check` passed. The original Excel remained untouched and 8911 is stopped after acceptance.
- C3 remains `in_progress`. The next safe action is user review of only the eight residual questions. Deterministic fact materialization and source-locator checks remain blocked until a confirmed mapping revision exists; no other real project should be opened yet.

## 2026-09-03 — Phase C C3 source-label inference and zero-question confirmation

- Root cause of the eight residual questions was a lost-evidence seam: the parser normalized full listing headers to stable field codes, but the original column labels did not survive into the frozen admission profile and model context. Added one generic `source_label` evidence field from parser → admission profile → bridge → direct harness prompt. Stable `source_field` codes remain the only identity and join key; labels cannot replace them or become a new parser/authority.
- Bumped the listing mapping prompt to v19 and focused adjudication prompt to v2. The prompt now requires the model to use the original label together with column values, same-row neighbours and full-table context, while retaining medically substantive ambiguity. Input validation rejects blank or overlong labels, and the closed role catalog accepts the project-neutral form-record metadata role without encoding any study, drug, disease or risk rule.
- Re-admitted only the isolated MG-K10-SAR copy as attempt `stg-a2e9dbf627534036b74e2907796d5fd1`: 1 file, 62 tables, 148,788 rows and 1,495 fields. All 151 direct `zhipu-coding-plan/glm-5.3-flash` jobs completed; two malformed responses were recovered through the existing same-route terminal retry. The harness produced 1,495 candidates, zero user questions and 1,495 system-adopted mappings. No alternate provider or local fallback ran.
- Draft `monmapdraft_06dfa20952806c007760a49eb74b` passed semantic quality with no global blocker and was automatically confirmed by `system_harness` as revision `monmaprev_47f018f9f7beede686eb40fcf021`. Five evidence-bound capability restrictions remain intentionally closed (study-drug action, treatment identity, date precision, laboratory lineage and scale lineage); they are downstream evidence limits, not questions for the user. There is still no active mapping state, canonical fact or monitoring run.
- Real ego(lite) use at 1712×947 found and repaired a confirmed-draft resume conflict. The ordinary project route now shows `字段对应已确认`, `1 个文件 · 62 张数据表 · 148788 行数据`, and `下一步：生成可用于监查的数据`, with no duplicate confirmation cards or engineering conflict. Semantic interaction passed; screenshot capture timed out, so no screenshot acceptance is claimed.
- Verification on the final source: broad selected backend regression `1001 passed` with 135 existing warnings; focused frontend state/render suites passed; Vite production build passed with 1,936 modules and the existing large-chunk advisory; changed Python modules compile and `git diff --check` passes. Protected medical-writing paths were not changed. The original workbook hash remained `81f47614ca6ab96c3d0a3e45d72ec49c98690fb49e8b574b1dc6b06f7e8259e3`, identical to the isolated copy after use.
- C3 remains `in_progress`. The next safe slice is deterministic canonical-fact materialization from confirmed revision `monmaprev_47f018f9f7beede686eb40fcf021`, followed by source-locator spot checks and focused/adjacent regression. Do not open another real project until this slice is independently reviewed; keep 8911 stopped between active checks.

## 2026-09-03 — Phase C C3 deterministic canonical facts materialized

- Added one deterministic fact-materialization service and two thin product endpoints. They reuse the accepted Store snapshots, confirmed mapping revision, existing value normalization and exact source-cell locator indexes; no new database, run authority, parser branch or project-specific rule was introduced. Fact bundles are split per snapshot and stored as content-addressed stdlib-gzip artifacts, while SQLite retains only compact manifests and readiness summaries.
- The user flow is automatic after mapping confirmation. It says the system is generating monitoring-ready data without asking for another review, resumes after refresh, and ends with one plain action, `进入医学监查`. Failed generation states say the original file is unchanged. Setup/run readiness now depends on verified fact artifacts instead of a directory-presence shortcut.
- The isolated MG-K10-SAR attempt produced 62 fact sets over 148,788 rows and 3,950,557 mapped values. The service explicitly recorded 63,473 unmapped values and zero derived values as skipped rather than guessing. All 62 snapshots reached `baseline_eligible`; no other real project was opened and the original workbook was not modified.
- Reopened and digest-checked every compressed fact set. Across all 62 tables, 555 deterministic first/middle/last cell checks resolved through the stored locator to the exact snapshot raw value. Idempotent ready replay completed in about 0.161 seconds. The retained pre-run SQLite backup is no longer needed for recovery and will be moved to Trash rather than deleted.
- Final verification: selected Python regression `154 passed` with 117 existing FastAPI deprecation warnings; frontend admission state/render/integration/API checks `73/128/42/98 passed`; Vite production build passed with the existing large-chunk advisory; `git diff --check` and protected medical-writing path scans passed.
- ego(lite) reviewed the actual admission component at 1280px with real project counts. The generating and ready states were plain Chinese, the ready state had one enabled action, and no horizontal overflow was present. Screenshot capture timed out twice, so no screenshot evidence is claimed. Port 8911 was stopped immediately after testing; the pre-existing user-owned Vite process was left untouched.
- Three governed read-only worker reports were reviewed by Codex. The direct source/runtime review and Ponytail review found the final implementation lean and evidence-bound. C3 remains `in_progress`; the next safe unit is downstream Phase C activation/review planning from these verified fact sets, still limited to the first isolated project until its product behavior is independently accepted.

## 2026-09-03 — Phase C C3 RUX admission and mapping safe pause

- Started the second Phase C project in the design-authority order, `proj_rux_03_002`. The registered monitoring source is the single file under `Ruxolitinib-AD/CFDI Inspection/准备阶段`; its source and isolated-copy SHA-256 both remain `b68d53feb7cd4501d5fae876a0053db2843597eed216b76203c2c9ea6daea343`. Historical processed monitoring attachments were not treated as compatible incremental snapshots.
- Deterministic admission `stg-8fbe3eef8c5c423196b96dbf66b31a86` is `profile_ready`: 1 file, 54 tables, 180,793 rows and 1,257 fields. The isolated Store contains 54 snapshots and 54 locator indexes covering 4,454,117 cells, all bound to the RUX project and the registered source digest. No other real project was opened or changed.
- The second project exposed two generic seams and both were fixed before model completion: malformed model questions can no longer be silently demoted to system-owned decisions (`1bc638f`), and header-only tables now enter the mapping bridge as zero-observation evidence that must remain unmapped rather than being rejected (`efb4109`). Focused regression passed (`2`, `49` and `17` selected tests across the two fixes and admission baseline).
- The existing direct harness ran only `zhipu-coding-plan/glm-5.3-flash` plus deterministic metadata mapping. All 129 jobs reached `completed`; three initial `invalid_ai_output` jobs completed after one explicit same-input/same-model retry. The cohort now contains all 1,257 field candidates: 612 source-collected, 599 source-metadata and 46 unmapped, with three medically material questions flagged for the later system-owned second pass.
- User-requested lossless pause was applied immediately after the active mapping process completed. No mapping draft, confirmed revision, project mapping state, canonical fact or monitoring run was created. Port 8911 is stopped. The original RUX source remained unchanged.
- Next safe action after resume: reopen the same attempt and candidate cohort; automatically assemble the draft and run the existing focused adjudication for the three flagged questions. Ask the user only if medically material ambiguity remains after the harness pass. Only after zero unresolved questions may the system confirm the mapping, materialize facts and run exact locator checks. Do not resubmit the 129 completed first-pass jobs and do not start a third real project yet.

## 2026-09-03 — Phase C dual-model first-listing review contract, P0 route slice

- A fresh independent `gpt-5.6-sol:high` read-only review confirmed that the existing focused adjudication is not a full dual-model review: it sees only model-flagged questions, cannot correct a first-pass mapping, and does not freeze separate main/verifier identities. The RUX 129-job GLM cohort is therefore retained only as a legacy baseline and is barred from representing the new workflow.
- Reversed the product-owned default as explicitly requested: direct `cms-smk/MiniMax-M3` is now the first-listing primary analyzer; `zhipu-coding-plan/glm-5.3-flash` has a distinct verifier contract and profile; the local MTPLX route remains fallback-only. The primary gate no longer accepts GLM as an interchangeable route. No OMP wrapper was added.
- The approved architecture is independent conclusions plus evidence reconciliation, not voting. MiniMax and GLM must each cover the frozen workbook field manifest; GLM's first verdict must be blind to MiniMax output. CTCAE grading, IB-informed risk interpretation, AE/MH/CM/IP/PD findings and Query generation remain downstream of confirmed mapping and canonical facts.
- Reuse decisions: keep the current listing parser, source registry, DOCX/PDF locators, selective OCR gateway and fact materializer. Add physical workbook completeness, cross-field/cross-sheet relationship evidence and typed current-document evidence in later bounded slices; do not create another parser, vector database, mapping app or project-specific dictionary.
- Focused route/bridge tests pass (`18 passed`). The larger role-setting selection initially exposed one stale GLM-default assertion, which was corrected; the final selected route/role/bridge suite passed (`37 passed`, 18 existing deprecation warnings), Python compilation and `git diff --check` passed. No service, real model call, real-project resubmission, draft, facts or risk run occurred; port 8911 remained stopped.

## 2026-09-03 — Phase C dual-cohort mapping reconciliation P0

- Completed a governed three-worker implementation pass on the declared `zcode/GLM-5.3-Flash:max` route, then independently reviewed and repaired the shared worktree. The primary MiniMax and blind GLM verifier now have separate runtime roles, prompt versions, business-key namespaces and identity-bound queue claims while receiving the same frozen field profile. The verifier receives no primary verdict or adjudication context.
- Added deterministic field-by-field reconciliation over exact profile coverage and cohort-local evidence references. Only full role/kind agreement with closed evidence on both remote routes can auto-pass. Missing, duplicated, unexpected or hallucinated evidence references block; CTCAE grade, risk and Query conclusions are rejected at mapping time. A local MTPLX first pass can never be labelled a dual-model pass.
- Added the legacy-cohort migration boundary and a cohort schema digest so the retained RUX 129-job GLM baseline cannot mix into a new MiniMax revision or enter a new draft. The product endpoint now starts and reads both cohorts by default, and confirmation recomputes repository-backed reconciliation instead of trusting a client projection.
- Codex corrected three integration defects found after worker completion: an unavailable identity-bound worker could otherwise fall through to an unfiltered claim, verifier revisions were absent from the current-revision resolver, and the first product integration did not actually gate confirmation. Technical coverage/evidence failures and model disagreements now remain system-owned review work; the UI explicitly tells the monitor that no bulk confirmation is needed.
- Final selected regression passed `742` tests with 135 existing warnings; changed Python modules compiled and `git diff --check` passed. One unrelated backup-restore test transiently returned `package_corrupt` in the preceding 740-test run and passed alone immediately afterward; it was retained as a flaky observation, not counted as acceptance evidence. No service, real model call, real-project resubmission, mapping draft, fact or risk run occurred; medical-writing paths were unchanged and port 8911 remained stopped.
- P0 does not complete the full dual-review lifecycle. The next bounded slice is automatic, evidence-focused adjudication of reconciliation differences, with user questions allowed only for residual medically material ambiguity. After synthetic verification, resume RUX from a fresh dual cohort in its existing isolated workspace; never reuse or resubmit the legacy 129-job cohort as current evidence.

## 2026-09-03 — Independent Sol review of first-listing dual harness

- A user-requested fresh `gpt-5.6-sol:high` subAgent reviewed commit `8965ef1` read-only. It ran 312 synthetic/backend/frontend checks and found the route isolation, frozen blind input, field-level coverage, evidence closure, server-side confirmation gate and fallback labelling suitable as a P0 technical base; no real data, service or model was run.
- The review rejected any claim that the full first-listing workflow is complete. Both models currently see only parser-produced fields, so they can agree while jointly missing hidden/veryHidden or empty sheets, merged/multi-row headers, hidden rows/columns, named tables, formulas without cached display values, number formats and other physical workbook evidence. Cross-sheet relationship evidence is also still empty.
- The next implementation order is therefore: (1) extend the existing listing parser/admission record with a deterministic physical workbook manifest and a fail-closed source-to-profile completeness gate; (2) add aggregate, de-identified cross-field/cross-sheet relationship evidence; (3) implement a dual-reconciliation adjudication state that resolves differences inside the harness and emits at most one plain Chinese question only for residual medically material ambiguity; (4) bind current effective protocol/IB/eCRF/SAP evidence through existing DOCX/PDF/selective-OCR locators.
- CTCAE term/grade matching, laboratory abnormality/trend assessment, IB expected-risk interpretation, AE/MH/CM/IP/PD linkage, risk grading and Query generation remain downstream of confirmed mapping and locator-backed canonical facts. They require explicit knowledge/document versions and may never be inferred or hardcoded during field mapping.

## 2026-09-03 — Phase C workbook physical-completeness gate P0

- Extended the existing listing parser and admission record rather than adding a second parser. Every workbook now carries a byte-bound physical manifest with workbook order, visible/hidden/veryHidden state, empty/header-only/data classification, used range, hidden rows/columns, merged regions, named tables, autofilter, formula/cache state, number formats and header-row locations. Leading-zero text is preserved as coordinate plus hash/length only, so identifier-like raw values are not persisted as manifest evidence.
- Added a deterministic source-to-profile reconciliation gate before the dual-model bridge. Every staged file and physical sheet must be accounted for; silent data omission, hidden data not profiled, digest mismatch, invalid order or contradictory empty/header claims fail closed. The reconciled manifest hash is part of the mapping input revision, so older jobs become stale when physical evidence changes.
- The governed three-worker pass ran on `zcode/GLM-5.3-Flash:max`; one worker used the runner's same-session recovery after an initial non-terminal failure and completed on the same provider/model. Codex repaired four matrix findings: formula-coordinate parsing, empty-sheet A1 placeholder normalization, mixed-format detection, privacy-preserving leading-zero evidence and merged group-header row inclusion.
- Final synthetic workbook matrix passed `106/106`; source-profile/bridge/dual-cohort checks passed `48/48`; adjacent admission/mapping/fact/startup/source validation selection passed `140` with 33 existing warnings and 14 real-file tests deliberately deselected. Changed modules compiled and `git diff --check` passed. No real project file, service, browser or model was run; medical-writing paths were unchanged and 8911 remained stopped.
- Next P0 is aggregate de-identified relationship evidence, followed by the dual-reconciliation adjudication state machine. The full first-listing dual-harness workflow is still not complete and no legacy RUX cohort may be promoted.

## 2026-09-03 — Phase C aggregate relationship evidence P0

- Added one pure deterministic relationship profiler before the existing mapping bridge. It computes bounded, recomputable same-table co-occurrence, missingness, value-overlap, cardinality and bidirectional dependency evidence plus cross-table same-name value-domain coverage; only aggregate counts/rates and admitted table/field names survive, never raw cell values or value hashes.
- The relationship payload is exact-row-digest bound, schema-gated and part of the frozen mapping input revision received independently by the MiniMax primary cohort and blind GLM verifier. Missing, malformed, oversized, stale-bound or conclusion-bearing evidence fails closed. Queue reconciliation now also refuses cohorts built from different input revisions.
- Codex rejected the worker draft's English-suffix-only coverage and ambiguous sample denominator. Known morphology may label a term/code, value/unit or performed/reason candidate, but every other bounded field pair—including Chinese and unfamiliar vendor labels—now reaches the models only as neutral `statistical_pair` evidence. When a table exceeds 512 rows, the payload states `sampled_row_count`; the prompt forbids treating it as the full-table denominator and treats cross-table overlap only as a potential join/synonym signal.
- Verification used synthetic data only: after removing the one-off 2,193-line worker test scaffold, the retained focused relationship/bridge/cohort/reconciliation suite passed `115`; the wider C3 and adjacent monitoring selection passed `399, 1 deselected`, with 98 existing FastAPI deprecation warnings. Changed Python modules compile, `git diff --check` passes, medical-writing routes/assets and real project files were not changed, no product model/service/browser ran, and port 8911 remained stopped.
- P0 relationship evidence is complete as a mapping-input layer, not as clinical analysis. CTCAE grading, IB/protocol-informed expected-risk assessment, AE/MH/CM/IP/PD linkage, risk confirmation and Query generation remain downstream of confirmed mapping and locator-backed facts. Next safe slice is the dual-reconciliation adjudication state machine; after that, bind current effective protocol/IB/eCRF/SAP evidence. The legacy RUX 129-job GLM cohort remains baseline-only and must not enter the new dual-model revision.

## 2026-09-03 — Phase C dual-review adjudication foundation

- Added an internal reconciliation-to-adjudication path that runs for every newly adopted dual-cohort draft, including fields the MiniMax primary did not itself flag. Incomplete verifier work remains `running`; malformed coverage or evidence remains `blocked`; neither can fall through to automatic confirmation or become bulk work for the medical monitor. Residual medically material ambiguity is projected as one plain Chinese question without model, JSON, confidence or internal-state language.
- Strengthened the blind GLM harness as a genuinely different cognitive pass: it must independently search for omissions, counter-evidence and alternative meanings over complete sheet/column coverage while preserving the mapping-stage ban on CTCAE grading, risk, Query and confirmed joins. The product runtime remains direct MiniMax plus direct GLM; Codex is not part of the deployed analysis or conflict-resolution chain.
- Reconciliation now reads the immutable primary cohort verdict rather than a user-edited draft and compares the full constrained semantic verdict, including standards references, derivation lineage, value constraints, treatment identity and dose semantics. Case-only role differences remain normalized; any substantive non-role semantic difference blocks auto-agreement.
- Replaced the first draft's string-only completion proof with append-only, typed, input-revision-bound adjudication receipts in the existing mapping repository. Receipts are idempotent and immutable, distinguish `primary_retained` from `escalated`, bind the reconciliation digest, job, candidate and evidence IDs, and are required by the server confirmation gate. The primary gate metadata now points to the actual CMS MiniMax endpoint rather than the GLM preset.
- A fresh user-requested `gpt-5.6-sol:high` read-only review challenged the mechanism. Its accepted findings define the remaining P0 order: stable source/sheet/column identity and stricter degraded-parser blocking; auditable terminal receipts before local fallback; anonymous dual-harness re-review that may safely adopt the verifier or a conservative unmapped result; and current protocol/IB/eCRF/SAP locator binding. The current slice does not claim those items, real dual-model execution, cross-project validation or clinical acceptance.
- Synthetic verification only: selected C3/mapping/service/repository regression passed `677`; related frontend state/API/project-isolation tests passed and the admission render wrapper passed `128`; targeted Ruff, Python compilation and `git diff --check` passed. Medical-writing paths and real project files were unchanged, no service/browser/product model ran, and port 8911 remained stopped.

## 2026-09-03 — Phase C autonomous dual-harness conflict resolution

- Replaced the remaining single-primary adjudication seam with two isolated product-harness second reviews. MiniMax and GLM receive the same frozen evidence plus deterministically sorted anonymous candidate options; the payload removes first-pass ownership, provider/model identity and candidate/job identity. Each route has its own prompt version, business-key namespace and direct runtime service. Codex is not present in the deployed analysis or conflict-resolution path.
- The deterministic coordinator now compares both second-review outputs over the complete constrained semantic verdict and cohort-local evidence closure. Agreement may adopt a corrected role, field kind, conservative unmapped result, treatment identity, dose semantics, standards reference or derivation/value constraint without asking the user. Continued semantic disagreement or either reviewer retaining medically material uncertainty yields one plain Chinese question; missing, failed or unclosed reviewer evidence stays internal `running`/`blocked` work and cannot auto-confirm.
- Extended the existing immutable adjudication receipt instead of adding another authority. Every resolved first-pass divergence binds both accepted second-review jobs/candidates, their prompt/input revisions, candidate content hashes and evidence IDs. When the agreed result changes the mapping, the effective draft and confirmed revision source lineage points to the selected adjudication candidate rather than the stale first-pass source. Provenance-bearing system edits remain restricted to `system_harness`.
- Mapping-stage clinical boundaries remain unchanged: no CTCAE grade, risk conclusion, Query or confirmed AE/MH/CM/IP/PD join can be produced here. The parser, real-project data, medical-writing routes/assets and fallback policy were not changed. Auditable terminal-unavailability receipts for local fallback and current protocol/IB/eCRF/SAP locator binding remain later P0 work.
- Synthetic verification only: focused mapping/service/repository regression passed `551`; wider C3 and adjacent mapping/activation/worker regression passed `815`; frontend admission integration/state/API/project-isolation checks passed and the admission render wrapper passed `128`; targeted Ruff, Python compilation and `git diff --check` passed. No real project, product model, service or browser ran, and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe slice is the stricter degraded-parser/stable source-sheet-column identity boundary, then auditable local-fallback terminal receipts and current-document locator binding before any fresh RUX dual-model run.

## 2026-09-03 — Phase C stable workbook evidence identity and degradation gate

- Closed the shared-omission failure mode identified by the independent review. An xlsx physical-evidence capture failure or per-sheet degraded evidence is now a blocking source-profile finding, so MiniMax and GLM cannot jointly pass a workbook whose hidden/layout/formula evidence was not reliably captured. Declared format limitations such as CSV layout not applying remain explicit but are not mislabelled as parser failure.
- Upgraded the existing mapping bridge to v7 and bound every emitted table to a deterministic `table_binding_id` derived from source revision, physical sheet index/name and accepted snapshot. Every field now carries a deterministic `field_binding_id` plus the same source revision, sheet index, table binding and zero-based column index. Ambiguous same-basename source resolution, missing manifest-sheet identity or malformed bindings fail closed before model submission.
- The direct harness validator checks the complete stable identity shape for v7 profiles, and same-table/read-only evidence carries the stable binding IDs when available. Human-readable Chinese sheet/column labels remain model context only; they do not replace the frozen source/sheet/column identity.
- Synthetic verification only: focused completeness/bridge/dual-cohort/service checks passed `515`; wider C3 and adjacent mapping/activation/worker regression passed `817`; targeted Ruff, Python compilation and `git diff --check` passed. No real project, product model, service or browser ran, medical-writing paths/assets were unchanged, and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe P0 is auditable terminal-unavailability receipts for the local fallback gate, followed by current protocol/IB/eCRF/SAP locator binding. Only after those contracts pass synthetic and independent review should RUX start a fresh MiniMax-primary plus GLM-blind cohort.

## 2026-09-03 — Phase C auditable local-fallback admission

- Removed the environment-variable authorization path for local MTPLX mapping. Setting `MONITORING_C3_REMOTE_ROUTES_UNAVAILABLE` no longer admits anything. The existing direct MiniMax and GLM services may create identity-bound jobs while their configured runtime is unavailable, allowing the ordinary worker to persist an actual terminal attempt instead of replacing evidence with configuration intent.
- Reused the existing AI job and immutable attempt history as the only fallback authority; no new table, probe service or scheduler was added. Local fallback requires one current-profile terminal receipt from each exact remote route. Configuration/transport failures must be non-retryable; provider runtime failures must exhaust the configured attempt budget. Response-identity errors, worker errors, stale contracts, incomplete attempts and failures from another profile/provider/model are rejected.
- The resulting bounded receipt records no credentials or failure messages. It binds route identity, job/input/prompt, failure code and attempt request/response hashes, is content-hashed into the fallback field profile and input revision, and is revalidated against repository history by the current-revision resolver even after the remote jobs are superseded by local jobs. Tampered or missing dual evidence fails closed before local submission.
- A local fallback cohort remains explicitly degraded and cannot satisfy `dual_model_pass` or substitute for GLM blind verification. This slice changes admission evidence only; it does not run a model, weaken mapping-stage clinical boundaries or add Codex to product runtime.
- Synthetic verification only: fallback happy-path, missing-evidence and ignored-env checks passed; wider C3 and adjacent mapping/worker regression passed `826`; targeted Ruff, Python compilation and `git diff --check` passed. Real projects, models, services and browser were not run, medical-writing paths/assets were unchanged, and port 8911 remained stopped.
- Phase C remains `in_progress`. Next P0 is current effective protocol/IB/eCRF/SAP locator binding and document-completeness policy before any new RUX dual-model cohort.

## 2026-09-03 — Phase C current-document evidence binding

- Added one typed, immutable document-evidence packet for the current medical-monitoring protocol, investigator brochure, eCRF and SAP. Mapping readiness now requires a current validated protocol and eCRF; IB/SAP absence is retained as an explicit downstream limitation. The packet binds source revision, content hash, parser and validator versions, expected project context, complete locator-index digest and bounded locator samples. It cannot assert clinical applicability, CTCAE grade, risk, Query or an AE/MH/CM/IP/PD join.
- MiniMax primary and blind GLM verifier now receive the same once-resolved frozen packet in the dual submission path. The deployed R7 POST no longer accepts a single-cohort override, and the legacy `/ai/field-mapping-jobs` route returns 410 in the deployed application. Codex is not part of the product runtime or conflict adjudication.
- Added a medical-monitoring R7 upload path for the two mapping prerequisites: DOCX protocol and XLSX eCRF. The source registry persists an independent expected locator count and locator-index digest; partial, duplicate, blank, stale or validation-mismatched indexes fail closed. A manifest schema revision is part of the source identity, so re-uploading unchanged bytes upgrades an old manifestless entry without overwriting the retained old record.
- Explicit document selection is now validated before versioning. Missing/wrong-role and stale/unusable documents return separate plain Chinese product errors; successful current-source inference needs no user confirmation. Medical-writing registration behavior remains unchanged.
- Synthetic verification passed: focused contract/API/service regression `577`, wider Phase C and adjacent mapping regression `1236`, synthetic source-registry checks `18` and source-intake checks `2`, targeted Ruff, Python compilation and `git diff --check`. A same-session independent `gpt-5.6-sol:high` review found and drove four repairs, then re-ran a synthetic migration probe and closed with `P0=0, P1=0`. One unrelated pre-existing frontend source-registry path scan still fails because a frontend file already contains `/Users/`; no frontend file changed in this slice and that failure is not counted as acceptance evidence. This is engineering evidence only, not clinical acceptance.
- Test-scope deviation retained for audit: one broad source-validation command and the reviewer's first pass each included an existing read-only real-file test before the scope was noticed. Neither changed source files, launched a service/model/browser nor contributed acceptance evidence; all subsequent checks were synthetic-only.
- Phase C remains `in_progress`. Before a fresh RUX dual cohort, the next safe slice is monitoring-owned IB/SAP registration and evidence retrieval plus the user-facing automatic document-readiness projection; keep 8911 stopped and do not reuse the legacy GLM-only cohort.

## 2026-09-03 — Phase C study-document readiness and automatic mapping entry

- Replaced the engineering-style prerequisite surface with a plain Chinese readiness panel. The monitor sees why the current protocol/eCRF are needed, which file is missing and one `添加文件` action; mapping questions remain hidden until both required documents are usable. The profile page no longer renders manifest hashes, file digests, source/snapshot/locator/profile IDs or a technical-details block.
- Product document upload is scoped to the current admission attempt. The server registers the file, validates and persists the exact `(attempt_id, role)` selection, then returns only the readiness projection; no registry entry ID reaches the client. Unique automatically inferred current documents are also frozen to the attempt before any MiniMax/GLM jobs are enqueued, preventing later document uploads from changing an active attempt.
- The upload path is an explicit replayable saga rather than a claimed cross-store transaction. If readiness refresh fails after a successful save/selection, the user is told that the file is retained and can click `重新核对研究文件` without uploading again. The UI preserves known role status, ignores stale readiness responses and serializes document uploads.
- A genuinely new admission now reads first, automatically starts the mandatory dual mapping POST only when no cohort exists, and polls only the active `generating` state. Terminal attention states stop polling and expose the existing recovery action. Codex is absent from both deployed analysis and conflict adjudication.
- Product mapping responses now use explicit top-level, summary, candidate, draft and semantic-quality allowlists. Provider/model/job/evidence/source IDs and hashes do not enter the product response. Product errors use ordinary Chinese instead of model, provider, primary/verifier or configuration language.
- Synthetic verification only: focused document/R7 tests `37 passed`; wider C3 and adjacent mapping regression `1241 passed` with 39 existing warnings; frontend API/render/state/mapping/integration checks `117/148/73/16/47 passed`; Vite production build passed with the existing large-chunk advisory; targeted Ruff, Python compilation and `git diff --check` passed. A same-session independent `gpt-5.6-sol:high` review drove two repair cycles and closed at `P0=0, P1=0`. No real project, service, browser or product model ran, medical-writing paths were unchanged and port 8911 remained stopped.
- Phase C remains `in_progress`. The next safe slice is monitoring-owned optional IB/SAP registration and locator-backed evidence retrieval, followed by synthetic verification before any fresh RUX dual-model run.

## 2026-09-03 — Phase C optional study-document registration

- Extended the existing medical-monitoring document intake rather than adding a parallel parser. Investigator brochures and statistical analysis plans now accept PDF or DOCX, reuse the established native-text extractors, persist only in the `medical_monitoring` namespace and retain a complete locator manifest for every readable span. The medical-writing routes and assets were not changed.
- Added generic, project-neutral file-role checks for IB and SAP. Two independent structural markers are enough for automatic role acceptance when project context has no contradiction; otherwise the existing validation boundary remains fail-closed. The monitoring freshness gate now canonicalizes protocol/eCRF/IB/SAP role names consistently, closing a context-hash mismatch without weakening validation.
- The product readiness panel presents both documents as `可稍后添加` with one plain optional action. Their absence does not block field mapping and does not create confirmation work for the medical monitor. Mapping remains limited to column semantics: no CTCAE grade, risk, Query or confirmed AE/MH/CM/IP/PD join was added, and Codex remains outside deployed analysis and conflict adjudication.
- Synthetic verification only: DOCX IB and PDF SAP registration/current-evidence tests plus the document-evidence suite passed `20`; adjacent R7/document tests passed `39`; wider C3 and mapping regression passed `399`; frontend API/render/state/mapping/integration checks passed `130/150/73/16/47`; Vite production build, targeted Ruff, Python compilation and `git diff --check` passed. No real project, service, browser or product model ran, and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe slice is an internal, current-document-bound evidence retrieval contract for the MiniMax primary and blind GLM verifier, followed by a phase-boundary independent review before any fresh RUX dual-model cohort.

## 2026-09-03 — Phase C current-document excerpt retrieval

- Added one internal retrieval contract over the existing source registry. A caller must present the still-current protocol/IB/eCRF/SAP binding; project, role, source entry, document content hash and complete locator-index hash are rechecked before any text is returned. Superseded or tampered bindings fail closed.
- Generalized the existing protocol span search without changing its legacy API. The new path remains restricted to the `medical_monitoring` namespace and an explicit role-specific source-kind allowlist. Results carry exact source/locator, bounded text, text hash and matched terms; the immutable packet contains no clinical conclusion.
- This is evidence plumbing only. It is not yet wired as a field-mapping conclusion source and cannot grade CTCAE, confirm risk, join AE/MH/CM/IP/PD or draft a Query. MiniMax and blind GLM remain the independent deployed analyzers; Codex is still outside runtime adjudication.
- Synthetic verification only: document registration/retrieval tests passed `20`, source-packet adjacency passed `65`, and wider C3/mapping regression passed `399` with 21 existing warnings. Targeted Ruff, Python compilation and `git diff --check` passed; no real project, model, service or browser ran and 8911 remained stopped.
- Phase C remains `in_progress`. Before a fresh RUX cohort, run a fresh-context independent review of the document registration/retrieval boundary and repair any P0/P1 finding; then plan the isolated real-project run without reusing the legacy GLM-only cohort.

## 2026-09-03 — Phase C document-boundary independent review closure

- A fresh-context read-only `gpt-5.6-sol:high` review found no P0 and four P1 defects: freshness was split by legacy source-kind aliases; excerpt retrieval did not compare the complete validation authority; optional IB/SAP inherited protocol-only indication/version checks; and an unusable newer upload could supersede the last usable document.
- Canonicalized monitoring freshness by logical protocol/eCRF/IB/SAP role across aliases and selected the latest usable authority, not merely the latest attempted registration. A failed or warning-only replacement is retained for audit but no longer removes the last usable document from service.
- Excerpt retrieval now requires complete `CurrentDocumentBinding` equality, including parser and validation identity/revision/context. IB/SAP retain technical readability, role and project-identity checks but no longer require the protocol's indication label or protocol-version text.
- Added synthetic production-context, revalidation/context-change, unusable-replacement and cross-alias supersession tests. Focused document tests passed `22`; wider C3/mapping regression passed `401`; source-packet/protocol-validation adjacency passed `46`; targeted Ruff, Python compilation and `git diff --check` passed. The same reviewer rechecked the repairs and closed at `P0=0, P1=0`.
- No real project, product model, service or browser ran; no clinical acceptance is claimed and 8911 remained stopped. Phase C remains `in_progress`; next action is to preflight the isolated fresh RUX dual-model cohort from the current source and current-document set, without reusing the legacy GLM-only cohort.

## 2026-09-03 — Phase C fresh RUX cohort read-only preflight

- The existing isolated RUX listing copy is present and its SHA-256 exactly matches the read-only source (`b68d53fe…a343`). The old runtime contains prior artifacts, but no process currently owns its SQLite file and port 8911 remains stopped. None of those artifacts is accepted as a fresh dual-model cohort.
- The shared source registry currently has RUX entries only under `safety_pv`; it has no current `medical_monitoring` protocol, eCRF, IB or SAP authority. The project manifest identifies one protocol source, while the read-only project tree contains multiple plausible eCRF/CRF, IB and SAP files and versions.
- A fresh MiniMax-primary plus blind-GLM cohort must not start by reusing the legacy GLM-only jobs, by silently borrowing `safety_pv` registrations, or by asking the medical monitor to manually adjudicate a file inventory. Codex also must not choose source authority from filenames on behalf of the deployed product.
- The current direct mapping gate remains `cms-smk/MiniMax-M3` primary plus `zhipu-coding-plan/glm-5.3-flash` blind verifier, with no OMP wrapper; local MTPLX remains terminal-evidence-only fallback. No credentials were read or recorded during this preflight.
- Phase C remains `in_progress`. The next safe implementation unit is a generic, project-neutral study-document candidate decomposition and dual-harness source-authority adjudication path that can auto-register a unique high-confidence protocol/eCRF/IB/SAP set, surface only unresolved material ambiguity in plain Chinese, and write only to isolated monitoring storage.

## 2026-09-03 — Phase C isolated study-document candidate decomposition

- Added a product-owned, project-neutral candidate decomposition boundary before source authority selection. Supplied XLSX/DOCX/PDF bytes are copied into content-addressed isolated storage and paired with immutable manifests; candidate and batch identities are deterministic, input-order independent and explicitly `not_promoted`/`not_adjudicated`. Nothing is written to the shared source registry, so filename order, upload order and modification time cannot establish current authority.
- Reused the existing workbook and DOCX parsing authorities and added a lightweight PyMuPDF-only candidate text pass that does not load the medical-writing runtime. XLSX manifests contain sheet/row/column structure but never row values; textual headers are emitted only when the parser records a detected header and subsequent data exists. The parser now preserves whether it detected a header or used the row-1 compatibility fallback.
- Fully scanned or image-only PDFs remain usable candidates with `needs_ocr`; malformed supported files retain a generic unreadable manifest. Only normalized input-corruption exceptions are converted to file damage. Dependency, storage and unexpected runtime/programming failures propagate and cannot become immutable false evidence. Model-facing excerpts and metadata redact Unix, Windows, UNC and file-URI paths, are bounded, and hash the emitted text.
- A fresh-context `gpt-5.6-sol:high` reviewer found and drove closure of headerless-XLSX leakage, damaged-XLSX persistence, path leakage, heavy PDF runtime coupling, image-block misclassification and exception-normalization defects. The final same-session recheck closed at `P0=0, P1=0`.
- Synthetic-only final verification passed `23` candidate/parser tests with `3` real-RUX tests deliberately deselected, plus `48` current-document/dual-cohort/mapping-bridge tests. Ruff, Python compilation and `git diff --check` passed. An earlier broad parser command unintentionally executed one existing read-only RUX parser test; it made no source change and is excluded from acceptance evidence. One pre-existing source-registry frontend path scan also remained unrelated and was not repaired in this backend slice. No service, product model or browser ran, medical-writing routes/assets were unchanged and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe slice is the typed MiniMax-primary plus blind-GLM document-authority task and immutable conflict adjudication over this frozen candidate batch. It must auto-promote only a unique high-confidence role/version set, keep Codex outside deployed runtime, ask at most one plain Chinese question for residual material ambiguity, and complete synthetic/independent review before any fresh isolated RUX cohort.

## 2026-09-03 — Phase C dual-model document-authority reconciliation contract

- Added a strict, project-neutral document-authority contract over the frozen candidate batch. Server-owned direct MiniMax-primary and blind-GLM run envelopes must have distinct run/job identities, exact provider/model/prompt bindings, complete candidate and role coverage, content-bound input/output hashes, closed locator evidence and matching high-confidence conclusions before any role can resolve automatically. Codex is not part of this deployed decision contract.
- Conflicts are rebuilt from the frozen batch plus both original first-pass run envelopes and sent to two independent second reviews. The anonymous packet includes every candidate for every conflicted role and excludes model/provider/owner identity. Evidence references bind both candidate ID and locator, so repeated locator strings across files cannot satisfy another file's evidence. A client-recomputed reconciliation or conflict-packet digest cannot replace the original run evidence.
- Automatic agreement now considers every potential competing candidate for the role, including optional-file missing decisions. Version, date, usability, role, evidence or uncertainty disagreement enters internal dual review. Only unresolved material disagreement becomes one plain Chinese file-selection question; unreadable batches can reach that question without invented evidence, while no file can be selected without candidate-bound evidence.
- A same-session independent `gpt-5.6-sol:high` review drove five repair rounds covering run authenticity boundaries, full-candidate review, forged digests, cross-file locator collisions, unreadable inputs and overlooked competing candidates; final closure was `P0=0, P1=0`. Focused and adjacent synthetic tests passed `74`; targeted Ruff, Python compilation and `git diff --check` passed. No real project, model, service or browser ran, medical-writing paths were unchanged and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe slice is to construct these first- and second-pass envelopes exclusively from the existing immutable AI job/attempt repository and direct MiniMax/GLM services, then verify the integrated synthetic flow before any fresh isolated RUX cohort.

## 2026-09-03 — Phase C repository-backed document-authority first pass

- Added a dedicated internal `document_authority_analysis` task to the existing monitoring AI queue instead of creating a second runner or database. Its only submission path is identity-bound: the primary role must resolve to direct `cms-smk/MiniMax-M3`, the verifier role to direct `zhipu-coding-plan/glm-5.3-flash`, with separate prompt versions and business keys. The generic task submission path rejects this specialized task.
- The two roles receive the same frozen candidate batch and exact file/hash source bindings. Provider output must be one complete strict `DocumentAuthorityAnalysis`; all candidates, all four document roles and candidate-local locators are validated before persistence. The server, not the provider, materializes the evidence graph and keeps CTCAE, risk, Query and AE/MH/CM/IP/PD conclusions outside this stage.
- Added a repository loader that reconstructs the server-owned run envelope only from a completed immutable job, its unique successful attempt, the final raw provider output and the persisted candidate. Role swapping, wrong provider/model/prompt, mismatched frozen input and unbound output fail closed; client-supplied analysis objects are not accepted as reconciliation evidence.
- Synthetic direct primary/verifier execution and role-swap tests passed `3`; existing monitoring AI service, repository, worker, startup-recovery and document-authority regressions passed `561`. Targeted Ruff and Python compilation passed. No real project, model, service or browser ran and port 8911 remained stopped.
- Phase C remains `in_progress`. Next safe slice is the matching repository-backed MiniMax/GLM second-review task plus an orchestrator that builds its anonymous conflict packet only from the two stored first-pass runs.

## 2026-09-03 — Phase C repository-backed document-authority conflict review

- Added the matching `document_authority_review` task to the existing monitoring AI queue and direct runtimes. The orchestrator reconstructs both first-pass envelopes only from completed jobs, the unique successful attempts, final raw outputs and persisted candidates, then builds the anonymous full-candidate conflict packet; it does not accept client-supplied model conclusions or create another runner/database.
- MiniMax and blind GLM receive separate identity-bound review jobs. Server-only source bindings are removed from model input while retained for evidence materialization. The two first passes and two reviews must all bind the same immutable input revision, exact provider/model/prompt identity and candidate-local evidence before final resolution; Codex is not part of deployed analysis or adjudication.
- Closed the document-authority stage against downstream medical conclusions with a fail-closed positive schema: uncertainty is a controlled code, version/date use controlled identifier grammars, and outer title/text are fixed task copy. Any first-output violation fails immediately with one auditable invalid attempt and no candidate; these tasks cannot use the generic provider repair loop to convert a contaminated first output into success.
- Synthetic verification passed `27` focused document-authority tests and `624` wider monitoring AI/startup/worker/repository/candidate/source-identity/mapping tests with `18` existing warnings. Targeted Ruff, Python compilation including `main.py`, and `git diff --check` passed. A same-session independent `gpt-5.6-sol:high` review drove revision-closure and fail-closed text repairs, then closed at `P0=0, P1=0`.
- No real project, product model, service or browser ran; medical-writing routes/assets were unchanged and port 8911 remained stopped. Phase C remains `in_progress`. Next safe slice is to wire this repository-backed coordinator into monitoring-owned admission so a fully resolved role/version set can be promoted atomically to the source registry; keep the next step synthetic until that promotion and rollback contract passes focused, adjacent and independent review.

## 2026-09-03 — Phase C atomic document promotion safe pause

- Began the monitoring-owned promotion seam after the four repository-backed authority jobs resolve. Selected candidate bytes are reloaded only from the content-addressed isolated candidate store, SHA-256 checked, role/technical/parser eligibility checked, then registered through the existing monitoring document registration methods. Unresolved authority returns `not_promoted`; Codex remains outside product adjudication.
- Added staged `SourceRegistryStore.transaction()` publication: registration methods and content validation run before one filesystem replace publishes the complete set. Any exception discards all staged source entries; content-addressed files and orphan validation audit rows may remain recoverable but are not visible as current registered sources. Existing non-transactional callers retain their current single-entry call shape.
- Current synthetic checkpoint passed targeted Ruff and Python compilation plus `9` focused promotion/registry tests (`20` unrelated source-registry tests deselected), including successful protocol/eCRF promotion, direct registry rollback and forced second-registration rollback. `git diff --check` passed and port 8911 remained stopped.
- This is a recoverable implementation checkpoint, not accepted completion. The shared registry store changed, so the next action must first run a fresh independent P0/P1 review of transaction concurrency/idempotency, candidate promotability and validation rollback semantics; repair findings, then run the full source-registry/medical-writing protected regression and wider monitoring admission tests before treating the slice as complete. Do not start RUX, providers, service or browser before that closure.

## 2026-09-03 — Phase C atomic document authority promotion closure

- Completed the monitoring-owned autonomous workflow from one frozen document batch through direct MiniMax primary analysis and blind GLM verification, internal dual review on semantic conflict, and atomic publication of the complete protocol/eCRF/IB/SAP authority set. Product clients receive only an opaque analysis token and plain Chinese progress/guidance; they cannot submit model conclusions, conflict packets, role assignments or promotion receipts. Codex is absent from deployed analysis and adjudication.
- The source registry now publishes under an inter-process file lock with latest-state reload, staged validation and atomic replace. A failed registration may retain content-addressed preparation files and immutable validation audit rows, but cannot expose a partial current authority. Same-source re-adjudication persists the new receipt instead of being swallowed by structural deduplication.
- Promotion receipts bind the immutable candidate batch, complete selected identities and content hashes, exact MiniMax/GLM first-pass and optional dual-review job/run identities, and the registered source group. Production evidence use reconstructs the workflow from the monitoring AI repository and current frozen payload rather than trusting a structurally self-consistent receipt; missing, stale, role-swapped or forged evidence fails closed.
- Replaced the engineering-style role-by-role confirmation with one multi-file action. The system identifies document roles and versions itself, completes high-confidence agreement without asking the monitor, and reserves one ordinary-Chinese question only for material ambiguity that remains after both independent review paths. The production backend blocks the legacy role-assigned upload path.
- Final synthetic verification passed `679` wider monitoring AI/document/source/admission/medical-writing protected tests; changed frontend API/integration/render tests passed `122/47/148`; Vite production build passed with the existing large-chunk advisory. Fatal Ruff checks, Python compilation and `git diff --check` passed. A broad all-rule Ruff probe exposed `98` pre-existing style findings in historical route/test files; they were not mechanically rewritten and are not counted as acceptance evidence.
- A fresh-context `gpt-5.6-sol:high` review drove three repair rounds covering direct promotion, inter-process consistency, rollback semantics, immutable provenance, workflow wiring, legacy bypass, re-adjudication, half-created jobs and forged receipts; final closure is `P0=0, P1=0`. This is engineering evidence only, not clinical acceptance.
- No real project, product model, service or browser ran; medical-writing routes/assets were unchanged and port 8911 remained stopped. Phase C remains `in_progress`. The next safe action is a fresh isolated RUX preflight against the newly committed authority workflow, followed only after explicit run conditions are satisfied by one new MiniMax-primary plus GLM-blind cohort; do not reuse legacy GLM-only jobs.

## 2026-09-03 — Phase C composite study-document authority closure

- Real RUX inventory preflight exposed that one-role/one-file authority would omit effective errata and amendments. The authority schema, both independent model prompts, dual-review conflict contract, promotion receipt and downstream evidence packet now represent one current primary plus every effective supplementary file for each protocol/eCRF/IB/SAP role. v2 model outputs must explicitly return the supplementary list, including an explicit empty list; a legacy-shaped response cannot silently mean “no supplements.” Codex remains absent from deployed analysis and conflict adjudication.
- Promotion is atomic at the visible registry boundary and the v2 receipt binds each supplement to its primary candidate and primary registry entry. Structural checks reject missing, duplicate, cross-role or malformed relationships; production verification also reconstructs the decision from immutable MiniMax/GLM jobs. Each primary and supplement receives an independent complete locator manifest, validation record and retrievable binding. A synthetic end-to-end case proved one DOCX protocol, two independent PDF supplements and one XLSX eCRF can be promoted, verified, resolved and queried without treating either supplement as superseded.
- v1 was never used for a real project/product-model authority run. Old synthetic resolver fixtures remain readable for regression purposes, while operational authority intentionally requires repository-backed v2 verification or fresh v2 re-promotion. Registry rollback continues the previously accepted audit semantics: no partial entry becomes current; content-addressed preparation blobs and immutable validation audit rows may remain recoverable and invisible after failure.
- Focused composite authority/evidence tests passed `82`; source-registry tests passed `22` with one unrelated existing frontend fixture-path assertion deselected. Python compilation, fatal Ruff checks, `git diff --check`, and the governed three-worker execution audit passed. A fresh-context `gpt-5.6-sol:high` review found four P1 concerns; explicit supplement accounting and multi-supplement retrieval were repaired, and the accepted v1/rollback boundaries were re-evaluated; same-session independent recheck closed at `P0=0, P1=0`.
- One overly broad regression glob accidentally admitted three existing read-only real-data tests before interruption. It was stopped at `2000 passed`; filesystem and Git checks found no extra product artifact or source change, but this is an execution-boundary deviation and is not counted as acceptance evidence. Future regression commands must use an explicit synthetic allowlist and exclude every `real_*` or named-project test rather than relying on a broad glob.
- No product model, service or browser ran; medical-writing routes/assets were unchanged and port 8911 remained stopped. Phase C remains `in_progress`. The next safe action is a fresh isolated RUX candidate preflight followed by one new MiniMax-primary plus blind-GLM v2 cohort, without reusing any legacy GLM-only job and without writing to the real-project source directories.

## 2026-09-03 — Phase C first RUX authority attempt and generic contract repair

- The fresh isolated preflight caught runtime configuration drift before product execution: the monitoring primary role had been pointed at GLM and the active workbench runtime lacked its MiniMax credential. Using the existing encrypted local provider store, the active role was restored to direct `cms-smk/MiniMax-M3` primary while the blind verifier remained direct `zhipu-coding-plan/glm-5.3-flash`; both resolved independently with credentials configured. No credential value was logged or committed.
- The first isolated RUX batch failed safely and is retained only as failed evidence. MiniMax first returned a near-valid authority object with a forbidden generic `claims` field, then two empty provider responses; GLM returned descriptive version/date text rejected by the controlled grammar, then followed the contradictory generic schema and emitted unsupported claims. Both jobs reached terminal failure, no authority was promoted, the shared source registry was not written, the read-only project sources were unchanged and port 8911 remained stopped.
- Removed that cross-task schema contradiction. Document-authority analysis/review outputs no longer advertise generic claims/evidence; prompts now state the exact outer JSON shape and controlled version/date forms. PDF and DOCX candidates expose all four neutral role hypotheses so protocol and eCRF documents are not excluded by file type before the independent models inspect their content.
- Added one narrowly admitted repair pass for extra JSON keys or controlled version/date formatting only. File selection, supplements, usability, confidence and locators cannot change during repair. Outer-copy violations, patient-level medical conclusions and other semantic/schema violations still fail closed without a repair call.
- Focused synthetic verification passed `59`; targeted Python compilation, fatal Ruff and `git diff --check` passed. This repair does not turn the failed RUX batch into success. Phase C remains `in_progress`; the next action is a new isolated batch containing the current IB V15 plus plausible current and historical protocol/eCRF/SAP candidates, followed by one independent MiniMax-primary and GLM-blind workflow run with no Codex adjudication.

## 2026-09-04 — Phase C second isolated RUX authority attempt and identity repair

- Built a new isolated candidate batch from 16 distinct read-only files: two plausible protocol V1.3 copies, protocol revision/erratum material, current IB V15 plus V14/V13 history, current and historical CRF/eCRF material, and signed/clean SAP representations. All content hashes were distinct; 15 candidates parsed and the stamped erratum remained explicitly `needs_ocr`. The source trees were read only, the fresh AI database began empty and port 8911 remained stopped.
- The product ran direct `cms-smk/MiniMax-M3` primary and direct `zhipu-coding-plan/glm-5.3-flash` blind verification without Codex or OMP adjudication. The batch reached terminal `failed / not_promoted`; the isolated source registry received no promoted authority. MiniMax first returned only one inner candidate assessment instead of the complete outer analysis, then returned empty provider responses. GLM returned complete 16-candidate/four-role analyses and corrected its controlled date formats on the one repair pass, but repeatedly copied the outer job-revision hash into the inner batch-identity field; immutable validation rejected both outputs as stale.
- Added a dynamic document-authority output-identity contract: analysis must copy the exact frozen candidate-batch hash into `structured_payload.input_sha256`, review must copy the exact conflict-packet hash, and neither may substitute the outer `input_revision_sha256`. The one controlled repair may correct this mechanical identity field while preserving every file selection, supplement, usability, confidence and locator decision. Missing outer envelopes, uncontrolled literals and medical-copy violations remain ineligible for repair.
- Prompt identities advanced to v4 so no v3 failed job can be treated as current. Focused synthetic verification passed `60`; targeted Python compilation, fatal Ruff and `git diff --check` passed. Phase C remains `in_progress`; the next action is one new empty isolated v4 run over the same content-complete candidate set, retaining MiniMax empty/incomplete responses as provider evidence rather than silently substituting another model.

## 2026-09-04 — Phase C v4 RUX authority run and MiniMax output-budget diagnosis

- A third empty isolated runtime executed the v4 authority contract over the same 16-file content-complete batch. Direct GLM blind verification completed on its first product attempt and passed exact provider/model/prompt identity, frozen-batch hash, 16/16 candidate coverage, four-role coverage and candidate-local locator checks. Direct MiniMax primary exhausted the product's bounded recovery and remained terminal `provider_runtime_error`; the workflow correctly ended `failed / not_promoted`, created no conflict-review jobs or promotion receipt and wrote no isolated source authority.
- The governed read-only execution audit independently recomputed the database, batch, content-addressed file and model-output hashes, reconstructed the GLM run through the product loader and confirmed the MiniMax job cannot be loaded as a valid run. It also confirmed no OMP/Codex runtime trace, no active database owner and port 8911 stopped. The audit observed four MiniMax HTTP 200 responses ending with `finish_reason=length`: approximately 77–79k reasoning characters consumed the 24k completion budget, leaving zero or 150 final-content characters and producing three empty-response errors plus one invalid-JSON error.
- Increased only document-authority analysis/review completion budget from 24k to 48k while retaining high reasoning, deterministic JSON mode, bounded product attempts and all fail-closed validators. Other monitoring tasks keep their existing limits. This is a generic large-document authority capacity fix, not a RUX-specific rule and not a relaxation of the two-model requirement.
- Focused synthetic verification remained `60` passed; targeted Python compilation, fatal Ruff and `git diff --check` passed. Phase C remains `in_progress`; next action is one fresh isolated run to determine whether the larger budget lets MiniMax return a complete primary analysis. GLM success alone remains insufficient for promotion, and MTPLX remains ineligible while GLM is available.

## 2026-09-04 — Phase C 48k RUX authority evidence-boundary diagnosis

- Re-ran the same 16-file batch from its isolated content-addressed copies in a new empty runtime; no real-project source file was reopened. The 48k document-authority budget removed MiniMax's length/empty-response failure: both MiniMax attempts returned complete 16-candidate/four-role analyses with the correct frozen-batch identity, while GLM again completed independently.
- Product validation still ended the batch `failed / not_promoted`, correctly. MiniMax selected the scanned stamped protocol erratum whose candidate manifest has `locator_count=0`: the first response supplied an empty supplementary evidence list and the second invented a locator not present in the frozen candidate. Both violate evidence closure; GLM success cannot compensate and no authority, conflict review or receipt was published.
- Advanced the independent analysis/review prompts to v5 with a generic zero-locator rule: a candidate without authorized locators must be unusable, must carry no evidence locators and cannot be selected as a primary or supplementary document. The model must never invent locators. No file or role choice is hard-coded, and validators remain unchanged and fail closed.
- Focused synthetic verification passed `60`; targeted Python compilation, fatal Ruff and `git diff --check` passed. Phase C remains `in_progress`; next action is one fresh v5 isolated run. If MiniMax still violates evidence closure, stop real retries and treat that as a model-quality blocker rather than weakening validation or asking the medical monitor to select files.

## 2026-09-04 — Phase C v5 dual first-pass success and v6 review-coverage repair

- The final authorized v5 isolated run reused only content-addressed copies. MiniMax primary and GLM blind verifier each completed the full 16-candidate/four-role first pass on their first product attempt with exact v5 identity, frozen-batch hash and locator closure. Their conclusions differed, so the deployed workflow autonomously created separate anonymous conflict-review jobs; Codex did not compare or select their answers.
- Both review cohorts failed closed twice with `document_authority_review_coverage_invalid`. Inspection showed a shared prompt-contract omission: validation requires every conflict-role decision to list all 16 authorized candidates and cite at least one authorized locator for every evidence-bearing candidate, including rejected candidates. MiniMax listed all 16 but cited only selected files; GLM considered only role-likely subsets. No review run completed, no user question was generated, and no authority or receipt was promoted.
- Added an anonymous dynamic v6 coverage contract that supplies each conflict role's exact required considered-candidate set and exact evidence-bearing candidate set. Prompts explicitly prohibit filtering by file-role hypotheses and require at least one candidate-local locator for every evidence-bearing candidate, including non-selected files; zero-locator candidates remain evidence-free and ineligible. This changes no role decision and does not let Codex adjudicate.
- Focused synthetic verification passed `60`; targeted Python compilation, fatal Ruff and `git diff --check` passed. The governed three-worker execution audit and Codex review gate passed with a `revise` verdict: runtime isolation/fail-closed behavior are verified, but RUX authority promotion is not accepted. No further real run was started. Phase C remains `in_progress`; the next safe action is an independent review of the v6 dynamic coverage contract, followed by one fresh isolated v6 run only if that review closes P0/P1.
- A fresh-context `gpt-5.6-sol:high` review found two P1 boundary defects in the v6 candidate-coverage helper: an inconsistent zero-count candidate could carry nested locators, and a batch above the `ConflictDecision` 100-item limit could create an impossible review. Both batch and conflict-packet validation now reject those states; the dynamic evidence set also requires a positive declared locator count. Negative tests cover zero-count locator injection and 101-candidate packets, while 100 remains valid. Same-session recheck closed at `P0=0, P1=0`; explicit adjacent synthetic regression passed `606`, with compilation, fatal Ruff and `git diff --check` clean. No real data, provider, service, browser or 8911 run occurred during this closure. The next safe action remains one new isolated v6 product run; no prior failed or partial cohort may be reused as success.

## 2026-09-04 — Phase C v6 RUX review result and false-conflict correction

- A fresh isolated v6 product run completed all four direct jobs: MiniMax primary analysis (one transient provider error, then success), GLM blind analysis, MiniMax anonymous review and GLM anonymous review. The workflow stayed `not_promoted` and returned all four roles unresolved; no source authority or receipt was published and port 8911 remained stopped.
- Compact comparison showed that both reviews selected the same primary protocol, current IB, eCRF and signed SAP. Protocol and eCRF supplementary sets also matched. Three roles were rejected only because equivalent dates used Chinese/ISO punctuation, IB used `V15` versus `15`, independent reviewers cited different authorized locators, and the GLM reviewer calibrated confidence at 0.75–0.85. SAP retained one material difference: MiniMax included the clean DOCX as supplementary while GLM selected only the signed PDF.
- Corrected only the second-round consensus comparator. Controlled numeric version and date spellings now canonicalize deterministically; two independently validated full-coverage reviews need not cite the identical locator tuple; and the extra-review consensus floor is 0.75 while the first-pass auto-resolution floor remains 0.9. Candidate identity, supplementary set, full considered-candidate coverage, controlled uncertainty, evidence closure and independent run identity remain exact fail-closed boundaries.
- Focused tests passed `37`. Replaying the immutable v6 batch and four completed outputs against the corrected comparator now resolves protocol, IB and eCRF without asking the user and leaves only SAP unresolved. This replay is diagnostic evidence, not a retroactive promotion: v6 remains `not_promoted`. The next safe slice is a bounded product-internal adjudication round for material supplementary-file disagreements; it must use only direct MiniMax plus blind GLM, remain evidence-closed and finite, and must not depend on Codex or expose an engineering confirmation screen.

## 2026-09-04 — Phase C bounded autonomous authority adjudication closure

- Added one finite product-internal adjudication round after the anonymous dual review only when material roles remain unresolved. Both direct cohorts receive the same frozen candidate evidence plus two identity-free, hash-bound prior options; each must independently return a complete evidence-closed decision and cannot select by option order, vote or prior confidence. The workflow never loops: agreement promotes atomically, remaining disagreement stops without promotion.
- The adjudication context is rebuilt from immutable MiniMax/GLM analysis and review jobs, deterministically orders the anonymous options, covers only unresolved roles, and is bound into each new job input. Final loading rechecks provider/model/prompt identity, exact input revision, candidate-local locators and output hash. Promotion receipt v3 records both adjudication jobs and runs; v2 receipts remain deep-replay compatible and have an explicit regression.
- The public admission surface now continues polling through a plain `adjudicating` state shown as “系统正在完成最后一次核对”. Internal provider, model, job, hash and confidence vocabulary remains hidden. If both final adjudicators still cannot converge, the product does not display a technical choice grid or imply unsupported incremental merge; it accurately asks the user to reselect the complete study file set.
- Focused authority/job/route tests passed `80`; authority/evidence/API tests passed `115`; frontend render and integration checks passed `148` and `47`; Vite production build passed with the existing large-chunk advisory. Source-registry adjacent tests passed `22` with one pre-existing project-neutral test-fixture absolute-path assertion explicitly deselected, matching the prior accepted boundary. Fatal Ruff, Python compilation and `git diff --check` passed.
- The governed three-worker execution audit and review gate passed. A fresh `gpt-5.6-sol:high` review found P1 issues in v2 receipt replay and the misleading partial-file reselect wording; both were repaired and same-session recheck closed at `P0=0, P1=0`. Generated workflow records and temporary v6 exports were removed after audit; no new `context/` pause or acceptance record remains.
- No real source file, medical-writing route/asset, product service, browser or model was run in this implementation slice; port 8911 remained stopped. Phase C remains `in_progress`. The next safe action is a fresh empty isolated RUX run through the complete MiniMax primary + GLM blind review + bounded adjudication chain; no v6 result may be retroactively promoted.

## 2026-09-04 — Phase C v7 full-chain run and explicit conflict-point contract

- Ran a new empty isolated product runtime using only the previously content-addressed 16-file RUX copies; every copy hash was rechecked before use and no real-project source tree was reopened. Direct MiniMax analysis, GLM blind analysis, both anonymous reviews and both internal adjudications completed. The workflow remained fail closed: no source registration or receipt was written, and the only remaining disagreement was whether two role-relevant eCRF support files belong in the supplementary authority set.
- The v7 evidence exposed a contract ambiguity rather than a primary-file dispute: both models selected the same eCRF V1.1 main file, but the schema could express only the included supplement list, not whether an absent candidate was deliberately excluded or merely omitted. Re-answering every role also allowed already resolved roles to drift without affecting the final result.
- Added adjudication-v2 as a stage-specific schema. The adjudication context now hash-binds the exact candidate-level symmetric difference for each unresolved role, while allowing an empty candidate difference for version/date-only conflicts. Each unresolved-role output must explicitly and disjointly partition every authorized candidate into primary, supplementary or excluded; omission fails closed. Ordinary v6 review output and hashes remain unchanged.
- New v2 jobs use versioned business keys so in-flight v1 jobs cannot be mistaken for the new contract. Legacy adjudication-v1 contexts, prompt identities and promotion-v3 receipts retain a schema-specific deep-replay path; no v7 result was retroactively promoted. Terminal-failure Chinese copy now accurately asks for one complete file re-selection instead of claiming the system will continue when no job is running.
- Three governed read-only workers completed the v7 predicate audit, test matrix and UX boundary audit; execution audit and review gate passed and generated process records were archived then removed from active context/plan/review surfaces. A fresh `gpt-5.6-sol:high` review found three P1 issues (metadata-only conflict scope, v6 hash mutation, v1 receipt/business-key compatibility); all were repaired and same-session recheck closed at `P0=0, P1=0`.
- Focused authority/job/route regression passed `82`; targeted Python compilation and `git diff --check` passed. Port 8911 remained stopped. Phase C remains `in_progress`; the next safe action is one fresh empty v2 isolated run over the same immutable copies, with no reuse of v7 outputs.

## 2026-09-04 — Phase C v8 authority-tier diagnosis and adjudication-v3 closure

- A fresh empty v8 runtime reused only the previously content-addressed 16-file RUX copies. Direct MiniMax primary analysis, blind GLM analysis, both full reviews and both bounded adjudications completed without Codex or OMP in the product path. All four current main-document selections matched exactly, but the workflow stayed `needs_user_input / not_promoted` because the cohorts classified related historical, duplicate and operational/reference files differently. No source registry or promotion receipt was written and port 8911 remained stopped.
- The evidence narrowed the remaining contract ambiguity to authority tiers. Adjudication-v3 now reserves `supplementary_candidate_ids` for documents that explicitly modify, correct, supplement or jointly constitute the current normative main content and must be read with it. Superseded complete versions, duplicate copies, historical summaries that do not enact current changes, filling/operational guides, database/export descriptions and other reference material are explicitly excluded from the current authority combination while remaining preserved in the isolated candidate store. Decisions must use document function and version relationships, not filename keywords; no RUX document identity or disease/drug rule is hard-coded.
- v3 uses distinct prompt identities and business keys. Completed adjudication-v1/v2 pairs remain strictly replayable, mixed generations fail closed, and startup recovery now preserves every current primary/verifier analysis, review and v3 adjudication prompt while retiring unfinished obsolete generations. Only completed/failed allowlisted v1/v2 evidence survives for replay.
- Explicit synthetic authority, admission, evidence, startup and repository regressions passed `207`; Python 3.9 and system-Python compilation plus `git diff --check` passed. A fresh-context `gpt-5.6-sol:high` review found one P1 startup-retirement defect; it was repaired with multi-current prompt support and terminal-only legacy preservation, and same-session recheck closed at `P0=0, P1=0`.
- Phase C remains `in_progress`. Do not ask the monitor to classify individual files and do not immediately repeat another real-model run. The next safe action is a new isolated v3 product run only when continuation is requested, followed by receipt/source-registry verification if both independent cohorts converge; 8911 must remain stopped until an explicit later runtime step.

## 2026-09-04 — Phase C v9 near-convergence and signed-carrier authority repair

- Executed one fresh isolated v3 product run from the 16 previously content-addressed RUX copies after rechecking every copy hash; no real-project source tree was reopened. Direct MiniMax primary analysis, blind GLM analysis, both full reviews and both bounded adjudications completed. The terminal state was `needs_user_input / not_promoted`, with no source registry, receipt or registration and port 8911 stopped.
- The v3 adjudication fully converged on protocol, investigator brochure and eCRF authority combinations. For SAP, both cohorts selected the same signed/final PDF as the current main file and both identified the same version; the only difference was whether the same-version editable DOCX was a supplement or an excluded duplicate carrier. This is an internal authority-carrier classification gap, not a file-selection task for the medical monitor.
- Adjudication-v4 now classifies a signed or approved frozen rendition as current main and an unsigned editable copy with substantively equivalent body/version as an excluded duplicate carrier. Date is supporting evidence only. An editable file remains supplementary only when document-body evidence proves effective normative content absent from the frozen rendition; substantive differences with insufficient evidence remain unresolved. The rule is format- and filename-neutral and contains no RUX, drug, disease or SAP-specific identity.
- v4 has distinct prompt identities and business keys. Completed v3 and v2 repository-backed job pairs plus legacy v1 pairs remain replayable; v2/v3 cross-generation pairs fail closed in both directions. Startup explicitly preserves current analysis/review/v4 prompts and only terminal v1–v3 adjudication evidence, while queued legacy generations are retired.
- Explicit synthetic authority, admission, evidence, startup and repository regression passed `209`; Python 3.9 and system-Python compilation plus `git diff --check` passed. A fresh-context `gpt-5.6-sol:high` review found two P1 issues in the initial wording and replay-test depth; both were repaired, and recheck closed at `P0=0, P1=0`.
- Phase C remains `in_progress`. Do not ask the monitor to compare signed and editable carriers and do not reuse or retroactively promote v9. The next safe action is one fresh isolated v4 product run when work continues; if it converges, verify the complete promotion receipt, registry group, source hashes and downstream evidence reconstruction before Phase C closure. Port 8911 remains stopped.

## 2026-09-04 — Phase C v10 contract failure and unresolved-only adjudication-v5 repair

- Executed one fresh isolated v4 product run from the v9 content-addressed copies after rechecking all 16 hashes. Both analyses and both blind reviews completed; GLM adjudication completed, while MiniMax adjudication failed both bounded attempts with `document_authority_review_coverage_invalid`. The workflow ended `failed / not_promoted`; no source registry, promotion receipt or registration was created and port 8911 remained stopped.
- The frozen adjudication context required only three still-unresolved roles, but the conflict packet retained all four historical conflict roles. MiniMax correctly returned only the three unresolved roles according to the stage instruction, while the validator still demanded all four. This was a contradictory product contract, not a medical conclusion or a reason to ask the monitor to classify files.
- Adjudication-v5 now requests, validates and applies exactly `unresolved_roles`; already resolved roles cannot be re-answered or overwritten. Historical v2-v4 full-role outputs remain replayable under their exact validated prompt generations, with complete candidate disposition required only for roles that were unresolved in that historical context. Mixed generations still fail closed, legacy v1 keeps its original full-role path, and current/replay prompt identities and startup retirement sets are explicit.
- Python compilation, `git diff --check` and focused plus adjacent authority/admission/evidence/startup/repository regression passed `211`. A fresh-context `gpt-5.6-sol:high` review found and drove closure of three replay-boundary P1 issues; final recheck closed at `P0=0, P1=0, P2=0`.
- Phase C remains `in_progress`; v10 is retained only as failed evidence and must not be retroactively promoted. The next safe action is one new empty isolated v5 run over the same verified copies. If it converges, verify receipt, registry grouping, source hashes and downstream evidence reconstruction before any Phase C closure. Port 8911 remains stopped.

## 2026-09-04 — Phase C v11 fresh run and scanned-evidence diagnosis

- Executed one fresh isolated v5 product run only from the previously content-addressed 16-file copies after rechecking all hashes; no real-project source tree was reopened. The complete direct MiniMax-primary plus GLM-blind chain reached terminal results for all six analysis, review and bounded-adjudication jobs without Codex or OMP in the product reasoning path.
- The batch remained `not_promoted`. Investigator-brochure authority converged, while protocol and eCRF remained unresolved. The eCRF difference concerned whether a comparison/support document enacted current normative content; protocol evidence remained materially uncertain because the signed/stamped scanned carrier exposed no authorized text locator. No registry group, promotion receipt or downstream authority reconstruction was created, and no prior batch was retroactively promoted.
- The v11 result is retained as failed/non-promoted evidence only. It demonstrated that prompt refinements alone cannot repair a physically unreadable current carrier: scanned-page recovery and immutable OCR provenance must occur before independent model analysis, while any failed, empty or incomplete OCR result must remain unusable. Port 8911 remained stopped.

## 2026-09-04 — Phase C scanned authority evidence and prompt-generation closure

- Added bounded page-level OCR recovery to the generic document-candidate pipeline for PDF pages with zero native text. Each exposed page is bound to page number, DPI, rendered-image hash, canonical locator, requested/actual model identity, provider, fallback state, status and recovered-text hash/count. OCR runs only within the existing evidence budget; unexposed, failed, empty or missing pages keep the document `needs_ocr` and ineligible for authority selection.
- Candidate evidence revisions are now content-addressed separately from file identity. A later OCR-enriched candidate batch can coexist with the earlier no-OCR manifest without mutating history. New-revision validation recomputes locator indexes, excerpt hashes, page/image bindings, OCR completeness and the evidence-revision hash; legacy manifests retain their exact replay semantics.
- The deployed API resolves the configured OCR runtime lazily inside the monitoring-owned runner, records the actual requested provider/model on controlled unavailability, leaves `actual_model` empty on failure, and propagates unexpected programming defects. Startup recovery wakes both independent mapping workers. Current document-authority analysis advanced to v7 and adjudication to v6; business keys derive their prompt generation, exact legacy pairs remain replayable and mixed generations fail closed.
- Product prompts now distinguish operative amendments, errata and normative supplements from historical redlines, comparison summaries and reference material using document-body evidence rather than filenames or project-specific rules. The product remains fully autonomous: MiniMax performs primary analysis, GLM performs blind full verification and both cohorts adjudicate bounded conflicts; Codex is absent from runtime decisions and the monitor is not asked to classify files.
- Focused candidate/authority/job/admission/evidence/startup/repository regression passed `237` with `45` deprecation warnings; four changed core modules compiled, targeted Ruff and `git diff --check` passed. Whole-file Ruff on `main.py` still reports pre-existing debt, so the current diff remained the lint boundary and no medical-writing code was altered. The same-session independent `gpt-5.6-sol:high` review drove closure of OCR completeness, page-domain and provenance-tamper defects, then finished at `P0=0, P1=0, P2=0`; its broader read-only matrix passed `130` focused plus `580` adjacent tests.
- Phase C remains `in_progress`. The next safe action is one fresh empty isolated v12 run from the verified content-addressed copies with OCR enabled and current v7/v6 contracts, never reusing v11 as success. If both independent cohorts converge, verify receipt, registry group, source hashes and downstream evidence reconstruction before any Phase C closure. Keep port 8911 stopped until a later explicitly authorized runtime step.

## 2026-09-04 — Phase C v12 failed-pre-fix evidence and OCR budget correction

- Ran one new isolated v12 authority attempt from the 16 verified v11 content-addressed file copies; no real-project source tree was reopened and port 8911 remained stopped. PaddleOCR recovered the previously unreadable four-page stamped erratum, but four mixed native-text/scanned PDFs remained `needs_ocr` because twelve native excerpts consumed the complete evidence budget before OCR was considered.
- Both direct analysis cohorts failed closed after their bounded second attempt. MiniMax and GLM each marked partially extracted candidates usable; MiniMax remained `document_authority_candidate_not_usable`, while GLM then omitted one of sixteen candidates and failed coverage. The terminal state was `failed / not_promoted`, with zero registrations, no receipt and no source registry. Run `phase_c_rux_authority_v12_20260904.H9lAzw` is frozen as `failed_pre_fix` evidence and must never be resumed or treated as acceptance.
- Corrected the generic extraction order: when OCR is available, the twelve-locator evidence budget first reserves one slot for every native-zero page up to the bounded maximum, then uses the remaining slots for native excerpts. This exact corpus has only one to four zero-text pages per affected file, so no budget increase or project-specific exception is needed. A synthetic thirteen-page mixed document proves native evidence no longer starves its scanned page.
- Analysis prompts advanced to v8 and explicitly require every non-`ready+parsed` candidate to be unusable and unselectable; completed v7 primary/verifier pairs remain terminal replay evidence and mixed generations remain rejected. The workflow now stops before creating either model job whenever any role-capable candidate is technically or extraction-incomplete, and the API returns the existing plain-Chinese document-completeness guidance rather than a misleading running state or model terminology.
- Focused candidate/authority/job/admission/evidence/startup/repository regression passed `240` with `46` deprecation warnings; targeted Ruff and `git diff --check` passed. A governed same-session independent conference audited the failed database, all sixteen manifests and the remediation. It confirmed the deterministic budget-order root cause, that all affected files require no more than four OCR slots, that the new preflight would have prevented the wasted v12 calls, and that the failed run cannot be resumed across the v7→v8 generation boundary.
- Phase C remains `in_progress`. The next safe action is a new isolated v13 run from the same verified CAS files after this remediation is committed. Re-decompose with OCR, require preflight green before providers, then run MiniMax primary-v8 plus GLM verifier-v8 and autonomous conflict resolution. Only a terminal receipt/registry/source-hash reconstruction may support promotion; keep 8911 stopped.

## 2026-09-04 — Phase C v13 valid analyses and blind-review locator correction

- Executed one fresh isolated v13 run from the same sixteen verified CAS files after commit `c0d5d40`; no real-project source tree was reopened and port 8911 remained stopped. OCR reservation recovered every native-zero page needed by this corpus, the product preflight passed, and both direct v8 analyses completed on their first attempts. MiniMax full anonymous review also completed on its first attempt.
- GLM full review remained fail closed. Its first response considered all sixteen candidates but omitted a required evidence reference for one; its bounded repair covered all candidates but invented one locator ending `p1:b10` where the frozen candidate exposed `p1:b0` through `p1:b9` and then `p2:b0`. The terminal state was `failed / not_promoted`; no adjudication, registration, receipt or source registry was created. This is a mechanical evidence-copy defect, not authority convergence evidence, and v13 must not be resumed or promoted.
- Did not substitute a nearby locator or let Codex infer what GLM meant. Instead, the server-owned review coverage contract now supplies one deterministic authorized `required_locator_by_candidate` for every evidence-bearing candidate and directs each reviewer to copy that exact locator at least once; optional additional locators still must come from the frozen candidate. This keeps full blind candidate coverage while reducing free-form locator transcription.
- Review prompt identities advanced to v7. Exact completed v6 primary/verifier review pairs remain terminal replay-compatible for historical receipts; mixed generations fail closed and startup retires unfinished obsolete v6 jobs. Current analysis remains MiniMax/GLM v8 and adjudication remains v6.
- Focused and adjacent regression passed `240` with `46` deprecation warnings; targeted Ruff, Python compilation and `git diff --check` passed. Phase C remains `in_progress`. The next safe action after committing this correction is one new isolated v14 run from the same CAS bytes. It must pass OCR/preflight before providers, then independently complete v8 analysis, v7 blind review and v6 bounded adjudication; only verified receipt and registry evidence can close this authority slice. Port 8911 remains stopped.

## 2026-09-04 — Phase C v14 non-convergence and full-content relationship evidence

- Executed one fresh isolated v14 run from the same sixteen hash-verified CAS files. Both v8 analyses, both v7 full blind reviews and both v6 adjudications completed through the direct MiniMax-primary plus GLM-verifier product path. All four current main files converged; only protocol and eCRF supplementary-file classification remained different. The workflow correctly ended `needs_user_input / not_promoted`, with zero registrations, no receipt and no source registry. The frozen v14 result is evidence of non-convergence only and was not altered or promoted.
- A fresh-context `gpt-5.6-sol:high` mechanism review classified the remaining issue as evidence-supply plus adjudication-contract insufficiency, not proven genuine source ambiguity. Primary identity/version signals were present near front matter, while duplicate, historical comparison, operative erratum and current supplement classification required cross-document evidence that the twelve displayed excerpts did not represent.
- Added a generic, hash-bound full-extracted-content profile behind the bounded display excerpts. PDF/DOCX profiles include all extracted blocks; XLSX profiles canonically hash sheet structure and all parsed rows without exposing row values. Candidate relationships report only exact normalized equivalence or bounded sampled overlap and extraction coverage; they are descriptive and never select authority. Pure local-path OCR output is now empty/non-admissible, while meaningful text preceding a redacted path remains usable.
- Current adjudication advanced to v7. Each decision must provide a bounded rationale and candidate-locator-bound counter-evidence, retain complete primary/supplement/excluded disposition, and deeply cite only that role's selected or genuinely disputed candidates. Exact v6 pairs remain replayable and mixed generations still fail closed. No third model, Codex or OMP path was added to the deployed runtime.
- Focused candidate/authority/job/admission/startup regression passed `141` with `46` existing deprecation warnings; targeted Ruff, Python compilation and `git diff --check` passed. The same independent reviewer found two contract defects in focused-evidence validation; both were repaired, including a two-role role-local regression, and the final bounded recheck closed at `P0=0, P1=0`. Port 8911 remained stopped.
- Phase C remains `in_progress`. The next safe slice is one bounded autonomous MiniMax↔GLM critique-response round using anonymous v7 rationale, counter-evidence and deterministic relationship metadata. It must run at most once, resolve only on agreement, distinguish missing evidence from genuine residual ambiguity, and ask one narrow plain-Chinese question only after adequate evidence still cannot converge. Do not rerun the isolated cohort until that contract passes synthetic and independent review.

## 2026-09-04 — Phase C bounded anonymous critique-response contract

- Added one and only one post-v7 anonymous critique round to the deployed direct MiniMax-primary plus GLM-verifier job chain. The critique context hash-binds the prior adjudication context, reasoned options, counter-evidence and exact disputed candidates without provider/model identity. Agreement resolves automatically, including optional-role agreement that the document is absent; no third model, Codex or OMP path exists in product execution.
- Critique outputs must fully partition each unresolved role and cite every newly disputed or newly selected file using frozen locators. Residual disagreement becomes `evidence_incomplete` whenever any actually implicated file lacks a complete extracted-content profile; only complete evidence may yield one narrow Chinese question, which now names the small set of relevant files instead of asking for wholesale reselection.
- The workflow creates deterministic `critique:primary:v1` and `critique:verifier:v1` jobs at most once, retries only through the existing bounded terminal retry, continues polling through the plain-Chinese `cross_checking` state, and does not promote unresolved evidence. Promotion receipt v4 binds critique jobs/runs while v2/v3 deep replay remains accepted.
- Targeted Ruff, Python compilation, `git diff --check`, 229 focused authority/evidence/repository/startup/admission tests, 152 rendered-admission assertions and the Vite production build passed. A broader source-registry run passed 250 tests with one pre-existing unrelated frontend-fixture absolute-path assertion failure; no production source was changed for it. The independent review found four P1 chain/UX defects, all repaired; same-session recheck closed at `P0=0, P1=0` with 122 reviewer tests.
- No real-project source, model or service was run. Port 8911 remained stopped (`connect_ex=61`). Phase C remains `in_progress`; the next safe action is one fresh empty isolated current-contract run from previously verified CAS copies, followed by receipt, registry, source-hash and downstream evidence reconstruction only if both independent cohorts converge.

## 2026-09-04 — Phase C v15/v16 evidence-integrity checkpoint (lossless pause)

- Rechecked all sixteen previously isolated RUX CAS files before use; every SHA-256 matched its frozen batch manifest. No real-project source tree was reopened and no original file was changed.
- The v15 diagnostic used a new project ID and new AI database but intentionally copied the immutable v14 candidate evidence to exercise the newly added critique-capable workflow. Direct MiniMax and GLM independently completed both v8 analyses, both v7 blind reviews and both v7 adjudications. They converged without reaching the new critique round: protocol V1.3, IB V15, eCRF V1.1 and signed SAP PDF were selected, with three protocol supplements.
- v15 was not promoted. Atomic source registration rejected the selected stamped protocol erratum with `monitoring reference has no complete text locator set`. Its four alleged OCR excerpts were only `[local_path_redacted]`, proving that this pre-fix v14 evidence cannot be reused as valid OCR even though the two models could converge over it. No receipt or source-registry group was committed; v15 remains failed diagnostic evidence only.
- The v16 attempt then re-decomposed the same hash-verified CAS bytes through the current product composition root before any model job. Current code correctly converted path-only OCR output to empty evidence and stopped at `document_authority_evidence_incomplete`. The frozen current batch is `mmbatch_c57579d87b8a9e7ff495017e`; five candidate records contain native-zero pages whose Paddle OCR recovery ended `ocr_runtime_unavailable`, including the stamped erratum, both protocol carriers, the current IB and the eCRF completion guide. No MiniMax/GLM authority job was created in v16, so no model call was wasted after the preflight failure.
- Preserve both ignored run roots exactly as evidence: `runs/phase_c_rux_authority_v15_20260904` and `runs/phase_c_rux_authority_v16_20260904`. The v16 isolated runtime contains its own protected provider settings/credential store; it must remain ignored and must never be copied into a commit or report.
- No runner process remains. Port 8911 is stopped (`connect_ex=61`). Phase C remains `in_progress` and this is a lossless pause, not acceptance or completion.
- Next safe action on explicit continuation: inspect the v16 Paddle failure class and recover/reconcile any accepted remote OCR job if one exists, without launching another full authority cohort. Do not weaken the all-page evidence contract, do not ask the monitor to classify files or pages, and do not reuse v15 as success. Only after a fresh current-code decomposition has complete immutable OCR provenance may a new MiniMax-primary plus GLM-blind authority run proceed; promotion still requires receipt, registry, source-hash and downstream evidence reconstruction checks.

## 2026-09-04 — Phase C v17 autonomous authority promotion checkpoint

- Diagnosed the v16 OCR stop without reopening any real-project source tree. Paddle's hosted submission API had returned HTTP 200 with a nonzero provider error code; the adapter treated the missing job ID as an unknown outcome instead of a terminal rejection, so the configured GLM OCR fallback never ran. The adapter now classifies an explicit nonzero provider code as a rejected submission, never polls it, and invokes the fallback exactly once; a code-zero response with no job ID remains outcome-unknown and fail closed.
- Re-decomposed all sixteen hash-verified CAS documents in a new ignored isolated v17 runtime. Fourteen native-zero pages required OCR and all fourteen were recovered by the actual PaddleOCR-VL-1.6 route with immutable page/image/text hashes; no original source file was changed. The authority preflight then passed.
- Ran the deployed direct MiniMax-primary plus blind GLM-verifier workflow under the canonical project identity `rux_03_002_monitoring_raw`. Both analyses, full blind reviews, bounded adjudication and one critique round ran inside the monitoring harness without Codex or OMP. A partial-adjudication role-validation defect was repaired so critique validates each prior adjudication against the full adjudicated role set while exposing only the still-unresolved subset.
- The v2 critique prompt now applies a format-neutral carrier rule: for substantively duplicate files of one version, a signed, stamped or approved frozen carrier takes precedence over an unsigned or unstamped duplicate regardless of PDF/Word format; the duplicate is supplementary only when its body contains unique current normative changes. Both independent cohorts then converged automatically, so the monitor received no classification question.
- Atomic promotion succeeded for protocol V1.3 plus the stamped erratum, IB V15, eCRF V1.1 plus its comparison PDF and database-structure XLSX, and SAP V1.0. The editable clean erratum duplicate was excluded automatically. Promotion receipt SHA-256 is `04a666503158098f4d408f45674ce76020afdf8e06abca02381aca74f2036dd1`; all registry state and outputs remain inside the ignored v17 isolated runtime.
- Closed generic registration gaps exposed by the real shape: complete hash-verified OCR candidate locators may back a scanned PDF only when native extraction is empty and the exact locator set is complete; PDF/DOCX eCRF carriers use the common reference-document path; supplementary eCRF XLSX validates as eCRF; a structural eCRF with no STUDYID values is not assessed rather than warned, while present mismatches still fail; generic listing reuse preserves the project resolver's expected role.
- Focused and adjacent authority/OCR regression passed `232` tests; the full source-registry file passed `23`, and the frontend project/path-neutral contract passed directly, all with only existing deprecation warnings. Six changed Python production modules compiled and `git diff --check` passed. A governed fresh-context GLM review found one conditional P1: the new signed/stamped-carrier text also changed adjudication semantics under the old v7 identity. Current adjudication therefore advanced to v8, v7 became terminal replay-only, and the same reviewer rechecked the current tree at `P0=0, P1=0`. It also identified and closed a one-shot-iterator hash-validation gap and an adjacent self-triggering `/Users/` test fixture. Port 8911 remained stopped. Phase C remains `in_progress`: this closes the first-project document-authority slice, not five-project admission, canonical-fact generation, snapshot diff, visual acceptance or clinical acceptance.
- Next safe slice after this checkpoint is to consume the promoted authority registry in the existing isolated first-project pipeline and continue deterministic listing structure/mapping preparation. Preserve high-confidence automatic inference and candidate/fact separation; do not ask the monitor to confirm clear fields, do not run the remaining four projects in bulk, and do not start port 8911 unless a later browser/runtime step explicitly requires it.

## 2026-09-05 — Phase C first listing admission and authority-to-mapping bridge

- Admitted the user-designated locked Data Listing through the product's deterministic upload path into `runs/phase_c_rux_listing_v1_20260904`. The 17,013,973-byte original and isolated copy both hash to `81f47614ca6ab96c3d0a3e45d72ec49c98690fb49e8b574b1dc6b06f7e8259e3`; source size, mode and modification time were unchanged. Attempt `stg-9d37e5f33a1949d39eeb7c2b75c638a4` reached `profile_ready` with one file, 62 tables and 148,788 rows; the workbook physical manifest reconciled completely with no blocking finding. No row values were printed or written to the journal.
- The first read-only mapping-document readiness check correctly exposed a bridge defect instead of calling either model: an eCRF supplementary XLSX had been validated as eCRF but registered with a non-supplement source kind, making the otherwise deep-verifiable composite receipt structurally incomplete. Registration now preserves `ecrf_supplement` identity while the validation service explicitly treats both `ecrf` and `ecrf_supplement` as the same eCRF-shaped workbook class; blank structure templates remain not-assessed for project identifiers, while present mismatches remain blocking.
- A second generic performance defect surfaced during v19 reconstruction: operational source usability repeated the same deep authority receipt reconstruction once per text span. The check now deduplicates by source entry before validation. The pre-fix v19 diagnostic was terminated after 22 minutes at sustained CPU because it had loaded the old per-span loop and was superseded by the corrected run; its isolated directory remains intact and no source or accepted registry was removed.
- Replayed the already completed MiniMax/GLM authority evidence into a new empty v20 isolated registry using current code; no model was called. All seven entries passed complete composite-receipt checks, both eCRF supplements retained supplementary identity, and the mapping document gate resolved protocol, investigator brochure, eCRF and SAP as current. Across 11,018 registered document spans, the file-level readiness pass made 14 verifier invocations instead of repeating by span; the cached deep receipt reconstruction executed once. Promotion receipt SHA-256 is `15b91bc775ba6a3dfe2fc3a3d9d03d9bbb000a6857f79c0e7ad5f1c827acdf65`.
- Focused document-evidence, authority-promotion and content-validation regression passed `77`; the full source-registry file passed `23`, with only existing warnings. Phase C remains `in_progress`. The next safe action is to freeze the admitted listing plus current document-evidence packet into the dual mapping harness input, inspect only counts/hashes and relationship-profile completeness, then start one direct MiniMax-primary plus GLM-blind field-meaning cohort only if the deterministic preflight is green. High-confidence agreements are system-adopted; only medically material residual ambiguity may reach the user.
- Closed the remaining authority-precedence seams before mapping: a newer ordinary upload cannot displace a promoted authority set; if a previously promoted set becomes unusable, the role now fails closed instead of falling back to that upload; operational AI also rejects any source whose content-validation record is absent. The bootstrap path remains unchanged when no authority has ever been promoted.
- Python compilation and the focused source-registry/document-evidence/authority/content-validation matrix passed `103` with existing warnings only. The same GLM review session audited the final delta at `P0=0, P1=0`; its lower-priority test-depth suggestions do not block this slice. Port 8911 remained stopped. Phase C is still `in_progress`, and the next safe action remains the deterministic frozen-input mapping preflight described above.

## 2026-09-05 — Phase C frozen mapping input and first long-run checkpoint

- Created a new ignored isolated mapping runtime without changing the v17/v20 evidence roots. It combines the corrected v20 seven-entry registry and validation database with a SQLite snapshot of the v17 MiniMax/GLM authority-job evidence; the v20 receipt remains structurally complete and deep-verifies against those original job records. The admitted Listing workspace was copied into the product's expected isolated project layout, and encrypted runtime credentials were copied without reading or logging their values.
- The deterministic mapping preflight passed twice with byte-identical output. The frozen input contains 62 tables, 1,495 fields and 148,788 rows; 360 bounded same-table relationships and 256 cross-table relationships; protocol, investigator brochure, eCRF and SAP are all current, with one protocol and two eCRF supplementary bindings. Frozen payload SHA-256 is `6c8834538c24a96d29ccfdf5d07c8487d760a393985718b71f6cf3d4277eebb4`; profile SHA-256 is `9eee8bfc3973f2f5659e0c5133dcf245ec47e5339eb5b2c952e8f59e62fe98a6`. No row value was printed or journaled.
- Started exactly one direct product-harness cohort: `cms-smk/MiniMax-M3` primary plus `zhipu-coding-plan/glm-5.3-flash` blind verifier, with no OMP or Codex in field interpretation. At the 120-minute hard wait, durable state held 151 jobs per cohort: primary 132 completed, 8 failed, 7 queued and 4 lease-running; verifier 65 completed, 84 queued and 2 lease-running. The controller exited and no local worker process remained; unfinished jobs were not discarded.
- All eight primary failures were fail-closed `invalid_ai_output` after the single controlled repair: four repair responses returned only a standards-reference object, one returned only a field-mapping object, two populated optional standards-reference fields with blank strings, and one assigned meaning to an all-empty column. The repair contract now requires the complete five-key outer envelope, exactly one complete candidate, `standards_reference=null` when no named standard is supported, and `unmapped` for all-empty fields. It remains one repair only and advances only the mapping repair envelope to `json-repair-2`; the v19 main semantic prompt and all evidence/medical validators remain unchanged.
- Python compilation, `git diff --check`, three focused repair tests and 537 mapping/service regressions passed. A governed independent GLM review reproduced broad tests and closed at `P0=0, P1=0`; it confirmed the change narrows output shape without weakening evidence, medical, user-confirmation or one-repair boundaries. Phase C remains `in_progress`; after commit, retry only the eight exact terminal failures through the repository retry API, recover expired leases, and continue the same durable cohort rather than resubmitting completed chunks. Port 8911 remains stopped.

## 2026-09-05 — Phase C mapping cohort aggregation and strict-repair checkpoint

- The continued durable mapping cohort reached terminal worker state without resubmitting completed chunks. The GLM blind verifier completed all 151 jobs; MiniMax completed 145 and retained six strict failures. Three failures were malformed or empty provider JSON, and three remained structurally incomplete after the single controlled repair. No failed output was accepted, no candidate was converted to a fact, and no user question was created.
- Diagnosed the apparent zero-candidate projection as a cohort-selection defect: each deterministic/model chunk can carry its own frozen revision, but `_latest_job_cohort` treated one chunk revision as the whole cohort identity. Cohort selection now uses the prompt generation plus the shared `full_profile_sha256`, so the isolated runtime resolves exactly 151 primary jobs and 151 verifier jobs. Every same-prompt member must have a readable shared-profile identity or the entire cohort fails closed; older prompt generations and different profiles remain excluded.
- Tightened only the generic mapping JSON-repair instruction: every returned field mapping must contain every required output-schema key and a non-empty `user_action`. The one-repair limit, v19 semantic prompt, evidence binding, all-empty-field rule and medical validators remain unchanged; no study-, disease-, drug- or column-specific exception was introduced.
- Python compilation, `git diff --check`, 547 service/core mapping tests and 308 broad mapping tests passed. A governed independent GLM review approved the change at `P0=0, P1=0` and identified three P2 hardening/coverage items; all were closed with strict same-prompt identity failure, prompt-version isolation coverage, missing-identity coverage and a corrected reconciliation comment. A same-session optional continuation failed terminally after its bounded retry and produced no contrary finding; it was not replaced by another model.
- Phase C remains `in_progress`. After this checkpoint is committed, retry only the six exact MiniMax terminal jobs once through the existing repository retry path, then resume autonomous primary/verifier reconciliation only if all 151 primary jobs complete. Do not expose structural failures to the monitor, do not weaken validation, and keep port 8911 stopped.

## 2026-09-05 — Phase C dual mapping reconciliation lossless pause

- Retried only the six failed MiniMax first-pass jobs through the repository retry path; five completed immediately and the final DUH chunk completed on one evidence-justified final retry. Both independent first-pass cohorts are now terminal at 151/151 jobs and 1,495/1,495 field candidates. No failed output was accepted and no fact was generated.
- Adopted the complete MiniMax candidate set into isolated draft `monmapdraft_768af1357bc0f4cefee4055b3c71`. The draft contains 1,495 fields and initially exposed only two primary-side questions. Full repository-backed GLM reconciliation found complete coverage with zero blocked fields but 700 semantic divergences, so automatic confirmation correctly stopped and did not send bulk review to the monitor.
- Started the existing anonymous dual-adjudication path for those divergences. The first 120-minute hard wait exposed a general repair-envelope ambiguity: models could confuse the inner `monitoring_mapping_dual_adjudication_v1` version with the required outer `monitoring_ai_v1`, or omit exact candidate/field keys. Repair envelope `json-repair-3` now requires the four outer identity values to be copied from `output_schema`, complete candidate keys, exact required field pairs, non-empty action text and a concrete Chinese question only when user decision is truly required. The semantic adjudication prompts and medical validators were not weakened. Core/service regression passed 547 before commit `122461e`.
- After retrying only the 20 terminal adjudication jobs and resuming the durable queues, the user requested a lossless pause. At pause, MiniMax adjudication holds 80 completed and 7 strict `invalid_ai_output` failures; GLM adjudication holds 62 completed, 23 queued and 2 interrupted running leases. Those two leases must be allowed to expire and be reclaimed on resume. No local worker or service process remains, and completed adjudication jobs must not be resubmitted.
- The user-requested one-time `gpt-6-astra:high` stage review was not launched: current `native-admit --explicit-route` rejected `gpt-6-astra` as an unsupported Codex subAgent model, and the native tool catalog does not offer it. No substitute model was used. Re-attempt only after the executable model catalog supports Astra; keep the review read-only and let Codex decide whether to adopt its recommendations.
- Phase C remains `in_progress`; this is a lossless pause, not mapping confirmation, fact generation, clinical acceptance or Phase completion. Next safe action: verify no worker remains, reclaim the two expired GLM leases, classify the seven MiniMax terminal failures under `json-repair-3`, retry only failures that have a bounded evidence-based recovery path, then drain the remaining adjudication queue. Re-run autonomous reconciliation and surface only medically material residual questions after both cohorts are terminal. Keep port 8911 stopped.

## 2026-09-05 — Phase C dual mapping adjudication and one-question product boundary

- Reclaimed the interrupted verifier leases and resumed only the existing durable adjudication jobs. Seven MiniMax terminal failures were classified as bounded output-contract defects and retried through the repository path; one remaining malformed outer envelope received one evidence-justified final retry. Both direct product cohorts then reached 87/87 completed second-pass jobs. No OMP or Codex participated in field interpretation, no failed candidate was accepted and no fact was generated.
- Full deterministic reconciliation covered all 1,495 fields. The former rule incorrectly converted every second-pass reviewer disagreement into user work; the corrected policy keeps MiniMax as the declared primary analyst after it has received the anonymous GLM challenge, preserves continuing GLM disagreement as durable dissent and escalates only an explicit evidence-bound user-only decision. The result is 1,494 system-handled fields and one medically material residual choice concerning planned versus actually administered dose semantics.
- Added replay-safe receipts and immutable first-pass reconstruction so a partially patched draft cannot create a second semantic cohort. Exact completed payload-equivalent cohorts may be reused only when all job payload, revision, prompt, provider, profile and requested-model identities match. Reconciliation receipt schema advanced to v2; exact duplicate relationship labels are mechanically collapsed. Deep frozen-revision verification is cached once per distinct revision. A no-op replay returned `complete / 699 resolved / 1 question` without creating any new model job.
- Strengthened the next adjudication prompt generation: supplied eCRF, protocol, investigator brochure/IB, SAP and same-/cross-table evidence must be exhausted internally; a model may not ask the monitor to re-read those files or expose sheet names, field codes or engineering identifiers. Primary/verifier prompt identities advanced to v4/v2; startup keeps both current identities active while preserving v3/v1 completed terminal evidence as replay-only. Existing durable receipts are checked before submission, so replay does not launch the new prompt over already decided fields.
- Simplified the residual confirmation surface for a nontechnical Chinese medical monitor. The default card hides table/column codes, asks one direct medical question, states the system's suggested dose interpretation as the one-tap answer and offers one plain alternative for a different meaning. The public projection now renders the question without CRF lookup instructions or source identifiers; the full engineering field list remains collapsed.
- Verification passed: 852 adjacent Python tests, 17 pure frontend state tests, 153 rendered-wizard assertions, Vite production build, Python compilation, fatal Ruff and `git diff --check`. The isolated runtime still reports one unanswered question; mapping remains unconfirmed and canonical facts remain absent. Port 8911 is stopped and no mapping worker remains.
- The requested one-time `gpt-6-astra:high` review remains unavailable: explicit native admission rejects Astra even though the deferred tool catalog advertises it. The admission boundary was not bypassed and no substitute model was used. Phase C remains `in_progress`; next safe action is the monitor's single planned-versus-actual dose choice, followed by mapping confirmation and deterministic fact-generation preparation. Browser/visual acceptance remains a later explicit runtime step and must not be claimed from render tests alone.

## 2026-09-05 — Phase C fact-generation preflight hardening

- Kept the one medically material dose question unresolved and did not generate any real-project fact. The real listing and promoted document evidence were not reopened; this slice used generated fixtures only.
- Made multi-table fact materialization batch-safe. Every snapshot, source digest, locator index and complete mapping is now validated across the full batch before any fact artifact is written or any snapshot becomes baseline-eligible. A generated two-table regression proves that a later incomplete mapping cannot leave an earlier table appearing accepted or create a ready summary.
- The completion screen now remains visible after deterministic fact generation, summarizes the number of tables, records and data items prepared, and waits for the monitor's explicit `进入医学监查` action instead of navigating away immediately. Internal identities remain hidden from the primary surface.
- Verification passed: 80 adjacent Python admission/mapping/fact tests, 154 rendered-wizard assertions, 17 mapping-confirmation state tests, 47 admission integration assertions, Vite production build, Python compilation, fatal Ruff and `git diff --check`. The existing Vite chunk-size warning is unchanged and unrelated.
- Phase C remains `in_progress`. Next safe action is still the monitor's single planned-versus-actual dose choice. Only then may the isolated mapping be confirmed and deterministic facts generated, followed by exact-cell spot checks. Keep port 8911 stopped; do not run the remaining four projects or claim browser/clinical acceptance.

## 2026-09-05 — Phase C automatic source-alignment evidence

- Reused the existing per-value locator round trip instead of adding a second manual spot-check workflow. Every generated value already resolves against its hash-bound original location before materialization; the ready summary now persists that checked-value count and the status path cross-checks table, row and value totals against the immutable fact-set manifests.
- The completion surface tells the monitor how many original data positions the system checked and explicitly says no item-by-item inspection is needed. This adds no new endpoint, model call or user decision and remains compatible with prior ready summaries.
- Generated-fixture verification passed: 81 adjacent Python admission/mapping/fact tests, 155 rendered-wizard assertions, 17 mapping-confirmation state tests, 47 admission integration assertions, Vite production build, Python compilation, fatal Ruff and `git diff --check`. No real-project fact was generated and no medical-writing source or asset was touched.
- The one medically material planned-versus-actual dose question remains unanswered. Phase C stays `in_progress`; keep port 8911 stopped and generate real facts only after that single answer.

## 2026-09-05 — Phase C audience-safe fact summary

- Removed internal materialization counters from the product response while retaining them in the persisted audit summary. The monitor now receives only table, record, data-item and automatic source-check counts; no unmapped/derived processing vocabulary reaches the admission client.
- Generated-fixture and adjacent verification passed: 81 Python admission/mapping/fact tests, 155 rendered-wizard assertions, 47 admission integration assertions, Vite production build, Python compilation, fatal Ruff and `git diff --check`.
- No real-project state changed and medical writing remained untouched. The single dose-semantics answer is still required before mapping confirmation and real fact generation; port 8911 remains stopped.

## 2026-09-05 — Phase C evidence-generation-aware focused re-review

- Re-examined the isolated first-project evidence instead of asking the monitor to interpret `EX2.EXDOSE1`. The prior fixed two-column window omitted a nearby execution-status field, and the global same-table relationship budget was exhausted in table order before later domains received a fair share. Same-row evidence now selects the nearest seven populated fields, and same-table relationships are allocated round-robin across domains. The focused adjudication profile keeps every relationship touching the question field while its counterpart remains read-only context.
- Durable adjudication replay is now bound to the current primary/verifier prompt generation. Historical escalation receipts remain immutable evidence, but a newer evidence generation creates a new business identity and resolution receipt instead of silently reusing the old user question. Current focused prompt identities advanced to v5/v3; completed v4/v2 jobs remain terminal history only.
- Read-only recomputation over the isolated listing preserved 62 tables and 1,495 fields, exposed `EXYN1` with date/time/timepoint context for the dose field, and changed the profile hash. No model or service was started during that diagnostic. Python compilation, `git diff --check` and 585 mapping, repository, startup and service regressions passed.
- The first focused submission correctly stopped before any model call because the upgraded profile hash no longer matched the historical full-cohort jobs. Reconciliation now permits those completed first-pass candidates only when the immutable listing source hashes, source bindings and complete document-evidence packet still match; strict current-profile verification remains mandatory for newly submitted adjudication jobs. The isolated historical reconciliation is readable again at 700 divergences and zero blocked fields without re-running 1,495 fields.
- A subsequent preflight exposed that generation-binding every prior receipt would reopen all 700 historical disagreements. The process was interrupted immediately after queue creation; all 174 v5/v3 rows (87 per cohort, including one claimed row each) were contract-retired as `stale_input`, no candidate was accepted and no draft field changed. Receipt selection now preserves 699 prior system resolutions while deliberately excluding only historical `escalated` decisions from suppressing a new review. A read-only real-runtime projection confirms exactly one pending pair: `EX2.EXDOSE1`.
- The requested `gpt-6-astra:high` stage review remains unavailable: live explicit native admission reports that Astra currently accepts only low or medium effort. No effort downgrade or substitute model was used. Phase C remains `in_progress`; after commit, the next safe action is exactly one fresh MiniMax-primary plus GLM-blind focused review for `EX2.EXDOSE1` in the existing isolated runtime, with port 8911 stopped and no full-cohort replay.
