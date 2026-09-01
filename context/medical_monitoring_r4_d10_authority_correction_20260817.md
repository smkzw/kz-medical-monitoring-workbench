# D10 authority correction checkpoint — 2026-08-17

## Status

`REOPENED_D10_ARTIFACT_AUTHORITY_ONLY`

The prior `ACCEPT_D10_ARTIFACTS` record remains historical evidence, but its
accepted-source-membership conclusion is superseded for four catalog cases.
This is a declared revision, not a silent overwrite. D10 runtime Worker 02/03,
R5/UI, 8911, real projects/models, product paths and medical writing remain
frozen.

## Decisive finding

Independent runtime review proved that the frozen fixture-authority registry
pins `SRC-REV-EXTERNAL-001` as accepted for D10-CASE-078/093/107/295. The
catalog rows intentionally use that extra pair as an invalid closed-world
membership attack. Because the authority mirrors the attack, a typed envelope
reduced to the external pair alone passes both intrinsic and authority source
audits and can emit a medical unit. Runtime prefix/case/mutation conventions
are forbidden and cannot repair a wrong authority.

The same review also found two Worker-01 defects: authority gates are derived
after `project_facts`, and an authority with model pins can be bypassed by
submitting `model_evidence=None`.

## Correction contract

- The fixture authority must pin only genuinely accepted source revision and
  content pairs. For an intentional extra/duplicate-pair catalog attack, the
  invalid submitted pair is evaluation input, never accepted authority.
- Catalog/artifact conformance must still prove that every authority-accepted
  pair is present, while allowing intentional submitted extras to be evaluated
  and rejected by the independent verifier/runtime. No case id, `EXTERNAL`
  prefix, mutation metadata or free-text branch may enter runtime decisions.
- Runtime authority missing/identity/source/model-presence-or-pin mismatch must
  return a zero-medical gate before project medical facts are computed.
- Regenerate and repin the complete affected artifact chain; preserve 312-case
  coverage and expected outcomes. Re-run generator checks, independent
  verifier, D10 artifact/runtime focused tests, D09 99/145 adjacency, compile,
  static closure and 8911-stopped checks.

## Current anchors before correction

- Contract SHA-256: `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`
- Worker-01 five-file snapshot:
  - contracts `4b3bb34d18624a19a88d424745fbefed09f98e95896a5549adcded6ef2ba2e59`
  - adapter `8e1d6fcd9b4ccc54caaaa0f25fcdc66fb3ce30f0d4049e59a4f3413907ec9e53`
  - evaluator `a341bde1a3873d440295a0622960970a746cdffbe50785d2dfa0192ad5ea8791`
  - adapter test `cde15796351db460d92098447498b6c52118024ce6b2a2a7db1cac43b7e8604f`
  - runtime test `f9c964cb2d4f2ad7e71d43e192c18a9e398cbcfdf477ec91ae36b48f7dd30930`

## Next safe action

Apply the smallest generator-first correction in an isolated Worker-01/artifact
slice, regenerate all affected derived files, then submit the stable snapshot
to a fresh independent verifier. Do not unlock Worker 02 before acceptance.
