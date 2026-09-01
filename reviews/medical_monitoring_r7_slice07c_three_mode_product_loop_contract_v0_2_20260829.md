# R7 Slice-07C 三模式产品闭环合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_R7_SLICE_07C_THREE_MODE_PRODUCT_LOOP_V0_2`

本附录与 v0.1 合并构成完整合同；冲突时本附录优先。它关闭独立会商 Round 1 的 A–J 项，
不扩大到真实项目、医学写作或安全功能。

## 11. 启动与运行操作边界

本切对 07A 做一个有界产品修订：具备医学监查使用权限的医学监察员可以完成
`prepare-and-start`，因为“开始一次监查”是该系统的核心用户动作；这不等同于开放底层运行
管理接口。停止、继续、工作范围重建和发布恢复仍沿用既有运行管理员动作边界。验收必须分别
使用医学监察员完成“向导→启动→查看进度→查看结果”，使用运行管理员完成“停止→继续”。

主界面不得显示角色、权限、管理接口或后端术语；无权动作由服务端返回稳定中文说明。

## 12. 日常增量与真实分母

日常增量的执行输入固定为：

1. 当前完整数据快照；
2. 同项目上一已发布快照；
3. 两者之间由稳定业务键生成的 canonical row-level diff；
4. 对需历时判断的对象同时提供既往上下文，而不是只截取变化行。

完整导出的 listing 是数据载体，不决定运行是全量还是增量。服务端按当前与既往已发布快照的
业务键差异标记“新增、修订、未变化、删除/不再出现、无法比较”；无法形成稳定业务键时不得
伪造增量，向导禁用并说明“当前数据尚不能与上次结果逐项比较”。

模式模板是 work-unit 的唯一生成源：模板节点、受试者/中心范围、增量标记和已确认特殊规则
确定性生成 manifest work-unit；页面范围摘要与进度分母从该同一集合投影。运行开始后分母
冻结。synthetic 夹具以明确的 canonical key 和固定排序证明跨 hash seed 稳定。

## 13. 锁库前修订归因

只有可追溯来源明确给出 `revision_attribution=query_driven`，并带有同项目 Query/数据修订关联
依据时，页面才使用“Query 后修订影响”。其他变化显示为“本轮数据修订变化”；系统不得从
时间先后或字段差异推断 Query 因果。

既往比较基线默认选择最近一次**已发布**的同项目锁库前运行，并展示推荐理由；用户可从其他
已发布候选中选择。发布失败、未完成、跨项目或固定总量核查运行不得作为默认锁库前基线。
所有比较基线必须与当前运行同模式且结果已发布；核查前固定总量快照不得作为任何其他模式的
比较基线。锁库前 full 的比较基线属于工作范围身份，不写入仅供 incremental 使用的
`prior_accepted_snapshot_ref`。

## 14. 核查前固定总量

固定发生在服务端成功开始运行的时刻，并固化
`project × run × snapshot × cutoff × site coverage`。同请求重放返回同一运行；原运行不得改变
范围。之后数据发生变化时，用户重新确认会创建新的核查前运行、新 snapshot 和新截止点；旧
运行及其结果永久可回看。向导必须明确提示“这是新的固定数据范围，与上次核查不同”。

opaque navigation token 只是公共运行标识，不是安全凭据；本切只验证项目隔离和身份对账，
不作防伪造或安全性结论。

## 15. 特殊风险规则生命周期

采用项目级版本化持久语义，以满足用户可在后续某次监查增加规则的需求：

- `POST /risk-rules/preview`：自然语言拆解，只生成待确认草案；
- `POST /risk-rules`：确认后追加项目级不可变 revision；
- `GET /risk-rules`：返回当前项目已确认规则的中文摘要、适用范围、起始运行和可选择状态；
- `GET /run-setup/options`：同时返回本次可选规则 revision；
- `prepare-and-start` 只接收已确认 rule option token，冻结具体 revisions。

规则修订不回写历史运行，也不自动进入未来运行；用户每次可沿用、取消或选择新 revision。
规则无法可靠拆解时只返回中文歧义说明和 2–5 个解释候选，不允许进入确认。规则生成的附加
work-unit 计入同一真实分母。

## 16. 结果发布事实面

新增 run-keyed 原子 `ResultPublication` 事实：至少绑定 project/run/snapshot/cutoff/site coverage、
R6 receipt set、R5 authority packet digest、状态与 revision。发布幂等；同 run 同内容重放不新增；
不同内容冲突；失败保留可恢复状态，不覆盖已接受发布。

R6 门禁逐项映射：

