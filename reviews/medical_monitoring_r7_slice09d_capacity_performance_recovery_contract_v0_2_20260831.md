# R7 Slice-09D 性能、容量与长任务恢复合同 v0.2

日期：2026-08-31  
状态：`FROZEN_ACCEPTED_R7_SLICE_09D_CONTRACT_V0_2`  
替代：v0.1

## 1. 目的、边界与严重度

本合同仅在 synthetic/offline 下建立当前工作站、当前源码和冻结 corpus 的可重复容量与恢复边界。禁止真实方案、IB、listing、报告、患者资料、真实模型、浏览器、8911/5174/8984、医学写作和安全专项。结果不是通用 SLO、R8 医学质量或 R7 总体接受。

P0=越界读取/写入、跨项目污染、覆盖可用项目或合同不可执行；P1=关键正确性、恢复、反过拟合或证据门缺失；P2=核心测量/用户任务实质不完整；P3=明显影响解释或操作效率；P4=轻微一致性/表述缺陷。冻结要求 P0-P4 全零。

## 2. Corpus profile 与固定测量网格

基础 tier：T0=`100/4/30`、T1=`1,000/40/300`、T2=`10,000/400/3,000`、T3=`50,000/2,000/15,000`、T4=`100,000/4,000/30,000`（events/indicators/risk anchors）。同一 seed 下，高 tier 必须包含低 tier 的全部稳定身份和关系，再追加记录，保证纵向可比。

固定 profile 共 15 个：

| ID | Tier | Shape | Projects | 用途 |
|---|---|---|---:|---|
| C01-C05 | T0-T4 | balanced | 1 | 主容量梯度；C05 仅在 C04 全绿后运行 |
| C06-C09 | T1 | wide/deep/sparse/high_entropy | 1 | 小规模结构敏感性 |
| C10-C13 | T3 | wide/deep/sparse/high_entropy | 1 | 大规模结构敏感性 |
| C14-C15 | T1/T3 | balanced | 16/4 | 根级多项目 fanout |

不做 shape×fanout 笛卡尔积。每个 profile 形成一个“基准包”，顺序执行七个独立 workload：首次备份、同值备份、首次恢复、同值恢复、公开读取、重开/恢复就绪、进度观察；每个 workload 单独计时和判定。每个基准包分别以 process-cold、process-warm 执行，因此主网格为 15 profiles×2 modes=30 cells。15 格确定性矩阵是另一独立门：固定 C01/C02 小 corpus，5 个 `PYTHONHASHSEED`×`normal/-O/-OO`，不与容量网格混称。

manifest 固定 generator/version/content hash/seed、profile、tier/shape/project count、对象计数、logical/database/artifact/member/package bytes、源码 commit/dirty-tree、环境 hash 和 input-side oracle digest。generator 只使用 opaque identity，不得包含疾病、药物、量表、风险、列名或布局分支。

## 3. 运行、采样、预算与统计

fixture 在计时外生成并只读复用。每个 bundle-run 使用一个独立进程：process-cold=新 subprocess/connection/staging 且不预热，明确 `os_cache_control=unknown`；process-warm=同一 bundle-run 进程预热一次后测量，但首次备份/恢复仍使用新 target/staging，不能以 already-current 冒充 warm full operation。cold/warm 交替运行，profile 顺序由冻结 seed 随机化。

所有 30 cells 先做 7 次 screening。只有 C02（T1 基线）、最大全绿 balanced profile、首个非全绿 balanced profile和至多两个相邻二分 profile做 30 次确认（3 seeds×10）；每方向二分最多 6 个 profile。T0 screening 后生成 balanced 单项目保护 watchdog：`min(3600s, max(300s, T0_p95 × tier_event_ratio × 3))`。非 balanced 或 fanout profile 按 workload 分别先做一次不计入统计但完整保留的 calibration trial，初始 guard 为 3600 秒；该 workload 其余 trial 的 watchdog 为 `min(3600s, max(balanced_watchdog, calibration_wall_time × 3))`，不得用重标定改写原 calibration 结果。任一 calibration 出现正确性失败、超时或停滞，即该 profile/cell 为 red，保留样本并停止其余 trial 和更高 tier，不再计算新 watchdog。单 cell 不超过其 watchdog×7/30；整个 09D 容量运行硬上限 24 小时，达到上限即保留证据并标为 `inconclusive_budget_exhausted`，不得删样本或宣称通过。

