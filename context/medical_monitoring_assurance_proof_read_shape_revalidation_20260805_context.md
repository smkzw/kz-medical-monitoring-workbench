# Task Context: medical_monitoring_assurance_proof_read_shape_revalidation_20260805

Created: 2026-08-05 05:07:27
Objective: Fail closed on malformed or misbound persisted assurance full-recompute proof rows
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py` (`FullRecomputeProof`,
  `_proof_from_row`, proof schema/read/write paths).
- `tests/test_monitoring_assurance.py` plus assurance principal, proof/rollup,
  release-gate, dossier and evidence-revalidation suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate persisted proof row identity/mode, root collection
  shapes, required text fields and timestamps; preserve content-hash
  verification and proof write/replay behavior; add focused tamper regressions,
  run assurance adjacency, compile/Ruff, hashes, evidence and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new proof hash/schema schemes,
  rollup semantics and runtime/release activation.

## Success Criteria

- Valid proof rows round-trip unchanged after restart.
- A misbound row, unsupported mode, malformed collection, missing required
  text, timestamp drift or invalid JSON fails closed before callers receive the
  proof.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:07:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Hardened `_proof_from_row` and added four isolated persisted-root
  tamper regressions. Focused 84 and adjacent 204 passed; compileall/Ruff
  passed; ports remained free; Hermes review gate returned `ok: true`.
- **Residual/next**: proof shape/hash integrity does not prove rollup or audit
  chain semantics, provider output, clinical correctness, browser usability,
  formal B6 review, C14 activation or commercial release. Continue with a
  bounded structural P7/P8/P9 source-only gap; keep runtime gates closed.
