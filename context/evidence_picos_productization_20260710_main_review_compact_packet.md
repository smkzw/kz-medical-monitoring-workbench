# Evidence/PICOS Main-Venue Compact Review Packet

Date: 2026-07-10
Conference: `evidence_picos_productization_20260710`
Role: Reasonix CLI `deepseek-pro` main-venue reviewer

## Objective

Decide whether the completed participant conference plus Codex verification is sufficient to begin production implementation of a multi-indication Evidence Research and PICOS Protocol Design workspace. The implementation must support real CRSwNP and PNH source packages, auditable evidence lifecycle, versioned PICOS decisions, independent-runtime AI revision, medical approval and typed medical-writing handoff.

## Conference Convergence

Five independent participant reviews and the Hermes sub-venue chair converged on five production blockers:

1. Evidence source routing and root selection are hard-coded to CRSwNP.
2. Shared PICOS questions, options and candidate labels leak CRSwNP semantics into other indications.
3. PICOS decisions are stored in JSONL, which is inadequate for versioning, concurrency, audit and approval.
4. The medical-approval field is structurally present but functionally always blocked.
5. The AI revision-thread field is structurally present but not connected to a persisted, anchored revision workflow.

The frontend also silently truncates evidence collections with five `.slice(0, N)` calls. PNH scale makes eager full-manifest loading unsuitable.

## Codex Independent Verification

Codex directly inspected the active code, tests, PNH SQLite and current rendered Evidence/PICOS page.

- PNH SQLite contains 26 products, 70 trials, 115 trial arms, 1,011 endpoints, 3,069 efficacy rows, 8,770 safety rows, 41 publications, 23 regulatory-status rows, 163 development-history rows and 1,359 baseline rows.
- PNH `evidence_registry` exists but contains zero rows. A PNH adapter therefore must create stable evidence identities from actual source tables, initially `trials`, `publications` and `regulatory_status`, while preserving source references. It must not depend on `evidence_registry`.
- The configured PICOS JSONL runtime file does not exist, so there is no live legacy data set that blocks migration. A defensive importer may remain, but is not a P0 dependency.
- The frontend limits products to 12, trials to 12, results to 14, documents to 10 and warnings to 4 using silent client-side slices.
- Shared frontend configuration still contains CRSwNP-specific candidate labels and source inputs.
- Current Evidence/PICOS baseline tests pass: 7 passed.
- The existing rendered page is a long report-style surface with PICOS before evidence review, rather than an evidence-first operational desktop workspace.

## Codex Architecture Adjudication

Codex proposes the following implementation decisions:

1. Use the existing shared `SqliteRuntimeStore`, migrate schema from v3 to v4 and keep one governed runtime database. Do not create one database per project.
2. Add a typed package-adapter registry keyed by canonical project/package identity. Indication-specific source handling stays inside adapters; the frontend never branches on indication.
3. Build CRSwNP candidates from its document index and PNH candidates from trial, publication and regulatory rows, with stable source-scoped IDs.
4. Replace eager full-manifest transfer and client slicing with paged list/detail endpoints, server-side filters and explicit result counts.
5. Move PICOS questions/options into package-scoped configuration and persist versioned immutable snapshots plus mutable working state in SQLite.
6. Wire snapshots into the existing approval/audit framework. Writing handoff is fail-closed and allowed only from an approved immutable PICOS snapshot.
7. Persist AI revision threads as anchored proposals. AI cannot directly overwrite evidence extraction or PICOS decisions; a medical user must accept, reject or return a proposal for revision.
8. Rework the desktop page as an evidence-first studio using existing tokens and visual language: saved search/queue rail, evidence canvas, and an anchored detail/PICOS/AI side panel. Remove silent truncation. Mobile feature parity is not a requirement.

## User Decisions Still Open

The following choices remain product decisions rather than technical blockers:

- two-tier versus three-tier medical approval roles;
- internal three-level evidence-quality rating versus formal four-level GRADE-like rating;
- evidence appraisal as a dedicated top-level view versus a panel/state inside evidence review;
- deduplication as a dedicated view versus an evidence-item candidate state.

Nonblocking P0 defaults proposed by Codex: two-tier approval with schema extensibility for a third tier; appraisal as a distinct evidence-review panel; deduplication as a candidate state; use an internal three-level quality rating unless the user explicitly selects formal GRADE-like grading.

## First Implementation Slice And Verification Obligations

The first vertical slice should cover adapter routing, PNH candidate generation, SQLite v4 persistence, paged Evidence APIs, package-scoped PICOS configuration, versioned snapshots, medical approval, writing handoff and anchored AI revision records. It must be tested against both CRSwNP and PNH.

Required Codex verification before acceptance:

- no cross-project fallback or cross-indication semantic leakage;
- deterministic stable IDs for both adapters and no dependency on empty PNH registry;
- pagination, count, filter and detail behavior without silent truncation;
- restart persistence, migration from SQLite v3, optimistic concurrency and audit history;
- legal state transitions for screening, appraisal, PICOS snapshots, approval and handoff;
- fail-closed behavior when AI provider is unavailable or returns incomplete provenance;
- browser interaction and visual QC on the actual desktop runtime using realistic CRSwNP and PNH records;
- regression tests for existing monitoring, enrollment review and medical-writing persistence.

## Prior Main-Review Attempt

The first Reasonix `deepseek-pro` run read the full participant packet and produced substantive reasoning, but the stream stalled immediately before writing the required output file. The process ended with `stream stalled - no data for 2m0s`. This compact packet is the single controlled retry and preserves that failure as conference evidence.

## Required Review Output

Write a concise review using exactly these headings:

1. `# Main-Venue DeepSeek Pro Review: evidence_picos_productization_20260710`
2. `## Inputs Reviewed`
3. `## Main-Venue Critique`
4. `## Remaining Disagreements`
5. `## Required Codex Verification`
6. `## Rerun Or Redo Recommendations`
7. `## Final Recommendation To Codex`

Separate verified evidence, inference, recommendation and uncertainty. Decide whether Codex may begin the proposed implementation slice. Do not claim final clinical, regulatory, visual or current-web authority.
