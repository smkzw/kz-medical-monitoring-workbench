# R6 v0.1 synthetic/offline runtime — slices 01–07

Deterministic, offline, synthetic-only implementation of the accepted R6 v0.1
external-report-mode contract. Slice 01 proves that the machine contract, the
frozen fixture catalog, the validator layer, and the metadata oracle agree.
Slice 02 adds immutable report-source registration, deterministic
ReportUnit / ReportClaim / ReviewIssue construction, a frozen expected-review
surface, reverse omission links, and the ClaimCoverageLedger two-gate runtime.
Slice 03 adds the ReportReviewBundle shared identity envelope, annotated
projection (sidecar / proven in_place_copy), original-byte hash retention,
verified-anchor fail-closed gates, optional DRAFT clean-draft provenance,
IssueTransition (reclassified/merge/split), and cross-revision issue diff.
Slice 04 adds immutable three-mode ``ModeContract`` builders, the Run entry
gate (execution basis, entry conditions, cutoff/source revision, carry-forward,
fixed-total, silent mode conversion), generic ``ModeOutput`` identity/
eligibility, daily four outputs, and structured ``affected_query_draft``
(依据/发现/行动项 Chinese projection; draft-only unsent/unclosed).
Slice 05 reuses that ModeOutput envelope for pre_lock four defaults
(``full_risk``, ``revision_impact``, ``check_package``,
``query_revision_package``) with shared authority/cutoff/revision binding and
numeric risk reconciliation — still draft-only, no Query send/PD close.
Slice 06 reuses the same envelope for post_lock_pre_cfdi four fixed-total
outputs (``full_project_report``, ``site_materials``, ``subject_materials``,
``checklist``) bound to one locked snapshot / authority / population totals
with cross-output reconciliation — still system draft-only, no sign/send.
Slice 07 adds an isolated ``ExecutionProfile`` registry and ``omp_print_v1``
adapter. It freezes the MTPLX medium default, preserves explicit DeepSeek V4
Flash max selection, validates public catalog/profile/argv/receipt identity,
and fails closed on malformed output, incomplete coverage, unknown exit state,
tool overreach, or silent fallback. This is adapter connectivity acceptance,
not product integration or medical-quality acceptance.
It produces **no medical
conclusions**, is **not** R6 product/runtime acceptance, and touches no real
projects, reports, services, browsers, OCR, or models.

Status is tracked per work item in the governed worker reports
(`runs/execution/mm_r6_runtime_slice_0*_20260827/worker_0*.md`); Codex is the
final authority for acceptance.

## Source of truth (frozen stable bytes)

| Artifact | SHA-256 |
|---|---|
| `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` (prose) | `1c6fc588335206020389527bf0841bbf57abe227dbea46a2420c0456ed2f1acd` |
| `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json` | `0fca738c19277777de25ce819285ace2e836b2e323e581ce04f52608ce0ed1d7` |
| `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json` | `cb5b30bc8397e022efff6bc7e57b4d23b99f1debff1c405879e42e698444b2dc` |

Accepted in `context/medical_monitoring_r6_contract_acceptance_record_20260827.md`
(`ACCEPT_R6_CONTRACT_V0_1_FOR_SYNTHETIC_OFFLINE_PLANNING`). Contract identity:
`medical_monitoring_r6_external_report_mode_output_contract` v0.1 — 3 modes,
3 pieces, 9 report-unit types, 8 claim statuses, 5 coverage statuses,
16 output kinds, 11 deterministic validators, 16 prohibitions; challenge
matrix: 86 unique single-mutation rows (R6C-001..R6C-086), 12 categories,
49 scenario diagnostic codes, `test_metadata_only == true` on every row.

## Create-only path map

### Slice 01 (accepted; keep read-only)

| Path | Work item |
|---|---|
| `src/mm_r6/__init__.py` | package (also updated by slice 02) |
| `src/mm_r6/contracts.py` | read-only contract/matrix loading + verification |
| `src/mm_r6/fixtures.py` | deterministic baseline fixture catalog + pointer preconditions |
| `src/mm_r6/validator.py` | 11-validator dispatcher + one-replace-per-row executor |
| `tests/conftest.py` | shared read-only pytest fixtures |
| `tests/test_contracts.py` | contract verification + fixture catalog tests |
| `tests/test_validator.py` | validator dispatcher tests |
| `tests/test_challenge_matrix.py` | 86/86 oracle parity + reproducibility tests |
| `evidence/r6_contract_runtime_receipt.json` | read-only evidence receipt |
| `README.md` | slice documentation (this file) |

