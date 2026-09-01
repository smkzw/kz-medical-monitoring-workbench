# Codex Main-Venue Plan: evidence_picos_productization_20260710

Date: 2026-07-10
Objective: Audit and productize the Evidence Research and Protocol Design subsystem using real CRSwNP and a second real indication, with auditable evidence lifecycle, versioned PICOS decisions, AI revision interaction, medical approval, and typed medical-writing handoff.

## Task Decomposition

1. Audit current CRSwNP-only manifest, hard-coded PICOS options, JSONL persistence, route binding and monolithic frontend.
2. Compare CRSwNP CSV and PNH SQLite source shapes and define a normalized package-adapter interface.
3. Define typed evidence-lifecycle contracts and transactional persistence.
4. Define versioned PICOS, anchored AI revision, medical approval and writing-handoff boundaries.
5. Define an editor-like desktop experience centered on evidence review and PICOS decisions.
6. Implement the bounded P0 slice after conference synthesis, then test both real indications.
7. Run Codex browser/visual acceptance and a post-implementation conference review before claiming the slice complete.

## Source Packet

- `context/evidence_picos_productization_20260710_conference_context.md`
- `records/active_slices/evidence_picos_productization_20260710/SOURCE_AUDIT.md`
- `records/research/evidence_design_external_benchmark_20260710.md`
- Current backend/contracts/frontend files listed in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/evidence_picos_productization_20260710/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/evidence_picos_productization_20260710/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/evidence_picos_productization_20260710/participant_ds_flash.md` |
| `participant_glm52_product` | `buddy` | `glm-5.2` | `runs/conference/evidence_picos_productization_20260710/participant_glm52_product.md` |
| `participant_kimi_frontend` | `buddy` | `kimi-k2.7-code` | `runs/conference/evidence_picos_productization_20260710/participant_kimi_frontend.md` |

Assignments:

- Qwen: whole-workflow product architecture and medical-manager operating model.
- MiMo: data contracts, persistence, API states and two-indication test strategy.
- Reasonix DeepSeek Flash: architectural defect/risk audit and smallest reliable implementation sequence.
- Buddy GLM: Chinese clinical terminology, medical-review interaction and approval semantics.
- Buddy Kimi: desktop information architecture, evidence/PICOS interaction and component decomposition.
- If a Buddy route terminally fails, use `opencode-go/qwen3.7-plus` or `opencode-go/mimo-v2.5` only as the explicitly recorded fallback; do not silently substitute.

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/evidence_picos_productization_20260710/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/evidence_picos_productization_20260710/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record route, actual model/provider markers, start/end, status, retry reason and whether the output was incorporated.
- Keep slow routes pending under the conference timeout policy.
- Retry Buddy Kimi with a compact prompt once if request-size parameters fail.

## Codex Verification Checklist

- Prompt preflight passes and every participant writes exactly one bounded output.
- All route/model markers are verified from stdout.
- Conference conclusions are reconciled against current source, contracts and frontend code.
- P0 code has tests first or alongside implementation.
- Two real indications run without cross-project fallback or absolute-path leakage.
- State transition, restart, privacy and handoff-gate tests pass.
- Frontend build, fixed-desktop browser interactions and reference-aware visual QC pass.
- Logs, source audit, LOOP ledger, conference review and metrics are updated.
