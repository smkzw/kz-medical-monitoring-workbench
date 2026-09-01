Continue the same bounded edit session. Codex has not accepted the first implementation.

Hard boundaries:
- Work only inside the current workspace (`.`).
- This is a bounded corrective edit round. Modify only the four newly created implementation/audit files named below; all pre-existing files remain read-only.
- No network, dependency install, service, browser, real data, product path, medical-writing path or port 8911.
- Runner-managed output path: `runs/pi_medical_monitoring_r1_integrated_closure_20260810_followup.md`. Never write it with a tool; return the report in your final response.

Read these files only:
- `context/medical_monitoring_r1_integrated_closure_20260810_context.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/scripts/run_integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_INTEGRATED_CLOSURE_GAP_AUDIT.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1`
- `poc/medical_monitoring_ai_native_r1/tests`

Read the current files you created and the task context. Do not modify any pre-existing accepted module, test, UI slice or data file. You may revise only the four newly authorized files from the first pass (and still need no README change).

Codex reproduced the following acceptance failures against the current implementation:

1. P2 false replay/resume claim. Running `run_integrated_closure()` a second time after a successful run raises `StoreError: illegal analysis transition complete -> running`. Running once with `skip_ai=True` and then trying to continue raises `IdempotencyConflictError` because the deterministic AE/MH objects are regenerated with different time-bearing content. The current tests only reopen and read; they do not replay or continue.
2. The four-unit manifest hides material work. AE/MH discovery happens before the facts work unit begins, while Patient Journey and Query generation are folded into one generic projection unit. This is not a truthful detailed progress denominator.
3. The controller-produced AI candidate is a dead-end: QC and audience outputs verify deterministic AE/MH only. The AI result must remain candidate-only, but its persisted raw/candidate evidence must be explicitly consumed by QC and represented as review support in the integrated audience bundle; it must never become a canonical fact or an established risk by itself.
4. Failure/skip currently leaves downstream items pending indefinitely and sets `EvidenceState.COMPLETE` even when the integrated chain is incomplete. Mark downstream work explicitly blocked/failed with audience-safe reasons and keep evidence/output states truthful.
5. The CLI says it requires a new directory but accepts a non-empty unrelated directory, omits `recovery.json` from its conflict list, and uses `default=str` instead of the existing domain serializer.

Required correction:

- Implement real idempotent completed re-entry: same Store/run and same frozen input return the stored closure result without new transport, new facts, new artifacts, new audit events or manifest revision. Conflicting frozen input fails closed.
- Implement real partial continuation across Store close/reopen using a deliberate bounded interruption hook (for example after facts or after AI) and durable intermediate objects. Do not solve the timestamp conflict by editing accepted AE/MH code or by silently rewriting prior objects. Persist and reconstruct the exact prior intermediate result using existing domain serialization contracts, or another equally explicit immutable approach.
- Use a manifest whose work units visibly cover at least input/snapshot confirmation, deterministic fact/candidate derivation, AI candidate review, QC, risk dashboard, Patient Journey/Profile-Timeline, and three-part Query drafts. Begin each work unit before its actual work. All terminal audience counts must come from the ledger.
- QC must bind both deterministic coverage/candidate-fact separation and the controller attempt's verified raw/candidate evidence. The audience bundle may expose a clearly candidate-only AI review-support section, but no AI output may enter `CanonicalFact` or become an established risk without an accepted existing authority path.
- On AI failure/skip, close dependent units as `blocked` with Chinese audience-safe reasons, do not set evidence complete, do not publish, and make `project_audience_progress` truthfully show that the run ended with unfinished work instead of appearing forever active.
- Tighten the CLI to an absent or empty caller directory, include every output filename in conflict checks, and serialize with `to_jsonable`/canonical JSON conventions.
- Add tests that actually perform completed re-entry and interrupted Store-close/reopen continuation, asserting transport counts, audit/artifact/fact counts, manifest revision and outputs. Add tests for AI evidence consumed by QC, separate journey/query work units, truthful failure progress/evidence state, and non-empty CLI directory refusal.
- Update the gap audit so it distinguishes the first-pass failure and the corrected proof. Do not claim that static UI fixtures are now runtime-connected.

Run focused and full R1 tests. Return a compact delta report with exact commands/results, current hashes and remaining unproven boundaries. Do not write the runner-owned report path and do not claim R1 overall acceptance.
