# Conference Context: mw_system_rearchitecture_audit_20260808

Created: 2026-08-08 18:50:49
Objective: 冻结当前医学写作进度，全量审计医学经理工作台与医学写作需求、实现、测试和缺口，调研 Graph engineering 与多 Agent 工作流，基于 TP-MA-07 模板完成需求访谈、目标架构和重构实施计划；用户确认前不实施产品重构
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Codex subAgent `gpt-5.6-luna` (max) as the sub-venue chair, leading one Pi/Alibaba `qwen3.8-max-preview` (xhigh) participant during the daytime route. During the Beijing overnight window the runner changes that participant and any exact Pi/Alibaba Preview fallback node to `qwen3.8-max` (xhigh). The participant's first fallback is Pi/OpenCode Go `deepseek-v4-flash` (max), followed by Pi/DeepSeek V4 Flash max; the chair's first fallback remains Pi/Alibaba Qwen3.8 xhigh, followed by Grok Build `grok-4.5` and Cursor CLI `cursor-grok-4.5-high`. In Codex App, the Codex subAgent chair is dispatched natively through `multi_agent_v1` so the parent can see progress and reuse the same session.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Current filesystem under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Frozen Protocol P0 records:
  `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`,
  `runs/mw_protocol_p0_max_clean_rounds_20260805.md`,
  `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`, and
  `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`.
- Earlier approved roadmap and commercial-gap records under `plans/`,
  `context/`, `runs/`, `reviews/`, and `metrics/`; implementation source,
  schemas/contracts, tests, frontend, document exporter/editor, and current
  generated artifacts are evidence, not presumed completion.
- User-supplied retained template, read-only:
  `/Users/smkzw/Documents/指导原则及临床试验规范合集/CRP知识库/模板/TP-MA-07 临床试验方案（2期或3期）.docx`.
- Current user request dated 2026-08-08, including the proposed five-Agent
  responsibilities and PICOS-M-A-Opr draft. These are design hypotheses to
  test and refine, not already-approved implementation contracts.
- Primary external sources for Graph engineering, orchestration, clinical
  protocol standards, and eligible open-source dependencies; external model
  reports remain advisory.

## Scope

- In scope: read-only full-system inventory; initial requirements and decision
  history; current architecture and data/contracts; implemented/unimplemented
  features; prior multi-model/E2E findings; TP-MA-07 structural/semantic/style
  analysis; Graph engineering and multi-Agent fit; target product/agent/data/
  semantic/rule/QC architecture; user decision questions; migration and
  staged implementation plan.
- Out of scope until the user approves the completed design: product-source
  changes, schema migrations, runtime-data changes, service startup, OCR,
  translation, downloads, E2E testing, project deletion/reset, Synopsis/CSR
  implementation, and production promotion.

## Success Criteria

- The current r17/Protocol P0 state is frozen with no source/runtime mutation
  and its exact recovery boundary remains explicit.
- An evidence-backed inventory maps original requirements, current modules,
  contracts/data stores, implemented capabilities, incomplete paths, test
  evidence, and known P0–P4 findings without treating green tests or UI
  reachability as production completion.
- The template analysis accounts for every chapter/section/table/page pattern
  and distinguishes document structure, authoring requirements, semantic
  inputs, cross-chapter constraints, and presentation rules.
- The Graph/multi-Agent assessment compares the current architecture, a small
  custom state-machine/graph kernel, and eligible open-source frameworks by
  license, maturity, observability, recovery, deterministic gates, privacy,
  local fit, and migration cost.
- A proposed document-per-workflow architecture defines typed state,
  semantic/rule maps, artifacts, provenance, versioning, human decisions,
  worker/reviewer isolation, idempotency, stop conditions, and non-LLM anchors.
- Multi-round questions cover only unresolved choices that materially change
  product behavior or architecture. The design and implementation plan remain
  provisional until the user answers and an independent conference accepts
  the revised design.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Read-only audit only. Do not start services, mutate product source, write
  runtime databases, delete projects, rerun clinical stages, or alter the
  frozen r17/r42 evidence.
- Do not read or modify medical-monitoring task files except to identify and
  preserve the ownership boundary.
