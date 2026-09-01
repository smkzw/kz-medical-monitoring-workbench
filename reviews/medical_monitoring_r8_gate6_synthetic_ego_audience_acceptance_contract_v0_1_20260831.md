# 医学监查 R8 G6 synthetic ego(lite) 受众验收合同 v0.1

状态：`REVISED_DRAFT_V0_2_FOR_SAME_SESSION_REVIEW`  
日期：2026-08-31  
上位门：G5 `PRE_REAL_INDEPENDENT_ACCEPTED`  
目标状态：`SYNTHETIC_EGO_READY`

## 1. 唯一目标与用户

G6 只回答一个问题：一名不熟悉计算机和 AI、希望少操作、对视觉、数据和风险高度敏感的
资深医学监察员，能否从实际本地应用入口，在纯 synthetic fixture 和 mock/recorded adapter
条件下完成一键进入、启动分析、离页等待、收到完成或失败提示、回到正确结果，以及完成
System Design §15.4 用户路径；全程不需要 Python/Node/数据库命令、环境变量、端口或内部标识。

G6 不评估真实研究、真实模型、医学判断正确性或真实通知送达能力。

## 2. 硬边界

1. 只允许 synthetic fixture；不得读取五个真实项目的文件、目录、名称或元数据。
2. 只允许 mock/recorded adapter。每次 run 必须冻结可重放的 synthetic profile binding digest；
   provider/model binding 不是 synthetic 时在调用前 fail closed。
3. 不得调用产品 harness 的真实 VLM/LLM，不得下载、安装、替换或 fallback 到任何模型。
4. 浏览器验收只用 `ego(lite)`，从实际本地应用入口进入。直接 URL、API、组件测试、静态截图、
   Playwright 或开发服务器页面不能替代受众证据。
5. G6 合同独立接受前不得启动应用、浏览器或 8911/5174/8984；实施验收期间只启动本次受控
   应用拥有的进程，完成或失败后必须停止并证明无残留。
6. 不修改 `deploy/medical_writing_local`；不进入真实项目输出目录。
7. 用户界面不得显示内部 hash/path/端口/PID、模型路由、状态码、日志词或“正式事实、候选信号、
   只读 xx”等工程化标签。技术证据可以保留 digest，但不得进入受众画面。

## 3. 冻结测试资料与身份

G6 实施前必须生成一个版本化 synthetic fixture 包，至少含：

- 2 个合成项目、3 个中心、12 名受试者；不得复刻任何真实项目名称、疾病、药物、评分或列名；
- full、定期增量、锁库修订增量三种模式的结构化输入；
- AE、MH、CM、IP 给药、检验检查、PD、疗效观察和访视事件；
- 高/中/低风险、无风险、缺资料、冲突、部分失败及完全失败；
- Patient Journey 横向访视轴、中心/项目流向和 §15.4 合成对象；
- `fixture_digest + app_version + contract_version + synthetic_profile_id + binding_digest`。

fixture 只验证通用结构和用户路径，不把特定项目/药物/疾病/表格格式硬编码进业务逻辑。

## 4. 受众任务矩阵

### A. 一键进入与生命周期

1. 用户从实际应用入口执行一个动作；应用自行完成依赖检查、服务启动与 ready 判断。
2. 重复启动只聚焦已有实例，不重复创建服务或半初始化项目。
3. 首次启动、正常关闭、重启、异常退出恢复、健康检查失败和残留进程分别有明确中文结果。
4. 任一失败不得留下半初始化、半迁移、无法恢复或需要用户处理端口的状态。

### B. 分析启动与后台进度

1. 用户用中文选择 synthetic 项目、full/定期增量/锁库修订增量和必要的特殊风险条件。
2. 主按钮、默认值、禁用原因和下一步清晰；一次操作只能创建一个绑定完整的 run。
3. 进度条数字与真实细节节点一致，下方滚动播报当前工作；用户可离开进度页并继续使用系统。
4. 页面刷新、离页返回和应用重启后仍回到同一 project/admission/run，不创建或续跑另一任务。

### C. 离页提示与精确返回

1. complete/failed/partial/final_partial/truncated/timed_out/cancelled/interrupted/blocked 均使用 G3
   冻结中文语义，保留上游终态，不把通道失败改写成分析失败。
2. 四类通知能力 `authorized/denied/unavailable/unknown` 均有应用内持久记录；允许时只尝试一次
   系统通知，重放不得重复送达。
