# Codex Main-Venue Plan: eligibility_visual_qc_vlm_20260711

Date: 2026-07-11
Objective: Design and critically review the production architecture for immutable eligibility visual-QC decisions, effective evidence projection, and an independently runnable clinical-photo VLM gateway using real D001 and MY009 source boundaries; no clinical conclusion generation and no production write before Codex review.

## Task Decomposition

1. Independently propose immutable QC/CAS/effective-projection state machines.
2. Independently propose a privacy-preserving, independently runnable clinical-photo VLM gateway and failure taxonomy.
3. Stress-test both designs against D001/MY009 project isolation, source drift, model drift, artifact tampering, retries and restart.
4. Have the `aishuo/MiniMax-M3` chair compare participant outputs and identify unresolved conflicts.
5. Have Reasonix DeepSeek Pro challenge the bounded package; Codex then decides whether any implementation is authorized.

## Source Packet

The authoritative bounded read list is recorded in the conference context and participant prompts. It contains current evidence schema/orchestration/worker/QC-adjacent code, focused tests, and safe D001/MY009 OCR/PDF execution records. Clinical source bodies and legacy conclusions are excluded.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_visual_qc_vlm_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_visual_qc_vlm_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/eligibility_visual_qc_vlm_20260711/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_visual_qc_vlm_20260711/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_visual_qc_vlm_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, late-output disposition, session id, and observed provider/model markers. Never silently substitute the chair route.

## Codex Verification Checklist

- Verify every prompt preflight and read/write boundary.
- Verify actual provider/model markers, output completeness and lack of silent fallback.
- Re-read current code after the concurrent parent-child OCR patch lands; reject stale recommendations.
- Verify schema migration, audit-chain, CAS, restart, idempotency, privacy and cross-project tests before any production write.
- Verify VLM gateway behavior with controlled non-clinical fixtures before any real clinical-photo pilot.
- Keep visual QC distinct from medical confirmation and final eligibility throughout API, storage and UI projections.
