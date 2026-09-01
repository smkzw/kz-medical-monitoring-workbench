# Conference Context: mw_study_schema_scale_docx_20260720

Created: 2026-07-20 09:48:47
Objective: 基于康哲设计规范与真实中外临床试验方案，审阅并改进医学写作子系统研究流程图/研究流程表的AI预填与模块化编辑体验，验证SVG矢量和图片型量表附件在Word中的准确可读嵌入；输出可执行设计、边缘场景和验收标准
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- User routing override for this project: the first visual/design participant is
  the visible Terminal `qodercli` process using `qwen3.8-max-preview`. It must be
  operated through AppleScript in the visible Terminal, not through a headless
  runner. Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning) is
  the second independent visual participant. The former Grok Build slot is
  therefore represented by Qoder for this conference.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Current implementation:
  - `services/api/app/medical_writing_study_schema.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_document_exporter.py`
  - `services/api/app/main.py`
  - `frontend/src/features/medical-writing/StudySchemaEditor.jsx`
  - `frontend/src/styles.css`
  - `tests/test_medical_writing_study_schema.py`
  - `tests/test_medical_writing_study_schema_api.py`
  - `tests/test_medical_writing_document_exporter.py`
- Real Word acceptance evidence:
  - `records/active_slices/medical_writing_ai_first_docx_release_v2_20260720/word_acceptance_frontmatter_v2_20260720/D017_PNH_frontmatter_v2.docx`
  - `records/active_slices/medical_writing_ai_first_docx_release_v2_20260720/word_acceptance_frontmatter_v2_20260720/D017_PNH_frontmatter_v2.pdf`
- Read-only reference packet:
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/kangzhe_design.md`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/CMS-D017_phase1_protocol.docx`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/MY009_UC_phase2_protocol.docx`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/SINUS52_phase3_protocol.pdf`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/APPLY_APPOINT_PNH_phase3_protocol.pdf`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/MY009_IBDQ_scale.pdf`
- Live desktop application: `http://127.0.0.1:5174/`; backend:
  `http://127.0.0.1:8911/`.
- The reference files may be read and locally rendered for this task. They must
  not be uploaded to third-party services or copied outside the workspace.

## Scope

- In scope:
  - independently use the live research-flow editor as a time-constrained,
    demanding senior Chinese medical writer;
  - compare the generated research-flow figure with the real I/II/III protocol
    references, including multi-part phase I, randomised branches, treatment
    switching, extension/follow-up and conditional paths;
  - audit the AI-prefill contract: proposal from confirmed framing/PICOS,
    explicit candidate/confirmed states, medical-manager edits, impact preview,
    commit, re-layout, projection into section 1.2 and DOCX export;
  - separate the research-flow figure from the Schedule of Activities table and
    its modular notes;
  - design the image-based scale-attachment workflow, using the real IBDQ PDF
    as the first acceptance source;
  - specify exact visual tokens, information hierarchy, interactions, loading
    states, edge cases and Word/PDF acceptance checks.
- Out of scope:
  - changing clinical facts in the reference protocols;
  - asking the user to confirm ordinary UI or implementation details;
  - production source edits in this conference round;
  - mobile-first compromises;
  - replacing the existing study-schema semantic model without proving a
    concrete incompatibility.

## Success Criteria

- The report distinguishes source observation, inference and recommendation.
- It identifies all material gaps between the existing editor/exporter and a
  genuinely usable "AI prefill, user revises/accepts" workflow.
- It proposes one coherent desktop interaction model with field-level default
  values, batch confirmation, direct manipulation, undo/revision handling and
  transparent progress indicators.
- It covers at least: SAD+MAD multi-part phase I; parallel randomised phase II;
  phase III placebo-controlled treatment switch/extension; and a long/wide
  figure requiring landscape Word layout.
- It gives a Word contract for SVG primary + PNG fallback and a separate
  contract for image-based scale appendices rendered at >=200 DPI without
  distortion, clipping or illegible text.
- It includes concrete acceptance scenarios and does not claim visual
  acceptance without rendered evidence.
- It ends with a bounded implementation sequence that Codex can reproduce and
  test.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Efficient Collaboration Policy

- Each participant receives this complete packet once.
- While the process is inside the 120-minute hard wait, Codex observes process
  state and output artifacts only. Do not send "progress?", "continue", or
  duplicate restatements.
- After a completed pass, consolidate all material omissions into at most one
  targeted same-session follow-up. A further pass requires new acceptance
  evidence or a reproducible unresolved defect.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-20 09:48:47: Conference initialized by `hermes_workflow_guard.py init-conference`.
