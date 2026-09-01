# Conference Context: monitoring_source_revision_gate_20260713

Created: 2026-07-13 04:16:51
Objective: 审阅并收敛医学监查真实项目source revision绑定、全目录drilldown和真实项目增量上传服务端失败关闭方案
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `services/api/app/rux_monitoring_service.py`
- `services/api/app/my009_monitoring_service.py`
- `services/api/app/monitoring_project_registry.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/main.py`
- `services/api/app/monitoring_intake.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_rux_monitoring_service.py`
- `tests/test_my009_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `tests/test_source_content_validation.py`
- `records/active_slices/monitoring_incremental_diff_20260712/ACCEPTED_ARCHITECTURE.md`
- Codex/SubAgent fresh read-only evidence: RUX `53 sheets / 180,793 rows / 241 subjects`; MY009 `61 sheets / 4,106 rows / 26 subjects`; MY009 subjects `S02002` and `S16001` currently fail drilldown because DS contains them while DM does not.

## Scope

- In scope: deterministic listing+protocol revision token; cache reload/fail-closed behavior after source change; inbox/disposition CAS binding; full 241+26 subject drilldown reliability; source-grounded identity fallback when DM is absent; server-side blocking of the generic demo/SAR intake engine for real RUX/MY009 projects while preserving file registration/content validation.
- Out of scope: adding new clinical rules, claiming full medical monitoring, real incremental row diff implementation, mobile UI, changes to source files, medical conclusions, or bypassing source confirmation.

## Success Criteria

- A source revision changes when either listing or protocol bytes change, without exposing paths or raw hashes in the public API.
- Adapter caches cannot silently serve an old listing/protocol after revision change.
- Existing read/disposition/approval tokens become stale after source revision change and are rejected without writes.
- All 241 RUX and 26 MY009 subjects return drilldowns; missing DM is handled only with existing DS/SV identity fields and no inferred demographics.
- Every real drilldown has the matching project, non-empty revision and public row locators for all events/trend points.
- `/monitoring/intake` and `/monitoring/intake/file` cannot execute the generic demo/SAR rule engine for registered real projects; the file route may still register and content-validate the uploaded source before returning a structured not-enabled response.
- CM remains non-investigational medication; investigational-product changes/dose adjustments remain separate.
- Tests cover both real projects, synthetic source mutation, fail-closed upload routes, no path/hash leakage, and unchanged demo intake behavior.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not recommend a source token based only on file name, mtime, static batch label, rule text, or locators.
- Do not read or modify the real clinical source files; use existing read-only test evidence and synthetic fixtures for mutation tests.

## Loop Log

- 2026-07-13 04:16:51: Conference initialized by `hermes_workflow_guard.py init-conference`.
