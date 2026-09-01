# Task Context: medical_monitoring_phase_b6_codex_review_recommendation_20260802

Created: 2026-08-02  
Objective: 在不生成授权医学/工程 review outcome 的前提下，核对 B6 五条 candidate 的
source evidence、身份守恒和 residual blocker，形成可交给授权 reviewer 的 Codex 独立
审查建议稿。

## Source of truth

- `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/MAPPING_REVIEW_AND_DRYRUN.json`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/runtime_zero_submit/medical_risks.sqlite3`
- `services/api/app/medical_risk_mapping_review.py`
- `services/api/app/medical_risk_mapping_approval.py`

## Scope and boundaries

- 只读打开 B3/B4/B6 evidence 与 isolated zero-submit clone 的 SQLite；
- 校对当前风险实例、evidence snapshot 可用性、source revision、legacy/current identity、
  disposition chain 和 B6 candidate fingerprint；
- 生成非授权建议稿及 checkpoint 记录；
- 不创建 `MedicalRiskMappingReviewOutcome`，不修改 B6 JSON，不写任何 runtime DB，不启动
  8911/5174、服务、浏览器、adapter、AI 或真实项目，不触碰 18911/PID 43191。

## Current facts

- B6 仍为 `pending_review`：5 candidates、0 outcomes、5 missing、
  `migration_ready=false`、`write_permitted=false`。
- MY009 三条映射到当前 `my009_risk_9c49023c2646` / S01003，但 legacy instance/key
  与 source token 缺失；须完成 source-token revalidation，并将三条链作为 aggregate replay
  单元核对。
- RUX 两条映射到当前 `rux_risk_fe2eff1e19` / S01003，source revision 与 risk key 为
  exact-after-identity；最新 evidence snapshots 可用，但仍没有授权 reviewer outcome。
- 证据支持“需要明确人工复核”，不支持 Codex 代替 reviewer 判断停药、AE、CTCAE、复测闭环
  或外部行动。

## Output and next action

Output: `runs/execution/medical_monitoring_phase_b6_codex_review_recommendation_20260802/CODEX_INDEPENDENT_REVIEW_RECOMMENDATION.md`。

下一安全动作：将建议稿交给授权 reviewer，取得绑定 B3 hash、B4 SHA-256、candidate
fingerprint、reviewer、带时区时间和 source locator 的五条显式 outcome；仅在 B6 返回
`approved_input_ready` 后再做 approved-input 内存 dry-run。之前不得真实 onboarding、
runtime 接线、event/projection activation、迁移或服务启动。
