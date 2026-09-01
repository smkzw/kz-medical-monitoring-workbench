# R4-D09 artifact / oracle 无损暂停点（2026-08-14）

## 当前结论

D09 v0.5 合同仍冻结，合同 SHA-256 为 `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`。Worker 01 已生成 179-case synthetic/offline typed catalog、29 个互斥主分区的 quota manifest、provisional registry 和确定性生成器；Worker 02 已生成独立 oracle、oracle 生成器，并把 registry 的 179 行 oracle 链接更新为 resolved。Codex 已完成当前步骤的聚焦静态验收。

**本暂停点不代表 D09 artifact freeze 已接受。** Worker 03 的 registry/bijection/import-closure/mutation/replay/quota 冻结测试尚未开始，独立 Luna freeze review 尚未开始，D09 runtime/UI/真实项目/模型均未解锁。

## 必须保持的边界

- TCP 8911 必须保持停止；暂停前 `lsof -nP -iTCP:8911 -sTCP:LISTEN` 无输出。
- 不读取或运行五个真实项目，不使用患者数据，不调用真实模型端点。
- 不修改医学写作子系统，不修改 `src/`、前端、R4 runtime 或产品服务。
- 当前仅为 synthetic/offline artifact 工作。
- 不删除 v0.3/v0.4 REVISE、v0.5 ACCEPT、Worker 01 截断及同会话恢复证据。

## 已完成

### 1. Worker 01：目录、配额、provisional registry

- 初始 session：`01a00068-90a4-7000-a2de-5c75fdf7fa90`
- 路由：Pi / `cms-smk` / `deepseek-v4-flash` / max；无 fallback。
- 初始轮次因模型输出长度截断，只留下进度句且未生成文件。
- 使用同一 session 的 follow-up1 恢复，未新开 session；第二轮完成文件生成。
- runner 报告：
  - `runs/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_01.md`（历史截断 stub）
  - `runs/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_01_followup1.md`（完整报告）
- 产物：
  - `tools/generate_d09_challenge_registry.py`
  - `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
  - `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`
  - `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
- Worker 01 阶段本地检查：179 cases、29 primary partitions、目录三套 `expected_*` 全为 JSON null、五个标识列唯一、quota 最小值合计 179、pairwise-disjoint 与 catalog-set equality 为 true。

### 2. Worker 02：独立 oracle 与 resolved registry

- session：`01a00092-33d8-7000-954e-ff9d1e7e684d`
- 路由：Pi / `cms-smk` / `deepseek-v4-flash` / max；无 fallback。健康预检失败被按全局规则记录为 advisory，真实 route 仍成功完成。
- runner 报告：`runs/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_02.md`
- 新增/更新：
  - `tools/generate_d09_expected_oracle.py`
  - `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
  - `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`（仅 oracle resolution/link/hash 更新）
- `python3 tools/generate_d09_expected_oracle.py check`：通过双遍字节一致、磁盘匹配、schema/bijection/canonical/hash 验证。
- Codex 聚焦静态验收：catalog/quota SHA 未变；catalog/registry/oracle 均为 179 行；五列全唯一；179 case 集合一致；registry 全部 `oracle_resolution=resolved`；catalog 三套 expected 字段仍全 null；oracle 三套 expected leaves 全非空；oracle generator AST 仅导入标准库，源码无 `open()`、`.read_text()`、`CATALOG`、`REGISTRY`、`QUOTA`，仅两处 `.read_bytes()` 用于冻结合同读取/哈希。

## 当前文件 SHA-256

- D09 v0.5 contract：`9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- catalog generator：`0f73e2fac2da7f211b5af8c7e4eadfe4283604921c762c9553ec84a8145a9308`
- oracle generator：`e0a33453cdd57aaf10085ed65e42478a6b90917ebd0aa7492c9188b38909c7c1`
- typed catalog：`b5e471e58abcb7a0ce09327d9cad42bb5313cd89ebcb2fb7d3cf2a7f39a201ad`
- partition quota manifest：`24250b745d13ad624b07ff86887c03b6ed69d7f372ec189ec8d6dc33103f3ec5`
- resolved registry：`7fcd73c0f70a811e848908d8eba47ba21c0bc996831ad5eb10139069dc3e866c`
- expected outcome oracle：`f54b45cf39188ec2628030040a53e56d88e2727aaac58701cd314dd7be6020de`

## 已知未闭合项（不得误报为完成）

1. `python3 tools/generate_d09_challenge_registry.py --check` 当前退出 1：catalog 和 quota 仍与 fresh generation 匹配，但 resolved registry 与 Worker 01 仍生成的 unresolved registry 不同。这是 staged generator/registry integration mismatch；Worker 03 必须通过最小修正或明确的两阶段 check 合同解决，不能忽略。
2. Worker 02 的 oracle 运行时文件读取闭包已静态证明，但其“作者层面的独立性”仍需 Worker 03 mutation/import-closure 测试和新鲜 Luna verifier 挑战。尤其要审计 embedded semantic tags 是否把 expected outcome 伪装成输入事实。
3. 尚无 `tests/test_d09_artifact_generator.py`，因此 179-case artifact 还没有非 LLM 冻结测试。
4. 尚未形成不可变 artifact snapshot SHA 清单并提交独立 Luna freeze review。
5. D09 runtime、R2 handoff、UI、真实项目和模型均未开始；不得据此宣称 D09 或 R4 完成。

## 下一次恢复的唯一安全顺序

1. 全量读取最新全局与 workbench `AGENTS.md`，本暂停记录、D09 v0.5 合同、execution context/plan、Worker 01/01-followup1/02 报告。
2. 重新核对上述 7 个 SHA、8911 停止、catalog/quota 字节未漂移；不得重新运行真实项目或服务。
3. 预检并串行启动 **Worker 03**：只实现 `tests/test_d09_artifact_generator.py`，并在测试证明必要时对六个 D09 artifact/generator 文件做有界修正。首先解决 unresolved/resolved registry 的 staged check mismatch。
4. Codex 本地运行聚焦 D09 test、双生成、canonical/hash、mutation/order/display-name/replay/import-closure/bijection/quota 检查。
5. 对稳定不可变快照启动新鲜 Codex Luna/max 独立 freeze review；只有 `ACCEPT_D09_ARTIFACTS` 才能把 artifact freeze 标为完成并解锁 D09 runtime。
6. 本暂停点恢复时不要补发 Worker 02；其 session 已成功终结。只有 Worker 03 或 verifier 发现具体 oracle 缺口时，才按同 session 继续规则决定是否恢复 `01a00092-33d8-7000-954e-ff9d1e7e684d`。

## 暂停状态

`PAUSED_R4_D09_ARTIFACT_WORKER02_LOCALLY_CHECKED_WORKER03_NEXT`

