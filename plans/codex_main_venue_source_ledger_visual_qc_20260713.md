# Codex Main-Venue Plan: source_ledger_visual_qc_20260713

Date: 2026-07-13
Objective: 审阅医学经理工作台项目级来源台账的桌面信息架构、中文标签、状态与override交互，基于真实MY009和RUX截图提出可执行修正，不编辑生产文件

## Task Decomposition

1. 三路独立读取同一最终截图、实现和QC指标。
2. 每路在同一会话完成独立分析、怀疑式挑战和修正版。
3. Codex比较共同意见与冲突，回到真实Chrome截图核实。
4. 仅落盘双方都认可且有证据的修改；重新构建、截图和回归。

## Source Packet

- MY009 1600桌面截图。
- RUX 1920桌面截图。
- QC JSON，当前failures为空。
- `SourceRegistryPage`和`.source-ledger-*`实现。
- Safety/PV来源准入旧页面截图作为视觉语言对照。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/source_ledger_visual_qc_20260713/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/source_ledger_visual_qc_20260713/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/source_ledger_visual_qc_20260713/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 初始化：2026-07-13 03:37。
- 运行状态和session id由runner日志记录；慢响应保持pending，按既定fallback规则处理。

## Codex Verification Checklist

- 三轴状态没有颜色/语义冲突。
- 历史版本默认不干扰当前工作，但入口可发现。
- override表单逐项确认与10字理由门槛明确。
- 1600/1920无横向溢出、截断冲突或元素重叠。
- 中文临床试验语境自然；不显示内部枚举、路径、hash或安全扫描文案。
- 项目切换后条目、统计和详情不串项目。
