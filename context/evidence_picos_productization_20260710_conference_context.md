# Conference Context: evidence_picos_productization_20260710

Created: 2026-07-10 18:23:22
Objective: Audit and productize the Evidence Research and Protocol Design subsystem using real CRSwNP and a second real indication, with auditable evidence lifecycle, versioned PICOS decisions, AI revision interaction, medical approval, and typed medical-writing handoff.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- `records/active_slices/evidence_picos_productization_20260710/SOURCE_AUDIT.md` is the bounded source inventory and current-state audit prepared by Codex from authorized read-only project files.
- `records/research/evidence_design_external_benchmark_20260710.md` contains the official-product interaction benchmark.
- Current implementation: `services/api/app/evidence_design_manifest.py`, `services/api/app/evidence_picos_workflow.py`, `services/api/app/project_source_manifest.py`, `packages/contracts/workbench_contracts/models.py`, `frontend/src/App.jsx`, `frontend/src/styles.css` and `frontend/AGENTS.md`.
- CRSwNP source: master CSVs and original source directories under the authorized CRSwNP competitive-research root. Existing report/HTML/PPT outputs are QA references only.
- PNH source: `pnh_competitor.sqlite`, its evidence registry, raw registry snapshots and normalized source documents. Existing report/HTML outputs are QA references only.
- Participant models may read only the explicit workbench files named in their prompt. They must not open the external project roots directly.

## Scope

- In scope: two-indication adapter/registry architecture; project-scoped route binding; search-task, evidence-item, screening, extraction, appraisal, conflict and update-diff state models; versioned PICOS decisions; anchored user/AI revision interaction; medical approval; typed writing handoff; desktop interaction architecture; persistence and verification plan.
- Out of scope: final clinical or regulatory conclusions; live-web completeness claims; unapproved protocol prose; editing original project files; replacing literature-review methodology, PV, statistics or medical approval; mobile-driven feature reduction.

## Success Criteria

- CRSwNP and PNH are independently routable with no project-specific fallback or semantic leakage.
- One normalized workflow supports CSV-backed and SQLite-backed evidence packages while retaining their source provenance.
- Saved searches, candidate pool, screening, extraction, appraisal, synthesis and update-diff states have explicit contracts and audit semantics.
- PICOS decisions are versioned and evidence-anchored; alternatives, assumptions, medical rationale and unresolved items remain visible.
- AI interaction is independent-provider only, fail-closed, source-bound and revision-oriented; Codex is never a runtime dependency.
- Only a medically approved typed PICOS snapshot can be handed to medical writing.
- Desktop UI is dense, clear and operational; tables are filtered/paged rather than silently truncated.
- Tests cover two real indications, invalid cross-project access, restart persistence, privacy, state transitions and writing-handoff gates.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-10 18:23:22: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-10 18:29 CST: Codex audited existing Evidence/PICOS code and selected PNH as the second real indication because it provides a materially different SQLite/evidence-registry source shape.
- 2026-07-10 18:32 CST: Codex bounded source counts, routing gaps, desktop interaction requirements and rejected shortcuts in `SOURCE_AUDIT.md`.
- 2026-07-10 19:18 CST: The first Reasonix DeepSeek Pro main-venue run formed a substantive review but failed before writing because the stream stalled; Codex preserved the failure evidence.
- 2026-07-10 19:22 CST: Codex created a compact review packet, corrected the guard prompt format after preflight rejected the first draft, and passed preflight without warnings.
- 2026-07-10 19:24 CST: The controlled Reasonix DeepSeek Pro retry completed, authorized the implementation slice and added acceptance checks for stable IDs, concurrency, AI anchors, typed handoff, adapter diagnostics and persistence-layer gates.
- 2026-07-10 19:26 CST: Codex rejected the main review's unsupported inference that GLM preferred formal GRADE; GLM explicitly recommended an internal three-level scale while leaving GRADE as a user choice. Conference closed as pass and implementation resumed without a soft pause.
