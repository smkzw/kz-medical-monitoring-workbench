# R7 Slice-07C-3 结果发布实现接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_07C3_SYNTHETIC_LIMITED`

## 1. 本切结果

synthetic/offline 三模式运行现在具备唯一、可恢复、原子化的结果发布路径：R5-owned typed assembler/
bridge 复用既有 S4 builder/validator；R7 registry v2 在 reserve 后 CAS 绑定 runtime manifest，随后检查
R6 receipt、双 manifest、site/member/source 闭合，只有全部一致才把 publication 与历史结果入口同事务
置为可用。

产品 progress 增加稳定发布状态和中文文案，history 保持七字段；result-entry 只返回项目、公开运行、
冻结快照、数据截止点、中心选项和 opaque result context token。不可用、漂移、审计链异常或发布中断均
失败关闭，不回退旧运行或其他项目结果。

## 2. Codex 关键纠偏

- 拒绝 reserve 前读取 runtime binding/manifest 的折中，新增 post-reservation manifest CAS API 与顺序探针。
- 以实际 typed R5 provider/bridge 从产品 POST 发布贯通 S4 builder/validator，并在 result-entry 重取。
- 从产品入口注入 finalize 两个事务故障点，证明 publication/launch 无单边提交且同身份可恢复。
- 补 snapshot token/ref/source/cutoff 映射门禁、fingerprint 规范化和 reserve completion-metadata 禁令。
- 将 completed+non-available 文案对齐为“分析已结束，结果整理未完成”，审计链异常改为 blocked。
- result-entry 重建精确 receipt gate，先对账 identities/digest，再向 provider 传递持久化 attempts。

## 3. 决定性证据

- 产品 07C-3：`7 passed, 43 deselected`。
- registry：`22 passed`。
- R5 bridge + 既有 S4 builder/validator：`179 passed`。
- combined product/R7/R5：`249 passed in 32.36s`。
- worker 最终回归另一次为 `249 passed in 30.93s`；`32.36s` 为 Codex 验收复跑，两者是同套件的两次独立执行。
- compileall 通过；8911/5174 均无监听。
- 执行审计与 review gate 通过。
- 独立 `codebuddy-cli/deepseek-v4-flash:max` 同 session 两轮：Round 1 的 6 个 P2 全部关闭，Round 2
  返回 `ACCEPT`，无新增 P0-P2；无 fallback。

## 4. 边界与下一步

接受仅覆盖 synthetic/offline backend 结果发布、公开投影和入口合同；不证明前端、真实项目/模型、
医学质量、R7 总体或 R8。下一子切为 07C-4：中文向导、历史/主按钮、进度/结果看板与 Patient Journey
贯通，并使用 ego(lite) 做真实用户视角视觉和交互验收。继续保持真实项目、8911 和医学写作子系统不动。
