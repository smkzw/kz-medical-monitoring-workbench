# Medical Monitoring P9 Source-Only Checkpoint — 2026-08-05

## Current objective

Continue the medical-monitoring subsystem toward the full commercial-release
goal while the authoritative real-loop gate remains closed. This checkpoint
covers only source-level evidence-chain hardening; it is not a runtime/UAT or
clinical-approval record.

## Completed bounded slices in this continuation

| Loop | Surface | Result |
|---|---|---|
| 5.251 | AI quality observation | Exact lowercase digest reads; 29 focused, 777 prior AI suite |
| 5.252 | AI service | Exact profile/source/revision/repair reads; service 451, combined AI 788 |
| 5.253 | AI router | Exact request/status/legacy/adoption matching; router 23, combined AI 792 |
| 5.254 | Daily-run AI locator | Exact present source locator hash; focused 14, adjacent 130 |
| 5.255 | Daily-run repository | Exact shared SHA-256/input validation; focused 31, adjacent 130 |
| 5.256 | Mapping-draft repository | Exact source profile matching; focused 54, adjacent mapping 195 |
| 5.257 | Batch derived-snapshot repository | Exact source-content digest; focused 53, adjacent 52 |
| 5.258 | Real-loop execution evidence | Exact prompt/output digests; focused 15, all real-loop 135 |
| 5.259 | Real-loop acceptance/mode evidence | Exact prompt/mode digests; focused 34, all real-loop 137 |
| 5.260 | Real-loop readiness evidence | Exact source/prompt/upstream digests; focused 22, all real-loop 138 |
| 5.261 | Downstream report-chain evidence | Exact acceptance/execution/revalidation digests; focused 51, all real-loop 142 |
| 5.262 | Daily-run removal/snapshot safety | Unresolved removal identity and unproven full snapshot fail closed; daily-run 23, real-loop 142 |
| 5.263 | Incremental AI diff lineage | Missing/wrong-baseline/unsafe diff cannot enter AI; analysis 17, real-loop 142 |
| 5.264 | Daily diff blocker consumer | UI explains structure/domain/removal/full-proof blockers; 33 pure tests, build passed |
| 5.265 | Project deep-link fail-closed consumer | Unknown explicit project cannot fall back to another study; route 44, pure 33, build 1.76s |
| 5.266 | Risk deep-link fail-closed consumer | Missing current-project risk is explicit and returnable; route 47, pure 33, build 1.86s |
| 5.267 | Subject deep-link fail-closed consumer | Missing current-project subject is explicit and preserved; route 50, pure 33, build 1.98s final |
| 5.268 | Site deep-link fail-closed consumer | Missing current-project center is explicit; pending is distinct; route 54, pure 33, build 1.92s |
| 5.269 | Principal digest exactness | Padded/uppercase identity digests fail closed; principal 17, pure 33, build 1.74s |
| 5.270 | AI current-revision digest exactness | Padded persisted profile digest fails closed; API 27, AI 796, compileall passed |
| 5.271 | Assurance signature digest exactness | Downstream signature token fails closed on non-canonical bytes; focused 4, adjacency 134 |
| 5.272 | Protocol candidate digest exactness | Padded input/frozen evidence digests fail closed; preparation 49, adjacency 121 |
| 5.273 | Evidence-panel hierarchy | Fixed `事实 → 方案 → 规则/计算 → 定位` order; locator disclosure; 33 pure tests, build passed |

## Aggregate verification

- Combined AI, daily-run and mapping source suites: **1116 passed, 5
  deselected, 17 warnings** in 22.67s.
- Combined AI, daily-run, mapping and batch/source suites after 5.257:
  **1221 passed, 10 deselected, 17 warnings** in 25.14s.
- All real-loop contract suites after 5.258–5.260: **138 passed** in 0.40s.
- All real-loop contract suites after 5.261: **142 passed** in 0.42s.
- Daily-run service suite after 5.262: **23 passed** in 0.93s; daily-run plus
  batch-diff suites: **46 passed**, one existing openpyxl warning, in 81.59s.
- All real-loop contract suites after 5.262: **142 passed** in 0.45s.
- Analysis service suite after 5.263: **17 passed** in 1.15s; focused lineage
  subset **7 passed** in 0.66s.
- All **33** frontend medical-monitoring pure test modules after 5.264 passed;
  the targeted daily-diff view includes **27** assertions. Vite builds passed
  in 2.02s and 1.75s with the existing >500 kB main-chunk warning.
- Project deep-link route resolver after 5.265: **44** assertions passed;
  all **33** frontend modules passed again; final Vite build **1.76s** with
  the same existing >500 kB main-chunk warning.
- Risk deep-link resolver after 5.266: **47** assertions passed; all **33**
  frontend modules passed again; final Vite build **1.86s** with the same
  existing >500 kB main-chunk warning.
- Subject deep-link resolver after 5.267: **50** assertions passed; all **33**
  frontend modules passed again; final Vite build **1.98s** (initial 1.78s)
  with the same existing >500 kB main-chunk warning.
- Site deep-link resolver after 5.268: **54** assertions passed; all **33**
  frontend modules passed again; final Vite build **1.92s** with the same
  existing >500 kB main-chunk warning.
- Principal digest contract after 5.269: focused **17** checks passed; all
  **33** frontend modules passed again; final Vite build **1.74s** with the
  same existing >500 kB main-chunk warning.
- AI current-revision digest contract after 5.270: focused router **27** and
  revision subset **5** passed; all non-`real_` AI source suites **796 passed,
  4 deselected, 17 warnings** in 14.61s; compileall passed. Ruff unavailable.
- Assurance signature context after 5.271: focused **4** and assurance/
  identity/runtime adjacency **134** passed in 1.99s; compileall passed; Ruff
  unavailable.
- Protocol candidate digest contract after 5.272: preparation **49 passed**;
  digest/lineage subset **5 passed**; protocol adjacency **121 passed** in
  3.98s; compileall passed; Ruff unavailable.
