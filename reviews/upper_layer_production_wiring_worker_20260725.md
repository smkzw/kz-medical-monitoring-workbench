# Upper-layer production wiring review — 2026-07-25

## Scope

This slice wires the existing durable upper-layer execution service into the
single `ChapterTranslationPipeline` shared by direct and batch writing-reference
translation. It does not modify the translation pipeline, batch orchestrator,
upper-layer execution service, repository, contracts, frontend, or stable
service scripts. No real model was called and no stable service was restarted.

## Implemented

- Added a production DeepSeek upper-layer adapter with server-owned routes:
  - default: `deepseek-v4-flash`
  - escalation: `deepseek-v4-pro`
  - provider: `deepseek`
  - transport: `openai_compatible`
- Reused the existing direct DeepSeek provider builder, including exact
  response-model verification. The production adapter additionally checks the
  provider/model/transport identity on every provider call.
- Centralized reviewed-equivalent prompts for:
  - `document_planning`
  - `post_hy_mt2_integration_qc`
- Kept Hy-MT2 as the only body translator. Neither adapter stage has a Hy-MT2
  callable or a body-translation route.
- Serialized `FlashPlanResult`, `FlashQcResult`, and
  `FlashIntegrationOutcome` into deterministic JSON payloads accepted by the
  durable service and decoded by the existing persisted bridge.
- Added a JSON-safe subclass of
  `PersistedUpperLayerStageExecutorAdapter`. This is required because the real
  batch planner context contains private `DocumentPlannerSegment` dataclasses;
  their source-span IDs remain server-side and are removed from the model
  payload.
- Added a concurrency-safe `ContextVar` owner scope for the historical direct
  translation callable surface. Direct planner/QC calls now route back through
  the same persisted stage API instead of silently invoking the old
  non-persisted Flash callables.
- Injected one pipeline instance into both:
  - `writing_reference_translation_service`
  - `writing_reference_translation_batch_service`
- Added startup recovery for queued and lease-expired running Pro escalations.
  Repository recovery excludes `failed_retryable`, so startup does not repeat a
  failed Pro call without an explicit retry contract.
- Confirmed public direct/batch request models expose no provider, model,
  transport, base URL, or API-key fields.

## Failure classification

- Provider configuration missing or transient provider/network failure:
  persisted as `failed_retryable`; never escalated to Pro.
- Exact response-model mismatch, invalid server route, unsupported stage, or
  HTTP 400/401/403/404:
  persisted as `failed_terminal`; never escalated.
- Deterministically malformed Flash domain output:
  `failed_escalatable`, producing one server-owned Pro escalation.
- Valid but degraded Flash QC with the exact Hy-MT2 map preserved:
  `completed_degraded`, producing one server-owned Pro escalation while
  retaining the usable Flash result.
- Pro may only succeed or fail terminal/retryable; it cannot create another
  escalation.
- QC validates the complete immutable target-map hash and exact string values.
  Duplicate unit ordinals, noncanonical map keys, non-string targets, missing
  units, or target-map mutation fail closed.

## Verification

Commands:

```bash
python3 -m ruff check \
  services/api/app/writing_reference_upper_layer_adapters.py \
  tests/test_writing_reference_upper_layer_production_wiring.py

python3 -m py_compile \
  services/api/app/writing_reference_upper_layer_adapters.py \
  services/api/app/main.py

python3 -m pytest -q \
  tests/test_writing_reference_upper_layer_production_wiring.py
```

Result:

- Ruff: passed.
- Py-compile: passed.
- Focused production-wiring tests: `12 passed`.

Adjacent regression:

```bash
python3 -m pytest -q \
  tests/test_writing_reference_upper_layer_production_wiring.py \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_repository.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_writing_reference_translation_durable_jobs.py \
  tests/test_document_pipeline_round8.py \
  tests/test_writing_reference_translation_batch.py \
  -k 'not http_core_contract_and_span_injection_rejection'
```

Result: `172 passed, 1 deselected`.

The deselected existing test expects a newly accepted asynchronous translation
batch to be synchronously `completed`. The current API contract correctly
returns `accepted`; this known assertion is unrelated to this wiring slice and
was not modified.

## Residual real-run gates

The following are intentionally not claimed:

1. Stable runtime has not loaded this source revision because no restart was
   performed.
2. No real `deepseek-v4-flash` or `deepseek-v4-pro` response was requested.
3. After an authorized later stable restart, runtime readiness must confirm the
   approved direct DeepSeek deployment profile, credential presence, official
   direct base URL, and exact response-model identity.
4. A real direct translation and a real batch translation must each persist
   planning and post-Hy-MT2 QC stage lineage. A deterministic Flash defect must
   produce exactly one Pro child while the Hy-MT2 target map and body-translation
   call count remain unchanged.
5. A controlled queued/expired-running escalation should be observed across an
   actual process restart; a `failed_retryable` Pro record must remain untouched
   until the explicit retry route is invoked.

