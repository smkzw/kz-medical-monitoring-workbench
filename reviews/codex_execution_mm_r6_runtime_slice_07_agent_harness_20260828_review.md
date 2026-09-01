# Codex Execution Review: mm_r6_runtime_slice_07_agent_harness_20260828

## Verdict

`ACCEPT_PENDING_INDEPENDENT_REVIEW` for the isolated slice-07 adapter candidate.
Final candidate SHAs at this gate: source
`0546c10c51a57795c521b2f605276e02c06c676bfe8625268863d8ddc961a515`, tests
`57326dced117c1ae29499b265bdd7a1859ae375e05b56e094843725141147155`, receipt
`fd61f5483360476d4f76d6a9f61642fe83aa69799a64f7aefb36cd44c126d98d`.

## Worker Outputs

- `worker_01` implemented profile registry/layering/alias/identity in Cursor session
  `250ac59e-84f9-40db-a319-d47c967c1e12`.
- `worker_02` implemented the OMP print adapter, public catalog, preflight, argv, invoke and
  receipt gates in Cursor session `74d75b70-9c76-4250-af68-5a56f578ba8f`.
- `worker_03` built the acceptance matrix, ran both real smokes and wrote evidence in Cursor
  session `d5a47ffa-76b8-45a9-8824-0dd9499d00bb`.
- All used the declared Cursor `auto` route in one pass with no fallback. Their concurrent
  shared-file writes were not treated as final state; Codex reconciled the final filesystem.

## Manager Assessment

No manager was declared by the live route. Codex inspected the merged source/tests/receipt and
owned integration, repair and final verification.

## Boundary And Hermes Transport

The governed execution route was Cursor CLI `auto`; Hermes was not used as a transport. Writes
stayed inside the declared R6 POC, its exact allowlist adjacency, and task records. Product
services/frontend, medical-writing content and real projects remained outside the change set.

## Codex Independent Verification

- Closed four inherited create-only allowlist failures by adding only the three new slice-07
  paths to the four exact prior allowlists.
- Found and repaired three fail-open classes missed by workers: profile-id-only selection did
  not rebase to the registered model template; forged frozen-profile identity was not checked
  before preflight/invoke; an injected successful preflight and unsafe invocation id could
  bypass binding/path expectations. Added focused negative tests.
- Added catalog/provider identity binding and expected-unit uniqueness checks.
- Grok independent round-1 exposed first-valid-object/incidental-brace NDJSON fail-open. Codex
  changed the parser to last-valid whole assistant chunk (or whole fenced JSON), routed a single
  OMP event envelope through the same extractor, removed brace-fragment promotion, and added four
  adversarial tests plus catalog-model-id/exit-code tightening.
- Final focused suite: `35 passed`; full POC suite: `763 passed`.
- The focused suite contains a parent-asserted 9-cell normal/`-O`/`-OO` ×
  `PYTHONHASHSEED=0/1/42` identity/argv probe.
- Codex reran authentic synthetic OMP smokes after the repairs: MTPLX full selector at
  `medium` and DeepSeek V4 Flash at `max` both exited 0, parsed `smoke_unit`, had zero missing
  units, `analysis_complete=true`, and `fallback_used=false`.
- Medical-writing protection remained 542 files with aggregate
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`;
  ports 8911/5174 had no listener. No product service, frontend, browser, OCR, real project or
  medical conclusion was used.
- Scope remains limited: this proves adapter contract/connectivity only, not product wiring,
  long-running session resume/cancel, medical quality, R6 overall or R7 acceptance.

## Cleanup Decision

Run execution audit and independent conference first. Archive only runner process material after
both gates pass; keep the contract, receipt, reviews, metrics and acceptance record durable.
