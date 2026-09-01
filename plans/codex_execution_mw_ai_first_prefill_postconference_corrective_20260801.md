# Codex Execution Plan: mw_ai_first_prefill_postconference_corrective_20260801

Objective: Correct the independently confirmed P2-P4 defects around AI-first corpus prefill adoption, evidence identity and semantics, recommended selection, exactly-once generation, and UX robustness; prove with focused deterministic tests and a fresh isolated-clone runtime without touching medical-monitoring files or frozen r42 artifacts.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Server-side single-candidate adoption gates and next-revision evidence catalog identity | `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_01.md` |
| `worker_02` | Durable in-flight generation reservation and one physical provider attempt for this route | `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_02.md` |
| `worker_03` | Evidence semantic term coverage, safe recommendation selection, wording/deduplication/negation/prompt hardening, and focused regression tests | `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/manager.md` |

## Codex Acceptance

Codex will inspect every actual diff and current file, run the complete focused suite, verify
the exact concurrency/transport/evidence/adoption regressions, and then create a new isolated
runtime clone for one real Computer Use click and SQLite logical-delta audit. The r4 clone is
immutable evidence, not a reusable test target. Acceptance requires no new P0-P4 in an
independent challenge; worker or manager confidence is not acceptance evidence.
