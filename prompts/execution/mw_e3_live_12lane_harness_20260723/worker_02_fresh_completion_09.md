You are a fresh Hermes/aishuo/cms-model W2 execution worker. Read and comply
with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`, and the
closest project `AGENTS.md`. Current routing remains Hermes until
2026-07-25 01:00 Asia/Shanghai.

Read first:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_08.md`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_parent.mjs`
- all `frontend/tests/final_release_12lane_isolation_*.mjs`

Hard boundaries:

- Write only the W2 files above and W2 tests named
  `final_release_12lane_isolation_*`.
- Do not edit W1, W3, W4, product source, fixtures, protocols, credentials,
  stable runtimes, or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_fresh_completion_09.md`.
  Return the report in final text; never write that path.

Codex independently reproduced a destructive bypass against acceptance_08:

```
const iso = await allocateLane(...);
const owned = Object.getOwnPropertySymbols(iso).find(s => iso[s] instanceof Set);
iso[owned].add(victim);
await cleanupAllocation(iso);
```

Observed: `ownedSymbolFound=true`, the cleanup `removed` list contained the
pre-existing victim directory, and `sentinelAfter=false`. A Symbol property is
discoverable and object spread/copy also carries enumerable Symbol properties.
The report's claim that callers cannot inspect or forge the private Symbol is
false.

Implement the real authority boundary:

1. Store owned paths only in a module-private `WeakMap` keyed by the exact
   allocation object returned by `allocateLane`. Do not place the path Set,
   capability, token or cleanup authority on the returned object's string or
   Symbol properties. Freeze the public allocation object after construction.
2. `cleanupAllocation(iso)` must use only `weakMap.get(iso)`. A spread copy,
   structured clone, Proxy, prototype clone, JSON round-trip, manually forged
   object, modified object, or object carrying copied Symbols must yield no
   deletable paths. It may clean the exact genuine allocation object.
3. Return snapshots only from inspection helpers. No exported function may
   accept a path for registration or mutate the private owned-path Set.
4. Preserve validated crash resume: `allocateLane` may create a new genuine
   allocation object from the exact manifest only after existing canonical
   lane/project/attempt/evidence/runtime/profile/task-root/non-symlink checks
   pass. Forged/mismatched/outside-root manifests fail closed.
5. Add a behavioral red sentinel reproducing Codex's exact
   `Object.getOwnPropertySymbols` exploit against the old design. Then prove
   symbol enumeration, spread copy, Proxy, prototype clone, JSON clone,
   mutation attempts, forged manifest/marker, symlink and sibling paths all
   leave the victim sentinel intact.
6. Now that W3 added the missing backend contract model, rerun the genuine
   green parent, deterministic readiness failure, timeout, malformed locator
   and true two-invocation resume. Do not weaken an assertion when a case fails.
7. Keep exact exit/report agreement, immutable durable identity and zero
   process/port/listener leakage.

Run syntax checks and every W2 suite. Report exact exports, exact attack
outcomes, commands, exit codes, one-to-one counts, two-run identities, runtime
disposition and residual uncertainty. No product-AI/browser/DOCX/Word claim.

End exactly:
`WORKER_02_E3_FRESH_COMPLETION_09_COMPLETE`
