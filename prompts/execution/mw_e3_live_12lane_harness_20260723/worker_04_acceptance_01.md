You are Hermes/aishuo/cms-model Worker 04, a bounded first-line execution Agent.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the closest workspace `AGENTS.md`, and current files before editing. This assignment
is a deterministic validator-construction pass. It is not a real E3 run, product-AI
run, browser acceptance, Microsoft Word acceptance, or release decision.

## Dispatch Stop Gate

Do not start implementation until Codex has accepted W2 and W3 and has replaced every
`CODEX_DISPATCH_FILL_*` token below with observed values. A worker must treat an
unresolved token, missing report, missing command list, hash mismatch, or non-complete
completion marker as a hard precondition failure. Do not infer acceptance from prose,
an earlier report, process exit alone, or a green self-test.

Return one of these stable precondition codes and make no writes when applicable:

- `W4_W2_NOT_ACCEPTED`
- `W4_W3_NOT_ACCEPTED`
- `W4_ACCEPTED_SOURCE_HASH_DRIFT`
- `W4_W1_AUTHORITY_LINEAGE_INCOMPLETE`
- `W4_ZERO_CASES`

The following W1 snapshot is frozen and already observed:

| Item | Frozen value |
|---|---|
| W1 final report | `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_oracle_authority_acceptance_01.md` |
| W1 report SHA-256 | `fcdb24388100742076ff3a794978ee15fdb95c8248a4404fef1a480c5490b404` |
| W1 command | `node frontend/tests/final_release_12lane_oracle_qc.mjs` |
| W1 result | exactly `80 passed, 0 failed` |
| `final_release_12lane_config.mjs` SHA-256 | `672dceef2e4a788b415fcf0dc6693d625149440e4ccdc3ad110d2ef480d50f0c` |
| `final_release_12lane_oracle_manifest.mjs` SHA-256 | `d76e2d58194dea64782e6e34f31777ed188a376489c141ce91177b49f17b43cf` |
| `final_release_12lane_oracle_qc.mjs` SHA-256 | `0fc97896b6817f4c5748f49003b6a320d7f08bf7fe394c7756572707929c2024` |

Before dispatch, Codex must fill and verify this W2/W3 snapshot. These are deliberately
blocking placeholders because both acceptance_04 runs were still in progress when this
contract was written:

| Item | Codex dispatch value |
|---|---|
| W2 final accepted report | `CODEX_DISPATCH_FILL_W2_REPORT_PATH` |
| W2 report SHA-256 | `CODEX_DISPATCH_FILL_W2_REPORT_SHA256` |
| W2 exact completion marker | `CODEX_DISPATCH_FILL_W2_COMPLETION_MARKER` |
| W2 accepted source manifest, path -> SHA-256 | `CODEX_DISPATCH_FILL_W2_SOURCE_HASH_MANIFEST` |
| W2 fixed accepted command list and exact counts | `CODEX_DISPATCH_FILL_W2_COMMANDS_AND_COUNTS` |
| W3 final accepted report | `CODEX_DISPATCH_FILL_W3_REPORT_PATH` |
| W3 report SHA-256 | `CODEX_DISPATCH_FILL_W3_REPORT_SHA256` |
| W3 exact completion marker | `CODEX_DISPATCH_FILL_W3_COMPLETION_MARKER` |
| W3 accepted source manifest, path -> SHA-256 | `CODEX_DISPATCH_FILL_W3_SOURCE_HASH_MANIFEST` |
| W3 fixed accepted command list and exact counts | `CODEX_DISPATCH_FILL_W3_COMMANDS_AND_COUNTS` |

If W2 or W3 legitimately changes a W1-frozen file, stop with
`W4_ACCEPTED_SOURCE_HASH_DRIFT`. Codex must rerun and reaccept all 80 W1 tests, then
update the frozen W1 report/source snapshot before W4 may start. Worker 04 may not
rewrite the snapshot or silently accept drift.

## Sources To Read

Read at minimum:

- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `plans/codex_execution_mw_e3_live_12lane_harness_20260723.md`
- the frozen W1 report and three W1 files above
- the Codex-filled final W2 report, source manifest, and fixed command list
- the Codex-filled final W3 report, source manifest, and fixed command list
- all accepted W2/W3 harness files named by those manifests
- `frontend/tests/cross_indication_e2e_config.mjs`
- current `frontend/tests/final_release_12lane_structure_qc.mjs`

The initial list is a starting set, not a tool prohibition. Read additional in-scope
test contracts and task-scoped fixtures only when needed. Record every additional
source used in the final report.

