# 医学监查子系统整体复盘 — 无损暂停检查点

Date: 2026-08-01 20:54 CST  
Updated: 2026-08-01 22:22 CST  
Updated: 2026-08-01 23:08 CST  
Updated: 2026-08-01 23:42 CST  
Updated: 2026-08-01 23:59 CST  
Updated: 2026-08-02 00:05 CST  
Updated: 2026-08-02 00:16 CST  
Updated: 2026-08-02 00:28 CST  
Updated: 2026-08-02 00:38 CST  
Updated: 2026-08-02 00:49 CST  
Updated: 2026-08-02 01:06 CST  
Updated: 2026-08-02 01:19 CST  
Updated: 2026-08-02 01:31 CST  
Updated: 2026-08-02 01:44 CST  
Updated: 2026-08-02 01:54 CST  
Updated: 2026-08-02 01:55 CST  
Updated: 2026-08-02 02:04 CST  
Updated: 2026-08-02 02:12 CST  
Updated: 2026-08-02 02:27 CST  
Updated: 2026-08-02 06:32 CST  
Updated: 2026-08-02 06:37 CST  
Updated: 2026-08-02 06:48 CST  
Updated: 2026-08-02 07:00 CST  
Updated: 2026-08-02 07:25 CST  
Updated: 2026-08-02 07:45 CST  
Updated: 2026-08-02 07:51 CST  
Updated: 2026-08-02 07:55 CST  
State: **Phase A A1-A6 and Phase C1-C14 offline contracts complete; B6 authority review pending; services remain stopped**

## 1. 本轮完成

- 完整复盘说明书、PRD 差距矩阵、P0-P10 LOOP 计划和现有 Goal Prompt。
- 只读审查医学监查后端、前端、数据身份、AI、risk、daily-run、assurance 和测试框架。
- 调研 ICH/FDA/NMPA/CDISC、全球厂商、中国平台、论文和开源实现。
- 形成 P0-P10 需求—实现—证据矩阵、代码问题优先级、九阶段路线图。
- 给出从当前 P10 v11 停止点贯穿商业化发布门的项目总 Goal 文本和下次恢复 Prompt；v12 仅是第一执行切片，不是 Goal 终点。
- 新增简洁重点界面、项目/中心/个例三级图形化钻取，以及 `subject-timeline-builder`、`clinical-patient-profile-html`、`ae-risk-assessment` 能力融合合同。
- 详细报告：
  `reviews/medical_monitoring_system_retro_roadmap_20260801.md`

## 2. 恢复性质

- 原父 Session JSONL 已删除。
- 当前工作是基于现存文件、哈希和运行证据的续作，不是原始逐条对话恢复。
- 当前文件系统是最终真相。

## 3. 当前最新 P10 停止点

- v11 offline corrective 已通过：
  - focused 17；
  - core 528；
  - adjacent 146；
  - full monitoring `1489 passed, 4455 deselected, 27 warnings`；
  - Luna 静态终审 PASS。
- v11 zero-submit clone：
  - 21 SQLite mains；
  - 18 integrity `ok`；
  - 3 个源空文件保持空。
- 单次 v11 canary：
  - job `monai_3632c414655546ad250ce8bf7dbd`
  - attempt `monattempt_564f58bf463c42758a4c394f190be9de`
  - source revision `mpr_40b82826a43e46342344841242e6`
  - 173 evidence spans
  - `failed / invalid_ai_output / retryable=0`
  - 2 provider outputs，0 candidates，0 active jobs
- 精确原因：
  - controlled repair 后 `claims[*].uncertainty` 仍有 `药物回收相关段落`；
  - validator 正确命中 `回收` 并 fail-closed；
  - 这是 repair 反馈不够精确，不是 validator 缺陷。

该 v11 终态仍完整冻结。其后完成的 v12 A1-A6 离线与隔离运行闭环是当前更新停止点：

- fresh prompt identity：
  `monitoring-protocol-clause-structuring-v12`；
- exact diagnostics：
  zero-based candidate index、one-based candidate number、field path、
  matched token/span、forbidden family/code 和完整字段 repair action；
- boundary 未放宽，uncertainty/user_action 继续参与验证；
- repair 必须重生成受影响完整字段，禁止只删词、输出后处理和无依据新事实；
- unchanged/partial repair terminal fail，0 candidates；完整字段重生成通过；
- v11 加入 immutable retirement-audit set，但继续不可
  status-compatible、retry 或 reuse；
- offline evidence：
  focused `5 passed`、core `533 passed`、adjacent `146 passed`、
  accepted full monitoring
  `1494 passed, 4480 deselected, 27 warnings`；
- Codex source review PASS，P0-P4 none；
- A6 fresh clone/zero-submit/单主题 RUX canary 已完成并立即停止服务；详见本节更新的
  terminal evidence。

2026-08-01 23:08 CST 更新：A6 已按独立门禁完成，且 Phase B B1 离线 authority
contract 已完成。新 clone 通过
zero-submit 后，仅运行一次 RUX `visit_window_and_order` POST；job
`monai_343e98b4992acc36e0c60da30e98` 以 `completed/success_repaired` 终态返回
3 个 proposed candidates。初始 provider output 的 3 个完整 boundary 命中在 repair
后归零；候选均保留来源和不确定性，未作 adoption。详见：
`runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/TERMINAL_EVIDENCE.md`。

## 4. 旧四项身份/治疗边界

旧恢复材料所列四项阻断已经在
`reviews/codex_monitoring_p10_identity_boundary_corrective_20260730_review.md`
中关闭：

1. 非试验治疗不能循环自证为 IP；
2. project-effective 不得静默过滤空/混合四元身份；
3. shadow prepare/confirm 统一四元身份并核对 effective-capabilities hash；
4. 首次 execute 前重验 frozen rule identity。

该 review 还记录：

- 中断 Kimi 历史没有未报告 source write；
- Codex 补齐两个遗漏比较；
- focused daily 20、shadow 36、adjacent writing 312；
- full monitoring 1119 pass + 3 个身份缺失旧 fixture 正确失败；
- 补齐 fixture 后精确 3 passed；
- 8911 未启动、运行库未写。

这些不是当前阻断。当前阻断是 v11 visit-topic repair。

## 5. 六个 v12 离线接受哈希

在全部源码修改结束、完整监查回归后重新计算，并在最后一次空白格式整理后再次以
pycompile、Ruff check 和 core 533 复核：

| 文件 | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_service.py` | `1fce0bf1c18803b9901039e38d700ae34715441d8857a0135f278cc851f2ebe5` |
| `services/api/app/monitoring_protocol_preparation_service.py` | `35ecbd629151d98e39499c7f7ae45481d6e813e4a477022a89aeb7b8bcab427a` |
| `tests/test_monitoring_ai_service.py` | `bb65b3ddf12f34b5892099cbc338721e74ed2895d72317f350a5422a47372b44` |
| `tests/test_monitoring_protocol_preparation.py` | `2ba514090a8ac44fae822325b5e09975369770c9bbefa9667b33c750cde6d9fe` |
| `tests/test_monitoring_ai_startup_recovery.py` | `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb` |
| `tests/test_monitoring_ai_api.py` | `e89cb84d26013682ffaeede50a556c018281a33c42e2282597b9844663fffb41` |

修改前六哈希与 v11 checkpoint 一致，因此没有把未报告并行 monitoring 修改
混入 v12。医学写作文件存在并行用户工作，本轮未触碰。

## 6. 当前运行边界

- 8911：无 listener，必须保持停止。
- 5174：无 listener，必须保持停止。
- 18911：PID 43191 listener，属于无关运行时，未触碰且不得触碰。
- v9/v10/v11：不得 retry、reuse、salvage、reclassify 或用于 candidate decision。
- 不运行第二主题、第二项目或三个真实项目。
- 不迁移隔离数据库进入权威 runtime。

## 7. 本轮变更与证据

产品与直接测试变更严格限制在：

- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

`tests/test_monitoring_ai_startup_recovery.py` 的内容和接受哈希未改变，动态合同测试覆盖
v12/v11 cutover。未修改说明书、运行库、医学写作或其他并行子系统。

新增/更新的恢复证据：

- `context/monitoring_p10_v12_structured_diagnostics_20260801_context.md`
- `reviews/codex_monitoring_p10_v12_structured_diagnostics_20260801_review.md`
- `metrics/monitoring_p10_v12_structured_diagnostics_20260801_metrics.md`
- `context/monitoring_p10_v12_offline_corrective_pause_20260801.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
  3.22
- 本复盘 checkpoint、详细 roadmap 和项目总 Goal 计划。

本切片按用户要求由 Codex 自行完成，未使用执行/会商机制或子代理。

Phase C1 当前 delta（纯离线，不改运行库）为：

- `services/api/app/monitoring_study_config.py`
- `tests/test_monitoring_study_config.py`
- `context/medical_monitoring_phase_c1_study_config_contract_20260802_context.md`
- `reviews/codex_medical_monitoring_phase_c1_study_config_contract_20260802_review.md`
- `metrics/medical_monitoring_phase_c1_study_config_contract_20260802_metrics.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` 3.31

C1 focused 12、B1-B6 compatibility + C1 58、frontend medical-monitoring Node 13 文件
sweep、pycompile、Ruff 与 review gate 均通过；下一切片仅可在同一离线边界内继续，
不得把契约误称为已完成真实 onboarding。

Phase B B1 的当前 delta（不改运行库）为：

- `services/api/app/medical_risk_authority.py`
- `tests/test_medical_risk_authority.py`
- `context/medical_monitoring_phase_b_risk_authority_20260801_context.md`
- `reviews/codex_medical_monitoring_phase_b_risk_authority_20260801_review.md`
- `metrics/medical_monitoring_phase_b_risk_authority_20260801_metrics.md`

B1 focused 7、既有风险兼容 97 均通过；其余 Phase B-I 尚未完成。

2026-08-01 23:42 CST 更新：Phase B B2-B6 也已完成为不写运行库的离线切片：

- B2 只读 reconciliation 在 A6 clone 的 35 个当前风险与 5 条处置上发现
  5 条 `disposition_identity_mismatch`，`migration_ready=false`；
- B3 生成 5 条 review-only exact `risk_id` 候选，并以内存副本 dry-run；2 条可匹配，
  3 条 MY009 source-version mismatch，1 条 aggregate-state drift；
- B4 形成 source-token/meaning-token、历史 lineage 和 append-only event replay
  的 residual decision package；5 条决策、4 个 residual blocker，全部未批准；
- B5 形成 hash-bound approval gate；实际 5 条候选均保持
  `approved=false`、`write_permitted=false`、`review_required=true`，没有独立批准
  证据，因此 gate 关闭；
- B6 形成 hash-bound explicit review-outcome gate；没有 review input 时只返回
  `pending_review / migration_ready=false / write_permitted=false`，当前实际输出的
  5 条候选均缺少 outcome，不会把“高置信候选”推断为批准；
- B7 形成不写入的 canonical risk projection contract：以唯一
  `risk_instance_id` 生成项目→中心→个例守恒投影，分离 finding/severity/status、
  unread/disposition、来源证据和 Timeline/Profile/AE/实验室/生命体征/ECG/PD 显式
  links；未接入 App/API/运行库；
- B1-B4/risk compatibility 记录已校正为 `108 passed, 17 warnings`；B5 加入
  approval focused 4 后为 `112 passed, 17 warnings`；B6 加入 review focused 5 后
  B1-B6/既有风险兼容为 `117 passed, 17 warnings`；B7 对应前端 13 文件 sweep
  全部通过。没有服务启动、API POST、运行库写入、迁移或长期 dual-write；8911/5174
  仍停止，18911 未触碰。