- Evidence-panel hierarchy after 5.273: all **33** frontend
  medical-monitoring pure test files passed; Vite production build passed with
  **1953 modules transformed** and the existing >500 kB main-chunk warning.
  Live browser/visual acceptance was not run because the formal gate remains
  blocked.
- Changed-module `compileall`: passed.
- Guard prompt preflight and per-slice review-gates: passed with no warnings or
  errors.
- Ruff is unavailable in the current venv/PATH; lint remains unverified.
- Reserved ports 8911, 5174, 8910 and 4173: `EMPTY`.
- A final source audit found no remaining `strip().lower()` digest normalizer
  in `services/api/app/monitoring_real_loop_*.py`; remaining `.lower()` calls
  are only canonical-shape predicates.

## Product files changed in this continuation

- `services/api/app/monitoring_ai_quality.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_daily_run_ai_service.py`
- `services/api/app/monitoring_daily_run_repository.py`
- `services/api/app/monitoring_mapping_draft_repository.py`
- `services/api/app/monitoring_batch_repository.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_mode_coverage.py`
- `services/api/app/monitoring_real_loop_readiness.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- `services/api/app/monitoring_daily_run_service.py`
- `services/api/app/monitoring_daily_run_analysis_service.py`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyDiffView.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyDiffSummary.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyDiffSummary.css`
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.test.mjs`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.test.mjs`
- `services/api/app/monitoring_ai_router.py`
- `tests/test_monitoring_ai_api.py`
- `services/api/app/monitoring_assurance_repository.py`
- `tests/test_monitoring_assurance.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `frontend/src/styles.css` (P9 evidence-panel hierarchy)
- `frontend/dist/` (generated by the verified P9 frontend build)
- `records/active_slices/medical_monitoring_p9_evidence_order_20260805/`
- Their focused regression modules under `tests/`.

## Hard boundary and next action

The authoritative gate is still `mode=read_only`, `status=blocked`,
`medical_approval_granted=false`, `provider_call_permitted=false`,
`runtime_activation_permitted=false`, `write_permitted=false`; formal medical
B6 outcomes remain zero and mode coverage remains empty. Do not start 8911,
5174, 8910 or 4173; do not start services/providers, browser/Playwright/API
login or real projects. The next safe action is another bounded source-only
integrity audit, or—only after authority changes—the formal sequence:
B6 outcomes → source-token/CAS replay → host/runtime identity → real projects
and modes → browser role rounds → release dossier.

## 5.262 source-only safety finding

`MonitoringDailyRunService.process_prepared()` now preserves the existing
`schema_drift` field meaning but adds `drift_review_required` and deterministic
`drift_reasons`. Ambiguous identity/removal (`removal_blocked_keys`) and a
non-true `full_snapshot_proven` value stop the run before `rules_running`.
This is source-level P7 evidence only; it does not alter the blocked authority
state or prove real listing, clinical, browser, AI or commercial acceptance.

## 5.265 source-only deep-link safety finding

`App.jsx` now resolves a requested monitoring `project_id` against the loaded
project membership before selecting any project-scoped consumer. An explicit
non-member remains visible as a recoverable unavailable-link state and cannot
be replaced by the first/initial project. The project selector can recover to a
known project; reset preserves unrelated URL state while clearing monitoring
focus. This is source-level P9 evidence only and does not prove server-side
permission, runtime, browser, real-project, clinical or commercial acceptance.

## 5.266 source-only risk deep-link finding

`MonitoringPage` now treats a requested risk absent from the current project
snapshot as an explicit unavailable focus. It preserves the current project,
does not substitute another risk, and presents a return-to-checklist action.
This is source-level P9 evidence only; stale snapshot semantics, server-side
authorization, browser interaction, real-project and clinical acceptance still
require the blocked formal gate to be reopened.

## 5.267 source-only subject deep-link finding

`App.jsx` now resolves a requested monitoring `subject_id` against the current
project catalog before constructing profile or Timeline reads. An explicit
non-member remains visible as a recoverable unavailable state and cannot be
replaced by the first/default subject. This is source-level P9 evidence only;
server-side authorization, browser interaction, real catalog data and clinical
acceptance still require the blocked formal gate.

## 5.268 source-only site deep-link finding

`MonitoringPage` now checks a site-scope deep link against the current
project's subject and risk-rollup identities. An unavailable center is shown
explicitly and can return to trial scope; an empty identity set remains
`pending` rather than being treated as missing. This is source-level P9
evidence only; server authorization, browser, real-center and clinical
acceptance still require the blocked formal gate.

## 5.269 source-only principal digest finding

`medicalMonitoringPrincipal.mjs` now rejects any identity-bound digest that is
not already an exact lowercase 64-hex SHA-256 string; no trimming or case
conversion occurs. This closes a frontend normalization ambiguity without
claiming server-side authentication or authorization. Runtime, browser,
provider, real-project and clinical acceptance remain blocked by the formal
gate.

## 5.270 source-only AI current-revision finding

`monitoring_ai_router.py` now fails closed when a persisted listing field
profile root or `profile_sha256` is malformed; padded profile digest bytes are
not stripped before revision computation. This is a source-only identity
boundary repair and does not prove provider, runtime, authorization, browser,
clinical or commercial acceptance. The formal gate remains closed.

## 5.271 source-only assurance signature finding

`MonitoringAssuranceAuditContext` now rejects non-canonical non-empty signature
evidence without `str`, whitespace or case normalization. This only hardens the
downstream contract token; it does not verify an e-signature or establish live
authorization, provider, browser, clinical or commercial acceptance. The formal
gate remains closed.

## 5.272 source-only protocol candidate finding

Protocol candidate lineage now rejects non-canonical supplied input digests and
frozen evidence source digests without stripping or lowercasing. This is an
offline evidence-chain repair; it does not prove protocol interpretation,
provider/runtime, authorization, browser, clinical or commercial acceptance.
The formal gate remains closed.

## 5.273 source-only evidence-panel hierarchy finding

The P1-03 evidence presentation gap is now addressed in the frontend source:
the risk disposition and source-evidence views render explicit stages in the
fixed order `1 原始事实 → 2 方案依据 → 3 系统规则 / 计算 → 4 来源定位`.
The first stage only uses frozen listing `primary_summary`/fields already
returned by the source-fragment contract; if no bound listing evidence exists,
the UI states that fact is unavailable rather than using the risk title as a
substitute. Rule rationale and recommended action are shown only in the rule
stage. Locator strings moved into keyboard-accessible disclosure elements while
the existing read-only source-fragment action and project identity checks were
preserved.

This is source/UI evidence only. No backend evidence payload, source capture,
risk identity, runtime, provider, browser, real-project or clinical/visual
acceptance occurred; the formal gate remains `read_only / blocked`.

## 5.274 source-only daily-run rule identity digest finding

Daily-run runtime identity digests are now treated as exact contract bytes.
`monitoring_daily_run_service.py` rejects padded, uppercase, non-string or
otherwise malformed `mapping_content_sha256`, `capability_manifest_sha256`,
`effective_capabilities_sha256` and `rule_identity_sha256` values across the
project-effective, record-applicability, active-mapping, frozen mapping and
persisted-run paths. Pre-execution comparisons no longer trim identity digests;
revision-token text semantics remain unchanged. The main runtime wiring
`_current_monitoring_rule_runtime` now rejects malformed published-rule digest
members before returning the resolver identity, rather than normalizing them.

Verification: focused daily-run service/repository/record-resolver suites
passed **96 tests and 41 subtests**; compileall passed; review-gate returned
`ok=true`. Router/P0 adjacency collection remains unavailable because the
current Python environment lacks `cryptography`; no dependency was installed.
`ruff` is unavailable. This is source-level identity-boundary evidence only;
no provider, runtime, browser, source-token/CAS, real-project, clinical,
visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked`; reserved ports remain empty.