## Write Boundary

Allowed writes only:

- `frontend/tests/final_release_12lane_structure_qc.mjs`
- `frontend/tests/final_release_12lane_behavior_qc.mjs`
- `frontend/tests/final_release_12lane_evidence_qc.mjs`
- `frontend/tests/final_release_12lane_docx_word_handoff.mjs`
- optional `frontend/tests/final_release_12lane_ooxml_qc.py`
- optional `frontend/tests/final_release_12lane_qc_suite.mjs`
- task-scoped synthetic golden and bad fixtures below
  `frontend/tests/fixtures/final_release_12lane/`

Do not edit config/oracle, W2, W3, production source, stable runtimes, credentials,
authoritative inputs, accepted evidence, or any report path. Do not install a package.
Do not call product AI, ClinicalTrials.gov, OCR, translation, a browser, LibreOffice,
Microsoft Word, or any external document renderer in this assignment.

The runner owns:
`runs/execution/mw_e3_live_12lane_harness_20260723/worker_04_acceptance_01.md`

Never write that path. Return the complete report in final text so the runner can
persist it.

## Objective And Four Independent States

Build a deterministic executable acceptance layer without fabricating real execution.
The report must keep these four states independent:

1. `validator_selftest`: validation code plus golden/bad fixtures.
2. `real_e3_evidence`: evidence from future real 12-lane product runs.
3. `ooxml_package`: a future real exported DOCX package inspected structurally.
4. `word_native_handoff`: future Microsoft Word open/navigation/render acceptance.

Each state has its own `status` from `passed|failed|blocked|not_run`, case counts,
evidence references, failures, and stable codes. No state may be derived from another.
In this assignment:

- only `validator_selftest` may become `passed`;
- `real_e3_evidence` must be `not_run`;
- `ooxml_package` must be `not_run` even if a synthetic DOCX fixture proves the
  package validator works;
- `word_native_handoff` must be `not_run`;
- `product_ai_called` must be `false`;
- `release_accepted` must be `false`.

A synthetic golden fixture is proof about validator behavior only. It is never proof
that the product, product AI, 12 lanes, a real DOCX, or Microsoft Word passed.

## Exact W1 Matrix And Authority Contract

Validate executable data, not source-string presence. All cardinality checks must
assert a nonzero exact count before iterating.

The matrix is exactly 12 unique lanes:

- indications: RA, AD, UC; exactly 4 lanes each;
- phases: I and III; exactly 6 lanes each;
- entry modes: `from_zero` and `synopsis_import`; exactly 6 lanes each;
- each indication x phase cell has exactly one lane per entry mode;
- exact keys:
  `RA_I_SCRATCH`, `RA_I_SYNOPSIS`, `RA_III_SCRATCH`, `RA_III_SYNOPSIS`,
  `AD_I_SCRATCH`, `AD_I_SYNOPSIS`, `AD_III_SCRATCH`, `AD_III_SYNOPSIS`,
  `UC_I_SCRATCH`, `UC_I_SYNOPSIS`, `UC_III_SCRATCH`, `UC_III_SYNOPSIS`.

Exact route cardinality:

- `small_molecule_oral`: 7
- `biologic_injection`: 4
- `topical_local`: 1

Exact design-pressure cardinality:

- `healthy_sad_mad`: 3
- `sad_mad_first_in_patient`: 3
- `background_therapy_placebo`: 1
- `active_comparator`: 1
- `interim_analysis_treatment_switch`: 1
- `vehicle_placebo_phase3`: 1
- `rescue_re_randomization_ole`: 1
- `placebo_induction_maintenance_switch`: 1

Source-mode rules:

- all 6 `from_zero` lanes have no synopsis path, synopsis hash, synopsis fixture, or
  source override;
- all 6 `synopsis_import` lanes have an exact, indication/phase-compatible source;
- `UC_I_SYNOPSIS` is the standalone UC Ib DOCX and preserves internal version/date
  separately from filename date;
- the other 5 synopsis lanes use versioned exact PDF page extracts;
- override-as-success is forbidden in every lane.

For each of these five lanes, validate the complete chain:
authoritative protocol -> extraction manifest record -> exact extract -> lane product
input. Validate canonical paths, NCT, indication, phase, physical page range, protocol
SHA-256, extract SHA-256, extract page count, extraction-manifest identity, lane key,
authority class, fixture status, and `is_product_input=false` on the full protocol:

