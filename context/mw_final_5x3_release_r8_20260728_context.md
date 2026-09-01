# Medical Writing Final 5x3 - release-r8-20260728

## Goal

Run the user-mandated five-tester, fifteen-indication, thirty-perspective
visual E2E matrix from isolated zero-project runtimes until complete protocol,
DOCX, PDF and native Word acceptance are achieved. Tester output must not
replace product independent-AI work.

## Governing Contract

- Global rules SHA-256:
  `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`
- Matrix: `scripts/qc/mw_final_5x3_matrix.json`
- Prompt package: `prompts/final_5x3_e2e_20260728/`
- Preparation/test root:
  `runs/execution/mw_final_5x3_harness_20260728/`
- Test order: A Luna -> B Aishuo -> C Hy3 -> D Gemini -> E Qwen.
- Qwen new starts: Beijing 22:00-06:00 only.
- Aishuo new starts: before 23:30 or after 08:30 only.
- Existing tasks may continue outside their start windows.
- No OCR or translation workload was started in this slice. Future product
  workloads remain subject to the shared oMLX lease and Hy-MT2 contract.

## Frozen Inputs And Deterministic Evidence

- Five testers, fifteen slots and fifteen unique indications validated.
- Frozen source receipts: 53, all present and matching.
- Baseline, harness and runtime regressions: 69 passed.
- `release-r8-20260728` input fingerprint:
  `52bcc9da139cfe569a704b9d04660f4ea2847602e604f978084fef7d60108076`.

## Invalidated Round

`release-r7-20260728` is invalidated before any tester or product evidence.
Its first A1 orchestration attempt showed that the shared baseline allowlist
still named only historical 4x3 roots. The failure happened before runtime
creation or page interaction. `R7_INVALIDATED.md` is preserved in that round
and the round must never be reused or counted.

## Bounded Infrastructure Repair

- Added the exact `mw_final_5x3_harness_20260728` run root to
  `mw_isolated_runtime_baseline.py`.
- Retained exact-root, adjacent-path and symlink rejection.
- Added a runtime-to-baseline cross-module regression.
- Added the baseline implementation and its tests to fail-closed frozen source
  receipts, increasing the receipt count from 51 to 53.

## Active A1 Run

- Round: `release-r8-20260728`
- Slot/perspective: `A1/lazy_medical_writer`
- Scenario: COPD, Phase III, inhaled fixed combination, greenfield.
- Frontend: `http://127.0.0.1:51565`
- Backend: `http://127.0.0.1:51564`
- Runtime identity SHA-256:
  `b3365c7fb61cf35d05df1b90a286669a89566e83bb8632136f5557e4d48b7ed0`
- Tester: `Codex subAgent/gpt-5.6-luna-high`
- Agent id: `019fa689-7bec-70f2-a835-d743a6d1e710`
- Polling policy: long wait only; do not inspect intermediate medical output.
- Product source edits are forbidden while this immutable run is active.

## Next Safe Action

Wait for the A1 tester to complete or report a material blocker. On blocker,
preserve its evidence, stop the isolated runtime, repair only the reproduced
cause, invalidate the affected round, refresh source receipts, and rerun from
a new clean round. On success, complete A1 engineer from another clean runtime
before A2.

## A1 Slow-Progress Adjudication

The tester initially reported `BLOCKED` after about fifteen minutes. Codex did
not accept that disposition because read-only runtime evidence showed:

- child job `mwjob_90cbf2e91545811b90bdefbb` remained `running`;
- 594 candidate results and 5/15 independent-AI batches were durable;
- the child lease was valid at inspection time;
- parent `mwjob_1332eb9f8863463d4cde2305` had entered recoverable attempt 2.

The same Luna session was resumed with the global 120-minute hard-wait rule.
No product edit, restart, new project or fallback was allowed. A material
blocker may be declared only after exhausted product retries or a terminal
failure, not from latency alone.

## Manual Pause Boundary

The resumed tester completed triage and visible basket lock, then reproduced
`MW-A1-002`: downstream translation still requires finalized triage. The
triage run is `confirmed`, its confirmation is `discovery_projected`, while
the parent remains `awaiting_triage_confirm`. Product retry controls are
disabled. This is the accepted terminal blocker for r8.

Per user instruction, no repair or next tester was started. API and frontend
services were stopped and both ports released. Exact hashes and the resume
procedure are in
`records/handoffs/CODEX_NO_LOSS_PAUSE_A1_R8_20260728.md`.
