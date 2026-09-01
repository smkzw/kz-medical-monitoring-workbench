# R5-S5 语义权威增补接受记录

- 日期：2026-08-20
- 接受标记：`ACCEPT_R5_S5_PUBLIC_AUTHORITY_SEMANTIC_DELTA_V0_1`
- 决策者：fresh isolated Codex reviewer v2；父 Codex 复核机械门禁后封存。
- 唯一接受对象：`artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json`
- manifest raw SHA-256：`66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d`

## 接受范围

仅接受 append-only、`synthetic_test_only`、`non_clinical=true` 的语义权威增补合同，用于为后续实现合同冻结以下机制：

- 事件 16 个 subtype 到 8 个 domain 的闭集关系；
- 原始语义 token 的 typed-source 证据绑定；
- 事件分类规则包、风险 taxonomy、严重度策略与 zh-CN 呈现词典的分权；
- 外部固定 acceptance registry，禁止候选 receipt 自授权；
- S4 仅允许 project/run/snapshot/cutoff/site/subject/risk/spine 八项身份连接，不转移 domain/severity 值权威。

## 决定性证据

- 66/66 个显式挑战为不同且非 no-op；完全重封的规则包自授权、伪造风险中文名、非法严重度、额外字段、缺失 legacy 规则、fuzzy 匹配、跨 owner 证据与 accepted-record 错配均 fail-closed。
- normal/O2 与两组 `PYTHONHASHSEED` 通过，嵌套 optimization matrix 级别实测一致。
- exact no-cache Ruff 通过。
- 15 项 accepted parent pins、9 项 rejected-snapshot negative pins、542 文件医学写作保护聚合、producer absence 与 8911 stopped 均通过。
- 审阅首尾 manifest raw SHA 稳定。

## 未接受的内容

本标记不接受：

- 已被拒绝的 public-authority implementation contract v0.1；
- subject-temporal 或 AE/MH producer；
- R5-S5 runtime、UI、浏览器行为；
- 真实项目、真实模型、临床规则包或临床权威；
- 产品、生产或医学写作子系统任何状态。

任何 manifest 字节变化均使本接受失效，必须重新进行 fresh isolated review。
