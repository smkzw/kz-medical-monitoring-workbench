# Codex Conference Review: mm_r7_slice_03_product_mount_acceptance_20260828

Date: 2026-08-28

## Verdict

Pass after revision. Recommend R7 Slice-03 limited offline acceptance.

## Boundary Compliance

- Read-only conference; neither role modified source, started 8911/5174, invoked a product model, or read a real clinical project.
- Both roles used the declared primary route for two rounds in the same session; no fallback or replacement session occurred.
- Hermes was not a transport or participant in this guard-generated conference route; the effective primary routes were Pi/google-antigravity and Grok Build, as recorded in runner logs.
- Medical-writing and frontend remained outside the accepted write surface.

## Participant Outputs Reviewed

- `general_pi_antigravity`: Pi / google-antigravity / Gemini 3.7 Flash high, two rounds, final recommendation accept with no remaining P0-P2.
- `general_grok46`: Grok Build / Grok 4.6 medium, two rounds. Round 1 found one P1 and three P2 evidence/contract gaps; round 2 verified their correction and found no remaining P0-P2.

## Conference Panel Review

- Accepted Grok round-1 findings: project alias scope failed canonical identity; unknown R7 subpaths/wrong methods could return FastAPI `detail`; RunEntry dynamic detail could cross the product boundary; project/DeepSeek assertions did not prove the frozen profile.
- Codex corrected all four at their shared product seam and added direct frozen-profile evidence.
- Excluded one unsupported Pi statement that tests asserted DeepSeek `requested_provider/requested_model`; current accepted evidence is the registered user-config name plus frozen `reasoning_effort=max` and empty fallback list.
- Remaining P3/P4 notes (namespace packaging and future SQLite load behavior) are outside this slice and do not block limited acceptance.

## Main-Venue Codex Review

- Re-read the frozen contract, final router, tests, minimal `main.py` wiring, R7 core public interfaces, receipt, and both conference rounds.
- Verified bootstrap is the only first-creation route; non-bootstrap requests require both SQLite stores.
- Verified path project, persisted project scope, and Run project use one canonical identity, including alias input.
- Verified R7-only Chinese `{code,message}` handling does not change the non-R7 dummy error shape.
- Verified MTPLX medium bootstrap and explicit DeepSeek V4 Flash max/no-fallback through temporary frozen-profile records.

## Codex Independent Verification

- Product-focused suite: 15 passed; independent Grok rerun: 15 passed.
- R7 full suite: 93 passed.
- R6 full suite: 763 passed.
- Adjacent product/principal/route-context suite: 132 passed.
- Changed-file Ruff and compileall: passed.
- Execution audit without conference coupling: passed. The guard's `--require-conference` lookup is same-task-id based and does not recognize the separately linked conference task; conference completeness is therefore established by this review gate and runner logs, not by overstating that flag.
- Ports 8911/5174 remained stopped; medical-writing boundary remained 542 files with aggregate SHA256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`.
- No browser/visual acceptance was required: Slice-03 is a backend product-mount seam with no frontend change.

## Final Decision

Accept Slice-03 only as an offline product-mount slice. This does not accept real model invocation, background execution, progress/resume/cancel, real-project runs, three monitoring modes end to end, frontend behavior, or R7 overall completion.
