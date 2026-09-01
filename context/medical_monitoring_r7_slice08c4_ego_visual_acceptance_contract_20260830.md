# R7 Slice-08C-4 ego(lite) 运行时与视觉专项验收合同

日期：2026-08-30  
状态：`FROZEN_ACCEPTED_FOR_GOVERNED_VISUAL_EXECUTION`

## 1. 目标与接受边界

本切只验收已接受 08C-1/2/3 在隔离 synthetic 产品运行时中的用户可见表现：项目/中心本轮变化、单条横向 Patient Journey 访视轴、七类变化、八域事件、overlay/push 详情抽屉、来源下钻与返回。验收浏览器唯一使用 ego(lite)，视口为 1280×900、1440×900、1920×1080。

本切不运行五个真实项目，不调用产品模型，不评价真实医学正确性或泛化，不修改医学写作，不新增依赖，不做系统安全设计/测试，不接受 R7 总体、生产或商业化。

## 2. 用户与视觉原则

验收用户是懒惰、视觉敏感、数据敏感、风险敏感、中文原生且不熟悉计算机/AI 的资深医学监察员：首屏先看到范围、截止点、本轮中高风险变化和下一层入口；不要求理解 provider、token、hash、DTO、正式事实、候选信号、只读等工程术语。

- 字体使用当前产品中文字体栈；页面标题 25–34px、二级标题 18–20px、正文 14px、辅助 12px，正文行高 ≥1.5，数字使用 tabular nums。
- 4px 基数；卡片/抽屉/表格只用 8/12/16/24/32 间距；中文不出现单字孤行、不美观跨行、按钮内断行或信息贴边。
- 暖灰页面、白卡、轻边框与克制多层阴影；品牌橙仅用于主要操作/选中，红/琥珀/蓝/绿只承载风险语义；不使用彩虹、3D、装饰渐变或毛玻璃。
- overlay backdrop 的实际 alpha 目标为 0.24–0.32；抽屉主阴影的垂直偏移不超过 16px、模糊半径不超过 40px、单层 alpha 不超过 0.18。阴影只分离层级，不压暗临床内容或代替边界。
- 图表标题直接表达结论，数字优先直接标注；图表与表格同源。复杂时间关系必须使用轴/流向，不得退化成卡片流水账。
- 动效 160–220ms，仅用于状态衔接；`prefers-reduced-motion` 下立即完成。按钮/卡片可以有轻微 hover/pressed/focus 阴影，不做抢夺数据注意力的“酷炫”动效。

外部设计依据仅用于方法，不替代本地产品证据：

- W3C APG modal dialog：打开后焦点进入对话框，Tab/Shift+Tab 留在内部，Esc 关闭，关闭后返回触发元素或逻辑后继；见 https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
- W3C keyboard interface：焦点与选择分离，方向键用于复合组件内部移动，若选择引发网络刷新不应随焦点自动执行；见 https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- McKinsey Design System 的 functional palette 主要服务数据可视化；本项目只借鉴“克制功能色+重点洞见”原则，不复制其资产；见 https://cdn.mckinsey.com/assets/sketch/McK_DS_core_Artboards.pdf

## 3. 参考证据与比较方法

### 3.1 固定参考

- 用户上传流向参考图的工作区冻结副本：`artifacts/mm_r7_slice08c4_ego_visual_20260830/reference_flow_sankey.png`。原始临时路径仅保留为来源记录：`/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/codex-clipboard-07757ff8-29c4-4136-a9fa-17bbbc40d16b.png`。只参考“知情同意→筛选→治疗→研究状态”的横向分流结构，不复制英文、颜色或数据。
- 既有产品参考：`artifacts/mm_r7_slice07c4_product_loop_ego_20260829/evidence_w03/03_subject001_journey_1280.png`、`12_subject001_journey_1920.png`、`artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/codex_browser_acceptance_20260826/s7-S7-B08-1440x900-journey-eight-domain-density.png`。
- Patient Journey 功能形态权威仍是冻结 08C 合同与当前产品源码；旧截图均降级为结构参考，不能作为当前中文、抽屉或像素的通过依据。

