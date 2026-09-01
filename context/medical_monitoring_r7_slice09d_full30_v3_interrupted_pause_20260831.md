# 医学监查 R7 Slice-09D 全量矩阵 v3 无损暂停检查点

状态：`PAUSED_LOSSLESS_R7_SLICE_09D_FULL30_V3_INTERRUPTED`

日期：2026-08-31（Asia/Shanghai）

## 1. 当前目标与边界

- 目标：在已接受的 09A–09C 产品 seams 上完成 09D §3/§4 的 30-cell、3-seed × 10-repeat 容量/性能量测，并经独立会商后判断边界。
- 当前只使用 synthetic/offline corpus；未运行任何真实研究项目、真实 listing、IB、模型、浏览器或 UI。
- 未触碰医学写作子系统。
- 8911、5174、8984 必须保持停止。
- 不得把量测 runner/oracle 缺陷解释为产品容量失败。
- §5 恢复/故障检查点仍保持已接受；§3/§4、09D、R7、R8 均未关闭。

## 2. 本轮修复的两个 runner 根因

### 2.1 calibration/screening 工作区碰撞

原实现把非平衡规格的 `calibration/0` 与 `screening/0` 都写入 `trial_000`，导致 screening 复用 calibration 状态，`first_restore` 返回 replay，随后形成假红和下游级联。

修订：

- `_trial_workspace_name(trial_kind, trial_index, trial_seed)` 使用 phase + index + seed 的确定性唯一目录；
- raw record 增加 `workspace_name`；
- 未执行的下游负载保持 fail-closed，但明确标记 `failure_class=dependency_not_measured`、`blocked_by_workload`、`accepted_seam_invoked=false`。

执行报告：`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_04.md`

### 2.2 confirmation seed 与 fixture 不一致

原实现只按初始 seed 生成 fixture；confirmation trial 10 起切换 seed 后，子进程用新 seed oracle 校验旧 fixture，导致 `identity=false`。

修订：

- fixture cache 改为 `(profile_id, seed)`；
- 路径为 `fixtures/<profile>/seed_<seed>.jsonl`；
- 同 seed 的 10 次重复复用同一 fixture，不同 seed 使用与 oracle 一致的确定性 fixture；
- confirmation 的 3-seed × 10-repeat 分配与容量阈值未改变。

执行报告：`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_05.md`

## 3. 已完成验证

- 工作区碰撞聚焦回归：3/3 passed。
- 首次修订 artifact suite：51/51 passed。
- 跨 seed 聚焦回归：2/2 passed。
- 最终 artifact suite：53/53 passed。
- C06 calibration + screening smoke：28/28 records green。
- C02 trial 9→10 跨 seed smoke：168/168 records valid/green；边界 28 条 identity 全 true。
- 当前 source-copy identity：`2b771fb1f3705241bda2ecbb35607a1f736c056eaa424cccd6f881c479be3ccd`；70/70 entries；双重 re-hash verified；无 missing/mismatch/error。
- 最后检查：8911、5174、8984 均 stopped；无量测进程残留。

## 4. 三次 full-run 证据状态

1. `measurement_full_30cell_accepted_09a_09c_20260831/`
   - 失效：calibration/screening workspace collision；目录内有独立失效说明；不得用于容量判断。
2. `measurement_full_30cell_accepted_09a_09c_20260831_v2/`
   - 失效：confirmation seed/fixture mismatch；目录内有独立失效说明；不得用于容量判断。
3. `measurement_full_30cell_accepted_09a_09c_20260831_v3/`
   - 用户要求暂停时中断于 `run_determinism_matrix()`；父进程 exit 130。
   - raw 主体已完整写入：2450 records、15 profiles、30 cells、7 workloads、3 seeds。
   - 2450/2450 `observed_green`；全部 `correctness.ok=true`、`identity=true`、`accepted_seam_invoked=true`。
   - trial kinds：calibration 140、screening 1470、confirmation 840。
   - raw SHA-256：`6986af8a404e698a4f50f09f8b9313a9d8ce50228246de3febafda29689573e6`。
   - 因 determinism/environment/stat summary/measurement manifest/source-copy post-validation 未完成，v3 仍是 interrupted evidence，不能接受。

## 5. 当前关键文件 SHA-256

- `measurement_runner.py`: `72da4acbf96b66510e29b2769319f1138cb21269dacee087e8bb5d21ed5c5410`
- `test_measurement_runner.py`: `f4e00c2bc81b2dedf5bdcd42abf1593b03cdbffda65890a89bcca08412c0a179`
- `source_copy_identity_v0_1.json`: `8719fb9c6f9cafb741f30413f6b88d5d78c1dfcb9568051c53e1ce66f0e51815`
- `consolidated_total_manifest_v0_2.json`: `f740d765ae1b70d9455ac42dd07b0075921bdaa66591b9bf7864ea0056e884cb`
- worker 02 followup 04：`e6e0ac5acfd3fdbbf1eafdd74c1c7b7f2f323cfa2d7cae616ec5e7781b288cc8`
- worker 02 followup 05：`c55cafe57b2d89879c5ff948118efed195fa0eef833e50885c9246cdeeb146d6`

## 6. 下一次恢复的唯一安全动作

1. 完整读取最新全局/工作台 `AGENTS.md`、本检查点、09D contract/checkpoint、worker 02 followup 04–05。
2. 确认无量测进程，8911/5174/8984 stopped。
3. 独立复核 `source_copy_identity_v0_1.json` 仍为 verified、70/70、无 drift。
4. 不向 v3 续写；从头运行到新目录：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py \
  --backend accepted_09a_09c_seams \
  --output artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4 \
  --source-copy-identity artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity_v0_1.json \
  --full-contract-run \
  --profiles C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15 \
  --screening-trials 7 \
  --confirmation-trials 30
```

5. 完成后必须核对：2450 raw records、30 cells、15 profiles、7 workloads、3 seeds、determinism 15/15、source-copy pre/post unchanged、summary/manifest schema、无 dependency-not-measured/child-output-incomplete、无红记录。
6. 再启动独立会商复核真实 full-run 边界；会商接受前不得关闭 §3/§4 或 09D。
7. 只有 09D 完整接受后，才复盘并进入下一 R7 slice/Phase；真实项目与独立 harness/LLM 的过拟合验证仍留在 R8 source admission 之后。

## 7. 明确未完成

- v4 完整 full-run：未执行。
- v4 determinism/environment/summary/manifest/post-validation：未形成。
- 独立 full-run 会商：未执行。
- §3/§4、09D、R7、R8：未接受。
- 真实项目、真实模型、ego(lite)、用户视觉 E2E：均未运行。

