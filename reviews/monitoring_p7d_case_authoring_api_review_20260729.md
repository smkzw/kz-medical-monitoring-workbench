# P7D 四类真实用例产品入口验收

日期：2026-07-29  
结论：源码合同通过；真实运行态待旧 V7 队列排空并重启后复验。

## 已关闭缺口

- 布尔 gold case 可通过正式 API 显式登记 `positive`、`negative` 和 `boundary`。
- `expected_match=true/false` 与正反标签的一致性继续由封闭底层模型验证。
- 不可判定输入通过独立 diagnostic-case API 登记，保存为
  `RuleDiagnosticCase`，不会伪装成 negative。
- 两类入口都要求精确规则修订、当前项目 shadow 规则包、EDC listing 权威来源、
  来源/批次修订、真实行定位与来源行绑定。
- 响应只返回用户所需的案例身份、覆盖标签或预期诊断，不暴露内容哈希。

## 验证

- Python 编译通过。
- `test_monitoring_protocol_rule_api.py`
- `test_monitoring_rule_authoring_service.py`
- `test_monitoring_gold_shadow_p7c.py`
- `test_monitoring_protocol_rule_repository_hardening.py`

组合结果：`42 passed`。

API 测试覆盖从方案登记、事实确认、规则确认、shadow 启动，到正例、边界反例、
不可判定诊断例登记、影子运行、结果确认和发布的完整产品链路。

## 剩余边界

- 当前 8921 仍运行旧 V7 服务进程，新入口尚未加载。
- 未使用真实 RUX/MG-K10 数据登记任何 gold 或 diagnostic case。
- API 重启后必须先用隔离测试项目验证运行态迁移和入口，再进入真实项目候选扫描。
- 真实数据若不存在某类用例，仍必须保持发布阻断，不能为满足覆盖门制造记录。
