# D08 runtime follow-up 1 — remove text-driven semantics and make tests root-runnable

Resume session `019fff62-1955-7000-8e3e-09cbac6f32cd`. This is one consolidated remediation pass on your existing D08 runtime implementation. Do not broaden scope or touch frozen D08 artifacts, D01-D07, medical-writing files, services, or port 8911.

Codex independent verification found two blocking defects:

1. From the workbench root, the required command
   `python3 -m pytest -q -p no:cacheprovider poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py`
   fails collection in four modules because `from tests.test_d08_adapter` resolves incorrectly. Make all D08 tests runnable both from the workbench root and from the R4 POC directory, without changing non-D08 tests.

2. `d08_evaluator.py` branches on free-text `mutation_context.mutation_description` and maps English prose/substrings to dispositions (`_PROPAGATION_HINT_SUBSTR`, `_QJ_HINT_SUBSTR`). This is prohibited fixture-text coupling and fails the user's cross-protocol/data-structure generalization requirement. The frozen contract explicitly defines structured propagation result values `in_sync/stale/derived_missing/producer_not_evaluable/ambiguous_chain/not_applicable/lineage_supersede_handoff`; model the relevant closed structured facts in the runtime types and make evaluation depend only on structured fields. Likewise, wrong-subject relation handling must use an existing or new closed structured status/fact, not prose.

Because the frozen catalog has three under-specified cases (053, 135, 148), the **test-only adapter** may translate their catalog input into the new structured facts at the parsing boundary. The production runtime must be invariant to arbitrary edits/removal/translation of `mutation_description`. Do not branch on case/fixture/oracle/manifest/test IDs in either runtime or adapter. Prefer a generic parsing rule based on existing typed structured facts; if the frozen artifact literally lacks the fact, keep any legacy prose bridge isolated in the test-only adapter and clearly label it as frozen-artifact compatibility, never in `mm_r4` runtime.

Also inspect identity evaluation: it currently maps free-form English `reason_codes` text and substrings to dispositions. Replace prose routing with closed structured reason/result codes or facts as far as the frozen v0.6 contract permits. A test-only compatibility mapping is acceptable only at adapter parsing; the runtime must not interpret natural-language sentences/substrings as semantics. Add closed enum validation for every new decision field.

Required new tests:

- root-directory and R4-directory collection/import robustness;
- mutation-description invariance: replace descriptions with unrelated Chinese/English prose and empty strings while structured facts stay fixed; results/leaves remain identical;
- structured propagation result mutation changes the outcome appropriately and rejects unknown values;
- structured wrong-subject/site status drives fail-closed behavior without description text;
- identity reason/result semantic tests use closed codes, and arbitrary prose cannot change disposition;
- static scan forbids runtime references to `mutation_description`, `_HINT`, and prose-substring decision tables.

After remediation run from the **workbench root**:

1. `python3 -m pytest -q -p no:cacheprovider poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py`
2. full R4 and R1/R2/R3 suites;
3. scoped Ruff and py_compile;
4. frozen hashes; confirm 8911 stopped.

Return exact changed files/hashes, exact commands/results, and residual risk. Do not claim acceptance; Codex and a fresh verifier own done.
