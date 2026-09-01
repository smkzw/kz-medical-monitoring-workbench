# Conference Context: mw_release_conflicts_20260727

Created: 2026-07-27 05:39:30
Objective: 只审阅医学写作上线前四项冲突风险：隔离clean receipt、旧12-lane资产干扰、六份摘要夹具边界、DOCX门及四模型启动顺序；不得重扫产品或修改产物
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `runs/execution/mw_final_4x3_harness_20260727/clean_probe_20260727_0545/CLEAN_STATE_RECEIPT.json`
- `scripts/qc/mw_isolated_runtime_baseline.py`
- `plans/mw_final_4x3_input_fixtures_20260727.md`
- `prompts/final_4x3_e2e_20260727/COMMON_TESTER_CONTRACT.md`
- `prompts/final_4x3_e2e_20260727/MATRIX_ASSIGNMENT.json`
- `prompts/final_4x3_e2e_20260727/ROUTE_TIME_GUARD.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `evidence/mw_docx_release_gate_20260727/` when the bounded DOCX worker finishes.
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: challenge only the four locked release conflicts: per-run isolation proof; legacy 12-lane interference; realism and non-leakage of six synopsis fixtures; DOCX gate completeness and four-tester launch order.
- Out of scope: broad product re-audit, source edits, project creation, tester dispatch, medical drafting, security review, and replacing product-independent AI with the conference model.

## Success Criteria

- Return issues only where the cited evidence is contradictory, incomplete, or unsafe for launch.
- Distinguish a deterministic gate from actual end-to-end product evidence.
- Recommend a bounded repair or launch-order change for each material issue; do not create duplicate artifacts.
- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- Read-only conference. No product, fixture, runtime, prompt, or evidence files may be modified by participants.
- Historical audit material may retain obsolete model names but cannot be treated as an active product configuration.
- A clean-state receipt proves only the state and identities it records; it does not prove the later browser journey or DOCX quality.
- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-27 05:39:30: Conference initialized by `hermes_workflow_guard.py init-conference`.
