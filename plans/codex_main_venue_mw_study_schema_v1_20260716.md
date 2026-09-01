# Codex Main-Venue Plan: mw_study_schema_v1_20260716

Date: 2026-07-16
Objective: 设计并实现医学写作研究流程图语义编辑器：由已确认StudyDefinition事实生成、医学经理可有限调整布局、版本化审计、确定性SVG与DOCX插入，并用PNH与D017Ⅰ期两个真实项目及RA合成反例完成桌面端E2E验收

## Task Decomposition

1. Audit the current StudyDefinition, invalidation, work-copy, document-object, exporter and frontend integration points.
2. Define a minimal typed graph and layout contract that separates clinical topology from presentation offsets.
3. Validate the contract against two real, clinically distinct projects (PNH and CMS-D017 Phase I), the synthetic RA negative/generalization fixture, and explicit missing/conflicting-fact cases.
4. Implement contracts, repository/API, deterministic SVG renderer and governed document-figure projection with tests.
5. Implement the desktop semantic editor with auto-layout, bounded movement, validation, preview and insert/update actions.
6. Run isolated API/browser/DOCX verification, visual QC at desktop viewports, regression tests and Codex skeptical review.
7. Persist decisions, failures and recovery state; keep stable ports available and do not pause without an explicit user instruction.

## Source Packet

- The source packet is defined in `context/mw_study_schema_v1_20260716_conference_context.md`.
- Participants may inspect additional in-workspace code/tests needed to substantiate a claim but may not edit production files in this conference pass.
- External product/library claims require authoritative current sources and must be labeled as evidence, inference or recommendation.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_study_schema_v1_20260716/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_study_schema_v1_20260716/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_study_schema_v1_20260716/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-07-16. Initial participants run in parallel; chair runs after their persisted outputs are available or explicitly pending under the configured wait policy.
- Codex records route, session, fallback and quality in `metrics/mw_study_schema_v1_20260716_conference_metrics.md`.

## Codex Verification Checklist

- [ ] Every clinical node/edge maps to confirmed StudyDefinition data or an explicit medical-manager confirmation.
- [ ] Topology and layout are versioned separately and stale writes fail closed.
- [ ] Same canonical input produces deterministic graph and sanitized SVG output.
- [ ] PNH and CMS-D017 Phase I real fixtures plus the synthetic RA negative fixture prove no project-specific defaults or topology leakage.
- [ ] Document insertion/update and DOCX rendering preserve a stable figure identity without duplicates.
- [ ] Desktop browser QC covers editor controls, keyboard/focus, maximum workspace, drag bounds, validation and reload recovery.
- [ ] Focused and broad tests, production frontend build and relevant full regression pass.
