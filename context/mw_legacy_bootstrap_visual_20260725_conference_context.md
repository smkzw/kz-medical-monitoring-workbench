# Conference Context: mw_legacy_bootstrap_visual_20260725

Created: 2026-07-25 07:02:11
Objective: 对医学写作旧导入方案研究设计bootstrap前端进行真实桌面交互与视觉QC，验证AI预填、文件角色确认/override、进度和重绑定入口
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Stable desktop runtime after the next controlled restart:
  - frontend `http://127.0.0.1:5174`
  - backend `http://127.0.0.1:8911`
- User-facing implementation:
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/src/features/medical-writing/LegacyAuthoringBootstrapPanel.jsx`
- Backend contract/state machine:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/medical_writing_legacy_authoring_migration.py`
  - `services/api/app/medical_writing_authoring_journey.py`
- Focused tests:
  - `tests/test_frontend_medical_writing_contract.py`
  - `tests/test_medical_writing_legacy_authoring_migration.py`
- Real acceptance project: `proj_rux_03_002` / `RUX-03-002`; its imported protocol is
  a read-only source. Reviewers may start extraction only after Codex confirms the
  restarted build is healthy. They must not confirm the medical candidate or bind the
  document; Codex owns those consequential actions after source review.
- Visual design authority: current CMS orange/neutral desktop workbench system in
  `frontend/src/styles.css`; do not replace it with an unrelated redesign.

## Scope

- In scope:
  - desktop discoverability of the legacy bootstrap blocker and next action;
  - progress visibility while product AI extracts the original protocol;
  - review density, hierarchy, typography, overflow, scrolling, and action placement;
  - explicit separation of system-detected role, author-confirmed role, role override
    reason, and independent content-validation warnings;
  - AI-prefilled framing/PICOS/synopsis review where users edit rather than start blank;
  - one author confirmation followed by a clear existing-document rebind action;
  - real click/keyboard/scroll inspection at 1600x1000 and maximized desktop.
- Out of scope:
  - medical confirmation of extracted facts;
  - production source edits by conference participants;
  - security/backdoor review;
  - mobile-driven feature reduction;
  - substituting conference-model content for the workbench's independent AI.

## Success Criteria

- A lazy but expert medical writer immediately understands why the original protocol
  is not yet editable under a StudyDefinition and can start the correct next action.
- File role is never silently finalized by the section-count heuristic; the detected
  role remains visible and author choice is explicit.
- Content validation and role override retain separate reasons and visual hierarchy.
- No text overflow, clipped actions, unusable scroll region, nested-card clutter, or
  persistent log-style information overload at desktop resolution.
- Progress, failure, reload/recovery, review, confirmation, and rebind states each have
  an observable next action.
- Participant reports identify concrete selectors/screens/states and distinguish pixel
  observation from source inference. Codex performs final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

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
- Until 2026-07-25 08:30 Asia/Shanghai, the active project override routes the visual
  Grok role to the existing QoderVIP `qodercli/qwen3.8-max-preview` process. Do not
  start another Qoder process. Kimi remains the independent second visual participant.
- Participants must operate the real workbench UI. They may not bypass product AI by
  generating replacement extraction results themselves.

## Loop Log

- 2026-07-25 07:02:11: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-25 07:03: Source, scope, acceptance and runtime-mutation boundaries filled.
  Dispatch remains gated on Codex confirming the restarted build IDs and readiness.