- Do not expose credentials, private documents, or local identifiers to public
  queries. External searches use generic architecture and standards terms.
- Allowed durable writes during this phase are limited to this tracked task's
  `context/`, `plans/`, `reviews/`, `metrics/`, `prompts/`, `runs/`, and
  `.hermes/plans/` records; template renders/extracts, if needed, stay in a
  task-specific temporary directory. No product implementation files may be
  changed.

## Loop Log

- 2026-08-08 18:50:49: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-08: Existing r17 pause retained; audit/interview/design phase opened.
  Conference routes are initialized but will not be dispatched until a design
  draft exists and the user has answered the material decision questions.
- 2026-08-08: Three independent read-only audit workstreams completed: current
  implementation, historical requirements/acceptance, and external graph
  engineering. No product or runtime mutation occurred.
- 2026-08-08: Confirmed current system has 124 company semantic nodes but lacks
  a uniform chapter-content contract; about 76 of 110 leaf nodes have no direct
  deterministic chapter projection. Current 3,878-entry company corpus has no
  populated semantic-node or M11 anchor identity.
- 2026-08-08: Confirmed latest authority remains r17 NOT_CLEAN at
  `awaiting_corpus_admission`; no PICOS, substantive full protocol, DOCX or
  Word evidence exists for that run.
- 2026-08-08: TP-MA-07 original hash rechecked as
  `a28e95d738ffad9199eee44a965164d89a04022dbcac7ea01a999bde5cf34f5e`.
  The temporary 49-page LibreOffice render was used only for topology and
  layout inspection because most Chinese glyphs did not render faithfully.
- 2026-08-08: Provisional direction recorded in
  `runs/MW_SYSTEM_REARCHITECTURE_AUDIT_CHECKPOINT_20260808.md`: preserve the
  existing semantic/durability/OOXML assets, introduce an application-owned
  canonical study/document graph and chapter-contract registry, and evaluate
  LangGraph against an internal typed facade and Microsoft Agent Framework via
  a bounded crash/replay/HITL PoC. No framework adoption has been approved.
- 2026-08-08: Overall frontend build drift observed from r17
  `web-e3cd9e93be9339b7` to current `web-c775724b9110e079`; attribution to
  medical writing is unproven because no r17 per-file frontend hash manifest
  exists and medical-monitoring work is concurrent. Backend build identity
  remains `api-5607f2bcd758c68e`.

## Current Decision State

- Audit/freeze: complete.
- Provisional architecture: complete enough for user interview, not approved.
- User interview: Round 1 pending.
- Formal independent conference: intentionally not dispatched.
- Product implementation: prohibited until user answers, design revision,
  conference acceptance, and explicit approval.
- 2026-08-08 19:13:23 CST: User requested a no-loss pause. Work stopped before
  interview Round 1. Resume only from
  `runs/MW_SYSTEM_REARCHITECTURE_NO_LOSS_PAUSE_20260808_1913.md`; do not
  dispatch the formal conference or change product code before the recorded
  interview and approval gates.
- 2026-08-08 23:39:45 CST: User explicitly resumed the task. Instruction hashes
  and the complete pause/audit checkpoint were rechecked unchanged. Status is
  now `DESIGN_INTERVIEW_ROUND_1`; product/runtime remains frozen, and the
  formal conference remains intentionally undispatched.
- 2026-08-08: Design decision D001 recorded in
  `plans/mw_system_rearchitecture_design_decisions_20260808.md`. The user
  corrected the initial answer to option C: product-internal AI plus
  deterministic QC may mark the complete output `可提交定稿`; no mandatory
  medical/statistical/regulatory sign-off workflow is in scope. Manual review
  remains the user's own downstream activity. Final content must contain no
  pending-confirmation language, placeholders, logs, prompts or unfinished
  state markers.
- 2026-08-08: Design decision D002 accepted as option A. TP-MA-07 is the
  authoritative Phase II/III company master; semantic structure and Word
  object contracts are versioned, conditional nodes are controlled by explicit
  applicability rules, and Phase I receives a separate template contract on
  the same platform kernel.
- 2026-08-08: Design decision D003 accepted as option A. StudyDefinition v3 / 
  PICOS-M-A-Opr becomes the single canonical fact authority; Synopsis, body,
  SoA, diagrams and Word are versioned projections, and fact-changing edits
  must use validated typed patches with impact propagation.
