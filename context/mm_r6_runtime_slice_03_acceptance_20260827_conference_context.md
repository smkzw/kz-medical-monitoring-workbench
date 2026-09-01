# Conference Context: mm_r6_runtime_slice_03_acceptance_20260827

Created: 2026-08-27 23:23:06
Objective: 独立审阅 R6 第三纵切 synthetic/offline ReportReviewBundle 实现是否满足 context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md 与权威合同 §7/contract.json。重点寻找内容寻址、三件身份与 issue/evidence/locator 共享、annotation/anchor map 一致性、DRAFT 未决项保留、IssueTransition/revision diff 的失败开放；核对 360 回归与 9 宫格证据。不得修改文件，不得接受产品/真实报告/医学/渲染范围。给出可执行缺陷或明确的条件接受结论。
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

- Linked execution task: `mm_r6_runtime_slice_03_20260827`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md`
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §7
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/report_bundle.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_report_bundle.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_report_bundle_runtime_receipt.json`
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: synthetic/offline JSON ReportReviewBundle、annotation/anchor map、DRAFT、IssueTransition/revision diff、相邻回归与确定性证据。
- Out of scope: 产品 runtime、真实报告/项目、医学结论、DOCX/PDF/HTML 渲染、前端/服务、医学写作子系统。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

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

- 2026-08-27 23:23:06: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-27: Gemini 独立审阅完成；其早期计数仅对应当时字节，不作为最终摘要。
- 2026-08-27 to 2026-08-28: Grok Build 同一 session 连续纠偏审阅，依次发现并复核 lifecycle/evidence-only resolved、身份组歧义、伪锚点、merge/split、遗漏单元改挂等失败开放。
- 2026-08-28: Codex 完成最终 ordinal-only locator 收紧；当前 71 focused、377 full、9/9 optimizer/hash-seed cells 通过，收据已同步。
