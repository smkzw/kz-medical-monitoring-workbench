# R7 Slice-07A 医学监查真实进度与恢复界面合同 v1.1

日期：2026-08-28  
状态：`ACCEPTED_FOR_GOVERNED_IMPLEMENTATION`

## 1. 目标与边界

把 R7 已持久化的运行分母、后台状态和恢复动作接入医学监查用户界面，让不熟悉
计算机和 AI 的资深医学监察员在一屏内看懂“这次监查处理多少、完成多少、现在在做
什么、是否可停止或继续”。页面离开、刷新或返回后必须读取同一服务器状态，不把
React 本地状态当权威。

本切只做 synthetic 隔离 UI；不运行五个真实项目，不修改医学写作，不扩展风险、
Patient Journey 或项目/中心流向图，不设计/实现/测试系统安全功能，不展示或编辑
凭据。浏览器验收只用 ego(lite)。

## 2. 数据权威与最小接线

- 复用已挂载的项目域前缀：
  `/api/projects/{project_id}/modules/medical-monitoring/r7`。
- 本切从 R5 路由已有 `run_ref` 取得本次运行标识，不从 localStorage、前端缓存或页面
  文案推断。缺少 `run_ref` 时不发 progress 请求，显示“尚无本次监查”的中性空态。
- 页面只调用既有公开接口：progress 与 execution start/cancel/resume。prepare 及其
  `work_units` 由上游运行准备流程或 synthetic 验收夹具提供，本切前端不得自行组装分母。
- `execution_not_prepared` 映射为“本次监查范围尚未准备”；`run_binding_not_found` 与未
  初始化映射为“尚无本次监查”。空态不用风险红，也不解析 HTTP 文案来判断类型。
- `progress` 响应是展示唯一权威：`completed/total/percent`、`stage_progress`、
  `current_work`、`latest_updates`、`run_status_text`、`available_actions`、`run_state`，以及
  `scope_version_text/mode_text/basis_text/data_cutoff_text`。`headline` 与
  `status_overview` 不重复渲染；大数字区直接使用服务器 `progress_text`。
- `run_state` 是轮询与状态分支的机器可读权威，至少覆盖 `waiting_start`、`running`、
  `stopping`、`interrupted_resumable`、`completed`、`ended_incomplete`、`failed`；
  `run_status_text` 只负责用户文案，前端不得解析中文来决定是否轮询。
- UI 不推算完成数，不按时间递增，不用模型 token、日志行数或动画位置制造假进度。
- 轮询只是重新读取事实：`running`/`stopping` 时 2 秒一次；页面不可见时停止轮询；
  恢复可见时立即刷新；其余稳定状态不持续轮询。`stopping` 可能等待当前分析自然结束，
  在服务端明确转态前持续轮询，不显示前端自造的超时失败。
- request 使用 AbortController；项目、run 或页面切换后拒绝迟到响应写入当前视图。
- 首次成功读取前只显示加载/空态，不渲染上一个项目或运行的任何旧数字。

## 3. 用户界面结构

桌面端在现有医学监查 R5 页面顶部导航下新增紧凑“本次监查进度”区域，不另建后端
概念页，不挤占风险/受试者主内容。

1. 顶行：`本次监查进度`、模式/全量或增量/截止日期/范围版本；这些范围信息使用次级
   字号。右侧动作仅在服务器提供且当前调用者实际可执行时显示。现阶段权限模型不在
   本切修改：医学监察员可查看真实进度，现有运行管理员可执行开始/停止/继续；不得用
   管理员身份冒充医学监察员完成动作验收。
2. 主进度：大号直接显示服务器 `progress_text`；一条克制的橙色进度条，使用服务器
   `percent` 设置可访问属性；状态文案用 `run_status_text`，不显示“AI 正在思考”。
3. 阶段分布：按 `stage_progress` 顺序横向展示阶段名称、已处理/总数；宽屏一行完整，
   窄屏在组件内部换行，不造成页面横向溢出。
4. 当前工作：最多展示 `current_work` 的 3 项，超过时显示“另有 N 项”；正文使用服务器
   的医学工作说明；运行中暂无内容时显示“正在准备下一项分析”。
5. 最近进展：按服务器既有顺序展示 `latest_updates` 前 5 项并显示 `time_text`，不在
   前端重排；无动态时显示简短空态。它属于用户可读工作播报，
   不出现 event type、node、attempt、provider、model、selector、lease、hash、path。
6. 失败/中断：保留完成进度与阶段信息，不清零；主文案说明“已中断，可继续”或稳定
   中文错误；不自动重试，不把失败包装成完成。

## 4. 动作与反馈

- `开始`：只在 `available_actions` 含“开始”时显示；点击后立即禁用重复提交，收到响应
  后重新读取 progress。
- 动作映射固定为：开始→`execution/start`、停止→`execution/cancel`、继续→
  `execution/resume`；未识别动作不渲染为按钮。
- `停止`：第一次点击后原位显示“确认停止”及“停止后不再开始下一项；当前正在分析的
  内容可能完成”；使用页面内联提示，不使用阻塞式浏览器 confirm。Esc 或 8 秒无操作
  复原，焦点保留在动作区；确认期间不允许其他动作。
