# Codex Main-Venue Plan: rux_monitoring_disposition_20260708

Date: 2026-07-08
Objective: Implement and verify a minimal RUX medical monitoring risk disposition loop: reviewed -> query_draft -> submitted_for_approval, preserving mark_read as notification state and using real RUX project risks.

## Task Decomposition

1. Locate current evidence.
   - Read RUX inbox, workbench action contract, frontend risk detail, tests, and monitoring logs.
   - Record current limitation: `mark_read` only.
2. External reference check.
   - Use official RBQM/RBDM product pages and bounded GitHub/open-source searches to inform the minimal risk-review workflow.
   - Do not import vendor-specific claims into code; use only to check that a risk-review disposition/audit loop is product-sensible.
3. TDD backend.
   - Add tests for ordered disposition transitions on a real RUX risk item.
   - Add invalid-transition and payload-boundary tests.
   - Observe failing tests before implementation.
4. Implement backend.
   - Extend `WorkbenchItemAction` and action request/record contract.
   - Persist latest disposition state without conflating with read state.
   - Hydrate RUX risk `WorkbenchItem.status`, `needs_action`, `action_label`, and `source_version` from disposition overlay.
5. TDD frontend/static contracts.
   - Add contract assertions that risk detail exposes state-aware actions and no longer says Query/正式处置 is deferred.
6. Implement frontend.
   - Add comment/query draft input and state-aware buttons.
   - Wire each action to the same backend route and refresh inbox.
7. Browser QC.
   - Extend `frontend/tests/rux_monitoring_inbox_qc.mjs` to run review -> query draft -> submit approval.
   - Assert item persists, status changes, unread/read semantics remain separate, no leakage/overflow, and drilldowns still work.
8. Verify and record.
   - Build, focused tests, full regression, browser QC, and logs.
   - Keep the slice bounded: not full RUX commercialization, not formal EDC/eTMF approval.

## Source Packet

- `context/rux_monitoring_disposition_20260708_conference_context.md`
- `services/api/app/workbench_inbox.py`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/main.py`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_workbench_inbox.py`
- `tests/test_frontend_monitoring_contract.py`
- `frontend/tests/rux_monitoring_inbox_qc.mjs`
- `frontend/AGENTS.md`
- `logs/subsystems/medical_monitoring_log.md`
- `logs/system_build_log.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/rux_monitoring_disposition_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/rux_monitoring_disposition_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/rux_monitoring_disposition_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/rux_monitoring_disposition_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/rux_monitoring_disposition_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

| Role | Status | Notes |
|---|---|---|
| `participant_qwen_plus` | pending | Run if route preflight passes. |
| `participant_mimo` | pending | Run if route preflight passes. |
| `participant_ds_flash` | pending | Run if route preflight passes. |
| `hermes_lead` | pending | Review participant outputs when available. |
| `main_deepseek_pro` | pending | Use after Codex implementation/review package is ready or if conflict emerges. |

## Codex Verification Checklist

- Backend focused tests:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_workbench_inbox -v`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_rux_monitoring_service -v`
- Frontend contract tests:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_frontend_monitoring_contract -v`
- Frontend build:
  - `npm --prefix frontend run build`
- Browser QC:
  - `APP_URL=http://127.0.0.1:<frontend-port>/ API_BASE=http://127.0.0.1:<backend-port> QC_OUTPUT_DIR=records/visual_qc_20260708/rux_monitoring_disposition_current CHROME_DEBUG_PORT=<port> node frontend/tests/rux_monitoring_inbox_qc.mjs`
- Full regression:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
