# Codex Main-Venue Plan: safety_pv_redesign_architecture_20260713

Date: 2026-07-13
Objective: 复核Safety/PV A方案、统一项目医学风险核查工作台、共享底层与四类PV文件医学审阅交互，形成Product Design Brief决策依据，不执行生产修改

## Task Decomposition

1. Preserve the user's two-entry product boundary, approved Option A, and newly added monitoring-owned safety risk warning entry.
2. Obtain three independent three-round critiques from distinct perspectives.
3. Run GLM chair only after participant outputs are complete.
4. Codex compares recommendations against current code and regulatory/product evidence.
5. Update the Product Design Brief decision packet; do not modify production behavior before user approval.

## Source Packet

- `records/active_slices/safety_pv_redesign_20260713/DISCOVERY_RECORD.md`
- `records/active_slices/safety_pv_redesign_20260713/SHARED_CONTRACT_AND_ACCEPTANCE_DESIGN.md`
- `records/active_slices/safety_pv_redesign_20260713/LEGACY_INTERFACE_MIGRATION_IMPACT.md`
- `records/research/safety_pv_dual_project_20260713/EXTERNAL_AND_LOCAL_BASELINE.md`
- Current monitoring, medical-writing and legacy Safety/PV contracts/services named in the role prompts.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/safety_pv_redesign_architecture_20260713/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/safety_pv_redesign_architecture_20260713/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/safety_pv_redesign_architecture_20260713/general_opencode_mimo.md` |
| `general_chinese_pv_fallback_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/safety_pv_redesign_architecture_20260713/general_chinese_pv_fallback_qwen.md` |

- MiniMax: medical-manager workflow and cross-module interaction ergonomics.
- DeepSeek: Chinese PV terminology, regulatory/document-review logic and user-AI collaboration.
- MiMo: contracts, ownership, compatibility migration, state/concurrency and test architecture.
- Qwen fallback: activated only because the Buddy DeepSeek role did not establish a resumable session after round 1; it repeats the Chinese/PV assignment in a new provider route.

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/safety_pv_redesign_architecture_20260713/general_chair_glm.md` |
| `general_chair_fallback_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/safety_pv_redesign_architecture_20260713/general_chair_fallback_qwen.md` |
| `general_chair_final_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/safety_pv_redesign_architecture_20260713/general_chair_final_mimo.md` |

GLM-5.2 failed after round 1 without a resumable session. The Qwen chair fallback is activated under the user-approved different-provider fallback rule; the incomplete GLM file remains evidence only.

Qwen chair completed three rounds but returned an incomplete patch/diff artifact. MiMo is activated as final chair fallback with a stricter complete-package schema and the latest unified risk-workbench inputs.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, session id, three-round continuation proof, pending/failed/incorporated status, retry reason and fallback.
- Do not start GLM chair before all available participant outputs are complete or terminally failed.

## Codex Verification Checklist

- Every recommendation traces to listed source or is labelled inference.
- No recommendation creates duplicate monitoring or writing facts.
- Option A is approved; verify the dedicated monitoring risk entry does not recreate Safety/PV ownership.
- DSUR/SAE/2.7.4/ISS are not collapsed into one template.
- RUX and MY009 acceptance covers actual controls and backend transitions, not display-only checks.
- Product Design Brief remains unapproved until user confirmation.
