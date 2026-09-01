# Conference Context: medical_monitoring_manual_20260716

Created: 2026-07-16 10:44:01
Objective: 编制医学监查子系统全量中文正式说明书，覆盖日常医学监查、锁库前整体医学监查、实时与总结性风险预警、增量diff、Subject Timeline、Patient Profile、AE/MH漏报、PD与CFDI核查前自查，并输出多章节Markdown和康哲规范交互式HTML
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Kimi Code (`kimi-code` / `kimi-code/kimi-for-coding`) latest authenticated model. If either is unavailable, the runner tries Grok Build `grok-4.5` (`grok-build`), then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Reasonix CLI `deepseek-v4-flash`, Kimi Code (`kimi-code` / `kimi-code/kimi-for-coding`) latest authenticated model, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User requirements in the current Codex thread, especially the required scope of daily medical monitoring, pre-database-lock comprehensive review, real-time and pre-inspection summary warning, incremental diff, subject timeline, patient profile, AE/MH under-reporting risk, prohibited-medication/protocol-deviation risk, and CFDI self-inspection checklist.
- `context/medical_monitoring_manual_source_packet_20260716.md` (Codex-curated source digest, terminology boundary and chapter blueprint).
- `logs/subsystems/medical_monitoring_log.md` (implemented behavior, known gaps and verified test history).
- `reviews/codex_conference_monitoring_incremental_diff_architecture_20260712_review.md`.
- `reviews/codex_conference_monitoring_source_revision_gate_20260713_review.md`.
- `reviews/codex_rux_monitoring_domestic_platform_benchmark_20260708_review.md`.
- Read-only authorized external local sources:
  - `/Users/smkzw/.cc-switch/skills/ae-risk-assessment/SKILL.md`.
  - `/Users/smkzw/.cc-switch/skills/subject-timeline-builder/SKILL.md`.
  - `/Users/smkzw/.cc-switch/skills/clinical-patient-profile-html/SKILL.md`.
  - `/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR/13. CFDI核查/自查/MG-K10-SAR_CFDI核查前自查问题分析报告.html`.
  - `/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR/13. CFDI核查/自查/自查checklist-医学/【医学相关风险自查表】MG-K10-SAR Checklists_V3.xlsx`.
  - `/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR/12. 其他/AE:MH漏报/【AE、MH漏报】MG-K10-SAR 实验室检验检查及生命体征异常风险.html`.
- External authority references are summarized by Codex in the source packet. Models must not browse or claim current regulatory authority independently.

## Scope

- In scope: a formal Chinese product/scientific specification manual; medical-monitoring workflow; system architecture and data flow; rule governance; source traceability; incremental and full-review modes; subject/site/study views; medical disposition and audit trail; examples; test and acceptance strategy; Markdown and interactive HTML delivery requirements.
- Out of scope: README-style installation notes; replacing investigator or medical-manager judgment; project-specific hardcoding; claiming an automated signal is a confirmed AE/MH/PD; building new production features in this conference; exposing subject-identifiable raw data in the manual.

## Success Criteria

- The manual is chapter-rich, coherent and usable by medical, product, engineering, validation and management stakeholders.
- First occurrence of each English abbreviation gives Chinese full name plus English full name; later use is consistent.
- Every risk family states source inputs, deterministic trigger, semantic-review step, exclusions, severity logic, evidence presentation, medical disposition, false-positive controls and limitations.
- Daily incremental monitoring and pre-lock/pre-inspection full review share one canonical risk object and rule library while retaining distinct execution chains.
- Investigational-product changes/dose adjustment are separated from concomitant medication; CM means non-investigational concomitant medication/treatment.
- Project examples are clearly labeled examples and are never generalized into universal thresholds without protocol or standard support.
- Markdown and HTML share one substantive content source; HTML uses official CMS logo, left table of contents, right reading pane, search, progress and chapter navigation.
- Codex independently checks regulatory sources, clinical logic, Chinese wording, browser rendering and final artifacts.

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
- No participant may convert a screening signal into a definitive medical conclusion. All formal conclusions remain pending medical approval.
- Do not expose subject identifiers or raw clinical row values beyond the bounded illustrative examples already present in source reports.
- Do not treat skill defaults (for example a 20% non-CTCAE change threshold) as universal scientific truth; they are configurable screening defaults requiring project confirmation.

## Loop Log

- 2026-07-16 10:44:01: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-16: Codex reviewed applicable skills, design specification, medical-monitoring logs, incremental-diff/source-revision reviews, MG-K10 self-inspection and AE/MH risk outputs, and current official regulatory references.
- 2026-07-16: Scope, source list, success criteria and clinical/product boundaries were populated before dispatch.
