# Codex Conference Review: medical_monitoring_r3_kernel_acceptance_20260810

Date: 2026-08-10

## Verdict

**PASS — 接受最新 R3 合成/隔离 Study Intelligence 内核快照。**

本结论只覆盖 R3-A/B/C 的合成内核：资料权威、异构 listing 画像/mapping/稳定身份/规范化、全量快照 diff/影响传播、结构化规则草稿/模拟/版本化激活。它不接受真实项目医学结论、真实 listing adapter、R4 风险推理、R5 UI/Patient Journey、产品迁移或临床/监管/视觉完成。

## Boundary Compliance

- 两名参与者均只读；未读取真实项目、产品应用或医学写作子系统，未启动服务。
- Pi 白天调度按 `beijing-qwen3.8-max-window` 从声明的 Alibaba Qwen 路由替换为有效路由 `pi/cms-smk/cms-model:high`；live route 成功且无 fallback。
- Grok 使用原生 `grok-build/grok-4.5`，同一 session 完成；无 Hermes Grok、无 fallback。
- Codex 只修改 `poc/medical_monitoring_ai_native_r3/**` 的 N-1 一行功能修复及其测试，并更新本任务记录；R1/R2、产品、医学写作均未修改。
- 8911 全程无监听者；未运行真实项目或浏览器/视觉验收；未增加系统安全设计/测试。

## Participant Outputs Reviewed

- `runs/conference/medical_monitoring_r3_kernel_acceptance_20260810/general_pi_qwen38.md`：工程对抗审阅，初始快照 `ACCEPT`，运行两次 338-test 全量套件并做 26 个额外合成探测；发现唯一值得立即收口的 N-1：内部 `_record_id` 会进入快照 clinical payload 并可能制造假 `MODIFIED`。
- `runs/conference/medical_monitoring_r3_kernel_acceptance_20260810/general_pi_qwen38_followup.md`：同一 Pi session 对 N-1 修复后快照复核，104 个聚焦测试、339 个全量测试通过，最终 `ACCEPT`。
- `runs/conference/medical_monitoring_r3_kernel_acceptance_20260810/general_grok45.md`：医学监查语义/用户边界审阅，最终 `CONDITIONAL ACCEPT`；没有复现 R3 语义阻断，条件是由 Codex/Pi 重新确认测试、摘要、覆盖/消失语义及明确“NLP/LLM 自然语言解析尚未实现”。这些条件现已满足并写入本记录。

## Conference Panel Review

- 一致结论：full-export 增量身份不含 source revision，记录缺失默认 `disappeared/potential_loss` 且需要复核；只有有来源的明确 coverage confirmation 才可形成 confirmed removal，不能把缩小导出范围等同风险解除。
- 一致结论：资料冲突、低置信度 mapping、身份歧义/重复、部分日期/单位/编码不确定性均不会静默进入权威基线。
- 一致结论：RuleDraft -> simulation -> versioned activation/evaluation scope 的内核合同成立；当前不存在模型调用或自由文本到规则 AST 的 NLP/LLM 解析实现，不能宣称该能力已完成。
- Pi 的 N-1 反例可复现且虽非原阶段阻断，却会在后续流水线制造虚假数据修订；Codex 采用其最小修复并由同一独立 session 复核关闭。
- 其余 N-2（RuleDraft 状态转换由外部编排而非内部可变状态机）与 N-3（NOT_EVALUABLE raw value 参与冲突时偏保守地表面化）均是未来整合观察，不阻断本合成内核。

## Main-Venue Codex Review

- Codex 逐模块复核并在会商前修正了来源赢家/修订绑定、跨快照身份、mapping 策略来源、重复/歧义阻断、外部 row locator、coverage note、规则 sealed lifecycle、中文原生字段/日期/性别/严重程度等问题。
- 对 Pi 的 `_record_id` 反例进行最小修复：`snapshot_diff.py:637-644` 将 `_row_index` 与 `_record_id` 都视为流水线 locator，不进入临床 payload；`test_r3_c_snapshot_diff.py:141-153` 证明 transient ID 改变不会形成假 `MODIFIED`。
- 中文原生隐藏挑战覆盖通用中文 AE 表头、中文日期与程度值、mapping 候选与受试者影响传播；未使用真实项目名或路径。
- 没有把后端状态名当作用户界面文案；未来 R5 必须映射为医学监察员自然理解的中文表达。

## Codex Independent Verification

- 修复前聚焦回归：`197 passed`；R3 全量：`338 passed`。
- N-1 修复后 Codex 聚焦：`55 passed`；全量：`339 passed`。同 session 独立 verifier 复跑 R3-C 聚焦：`104 passed`；全量：`339 passed`。
- 最新 R3 根目录相对路径摘要：`418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`。命令从 `poc/medical_monitoring_ai_native_r3/` 运行，文件名以 `./` 开头。
- 同一文件集合从 workbench 运行、带 `poc/medical_monitoring_ai_native_r3/...` 路径前缀的摘要为 `30f792065ca9e01de9e3dc0b51b1dc67627da376adf7c65df6d8bb7394ccc54f`。两者差异仅来自二次哈希包含路径文本，逐文件 SHA 与 mtime 稳定，不是源码漂移。
- 上游锚点：R1 full tree `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；R2 Python `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`，均未变化。
- 最新关键逐文件 SHA：`snapshot_diff.py=d066fb9fcd5b18abcf325a3f00d03a0d3d64522a09bd7418bdb169cb2c74aec1`；`test_r3_c_snapshot_diff.py=cb266d5b78a92f9f3a0954572b2047d1eb70463876aff385691073bf7c97588a`。
- 无 `__pycache__` / `.pytest_cache`；8911 无 TCP LISTEN。

## Final Decision

冻结当前 **R3 合成/隔离内核** 为接受历史，摘要采用“R3 根目录相对路径”口径 `418b5aac…f4120d`，同时保留 workbench 前缀口径以避免误判漂移。

下一步不是直接宣称 R3 或系统完成，而是先根据实施计划建立真实 listing **结构盲测的只读/隔离输入合同**：只验证表/字段/类型/映射/身份/差异结构和反过拟合，不生成或接受真实医学结论；通过后再决定进入 R4 风险分析内核。NLP/LLM 自然语言规则解析、R4 多维风险、R5 Patient Journey/Profile/Timeline 都仍是明确未完成项。
