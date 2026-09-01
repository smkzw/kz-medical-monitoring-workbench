# 执行成员合同：真实 652 项竞品分诊吞吐决策

你是 Hermes/aishuo/cms-model 的有限代码审阅执行成员。完整读取最新全局
`/Users/smkzw/.codex/AGENTS.md`，并以当前工作区文件为事实来源。

Runner-managed output file:
`runs/execution/mw_triage_throughput_20260727/worker_aishuo_throughput_decision_01.md`

不要通过工具自行写上述 runner 输出；最终响应返回完整报告，由 runner 持久化。

## Read these files

- `context/mw_triage_throughput_20260727_context.md`
- `runs/execution/mw_triage_throughput_20260727/evidence/real_ra_652_reduction.json`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage.py`
- `records/handoffs/codex_retake_20260726/NO_LOSS_PAUSE_20260727_0952.md`

## Hard boundaries

- 本轮只读，不修改产品代码、测试、数据库、语料库、运行配置或任务记录。
- 不调用产品独立 AI，不创建分诊 run，不替代 Codex 做上线判断。
- 不做安全、后门、渗透或无关工程审计。
- 不重新遍历已通过的 Word、前端、OCR、翻译或独立 AI 路由。
- 只判断当前 652 项分诊吞吐门是否需要代码修复。

## Required analysis

1. 核对 652 项真实重放证据是否证明：
   - 完整且无重叠的确定性/AI 分区；
   - 确定性排除未扩大到适应症、分期、机制等医学判断；
   - 90 个 AI 候选、18 个 5 项批次、最大 7,208 字符符合当前保守合同；
   - 395 项聚焦回归是否足以覆盖失败重试、部分失败、取消、claim ownership、
     progress、route identity 和重启恢复。
2. 基于已有真实 Qwen 结构化探针约 3.6 秒响应，只做工程估算：
   - 18 批串行的合理完成时间区间；
   - 该时长在用户手动触发、前端可显示批次进度的竞品 Protocol/SAP 调研步骤中，
     是否达到“可上线候选”而无需现在引入并发。
3. 批判性比较两个方向：
   - 保持当前串行、通过当前 durable chunk 逐批保存；
   - 在同一 job 内增加有界并发。
   必须具体指出并发对 claim lease、取消、逐块保存、重试仅失败批次、provider
   限流、输出顺序和故障恢复的新增风险。
4. 只给一个明确结论：
   - `ACCEPT_CURRENT_SERIAL_FOR_RELEASE_ROUND`，或
   - `REPAIR_REQUIRED_BEFORE_RELEASE_ROUND`。
5. 若选择修复，给出单一路径的最小补丁合同、写集、测试和回滚；若不修复，
   明确把真实端到端运行中哪些时延/失败信号设为触发并发优化的后续阈值。

## Report schema

- Sources read
- Evidence checked
- Conflicts or defects
- Decision marker
- Release-round acceptance conditions
- Residual risk and trigger thresholds
- No-write confirmation

不要根据主观“并发更快”直接要求改造。医学召回、确定性来源边界、耐久恢复和
当前用户体验同等重要。