## 5.275 source-only rule-pack identity digest finding

Immutable protocol-rule mapping digests are now canonical at both the rule
factory and repository pack boundary. `_validate_rule_identity()` rejects
padded, uppercase, non-string or otherwise malformed non-empty
`mapping_content_sha256`, `capability_manifest_sha256` and
`effective_capabilities_sha256` values without coercion. Repository pack
uniformity checks validate raw digest bytes with an anchored lowercase pattern;
mapping revision text retains its existing token semantics. A complete
persisted rule-definition with a tampered mapping digest now fails closed on
read, while legacy partial identity still routes to the existing explicit
readiness diagnostic.

Verification: focused rule/factory/repository suite **53 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed**; daily-run,
record-resolver and repository adjacency **96 passed with 41 subtests**;
compileall, source contract scan and review-gate (`ok=true`) passed. The real
MY008 fixture collection remains unavailable because the environment lacks
`cryptography`; no dependency was installed. This is source-level identity
evidence only; no provider, runtime, browser, source-token/CAS, real-project,
clinical, visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## 5.276 source-only protocol source hash finding

Protocol source lineage now rejects non-canonical supplied digest bytes at the
earliest factory boundary. `ProtocolSourceVersion.create()` requires an exact
lowercase 64-hex `content_sha256`; `RuleSourceReference.create()` rejects
padded, uppercase or non-string supplied `source_text_sha256` before comparing
it with calculated source text, while an omitted value still receives the
calculated digest. Persisted protocol-version rows with malformed digest shape
now fail closed on read through the repository boundary.

Verification: focused source/reference/repository-hardening suite **55
passed**; protocol API/lifecycle/review/cross-project adjacency **57 passed**;
daily-run/record-resolver/repository adjacency **96 passed with 41
subtests**; compileall, source scan and review-gate (`ok=true`) passed. Real
MY008 fixture collection remains unavailable because the environment lacks
`cryptography`; no dependency was installed. This is source-level lineage
evidence only; no provider, runtime, browser, source-token/CAS, real-project,
clinical, visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## 5.277 source-only gold/diagnostic case hash exactness

Gold-standard and diagnostic evidence cases now require exact lowercase
64-hex `source_content_sha256` bytes at their factories. The repository's
release-binding validators apply the same raw-byte shape check and bind
locators without lowercasing the digest. Persisted SQLite gold/diagnostic
case reads reconstruct through the strict factories, so padded, uppercase and
non-string digest tampering fails closed while legacy gold rows without
coverage labels retain the existing migration path.

Verification: rule/factory/repository/lifecycle suite **98 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
compileall and source contract scan passed; review-gate **`ok=true`**. Real
MY008 fixture collection remains unavailable because the environment lacks
`cryptography`; no dependency was installed. This is source-level evidence
only; no provider, runtime, browser, source-token/CAS, real-project, clinical,
visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
8911, 5174, 8910 or 4173, services/providers, browser/Playwright/API login or
real projects until the five formal reviewer outcomes are hash-bound and the
source-token/CAS gate is revalidated.

## 5.278 source-only shadow/provisional hash exactness

`RuleShadowRun.create()` now treats the frozen gold case-set digest and every
non-empty diagnostic case-set digest as exact lowercase 64-hex SHA-256 bytes;
no trim/lower/string coercion occurs. Omitted diagnostic set hashes retain the
deterministic empty-set default. The shared `_optional_sha256` boundary used by
`ShadowProvisionalSampleSet` and `ShadowSampleMedicalConfirmation` now applies
the same raw-byte rule while preserving only `None`/empty-string omission.
Persisted modern shadow runs fail closed when their gold case-set, diagnostic
case-set, diagnostic-result or coverage snapshot digest is padded, uppercase
or non-string; computed snapshot hashes remain derived from frozen content.

Verification: rule/factory/repository-hardening suite **59 passed**;
gold-shadow/lifecycle suite **57 passed**; shadow-sample service plus protocol
API adjacency **49 passed, 1 warning**; daily-run/record-resolver/repository
adjacency **96 passed, 41 subtests**; compileall, prompt preflight and
review-gate (`ok=true`) passed. Real MY008 fixture collection remains blocked
by missing `cryptography`; no dependency was installed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains a bounded source-only integrity audit. Do not
start services/providers, browser/Playwright/API login or real projects until
the five formal reviewer outcomes are hash-bound and the source-token/CAS gate
is revalidated.

