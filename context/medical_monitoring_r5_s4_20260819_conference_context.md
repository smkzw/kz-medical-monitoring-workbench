# Conference Context: medical_monitoring_r5_s4_20260819

Created: 2026-08-19 06:01:06
Objective: 冻结并实现R5-S4 Risk Inspector与多模型证据归并的synthetic/offline renderer-neutral合同和runtime
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route, then Codex subAgent Luna (max). The Codex subAgent route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is night Pi/Alibaba `qwen3.8-max` (xhigh) -> Codex subAgent `gpt-5.6-luna` (max), and day Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `gpt-5.6-luna` (max) -> Kimi Code `k3-256k` (high). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，尤其 §9、§10、§12、§17。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，尤其 R5 当前停止点与 S4 顺序。
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`，尤其 §6、§10.1、§11、§13–§15、S4 Done。
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json` 中 `R5RiskInspectorProjection`、closed enums、field mappings 与 invariants。
- R4 只读 public authority：`poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble_contracts.py`、`ensemble.py`、`d10_contracts.py`、`d10_projection.py`。
- 已接受 R5 只读基座：`poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_contracts.py`、`s2_authority_builder.py`、`s2_thin_slice.py`、`s3_contracts.py`、`s3_projection.py`。
- 接受边界：`context/medical_monitoring_r5_s2_acceptance_record_20260818.md`、`medical_monitoring_r5_s3_contract_acceptance_record_20260819.md`、`medical_monitoring_r5_s3_acceptance_record_20260819.md`。
- 当前文件系统与接受记录内 SHA 是最终真相；外部 Agent 输出仅为建议/审查证据。

## Scope

- In scope：冻结 R5-S4 synthetic/offline、renderer-neutral Risk Inspector 实施合同；精确 typed packet/projection、上游逐叶 authority mapping、canonical hash/receipt、0/1/N、基座来源回查、原始模型输出、确定性验证、冲突关系、独立裁决、正反证、来源、三分句 Query 草稿与历史引用、普通用户中文投影、挑战 registry/oracle/verifier/test 及实施写入边界。
- Out of scope：S4 runtime 实现、UI/浏览器/前端、8911、真实项目/模型/API、医学写作、产品服务、生产、安全专项、临床风险重算、Query 发送/回复/关闭/待办。

## Success Criteria

- 两名 participant 分别独立返回可审计的合同方案/对抗报告；不互读输出。
- 合同闭合 exact keys/type/cardinality/nullability/closed enums、跨对象 invariants、逐叶真实 source path/join recipe、deferred 诚实边界与固定错误码。
- 机械覆盖 0/1/N、同题同输入版本/隔离上下文、单模型不得伪造一致性、baseline source recheck、raw output immutable、worker≠adjudicator、高风险/相互否定/baseline miss 不可隐藏、证据篡改 fail-closed。
- 普通受众只用中文临床表达：分析一/分析二/独立核对；provider/model/attempt/hash 仅审计层；不得出现正式事实/候选信号/只读xx/待办等研发或任务化标签。
- 冻结 generator/verifier/artifact-set/pins/normal+O2/challenge tests 与首尾 SHA 门禁；任何 P0–P4 均阻断。
- 只允许合同工件路径写入；R4、既有 R5 S1–S3、前端、医学写作与真实项目字节不变；8911 全程停止。
- fresh isolated reviewer 对唯一稳定 SHA 组返回 `ACCEPT_R5_S4_CONTRACT` 后，才解锁 S4 runtime。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- 不把 `ReferenceBaseline` 当金标准，不以多数票代替来源证据，不允许单模型输出被标为“多个分析结果一致”。
- S4 只适配 R4 已接受事实/风险/Query/ensemble/D10 ModelEvidence；不得在 R5 新算医学风险、严重度、分子分母或裁决。
- 高风险、mutual negation、baseline miss、重要低置信度/验证失败必须持续可见；独立裁决只能增加解释，不能删除风险。
- 8911 仅计划 S7 临时启动；本会商和 S4 合同阶段必须保持停止。

## Loop Log

- 2026-08-19 06:01:06: Conference initialized by `hermes_workflow_guard.py init-conference`.
