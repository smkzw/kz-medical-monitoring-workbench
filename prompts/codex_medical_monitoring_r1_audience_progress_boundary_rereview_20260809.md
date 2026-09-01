请继续同一审阅 Session，对当前最新文件做只读复核。你上轮 VETO 基于：

Hard boundaries:

- 只读审阅，不修改任何工作区文件，不启动服务，不访问真实项目、provider、harness 或外部端点。
- 只审查 isolated synthetic/offline R1 audience-progress 切片；Codex 保留最终接受权。
- Runner-managed report path: `runs/codex_medical_monitoring_r1_audience_progress_boundary_rereview_20260809.md`。不得自行写入该路径，只在最终回复中返回完整报告。

Read these files only:

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
- `context/medical_monitoring_r1_audience_progress_20260809_context.md`

- `audience_progress.py`：`d2335130b5498233197bacd2597f17e30c68a077a0ada03868f283c230a3b7c5`
- `test_audience_progress.py`：`682c1883516ccdfa7808c399ca32c861a06ff58a5e1ee985df84e807455f646b`

VETO 后只修了你指出的中文相邻协议、地址、技术路径边界及其测试。当前候选 SHA：

- `audience_progress.py`：`0a93c7326d3efdb45847354f4a90ccfdf89c6884b3abe80a42fd51057c542aa5`
- `test_audience_progress.py`：`3568e17cb9f30f5c579c8f117f8896ddd67442d695e3d1b381c10cbe8f79be12`

请先核对 SHA、重新读取实现和测试，不能沿用旧版判断。请重点复跑上轮 6 个
`ACCEPTED_AND_RETURNED`：

1. label `医学 tel:+8613800138000`
2. label `医学localhost:8911`
3. label `医学 SRC/MM_R1`
4. label `医学/tmp/private`
5. target `受试者 S001 urn:example:clinical`
6. target `SRC/受试者 S001`

并扩展核查：通用 `scheme://`、小写 opaque scheme、中文紧邻 IPv4/domain、绝对/相对路径、
含中文 target 的受控技术目录段。确认这些均 fail closed，同时保留：`S001/AE`、`MG-K10`、
`SITE01`、`001-001`、`01/PD`、`受试者 S001`、`受试者 S001/AE`，以及临床标签
`核查 AE/MH 记录与 ALT:轻度升高`。

当前主进程 audience+authoritative 为 100 passed，Ruff 通过；这些不替代你的独立复核。
还请复跑聚焦/相邻测试、此前的只读与篡改 probe，并核对起止 SHA 稳定。仍只读，禁止修改
文件、启动服务、访问真实项目/provider/harness。输出新的 ACCEPT/VETO；若 ACCEPT，明确
P0-P4=0，并将 `FOO/BAR2` 这类格式合法但语义不可绝对判定的字符串记为残余风险，不作为
无限枚举理由。
