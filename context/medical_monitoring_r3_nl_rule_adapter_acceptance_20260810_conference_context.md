# Conference Context: medical_monitoring_r3_nl_rule_adapter_acceptance_20260810

Created: 2026-08-10 18:47:05
Objective: 独立验收医学监查 R3 中文自然语言规则适配器：功能正确性、R1-R3身份闭环、候选隔离、中文原生作用范围与冻结边界；不做安全性设计测试，不运行真实项目或服务
Task type: `complex_delivery_conference`
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

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（R3 与自然语言规则相关条款）。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（R3 步骤与当前恢复点）。
- `context/medical_monitoring_r3_nl_rule_adapter_20260810_context.md`。
- `reviews/medical_monitoring_r3_nl_rule_adapter_external_discovery_20260810.md`。
- `poc/medical_monitoring_ai_native_r3_rule_ai/README.md`、`src/mm_r3_rule_ai/*.py`、`tests/*.py`。
- 冻结 R1/R2/R3 只作为公开合同与摘要锚点；不得运行 R1 全量测试，因为其中浏览器测试会覆盖冻结截图。
- 当前最终复核快照的 rule-AI 全树摘要：`8130880453d935fdd9490c19519a564a6257c8ebb51d2f53a18fd4382e20426c`（13 个文件）。初始会商快照为 `a75a94af879c0ddb03ede07245750a15b1aebd45bab1aa228f2773f4c2f2270e`；随后先纠正 `catalog.py` 与 `parser.py` 的两处文档事实形成 `a1a954b1...`，再将数值列表中的布尔值与标量数值布尔值统一分类为 `BOOL_AS_INT` 并新增一项反例测试，形成当前最终快照。
- 冻结锚点：R1 全树 `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；R2 Python `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`；R3 root-relative Python `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`。
- 摘要配方（路径字符串属于摘要输入，必须在 workbench 根执行；R3 例外为明确的包根 `./` 路径）：
  - rule-AI：`find poc/medical_monitoring_ai_native_r3_rule_ai -type f | LC_ALL=C sort | while IFS= read -r f; do shasum -a 256 "$f"; done | shasum -a 256`
  - R1：`find poc/medical_monitoring_ai_native_r1 -type f | LC_ALL=C sort | while IFS= read -r f; do shasum -a 256 "$f"; done | shasum -a 256`
  - R2 Python：`find poc/medical_monitoring_ai_native_r2 -type f -name '*.py' | LC_ALL=C sort | while IFS= read -r f; do shasum -a 256 "$f"; done | shasum -a 256`
  - R3 root-relative Python：`(cd poc/medical_monitoring_ai_native_r3 && find . -type f -name '*.py' | LC_ALL=C sort | while IFS= read -r f; do shasum -a 256 "$f"; done | shasum -a 256)`
- 主会场当前最终快照非 LLM 证据：rule-AI `247 passed`；冻结 R3 `339 passed`；Ruff `All checks passed`；12 个 Python 文件内存编译通过；无 cache；8911 无监听；R1/R2/R3 锚点不变。

## Scope

- In scope:
  - 独立审查中文自然语言规则→严格结构化候选→R1 证据链校验→R3 RuleDraft→本地试算→三种数据范围建议→用户确认激活的隔离合同。
  - 反证 canonical capability input、请求重算、profile/binding/run identity、sealed raw JSON-RPC、候选工件 exact linkage/negative authority/commit identity、coverage、parser truncation/ambiguity/BOOL_AS_INT、simulation/draft binding。
  - 从不熟悉计算机的中文医学监察员视角审查 `本次数据`、`全部历史数据`、`仅后续数据` 的标题、理由和影响说明是否直白、准确、不暴露内部字段或工程词。
  - 只读重跑 synthetic/offline rule-AI 与冻结 R3 测试；检查摘要、cache 与 8911。
- Out of scope:
  - 任何源文件修改、产品接线、界面/浏览器、真实 provider/harness、五个真实项目、真实临床判断、8911 或其他服务。
  - 医学写作子系统、产品源码、共享运行库以及 R1/R2/R3 冻结树写入。
  - 安全性架构、攻击面、权限、认证、威胁模型或安全测试；本轮只评功能正确性和用户语义。

## Success Criteria

- 先重算 rule-AI 13 文件摘要；不匹配则首行 `STALE_INPUT`，不得审阅漂移快照。
- 亲自运行 rule-AI 全量并得到 `246 passed`，运行冻结 R3 并得到 `339 passed`；Ruff、内存编译、无 cache、8911 停止均复核。
- 独立构造或检查至少一组正例与高价值反例；不得以既有 246 项数量替代源级审阅。
- 按 P0-P4 给出可复现缺陷；无阻断缺陷时首行 `VERDICT: ACCEPT`。明确只接受该隔离适配器，不接受 R3 总体或产品。
- 全程只读，不运行 R1 全量测试、不修改 frozen/product/medical-writing/真实项目，不做安全性设计测试。

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
- Reviewer 只读；不得写任何源、测试、context/review/metrics 或 runner 报告路径。
- 只能运行 synthetic/offline 单元与静态检查；不得启动监听器或访问外部 provider。
- R1 浏览器测试有已知截图写副作用，禁止运行 R1 全量测试；只可重算 R1 摘要。

## Loop Log

- 2026-08-10 18:47:05: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10: Grok Build session `74e238da-b0a0-4881-b934-4c8a57e36216` produced two cancelled, schema-incomplete outputs; same-session recovery exhausted. Declared Cursor fallback completed source reading but its venue rejected executable checks, so its P0 was an evidence-gate veto rather than a product defect. Declared Minimax fallback first pass returned `STALE_INPUT` because the context omitted the path-sensitive digest recipe. Codex reproduced all four declared hashes exactly with the recipes now recorded above; the same Minimax session must continue before any fallback verdict is accepted.
- 2026-08-10: Minimax same-session round 2 reproduced the documented recipes, ran `246`/`339`, static/compile/cache/8911 and synthetic counterexamples, and returned ACCEPT for initial snapshot `a75a94af...`. Codex then corrected only two inaccurate source comments identified independently by Pi/Cursor: catalog operator equality is cross-checked by isolated tests rather than parser import, and assumptions are retained by the parser then blocked by the workflow conversion gate rather than an absent `blocked_assumption` status. Final snapshot is `a1a954b1...`; main-venue rerun remains `246`/`339`, Ruff/compile green, caches absent, 8911 stopped. Both independent sessions must target-check this final snapshot before closure.
- 2026-08-10: Pi/CMS and Minimax both accepted `a1a954b1...`. Pi additionally identified that a bool inside `NUMBER_LIST` was correctly blocked but reported only `threshold_type_mismatch`, unlike scalar numeric bools. Codex made the smallest functional correction (`parser.py`) and added one focused counterexample (`test_w04_manager_remediation.py`), yielding final `81308804...`, `247 passed` and unchanged R1/R2/R3 anchors. `extracted_from` substring presence remains explicitly a minimum provenance check rather than semantic truth; no arbitrary length rule is introduced because short medical terms may be valid. Final same-session targeted review is required before closure.
- 2026-08-10: Final same-session targeted reviews completed: Pi/CMS and Minimax independently reproduced `81308804...`, `247`/`339`, Ruff/compile/cache/8911 and classification counterexamples, and both returned ACCEPT with no P0-P4. Minimax corrected its own historical wording: the pre-fix bool list was already blocked and only misclassified, so this was not fail-open. Codex main-venue review accepts only this isolated adapter snapshot and advances the program to R4.
