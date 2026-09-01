You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner's current workspace (`.`); do not resolve or
  access any parent, sibling, production, real-project or medical-writing path.
- Do not read or modify production paths.
- This is an explicitly authorized Worker-01 edit round. Write only the five
  Worker-01 paths listed in the task context; all other paths are read-only.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_runtime_20260817.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r4_d10_runtime_20260817_context.md`
- `AGENTS.md`
- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`
- `context/medical_monitoring_r4_d10_artifact_freeze_acceptance_record_20260817.md`
- `context/medical_monitoring_r4_d09_runtime_final_acceptance_20260816.md`

Then inspect only the D10 frozen artifact/generator/verifier/test files and the
D09 contracts/evaluator/adapter/runtime-closure files that are directly needed
for Worker 01. Do not read real-project or medical-writing paths.

Task:
Implement Work item 1 completely: immutable D10 typed contracts, a test-only
artifact adapter, and a deterministic evaluator in the authorized new files.
Prove exact 312-case disposition/gate plus core/trace/source parity against the
test-side oracle. Runtime code must never import/read artifact files, generator,
oracle, registry, quota, verifier or tests and must not branch on case/fixture/test
identity, mutation metadata/class, `SYN-*` strings, descriptions, or synthetic
revision-hash conventions. Add static closure tests and focused negative tests
for the five final artifact gates. Use no package changes and no network/service.
Run focused tests, D09 artifact 99-test adjacency, compile, Ruff if configured,
and verify 8911 has no listener. If exact parity exposes missing explicit facts,
stop with the exact case/field/fact gap; do not translate mutation metadata into
runtime flags and do not weaken the oracle.

Output schema:
1. `# Hermes Worker 01: medical_monitoring_r4_d10_runtime_20260817`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Runtime Semantics And Anti-Overfit Proof`
5. `## Verification`
6. `## Residual Gaps And Next Slice`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not claim D10 runtime acceptance; Worker 02/03 and independent review remain.