资源保护阈值不是 SLO：RSS 持续 60 秒达到物理内存 70% 为 yellow、85% 为 red；可用磁盘低于 `max(20 GiB, 总容量15%)` 为 yellow，低于 `max(10 GiB, 总容量8%)` 或预测下一 staging 超过当前可用空间 50% 为 red。环境可比需 commit/corpus/Python/SQLite/架构/物理内存一致，dirty-tree=false；OS patch、可用磁盘和后台负载变化记录但不自动合并，不满足则 `inconclusive_environment_drift`。

每 trial 记录 wall/cpu、peak RSS、输入/输出/staging/package/最大成员、对象数、first-progress、max-progress-gap、terminal latency、终态、watchdog、全部原始样本与环境 manifest。`max-progress-gap > 当前 workload watchdog` 即进度停滞 red。确定性正确性任何一次失败，该 cell 立即 red 并停止更高 tier；时序/资源按 seed 分层报告 raw、p50、nearest-rank p95、IQR，不隐藏异常值。基础设施瞬态失败只允许一次“调查性重跑”，原失败仍保留且最终裁决不得用重跑覆盖。

容量边界仅表述为：最后一个全部 correctness 通过的 balanced profile、相邻非通过 profile、环境/commit/corpus 和完整资源区间；不能写成“系统支持 X”。

## 4. 判定与停止

- `observed_green`：identity/closure/digest/原子性/终态全部通过，且未触发 yellow/red。
- `observed_yellow`：正确性通过但触发 yellow；停止自动升级，进入边界确认。
- `observed_red`：正确性失败、半发布、覆盖/串扰、OOM/ENOSPC/崩溃/死锁/watchdog、进度终态不可达或 red 资源阈值；立即终止当前 cell 剩余运行及所有更高 tier。
- `inconclusive_*`：预算、环境或无法归因的基础设施问题；不得计入 green 或容量声明。

每个 workload 先独立判定；任一 workload red 则整个 cell red，零 red 但任一 workload yellow 则 cell yellow，全部 workload green 才可判 cell green。

## 5. 长任务、取消与恢复矩阵

冻结矩阵至少覆盖 claim/begin/attempt 中断、异步 cancel、同步 transport 不可取消、lease/heartbeat 过期、新旧 generation、迟到回调、依赖失败、backup publish 前后、restore/migration 两次切换、live-verifying、rollback failure、audit append/head CAS、日志 lock/ENOSPC/fsync/rotation、低磁盘/watchdog。每格固定持久前态、注入点、允许中间态、唯一恢复入口、用户投影、禁止动作、独立 oracle、等待上限与证据保留。

cancel 后不得领取下一 unit；提交临界区允许完成原子动作但必须显示“正在安全停止”。同步 harness transport 不可取消时显示“分析已中断，可继续”，不得宣称立即取消。启动扫描是 best-effort；业务恢复必须走同 key 显式继续。旧 generation/迟到 callback 不得改变状态或进度。

## 6. 中文用户投影

| 内部状态 | 中文展示 | 下一动作 |
|---|---|---|
| running | 正在处理本次医学监查 | 可离开页面，后台继续 |
| stopping | 正在安全停止 | 稍后查看 |
| interrupted_resumable | 本次监查已中断，进度已保留 | 继续本次监查 |
| partial/not_evaluable | 资料不足或存在歧义，暂不能完成 | 查看缺失或冲突来源 |
| yellow | 当前数据量较大，处理速度可能变慢 | 可继续等待 |
| red_resource | 当前设备资源不足，已安全停止 | 释放空间后继续 |
| red_correctness | 本次结果无法确认，已安全停止 | 重新核对项目 |
| inconclusive_budget/environment | 本次处理因时间或运行环境变化未完成，结果不可用 | 稍后重新运行 |
| fail_closed | 暂无法完成本次解析 | 检查来源完整性后重试 |
| recovery_required | 项目需要重新核对 | 重新恢复 |
| anomaly | 项目记录存在异常 | 保留项目并查看说明 |
| complete | 本次处理已完成 | 查看结果 |

