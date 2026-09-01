# Codex Main-Venue Plan: mw_paddle_ocr_cutover_20260801

Date: 2026-08-01
Objective: 只读反证审阅医学写作 PaddleOCR-VL-1.6 文件级切换、429退避并发与回退审计合同

## Task Decomposition

1. Independently audit the file-level OCR pin, hosted Paddle adapter, fallback
   provenance, and mixed-model QC boundary.
2. Remediate only bounded correctness gaps without restarting the active
   runtime.
3. Prove the new contracts with deterministic fakes and focused tests.
4. Reuse the same participant sessions for delta review, then obtain the
   sub-venue chair recommendation and perform Codex final acceptance.

## Source Packet

- Current workbench filesystem and the explicit read set in
  `context/mw_paddle_ocr_cutover_20260801_conference_context.md`.
- Real isolated-runtime probe and persisted page-level provenance.
- Focused deterministic test output and compileall evidence.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/mw_paddle_ocr_cutover_20260801/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/mw_paddle_ocr_cutover_20260801/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_paddle_ocr_cutover_20260801/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Native Codex participant: one initial pass plus same-session delta review;
  final READY incorporated.
- Pi/DeepSeek participant: initial pass plus same-session round 2 completed;
  its final retry-boundary P3 was incorporated and proved before chairing.
- No participant was redispatched because of latency.

## Codex Verification Checklist

- [x] Durable file-level OCR model pin survives restart/retry.
- [x] Outcome-unknown Paddle work cannot enter generic retry or worker claim.
- [x] Only verified rejection/terminal failure can transfer to GLM.
- [x] Hosted concurrency is hard bounded to 1..4.
- [x] Retry-After is capped and 5xx submit is not blindly retried.
- [x] 106 focused tests pass; compileall passes.
- [x] Real Chrome runtime inspected; active service was not restarted.
- [ ] Sub-venue chair completed and Codex final synthesis recorded.
