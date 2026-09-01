# Conference Context: medical_monitoring_r4_d03_stable_acceptance_20260811

Created: 2026-08-11 22:45:40
Objective: 独立验收稳定哈希快照中的R4-D03研究药暴露、依从性、处置关系与renderer-neutral Patient Journey纵切
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then the distinct Cursor `cursor-grok-4.5-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window. Outside that window its exact Qwen Max node is replaced by Pi/OpenCode Go `deepseek-v4-flash` (max); during the night window, every exact Pi/cms-smk `deepseek-v4-flash` node is replaced by the same Pi/OpenCode Go route. Its remaining fallbacks are Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max), with effective-route deduplication. Participant 2 is Grok Build `grok-4.5`, with the distinct Cursor `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Frozen contract: `reviews/medical_monitoring_r4_d03_ip_slice_contract_v1_20260811.md` (`FROZEN_R4_D03_CONTRACT_V1_1`, SHA-256 `fa62e2293dd0951c7da76717186ff7d6d8aa3733ee5e1a51804a17c4dd776de9`).
- Stable D03 snapshot after round-1 remediation: `ip.py 10c8911a53ec3e271e3cc248113b667917dbcb849d3adf2d428bb54997a68429`; `test_ip_slice.py 7250124d53b9735b8941107d383664c8a2265ba9f0405468c5e5595eb0b366c2`; `ip_projection.py 3a0962ee27f67bf0010c7ce94af0b7780723f24fea0264ffabec468ca395cfa7`; `test_ip_projection.py 9bb2e28f483edbf90258fff9b2b46a0b52900ffb533db3b84f1663479ab2dbcb`; `ip_fixtures.py 21a3ef0f063329bf9df8e31e64a0b1103f574f2440b8cb72352360797418253d`; `test_ip_challenge_matrix.py e197d9ba38eaa594d29b8711fa43ffd1eaf01b6f457f018914f3c41423ac7e2c`; `__init__.py ea2c413b8a8ec03156edc5539a08a23a3571aacfa776597c119a3bb01ba6d063`; `test_shared_domain_protocol.py 145cc0112237fc653c358ab5cf7915eef3ea72310d8f84e61faf1a113aebf02e`.
- Frozen adjacent D02 evidence: `cm.py 7f46942509d5b10453898630494a1bcc6cd22d126cdf7d56833a785756859515`, `cm_projection.py 3298618d38d0bfd87da9973aa03cb95cd8d6ec8ec0412ac40e4a4dd843ecd98e`.
- Current filesystem is authoritative. Worker and manager reports are deliberately excluded from participant read sets to preserve verifier isolation.

## Scope

- In scope: read-only contract-to-code challenge, stable hash pre/post check, D03 focused/full R4 tests, R2/R3 adjacent regressions, Ruff/compileall, root object identity, deterministic projection payload, Chinese user-facing terminology and accountability-proxy wording.
- Out of scope: edits, product/R5 UI, real projects, services, security work, medical writing, production acceptance.

## Success Criteria

- Each participant independently returns `ACCEPT`, `REVISE`, or `BLOCKED` with file/line/test evidence and no access to peer or worker reasoning.
- Start and end hashes are identical; any drift forces `BLOCKED`.
- No unresolved contract violation, root-export shadowing, Chinese wording leak, proxy-as-actual-days conflation, or deterministic/join defect remains.
- Decisive non-LLM checks pass and port 8911 remains stopped.
- No file is modified; Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-11 22:45:40: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Round 1 returned REVISE for accountability raw-unit comparison. Remediation converts dispense, return and recorded values to the algorithm canonical unit, fails closed without a versioned basis, and adds challenge cases 50/51.
- Remediated local gates: R4 677, R2 598, R3 339, Ruff/compileall green, deterministic case-11 payload hash `f575a16827f25595094d0b104b34656a89e01d75bdd057fda6a7a499495429aa`, 8911 stopped.
- 2026-08-12: Grok/Cursor fallback static audit identified that derived assignment binding used subject+site+role+phase but did not enforce the frozen non-ambiguous time-window condition. Codex verified the defect from the contract and source, then changed only `ip.py` and `test_ip_slice.py`: definitely disjoint candidates are excluded; exact containment is eligible; partial/missing/boundary-overlap windows remain ambiguous and cannot bind. Four focused regressions cover disjoint, unique-window, partial-window, and exact-plus-unresolved cases.
- Current stable snapshot for the post-review remediation: `ip.py 8de705300763d4dbb6b9d7aba683445c843ae1f9b7bf68a679e5c44669c43c45`; `test_ip_slice.py f3764c609b582b4e63858a798b6155b9cf33b232989201d7f9416ce7639b3b73`; all other listed D03/D02 files retain the preceding hashes. Local gates: focused assignment binding 12 passed; R4 681 passed; R2 598 passed; R3 339 passed; Ruff/compileall green; case-11 payload hash remains `f575a16827f25595094d0b104b34656a89e01d75bdd057fda6a7a499495429aa`; payload contains `按发放/回收核算` and excludes `实际服药天数`; 8911 not listening; pre/post hashes identical.
