# R1 医学监察员进度投影证据

日期：2026-08-09  
范围：隔离 `medical_monitoring_ai_native_r1` synthetic/offline POC。未运行 UI、服务、
真实 provider/harness/项目或 8911，未触碰医学写作与产品源码。

## 1. 已实现边界

新增 `audience_progress.py`，只调用 `Store.structured_progress()`、`get_manifest()` 和
`list_work_unit_runs()` 三个读接口。它不推进工作单元、不修改台账、不追加审计事件，也不
读取 capability runtime 的原始输出。

投影只返回：总体说明、已处理数、总数、百分比、总体进度文字、状态概览、阶段进度、
当前工作和最近动态。manifest revision、工作单元 ID、node、attempt、provider、model、
backend、hash、audit、原始 detail/log 和 execution identity 均不进入返回值。

## 2. 面向医学监察员的语义

- `pending`：等待开始；`running`：进行中；`passed`：已完成。
- `reused`：已沿用已有结果；`skipped`：本次无需处理；`not_applicable`：本研究不适用。
- `blocked`：暂时受阻；`failed`：未完成。
- 终态均进入“已处理”分母，但失败和阻断不会被写成成功。
- 重试只显示“正在继续处理”，不显示尝试编号或模型身份。
- 当前工作和动态只采用冻结 manifest 的中文阶段、工作说明、临床对象及受控模板。
- “正式事实”“候选信号”“只读xx”及技术日志类表达均失败关闭。

对象范围只接受受控临床范围；纯 ASCII 对象必须是含数字的临床编号。中文临床名称继续
可用。协议、网络地址、文件/目录路径、内部字段和未知 scope 均失败关闭。通用 scheme
检测覆盖大小写和单字符；`ALT:轻度升高` 等明确临床缩写由小型白名单保留。

## 3. 权威守恒与失败关闭

投影先调用权威结构化进度，再把 manifest 分母、work-unit 台账和权威分类逐项对账：

- work-unit ID 集、总数、终态完成数和各状态计数必须完全一致；
- running 列表必须与台账 running 集完全一致且不得重复；
- begin/retry 动态只能处于 running，complete 动态只能使用允许的终态；
- revision、计数、百分比、列表形状、时间和对象任一异常均拒绝展示。

真实 synthetic Store 探针确认投影前后 SQLite `total_changes` 与审计事件数不变。

## 4. 独立审阅闭环

独立 Luna CLI compatibility 会话 `019fe705-138e-7761-abf4-543376be45c6` 保持同一上下文
连续挑战，没有因延迟或 VETO 重派。它依次发现并推动封闭：

1. 内部字段后缀、unknown scope、retry 状态错配和重复 running；
2. URI、文件后缀、网络地址与相邻变体；
3. 大写相对路径/技术目录对象；
4. 中文紧邻协议、地址、绝对/相对路径及含中文 target 技术目录；
5. 大写和单字符 opaque scheme。

最终同会话对实现 SHA 和测试 SHA 做 hash-bound 复核，返回 **ACCEPT，P0-P4：0**；
其后仅为满足工作台 Ruff 移除测试 import 分组的一个空行，同会话再次核对最终 SHA、
focused 68 和 audience+authoritative 105，仍为 **ACCEPT，P0-P4：0**。

原生 Luna 当前会话能力探针未提供可创建的 Luna child handle，因此按全局合同使用
`codex exec -m gpt-5.6-luna` CLI compatibility route；没有替换为其他 Codex 模型。

## 5. 决定性验证

```text
audience progress focused: 68 passed
audience + authoritative progress: 105 passed
R1 core: 259 passed
AE/MH audience: 18 passed
Patient Journey: 16 passed
grouped runnable evidence: 293 passed
independent boundary probe: 41 cases passed
independent read-only/tamper probe: 39 checks passed
scoped Ruff: pass
compileall: pass (temporary bytecode cache removed)
8911 listener: none
```

最终冻结 SHA-256：

- `audience_progress.py`：`97e9fa8256b188dcd0c4be6c0867ee2a13668e5dca3f08df25e905908e82617e`
- `test_audience_progress.py`：`b89c010dd1a7cbafe6c90c43fabce5943b766e6b6a70bf916b646edd58144d4f`

本切片产生的临时 compile cache 和两个 audience bytecode 文件已精确清理；审阅提示和
VETO/ACCEPT 证据属于审计链，不作为“旧缓存”删除。

## 6. 尚未声称

- 本结论只接受 isolated synthetic/offline R1 audience-progress 切片，不代表 R1 总体、
  产品集成、真实项目或商业化接受。
- 尚未实现后台 controller 自动监听 capability attempt 并推进 work unit，也未实现 UI
  轮询、后台通知、真实进度条或浏览器验收。
- `FOO/BAR2` 这类含数字、无技术目录词段且格式合法的字符串，仅凭字符串无法绝对判定
  技术或临床含义；该边界记录为残余风险，不以无限枚举替代上游受控 manifest。
