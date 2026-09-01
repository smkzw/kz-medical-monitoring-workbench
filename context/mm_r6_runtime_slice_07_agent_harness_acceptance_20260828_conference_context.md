# Conference context — R6 slice-07 Agent Harness acceptance

## Question

独立审查最终文件系统候选是否可按
`ACCEPT_R6_RUNTIME_SLICE_07_AGENT_HARNESS_ADAPTER_LIMITED` 接受；重点寻找可使错误 provider/
model/effort/profile/input/coverage 仍被标记 complete 的反例，以及命令、NDJSON、路径、
fallback、凭据和证据声明的越界。

## Read set

- `context/medical_monitoring_r6_runtime_slice_07_agent_harness_contract_20260828.md`
- `reviews/codex_execution_mm_r6_runtime_slice_07_agent_harness_20260828_review.md`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_agent_harness.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_agent_harness_runtime_receipt.json`

## Frozen candidate

- source SHA: `0546c10c51a57795c521b2f605276e02c06c676bfe8625268863d8ddc961a515`
- test SHA: `57326dced117c1ae29499b265bdd7a1859ae375e05b56e094843725141147155`
- receipt SHA: `fd61f5483360476d4f76d6a9f61642fe83aa69799a64f7aefb36cd44c126d98d`
- focused: 35 passed; full POC: 763 passed
- real smokes rerun by Codex after repair: MTPLX medium and DeepSeek max both complete/parsed,
  zero missing units, no fallback.
- Grok round-1 P1 已修复：NDJSON 只接受完整 assistant chunk/完整 fenced JSON，最后一个
  有效对象为准；不再从散文中的花括号片段提取；单事件 OMP envelope 进入相同提取路径。

## Hard boundaries

- Read-only review. Do not edit files, start services, use real projects, browser or OCR.
- Do not inspect or reveal credentials. Public model catalog and recorded hashes are sufficient.
- Do not claim product, medical-quality, long-session resume/cancel, R6 overall or R7 acceptance.
- Findings must include concrete reproducible counterexample and severity. Distinguish blocking defect,
  bounded limitation and future product work.

## Acceptance response

Return `accept_limited` only if no open P0/P1/P2 contract defect remains. Otherwise return
`revise` with the smallest exact repair and test. Codex owns final disposition.
