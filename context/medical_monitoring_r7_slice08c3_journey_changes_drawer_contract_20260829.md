# R7 Slice-08C-3 Patient Journey 变化标记与详情抽屉最小实施合同

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08C3_CONTRACT_V0_2`

## 1. 目标与完成边界

在现有 R5/R7 受试者医学旅程上完成一个 synthetic/offline 前端纵切：沿用唯一的横向访视/实际日期轴，把同一受试者同一时间窗内的本轮变化映射到既有事件节点；点击事件或风险后，以既有路由选择打开右侧详情抽屉，展示前后依据、关联记录、Query 草稿和来源入口。

本切片完成只证明离线合同、状态投影、交互结构、可访问行为与相邻回归；不证明浏览器视觉、真实项目、真实模型、医学质量、R7 总体、生产或商业化。8911/5174、ego(lite)、真实项目和模型在本切片保持停止；三视口与专项视觉统一属于 08C-4。

## 2. 权威与复用边界

- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md` 优先于 v0.1；冲突时 v0.2 胜出。
- 只复用现有公开 `result_context_token` 身份、`risk_instance_ref`、`risk_anchor_ref`、`event_ref`、`source_locator_ref` 和既有 evidence route，不增加 URL 键。
- 不改变 R5 `layoutJourneyTimeline` 的横向时间几何、八域顺序、日期缺失/冲突下沉规则或 calendar/study_day 事实语义。
- 不渲染第二条历史时间轴，不把 continuity 列表平铺到 Journey 主体；跨轮差异只显示为事件节点变化标记、摘要和抽屉前后依据。
- 医学写作路径为并行保护边界，本切片不得写入。

## 3. Continuity 读取与同身份选择

1. 项目/中心页维持 08C-2 读取；进入 `journey/profile/timeline` 后，只有同时具备 `project_ref + result_context_token + site_ref + subject_ref + spine_ref + window_start + window_end` 才读取 continuity。
2. 请求仅传公开 `site_ref`，随后在已严格验证的 continuity rows 中按 `object_type=risk`、完全相同的 `site_ref/subject_ref` 与闭区间包含筛选。筛选轴窗唯一取自本次受试者结果中实际用于绘图的 `projection.temporalSpine.windowStart/windowEnd`；仅当服务端结果未提供该轴窗时才回退到 `route.window_start/route.window_end`。经与 08C-2 相同的 trim 归一化后，只有 `row.window_start >= axis.windowStart && row.window_end <= axis.windowEnd` 才属于当前轴窗，等边界有效。部分重叠、不相交或缺任一日期均不进入轴内。08C-2 从单条变化进入时仍请求该行窄窗；若服务端确认并返回窄轴窗，不在该窗内的其他变化不显示，这是显式限定而非前端自动扩窗。
3. 项目、结果上下文、中心、受试者、spine、轴窗或视图变化时取消旧请求并清空旧结果；旧受试者变化不得闪回。
4. continuity 失败或加载不阻塞既有 Patient Journey；失败时不伪造变化标记，不在 Journey 显示工程错误。
5. 事件关联优先使用完全相同的 `event_ref`；没有 `event_ref` 但具有同身份 `risk_anchor_ref` 时，可绑定到已经携带该锚点的既有事件。不能绑定事件但 `risk_instance_ref` 能与当前风险匹配的变化，只标记在既有右侧风险列表并可由该风险打开抽屉；从 08C-2 携带该 `risk_instance_ref` 进入时，即使当前风险已关闭而不存在，也可打开 continuity-only 抽屉。其余未绑定变化不制造虚拟日期节点，仅保留在 08C-2 项目/中心“本轮变化”列表。
6. 若 `comparison.truncated=true`，Journey 在共享时间轴标题下显示固定提示“本轮变化较多，当前仅显示服务端已返回的前 M 条；请返回项目或中心概览查看完整范围说明。”；轴内标记只代表已返回行集，不得暗示完整。

## 4. Journey 节点变化标记

1. 既有八类 Lucide 图标与短中文双编码不变：AE、MH、合并用药、试验用药、检验检查、诊疗操作、疗效/症状、方案执行；未知类别继续使用问号图标与“类别待确认”。
2. 既有 point/interval/pending 几何不变；日期缺失或冲突继续在“日期待确认记录”区列示，不吸附到轴。
3. 关联 continuity row 的事件按钮新增一个紧凑变化标记，三通道同时存在：Lucide 图标、中文变化词、语义色；闭集与图标为新增 `CirclePlus`、升级 `CircleArrowUp`、持续 `CircleDot`、降级 `CircleArrowDown`、关闭 `CircleCheck`、重开 `RotateCcw`、需重新判断 `CircleHelp`。若当前 Lucide 版本的导出名不同，只可使用同库中语义最近的正式图标，不得用字符、emoji、手绘 SVG 或 CSS 图形代替。
4. 风险等级始终显示“高/中/低”文字；升级/降级/持续显示“前等级 → 后等级”，关闭显示“前等级（已关闭）”，重开显示当前等级；不得只靠颜色或单字缩写。
5. 同一事件关联多条变化时，按服务端 `ordinal` 顺序选首条作为节点主标记，并在可访问名称中说明总数；全部关联行在抽屉中逐条可切换，不改变服务器权威顺序。
6. 低风险与常规记录仍受现有缩放/聚合规则约束，中高风险不因变化标记而被隐藏。

## 5. 路由驱动详情抽屉

### 5.1 打开、切换与关闭

