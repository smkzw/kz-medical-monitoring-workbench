# Synopsis Source-Fidelity P0 Direct Evidence

Observed: 2026-07-20
Authority: Codex direct inspection of retained isolated product runtime

## Real source

- Path:
  `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/Ib期/MY009212A-UC-Ib-方案摘要-LXN.2024.01.27.docx`
- Size: `100977` bytes
- SHA-256:
  `7a038d8d90908b9a7e1525d32d65a8789c231bf9e04e7031cf879e59f7437267`
- Product parser output: 26 spans, approximately 7968 extracted characters.

## Product probe

- Retained runtime:
  `/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/w02-probe-HE4Zqj`
- API: isolated `http://127.0.0.1:60266`
- Start: `2026-07-20T08:32:06.425Z`
- Failure: `2026-07-20T08:43:08.348Z`
- Wall time: approximately 11 minutes.
- Product response: HTTP 503.
- Exact decisive error:

  `protocol synopsis source fidelity error at picos.safety_endpoints:
  expected 1 ordered source item(s), got 0`

- Expected ordered source text:

  `AE、药物不良反应（ADR）、SAE等的发生率，以及体重、体格检查、
  生命体征检查、十二导联心电图检查、妊娠检查（仅限育龄期女性）、
  临床实验室检查等的异常情况或变化情况。`

## Retained AI run

File:
`/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/w02-probe-HE4Zqj/ai_task_runs.jsonl`

- Run status: `failed`.
- Initial `provider_output_attempt` used the bare six-key study-definition
  shape rather than the required task envelope and failed required-key checks.
- The repair `provider_output` used the correct top-level envelope and carried
  16 evidence spans, but strict validation still reported the missing
  `picos.safety_endpoints` item.
- The retained audit artifact stores output hashes/key counts rather than the
  full sensitive provider payload, so the exact repaired JSON field value
  cannot be reconstructed from that artifact alone.

## Correct conclusions

1. The anchor builder produced exactly one expected safety item. A claim that
   the builder failed to recognize the row is contradicted by the error.
2. The independent model or repair flow failed to preserve the already
   deterministically anchored item and its evidence mapping.
3. A small-source synchronous fast path is unsafe: this 7968-character source
   still blocked for about 11 minutes.
4. Every AI-dependent synopsis import must use a persistent asynchronous job.
5. Exact source anchors should be materialized deterministically into the
   structured result and evidence mapping before final strict validation.
   DeepSeek should handle semantic extraction for unanchored fields; it should
   not be asked to regenerate exact clauses the deterministic parser already
   knows.
6. Strict one-to-one validation must remain. The fix is authoritative
   deterministic restoration plus targeted model repair for unanchored
   semantic fields, not weakening validation.