- `继续`：只在服务器允许时显示；点击不改变分母、档案或数据版本。
- 操作失败：动作区域附近显示服务器中文错误，保留当前事实面；提供“重新读取进度”，
  不把 POST 失败转成前端成功态。
- 403 单独显示“当前账号不能操作本次监查运行”，随后隐藏本次加载周期中的动作，继续
  保留进度事实面；这不是对权限模型的修改或验收。
- progress 读取失败：保留最后一次事实，不清零；显示“进度刷新失败，最后读取于
  HH:MM”并提供“重新读取进度”。连续失败按 2→5→10→30 秒退避；该时刻只是页面成功
  接收信息的时间，不代表医学数据更新时间。
- 离页后台：用户切到医学监查其他看板后不显示阻断蒙层；再次打开进度区域时从服务器
  恢复。前端卸载不发送停止请求。

## 5. 视觉与中文

- 使用康哲暖白基底、深蓝正文、橙色唯一主强调；风险红只表达真正失败/阻断。
- 进度组件为信息密集的工作台卡片，不做大面积渐变、玻璃态、聊天气泡、霓虹或夸张
  loading 动画。
- 数字使用 tabular nums；进度条不能成为唯一状态表达；所有颜色均有文字或图形补充。
- 用户可见文案禁止：正式事实、候选信号、只读、provider、model、selector、attempt、
  session、owner、lease、generation、invocation、profile、adapter、hash、path、SQLite、
  后端、日志、token。
- 不把“人工复核未完成”设为横幅或待办，不建立审批/关闭交互。
- 支持 `prefers-reduced-motion`；动作按钮有可见焦点；只有 `run_status_text` 变化才进入
  `aria-live="polite"`。进度条使用 `role="progressbar"` 及 `aria-valuenow/min/max`、
  `aria-valuetext`；进度数字和最近进展不进入 live region；错误使用 `role="alert"`。

## 6. 状态矩阵

| 服务器状态 | 主文案 | 动作 | 关键展示 |
|---|---|---|---|
| 缺少运行标识/未绑定 | 尚无本次监查 | 无 | 不发请求或按错误码进入中性空态 |
| 未准备 | 本次监查范围尚未准备 | 无 | 按 `execution_not_prepared` 映射，不解析文案 |
| `waiting_start` | 以服务器文案为准；核对基线为“等待开始医学监查” | 开始（仅有权限者） | 0/Y、阶段分母、无当前工作 |
| `running` | 以服务器文案为准 | 停止（仅有权限者） | X/Y、当前工作、最近进展；后台可离页 |
| `stopping` | 以服务器文案为准；核对基线为“正在停止…” | 无 | 保留 X/Y，持续轮询，不显示已取消 |
| `interrupted_resumable` | 以服务器文案为准 | 继续（仅有权限者） | 保留 X/Y 与中断前进展 |
| `failed` | 以服务器文案为准；核对基线为“分析服务连接异常，本项分析未完成” | 仅以服务器动作为准 | 本切同步修订服务端中文；不泄漏配置身份或原始错误 |
| `ended_incomplete` | 本次监查已结束，部分工作未完成 | 无 | 保留完成事实，不包装成完成 |
| `completed` | 本次监查已完成 | 无 | Y/Y、100%、阶段全量完成 |

重试耗尽但仍可继续时归入 `interrupted_resumable`；重试耗尽且没有可用动作时归入
`failed`。UI 不根据“重试上限”等中文词语自行分类。

## 7. 验收矩阵

1. 组件 projection 单测覆盖完整、缺字段、错误响应、项目/run 身份漂移和禁止词扫描；
   禁止词扫描覆盖所有状态分支与重试耗尽文案。
2. API client 单测钉住 GET/POST 路径、空 body、AbortSignal 与错误不吞。
3. React 交互测试覆盖开始、停止、继续、重复点击、刷新恢复、离页不取消后台任务。
4. synthetic 产品路由证明数字来自 manifest/work-unit，状态动作与当前 R7 API 一致。
5. Vite build、现有医学监查前端回归与 R7 产品路由回归通过。
6. ego(lite) 桌面宽屏及 1280px 验收：首屏能看懂状态、精确进度、阶段、当前工作与动作；无横向
   页面溢出；页面离开后后台继续；返回/刷新恢复同一进度。
7. ego(lite) 错误/中断验收：不清零、不假完成、不自动重试、无后端词、按钮可键盘操作。
8. ego(lite) 键盘走查开始、停止内联确认、继续；验证 reduced-motion 与轮询不产生重复
   屏幕阅读器公告。
9. 视觉独立会商后由 Codex 查看真实截图、DOM/AX 与 API/SQLite 对账；模型自述不作为接受。

身份边界：进度查看、离页后台、刷新恢复以医学监察员身份验收；开始/停止/继续动作以
现有运行管理员身份验收；同一验收项不混用身份，也不修改或测试权限模型。

## 8. 非本切内容

- 项目/中心 Sankey 流向看板与表格（Slice-07B）。
- Subject Journey/共享访视轴真实产品接线（Slice-07C）。
- 真实项目、医学质量判断、多模型风险归并、报告/Query 导出。
- 凭据管理、安全审批、权限设计或安全测试。
