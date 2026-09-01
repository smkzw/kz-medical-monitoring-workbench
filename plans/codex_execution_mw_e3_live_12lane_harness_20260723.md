# Codex Execution Plan: mw_e3_live_12lane_harness_20260723

Objective: Rebuild and prove an isolated 12-lane real-product-AI E3 harness for medical writing across RA, AD and UC, Phase I/III, from-zero/synopsis-import, preserving stable runtime and collecting auditable service receipts

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Define 12-lane design/input oracle manifest, stable-runtime non-contamination contract, model/service identity schema, and deterministic canary/release gates | `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01.md` |
| `worker_02` | Implement isolated parent/child orchestration with per-lane runtime, API/Vite/CDP/browser profiles, immutable input/output manifests, crash recovery, and cleanup | `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02.md` |
| `worker_03` | Implement real workflow driver for project creation, source import, CT.gov retrieval/download/parse/translation, corpus admission, chapter candidates/adoption/rewrite, citations, tables/figures and DOCX export using product APIs and UI where required | `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03.md` |
| `worker_04` | Implement evidence collection and QC including server-side product-AI receipts, all-chapter completeness, reference links, SVG/scale embedding, DOCX package checks, browser artifacts, failure injection, and Word-native acceptance handoff | `runs/execution/mw_e3_live_12lane_harness_20260723/worker_04.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_e3_live_12lane_harness_20260723/manager.md` |

## Sequence And Ownership

1. Manager planning pass first. It must inspect current harness and context, then provide the exact
   ownership map, interface schema, dependency order, red tests and stop conditions. It performs no
   product-AI calls and no implementation in this pass.
2. Worker 01 runs serially and owns only the lane/input/service-evidence contract: the config file plus
   a new task-scoped acceptance/manifest artifact. It must replace PsO with UC and reject every
   phase/type-mismatched source rather than preserve override fixtures.
3. After Worker 01 is accepted, Workers 02-04 may proceed where their write sets do not overlap:
   Worker 02 owns parent orchestration and new runtime-isolation helpers; Worker 03 owns child/pipeline/
   contract-probe workflow driving; Worker 04 owns structure/behavior QC and new evidence/DOCX/Word
   handoff validators. Any shared-file need returns to manager instead of concurrent editing.
4. Manager second pass reviews actual diffs/tests, requests same-session targeted repairs, then produces
   a canary command. Codex reads source and runs deterministic canary/structure tests.
5. Only after Qoder W5 audit is READY and Codex accepts the harness may a one-lane real product-AI
   canary run. Twelve-lane execution begins only after that canary proves isolation and receipt capture.

## Acceptance Gates

- `G0`: prompt preflight, source identities/hashes, stable-runtime baseline and no credential output.
- `G1`: exactly 12 RA/AD/UC x I/III x two-entry lanes; no phase/type relabelling and all required design
  pressures genuinely supported by source evidence.
- `G2`: per-lane runtime/API/Vite/CDP/browser isolation, asynchronous orchestration, crash resume and
  exact cleanup ownership.
- `G3`: product workflow uses current durable APIs and exact job/result artifacts for every long step;
  workers do not author content in place of product AI.
- `G4`: every included chapter is generated/reviewed/adopted; applicable tables, SVG flowchart, scales,
  citations and reference reindexing are covered; excluded dynamic chapters are justified by confirmed
  design, not silently skipped.
- `G5`: DOCX OOXML checks plus later Microsoft Word native open/navigation/render acceptance; export
  styling remains a separate E5 gate and is never inferred from API success.
- `G6`: stable runtime before/after hashes match and each lane has a complete immutable evidence bundle.

## Codex Acceptance

Codex verifies the manager plan, all current diffs, deterministic behavior tests, real canary receipts,
stable-runtime hashes, browser workflow and Word-native outputs. A model completion marker is never
acceptance. Any production-source defect discovered by this harness is fixed in a separate bounded
remediation task and the affected lane is rerun from a clean task-owned state.
