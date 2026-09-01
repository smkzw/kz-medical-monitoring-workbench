# R7 Slice-08D 三模式综合回归合同接受记录

日期：2026-08-30  
决定：`ACCEPT_R7_SLICE_08D_CONTRACT_V0_2`

## 已接受范围

- v0.1 与 v0.2 纠偏附录合并构成 08D 完整合同；冲突时 v0.2 优先。
- 四类业务场景展开为 20 个固定 case key，并补齐反向 mode/basis、同值重放、冲突、缺失和恢复断言。
- 确定性门固定为 5 个 `PYTHONHASHSEED` × `normal/-O/-OO` 共 15 格。
- oracle 必须从输入侧冻结事实独立重建，不得从产品 DTO、数据库结果、自报 digest、fixture 名或 case id 反算 expected。
- 08D 只做 synthetic/offline 综合回归，不重复 08C-4 的 ego(lite) 视觉算法、截图或页面设计。

## 会商与治理证据

- 冻结合同：`reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_2_20260830.md`
- 首轮挑战：`runs/conference/mm_r7_slice08d_contract_20260830/general_single_object.md`
- 同会话复核：`runs/conference/mm_r7_slice08d_contract_20260830/general_single_object_round2.md`
- 最终结论：`ACCEPT_CONTRACT_V0_2`，P0/P1/P2/P3/P4 = `0/0/0/0/0`。
- `validate-conference` 与 `review-gate --require-verification` 均通过。

## 边界

本记录只接受 08D 实施合同，不接受实现完成、Slice-08 总体、真实项目/模型医学质量、R7、R8、生产或商业化。8911/5174 保持停止；医学写作保持不变。

## 下一安全动作

按冻结合同启动 08D governed execution：分工实施 20 格 synthetic 矩阵与独立 oracle、15 格确定性和故障/CAS/重开恢复、相邻回归与证据包；由执行经理汇总，随后再做独立接受会商。
