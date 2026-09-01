# R7 Slice-07C-4 中文产品闭环接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_07C4_SYNTHETIC_VISUAL_LIMITED`

## 接受范围

- synthetic/offline 三模式中文四步向导、监查历史、后台进度与结果入口闭环；
- 项目/中心默认看板及“知情同意→筛选→治疗→研究状态”阶段流向；
- 受试者 8 域访视轴、Journey/Profile/Timeline、风险锚点与来源证据返回；
- 1280×800、1440×900、1920×1000 桌面 ego(lite) 视觉与交互；
- 当前项目/中心/受试者公开身份范围、离页恢复、中文、焦点和页级溢出。

## 纠偏闭环

1. D1：声明 `entryLoading` 状态并纳入加载门禁；真实点击“查看本次结果”产生 result-entry 请求、切换 result-context、0 runtime exception。
2. D3：中心结果身份条改为当前中心标签；中心夹具按 `site_ref` 重算中心、受试者、风险、覆盖与阶段流向。
3. O1：subject-workspace 合成响应按 subject/site/spine 过滤风险与锚点；受试者 001 页面不再出现受试者 002/中心 010。
4. O2/O3：风险标题与关键 subject/site 元数据允许双行，1280 下关键医学身份完整；冗余变化原因尾部省略由独立 `新增` 标签补足，作为非阻塞紧凑布局接受。

## 决定性证据

- 医学监查前端全部 52 个 `.test.mjs` 文件通过；
- 后端 R7/R5 相邻组合 `129 passed`；
- 最终夹具合同 `15 passed`，真实前端公开信封合同 `13/13 passed`；
- Vite build 与 Python compileall 通过；
- ego(lite) 关键证据位于 `artifacts/mm_r7_slice07c4_product_loop_ego_20260829/evidence_1440/` 与 `evidence_w03/`；
- 独立 Gemini 视觉会商 PASS；Codex 亲自打开最终 1280/1440/1920 截图复核；
- 8978、8911、5174 最终无监听。

## 边界

本接受仅覆盖 R7 Slice-07C-4 synthetic/offline 用户产品闭环与桌面视觉。没有运行五个真实项目、真实模型医学分析或真实服务；不代表医学结论准确性、跨项目泛化、R7 总体、R8、商业化或监管级接受。医学写作子系统未被修改。

## 下一安全动作

07C-4 执行审阅门禁、执行审计、独立视觉会商及会商审阅门禁均已通过，执行包已可恢复归档。会商临时会话 ID 不在当前 Hermes 状态库中，故没有可归档会话，正式会商输出与审阅证据仍完整保留。

下一步按 R7 计划完成阶段复盘并界定下一切片合同。继续保持 8911 与真实项目停止；下一阶段开始前重新读取当前 AGENTS、计划、LOOP ledger 和本接受记录，不把本次 synthetic/offline 接受外推为真实医学质量或 R7 总体接受。
