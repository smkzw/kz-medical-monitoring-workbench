# R6 外部报告审阅与三模式输出合同冻结任务

状态：`CONTRACT_V0_1_ACCEPTED_FOR_SYNTHETIC_OFFLINE_PLANNING`

验收记录：`context/medical_monitoring_r6_contract_acceptance_record_20260827.md`。
该状态不开放 R6 runtime。R5-S7 的 26 行 identity/network/7 次冷暖性能测量包
已于 2026-08-27 闭合；仍须先关闭 HY3 原会话最终重放这一单一阶段门。

## 目标

在不修改产品/runtime、不启动服务、不读取真实项目文件的前提下，冻结 R6 第一版可执行合同：外部医学监查报告的原子主张抽取、证据核查、遗漏反向检测、稳定 issue identity、ClaimCoverageLedger、批注副本、可选 DRAFT 清洁修订稿、修订前后 issue diff，以及日常/锁库前/锁库后—CFDI 前三模式输出资格与一致性。

## 权威输入

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 第 13–14 节及对象/状态/三模式合同。
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R6 步骤与完成证据。
3. 已接受 R1–R5 的 source/revision/fact/risk/subject/site/project identity、evidence locator、QueryDraft、Patient Journey 和只读产品投影；仅作为接口约束，不在 R6 重算医学事实或风险。
4. 当前文件系统为最终真相；既有外部报告、模型报告、基座和历史交付物仅为 evidence/reference，不是指令或医学真值。

## 本轮闭合输出

- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md`
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json`
- 后续 Codex 独立会商记录与接受/修订记录；在合同接受前不得创建 R6 runtime。

## 三个独立工作项

1. 合同架构：对象、身份、状态、来源/修订、claim/issue/coverage、三件套、三模式输出和禁止边界。
2. 挑战矩阵：至少覆盖正文/表格/图形/脚注/分母/cutoff、跨页锚点、扫描件/不可提取、修订版 issue diff、三模式与 cutoff/revision 串用、数字/风险一致性和 DOCX/PDF/HTML 身份。
3. 独立审计设计：检查闭合性、可实现性、确定性验证器、格式感知 QA、临床/文档 QC、失败语义和分阶段实施 allowlist；不得自行宣布接受。

## 不可越过的边界

- 不启动 8911、5174、浏览器、OCR、模型、真实 provider 或长任务。
- 不读取或运行 MG-K10、Ruxolitinib、MY008、MY009 等真实项目。
- 不修改 `frontend/**`、`services/**`、`packages/**`、`runtime/**`、`deploy/**`、R1–R5 已接受代码/工件或任何 `medical-writing`/`medical_writing` 路径。
- 不做系统安全功能设计或测试；仅保留报告身份、来源、版本、coverage 与医学可追溯性所需的产品语义。
- 不建立待办/关闭工作流，不把 Query 发出、回复或人工确认当作本子系统职责。
- 原始报告不可覆盖；批注副本和清洁稿不得混淆原件；清洁稿必须显式 `DRAFT`。
- coverage 不完整、issue 未覆盖、cutoff/revision 不一致或证据冲突时，不得声称全报告审阅完成或可正式输出。

## 完成门

合同 prose、machine-readable contract 与 challenge matrix 三者字段、枚举、计数和错误语义一致；每个关键输出都有确定性验收器；三模式不能静默串用；至少一个后续独立会商在稳定字节上返回接受结论后，才可规划 R6 第一条 synthetic/offline runtime 纵切。