### Slice 02 (accepted; keep read-only except package/README/allowlist adjacency)

| Path | Work item |
|---|---|
| `src/mm_r6/report_review.py` | source/object (+ coverage APIs by coverage worker) |
| `tests/test_report_review.py` | source/object (+ coverage/ledger tests by other workers) |
| `evidence/r6_report_review_runtime_receipt.json` | verification worker receipt |

### Slice 03 (accepted; keep read-only except package/README/allowlist adjacency)

| Path | Work item |
|---|---|
| `src/mm_r6/report_bundle.py` | Bundle / annotated projection / clean-draft / IssueTransition / revision diff |
| `tests/test_report_bundle.py` | Bundle / projection / draft / transition / revision-diff tests |
| `evidence/r6_report_bundle_runtime_receipt.json` | verification worker receipt |

### Slice 04 (accepted; keep read-only except package/README/mode_output adjacency)

| Path | Work item |
|---|---|
| `src/mm_r6/mode_output.py` | ModeContract / Run gate / ModeOutput / daily Query draft |
| `tests/test_mode_output.py` | ModeContract / Run gate / ModeOutput / Query tests |
| `evidence/r6_mode_output_runtime_receipt.json` | verification worker receipt |

### Slice 05 (accepted; keep read-only except package/README/allowlist adjacency)

| Path | Work item |
|---|---|
| `src/mm_r6/mode_output.py` | pre_lock four payloads + ``build_pre_lock_mode_outputs`` |
| `tests/test_mode_output.py` | pre_lock positive / fail-closed / determinism tests |
| `evidence/r6_pre_lock_output_runtime_receipt.json` | verification worker receipt |

### Slice 06 (accepted; keep read-only except package/README adjacency)

| Path | Work item |
|---|---|
| `src/mm_r6/mode_output.py` | post_lock four fixed-total payloads + ``build_post_lock_mode_outputs`` |
| `tests/test_mode_output.py` | post_lock positive / fail-closed / determinism tests |
| `evidence/r6_post_lock_output_runtime_receipt.json` | verification worker receipt |

### Slice 07 (accepted; limited Agent Harness / ExecutionProfile adapter scope)

| Path | Work item |
|---|---|
| `src/mm_r6/agent_harness.py` | profile registry / freeze / alias + ``omp_print_v1`` catalog/preflight/argv/invoke/receipt |
| `tests/test_agent_harness.py` | offline acceptance matrix, 9-cell determinism, adjacent protection, adapter fail-closed |
| `evidence/r6_agent_harness_runtime_receipt.json` | offline + MTPLX/DeepSeek controlled smoke receipt |

Slice 01–06 sources/tests/receipts remain read-only for slice 07 except the
declared `__init__.py` / `README.md` / adjacency allowlist edits. Model
provider/selector/effort stay in the harness registry only — not in ModeOutput
or other medical business objects. DeepSeek is explicit profile selection only.

## Fixture catalog design (work item 1)

Per the frozen `fixture_binding` of `challenge_matrix.json`:

- `fixture_id` equals `challenge_id`; each of the 86 challenges freezes its
  own complete synthetic candidate document rooted at the top-level key
  `candidate` (mutation pointers are all under `/candidate/...`).
- **Pointer precondition** (verified by construction and re-checkable):
  `single_mutation.path` exists in the fixture and its value is type-aware
  equal to `baseline_value` before mutation.
- **Freeze rule**: every non-mutated field is deep-equal to the canonical
  template (`mm_r6.fixtures.CANONICAL_TEMPLATE`), with the row pointer
  stripped on both sides.
- Nine pointers carry different `baseline_value`s across different rows
  (e.g. `/candidate/cutoff/ref` is `null` for R6C-032 and
  `cutoff-2026-08-01` for R6C-033/R6C-034). Template defaults for those nine
  contested pointers are deterministic documented choices (see the
  `EXPECTED_CONTESTED_PATHS` list in `tests/test_contracts.py`); every
  challenge fixture overwrites its own row pointer with the row
  `baseline_value`, so per-row correctness holds by construction regardless
  of the default.
