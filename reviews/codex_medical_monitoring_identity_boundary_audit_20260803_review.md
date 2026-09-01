# Codex Review: medical_monitoring_identity_boundary_audit_20260803

Date: 2026-08-03 CST  
Review type: direct Codex offline static review

## Verdict

**PASS as a bounded audit; P1 commercial-release residual remains open.**

The existing identity/RBAC module is a meaningful offline contract, but it is not yet
runtime authentication, authorization middleware, or server-derived actor identity.
No source or runtime mutation was made in this slice.

## Direct evidence

| Surface | Observation | Interpretation |
|---|---|---|
| `monitoring_identity_authorization.py` imports | Only `monitoring_audit_contract.py` and identity tests import it; no `main.py` or monitoring router import | Offline contract is not wired to API requests |
| Assurance API schemas | 5 `default="medical_manager"` actor/confirmed-by fields | Client/body value can stand in for identity unless a future dependency rejects it |
| Medical monitoring API schemas | 9 default actor/created-by/confirmed-by fields | Same residual across protocol/risk/rule actions |
| AI/protocol routers | 4 + 1 default actor fields | AI and protocol authoring paths share the same missing principal boundary |
| Frontend | 32 literal actor payloads in `App.jsx` plus 1 in Assurance panel | Browser currently supplies a role-like actor string instead of a session principal |
| Assurance UI | Creation requires complete frozen identity and explicit `assurance_write_permitted=true` | Correct UI gate, insufficient as server authorization |
| API dependency scan | No principal/session/auth dependency was found on the affected routes | Project scope, role, re-authentication and e-sign are not runtime-enforced here |

## Risk classification

- **P1 release blocker:** a commercial deployment cannot treat a client-supplied
  `actor` string as an authenticated medical identity or audit signer.
- **Not a new B6 blocker:** this audit does not alter the pending formal reviewer outcome,
  aggregate/CAS replay, source-token revalidation or approved-input gate.
- **Not automatically P0:** the current offline contracts and UI fail-closed states prevent
  us from claiming production readiness, but no live write was executed or observed.

## Required Phase G order

1. Define a runtime principal adapter carrying authenticated subject, tenant, project scope,
   roles, authn method, session id and directory revision.
2. Inject the principal through API dependencies and derive `actor`/`confirmed_by` on the
   server; reject or ignore those client body fields rather than trusting them.
3. Apply the existing `MonitoringAuthorizationRequest` decision to read, review,
   disposition, rule-change, high-risk close and assurance actions, including project scope,
   re-authentication and electronic-signature evidence.
4. Persist `MonitoringAuditEvent`/decision hash in the append-only audit path and make
   correlation/idempotency keys independent of the actor string.
5. Bootstrap the frontend from the session principal; remove literal actor payloads from
   write requests while retaining visible identity/permission explanations.
6. Add negative API tests (missing session, wrong project, wrong role, forged actor,
   stale directory revision, high-risk missing re-auth/signature) and browser evidence for
   two distinct roles.

## Verification and boundary

- Source searches and deterministic counts only.
- Workbench and CxH mirror review-gates returned `ok: true` with no warnings or errors.
- No pytest, Node, Vite, service, provider, browser/API login, runtime DB, migration,
  aggregate/CAS replay, B6 outcome or real-project operation occurred in this slice.
- 8911 and 5174 remain stopped; no unrelated runtime was touched.

## Hermes workflow review

No delegated route was dispatched. Direct Codex performed and accepted the audit.
