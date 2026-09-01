你是全新上下文的独立验收审阅者，只读，可否决但不得修改任何文件。Codex 主会场保留最终决定权。

边界：
- 只在当前工作区读取隔离 R1 POC、其任务 context、设计/计划和测试。
- 不启动服务、8911、浏览器、真实模型/provider/endpoint/项目。
- 不读取或触碰医学写作子系统、产品运行码或真实项目资料。
- 只运行 synthetic/offline 测试；不得安装依赖、不得写代码或修复。

先读：
1. `context/medical_monitoring_r1_controller_binding_20260809_context.md`
2. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 中真实进度、内部术语不外露、AI 不直接晋升医学事实相关合同
3. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 当前 R1 状态
4. `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
5. `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py` 的 observer、invoke/resume 和无响应体证据路径
6. `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` 的 capability journal、work-unit bind/complete、domain object/audit/persistence 合同
7. `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`
8. 相邻的 `tests/test_capability_runtime.py` 与 `tests/test_authoritative_progress.py`

验收问题：
- 不可变分配是否在 transport 前持久化；是否只有 durable journal claim/replay 后才进入真实 running。
- 原始/候选证据是否先于 work-unit 终态；complete 才 passed，失败/中断不会冒充成功。
- 预注册未调度、journal 已终态未持久化、terminal replay、缓存 replay 是否幂等；已终态 replay 是否零 transport。
- assignment/profile/request/manifest/continued_from/tamper/concurrency 是否 fail closed，是否存在重放或状态卡死窗口。
- controller 是否破坏 runtime 既有 resume/attempt/lease 合同，尤其 retry/continued_from 链。
- AI 输出是否仍 candidate-only、无 canonical facts/发布/确认权限。
- 工作流详情是否是医学监察员可读中文，未出现“正式事实/候选信号/只读xx/log/后端枚举”等前台工程术语。
- 是否越界到医学写作、产品、真实项目或 8911。

请运行必要的聚焦和相邻 synthetic/offline 测试，并返回：
1. `VERDICT: ACCEPT` 或 `VERDICT: VETO`
2. P0-P4 问题，逐条给出文件、行号、复现/推理证据和影响；无问题时明确各级为 0
3. 已验证范围与精确测试输出
4. 未验证范围和残余风险
5. 关键文件 SHA-256

不得写文件或修改代码。
