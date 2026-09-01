# R4-D09 artifact freeze 验收记录（2026-08-15）

## 结论

`ACCEPT_D09_ARTIFACTS`

D09 v0.5 合同下的 179-case synthetic/offline catalog、partition quota
manifest、resolved registry、independent oracle、双生成器和非 LLM
冻结测试已完成。独立 Luna/max verifier 在全新上下文首轮发现
CASE-047 D08 跨域成员风险类型未进入 definition 白名单，给出
`REVISE_D09_ARTIFACTS`；修复并把该不变量放入生成器真实校验路径后，
同一 verifier session 对新的不可变快照返回
`ACCEPT_D09_ARTIFACTS`。

## 最终冻结 SHA-256

- contract: `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- typed catalog: `4c0ad3b8e5e63d2f9e03162d6f36fe19be024cb2ab1df87f8f279f36db1ee239`
- quota manifest: `e6fd75b512222fe0ee79845c0b1bb5248ef7f91b8197a3b1d99d3fee88bc7785`
- resolved registry: `23ae043f607aeb4de936fdf49f6afa4988055cee5083743484447f337948f9e6`
- expected oracle: `b5c937739493613d00abd92cbef24fddfd1c88ff230cb7150bde784bbcee53e4`
- catalog/registry generator: `b5be914d1c0dd7740c586fcd04567c004f786c201ec2cfd2147568d70f11baeb`
- oracle generator: `ff6096de5b054e877f4076543bcab20a084136f8ed428221e03336099d6a8407`
- artifact tests: `bdaf3d2e0842842003e28658a9b0776a02a9cc1156168fb5cca0ff0cbee1ad8a`
- frozen generator pin: `ff0be3b8a82c4d2d9cc63f3f23c45c9cd7796d842bfe04fccedd854eed58b267`

## 决定性证据

- `tests/test_d09_artifact_generator.py`: `96 passed`。
- D08 相邻冻结测试: `54 passed`。
- `generate_d09_challenge_registry.py --check`: 双遍生成字节一致，catalog/quota
  与磁盘一致，resolved registry stage-B 校验通过。
- `generate_d09_expected_oracle.py check`: 双遍生成与磁盘一致，oracle
  content hash 为 `45ff4deb7a149be29162919f33da9d804624d72fe884bdc8c3822c33a91fbc07`。
- 179/179 处置与决定性计数均由合同允许的 typed input 独立重建；
  无隐藏 oracle 语义标签、跳过表、case-ID 分支、自由文本或 catalog
  disposition 泄漏。
- CASE-047 四条成员形成两组 D01/D08 verified same-origin pair，独立计数
  为 2/2/2；179 例 risk-kind 白名单违规数为 0。
- 对 D08 成员风险类型做未列明突变并一致重签 fixture/catalog hash 后，
  真实 `validate_catalog()` 仍以 `schema_error` 拒绝。
- canonical JSON、NFC、有限数值、文件/内容哈希、顺序/显示名不变性、
  mutation gates、stage-A/stage-B delta 与 reseal/tamper fail-closed 全部通过。
- 验收首尾八个 SHA 完全一致；TCP 8911 始终停止。

## 会话与证据

- Worker 03: `01a0057b-4688-7000-b14b-92c369fe67e8`（原会话两次定向续作，无 fallback）。
- 独立 verifier: Codex native `gpt-5.6-luna` / max，任务
  `/root/d09_artifact_freeze_review`（同会话 `REVISE` 后复验 `ACCEPT`）。
- 首轮验收: `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_20260815.md`。
- 最终验收:
  `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup1_20260815.md`。

## 边界与下一动作

本验收仅覆盖 D09 synthetic/offline artifact freeze，不等于 D09 runtime、D10、
R4 总体、R5 UI、真实项目/模型、产品、生产或医学写作接受。下一安全动作
仅为依据冻结 D09 v0.5 合同与已接受 artifact 设计 synthetic/offline D09 runtime
实施合同、工作项与验收门；继续保持 8911 停止，不运行五个真实项目，不触碰
R5 UI、产品服务或医学写作。

## 后续纠偏（2026-08-15）

运行时 Worker 01 在实施阶段复现出新证据：若评价器不读取
`mutation_context.mutation_class`、合成 locator/anchor 哨兵值和合成 revision
hash 约定，当前 catalog 只有 151/179 例可完整重建，28 例缺失合同已命名
但 artifact 未显式承载的领域决策事实。因此本文的 ACCEPT 仅作为当时快照和
验收轨迹保留，不再作为 D09 runtime 解锁证据。详见
`context/medical_monitoring_r4_d09_runtime_worker01_overfit_correction_20260815.md`；
必须等原独立 verifier 对该新证据给出裁决，并在必要时完成 artifact
schema 纠偏与重新冻结，才可继续 Worker 02。

## Fact completeness 纠偏（2026-08-16）

原 Luna verifier 在 follow-up3 对达到 179/179 clean parity 的候选返回
`REVISE_D09_CORRECTED_FREEZE`：默认 fanout、未版本化的 `2/4/3` 数值阈值、
未校验的 Query member-set/proof 以及未与顶层 revision/hash 对齐的 source
verification 仍可产生医学输出。因此 2026-08-15 的旧 ACCEPT 继续只保留为
历史轨迹。

Codex 已按最小修复清单完成显式 ModeContract 数值 authority、完整 Center
Query policy、Query proof/source alignment fail-closed，并重新生成冻结链。
当前新候选达到 D09 artifact 99 passed、D09 runtime/adapter 71 passed + 3
subtests、179/179 cases 与 537/537 leaf sets 零差异；D08 adjacency 54 + 186
passed，生成器 determinism/Ruff/compile/8911 停止均通过。权威记录为
`context/medical_monitoring_r4_d09_fact_completeness_correction_20260816.md`。
但该候选仍不是 ACCEPT；Worker02/03 继续锁定，等待原 Luna verifier 对新
不可变 SHA 再次复核。

## Corrected freeze ACCEPT（2026-08-16）

原 Luna verifier 已在同一独立审阅会话对新 SHA 返回
`ACCEPT_D09_CORRECTED_FREEZE`，并重放此前全部负向探针。权威报告为
`runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup4_20260816.md`。
当前 artifact + Worker01 kernel 以
`context/medical_monitoring_r4_d09_fact_completeness_correction_20260816.md`
所列 SHA 为正式冻结候选，现已满足 runtime-ready fact completeness、clean
parity 与 fail-closed；Worker02 可按串行计划解锁。该 ACCEPT 仍不代表
Worker02/03、D10、R5/UI、真实项目/模型、产品、生产或医学写作接受。
