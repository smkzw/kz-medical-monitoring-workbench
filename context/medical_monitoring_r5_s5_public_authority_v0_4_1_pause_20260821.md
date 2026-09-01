# 医学监查 R5-S5 Public Authority v0.4.1 无损暂停记录

日期：2026-08-21（Asia/Shanghai）

状态：`PAUSED_BLOCKED_AT_V0_4_1_CONTRACT_REVIEW`

## 1. 当前目标与边界

当前细分任务是冻结 R5-S5 public-authority implementation contract v0.4.1，并在独立审阅接受后才解锁精确 11 个 producer/runtime/test/evidence 新文件。当前未达到接受条件，因此不得进入 producer、S5 runtime、UI、浏览器或真实项目/模型测试。

持续边界：

- 医学写作子系统及其 542 项聚合保护面不得改动。
- 8911 必须保持停止。
- 不运行真实项目、真实模型、浏览器或产品服务。
- v0.4.1 候选不得被描述为已接受；不存在 acceptance record。
- 已接受的 parent、semantic、temporal 和 error-replay 历史保持不可变。

## 2. 已完成并冻结的上游

- Parent manifest：`92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270`
- Semantic v0.1 manifest：`66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d`
- Temporal v0.1 manifest：`e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97`
- Temporal v0.2：`ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_2`
  - manifest：`466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8`
  - acceptance record SHA：`d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4`
- Error replay coverage delta：`ACCEPT_R5_S5_PUBLIC_AUTHORITY_ERROR_REPLAY_COVERAGE_DELTA_V0_1`
  - manifest：`0dbc0763b9c282c5e2363707a1f6ea99ae8e730e00acb716dcfc61bf9cd3186b`
  - acceptance record SHA：`814f3e7b36aade049e9a5267a3b247ec23089a0ec0696f9d07b82133ca6b42e9`
  - 仅证明 170 + 22 = 192 个既有错误码 replay coverage，不增加错误码或临床权威。

被拒绝的 v0.4 manifest `c363811be037a107a369523c47f43a7e589ddc9f8e608ca87309e1f15b6f7a94` 仅作为负面历史证据，不得修改或复用为接受依据。

## 3. 当前 v0.4.1 候选快照

该快照机械门禁曾报告 272/272 joins、236/236 traces、10/10 positives、226/226 rejects、58 active attacks、22 governance，且 8911 stopped；但 fresh reviewer 的实质攻击证明这些数字存在 fail-open，不能作为接受证据。

- context：`d9eb6f1050c3555dee1eafe04d5c7f85934e6089e2febd28ee546b3a9a9ac393`
- review：`a7b045df894c5d53d4ba173242926285dfef660f7d3cf8a4405740a8b0742b81`
- public_api：`926ac1338c72f4b9c381f1c4690fc14412ad97027109dc91da45245ba4ab4999`
- source_join_matrix：`32df331bb5f48b174194384f9297ece2df9d26c80367507ac66657d0a2f7ee36`
- invariant_error_matrix：`f7545cc977ab2143b545a2ce28bdedaf24cf351789865d44c443816d2eacbf50`
- test_matrix：`a244f5dd877cf19393614f407d1c333f5b4c1ec8736c796058091591f1ccaba3`
- manifest：`1033daaa81eb4c0eede2445b5a8228e37d54d6621feb8b35ebb179a20d55c5bd`
- generator：`405cd6e2d37f901fc3595cb66aef893fb2d57c95e8def4aceecf5e1714a08792`
- verifier：`9f44814784614cf400ec2a05ff1418c3cfb7fb70a03ac2e766d442297671dc15`

Fresh reviewer verdict：`REVISE_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_4_1`。

## 4. 决定性阻断

Fresh reviewer 复现了四项 fail-open：

