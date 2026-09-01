# CRSwNP Competitor-Triage Scientific Fix Worker Report

## Scope And Trigger

- Historical failing run: `ct_run_7d9db4c3d935b989b0b4`.
- Observed failure: all 12 saved CRSwNP Phase III candidates were classified
  `excluded` because Chinese/English CRSwNP aliases were not deterministically
  equivalent and every model exclusion was preserved even when project
  modality, route, or target evidence was merely unknown.
- No service was restarted and no real AI call was made.

## Changed Files

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- `tests/test_medical_writing_competitor_triage_crswnp.py`
- `reviews/crswnp_competitor_triage_scientific_fix_worker_20260725.md`

## Bounded Condition-Equivalence Algorithm

The existing strict exact-token and proven-abbreviation matcher remains the
default. CRSwNP adds one closed concept family:

1. The project must itself establish CRSwNP through an exact controlled Chinese
   or English full label, or the fixed `CRSwNP` abbreviation.
2. Candidate full labels match only exact controlled forms, including
   `Chronic Rhinosinusitis With Nasal Polyps`,
   `Chronic Rhinosinusitis Phenotype With Nasal Polyps (CRSwNP)`,
   `Chronic Rhinosinusitis With Nasal Polyposis`, and exact Chinese equivalents.
3. Separate authoritative condition labels compose without title evidence only
   when the sinus condition is exactly `Chronic Sinusitis` or
   `Chronic Rhinosinusitis` and the second condition is an exact nasal-polyp
   label.
4. Generic `Sinusitis` plus `Nasal Polyps`, or `Nasal Polyps` alone, is not
   equivalent to CRSwNP without corroboration. It is accepted only when
   `official_title` or `brief_title` also contains an exact contiguous
   controlled CRSwNP full-name sequence. This is why the saved NCT06639295
   record remains a deterministic match.
5. Acute sinusitis explicitly blocks title-corroborated composition. No edit
   distance, stemming, percentage overlap, token-subset score, or fuzzy disease
   matching is used. Unspecified sinusitis plus polyps without corroboration,
   asthma plus polyps, isolated chronic rhinosinusitis, and chronic
   rhinosinusitis without nasal polyps remain non-matches.

## Classification And Source Truth

- Prompt version is now
  `competitor_triage_deepseek_v10_crswnp_chronicity`.
- `全部` is treated as a scope placeholder, not as a known target/mechanism.
- Intervention evidence is separated into `pharmacologic`,
  `non_pharmacologic`, and `unknown`.
- Missing project modality, route, or target blocks `direct_competitor`, lowers
  confidence, and is emitted as an evidence gap.
- Same-indication candidates without explicit non-pharmacologic evidence remain
  at least `indirect_reference` when critical project facts are missing.
- A same-indication pharmacologic study with public Protocol/SAP is reconciled
  to at least `indirect_reference` even when all project critical facts are
  known.
- Explicit DEVICE/PROCEDURE/RADIATION-only evidence can still support
  exclusion.
- Unknown intervention type is never relabeled as a drug. Sanitized reasons use
  `候选干预类型待核实，可作为同适应症研究参考`.
- Reviewer-facing indication text is rebuilt from deterministic facts, so a
  true deterministic match cannot retain `适应症不同`. Model-authored evidence
  gaps and unsupported route/mechanism claims remain discarded.

## Verification

Focused and adjacent checks:

- `python3 -m pytest -q tests/test_medical_writing_competitor_triage_crswnp.py`
  - `9 passed`
- `python3 -m pytest -q tests/test_medical_writing_competitor_triage.py tests/test_medical_writing_competitor_triage_v4_source_truth.py tests/test_medical_writing_competitor_triage_crswnp.py`
  - `236 passed`
- `python3 -m pytest -q tests/test_d017_competitor_triage_v5_acceptance.py tests/test_medical_writing_triage_durable.py tests/test_medical_writing_triage_recovery_api.py`
  - `86 passed`
- `python3 -m py_compile` on the implementation and three scoped test modules
  - passed
- Read-only deterministic replay of
  `runs/evidence/crswnp_competitor_triage_real_20260725/search_snapshot.json`
  with the saved project indication and historical `excluded` input:
  - `12/12` candidates matched the project indication.
  - `12/12` reconciled to low-confidence `indirect_reference`.

Pytest emitted 10 pre-existing FastAPI `on_event` deprecation warnings. No test
failure remained.

## Residual Risks

- Registry records with an isolated `Nasal Polyps` condition and no exact CRSwNP
  title corroboration intentionally remain unmatched, even if a human may know
  the study is CRSwNP.
- Retaining an unknown-intervention same-indication study as low-confidence
  `indirect_reference` prevents false exclusion but still requires medical
  review before basket confirmation.
- This worker did not run real `deepseek-v4-pro`, browser acceptance, service
  restart, or production persistence. The historical run remains historical and
  stale under the v10 prompt identity; no real-AI acceptance is claimed.
