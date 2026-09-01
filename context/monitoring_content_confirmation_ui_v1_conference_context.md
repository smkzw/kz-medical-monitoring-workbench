# Conference Context: monitoring_content_confirmation_ui_v1

Created: 2026-07-13 00:28:33
Objective: 在医学监查桌面上传门禁中加入文件内容一致性提示、逐项确认和确认后重试，复用既有写作核验交互并保持高信息密度
Task type: `visual_delivery_conference`
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

- Existing monitoring upload layout: `frontend/src/App.jsx` (`MonitoringPage`) and `frontend/src/styles.css` (`upload-gate`).
- Existing approved interaction pattern: `frontend/src/features/writing-reference/WritingReferencePanel.jsx` lines 430-471 and matching `writing-reference-override` CSS.
- Current monitoring desktop screenshot: `records/active_slices/rux_monitoring_raw_intake_20260709/monitoring_raw_intake_desktop_1440_loaded.png`.
- Existing confirmation reference screenshot: `records/visual_qc_20260712/medical_writing_reference_override/medical_writing_reference_override_after.png`.
- Backend response contract: HTTP 409 detail code `source_content_confirmation_required`, `source_entry_id`, and public validation; confirmation endpoint then retries the original upload.

## Scope

- In scope: desktop-only interaction inside the existing upload gate; preserve information density; show technical/content outcomes; one checkbox per unresolved check; empty reason field; confirm and automatically retry the same selected file; show confirmed-after-warning without relabeling content as matched.
- Out of scope: new route/page, mobile-driven feature cuts, security scan language, redesign of monitoring ledger/timeline/profile, or automatic rule run before confirmation.

## Success Criteria

- Reuse existing panel/card/radius/type/color system and the writing-reference confirmation anatomy.
- A 409 does not become a generic API error; it opens an inline confirmation block next to the upload controls.
- The confirm button remains disabled until all current checks are acknowledged and the reason has at least 10 characters.
- Confirmation success triggers exactly one retry of the original upload; no duplicate manual file selection.
- Content status remains warning/mismatch while a separate label states that the medical manager confirmed continued use.
- No desktop overlap or horizontal page overflow at 1600x1000 and 1920x1080.

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
- Do not expose hashes or local paths.
- Do not add security/malware scan terminology.
- Desktop is the acceptance target; mobile is only a catastrophic-breakage smoke target.

## Loop Log

- 2026-07-13 00:28:33: Conference initialized by `hermes_workflow_guard.py init-conference`.
