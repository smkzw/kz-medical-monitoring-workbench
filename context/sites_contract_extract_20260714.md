# Sites Contract Extract For Deployment Review

Read by Codex: 2026-07-14

## Source identities

| Source | SHA-256 |
|---|---|
| Sites building skill | `be568720e1e1a7577ff3f5826b75abdcd0d06affd6cf2b10ff5245bc3aec9d2b` |
| Sites hosting skill | `403c73cc078b05a5da72eb1fd6c19ffb44d81c6833b5dda2a3676f9c34e5aded` |
| Persistence guidance | `a4f6e53e07564b4f3ddfa462c76e219615f25e30a7848ebd3b5787e7d12319b5` |
| Authentication guidance | `d96b347d8ba0d9efa577a5594209352b9e900204c10ff12b7eeb5d5ca4891450` |

## Verified build and hosting contract

- An existing site with persistence, uploads, authentication, external data or browser testing follows the capability path.
- Sites source uses a Cloudflare Worker-compatible ESM build. The hosting package expects a server entry such as `dist/server/index.js`, static assets and `.openai/hosting.json`.
- `.openai/hosting.json` stores only the Sites project ID and optional logical D1/R2 bindings; runtime values are managed through Sites.
- A new site is created once, source is versioned, a validated version is saved, and only a saved version is deployed.
- Sites exposes connector capabilities for private/shared deployment, access policy, versions, environment variables and custom domains.

## Verified persistence contract

- D1 is the default for durable structured product state needing filtering, sorting, joins, ownership checks or durable IDs.
- R2 is used for documents, uploads, images, exports and other blobs; D1 can store their metadata.
- Browser storage is only for local, non-authoritative UI preferences or explicitly local state.
- D1 schema/migrations and R2 metadata/ownership must be designed; Sites does not migrate SQLite or local files automatically.

## Verified authentication contract

- Sites can use dispatch-owned Sign in with ChatGPT for protected browser routes and can forward an authenticated workspace email/name.
- Successful SIWC identifies a ChatGPT user but does not prove company workspace membership.
- Workspace-wide restriction needs Sites access policy, and stricter membership/allowlist requirements need server-side enforcement.
- Authentication is not equivalent to project authorization or role-based authorization.

## Current connector observation

The current Codex session exposes callable Sites tools for create/get/list, save version, private/shared deployment, deployment status, access policy, runtime environment variables, custom domains and SIWC bypass token. No tool was called to create or deploy a Site.

## Claims not established by these contracts

- Python FastAPI execution on Sites.
- Direct reuse of SQLite or macOS local filesystem paths.
- Connectivity from Sites to private company networks or local AI/OCR endpoints.
- Suitability for long-running document parsing, OCR or model tasks without an external execution service.
- Compliance with Kangzhe security, privacy, data residency, supplier management or clinical-data policies.
- Replacement for company SSO, project isolation or fine-grained clinical RBAC.
