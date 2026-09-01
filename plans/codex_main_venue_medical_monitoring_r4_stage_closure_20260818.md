# 医学监查 R4 阶段总体关闭执行计划

日期：2026-08-18  
目标：在不启动产品/服务、不触碰真实项目或医学写作的前提下，以当前文件系统证据独立裁决 R4 D01–D10 是否达到阶段完成门。

## 工作项

1. 重建 D01–D10 合同、最终接受记录、源码、测试和冻结锚点清单。
2. 运行完整 R4 与关键 generator/anchor/Ruff/compile/端口门，审计跨域传播与反过拟合路径。
3. 由 fresh-context Sol/high reviewer 独立复核全部关闭门并给出单一 verdict。
4. 若 `REVISE_R4_STAGE`，仅修复有证据的传播路径并复验；若 `ACCEPT_R4_STAGE`，写入不可混淆的 R4 阶段接受记录并更新 R0–R8 恢复锚点。
5. R4 接受后再建立 R5 阶段合同、外部模式调研和用户面实施路线；不得提前混入本轮。

## 验证

- 每个结论都绑定文件、测试或静态定位；历史 `ACCEPT_Dxx` 不能替代当前阶段级重建。
- 完整 R4 测试、Ruff、compile、generator/anchor 与 8911 停止必须在 reviewer 使用的稳定快照上可复现。
- 独立 reviewer 拥有阶段 done；Codex 复核其证据和最终文件状态。

## 保护边界

- 允许写入：本任务 context/plan/review/metrics/prompt/run/log，以及经退回后确有必要的 R4 POC 源码/测试。
- 禁止写入：医学写作、产品源码、五个真实项目来源；8911 必须保持停止。