- 2026-08-08: Design decision D004 accepted as option A with a refined key-
  design overview. AI analyzes competitor designs and other applicable sources,
  preselects a recommended default per design card, offers reasoned alternatives
  plus `其他，请输入`, and supports one-click accept-all or per-card changes.
  Custom input is parsed and consistency-checked before adoption; conflicts,
  low confidence and major safety/feasibility risks remain blocking exceptions.
- 2026-08-08: Design decision D005 accepted as the first option (A). Agent②
  remains one user-facing design/Synopsis role but internally isolates clinical
  and statistical/estimand workers, then joins them through deterministic
  cross-domain consistency checks before presenting any unresolved decision.
- 2026-08-09: Design decision D006 accepted as option A with a refined source
  authority matrix. Current effective regulations and latest applicable
  guidelines/consensus receive normative priority; superseded versions are
  down-weighted and lineage-labelled. Competitors are scored transparently by
  recency plus target/mechanism, indication subtype, population, severity,
  treatment line, intervention, design, endpoint, geography and evidence
  quality. Unresolvable material uncertainty is presented as reasoned options
  for user selection, never left as pending text in the final document.
- 2026-08-09: Design decision D007 accepted as option A. Opr covers all
  protocol-impacting operational feasibility but not full CTMS/budget/vendor
  procurement. The default is a China domestic multicentre study; alternative
  geographies or centre models are surfaced only when project strategy or
  evidence supports them. Opr findings feed back into population, centre count,
  recruitment, sample-size assumptions, visits, assessments and duration.
- 2026-08-09: Design decision D008 accepted as option A. Agent④ is a fresh-
  context independent verifier with veto and bounded repair-dispatch authority,
  not a canonical-fact writer. Low-risk language/format/reference issues are
  auto-repaired; clinical/statistical defects return to their owning Agent②
  worker and content defects to Agent③. Only unresolved material exceptions
  reach the user, and a clean Agent④ verdict is required for `可提交定稿`.
- 2026-08-09: Design decision D009 accepted as option A. All TP-MA-07 leaf
  semantic nodes receive versioned Chapter Contracts, while Agent③ remains a
  reusable worker role instantiated per dependency-aware writing packet rather
  than 110 persistent agents or fixed eight-section chunks.
- 2026-08-09: User enabled the brainstorming visual companion for AI-first UI
  decisions. Session artifacts are isolated under
  `.superpowers/brainstorm/24247-1786205440/`; no product source or runtime was
  changed.
- 2026-08-09: Design decision D010 accepted at direction level: combine A over
  C in one default workspace, with AI conclusions/exceptions above and a live
  final-Word-style document canvas below. Recommendations and analysis are
  bidirectionally anchored to document blocks through non-exporting overlays.
  B-style guidance is reserved for irreducible minimum inputs that AI needs to
  search, extract and recommend accurately. A combined v2 mockup was pushed for
  visual validation.
- 2026-08-09: The combined A+C visual structure was accepted. D011 adds that
  the central canvas must provide direct, full Word-style editing and shortcut
  behavior, not merely a rendered preview. Sentence/paragraph/subsection or
  table selections receive a context-menu `AI润色` action using stable semantic
  range anchors, protected facts/formatting, candidate diff and reversible
  adoption. The visual companion was moved to a waiting screen while document
  authority and round-trip behavior are discussed in the terminal.
- 2026-08-09: Design decision D012 accepted as option A. The in-product
  semantic document remains the authoritative working version and DOCX remains
  a fully editable submission artifact. Externally edited Word files can be
  reimported as immutable artifacts, semantically diffed into wording,
  formatting, structure and fact changes, then safely merged into a new
  revision with StudyDefinition impact propagation and renewed QC.
- 2026-08-09: Design decision D013 uses A-style AI-first guided intake but
  replaces the old three-field minimum with eight Research Seed domains: drug,
  formulation/route, expected dose, target/mechanism, indication, phase,
  adult/adolescent/child multi-select, and comparator. Upload extraction may
  prefill them. Non-standard natural language is preserved and mapped through
  fuzzy semantic normalization; only ambiguous/low-confidence critical matches
  trigger a reasoned second confirmation.
