你是 R4-D07 最终独立只读 verifier，使用全新上下文。完整读取 `/Users/smkzw/.codex/AGENTS.md` 与工作台 `AGENTS.md`。

Read these files only:

- `AGENTS.md`
- `context/medical_monitoring_r4_d07_runtime_20260813_execution_context.md`
- `context/medical_monitoring_r4_d07_oracle_erratum_decision_20260814.md`
- `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_query.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- all `poc/medical_monitoring_ai_native_r4/tests/test_d07_*.py` files and `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py`
- `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_followup2.md`
- `runs/review/medical_monitoring_r4_d07_case030_verifier_20260814.md`

## Hard boundaries

- 严格只读，禁止修改文件、启动服务或读取真实项目。
- worker 与前一 verifier 报告只是待复核证据；不得照抄结论。
- 直接运行 generator 三项检查、144-case exact matrix、D07 focused suites、R4 全套、R2/R3 相邻回归、Ruff/compile/import、8911 停止检查。R1 仅运行其 `tests/` 核心目录，不收集 slices/spikes 可选依赖测试。
- 审查 runtime 是否读取 oracle/reviews、包含 case/fixture ID 分支、弱化 exact checks、修改 sys.path，或用不透明启发式过拟合 144 fixtures。
- 特别抽查 source jump、visit refs、case-free grade_state/priority/trend，以及中文 Query/Journey 是否仍保持通用合同和具体 AE/MH/CM/IP/检查事件语义。
- 对两次 oracle 窄勘误核对只改变批准叶，合同/catalog/generator 哈希保持原冻结值。
- 本阶段是 synthetic/offline D07 后端 POC，不代表产品 UI、真实模型/真实项目或医学写作子系统接受；不得启动 8911。

Write exactly one output file:

runs/review/medical_monitoring_r4_d07_final_verifier_20260814.md

该文件由 runner 持久化；你只在最终回答返回完整报告，不自行写文件。

返回 `ACCEPT_D07_RUNTIME` 或 `REVISE_D07_RUNTIME`。给出实际命令/计数、源哈希、审查发现、残余边界和下一安全动作；任何失败都必须精确定位。