2026-08-02 00:16 CST 更新：Phase C1 已完成为纯离线项目中立 onboarding contract
slice：

- 新增 `services/api/app/monitoring_study_config.py` 与
  `tests/test_monitoring_study_config.py`；不修改 `main.py`、现有 adapter、API
  注册、运行库或医学写作路径；
- `StudyMonitoringConfig` 要求 opaque source-registry listing/protocol bindings、
  source revision/content SHA-256、显式 CM/IP/background treatment identity、
  版本化 mapping、八项共享 capabilities 与 deterministic `config_sha256`；
- absolute/path-traversal-like local reference、缺 source/capability、重复 ID、
  SDTM/CM-IP/self-lineage 语义违规、篡改 hash 和 malformed payload 均 fail-closed；
- C1 focused **12 passed**；B1-B6 compatibility + C1 **58 passed**；全量医学监查
  frontend Node 13 文件 sweep、pycompile、Ruff 与 `review-gate --require-verification`
  均通过；review/metrics/context/LOOP 3.31 已固化；
- C1 只是配置契约，不代表 real-project onboarding、adapter migration、浏览器
  接线或商业发布。B6 实际 reviewer outcome 与 B4 residual 仍未解决。

2026-08-02 00:28 CST 更新：Phase C2 已完成为纯离线 config→adapter translation /
read-only source-registry contract：

- 新增 `services/api/app/monitoring_study_adapter_contract.py` 与
  `tests/test_monitoring_study_adapter_contract.py`；descriptor/config identity、
  required listing/protocol source、opaque registry conflict、read-only 和
  deterministic binding hash 均有 fail-closed 校验；
- adapter 未声明的 C1 full capability 显式降为
  `unavailable/adapter_capability_missing`，既有 limited capability 不被覆盖；
- C2 focused **7 passed**；C1+C2 **19 passed**；B1-B6 compatibility + C1/C2
  **65 passed**；frontend medical-monitoring Node 13 文件 sweep、pycompile、Ruff
  与 review gate 均通过；LOOP 3.32 已固化；
- C2 未注册真实项目、未调用 adapter、未写 source registry/API/runtime、未启动
  服务，B6 reviewer outcome 与 B4 residual 继续阻断 runtime authority work。

2026-08-02 00:38 CST 更新：Phase C3 已完成为固定 sheet/metric 表面观察清单：

- 新增 `services/api/app/monitoring_adapter_mapping_plan.py` 与
  `tests/test_monitoring_adapter_mapping_plan.py`，并以代码常量/方法 locator 生成
  RUX 11、MY009 18、MG-K10 17 共 46 条 `review_only` observations；
- C3 发现并最小修复 shared mapping validator 对 canonical
  `cm.non_ip_medication` 的 `ip_` false positive，真实 `ip_*` role 仍 fail-closed；
- C3 focused **6 passed**；C1/C2/C3 + semantic quality **159 passed**；inventory
  hash `f395dc787910648362c41475266bfab80de171ab7615e68cdce904ddbe01807c`；
  pycompile、Ruff、review gate 与无绝对路径扫描通过；LOOP 3.33 已固化；
- C3 未读取真实 listing/protocol、未调用 adapter、未激活 mapping、未写 registry/API/
  runtime、未启动服务。观察清单不等于医学批准映射或完整临床事件层。

2026-08-02 00:49 CST 更新：Phase C4 已完成为统一临床事件/观察离线契约：

- 新增 `services/api/app/monitoring_clinical_event_contract.py` 与
  `tests/test_monitoring_clinical_event_contract.py`；契约明确
  project/trial/site/subject、source binding/revision/sheet/row、日期精度与实际
  日历日期、visit、raw/normalized value、unit/range、AE/MH/CM/IP/finding/PD/risk
  links、evidence、rule/threshold、completeness、uncertainty、canonical hash 与
  round-trip；不解析源、不推断链接、不持久化、不调用 adapter；
- local/absolute/path-traversal-like locator、CM/IP 交叉、未声明 evidence/rule、
  event/observation identity mismatch、非 present 的 normalized value、malformed
  completeness/uncertainty 和 tampered hash 均 fail-closed；numeric zero、partial
  date 和 nested JSON snapshot 有回归覆盖；
- C4 focused **18 passed**；C1-C4 contract + mapping semantic-quality regressions
  **131 passed**；pycompile、Ruff 与 review/metrics/context 已固化；source hash
  `038149cbfc30e835c6e1792e6b74d6bead816120e40adaf3465f7c33216815f8`，test hash
  `b2ec5fe04757afaae5d23c9a0d500a3e80615ef6e79817ef7ba1d69409aaaf96`；
- C4 仍是共享数据边界，不代表三项目真实 source mapping、Timeline/Profile/AE/
  lab/vitals/ECG UI、runtime persistence、医学批准或商业发布。

2026-08-02 01:06 CST 更新：Phase C5 已完成为只读 projection/read-model 契约：

- 新增 `services/api/app/monitoring_clinical_projection_contract.py` 与
  `tests/test_monitoring_clinical_projection_contract.py`；只消费 C4 validated
  events，不解析 listing、不推断医学关系、不运行规则、不调用 adapter、不写 API/
  runtime；
- `MonitoringClinicalProjectionScope` 显式绑定 project/trial、all subjects /
  randomized-only / allowlist、site filter 与 include/exclude USV；
  `MonitoringClinicalProjectionContext` 把 population/visit classification 与 C4
  `event_sha256` 和 evidence IDs 绑定，未知分类在排除范围时 fail-closed；
- Timeline、AE/lab/vitals/ECG observation cards、subject Profile、site/project
  rollups 保留 event hash、证据 IDs/locators、rule/threshold、raw/normalized value、
  completeness/uncertainty，并对 event/observation/risk identity 守恒、重复上下文、
  observation reuse、subject-site drift、mixed project 和篡改 hash 做 fail-closed；
- C5 focused **12 passed**；C1-C5 contracts + mapping semantic regressions
  **143 passed**；pycompile、Ruff 与 review gate 通过；source hash
  `be40f2538c9474d15091bbd61b7e7a8ee58c6b4120300a31302a6ab48b6d1579`，test hash
  `cb971ba8dd9ad2fe9b438574aab8403f0cadaa7fb1e1f0c161adecf973b72760`；
- C5 仍是 read-only 数据边界，不代表真实 adapter mapping、UI/browser、runtime
  persistence、医学批准、风险 authority migration 或商业发布。

2026-08-02 01:19 CST 更新：Phase C6 已完成为 source-preserving consumer handoff：

- 新增 `services/api/app/monitoring_clinical_consumer_handoff.py` 与
  `tests/test_monitoring_clinical_consumer_handoff.py`；由一个 C5 read model 生成
  Timeline、Profile consumer records、AE/LAB/VITALS/ECG safety metrics、risk
  drilldown 和既有 site/project rollups；不新增临床事实或第二事实源；
- event/observation/risk IDs、event hash、日期精度/raw date、visit/USV、raw/
  normalized value、unit/range、evidence ID→locator、rule IDs、completeness 和
  uncertainty 全部保留；只有显式 AE/LAB/VITALS/ECG 输出 safety metric，非安全域仍
  只保留 Timeline，风险只来自显式 risk IDs；
- 缺失 source trace、event hash mismatch、project/trial/subject identity 漂移、错误
  domain→event type、metric identity 不一致、重复 ID 和 evidence locator 冲突均
  fail-closed；证据 ID 与 locator 的配对经 hardening 后确定性排序；
- C6 focused **6 passed**；C1-C6 contract files **61 passed**；pycompile、Ruff、
  review gate 通过；source hash
  `d8a2e42144b4910bed4c28ae84f66193a3fef3a94e007981f2a7d6eedf3b2c9e`，test hash
  `6055275b9b7f996b14e971933d949dbd036dc3147b0c1b660bae5ece8d5ac174`；
- C6 仍未接 frontend/API/runtime、未调用 adapter、未读真实 listing、未启动服务、未
  迁移 authority；8911/5174 保持停止，18911/PID 43191 未触碰。

2026-08-02 01:31 CST 更新：Phase C7 已完成为 frontend-facing fixture/contract：

- 新增 `frontend/src/features/medical-monitoring/medicalMonitoringConsumerContract.mjs`
  与对应 test；它验证一个序列化 C6 handoff，并把显式 clinical domain 映射到现有
  Timeline/Profile vocabulary（如 `ae→AE`、`lab→LB`、`vitals→VS`），保留 event/
  observation/risk IDs、hashes、日期精度/raw date、visit/USV、raw/normalized value、
  unit/range、evidence ID→locator、rule IDs、completeness/uncertainty 和 limitations；
- fixture 只输出 raw profile、安全 metric 和 link-only risk records；不生成 canonical
  risk severity/status/normality、baseline/study-day、clinical interpretation、efficacy
  或 risk prompt。缺失/重复/混合身份、未知 domain、point/event hash mismatch、subject
  conservation、trusted handoff hash mismatch 和证据配对错误均 fail-closed；
- C7 focused Node **13 passed**；医学监查 frontend **14 个 test files 全部通过**；
  `node --check`、review gate 通过；source hash
  `0ab060e82e38113b2189986299c3d2391dd1c2d1f4d43feda16caa01fb41bacb`，test hash
  `5e273d55314199997aeb53fcc8e2b8f1c73c29c2fd8a958825cb76d8461ba286`；
- C7 未修改 React/App/CSS/API/runtime，未启动服务、浏览器、adapter 或真实项目；下一
  安全动作是 C8 read-only adapter fixture matrix 与 source/field coverage，仍保持
  8911/5174 停止和 B6 `pending_review`。

2026-08-02 01:44 CST 更新：Phase C8 已完成为 review-only adapter consumer coverage matrix：

- 新增 `services/api/app/monitoring_adapter_consumer_coverage.py` 与对应 test；coverage
  对每个 C3 observation 给出显式 Timeline/Profile/safety_metric/risk_link surfaces、
  C4/C5/C6 required event/observation fields、原始 adapter/project/trial/source
  sheet/field/evidence locator 和 review-only status；risk policy 固定为
  `explicit_risk_instance_id_only`，`activation_allowed=false`；
- `AE`/`LAB`/`VITALS`/`ECG` 才能声明 safety metric；`SOURCE` 与
  `BACKGROUND_TREATMENT` 明确归入 `OTHER` 并保留 observed label，不把治疗身份误标为
  IP/CM；缺失/重复/未知 domain、surface overclaim、非 review-only 或 activation 均
  fail-closed；
- 从现有 C3 inventory 生成矩阵
  `runs/execution/medical_monitoring_phase_c8_adapter_consumer_coverage_20260802/ADAPTER_CONSUMER_COVERAGE_MATRIX.json`：
  RUX 11、MY009 18、MG-K10 17，共 **46 observations**，三项 plan hash 全匹配；matrix
  hash `ce7dd80adc1806ef9ffaf22dd1a1f8a5f63e571125aa93e6d4c5c76e1714983d`；
- C8 focused **4 passed**；C1-C8 Python contract suite **65 passed**；pycompile、Ruff、
  matrix builder 和 review gate 通过。无 adapter/source listing/browser/service/
  runtime/real-project invocation；8911/5174 保持停止，18911/PID 43191 未触碰。

