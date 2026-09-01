# P8 锁库前与核查前后端实施合同

日期：2026-07-29  
风险：高  
目标：在不复制风险、不写真实项目运行库的前提下，实现锁库前全量医学监查与核查前三级总结性自查的可恢复产品后端。

## 权威来源

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` 第 8.3、8.4、11、12、13 章。
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` P8。
- `context/monitoring_p7d_real_evidence_matrix_20260729.md`。
- 当前 `monitoring_batch_repository.py`、`monitoring_daily_run_repository.py`、
  `medical_risk_repository.py`、`medical_monitoring_summary.py`、处置投影与方案规则仓库。

## 不可退让边界

1. 任务模式由用户显式选择：`pre_lock` 或 `pre_inspection`，不能从文件名推断。
2. 只引用同一权威原始 listing 批次、active mapping、方案/规则、字典/CTCAE/模型修订；
   不复制或重写医学风险。
3. 锁库前必须记录全量重算证明；不能拿日常增量缓存或现有风险清单冒充。
4. 前置条件不足允许保存 draft，但不得进入全量复核完成。
5. 核查前三级汇总必须从同一钉住风险快照计算，受试者→中心→试验计数逐层可对账，
   每个汇总可回到风险实例。
6. 中心聚集只保存分子、分母、缺失率、方法和样本量判断。无项目批准方法或样本量不足时
   只作描述性，不输出“中心异常/违规”。
7. Safety/PV 是附加维度；CM 与 EX/EC/DA/IP 边界继续强制。
8. 医学经理确认当前项目内容后即为当前医学记录，不新增“待医学批准”。
9. 不修改医学写作、共享独立 AI 配置、P7 字段映射/规则逻辑、前端或真实运行数据库。

## 建议模型与状态

建立独立 SQLite 仓库和服务（文件名可在既有规范内调整）：

- `MonitoringAssuranceTask`
  - task_id, project_id, mode, status, version
  - frozen batch/mapping/protocol/rule/dictionary/ctcae/model/risk snapshot identities
  - created/updated/confirmed actor/time
- 状态：`draft` → `ready` → `full_recompute_recorded` → `medical_review`
  → `ready_to_complete` → `completed`；以及 `superseded`。
- 任一冻结身份变化关闭原任务的继续执行资格，必须新建任务。

锁库前全量重算证明至少包括：

- 计划/实际受试者、中心、关键域、规则数量；
- 逐域计划/处理行数；
- 失败、跳过、重试；
- 新生成且钉住的风险快照；
- 风险明细与受试者/中心/试验汇总对账；
- 开放高风险、全部开放项、已关闭但证据不足项、负责人和锁库影响判断。

核查前输出：

- subject rollup、site rollup、trial rollup；
- category/severity/disposition/Safety-PV 分布；
- 所有 rollup 的风险实例 ID；
- 中心描述性分子、分母、缺失数/率；项目未提供批准方法时 signal_status =
  `descriptive_only`；
- 整改状态矩阵和证据包 manifest（只引用，不复制原始证据）。

## API

在医学监查模块下提供最小正式产品路径：

- 创建任务；
- 获取/列表任务；
- 评估 readiness；
- 记录全量重算证明；
- 生成/读取三级汇总；
- 记录医学复核结论；
- 完成任务。

全部写操作使用 expected_version/CAS 与 idempotency key；跨项目访问 404；状态不允许 409；
请求 extra forbid；响应不暴露本地路径或内部哈希日志。

## 验收

- 临时 SQLite 的迁移/重启幂等。
- draft 可保存但 readiness 不通过时不能完成。
- 冻结身份漂移关闭失败。
- 全量重算证明缺任何关键覆盖或存在失败/跳过时不能完成。
- 三层风险总数和实例集合严格一致。
- 关闭风险无可验证处置/证据时在 readiness 中显式出现。
- 中心无批准方法或样本不足时只描述，不定性。
- CM 与试验药物风险在分类/汇总中保持独立。
- 聚焦、相邻医学监查测试和 Python 编译通过。
- 不重启当前 8921 API，不触碰真实 DB；真实运行态留到旧 V7 队列排空后。
