# R7 Slice-07C-4 中文产品闭环合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_07C4_USER_PRODUCT_LOOP_V0_2`

本附录与 v0.1 合并构成待冻结合同；冲突时本附录优先。它关闭独立会商 Round 1 的 P0/P1，
不扩大到真实项目、真实模型、医学写作或安全功能。

## 12. 监查方式固定为三类

向导第 1 步只展示服务端 options 的三张卡：**日常监查、锁库前监查、核查前监查**。

- 日常监查在第 2 步选择“基于上次结果分析变化”或“重新全面分析”；前者需要同项目同模式已发布
  基线和稳定业务键，后者不使用 prior snapshot。
- 锁库前监查始终读取当前完整数据做全面复核，可在结果中比较上一轮同模式已发布结果；不得出现
  “锁库前修订增量”“只分析差异行”或 `execution_basis=incremental`。
- 核查前监查始终是新的固定总量；若数据较上一轮变化，确认页必须显示“这是新的固定数据范围，
  与上次核查不同”。
- “Query 后修订影响”只有服务端给出 `revision_attribution=query_driven` 时出现，否则统一显示
  “本轮数据修订变化”。

前端只投影 options 的 label/description/available/recommendation reason，不自行定义第四类模式。

## 13. 当前运行与下一轮主动作

同一项目最多存在一个未结束的 in-flight 运行（`waiting_start|running|stopping|interrupted_resumable`）。
`failed/ended_incomplete` 是终态，不阻断下一次监查；`completed + result_available=false` 按下表第四行
继续占用本次结果整理闭环。服务端在 prepare-and-start 前检查；若已有 in-flight，返回“当前已有监查
正在进行，请先查看本次进度”。已发布结果不是 in-flight，不阻止下一次监查。

工作条固定为：

| 当前 in-flight | 最近结果 | 主动作 | 次动作 | 其他 |
|---|---|---|---|---|
| 无 | 无 | 开始一次监查 | 查看历史 | — |
| 有 | 任意 | 查看本次进度 | 查看历史 | 不显示新建 |
| 无 | 可用 | 查看本次结果 | 开始一次新的监查 | 查看历史 |
| 无 | 已完成但结果未可用 | 查看本次进度 | 查看历史 | 不显示新建，直至发布闭合 |

表中主动作标签不由前端根据状态生成：有 selected run 时必须逐字使用服务端 `main_action`；表只冻结
次动作/其他入口的呈现条件。选择历史行后，工作条、结果身份条、看板、Journey 和来源全部绑定同一
selected public run/result context，不允许工作条指向 in-flight、主体却显示另一历史结果。若 selected
历史结果之外另有 in-flight，次动作显示“返回正在进行的监查”，不静默切换。

用户显式打开历史结果时，路由中的该 `result_context_token` 优先，页面不得被“最新一条历史”覆盖；
若该历史结果之外另有 in-flight，只允许用次动作“返回正在进行的监查”提示。普通返回项目概览时，
若存在 in-flight 则恢复其 public token；否则展示最近可用结果与开始新监查入口。不得无条件使用
`runs[0]`。

中心页不启动新监查。只有当前路由携带可用 result context 时显示本次中心结果；若项目有 in-flight
但没有可用 result context，则显示“查看本次进度”和“返回项目概览”，不展示空看板或旧结果。

## 14. 历史公开投影

历史不显示百分比；百分比只属于单次 progress。原七字段保留，并有界新增服务端中文
`status_text`，形成八字段闭集：

`public_run_token, mode_text, data_cutoff_text, comparison_range_text, run_state,
result_available, main_action, status_text`。

前端不显示或解释 `run_state`，只显示 `status_text`，只执行 server-owned `main_action`。不得对历史
逐条 N+1 请求 progress。默认 50 条，不建立第二套前端分页上限。

## 15. Public result context 是唯一浏览器结果身份

浏览器地址和 network query 的结果身份闭集为：

`project_id + result_context_token + optional site_ref/subject_ref/spine_ref/window_start/window_end/
risk_instance_ref/risk_anchor_ref/visit_ref/event_ref/source_locator_ref`。

禁止浏览器接收、保存或发送内部 `run_id/run_ref`、内部 snapshot/cutoff ref、authority hash/digest、
receipt identity、S4 identity。`public_run_token`只用于历史与进度，不代替 R5 run_ref。

### 15.1 Token 持久化与解析

`result_context_token` 在 `finalize_publication` 成功进入 `available` 时铸造并写入该行，registry v2 做
additive migration；同 publication revision 重放必须得到同 token。建立 project + token 唯一查找，
不扫描全部发布记录，不把截断 hash 当作可逆编码。`available` 行不得因后续 identity/digest 变化改
token 或升 revision；再读取不一致时按既有失败关闭，显示“本次结果暂不可查看，请返回进度页”，
不铸造新 token。

### 15.2 公开进度

新增 `GET /runs/{public_run_token}/progress` 的明确产品语义：服务端先解析同项目 public token 到唯一
internal run，再调用现有 progress adapter 和 publication overlay。07A 前端改为绑定 public token；
不得把 public token 直接当 internal run id。既有管理员 internal 路径可保留，但不进入医学监察员页面。
07A 投影有界读取 `publication_state/result_available/publication_status_text`：当分析 completed 但发布仍为
`not_started/publishing` 时，工作条与 progress 继续轮询；到 `available/blocked/recoverable_failed` 才停止。
轮询依据机器字段，不解析中文。