## 5.279 source-only protocol applicability evidence hash exactness

`ProtocolApplicabilityAssignment.create()` now requires an exact lowercase
64-hex `evidence_source_content_sha256`; padded, uppercase and non-string
values are rejected before assignment identity calculation. Persisted
applicability assignments reconstruct through the strict factory and fail
closed on the same digest-shape tampering. Applicability overlap, resolution
and CAS semantics are unchanged.

Verification: rule/repository-focused suite **60 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
compileall, prompt preflight and review-gate (`ok=true`) passed. Real MY008
fixture collection remains blocked by missing `cryptography`; no dependency
was installed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS replay, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.317 source/UI Patient Profile domain coverage

Patient Profile now presents a compact source-domain coverage strip adjacent
to the summary. `profileDomainCoverage()` keeps missing, empty, explicit
`available` / `absent` / `unmapped` / `unsupported`, unknown and malformed
states distinct, uses stable domain labels, and never infers coverage from
trend arrays. The view replaces the ambiguous bottom aggregate footnote and
states that coverage is a source/mapping declaration, not evidence of no risk.

Verification: focused subject-model test **passed**; all **33** medical-
monitoring frontend pure test modules **passed**; Vite build **passed** with
1954 modules transformed and the existing >500 kB main-chunk warning. No
browser/visual/runtime check was run because the authoritative gate remains
`read_only / blocked`, with activation, provider, runtime and write authority
false; reserved ports remain empty. This is source/UI evidence only and does
not establish clinical, real-project, browser or commercial acceptance.

## 5.286–5.313 continuation slices (2026-08-05)

The following additional P9 source-only integrity slices were completed after
the earlier checkpoint rows. Each has its own task record, change manifest,
test evidence, Codex review, metrics and `LOOP_LEDGER.md` entry:

| Loop | Surface | Verification | Result |
|---|---|---:|---|
| 5.286–5.298 | downstream evidence/revalidation, prompt manifest and daily resolution hash contracts | per-slice focused/adjacent suites | passed |
| 5.299 | rule-template recommendation raw input hash | 19 focused; 567 selected | passed |
| 5.300 | study config source/declared config hashes | 18 focused; 87 selected | passed |
| 5.301–5.302 | gold-case row locator/fingerprint and structured source hashes | 39–40 focused; 158 selected | passed |
| 5.303 | release dossier exact evidence hashes | 10 focused; 121 selected | passed |
| 5.304–5.305 | protocol fact projection and rule-template immutable mapping identity | 19–22 focused; selected adjacency | passed |
| 5.306 | AI repository attempt/source hash boundaries | 100 focused; 482 selected; 94 selected | passed |
| 5.307 | mapping-draft persisted chunk/source hash shape | 55 focused; 81 + 549 + 54 selected | passed |
| 5.308 | daily-run record-applicability mapping/binding raw hashes | 3 boundary; 71 focused; 112 adjacent | passed |
| 5.309 | record-rule aggregate identity hashes | 15 boundary; 111 focused; 103 adjacent | passed |
| 5.310 | persisted deterministic batch-rule output hash | 4 boundary; 97 focused; 112 adjacent | passed |
| 5.311 | profile-ready frozen batch source bindings | 1 boundary (4 cases); 54 batch; 64 adjacent | passed |
| 5.312 | source-registration prior lineage binding/content hashes | 2 boundary; 105 adjacent | passed |
| 5.313 | batch idempotency replay request hash | 2 boundary (4 cases); 106 adjacent | passed |
| 5.314 | legacy source-table migration content hash | 2 boundary (5 cases); 107 adjacent | passed |
| 5.315 | persisted mapping-revision hash before reuse | 1 boundary (5 cases); 108 adjacent | passed |
| 5.316 | supplied row-fingerprint input hash | 1 boundary (valid + 5 cases); 109 adjacent | passed |

Final joint offline regression after 5.314: the nine related batch/daily-run/
record-rule/AI modules passed **285 tests** in 10.02s; final changed-module
compileall and Ruff passed. This remains source-only evidence.

Final joint offline regression after 5.315: the same nine related modules
passed **286 tests** in 11.54s; final changed-module compileall and Ruff
passed. This remains source-only evidence.

Final joint offline regression after 5.316: the same nine related modules
passed **287 tests** in 10.56s; final changed-module compileall and Ruff
passed. This remains source-only evidence.

Shared source changes in 5.308–5.315 are limited to existing daily-run,
record-rule, batch-rule and batch-repository integrity boundaries; no clinical
rule semantics, medical conclusions, UI architecture, authority state or
runtime behavior was intentionally changed. All per-slice Hermes review-gates
with `--require-verification` passed with empty warnings/errors; Ruff was
available for these slices and passed. No provider call, service startup,
browser/Playwright/API login, real study project, B6/C14 action, source-token /
CAS replay or release activation occurred.

## Current gate / next safe action (post 5.313)

