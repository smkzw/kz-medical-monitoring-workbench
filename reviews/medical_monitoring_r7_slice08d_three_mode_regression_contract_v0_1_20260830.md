# R7 Slice-08D 三模式综合回归合同 v0.1

日期：2026-08-30  
状态：`DRAFT_FOR_INDEPENDENT_REVIEW`

## 1. 目标

在不新增产品功能和页面的前提下，用 synthetic/offline 证据证明 Slice-08A/08B/08C 的同一套跨轮连续性事实在日常、锁库前、核查前三种模式下保持一致、可恢复、可重放、可对账，并关闭进入 Slice-08 总体复盘前的综合回归缺口。

## 2. 冻结来源

- `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice08a_continuity_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice08b_authority_artifact_bridge_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice08c4_visual_acceptance_record_20260830.md`
- 当前 `poc/medical_monitoring_ai_native_r7` 与 `services/api/app/medical_monitoring_r7_product_router.py`

08D 只验证上述冻结语义，不引入第二套风险生命周期、结果发布器、continuity store、前端投影或模型选择逻辑。

## 3. 用户可感知的不变量

1. 日常监查可以 full 或 incremental；incremental 只能选择同项目、同模式、已发布且兼容的基线。没有合格基线时不得伪装增量。
2. 锁库前监查只允许 full。只有明确的 Query 关联证据完整时，才显示“Query 后修订影响”；否则显示“本轮数据修订变化”。
3. 核查前监查强制 full 且 `fixed_total=true`。项目、快照、截止点、规则、决定版本和中心覆盖相同才可同值重放；任一变化必须生成新运行，旧发布结果不变。
4. 七类变化固定为 `新增/升级/持续/降级/关闭/重开/需重新判断`；R2 继续拥有唯一生命周期状态。
5. 项目/中心五项摘要、风险 Inspector、Patient Journey 与来源比较必须来自同一 continuity plan/publication 身份，不得各自重算出不同计数或顺序。
6. 公开响应和用户界面不得暴露内部 run/hash/artifact/CAS/SQLite/R5/R6/R7 术语。

## 4. 四类 synthetic 场景矩阵

| 场景 | 必测路径 | 预期 |
|---|---|---|
| 日常 full | 无基线、当前完整快照、七类变化输入 | 全量事实生成；不伪造“与上次比较” |
| 日常 incremental | 推荐兼容基线、用户改选兼容基线、无/错/漂移基线 | 合格基线逐对象沿用或重评；不合格基线失败关闭 |
| 锁库前 full 修订 | `query_driven` 证据完整/不完整、一般 `data_revision`、多轮已发布历史 | 归因准确；每轮新完整 listing；历史不覆盖 |
| 核查前 fixed-total | 同值重放、snapshot/cutoff/rule/decision/center 任一变化、迟到回调 | 同值幂等；变化建新运行；旧结果不可变 |

每格至少覆盖：正常、边界、缺失/不兼容、同值重放、冲突或篡改；不得用 fixture 名、case id、mutation class 或预期摘要作为业务决策输入。

## 5. 逐对象对账

每个场景必须由测试独立重建并比对：

- DecisionBaseline、CarryForwardPlan 与 item 顺序/摘要；
- 四种 object type 与六种 disposition；
- 七类公开变化与前后 R2 状态/严重度；
- R5 authority digest、R6 publication/receipt/output-set digest；
- publication 四成员闭包、member-set digest 与实际字节 SHA-256；
- continuity `staging→verified→published` 与 publication `publishing→available` 的同事务门；
- 九项结构化计数与五项首屏摘要同源；
- 当前/比较来源、项目/中心/受试者/风险/Journey identity 一致。

测试 oracle 必须从输入事实重新计算，不能读取产品输出后再生成 expected。

## 6. 确定性与恢复矩阵

1. `PYTHONHASHSEED=0/1/42/随机固定值` 两次独立进程输出字节一致。
2. 普通解释器与 `python -O` 的公开 JSON、摘要、排序和错误码一致。
3. SQLite 关闭重开后 plan/publication/history 与关闭前一致；`busy_timeout` 和项目作用域保持。
4. 保存 plan、写 item、verified、publication finalize、plan published、版本推进及 commit 前后故障全部回滚且可重试。
5. CAS 冲突、迟到 callback、重复 finalize、摘要漂移、成员丢失/篡改/跨项目/不在 publication 成员集均失败关闭，不产生半发布。
6. 恢复后同值请求返回原事实；不同值请求保持稳定中文冲突，不静默新建或覆盖。

## 7. 相邻回归

- Slice-08A continuity/registry、08B bridge/product route、08C frontend contract tests；
- R7 完整测试与产品医学监查路由；
- 共享 R2 lifecycle、R5 authority、R6 ModeOutput/receipt/artifact envelope 的最小决定性测试；
- compileall 与项目/路径中性扫描；
- 医学写作保护面前后 mtime/聚合校验；
- 8911/5174 保持停止。

## 8. P0-P4 与完成门

- P0：跨项目/跨模式污染、旧结果覆盖、半发布、公开身份错绑、错误基线被使用。
- P1：任一模式入口/发布不可用、固定总量失效、七类变化或五项摘要明显错计、恢复后结果漂移。
- P2：Query/数据修订归因错误、沿用/重评/关闭语义错误、来源/风险/Journey 下钻身份不一致、内部术语泄漏。
- P3：顺序/中文错误、历史/重放信息不清、非阻断对账或诊断缺口。
- P4：不影响事实与任务完成的局部测试表达、记录或维护性问题。

接受条件：四类场景全部通过、不同 seed/优化级别字节一致、故障矩阵无半发布、相邻回归通过、独立会商 P0-P4 全零、Codex 复核当前源码/测试/记录。任何开放 P0-P4 都不接受 08D。

## 9. 边界

- 不新增或修改 UI，不做移动端/窄屏或新视觉验收。
- 不启动 8911/5174，不运行五个真实项目，不读取真实 listing，不调用真实模型。
- 不修改医学写作，不设计或测试系统安全功能。
- 不以 08D 接受声称 Slice-08、R7、R8、真实医学质量、生产或商业化完成。

## 10. 最小实施形态

优先新增一组参数化综合测试和一个标准库 subprocess 确定性探针；只有测试证明现有实现存在合同缺口时，才对共享根因做最小源码修复。不得为 08D 新建第二套 orchestration 或生产模块。