3. 点击提示只导航到现有结果或说明页，必须重新核对当前 revision、binding、source/output
   manifest、目标存在与可访问性；不得隐式启动、重试、续跑、取消或修复分析。
4. 旧 revision、binding 变化、目标删除或不可访问时只显示简洁中文阻止提示，不能跳到别的项目。

### D. 结果与下钻可读性

1. 默认看板先呈现中高风险、项目/中心/受试者层级与本轮变化，不让用户先阅读大段说明。
2. 项目/中心页包含“知情同意→筛选→治疗→研究状态”流向图和配套表格；点击节点/连线的筛选
   范围、数量和下钻身份一致。
3. Patient Journey 必须是一条按时间节点横向展开的访视轴；AE/MH/CM/IP/检验/PD/疗效和风险
   使用可区分的图形标记，点击后显示该事件详情和来源，不能退化为纵向卡片平铺。
4. 风险下钻可跳到原始受试者 Profile/Timeline/来源定位；返回后保留原筛选和阅读位置。
5. 所有用户文字中文原生、医学语义明确、信息简洁；不得用工程日志或强行翻译术语。

### E. §15.4 用户路径

用 ego(lite) 从应用内逐项验证：导出/导入、manifest/identity/lineage 结果摘要、损坏备份阻止、
干净恢复、升级前保护、迁移成功、关键边界失败后原版本可用、实际 rollback、普通包不展示凭据、
默认卸载保留数据、显式清除的预览/取消/确认、混合版本与迟到回调阻止。不得把命令行 synthetic
程序通过替代用户路径；所有写入只在受控 synthetic 临时根。

## 5. 宽屏视觉与交互门

生产目标视口只覆盖 1920×1080、2560×1440、3840×2160；不新增手机或窄屏义务。每个关键任务
至少在三个视口完成 ego(lite) 操作和整页截图，并核对：

- 页面主次、字体字号/字重/颜色、行距、对齐和中文断行；
- 文字到卡片边缘、卡片之间、图表与表格之间的节奏一致；
- 桑基图、柱状图、折线图、雷达图、表格在默认状态即清晰可读，颜色不作为唯一编码；
- 按钮、卡片、弹窗、抽屉的 hover/focus/click/关闭动效一致，不遮挡重要数据；
- Patient Journey 默认宽屏完整显示主要访视轴，密集事件可缩放/滚动但时间先后不可丢失；
- 无整页横向溢出、半行裁切、重叠、不可见焦点、滚动锁泄漏或弹窗关闭后焦点丢失；
- 风险强调克制且明确，不用装饰性阴影/动效压过医学信息。

“高级感”只接受为上述可观察证据，不以设计形容词、单张截图或 reviewer 主观喜欢替代。

## 6. 失败关闭与对抗性场景

至少覆盖：错误/过期 synthetic binding、非 synthetic provider、fixture digest 改变、重复点击、
刷新/离页/重启、并发同 run、旧 notification、目标删除、无权限/能力未知、导入损坏、迁移中断、
rollback 失败、清除取消、迟到回调、前端信封未知字段/缺字段/截断和服务 ready 超时。

任何身份、版本、manifest 或目标可访问性不能证明时，用户路径必须停止在当前上下文，显示可行动
中文，不创建新 run、不跳错项目、不修改既有结果。

## 7. 证据与通过条件

G6 通过必须同时具备：

1. 冻结合同、fixture、app、binding、adapter、测试矩阵和工具版本 digest；
2. actual-app 启动/关闭/异常/残留进程证据；
3. ego(lite) 逐步交互记录、DOM/焦点/滚动状态和三视口截图；
4. mock/recorded adapter 调用账本，证明零真实模型调用与无 fallback；
5. 通知事实/导航、§15.4、结果下钻和失败关闭的 canonical replay；
6. 聚焦、相邻、确定性、发布闭包、端口回收与医学写作边界复核；
7. 独立视觉 reviewer 与独立工程/边界 reviewer 分别审阅，Codex 重开实际运行画面最终验收；
8. 所有 P0-P4 为零，且 required 场景无 partial/not_evaluable/conflict/blocked。

若视觉执行包未完成，一般代码/证据会商不得替代视觉接受。任何修复都须按传播范围重跑，并由
原独立 reviewer 在同一会话复核。

## 8. 禁止声明与门后动作