### 15.3 三个公开结果 GET

在 R7 product prefix 下冻结：

1. `GET /results/{result_context_token}/overview?site_ref=`；
2. `GET /results/{result_context_token}/subjects/{subject_ref}` 必须带 `site_ref`，再加窗口和定位参数；
3. `GET /results/{result_context_token}/source-evidence` 加风险实例与 source locator。

服务端每次解析 token 并核对 project/public run/snapshot/cutoff/publication revision/R5 packet digest/site
coverage，再调用现有 R5 adapter/provider；不得复制 assembler。中心、subject、spine/window、风险和
source 必须是该 packet 的精确成员。

### 15.4 公开 envelope 闭集

公开 envelope 只含：

- `identity`：project_ref、public_run_token、snapshot_token、data_cutoff_text、view，以及请求需要的
  site/subject/spine/window/risk/event/source 公共定位，并包含 server-owned `mode_text`、
  `site_scope_text`（或等价 `site_options[]`），供结果身份条直接投影；
- `projection`：复用既有 R5 audience projection，不含 authority receipt；
- `result_context_token`；
- `response_digest`：服务端对 canonical public identity + projection JSON 生成 SHA-256 公开响应摘要。

不得返回 `authority_hash`、`authority_receipt`、receipt ids、内部 run/snapshot/cutoff、S4/R5 packet
digest。前端为该公开 envelope 增加独立验证器，不削弱或混用现有 internal R5 adapter 验证。

token 不存在/过期、跨项目、publication 非 available、中心越界、packet identity/digest 漂移时，三个
GET 均整页失败关闭；不回退上一运行，不切换到 synthetic fixture，不返回半个看板。

## 16. 页面层级与密度

- 项目页唯一持久工作条高度目标不超过 56 px；不新增第二张工程状态卡。
- 结果路径的“监查方式 · 数据截止 · 中心范围”单行身份条**替换**现有四格 IdentityStrip；不得同时
  堆叠“分析批次/数据版本”等 fixture 映射文案。
- 结果概览不挂载完整 07A progress 面板；“查看本次进度”进入同一既有 progress 目的地。只有完成但
  结果未发布时继续显示 progress，并显示“分析已结束，结果整理未完成”。
- 更精确地说：selected run 为 in-flight 或 completed-unpublished 时保留 07A；仅在 selected published
  result 的 overview/site/Journey 路径卸载 07A。
- 项目/中心流向 SVG、Journey 时间轴和表格继续使用组件内部 overflow；1280/1440/1920 页面级
  `scrollWidth <= clientWidth`。Journey 上方不得新增第二条身份带。

## 17. 特殊关注规则确认

保留用户在向导内“增加特殊关注”的需求：preview 不持久化；用户选择解释候选后，必须在独立确认
对话中看到“确认后将保存为本项目规则；即使关闭本次向导，该规则也会保留”。只有再次确认才 POST
不可变 revision，并回到第 3 步默认勾选。关闭确认或关闭 preview 不写 revision；关闭主向导不删除已
明确确认的项目规则。

## 18. 纠偏后的验收补充

除 v0.1 §10 外必须证明：

1. 第 1 步只出现三张模式卡；锁库前 request 始终 full，页面无“锁库前修订增量”。
2. 同项目第二个 in-flight prepare 失败关闭；已发布后工作条出现“开始一次新的监查”。
3. 历史 JSON 正好八字段，页面不显示 run_state/百分比，不产生逐条 progress 请求。
4. 地址栏与医学监察员 result network 不出现内部 run/snapshot/cutoff 或 authority/receipt/S4/R5 digest；
   overview/Journey/source 只以 result_context_token 读取。进度路径允许 public_run_token，但不得把它
   作为 R5 `run_id/run_ref` 使用。
5. 历史结果显式 token 不被当前 in-flight 覆盖；普通项目恢复优先 in-flight。
6. result overview 只有工作条 + 一条结果身份条，不挂载完整 progress；Journey 不重复身份条。
7. 公开 token 过期、跨项目、中心越界、publication drift、authority drift 返回统一中文不可用页，
   network 中无旧运行/fixture fallback。
8. 1280/1440/1920 ego(lite) 验证工作条动作矩阵、三类模式/日常两种 basis、历史、向导确认、键盘
   焦点、项目→中心→风险/流向→Journey→Profile/来源同 token 以及页面无横向溢出。
9. 1440 保留 180px 侧栏时单独验证 1220px 流向画布缩放/组件内滚动，不得只用 1280 已折叠侧栏证明。
10. prepare-and-start 超时时：若响应已给 public token，读取该 token；若未给 token，只用原随机
    idempotency key 重放一次，不扫描历史猜测。key 是随机 client nonce，模式/数据/基线/规则实质变化时
    轮换，不以 payload hash 充当 key。
11. 结果内部的“返回项目概览”只改变 `view` 并保留 selected result_context_token；从模块导航重新进入
    医学监查才执行 §13 默认选择（in-flight 优先，否则最近可用结果）。

## 19. 冻结条件

v0.1 + 本附录已由同 session 独立复核为 `ACCEPT`。实现必须先做公开身份桥和产品 API 测试，
再做前端；不得先用 fixture 拼出视觉闭环。