- **Canonical bytes**: `json.dumps(obj, ensure_ascii=False, sort_keys=True,
  separators=(",", ":"))` UTF-8. Key sorting removes dict hash-order
  dependence, so builds are byte-identical under any `PYTHONHASHSEED` and
  optimizer level (`-O`/`-OO`). Two-pass catalog builds are byte-identical
  (asserted in tests); catalog digest is a fixed-point
  `catalog_sha256` over the manifest without that key.
- Pointer handling is RFC 6901 with `~0`/`~1` unescaping and is
  **fail-closed**: setting a missing path raises `FixtureError` (no silent
  path creation).
- Synthetic data conventions (kept internally consistent for the validator
  layer): rate numerator 5 / denominator 42 with `reported_value 0.119` as
  the declared display value at precision 3 (display_rounding_rule; exact
  rational recomputation stays authoritative for raw values); numerator
  42 subjects ≤ denominator 42 subjects (same population/cutoff,
  count_semantics_rule); `risk.project_member_count 4 == len(member_ids)`,
  `risk.project_total 12 == sum(site_totals)`.

## Shared API (for work items 2 and 3)

```python
from mm_r6 import contracts, fixtures, validator

raw_c = contracts.contract_raw()          # bytes; raises on SHA mismatch
raw_m = contracts.matrix_raw()
c = contracts.contract_obj(raw_c)         # parsed dict (read-only use)
m = contracts.matrix_obj(raw_m)
report = contracts.verify_all(c, m)       # raises ContractVerificationError

rows = m["rows"]                          # 86 rows
for row in rows:
    doc = fixtures.build_fixture(row["challenge_id"], row)   # frozen candidate doc
    # doc["candidate"] is the pre-mutation synthetic document;
    # the row pointer exists and equals row["baseline_value"]
    violations = fixtures.verify_pointer_preconditions(doc, row)  # [] expected

catalog = fixtures.build_fixture_catalog(rows)   # deterministic manifest
bytes_ = fixtures.canonical_catalog_bytes(catalog)  # two-pass identical
viols = fixtures.verify_fixture_catalog(catalog, rows)  # [] expected

# Work item 2 — one replace per row, full content-validator dispatch:
result = validator.execute_challenge(row, c, m)
# result.outcome / .error / .projection / .blocking / .findings
# result.mutations_applied == 1
parity = validator.oracle_parity_report(rows, c, m)  # mismatch_count == 0
```

The validator layer applies exactly one RFC 6902 `replace` per row
(`row["single_mutation"]`) to a deep copy of the fixture document. Because the
frozen contract marks `category_validator_map_normative=false`, it runs all ten
content validators for every row; the governed audit owns the boundary
validator. It then emits canonical
`failure_code` / diagnostic / `blocking` / `outcome` / `projection` via
`challenge_matrix.json` `error_semantics` and `error_code_map`
(49 codes → 11 validators, all `blocking: true`). `R6-C-BOUNDARY-001` stays
outside the 12 content categories.

## Slice 02 source/object API (worker_01)

```python
from mm_r6 import report_review as rr

result = rr.register_report_source(
    raw_bytes,           # report file bytes (synthetic in this slice)
    descriptor,          # project/media/lineage/cutoff/parent fields
    existing_revisions,  # prior ReportSourceRevision dicts
)
# result["status"] in {"registered", "deduplicated"}
# result["report_source_revision"] is immutable; same raw hash dedups

unit = rr.build_report_unit(unit_spec, result["report_source_revision"])
claim = rr.build_report_claim(
    claim_spec,
    result["report_source_revision"],
    identity_algorithm_version="...",
    identity_algorithm_digest="...",
)
issue = rr.build_review_issue(
    issue_spec,
    result["report_source_revision"],
    identity_algorithm_version="...",
    identity_algorithm_digest="...",
)
codes = rr.validate_object_cross_identity(
    result["report_source_revision"],
    units,
    claims,
    issues,
    run_source_revision_id="run-source-...",  # must differ from report
)
# codes == () when cross-identity is closed; otherwise sorted unique
# frozen failure codes (not first-error-only)
chain = rr.rebuild_parent_lineage(report_revision_id, all_revisions)
```

matrix = rr.build_report_review_matrix(
    binding, report_source, units, claims, issues,
    expected_review_surface, reverse_coverage_links,
)
ledger = rr.build_claim_coverage_ledger(matrix)
codes = rr.validate_report_review_matrix(matrix)
# A reasoned not_evaluable unit may close accounting while remaining
# ineligible for a full-report-reviewed claim.

