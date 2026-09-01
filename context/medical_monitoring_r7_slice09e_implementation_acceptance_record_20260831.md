# R7 Slice-09E implementation acceptance record

Date: 2026-08-31

## Decision

`ACCEPT_R7_SLICE_09E_LOCAL_DISTRIBUTION_SYNTHETIC_OFFLINE`

This decision accepts only the synthetic/offline local-distribution and data-disposition shell defined by the frozen Slice-09E v0.2 contract. It does **not** accept a signed installer, a real runnable release, Windows packaging, the whole R7 phase, or R8 readiness.

## Accepted scope

- Chinese local management entry for preflight, status, start, stop, upgrade preparation and uninstall preview.
- Exact ownership checks for 8911/5174 and optional 8984; foreign listeners fail closed and are never killed.
- Backup-first and schema-precheck upgrade preparation with deterministic busy/failure results and single-writer staging ownership.
- Preview-only uninstall disposition; project data is retained by default and no delete tool exists in this slice.
- Allowlisted release manifest excluding medical writing, real projects, credentials, databases, backups, caches and logs.
- Synthetic acceptance isolation, deterministic digests and root identity without absolute-path disclosure.

## Remediation closed before acceptance

Independent round 1 found two P3 items. Codex added synthetic-root enforcement to `uninstall_plan_main`, documented `MM_MONITORING_OFFLINE=1`, and added the corresponding rejection regression. The same reviewer session independently confirmed both closed with no P0-P2 regression.

## Decisive evidence

- Frozen contract: `reviews/medical_monitoring_r7_slice09e_local_distribution_contract_v0_2_20260831.md` (`781a17d64da7d040e3781d29dfe8dc169292931c691cf2fa8f1bb336ffed3c15`).
- Governed execution audit: passed for `mm_r7_slice09e_implementation_20260831`.
- Focused suite after final remediation: `45 passed`.
- Combined R1 + R7 + 09E before the final one-line gate/doc/test change: `897 passed, 19 warnings`; the final changed surface is covered by the 45-test focused suite.
- Ruff: all checks passed. Compileall: passed.
- Independent conference: Pi/cms-router/minimax-m3:xhigh, same session `01a055aa-23bd-7000-b4ae-0b0f5157b20b`, two rounds, no fallback.
- Conference review gate: passed.
- Ports 8911/5174/8984: stopped at acceptance.
- No real project, external model, browser, service startup or deletion was used.

## Medical-writing boundary

No Slice-09E edit targeted `deploy/medical_writing_local` or medical-writing source. The focused boundary test passed. A fresh all-files aggregate is not used as an immutability claim because that directory contains parallel-development logs and bytecode; current source-only aggregate observation is `ec1282f944b4455141d8e83936f668031659b9ff2c2174d9b895024cbf95bf4e`, without attributing unrelated parallel changes to this slice.

## Remaining accepted limitations

- PID liveness treats cross-user `PermissionError` as live; appropriate for this synthetic single-user scope.
- PID reuse is not bound to process start time; no safety defect was reproduced in this scope.
- Listener discovery is macOS `lsof` based; Windows packaging is not claimed.
- The checked-in deploy directory is a shell and source inventory, not evidence that runtime dependencies, start scripts or a distributable installer are present.

## Next safe action

Reconcile all R7 requirements and prior Slice-01 through Slice-09 records in an R7 phase review. Only after that independent phase review may R7 be closed. Before any R8 real-project read or model invocation, freeze and independently accept an R8 source-admission and anti-overfitting contract.
