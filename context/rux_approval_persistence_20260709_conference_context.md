# Conference Context: rux_approval_persistence_20260709

Created: 2026-07-09 10:20:39
Objective: Harden RUX medical-monitoring internal approval so ApprovalGate and approval actions persist across backend restart without changing clinical boundaries or leaking local source paths.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- Current handoff package:
  - `records/soft_pause_20260709_lossless_handoff/README_RESUME.md`
  - `records/soft_pause_20260709_lossless_handoff/SYSTEM_AND_SUBSYSTEM_BACKUP.md`
  - `records/soft_pause_20260709_lossless_handoff/CURRENT_PROGRESS_AND_VALIDATION.md`
  - `records/soft_pause_20260709_lossless_handoff/PITFALLS_AND_OPEN_RISKS.md`
- Current implementation files:
  - `services/api/app/demo_repository.py`
  - `services/api/app/workbench_inbox.py`
  - `services/api/app/main.py`
  - `frontend/src/App.jsx`
- Current contract/tests:
  - `packages/contracts/workbench_contracts/models.py`
  - `tests/test_approval_center.py`
  - `tests/test_workbench_inbox.py`
  - `tests/test_frontend_monitoring_contract.py`
  - `frontend/tests/rux_monitoring_inbox_qc.mjs`
- Runtime root:
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime`
- Real RUX source files are authorized read-only sources, but this slice should not modify or copy them unless a test explicitly needs metadata:
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx`
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`

## Scope

- In scope:
  - Make RUX `medical_monitoring_risk_disposition` ApprovalGate state durable across backend/repository/service re-instantiation.
  - Persist RUX approval decisions/actions, including approve/return/reject/view-quality-gate audit trail, without losing clinical boundaries.
  - Ensure dashboard `pending_approvals` does not resurrect already approved/rejected gates after restart.
  - Preserve existing JSONL append-only runtime style unless a stronger small local store is clearly necessary.
  - Add tests that simulate restart by creating a fresh `DemoRepository` / service instance over the same runtime store.
- Out of scope for this slice:
  - Full enterprise RBAC/e-signature implementation.
  - Replacing all demo repository state with a production database.
  - Query external dispatch, center reply, risk closure, or regulatory archive workflow.
  - RUX 192-subject full medical monitoring scan.
  - Visual redesign beyond any minimal copy/contract adjustment needed for this persistence fix.

## Success Criteria

- TDD red-green is preserved: at least one new test must fail before implementation.
- After creating a RUX internal approval, a fresh repository/service instance over the same runtime store can recover the ApprovalGate.
- After approving/returning/rejecting a RUX internal approval, a fresh repository/service instance recovers the terminal or returned state and does not show incorrect pending dashboard state.
- `view_quality_gate` remains non-mutating.
- Approval comments/copy do not imply external Query execution, risk closure, formal approval, regulatory submission, or archive.
- Public API/browser-facing payloads do not expose `/Users/`, `file_path`, `root_path`, hashes, storage keys, raw runtime paths, or local source locators.
- Existing full unit suite and frontend build continue to pass.
- Records/logs are updated so another agent can resume.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- RUX approval approval means only internal Query draft / disposition recommendation approval. It must not close a risk or mark a site/center Query sent.
- Original clinical source folders may be read, or copied into the work area when needed, but must not be deleted, moved, cut, or overwritten.
- Product AI must remain independent of Codex; this persistence slice should not add Codex fallback.

## Loop Log

- 2026-07-09 10:20:39: Conference initialized by `hermes_workflow_guard.py init-conference`.
