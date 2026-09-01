# R2 Batch A post-fallback Codex negative gate — VETO

Date: 2026-08-10
Scope: current `poc/medical_monitoring_ai_native_r2/` Batch A only
Decision: **VETO**; Batch B/C remain frozen.

## Observed anchor

- Existing full R2 test suite: `176 passed` before this gate.
- The passing suite does not cover the authority bypasses below.
- Product, medical writing, real projects, R1 and 8911 remain outside this repair scope.

## Executed reproductions

The following six checks all returned `True` against the current filesystem:

1. `dict.__setitem__` mutates nested `ImmutableDict` and changes its content hash.
2. A nested value in `StudyProject.config` remains mutable and changes serialized state.
3. Direct `SourceRevision(..., _verified=True)` accepts a caller-selected valid-looking digest.
4. Editing `to_dictable(SourceRevision)` then calling public `from_dictable` blesses the edited digest.
5. Directly fabricated `AcceptanceEvidence` plus ID-only registration reaches `baseline_eligible`.
6. `AcceptanceEvidence.from_binding` accepts a low-confidence result plus a substituted unrelated high-confidence critical mapping, and the substitution reaches `baseline_eligible`.

Observed output:

```text
immutable_dict_base_bypass=True
study_project_config_mutable=True
direct_verified_fabrication=True
codec_fabrication=True
invented_evidence_reaches_eligible=True
substituted_mapping_reaches_eligible=True
```

## Required disposition

- Do not defer public trust escalation to Batch C.
- Replace the mutable dict subclass with a genuinely immutable mapping representation and freeze all adjacent nested fields.
- Remove public boolean-based authoritative construction and fail closed on generic authoritative rehydration.
- Bind acceptance registration/evidence to real verified objects, and derive mapping authority from the definitions that produced the registered results.
- Add the six exact reproductions plus adjacent mismatch cases as negative regressions.
- Re-run Codex negative gate and full tests, then request a fresh independent stable-snapshot ACCEPT/VETO.

This record is immutable history and is not an implementation report.
