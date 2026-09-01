# Route And Time Guard

This guard is evaluated immediately before each external-tester launch and
again before every targeted follow-up. It does not authorize fallback models
to count as the named final tester.

## Clock Authority

- Use `Asia/Shanghai`.
- Record ISO timestamp, UTC offset and local wall-clock time in
  `TESTER_ROUTE_RECEIPT.json`.
- Do not infer the time window from a stale prompt or session.

## Exact Tester Routes

| Tester | Required runtime identity | Mandatory evidence | Acceptance behavior |
|---|---|---|---|
| A | Codex subAgent `gpt-5.6-luna`, exact reasoning `high` | spawn receipt plus effective model and reasoning effort | No artificial time window; identity or effort mismatch fails closed |
| B | Pi/OMP `aishuo/cms-model` | requested selector, stdout/session `model_change`, durable provider/model | Never start or follow up in blackout; no substitute counts as B |
| C | CodeBuddy CLI `hy3` | executable/session identity and visible model receipt | Different model fails closed |
| D | Pi/OMP `google-antigravity/gemini-3.6-flash` with thinking `high` | requested selector, durable `model_change`, `thinking_level_change`, provider/model response identity | another Gemini model, provider or thinking level does not count as D |

## OMP Integrity

For Tester B and D:

1. Use `/Users/smkzw/.local/bin/omp`.
2. Pin one exact provider/model.
3. Use `--no-prewalk`.
4. Do not use `smol`, `slow`, `plan`, model cycling, auto-selection or a saved
   session whose active model differs.
5. Reject every undeclared model.
6. Compare the requested selector with both stdout and durable-session
   `model_change` evidence. Missing or conflicting identity means FAIL.
7. A route parser label is not enough; preserve raw identity evidence.
8. Tester D's declared identity is
   `pi/google-antigravity/gemini-3.6-flash`; the exact model uses the separate
   OMP thinking level `high`. OMP does not expose a
   `gemini-3.6-flash-high` model ID.
9. Tester A is not an OMP route. Its subAgent spawn must explicitly request
   `gpt-5.6-luna` with `high`; inherited defaults or a different Luna effort do
   not count.

## Beijing Aishuo Blackout

- Blackout: `00:00 <= local time <= 08:30` Beijing.
- To avoid boundary ambiguity, schedule new Tester B passes and follow-ups
  before `00:00` or from `08:31` onward.
- A complete pass started before midnight may finish naturally.
- After midnight, do not continue, remediate or follow up in that Aishuo
  session.
- The global route policy allows cross-provider replacement for general work,
  but a replacement no longer proves the exact Tester B identity. Therefore:
  defer the final B test until the route is legal. A fallback run may be
  retained as diagnostic evidence only and cannot satisfy B1-B3 acceptance.

## Tester And Product-AI Separation

Each run records two independent identities:

1. `tester_route`: the external model controlling the browser and evaluating
   the product;
2. `product_ai_route`: the provider/model reported by the product for each
   competitor search, analysis, prefill, candidate or revision job.

The two receipts must not be conflated. The tester must not call its own model
to supply product outputs. Product AI calls require prompt version, input/output
hash, job/run ID and failure/recovery lineage.

## Dispatch Decision

The orchestrator writes one of:

- `ALLOW`: exact identity, legal time, clean state and product readiness pass;
- `DEFER`: time window or a prerequisite is not yet satisfied;
- `FAIL_CLOSED`: selector/model identity is wrong or unverifiable.

No slot starts on `DEFER` or `FAIL_CLOSED`.
