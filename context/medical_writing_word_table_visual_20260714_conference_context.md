# Conference Context: medical_writing_word_table_visual_20260714

Created: 2026-07-14 08:11:39
Objective: 独立审阅RUX、D001、PNH三个真实研究项目医学写作草稿Word的68张表、259页渲染，重点验证研究流程表跨页重复表头、宽表列宽、合并单元格、普通领域表、长附注、中文字体与页面可审阅性；只返回有页面证据的缺陷或通过结论，不修改生产文件
Task type: `visual_report_structure`
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

- `records/active_slices/medical_writing_word_table_fidelity_20260714/CONFERENCE_VISUAL_PACKET.md` defines the exact visual packet and known viewer artifact.
- `records/active_slices/medical_writing_word_table_fidelity_20260714/reports/word_table_fidelity_cjk_qc.json` is the structured OOXML/PDF check.
- `records/active_slices/medical_writing_word_table_fidelity_20260714/reports/contact_sheets_cjk/` contains all 259 rendered pages in 17 RGB contact sheets.
- The 24 original-resolution PNGs listed in the packet are the authority for detailed visual findings.
- Original protocol DOCX and production source are outside the participant read list and remain immutable.

## Scope

- In scope: CJK glyph visibility; table/page fit; merged-cell coherence; repeated-header usability; captions; notes; landscape/portrait transitions; representative schedule and non-schedule tables; page-level evidence.
- Out of scope: clinical correctness, protocol authoring choices, watermark redesign, approval status, production edits, browser UI, DOCX round-trip editing and web research.

## Success Criteria

- Every participant inspects all 17 contact sheets and opens original-resolution pages before raising a defect.
- Every defect cites project and page number and separates observed pixels from inference.
- Slow output remains pending under the timeout policy; each participant completes independent, challenge and corrected rounds in one session.
- Codex compares model findings with the actual PNG/PDF/OOXML facts and accepts only reproduced issues.

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

## Loop Log

- 2026-07-14 08:11:39: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Source packet fixed to 17 contact sheets, 24 original-resolution pages and the zero-failure structured QC JSON. Participants may use image inspection only on these paths and may not edit files.
