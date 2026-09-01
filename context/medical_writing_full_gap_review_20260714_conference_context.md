# Conference Context: medical_writing_full_gap_review_20260714

Created: 2026-07-14 20:57:48
Objective: 从中国创新药医学经理用户视角，审阅现有医学写作子系统与两阶段项目向导、PICOS设计、ClinicalTrials.gov竞品语料准备、中文ICH M11全章节模块化写作、真实表格/研究摘要/矢量流程图/量表/目录索引之间的差距，提出不推翻现有系统的最优产品路径和需用户决策项
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

- User requirements and current-loop state: `records/active_slices/medical_writing_full_gap_review_20260714/TASK_RECORD.md`.
- Authority and vendor source manifest: `records/active_slices/medical_writing_full_gap_review_20260714/SOURCE_MANIFEST.md`.
- Target M11 object/interaction model: `records/active_slices/medical_writing_full_gap_review_20260714/M11_TARGET_MODEL.md`.
- User-provided Chinese draft extraction: `records/active_slices/medical_writing_full_gap_review_20260714/source/ich_m11_cn_20250114_extracted.txt`.
- Current CDE Chinese extraction: `research/medical_writing_gap_20260714/sources/CDE_M11_template_cn_20260612.txt`.
- Current frontend and service evidence may be read from the exact code paths listed in the task record; this is a read-only architecture/product review.
- Codex has separately verified the live endpoint and current web/regulatory sources. Participants must not browse and must identify any statement that depends on unreviewed current authority.

## Scope

- In scope: two-stage study-framing/PICOS journey, project-level state machine, competitor protocol/SAP corpus preparation, manual upload, Chinese translation and medical admission, complete Chinese M11 chapter model, synopsis/SoA/content-table boundaries, study-schema vector editor, scale governance, TOC/table/figure index and Word fidelity, AI/user interaction, source traceability, change impact and implementation sequencing.
- In scope: preserve and reuse current rich editor, structured-table, revision dialogue, approval, evidence and DOCX foundations where their contracts remain valid.
- Out of scope: production code edits, final regulatory conclusions, live product/browser verification, unrestricted web research, medical-writing of IB/ICF/CTD, non-China protocol variants and claims based only on vendor marketing.

## Success Criteria

- Produce a user-journey recommendation that can be mapped to current capabilities without replacing proven foundations.
- Separate evidence, inference, recommendation and unresolved user decisions.
- Identify state transitions, invalidation behavior, object boundaries and failure modes, not only a feature list.
- Challenge fixed assumptions such as always generating 3-5 candidates, treating every DOCX table equally, or declaring a corpus ready after one document.
- Return a prioritized, testable implementation sequence and a compact set of decisions that genuinely require the user.

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
- Do not copy or expose local source-document contents beyond the bounded review purpose.
- Do not infer that a vendor feature exists unless recorded in the source manifest as public evidence.
- Do not recommend bypassing medical approval, provenance, versioning or change-impact review.

## Loop Log

- 2026-07-14 20:57:48: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14 21:36: All three participants completed three same-session rounds. Codex identified conflicts the chair must challenge rather than average:
  - The current system already has ClinicalTrials.gov search, candidate classification, public-document download, extraction, translation, medical review and admission foundations. Any claim that CT.gov integration is absent is factually wrong; the gap is journey orchestration, manual-upload parity and project-level readiness.
  - The user explicitly requires corpus preparation confirmation before the formal writing platform. A warning-only path conflicts with that requirement unless it is modeled as a reasoned senior-medical override that preserves not-ready status.
  - CQRS, decorator patterns and other named architecture patterns are not goals. Recommend the smallest contract compatible with the current codebase.
  - The user asked to deepen the existing system, not replace it. Existing rich editor, structured tables, AI revision, approval, real-project import and DOCX export are reusable foundations.
  - `M11 authority`, two-stage guidance, dedicated synopsis/table/schema/scale/index behavior and China-only protocol scope are substantially set by the user/current authority. Do not turn every implementation detail into a user question.
  - `general_opencode_mimo` disclosed reading supplementary code outside its exact read list while also claiming read-list compliance. Treat code-specific claims from that participant as boundary-tainted and verify them against the designated task record instead of accepting them as independent evidence.
