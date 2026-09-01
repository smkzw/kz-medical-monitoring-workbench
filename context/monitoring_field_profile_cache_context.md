# Task Context: monitoring_field_profile_cache

Created: 2026-07-30 05:57:52
Objective: 为医学监查字段画像实现绑定批次内容身份、源绑定修订和 profiler 合同版本的可审计、可失效、完整性校验失败关闭缓存，不绕过 V13 正式 API 与独立 AI
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `AGENTS.md`
- `context/monitoring_p10_input_revision_compatibility_recovery_20260730.md`
- `services/api/app/monitoring_ai_field_profiler.py`
- `services/api/app/monitoring_batch_repository.py`
- `services/api/app/monitoring_ai_router.py`
- `tests/test_monitoring_ai_field_profiler.py`
- `tests/test_monitoring_ai_api.py`

## Scope

- In scope:
  - content-addressed field-profile cache for immutable monitoring batches;
  - cache identity bound to row/schema content, source binding revisions and
    profiler contract;
  - integrity-checked read, fail-closed recomputation and atomic replacement;
  - formal field-mapping API integration without changing V13/AI semantics;
  - focused backend tests, Ruff and Python compilation.
- Out of scope:
  - frontend;
  - medical-writing;
  - protocol/rule-template behavior;
  - direct runtime/database mutation;
  - V13 candidate reduction, source-revision bypass or AI-result caching.

## Success Criteria

- A second field-mapping start for the same immutable batch does not load all
  normalized row JSON again.
- Any row/schema identity, source binding revision, profiler contract or cache
  integrity mismatch produces a cache miss and full recomputation.
- Cached snapshots pass both byte-level and semantic digest validation before
  use.
- Formal API still submits the complete V13 field set and builds its input
  revision from current server-side source bindings.
- Focused and adjacent tests, Ruff and `py_compile` pass.

## Risk Boundaries

- Do not change the medical-writing subsystem, frontend, protocol/rule-template
  logic or runtime data.
- Do not write directly to the monitoring database.
- Cache corruption must never be interpreted as a valid hit.
- Cache is only for deterministic field profiling; AI candidates and decisions
  remain in their existing repositories and APIs.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 05:57:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 06:05:00: Existing data flow inspected. The formal start route
  currently loads all normalized rows before profiling; current
  `source_bindings` omit binding revision. Chosen design adds a lightweight
  repository identity projection and a content-addressed file cache.
- 2026-07-30 06:08:00: First implementation loop completed. Cache key binds
  row/schema content evidence, current batch revision/state, source
  entry/content/binding revision/binding hash and profiler contract. Snapshot
  and manifest digests are validated before deserialization; any failure
  recomputes and atomically replaces the entry.
- 2026-07-30 06:10:00: Added lightweight listing revision identity. New jobs
  bind `source_binding_revision`; empty values are omitted from hashing so
  previously persisted jobs keep their historical hash. The main runtime
  continues to call `_current_revision_for_job()` through the same helper, but
  listing checks now use the lightweight identity and job-bound
  `profile_sha256`, not complete rows.
- 2026-07-30 06:12:00: Focused cache/API tests passed, including repeated formal
  starts, cache byte corruption, semantically tampered/rehashed cache,
  content/binding/profiler invalidation, row-evidence drift, and AI pre/post
  revision checks without row reload.
- 2026-07-30 06:13:00: Adjacent medical-monitoring AI, mapping, batch repository
  and batch service regression: 417 passed.
  Ruff and `py_compile` passed. No frontend, medical-writing, protocol/rule or
  runtime files were changed.

## Implemented Contract

1. `monitoring_field_profile_batch_identity.v1`
   - current batch ID, project, state, version, expected domains and mapping
     revision;
   - row count plus immutable `replace_rows` row-set digest;
   - schema field count plus recomputed schema digest;
   - each attached source ID, registry entry ID, content SHA-256,
     `binding_revision` and `binding_sha256`;
   - separate content, source-binding and complete identity digests.
2. `monitoring_ai_field_profile_cache_key_v1`
   - exact batch identity above;
   - `monitoring_ai_field_profiler_contract_v1`, field-profile schema and all
     profiler limits.
3. `monitoring_ai_field_profile_cache_manifest_v1`
   - complete batch identity and profiler contract;
   - snapshot size/SHA-256, input/profile SHA-256, creation time and
     self-digest;
   - snapshot written first and manifest last through fsync + atomic replace.
4. Listing revision validation
   - new listing jobs bind source-binding identity in
     `MonitoringAiInputRevision`;
   - the field-profile SHA remains an authorized synthetic source binding;
   - old jobs with an empty source-binding revision retain their previous hash;
   - current revision checks use lightweight SQL only and return an empty
     current revision on source/batch/profile identity failure.

## Residual Risk

- Old content-addressed cache entries are retained for audit and rollback; a
  retention/garbage-collection policy is intentionally not part of this slice.
- The lightweight row content identity trusts the immutable `replace_rows`
  event digest and verifies current row count plus full current schema digest.
  It does not rescan every `data_json` byte on a cache hit, because that would
  recreate the 1 GB performance problem. Direct database mutation is outside
  the supported contract; count/schema drift still fails closed.
- This slice was validated in temporary repositories and API test applications.
  It did not start or mutate the current runtime service/database.