1. 272 joins 未实例化并读取真实 typed source；验证器从 v0.2 bundle 复制值作为伪 typed plane。污染 recipe sealed cutoff 后，join 仍可返回无问题。
2. 192 error rows 未真实执行 170+22 replay；全部替换为 fake gate/base/mutation/reseal 后仍可通过。
3. 58 active_gate_specs 未逐条执行；全部替换为 fake specs 后仍返回 58。
4. 226 reject 的 path/message/origin/priority 来自候选 error matrix 回填；协调篡改 error matrix 与 spec 后仍可通过。

同一作者 session 的定向修复随后触发 P0/P1 STOP，且本次未改九文件：

- 当前 typed/v0.2 selector raw authority 与 ConstructionGraph target leaf 有 264/272 不等。
- 例：`PublicAuthorityReceipt.audience_contract_id` target 为 `contract.s4.1`，当前 typed selector 却是 `MonitoringRun.run_id=run::synthetic-contract-example`。
- 例：cutoff `exact_date` target 为 `2026-08-19`，当前 selector 却落到 `MonitoringRun.project_id`。
- 缺口分布：subject receipt 12、identity/cutoff 12、locators/revisions 29、packet 3、projection 16、axis 8、temporal members 50、domains/pending/membership 20；AEMH current membership/prefix/cutoff 14、threads 32、identity/locators/revisions 26、packet 3、projection 14、receipt 25。
- 现有五个绑定类 `MonitoringRun`、`SourceRevision`、`ListingSnapshot`、`TemporalEvent`、`AEMHResult` 均不是 frozen dataclass；accepted v0.2 bundle 也未提供完整 constructor authority 或将真实 typed object graph 转换为 272 target leaves 的 reducer handler。
- 强行补 constructor 参数、包装 frozen 类型或逐叶复制目标值会创造新的权威/自证 oracle，因此必须停止。

## 5. 当前真实文件系统状态

- v0.4.1 九文件保持上述 SHA；作者 STOP pass 未修改它们。
- 11 个 producer create-only 路径全部不存在：
  - `src/mm_r5/public_authority_contracts.py`
  - `src/mm_r5/public_authority_source_joins.py`
  - `src/mm_r5/public_authority_builder.py`
  - `src/mm_r5/public_authority_validator.py`
  - `tests/public_authority_fixture_support.py`
  - `tests/test_public_authority_contracts.py`
  - `tests/test_public_authority_source_joins.py`
  - `tests/test_public_authority_builder.py`
  - `tests/test_public_authority_validator.py`
  - `tests/test_public_authority_readonly_gate.py`
  - `evidence/medical_monitoring_r5_s5_public_authority_implementation_evidence.json`
- 8911 检查：`connect_ex=61`，无监听。
- 本次暂停收口未启动服务、浏览器、真实项目、模型或测试长任务。
- 未发现可安全删除且属于本细分任务的缓存；未执行清理，以免误删并行工作或审阅证据。

## 6. 下一次恢复的唯一安全动作

恢复后不要直接修改 v0.4.1 九文件，也不要创建 producer。先设计并冻结一个上游 authority-contract delta，明确解决以下问题：

1. 哪些真实 frozen typed records 对 272 个目标叶提供独立权威；
2. 每个真实 constructor 的完整字段来源、身份和 content hash recipe；
3. typed source → v0.2 recipe output → ConstructionGraph target 的逐叶 reducer/selector/cardinality 合同；
4. 无法由现有 accepted authority 构造的叶应明确 deferred，而不是镜像目标值；
5. delta 必须经 fresh isolated reviewer 接受后，才回到同一 v0.4.1 作者 session 关闭四项 fail-open，并重新做 full matrix 与 fresh review。

只有 fresh reviewer 返回精确 `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_4_1` 并写入独立 acceptance record 后，才可解锁 11 个 producer 路径。恢复期间 8911 继续保持停止。

## 7. 暂停结论

当前细分任务已完成到可审计的真实阻断点，未以机械绿灯替代语义接受。状态不是完成，也不是接受；是可无损恢复的受控暂停。
