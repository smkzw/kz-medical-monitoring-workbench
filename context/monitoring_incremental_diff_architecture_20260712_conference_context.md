# Conference Context: monitoring_incremental_diff_architecture_20260712

Created: 2026-07-12 10:33:20
Objective: Review two-real-project monitoring listing batch-diff evidence, challenge row-key/schema/persistence/audit boundaries, and recommend a production-grade incremental diff architecture and TDD slice without reading raw clinical row values.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- The user's project-specific override assigns every future Hermes sub-venue chair/review to exact `aishuo / MiniMax-M3`.
- Independent participants are `buddy / deepseek-v4-pro`, `opencode-go / mimo-v2.5`, and `buddy / glm-5.2`.
- The aishuo chair starts only after participant outputs complete or terminally fail. No silent chair substitution is allowed.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/monitoring_incremental_diff_20260712/SOURCE_AUDIT.md`
- `records/active_slices/monitoring_incremental_diff_20260712/EXTERNAL_RESEARCH.md`
- `records/active_slices/monitoring_incremental_diff_20260712/LOOP_LEDGER.md`
- `services/api/app/monitoring_intake.py`
- `services/api/app/listing_file_parser.py`
- `packages/contracts/workbench_contracts/models.py`
- Raw clinical row values, original Excel bytes and local source paths are excluded from model read lists.

## Scope

- In scope: batch identity, schema/header normalization, per-sheet row-key profiles, uniqueness gates, row/cell diff semantics, immutable lineage, persistence/CAS/idempotency, preview-vs-commit workflow, audit, CM/IP boundary, TDD decomposition and failure modes.
- Out of scope: reading raw row values, deriving medical conclusions, changing production code, frontend visual design, browser acceptance, auto-approving schema/key mappings or opening real-project upload before implementation verification.

## Success Criteria

- Identify every P0/P1 defect in the existing demo intake/diff path.
- Recommend a data model that preserves original batch, normalized projection, mapping/key profile, schema diff, row/cell diff and audit lineage without storing only aggregates.
- Define deterministic canonicalization and per-sheet key validation, including duplicate/missing/changed-key behavior.
- Preserve CM/CM1 as non-investigational medication and DA/EX/ECB/ECA as investigational-product change/exposure domains.
- Produce a narrow TDD implementation order and two-real-project verification matrix.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not expose identifiers, cell values, source paths or raw hash inventories in conference output.
- Do not treat external listing diffs as a substitute for EDC audit trail.
- AI mapping suggestions remain unapproved until a user confirms a versioned profile; ambiguous keys fail closed.

## Codex Main-Venue Corrections For Chair Review

- Exact-content retries are idempotent: return the existing preview or commit result when content, project, metadata, parent and profile inputs match. Reject only conflicting reuse, such as identical content attached to incompatible metadata or lineage; do not blanket-reject every duplicate upload.
- The current normalizer preserves original unmapped fields under `raw__{source_field}`. The defect is that unmapped fields are excluded from the canonical and rule projection while preview risks may still be produced; do not misstate this as raw-field loss.
- Schema drift requires classification. Cosmetic header-format drift and approved metadata additions may pass under a versioned profile; unapproved clinical rename/removal, type change or key-impacting drift must block commit and downstream rules.
- A listing-to-listing diff is a workbench evidence artifact, not an EDC audit trail. Preserve lineage and auditability without claiming source-system equivalence.
- Human-readable sequential batch IDs may coexist with content-addressed artifact identity. Do not replace every business identifier with a hash.
- A first accepted batch is a registered baseline after schema/key approval; it has no prior-batch diff. Rule execution begins only after the approved baseline or a later committed diff is available.
- Codex's aggregate-only scan confirmed zero `CHANGE_FLAG` headers across all 54 + 54 RUX sheets and 57 + 63 MY009 sheets; the newer MY009 workbook also contains one empty sheet. Therefore the current `CHANGE_FLAG`-driven summary cannot compute real-project incremental diffs.

## Loop Log

- 2026-07-12 10:33:20: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Generic initialization proposed a GLM chair; it was replaced before dispatch by the user's exact aishuo-chair override.
- 2026-07-12: Codex completed a header-only aggregate scan of all four real listing workbooks. No clinical cell values or identifiers were emitted; all four had zero `CHANGE_FLAG` sheets, and the newer MY009 workbook had one empty sheet.
