# Phase G identity authorization — context checkpoint

Date: 2026-08-02 08:10 CST  
State: **offline identity/action contract complete; controlled runtime integration blocked**

## Source of truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §5.1、§29.1–29.2；
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P2-01、§7；
- `services/api/app/medical_risk_authority.py` identity/CAS contract；
- B6 `B6_REVIEW_OUTCOME_GATE.json` and C13 `ACTIVATION_PROJECTION_BLOCKED_REPORT.json`.

## Completed

- Added immutable `MonitoringPrincipal`, `MonitoringAuthorizationRequest` and
  `MonitoringAuthorizationDecision` with explicit principal/session/project scope.
- Added closed role/action policy for target medical-monitoring deployment, including medical-writer
  read/export boundary and system-admin non-medical boundary.
- Added high-impact reauthentication/e-signature requirements and medical-director-only high-risk
  close/rule-change actions.
- Added first-release unified medical-manager helper with no hidden actor fallback.
- Focused **9 passed**; adjacent identity/risk/capability/AI release contracts **27 passed**;
  full monitoring regression **1579 passed, 25 warnings**; Ruff/compile passed after formatting.

## Not done / blocked

- No authentication provider, directory scope, middleware, router integration, real e-signature,
  session revocation, append-only audit persistence or CAS-bound runtime write.
- B6 remains `pending_review` (5 candidates/0 outcomes/2 blockers); C13 remains schema-only with
  `activation_allowed=false`; 8911/5174 remain stopped.
- No real three-project onboarding, AI runtime, browser acceptance, UAT or commercial deployment proof.

## Parallel-change boundary

The previously observed `medical_writing_*`, `chapter_translation_pipeline.py`,
`workbench_inbox.py`, `workbench_notifications.py` and `writing_reference*` mtime group remains
outside this slice. It was not edited, formatted, hashed or semantically reviewed; preserve it as
parallel user work until its owner supplies a handoff.

## Next safe action

Keep the contract offline. First recheck B6/C13/ports and any new review outcome; if B6 is still
pending, continue only with a narrowly bounded release-hardening contract that does not change
runtime defaults. If B6 becomes authorized, re-read the current files and obtain explicit scope for
aggregate/CAS/source-token replay before any runtime or identity middleware integration.
