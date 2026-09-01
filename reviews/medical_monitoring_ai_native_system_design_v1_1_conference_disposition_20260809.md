# 医学监查 AI 原生系统设计 v1.1 会商处置表

**日期**：2026-08-09  
**状态**：`READY_FOR_USER_APPROVAL`  
**会商结论**：主审对原 v1 给出 `VETO`；v1.1 已完成设计级修订，但尚未授权实施  
**冻结边界**：产品源码不改；8911 保持停止；不运行五个真实项目；旧 P10/B6/真实 LOOP 不恢复

## 1. 会商证据

- 独立参与者路由在 session 建立前终止：夜间 Pi/Alibaba `qwen3.8-max` 主路由与两条 DeepSeek V4 Flash 回退均未通过 provider/model 健康检查，未产生审阅观点。
- 隔离主审 `codex-subagent/codex/gpt-5.6-luna` 完成一次只读独立审查，无模型回退。
- 主审报告：`/Users/smkzw/Documents/AI Cache/Codex x Hermes/runs/conference/medical_monitoring_ai_native_design_v1_review_20260809/general_chair_pi_qwen38.md`。
- 参与者失败日志：`/Users/smkzw/Documents/AI Cache/Codex x Hermes/logs/conference/medical_monitoring_ai_native_design_v1_review_20260809/general_pi_deepseek_flash_stdout.txt`。
- 本轮没有读取或修改产品源码、8911 或五个真实项目。

因此，本轮有一个有效隔离审阅视角，不得表述成多模型一致意见。v1.1 的最终处置由 Codex 根据 D1-D39 与实际设计原文核验后作出。

## 2. 问题处置

| ID | 主审意见 | Codex 处置 | v1.1 落点 |
|---|---|---|---|
| BLOCK-01 | 分析完成、证据状态、医学处置和输出资格混为一体 | **部分接受、修正方案**。接受正交状态；拒绝恢复强制人工门或“人工复核未完成”。看板直接可见，高风险保留证据/审阅状态，用户确认只在实际动作后记录 | Design §5.1、§12 |
| BLOCK-02 | R8 零 P0-P4 不可复现 | **接受**。P0-P4 语义、任务覆盖、gold/negative/boundary/hidden cases、缺失输入和非问题证据在 R0 冻结 | Design §17.1；Plan R0、R8、§13.3 |
| HIGH-03 | Agent 与确定性服务、副作用边界不清 | **接受**。节点分为 deterministic_service、AI_candidate、human_decision、projection；LLM 不提升事实/基线/用户确认 | Design §5.2、§8.2 |
| HIGH-04 | 快照、mapping、数据基线接受权威不闭合 | **接受**。加入 SnapshotAcceptance 链、system_policy/本地 OS 用户接受主体、Run manifest 冻结项与歧义阻断 | Design §5、§6.2；Plan R2 |
| HIGH-05 | 风险 identity 与自动关闭不可执行 | **接受**。加入稳定风险键、merge/split、identity_ambiguous、superseded/not_evaluable/resolved_by_data | Design §10.1；Plan R1/R2 |
| HIGH-06 | AI Adapter 完整性、隔离和审计合同不足 | **接受但控制范围**。加入 CapabilityRegistry/AdapterContract；用户选择外部端点即执行选择，不增设企业级数据外发审批 | Design §9.1、§9.4；Plan R1 |
| HIGH-07 | Artifact 缺少 coverage/partial/truncated | **接受**。ArtifactEnvelope 和发布 QC 增加 expected/produced coverage 对账及完整性状态 | Design §5、§12；Plan R1 |
| HIGH-08 | 恢复和原子性验证过晚 | **接受**。原子提交、重复/迟到回调、崩溃点和损坏 artifact 故障注入前移 R1 | Design §12、§15.4；Plan R1/R2 |
| HIGH-09 | 风险域只有名称，没有可判定覆盖合同 | **接受**。每域 coverage matrix；R1 先完成 AE/MH 端到端纵切，再扩展其他域 | Design §10.4；Plan R1/R4 |
| HIGH-10 | 三模式无入口/冻结/修订状态机 | **接受**。加入不可静默转换的 ModeContract、cutoff/revision/carry-forward/输出资格 | Design §6.4；Plan R1/R2 |
| HIGH-11 | 外部报告无法证明全部主张已处理 | **接受**。加入 ClaimCoverageLedger、页/表/图/脚注/分母/cutoff 覆盖和批注锚点验证 | Design §13；Plan R1/R6 |
| MED-12 | 所有模型同时看到 reference baseline 会共同锚定 | **接受为验证项**。保留 D22 的默认基座可见，同时增加 baseline-free/hidden challenge 验收 | Design §17.1；Plan R3/R8 |
| MED-13 | Query“内部待办”与无强制队列冲突 | **接受**。统一为可检索、可筛选的 Query 草稿视图，不形成全局完成门 | Design §10.2 |

## 3. 三个边界问题的确定解释

1. `analysis_complete` 仅表示 manifest 范围的产物与 coverage/QC 完成、可以查看；不代表用户已确认医学结论。
2. 快照/mapping 接受主体可以是已批准的 `system_policy` 或当前本地 OS 用户。高置信度且确定性校验通过的 mapping 可自动接受；任何关键歧义阻断 baseline eligibility，并在对应页面显著显示，不生成强制任务队列。
3. adjudication 必须是独立 binding/session 和隔离上下文，worker 不得自审；底层模型可以相同，以保持单模型也能运行。无法建立独立 binding 时保留 `needs_user_attention`，不伪造一致度、不静默关闭。

以上均可由 D1、D23、D25、D32 和本地单用户/低干预目标推导，无需新增用户产品偏好决策。

## 4. v1.1 批准含义

如果用户批准 v1.1，仅表示：

- 允许进入 R1 的非真实/隔离 fixture POC；
- 允许验证状态、coverage、恢复、Adapter、AE/MH 纵切、三模式和报告 claim coverage；
- 允许在 POC 证据后选择 graph/persistence 框架。

批准不表示：

- 允许修改或迁移现有产品源码；
- 允许启动 8911 或运行五个真实项目；
- 认可任何框架、adapter 或医学能力已经通过；
- 接受商业化、法规认证、电子签名或多用户目标。

## 5. R1 进入门

用户批准后，R1 仍需先建立隔离工作目录、synthetic fixtures、可删除/回滚的存储和明确输出路径。R1 完成证据至少包括：

1. 正交状态与快照接受链可重放；
2. Artifact coverage、partial/truncated 与 publication gate 对账；
3. Adapter 正常/失败/截断/取消/恢复证据；
4. 崩溃、重复、迟到回调和 artifact 损坏下无假通过/重复副作用；
5. AE/MH 一个完整医学纵切及 Profile/Timeline/Query/中心聚合；
6. 三个 ModeContract 最小状态机；
7. 报告 ClaimCoverageLedger 与批注锚点；
8. 独立 reviewer 接受，并形成框架/存储 ADR。

任一基础合同失败都先缩小 POC 或回退设计，不进入真实项目。
