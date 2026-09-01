# R6 外部报告审阅与三模式输出合同 v0.1 验收记录

日期：2026-08-27

内容裁决：`ACCEPT_R6_CONTRACT_V0_1_FOR_SYNTHETIC_OFFLINE_PLANNING`

治理状态：`CONFERENCE_VALIDATOR_POLICY_GAP_RECORDED`。合同内容和独立席意见已闭合，
但当前 guard 的 `validate-conference` 同时要求 live route 未生成的 Cursor 标记；不以
手工补词或伪造席位制造通过。该治理工具不一致不解除既有 R5-S7 runtime 阻断。

## 接受对象

以下三个候选工件由本记录在其稳定字节上接受；工件内部保留
`candidate_for_independent_acceptance`，用于区分“候选内容”与外部验收记录，
不再通过回写状态破坏已审阅内容身份。

| 工件 | SHA-256 |
|---|---|
| `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` | `1c6fc588335206020389527bf0841bbf57abe227dbea46a2420c0456ed2f1acd` |
| `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json` | `0fca738c19277777de25ce819285ace2e836b2e323e581ce04f52608ce0ed1d7` |
| `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json` | `cb5b30bc8397e022efff6bc7e57b4d23b99f1debff1c405879e42e698444b2dc` |

## 验收依据

1. governed execution 的三个独立工作项均完成，`audit-execution` 通过；worker 分别覆盖合同架构、86 行单变异挑战矩阵和独立可实现性/确定性审计。
2. Gemini 3.7 Flash 独立席在同一 session 复核后建议接受。
3. Grok Build 4.6 独立席在同一 session 连续三轮挑战；其最终四项补丁中 MUST 1–3 已全部落地，MUST 4 明确规定补丁落地后撤回语义冻结异议，余项不阻断。
4. Codex 对最终字节执行确定性对账：86 个唯一挑战用例，12 个分类计数、P0/P1/P2 严重度计数、49 个实际诊断码与逐码映射、11 个验证器、16 项禁止边界全部闭合；reverse expected surface 与 comparison links 已分离，遗漏反向检测、稳定身份、三件套、三模式和正式输出门均可实现。
5. `contract.json` 与挑战矩阵的 `schema_version` 属于不同版本平面，已在 prose 中显式说明，并共同绑定 `contract_id + contract_version=0.1`。
6. `audit-execution` 与两个 review-gate 作为确定性治理证据执行；conference validator
   的 Cursor/live-route 不一致单独记录，未被隐瞒或解释为通过。

## 已关闭的关键问题

- 冻结的 `ExpectedReviewSurfaceEntry` 不再混入比较结果；新增有类型的
  `ReverseCoverageLink` 和 `expected_review_surface_hash`。
- 反向遗漏空映射统一为 `reverse_omission_uncovered`，进入完整审阅/正式输出阻断；
  R6C-006 使用 `block`，保留受限工件而不丢失问题。
- claim/unit 多对多、IssueTransition、来源版本与报告版本、稳定 issue/claim identity、
  原件/批注/可选 DRAFT 三件套、raw/display 数值政策和三模式隔离均已闭合。
- 49 个场景诊断码均映射到唯一验证器、canonical failure code 和 blocking 布尔值。

## 边界与未关闭事项

- 本裁决只允许规划和实现隔离的 synthetic/offline R6 第一纵切；不等于 R6 runtime、产品、真实项目、外部报告实例、DOCX/PDF/HTML 渲染、医学结论或用户确认已接受。
- R5-S7 的 Codex 26 行 identity/network/7 次冷暖性能测量包已于 2026-08-27 闭合并通过；CodeBuddy/HY3 原会话最终重放仍未闭合。按既有阶段边界，在该单一门关闭前不得启动 R6 runtime。
- 8911 与 5174 必须保持停止；不得读取/运行五个真实项目，不得修改医学写作子系统。

## 下一安全动作

先回到 R5-S7：在原 HY3 session 可用时完成最终重放并由 Codex 复核原始结果，
随后关闭 S7。再按本合同先实现 fixture catalog、stdlib 确定性验证器与 86 行
metadata oracle 执行器，进入 R6 synthetic/offline runtime；不先接产品或真实报告。
