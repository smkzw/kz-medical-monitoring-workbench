Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09c_implementation_20260830`, role `worker_03`.

Continue the same worker_03 session. Do not restart or broaden scope.

Codex combined the current implementation suites and found one deterministic contract defect:

`test_verifier_maps_root_head_tamper_to_anomaly` raises `ProjectAuditError: project_audit_tail_mismatch` from `_append_started()` instead of returning the fixed Chinese `发现异常` DTO. A tampered root audit chain is evidence the verifier must classify; it must not attempt an ordinary audit append before it can safely report the anomaly.

Repair the smallest coherent cause in `project_verifier.py` and its focused tests. Requirements:

1. Verify the root project-audit chain before `verification_started` append, or otherwise catch only the stable audit-integrity errors and produce `发现异常` without weakening fail-closed behavior.
2. Do not silently repair the head, append over tamper, delete events, or report `需重新恢复` for a proven hash/head mismatch.
3. Preserve the every-successful-verifier-call started/completed event rule when the existing chain is valid.
4. Add/adjust focused tests for head tamper, payload tamper and valid repeat verification.
5. Re-run `test_project_verifier.py`, `test_project_audit.py`, product-router verification tests and compile checks. Do not touch technical-log files or unrelated systems.

Return a compact handoff with changed files and exact results. Codex remains final authority.