| Lane | NCT | Physical pages | Extract pages |
|---|---|---:|---:|
| `RA_I_SYNOPSIS` | `NCT03156023` | `3-6` | 4 |
| `RA_III_SYNOPSIS` | `NCT02629159` | `9-19` | 11 |
| `AD_I_SYNOPSIS` | `NCT04668066` | `12-18` | 7 |
| `AD_III_SYNOPSIS` | `NCT03745638` | `12-19` | 8 |
| `UC_III_SYNOPSIS` | `NCT02407236` | `25-39` | 15 |

Exactly five `protocol_authority` records must be non-null. The standalone
`UC_I_SYNOPSIS` record must have null protocol authority. A full protocol path may
never appear as a synopsis product input.

`frontend/tests/cross_indication_e2e_config.mjs` contains the legacy
AD/PNH/OBESITY/SLE four-indication configuration. It is not authority for lane
identity, fixtures, artifacts, chapters, cardinality, gate applicability, source
lineage, or accepted values in this suite. A W3 file may reuse only a named generic
constant whose value is independently compared with and exactly equal to the accepted
12-lane contract. Any legacy indication key or legacy authority leaking into a real
12-lane result is a failure.

## Validator Requirements

### A. Structure And Behavior

Replace the stale structure QC. Do not retain checks for old RA hashes, PsO wording,
old parent loop/function names, `mkdtemp`, `stopProcess`, route substrings, or mere
function-name presence.

Do not use source text searches as behavior proof. Call exported validators/helpers or
run the accepted parent/W2/W3 tests. A dead function, unused string, manually assigned
boolean, or simulated child result cannot pass a behavior gate.

The suite must:

- execute the frozen W1 command and require exactly 80/0;
- execute every Codex-filled W2 command and require its exact accepted counts;
- execute every Codex-filled W3 command and require its exact accepted counts;
- verify accepted source/report hashes immediately before tests and again before
  writing the W4 report;
- fail on missing fixed commands; do not use globs as a substitute for an enumerated
  W3 list;
- await every asynchronous case; no sync wrapper may launch an unawaited callback;
- count zero cases as `W4_ZERO_CASES`;
- treat missing fields and unknown statuses as failures.

### B. Real-E3 Evidence Validator

Build the validator now, but exercise it only against synthetic golden/bad fixtures.
The future real-evidence mode must require exactly 12 lane bundles and all 18
applicable artifacts per lane:

`input_manifest.json`, `output_manifest.json`, `process_ownership.json`,
`journey_trace.json`, `service_receipts.json`, `source_receipts.json`, `ai_runs.json`,
`study_definition.json`, `chapter_matrix.json`, `candidate_sets.json`,
`citation_qc.json`, `browser_qc.json`, `docx_qc.json`, `figure_scale_qc.json`,
`word_handoff.json`, `lane_report.json`, `gate_results.json`,
`synopsis_import_receipt.json`.

Applicability must be explicit. A non-applicable artifact needs a source-bound reason
allowed by the exact lane contract; an absent artifact cannot be silently treated as
non-applicable. Validate bundle and artifact schema versions, immutable file hashes,
lane/project/runtime/source/allocation identity, cross-file referential integrity, and
stable-runtime before/after equality.

Reject at least:

- dry-run or synthetic evidence presented as a real product run;
- wrong lane, project, runtime, allocation, source, job, run, request, artifact, or
  output identity;
- cross-lane/project/runtime locator reuse;
- missing, malformed, stale, unresolved, prematurely cleared, or falsely reconciled
  durable locator;
- status/result/artifact disagreement or status used in place of `/result`;
- failed/cancelled/interrupted work without explicit terminal reconciliation;
- incomplete required-stage checkpoint or resumed duplicate POST;
- missing included chapter, zero included chapters, partial chapter traversal, or a
  required chapter excluded without a persisted source-bound design decision;
- stale candidate, lost retry replacement, missing new candidate identity, or rewrite
  without authoritative terminal result;
- half-adoption, flat-vs-nested working-copy mismatch, missing selected suggestion,
  sibling-state corruption, non-idempotent replay, or replacement loss;
- missing citation, broken citation target, missing reference entry, or missing
  deterministic citation reindex after source import/adoption;
- missing or unbound study-flow figure when applicable;
- missing scale/assessment image, relationship, source identity, or readability
  metadata when applicable;
- missing/corrupt DOCX, output/source hash mismatch, or DOCX from another lane;
- credential, bearer token, API key, cookie, authorization header, private request
  body, or unredacted secret leakage;
- legacy four-indication authority leakage.

Receipt validation must distinguish:

