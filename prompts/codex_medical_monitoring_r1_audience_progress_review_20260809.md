你是独立只读验收者。不得修改任何文件。

工作区：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

边界：

- 仅审查 isolated synthetic/offline R1 新增切片；
- 不启动服务，不访问真实项目、provider、harness 或外部端点；
- 不触碰医学写作或产品源码；
- 只可 VETO/ACCEPT，不直接修复实现。

审查对象：

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_audience_progress.py`

权威上游与验收合同：

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py` 中的
  `ManifestWorkUnit`、`NodeStatus`、`TERMINAL_NODE_STATUSES`；
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` 中的
  `structured_progress`、`get_manifest`、`list_work_unit_runs`；
- `context/medical_monitoring_r1_audience_progress_20260809_context.md`。

独立验证以下结论，不依据作者说明：

1. 投影严格只读，`completed`、`total`、`percent`、阶段计数与权威记录守恒；
2. pending/running/passed/reused/skipped/not_applicable/blocked/failed 和 retry 的中文语义准确，
   不把失败/阻断误写为成功；
3. 任何返回值都不泄露 run/work-unit/node/attempt/provider/model/selector/hash/audit/backend、
   原始 detail/log、文件路径或技术地址；
4. 不出现“正式事实”“候选信号”“只读xx”等非医学监查表达；
5. audience stage/label/target 不合格时失败关闭，且不能靠异常类型或非预期输入绕过；
6. 新模块不修改 Store/Runtime，不造成已有权威进度合同回归。

可运行必要的只读测试、静态检查和临时进程内 adversarial probe；临时文件仅可使用系统临时目录，
结束后不得保留。禁止修改审查对象或工作区证据文件。

输出格式：

- 首行 `ACCEPT` 或 `VETO`；
- 按 P0-P4 列出问题，每项含文件:行号、复现、影响、最小修复；
- 列出实际命令及结果、确认无问题的范围、残余风险；
- 若无 P0-P4，明确写“P0-P4：0”。
