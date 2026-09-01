# Codex Main-Venue Plan: medical_writing_domain_table_designers_20260714

Date: 2026-07-14
Objective: 基于真实跨项目方案表格，将现有11类医学写作模板中高复用、高风险的非研究流程表升级为领域化交互设计器、服务端语义验证和确定性Word输出，并保持统一工作副本、AI修订、审批和审计链

## Task Decomposition

1. Re-audit the 11-template catalog against eight real protocols and rank evidence.
2. Obtain independent architecture, medical-language and code-path critiques, then a GLM chair synthesis.
3. Codex decides the first promoted domains and schema boundary.
4. Add failing contracts for semantic roles, mapping state, validations, dual representation and Word persistence.
5. Implement the smallest backend registry and schema-driven desktop inspector on the existing designer.
6. Verify at least two projects per A-grade domain, destructive cases, Word export, frontend build and full regression.
7. Persist review, metrics, task record and runtime state; continue the overall Goal.

## Source Packet

- Verified real-table evidence and evidence ranking in the active-slice record.
- Existing 11-template service and generic table service.
- Existing structured-table contracts and SoA typed model.
- Existing desktop designer, where only SoA currently has a domain panel.
- Existing tests for template coverage and frontend controls.

## Initial Main-Venue Hypothesis

- Promote `objectives_endpoints`, `treatment_dose`, `laboratory_panel`, and `version_history` based on A-grade cross-project evidence.
- Keep `dose_modification` as a separate, generic-threshold domain profile because its medical risk is high and its boundary from CM is explicit, while acknowledging only B-grade table evidence.
- Keep sample-size, stopping, AE management, PK/ADA schedule and analysis-set templates in generic mode until stronger real-table evidence exists.
- Prefer one domain-profile registry plus one schema-driven inspector and validator over separate components for each domain.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_domain_table_designers_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_domain_table_designers_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_domain_table_designers_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_domain_table_designers_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- Exact source files and hashes remain unchanged.
- Promoted domain profiles have typed semantic roles and fail-closed validation without project-specific rules.
- Existing raw/source tables remain fully visible and editable in generic mode even before mapping confirmation.
- Template instances preserve semantic roles through save/reload, cell AI application and Word export.
- At least two real projects cover each A-grade promoted domain where source examples exist.
- Existing SoA and paragraph/table AI flows do not regress.
- Desktop layout is verified separately by Codex; Hermes output cannot substitute for browser acceptance.
