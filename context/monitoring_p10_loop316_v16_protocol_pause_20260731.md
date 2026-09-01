# P10 LOOP 3.16 V16 / RUX 方案证据细分任务无损暂停

时间：2026-07-31 16:16 CST  
Goal：保持 active；本文件仅记录用户要求的阶段性无损暂停，不代表 P10 完成。

## 1. 本次细分任务范围

本次只完成并收口以下工作：

1. MG-K10 V16 四项科学边界后的 RUX V16 串行扩展；
2. RUX V16 早期候选审计暴露的 MedDRA 词典支持字段归一缺口；
3. RUX V1.3 方案证据包当前合同 7 个失败主题的正式重试；
4. 方案 absence claim 质量门的否定语境误判纠偏；
5. 聚焦、相邻和全医学监查回归；
6. 停服、运行库一致备份和精确恢复锚点。

未启动 MY009 V16，未启动前端，未 adopt/assemble/confirm/activate mapping，未接受或
驳回方案候选，未创建 daily run，未修改医学写作业务。

## 2. 已完成的代码纠偏

### 2.1 MedDRA 词典支持字段

RUX V16 前 14 个完成块的只读审计发现 `MDRAVER` 已被独立 AI 明确识别为
`meddra_dictionary_version`，但字段性质仍为 `source_collected`；与同一 MedDRA 链的
标准 term/code 形成 `XJOB-CODING-CHAIN-DRIFT`。

现行处理：

- 闭合角色目录补充 `meddra_language` 别名；
- draft assembly 仅对独立 AI 已明确声明的 MedDRA/药品词典版本或语言角色，确定性归一
  为 `source_metadata`；
- 不根据字段名、值或域自行推断编码体系；
- 不改写不可变 AI 候选；原候选字段性质保留在候选审计中；
- 添加 `coding_support_metadata_closed` 动作，正式编码血缘仍必须通过来源 term/code、
  独立版本字段和既有 MedDRA 跨 chunk anchor 门；
- 候选审计将该状态报告为
  `XJOB-CODING-SUPPORT-METADATA-NORMALIZATION` warning，不再把可审计的确定性
  assembly 归一误报为候选链全局错误。

同一 14 块审计由 1 error / 6 warnings / 1 observation 收敛为
0 errors / 3 warnings / 1 observation；剩余 warning 分别为 MedDRA 来源术语跨块锚点
和两个词典支持字段待 assembly 归一。

### 2.2 方案 absence claim 否定语境

RUX 7 个主题的第 3 次尝试均被
`bounded protocol evidence may only report a retrieval gap` 拒绝。尝试审计证明模型写的
是“不能断言方案未规定”“该缺口不代表方案未规定”等明确否定句，旧正则只匹配内部
“方案未规定”而产生假阳性。

现行处理：

- 直接的“方案/研究方案未规定、未提供、未说明、缺少、不存在”继续失败关闭；
- 只放行同一分句内明确的否定前缀，如“不能/不得/无法断言”“不代表”
  “不能据此推断”；
- 表格同行、表头、列表标题/条目、冲突保留、CM/IP 等既有 v2 门保持原样。

首次实现把 helper 插入到函数中段，聚焦测试立即复现表格同行门未执行；已将 helper
移到完整协议候选校验之外并恢复两项结构校验调用。运行中的 8911 当时仍是旧代码，
没有受到该中间状态影响。修订后正反例与完整协议准备回归全部通过。

## 3. RUX 方案证据包终态

项目：`proj_rux_03_002`  
方案版本：`protov_21c4b5a4a3883a8119d74e18`（V1.3）  
当前结果：2 `candidate_review`、6 `failed`、0 running/queued。

| 主题 | 终态 | attempt | 候选 | 失败关闭原因 |
|---|---|---:|---:|---|
| eligibility_continuity | candidate_review | 4 | 5 proposed | — |
| visit_window_and_order | failed | 4 | 0 | 未同时绑定表格同行条件与动作 |
| study_treatment | failed | 4 | 0 | 未同时绑定列表标题与条目 |
| concomitant_medication_policy | candidate_review | 2 | 5 proposed | — |
| safety_assessment | failed | 4 | 0 | 单候选 evidence IDs 60，超过 50 上限 |
| efficacy_assessment | failed | 4 | 0 | 未引用可用表头 |
| early_withdrawal_and_deviation | failed | 4 | 0 | 未同时绑定列表标题与条目 |
| data_quality | failed | 4 | 0 | 未引用可用表头 |

这证明 absence 否定语境假阳性已消除；余下 6 项均为真实结构证据/输出压缩门失败。
不得通过放宽表格、列表或 evidence 上限来静默接受。10 个当前候选全部为 `proposed`，
未作用户决定；后续必须先只读复审 eligibility 的 estimand/入排边界和 CM 的禁用清单/
洗脱期/试验药物边界。

