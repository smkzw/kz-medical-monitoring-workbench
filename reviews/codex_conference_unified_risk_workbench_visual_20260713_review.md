# Codex Conference Review: unified_risk_workbench_visual_20260713

Date: 2026-07-13

## Verdict

通过会商并带实施条件。三轮有效输出足以支持当前风险 Checklist 与原位证据工作区；Qwen 和 MiMo 路线均在首轮后终止，已按规则启用 Kimi 2.6 三轮替代。Codex 不接受参与者中与产品边界、品牌视觉或桌面优先要求冲突的建议。

## Boundary Compliance

- MiniMax-M3、Kimi-K2.7-Code、Kimi-K2.6 均完成同一会话三轮。
- Qwen3.7-Plus 与 MiMo-V2.5 未建立可续接会话，记录为终止失败，不伪造后续轮次。
- 三个有效参与者均保持只读，没有修改生产源码，也没有声称最终浏览器验收。
- 参与者视觉工具超时，像素级结论均由 Codex 在内置浏览器中独立完成。

## Participant Outputs Reviewed

- `aishuo/MiniMax-M3`: 接受 12 列高密度清单、原位证据标签、来源定位和最多三标签的方向；否决其“Safety/PV 不共享风险ID”和将 CAS 误解为注释系统的假设。
- `buddy/kimi-k2.7-code`: 接受范围/筛选/选择状态模型、八分支处置、Timeline/Profile 焦点上下文；否决隐藏六列、棕/奶油色 Timeline、`sessionStorage` 跨标签共享等建议。
- `buddy/kimi-k2.6`: 接受桌面分栏/叠加工作区、项目级状态隔离和 Safety/PV 只读投影；否决为移动端缩减功能、缩写“医学严重度”和未验证即引入 `react-window`/Radix 的建议。

## Hermes Sub-Venue Review

视觉会商采用 Codex 直接主持，无 Hermes 分会场主席。替代参与者只补足缺失的第三视角，不覆盖 MiniMax/Kimi 的独立意见。

## Main-Venue Codex Review

裁决后的实施基线：

1. 宽桌面保留完整 12 列，1440px 允许表格内部横向滚动，不删除功能。
2. 使用现有白/灰/康哲橙设计系统和准确 CMS Logo，不采用棕/奶油色。
3. 风险行打开同页叠加证据工作区；风险处置、Subject Timeline、Patient Profile、AE/MH 和来源证据可直接切换。
4. Safety/PV 是同一风险对象的标签与投影，必须共享 `risk_key`/`risk_instance_id`、来源和处置审计。
5. 八类处置分支保留；只有“向中心发起 Query”分支允许生成 Query 草稿。

## Codex Independent Verification

- 1920x1080 内置浏览器：页面级横向溢出为 0；风险表格 `clientWidth=1687`、`scrollWidth=1687`。
- RUX-03-002：真实 241 例、16 条项目医学风险、16 条可处置工作项；受试者筛选 S01017 后显示 2/16 条。
- MY009-UC：真实 26 例、10 条项目医学风险，覆盖用药依从性与临床意义实验室异常，未复用 RUX 规则。
- 证据叠加层：1920 桌面为 1320x560；五个标签均可切换；Timeline 显示真实事件标题，Patient Profile 显示 7 个真实趋势指标及异常标记。
- 八分支验证：切换为 `safety_pv_collaboration` 后 Query 文本框禁用，并显示“不生成中心 Query”的边界提示。
- 聚焦测试：34 项通过；前端生产构建通过，仅保留既有 Vite 大包警告。
- 浏览器 QC 捕获并修复相同快照并发计算因 `created_at` 不同而误报冲突的 500 缺陷。

## Final Decision

会商完成，当前 Checklist/证据工作区实现可继续迭代。尚未完成的验收条件为：按 `source_locator` 精确高亮 Timeline/Profile 点位、叠加层内完整图形嵌入、Safety/PV 摘要投影和 PV 文档审阅工作区；这些进入后续任务，不将本次裁决误写为整个系统完成。
