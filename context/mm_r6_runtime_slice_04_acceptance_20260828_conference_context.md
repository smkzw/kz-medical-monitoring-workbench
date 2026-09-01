# Conference Context: mm_r6_runtime_slice_04_acceptance_20260828

Created: 2026-08-28 00:26:21
Objective: 独立审阅 R6 第四纵切 synthetic/offline ModeContract、ModeOutput、daily 四输出与结构化 Query 草稿是否满足 slice-04 合同和权威 §8/contract.json；重点寻找 Run/mode/carry-forward、output identity/eligibility、authority/numeric、Query 依据+发现+行动项及 sent/closed/PD 边界失败开放；核对 460 回归与 9 宫格。不得修改文件或接受产品/真实项目/医学范围。
Task type: `complex_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is ``; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r6_runtime_slice_04_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_04_contract_20260828.md`
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_mode_output_runtime_receipt.json`

## Scope

- In scope: synthetic/offline ModeContract、Run gate、ModeOutput、daily 四输出、结构化 Query 草稿及失败关闭。
- Out of scope: 产品 runtime、真实项目/报告、医学结论、Query 外发、PD 登记/关闭、浏览器/视觉、Agent Harness 模型接入、pre_lock/post_lock 深层 payload。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 当前字节通过 focused、全量、9 宫格；会商发现的失败开放经修订后在原 session 复核关闭。

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

## Loop Log

- 2026-08-28 00:26:21: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 初轮：Pi 建议接受但发现两个畸形输入异常；Grok 以可复现探针发现 D1-D7，主场裁定 revise。
- Codex 修订：显式入口/资格、完整承接来源、固定锁定身份、数字语义、变化来源、Query 身份/范围及畸形输入失败关闭。
- 验证：focused 96、full 473、9/9 每格 96；8911/5174 停止，医学写作 542 文件 aggregate 未变。
- 原 session targeted follow-up：Pi 与 Grok 均完成、无 fallback，所有原缺陷 CLOSED；建议限域接受。