- 2026-08-09: Design decision D014 accepted as option A with project-specific
  applicability. The 110 leaf contracts form the coverage matrix, not a demand
  that every project render all nodes. A versioned ApplicabilitySnapshot gates
  the project; every applicable node requires substantive, source-traceable,
  clean content, followed by independent QC and native Microsoft Word checks.
  Empty headings, generic non-applicability, pending text, logs and AI/workflow
  traces cannot satisfy the gate.
- 2026-08-09: Design decision D015 accepted as option A. Conditional nodes
  marked not-applicable are omitted from final body/TOC with deterministic
  renumbering; applicability reasoning remains audit-only. Template-mandatory
  nodes receive study-specific scientific text rather than generic `无` or
  `不适用`. The two key interview rounds are now closed and architecture
  approach comparison begins.
- 2026-08-09: Design decision D016 approved route A: application-owned
  canonical/event/artifact control plane plus OSS LangGraph as a replaceable
  orchestration kernel, subject to the previously defined crash/replay/HITL/
  migration PoC. The first architecture design section was pushed to the
  visual companion for incremental approval.
- 2026-08-09: Architecture design section 1 was explicitly accepted in the
  terminal and through repeated identical browser events; the repeated clicks
  are treated idempotently as one approval. Section 2, covering the canonical
  Research Seed→evidence→recommendation→fact→applicability→semantic/Word chain
  and a leaf Chapter Contract example, was pushed for visual review.
- 2026-08-09: Architecture design section 2 was explicitly accepted in the
  terminal and browser. Section 3, defining Agent①–④ subgraph stages, typed
  outputs and exit gates, the three user exception points, native Word delivery,
  and checkpoint/idempotent/impact-scoped recovery, was pushed for visual
  review.
- 2026-08-09: Architecture design section 3 was accepted with a stricter Agent①
  evidence gate. Every researched competitor protocol with a download link
  must be fully downloaded and integrity-verified, page-completely OCR/parsed,
  accurately structure-aligned translated and fidelity-QC passed; any pending,
  missing, corrupt, illegible or mistranslated item blocks corpus completion.
  Section 4, detailing the AI cockpit, full Word-style editor, selection-bound
  AI actions and non-exporting analysis overlays, was pushed for review.
- 2026-08-09: Architecture design section 4 was accepted with chapter-level AI
  cockpit and lock semantics. Each chapter can one-click accept all and create
  a version-bound LockSnapshot; later dependency-impacting changes automatically
  unlock only affected chapters, synchronize revisions and rerun QC. Purely
  deterministic clean projections may relock with notification; substantive or
  uncertain rewrites remain unlocked for review. Section 5, including this
  lifecycle plus role-separated AI configuration and runtime/audit boundaries,
  was pushed for review.
- 2026-08-09: Architecture design section 5 was accepted with an expanded LLM
  harness boundary: configured Codex models, OMP models and other Agent App/CLI
  backends may enter workflow nodes through a common typed, resumable,
  permission-bounded NodeExecutionContract. Dialogue/scratchpads remain non-
  authoritative and canonical writes remain product-controlled. Section 6,
  covering Phase 0–8 strangler migration, reuse/replace boundaries and full
  release acceptance, was pushed for final design review.
- 2026-08-09: Architecture design section 6 and the six-section target design
  were accepted with final scope correction D017. The complete multi-Agent
  graph is Protocol-only. Synopsis is only a standalone export window after the
  full Protocol workflow passes; it is not an independent workflow or fact
  authority. CSR is explicitly out of this graph and will receive a separate
  future multi-Agent design. Formal spec drafting and fresh-context challenge
  now begin; product implementation remains frozen.
- 2026-08-09: Formal consolidated design spec drafted at
  `plans/mw_protocol_multi_agent_rearchitecture_design_20260809.md`, status
  `DRAFT_FOR_INDEPENDENT_CHALLENGE`. It incorporates D001–D017, the stricter
  Agent① all-linked-competitor gate, full Word-style editing, chapter lock/
  impact semantics, Harness adapters, Protocol-only scope and Synopsis export-
  only boundary. No product implementation was performed.