## 4. RUX V16 mapping 暂停点

项目：`proj_rux_03_002`  
批次：`monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb`  
profile：
`bc23dca0f1b85107110d0c1bbb7264014813751e01b26e2ca1db889c472e02ab`  
input：
`c856b63631897df44819391a5aee0eba2f50b64d603c707d15e3a0fac42a1f0b`  
字段/作业：1,805 / 175。

停服前正式状态：

- completed：45；
- running：8；
- queued：122；
- failed/blocked：0；
- 当前 V16 mapping 候选：45，全部 proposed；
- draft：空；
- semantic-quality persistence：空；
- active mapping：空。

8 个 `running` 是优雅停服时数据库中仍持有 lease 的持久作业；8911 停止后不存在真实
worker 或外部调用。lease 范围为
`2026-07-31T08:19:57.829143Z` 至 `2026-07-31T08:20:20.858674Z`。
下一次启动已晚于该时间，启动恢复会按既有 lease expiry/CAS 路径回收；不得直接改库，
也不得重新 POST 整批 mapping。

## 5. 验证

- coding-support 聚焦：145 passed；
- mapping AI/service、draft、语义门、激活、cutover、批次生命周期、审计：
  306 passed；
- protocol v2 正反例：9 passed；
- AI service + protocol preparation：164 passed；
- 全医学监查：`1129 passed, 4288 deselected, 27 warnings, 0 failed`
  （612.06 秒）；
- 修改模块 `py_compile`：通过。

27 个 warning 为既有 SWIG、FastAPI `on_event`、openpyxl header/style 提示；没有新增
测试失败。当前环境仍无 Ruff，不声称 Ruff 通过。

## 6. 修改文件与暂停哈希

| 文件 | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_service.py` | `8b3c34bac60a3672af2f7f0d8fcb67774124d70ed64d39a7ead6355f2df9641a` |
| `services/api/app/monitoring_mapping_semantic_quality.py` | `685dc32166ded1fbfbe7d146d6945c87414fa15193bcca1c71959bcef7d4cea9` |
| `services/api/app/monitoring_mapping_draft_repository.py` | `494dac108b70a387d79ae39dbe1b8f29f536f5c3e22e02c36127c396b18e1f92` |
| `scripts/monitoring_mapping_candidate_audit.py` | `dab6815f564605f9f95d6b4f89a17d375d058ad4154cb6c3ca11fb5d564940b0` |
| `tests/test_monitoring_ai_service.py` | `7a9adb667ba4c11a4903c69ffe8ec6032303c0852d74610e7d8103999d2203a3` |
| `tests/test_monitoring_mapping_draft_repository.py` | `aa98844807703efe8cd58984375d51a05d2bb7a0042542ffc3f6422b34642567` |
| `tests/test_monitoring_mapping_candidate_audit.py` | `f5b68169d2f490a826f3e7539acccdb5b31280b0cef8ea796670a80791021bdc` |

## 7. 停机与备份证据

- 8911 listeners：0；
- 5174 listeners：0；
- 无 `uvicorn.*8911`、`start_stable_backend` 或监查 pytest 进程；
- 停机一致备份：
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pause_loop316_20260731_1615CST/`；
- runtime 根目录 21 个 SQLite 均有对应备份；
- 18 个非空备份 `PRAGMA integrity_check=ok`；
- 3 个空库按零字节保留；
- 备份 `medical_monitoring_ai.sqlite3` SHA-256：
  `1a1742d1b2f8faed7c404de3ab63ebc3a74d1e5757b8dd082f4545567b1d6781`。

## 8. 下一次唯一安全恢复动作

1. 先读取本文件、`TASK_CONTEXT.md`、`LOOP_LEDGER.md` 和
   `context/monitoring_p10_loop316_runtime_v15_20260731.md`。
2. 核对上述 7 个修改文件哈希及 8911/5174 仍无监听；并行医学写作的合法变化不得回滚。
3. 仅运行 `scripts/start_stable_backend.zsh` 恢复唯一 8911，核验
   `/api/runtime-readiness` 和产品独立 AI；
4. 不再 POST RUX mapping；只 GET 同一批次 `field-mapping-status`，确认 8 个过期 lease
   被正式启动恢复并继续 122 个 queued；
5. 不自动重试 6 个方案失败主题。先设计并验证结构证据聚焦/输出压缩纠偏，再决定是否
   用原 job 做下一次受控 retry；不得放宽 v2 医学门；
6. 先只读复审 10 个 proposed 方案候选，不作医学决定；
7. RUX 175 个 V16 作业全部终态后，生成正式
   `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.{json,md}`，
   完成 CM/IP、量表、编码、日期与治疗身份断言；
8. RUX 通过前不得启动 MY009 V16。

