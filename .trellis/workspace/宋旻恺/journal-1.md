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
