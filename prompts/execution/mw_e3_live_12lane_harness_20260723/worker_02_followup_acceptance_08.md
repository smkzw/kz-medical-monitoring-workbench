You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session
before the user-mandated 2026-07-24 01:00 Asia/Shanghai route switch. Read and
comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`.

Codex reran acceptance_07 (isolation 13/0, adversarial 14/0, parent smoke 7/0)
but rejects its security claim after direct source review. Fix this single
authority-boundary root cause and preserve the now-working resume/readiness
behavior.

Read these files first:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_07.md`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- `frontend/tests/final_release_12lane_isolation_adversarial.mjs`
- `frontend/tests/final_release_12lane_isolation_parent_smoke.mjs`

The initial list is a starting set, not a tool prohibition. Read additional
W2-only files when required and record them.

Hard boundaries:

- Allowed writes remain the W2 files above plus W2-only executable tests named
  `final_release_12lane_isolation_*`.
- Do not edit W1, W3, product/stable runtime, fixtures, protocols, credentials,
  source inputs, or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_08.md`.
  The runner owns it. Return the report in final text and never write it.
- Do not weaken, remove, rename away, or replace the genuine two-invocation
  resume, deterministic readiness failure, timeout, malformed locator,
  process-identity, exact manifest, or zero-leak checks with source-string or
  hand-built-object assertions.

Decisive rejection:

`process_ownership.mjs` says `_ALLOC_KEY` is private and unforgeable, but lines
254-255 export both the exact key as `_ALLOC` and the channel getter as
`_getAllocatorChannel`. Any importer can therefore run:

```
const ch = po._getAllocatorChannel(po._ALLOC);
ch.addOwnedDir("victim-lane", arbitraryExistingPath);
await po.cleanupLaneEphemeralDirs("victim-lane");
```

and delete an arbitrary existing directory. Existing tests assert only that a
different Symbol fails and even require `_ALLOC` to be exported. That is false
security evidence.

Required design:

1. No module may export an allocation-channel key, channel getter, owned-dir
   mutator, registration/adoption function, token minting function, or another
   capability that lets an arbitrary importer add an existing path to cleanup
   ownership. Private-by-comment and underscore names do not count.
2. Put allocation plus cleanup authority behind one real module closure. A
   preferred small design is for `runtime_isolation.mjs` to own its private
   allocation registry and expose only:
   - allocation/resume returning an opaque lane allocation object;
   - disposal/cleanup that accepts that exact in-memory opaque object for the
     current process; and
   - a narrowly scoped manifest-validated recovery operation required after a
     process crash.
   Equivalent designs are acceptable only if the public export surface cannot
   register or adopt an arbitrary pre-existing directory.
3. Crash recovery must remain possible. Its persisted authority must be bound
   to exact task root, lane, project, durable attempt/allocation identity,
   runtime child, Chrome-profile child, evidence directory and non-symlink
   canonical paths. Merely writing forgeable JSON or a marker beside an
   arbitrary directory must not make that directory deletable.
4. `cleanupLaneEphemeralDirs(laneKey)` must not remain a public ambient
   lane-name deletion primitive if public state can influence its registry.
   Prefer cleanup through the opaque allocation object held by the parent.
   Recovery cleanup may use the exact validated manifest path already selected
   by the parent, but must fail closed on missing/mismatched identity or paths.
5. Testing-only inspection/reset helpers must not return mutable internal sets
   or grant mutation/deletion authority. A reset helper may clear in-memory
   state but must not accept a path.

Executable adversarial acceptance:

- Dynamically import both ownership and runtime-isolation modules; print every
  exported key. Assert none is `_ALLOC`, `_getAllocatorChannel`, registration,
  adoption, token minting, owned-dir mutation, or an equivalent ambient
  authority.
- Create a real pre-existing victim directory containing a sentinel file.
  Enumerate and call every exported W2 function that can safely accept
  attacker-controlled lane/path/object values. Try forged Symbol, forged
  marker, forged manifest, copied allocation object, modified allocation
  object, wrong lane/project/attempt, symlink path and same-basename sibling.
  The sentinel must survive every attempt and no cleanup result may claim it
  was removed.
- Positive fresh allocation must still be created under the exact task root,
  cleaned after green completion and leave zero assigned-port/process leaks.
- Genuine two-parent-invocation resume must still pass with the same durable
  attempt/allocation/runtime/project identity, `resume=true`, no duplicate
  completed work, final cleanup per policy and zero leaks.
- Deterministic readiness failure, child timeout and malformed/mismatched
  locator cases must remain exact and green.
- Include a red sentinel that fails against the acceptance_07 exported
  `_ALLOC` design, then passes after the fix. The sentinel must be behavioral,
  not a source substring check.

Acceptance:

- Syntax-check every changed file and run all W2 suites.
- Codex expects exact command lines, exit codes, per-suite counts, exported-key
  list, victim sentinel outcome, two-run resume identity values,
  runtime/evidence disposition and zero-leak evidence.
- Report changed files and residual uncertainty honestly. Do not claim W1, W3,
  product AI, browser, DOCX, Word or release acceptance.
- End exactly:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_08_COMPLETE`
