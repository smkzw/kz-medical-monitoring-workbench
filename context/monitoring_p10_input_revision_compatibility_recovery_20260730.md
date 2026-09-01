# 医学监查 P10 输入修订兼容性恢复

## 1. 事件与影响边界

- 为规则模板建议增加空值 `fact_revision` 后，旧作业持久化的
  `input_revision_json` 不含该字段，而新模型序列化会补出空字段，导致同一真实输入被
  计算为不同哈希。
- 运行态因此把旧作业误标为 `stale_input`，并在一次正式重试中创建了新的重复合同：
  RUX 字段映射 175 个、MY009 方案主题 8 个。
- 未修改来源、候选正文、用户决定、正式 mapping 或规则；事件只影响任务状态、候选
  proposed/superseded 状态和重复队列。

## 2. 恢复设计

1. 空 `fact_revision` 不参与哈希；非空事实修订仍严格参与哈希，保证新增规则模板作业
   对事实版本敏感。
2. `retry_terminal` 接受同哈希 `stale_input`：
   - 已有候选的旧完成任务恢复为 `completed`，并仅恢复由系统技术性 supersede 的
     proposed 候选；
   - 无候选的任务进入 `queued`；
   - failed/blocked 始终重新排队，不因残留候选误判完成；
   - 当前输入哈希不同则继续拒绝。
3. 字段映射正式 `retry_failed=true` 同时处理 stale 状态。
4. 方案准备的状态聚合只使用“当前模型重算哈希等于持久化哈希”的兼容作业，避免按
   创建时间选中后来误建、已退役的任务。
5. 所有业务恢复只走正式 API；运行数据库只作只读核对。

## 3. 验证与运行证据

- 恢复前使用 SQLite 在线备份：
  `runtime/backups/medical_monitoring_ai_pre_compat_recovery_20260730_053946.sqlite3`，
  `PRAGMA integrity_check=ok`。
- 聚焦兼容性测试 42 项通过；医学监查 AI、方案准备、规则模板与方案规则相邻合同
  327 项通过；Ruff 与 `py_compile` 通过。
- 稳定 API 于 `127.0.0.1:8911` 启动，产品独立 AI 为已配置的综合 AI profile，
  `codex_runtime_dependency=false`；规则模板三条正式路由存在。
- 三项目字段映射正式恢复：
  - RUX：175 个当前 V13 作业，响应时 116 completed / 59 queued；
  - MG-K10：150 个，133 completed / 17 queued；
  - MY009：148 个，55 completed / 93 queued。
- 误建的新哈希任务全部保持 `stale_input`，不会再次调用模型。
- 方案准备正式恢复：
  - RUX 8/8 当前合同 completed，候选待审；
  - MG-K10 8/8 当前合同 queued；
  - MY009 8/8 当前合同 queued，另 8 个误建合同 stale。

## 4. 新发现的性能债

- RUX 约 1 GB 当前批次执行完整字段画像耗时约 462 秒；MG-K10 约 59 秒，MY009
  约 5 秒。
- 日常增量上传不能把不变批次反复全量画像作为常规路径。后续应按批次内容哈希和
  profiler 合同版本缓存字段画像，只在新批次或 profiler 版本变化时重新计算；缓存
  必须可校验、可失效，不能绕过来源修订和全量候选门。

## 5. 下一安全动作

- 等待当前正式队列完成，不频繁轮询或中断运行中租约。
- 受控重启加载方案状态聚合修复，再核对 MY009 显示为当前 queued/completed 合同。
- 三项目 V13 全量完成后执行只读语义审计；只有全量覆盖和质量门通过才使用正式
  API cutover 工具采纳、组装、确认和激活。

