# Codex Main-Venue Plan: mm_r7_slice08c4_visual_acceptance_20260830

Date: 2026-08-30
Objective: 独立打开08C-4当前参考、baseline/revised并列图、三视口原图和结构化记录，审阅中文原生性、时间轴/流向层次、卡片/表格/抽屉、overlay/push、文字间距配色动效与交互一致性；不得只读源码，全部P0-P4为零才可接受运行时视觉交付

## Task Decomposition

1. 参与方先读 frozen contract 与 conference pack manifest，再实际打开 Sankey、7 张并列图和三视口 current 原图。
2. 独立审阅信息层级、中文、时间轴、流向、风险卡、overlay/push、裁切/重叠、配色/阴影/动效与可访问性结构化证据。
3. 逐级报告 P0-P4；若有缺陷，Codex 组织同一 execution session 修复和同一 conference session 复核。
4. 只有全部 P0-P4=0 且 Codex 自己的图像/结构化/测试证据一致，才接受 08C-4 visual runtime。

## Source Packet

- `artifacts/mm_r7_slice08c4_ego_visual_20260830/visual_conference_input_pack/{README.md,MANIFEST.json}`
- `artifacts/mm_r7_slice08c4_ego_visual_20260830/reference_flow_sankey.png`
- `artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_revised/collage/*.png`（7 张）
- `artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_revised/{1280,1440,1920}/*.png`
- `artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_revised/FINDINGS_revised.json`
- `artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_revised/reconciliation/*.json`
- frozen 08C-4 contract/spec and execution review/metrics

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `grok-build` primary unavailable → `cursor` fallback | `grok-4.6` → `cursor-grok-4.6:high` | `runs/conference/mm_r7_slice08c4_visual_acceptance_20260830/visual_single_object.md` through `visual_single_object_round8.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Grok Build primary was unavailable before a usable conference response. The declared Cursor fallback stayed in session `01a04f3f-8f1b-7000-a20e-989c45d36cf4` through eight visual-review rounds. Execution remediation progressed through R10; the final conference round independently reopened the R10 1920 originals and returned `ACCEPT_VISUAL` with P0-P4 all zero for the declared desktop-only 1920×1080–4K scope.

## Codex Verification Checklist

- [x] Contract and execution packets are separate and accepted at their own scope.
- [x] 8911/5174/8984 stopped; ego task spaces empty.
- [x] Codex opened current combined/original images and independently closed one missed 1280 risk-card P2.
- [x] Participant opens all required visual evidence, not source-only.
- [x] P0-P4 zero independently confirmed for desktop 1920×1080–4K; 1280/1440 remain resilience evidence, not production gates.
- [x] Codex independently reopened the final 1920 originals and accepted the fold repair; governance audit results are recorded in review/metrics.
