# R7 Slice-08C-2 项目/中心连续性前端纵切接受记录

日期：2026-08-29  
决定：`ACCEPT_R7_SLICE_08C2_SYNTHETIC_LIMITED`

## 已接受结果

- R7 公开结果客户端支持 continuity GET，仅传可选 `site_ref` 并透传取消信号。
- 前端严格校验响应身份、字段闭集、九项计数、顺序、截断、中文枚举、摘要 digest 与内部字段泄漏；异常时整块失败关闭。
- 项目/中心看板前展示“本轮变化”、五项摘要、默认中高风险列表、变化/对象/等级/需重新判断/受试者筛选；continuity 加载或失败不阻塞既有看板。
- Journey 入口同时绑定当前 overview subject 与 matched R5 subject-flow 的同一 subject/site/spine，要求 R5 Journey 窗包含当前风险窗口；来源入口只复用当前行 `risk_instance_ref + source_locator_ref`。
- `reopened` 缺少当前风险等级时严格失败关闭；`needs_rejudgment` 仍可显示“等级变化待确认”。
- 项目、结果上下文、中心或视图变化会取消旧请求并清空旧比较，禁止旧结果闪回。

## 决定性证据

- 独立会商同一 Cursor session 三轮：Round 1/2 提出并复核纠偏，Round 3 无 P0–P2并建议接受。
- Codex 最终树：12 个 R7 suite 合计 1136 checks 全通过；6 个相邻 R5 suite 全通过；Vite 1977 modules build 通过。
- 独立反例：`reopened + severity_after_text=""` 返回 `ok=false`。
- 8911/5174 无监听；未启动服务、浏览器、真实项目或模型。

## 医学写作保护说明

本切所有产品写入均在 `frontend/src/features/medical-monitoring/r7/`，医学写作路径在任务时段内无新 mtime。历史冻结的 542 文件聚合已与当前并行树不一致；当前按同一算法观察为 445 文件、SHA-256 `59dd4628eeedd376ab60e54806d0b9eeb3486ba444b5316fcfef8f9829863299`。该漂移发生在本切任务时段之前，不能由本切归因，也不伪称旧聚合仍通过。下一切片开始与结束均以当前 445 文件基线复核，若并行医学写作继续变化则单独标记为外部并行变更。

## 接受边界与下一安全动作

本记录仅接受 synthetic/offline 08C-2，不接受 08C-3 Journey 变化标记、详情抽屉、视觉质量、ego(lite) 三视口、真实项目/模型医学质量、R7 总体、生产或商业化。

下一安全动作：按 v0.1 §8 与 v0.2 §19 冻结 08C-3 最小合同，先实现单条横向 Patient Journey 访视轴上的本轮变化标记、八类事件图标与 overlay/push 详情抽屉，再做离线交互/可访问性回归；仍不启动服务、浏览器或真实项目。浏览器与专项视觉统一留到 08C-4。
