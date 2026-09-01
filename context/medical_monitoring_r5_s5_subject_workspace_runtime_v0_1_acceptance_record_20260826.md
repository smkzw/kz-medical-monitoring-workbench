# R5-S5 Subject Workspace Runtime v0.1 Acceptance Record

Decision: `ACCEPT_R5_S5_SUBJECT_WORKSPACE_RUNTIME_V0_1`

Date: 2026-08-26 CST

## Accepted scope

The exact eleven-path synthetic/offline, renderer-neutral S5 Subject Workspace
runtime is accepted. It consumes only the previously accepted typed public
authority producers and provides a shared subject identity, temporal spine,
window and selection contract for Journey/Profile/Timeline projections.

This decision does not accept a frontend, browser interaction or visual design,
real project/model data, a clinical conclusion, product/production behavior,
security work or medical-writing.

## Decisive evidence

- exact owned allowlist: 11/11 paths present;
- focused S5 normal/`-O`/`-OO`: `349 passed` in every mode;
- adjacent public-authority regression: `68 passed + 15 subtests`;
- frozen challenge registry: 250/250 structured mutations, 250/250 exact
  oracles, 250 unique mutation tuples;
- real S5 execution: 36 S5-specific rows; accepted graph replay: 10/10;
- hash evidence: 10/10 created runtime/test paths and 51/51 frozen paths match;
- governed execution audit: `ok=true`, three roles complete, no route drift or
  fallback;
- port 8911 stopped; medical-writing protected; no service, browser, real
  project or model run.

## Accepted owned hashes

- `s5_contracts.py`: `39581506e11945f78d07906eeee4bb8ac267171928d20abb1dbe39c5c4094456`
- `s5_authority_adapter.py`: `92a5b163a7865d0353a071bd37e2946f54a38a4f57624e0f9ea6688b5161d0a7`
- `s5_projection.py`: `3f4c81f60f620bfcc56c578887cbab7a6820283b799808c55b7efb7dde247ac0`
- `s5_validator.py`: `6c4011328fc113f67a69b35361f5e401c004a493a042e26fec92bed14ebe239d`
- `s5_runtime_fixtures.py`: `dfc8033f173d02d451a08dbe51f79d4049fb8484879f437516a1c49776d8dc9b`
- `test_s5_contracts.py`: `1c232c09613b7cdec6edbcbe79db4f325f69bd11993f50b5a4444ce4332e248e`
- `test_s5_authority_adapter.py`: `957d13dcfd687514dec7ecd96ba83d3f6ff0f763956b78b744b217192830f5cf`
- `test_s5_projection.py`: `3d22a10b122baf43926d808bc3d299da8e8b24a289e37a3745f3fa63f8a7e543`
- `test_s5_validator.py`: `44b65f929954d1ffc4f9abf35727fae39247e75bfdf794c01ecb441779cec841`
- `test_s5_runtime_challenges.py`: `373e33058602bdc8f0e72a8bbbf380efed0b299a2461e98c27211705f0e51159`
- `r4_r5_s5_subject_workspace_readonly_sha256.json`: `1528e631bf2374592f57b4f18ed2d84749e99af4d158a90852366c93eb99109c`

## Adjacent debt boundary

The full R5 POC suite still has five pre-existing S4 failures: S4 generator and
verifier consequences of one known execution-context source-pin drift, plus a
stale contract-era assertion that no S4 runtime file exists. This task did not
rewrite or rebaseline those accepted historical artifacts. Six S4 bytecode
cache files created during current test activity were removed by exact path;
the dedicated cache gate now passes.

## Next unlocked action

Proceed to R5-S6 as a contract-first tranche: deep links, exact return-context
restoration, density/semantic zoom, keyboard and non-colour encoding, and the
frozen 1,000-event/40-indicator/300-risk performance corpus. Keep 8911 stopped;
S7 remains the first stage allowed to perform product integration and real
browser/visual acceptance.