G6 最多声明 `SYNTHETIC_EGO_READY`。它不证明真实通知、真实 §15.4、真实项目/模型/harness、医学
质量、G7-G15 或 R8 总体，也不构成生产、商业化、监管或合规声明。

只有 G6 独立接受后，才可逐项目进入 G7 source admission；每个项目仍须单独只读准入，不能用
synthetic 浏览器通过继承真实项目结论。

## 9. v0.2 纠偏附录（与 v0.1 合并适用，冲突时本节优先）

### 9.1 可证伪的执行闭集

每轮必须先冻结 `execution_boundary_manifest`：允许的 release 根、fixture 根、系统临时运行根、
应用数据根、入口产物、owned process tree、loopback 端口、mock/recorded adapter、synthetic profile
及 binding digest。允许网络闭集为空；除已冻结 loopback 应用通信外，不允许域名解析或外部连接。

必须保存独立于应用自报的文件访问、进程树、端口/网络和 adapter 调用观察账本，并与应用内部
write/call ledger 对账。任一观察器不可用、事件丢失、未知进程/根/网络、真实根访问、未知 binding、
非 synthetic provider 或 fallback 均使整轮 `blocked`，不得以 UI 正常或“未发现”通过。

### 9.2 实际入口身份与冷启动

实施前冻结 `entry_manifest`：release root、入口类型（必须为用户可双击的本地应用产物）、相对入口
路径、入口文件/目录 digest、release/app digest、预期 owned process tree、ready/failure 信号、窗口
身份与协议版本。`manage.py`、终端命令、预开的 URL、预启动开发服务和浏览器书签均不是入口。

每个入口场景从冷态开始：三个端口停止、无 owned process、无预开应用页面。用户只执行一次 OS
应用启动动作；ready 必须同时满足 owned process 身份、健康信号和主窗口实际可见。failure 必须给出
中文结果并回收到冷态或合同明示的可恢复状态。

### 9.3 生命周期可执行矩阵

| 场景 | 冻结前态/注入 | 用户动作 | 必须可见结果 | 终态与清理 |
|---|---|---|---|---|
| cold start | 全停、无页面 | 启动一次 | 主窗口 ready | 唯一 owned tree/端口 |
| duplicate start | 已 ready | 再启动一次 | 聚焦原窗口 | 无第二实例/端口 |
| normal close | 已 ready | 退出应用 | 已安全退出 | owned tree/端口全无 |
| restart | 正常退出 | 再启动 | 回到可用入口 | 新进程身份、旧 run 不重复 |
| main crash | 冻结主进程故障点 | 无额外命令 | 中文异常终态 | 子进程回收，可再次冷启 |
| child crash | 冻结子进程故障点 | 保持页面 | 中文服务异常 | 不假 ready，不留孤儿 |
| ready timeout | 健康信号冻结超时 | 启动一次 | 启动失败可行动提示 | 超时值固定，全部回收 |
| health failure | ready 前/后健康失败 | 启动或继续 | 明确不可用 | 不创建半初始化状态 |
| orphan before start | 合成孤儿进程 | 启动一次 | 自动识别并安全处置或阻止 | 不接管未知进程 |

每行冻结超时、故障点、允许残留（默认零）、恢复后的 project/admission/run 身份和端口断言；任一
不满足即 required failure。

### 9.4 Path A 通知完整矩阵

九类终态全部 required：每类必须产生应用内持久记录并导航到对应结果或说明；不得抽样。四种能力
全部 required：`denied/unavailable/unknown` 证明应用内降级，`authorized` 至少选择 complete 与 failed
各一例，通过真实本机通知通道达到可观察 `presented`，不能以 queued/accepted_by_platform 代替。

complete 与 failed 两例都要分别证明：系统通知和应用内记录来自同一 fact/revision；从系统通知
点击、从应用内点击均精确返回同一 project/admission/run；点击无启动/重试/续跑/取消副作用。
旧 revision、binding 漂移、source manifest 漂移、output manifest 漂移、目标删除、目标不可访问六项
必须逐项实机 blocked 且导航副作用为零。若当前环境不能观察 `presented` 或不能点击本机通知，G6
为 `blocked`，不得降级为应用内单通道接受。

### 9.5 §15.4 十三项用户任务矩阵

每行都须从应用内入口独立开始，冻结 fixture 初态、点击步骤、中文预期、文件状态摘要、需要的重启
点、负断言、清理与证据；全部 required：

