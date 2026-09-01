# Conference Context: mw_current_full_audit_20260722

Created: 2026-07-22 10:22:00
Objective: 从资深医学撰写用户、产品、临床科学、后端、前端、独立AI与DOCX成品视角审计当前医学写作子系统，输出可复现差距和修复优先级
Task type: `complex_delivery_conference`
Risk: `critical`
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

- Current production source: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Durable current-state records: `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`, `CURRENT_GAP_MATRIX.md`, `END_TO_END_PROGRESS_AUDIT.md`, `PROTOCOL_ASSEMBLY_PLAN_DECISION.md`.
- Historical Qoder report is context only: `records/qoder_full_system_audit_20260719/QODER_FULL_AUDIT.md`; it predates the current implementation and must not be copied forward as current evidence.
- Current task-created Word evidence is under `records/active_slices/medical_writing_production_rebaseline_20260722/docx_layout_qc/word_e5/`.
- Ports 5180/8910 currently point to an older `qoderwork` tree and are not current-product acceptance evidence.

## Scope

- In scope: full current medical-writing journey; project creation; greenfield and synopsis-import paths; StudyDefinition authority and quarantine; AI-first prefill; competitor/IB/corpus; independent product AI boundaries; synopsis/chapters/dynamic applicability; editor and tables; literature/reindex; SoA/flowchart/attachments; DOCX; concurrency/recovery; source/API/frontend/test consistency.
- In scope: reproduce defects with read-only probes and isolated temporary runtime; assess whether current Qwen audit is complete enough and identify evidence gaps.
- Out of scope: editing production source, changing production databases, final clinical/regulatory/visual/Word acceptance, and substituting auditor-model prose for product AI output.

## Success Criteria

- Each P0/P1 claim has a source locator plus a reproducer, failing test, API probe, browser step, or explicit evidence gap.
- Separate current defects from already-fixed history and from untested hypotheses.
- Audit the entire medical-writer path from minimum facts to exported DOCX, including lazy-user friction and cross-module invariants.
- Explicitly test that product AI, not Qoder/Kimi, performs AI business functions.
- Return a ranked remediation map with dependency order and release gates; do not declare production ready.

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

## Loop Log

- 2026-07-22 10:22:00: Conference initialized by `hermes_workflow_guard.py init-conference`.
