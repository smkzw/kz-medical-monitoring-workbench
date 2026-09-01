# Codex Conference Review: safety_pv_unified_projection_20260713

Date: 2026-07-13

## Verdict

当前“统一风险只读投影”切片通过，后续迁移带明确条件。MiniMax-M3和Kimi-K2.7-Code均完成同一会话三轮；Qwen3.7-Plus首轮路由在三次HTTP 500重试后终止，未形成可续接三轮会话，不计为有效参与者。Codex用双真实项目、源码、测试和内置浏览器完成最终裁决，不把该切片误写为Safety/PV整体完成。

## Boundary Compliance

- 视觉会商由Codex直接主持，无Hermes分会场主席。
- MiniMax与Kimi只读审阅指定源码和截图，没有修改生产代码，也没有声称最终浏览器验收。
- Qwen输出保留为失败路径证据；虽包含首轮和部分自我修订内容，但runner明确记录`no usable Hermes session was established`，不伪记为三轮完成。
- 暂停时终止的Kimi 2.6替代runner没有形成完整可验收输出，不计入会商结论。

## Participant Outputs Reviewed

- `aishuo/MiniMax-M3`：接受默认风险投影、PV文档并列工作区、桌面高密度表格和风险行回跳；否决新增URL hash状态、第三个“原始资料登记”标签和另建`useRiskIndex`抽象，这些不符合当前路由和最小变更原则。
- `buddy/kimi-k2.7-code`：接受统一`risk_instance_id`、只读投影、同一状态所有权、精确打开医学监查证据和明确空/加载/错误状态；否决将Safety/PV注释发展为第二状态机。
- `opencode-go/qwen3.7-plus`：仅作为失败路径参考。其“个体风险与聚合信号不可强行合并”的批判有医学逻辑价值，但其垂直折叠方案与用户批准的双工作区方向冲突，且没有有效三轮会话支持。

## Hermes Sub-Venue Review

本任务为视觉会商，不设Hermes主席。MiniMax和Kimi的共识是：首屏必须回答当前项目有哪些Safety/PV相关医学风险，PV文件审阅保持独立工作面，风险处置回到医学监查且共享同一风险身份与审计。

## Main-Venue Codex Review

裁决后的实现基线：

1. Safety/PV默认显示统一风险仓库中带`Safety/PV关注`标签的只读投影。
2. 首屏保留5项摘要和9列桌面表格，不复制医学处置控件；点击“打开”进入医学监查同一`risk_instance_id`。
3. “PV文件医学审阅”作为并列工作区保留，但当前旧候选信号与五动作仅属过渡实现，后续需冻结写入并迁移为真正的DSUR/SAE/2.7.4/ISS文档审阅。
4. 项目切换采用递增请求序号，禁止旧项目响应覆盖新项目；精确回跳等待实例ID匹配，不按同一受试者近似选中其他风险。
5. CM继续只表示非试验用药；试验药物与剂量调整保持独立数据域。

## Codex Independent Verification

- 聚焦测试：Safety/PV投影5项、统一风险4项、TFL/Safety来源准入6项，共15项通过。
- 前端生产构建通过，仅保留既有Vite大包警告。
- RUX-03-002：2048x1024显示14条Safety/PV关注风险、14条高风险、7个中心、12名受试者；页面和表格横向溢出均为0。
- MY009-UC：2048x1024显示7条Safety/PV关注风险、7条高风险、5个中心、7名受试者；页面和表格横向溢出均为0。
- MY009同一受试者存在两条不同风险时，从投影点击“S01003 临床意义实验室异常需核对AE/复测”，医学监查选中行和证据工作区标题均为该风险，不误选“S01003 试验药物服用记录需核对”。
- PV文件医学审阅工作区可打开；修复文档表复合key后，当前浏览器控制台error为0。
- 视觉证据：`visual_sources/safety_pv_projection_rux_2048x1024.png`和`visual_sources/safety_pv_projection_my009_2048x1024.png`。

## Final Decision

会商review gate可对“Safety/PV统一风险只读投影”通过。Safety/PV整体仍未完成：严格只读后端接口、旧候选信号写状态冻结、通用PV文档审阅契约、风险级批次diff和非Query处置终态继续作为后续P0/P1，不得以本次投影验收替代。
