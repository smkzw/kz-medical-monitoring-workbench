# Task Context: monitoring_p8_assurance_backend_20260729

Created: 2026-07-29 23:46:51
Objective: 实现医学监查P8锁库前/核查前后端，含冻结身份、CAS幂等状态机、readiness、全量重算证明、三级rollup与临时SQLite验收
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p8_assurance_backend_context.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书.md` 第 8.3、8.4、11、12、13 章
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` P8
- `context/monitoring_p7d_real_evidence_matrix_20260729.md`
- 当前 `monitoring_batch_repository.py`、`monitoring_daily_run_repository.py`、
  `medical_risk_repository.py`、`medical_monitoring_summary.py`、处置投影及方案规则仓库合同
- 用户本轮明确要求，优先级高于历史记录

## Scope

- In scope:
  - 新建 `monitoring_assurance_repository.py`、`monitoring_assurance_service.py`、
    `monitoring_assurance_router.py`（可按项目既有命名规范微调）
  - `services/api/app/main.py` 最小依赖注入与 `include_router`
  - 医学监查专用测试
  - handoff/review/metrics 记录
- Out of scope:
  - `frontend/`
  - 医学写作
  - shared AI / 独立 AI 配置
  - P7 字段映射、规则计算、风险仓库模型
  - 真实 runtime DB
  - 当前 8921 API 进程

## Success Criteria

- 显式支持 `pre_lock` 和 `pre_inspection`，不得从文件名推断。
- 冻结 batch/mapping/protocol/rule/dictionary/ctcae/model/risk snapshot 身份；
  任一身份漂移后原任务不能继续。
- 全部写操作使用 expected_version/CAS 和 idempotency key，重启后可恢复。
- readiness 不足允许保存 draft，但不得完成。
- 锁库前全量重算证明覆盖计划/实际受试者、中心、关键域、规则、逐域行数、
  失败/跳过/重试、钉住的新风险快照、三级对账、开放/关闭依据、负责人和锁库影响。
- 核查前从同一风险快照生成受试者/中心/试验三级 rollup 与整改/证据 manifest，
  只引用风险和证据，不复制。
- 中心聚集无项目批准方法或样本不足时只输出 `descriptive_only`，
  不输出“异常/违规”定性。
- Safety/PV 为附加维度；CM 与 EX/EC/DA/IP 继续保持独立。
- 跨项目访问 404、状态冲突 409、请求 `extra="forbid"`；
  公共响应不暴露本地路径、内部日志或敏感内部哈希。
- 临时 SQLite 迁移/重启/漂移/缺口/三级一致性/CM-IP 边界测试通过。
- 聚焦测试、相邻医学监查回归和 Python 编译通过。

## Risk Boundaries

- 只允许写 Scope 明列的文件；共享工作区直接编辑，但不得修改真实运行库。
- 不重启当前 API。
- 不以日常增量缓存或现有风险清单冒充锁库前全量重算证明。
- 不复制或重写风险事实；只保存冻结身份、引用、聚合与执行证明。
- 医学经理对当前项目内容作出确认即为当前医学记录，不新增第二次“待医学批准”。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 23:46:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 23:49:00: Codex 补全权威来源、允许写范围、验收门和禁止边界。
