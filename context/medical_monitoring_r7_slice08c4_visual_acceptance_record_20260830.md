# R7 Slice-08C-4 ego(lite) 桌面视觉接受记录

日期：2026-08-30  
决定：`ACCEPT_R7_SLICE_08C4_SYNTHETIC_VISUAL_LIMITED`

## 已接受结果

- 项目/中心默认结果页在 synthetic/offline 条件下形成面向资深医学监察员的中文宽屏看板：五项本轮连续性摘要、受试者四阶段流向、同源明细表、高中风险定位和医学旅程入口均可直接查看。
- Patient Journey 保留唯一横向访视/实际日期轴；事件与风险变化仍按同一身份落在轴上，详情通过 overlay/push 抽屉查看，没有退回平铺卡片列表。
- 当前生产视觉边界明确为 1920×1080 至 4K 宽屏电脑；1280/1440 仅作为韧性证据，不再产生移动端或窄屏专项义务。
- R10 的 1920×1080 overview/site 将下一个中心覆盖模块完整放到折叠线下，不再出现半行、半字或模块残片；首屏保留完整五 KPI、四阶段流向、11 列表头、风险定位和 Journey 入口。
- 当前前端中文未出现 `正式事实`、`候选信号`、`只读xx` 等内部/工程化标签；可见变化闭集保持 `新增/升级/持续/降级/关闭/重开/需重新判断`。

## 决定性证据

- ego(lite) 原生截图：`artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_revised/1920/01_overview.png`、`1920/02_site.png`，均为 1920×1080。
- 参考/产品同画布：`collage/overview_flow_strip.png`、`1920_overview_baseline_vs_r10.png`、`1920_site_baseline_vs_r10.png`。
- 结构化当前事实：`FINDINGS_revised.json` 为 `p0_to_p4_clear=true`、`open_defects=[]`；overview/site `centerFoldClear=true`，当前 packet 为 `ego_only_r10`、任务空间 `mm08c4 w03 r10`。
- Codex 独立打开最终原图并确认可见像素；没有用结构化全绿替代视觉判断。
- 独立视觉会商复用 Cursor Grok session `01a04f3f-8f1b-7000-a20e-989c45d36cf4`，八轮逐项复核后在 R10 返回 `ACCEPT_VISUAL`；当前桌面 P0/P1/P2/P3/P4 为 0/0/0/0/0。
- 聚焦 R5/R7 23/23、医学监查前端 61/61 test files、Vite build 1981 modules；8911/5174/8984 无监听，ego task spaces 为空。
- conference validate 与 review-gate 均通过；execution audit 本体通过。带 `--require-conference` 的 execution audit 因 visual conference 采用独立 task id 而报告 `conference_status=not_initialized`，该工具限制未被伪造为通过，改以独立 conference validate/review-gate 作为会商治理证据。

## 路由与会商事实

- visual conference 的 Grok Build primary 不可用，按冻结链使用 `pi/cursor/cursor-grok-4.6:high`，未静默替换。
- worker_03 R2-R9 使用原 Cursor CLI session；R10 旧会话继续失败后，guard 记录并使用 `pi/openai-codex/gpt-5.6-luna` fallback 完成，不将其冒充 Cursor 输出。
- Hermes workflow guard 管理 execution/conference packet、route identity、validate/review gate；Codex保留最终源码、截图、视觉和用户交付责任。

## 医学写作保护

产品修改局限于医学监查 R5/R7 前端、相关测试与 08C-4 synthetic fixture/evidence。医学写作保护面在执行时段内没有新 mtime；未修改医学写作产品源码。

## 接受边界

本记录只接受 Slice-08C-4 synthetic/offline 桌面运行时视觉。它不接受真实项目、真实模型医学质量、4K 实机专项截图、完整可访问性认证、R7 总体、R8、生产、监管或商业化。

## 下一阶段

进入 Slice-08D 三模式综合回归：按冻结 Slice-08 v0.2 合同验证日常 full/incremental、锁库前 full 修订、核查前 fixed-total 的 carry-forward、hash-seed/优化级别确定性、故障恢复、相邻回归和独立接受。08D 不新增 UI 设计，不运行五个真实项目，不启动 8911/5174，不修改医学写作。
