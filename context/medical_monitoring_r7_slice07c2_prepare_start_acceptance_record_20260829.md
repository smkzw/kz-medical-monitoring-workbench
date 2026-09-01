# R7 Slice-07C-2 一键准备、启动与运行历史接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_07C2_SYNTHETIC_LIMITED`

## 1. 本切目标与结果

在不启动服务、不运行真实项目、不调用模型的前提下，将 07C-1 的三模式设置、完整快照、
已发布基线和特殊关注规则接入一键“准备并开始”。服务端解析公开 token，冻结 work-unit
manifest，先原子保留运行身份，再绑定、准备和启动后台工作；浏览器重试不会创建第二个运行。

项目运行历史只返回公开运行 token、中文模式、数据截止点、比较范围、运行状态、结果可用性和
主要动作。历史状态以真实运行进度校准，已完成或已中断的任务不会长期显示“运行中”；单条
异常记录也不会拖垮整个项目历史。07C-2 内结果入口始终不可用。

## 2. Codex 纠偏

- 修复首次请求只完成 reservation、尚未完成 prepare 时的“死运行”：同一幂等请求继续完成
  原运行并复用同一 public token。
- 修复 launch history 状态永久停在 `running`：按冻结 manifest 读取 runtime 状态并持久校准。
- 补齐首次 start 失败、管理员随后 start 并快速完成时的 `waiting_start → completed` 合法恢复。
- 校准逐记录降级；某一运行状态异常不再导致整个 `GET /runs` 失败。
- 补产品层跨项目 snapshot/baseline token fail-closed、医学监察员可启动/医学写作角色被拒绝。

## 3. 决定性证据

- 产品路由：`43 passed in 4.04s`。
- 完整 R7 POC（最终复跑）：`181 passed in 14.83s`。
- `compileall` 通过；8911/5174 均无监听。
- 执行审计 `ok=true`。
- 独立 `codebuddy-cli/deepseek-v4-flash:max` 会商保持同一 session：Round 1 与 Round 2
  提出可复现纠偏，Round 3 返回 `ACCEPT`，无 P0–P2 或合同阻断。

## 4. 路由与资源事实

执行首路由 CodeBuddy/GLM 因配额终态失败，随后使用执行包已声明的
`openai-codex/gpt-5.6-luna:xhigh` CLI 兼容降级完成三个工作项。本地 MTPLX 因当时可用内存
不足 50 GB 路由准入阈值而未调度；这是资源门禁，不是 MTPLX 模型调用失败。独立会商没有
fallback。后续真实本地 MTPLX 调用必须继续采用长等待，不能以短时无输出判断失败。

## 5. 保留边界与下一步

本接受仅证明 synthetic/offline prepare-and-start、幂等恢复、项目隔离、公开历史和产品路由
合同；不证明结果发布、结果入口、前端、真实项目/模型、医学判断、R7 总体或 R8。

下一子切 Slice-07C-3 只实现 run-keyed 原子 `ResultPublication`、有界 progress 扩展和 R5
authority packet/result-entry：必须冻结 project/run/snapshot/cutoff/site coverage、风险/受试者/
中心/项目聚合与 Patient Journey 引用；发布失败不得开放结果入口，发布成功后才可将
`result_available` 置为 true。继续保持 8911 与真实项目停止，并保护医学写作子系统。