2026-08-02 01:54 CST 更新：Phase C9 已完成为 source-bound schema-only fixture validation：

- 新增 `services/api/app/monitoring_source_fixture_validation.py` 与 test；`SourceFixtureRecord`
  只验证 C8 mapping/project/trial/source sheet/field/evidence locator/source revision，保留
  raw value（含 numeric zero）和 explicit missing/unknown，拒绝 normalized value、path-like
  locator、active mapping、非 schema-only 记录和无效日期；不创建 C4 clinical event；
- 由 C3/C8 evidence 生成
  `runs/execution/medical_monitoring_phase_c9_source_bound_fixture_validation_20260802/SCHEMA_ONLY_SOURCE_FIXTURE_MANIFEST.json`：
  RUX 11、MY009 18、MG-K10 17，共 **3 reports / 46 records**，0 missing mappings，
  `schema_only=true`、`activation_allowed=false`；manifest hash
  `1648fa85e6daba48e28acfa6409595b94baf3582af81d5aefb1e05b665476e60`；
- C9 focused **3 passed**；C1-C9 Python suite **68 passed**；pycompile、Ruff、manifest
  builder 和 review gate 通过。未读取真实 listing/protocol、未调用 adapter、未启动服务或
  写入 runtime；8911/5174 保持停止，18911/PID 43191 未触碰。

2026-08-02 01:55 CST 更新：Phase C10 已完成为 source-bound schema-only fixture
field-presence/diff report：

- 新增 `services/api/app/monitoring_source_fixture_diff.py` 与 test；在 C8 coverage
  和 C9 manifest 上逐条报告 source identity/raw/date 字段的 `present_fields`，把事件、
  observation、normalized value、completeness、uncertainty 与 rule fields 明确列为
  `not_assessable`，固定 `status=schema_only_unassessed`，拒绝 complete/active/unknown
  field、hash drift 与 mapping conservation 破坏；
- 生成
  `runs/execution/medical_monitoring_phase_c10_source_fixture_diff_report_20260802/SOURCE_FIXTURE_FIELD_PRESENCE_REPORT.json`：
  RUX 11、MY009 18、MG-K10 17，共 **3 reports / 46 rows**，0 missing mappings、736
  not-assessable clinical-field entries，`schema_only=true`、`activation_allowed=false`；
  report content hash `00b421dab4c9672e2d3ceda9432254c3d4db067f7a0596f1340a1ca838b423bc`；
- C10 focused **3 passed**；source/test/builder pycompile、Ruff、review gate 通过。未读取
  真实 listing/protocol、未调用 adapter、未启动服务或写入 runtime；8911/5174 保持停止，
  18911/PID 43191 未触碰。

2026-08-02 02:04 CST 更新：Phase C11 已完成为只读 onboarding/consumer cross-surface
conservation contract：

- 新增 `services/api/app/monitoring_onboarding_consumer_conservation.py` 与 test；逐条
  join C8 review-only coverage、C9 schema-only fixture、C10 field-presence row 和 C7
  frontend `timeline`/`subjects`/`safety_metrics`/`risk_links` vocabulary；身份、C8/C9/C10
  hash、surface、missing-set 和 schema-only/inactive flags 任一漂移均 fail-closed；
- 生成
  `runs/execution/medical_monitoring_phase_c11_onboarding_consumer_conservation_20260802/ONBOARDING_CONSUMER_CONSERVATION_REPORT.json`：
  RUX 11、MY009 18、MG-K10 17，共 **3 reports / 46 rows**，0 missing；Timeline/Profile/
  risk-link 46/46，safety metric 21/46；全部 `readiness=structural_only`、
  `status=schema_only_cross_surface_unassessed`、`schema_only=true`、
  `activation_allowed=false`；report content hash
  `dd96e05a5faab4a56506a00e0244b4e22ecc2b3639b7861914b51e26e564c327`；
- C11 focused **4 passed**；C1-C11 Python suite **75 passed**；source/test/builder
  pycompile、Ruff、review gate 通过。未读取真实 listing/protocol、未调用 adapter、未启动
  服务或写入 runtime；8911/5174 保持停止，18911/PID 43191 未触碰。

2026-08-02 02:12 CST 更新：Phase C12 已完成为 source-specific adapter fallback/
retirement policy contract：

- 新增 `services/api/app/monitoring_adapter_fallback_contract.py` 与 test；每条 C8/C11
  mapping 只允许 `limited`/`unavailable`，默认 `unavailable`，payload policy 固定
  `metadata_only_no_clinical_records`，risk action 固定 `blocked`，并要求六项真实 source/
  医学/字段证据/consumer/risk authority/browser-runtime 条件后才可退休；任何 active、
  clinical-ready、retired、unsupported trigger 或不完整条件均 fail-closed；
- 生成
  `runs/execution/medical_monitoring_phase_c12_adapter_fallback_retirement_20260802/ADAPTER_FALLBACK_RETIREMENT_POLICY_MATRIX.json`：
  RUX 11、MY009 18、MG-K10 17，共 **3 reports / 46 policies**，0 missing，全部
  `default_state=unavailable`、`not_retired`、`schema_only=true`、`activation_allowed=false`；
  report content hash `0cd6d75dc37f3a420928948aca6ec75b97c1c7ab546828dd499f08e97231bb42`；
- C12 focused **4 passed**；C1-C12 Python suite **79 passed**；source/test/builder
  pycompile、Ruff、review gate 通过。未读取真实 listing/protocol、未调用 adapter、未启动
  服务或写入 runtime；8911/5174 保持停止，18911/PID 43191 未触碰。

2026-08-02 02:27 CST 更新：Phase C13/C14 已完成为 blocked activation route 与实际
B6 authority gate：

- C13 新增 `services/api/app/monitoring_activation_projection_contract.py` 与 test；未来
  approved mapping 只能进入 C4 `MonitoringClinicalEvent/Observation` 与 C5/C6
  `ReadModel/ConsumerHandoff`，当前 C8/C11/C12 输入全部保持 `blocked_pending_approval`，
  46/46 rows event creation、projection、activation 全 false；报告 content hash
  `297823fd71ab6be982ecb6b869a97440653a0b61cfb378d814afa75c6b0d7399`；C13 focused **4
  passed**，C1-C13 Python suite **83 passed**；
