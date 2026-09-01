# Same-session follow-up: verify P3 closure

Continue in the same `general_single_object` session. Codex chose to close both low-cost P3 items before acceptance:

1. `distribution.uninstall_plan_main` now applies `_enforce_acceptance_synthetic` to both `distribution_root` and `output_dir` before creating output.
2. The Chinese README now documents that synthetic/offline acceptance must set `MM_MONITORING_OFFLINE=1`, and that `start` then refuses to start services and is not real-install readiness evidence.
3. Added `test_acceptance_runner_rejects_non_synthetic_uninstall_root`; focused suite is now `45 passed` and compileall passes. No service, browser, model, real project, deletion, or medical-writing write occurred.

Read the changed source/test/doc directly. Verify that the patch closes your P3 #1 and #2 without creating a regression or expanding scope. Reassess all severity findings. Return the complete original conference schema. Use only `ACCEPT_R7_SLICE_09E_LOCAL_DISTRIBUTION_SYNTHETIC_OFFLINE` if every P0-P2 remains closed; otherwise give exact blocking evidence. Do not edit files and do not claim a real install package, R7 phase completion, or R8 readiness.