### 3.2 每轮比较

每个视口至少保存：参考图、修订前产品截图、修订后产品截图、参考+产品同画布并列图、DOM/可访问性/溢出结构化记录。Codex 必须实际打开并查看并列图，逐项判断轴顺序、卡片边界、文字、间距、色彩、图标、焦点、抽屉和信息密度；截图存在本身不是 PASS。

参考绑定如下：

| 用户任务 | 比较依据 | 允许判断 | 禁止判断 |
|---|---|---|---|
| 项目/中心受试者流向 | 工作区 Sankey 副本 + 当前修订前/后同视口截图 | 四阶段横向分流结构、节点/连线层级、同源表格关系 | 英文、原图颜色、原图数据或像素复刻 |
| Journey 单轴/八域 | 07C-4 1280/1920 与 R5 1440 截图仅作结构参考 + 当前修订前/后 | 单条横向轴、访视顺序、事件在轴下、信息密度变化 | 旧中文标签、旧内联“检查依据”、旧抽屉形态作为权威 |
| overlay/push 抽屉 | 当前 08C-4 修订前/后产品截图与结构化 DOM 记录 | 当前抽屉尺寸、位置、遮挡、焦点、滚动和来源入口 | 用无抽屉旧图证明通过或失败 |

并列图必须同一产品视口、同一状态、同一轴容器 `scrollLeft`。流向参考只裁剪到 Sankey 主体带；不得拉伸。抽屉任务采用“当前产品修订前+修订后”并列，不强行拼入无抽屉旧图。

## 4. 隔离运行时

- 只启动本工作台的隔离 synthetic 服务与前端，不挂载真实项目/真实数据/产品模型。08C-4 专用 fixture 路径、路由、身份与状态矩阵必须遵循 `context/medical_monitoring_r7_slice08c4_synthetic_fixture_spec_20260830.md`；不得直接启动缺少 continuity 路由的 07C-4 fixture。
- 专用端口预留为 `8984`；启动前必须以只读命令确认空闲。若被占用，选择新的空闲专用端口并同时更新证据记录，不得复用 8911/5174。
- 证据根目录固定为 `artifacts/mm_r7_slice08c4_ego_visual_20260830/`；网络域名闭集为当前专用 `127.0.0.1:<port>`，任何其他域名请求均判为失败。
- 运行端口必须预先确认空闲并在证据中记录；8911/5174 在开始前保持停止。若专用端口启动，结束时必须停止并复核所有临时端口。
- 不把 fixture 写入生产数据库；不安装依赖；不修改全局配置。

## 5. 三视口硬门

### 5.1 全视口

- `document.documentElement.scrollWidth === window.innerWidth`；时间轴只允许自身容器横向滚动。
- 页面标题、范围/截止点、默认中高风险、变化类别、受试者/中心身份不漂移；无内部字段/工程标签/英文裸状态。
- 面包屑/身份条中文闭集为 `项目概览 / 中心概览 / 受试者医学旅程 / 原始记录`；返回按钮用“返回项目概览/返回中心概览”等任务语义，不展示“中心已绑定”等实现状态。
- 正文实际对比度 ≥4.5:1，图标/边界/大字 ≥3:1；交互目标 ≥24×24 CSS px；焦点环 2px 且不被裁切。
- 单条横向访视轴可在默认宽屏首屏理解时间先后；事件在轴下按八域标记，点击/Enter/Space 打开详情；左右方向键顺序等于视觉顺序。
- 八域显示闭集固定为 `AE / MH / 合并用药 / 试验用药 / 检验检查 / 诊疗操作 / 疗效/症状 / 方案执行`；旧截图中的 `试验药 / 检验/检查 / 住院/操作 / 症状/疗效 / 方案符合性` 不是 08C-4 文案权威。
- 抽屉九段顺序、来源按钮、逐条切换、aria-live、关闭与返回保持同一 project/result/site/subject/spine/window。

