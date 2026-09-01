# P10 RUX dashboard / inbox 测试隔离诊断

## 1. 任务边界

- 目标：定位 `tests/test_rux_monitoring_service.py` 中 dashboard
  `open_risk_count=0` 与 workbench inbox 无医学监查风险项的偶发失败。
- 允许改动：`tests/` 与本记录。
- 禁止改动：生产代码、实际运行库、原始来源文件。
- 诊断对象：测试运行库选择、并发 API 进程、测试导入顺序、资源生命周期与缓存。

## 2. 最小可重复证据

### 2.1 失败可独立复现

仅运行以下两个测试，无需联合测试或并发 API 请求即可稳定复现：

```bash
python3 -m pytest -q \
  tests/test_rux_monitoring_service.py::RuxMonitoringServiceTests::test_rux_dashboard_returns_real_project_metadata_without_mgk10_fallback \
  tests/test_rux_monitoring_service.py::RuxMonitoringServiceTests::test_workbench_inbox_projects_verified_rux_monitoring_risks \
  -vv
```

修复前结果：`2 failed`。dashboard 返回 `open_risk_count=0`，inbox
中不存在 `module=medical_monitoring,item_type=risk` 的项目。

### 2.2 导入顺序决定应用绑定的运行库

`tests/__init__.py` 在未显式指定 `WORKBENCH_RUNTIME_DIR` 时，会先创建全新临时
运行目录，并设置该环境变量。`services.api.app.main` 又会在模块导入时创建
`medical_risk_repository`、summary service 与 inbox service。因此：

1. `import tests` 后再导入应用：
   - 应用绑定 `/private/.../medical-workbench-test-runtime-*/medical_risks.sqlite3`；
   - 临时库中没有 RUX 快照；
   - `current_snapshot("proj_rux_03_002")` 返回 `KeyError`。
2. 先导入应用再 `import tests`：
   - 应用已经绑定实际运行目录；
   - 当前 RUX 快照为 `risksnap_816c2aef9e52befc0411`；
   - 仓储中有 16 个风险实例。

这解释了“普通脚本可返回 16，但 pytest 有时返回 0”的表象：两者并非读取同一
进程内的仓储对象。pytest 正确执行了测试隔离；旧测试错误地依赖了实际运行库
预先存在的快照。

## 3. 排除的假设

- **共享实际运行库被清空：排除。** 实际运行库的当前 RUX 快照仍为 16 条；
  失败 pytest 进程读取的是临时空库。
- **并发 API 进程覆盖快照：排除。** 两项测试在没有调用外部 API 的独立
  pytest 进程中稳定失败；`TestClient` 直接调用进程内 ASGI 应用。
- **SQLite 缓存或连接复用：排除。** `MedicalRiskRepository` 每次查询都会
  新建连接；summary 与 inbox 引用的是同一个进程内仓储对象。问题发生在
  仓储构造时选择的数据库路径，不是查询缓存。
- **FastAPI startup/shutdown 生命周期：排除为根因。** 不进入 lifespan 也能
  复现；通过显式监查运行命令生成快照后，同一 `TestClient` 立即返回 16。
- **inbox 过滤规则错误：排除。** 在临时库生成与当前适配器版本一致的快照后，
  inbox 可投影 16 个医学监查风险项；此前为空是因为没有快照，而不是版本过滤。

## 4. 最小测试修复

仅修改 `tests/test_rux_monitoring_service.py`：

- 新增 `_client_with_current_rux_snapshot()`；
- dashboard 与 inbox 两项测试在读取投影前，通过正式命令端点
  `POST /api/projects/proj_rux_03_002/modules/medical-monitoring/runs`
  在测试临时库生成或复用当前快照；
- 校验命令状态为 `snapshot_generated` 或 `current_snapshot_reused`，并要求
  `risk_count >= 3`；
- 未直接写 SQLite，未绕过生产服务合同，未改变 dashboard/inbox 生产语义。

该方式使每个测试在单独执行、任意导入顺序和联合执行时都自足，不再依赖开发机
实际运行库的历史状态。

## 5. 回归结果

### 聚焦节点

```text
2 passed, 10 warnings in 62.08s
```

### 完整 RUX 服务测试

```text
15 passed, 10 warnings in 101.63s
```

### 联合隔离回归

联合运行：

- `tests/test_runtime_directory_configuration.py`
- `tests/test_medical_monitoring_module_contract.py`
- `tests/test_workbench_inbox.py`
- `tests/test_rux_monitoring_service.py`

结果：

```text
60 passed, 10 warnings in 110.60s
```

警告均为既有 FastAPI `on_event` 弃用警告，与本问题无关。

## 6. 结论与后续规则

根因是测试隔离增强后，旧集成测试仍把“实际运行库已有 RUX 快照”当作隐式前置
条件。修复应保留 `tests/__init__.py` 的进程级临时运行库隔离，并让需要风险快照
的测试通过公开命令边界自行建立前置状态。不得通过移除隔离、指定实际运行目录或
复制实际数据库来让测试通过。
