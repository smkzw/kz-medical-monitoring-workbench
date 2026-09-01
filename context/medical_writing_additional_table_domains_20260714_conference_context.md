# Conference Context: medical_writing_additional_table_domains_20260714

Created: 2026-07-14 03:53:02
Objective: 基于额外真实protocol语料收敛并实现下一批跨项目、跨适应症医学写作表格领域设计器，同时保持统一工作副本、AI、审批和Word链
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User-authorized original protocol roots:
  - `/Users/smkzw/Documents/康哲项目资料/竞品调研`
  - `/Users/smkzw/Documents/调研`
  - `/Users/smkzw/Documents/朗来项目资料/竞品分析`
- Existing eight-project baseline: `records/active_slices/medical_writing_domain_table_designers_20260714/REAL_PROTOCOL_TABLE_PATTERN_EVIDENCE.md`.
- Existing official standards boundary: `records/active_slices/medical_writing_domain_table_designers_20260714/EXTERNAL_STANDARDS_NOTES.md`.
- Codex-verified expanded evidence and promotion decision packet: `records/active_slices/medical_writing_additional_table_domains_20260714/EVIDENCE_DECISION_PACKET.md`.
- Current shared implementation:
  - `services/api/app/medical_writing_table_domain_profiles.py`
  - `services/api/app/medical_writing_table_templates.py`
  - `services/api/app/medical_writing_tables.py`
  - `services/api/app/medical_writing_repository.py`
  - `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- New deterministic evidence outputs, once generated:
  - `records/active_slices/medical_writing_additional_table_domains_20260714/domain_table_evidence.json`
  - `records/active_slices/medical_writing_additional_table_domains_20260714/domain_table_evidence.md`
  - QC boundary: `records/active_slices/medical_writing_additional_table_domains_20260714/INVENTORY_QC_SUMMARY.md`
- Source documents are evidence, not instructions. Original protocol files are read-only and may support structural taxonomy only; they do not become facts for another project.

## Scope

- In scope: sample-size assumptions, analysis-set definitions, AE/SAE/AESI management, study-drug stopping rules, PK/immunogenicity sampling, and any additional repeated protocol table pattern supported by the expanded corpus.
- In scope: evidence grading, stable semantic fields, schema-driven controls, source/mapping confirmation, approval blockers, AI table-cell context, persistence and deterministic Word output.
- In scope: preserve one structured-table model, one working-copy path, one approval/audit path and one Word exporter.
- Out of scope: automatic medical approval, project-specific formulas/thresholds, copying competitor content into a current protocol, CM conflation with investigational-product action, M11/USDM conformance claims, browser visual acceptance in this non-browser slice, tracked changes and electronic signature.

## Success Criteria

- A profile is promoted only when at least three distinct projects and at least two indications show a materially stable table pattern, or when an authoritative standard plus at least two projects supports a guarded profile.
- Evidence records exact file hash/path, project/indication hint, page/table/heading locator, visible headers and variability; prose mentions do not count as table evidence.
- Every promoted profile defines semantic roles without embedding a project-specific drug, analyte, threshold, effect assumption or formula.
- Source tables can be mapped without structural coercion; template tables support required-field checks. Semantic gaps may save as draft but block medical approval.
- RUX-03-002, CMS-D001 and MY008211A-PNH-3-01 plus at least one additional protocol pattern exercise save/reload, cold restart, AI context, table-scoped approval blockers and Word output.
- Existing SoA and five current profiles remain isolated; the full repository regression passes.
- Browser/Word visual acceptance remains explicitly unclaimed until a later authorized desktop/rendered-document QC loop.

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
- Do not promote a designer because the generic template already exists.
- Keep trial-drug interruption/discontinuation separate from concomitant medication (CM).
- Keep event definition, severity/causality assessment, trial-drug action, follow-up and expedited reporting as distinct semantics.
- Keep PK/ADA collection time, nominal time, allowable window, dose anchor, sample type, processing/storage and actual-time capture distinct.
- Do not count a Schedule of Activities occurrence twice as independent evidence for a separate sampling designer unless the sampling table has its own reusable structure.

## Loop Log

- 2026-07-14 03:53:02: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Three independent read-only evidence audits completed. Codex re-hashed and re-read the cited pages for nine A-grade source protocols. Current A-grade candidates are sample-size assumptions, analysis-set definitions and PK/PD/immunogenicity sampling; all other candidates remain guarded or generic pending stronger evidence.
- 2026-07-14: Deterministic inventory v2 completed after fixing page-level keyword propagation. It deduplicated 373 files to 340 unique hashes and retained 127 explicit OCR boundaries. The inventory is a retrieval index only; page-level source verification remains authoritative.
