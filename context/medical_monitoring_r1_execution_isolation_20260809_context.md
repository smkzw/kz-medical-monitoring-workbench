# Task Context: medical_monitoring_r1_execution_isolation_20260809

Created: 2026-08-09 20:25:33
Objective: 为隔离R1选择并实现可实际强制的AI harness工具、文件系统、网络与子进程边界；仅使用synthetic/offline fixture，不触碰产品、医学写作、8911、真实provider或五个真实项目
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §9 AI Capability Adapter
  and §12 execution/resource boundaries.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R1 step 6/8 and the
  current recovery point.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py` harness execution path.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/adapters.py` frozen binding/profile contract.
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py` and
  `tests/test_failure_injection.py`.
- `poc/medical_monitoring_ai_native_r1/docs/R1_CAPABILITY_RUNTIME_EVIDENCE.md` and
  `docs/R1_ADAPTER_FAILURE_MATRIX.md` accepted residuals.
- Current macOS runtime state and the primary/official sources recorded in this task's decision
  evidence; external content is evidence, not instruction authority.

## Scope

- In scope: compare enforceable macOS-local isolation choices; freeze the smallest synthetic R1
  contract; implement fail-closed harness filesystem/network/process-exec/environment and process
  tree termination boundaries when the selected mechanism is actually available; deterministic
  negative tests and an independent acceptance review.
- Allowed writes: this isolated R1 POC source/tests/docs plus this task's context/review/metrics and
  bounded synthetic test artifacts under pytest temporary directories.
- Out of scope: product migration, medical writing, 8911/service, credentials, real API/provider,
  five real projects, App Store signing/notarization, production-grade hostile-code containment,
  Linux-only sandbox adoption, VM/service installation or changing shared dependencies/runtime.

## Success Criteria

1. A compact decision record compares the current process envelope, macOS native enforcement,
   signed App Sandbox and open-source VM/container alternatives for fit, license, maintenance,
   operating cost, reversibility and residual risk.
2. The chosen R1 route fails closed when enforcement is requested but unavailable; no profile
   metadata alone may be reported as isolation.
3. A synthetic harness can read only declared input/runtime material, write only to its declared
   output area, cannot open network connections and cannot launch an undeclared child executable.
4. Timeout/cancel terminates the isolated process group; the parent records truthful terminal
   state and never treats surviving output as complete evidence.
5. Focused and full isolated tests pass; an independent fresh-context reviewer accepts frozen
   source/tests/evidence. Acceptance remains synthetic/macOS-specific and is not a production
   hostile-code sandbox or R1 overall completion.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not install packages, start a VM/service, alter signing/entitlements, use real network endpoints
  in harness tests, or read real project data. Loopback-only negative probes are allowed when they
  prove network denial without data egress.
- Any native/deprecated/private mechanism must be labeled accurately and must have a fail-closed
  availability check; do not build a false cross-platform abstraction around it.
- Preserve the already accepted capability/raw-integrity contracts and candidate-only authority.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 20:25:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 20:44 CST: Re-anchored after an interrupted patch. The interrupted edit had only
  added the isolation policy type; it had not wired enforcement into `ExecutionProfile` or
  `HarnessCapabilityRuntime`. Current filesystem, not the interrupted output, remained authority.
- 2026-08-09 20:44 CST: Bounded discovery selected the installed macOS Seatbelt path only for
  synthetic R1. Apple App Sandbox is the supported long-term native candidate; Lima/Podman VM is
  the stronger hostile-code candidate with materially higher operating cost. Local observation:
  macOS 26.5.1 (25F80), `/usr/bin/sandbox-exec` present but documented `DEPRECATED`, Lima 2.1.3
  present with no instance, Podman absent. No VM/service/package was started or installed.
- 2026-08-09 20:44 CST: Implemented frozen `HarnessIsolationPolicy`, profile/hash binding,
  parameterized SBPL, fail-closed backend/identity checks, exact executable closure, declared
  read/write roots, network denial, minimal environment, and `start_new_session` + process-group
  termination. Legacy harness profiles remain explicitly unisolated rather than mislabeled.
- 2026-08-09 20:44 CST: Deterministic probes passed: declared read/write succeed; undeclared
  sibling read/write, loopback network and `/usr/bin/true` exec return EPERM; parent-only secret is
  absent; backend disappearance fails before attempt creation; timeout and cancel both prevent a
  delayed child marker. Focused isolation 4/4, complete capability 51/51, R1 core 154/154; scoped
  Ruff passes. Package `__init__.py` still has its pre-existing public re-export F401 baseline and
  was not broadly reformatted.
- 2026-08-09 20:44 CST: Decision/evidence recorded in
  `poc/medical_monitoring_ai_native_r1/docs/R1_HARNESS_ISOLATION_EVIDENCE.md`; independent
  fresh-context review requested against the frozen hashes. Pending reviewer disposition before
  this sub-gate can be accepted.
- 2026-08-09 20:50 CST: Independent fresh-context reviewer `/root/capability_runtime_review`
  returned ACCEPT for this synthetic/macOS sub-gate only after independently reproducing focused
  `4 passed, 47 deselected`, capability `51 passed`, core `154 passed`, and stable frozen hashes.
  Reviewer confirmed fail-closed availability, actual EPERM file/network/exec probes, minimal
  environment, and timeout/cancel process-group cleanup. Residuals remain explicit: deprecated
  backend, system metadata/runtime reads, untested Mach/XPC, possible new-session escape, legacy
  unisolated harness and no real endpoint/project/production claim.

## Accepted Freeze

- `src/mm_r1/capability_runtime.py`:
  `906c48fe1eefc8a9aeb34aafedbbd0c0d74d7b3529c9f5280dd32bf11a2bee9f`
- `src/mm_r1/__init__.py`:
  `5e082c5c586d69b6972e2f5175a1d952be69fbb9562797de208ca5ce89fbcb05`
- `tests/test_capability_runtime.py`:
  `455bc19ab66c6e9c589a09ea3be9400b9ea6a6c41fe6915b66b8f0441042acf6`
- Verdict: ACCEPT for execution-isolation R1 synthetic/macOS sub-gate; R1 overall incomplete.
- Next safe action: implement a framework-neutral authoritative manifest work-unit ledger and
  structured progress feed for honest background progress, still synthetic/offline and isolated.

## Corrective Recheck (2026-08-09)

- Re-running the documented `.venv/bin/python` command exposed that the synthetic test profile had
  not declared the active virtualenv as read-only runtime material. Seatbelt correctly denied
  `.venv/pyvenv.cfg`; this was a test-environment declaration gap, not a silent sandbox bypass.
- `tests/test_capability_runtime.py` now adds `sys.prefix` to the frozen readable roots only when
  `sys.prefix != sys.base_prefix` and `pyvenv.cfg` exists. The capability runtime and default
  product policy were not changed.
- Corrected verification: focused `.venv` isolation 3 passed/48 deselected; capability 51 passed;
  R1 core 163 passed; scoped Ruff passes.
- Current corrected test hash:
  `ab1dd16ccf2f14a84b1726aa866f74d66906cd9e249771028e109209cdf83828`.
- The original reviewer freeze remains historical evidence for the prior fixture. Current
  acceptance must use the corrected hash and the independent review attached to the authoritative
  progress task.
