# P10 LOOP 3.16 v9 cutover 持久退役直接证据无损暂停

日期：2026-08-01  
状态：offline PASS；本细分项完成并无损暂停；主 Goal 未完成

## 已完成

- v8→v9 四项直接证据已闭合：terminal audit preservation、same-revision
  queued/RUNNING retirement、late completion CAS fail-closed、distinct v9。
- 三类 supersession 使用独立、可迁移、不可重试的持久退役标记；原 provider
  failure evidence、attempt 和 candidate audit 不被覆盖。
- 旧 schema 三种 `superseded_*` 码在初始化事务中回填，并由 retry 旧码防线
  双重保护。
- exact production business key、service fail-loud、input-only verified
  compatibility、prompt/profile/model contract changes 均有直接测试。

## 最终验证

- Compile：PASS。
- Repository/protocol/API：`83 passed in 3.38s`。
- 四文件共享监查契约：`439 passed in 16.48s`。
- 全监查（仅排除已知无关 collection blocker）：
  `1410 passed, 4291 deselected, 27 warnings in 605.73s`。
- Luna round 4：本切片无 P0-P4，offline durable cutover PASS。
- 8911/5174：无 listener；无本切片 runner/pytest/worker。

## 并行边界与残余风险

- 医学写作相邻抽样 `98 passed, 2 failed`；两项均为并行章节投影仍期待
  `待补充`、当前实现返回空文本。本切片未修改或回退医学写作文件。
- 独立 P2：provider-only stable ID 与 SQLite unique tuple 不一致；不影响当前
  v8→v9 prompt cutover，但 provider-only rotation 前必须单独设计迁移。
- Runtime DB、startup ordering、provider 与 canary 未验证；本记录不是 release、
  RUX/MY009、真实项目或候选决定通过。

## 最终哈希

- `monitoring_ai_contracts.py`:
  `ec63cc67067395cac1a436fbc7e65b9d260c4a0a8046ee46b8f3ed624f8c8196`
- `monitoring_ai_repository.py`:
  `9141cf512e358bedec243d338a6fab3c0195e9ec5f24893a404eefdab0471443`
- `test_monitoring_ai_repository.py`:
  `a9787efb982e275d1812ce954a516506b91862f6be4a47719ab1d319aa365692`
- `test_monitoring_protocol_preparation.py`:
  `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`
- `test_monitoring_ai_api.py`:
  `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`

## 下一安全动作

下一次用户明确继续主 Goal 时：

1. 重读最新全局/项目 AGENTS、本暂停记录、Codex review、Luna round 4 与
   LOOP ledger。
2. 只读核查并行医学写作漂移，仍不得擅自修复或回退。
3. 核对上述哈希、8911/5174 停止、无遗留任务；再只读核对 runtime v4-v9
   计数、旧 active eligibility 与 startup migration/backfill 预期。
4. 将 provider-only identity/unique P2 留在独立 schema 任务，不混入 canary。
5. 只有 runtime preflight 独立通过后，才可讨论一次 fresh v9
   `visit_window_and_order` canary；不得 retry/reuse/salvage v4-v8，不得启动
   其他 topic、MY009/真实项目或作候选决定。

8911 必须保持停止。
