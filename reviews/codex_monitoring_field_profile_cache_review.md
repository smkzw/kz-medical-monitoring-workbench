# Codex Review: monitoring_field_profile_cache

Date: 2026-07-30
Delegated-agent output: not used; the user requested direct implementation in
the isolated workspace.

## Verdict

Pass for the requested backend cache slice.

## Boundary Check

- Changes are limited to medical-monitoring backend contracts, profiler,
  repository/router integration, focused tests and this task record.
- No frontend, medical-writing, protocol/rule-template or runtime data was
  changed.

## Codex Verification

- Focused and adjacent medical-monitoring regression: 417 tests passed.
- Ruff passed on all changed Python and test files.
- `py_compile` passed on all changed Python and test files.
- Tests prove a repeated formal field-mapping start does not reload normalized
  rows and per-job current-revision checks do not reload them before or after
  the provider call.
- Corrupt, semantically tampered, content-drifted, binding-drifted and
  profiler-contract-drifted entries fail closed.

## Delegated-Agent Output Review

No delegated output was used. Codex reviewed the actual implementation and
test behavior directly.

## Residual Risk

- No cache retention/garbage-collection policy is implemented.
- Cache hits trust the repository's immutable `replace_rows` digest and current
  counts/schema rather than rescanning every row JSON byte.
- Runtime activation and a real 1 GB timing measurement were intentionally not
  performed because the requested slice excluded runtime mutation.