- 身份：每个 receipt 的 profile、adapter、input 及 run scope 与冻结绑定一致；
- 覆盖：所有 mandatory work-unit 都有 receipt，missing=0；
- 解析/QC：`state=complete`、`parse_state=parsed`、coverage complete、合同校验通过；
- 聚合：模式所需输出集合齐全，且可确定性组装一个同身份 R5 authority packet。

R7 progress 作为唯一展示权威，有界新增：

- `publication_state = not_started | publishing | available | recoverable_failed | blocked`；
- `result_available` 布尔值，仅在 `available` 为 true；
- 对应中文 `publication_status_text` 和管理员可用恢复动作。

主动作严格三态：运行中/等待/中断为“查看本次进度”；运行完成且结果可用为“查看本次结果”；
运行完成但发布未完成为“查看本次进度”，面板显示“分析已结束，结果整理未完成”。不得用
`completed` 单独推断结果可打开，也不得回退到上一运行看板。

## 17. 项目、中心与 Journey 身份

`result-entry` 返回项目看板四元组 project/run/snapshot/cutoff；中心视图继续使用既有 overview
请求加 `site_ref`。ResultPublication 同时冻结站点覆盖集合。请求不在集合中的中心时返回
“该中心不在本次监查范围”，不得显示空看板或旧数据。项目/中心流向、风险与 Journey 全部
读取同一 R5 authority packet；任何一处身份不一致整页失败关闭。

## 18. 幂等、超时与创建未完成

- 已确认请求的规范内容生成 client idempotency key；模式、数据、比较基线或规则 revisions 任一
  改变时必须轮换 key。
- 相同 key/相同请求返回同一 public run；相同 key/不同请求返回 409 中文冲突。用户确认新内容
  后用新 key 新建，不静默覆盖。
- 浏览器超时先按 public token 查询：存在则进入同一进度；不存在则以同 key 重试一次。再次
  失败才显示“本次监查尚未建立”，保留输入供用户重试。
- `waiting_start` 也属于“已有当前运行”，项目页主动作进入进度，不重复打开向导。
- 医学监察员创建后若停留在 `waiting_start`，页面显示“本次监查已建立，等待开始”；仍由运行
  管理员执行继续/恢复，不在本切新增监查员自恢复接口。
- MTPLX 只要租约和心跳有效即保持运行态；短期没有文本输出或浏览器请求超时不得转失败。

## 19. 补充验收矩阵

除 v0.1 §9 外，必须增加：

1. 医学监察员完成向导/启动/结果回看；运行管理员停止/继续/发布恢复，身份不混用。
2. 当前全量快照 + 既往已发布快照 + keyed diff 生成同源 work-unit；跨 hash seed 顺序和分母一致。
3. 无稳定业务键、混合模式基线、未发布基线、多候选锁库前基线均给出正确禁用/推荐理由。
4. Query 归因有证据时显示因果；无证据时降级为“本轮数据修订变化”。
5. 核查前同请求重放；数据变化后新建固定总量；旧结果仍可打开。
6. 规则预览成功、歧义候选、确认 revision、后续运行显式选择、历史运行不变。
7. option token 过期/跨项目/数据变化后 fail closed，并回到重读 options + 用户重确认。
8. 同 key 同请求重放、同 key 异请求 409、规则变更轮换 key、超时后查询与一次重试。
9. mandatory receipts 齐全/缺失、解析失败、身份漂移、发布原子重放/冲突/可恢复失败。
10. `completed + result_available=false` 不打开结果；恢复后同一身份翻转为 true。
11. 项目结果入口、中心站点覆盖与越界、Journey 跳转的四元组/站点身份一致。
12. 1280/1440/1920 ego(lite) 主按钮三态、向导、进度、结果入口、409/过期/越界中文均通过。

## 20. 冻结条件与实施拆分

合同会商接受后，实施拆成四个有序子步，上一子步未通过不得并行消费其接口：

1. 07C-1：run options、规则 preview/registry、模式模板与 keyed diff 的纯数据合同；
2. 07C-2：原子 prepare-and-start、public run history、幂等与长等待恢复；
3. 07C-3：ResultPublication、progress 有界扩展、R5 authority packet/result-entry；
4. 07C-4：中文向导、历史/主按钮、进度/看板/Journey 贯通与 ego(lite) 验收。

每步都只用 synthetic；不得先做前端假闭环或以静态 fixture 冒充已发布结果。

实施时还必须遵循：低层管理员 `execution/prepare` 继续接受显式 work-unit，向导路径则由服务端
模板生成并注入同一 manifest；public token 仅由服务端派生；ResultPublication 的 `blocked`
表示不可自动恢复的身份/QC 阻断，`recoverable_failed` 表示管理员可重试的发布失败；R5 packet
组装复用既有 S4 builder，不建立平行组装器。
