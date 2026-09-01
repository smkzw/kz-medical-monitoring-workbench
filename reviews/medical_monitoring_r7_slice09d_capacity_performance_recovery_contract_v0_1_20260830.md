# R7 Slice-09D 性能、容量与长任务恢复合同 v0.1

日期：2026-08-30  
状态：`DRAFT_FOR_INDEPENDENT_REVIEW`

## 边界

仅在 synthetic/offline 下回答当前工作站、当前源码和固定 corpus 的可重复容量边界。禁止真实方案/IB/listing/报告/患者资料、真实模型、浏览器、8911/5174/8984、医学写作和安全专项。结果不是通用 SLO、R8 医学质量或 R7 总体接受。

## Corpus 与 workload

| Tier | events | indicators | risk anchors |
|---|---:|---:|---:|
| T0 | 100 | 4 | 30 |
| T1 | 1,000 | 40 | 300 |
| T2 | 10,000 | 400 | 3,000 |
| T3 | 50,000 | 2,000 | 15,000 |
| T4 | 100,000 | 4,000 | 30,000 |

主梯度 `balanced`；T1/T3 增加 `wide/deep/sparse/high_entropy` 与 1/4/16 项目 fanout。T4 仅在 T3 完整通过后执行，首次边界后只做相邻二分探针。manifest 固定 generator/version/hash/seed、tier/shape/counts、逻辑与物理字节及 input-side oracle digest。生成器只使用 opaque identity，不得包含疾病、药物、量表、风险、列名或布局分支。

独立 workload：首次备份、同值备份、首次恢复、同值恢复、公开读取、重开/恢复就绪、进度观察。首次完整运行不得与 already-current 混合。每次记录 wall/cpu、peak RSS、输入/输出/staging/package、对象数、first-progress、max-progress-gap、terminal latency、原始样本与环境 manifest；成功必须同时通过身份、闭包、digest、无半发布、失败不覆盖已有项目和终态一致。

`process-cold` 使用新 subprocess/connection/staging 并标记 `os_cache_control=unknown`；`process-warm` 预热一次但使用新 target/staging。每格先 7 次 screening；T1、最大通过、首个硬失败及相邻边界做 30 次确认（3 seeds×10）。保留所有失败和离群点。

## 判定与恢复

`observed_green`=正确性全过且不越实验预算；`observed_yellow`=正确但资源预警，停止扩容并做边界确认；`observed_red`=身份/digest/闭包错误、半发布、覆盖/串扰、OOM/ENOSPC/崩溃/死锁/watchdog、进度或终态不可达，立即停止更高 tier；环境不可比为 `inconclusive`。正确性优先于速度，容量只按环境+commit+corpus 表述。

故障矩阵至少覆盖：claim/begin/attempt 中断、cancel、lease/heartbeat 过期、新旧 generation、迟到回调、依赖失败、backup publish、restore/migration 两次切换、live-verifying、rollback failure、audit append/head CAS、日志 lock/ENOSPC/fsync/rotation、低磁盘/watchdog。每格固定前态、注入点、中间态、唯一恢复入口、中文投影、禁止动作、独立 oracle、最大等待与证据保留。同步 harness transport 不可取消时只能显示“分析已中断，可继续”，不得宣称立即取消。

## 反过拟合与 harness 责任

09D 不接触真实来源；R8 须另行 source-admission，记录只读隔离副本大小、SHA-256 和前后完整性。公共内核/prompt/schema/validator/oracle/fixture/routing/metrics 不得按项目/文件/路径、疾病/药物/量表/风险、listing 列名/表名/坐标/布局、fixture ID 或 mutation label 分支。

listing 解构和药物/疾病提取必须由独立 harness/LLM 产出 candidate envelope，绑定 capability/binding、input/prompt/schema digest、隔离上下文、状态、coverage、source anchors、uncertainty 与 raw-output hash；不得自动 fallback。确定性层只校验结构、身份、锚点、coverage、canonical hash 与状态机，不得从文件名、术语或内置字典补全医学语义。不可用、部分、截断、超时、未知实体或来源冲突均 fail-closed。

expected 只能来自 input-side frozen facts/manifest 或独立 gold，不得读取产品 DTO、模型输出、自报 coverage/digest 或被测数据库。harness 不得看到 gold/case/mutation label。挑战至少覆盖随机化名称、未见实体、列名重排、wide/long/merged/repeated-header/hidden/decoy、同义/否定/Unicode、缺失/冲突、harness unavailable/swap、malformed/multiple-object/extra-key、wrong digest 与 hash-seed/normal/-O/-OO。专有常量、gold 泄漏或自动 fallback 至少 P1。

## 完成门

合同会商 P0-P4 清零；实现前冻结 generator/oracle/measurement/fault matrix；实现后通过聚焦、15 格确定性、资源恢复矩阵、R1/R7 相邻回归和三端口停止检查。只有 09A–09D 均独立接受后才复核 Slice-09/R7；R8 另行准入。
