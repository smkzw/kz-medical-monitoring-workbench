You are a fresh-context independent verifier using the Codex CLI compatibility fallback because the native `gpt-5.6-luna` spawn was explicitly rejected by the App runtime. The runner supplies the global Codex instructions; also read and comply with the workbench `AGENTS.md`. This is one independent veto/accept pass, not implementation and not consensus.

## Hard boundaries

- Strictly read-only. Do not modify any file, test, report, prompt, context, plan, source, README, cache, product, medical-writing, real-project, service, or security surface.
- Work only inside the current workbench workspace.
- Do not start port 8911 or any service. Do not read real project data. No external provider/model call or browser is needed.
- Runner-managed output path: `runs/conference/medical_monitoring_r4_d05_final_acceptance_20260812/codex_luna_verifier.md`. Return the complete report in the final response; never write this path yourself.

Initial read set:
- `AGENTS.md`
- `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- `context/medical_monitoring_r4_d05_implementation_20260812_execution_context.md`
- the current eight D05 source/test files under `poc/medical_monitoring_ai_native_r4`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/README.md`

Current filesystem is the only implementation truth. Do not rely on stale Worker-02/03 or manager reports. Verify whether the live snapshot deserves final D05 acceptance.

Acceptance criteria:
1. Frozen contract v1.2 is implemented without overfitting to a real project: dual cutoff, gates, typed anchors, bidirectional assignment and consumption ledger, five exclusive L1 states, not-evaluable behavior, enrollment-aware three-part Chinese Query, priority/machine-close constraints, planned-vs-actual renderer-neutral Journey.
2. The 116-row challenge matrix provides real semantic proof: focus on rows 18/19, 91-96, 102, 105, and whether direct `assert_expected` can self-certify weak builders. Inspect actual tests/functions, not just green counts.
3. Audit the final Worker-03 hashes: fixtures `18626fa1447893bf84a5cef778df67b5eac28ade64b7b8cb34e8b576655fd3b7`; challenge test `101e443d8416afbf707fd94fca60a6192880ad9ccac9380c40ad41839b4b67be`. Confirm the changes only tighten row-102 proof and do not introduce circular proof or mask another discrepancy.
4. Root exports must not overwrite earlier D04/D02 values. README boundary and Chinese-native audience terminology must be appropriate; technical contract docs may use developer vocabulary but audience payload must not leak it.
5. Protected hashes must be stable. Port 8911 must remain stopped. No pycache should remain after checks.

Run decisive read-only checks: focused Worker-03 twice; all D05; full R4; R2; R3; Ruff; import and root `__all__`; 116-row validator; exact hashes; 8911 check. `compileall` writes bytecode, so do not run it in this strict read-only pass; source parsing/import is sufficient.

Output:
- Lead with `VERDICT: ACCEPT` or `VERDICT: REJECT`.
- State exact evidence and any P0-P4 findings. A green test alone is not acceptance.
- State residual limitations: this is synthetic/offline R4-D05, not R5 product UI or real-project acceptance.
- Do not fix anything.
