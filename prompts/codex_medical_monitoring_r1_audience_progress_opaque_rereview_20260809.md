请继续同一审阅 Session，只读复核上轮 opaque-scheme VETO 的最新修订。

Hard boundaries:

- 只读审阅，不修改任何文件，不启动服务，不访问真实项目、provider、harness 或外部端点。
- 只审查 isolated synthetic/offline R1 audience-progress 切片；Codex 保留最终接受权。
- Runner-managed report path: `runs/codex_medical_monitoring_r1_audience_progress_opaque_rereview_20260809.md`。不得自行写入，只在最终回复中返回完整报告。

Read these files only:

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
- `context/medical_monitoring_r1_audience_progress_20260809_context.md`

你的上轮 VETO 基于 SHA：

- `audience_progress.py`：`0a93c7326d3efdb45847354f4a90ccfdf89c6884b3abe80a42fd51057c542aa5`
- `test_audience_progress.py`：`3568e17cb9f30f5c579c8f117f8896ddd67442d695e3d1b381c10cbe8f79be12`

当前候选 SHA：

- `audience_progress.py`：`97e9fa8256b188dcd0c4be6c0867ee2a13668e5dca3f08df25e905908e82617e`
- `test_audience_progress.py`：`fa4f1b3e492957a67d2009124a6383e0b0ea65389d7fd811f03c6cedb3fa53dd`

修复采用通用大小写不敏感、允许单字符的 scheme 拦截；仅对明确临床缩写白名单后的临床值
放行。请先核对 SHA 并重新读取，重点复跑：`医学 x:opaque`、`医学 X:opaque`、
`医学 TEL:+8613800138000`、`医学 ABOUT:blank`、`受试者 S001 x:opaque`，并扩展大小写、
单字符、`scheme://` 变体；确认它们 fail closed。必须同时保留临床标签
`核查 AE/MH 记录与 ALT:轻度升高` 和此前允许的 7 个临床 target。

主进程 audience+authoritative 为 105 passed、Ruff 通过，但不替代独立复核。还请复跑上轮
六项、聚焦/相邻测试、只读/篡改 probe，并核对起止 SHA 稳定。输出新的 ACCEPT/VETO；
若 ACCEPT，明确 P0-P4=0，并继续把 `FOO/BAR2` 记为格式合法但语义不可绝对判定的残余风险。