### 5.2 1280 overlay

- 宽度 ≤480px，`role=dialog`、`aria-modal=true`、稳定 `aria-labelledby`。
- 初始焦点在可见关闭按钮；Tab/Shift+Tab 循环；body 滚动锁；抽屉独立滚动。
- backdrop、Esc、关闭按钮均可关闭；焦点返回原事件/风险，触发元素不存在时返回轴标题。
- overlay 不遮蔽关闭按钮、行切换器、来源入口或当前变化摘要；背景内容不可交互。

### 5.3 1440/1920 push 与自动降级

- 至少一个状态真实进入 420px push，主 Journey 剩余宽度 ≥760px；push 是非 modal aside，无 `aria-modal`、无焦点陷阱。
- push 判定宿主为 `.r5-subject-columns`，共享常量为 viewport `1440`、drawer `420`、gap `16`、Journey 最小宽 `760`、overlay 最大宽 `480`；不得另写第二套阈值。
- 默认 1440/1920 先验证真实 420px push；再在 fixture 的 `?host_width=1195` 状态由隔离页面把 `.r5-subject-columns` 确定性限制为 1195px，验证自动降级 overlay。`?host_width=1196` 必须进入 push，形成边界对照；不得用 DevTools 停靠或浏览器外框偶然缩窄代替。
- 页面首次渲染不得先闪现 overlay 再变为 push；在 `requestAnimationFrame` 后和两帧稳定后分别记录 layout mode。
- push 打开后轴顺序、事件位置、风险列表与抽屉均无重叠/裁切；Tab 可离开抽屉切换其他事件/风险。
- 1440×900 和 1920×1080 必须记录抽屉标题、关闭按钮、逐条切换、当前变化摘要、来源入口的 bounding box；全部在 viewport 内且不被父容器裁切。必要时抽屉自身纵向滚动，不能让嵌套风险列表挤走关闭/来源。

## 6. 用户任务矩阵

每个视口至少完成：

1. 项目结果默认页：核对首屏五项 `新增 / 升级 / 重开 / 需重新判断 / 中高风险`、默认中高风险、本轮变化、流向图与同源表格；不得以筛选后的列表数冒充总口径。九项计数只在结构化记录中逐键重建，不要求首屏平铺九个数字。
2. 中心下钻：中心身份、返回上下文、筛选与关键计数一致。
3. 风险变化筛选：七类中文闭集固定为 `新增 / 升级 / 持续 / 降级 / 关闭 / 重开 / 需重新判断`，核对当前/原等级、默认中高风险和服务端顺序。流向页若显示变化标签，也必须用该闭集；旧 `升高 / 降低 / 解除 / 重新出现 / 暂不可评估` 不得出现。
4. Patient Journey：单轴、访视顺序、八域图标、变化标记、pending 区与局部横滚；八域中文服从 §5.1 闭集。
5. 事件入口与风险入口分别打开抽屉；逐条切换不会整页闪烁或卸载。fixture 固定 `subject_ref=S08C4-001`：`event_ref=event-multi-001` 至少 2 行，`risk_instance_ref=risk-multi-001` 至少 2 行；检查 `[data-change-row]` 数量、当前 `aria-pressed=true` 数量恰为 1、行标题与抽屉“共 N 条”一致。事件入口只出现同 `event_ref` 行，风险入口只出现同 `risk_instance_ref` 聚合行。
6. 来源下钻与返回：项目/结果/中心/受试者/spine/轴窗保持。
7. 七状态分层：首次全面分析、可比增量和篡改阻断必须是浏览器可达实机页；不可比/覆盖不足、本轮缺行、关闭有证据、规则变化允许以命名 envelope 验证数据语义，但每类仍须在同一隔离页提供一条可见行或明确空状态。篡改阻断必须实机显示 `本轮变化暂不可查看`，不得降级为普通空状态。envelope-only 证据不得冒充像素 PASS。
8. reduced-motion、键盘、焦点、滚动锁、关闭归还和 aria-live。