1. server-returned public provider/model/policy/task/job/run/artifact identity, which
   must never be invented;
2. client-computed SHA-256 of recursively canonicalized exact raw status and result
   DTOs, both required and distinct;
3. server input/output/policy fields that may be unavailable and must be represented
   honestly rather than fabricated.

AI roles require the actual server-exposed provider/model identity. Product backend
roles such as CT.gov, citation resolution, and DOCX export may legitimately expose
`model=null`. Every receipt still binds lane, project, step, service role, endpoint
class, task/job/run as applicable, status hash, result hash, artifact IDs, timestamps,
terminal state, and request/idempotency identity where the real contract exposes it.

### C. Golden And Bad Fixtures

Create a complete synthetic golden fixture set for validator self-test only. Create
targeted bad fixtures so each major defect class fails with its expected stable code
and does not rely on an unrelated earlier failure. Include at minimum:

- wrong matrix/cardinality, route count, design-pressure count, or legacy-config leak;
- broken protocol -> manifest -> extract -> lane lineage for each link type;
- wrong extract page count/range/hash and protocol presented as product input;
- synopsis mismatch or override-as-success;
- dry-run presented as real;
- stale status/result, corrupt/cross-lane locator, and premature locator clear;
- incomplete checkpoint and duplicate resume POST;
- incomplete/forged receipt and status/result hash substitution;
- first-chapter-only, zero included chapters, and unjustified exclusion;
- stale candidate, lost replacement, half-adoption, sibling mutation, replay mismatch;
- missing citation/reindex;
- missing study-flow figure;
- missing scale/assessment image;
- corrupt/mismatched/incomplete DOCX;
- credential leakage.

Golden and bad fixture counts must be nonzero and reported by gate class. Every bad
fixture invocation must exit nonzero and emit its stable primary code. No fixture may
contain a real credential or claim to be real E3 evidence.

### D. Structured OOXML Package Validator

Allow a dedicated Python helper because OOXML is ZIP plus XML. Use Python `zipfile`
and `xml.etree.ElementTree`, or an already-installed and license-compatible structured
XML library if its use is recorded. Do not parse XML with regular expressions or
string counts. Do not install LibreOffice, a commercial engine, or a new dependency.

The package validator must fail closed and structurally inspect:

- ZIP/package integrity, required content types, relationships, and non-dangling parts;
- section order and dynamic chapter applicability;
- an unnumbered TOC title;
- real Word Heading 1-4 paragraph styles and multilevel numbering bindings;
- TOC, table-list, figure-list and reference fields; bookmarks and internal hyperlinks;
- title page structure;
- synopsis as its own outer table, including required nested tables and actual bullet
  paragraph properties where the accepted template requires them;
- Chinese run fonts as Songti and Latin/digit fonts as Times New Roman;
- black body text and black table borders where applicable; no unintended blue text or
  borders;
- first-line indentation for applicable body paragraphs;
- real editable Word tables for printed tables, distinct from layout-only tables;
- study-flow SVG/vector relationship, or an explicitly permitted high-resolution
  fallback with dimensions/DPI/readability metadata;
- scale/assessment image relationships, source identity, dimensions and readability
  metadata;
- figure/table numbering and corresponding indexes;
- headers, footers and page numbering;
- no unresolved template token or placeholder;
- package hash and lane/export/source linkage.

A synthetic OOXML fixture can pass the validator self-test but cannot set
`ooxml_package.status=passed`. Real package acceptance requires a future real product
DOCX whose hash is bound to a real accepted lane.

### E. Word-Native Handoff

Build and self-test the handoff-manifest generator. It may emit a real handoff manifest
only after a future real DOCX passes `ooxml_package`. The manifest must include:

- absolute DOCX path and SHA-256;
- project, lane, source, export job, evidence bundle and OOXML report identities;
- expected TOC/table/figure/reference navigation and bookmark targets;
- pages/elements requiring visual inspection;
- explicit Microsoft Word actions for field refresh, navigation, styles, layout,
  headers/footers, figures, scale images and print readability;
- reviewer, timestamp and result placeholders that cannot default to accepted.

This assignment does not open Word. `word_native_handoff.status` remains `not_run`.

## Fixed Execution Order

The dispatch copy must contain no unresolved placeholders. Run in this order:

