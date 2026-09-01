# Fresh-context R1 lifecycle observer integration review

你是独立 verifier，在当前工作台只读审阅 `poc/medical_monitoring_ai_native_r1`。

目标：判断最近加入的 lifecycle observer 接线是否满足隔离 R1 现有合同，是否引入未测副作用，
或破坏 capability/runtime/controller/manifest 的单一权威与审计边界。

执行要求：

1. 遵循运行时自动加载的全局 AGENTS.md，并完整读取工作台 AGENTS.md；再读取 R1 实施计划步骤 6-8。
2. 读取当前 `capability_runtime.py`、`test_capability_runtime.py`、`__init__.py`，用 `rg` 定位
   lifecycle observer 的所有定义、调用者、导出和测试；不得读取任何其他 reviewer 输出。
3. 首次读取后记录这些相关文件 SHA；只运行最小决定性测试及必要相邻回归；结束前再次比对 SHA。
4. 不得修改任何文件，不得启动服务/8911，不得访问产品、医学写作、真实项目、真实 provider 或凭据。
5. 输出 `ACCEPT` 或 `VETO`，仅针对 lifecycle observer 的 R1 接线；给出代码/测试定位、实际命令
   与结果、未覆盖面、是否阻断 R1 总体验收。若执行中 SHA 漂移，报告 `UNFROZEN`，不得 ACCEPT。

Read these files only:
- `AGENTS.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/__init__.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/graph.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_integrated_closure.py`

Runner-managed report path: `runs/conference/medical_monitoring_r1_overall_acceptance_20260810/lifecycle_observer_luna_review.md`.
只把最终报告返回给调用者，不得自行编辑该报告文件。

## Hard boundaries

- 本审阅不接受生产沙箱、产品接线或 R1 总体完成。
- 只读；不得修改源码、测试、记录或输出目录中的既有文件。
- 不启动任何服务、8911、真实项目或 provider；不使用网络。
- 不读取任何其他 reviewer 输出或会议记录。
