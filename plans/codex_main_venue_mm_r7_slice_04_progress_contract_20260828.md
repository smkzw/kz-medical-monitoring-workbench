# Codex Main-Venue Plan: mm_r7_slice_04_progress_contract_20260828

Date: 2026-08-28
Objective: 独立挑战并冻结 R7 Slice-04 持久化 Run 进度事实面合同，重点核查产品 Run 与 R1 manifest/work-unit ledger 的身份映射、显式创建与零写入边界、revision 幂等、中文受众投影和后续后台恢复可演进性；不得修改源码、启动服务、调用模型或运行真实项目。

## Task Decomposition

1. 各席独立核对合同与 R1/R7 现有实现，寻找身份、持久化、幂等、恢复演进和用户投影缺口。
2. 各席给出具体合同修订和验收矩阵，不修改源码。
3. Codex 比较独立发现，复核源代码事实，修订合同并运行文本/边界门禁。
4. 合同冻结后才初始化独立实现执行包；本会商不授权实现。

## Source Packet

- `context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`
- `context/medical_monitoring_r7_phase_review_and_slice04_plan_20260828.md`
- `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`
- R7 实施计划与系统设计进度章节
- R1 manifest/work-unit ledger/audience progress/background facade
- R7 product API/run entry/product router

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_04_progress_contract_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_04_progress_contract_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 由 runner 记录每席开始/结束、session、provider/model/effort、fallback、usage 与失败原因。
- 首轮后只在结论不完整或需核查修订时使用同一 session 定向续轮；不因耗时重开会话。

## Codex Verification Checklist

- 两席均未修改源码、未启动服务、未调用任务内模型或真实项目。
- 每项采纳/不采纳意见均与当前 R1/R7 代码事实交叉核对。
- 修订合同不存在第二套进度状态、隐式 GET 写入或内部标识前台暴露。
- 合同明确 Slice-04 与后台执行、模型、UI、受试者流向看板的边界。
- review-gate 与 metrics 通过后才声明合同冻结。