- C14 新增 `services/api/app/monitoring_b6_activation_gate.py` 与 test，把只读的实际
  `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  绑定到 C13：`pending_review`、5 candidates、0 outcomes、5 missing candidate records、
  2 unresolved blockers、`migration_ready=false`、`write_permitted=false`，C13 46/46 rows
  blocked；报告 content hash
  `5db5fedf9ba9c62d6b1605c9869d9051455584b2d61a19245861a273c9596a85`；C14 focused **4
  passed**，C1-C14 Python suite **87 passed**；
- C13/C14 pycompile、Ruff、deterministic generation 与 review gates 通过。B6 原文件未改写，
  未读取真实 listing/protocol、未调用 adapter、未启动服务或写入 runtime；8911/5174 保持
  停止，18911/PID 43191 未触碰。

2026-08-02 续作更新：在不改变 B6 gate 的前提下，对五条 candidate 做了只读证据核对，并
形成 `runs/execution/medical_monitoring_phase_b6_codex_review_recommendation_20260802/CODEX_INDEPENDENT_REVIEW_RECOMMENDATION.md`
（hash `593e8ba22243f71e0307c74d6c600867122be90b6a8ae7f9dcfe4057bbaec996`）。MY009 三条
记录均指向当前 S01003 风险，但 legacy instance/key 与 source token 缺失，必须先完成
source-token revalidation 并作为一条 append-only chain replay；RUX 两条可 exact-after-identity
对齐且最新证据 snapshot 可用，但仍需授权医学/工程显式 outcome。建议稿明确五条均为
`pending_review`，不是 `MedicalRiskMappingReviewOutcome`，不授予批准或写入。B6 仍为
5 candidates/0 outcomes/5 missing、2 blockers、`migration_ready=false`、`write_permitted=false`；
8911/5174 继续停止，18911/PID 43191 未触碰。

2026-08-02 续作产品修正：为满足项目→中心→个例的清晰查询，Inbox 风险投影现在优先
读取显式 `site_id`/`site`/`siteId`/site scope `scope_id`，仅在旧 payload 缺少显式身份时
回退到 `S<site><subject>` 兼容切片；新增 `target_id="10008"` + `site_id="10"` 回归。
focused model **45 passed**、14 个医学监查 Node suite 全部通过，Vite `1914 modules`
生产构建成功。记录位于
`records/active_slices/medical_monitoring_inbox_site_identity_20260802/`，LOOP 3.46
已登记。该修正未触碰 `App.jsx`、`main.py`、API/adapter、运行库、B6 gate、服务、浏览器、
真实项目或医学写作；不改变 B6 `pending_review` 或下一安全动作。

2026-08-02 P8 产品面增量：医学监查页新增“锁库 / 核查工作区”，展示两种保障模式、当前
风险快照、任务状态、冻结身份完整性和 proof/rollup 证据状态。初始读取和刷新为 GET-only；
当前页面缺少完整九字段 frozen identity 或明确 authority 写入许可时，创建任务保持阻断并显示
缺失状态，不猜测版本或绕过 B6。
新增 feature 文件与记录位于
`records/active_slices/medical_monitoring_p8_frontend_assurance_20260802/`；focused **18
passed**，医学监查 **15 个 Node test files** 全部通过，Vite `1918 modules transformed`
构建成功。该切片未接通写入型 proof/rollup/medical-review/complete 操作，不改变 B6 gate、
服务停止或下一安全动作。

2026-08-02 P4/Phase F 离线质量观测增量：新增
`services/api/app/monitoring_ai_quality.py` 与专属测试，从既有 job/attempt snapshot 生成
稳定、不可变的质量观测，保留 raw attempt outcome、输入 revision/source、prompt/profile/
provider/model、failure/repair、可选 latency/token/cost 和独立人审反馈；真实产品 outcome
集合采用显式有限归一化，未知值 fail-closed。coverage summary 只报告 project×task 覆盖和
失败/修复/人审计数，不输出医学正确、批准或 release-ready 结论。focused **9 passed**，
产品 AI 相邻 `608 passed, 17 warnings`，`.venv` 编译/Ruff/格式检查通过。记录位于
`records/active_slices/medical_monitoring_p4_quality_observation_20260802/`；本切片未改
repository/schema/API/router/main.py/frontend/adapter/医学写作/运行库，未调用 provider 或
启动服务。它只关闭离线质量证据合同，不关闭 P4/Phase F；运行时 telemetry 接线、三项目
质量矩阵、anti-overfit、prompt release/rollback 与真实人审仍待后续 Controlled 切片。

## 8. 项目总 Goal 与下一安全动作

项目总 Goal 从当前停止点持续覆盖：

1. Phase A：v12 与证据重基线；
2. Phase B：统一风险与处置权威；
3. Phase C：项目中立 onboarding；
4. Phase D：日常真实 LOOP；
5. Phase E：锁库前/核查前产品化；
6. Phase F：产品 AI 质量系统；
7. Phase G：平台硬化；
8. Phase H：三真实项目端到端系统验收；
9. Phase I：安装升级、质量追溯、许可/SBOM、UAT、运维支持和商业发布。

阶段 checkpoint 仅用于验证与无损恢复，不代表项目总 Goal 完成。只有 Phase I 商业发布门全部通过，且无未关闭 P0/P1 发布阻断项并形成明确发布决定，才可标记项目总 Goal 完成。

后续所有产品阶段还必须满足：

- 首页信息量克制，只突出关键变化、最高优先级风险、待办和阻断；
- 项目→中心→个例→原始记录逐层图形化下钻；
- Timeline、Patient Profile、AE/实验室/生命体征/ECG 风险评估、Finding/PD 和处置共享同一事件/证据与风险身份；
- 三级数量、严重度、状态和处置对账；图表/HTML 只做投影，不成为第二事实源；
- 风险依据、CTCAE/阈值、项目规则、计算、不确定性和 locator 全部可追溯。

v12 A1-A6、Phase B B1-B7 离线合同和 Phase C1-C14 配置/翻译/观察清单/临床事件/投影/消费者交接/前端 fixture/adapter coverage/source-bound validation/field-presence-diff/cross-surface-conservation/fallback-retirement/blocked-activation/B6-gate 契约已通过并固化，但 Phase B
仍未关闭。当前下一安全动作是取得授权 reviewer 的显式 outcome，再进入 B6
approved-input dry-run；但当前没有可安全进入的下一实现切片：必须先取得授权 reviewer
对 5 条 B6 candidate 的显式 outcome，重放 append-only disposition chain 到 aggregate，
并完成 legacy source revision token revalidation；在此之前只能保持 C13/C14 blocked/read-only：

1. 恢复时先完整读取最新指令、A6 terminal evidence 和
   `context/medical_monitoring_p10_v12_runtime_gate_20260801_context.md`；
2. 重算六哈希并确认 8911/5174 仍停止；
3. 复核 v9-v11 冻结历史和 authority hash；
4. B1-B7 已完成 `MedicalRiskAggregate`、事件/证据身份、CAS、只读 reconciliation、
   review-only mapping、residual decision、hash-bound approval 和 explicit review
   outcome gate/tests 与不写入风险投影；现阶段必须先取得五条候选的显式医学/工程 review outcome，
   只有明确批准且 residual blocker 清零后才能在内存副本重跑 approved-input dry-run；
   不迁移权威库、不长期 dual-write；
5. B6 approved-input dry-run 通过后再按 Phase B 退出门设计 dual-read/reconciliation、重启、旧深链和三级
   投影回归；任何权威迁移仍需另立 versioned migration 任务和回滚证据；下一安全
   C10/C11/C12/C13/C14 已完成且只允许离线 source-bound/consumer conservation/fallback/authority-gate 验证；未取得 reviewer outcome 前不得注册真实项目或启动服务。

A6/C1/C2/C3/C4/C5/C6/C7/C8/C9/C10/C11/C12/C13/C14 关闭后也不得把整个项目标记完成。后续应按 Phase B-I 继续统一风险/处置
权威、项目中立 onboarding、三级图形化钻取、Profile/Timeline/AE 风险联动、
真实项目矩阵和商业发布门。项目总 Goal 与恢复 Prompt已写入详细报告第 12-13 节，
并在 `.hermes/plans/2026-08-01_210824-medical-monitoring-commercialization-goal.md`
中形成独立总计划。

## 2026-08-02 03:25 CST：LOOP 3.49 P8 rollup drilldown 增量

为满足“信息量克制、项目→中心→个例可查、Timeline/Profile 可联动”的产品目标，在不
触碰 B6/authority/runtime 的前提下新增 `medicalMonitoringAssuranceRollup.mjs` 与测试，
并扩展 `MedicalMonitoringAssurancePanel` 的 pre-inspection 只读展示：项目总量、开放/高风险、
已关闭/缺关闭证据、严重度分布、中心层和有限个例层列表。项目/中心/个例只显示后端显式
reference；同一 `risk_instance_id` 集合和显式计数不守恒时显示“三级对账阻断”，不推断或
修复医学事实。中心按钮复用既有风险范围回调，个例按钮显式传 `subject_id` 后进入既有
Patient Profile / Subject Timeline。

证据：focused rollup **16 passed**；医学监查前端 **16 个 test files passed**；Vite
**1919 modules transformed**；仅既有 large chunk warning。切片记录、review、metrics 和
哈希位于 `records/active_slices/medical_monitoring_p8_rollup_drilldown_20260802/`。
未启动 8911/5174、服务、provider、浏览器或真实项目，未写 B6/运行库/医学写作；18911/PID
43191 未触碰。本增量不是 P8/Phase E 退出。恢复时仍先取得 B6 五条 candidate 的显式
review outcome，重放 aggregate 并完成 legacy source revision token revalidation，再做
approved-input 内存 dry-run；之前保持 C13/C14 blocked/read-only。

## 2026-08-02 03:30 CST：LOOP 3.50 P4 prompt/model release governance 增量

新增 `services/api/app/monitoring_ai_release.py` 与测试，建立纯离线、不可变的
candidate→approval→activation→retirement/rollback 契约。候选绑定 prompt 精确内容 hash、
task/model/input/evaluator revision、真实 observation IDs 与 evaluation snapshot hash；审批、
激活、旧版本退休和回滚均要求同 task、合法状态与 hash-bound reviewer evidence。函数只返回
新快照，不改 PromptRegistry、AI queue、job retirement、API/schema/runtime 或 provider。

证据：focused **9 passed**；产品 AI 相邻 **617 passed, 17 warnings**；py_compile、Ruff
format/check 通过。记录位于
`records/active_slices/medical_monitoring_p4_prompt_release_governance_20260802/`，哈希已固化。
未启动 8911/5174、服务、provider、浏览器或真实项目，未写 B6/运行库/医学写作；18911/PID
43191 未触碰。该切片不关闭 P4/Phase F，不代表真实 AI 评测、prompt release/rollback 演练或
商业发布。恢复时仍先处理 B6 显式 reviewer outcome、aggregate replay 和 source revision
revalidation，再做 approved-input 内存 dry-run；随后另立受控 runtime integration。

## 2026-08-02 03:45 CST：LOOP 3.51 真实源文件只读分类预检

在不改变 B6 gate、未注册 study、未调用 adapter 和未启动服务的前提下，对当前可见的三份
真实 listing workbook 执行只读 parser/classifier preflight。聚焦测试 **8 passed, 1 warning**；
MY009 comparison 被识别为 `comparison_workbook`（63 sheets/4,414 rows），RUX 处理后文件被
识别为 `processed_full_snapshot`（54/180,793），RUX 原始工作簿的 XML dimension 缺陷被识别为
`raw_snapshot_with_format_defect`（54/180,793）；三者 baseline 资格均为 false。原始文件只
输出大小、SHA-256、sheet/row 计数和技术警告，不保存单元格或受试者内容。完整证据、源码哈希和
审阅见 `records/active_slices/medical_monitoring_source_preflight_20260802/`。

该切片证明真实源技术分类门可以暴露比较/处理/格式缺陷而不静默降级，但不证明字段 mapping、
协议规则、临床事件/风险链接、医学正确性、项目 onboarding 或日常 LOOP。B6 仍为
`pending_review`（5 candidates、0 outcomes、2 unresolved blockers、`migration_ready=false`、
`write_permitted=false`）；8911/5174 继续停止。下一安全动作仍是取得授权 reviewer outcome、
重放 append-only disposition chain 到 aggregate、完成 legacy source revision token revalidation，
再做 approved-input 内存 dry-run；此前继续保持 C13/C14 blocked/read-only。
## 2026-08-02 04:10 CST：LOOP 3.52 P4 §40.3 cross-project AI evaluation matrix

为补齐现有 quality observation 只有覆盖统计、没有三真实项目×任务与未见项目 anti-overfit
结构门的缺口，新增离线 `monitoring_ai_evaluation_matrix.py` 与专属测试。矩阵消费 immutable
observation，分离 real/unseen tracks，逐 project×task 保留 observation IDs、完成/失败/修复/
人工审阅计数；missing、unreviewed、failed-only、矩阵外项目/任务、重复 ID 和轨道重叠均
fail-closed。`build_independent_ai_release_matrix` 固定说明书 §40.3 的四项必需产品 AI 面：
字段语义映射、方案条款提取、风险证据摘要、交互追问；状态固定为
`evidence_matrix_only`，不表达医学正确性或 release-ready。

证据：focused **6 passed**；产品 AI 相邻 **623 passed, 17 warnings**；py_compile、Ruff
format/check 通过。记录与哈希位于
`records/active_slices/medical_monitoring_p4_ai_evaluation_matrix_20260802/`，metrics 位于
`metrics/medical_monitoring_p4_ai_evaluation_matrix_20260802_metrics.md`。未调用 provider、
未启动服务/浏览器/真实项目、未写 API/运行库/B6/医学写作；8911/5174 保持停止。

该切片只建立 Phase F 的离线 evidence matrix contract，不关闭真实 AI 评测、三项目矩阵、
anti-overfit、人工医学评价或 Phase F/商业发布门。B6 仍 `pending_review`（5 candidates、0
outcomes、2 blockers、`migration_ready=false`、`write_permitted=false`）；后续仍先取得授权
reviewer outcome、重放 aggregate/source-token，再做 approved-input 内存 dry-run。

## 2026-08-02 LOOP 3.53：Phase G versioned migration ledger / startup reconciliation contract

代码审查确认监查侧多个 repository 仍在各自启动路径中补表/补列，缺少统一的版本化迁移账本、
备份/回滚证据和跨库启动对账边界。本切片新增纯内存、只读
`services/api/app/monitoring_migration_contract.py` 与测试：迁移显式绑定 from/to schema、
store scope、preflight/post-check、migration/rollback SHA-256、backup/rollback；版本区间重叠、
缺失/重复/未知观察、部分终态证据、当前版本漂移和失败无 error code 均 fail-closed。

`build_migration_reconciliation_report` 对非明确 approved authority（当前 B6 为
`pending_review`）固定输出 `blocked_pending_authority`；即使输入 approved，也只生成
pending/no-op/`reconcile_required` 的不可变证据，报告强制
`write_permitted=false`、`migration_write_permitted=false`。focused **10 passed**；B6、AI
startup recovery、mapping activation 相邻 **36 passed, 17 warnings**；py_compile、Ruff
format/check 全部通过。记录和哈希位于
`records/active_slices/medical_monitoring_phase_g_migration_contract_20260802/`，metrics 位于
`metrics/medical_monitoring_phase_g_migration_contract_20260802_metrics.md`。

本切片没有打开 SQLite、创建/恢复备份、接入 `main.py`/API/provider、启动服务/浏览器/真实项目，
也未触碰 B6 原文件或医学写作；8911/5174 保持停止，18911/PID 43191 未触碰。它只是 Phase G
离线平台硬化合同，不是 migration executor、重启/灾备、身份/RBAC、API v1、三项目 LOOP 或商业
发布证据。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers）；下一安全动作仍为
授权 reviewer outcome → aggregate replay/source-token revalidation → approved-input 内存
dry-run。

## 2026-08-02 LOOP 3.54：B4/B6 legacy source-token compatibility revalidation

只读复核 B4 residual package 并新增
`services/api/app/monitoring_source_revision_compatibility.py`：支持 legacy/current revision
的 family、rule、source-token、meaning-token 比较；MY009 legacy 只有 meaning token 时固定标记
`legacy_source_revision_missing_same_meaning`，不从 candidate source revision ID 推断 bytes、
不补 token、不选择 candidate。RUX 两条 exact token identity 也只说明结构相等，不是 B6 outcome、
aggregate replay 或迁移授权。

B4 五条 decisions 的 metadata-only replay：`case_count=5`、`exact_count=2`、
`revalidation_required_count=3`、`source_revalidation_complete=false`、`migration_ready=false`；
report SHA-256 为 `2c4628ea5517f5818eef9be285f659c0930f7c41218b227f15a91e6744ef4f91`。compatibility、
既有 reconciliation、B6 gate 共 **21 passed**；py_compile、Ruff format/check 全部通过。记录与
哈希位于 `records/active_slices/medical_monitoring_phase_b_source_revision_revalidation_20260802/`，
metrics 位于 `metrics/medical_monitoring_phase_b_source_revision_revalidation_20260802_metrics.md`。

本切片未读取 listing/protocol bytes、未打开 SQLite、未修改 B6/aggregate/runtime、未调用
API/provider、未启动服务/浏览器/真实项目；8911/5174 保持停止，18911/PID 43191 未触碰，医学写作
未触碰。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers）；下一安全动作仍为授权
reviewer outcome → 原始 source-content lineage revalidation → aggregate replay → approved-input
内存 dry-run。

## 2026-08-02 LOOP 3.55：B6 append-only disposition chain → aggregate read-only replay

为处理 B6 的 `append_only_disposition_chain_must_be_replayed_into_aggregate` 残差，新增纯内存
`services/api/app/monitoring_disposition_chain_replay.py`。链从 canonical `pending_review` 开始，
按 `created_at + record_id` 排序；canonical state、时区、previous-state gap、重复 event ID 和
expected aggregate drift 均 fail-closed，不自动修复或写入 aggregate。

B4 五条 decisions 按当前 `(project_id, current_risk_instance_id)` 去重为两条独立链：MY009 最终
`submitted_for_approval`，RUX 最终 `pending_review`，metadata replay `replay_complete=true`、
`issue_count=0`；report SHA-256 为
`85e3e8c64b29e1b1699904d61958a1b8aac6efbeb67908f9b72ae6085a191f5d`。报告强制
`aggregate_write_permitted=false`、`migration_ready=false`，因此不代表权威 aggregate 已应用、
CAS/幂等/重启已通过或医学审查已批准。

replay、risk authority、reconciliation、B6 gate 共 **28 passed**；py_compile、Ruff format/check
通过。记录和哈希位于
`records/active_slices/medical_monitoring_phase_b_disposition_chain_replay_20260802/`，metrics 位于
`metrics/medical_monitoring_phase_b_disposition_chain_replay_20260802_metrics.md`。未读取当前
aggregate、未打开 SQLite、未修改 B6/runtime、未调用 API/provider/adapter、未启动服务/浏览器/真实
项目；8911/5174 保持停止，18911/PID 43191 未触碰，医学写作未触碰。B6 仍 `pending_review`（5
candidates/0 outcomes/2 blockers）；下一安全动作仍为授权 reviewer outcome → 实际 aggregate
snapshot/CAS replay → source lineage revalidation → approved-input 内存 dry-run。

## 2026-08-02 LOOP 3.70–3.75：风险下钻、Profile/Timeline 与 Checklist 只读边界收敛

在 B6 未取得授权 outcome、8911/5174 停止且不得写权威运行库的前提下，前端只读产品面继续完成
严格形状和范围一致性收敛：项目→中心→个例风险身份/来源/linked views、Profile/Timeline payload、
范围待行动计数以及 Checklist rows/taxonomy/total/locked-filter/refresh 均 fail-closed；异常字段不会被
包装成展示事实，受限能力和来源证据异常会在界面显式提示。LOOP 3.70–3.75 的 Node 合约、Python
静态合同和生产构建均通过；最新 Checklist 切片为 16 个 Node 文件、Python **54 passed**、Vite
**1919 modules**，详情见 `context/medical_monitoring_checklist_shape_guard_20260802.md`。

这些是离线 UI/contract 证据，不是三项目真实 runtime、浏览器、科学性、连续批次、B6 authority、迁移
或商业发布证据。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；下一
安全动作保持为授权 reviewer outcome → aggregate/source-token replay → approved-input 内存 dry-run，
之前不得真实 onboarding、Timeline/Profile runtime activation、API POST、迁移或 dual-write。

## 2026-08-02 LOOP 3.76：日常医学监查状态机消费边界

在同一离线边界内，日常运行面新增 list/detail/steps、风险计数、AI 进度和比较基线 revision 的严格
形状消费：异常 payload 清理旧状态并停止展示，风险计数不再把 malformed 值当成零，baseline CAS 版本
异常时不显示确认按钮。17 个 Node 合约文件、Python 54 passed 和 Vite 1920 modules 构建通过；详情见
`context/medical_monitoring_daily_run_shape_guard_20260802.md`。

该切片仍不是真实日常 LOOP、连续全量批次、AI runtime、人审、浏览器或商业发布证据。B6 继续为
`pending_review`（5 candidates/0 outcomes/2 blockers），C13 继续 blocked；下一安全动作仍为授权
reviewer outcome → aggregate/source-token replay → approved-input 内存 dry-run，之前不得 API POST、
真实项目 onboarding、迁移或 dual-write。

## 2026-08-02 LOOP 3.77：方案原文结构化状态边界

方案准备/规则建议入口新增 status/topics/candidates/allowed fact types/证据 ID 的统一形状校验；
malformed payload 会停止候选展示和状态推进，不补造方案事实或来源证据。17 个 Node 合约文件、Python
54 passed 与 Vite 1920 modules 构建通过；详情见
`context/medical_monitoring_protocol_preparation_shape_guard_20260802.md`。

该切片仍不是真实方案 bytes→结构化→医学采纳→规则发布证据。B6 继续为 `pending_review`（5 candidates/
0 outcomes/2 blockers），C13 继续 blocked；下一安全动作仍为授权 reviewer outcome → aggregate/source-token
replay → approved-input 内存 dry-run，之前不得 API POST、真实项目 onboarding、迁移或 dual-write。

## 2026-08-02 LOOP 3.78：Field Mapping 状态/草稿/正式版本形状边界

复核字段识别与映射校对面板，发现启动回执、`job_details`、候选
`structured_payload.field_mappings`、草稿 `fields`、正式 revision 与语义质量报告仍有直接消费路径；
scalar/缺失数组、字符串 confidence/count、计数不一致或错误 activation 形状可能抛错、静默变空或继续
允许医学确认。新增 `medicalMonitoringFieldMappingView.mjs`，统一校验 job/candidate/field/draft/revision/
semantic-quality 的闭合集合、显式非负计数、0–1 confidence、数组与身份字段；面板的状态、启动、草稿编辑、
正式版本读取和确认回执均先过 guard，malformed shape 清理旧映射状态，不把错误数值转成 0；确认回执保存完整
activation 对象。

Field Mapping view **11 passed**；state **8 passed**（共享语义质量 malformed guard）；project-switch isolation **35 passed**；医学监查全部
**18 个 Node 合约文件通过**；前端监查/统一风险/Timeline Python 合同 **54 passed**；`npm run build`（frontend）
成功（Vite **1921 modules transformed**，仅既有大 bundle warning）。详情与 SHA 见
`context/medical_monitoring_field_mapping_shape_guard_20260802.md`。

本切片仅修改前端 Field Mapping 只读状态消费、草稿/正式回执 guard 与测试；未启动 8911/5174、API、provider、
浏览器或真实项目，未读写权威 SQLite，18911/PID 43191 与医学写作未触碰。B6 仍 `pending_review`（5 candidates/
0 outcomes/2 blockers），C13 仍 blocked。Product Design 视觉审计因当前边界禁止启动服务/浏览器而未宣称完成；
没有 reviewer outcome、迁移、事件创建、投影激活或商业发布授权。下一安全动作仍为授权 B6 reviewer outcome →
实际 aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run，之前不得
真实 onboarding、Timeline/Profile runtime activation、API POST、迁移或 dual-write。

## 2026-08-02 LOOP 3.79：批次/来源入口形状边界

复核“原始 listing → 来源身份 → 批次状态机”前端消费，发现批次列表/详情、来源注册、内容校验、来源分类、
intake/transition/freeze 回执仍有 `|| []` 或未验证嵌套路径，malformed payload 可能被显示为空、继续进入冻结/基线
路径或产生未处理 Promise。新增 `medicalMonitoringBatchView.mjs`：校验项目绑定、batch state/version/domains、
source class/hash/file/technical status/warnings、row/domain counts、validation checks、classification 和
mutation identity；面板所有列表、详情、导入、转换、冻结、选择、刷新与确认错误均先过 guard。异常清空旧批次状态
并停止推进；比较/混合/格式异常/还原/未知来源不会被改写为原始全量基线，处理后来源仍需 B 级确认。

Batch view **13 passed**；project-switch isolation **40 passed**；医学监查全部 **19 个 Node 合约文件通过**；
前端监查/统一风险/Timeline Python 合同 **54 passed**；`npm run build`（frontend）成功（Vite **1922 modules transformed**，
仅既有大 bundle warning）。详情与 SHA 见 `context/medical_monitoring_batch_shape_guard_20260802.md`。

本切片仅修改前端批次/来源只读消费、确认错误处理与合同测试；未启动 8911/5174、API、provider、浏览器或真实项目，
未读写权威 SQLite，18911/PID 43191 与医学写作未触碰。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers），
C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；无 reviewer outcome、迁移、事件创建、投影激活或商业
发布授权。下一安全动作仍为授权 B6 reviewer outcome → aggregate snapshot/CAS replay 与 MY009 source-token revalidation →
approved-input 内存 dry-run，之前不得真实 onboarding、API POST、迁移或 dual-write。

## 2026-08-02 LOOP 3.80：规则发布/影子证据形状边界

复核规则包列表/详情、自动影子样本、影子运行、谱系恢复、差异、冻结批次与日常就绪在规则发布面板的消费，发现
`items || []`、宽松 pack/result 嵌套和未验证的 provisional/trusted evidence 可能把 malformed 或跨项目响应继续带入发布链。
新增 `medicalMonitoringRuleReleaseView.mjs`：校验项目/方案/规则包/规则身份、闭合 lifecycle、影子样本状态与计数、影子运行标准/诊断计数守恒、谱系确认集、差异和 readiness；面板所有读取与 draft/shadow/confirm/publish 回执先过 guard，异常清空旧规则发布状态。后端公开视图主动裁剪的内部哈希及行级 project/rule identity 由已验证父级上下文补足，不从缺失字段猜测医学内容；provisional UI 继续拒绝 `shadow_passed`/“验证通过”词汇。

Rule-release view **21 passed**、Rule release **63 passed**、project-switch isolation **49 passed**；医学监查全部 **20 个 Node 合约文件通过**；前端监查/统一风险/Timeline Python 合同 **54 passed**；Vite **1923 modules transformed** 构建成功。详情与 SHA 见 `context/medical_monitoring_rule_release_shape_guard_20260802.md`。

该切片仍只是规则发布 UI 的输入形状/项目隔离/证据显示安全合同，不是真实方案/listing、连续全量批次、规则医学科学性、B6 authority、aggregate/CAS、source-token lineage、runtime、浏览器或商业发布证据。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers，`migration_ready=false`、`write_permitted=false`），C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；8911/5174 必须继续停止。下一安全动作保持为授权 B6 reviewer outcome → aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run，之后才可重新申请受控 runtime、三项目真实 LOOP 与浏览器/科学性验收。

## 2026-08-02 LOOP 3.81：独立 AI 规则建议形状边界

复核“已确认方案事实 → 独立 AI 规则建议 → 医学经理采用/驳回”链，发现规则建议 status/candidates/mapping_fields/source/revision 和 decision response 仍由宽松默认对象/数组消费，malformed 或跨项目响应可能继续展示旧候选或进入采用路径。新增 `medicalMonitoringRuleTemplateView.mjs`：校验 project/fact/source/mapping/input revision、闭合状态、候选身份与字段映射、决策候选一致性、confirmed fact/compiled rule/next action；面板 status/start/decision 响应均先过 guard，形状异常清空旧规则建议 payload，不触发真实 AI 任务。

Rule-template view **13 passed**、Rule-template recommendation **22 passed**、project-switch isolation **52 passed**；医学监查全部 **21 个 Node 合约文件通过**；前端监查/统一风险/Timeline Python 合同 **54 passed**；Vite **1924 modules transformed** 构建成功。详情与 SHA 见 `context/medical_monitoring_rule_template_shape_guard_20260802.md`。

该切片仍只是独立 AI 规则建议 UI 的输入形状/项目隔离/候选证据显示安全合同，不是 AI 语义正确性、四类任务 × 三项目独立评估、超时/低置信度/无效 JSON/重启恢复、真实方案/listing、医学采用科学性、B6 authority、aggregate/CAS、runtime、浏览器或商业发布证据。B6 仍 `pending_review`（5 candidates/0 outcomes/2 blockers，`migration_ready=false`、`write_permitted=false`），C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；8911/5174 必须继续停止。下一安全动作仍是授权 B6 reviewer outcome → aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run，之后才可重新申请受控 runtime、独立 AI 评估、三项目真实 LOOP 与浏览器/科学性验收。

## 2026-08-02 LOOP 3.82：P8 assurance 输入形状与项目隔离边界

在 B6 仍 `pending_review`、8911/5174 停止且不得写权威运行库的边界内，保障工作区新增 `medicalMonitoringAssuranceView.mjs`，对任务列表、任务详情、全量重算 proof、核查前三级 rollup 和任务创建回执做严格 project/task/mode/status/version/frozen-identity/evidence shape 校验。malformed collection、跨项目或跨任务身份、缺失九字段 frozen identity、boolean/string 计数和错误 content hash 均 fail-closed；面板在形状错误时清空旧任务/证据状态，不将异常显示为“暂无任务”或完成证据。

验证：assurance view **18 passed**、原 assurance **20 passed**、project-switch isolation **66 passed**、医学监查 **22 个 Node 文件全部通过**、assurance/API + frontend static **48 passed, 1 warning**、frontend/unified-risk/Timeline Python **54 passed**、Vite **1925 modules transformed** 构建成功（仅既有 bundle warning）。详情与 SHA 见 `context/medical_monitoring_assurance_shape_guard_20260802.md`。

该切片只关闭 P8 前端 malformed payload/项目隔离消费缺口，不代表真实 assurance、B6 reviewer outcome、aggregate/CAS、source-token lineage、迁移、浏览器、三项目运行或商业发布门。C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；下一安全顺序仍为授权 B6 outcome → aggregate/CAS 与 source-token revalidation → approved-input 内存 dry-run。

## 2026-08-02 LOOP 3.83：Phase F independent-AI release-gate 证据契约

在 B6 仍 `pending_review`、C13 blocked、8911/5174 停止且不得接入 provider/运行库的边界内，
新增 `services/api/app/monitoring_ai_release_gate.py` 与测试，把说明书 §40.3 的独立 AI
发布条件收敛为一份不可变离线报告：

- 对 `real_project`/`unseen_project` 每个 project×task cell 进一步要求 completed evidence、
  分类守恒和每条 observation 人审，避免 matrix 仅凭一条已审阅记录假装整格通过；
- 引用/定位审阅独立记录 accepted/edited/rejected、错误 locator、跨项目污染和
  unsupported-negative；任何 traceability finding 阻断；
- 六类失败/运行模式（timeout、rate limit、invalid JSON、low confidence、model switch、
  retry）和五个 AI 不可用降级面（原始数据、确定性规则、人工映射、医学处置、批次历史）
  使用闭合集合与 hash-bound evidence；
- prompt/model release 必须绑定 evaluator revision、矩阵 snapshot hash 和同任务 observation
  IDs；candidate 只能 `approval_required`，retired/rolled_back 不可作为可激活输入；
- 报告即使为 `ready_for_controlled_activation`，也固定
  `runtime_activation_permitted=false`、`provider_call_permitted=false`、`write_permitted=false`。

证据：focused **8 passed**；产品 AI 相邻 **631 passed, 17 warnings**；assurance/frontend/
unified-risk/Timeline shared contracts **80 passed**；pycompile、Ruff check/format check
通过。源码 hash `c39de70afb3dddbb979f1aace79ace848e632d3ace92558408c899449e2bd453`，测试 hash
`1303ce5993a33d592ed32cb9bd4fd7194e2036a91318fd0047f589eefad7d41f`。记录见
`context/medical_monitoring_p4_ai_release_gate_20260802_context.md`、
`records/active_slices/medical_monitoring_p4_ai_release_gate_20260802/` 和
`metrics/medical_monitoring_p4_ai_release_gate_20260802_metrics.md`。

该切片只关闭 Phase F 离线 evidence-gate 结构缺口，不代表真实产品 AI、三项目/未见项目
anti-overfit、医学科学性、人审、runtime telemetry、rollback、浏览器或商业发布门；B6
仍为 5 candidates/0 outcomes/2 blockers，C13 仍 schema-only/activation false。下一安全动作
仍为授权 B6 outcome → aggregate replay/source-token revalidation → approved-input 内存 dry-run；
之前不得真实 onboarding、API POST、迁移、dual-write 或服务启动。

收口时还观察到多份医学写作相关源文件（`medical_writing_*`、
`chapter_translation_pipeline.py`、`workbench_inbox.py`、`workbench_notifications.py`、
`writing_reference*`）统一有 **2026-08-02 07:47:25 CST** 新 mtime；它们属于并行变更候选，
本监查切片未编辑、未格式化、未纳入 hash 或语义回归，后续恢复必须先由其独立 handoff/owner
核对，不能把它们视为本轮监查改动。

## 2026-08-02 LOOP 3.84：身份、角色、动作和项目范围离线合同

在 B6 仍 `pending_review`、C13 `activation_allowed=false` 且 8911/5174 停止的边界内，新增
`monitoring_identity_authorization.py`，把说明书 §5.1、§29 的身份/RBAC/最小权限要求落实为
immutable、hashable、fail-closed decision：principal、角色、项目 scope 必须显式；拒绝匿名和
wildcard；医学写作只读/导出；系统管理员只做运行管理；医学经理可直接完成普通医学处置，不默认
“二次医学批准”；高风险处置要求再认证/签名，高风险关闭和规则变更仅医学总监。

focused **9 passed**，相邻风险/能力/AI release contracts **27 passed**，全量
`tests/test_monitoring_*.py` **1579 passed, 25 warnings**（501.42s），Ruff/compileall 通过。
该切片未接认证目录、API middleware/router、SQLite、e-sign provider、provider、浏览器或真实项目，
未修改历史默认 actor，未触碰医学写作。它关闭的是离线权限合同缺口，不是生产认证/RBAC/e-sign
或商业上线证据。下一安全动作仍为重新核对 B6 outcome；在授权前不得把合同接入运行时写入。

## 2026-08-02 LOOP 3.85：身份授权到 append-only 审计链

在 B6 仍 `pending_review`、C13 `activation_allowed=false` 且 8911/5174 停止的边界内，新增
`monitoring_audit_contract.py`，把 principal snapshot、授权 decision hash、角色/动作/项目/目标、
source revision 和 aggregate CAS 版本绑定为不可变 hash-linked 事件链。拒绝动作可被记录但不能声明
mutation；写入事件必须严格 `after=before+1`；错误前驱、ID 重用、payload 改写、session snapshot
漂移和 raw secret 字段均 fail-closed，精确事件可幂等重放。

focused **8 passed**，相邻 **35 passed**，全量 `tests/test_monitoring_*.py` **1587 passed, 25 warnings**
（514.13s），Ruff/compileall 通过。未接审计数据库、事务/恢复、认证/电子签名、API/provider，未
查询或修改现有 18911/18913/15174，未触碰医学写作。该切片只关闭离线审计合同缺口，不代表监管
审计或商业发布完成；下一安全动作仍是 B6 outcome → aggregate/CAS/source-token revalidation。

## 2026-08-02 LOOP 3.86：真实运行表面的医学监查 UI 只读审计

在不越过 B6/C13、不开 8911/5174、不调用 API/provider/SQLite 的前提下，使用现有 15174 Vite
表面完成一次 Codex in-app browser 只读流：项目总看板 → 唯一“医学监查”按钮 → 实际
`/monitoring?...&scope=trial&view=checklist`。项目总看板壳层紧凑清晰，但医学监查真实页面明确显示
`功能未配置`，并说明当前项目没有配置真实来源与执行链路；没有风险队列、个例时间线/患者画像、
中心/项目汇总、图形或风险分级联动。未以零值或静态示例冒充监查结果。

两张截图已保存并检查：`reviews/visual_audits/medical_monitoring_ui_20260802/`；完整记录、
DOM 观察、限制和 P0/P1 问题见 `records/active_slices/medical_monitoring_ui_audit_20260802/`
及 `context/medical_monitoring_ui_audit_20260802_context.md`。结论是 UI/browser **未通过验收**，
且不构成激活授权；键盘、对比度、响应式、读屏、科学性、三项目和 UAT 尚未验证。B6 仍
`pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 activation-blocked；下一安全动作
仍为授权 B6 outcome → aggregate/CAS/source-token revalidation → approved-input dry-run。

