# Conference Context: eligibility_review_frontend_20260711

Created: 2026-07-11 15:27:49
Objective: 设计并实现资格审核桌面三列审阅工作区，基于真实review API，保持IN/EX语义、证据与医学决策边界、项目隔离和无正式资格结论
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair for this and future sub-venue review: `aishuo/MiniMax-M3`, per the user's 2026-07-11 routing override.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.
- User routing override dated 2026-07-11: Hermes sub-venue review uses provider/model `aishuo/MiniMax-M3`. This override applies to this conference because the chair had not started, and to future project conferences unless the user changes it.

## Source Of Truth

- `frontend/src/App.jsx` and `frontend/src/styles.css`: current desktop implementation and design system.
- `services/api/app/eligibility.py`: current raw-intake and versioned subject-review APIs.
- `packages/contracts/workbench_contracts/models.py`: strict eligibility action/state contracts.
- `tests/test_frontend_eligibility_contract.py` and `tests/test_eligibility_review_api.py`: current interaction and backend boundaries.
- `/Users/smkzw/Documents/康哲项目资料/AI/入排/enrollment-review-app/`: read-only interaction reference explicitly authorized by the user; do not copy its cached conclusions.
- `/Users/smkzw/.cc-switch/skills/ppt-master/projects/kangzhe_promotion_ppt169_20260606/templates/header_logo.png`: canonical CMS logo asset.

## Scope

- In scope: desktop-only 3-column eligibility review workspace; subject pool, criterion ledger, evidence/decision inspector; IN/EX independent labels and controls; stale-response protection; review API consumption; dense real-project data; explicit pending-medical-confirmation boundary.
- Out of scope: mobile compromise, formal eligible/not-eligible output, randomization release, invented evidence, production source writes by Hermes, browser/visual acceptance by Hermes, reuse of legacy project conclusions.

## Success Criteria

- First viewport at 1600x1000 prioritizes the three-column operating surface; preparatory summaries do not push the ledger below the fold.
- Left subject pool never overflows; middle criterion ledger is the primary work surface; right inspector is at least as informative as the ledger and contains source/evidence plus medical actions.
- Selecting a subject loads `/review`; selecting criteria cannot mix prior subject/project responses.
- IN uses `met/not_met`; EX uses `absent/present`; shared gap/judgment states remain explicit.
- Decisive actions cannot be enabled without current evidence; AI suggestions remain separate from medical decisions.
- No public path/content hash, legacy conclusion, provider name, formal eligibility or randomization-release language appears.
- Every visible control proposed for the first slice has a real backend or local interaction path; no decorative primary buttons.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-11 15:27:49: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Buddy GLM first run exceeded its read allowlist and was excluded; the bounded retry complied. Buddy Kimi returned a patch proposal that Codex did not apply directly. `aishuo/MiniMax-M3` completed the actual sub-venue synthesis.
- 2026-07-11: Codex implemented the reviewed three-column workspace, passed focused tests/build, and completed D001/MY009 Chrome action and visual QC at 1600x1000 and 2048x1024. Main-venue DeepSeek Pro now reviews the implemented state rather than placeholders.
