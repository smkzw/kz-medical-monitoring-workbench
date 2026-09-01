# Codex Main-Venue Plan: medical_writing_additional_table_domains_20260714

Date: 2026-07-14
Objective: 基于额外真实protocol语料收敛并实现下一批跨项目、跨适应症医学写作表格领域设计器，同时保持统一工作副本、AI、审批和Word链

## Task Decomposition

1. Build a deterministic inventory from original protocol DOCX/PDF files and retain parse/OCR gaps.
2. Independently audit three domain groups through parallel SubAgents; Codex verifies exact evidence before use.
3. Grade each candidate against the explicit multi-project threshold and prepare a bounded conference packet.
4. Run the three-participant, three-round Hermes conference plus the GLM chair in same-session loops.
5. Implement only Codex-accepted profiles through the existing registry and shared React designer.
6. Run multi-project persistence, AI, approval, Word and full-repository regression; update durable records and review gate.

## Source Packet

- Conference context and source boundaries: `context/medical_writing_additional_table_domains_20260714_conference_context.md`.
- Expanded evidence: `records/active_slices/medical_writing_additional_table_domains_20260714/domain_table_evidence.md` and JSON peer.
- Codex-verified decision packet: `records/active_slices/medical_writing_additional_table_domains_20260714/EVIDENCE_DECISION_PACKET.md`.
- Existing evidence/standards: the two files listed in the context.
- Current profile/template/contract/frontend implementation listed in the context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_additional_table_domains_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_additional_table_domains_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_additional_table_domains_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_additional_table_domains_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Not dispatched yet. The three independent audits and Codex source verification are complete. Prompt preflight follows after adding the verified decision packet and current implementation/tests to each read list; the slower full-corpus inventory remains corroborating evidence rather than a substitute for page-level verification.

## Codex Verification Checklist

- Verify every cited source exists and every promoted domain has sufficient distinct project/indication evidence.
- Reject prose-only or SoA-only false positives and duplicate-file inflation.
- Check no project-specific values enter profile defaults, options or validation.
- Test source mapping and template instances separately.
- Test table-scoped blockers, sibling isolation, cold restart and Word table content/order.
- Run frontend contracts/build, backend compile, medical-writing suite and full repository suite.
- Verify running API health/profile catalog after restart.
- Record browser/Word visual acceptance as pending, not passed.
