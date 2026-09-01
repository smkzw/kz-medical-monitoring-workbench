# Final 4x3 E2E Orchestration Package

Status: prepared only; no tester has been launched and no product/runtime state
has been changed by this package.

Workspace:
`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Authoritative inputs:

- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TEST_MATRIX_DRAFT.md`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TESTER_D_AMENDMENT_20260727.md`
- global and project `AGENTS.md`

Read in this order before any future launch:

1. `COMMON_TESTER_CONTRACT.md`
2. `ROUTE_TIME_GUARD.md`
3. `CLEAN_STATE_BACKUP_RESET_CHECKLIST.md`
4. The tester-specific launch prompt
5. `PER_SLOT_COMPLETION_SCHEMA.json`
6. `MATRIX_ASSIGNMENT.json`
7. The original matrix for the complete slot-specific medical contract

Tester prompts:

- `TESTER_A_CODEX_SUBAGENT_LUNA_HIGH.md`
- `TESTER_B_PI_AISHUO_CMS.md`
- `TESTER_C_CODEBUDDY_HY3.md`
- `TESTER_D_PI_ANTIGRAVITY_GEMINI36_FLASH_HIGH.md`

Preparation findings:

- `../../evidence/final_4x3_e2e_20260727/MATRIX_CONTRADICTIONS.md`
- `../../evidence/final_4x3_e2e_20260727/SUBAGENT_REPORT.md`
- `../../evidence/final_4x3_e2e_matrix_20260727/MATRIX_AUDIT_REPORT.md`
- `../../evidence/final_4x3_e2e_matrix_20260727/MATRIX_VALIDATION.json`
- `../../evidence/final_4x3_e2e_matrix_20260727/CLINICALTRIALS_PROTOCOL_COUNT_RECEIPT.json`

The package is not a launch authorization. The orchestrator must first confirm
that the current Slice B, live Hy-MT2 translation acceptance, and other
release prerequisites recorded in the audit journal are closed.
