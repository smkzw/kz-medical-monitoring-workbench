# Codex Main-Venue Plan: monitoring_p10_release_chain_mapping_gate_20260730

Date: 2026-07-30
Objective: 独立挑战医学监查字段映射新版科学性合同与规则发布链，重点审查CM/IP/背景治疗边界、来源身份贯穿、二次医学批准消除、影子验证和daily-run失败关闭

## Task Decomposition

1. 等待字段映射合同与规则发布链两个互不重叠的实现切片完成离线回归。
2. Codex 只复核二者的交叉身份、状态机和医学边界，不重复完整遍历代理已验证范围。
3. 固定实现文件、测试、任务记录和 SHA-256；将精确 read set 写入参与者 prompt。
4. 并行分发两个独立参与者：一个偏医学/工作流反例，一个偏工程合同/状态机反例。
5. 参与者完成后由独立 chair 综合冲突，必要时在原 session 做一次目标化追问。
6. Codex 复现高风险发现；只接受有源定位或可运行断言的问题。
7. 修复后运行聚焦、相邻、前端构建和真实只读状态投影，再决定是否恢复产品独立 AI。

## Source Packet

- 会议上下文中列出的 P10 task context、LOOP ledger、MG-K10 审计、科学性放行矩阵、
  规则发布链缺口、推荐合同、旧旁路关闭和方案 evidence v2 合同记录。
- 两个实现切片完成后的精确源码、测试和 SHA-256。
- 真实运行库仅可只读，不允许候选决定、mapping 激活、规则发布或 daily run。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 分发前记录北京时间、原始/有效 route 和 prompt SHA。
- 慢响应保持 pending；只有终止错误、资源耗尽或硬等待后无进展才走 fallback。
- 同一角色需要补证时继续原 session，不新建会话。

## Codex Verification Checklist

- [ ] 参与者均读取相同冻结 source packet，未查看彼此输出。
- [ ] chair 只在参与者输出完成后启动并比较冲突。
- [ ] 每个 P0/P1 发现有文件/测试/真实只读状态定位。
- [ ] 字段映射反例覆盖 IP/背景治疗/CM、剂量不确定、量表和能力缺口。
- [ ] 规则链反例覆盖身份漂移、项目切换、二次审批、影子样本和发布门。
- [ ] Codex 复现高风险发现并完成修复后回归。
- [ ] 最终真实运行与浏览器验收仍由 Codex 执行。