`records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
still reports `mode=read_only`, `status=blocked`, with
`medical_approval_granted=false`, `provider_call_permitted=false`,
`runtime_activation_permitted=false`, and `write_permitted=false`. Ports 8911,
5174, 8910 and 4173 are empty. Continue only bounded source-only audit work;
the next authorized sequence remains five formal reviewer outcomes → source
token/CAS byte and expected-version revalidation → host/runtime identity →
controlled three-mode/five-project Playwright rounds → release dossier. Do not
infer or manufacture B6 outcomes and do not activate the runtime while the gate
is blocked.

## 5.315 source-only persisted mapping-revision hash exactness

`_validation_evidence_mutation()` now validates an existing
`monitoring_mapping_revisions.mapping_sha256` as an exact lowercase 64-hex
SHA-256 value before comparing it with the canonical mapping payload. Uppercase,
padded, non-hex, short and non-string SQLite tampering therefore fails at the
persisted identity boundary; valid same-revision reuse and mapping lifecycle
semantics are unchanged.

Verification: focused **1 passed** with five malformed subcases; full batch
repository **58 passed**; batch/field-profiler/daily-AI/analysis **108 passed**;
nine-module joint regression **286 passed** in 11.54s; compileall, Ruff,
prompt preflight and Hermes review-gate (`ok=true`) passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## 5.316 source-only supplied row-fingerprint input hash exactness

`_normalize_rows()` now validates a present caller-supplied `row_fingerprint`
as an exact lowercase 64-hex SHA-256 value before comparing it with the
deterministic domain/data digest. Omitted values still receive the calculated
fingerprint; a canonical but different value still follows the existing
mismatch path. Uppercase, padded, non-hex, short and non-string inputs fail
closed at the identity boundary.

Verification: focused **1 passed** with a valid case and five malformed
subcases; full batch repository **59 passed**; batch/field-profiler/daily-AI/
analysis **109 passed**; nine-module joint regression **287 passed** in 10.56s;
compileall, Ruff, prompt preflight and Hermes review-gate (`ok=true`) passed.
This is source-level input-contract evidence only; no provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## 5.307 source-only mapping-draft raw hashes

Persisted mapping chunk and draft hash reads now pass raw values directly to
the strict lowercase 64-hex validator. `str(...)` coercion was removed for
chunk input/output/profile-input digests and draft anchor/revision digests;
non-canonical source hashes are surfaced as controlled mapping-source state
errors. Canonical mapping assembly, lineage, confirmation and lifecycle
semantics remain unchanged.

Verification: focused mapping-draft **55 passed**; mapping
activation/batch-lifecycle **81 passed**; selected AI repository/service/API
**549 passed**; release/readiness/revalidation **54 passed**; targeted
`py_compile` passed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains another bounded source-only integrity audit.
Do not start services/providers, browser/Playwright/API login or real projects
until the five formal reviewer outcomes are hash-bound and the source-token/CAS
gate is revalidated.

## 5.306 source-only monitoring-AI repository raw hashes

The monitoring-AI repository now requires persisted digest fields to be raw
strings of exactly 64 lowercase hexadecimal characters. `_required_sha256()`
no longer trims values, and request/response attempt payload hashes pass
through the same strict boundary before payload comparison. Padded, uppercase,
non-string and malformed job/candidate/turn/repair/attempt identities fail
closed; canonical retry, CAS, idempotency and payload semantics are unchanged.

Verification: repository/deterministic-repair **100 passed**; selected AI
service/worker/API **482 passed**; selected AI contract/quality/evaluation/
startup/risk **94 passed**; targeted `py_compile` passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains another bounded source-only integrity audit.
Do not start services/providers, browser/Playwright/API login or real projects
until the five formal reviewer outcomes are hash-bound and the source-token/CAS
gate is revalidated.

## 5.305 source-only rule-template replay identity raw hashes

The rule-template recommendation replay identity now preserves raw string
bytes for `mapping_content_sha256`, `capability_manifest_sha256` and
`effective_capabilities_sha256`; it no longer coerces or trims persisted
mapping digests. Non-string values become empty at this identity seam so the
downstream strict rule compiler fails closed. Intentional text normalization
for mapping revision and recommendation candidate ID is unchanged.

Verification: focused recommendation **22 passed**; selected
authoring/protocol hardening **64 passed**; mapping/release-chain **40
passed**; release/readiness/revalidation **54 passed**; targeted
`py_compile` passed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains another bounded source-only integrity audit.
Do not start services/providers, browser/Playwright/API login or real projects
until the five formal reviewer outcomes are hash-bound and the source-token/CAS
gate is revalidated.

## 5.304 source-only shared protocol-fact hash exactness

The shared protocol-fact projection boundary now requires raw exact lowercase
64-hex source digests. It no longer accepts padded or uppercase values after
implicit `str(...).strip()` normalization: medical-writing `state_sha256` and
evidence `quote_sha256` are checked as persisted values, and non-string
values fail closed. Valid confirmed projection, source lineage, consumer
isolation and DTO safety semantics are unchanged.

Verification: focused projection/API **19 passed**; selected adjacent
protocol/repository tests **52 passed**; readiness/revalidation/protocol-rule
tests **68 passed**; targeted `py_compile` passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains another bounded source-only integrity audit.
Do not start services/providers, browser/Playwright/API login or real projects
until the five formal reviewer outcomes are hash-bound and the source-token/CAS
gate is revalidated.

## 5.303 source-only release-dossier hash exactness

The offline commercial release dossier now requires exact lowercase 64-hex
evidence hashes; padded, uppercase and non-string section evidence values fail
closed. The shared helper also protects signoff and residual-risk decision
evidence. Complete/partial status, control partitions, gate binding and
`authority_granted=false` remain unchanged; no dossier was submitted.

Verification: focused release-dossier **10 passed**; selected
release-dossier/revalidation/nonfunctional/release-gate/formal-review,
approved-input and real-loop readiness/revalidation adjacency **121 passed**;
`py_compile` and targeted `compileall` passed. This is source-level identity
evidence only; no provider, runtime, browser, source-token/CAS, real-project,
clinical, visual or commercial authorization occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.302 source-only gold frozen-row binding hash exactness

Frozen gold/diagnostic authority now compares row fingerprints and structured
source-content hashes without lower/strip normalization. Uppercase tampered
row identity bytes fail closed; the canonical locator parser remains the
first rejecting boundary for non-canonical structured hashes. Valid frozen-row
resolution, field bindings and legacy locator semantics are unchanged.

Verification: focused gold-case authority **40 passed**; selected
protocol-rules/repository-hardening/shadow-sample/gold-shadow and real-loop
readiness/revalidation adjacency **158 passed**; `py_compile` and targeted
`compileall` passed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.301 source-only gold locator hash exactness

Canonical frozen gold/diagnostic row locators now preserve exact lowercase
source digest bytes. An uppercase hash embedded in a canonical
`listing:<hash>:sheet:<sheet>:row:<row>` locator fails closed before locator
construction; valid lowercase, structured-coordinate agreement and legacy
locator binding remain unchanged.

Verification: focused gold-case authority **39 passed**; selected
protocol-rules/repository-hardening/shadow-sample/gold-shadow and real-loop
readiness/revalidation adjacency **158 passed**; `py_compile` and targeted
`compileall` passed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.300 source-only study-config hash exactness

The project-neutral study configuration now preserves raw exact lowercase
64-hex bytes for source-binding `content_sha256` and optional declared
`config_sha256`. Padded, uppercase and non-string values fail closed; omitted
or empty optional declared hashes retain the established omission semantics.
Canonical config round-trip and deterministic identity are unchanged.

Verification: focused study-config **18 passed**; selected
mapping-batch/protocol-preparation/real-loop readiness and
acceptance-revalidation adjacency **87 passed**; `py_compile` and targeted
`compileall` passed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.299 source-only rule-template recommendation hash exactness

The rule-template recommendation decision service now compares the caller's
raw `expected_input_revision_sha256` bytes to the persisted job identity;
padded and uppercase direct-service values fail closed through the established
stale-input response. Canonical acceptance/rejection, idempotent replay and
mapping-drift behavior are unchanged, and the router's lowercase digest
contract remains intact.

Verification: focused recommendation **19 passed**; selected offline
recommendation/rule/mapping/protocol/AI/readiness adjacency **567 passed, 2
warnings**; `py_compile` and targeted `compileall` passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.298 source-only daily resolution hash exactness

The daily record-applicability snapshot validator now passes raw
`resolution_sha256` bytes directly to the strict lowercase 64-hex checker;
padded values fail closed instead of being stripped. Resolver identity
recomputation, mapping/rule binding and record-applicability semantics are
unchanged.

Verification: focused record-rule resolver **38 passed**; selected daily-run
repository/service/router/readiness/acceptance adjacency **148 passed**;
`py_compile` and targeted `compileall` passed. This is source-level identity
evidence only; no provider, runtime, browser, source-token/CAS, real-project,
clinical, visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.297 source-only prompt manifest hash exactness

The offline real-loop prompt manifest now requires raw exact lowercase 64-hex
`prompt_sha256` values matching the exact UTF-8 prompt text. Padded/uppercase
hashes fail closed; canonical 40-row project/role/task/scenario coverage and
identity markers remain unchanged. No provider, runtime or project prompt was
executed.

Verification: focused prompt-manifest **6 passed**; selected
prompt/readiness/current-manifest/manifest-replay/upstream adjacency **56
passed**; `py_compile` and targeted `compileall` passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.296 source-only aggregate/CAS revalidation hash exactness

Aggregate/CAS replay evidence revalidation now requires exact raw lowercase
64-hex SHA-256 strings for the artifact and optional source expectations.
Padded values fail with the existing artifact-field-invalid path rather than
being trusted through whitespace normalization. Artifact/source byte checks,
replay reconstruction, incomplete-CAS status and authority flags are unchanged;
no aggregate or CAS operation was executed.

Verification: focused aggregate/CAS revalidation **8 passed**; selected
aggregate/CAS revalidation/replay/disposition/readiness/acceptance/manifest
adjacency **77 passed**; `py_compile` and targeted `compileall` passed. This is
source-level identity evidence only; no provider, runtime, browser,
source-token/CAS, real-project, clinical, visual or commercial acceptance
occurred. The formal gate remains `read_only / blocked` and reserved ports
remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.295 source-only rule-risk bridge source hash exactness

Deterministic-rule evidence locator construction now requires any supplied
`source_content_sha256` to be an exact lowercase 64-hex string. Padding,
uppercase and non-string values fail closed rather than being trimmed/coerced
into a different evidence identity. Canonical locator output, RiskCase
lineage, category/severity and medical-review-only status are unchanged.

Verification: focused rule-risk bridge **16 passed**; selected
bridge/rule-runner/taxonomy/readiness/acceptance/manifest adjacency **76
passed**; `py_compile` and targeted `compileall` passed. This is source-level
identity evidence only; no provider, runtime, browser, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.294 source-only migration contract hash exactness

The read-only migration ledger, observation and reconciliation contract now
requires exact raw lowercase 64-hex SHA-256 strings for migration, rollback,
backup and authority evidence hashes. Backup observations no longer strip or
lowercase supplied values before validation. Migration ordering, reconciliation
decisions and all write-permitted false invariants are unchanged; no migration
or SQLite operation was executed.

Verification: focused migration-contract **20 passed**; selected
migration/startup-recovery/readiness/acceptance/manifest adjacency **70 passed,
17 deprecation warnings**; `py_compile` and targeted `compileall` passed. This
is source-level identity evidence only; no migration execution, provider,
runtime, browser, source-token/CAS, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.293 source-only mapping activation hash exactness

Mapping activation now requires raw exact lowercase 64-hex SHA-256 strings for
new batch profile hashes and capability-manifest revalidation. Supplied values
are no longer coerced, trimmed or lowercased; padded/uppercase values fail
closed while canonical profile comparison and activation semantics remain
unchanged.

Verification: focused mapping-activation **24 passed**; selected
mapping/batch/draft/semantic-quality/readiness/acceptance/manifest-replay
adjacency **212 passed**; `py_compile` and targeted `compileall` passed. This
is source-level identity evidence only; no provider, runtime, browser,
source-token/CAS, real-project, clinical, visual or commercial acceptance
occurred. The formal gate remains `read_only / blocked` and reserved ports
remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.292 source-only source-token evidence hash exactness

Source-token evidence revalidation now requires exact raw lowercase 64-hex
SHA-256 values for the artifact, source-inventory and archive-inventory file
expectations, as well as persisted inventory hash fields. Padding is no longer
stripped before validation; canonical values continue through exact byte and
inventory replay. The historical `not_proven` conclusion, token-synthesis
prohibition, CAS/B6 boundary and authority flags are unchanged.

Verification: focused source-token evidence **10 passed**; selected
source-token/readiness/acceptance/upstream/manifest adjacency **67 passed**;
`py_compile` and targeted `compileall` passed. This is source-level identity
evidence only; no source-token rescan, provider, runtime, browser,
source-token/CAS, real-project, clinical, visual or commercial acceptance
occurred. The formal gate remains `read_only / blocked` and reserved ports
remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.291 source-only signal-lifecycle revalidation hash exactness

Signal-lifecycle artifact revalidation now requires the supplied
`expected_sha256` bytes themselves to be a lowercase 64-hex SHA-256 string;
leading/trailing whitespace is no longer stripped before validation. Canonical
artifact hashes continue to pass exact byte comparison, while padded inputs
fail closed with the existing `FILE_SHA256_MISMATCH` diagnostic. Lifecycle
status, report replay, authority flags and file safety semantics are unchanged.

Verification: focused signal-lifecycle revalidation **8 passed**; selected
lifecycle/manifest-replay/readiness/acceptance adjacency **60 passed**;
`py_compile` and targeted `compileall` passed. This is source-level identity
evidence only; no provider, runtime, browser, source-token/CAS, real-project,
clinical, visual or commercial acceptance occurred. The formal gate remains
`read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.286 source-only runtime identity evidence hash exactness

