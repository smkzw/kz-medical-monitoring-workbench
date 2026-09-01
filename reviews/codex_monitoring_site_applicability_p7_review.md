# Codex Review: monitoring_site_applicability_p7

Date: 2026-07-29
Accepted execution handoff: `runs/cursor_monitoring_site_applicability_p7_fallback.md`

## Verdict

P7A 的方案适用性 assignment 数据模型、状态机、精确解析器、发布门和 API 通过针对性验收，可进入逐记录运行时集成。未发现需要回退执行切片的阻断项。

## Boundary Check

- 实现仅触及合同声明的医学监查规则、仓储、服务、路由与测试文件。
- 未修改医学写作、共享独立 AI 配置或前端。
- 首选与第一回退均未建立有效写入会话；只有最终执行回退产生代码变更。

## Codex Verification

- assignment 不可变主体与 `candidate -> confirmed -> retired` 状态分离，状态变更使用 `state_version` CAS。
- 中心编号和受试者编号仅作精确标识符处理并保留前导零。
- 适用区间要求完整 ISO 起止日期与可读证据正文；公开载荷先显示证据正文，再显示定位信息，并隐藏来源内容哈希。
- 同一精确范围的已确认区间重叠会在确认时拒绝；受试者级命中优先于中心级命中。
- 仅已确认 assignment 且其方案版本仍为 `confirmed/site_specific` 时可解析；candidate 与 retired 均不参与。
- 未解析、冲突、无效日期均返回稳定诊断；不存在方案日期、伦理日期、培训日期、首次观察日期或文件名兜底。
- `site_specific` 规则包发布除原有 shadow/确认门外，还要求该方案版本至少存在一个已确认 assignment。
- `project_effective_confirmed` 既有路径未被改写。
- 目标与相邻规则生命周期测试：`71 passed in 2.66s`。

## Delegated-Agent Output Review

交接明确指出逐记录运行时集成尚未完成，没有把“前端可见”或“存在一个 assignment”误报为项目级覆盖完成。其剩余风险判断与源代码一致。

## Residual Risk

- “至少一个已确认 assignment 可发布”只证明该版本在项目内存在可用范围，不代表所有中心、受试者和日期均被覆盖。运行时必须逐记录解析，未覆盖记录关闭失败；P7B 正在处理。
- RUX、MG-K10、MY009 现有原始资料不足以证明全项目统一启用日期。不得为演示伪造适用区间；真实 assignment 仍需用户基于可读来源明确确认。
- 当前长驻 API 尚未重启，因此新端点只在源代码与测试态通过；待旧版字段映射运行完成并采用后统一重启验收。
