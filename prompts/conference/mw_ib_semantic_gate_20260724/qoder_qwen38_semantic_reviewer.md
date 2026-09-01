# Qoder Scientific Semantic Review Contract

Use the existing QoderVIP `qodercli` session and model
`qwen3.8-max-preview`. Read the full global `/Users/smkzw/.codex/AGENTS.md`,
the workspace overlay `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`,
and then:

1. Read `context/mw_ib_semantic_gate_20260724_conference_context.md`.
2. Inspect only the listed source-of-truth files and any directly required
   adjacent functional/scientific code.
3. Do not perform security, vulnerability, attack-surface or backdoor review.
4. Do not edit production source. This is an independent medical-scientific
   and product-function review.
5. Distinguish:
   - direct product fact from an IB;
   - prior-study observation;
   - inferred interpretation;
   - current-study design decision;
   - unresolved high-impact fact.
6. For every observed unsafe proposal in the context, specify:
   - correct fact class;
   - whether it may populate current StudyDefinition automatically;
   - prompt constraint;
   - deterministic server-side validation/quarantine rule;
   - focused regression case.
7. Check whether the proposed policy generalizes across small molecules,
   antibodies, RNA products, oral, IV/SC, inhaled, intranasal and topical
   products without hard-binding to MY004 or rheumatoid arthritis.

Write a concise but implementation-ready report to
`runs/conference/mw_ib_semantic_gate_20260724/qoder_qwen38_semantic_reviewer.md`.
Include sources read, concrete observations, rejected approaches, uncertainty,
recommended implementation order and the completion marker:
`QODER_IB_SEMANTIC_REVIEW_COMPLETE`.
