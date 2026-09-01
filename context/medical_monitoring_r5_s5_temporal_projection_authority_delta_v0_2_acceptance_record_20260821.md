# R5-S5 统一时间投影权威增补 v0.2 接受记录

- 日期：2026-08-21
- 接受标记：`ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_2`
- 决策者：fresh isolated Codex reviewer；父 Codex 完成机械门禁复核后封存
- 唯一接受对象：`artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json`
- manifest raw SHA-256：`466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8`

## 接受范围

仅接受 append-only、`synthetic_test_only`、non-clinical 的 full-parent-graph 时间投影权威增补。v0.2 仅在固定 manifest、`execution_profile=full_parent_graph` 且目标合同为 `subject-temporal-public-v1` 或 `aemh-match-history-public-v1` 时，取代 v0.1 的 synthetic executor composition；v0.1 既有字节和历史接受记录保持不变。

本接受为后续 public-authority implementation-contract v0.4 生成冻结以下边界：

- Subject 17 类与 AE/MH 13 类父对象按 typed authority input 构造完整父合同有效图；
- 八个医学域、时间端点、study-day、截止日、访视、事件、阶段、风险、待补日期、成员关系、来源定位与可见性闭环；
- AE/MH previous-prefix、identity evidence、追加链与保留历史闭环；
- 16 个 superseding recipe 的 closed `node.op → handler` 分阶段执行与最终 packet 等价；
- 236 条真实变换、236 条执行 trace、零别名，以及 10 条完整正向 post-graph。

## 决定性证据

- baseline full graphs `2/2`，父 validator errors `0/0`；positive full post-graphs `10/10`，errors `0`，post hashes `10/10` 唯一。
- 236/236 trace 均实际执行，identity 236 个唯一、aliases=0；10 条 accept 的 path、前后值、linked operations 与真实 authority transform 完整一致。
- Subject 15/15 与 AE/MH 13/13 父错误复活探针全部命中。
- 16/16 recipe 分阶段输出和 2/2 最终 packet 等价；32/32 closed op handlers 真实 dispatch。合法 op 交换、phase/op 错配、输入输出 schema 漂移、循环和跨目标依赖均 fail-closed。
- exact-key/type/cardinality/closed-enum、contract/schema/profile/target/source variant、v0.1 supersession pin、15 项 typed-source pins 与 external pins 的完全重封攻击均 fail-closed。
- normal、`-O`、`-OO` × `PYTHONHASHSEED=0/1/777` 的 generator `--check` 与独立 verifier 全通过；两次 bundle SHA 一致；exact no-cache Ruff 通过。
- 5-file artifact exact set、542 文件医学写作保护聚合、producer/S5/bytecode absence 与 8911 stopped 通过。
- fresh isolated reviewer 对冻结 SHA 返回精确接受标记。

## 未接受

本标记只解锁 public-authority implementation-contract v0.4 的生成与审阅，不接受或解锁：

- implementation-contract v0.4 本身；
- subject-temporal / AE-MH producer、tests 或 evidence；
- R5-S5 runtime、UI、浏览器；
- 真实项目、真实模型、临床真值或临床权威规则包；
- 产品、生产、安全专项或医学写作子系统任何状态；
- 端口 8911。

任何 v0.2 manifest 字节变化均使本接受失效，必须重新进行 fresh isolated review。