## 2026-08-02 LOOP 3.87：参考项目可见性与医学写作隔离运行时边界

复核源码目录、监查注册、稳定启动脚本与当前 18911/18913 进程环境后，确认
`ProjectSourceManifestService` 默认包含八个规范项目，`main.py` 已注册 RUX/MY009 监查适配器；
当前可见运行时却显式设置 `WORKBENCH_INCLUDE_REFERENCE_PROJECTS=false`，这是医学写作隔离
合同。因此 `/api/projects` 仅列用户项目，15174 的监查页显示“功能未配置”，不能据此判定
监查适配器缺失。

稳定后端脚本不强制关闭该开关，说明真实监查浏览器验收必须在单独的 reference-enabled
生产样式运行时进行。改变现有隔离运行时会跨越医学写作边界，也不能替代 B6 reviewer outcome、
source-token lineage、aggregate/CAS 闸门。本切片未改源码、未启动/修改任何服务、未调用 API/
provider、未写 SQLite、未运行真实项目、未触碰并行医学写作；记录见
`records/active_slices/medical_monitoring_reference_visibility_boundary_20260802/`。

## 2026-08-02 LOOP 3.88：MY009 legacy source-token 定点证据探针

按 B6 五条候选的唯一旧 revision `monsrcv_eeceacd52bd0086cd5549448` 做了受限只读查找，
范围仅覆盖 B4/B6 记录、监查 records/reviews、archives、当前 MY009 项目目录与 Trash。
命中内容只有 metadata/recommendation，没有历史 workbook/protocol bytes 或冻结 legacy snapshot。

