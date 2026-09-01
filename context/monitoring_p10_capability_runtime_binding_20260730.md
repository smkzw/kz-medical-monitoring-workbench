# 医学监查 P10：Timeline/Profile 能力边界运行态接线

日期：2026-07-30  
状态：代码与聚焦回归完成；稳定 API 待字段映射队列适宜窗口受控重启

## 1. 问题

前一切片已经在 `BoundMonitoringProjectAdapter` 中实现 Timeline 与 Patient Profile 的
能力受限投影，但主运行态没有绑定正式映射的 capability resolver。因此，即使项目字段
映射已经激活，受限日期、CTCAE 或量表血缘也不会自动反映到受试者视图。

直接在启动时绑定 resolver 还有一个兼容性边界：RUX、MY009 和 MG-K10 目前存在基于真实
原始文件的来源适配器，而正式项目映射尚未激活。如果把“尚无活动映射”当作能力失败，
现有受试者视图会错误返回 404。

## 2. 实现

- 主运行态把 `monitoring_mapping_activation_service.require_monitoring_capability`
  绑定到 `monitoring_project_registry`。
- 尚未存在首个活动映射时，adapter 明确回到当前来源适配器的既有只读视图；它不生成
  capability 快照，也不声称正式映射已经 ready。
- 一旦活动映射存在，每次 Timeline/Profile 请求都读取该不可变映射的能力快照：
  - 精确时间受限时保留来源日期，清除研究日及访视偏差推断；
  - 量表复算受限时保留来源值，清除标准化值和相对基线推断；
  - CTCAE 受限时保留实验室原值，清除自动 CTCAE 分级；
  - Timeline 与 Patient Profile 两项主能力同时受阻时返回明确的 HTTP 409，不返回空页面
    冒充成功。

## 3. 验证

- `tests/test_monitoring_project_capability_guard.py`：3 passed。
- Ruff：通过。
- Python 编译：通过。
- RUX/MY009/MG-K10 相邻服务联合回归共 38 项中 36 项通过；2 项 MY009 dashboard/inbox
  断言因共享真实运行库当前无 MY009 风险快照而失败，与本切片受试者视图变更无关。
  该测试隔离缺口需在发布回归前收口，不能将共享运行库状态当作固定测试夹具。

## 4. 运行态边界

当前稳定 API 正在处理三个真实项目的独立 AI 字段映射队列。为避免再次制造遗留 lease，
本切片不立即重启 API。待正式映射进入确认/激活窗口时进行一次受控重启，并完成：

1. 激活前真实受试者视图仍可读取；
2. 激活后按项目能力快照产生 full/restricted 投影；
3. 双主能力受阻时 HTTP 409 的浏览器错误态；
4. 页面不展示内部 capability 日志，只在确实影响当前视图时给出简洁限制说明。
