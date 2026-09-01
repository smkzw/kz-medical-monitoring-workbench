# Conference Context: medical_writing_content_quality_architecture_20260714

Created: 2026-07-14 08:38:06
Objective: 审阅医学写作源内容异常闭环架构：保守确定性检测、正文优先证据、带理由医学确认/纠正、内容指纹失效、审计、working-copy批准阻断、approved-final兜底门禁及编辑器内紧凑交互；基于RUX真实<0}阳性和D001/PNH对照，不修改原始方案
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- The visual-only route (`kimi-k2.7-code` and `qwen3.7-plus`) is intentionally not used because this bounded conference excludes browser and visual acceptance; Codex performs those checks independently after implementation.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass.

## Source Of Truth

- `records/active_slices/medical_writing_content_quality_20260714/ARCHITECTURE_REVIEW_PACKET.md` is the bounded evidence and proposal packet.
- `records/active_slices/medical_writing_content_quality_20260714/TASK_RECORD.md` is the current execution contract.
- RUX exact positive source text is `对于研究中具有生育能力的女性受试者：<0}` at `docx:table:10:row:2:cell:0`.
- D001 and MY008211A-PNH-3-01 are real cross-project controls containing many legitimate comparison operators.

## Scope

- In scope: challenge the proposed deterministic rule, finding identity/fingerprint model, disposition state machine, concurrency/audit, approval/export gates, three-project verification, and editor-first interaction.
- Out of scope: production edits, web research, source DOCX modification, autonomous medical correction, malware/security scanning, unrelated modules, browser or visual acceptance.

## Success Criteria

- Identify concrete false-positive, false-negative, stale-state, bypass, concurrency, audit and UX failure modes.
- Recommend the smallest coherent backend/API/frontend contract that preserves immutable source and draft usability.
- State which proposal elements are accepted, rejected or require tests; keep evidence, inference and recommendation separate.
- Return a compact three-round same-session loop trace and no production writes.

## Parallel Work Rule

Each participant independently runs the whole bounded workflow and writes a separate output. The GLM chair compares only after all available participant outputs are in or explicitly pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns browser/visual acceptance, final clinical/product conclusions and production writes.
- Read only the files listed in each role prompt. Do not inspect patient-level data or any source DOCX.
- Exact source text is primary evidence; locator is secondary. Do not recommend hiding a confirmed warning.
- Do not recommend project-specific rules or AI-only approval gates.

## Loop Log

- 2026-07-14 08:38:06: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Bounded architecture packet added after Codex verified the three-project operator baseline and existing source/working-copy/approval architecture.
