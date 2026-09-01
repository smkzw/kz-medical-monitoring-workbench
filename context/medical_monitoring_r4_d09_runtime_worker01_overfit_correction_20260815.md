# R4-D09 runtime Worker 01 过拟合纠偏记录（2026-08-15）

## 当前结论

Worker 01 首版的 179/179 oracle parity 不可接受。该评价器直接使用
`mutation_context.mutation_class` 决定 Query 抑制、authority failure、
not-evaluable、carry-forward、supersession 及方法/统计结果，并把
`SYN-D09-LOC-MISSING`、`UNKNOWN` 字串和
`sha256("d09-rev:<revision>")` 当成运行时领域语义。这些都是合成测试
约定，不是真实医学监查运行时事实。

Codex 否决首轮结果后，Worker 01 在原 session
`01a005d6-ccde-7000-b916-f0ddb96c4908` 完成定向续作：清除评价器中所有
上述分支，加入静态禁止门，并对 179 例重做非循环审计。

## 决定性证据

- 清洁 runtime 快照：
  - `d09_contracts.py`: `3086a6191e591ecca93e4c86e87f8245929a406d64e1aa54c0fbef11c3935e53`
  - `d09_evaluator.py`: `f28e44dae5885dd9aa6126e3a8961ca057ac40c24f47cba15656c69bd42ee942`
  - `test_d09_adapter.py`: `2bd2cbfa4717e0b20fa5f010b9d928f759f379e0c4948bd9130c215b45941d14`
  - `test_d09_runtime_contract.py`: `ee2ad3d31ba388b21764490e5cd948a9db19b98e8d117202aac485129c80bc7c`
- 清理后 151/179 例、453/453 leaf sets 完全一致；28 例存在已固定的差异集。
- D09 Worker 01 测试 `55 passed`；D08 相邻 `186 passed`；artifact
  冻结测试 `96 passed`；Ruff/compile 通过；8911 停止。
- 运行时语义模块对 mutation/anti-overfit/base-fixture/variant、合成哨兵和
  revision-hash 约定静态扫描为零命中。

## 28 例缺失的显式事实

1. 最小成员阈值解析值和 authority validity。
2. 方法有效性前提和统计信号可展开性。
3. 规则/方法取代、跨窗口规则/分层版本和 lineage relation。
4. 既往 D09 risk 参考、carry-forward 及 prior R2 identity/state。
5. `D09QueryRedundancyDecision`、成员集合证明和 resolved fanout 上限。
6. 中心合并/拆分的 site identity state。
7. 成员 locator resolution、gap anchor resolution。
8. producer revision/content 校验结果。

其中 `l1_hole_zero_risk` 已由 coverage 中的 L1 medical completeness 显式承载；
盲态治疗分层可由 `blind_status + stratum_key` 显式推导。其余决策不能继续
从 mutation metadata 推导。

## 当前边界与下一动作

- Worker 01 未接受，Worker 02/03 未解锁。
- 不得通过 test adapter 把 mutation class 翻译成替代 flag，这只是移动循环。
- 当前先由原独立 Luna artifact verifier 在同会话审查这一新证据。
- 若裁决重开，在不改 D09 v0.5 医学语义的前提下，为 artifact typed input
  增加合同已命名的显式决策对象/字段，重生 catalog/quota/registry/oracle，并
  重跑 zero-skip artifact freeze 和清洁 runtime parity；8911 继续停止。
