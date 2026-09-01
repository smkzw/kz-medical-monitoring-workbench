# Codex Main-Venue Plan: project_source_manifest_20260709

Date: 2026-07-09
Objective: Build ProjectSourceManifest as the unified real-project source and identity layer for the medical manager workbench, covering dashboard, eligibility, monitoring, TFL, writing, safety/PV, and source-boundary governance.

## Task Decomposition

1. Establish a real-project source/identity manifest covering MG-K10 demo, RUX-03-002, CMS-D001, and MY009 UC.
2. Add backend API with sanitized public payload and explicit source roles/route bindings.
3. Add frontend source context display and make monitoring use the monitoring source project for subject catalog, drill-down, inbox, raw-intake, intake submit, read action, and RUX risk disposition.
4. Add tests/contracts and desktop browser QC.
5. Ask Hermes/Reasonix to review remaining gaps after Codex implementation and verification.

## Source Packet

- Code: `services/api/app/project_source_manifest.py`, `services/api/app/main.py`, `frontend/src/App.jsx`, `frontend/src/styles.css`.
- Tests: `tests/test_project_source_manifest.py`, `tests/test_frontend_source_manifest_contract.py`, `tests/test_frontend_monitoring_contract.py`, `tests/test_frontend_timeline_contract.py`.
- Browser QC: `frontend/tests/project_source_manifest_qc.mjs` and outputs under `records/active_slices/project_source_manifest_20260709/visual_qc/`.
- Logs: `records/active_slices/project_source_manifest_20260709/*.md`, `logs/subsystems/module_scope_log.md`, `logs/subsystems/medical_monitoring_log.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/project_source_manifest_20260709/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/project_source_manifest_20260709/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/project_source_manifest_20260709/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/project_source_manifest_20260709/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/project_source_manifest_20260709/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Pending: Hermes/Reasonix review dispatch not completed yet.
- Codex implementation verification completed before dispatch.

## Codex Verification Checklist

- Backend manifest API: covered by `tests/test_project_source_manifest.py`.
- Frontend source context: covered by `tests/test_frontend_source_manifest_contract.py`.
- Monitoring route write boundary: covered by `tests/test_frontend_monitoring_contract.py`.
- Timeline source catalog: covered by `tests/test_frontend_timeline_contract.py`.
- Full regression: `183 tests OK`.
- Frontend build: `npm run build OK`, chunk warning unchanged.
- Browser QC: desktop Chrome CDP script passed; metrics/screenshots saved.
