# Conference Context: commercial_platform_foundation_20260710

Created: 2026-07-10 10:01:52
Objective: 为康哲AI医学经理工作台确定并落地共享事务持久化、独立AI执行治理、审计与私有化迁移边界，作为六个医学子系统商业化的共同底座
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- Binding requirements and recovery state:
  - `records/soft_pause_20260709_1105_lossless_full_backup/USER_REQUIREMENTS_FULL_LEDGER.md`
  - `records/soft_pause_20260709_1105_lossless_full_backup/CROSS_PROJECT_GENERALIZATION_TEST_GATE.md`
  - `records/soft_pause_20260710_0945_canonical_project_context/README_RESUME.md`
  - `records/soft_pause_20260710_0945_canonical_project_context/CURRENT_STATE_AND_VALIDATION.md`
  - `records/soft_pause_20260710_0945_canonical_project_context/SYSTEM_AND_SUBSYSTEM_STATUS.md`
  - `records/soft_pause_20260710_0945_canonical_project_context/PITFALLS_AND_OPEN_RISKS.md`
  - `records/soft_pause_20260710_0945_canonical_project_context/FUTURE_EXECUTION_PLAN.md`
- Approved product and architecture sources:
  - `../../docs/Codex执行版_医学经理工作台架构与执行规范_V0.1_20260707.md`
  - `../../records/Product_Design_Brief_Gate_V0.2_20260707.md`
  - `../../records/architecture_20260707/独立AI能力边界与Prompt治理_V0.1.md`
  - `frontend/AGENTS.md`
- Current implementation and tests:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/demo_repository.py`
  - `services/api/app/ai_gateway.py`
  - `services/api/app/ai_task_runner.py`
  - `services/api/app/source_intake.py`
  - `services/api/app/evidence_picos_workflow.py`
  - `services/api/app/tfl_review_workbench.py`
  - `services/api/app/safety_pv_review_workbench.py`
  - `services/api/app/workbench_inbox.py`
  - `services/api/app/main.py`
  - `tests/`
- Current slice records:
  - `records/active_slices/commercial_platform_foundation_20260710/COMMERCIAL_REQUIREMENTS_TRACEABILITY_MATRIX.md`
  - `records/active_slices/commercial_platform_foundation_20260710/RESEARCH_AND_DECISION_LOG.md`
  - `runs/subagents/20260710_commercialization_baseline/architecture_generalization_audit.md`
- Authorized real-project roots are read-only in place:
  - `/Users/smkzw/Documents/康哲项目资料`
  - `/Users/smkzw/Documents/朗来项目资料`
- Original project files must never be deleted, moved, renamed, or modified. Writable derivatives belong under this workbench.

## Scope

- In scope:
  - one shared write envelope for all medical-module state changes;
  - local single-machine SQLite transactional persistence with explicit migration boundary to PostgreSQL;
  - idempotent replay, optimistic concurrency, atomic domain-state plus audit writes, restart recovery, corruption diagnostics, and project-qualified identifiers;
  - project/task/data-classification AI execution policy for independent LLM, VLM, and OCR;
  - source allowlists, prompt/config/model versions, retry/error state, output validation, medical disposition, and privacy-safe public projections;
  - interfaces that can be adopted incrementally by evidence/PICOS, eligibility, monitoring, TFL, writing, Safety/PV, dashboard, and approval center.
- Out of scope for this slice:
  - final RBAC/e-signature certification, although actor and authorization boundaries must be preserved in the schema;
  - rewriting every subsystem store in one change;
  - deploying PostgreSQL or Temporal in the local first release;
  - changing approved frontend layout or clinical business copy;
  - clinical rule generation or final medical conclusions.

## Success Criteria

1. At least three independent model perspectives plus Codex compare the three architecture options and record benefit/risk/rejection reasons.
2. The accepted design uses a storage interface that runs locally without a new external service and has an explicit PostgreSQL migration contract.
3. A common write envelope contains tenant placeholder, canonical project id, actor context, request/idempotency ids, expected version, reason/comment, source/config/prompt versions, client/server timestamps, and medical-approval boundary.
4. One transaction can atomically persist domain state, append immutable audit metadata, and register idempotent response replay.
5. Tests prove same-id cross-project isolation, stale-write `409` semantics, idempotent replay, restart recovery, rollback on failure, malformed-store diagnosis, and no local-path/private-field public leakage.
6. AI execution policy resolves by project + module/task + data classification + deployment profile and fails closed when no allowed provider/model/source policy exists.
7. AI run audit records model/provider/policy/prompt/source/config versions, validation, retry/error, and medical disposition without exposing secrets or unrestricted source text.
8. The design names the first existing JSONL stores to migrate and keeps compatibility adapters until each subsystem passes regression.
9. No participant or implementation claims the total workbench or a subsystem commercializable from this foundation slice alone.

## Architecture Options To Adjudicate

- Option A, recommended candidate: standard-library `sqlite3` transaction kernel now, repository/Unit-of-Work interface, schema migrations owned in code, PostgreSQL adapter later. Lowest deployment burden and directly replaces unsafe JSONL behavior.
- Option B: add SQLAlchemy 2 + Alembic now and use SQLite/PostgreSQL through one ORM. Better migration ergonomics, but adds dependency and broadens the first change.
- Option C: introduce Temporal plus PostgreSQL now for durable distributed workflows. Strong long-running orchestration, but premature for the current single-machine service and does not replace the need for domain transactions.

The conference must challenge these candidates and may recommend a hybrid, but it must not approve a heavy component merely because it is enterprise-branded.

## Evidence Boundary

- External vendor pages are capability claims, not proof of our implementation.
- Regulatory sources establish design expectations; they do not certify this product.
- Current tests and code are authoritative for implementation status. Prior reports are leads and must be rechecked where material.
- DeepSeek V4 review uses Reasonix CLI under current project governance. It is not dispatched through Hermes or OpenCode.

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
- Do not include patient-identifying content in conference outputs.
- Do not edit production code in the conference round.
- Do not infer authentication, electronic-signature compliance, or Part 11 validation from a persistence schema.
- Keep AI provider secrets out of prompts, stdout, metrics, and run artifacts.

## Current LOOP Contract

- Objective: choose a small, durable common platform slice that all six medical subsystems can adopt without preserving unsafe JSONL and global-provider behavior.
- Hypothesis: a transaction-first SQLite kernel plus policy-governed AI execution is the smallest coherent local architecture; PostgreSQL and durable workflow orchestration remain explicit later adapters.
- Action: audit current code, compare external/regulatory patterns, obtain independent model critiques, implement with TDD, migrate one cross-module path, and run failure/restart/isolation tests.
- Observation: exact code evidence, failing-then-passing tests, database integrity checks, API contracts, provider stdout/metrics, and restart behavior.
- Evaluation: accept only behavior that survives process restart and conflicting/replayed writes without cross-project leakage.
- Decision: expand migration only after the shared kernel passes; revise architecture if conference evidence exposes an unhandled data-integrity or deployment risk.
- Record: update the active-slice ledger, system/subsystem logs, conference artifacts, and requirement matrix after each iteration.

## Loop Log

- 2026-07-10 10:01:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
