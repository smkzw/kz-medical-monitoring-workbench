# R5-S5 Subject Workspace / Patient Journey Contract v0.1 Review

## Review scope

本文件由 worker-01 generator 生成，供 Codex 和独立 verifier 复核；不是接受记录，
不包含 `ACCEPT_R5_S5_CONTRACT` verdict。

## Mechanical contract facts

- contract：`medical-monitoring-r5-s5-subject-workspace-contract-v0.1` / schema `2026-08-26.1`。
- canonical typed leaves：265；core accepted leaves：216。
- deferred/placeholder/self-signed core leaves：0/0/0。
- parent mapping rows：195；replaced S5 parent rows：53。
- challenge registry rows：250；future runtime paths：11。
- structured executable challenge rows：mutation 250 / oracle 250；
  every row has one concrete `op/path/value` mutation and a rule/outcome/error/projection/non-LLM-anchor/test-locator oracle.
- accepted public-authority producer/test/evidence explicit pins：11；
  input raw pin map count：59。
- presentation leaves：22，均为 S5-owned non-core renderer vocabulary，
  `acceptance_claim=false`。Concrete domain labels/shapes/line styles, forbidden terms and subtype list bind exact accepted
  stage Markdown rows/spans plus stage raw SHA and parent raw/content SHA；legacy treatment binds actual
  `/legacy_domain_policy/<kind>` objects。Schema descriptors and invariant predicates are never scalar authority，且
  `/contract_constants/*` pseudo-selectors are forbidden。
- `S5SeverityEncoding.line_weight` numeric value and `S5AudienceLexicon.content_hash` remain null future-renderer parameters
  without acceptance claims；clinical/identity/date/domain-event/history leaves remain core accepted public-packet leaves。
- runtime surface：51 frozen non-cache files across
  `poc/medical_monitoring_ai_native_r5/src/mm_r5, poc/medical_monitoring_ai_native_r5/tests, poc/medical_monitoring_ai_native_r5/evidence`; inventory SHA `d94c9e7203572519f9db92c219d4f18a9b76fdd3af0fd8a60b98b85120ecb915`;
  exact 11 future allowlist paths are absent and arbitrary new paths fail closed.

## Authority review points

1. Core temporal and AEMH fields point to accepted public packet types and named producer validators.
2. Lossy parent objects are marked as compatibility replacements; no cutoff/date/history information is
   silently dropped.
3. Navigation state is typed and hashable but explicitly non-authoritative; selections must be verified
   against the same packet membership and cannot rewrite source identity.
4. Exact eight-domain subtype matrix rejects `ae/ip_dose` and every unlisted pair; legacy severity is exactly
   `severe→high`, `moderate→medium`, `mild→low`, with unknown values fail-closed.
5. Domain, date, severity, lexicon, legacy mapping and non-color encoding are closed and fail-closed.
6. Future exact-allowlist `s5_validator.py::validate_domain_subtype_pair` plus its test/challenge contract must reject
   `domain=ae, subtype=ip_dose` with `DOMAIN_SUBTYPE_MISMATCH` before projection acceptance; all such runtime/test paths remain absent.
7. Acceptance unlock text is exact and excludes 8911, UI/browser, real projects/models, production,
   medical-writing, accepted producer mutation and security work.
8. Fresh isolated acceptance must bind exact/manifest/generator/verifier/all-generated-artifact hashes and the exact token;
   the worker does not emit the token and the verifier cannot self-hash inside its own source.

## Required independent checks

The verifier must rerun generator `--check`, normal/`-O`/`-OO`, deterministic replay, source/path hash
tamper gates, core-leaf zero-deferred gates, challenge realization, protected medical-writing boundary and
stopped-port check. A verifier result is required before any downstream S5 runtime path is created.
