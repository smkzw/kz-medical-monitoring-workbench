# Codex Main-Venue Plan: medical_writing_revision_dialogue_20260713

Date: 2026-07-13
Objective: 将医学写作的一次性要求重写升级为同一来源段落内可追溯、多轮、独立AI驱动的细节修订会话；保留每轮用户反馈、AI候选、证据、父版本和审计，用户选择候选后仍须医学批准并显式应用工作副本。

## Task Decomposition

1. Define a backward-compatible per-suggestion turn contract and server-derived parent linkage.
2. Feed the previous persisted candidate and current user feedback into the independent-AI rewrite request without weakening source/evidence validation.
3. Persist each rewrite atomically with audit and enforce latest-pending-only actions.
4. Replace the latest-only AI rail detail with a dense chronological review ledger and preserve the approved-application band.
5. Run destructive repository/API tests and RUX/D001/PNH isolated multi-turn flows.
6. Run desktop browser QC, production build, full regression, conference synthesis and log persistence.

## Source Packet

- Contracts: `packages/contracts/workbench_contracts/models.py`.
- Services: `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `services/api/app/sqlite_runtime_store.py`.
- Frontend: `frontend/src/App.jsx`, `frontend/src/styles.css`.
- Tests: `tests/test_medical_writing_revision_api.py`, `tests/test_medical_writing_real_project_flow.py`, `tests/test_frontend_medical_writing_contract.py`.
- Prior closure: `records/active_slices/medical_writing_ai_change_application_20260713/TASK_RECORD.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_revision_dialogue_20260713/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_revision_dialogue_20260713/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_revision_dialogue_20260713/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_revision_dialogue_20260713/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end, same-session id, round count, pending/failed/incorporated status and any fallback in `metrics/medical_writing_revision_dialogue_20260713_conference_metrics.md`.

## Codex Verification Checklist

- Backward-compatible validation of existing thread fixtures and persisted databases.
- Server-derived parent and previous proposal; no client-provided proposal authority.
- Latest-pending-only action enforcement and atomic provider-failure rollback.
- All turns survive cold restart with their own instruction/comment/run/evidence/time metadata.
- Final accepted candidate alone can be medically approved and explicitly applied.
- Editor remains largest column; AI ledger is readable at 2048x1024 with internal scrolling and no page overflow.
- Three real protocols complete at least two turns from original source text.
- Review gate, relevant/full tests, build and logs pass.
