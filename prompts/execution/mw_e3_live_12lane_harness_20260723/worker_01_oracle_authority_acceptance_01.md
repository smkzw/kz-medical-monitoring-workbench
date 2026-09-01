You are continuing the same Hermes/aishuo/cms-model Worker 01 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and current files before editing. This is a narrow source-
authority acceptance repair. Do not redesign the 12-lane matrix.

Read these files only:
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_fixture_mapping_completion.md`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope W1 evidence only when necessary and record it.

Hard boundaries:

Allowed writes are only:
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`

Do not edit W2, W3, W4, production source, fixtures, authoritative protocols,
credentials or stable runtimes.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_oracle_authority_acceptance_01.md`.
The runner owns this report path; return the complete report in final text and never
write that path.

Codex reproduced a false-green in the accepted W1 baseline:

- The five PDF synopsis inputs now have authority class
  `versioned_exact_synopsis_extract`.
- `buildProtocolAuthority()` only creates a record for the obsolete
  `authoritative_protocol_synopsis_pages` class.
- Therefore all six synopsis lanes currently have `protocol_authority: null`.
- The QC at the protocol-authority test silently skips null records, so 67 tests pass
  through an empty loop.

Repair the authority lineage without changing the accepted product-input split:

1. Exactly the five PDF-extract synopsis lanes
   `RA_I_SYNOPSIS`, `RA_III_SYNOPSIS`, `AD_I_SYNOPSIS`, `AD_III_SYNOPSIS`,
   `UC_III_SYNOPSIS` must have a non-null oracle-layer `protocol_authority`.
   `UC_I_SYNOPSIS`, whose product input is a standalone exact DOCX synopsis, does not
   require a full-protocol authority record unless an existing authoritative mapping
   explicitly provides one.
2. Each of the five authority records must bind the accepted NCT, canonical protocol
   path, protocol SHA256, synopsis page range, extract path and extract SHA256,
   extraction manifest path/hash or equivalent immutable lineage, authority class,
   READY fixture status and `is_product_input:false`.
3. The product input remains only the exact extracted synopsis fixture. Never put the
   full protocol path or bytes into `product_inputs`.
4. Validate protocol file -> extraction manifest -> extracted PDF -> lane. Recompute
   file hashes from disk in QC; require exact page counts `4/11/7/8/15` for the five
   accepted extracts and exact lane cardinality.
5. Replace skip-null tests with exact cardinality and named-lane assertions. A zero-
   iteration loop must fail. Add negative fixtures/in-memory mutations proving missing
   authority, wrong lane, wrong hash, wrong page range, extract-as-protocol and
   `is_product_input:true` are rejected.
6. Update comments to the current authority class; remove obsolete wording that says
   the extract does not exist.

Acceptance:
- `node --check` all changed `.mjs`.
- Run `node frontend/tests/final_release_12lane_oracle_qc.mjs`.
- Print a deterministic summary showing six synopsis lanes, exactly five non-null
  protocol authorities, each authority's NCT/page range/protocol hash/extract hash,
  and no full protocol in product inputs.
- Report exact test counts and negative-case counts. Do not claim W2/W3/W4, product AI,
  browser, DOCX/Word or release acceptance.
- End exactly with:
  `WORKER_01_ORACLE_AUTHORITY_ACCEPTANCE_01_COMPLETE`