The read-only runtime identity evidence revalidator now requires raw exact
lowercase 64-hex SHA-256 values for evidence, principal identity and host
attestation fields; whitespace, uppercase and non-string values cannot be
normalized into verification. Valid canonical values are retained in the
diagnostic report, while invalid values are blanked in blocked reports. No
authentication, host attestation or authority flag behavior changed; all
permissions remain false.

Verification: focused runtime identity suite **8 passed**; runtime
identity/readiness/upstream adjacency **56 passed**; release evidence/gate/
dossier adjacency **35 passed**; identity authorization/route adjacency **22
passed**; `python3 -m py_compile` and compileall passed; prompt preflight and
review-gate returned `ok=true`. This is source-level identity evidence only;
no provider, runtime, browser, host attestation, source-token/CAS,
real-project, clinical, visual or commercial acceptance occurred. The formal
gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The current bounded slice is complete; on resume, re-read latest AGENTS.md,
this checkpoint/ledger, gate and ports before choosing the next safe action.
Do not start services/providers, browser/Playwright/API login or real projects
until the five formal reviewer outcomes are hash-bound and the source-token/
CAS gate is revalidated.

## 5.287 source-only project-admission hash exactness

Project-admission batch `listing_sha256` and prompt `prompt_sha256` values now
require an exact raw lowercase 64-hex SHA-256 string. Uppercase, whitespace-
padded and non-string values fail closed; canonical lowercase values and the
diagnostic-only authority flags are unchanged. Audit-chain hash handling is
intentionally out of scope for this slice.