- 2026-08-09: Codex self-review completed at
  `reviews/mw_protocol_rearchitecture_design_self_review_20260809.md`. It
  resolved Protocol Summary versus Standalone Synopsis, added the missing
  Agent⑤ and Skill Registry contracts, added E0/E2/E3 around strict E1, made
  semantic editor changes fact-safe, and demoted PostgreSQL from an untested
  fixed choice to a PoC-gated preferred repository target. The stale paused UI
  Goal's pre-D017 bidirectional Synopsis text is explicitly superseded by the
  user's latest D017 decision. Formal fresh-context challenge is now eligible;
  product implementation remains frozen.
- 2026-08-09 01:31–01:32 CST: Both formal conference roles passed guard
  preflight and were launched once. Participant declared
  Pi/Alibaba/qwen3.8-max-preview and was substituted by the executable night
  policy to qwen3.8-max. The declared native Codex gpt-5.6-luna chair could not
  be selected in the current App interface; its first Qwen fallback would
  duplicate the participant, so the next declared fallback Grok Build/grok-4.5
  was launched read-only. Controller PTYs are 99819 and 69014; provider session
  IDs remain pending in runner stdout. One bounded wait per role returned
  running with no output; no re-dispatch or fixed polling occurred.
- 2026-08-09 01:32 CST: The brainstorming visual companion was cleanly stopped
  after all six sections were accepted. `.superpowers` content and state remain
  preserved; no product runtime was stopped or started.
- 2026-08-09: Both independent pass-1 reports completed without fallback. Pi
  participant session `019fe26d-ca35-7000-8656-b0162ffd1c4a` independently
  found Word-receipt-producer, batch-reject precedence, non-vacuous contract,
  unknown-outcome reservation, denominator approval, coverage digest and
  rollback/versioning gaps. Grok chair session
  `4942b210-ab2d-4c34-aeb4-58cd5c4e76cb` independently found three P0 and
  supporting P1/P2 design holes. Both verdicts were
  `REVISE_BEFORE_USER_SPEC_REVIEW`.
- 2026-08-09: Codex incorporated the accepted findings into design-v1.2:
  SubstantiveContentContract, MedicalAdmissionUnit, three acquisition
  denominators/evidence_class, per-item admission precedence, user-only E1
  reclassification/no quality waiver, non-vacuous registry lint,
  ExecutionReservation/unknown_outcome, full Q1 coverage digest/dispositions,
  EditClass, logical identity/CAS, event-checkpoint recovery, rollback,
  SubmissionEvidencePackage, and §23.4 Word-native receipt producer PoC. Delta
  mapping is at
  `reviews/mw_protocol_rearchitecture_conference_pass1_delta_20260809.md`.
- 2026-08-09: One delta-only follow-up was launched on the same Grok chair
  provider session after successful preflight; controller PTY 70392. It will
  compare the now-complete participant report and design-v1.2. No product
  implementation or new chair session was started.
- 2026-08-09: The first same-session delta continuation ended `cancelled` after
  one sentence and was correctly rejected despite return code 0. One allowed
  same-session completion pass on the same provider session returned the full
  closure matrix and final verdict `READY_FOR_USER_SPEC_REVIEW`; no new session
  or fallback was used.
- 2026-08-09: Codex main-venue verification accepted design-v1.2 for user review.
  Spec SHA-256 is
  `321169afc9f33f572b803661b6c6eeb598304267fcb33cdf7de4faf0b00ad0d8`;
  source TP-MA-07 hash remains
  `a28e95d738ffad9199eee44a965164d89a04022dbcac7ea01a999bde5cf34f5e`.
  Conference validation passed and no `services/`, `frontend/` or `tests/` file
  changed after 2026-08-09 00:00. Product implementation remains frozen pending
  user approval of the written spec and then a separately approved detailed plan.
- 2026-08-09: Final workflow `review-gate --require-verification` passed with no
  warning after the review explicitly recorded Boundary Compliance, the absence
  of a declared Hermes role, and Codex Independent Verification. The task is
  now durably frozen at
  `runs/MW_PROTOCOL_REARCHITECTURE_DESIGN_READY_FOR_USER_REVIEW_20260809.md`.
