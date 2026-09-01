# R7 Slice-07C-3 结果发布合同冻结记录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_07C3_RESULT_PUBLICATION_V0_2`

## 1. 冻结目标

冻结 synthetic/offline 三模式运行完成后的唯一结果发布路径：只有 runtime、R6 receipts、双 manifest、
site coverage 与 R5 authority packet 全部闭合，才能原子开放本次结果入口。

## 2. 核心决定

- 实施第 0 步由 R5-owned assembler/bridge 唯一复用既有 S4 builder/validator，不在 R7 重算医学事实。
- 每个 run 只有一个 publication；请求指纹只含冻结身份，receipt-set digest 在 finalize 时绑定。
- registry v2 采用 additive transaction migration；publication available 与 launch result flag 同事务提交。
- blocked/recoverable_failed 可按冻结状态机恢复；available 不可回退或覆盖。
- progress 仅由产品 router 叠加；history 保持七字段；result-entry 只接受 public run token。
- site coverage 来自冻结快照，snapshot option token 与 packet snapshot_ref 通过冻结 run options 对账。

## 3. 独立会商

`codebuddy-cli/deepseek-v4-flash:max` 在同一 session
`ee449ae8-e72f-4c61-ab8f-692415599dc5` 完成三轮：Round 1/2 提出并复核可复现缺口，Round 3
返回 `ACCEPT`。无 fallback、无模型失败。最终一项 setup/runtime manifest 指纹优先级措辞已在冻结前并入。

## 4. 边界与下一步

本记录只接受合同，不接受任何源码实现、前端、真实项目/模型、医学质量、R7 总体或 R8。下一安全动作
是按合同 §10 初始化独立执行包，从 R5-owned assembler/bridge 开始，再实现 registry/gate/finalize 与
product progress/history/result-entry，最后运行 synthetic 故障矩阵和相邻回归。8911 与真实项目保持停止，
医学写作子系统保持不变。