当前 listing/protocol 的 SHA-256 已重新核对，且此前当前源只读评估得到
`monsrcv_4d371d8c167050747a122931` 与期望的当前 meaning/source token；这只能证明当前 lineage，
不能替代旧版本 source-content revalidation。B6 继续 `pending_review`，不创建 reviewer outcome，
不写 aggregate/CAS/runtime。详细探针证据见
`records/active_slices/medical_monitoring_reference_visibility_boundary_20260802/TEST_EVIDENCE.md`。

## 2026-08-02 LOOP 3.89：MY008 当前源重锚定与 record-level visit 复核

重新核对 MY008 3-02 同一路径后，发现当前 listing 字节已不同：当前 14,989,958 bytes、SHA
`c91193f290c4c7d7a568a0f94a9189e672c788aeac62176f46d105f51fc29703`，旧证据为 15,149,424 bytes、
`152b8c2b...`。当前 fresh parser/classifier 为 59 sheets、82,582 rows、0 warning、PC3 empty、
`raw_full_snapshot_candidate`；旧 precheck/classification hash 不再代表当前文件。

当前 observation records 实际保留 `表单集名称`/`表单集OID`，`SUBJ` 是非访视身份表；此前“多数域没有
显式访视号”的说法过宽，已纠正。但方案表 10 的 D70/D98（对照组）和 V17/提前退出与当前 listing
的 V10=D84、V12=D126、V15=D168、`WITHDRAW` 不一致，且未观察到 D70/D98 label，因此仍不能用
OID 顺序替代 protocol V 编号。详细 evidence 与待审 crosswalk 见
`records/active_slices/medical_monitoring_my008_mapping_review_20260802/`。

