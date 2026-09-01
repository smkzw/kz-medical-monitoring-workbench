# medical_monitoring_ai_native_r3_rule_ai

Isolated POC slice: vendor-neutral, JSON Schema 2020-12 compatible contract for
converting Chinese natural-language risk rules into structured `RuleCandidateDraft`
objects, a strict single-object parser, an immutable field catalog, a Chinese
structured prompt contract, and an R1→R3 workflow bridge.

This is the isolated `medical_monitoring_r3_nl_rule_adapter` package.  The
contract/parser layer is stdlib-only; the workflow bridge imports frozen R1/R3
public contracts lazily.

## Contract and parser

- **JSON Schema 2020-12 contract** (`schema.py`): the single authoritative
  schema document. `additionalProperties: false` at every level; operator enum
  kept byte-identical to frozen R3 `CONDITION_OPERATIONS`.
- **Immutable field catalog** (`catalog.py`): `FieldSpec` / `FieldCatalog`
  infrastructure with per-field allowed operators and value types. **No built-in
  default catalog** — production callers must supply an explicit catalog.
  Representative synthetic catalogs for tests live in `tests/fixtures_catalogs.py`.
- **Strict single-object parser** (`parser.py`): accepts exactly one JSON object;
  rejects Markdown fences, prose wrappers, multiple JSON values, duplicate keys,
  undeclared keys, unknown fields, invalid operators, type mismatches (including
  bool-as-int and non-finite numbers), and missing/empty `extracted_from`.
  Requires an explicit `FieldCatalog`. Typed failure kinds. Parser required/
  allowed keys and enums are derived from the JSON Schema (single source of truth).
- **Chinese structured prompt** (`prompt.py`): deterministic, vendor-neutral
  prompt payload binding schema hash + catalog fingerprint; requires an explicit
  `FieldCatalog`; never includes simulation records.

## Workflow bridge

- **Workflow bridge** (`workflow.py`): consumes the frozen R1
  `CapabilityAttemptResult` (not a bare `AdapterRun`) produced by a real
  `ApiCapabilityRuntime` with an injected transport.  Enforces fail-closed
  blocking gates with distinct, testable reasons: terminal R1 states
  (partial/truncated/failed/timeout/cancelled), missing raw-output provenance,
  raw JSON-RPC/request identity drift, missing candidate artifact, incomplete
  coverage, non-canonical frozen request input, input-hash chain inconsistency,
  profile/binding identity mismatch, source revision mismatch, candidate
  artifact link/coverage/commit/negative-authority drift, non-string candidate
  payload, candidate/raw divergence, parse failures, nonempty assumptions (R3
  has no assumptions field), and absent `extracted_from` phrases.  Converts
  only fully-covered no-blocker candidates to frozen R3 `RuleDraft`; preserves
  original rule text verbatim.
- **Frozen identity builder** (`build_capability_input`): deterministic R1
  capability input payload from `PromptPayload` + project/source identifiers,
  including capability kind/version, exact rule text, schema hash, catalog
  fingerprint, prompt payload hash and full prompt payload.
- **Durable provenance** (`ConversionProvenance`): frozen object with attempt id,
  monitoring run id, node id, profile fingerprint, binding id, provider, model,
  selector, adapter version, input hash, raw output ref, candidate artifact id,
  catalog fingerprint, schema hash, prompt payload hash and parsed candidate
  content hash.  No secret values.
- **Exact candidate text** (`extract_candidate_text`): returns the model's exact
  output string (rejects mappings); verifies the same string is sealed in
  immutable `RawOutputProvenance.raw_output_json`.
- **Local simulation** (`simulate_draft`): deterministic wrapper around frozen
  R3 `simulate_rule`; never calls a model, never writes back to raw output.
- **Three scope recommendations** (`scope_recommendations`): exactly
  `current_snapshot`, `full_history`, `future_only` in fixed order.  Bound to
  the supplied draft (rejects mismatched project/draft/content hash).  User
  titles are `本次数据`、`全部历史数据`、`仅后续数据`; the explanations state what
  will actually be checked and never expose the internal effective-date field
  name.
- **Explicit activation** (`activate_draft`): forces `is_machine=False` and
  `user_confirmed=True`; delegates to frozen R3 `activate_rule` (the only path
  to a `RuleActivation`).

## Run tests

```bash
cd poc/medical_monitoring_ai_native_r3_rule_ai
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
```

## Boundaries

- Writes only under `poc/medical_monitoring_ai_native_r3_rule_ai/**`.
- Does not modify frozen R1/R2/R3, product source, medical-writing subsystem,
  or real-project files.
- Does not start services or listeners; port 8911 stays stopped.
- No model/API/harness calls; synthetic data only.
