# R7 Slice-06 Harness 真实 synthetic 调用受限验收记录

日期：2026-08-28  
状态：`ACCEPT_R7_SLICE_06_HARNESS_LIVE_SYNTHETIC_LIMITED`

## 1. 验收结论

Slice-06 在 synthetic、无真实项目、无产品服务的边界内受限接受。R7 已用最薄
接缝复用 R1 attempt journal/controller 与冻结 R6 OMP adapter，完成真实 MTPLX
medium 与显式 DeepSeek V4 Flash max 的串行最小调用，未自动替换模型或使用
fallback。

本结论不等于真实项目、产品服务、前端/浏览器、医学质量、生产运行、医学写作或
R7 总体接受。

## 2. 不可变历史

- 首个 Matrix-14 包因 R1 冒号 attempt ID 不符合 R6 invocation grammar 而失败；
  R7 随后加入确定性映射和输出覆盖合同，R1/R6 未改。
- 修复后的首个 MTPLX 真实调用在原冻结 120 秒超时；唯一 linked retry 后续被
  恢复为 interrupted。该失败仍保留在
  `context/medical_monitoring_r7_slice06_matrix14_live_smoke_checkpoint_20260828.md`，
  不因后续成功而被覆盖或改写。
- 用户要求本地 MTPLX 等待更长后，新建独立受治理 timeout=300 执行包；未在旧包
  上静默重跑。

## 3. Codex 独立验收证据

### MTPLX medium

- 成功临时 workspace：`mm_r7_matrix14_4spl13_m`；worker 报告最初列出的
  `w23e14ng` 是早期空跑目录，未被用作成功证据。
- 冻结 selector：`mtplx/Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality`；
  effort `medium`；timeout 300 秒；fallback 为空。
- 一次 attempt；journal terminal `complete`；control `finished`；work unit
  `passed`；R6 receipt `parsed`、`analysis_complete=true`、exit 0、
  `fallback_used=false`；精确覆盖 `subject:SYN-MATRIX14-001`。
- 真实 adapter 时长 156.852 秒；profile digest
  `86f744ca7b8b9800d75761ac82849e584d46d6791fb41529eba3b708f0aad058`。

### DeepSeek V4 Flash max

- 独立临时 workspace：`mm_r7_matrix14_ds_csqz_ebu`。
- 冻结 selector：`deepseek/deepseek-v4-flash`；effort `max`；timeout 300 秒；
  fallback 为空。
- 一次 attempt；journal terminal `complete`；control `finished`；work unit
  `passed`；R6 receipt `parsed`、`analysis_complete=true`、exit 0、
  `fallback_used=false`；精确覆盖同一 synthetic 单元。
- 真实 adapter 时长 16.461 秒；profile digest
  `5e879bcf652fcdbb7692e70d47f60db877da88da8fd2b53cfa6e103ec95296ad`。

## 4. 确定性与边界门禁

- 当前 R7 + 产品路由回归：`192 passed in 11.52s`；compileall 通过。
- R1/R6 固定文件哈希与修复前一致；医学写作未修改。
- 没有活动 OMP 进程；8911/5174 均保持停止（`connect_ex=61`）。
- 执行包 review-gate 与 audit-execution 均 `ok=true`，三个声明 worker 均有
  完整输出，CodeBuddy `hy3-x:max` 路由无 runner fallback。

## 5. 下一阶段

按既定 R7 顺序进入 Slice-07 用户界面：先冻结用户可见的真实进度、后台离页、
中断恢复入口和中文状态合同，再做最小产品接线与 ego(lite) 浏览器验收。该阶段
不显示 provider/model/attempt/lease 等后端标识，不建立强制待办，也不设计或测试
系统安全功能。项目/中心受试者流向看板进入同一 UI 阶段的后续独立子切片，并继续
要求节点、连线与表格可重建对账。
