# Conference Context: medical_monitoring_r4_d02_cm_contract_20260811

Created: 2026-08-11 08:31:27
Objective: Freeze and independently review the isolated synthetic R4-D02 CM medication rationale, indication, prohibited/restricted medication coverage contract and implementation boundary without touching product, medical-writing, real-project, or frozen R1-R3 files
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R4 步骤 1-13。
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`，状态 `FROZEN_R4_CONTRACT_V1`，SHA-256 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`。
- 已接受 R4-D01 最终快照：`poc/medical_monitoring_ai_native_r4/`，cache-excluded 摘要 `f100a0344db27f1d6e404a8b1fdd88a849dd43e5f0996a2e9e609b1c42546550`。
- 本轮待冻结草案：`reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`。
- 冻结 R1/R2/R3 公共合同只读；真实项目、产品源码和医学写作子系统不在读写范围。

## Scope

- In scope：D02 CM 用药合理性、适应证、禁限用药、CM→AE/MH 证据共享、Query/journey 投影和公共生命周期输入边界的合同审阅。
- Out of scope：代码实现、产品/R5、真实项目、真实词典/provider、系统安全、正式 PD 报送、医学写作。
- 允许写入：本任务 `context/plans/prompts/runs/reviews/metrics/logs`；参与者只读，不编辑草案。

## Success Criteria

- 两位独立复核者逐项挑战 L1 dispositions、复方拆分、J07/活疫苗反例、时间端点、适应证缺失、CM/IP 分层、风险身份、D02→D01 共享和 Query/旅程边界。
- 每个 VETO 给出具体合同段落、反例和可实施修订；区分缺陷、需要用户决策的医学分叉和合成切片限制。
- 正确记录 Agent/provider/model/session/工具与 fallback；参与者不互读输出。
- Codex 逐项裁决并将草案冻结为可执行 D02 合同后才初始化代码执行包。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- 不改 R4 源码、冻结 R1-R3、产品、医学写作或真实项目；不启动服务/8911；不做安全设计/测试。
- 不从药名猜成分/类别，不把模型输出当权威药物身份，不正式判定 PD。
- 不因复核者一致就自动接受；Codex 对本地权威和实际合同文本拥有最终裁决权。

## Loop Log

- 2026-08-11 08:31:27: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-11: R4-D01 完成独立验收后进入 D02；Codex依据冻结共同矩阵和已接受公共合同形成 v1.0-draft，等待独立医学/工程反证。
- 2026-08-11: 医学参与者 declared `pi/alibaba/qwen3.8-max:xhigh`，北京日间 effective `pi/cms-smk/cms-model:high`，session `019fee42-0121-7000-8f86-d7ed22f72e7c`，首轮 `ACCEPT_WITH_GAPS`；指出适应证 subtype 重叠、boundary/not_evaluable 角色冲突、笼统适应证、缺失用户标签及 priority/Query/跨域边界缺口。
- 2026-08-11: 工程参与者 Grok session `ae34e41d-6171-48a3-9528-90c09081344d` 首轮被 runtime cancelled，仅有过程文字，不计结论；同会话 round 2 完成并 `VETO`，指出 stable_core/lineage 混写、生命周期仍依赖 D01 类型、复方 unresolved component 可能不进 expected-set、cm_indication 跨域所有权未冻结。
- 2026-08-11: Codex 对照冻结矩阵和 D01 公共面裁决，形成 `v1.1-rc1 / REVISION_1_PENDING_DELTA_REVIEW`：冻结结构协议、中性 identity surface、两层身份、复方 expected-set、适应证 precedence、边界优先、上位类别粒度、版本化 priority、CrossDomainEvidenceRef、Query/旅程字段及挑战 19-30。
- 2026-08-11: 工程同会话 delta 为 `ACCEPT_WITH_GAPS`，确认 I-1-I-10 关闭并给出 G1-G6；医学 delta 为 `ACCEPT_WITH_GAPS`。Codex 已逐项并入 G1-G6 和医学唯一措辞项。
- 2026-08-11: 医学日间重写产生的 effective CMS session `019fee4e-e04e-7000-aa56-77ee0905f942` 在同会话终末核对最终 `ACCEPT`；Grok session `ae34e41d-6171-48a3-9528-90c09081344d` 保留工程 `ACCEPT_WITH_GAPS`，其全部 gap 已由 Codex逐项闭合。
- 2026-08-11: 合同冻结为 `FROZEN_R4_D02_CONTRACT_V1`，SHA-256 `adf6150ecb25886ac4f31123cc639ad13c3530812bfe1607958b9d68e68e4cd7`；共同矩阵和已接受 D01 摘要未变，8911 无监听。下一步先串行公共结构协议适配，再实现 D02-owned 文件；尚未开始源码实现。