## 7. 数据对账与自动结构化门

- 用 continuity rows 独立重建九项 `change_counts`，逐键等于服务端摘要；默认筛选不改变摘要。
- 九项闭集为 `new / upgraded / continued / downgraded / closed / reopened / needs_rejudgment / changed_subject_count / mid_high_total`；结构化记录同时保存服务端值、按 rows 重建值与相等布尔值。
- 新增/升级/持续/降级/关闭/重开/需重新判断的图标、文案、语义色与抽屉当前行一致。
- 轴节点 marker 的“共 N 条变化”必须等于该入口可切换行数；risk 与 event 两类入口分别对账。
- 每个截图同时保存 viewport、页面 scrollWidth/clientWidth、时间轴 scrollWidth/clientWidth/scrollLeft、drawer role/aria/modal/尺寸、`requestAnimationFrame` 后 activeElement、body overflow、可聚焦元素序列、关键颜色对比度和网络请求域名。对比度按 WCAG 相对亮度公式由实际 computed color/background 计算。
- 1280 overlay 验证 `prefers-reduced-motion: reduce` 时 transition/animation 的实际 computed duration 为 0；普通模式记录 160–220ms。图标按整个交互命中框评估 ≥24×24，不以内部 glyph 10px 单独判失败；视觉隐藏的 aria-live 不要求显示。

## 8. 缺陷与完成规则

- P0：身份/路由漂移、overlay/push 语义错误、整页横向溢出、event/risk 行集混淆、九项计数错、伪造视觉 PASS、启动 8911/5174 或真实数据。
- P1：中文闭集破坏、对比度不达标、overlay 焦点循环/归还/滚动锁失败、首屏口径错、必需实机状态缺失、关键入口不可达。
- P2：影响扫描和操作的间距/孤行/裁切、抽屉 padding 偏离约定网格、1440 push 关闭/来源/摘要被裁、宿主测量或边界状态不可复现。
- P3：不影响任务完成的阴影轻重、字号层次、图标 glyph 比例、轻微动效或抛光问题。
- P4：标点、微小对齐、不可见 aria-live 等不影响理解或交互的细节。
- 任何 P0/P1/P2/P3/P4 都必须修复并重跑受影响任务；本切不接受“已知 P3/P4”带病通过。
- 抽屉当前 CSS 中 `18/14/11/6/9px` 等值不自动豁免；视觉执行必须按实际效果与 4px 基数审阅，修复为 8/12/16/24/32 网格或在接受记录中给出可复现的必要性证据。不存在沿用 07C-4 “O3 省略号”的默认豁免。
- 焦点权威以 08C-3/v0.2 为准：overlay 初始焦点在可见关闭按钮且陷阱生效；push 不设陷阱。v0.1 “焦点进入标题/所有抽屉均陷阱”的旧句不再适用。
- 视觉执行与视觉会商分开；先完成 Codex 主导的 ego(lite) 真实页面循环，再初始化独立 visual conference。参与方必须看到当前截图/并列图/结构化记录，不能只读源码。
- 最终 ACCEPT 要求：三视口用户任务全部通过、结构化对账通过、参考并列审阅通过、全部开放 P0-P4=0、聚焦/全量前端测试与 build 通过、医学写作保护面无本任务写入、所有临时服务/浏览器任务空间清理或按明确理由保留。

## 9. 下一动作

本合同先经独立只读会商关闭 P0-P2 并冻结。冻结后建立 governed visual execution：准备/校验 synthetic fixture，启动隔离端口，用 ego(lite) 完成首轮基线捕获；按“测试→原图/并列审阅→修订→复测”循环，最后再做独立视觉会商。合同接受不等于视觉完成。