## Slice 03 bundle / clean-draft / revision-diff API

```python
from mm_r6 import report_bundle as rb

projection = rb.build_annotated_projection(
    matrix,
    report_source,
    annotations,
    lossless_in_place_proven=False,  # unproven → mandatory sidecar
)
# projection["annotation_mode"] in {"sidecar", "in_place_copy"}
# projection["source_bytes_hash"] == report_source["report_artifact_id"]
# failed anchors → projection_state=qc_blocked + annotation_anchor_invalid

draft = rb.build_clean_draft(
    matrix, report_source, modifications, requested=True
)
# draft is None when requested=False
# draft["draft_label"] == "DRAFT"; is_final/is_user_confirmed always False

transition = rb.build_issue_transition(
    spec, from_issues, to_issues
)  # reclassified | merge | split

diff_rows = rb.build_revision_diff(
    previous_matrix, current_matrix, transitions=[transition]
)
# incomparable identity/cutoff/revision → revision_diff_state=not_evaluable

bundle = rb.build_report_review_bundle(matrix, projection, draft)
codes = rb.validate_report_review_bundle(bundle, matrix, projection, draft)
# codes == () only when shared identity, anchors, DRAFT gates, and matrix pass
```

## ModeContract / Run gate (slice 04)

```python
from mm_r6 import mode_output as mo

contract = mo.build_mode_contract("daily")  # or pre_lock / post_lock_pre_cfdi
assert mo.validate_mode_contract(contract) == ()
# contract["immutable"] is always True; bytes are stable across rebuilds

run = {
    "project_id": "...", "run_id": "...", "mode": "daily",
    "execution_basis": "full", "data_cutoff": "...",
    "source_revision_id": "...", "carry_forward_run_ids": [],
    # ... common_binding fields ...
    "mode_transition": "explicit_new_run",
}
ctx = mo.default_entry_context_for_mode("daily", run_binding=run)
codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
# Fail-closed codes: mode_entry_blocked | silent_mode_conversion |
# identity_mismatch | cutoff_mismatch | revision_mismatch
```

## ModeOutput / daily Query draft (slice 04)

```python
auth = {"digest": "...", "project_id": run["project_id"], "run_id": run["run_id"],
        "data_cutoff": run["data_cutoff"], "source_revision_id": run["source_revision_id"]}
cov = {**auth, "coverage_digest": auth["digest"]}
qc = {**auth, "qc_digest": auth["digest"]}

change, risk, query, note = mo.build_daily_mode_outputs(
    run, contract,
    authority_refs=auth, coverage_refs=cov, qc_refs=qc,
    findings=[{
        "finding_id": "f1", "risk_id": "r1", "issue_id": "i1",
        "subject_id": "S1", "site_id": "C1",
        "basis": "方案条款…", "finding": "数据线索…", "action": "请核实…",
        "evidence_refs": ["ev-1"],
        "locator": {"path": "AE.AETERM", "record_id": "rec-1"},
    }],
    entry_context=ctx,
)
assert all(mo.validate_mode_output(o, run, contract) == () for o in (change, risk, query, note))
# Query drafts: display_text == basis+finding+action; is_sent/is_closed/is_user_confirmed False
# Fail-closed codes also include: output_not_eligible | authority_mismatch
```

## Running the tests

Python 3 stdlib + pytest only (pytest is already present in the workbench
environment; nothing is installed by this slice).

```bash
cd poc/medical_monitoring_ai_native_r6
python3 -m pytest tests/test_contracts.py -q
# reproducibility matrix (all must pass):
PYTHONHASHSEED=0 python3 -m pytest tests/ -q
PYTHONHASHSEED=1 python3 -O  -m pytest tests/ -q
PYTHONHASHSEED=42 python3 -OO -m pytest tests/ -q
```

## Hard boundaries

- No product/frontend/service/runtime/database/API changes; no third-party
  dependencies.
- No real project, real report, OCR, model/provider, browser, or
  long-running execution; ports 8911 and 5174 must remain stopped.
- No writes outside this POC tree and the governed process directories
  (`plans/`, `prompts/`, `runs/`, `logs/`, `metrics/`, `reviews/`,
  `context/`).
- Fixtures and the receipt are metadata only; they are not medical
  conclusions, not report-review completion, not product acceptance, and not
  real-project evidence.
