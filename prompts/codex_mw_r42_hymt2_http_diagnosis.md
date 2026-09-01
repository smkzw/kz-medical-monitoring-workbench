# MODE=CONFERENCE — r42 Hy-MT2 HTTP route diagnosis

## Objective

Read-only diagnose why the isolated controlled replay reached
`translating_hy_mt2` for three recovered plans but failed with
`CompositePipelineUnavailableError: body translation model unavailable:
HTTPError`. Determine the smallest safe recovery action; do not perform it.

## Read these files only

Read these files only:
- `runs/mw_r42_planner_retry_controlled_replay_20260731.md`
- `services/api/app/main.py`
- `services/api/app/ai_role_runtime_settings.py`
- `services/api/app/omlx_workload_gate_client.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/SCHEDULED_AI_ROLE_BINDINGS.json`

Read-only local process/listener, oMLX gate-status, installed executable/model,
and loopback endpoint inspection is allowed. Do not read provider secret files,
API keys, credentials, clinical source text, prompts, or provider outputs.

## Questions

1. Which exact profile/base URL/model does `translation_body` resolve to?
2. Did the product correctly acquire/release the shared translation lease?
3. Was the failure admission/gate, connection/listener, model availability,
   endpoint contract, or response-schema related?
4. Is an oMLX server currently listening, and is the required exact model
   available locally?
5. What exact bounded command/config is the next safe recovery action under the
   global oMLX gate contract? Distinguish starting a model server from issuing a
   translation request.
6. What preflight and stop conditions must pass before another item retry?

## Hard boundaries

- Read-only diagnosis except the single report below.
- Do not start/stop a service or model server.
- Do not acquire a translation lease or issue any model/provider request.
- Do not retry any batch/item or modify either original/clone runtime.
- Do not expose secrets or raw clinical/provider content.
- Do not read/write outside the explicit file list plus permitted read-only
  process/listener/gate/model-status inspection.

## Output

Write exactly one output file:
`runs/codex_mw_r42_hymt2_http_diagnosis.md`

Report root cause with evidence, current gate/listener/model state, exact next
safe action, acceptance checks, and residual risk. End with
`DIAGNOSIS_COMPLETE`.
