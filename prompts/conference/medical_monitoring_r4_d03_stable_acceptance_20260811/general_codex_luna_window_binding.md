MODE=CONFERENCE
TASK_ID=medical_monitoring_r4_d03_stable_acceptance_20260811
ROLE=independent_verifier
MODEL_ROUTE=codex-subagent/codex/gpt-5.6-luna:max
WORKSPACE=/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench

You are an independent verifier in a fresh context. Codex is final authority.

Hard boundaries:
- Work only inside the current workspace `.`.
- Read-only: do not edit any file, start services, or access real projects.
- Do not read worker, manager, prior participant, peer-review, or final-review reports.
- Do not access medical-writing files.
- Port 8911 may receive only a read-only listen check; do not start it.
- Runner-managed report path: `runs/conference/medical_monitoring_r4_d03_stable_acceptance_20260811/general_codex_luna_window_binding.md`. Return the report; never write it with tools.

Objective: accept or reject the current post-remediation R4-D03 stable snapshot. The frozen contract requires a derived assignment link to be unique by subject + site + treatment role + phase + non-ambiguous time window. Challenge the current implementation rather than trusting prior claims.

Read these files only:
- AGENTS.md
- reviews/medical_monitoring_r4_d03_ip_slice_contract_v1_20260811.md
- poc/medical_monitoring_ai_native_r4/src/mm_r4/ip.py
- poc/medical_monitoring_ai_native_r4/tests/test_ip_slice.py
- poc/medical_monitoring_ai_native_r4/src/mm_r4/ip_projection.py
- poc/medical_monitoring_ai_native_r4/tests/test_ip_projection.py
- poc/medical_monitoring_ai_native_r4/src/mm_r4/ip_fixtures.py
- poc/medical_monitoring_ai_native_r4/tests/test_ip_challenge_matrix.py
- poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py
- poc/medical_monitoring_ai_native_r4/tests/test_shared_domain_protocol.py
- poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py
- poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_projection.py
- context/medical_monitoring_r4_d03_stable_acceptance_20260811_conference_context.md

Expected current SHA-256 values:
- contract fa62e2293dd0951c7da76717186ff7d6d8aa3733ee5e1a51804a17c4dd776de9
- ip.py 8de705300763d4dbb6b9d7aba683445c843ae1f9b7bf68a679e5c44669c43c45
- test_ip_slice.py f3764c609b582b4e63858a798b6155b9cf33b232989201d7f9416ce7639b3b73
- ip_projection.py 3a0962ee27f67bf0010c7ce94af0b7780723f24fea0264ffabec468ca395cfa7
- test_ip_projection.py 9bb2e28f483edbf90258fff9b2b46a0b52900ffb533db3b84f1663479ab2dbcb
- ip_fixtures.py 21a3ef0f063329bf9df8e31e64a0b1103f574f2440b8cb72352360797418253d
- test_ip_challenge_matrix.py e197d9ba38eaa594d29b8711fa43ffd1eaf01b6f457f018914f3c41423ac7e2c
- __init__.py ea2c413b8a8ec03156edc5539a08a23a3571aacfa776597c119a3bb01ba6d063
- test_shared_domain_protocol.py 145cc0112237fc653c358ab5cf7915eef3ea72310d8f84e61faf1a113aebf02e
- cm.py 7f46942509d5b10453898630494a1bcc6cd22d126cdf7d56833a785756859515
- cm_projection.py 3298618d38d0bfd87da9973aa03cb95cd8d6ec8ec0412ac40e4a4dd843ecd98e

Verify hashes before and after review. Any drift is BLOCKED. Inspect the derived-binding algorithm and adversarially reason about: definite disjointness, exact containment, partial dates, missing/ongoing endpoints, multiple exact candidates, exact plus unresolved candidates, and direct-link precedence. Confirm ambiguous or missing binding cannot silently yield a positive/negative assessment. Also re-check accountability canonical-unit conversion cases 50/51, proxy wording, six Chinese user labels, deterministic typed journey joins, root export non-shadowing, and D01/D02 adjacent behavior.

Run these decisive gates with real command evidence:
- focused AssignmentBinding tests
- full R4 tests
- R2 and R3 test suites
- Ruff on R4 source/tests
- compileall on R4 source/tests
- deterministic case-11 projection payload hash; expected f575a16827f25595094d0b104b34656a89e01d75bdd057fda6a7a499495429aa; payload must contain 按发放/回收核算 and must not contain 实际服药天数
- port 8911 must not be listening

Return a concise report with exact commands/results, path/line findings, residual risks, and one verdict: ACCEPT, REVISE, or BLOCKED. ACCEPT only if there is no unresolved contract violation and all decisive gates pass. Do not modify files and do not claim product/R5/real-project acceptance.
