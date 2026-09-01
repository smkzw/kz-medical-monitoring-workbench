# Conference Context: monitoring_p10_release_chain_mapping_gate_20260730

Created: 2026-07-30 08:33:22
Objective: 独立挑战医学监查字段映射新版科学性合同与规则发布链，重点审查CM/IP/背景治疗边界、来源身份贯穿、二次医学批准消除、影子验证和daily-run失败关闭
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_monitoring_goal_p10_20260730/TASK_CONTEXT.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- `context/monitoring_p10_mapping_scientific_release_matrix_20260730.md`
- `context/monitoring_p10_mgk10_v13_scientific_audit_20260730.md`
- `context/monitoring_p10_rule_release_chain_gap_audit_20260730.md`
- `context/monitoring_p10_rule_template_recommendation_backend_20260730.md`
- `context/monitoring_p10_legacy_risk_bypass_closure_20260730.md`
- `context/monitoring_protocol_contract_v2_context.md`
- 当前字段映射 prompt/质量门/组装/激活代码与测试。
- 当前规则事实、规则定义、规则包、影子验证、发布、daily-run readiness 的代码与测试。
- 真实运行数据库只允许 `mode=ro/query_only` 读取，且仅用于验证状态投影；不得修改。

### Frozen mapping slice

The mapping slice is frozen at `monitoring-listing-field-mapping-v15`:

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_service.py` | `e45996b48512497be0cc44aa88df2bf834ac7255024ce2d0fc94ca1856d9b323` |
| `services/api/app/monitoring_mapping_semantic_quality.py` | `c793f3689a95aab32d253c2bc059a97ac1665c67b55a2897e38f91215fd94e1c` |
| `services/api/app/monitoring_mapping_draft_repository.py` | `72c293edf5fdfb57faab9addc06f4369897959ace81adf0f377475b120f9105a` |
| `tests/test_monitoring_ai_service.py` | `ec0fedd603f0e93a2d5714d685dbd0ea41bcd4b914551590639b95acb0a339ef` |
| `tests/test_monitoring_mapping_semantic_quality.py` | `370ead05f661fdd16a8d2cf3f0ab34b037950131788920e291c6a7e06510e80f` |
| `tests/test_monitoring_mapping_draft_repository.py` | `31446b787968f28fdb3afb5c42eded15750d49968fa536b19d7f5125f9ee5737` |

Codex independently reran mapping service, semantic quality, draft assembly and
activation tests: `269 passed`; production modules compiled. The original delegated
runner remains rejected because its output exceeded the hard ceiling; this frozen
slice was independently reviewed and accepted in the main venue.

### Frozen rule-release-chain slice

The offline rule-release chain is frozen after the worker_03 same-session atomic
commit follow-up:

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_protocol_rule_repository.py` | `71b47b5b29750ab391f98665bed3a4be09c9e3e6a21d013d790f8be40db617ef` |
| `services/api/app/monitoring_protocol_rule_service.py` | `7a0b68397c4ee82a4148ac4667c8cb5a595f6839b15a7087394fb591e49f9751` |
| `services/api/app/monitoring_shadow_sample_service.py` | `890c86cbb554238546f127b819428994059163cf922b2f3ef86dff74e45694ba` |
| `services/api/app/monitoring_record_rule_resolver.py` | `2df5f4f16d8e19db3dda0f28ec71836c26db94fab350c0e35cc48195b05b303f` |
| `services/api/app/monitoring_daily_run_service.py` | `948b5b0abd77b497a341af3f3452f451c9e99b6a9a62226abd5e4b8ebf15f4b8` |
| `services/api/app/medical_monitoring_router.py` | `5ed3350dc8fab3f5ed47ba119590c109bd4491b7ed6dfd1c40814c0c44d73f14` |
| `services/api/app/monitoring_rule_templates.py` | `1d91eeefa2fc3e7b910864bcbdeeb99431c0f26d1e7ee9d6979dc9c62ca04fe9` |
| `tests/test_monitoring_rule_release_chain_p0_20260730.py` | `93c91be0d480fa540f00c404f5214d28eb0d3dcd8bbefa8ab1abfb0f07aeec43` |
| `tests/test_monitoring_shadow_sample_service.py` | `208647128cbc96248bc3b7f51e78df4f446a95c45c4040afdeb5ebed824ef9eb` |
| `tests/test_monitoring_record_rule_resolver.py` | `b884da26565c6683c7484c71f3745ac5e07ef54f8d92381a68703dd2cab153e8` |
| `tests/test_monitoring_daily_run_service.py` | `0a962d1aa3a5ed78c538c3a349db0bdba37634ede1902ba0e7455d9935bf8642` |
| `tests/test_monitoring_rule_templates.py` | `2e210df2e17bf1ca128abbfdd74f3c42285083da7120afea5fbb2372b439430d` |
| `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs` | `f6d4a96c4b118f7f91ac88385e6c427325a905ff5f5af9974100726e6d61efd4` |
| `frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.mjs` | `a108f3cd80e2d04ebe5d995d605eddb8f918b0a18db8170bf9314dd0e9f1ac7b` |
| `frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx` | `4a3338d3b57c58a0dceaaebeef7c77c7ca06040a0b34e81ae10f01ea768fea0b` |
| `frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs` | `ed848b584fe27573ef2a24a1e514e6ac57bff4b268d1ab865409daa51087242c` |
| `frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.test.mjs` | `2bf16b99d71651239cf5506f2aa12e229275194cf45e4b3fa49541af34b3f1a0` |
| `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs` | `1f772a47dcbf09ed5b84b5cd84dde7f26ea9cb126f04bb15484356b4fcc09b6b` |