| # | 用户任务 | 必须可见与磁盘终态 |
|---|---|---|
| 1 | 导出后导入 | 预览对象/版本，导入后所属对象与版本来源一致；后台核对 identity/lineage |
| 2 | 查看备份归属 | 用户只见“备份完整性、所属对象、版本来源”；后台核对 manifest/identity/lineage |
| 3 | 导入损坏备份 | 导入前阻止，当前项目不变 |
| 4 | 干净恢复 | 明确预览，恢复后可打开且摘要一致 |
| 5 | 升级前保护 | 自动生成保护点，原项目不变 |
| 6 | 迁移成功 | 重启后新版本可用、身份不变 |
| 7 | 关键边界失败 | 中文失败，未切换半成品 |
| 8 | 验证原版本 | 失败后原版本仍可打开和使用 |
| 9 | 实际回滚 | 用户看到回滚完成，重启后旧版本可用 |
| 10 | 普通导出 | 页面摘要无凭据值；独立检查包成员名、manifest 和全部可解码内容，synthetic credential canary、凭据字段名与 `.env` 均零命中 |
| 11 | 默认卸载 | 预览明确保留数据，重启/重装后仍可识别 |
| 12 | 同时清除数据 | 分别完成预览→取消不变、预览→显式确认后清除 |
| 13 | 混合版本/迟到回调 | 旧回调被阻止，不覆盖当前版本结果 |

CLI replay 只作后台一致性佐证，不是任何一行的受众通过证据。

### 9.6 G6 缺陷分级与禁止值

- P0：真实项目/模型/外网/越界根污染，身份错配造成跨项目展示或破坏现有数据，观察边界不可证伪。
- P1：实际入口、一键生命周期、通知双通道、精确导航、§15.4 required 用户路径、核心结果/来源下钻
  任一不可完成、错误或缺决定性证据。
- P2：主要图表、Journey、中文信息层级、焦点/滚动/三视口可读性显著妨碍医学监察员判断。
- P3：局部文字、间距、动效或次要一致性问题，不改变任务结论且有明确 workaround。
- P4：不影响当前任务的轻微润色建议。

任一 required 场景出现 `N/A`、`not_applicable`、`out_of_scope`、`irrelevant`、`partial`、
`not_evaluable`、`conflict`、`parse_failed`、`blocked` 或观察器不可用，整门不得通过；不得改标签、
降级严重度、缩小矩阵或以豁免关闭。

### 9.7 宽屏结构化视觉指标

三视口固定 browser zoom 100%；记录 CSS viewport、DPR 与原始像素。首次视觉基线执行前必须冻结且
本轮不可变的 `viewport_layout_manifest`，逐视口给出 numeric content max-width、左右 gutter、栏数、
栏宽和主要图表有效宽度；看到页面后不得回填阈值。禁止 4K 中央小岛、正文超长行和图表无意义
拉伸。正文主要阅读列必须等效 45–90 个中文字符；超出即 P2，不得由运行后 reviewer 豁免；如确需
改变，只能在首次视觉基线前修订合同与 manifest，并重新完成合同独立接受。点击目标最小
32×32 CSS px；核心按钮、风险摘要、流向图、Journey 主轴和表格
首行分别保存 bounding box、可见比例、有效绘图区和首屏位置。每个关键任务三视口均保存当前原图、
DOM 结构与结构化测量，不以三张截图代替交互。

### 9.8 Journey/流向挑战夹具与独立重建

fixture 必须加入：密集访视、同日 AE/MH/CM/IP/检验/PD 多事件、长中文标签、跨期风险、局部缩放/
滚动，以及含分流、汇流、零值和中心差异的 flow rows。独立 oracle 从 fixture 重建访视顺序、marker
数、风险绑定、流向节点/连线/数量及同源表格合计；页面逐项对账。下钻和返回必须保持精确身份、
筛选、缩放/滚动与阅读位置，装饰性轴线或 Sankey 外形不能算通过。

### 9.9 独立审阅隔离与顺序

顺序固定为：actual-app execution → 绑定本轮 app/fixture/contract/binding digest 的当前原图、DOM、
边界观察与调用账本 evidence pack → fresh 独立视觉审阅 + fresh 独立工程/边界审阅 → 修复后分别在
原会话复验 → Codex 重新打开当前运行画面最终验收。两个 reviewer 不得互看结论或继承实现者处置；
旧 R7 图片/记录只作结构参考，不能进入当前 PASS 证据。