本切片只读、未改源码/运行库/API/provider/SQLite/service/browser/真实项目/并行医学写作。B6
仍 `pending_review`，C13/C14 blocked，8911/5174 保持停止；下一步需在授权 B6/source-lineage
之后按当前 hash 做 arm-aware crosswalk 和 precheck replay。

## 2026-08-02 LOOP 3.90：MY008 listing 双副本路径校正

继续做窄范围文件清单核对后，确认 LOOP 3.89 把两个同名/同项目 listing 副本混在了一起：
`原始数据/【3-02初治锁库后数据集】...xlsx` 是 canonical copy，大小/SHA 为
15,149,424 / `152b8c2eb4d398ca2cfd861ee7932942eb753d6494ae7c93a5806734d5ced106`，与历史
classification/precheck 完全一致，fresh parser 为 59 sheets、82,583 rows、0 warning、PC3 empty；
`NDA相关/SAE病例叙述-20250925/...xlsx` 是另一个 byte variant，SHA
`c91193f290c4c7d7a568a0f94a9189e672c788aeac62176f46d105f51fc29703`，不纳入同一 baseline。

因此旧 canonical 证据没有被当前文件系统“改写”；需要做的是 source-copy 选择和 lineage 记录。
record-level visit 字段、D70/D98/V17 与 OID ordinal 冲突的 mapping 阻断不变。详细校正见
`records/active_slices/medical_monitoring_my008_mapping_review_20260802/`；本次仍未改源码/运行库、
未写 API/SQLite、未启动服务/浏览器/provider/真实项目、未触碰医学写作。

## 2026-08-02 LOOP 3.91：离线 protocol→listing visit crosswalk 合同

为 MY008 record-level visit 证据补齐了纯函数、hash-bound 的
`services/api/app/monitoring_visit_crosswalk.py` 与聚焦测试。合同保留 protocol/listing
source SHA、source locator、OID/label、arm scope 和 reviewer binding；required protocol
visit 必须恰有一个 binding，scheduled listing visit 不得未绑定，missing/ambiguous/conflict/
unknown/duplicate、label/arm/hash/locator 错误均 fail-closed。`LABEL_MATCH` 的 OID ordinal
差异只产生显式 review finding，UNS/WITHDRAW/COMMON/non-visit 不得冒充 scheduled visit。
报告固定 `activation_allowed=false`，不授予 onboarding、迁移或运行库写入权。

验证：focused **8 passed**；precheck/B6 activation/source-token 相邻回归 **44 passed**；
py_compile、Ruff format/check 和 workflow review-gate 均通过。首轮 `4 failed, 4 passed` 是测试
夹具解包 dataclass 的局部错误，已修复并重跑通过。该切片未接 runtime/API/provider/SQLite/
browser/真实项目，未修改 B6/C13/C14 或医学写作；B6 仍 `pending_review`、C13/C14 blocked、
8911/5174 保持停止。证据见
`records/active_slices/medical_monitoring_visit_crosswalk_20260802/`。

## 2026-08-02 LOOP 3.92：Checklist 处置标签显示纠偏

代码审查发现 Checklist 的“当前处置”直接显示原始状态码，不符合医学经理首屏简洁、中文重点
优先的要求。现改为复用既有 `riskDispositionStatusLabel`，按 `dispositionState` →
`disposition_state` → `status` 读取显示值；底层原始值、筛选和 API 合同不变。

验证：Python frontend contracts **61 passed**；医学监查 Node contracts **22 个测试文件通过**；
Vite **1925 modules transformed**、构建成功；workflow review-gate 通过。未启动浏览器/服务，未
改 `App.jsx`/`styles.css`、API/SQLite/provider、B6/C13/C14、真实项目或医学写作；8911/5174 保持
停止。该切片只改善显示层，不改变真实 runtime、三项目科学性或商业发布门。证据见
`records/active_slices/medical_monitoring_checklist_disposition_labels_20260802/`。

## 2026-08-02 LOOP 3.93：个例风险卡来源追溯纠偏

### 观察

对既有 Timeline/Profile/AE 风险模型做静态合同复核时，发现
`referenceRiskCards()` 曾把 `说明书/IB：感染/实验室风险` 作为固定文字拼到所有选中 AE 上，
即使当前 profile 没有 IB/说明书或安全主题证据。这会把展示层的通用卡片误变成项目安全结论。

### 修正

- 风险卡现在只显示 AE 明确的标题、详情、严重程度、相关性、转归、临床解释、日期、访视、
  来源记录/定位；提示只显示显式 prompt 文本、建议、状态和定位。
- 安全性主题/依据只在 AE 或 prompt 显式提供 `safety_topic`/`safety_reference`/`safety_basis`/
  `evidence_summary` 时显示。
- 实验室证据仅接受 AE event ID/linked ID 或共同 risk ID 的显式关联；同访视不会被自动当作关联。
  对象型 locator 以可读键值展示，不再退化为 `[object Object]`。
- 无 CM/PD 证据时改用“未提供证据，暂不能判定”的中性空态，不把缺数据写成规则命中。

### 验证与边界

focused model、医学监查 22 个 Node 文件、Python frontend contracts 61/61、Vite 1925 modules
均通过，review-gate 通过。未启动服务/浏览器/provider，未写 SQLite，未触碰 `App.jsx`、
`styles.css`、B6/C13/C14、真实项目或医学写作；8911/5174 保持停止。此修正不等于 protocol/IB/
CTCAE 科学性或商业发布验收。证据位于
`records/active_slices/medical_monitoring_subject_risk_card_source_grounding_20260802/`。

## 2026-08-02 LOOP 3.95：MY008 PNH 2-03 两批真实 listing 重验证

当前文件系统中，两份 MY008 PNH 2-03 listing 已重新找到并只读重放：2025-04-17 与 2025-12-02。
SHA-256 与 P2 历史 evidence 完全一致；当前 parser/classifier 两批均 33 sheets、32 domains、
0 warnings、`raw_full_snapshot_candidate`。规范化 identity/diff 使用当前版本化引擎重算，得到新增
25,156、变更 1,258、持续 7,401、删除 40、字段变化 5,295、schema diff 0，与历史 P2 counts 一致。

这使 MY008 PNH 2-03 成为一个具备当前字节锚点和可重放两批 diff 的 P2 证据候选；但
`full_snapshot_proven` 仍沿用既有冻结 Source Registry 断言，本切片没有重新签署或修改来源台账。
MY008 3-01 第三泛化项目、MY009/RUX 连续批次、B6 reviewer outcomes、aggregate/CAS/source-token、
风险迁移、独立 AI、runtime、浏览器/科学性/UAT 和商业发布仍未完成。

记录见 `records/active_slices/medical_monitoring_my008_p2_two_snapshot_revalidation_20260802/`。
本切片未启动服务/provider/browser/8911/5174，未写 SQLite/API/runtime，未触碰 App/styles 或医学写作。

## 2026-08-02 LOOP 3.96：RUX/MY009 候选来源资格重验证

为继续推进 P2 而不越过 B6，对当前文件系统中 12 个 RUX/MY009 workbook 候选进行只读重验证。
RUX 2025-04-16 及历史医学监查附件被分类为 `processed_full_snapshot` 或
`mixed_monitoring_workbook`；RUX 2025-06-12 原始文件被分类为
`raw_snapshot_with_format_defect`，两个处理后副本被分类为 `processed_full_snapshot`；MY009
2026-04-08 为 `restored_transitional`，2026-03-04 为 `comparison_workbook`。

本轮没有发现 provenance-complete 的 RUX/MY009 双原始全量快照，因此没有升级 P2、没有创建
baseline 或 diff activation。RUX 2025-04-16→2025-06-12 仍可在未来 approved-input/隔离环境
做诊断 diff，但必须保留“处理后历史基线 + 当前 raw dimension defect”的来源风险；MY009 当前候选
范围没有第二个原始全量快照。聚焦分类测试 8 passed、py_compile 通过、workflow review-gate
`ok:true`。未写 source registry/API/SQLite/runtime，未启动服务/provider/browser/真实项目，未改
App/styles 或医学写作；8911/5174 继续停止。

证据见 `records/active_slices/medical_monitoring_rux_candidate_source_revalidation_20260802/`。

## 2026-08-02 LOOP 3.97：医学写作并行保护面 metadata checkpoint

为处理发布总账中保护状态仍为 partial 的未报告 07:47:25 mtime cohort，按当前
filesystem 做了窄范围只读 inventory：精确 cohort 66 files，26 code/test surfaces，
40 records/handoffs/run surfaces；sorted path-list SHA-256 为
`ae32ae1f43b4af2c3728d3a6a8a7812d0faa2d3722eae99d3b99d77cea585280`。其中 22 个
medical-writing/shared source surfaces 和 5 个 supporting QC/test surfaces 的
bytes/mtime/SHA-256 详见
`records/active_slices/medical_monitoring_protected_surface_inventory_20260802/TASK_RECORD.md`。

本切片只读取 metadata 和 hash，不读取医学写作 source semantics，不比较 stale
baseline，不判断 owner/authorization，不修改产品源码、医学写作、App/styles、
运行库或任何服务。没有运行测试、provider、API、SQLite、browser 或真实项目；
8911/5174 继续停止，18911/PID 43191 未触碰。review-gate `ok=true`、warnings/errors
均为空。

该记录只能建立可复核的 metadata checkpoint，不能清除并行写作 owner/handoff gap；
发布总账的医学写作保护仍为 partial。后续恢复必须先取得独立 writing-lane owner
确认，再继续监查工作。B6/C13 仍 `pending_review`/read-only，正式 B6 outcome、
aggregate/CAS replay 和 legacy source-token revalidation 的顺序不变。

## 2026-08-02 LOOP 3.98：发布总账旧 mtime 引用校正

复核当前 `RELEASE_GATE_AUDIT_20260802.md` 时发现其中仍保留旧的 `04:25:18` cohort
描述。对当前 filesystem 的精确窗口只读核对结果为 **0 files**；实际存在并已由 LOOP
3.97 固化的是 `2026-08-02 07:47:25 +0800` 的 66-file cohort。故只校正 evidence
ledger 的引用和判定：医学写作保护仍为 **partial**，因为 owner/handoff 尚未确认，
不能把旧 cohort 消失解释为授权完成。

