# Codex Conference Review: medical_monitoring_r1_framework_persistence_adr_20260809

Date: 2026-08-09

## Verdict

**PASS WITH EXPLICIT R1-OPEN GATES.** The architecture decision is accepted for
the next isolated R1 validation. It is not product adoption, production
durability evidence, a shared-runtime migration, or an R1 completion decision.

## Boundary Compliance

- All reads and writes remained under the medical-monitoring R1 POC and this
  task's `context/`, `plans/`, `prompts/`, `runs/`, `logs/`, `reviews/` and
  `metrics/` surfaces.
- No product source, medical-writing subsystem, shared `.venv`, lockfile,
  service, real project, credential, port or user configuration was modified.
- The conference was read-only for participants. Codex alone wrote the ADR,
  matrix and task records.
- Same-day official-source/license/security evidence from Slice2 was reused
  because the pins and assumptions were unchanged; no new dependency was
  installed.

## Participant Outputs Reviewed

- `general_grok45`: first pass exited without a valid work product (170-byte
  progress sentence, stop reason `cancelled`). One authorized same-session
  completion on session `2dc54980-0b8e-49ca-a732-59996f62ed9b` produced a
  complete 24,174-byte report, stop reason `end_turn`, no fallback. Incorporated.
- `general_pi_qwen38`: the time policy rewrote the declared primary to
  `cms-smk/cms-model`; that route and the declared `cms-smk`, `opencode-go` and
  `deepseek` fallbacks all failed health before session creation. No valid
  report exists. Not incorporated; recorded as a coverage limitation rather
  than silent agreement.

## Conference Panel Review

The valid independent challenge made five explicit dispositions:

1. framework-neutral Graph IR + SQLite + content-addressed artifacts: ACCEPT;
2. LangGraph 1.2.10: ACCEPT WITH GATES as the next isolated validation adapter;
3. Agent Framework Core 1.13.0: ACCEPT WITH GATES as a conformance/reference
   adapter, with checkpoint-after-domain-commit residual preserved;
4. Temporal 1.31.0: DEFER with requirement-driven reopen conditions;
5. any R1-complete claim: REJECT while API/harness, failure, ModeContract and
   ClaimCoverageLedger gates remain open.

It also correctly identified the Python 3.9 shared runtime versus candidate
Python ≥3.10 packaging gap and recommended retaining GraphPort-only as both the
minimum path and rollback path.

## Main-Venue Codex Review

Codex accepts the panel's dispositions with one terminology control: the ADR
uses “下一轮隔离验证的首选编排适配器” instead of an unqualified “主框架”. This
prevents users or later implementers from treating LangGraph as domain authority
or approved product runtime.

`ADR-002-provisional-langgraph-orchestration-adapter.md` affirms ADR-001, pins
the validated LangGraph components and security controls, preserves historical
FAIL→PASS evidence, keeps Agent Framework's residual visible, tightens Temporal
reopen/stop conditions, lists R1 open gates and defines full rollback.

`R1_ADAPTER_FAILURE_MATRIX.md` separates graph-engine adapter evidence from the
still-open AI Capability Adapter contract. This avoids the most likely false
closure: using 113/113 graph-engine tests as evidence that API/harness
partial/truncated/cancel/resume/late-callback behavior already works.

## Codex Independent Verification

- Re-read current System Design v1.1, R0-R8 plan, ADR-001, dependency/security
  decision, spike evidence and accepted Slice2/Slice3 reviews.
- Current Slice1 deterministic suite: `103 passed in 0.70s`.
- Markdown table-shape and referenced-file existence checks passed.
- Current SHA-256 anchors:
  - ADR-002: `759ea8f1f1ca2968256ab6c853e60b66dc91b4de12d38858835036dea1778a4a`
  - failure matrix: `66519bcc779ab29456edc2fbd3e635721ce715f8f38b5aa7701ff7dce73ccc9a`
  - ADR-001: `899f4ff4c227201b648f755bef1dafb7815f1c54fe0d6f54e5b5269fbdb24979`
  - dependency decision: `c5bbbfaa0c0af0ba7c3350cf63f3c61281808f255b35d6cd8365805271a23d3f`
  - spike evidence: `9ca3da15de913267d988787fcc1f06c424b643b123ee7a269c279e7a102e9998`
- The disposable candidate venvs were intentionally cleaned after Slice2, so
  the 113/113 candidate suites were not reinstalled or rerun. Their accepted
  command/output evidence remains in Slice2 records. No new browser run was
  needed because this task changed no audience-facing runtime.

## Final Decision

1. **Affirm** Graph IR, SQLite domain Store, CAS artifacts, audit chain and
   publication gate as the permanent framework-neutral authority boundary.
2. **Use LangGraph 1.2.10 only as the preferred adapter for the next isolated
   validation**, behind GraphPort and outside product/shared runtime.
3. **Keep Agent Framework 1.13.0 as reference**, not primary, until its
   checkpoint ordering residual is falsifiably resolved or a later ADR drops it.
4. **Keep Temporal deferred** until durable cross-process/multi-day requirements
   and a failed local recovery gate justify a disposable server/worker spike.
5. **R1 remains in progress.** Next safe construction target is the shared AI
   Capability Adapter contract with one synthetic API adapter and one synthetic
   harness adapter plus its failure matrix.

Hermes workflow guard and runner records are accepted as routing evidence only;
they do not substitute for the local tests, files, hashes or Codex acceptance.
