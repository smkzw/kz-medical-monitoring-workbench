# Slice 3 AE/MH Audience Workbench — Data Contract

## Purpose

`build_data.py` projects accepted Slice 1 synthetic AE/MH results into a
classic-script payload for the audience workbench:

```text
window.MM_R1_DATA = {...};
```

The file is meant to load under `file://` with no `fetch`, no CDN, and no
server. Candidates remain candidates; formal AE/MH facts remain separate.

## Authorized files (worker 01)

| Path | Role |
|---|---|
| `build_data.py` | Read-only Slice 1 importer + deterministic generator |
| `data/mm_r1_data.js` | Generated classic script (`window.MM_R1_DATA`) |
| `tests/test_data_contract.py` | Determinism / locator / delta / spine contract tests |
| `docs/DATA_CONTRACT.md` | This note |

Accepted Slice 1 sources under `poc/.../src` and `poc/.../tests` are
**read-only** for this slice.

## Payload surface

Minimum keys:

- `fixture_marker` / `synthetic_only` / `disclaimer` / `ai_boundary`
- `snapshot_lineage` / `run_lineage`
- `analyses.n` / `analyses.n1` (full synthetic analyses; N is prior for N+1)
- `project_dashboard` / `site_dashboards` / `subject_profiles` / `subject_timelines`
- `source_rows` keyed by `SYNTHETIC|snapshot=...|table=...|row=...`
- `queries` / `counterevidence` / `coverage` / `candidate_fact_separation`
- `delta_groups` with `current` / `new` / `escalated` / `carry_forward` /
  `resolved` / `not_evaluable`
- `progress` (deterministic completed static run)

## Semantics guards

1. Candidate counts never inflate reported AE/MH counts.
2. High/severe absence is `carry_forward` (or not-evaluable), never silent
   resolution; `absence_is_not_resolution` remains true.
3. Profile and Timeline share the same `temporal_spine_id` and byte-equivalent
   `temporal_spine` payload.
4. Generated JS contains only synthetic identifiers and no absolute filesystem
   paths.
5. Generation is byte-deterministic (frozen `now_iso`).
6. Each top-level Query carries `risk_identity_keys` derived from overlapping
   evidence locators. Consumers must not guess a Query binding from subject ID
   alone because one subject may have multiple concurrent risks and Queries.

## Regenerate

```bash
.venv/bin/python poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/build_data.py
.venv/bin/python -m pytest -q \
  poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/tests/test_data_contract.py
```
