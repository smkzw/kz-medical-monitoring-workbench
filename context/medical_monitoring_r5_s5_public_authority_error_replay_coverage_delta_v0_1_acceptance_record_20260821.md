# R5-S5 Public Authority Error Replay Coverage Delta v0.1 接受记录

- 日期：2026-08-21
- 接受标记：`ACCEPT_R5_S5_PUBLIC_AUTHORITY_ERROR_REPLAY_COVERAGE_DELTA_V0_1`
- 决策者：fresh isolated Codex reviewer；父 Codex 完成机械复核后封存
- 唯一接受对象：`artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json`
- manifest raw SHA-256：`0dbc0763b9c282c5e2363707a1f6ea99ae8e730e00acb716dcfc61bf9cd3186b`

## 接受范围

仅接受 append-only、`synthetic_test_only`、non-clinical 的错误回放覆盖增补。该增补不新增、重命名、重排或改写任何 public error code、priority、父合同、语义规则、时间投影规则或临床真值，仅为既有 accepted challenge 未实际触发的 22 个既有错误码提供可执行 replay gate。

本接受冻结：

- accepted challenge 实际 pre-delta union 为 170/192；
- 22 条增补 challenge 各自由真实 parser、typed validator、constructor comparison 或隔离 artifact-governance entrypoint 触发；
- 22 条 trace identity 唯一、aliases=0，且与 pre-delta 170 无交集；
- post-union 精确为 192/192。

## 决定性证据

- Accepted entrypoints 实际执行：parent 194 cases / 70 codes；semantic 66 / 38；temporal v0.1 418 / 62；temporal v0.2 236 / 65。
- 22/22 replay 均得到完整有序实际 issue；12 个 gate 全部真实调用；runtime-surface gate 在隔离临时目录执行实际文件动作。
- identity replay 从 accepted Subject invariant 构造并检查 receipt、projection、visibility、every member 的 project/run/snapshot/site/spine 五维一致性。
- AE/MH history replay 从 accepted invariant 12 构造 withdrawn/reappeared byte-identical ordered-subsequence 检查，不混入 invariant 13。
- 94 个主动一致性检查进入真实 gate；expected poisoning、gate substitution、reseal、duplicate/negative/protected pin 和 coordinated fully-resealed drift 均 fail-closed。
- accepted parent/semantic/temporal 根 manifest 与 acceptance record 使用 immutable external raw pins；四个 protected scalar 同时绑定 hard expected、实际文件、temporal nested 与 delta duplicate。
- normal、`-O`、`-OO` × `PYTHONHASHSEED=0/1/777` 全通过；双生成 byte-identical；exact offline Ruff 通过。
- 542 文件医学写作聚合、blocked v0.4 九 SHA、producer/S5/bytecode absence 与 8911 stopped 通过。
- fresh isolated reviewer 对冻结 SHA 返回精确接受标记。

## 未接受

该标记只解锁新的 append-only public-authority implementation-contract v0.4 修订快照生成，并允许其消费这 22 条 executable replay。它不接受旧 blocked v0.4，也不接受或解锁 producer、runtime、tests、evidence、S5、UI、浏览器、真实项目/模型、临床权威、产品/生产、医学写作或 8911。

任何 delta manifest 字节变化均使本接受失效，必须重新进行 fresh isolated review。
