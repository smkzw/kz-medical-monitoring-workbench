# Codex Main-Venue Plan: mw_system_rearchitecture_audit_20260808

Date: 2026-08-08
Objective: 冻结当前医学写作进度，全量审计医学经理工作台与医学写作需求、实现、测试和缺口，调研 Graph engineering 与多 Agent 工作流，基于 TP-MA-07 模板完成需求访谈、目标架构和重构实施计划；用户确认前不实施产品重构

## Task Decomposition

1. Freeze and independently verify the current r17/Protocol P0 boundary.
2. Audit original requirements, approved decisions, current code/data/state,
   implemented slices, missing production evidence, and all material historic
   E2E/multi-model findings.
3. Inspect TP-MA-07 as both a semantic template and a Word object model.
4. Run two-pass primary-source research on graph orchestration candidates,
   licenses, persistence/HITL/replay semantics, and ICH constraints.
5. Produce a provisional canonical study/document graph, chapter-contract
   model, five-responsibility Protocol workflow, and strangler migration path.
6. Run multi-round user interviews for authority, approval, source hierarchy,
   operational scope, chapter behavior, UI, and acceptance decisions.
7. After the revised design exists, dispatch the initialized fresh-context
   conference for contradiction review; do not dispatch prematurely.
8. Codex verifies the resulting artifacts and submits the final staged plan for
   user approval before any product implementation.

## Source Packet

- Current filesystem under the workbench root.
- Frozen Protocol P0 r17 context/run/review/metrics dated 2026-08-05.
- Original requirements ledger, 2026-07-27 PRD, approved 2026-07-31 roadmap,
  production rebaseline, Phase 0B/0C, 4x3/5x3 role-acceptance evidence.
- Backend/frontend contracts, repositories, state machines, template registry,
  corpus, full-draft/QC services, DOCX exporter, Word receipt and tests.
- User-supplied TP-MA-07 template and its 49-page temporary render.
- Official LangGraph, Microsoft Agent Framework, Pydantic AI, CrewAI,
  AutoGen, Semantic Kernel, Temporal, ICH M11 and ICH E6(R3) sources.
- Consolidated checkpoint:
  `runs/MW_SYSTEM_REARCHITECTURE_AUDIT_CHECKPOINT_20260808.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_deepseek_flash` | declared `pi/alibaba`; effective night route | declared `qwen3.8-max-preview`; effective `qwen3.8-max` | `runs/conference/mw_system_rearchitecture_audit_20260808/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | effective fallback `grok-build` | `grok-4.5` | `runs/conference/mw_system_rearchitecture_audit_20260808/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Conference was dispatched once after D001–D017, six-section approval, formal
  spec self-review and prompt preflight. Both pass-1 reports completed; the
  same-session chair delta completion accepted design-v1.2 for user review.
- Native `gpt-5.6-luna` was unavailable in the current App selector. Because the
  first chair fallback would duplicate the effective Qwen participant, the next
  declared Grok Build fallback was selected and recorded.
- Three bounded native read-only audit workers completed in the current Codex
  task: current implementation, history/requirements, and external graph
  engineering. Their outputs were independently checked against source files
  and consolidated; they are not the formal conference roles in the table.

## Codex Verification Checklist

- [x] Global, workspace and frontend instructions read and hashed.
- [x] Current r17 authority and stopped runtime confirmed from durable records.
- [x] No product service, database, OCR, translation, download, test or E2E run.
- [x] Current implementation and test inventory statically audited.
- [x] TP-MA-07 extracted, rendered to 49 pages and visually inspected; original
      file hash rechecked unchanged.
- [x] External framework claims checked against primary docs, source,
      releases and licenses.
- [x] Provisional architecture and migration boundaries recorded.
- [x] User interview rounds complete through D017.
- [x] Revised full design complete and Codex self-reviewed.
- [x] Formal fresh-context conference dispatched, revised and accepted for user spec review.
- [ ] User approves design-v1.2 written specification.
- [ ] Detailed implementation plan is written, independently challenged and user-approved.
