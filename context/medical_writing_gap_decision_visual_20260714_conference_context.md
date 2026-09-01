# Conference Context: medical_writing_gap_decision_visual_20260714

Created: 2026-07-14 22:06:14
Objective: 对照现有医学写作工作台，对新建医学写作Gap决策页进行桌面端视觉、信息密度、中文临床产品语境和交互可读性复核，提出可直接修订的问题
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

- Conference governance extract: `context/global_agents_conference_rules_20260714.md`.
- Same-viewport reference comparison: `output/playwright/medical_writing_gap_decision_page_20260714/reference_comparison_3880x1212.png`.
- Existing workbench reference at 1920x1080: `output/playwright/medical_writing_gap_current_baseline_20260714_v2/greenfield_setup_1920x1080.png`.
- New decision page at 1920x1080: `output/playwright/medical_writing_gap_decision_page_20260714/baseline_1920x1080.png`.
- Completed and restored states:
  - `output/playwright/medical_writing_gap_decision_page_20260714/completed_1920x1080.png`
  - `output/playwright/medical_writing_gap_decision_page_20260714/restored_midpage_1920x1080.png`
- Browser/interaction QC: `output/playwright/medical_writing_gap_decision_page_20260714/medical_writing_gap_decision_page_qc.json`.
- Page source: `output/medical-writing-gap-review-20260714/index.html`, `styles.css`, `app.js`.
- Participants may inspect only the listed screenshots and files. They must not open a browser, edit source, browse, or claim final acceptance.

## Scope

- In scope: desktop 1600-2048px hierarchy, density, whitespace, alignment, font sizing, borders, colors, CMS logo use, decision scanning, recommended-option emphasis, sticky directory/summary, Chinese medical-product wording and interaction-state clarity.
- Out of scope: redesigning the established workbench shell, mobile optimization, changing the 8 decision semantics, production code edits, browser execution and final visual acceptance.

## Success Criteria

- Compare visible differences against the existing workbench rather than inventing a new design language.
- Identify only concrete issues visible in the provided screenshots or provable from source/QC.
- Separate pixel-level observation, source inspection, inference and recommendation.
- Rank findings by user impact and provide exact selectors/regions and bounded fixes.
- Confirm whether the page is usable for the user to make all 8 decisions now; do not require cosmetic churn without benefit.

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
- No participant may declare final visual acceptance; Codex compares screenshots and owns that decision.
- Do not recommend mobile concessions, marketing styling, hero sections, decorative cards, gradients or a new palette.
- Preserve accurate `frontend/src/assets/header_logo.png`, the 180px sidebar, 72px header, orange/blue/neutral palette and 4px radius system.
- Do not mistake intentional desktop information density for a defect unless text becomes unreadable, overlapping or operationally slow.

## Loop Log

- 2026-07-14 22:06:14: Conference initialized by `hermes_workflow_guard.py init-conference`.
