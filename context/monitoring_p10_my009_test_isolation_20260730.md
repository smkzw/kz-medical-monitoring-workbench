# MY009 dashboard / inbox 测试隔离收口

日期：2026-07-30  
范围：仅医学监查测试与测试辅助逻辑；未修改产品服务、真实 runtime、医学写作或 protocol preparation 前端。

## 1. 问题

以下两项测试会随共享真实运行库状态发生非确定性失败：

- `test_my009_dashboard_reports_real_first_batch_and_monitoring_counts`
- `test_my009_workbench_inbox_keeps_source_grounded_monitoring_items_in_cross_module_inbox`

失败表现为 dashboard 的 `open_risk_count == 0`，且统一 inbox 中没有
`medical_monitoring / risk` 条目。

## 2. 根因判定

### 直接根因：测试未隔离

两项测试通过全局 FastAPI `app` 读取 dashboard 和 inbox，但没有为本测试建立独立的
MY009 风险快照。两个读接口的风险权威来源均为持久化 `MedicalRiskRepository`：

- dashboard 通过 `MedicalMonitoringSummaryService` 和当前风险快照计算开放风险数；
- inbox 通过 `WorkbenchInboxService` 投影与当前适配器
  `source_revision / rule_profile_revision / engine_version` 一致的风险快照。

共享真实 runtime 当前没有符合上述身份的 MY009 风险快照，因此产品返回 0 风险是符合
读模型合同的空态，不是产品逻辑错误。

### 次生表现：顺序和外部状态依赖

旧测试只有在其他测试或人工流程预先向共享 runtime 写入了当前 MY009 快照时才会通过；
当快照被清理、替换或版本变化时便失败。因此其表现具有顺序依赖，但顺序依赖是“未隔离”
的结果，不应通过固定测试顺序解决。

### 排除：产品读接口错误

产品设计明确要求 dashboard/inbox 只读持久化快照，不能在 GET 请求内临时枚举受试者并
重新执行风险规则。将“无快照”改为临时计算会破坏来源版本、规则版本、引擎版本和处置状态
的一致性，因此未修改该产品行为。

## 3. 最小修复

仅修改 `tests/test_my009_monitoring_service.py`：

1. 增加类级惰性临时 `MedicalRiskRepository`，数据库位于
   `TemporaryDirectory`，类测试结束后清理。
2. 使用产品现有 `MedicalMonitoringRunService`、真实
   `MonitoringProjectRegistry` 和真实 MY009 适配器生成快照；未手工构造风险、未伪造
   生产响应。
3. 仅在两个 API 断言执行期间，原子替换以下三个只读投影引用：
   - `main.medical_risk_repository`
   - `medical_monitoring_summary_service.risk_repository`
   - `workbench_inbox_service.medical_risk_repository`
4. 上下文退出后自动恢复全部全局引用。原有风险数、来源 locator、状态、项目身份和禁止
   泄露本地路径等断言全部保留，没有放宽。

## 4. 验证

### 失败复现

修复前定向运行两项测试：`2 failed`。

### 定向与顺序隔离

- 两项按原顺序运行：`2 passed`
- 两项按反向顺序运行：`2 passed`
- dashboard 单项独立进程：`1 passed`
- inbox 单项独立进程：`1 passed`

### 真实 runtime 未被修改

在独立运行 inbox 测试前后计算真实
`runtime/medical_risks.sqlite3` SHA-256：

`0a8a9095b75b473f3b59b38c3767c00aa89dab5967e64161a3b045c4740e4ffd`

前后完全一致。

### 相邻回归

联合运行：

- `tests/test_my009_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `tests/test_source_manifest_dashboard_approval_overlay.py`
- `tests/test_medical_monitoring_module_contract.py`

结果：`58 passed`。

静态检查：

- `.venv/bin/python -m ruff check tests/test_my009_monitoring_service.py`
- 结果：`All checks passed`

运行中仅出现既有 FastAPI `on_event` 弃用提示及 openpyxl 页眉页脚解析提示；没有新增失败
或本切片引入的警告。

## 5. 残余风险

- 测试通过短生命周期 patch 替换模块级只读依赖，适用于当前串行测试运行方式。若未来在
  同一 Python 进程内启用线程级并发测试，应进一步把风险仓库改为 app factory 或显式
  dependency override，以避免不同测试线程同时修改模块级引用。
- 真实 MY009 原始 listing 或方案文件不存在时，测试类继续按既有规则 skip；本切片没有
  改变真实资料可用性门禁。
- 本修复仅解决测试隔离，不为共享真实 runtime 生成风险快照，也不改变产品上线前仍需
  通过正式运行链路生成、确认并激活快照的要求。