不得显示 provider/model/session/prompt/path/hash/表名、内部错误码、堆栈或技术日志标签。所有映射纳入 DTO/投影测试。

## 7. 反过拟合、coverage 与独立责任

09D 不接触真实来源。R8 source-admission 是证据准入而非权限/安全系统：另行记录来源身份、版本/日期、隔离副本路径、大小、SHA-256、用途、使用前后复 hash 和撤销状态；不得作训练、prompt tuning、schema default、lookup dictionary、benchmark 或 SLO 校准。用户既有授权不被重复解释为审批流程。

公共内核/prompt/schema/validator/oracle/fixture/routing/metrics 不得按项目/文件/路径、疾病/药物/量表/风险、listing 列名/表名/坐标/布局、fixture ID 或 mutation label 分支。以可复跑静态扫描和 mutation 测试验证：随机化名称、重排列名/布局后，确定性层的结构/身份结果不应依赖专有字面量。

listing 解构和药物/疾病提取由独立 harness/LLM 产出 candidate envelope，绑定 capability/binding、input/prompt/schema digest、隔离上下文、状态、source anchors、uncertainty、raw-output hash 和自报 coverage。确定性层必须依据 source anchors 与冻结 source manifest 重新计算 coverage；自报 coverage 仅作对照，不得作为 expected。不可用、部分、截断、超时、相对开发 corpus 未见实体或来源冲突均 fail-closed，不自动 fallback。

expected 只能来自 input-side frozen facts/manifest 或独立 gold，不读取产品 DTO、模型输出、自报 digest/coverage 或被测数据库。generator 作者、oracle/gold 作者和最终冻结 reviewer 必须是三个明确角色；同一人不得同时编写被测实现与最终 oracle。harness 不得看到 gold/case/mutation label。

## 8. 交付物与条款门

交付物：冻结 corpus manifest+SHA、generator/oracle/fault matrix、每 trial JSONL、环境 manifest、统计 summary、容量边界报告、中文 DTO 结果、静态扫描/mutation 报告、15 格确定性记录、相邻回归记录、三端口证据和总 manifest。全部写入隔离 `artifacts/mm_r7_slice09d_*`，不写真实项目目录。

| 合同条款 | 决定性检查 | 完成标准 |
|---|---|---|
| §2 | profile/manifest/oracle tests | 15 profiles 身份与嵌套闭合 |
| §3-4 | 30-cell screening + 指定确认格 | raw 样本齐全，裁决可重算 |
| §5 | fault/recovery matrix | 每格持久前态、注入点、中间态、唯一恢复、用户投影、禁止动作、独立 oracle、等待上限与证据保留全部闭合，JSONL 证据齐全 |
| §6 | DTO projection tests | §6 全表状态逐行通过，无内部标识 |
| §7 | static scan + mutation + harness swap | 无专有分支、无内置补全/自动 fallback |
| 确定性 | 5 seeds×3 optimization | 15/15 canonical bytes/digests 一致 |
| 相邻 | 固定 R1 与全 R7 suites | 零失败；具体命令/计数写入接受记录 |
| 边界 | `lsof` 8911/5174/8984 + source hashes | 三端口无监听、真实来源未读、医学写作未改 |

v0.2 独立会商 P0-P4 清零后才能冻结。实现阶段不得把 test count 替代上述逐条证据。09A、09B、09C 的权威接受记录分别为 `context/medical_monitoring_r7_slice09a_implementation_acceptance_record_20260830.md`、`context/medical_monitoring_r7_slice09b_implementation_acceptance_record_20260830.md`、`context/medical_monitoring_r7_slice09c_implementation_acceptance_record_20260830.md`；09D 接受后才启动 Slice-09/R7 总体复核，R8 另行 source-admission。