```bash
# 0. Hash preflight: compare every W1/W2/W3 report and accepted source with this contract.
#    Stop before writes/tests on mismatch.

node --check frontend/tests/final_release_12lane_structure_qc.mjs
node --check frontend/tests/final_release_12lane_behavior_qc.mjs
node --check frontend/tests/final_release_12lane_evidence_qc.mjs
node --check frontend/tests/final_release_12lane_docx_word_handoff.mjs
# If present:
python3 -m py_compile frontend/tests/final_release_12lane_ooxml_qc.py
# If a suite entrypoint is created:
node --check frontend/tests/final_release_12lane_qc_suite.mjs

node frontend/tests/final_release_12lane_oracle_qc.mjs

CODEX_DISPATCH_FILL_W2_FIXED_COMMANDS_EXACTLY

CODEX_DISPATCH_FILL_W3_FIXED_COMMANDS_EXACTLY

node frontend/tests/final_release_12lane_structure_qc.mjs --mode=validator-selftest --json-stdout
node frontend/tests/final_release_12lane_behavior_qc.mjs --mode=validator-selftest --json-stdout
node frontend/tests/final_release_12lane_evidence_qc.mjs --mode=validator-selftest --fixture-root=frontend/tests/fixtures/final_release_12lane
node frontend/tests/final_release_12lane_docx_word_handoff.mjs --mode=validator-selftest --fixture-root=frontend/tests/fixtures/final_release_12lane
# If a suite entrypoint is created, it reruns/coordinates the same enumerated commands;
# it may not replace or hide their individual results.
# Run only when that optional file was created:
node frontend/tests/final_release_12lane_qc_suite.mjs --mode=validator-selftest --fixture-root=frontend/tests/fixtures/final_release_12lane

# Final hash postflight: repeat the full accepted source/report comparison.
```

Codex must replace `CODEX_DISPATCH_FILL_W2_FIXED_COMMANDS_EXACTLY` and
`CODEX_DISPATCH_FILL_W3_FIXED_COMMANDS_EXACTLY` with the enumerated W2/W3 acceptance_04
commands before dispatch. A glob, report prose, generic "run all tests", or omission
is `W4_W2_NOT_ACCEPTED` or `W4_W3_NOT_ACCEPTED`, respectively.

Every command result must record command, exit code, duration, case counts, failures
and output hash. Any command failure, count mismatch, zero cases, unknown status,
unawaited test, missing fixture, unexpected write, or source hash drift fails W4.

## Required Machine-Readable Report

Emit one JSON report and a concise Markdown explanation. The JSON must contain at
least:

```json
{
  "schema_version": "mw_e3_w4_qc_v1",
  "acceptance_level": "deterministic_validator_only",
  "source_snapshot": {
    "w1": {},
    "w2": {},
    "w3": {},
    "preflight_verified": false,
    "postflight_verified": false
  },
  "preconditions": [],
  "validator_selftest": {
    "status": "not_run",
    "case_counts": {},
    "fixture_counts": {},
    "evidence": [],
    "failures": []
  },
  "real_e3_evidence": {
    "status": "not_run",
    "lane_count": 0,
    "artifact_count": 0,
    "evidence": [],
    "failures": []
  },
  "ooxml_package": {
    "status": "not_run",
    "docx_path": null,
    "docx_sha256": null,
    "evidence": [],
    "failures": []
  },
  "word_native_handoff": {
    "status": "not_run",
    "evidence": [],
    "failures": []
  },
  "lane_cardinality": {},
  "fixture_authority": {},
  "gate_results": [],
  "case_counts": {},
  "lane_results": [],
  "artifact_counts": {},
  "bad_fixture_results": [],
  "command_results": [],
  "changed_files": [],
  "additional_sources_read": [],
  "failures": [],
  "product_ai_called": false,
  "word_native_status": "not_run",
  "release_accepted": false
}
```

Do not omit a field because the corresponding activity did not run. Use explicit
`not_run`, zero, empty array, or null values. Unknown states fail closed.

## Acceptance And Completion Marker

Acceptance for this Worker 04 assignment requires:

- every dispatch precondition verified;
- W1 remains exactly 80/0;
- every accepted W2/W3 fixed command passes with its frozen exact count;
- all changed JavaScript syntax checks and any Python syntax check pass;
- all validator self-test golden fixtures pass;
- every bad fixture fails nonzero with its expected stable primary code;
- all validator gate classes execute at least one case;
- preflight and postflight accepted-source hashes match;
- no out-of-scope write and no prohibited service call;
- the report keeps real E3, real OOXML, Word-native and release acceptance false/not-run.

End exactly with `WORKER_04_E3_QC_COMPLETE` only when all deterministic validator
acceptance conditions above pass. Otherwise end exactly with
`WORKER_04_E3_QC_BLOCKED`.
