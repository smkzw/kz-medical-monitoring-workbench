# R7 Slice-07C-3 执行纠偏请求记录

日期：2026-08-29

本文件保存执行包初始化后由 Codex 发出的三个同会话定向纠偏。对应 runner stdout 与结果分别保留在
`logs/execution/mm_r7_slice07c3_result_publication_implementation_20260829/` 和
`runs/execution/mm_r7_slice07c3_result_publication_implementation_20260829/`。

## Worker 03 follow-up 1

- 把 runtime metadata 读取移到 publication reserve 之后。
- 以实际 typed `R5PublicationAuthorityInput`/bridge 贯通产品发布和 result-entry 重取。
- 从产品入口覆盖 `finalize.after_publication_update` 与 `finalize.after_launch_update`，证明无单边提交。

## Worker 02 follow-up 1

- 新增 registry `bind_publication_runtime_manifest(...)`：publishing 状态下以 CAS 在 reserve 后绑定
  runtime revision/identity/digest；精确重放幂等，冲突、陈旧状态、部分字段与 setup/runtime 不一致失败关闭。

## Worker 03 follow-up 2

- 删除被 Codex 拒绝的 reserve 前 binding/precomputation 折中。
- reserve 时 runtime 字段保持未绑定；reserve/retry 后才打开 runtime、读 progress/manifest 并调用新 CAS API。
- 增加顺序探针，证明 `reserve → entry → progress → binding`；保留实际 R5 与两处 finalize 故障证明。
