# Codex Main-Venue Plan: mw_protocol_structure_corpus_conf_20260719

Date: 2026-07-19
Objective: 会商公开原始Protocol跨适应症/跨分期结构语义分析的方法、抽样充分性、必选与条件可选判定阈值、语料标签和产品回写边界

## Task Decomposition

1. 独立审阅分层抽样、申办方去重、文档角色和版本策略。
2. 建立章节标题到医学/监管功能的语义归并方法和人工复核边界。
3. 设计频率证据与定性裁决结合的适用性分类规则。
4. 将可复核结论映射至模板节点、语料标签、AI候选路由和回归测试。

## Source Packet

- `context/mw_protocol_structure_corpus_20260719_context.md`
- `context/mw_protocol_structure_corpus_conf_20260719_conference_context.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`
- 三路执行者的候选Protocol报告和ClinicalTrials.gov官方复核结果

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_protocol_structure_corpus_conf_20260719/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_protocol_structure_corpus_conf_20260719/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_qoder` | live QoderCLI PID `39908` | `qwen3.8-max-preview` | `runs/qoder/mw_protocol_structure_corpus_qoder_manager_chair_20260719.md` |
| fallback only: `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_protocol_structure_corpus_conf_20260719/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Qoder is considered unavailable only after terminal failure, loss of PID,
  unrecoverable authentication/model failure, or no useful progress after the
  configured long wait and a controlled same-session retry.
- Slow output alone is not failure. Do not poll frequently.
- Grok fallback must not start while Qoder remains live and progressing.

## Codex Verification Checklist

- Recheck every selected NCT and ProvidedDocs URL against the official API.
- Verify document role from file metadata and the actual first pages/TOC.
- Enforce distinct sponsors and one primary analysis version per study.
- Separate observed sample frequency from regulatory requirement.
- Require tests before any production template or routing change.
