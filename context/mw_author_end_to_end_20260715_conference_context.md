# Conference Context: mw_author_end_to_end_20260715

Created: 2026-07-15 20:39:55
Objective: 以中国创新药临床方案医学撰写人员视角实际操作常驻医学写作工作台，审计从新建项目、两阶段反问、竞品Protocol/SAP与语料准备、PICOS、ICH M11章节写作、AI候选、文献引用到DOCX导出的端到端产品断点，并提出可验证的优先修复序列
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Grok Build `grok-4.5`. If either is unavailable, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`. Hermes' own Grok route is not used.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and Hermes OpenCode Go `deepseek-v4-flash`. If the OpenCode Go Flash role fails, the runner first switches to Reasonix CLI `deepseek-v4-flash`, then tries Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as the declared Flash fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Stable product surface: `http://127.0.0.1:5174/` with API proxy to `http://127.0.0.1:8911/`.
- Product goal and current slice: `records/active_slices/medical_writing_editor_references_20260715/TASK_RECORD.md`.
- Two-stage and dual-entry journey: `records/active_slices/medical_writing_authoring_journey_20260714/TASK_RECORD.md`.
- Existing gap matrix: `records/active_slices/medical_writing_full_gap_review_20260714/GAP_MATRIX.md`.
- Current usability decisions: `records/active_slices/medical_writing_workspace_usability_20260715/TASK_RECORD.md`.
- Current stable read-only report and screenshots:
  `records/active_slices/medical_writing_editor_references_20260715/browser_qc/stable_readonly_current/`.
- Existing isolated real-project citation report:
  `records/active_slices/medical_writing_editor_references_20260715/browser_qc/isolated/medical_writing_literature_citation_isolated_qc.json`.
- Frontend journey/test sources: `frontend/src/App.jsx`,
  `frontend/tests/medical_writing_greenfield_qc.mjs`,
  `frontend/tests/medical_writing_synopsis_import_qc.mjs`,
  `frontend/tests/medical_writing_real_projects_qc.mjs`.
- Backend journey sources: `services/api/app/main.py`,
  `services/api/app/medical_writing_authoring_journey.py`,
  `services/api/app/medical_writing_synopsis_import.py`,
  `services/api/app/medical_writing_greenfield.py`.

## Scope

- In scope: act as a senior China clinical-protocol medical writer and walk the
  actual desktop surface from project creation/entry choice through framing,
  PICOS, competitor corpus preparation, writing, AI suggestions, references and
  Word export; distinguish implemented, disconnected, blocked and misleading
  steps; recommend the smallest prioritized repair sequence.
- In scope: read-only interaction with the stable product. Participants may
  launch an isolated headless Chrome profile, select projects, navigate, open
  drawers/tabs, inspect editable controls and issue GET requests.
- Out of scope: production writes, saving a working copy, submitting AI jobs,
  changing approval/review state, importing files into the stable runtime,
  final visual acceptance, or final clinical/regulatory conclusions.

## Success Criteria

- Each finding identifies the exact user step, observed UI/API evidence, expected
  medical-writing behavior, severity and a reproducible verification method.
- At least one existing-protocol project and the new-project entry surface are
  actually opened. Claims based only on source inspection are labeled as such.
- The report separates obsolete test assertions from product defects.
- Recommendations preserve immutable source documents, independent production
  AI, project isolation, medical approval and the corpus readiness boundary.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-15 20:39:55: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-15 20:40 +0800: Codex reread all 565 lines of the current global
  `/Users/smkzw/.codex/AGENTS.md`; SHA-256
  `35d38706079cf4fbb0be78c0567541e2f3e8fcc119a274fd2f372a6628af46ad`.
  This packet follows its current Grok-chair route.
