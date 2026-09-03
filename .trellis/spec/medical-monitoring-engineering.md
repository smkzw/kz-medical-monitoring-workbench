# Medical Monitoring Engineering Standard

## Authority

- Current requirements come from `reviews/medical_monitoring_engineering_review_20260901.md`, the v1.2 design amendment, and implementation plan v2.0.
- Git is the version and integrity authority. Trellis tasks, specs, and journals are the only new engineering progress records; do not add pause, recovery, or acceptance records under `context/` or `reviews/`.

## Protected boundaries

- Treat the five real study source directories as read-only. Work only from isolated copies and write all analysis output to isolated directories.
- Do not change the medical-writing subsystem routes or assets under `services/api/app` except for a separately authorized medical-writing task.
- Ask before irreversible deletion of archived data or old database tables. Deleting versioned duplicate source trees after migration is allowed only when tests are green and git can restore them.
- Preserve unrelated work in the shared worktree.

## Target structure and migration

- `packages/medical_monitoring/` is the only authoritative backend package. Organize it as `domain`, `graph`, `intelligence`, `risks`, `projections`, `reports`, `runtime`, and a thin `api` layer.
- `services/api/app` keeps one thin medical-monitoring router mount; do not add domain logic to `main.py`.
- `frontend/src/features/medical-monitoring/` is the only current medical-monitoring frontend. Keep medical-writing UI untouched.
- Move behavior before changing it. For each layer: trace imports, move code and behavior tests, repair imports, run focused tests, then commit. Do not combine migration and redesign in one commit.
- When splitting an authority module, keep its established import path as the compatibility facade and re-export every existing public symbol. Validate both the authoritative package and live compatibility consumers; do not duplicate new modules into frozen POC trees merely to satisfy obsolete source-layout or isolated-path gates.
- Keep legacy `monitoring_*` LOOP/assurance/daily-run code read-only during Phase B unless a route collision requires the smallest isolation change.

## Code constraints

- Apply Ponytail full: reuse existing code, prefer the standard library and platform features, avoid speculative abstractions, and fix shared root causes.
- Aim for no more than 800 lines per source file; 1500 lines is a hard limit. Split by cohesive domain, not arbitrary line counts.
- Externalize fixture literals longer than 200 lines to data files such as JSON.
- Do not add a dependency when an installed dependency, native browser capability, CSS, or the standard library covers the requirement.

## Medical semantics and language

- Preserve candidate-versus-fact separation, orthogonal publication state, accepted snapshot and dual-baseline semantics, stable risk identity/lifecycle, evidence provenance, AE/MH under-reporting semantics, and three-part Query drafts (`basis + finding + action`).
- Do not expose internal or engineering terms such as `formal fact`, `candidate signal`, `read-only`, manifest identifiers, digest labels, or backend state names in the user interface.
- Use concise native Chinese for a senior medical monitor. Prioritize medium/high risk information, source drill-down, and clear project/center/subject chronology.
- Patient Journey uses one horizontal visit/time axis with typed event and risk markers; selecting a marker reveals the event details and source location.

## Anti-overfitting and model use

- Never hardcode project names, proprietary listing columns, drugs, indications, scales, risk patterns, or one vendor's table shape into the shared core.
- Real study documents are generalization challenges and evidence sources, not a product constant library.
- Use the independent harness/model for semantic mapping and protocol/drug/disease interpretation. Product code owns prompts, schemas, deterministic evidence checks, and workflow orchestration.
- For first-listing semantic decomposition, use direct `cms-smk/MiniMax-M3:high` as the primary analysis and direct `zhipu-coding-plan/GLM-5.3-flash:high` as a blind, full-coverage verifier. Do not wrap either product call in OMP. Local `MTPLX/Qwen3.8-next-flash` is allowed only after both remote routes have auditable terminal-unavailable evidence and can never be labelled a dual-model pass.
- Dual-model agreement covers only the frozen evidence packet. It cannot compensate for parser omissions: physical workbook completeness, cross-sheet relationships and current-document evidence must close before automatic mapping confirmation.
- Relationship evidence is aggregate, de-identified and recomputable. Unfamiliar labels receive neutral statistical-pair evidence rather than being dropped or assigned a guessed semantic type; sampled evidence must state its observed-row denominator, and cross-table overlap is a candidate join signal rather than a confirmed mapping.

## Verification

- Prefer behavior tests. Do not add frozen file-hash assertions, digest-refresh gates, optimizer/hash-seed matrices, or bulk synthetic case-count gates.
- A frozen POC import-path, file-count, source-hash or create-only allowlist failure is migration evidence for B7, not permission to repin an obsolete gate. Record it separately from live behavior failures.
- Verification order: real-data spot check, representative behavioral test, then larger synthetic coverage only when justified.
- During a migration, run the smallest focused test first and broaden only across shared contracts.
- For user-facing work, verify the actual workbench in `ego(lite)` at the user's primary wide-screen resolution. Mobile-specific work is out of scope.
- Stage boundaries require one independent fresh-context review and user confirmation; stage-internal work uses Codex self-checks and focused tests.