`services/api/app/main.py` is a concurrent medical-writing shared file and is not
treated as a whole-file frozen artifact. The monitoring slice owns only the
`rule_effective_capabilities_sha256` projection in
`_current_monitoring_rule_runtime`; participants must inspect that locator and
must not infer ownership of unrelated current changes. `frontend/src/App.jsx`
remained unchanged at
`a94e7bd795d236c7166c13b0e12fee90094975660feb0dc2594dbc0f6b1d7af1`.

Codex independently reran the ten focused backend suites after the atomic
follow-up: `199 passed`. The execution worker's final all-monitoring regression
was `1086 passed, 4251 deselected, 0 failed`; six injected atomicity tests cover
rollback during promoted-case, trusted-run, confirmation and event writes,
idempotent retry, and preservation of pre-existing independent evidence. The
medical-monitoring frontend has 12 passing test files and a successful Vite
production build. Port 8911 remained stopped and no real candidate, mapping,
rule pack or daily run was changed.

## Scope

- In scope:
  - 审查新版字段映射合同能否跨项目区分 IP、背景治疗、CM、救援/对照治疗和未确认对象；
  - 审查剂量、量表、日期精度、编码血缘和能力缺口是否失败关闭；
  - 审查 mapping/source/capability/fact/rule identities 是否贯穿规则包、影子、发布和 daily run；
  - 审查用户采用规则建议后是否仍存在无意义的二次医学批准；
  - 审查自动真实批次影子样本、项目隔离、幂等、来源漂移和 daily-run readiness；
  - 只给出冲突、风险、缺口和具体修复建议，不重复无差别遍历已通过的功能。
- Out of scope:
  - 修改产品代码、真实候选或运行数据库；
  - 采纳、确认、激活任何医学候选；
  - 医学写作子系统；
  - 把已解构 Timeline/Profile/风险成品作为工作流输入；
  - 视觉最终验收和上线结论。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 结论必须分别标明代码合同证据、医学推断和仍需真实项目验证的事项。
- 至少提供一个可能逃过现有测试的反例，并给出可自动化的验收断言。
- CM 仅为非试验用药；dose adjustment、administration、interruption、restart、
  discontinuation、dispense、return、compliance 保持独立。
- 用户采用推荐即为医学决定；影子结果确认和发布可以保留，但不得再次审批同一规则内容。

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

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-30 08:33:22: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 等待两个实现切片落盘后更新精确文件哈希，再做 prompt preflight 与并行参与者分发；
  不允许评审过时中间态。
- 2026-07-30 09:40 CST：字段映射 V15 切片已冻结并记录哈希；规则发布链仍在运行，
  因此参与者尚未分发。
- 2026-07-30 15:55 CST：规则发布链经 Codex 冲突点复核和原 Kimi session 原子提交续跑
  后冻结。参与者现在只审查上述冻结合同的冲突、反例和遗漏，不重做实现，不读取或修改
  真实运行库。
