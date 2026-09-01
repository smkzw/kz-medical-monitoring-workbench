You are continuing the same fallback Batch A repair session after Codex ran an independent negative gate against your 176-test result. The test suite passes, but six public fail-open paths still reproduce. Repair them in this same session; do not defer any of them to Batch C.

Hard boundaries:
- Work only inside the current workbench workspace root.
- Modify only Batch A files under `poc/medical_monitoring_ai_native_r2/`.
- Preserve all prior worker reports and independent/Codex VETO records as immutable history.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01_fallback_repair_followup_01.md`. Do not write this report file yourself; return the report in your final response.
- Do not edit R1, product, medical-writing, real-project, shared-runtime or 8911 surfaces.
- Python 3.9 standard library + existing pytest only; no new package, service, network, credential or real data.
- Do not implement Batch B/C risk lifecycle, baselines, modes, diff, SQLite, migration or publication.

Read these files only:
- current Batch A source files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/`
- current Batch A tests under `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r2/README.md`
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `plans/codex_execution_medical_monitoring_r2_kernel_execution_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_a_independent_veto_20260810.md`
- `reviews/codex_medical_monitoring_r2_batch_a_postfallback_negative_gate_20260810.md`

Codex reproduced all six failures against the current filesystem:

1. `ImmutableDict` is a `dict` subclass. `dict.__setitem__(frozen["outer"], "x", 2)` bypasses the override and changes the content hash. Replace it with a genuinely immutable Mapping/value type that has no mutable base-class backdoor. Update canonical JSON/plain conversion so hashes remain deterministic. Preserve useful `dict(...)`, equality and codec behavior where appropriate.

2. `StudyProject.config` is not deep-frozen. A nested value reachable through a frozen project changes after construction and changes serialized/hash-relevant state. Audit every Batch A nested mapping/sequence field, including config, ambiguity candidates, resolutions, lineage, evidence gaps and mapping collections; copy/canonicalize/freeze them at construction.

3. A caller can pass `_verified=True` directly to `SourceRevision`, `ListingSnapshot`, `MappingResult`, `CanonicalFact`, `RecordIdentity` or `RiskIdentity` and fabricate authoritative objects. A public boolean is not an authority boundary. Replace it with a non-public capability/sentinel or an equivalent factory-only construction contract. The normal constructor signature must not accept a caller-chosen boolean that silently blesses arbitrary digests/references. Add direct-constructor negative tests.

4. Public `from_dictable` detects `_verified` and silently sets it to true. Editing serialized `content_digest` to any valid-looking 64-hex value and clearing `content_hash` produces a fabricated authoritative object. Generic untrusted deserialization must fail closed for authoritative/content-addressed entities. If verified rehydration cannot be securely implemented until Batch C owns artifact verification, expose no public trust-escalating codec now: require an explicit verifier/capability or reject authoritative rehydration. Do not export a function whose ordinary call silently upgrades untrusted payloads. Add tampered and untampered authoritative-codec regressions; document the exact Batch C hook without treating it as current acceptance.

5. A directly constructed `AcceptanceEvidence` with invented non-empty IDs/digests, a fabricated confidence=1.0 `MappingDefinition`, and all booleans true advances a merely ID-registered snapshot through all four steps to `baseline_eligible`. `AcceptanceService.register(snapshot_id, project_id, actor)` does not bind a real source/snapshot/algorithm/mapping set, and `_evidence_binding_reasons` checks only string presence. Make registration and evidence issuance bind actual verified `ListingSnapshot`, `SourceRevision`, `IdentityAlgorithm`, `MappingDefinition` and `MappingResult` objects (and `IdentityResolution` or equivalently derived identity-review evidence where needed). Directly fabricated/self-declared evidence must not be accepted. Evidence creation must be service/factory controlled and tied to the exact registered binding.

6. Even `AcceptanceEvidence.from_binding` accepts a real low-confidence critical mapping result while the caller supplies an unrelated high-confidence `critical_mappings` tuple. The substituted mapping makes system-policy advancement deterministic and reaches eligible. Require one-to-one consistency among mapping definitions, mapping results, mapping version, project, source revision, snapshot and identity algorithm. Derive critical-map cleanliness/determinism from the definitions that actually produced the registered results. Reject missing, extra, substituted, duplicated or version-mismatched mappings.

Acceptance design constraints:
- Replace caller-self-declared authority booleans with properties derived from bound objects or explicit service-issued decisions. A human/local-user scope approval may be an explicit decision, but it must be issued/audited by the trusted actor and bound to the registered snapshot; arbitrary standalone `AcceptanceEvidence(...)` construction must not grant authority.
- `register` should receive/retain the real immutable binding (or an equivalently strong verified bundle), not only IDs. Repeated use of mismatched objects must fail closed.
- Unknown actors and every attempted post-registration transition remain audited without changing accepted state.
- Keep the corrected API coherent for Batch B/C; update all current tests and README rather than preserving insecure compatibility.
- Python cannot provide cryptographic secrecy for in-process internals, but normal documented/public APIs must not contain a boolean/string shortcut that blesses arbitrary caller data. Private implementation tokens must not be re-exported.

Required regression evidence:
- Each of the six exact Codex reproductions fails after repair.
- Ordinary nested mutation and base-class mutation backdoors fail or are inert; recomputed hashes remain stable.
- Direct constructor `_verified=True` is rejected (ideally no longer a valid parameter).
- Generic codec cannot bless either tampered or untampered authoritative serialized entities without an explicit verified rehydration capability.
- An invented evidence object cannot reach any acceptance step; a real registered bundle with valid mappings can follow the chain.
- A real confidence=0.0 critical mapping cannot be masked by an unrelated confidence=1.0 definition; missing/extra/substituted/duplicate/version-mismatched mappings all fail closed.
- StudyProject config and all adjacent JSON-like/tuple collections are deeply immutable/defensively copied.
- Focused tests, entire Batch A suite and all current R2 tests pass; compile succeeds.
- Record before/after SHA, R1 tree digest unchanged, 8911 absent.

Return a compact repair report with exact files, API changes, negative reproductions, commands/counts and residual limitations. Do not claim Batch A acceptance; Codex and the independent verifier own the gate.