本校正只修改 `RELEASE_GATE_AUDIT_20260802.md` 的证据行和索引；没有修改产品源码、
医学写作、App/styles、运行库、B6/C13 或服务。没有运行测试/provider/API/SQLite/
browser/真实项目；8911/5174 继续停止，下一安全顺序不变。

## 2026-08-02 LOOP 3.99：商业发布证据覆盖报告

为把商业发布 dossier 从“已有叙述”推进到“可重放的当前判定”，新增只读证据切片
`records/active_slices/medical_monitoring_release_evidence_coverage_20260802/`。报告读取当前
发布审计、B6 review gate、C14 B6→C13 gate，并按 16 个 canonical gate 绑定唯一 evidence ID
与发布审计 SHA-256；它不生成 reviewer outcome，也不授予写入或医学批准权限。

当前结果：16 门 `passed=0`、`partial=12`、`unproven=3`、`blocked=1`；B6
`pending_review`、5 candidates、0 outcomes、`migration_ready=false`、`write_permitted=false`、
`migration_write_permitted=false`。纯函数重放为 `status=blocked`、`release_ready=false`，
decision SHA `442e59a67df85187e73b0b9739164cad3678b6e9443b40ef7b848fd29c7e3229`。

验证：release-gate focused **7 passed**、py_compile 通过、JSON/source-hash/decision replay
通过、Hermes review-gate `ok=true` 且无 warnings/errors。本切片未启动服务、浏览器、provider、
API、SQLite、migration、adapter 或真实项目，未改 `App.jsx`/`styles.css`、医学写作、B6/C13
或运行库；8911/5174 保持停止。下一安全顺序仍为真实 B6 reviewer outcomes → aggregate/CAS/restart
与 MY009 legacy source-token revalidation → approved-input dry-run → 三项目真实科学性/浏览器/UAT。

## 2026-08-02 LOOP 4.00：Timeline 实际日期证据覆盖守卫

从资深医学监查员的“少点击、视觉敏感、数据敏感、风险敏感”视角复核 Timeline 后，发现旧的
`ReferenceTimelineSvg` 在没有可用日期时会用 `Date.now()` 形成视觉轴；混合数据时，无日期事件也
会被放在回退位置，容易被读成真实时间窗或先后关系。该问题属于数据呈现完整性风险，不是装饰性优化。

本切片新增严格的 `hasActualTimelineDate` 和只读 `timelineDataCoverage`：只有完整且日历有效的
`YYYY-MM-DD` 可进入图形坐标；计划日、研究日、访视编号、部分日期和无效日期均不替代实际日期。
无日期时图形轴明确停用；混合数据只绘制有日期证据的访视/事件，缺失记录仍在来源明细中，并显示
“不作时间窗或先后结论”的警示。`dateAtStudyDay` 也拒绝无效基线日期，避免在旁路生成错误日期。

验证：医学监查 Node **22/22 个测试文件通过**；Timeline/统一风险/安全投影 Python 前端合同
**41 passed**；Vite **1925 modules transformed** 构建成功，保留既有 chunk warning；workflow
review-gate `ok=true` 且无 warnings/errors。保护哈希仍为 `App.jsx` `3346d945...c9f61`、
`styles.css` `f7020f...05479`；B6 `pending_review`、C14 `activation_allowed=false`；8911/5174
无监听。

本切片未启动服务、provider、API、SQLite、browser、adapter 或真实项目，未触碰医学写作、
`App.jsx`/`styles.css`、B6/C13/C14。该切片只关闭前端时间轴的日期证据失真风险，不把离线测试
冒充真实浏览器/科学性/UAT 或商业发布证据。下一安全顺序仍为正式 B6 reviewer outcomes →
aggregate/CAS replay → MY009 legacy source-token revalidation → approved-input dry-run →
reference-enabled runtime 与三项目真实 LOOP。

## 2026-08-02 LOOP 4.01：风险清单键盘与选中语义

从“少点击但风险敏感”的资深医学监查员视角复核 Risk Checklist：行已有鼠标/键盘选择路径，但没有
明确的选中语义和可读上下文，Space 还会触发浏览器默认滚动。对一张高密度风险表而言，这会增加聚焦
误差和重复操作。

本切片新增 `riskRowAccessibleLabel`，仅由当前行已显示的受试者、中心、级别、类别、风险标题、当前处置
和未读字段组成，并复用既有 severity/category/disposition 标签；每行增加 `aria-selected`、`aria-label`。
Enter/Space 仍调用原 `onSelect`，同时 `preventDefault()` 防止 Space 滚动。未改风险数据、查询、排序、
筛选、分页、导出、权限或医学判断。

验证：统一风险/监查/安全投影 Python 前端合同 **44 passed**；医学监查 Node **22/22 个测试文件通过**；
Vite **1925 modules transformed** 构建成功，既有大 chunk warning 保留；workflow review-gate `ok=true`。
8911/5174 无监听，B6/C14 仍 `pending_review`/`blocked_pending_b6_review`，`App.jsx`/`styles.css` 保护哈希
未变。本切片未启动服务、provider、API、SQLite、browser、真实项目或医学写作；浏览器级焦点和视觉验收仍须
未来授权 reference-enabled runtime。

该切片只完成清单操作语义的离线改进，不把静态合同冒充真实用户验收或商业发布。下一安全顺序仍是
B6 reviewer outcomes → aggregate/CAS replay → MY009 legacy source-token revalidation → approved-input
dry-run → reference-enabled runtime 与三项目真实 LOOP。

## 2026-08-02 LOOP 4.02：Patient Profile 数值形状守卫

复核 Patient Profile 趋势图时发现，非数值、`null`、`NaN` 或缺少完整实际评估日期的测量点直接进入 `Math.min` 和 SVG 几何，
可能形成 NaN 坐标或外观完整但不可解释的假趋势。对数据敏感和风险敏感的医学监查员，这比显示一个明确
“不可绘制”状态更危险。

本切片新增 `metricDataCoverage`，仅同时具备有限数值 `point.value` 与完整、日历有效 `YYYY-MM-DD`
实际 `assessment_date` 的点参与图形；不把数值字符串、缺失值、部分/月/年日期或其他类型强制转换为临床测量或时间轴。
不可绘制原始点继续保留在明细列表，显示“数值未提供”或“日期未提供”；完全没有可绘制点时，不输出 SVG，
而显示“暂无可绘制”并保留下方原始明细。风险标记、参考范围、基线规则、临床解释和 API 数据均未改变。

验证：Subject model tests 通过；Timeline/统一风险/安全投影 Python 前端合同 **42 passed**；医学监查 Node
**22/22 个测试文件通过**；Vite **1925 modules transformed** 构建成功，既有 chunk warning 保留；workflow
review-gate `ok=true`。8911/5174 无监听，B6/C14 仍只读阻断。本切片未启动 service/provider/API/SQLite/browser/
真实项目，未触碰 `App.jsx`/`styles.css` 或医学写作。

经 bounded source audit，MG-K10/RUX/MY009 legacy trend builders 对保留趋势点使用 day-level ISO 日期；独立 C5 consumer contract 允许 month/year 精度，当前日轴有意将其保留为明细而非虚构日点。该切片只关闭 Profile 图形的数值/时间形状风险，不把离线测试冒充真实指标科学性、浏览器/UAT 或商业发布证据。

## 2026-08-02 LOOP 4.03：风险清单非零报告空态守卫

复核风险清单时发现，若接口报告总数大于 0、但当前页经安全形状过滤后没有可展示行，旧的普通空态会把分页漂移、数据形状异常或当前快照问题误读成“没有风险”。这对懒惰且风险敏感的医学监查员尤其危险。

本切片在 `MedicalMonitoringRiskChecklist` 增加 `hasReportedRowsButNoSafeRows` 分支：非零 `safeTotal` 且 `safeRows` 为空时，以 `role=alert` 明确说明“不能据此判定无风险”，并提示刷新或检查快照/数据形状；真实零总数仍显示原有克制空态，loading/error/stale snapshot 行为不变。未修复或推断任何风险数据，也未改 API、分页、处置、来源证据、`App.jsx` 或 `styles.css`。

验证：Timeline/统一风险/安全投影前端合同 **42 passed**；医学监查 Node **22/22 个测试文件通过**；Vite **1925 modules transformed** 构建成功；workflow review-gate `ok=true`。8911/5174 无监听，B6/C13/C14 继续 blocked/read-only，未启动服务/provider/API/SQLite/browser/真实项目，未触碰医学写作。

本切片只关闭“非零报告被当作无风险”的显示歧义，不是 API 分页或真实风险库验收。下一顺序仍为正式 B6 outcomes → aggregate/CAS replay → source-token revalidation → approved-input dry-run → reference-enabled runtime 与三项目真实 LOOP。

## 2026-08-02 LOOP 4.04：Patient Profile 指标可用性空态语义

原有 Patient Profile 在疗效/安全性指标为空时显示“等待生成”，无法区分个例资料尚未载入、字段映射受限、来源域明确缺失和普通未提供；资深医学监查员可能因此重复等待，或把空态误读为稳定/无风险。

本切片新增 `profileMetricEmptyStateMessage`，仅使用现有 `rawProfile.capability_mode`、`domain_availability` 和指标数组状态，输出未载入、受限、来源未提供或普通未提供的说明，并明确“空态不代表疗效稳定或安全性无风险”；指标存在时不改变任何图表、风险、阈值或参考范围。未改 `App.jsx`/`styles.css`、API、运行库、B6/C13、浏览器或医学写作。

验证：Subject model tests 通过；Timeline/统一风险/安全投影前端合同 **42 passed**；医学监查 Node **22/22 个测试文件通过**；Vite **1925 modules transformed** 构建成功；workflow review-gate `ok=true`。8911/5174 无监听，B6/C14 继续 blocked/read-only。

本切片只关闭 Profile 空态语义歧义，不是来源能力、科学性、浏览器/UAT 或商业发布证据。下一顺序仍为正式 B6 outcomes → aggregate/CAS replay → source-token revalidation → approved-input dry-run → reference-enabled runtime 与三项目真实 LOOP。

## 2026-08-02 LOOP 4.05：商业发布覆盖报告重绑当前审计哈希

4.00–4.04 更新了 `RELEASE_GATE_AUDIT_20260802.md` 的证据索引，发现 3.99 覆盖报告仍绑定旧 audit SHA。已只读重放并重绑
`CURRENT_RELEASE_COVERAGE.json`：当前 audit SHA 为
`d246ba57cac0aa4dc4bcc2cd456282ddb330db4a057d20311b600ec816bcf17a`，decision SHA 为
`384bca2b068ca1b481f6557fc9f10198cec1530c88fc89df91c1b82fe6b74c05`；16 门状态仍为 `passed=0`、`partial=12`、`unproven=3`、`blocked=1`，总判定仍 `blocked/release_ready=false`。

coverage JSON/source hash/evaluator replay 通过，release-gate focused **7 passed**。没有启动 service/provider/API/SQLite/browser/真实项目，8911/5174 无监听，未授予 B6/C13 或任何写入权限。本动作只修复证据索引一致性，不改变发布门状态。
下一安全顺序仍为 B6 reviewer outcomes → aggregate/CAS replay → MY009 legacy source-token revalidation →
approved-input dry-run → reference-enabled runtime 与三项目真实 LOOP。