- 抽屉和 continuity 变化标记只在具备 `result_context_token` 的 R7 产品路由启用；legacy R5 保持现有 inline inspector，不改行为。
- R7 时间轴事件点击继续写入既有 `event_ref`；风险点击继续写入既有 `risk_instance_ref/risk_anchor_ref`。抽屉是否打开只由这些选择与当前结果或已验证 continuity row 匹配决定。
- R7 中新抽屉替换既有 aside 的 `EventDetailPanel + selectedRisk` 详情卡；右侧 16 项优先风险列表保留。不得同时显示两套事件/风险详情。
- push 模式可直接点击或 Tab 到另一个事件/风险切换详情；overlay 模式由焦点陷阱保护，先关闭再选择其他节点。不得叠开多个抽屉。
- 关闭按钮、Esc 或 overlay backdrop 清除 `event_ref/risk_instance_ref/risk_anchor_ref/visit_ref`，保留项目、结果、中心、受试者、spine、轴窗和当前 `journey/profile/timeline`。
- 关闭后焦点回到本次触发元素；若该元素已不存在，回到共享横向时间轴标题。

### 5.2 固定内容顺序

1. 标题；
2. 事件类别；
3. 风险等级；
4. 本轮变化；
5. 日期；
6. 前后依据；
7. 关联记录；
8. Query 草稿（依据 + 发现 + 行动项）；
9. 来源入口。

固定缺值文案：事件类别“类别待确认”、风险等级“风险等级待确认”、本轮变化“本轮变化待确认”、日期“日期待确认”、前后依据“本轮未提供前后比较依据”、关联记录“本轮未提供关联记录”、Query 草稿“本轮未提供 Query 草稿”、来源入口“原始记录位置待确认”。不得显示 token、schema、log、只读状态、人工复核状态或处理待办。

事件关联多条变化时，事件类别和日期取当前事件且保持不变；抽屉内按 `ordinal` 提供紧凑的变化切换器。当前显示行优先匹配路由 `risk_instance_ref`，否则为首条；风险等级、变化、前后依据、关联记录、Query 草稿和来源入口随当前行切换。

### 5.3 overlay / push

- 抽屉布局同时受视口和容器约束：视口 `<1440px` 必为 overlay；视口 `>=1440px` 且宿主内容宽减去 420px 抽屉与 16px 间隔后仍 `>=760px` 才为 push，否则 overlay。该阈值作为共享常量供离线测试和 08C-4 实机复核。
- overlay：宽度不超过 480px，`role=dialog aria-modal=true aria-labelledby=<稳定标题 id>`；打开后焦点在可见关闭按钮，Tab/Shift+Tab 锁定，body 垂直滚动锁定，抽屉独立滚动，backdrop/Esc/关闭按钮均可关闭。
- push：使用非 modal `aside aria-labelledby=<同一稳定标题 id>`，不得设置 `aria-modal` 或焦点陷阱；用户可以直接 Tab 或点击其他节点切换详情。Esc 与关闭按钮均关闭。主内容与抽屉均不得造成整页横向溢出，时间轴只在自身容器滚动。
- `prefers-reduced-motion: reduce` 时打开/关闭和阴影过渡瞬时完成。

## 6. 前后依据与来源

- continuity row 是跨轮变化的权威显示来源：显示 `change_text`、`severity_before_text/severity_after_text`、`reason_text`、`data_change_text`、`attention_text`。
- 当前事件继续提供事件类别、日期/访视、现有 risk、来源数量与 `sourceLocatorRefs`；不得用 continuity 文本覆盖当前事实。
- “前后依据”必须明确区分上轮等级/状态、本轮等级/状态和本轮变化原因；缺少上轮基线时显示“本轮为首次全面分析，无比较基线”。
- Query 草稿只取当前所选 R5 risk 的 `evidenceSummary.query_draft`；事件没有可匹配风险或该字段为空时显示“本轮未提供 Query 草稿”，不得从 continuity `query_draft` 对象类型跨行猜配。
- 来源按钮只有现有 `risk_instance_ref + source_locator_ref` 成对可用时启用，继续进入既有 evidence route；半身份失败关闭。

## 7. 离线验收门禁

1. 纯函数：同身份/同窗筛选、event/ref 关联、顺序、主标记、多变化、严重度文案与关闭路由补丁；同窗必须覆盖相等、真包含、部分重叠、不相交和缺窗字段。
2. 渲染：单条横向轴仍存在；八类图标/中文、七类变化、明确等级、pending 下沉、固定抽屉内容顺序均可断言。
3. 交互：overlay 与 push 阈值、稳定标题 id、Esc/backdrop/关闭、焦点进入/循环/归还、body 锁定、reduced-motion、push 直接切换；时间轴继续支持方向键浏览与 Enter/Space 打开，详情切换/打开以 `aria-live=polite` 提示当前标题。
4. ProductLoop：受试者视图读取 continuity、完整身份门禁、AbortController 取消、旧结果清空、失败不阻塞、route-only 开关抽屉；legacy R5 不渲染新抽屉。
5. 相邻回归：R5 Journey 几何/路由/产品合同、08C-2 continuity、全部 R7 suite、Vite build。
6. 独立代码会商关闭全部 P0-P2；本切片不做 visual conference，不用离线 DOM 测试代替 08C-4 ego(lite) 实机验收。

## 8. 接受与下一安全动作

合同经独立只读会商明确 ACCEPT 后方可进入实现。实现及代码会商接受后，进入 08C-4：启动隔离服务，以 ego(lite) 在 1280/1440/1920 完成真实运行时视觉、整页无横溢、overlay/push、自适应宽度、键盘、焦点、动效、中文信息密度和图表/表格一致性专项验收。
