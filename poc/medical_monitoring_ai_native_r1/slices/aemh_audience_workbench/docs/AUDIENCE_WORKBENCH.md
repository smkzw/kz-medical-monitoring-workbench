# R1 Slice 3 — AE/MH 受众看板（worker 02）

## 范围

本目录实现 `file://` 可用的中文交互单页看板，只读消费 `window.MM_R1_DATA`。

- UI 归属：`index.html`、`styles.css`、`app.js`、`assets/logo_bot.svg`、本说明
- 数据归属：`data/mm_r1_data.js`（worker 01 / `build_data.py`），UI 不创建、不修改、不内嵌受众 mock

## 数据合同（UI 校验）

`app.js` 在启动时校验 `window.MM_R1_DATA`，缺任一项即显示 `.kz-error` 并隐藏主界面。
对齐 worker 01 `docs/DATA_CONTRACT.md`：

| 字段 | 要求 |
|---|---|
| `fixture_marker` | 必须为 `SYNTHETIC` |
| `project_dashboard` / `site_dashboards` / `subject_profiles` / `subject_timelines` | 对象 |
| `source_rows` | 以 `SYNTHETIC\|snapshot=...\|table=...\|row=...` 为键；行含 `raw_values`、`polarity` 等 |
| `delta_groups.groups` | 含 current/new/escalated/carry_forward/resolved/not_evaluable |
| `run_lineage` / `snapshot_lineage` | 用于页眉血缘（可选缺失时回退 project_dashboard） |
| `progress.detail_nodes` | 静态完成进度 |

可选渲染：`disclaimer`、`ai_boundary`、`queries`、`counterevidence`、`coverage`、`analyses`。

## 交互合同落点

- 变化优先：默认只展示中高严重度与有意义生命周期/delta 变化；可关闭后看低风险细节；主列表不人为截断为 3–5 条，改用每页 8 条分页
- 下钻：项目 → 中心 → 受试者 → 证据抽屉 / Query 三件套；面包屑与“返回上层”保留上下文
- Profile / Timeline：同一 `temporal_spine_id` + 同一时间窗控件；正式事实=实线方块，漏报候选=虚线圆；颜色不单独承担语义；提供 `.kz-legend`
- 证据抽屉：展示数据批次、中文表名、记录编号、受试者、中心、日期、证据作用与去除合成控制字段后的原始源字段；底层稳定定位符仍保留在数据和交互绑定中
- Query：依据 / 发现 / 行动项三件套；无提交/分派/“人工复核未完成”工作流
- AI 边界固定文案：`AI辅助定位证据与风险，医学经理终审`
- 进度条：渲染载荷中的 completed/total/nodes/current_work；静态 POC 不伪造异步加载
- 完成态进度默认压缩为“完成数/总数 + 可展开处理步骤”，不挤占风险首屏
- 用户语言层：界面不显示 workflow 枚举、内部身份哈希、绘图参数、worker/build 名称或 synthetic 控制字段；风险类型、严重程度、生命周期、事件和数据表均以原生中文展示
- Query 绑定：仅按明确 `risk_identity_keys` 或共享证据定位符关联，不按受试者猜测；只有真正绑定的风险卡显示 Query 操作
- 空态：筛选无结果时解释原因并提供重置
- 无障碍：`:focus-visible`、Tab 左右切换、Escape 关抽屉、抽屉焦点陷阱与恢复
- 冻结态：`prefers-reduced-motion`、`data-export=true`、`data-qc=true` 关闭动效

## 视觉约束

- 本地模块化资源；无 CDN / 远程字体 / 远程脚本 / fetch
- Logo：仅 `assets/logo_bot.svg`（自批准缓存复制，`viewBox="0 0 121 25"`）
- 白/浅表面为主；橙 `#FF9900` 克制；红 `#C00000` 仅风险语义
- 中文字体栈以 `"Microsoft YaHei","PingFang SC"` 开头；数字 `tabular-nums`
- 组件类名 `kz-` 前缀；时间脊使用 HTML/CSS 标记，**零业务 SVG 图**（Logo SVG 除外），便于 worker 03 对业务图做显式 zero-SVG 观察

## 打开方式

```text
file://.../poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/index.html
```

需同目录存在 `data/mm_r1_data.js`。缺失时页面应显示恢复性错误，而不是空白或假数据。

## worker 02 自检（允许项）

- 静态语法：`node --check app.js`（若本机有 node）
- 占位符/违禁可见串扫描：`&&`、`@@`、模板字面量残留、`AI自动判断`、`AI替代医学判断`
- 不安装依赖、不启服务、不跑 Playwright（属 worker 03 / Codex）