Verification: focused project-admission suite **7 passed**; selected
real-loop readiness/upstream adjacency **41 passed**; `python3 -m py_compile`
and targeted `compileall` passed. No provider, runtime, browser, source-token/
CAS, real-project, clinical, visual or commercial acceptance occurred. The
formal gate remains `read_only / blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
This bounded slice is complete; on resume, re-read latest AGENTS.md, this
checkpoint and the LOOP ledger, recheck gate and ports, then choose the next
explicit bounded source-only task. Do not start services/providers,
browser/Playwright/API login or real projects until the five formal reviewer
outcomes are hash-bound and the source-token/CAS gate is revalidated.

## 5.290 source-only upstream evidence hash exactness

The five-gate upstream assembly now preserves raw string `evidence_sha256`
values rather than stripping whitespace before validation. Uppercase and
whitespace-padded values fail with the existing hash-invalid issue; non-string
values remain on the existing field-invalid path and cannot prove a gate.
Evidence pairing, duplicate detection, status derivation and authority flags
are unchanged.

Verification: focused upstream-assembly suite **13 passed**; selected
upstream/manifest/replay/readiness/acceptance adjacency **85 passed**;
`python3 -m py_compile` and targeted `compileall` passed. No provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
This bounded slice is complete; continue with the next explicit source-only
slice while the gate remains blocked. Do not start services/providers,
browser/Playwright/API login or real projects until the five formal reviewer
outcomes are hash-bound and the source-token/CAS gate is revalidated.

## 5.289 source-only current-manifest artifact hash exactness

The current real-loop manifest builder now requires a raw exact lowercase
64-hex `artifact_sha256` when an artifact identity is supplied. Uppercase,
whitespace-padded and non-string values produce a fail-closed `HASH_INVALID`
issue; the optional empty artifact identity and evidence-reference pairing are
unchanged. Manifest replay comparison and authority flags were not changed.

Verification: focused current-manifest suite **7 passed**; selected
manifest/replay/readiness/upstream/acceptance adjacency **84 passed**;
`python3 -m py_compile` and targeted `compileall` passed. No provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
This bounded slice is complete; continue with the next explicit source-only
slice while the gate remains blocked. Do not start services/providers,
browser/Playwright/API login or real projects until the five formal reviewer
outcomes are hash-bound and the source-token/CAS gate is revalidated.

## 5.288 source-only audit-contract hash exactness

The offline append-only audit contract now requires raw exact lowercase 64-hex
SHA-256 values for `authorization_decision_sha256` and `prev_event_hash`; only
the exact empty string remains valid for an initial predecessor. Uppercase,
whitespace-padded and non-string values fail closed. Authorization policy,
event-chain semantics and authority flags are unchanged.

Verification: focused audit-contract suite **15 passed**; selected
identity/audit/route/readiness/upstream adjacency **92 passed**; `python3 -m
py_compile` and targeted `compileall` passed. No provider, runtime, browser,
source-token/CAS, real-project, clinical, visual or commercial acceptance
occurred. The formal gate remains `read_only / blocked` and reserved ports
remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
This bounded slice is complete; continue with the next explicit source-only
slice while the gate remains blocked. Do not start services/providers,
browser/Playwright/API login or real projects until the five formal reviewer
outcomes are hash-bound and the source-token/CAS gate is revalidated.

## 5.285 source-only release evidence hash exactness

The read-only release evidence revalidator now accepts declared source and
gate evidence digests only as raw lowercase 64-hex SHA-256 strings. It no
longer trims or lowercases source/gate values: uppercase source input is a
source-field error and uppercase gate input remains unbound to canonical
sources. The revalidator remains diagnostic-only and cannot grant authority.

Verification: focused release revalidation suite **10 passed**; release
gate/dossier/revalidation adjacency **25 passed**; runtime identity
revalidation **7 passed**; LOOP readiness/revalidation **36 passed**;
`python3 -m py_compile` passed; prompt preflight and review-gate returned
`ok=true`. This is source-level identity evidence only; no provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.284 source-only gold authority hash exactness

Gold-case authority now requires exact raw lowercase 64-hex equality for the
registered source entry and the source attached to the frozen batch. The
normalized-row locator parser applies the same rule to explicit
`source_content_sha256` values, and gold/diagnostic release-binding prechecks
no longer lowercase evidence locators. Uppercase, padded or non-string values
fail closed; valid canonical bindings remain unchanged.

Verification: authority plus rule/repository suite **104 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
gold-shadow plus shadow-sample adjacency **57 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
`python3 -m py_compile` passed; prompt preflight and review-gate returned
`ok=true`. This is source-level identity evidence only; no provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.283 source-only case evidence-locator hash exactness

Gold and diagnostic case factories now require the exact raw lowercase
`source_content_sha256` bytes to occur in each evidence locator; uppercase
digest text no longer passes through `locator.lower()`. Persisted case reads
therefore fail closed when evidence locators or bound source-row locators are
tampered with uppercase digest text. Case IDs, source locator text other than
the digest, and clinical rule semantics are unchanged.

Verification: focused rule/repository suite **65 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
gold-shadow plus shadow-sample adjacency **57 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
`python3 -m py_compile` passed; prompt preflight and review-gate returned
`ok=true`. This is source-level identity evidence only; no provider, runtime,
browser, source-token/CAS, real-project, clinical, visual or commercial
acceptance occurred. The formal gate remains `read_only / blocked` and
reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.282 source-only frozen shadow-source hash exactness

Frozen listing/source lineage handoffs now require exact raw lowercase 64-hex
SHA-256 values. `MonitoringRuleAuthoringService` no longer compares registry
and validation hashes with `.lower()` or crashes on non-string input; both
usable-source paths fail closed on non-canonical or mismatched values.
`MonitoringShadowSampleService._batch_source()` applies the same exact check
to the frozen batch binding, registry entry and source registration, and
projects the unchanged bound digest. Evaluation-state and diagnostic-code
normalization remain intentionally unchanged.

Verification: shadow-sample service **41 passed, 1 warning**; authoring **9
passed**; gold-shadow **16 passed**; protocol-rule/repository **63 passed**;
batch/authoring adjacency **73 passed, 27 subtests**; protocol adjacency **57
passed, 1 warning**; daily-run/record-resolver/repository **96 passed, 41
subtests**; compileall, prompt preflight and review-gate returned `ok=true`.
This is source-level identity evidence only; no provider, runtime, browser,
source-token/CAS, real-project, clinical, visual or commercial acceptance
occurred. The formal gate remains `read_only / blocked` and reserved ports
remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.281 source-only gold source-row fingerprint exactness

Gold source-row bindings now require an exact raw lowercase 64-hex
`row_fingerprint` at both the canonical factory and the legacy partial-mapping
reader. Padded, uppercase and non-string values are rejected rather than
trimmed, lowercased or coerced. Persisted modern gold-case reads reconstruct
through the same strict binding boundary, so tampering in
`source_row_bindings_json` fails closed; case identity and clinical rule
semantics are unchanged.

Verification: focused rule/repository suite **63 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
shadow/lifecycle plus shadow-sample adjacency **56 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
`python3 -m py_compile` passed; prompt preflight and review-gate returned
`ok=true`. The MY008 real fixture was only collected (one test), not executed
under the blocked gate. This is source-level identity evidence only; no
provider, runtime, browser, source-token/CAS, real-project, clinical, visual
or commercial acceptance occurred. The formal gate remains `read_only /
blocked` and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.

## 5.280 source-only persisted monitoring-rule source hash exactness

Complete persisted monitoring-rule rows now require `source_text_sha256` to be
an exact lowercase 64-hex SHA-256 string equal to the digest of stored
`source_text`; padded, uppercase and non-string values fail closed without
normalization. Legacy partial-identity rows still take the established
readiness diagnostic path before strict revalidation. Rule semantics and
clinical source content are unchanged.

Verification: rule/repository-focused suite **61 passed**; protocol
API/lifecycle/review/cross-project adjacency **57 passed, 1 warning**;
shadow/lifecycle plus shadow-sample service **56 passed, 1 warning**;
daily-run/record-resolver/repository adjacency **96 passed, 41 subtests**;
compileall, prompt preflight and review-gate (`ok=true`) passed. Real MY008
fixture collection remains blocked by missing `cryptography`; no dependency
was installed. This is source-level identity evidence only; no provider,
runtime, browser, source-token/CAS replay, real-project, clinical, visual or
commercial acceptance occurred. The formal gate remains `read_only / blocked`
and reserved ports remain empty.

## Current gate / next safe action

The authoritative gate is still `mode=read_only`, `status=blocked`, with
medical approval, provider calls, runtime activation and writes all false.
The next safe action remains bounded source-only audit work. Do not start
services/providers, browser/Playwright/API login or real projects until the
five formal reviewer outcomes are hash-bound and the source-token/CAS gate is
revalidated.
