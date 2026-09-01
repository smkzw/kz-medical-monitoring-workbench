# R2 Batch B 独立只读验收

你是独立验收者。当前工作目录就是医学经理工作台的 `implementation/workbench`；仅验收 synthetic/offline R2 Batch B。

Read these files only:

- `poc/medical_monitoring_ai_native_r2/src/mm_r2/baselines.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/modes.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/diff.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py`
- 对应四个 `tests/test_r2_b_*.py`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_local_gate_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_negative_gate_veto1_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_negative_gate_veto2_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_review_20260810.md`

## Hard boundaries

- 不得修改 `poc/medical_monitoring_ai_native_r2/` 或任何其他产品、医学写作、真实项目文件。
- 除上述唯一验收报告外不得创建、修改、移动或删除文件。
- 不得启动服务，不得接触真实项目，不得让 8911 出现监听。
- 不得把 Batch B 扩大解释为 Batch C、R2 总体、真实端点、产品或生产验收。

不要读取或复述 worker 私有推理；从工件、System Design v1.1、R0-R8 v1.1、既有 VETO 记录和可执行证据独立判断。先记录上述八个代码/测试文件与整棵 R2 树的 SHA，结束时再次复核，若漂移则停止并报告未冻结。

必须独立检查并攻击：

1. 模块、类、服务实例或普通构造参数是否仍能伪造 DataBaseline、MedicalDecisionVersion、MonitoringRun、RiskInstance、AdjudicationRecord。
2. duck type、恶意子类、同 ID 不同内容、跨 AcceptanceService/BaselineService/项目替换能否越权。
3. baseline eligible 后发生阻断时，基线提升、运行创建、增量 diff、风险关闭是否仍 fail closed。
4. 医学判断版本的 data baseline 引用是否存在且同项目；增量 diff 是否绑定 live accepted baseline。
5. daily/pre-lock/post-lock-pre-CFDI 模式边界，尤其锁库后仅 FULL、固定快照和终态约束。
6. 候选只能建立一次；裁决 action/outcome、证据引用、当前风险对象、目标全集与本地用户身份是否在签发和使用时受约束。
7. merge/split 的完整目标、child specs、同受试者/同域/唯一身份、失败原子性和 hash chain 是否真实成立。
8. config/diff 规范化与语义哈希是否对顺序稳定、对不同数据敏感。

执行：

```bash
cd poc/medical_monitoring_ai_native_r2
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_r2_b_*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests
```

同时做内存 compile、R2 cache 检查、8911 listener 检查。仅在无 P1/P2、所有负向路径 fail closed、测试通过且首尾 SHA 一致时给 `ACCEPT`；否则给 `VETO`，列出可复现命令、实际输出、文件与行号。明确残余边界：Python 同进程反射不是安全沙箱；本验收不代表 Batch C、真实端点、产品、真实项目或生产可用性。
