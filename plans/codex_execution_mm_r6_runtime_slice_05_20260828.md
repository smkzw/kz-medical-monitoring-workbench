# Codex Execution Plan: mm_r6_runtime_slice_05_20260828

Objective: 实现并验证 synthetic/offline 锁库前四类专属 ModeOutput 内容，严格复用 slice-04 身份与失败关闭边界，不接产品、真实项目、服务或模型。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 复用 ModeOutput 实现 pre_lock 四输出 payload 构建与验证，覆盖同一 authority/cutoff/revision、数字风险和输入不变。 | `runs/execution/mm_r6_runtime_slice_05_20260828/worker_01.md` |
| `worker_02` | 增加 focused 阴性与确定性测试，覆盖 revision impact、check coverage、Query revision draft-only、tamper 与跨 mode 混用。 | `runs/execution/mm_r6_runtime_slice_05_20260828/worker_02.md` |
| `worker_03` | 独立运行 focused/full/9-grid、邻接/边界验证并生成 slice-05 runtime receipt，不修改产品或医学写作。 | `runs/execution/mm_r6_runtime_slice_05_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Verify every edit is within the slice-05 contract and reuses slice-04 identity/eligibility.
- Run focused, full POC, and 9-grid independently after all workers finish.
- Recheck medical-writing aggregate and 8911/5174 stopped state.
- Require execution audit plus independent acceptance conference; no product/medical claim.
