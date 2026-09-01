# P10 LOOP 3.16 / RUX 协议结构聚焦细分任务无损暂停检查点

时间：2026-07-31 CST  
Goal：保持 active；本文件只记录细分任务暂停边界，不代表 P10 或 RUX 科学验收完成。

## 1. 本轮完成

1. 恢复唯一 8911 稳定 API；5174 始终停止。
2. RUX V16 mapping 从旧暂停点继续到持久终态：
   `173 completed / 2 failed`，未重复 POST mapping，未形成 draft/active mapping。
3. 为协议结构化新增 provider-only 聚焦视图：
   - 冻结输入、source revision、business key 和持久 evidence packet 不变；
   - 表格同行/表头和列表标题/条目按结构闭合；
   - 冲突证据强制保留；
   - 每候选结构化 evidence ID 上限显式为 50；
   - repair envelope 复用聚焦视图，减少重复输入。
4. 独立高风险会商发现 item-only 命中时可能丢失前置列表标题；Codex 已修复为同节内
   最多向后回看 12 段，并增加 expander→focus 闭合回归。
5. provider-visible 协议提示合同从 v3 升为 v4；仅在业务键和 source revision 不变时，
   v3 终态仍可被状态接口兼容投影。旧候选不删除、不接受、不恢复为当前候选。
6. 聚焦最终 `189 passed`；结构修复后的全医学监查
   `1144 passed, 4291 deselected, 27 warnings, 0 failed`。

## 2. 真实 RUX v4 协议执行边界

项目：`proj_rux_03_002`  
方案版本：`protov_21c4b5a4a3883a8119d74e18`

一次批量 start 返回 202 后，状态接口明确显示 7 个新 v4 job 已创建，而
`data_quality` 仍为 `ready` 且没有 job。没有重发整批；只对这个已证实未变更的主题
补做一次定向 start，返回：

- job：`monai_a4d7b64b79dfe261fb165b270c2a`
- source revision：`mpr_410c66f6d9cebb83f5cfadc6e326`
- 初始状态：running / attempt 1

其余 7 个 job：

| Topic | Job |
|---|---|
| eligibility_continuity | `monai_e847991f1943e2e6c2c14d1c80c1` |
| visit_window_and_order | `monai_e963986fbc88d53a1dd77f56c829` |
| study_treatment | `monai_df9856664e7dd77163c8bcf6d246` |
| concomitant_medication_policy | `monai_33f533ed3d93fcffb8be848e8d9b` |
| safety_assessment | `monai_16f6004c23df2398c9b8a9e9d3c5` |
| efficacy_assessment | `monai_b9f2baa24baca94744523799e64c` |
| early_withdrawal_and_deviation | `monai_f8324e50ea946220f80e772cbdd5` |

一次 10 分钟硬等待后的最后紧凑 GET：

| Topic | 暂停前状态 | 候选 | 失败信息 |
|---|---|---:|---|
| eligibility_continuity | failed | 0 | available table header 未绑定 |
| visit_window_and_order | running | 0 | attempt 1，未返回终态 |
| study_treatment | failed | 0 | list title and entries 未同时绑定 |
| concomitant_medication_policy | failed | 0 | list title and entries 未同时绑定 |
| safety_assessment | failed | 0 | available table header 未绑定 |
| efficacy_assessment | failed | 0 | available table header 未绑定 |
| early_withdrawal_and_deviation | candidate_review | 5 proposed | — |
| data_quality | candidate_review | 3 proposed | — |

总计：`1 running / 2 candidate_review / 5 failed`，8 个新候选全部
`proposed/pending_user_confirmation`。本轮没有接受/驳回任何候选，没有将旧 v3 的
10 个 proposed 候选视为当前医学事实。五项失败均在一次 controlled repair 后由现有
表头/列表绑定门失败关闭；不得通过重试或放宽门掩盖。

## 3. 不得误报

- 原父 Session JSONL 已删除，本任务是证据重建后的替代续作，不是原始逐条对话恢复。
- RUX mapping 的 2 个 failed 尚未做正式候选审计；`173/175` 不是 mapping 科学通过。
- 协议 v4 job 创建成功不等于候选科学通过。
- 旧 v3 10 个 proposed 候选保留审计，但当前 source revision 已变化，不得自动迁移、
  决定或激活。
- MY009 V16 未启动。

## 4. 当前运行边界

- 8911：已优雅停止，listener=0。`visit_window_and_order` 以持久 running/lease 状态
  保留，下一次只允许既有 lease-expiry/CAS 恢复。
- 5174：listener=0。
- 不启动第二个后端、不启动前端、不运行 pytest、不启动执行/会商/子代理。
- 不修改医学写作业务文件。

停服一致备份：
`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pause_loop316_protocol_focus_20260731_2325CST/`

- runtime SQLite：21 个；
- 非空库：18 个，全部 `PRAGMA integrity_check=ok`；
- 空库：3 个，按字节保留；
- `medical_monitoring_ai.sqlite3` SHA-256：
  `bcc956c902b32ea916e9f2933901392b8e6313c5920f38acae2b09884bca4bdf`。

## 5. 恢复后的唯一安全顺序

1. 先读本文件、`context/monitoring_p10_loop316_v16_protocol_pause_20260731.md`、
   `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`。
2. 核对 8911 只有一个 listener、5174 为 0；如 8911 已停止，只能通过
   `scripts/start_stable_backend.zsh` 恢复一个实例。
3. 启动后只 GET 八项协议状态，不重复 start；让
   `visit_window_and_order` 通过既有 lease-expiry/CAS 恢复。记录其终态，不重试五项
   failed，不自动作 8 个新 proposed 候选的决定。
4. 对 RUX mapping 的 173 completed / 2 failed 运行正式只读候选审计，生成
   `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.{json,md}`，
   解释两项失败；不重发整批、不 adopt/assemble/confirm/activate。
5. 只有 RUX mapping 与协议科学审计均通过后，才决定是否串行启动 MY009 V16。

## 6. 审查与证据

- 执行 review：
  `reviews/codex_monitoring_p10_loop316_protocol_focus_20260731_review.md`
- 会商 review：
  `reviews/codex_conference_monitoring_p10_loop316_protocol_focus_review_20260731_review.md`
- 执行 metrics：
  `metrics/monitoring_p10_loop316_protocol_focus_20260731_metrics.md`
- 会商 metrics：
  `metrics/monitoring_p10_loop316_protocol_focus_review_20260731_conference_metrics.md`
- 会商主席：
  `runs/conference/monitoring_p10_loop316_protocol_focus_review_20260731/general_chair_pi_qwen38.md`
