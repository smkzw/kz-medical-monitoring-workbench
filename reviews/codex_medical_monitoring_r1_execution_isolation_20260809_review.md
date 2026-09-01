# Codex Review: medical_monitoring_r1_execution_isolation_20260809

Date: 2026-08-09
Delegated-agent output: `runs/codex_medical_monitoring_r1_execution_isolation_20260809.md`

## Verdict

ACCEPT for the isolated synthetic/macOS execution-isolation sub-gate only. R1 overall, product
integration, real harness/provider/project execution and production hostile-code containment remain
unaccepted.

## Boundary Check

- Changes stayed inside the isolated R1 POC and this task's context/review/metrics plus the approved
  R1 implementation-plan recovery point.
- Product source, medical-writing subsystem, shared runtime, 8911, credentials, real providers,
  real projects, VM instances and services were not modified or started.
- The runner-owned run report was not manually edited.

## Codex Verification

- Current local macOS reports 26.5.1 (25F80); `/usr/bin/sandbox-exec` exists and its man page says
  `DEPRECATED`; Lima 2.1.3 has no instance; Podman is absent.
- Codex reproduced focused isolation `4 passed`, full capability `51 passed`, R1 core `154 passed`,
  compileall and scoped Ruff success.
- Actual negative probes returned EPERM for undeclared sibling read/write, loopback networking and
  `/usr/bin/true` exec; declared input/output succeeded and parent-only environment data was absent.
- Timeout and cancel killed same-process-group delayed children before marker creation.
- UI/browser/PPT/PDF checks are not applicable to this backend-only slice.

## Hermes

The task was initialized through `hermes_workflow_guard.py init-task`, which selected direct
Codex execution. No Hermes provider/model was dispatched. Independent acceptance used the native
fresh-context reviewer `/root/capability_runtime_review`; Codex retained final authority.

## Delegated-Agent Output Review

Independent fresh-context reviewer `/root/capability_runtime_review` reread frozen source/tests/docs,
reran 4/51/154 checks and returned ACCEPT with stable hashes. It confirmed that unavailable backend
fails before attempt creation and that evidence does not overclaim a production sandbox.

Frozen hashes:

- `capability_runtime.py`: `906c48fe1eefc8a9aeb34aafedbbd0c0d74d7b3529c9f5280dd32bf11a2bee9f`
- `__init__.py`: `5e082c5c586d69b6972e2f5175a1d952be69fbb9562797de208ca5ce89fbcb05`
- `test_capability_runtime.py`: `455bc19ab66c6e9c589a09ea3be9400b9ea6a6c41fe6915b66b8f0441042acf6`

## Residual Risk

- `sandbox-exec` is deprecated and accepted only for this current-macOS synthetic POC.
- System runtime material, global file metadata and untested Mach/XPC surfaces remain outside proof.
- `killpg` covers the same process group, not an adversarial child that creates a new session.
- Legacy harness profiles without an isolation policy remain ordinary `Popen` and must not be
  represented as isolated.
- Signed App Sandbox helper and VM options were researched but not implemented, installed or run.
